"""Routing intervention done RIGHT — length-padding on RouteLLM (clean C2).

Replaces the discredited code-fence SIV (a StandardScaler×rare-feature artifact).
Here we target the ACTUAL learned shortcut (length) with an intent-preserving,
in-distribution perturbation and a RobustScaler model — so a flip is real model
behaviour, not OOD extrapolation.

Take prompts the router sends to the WEAK model (proba<0.5). Pad each with
content-free filler until its token count reaches the dataset MEDIAN (a normal
length — firmly in-distribution; capped so we never exceed p90). The task is
unchanged, so the gold routing label is unchanged. Escalation rate = fraction
that flip to "needs the strong model". A length-keyed router escalates verbose-
but-simple prompts; a semantic router should not.

Outputs results/r_routellm_padding.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routellm as rl  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "r_routellm_padding.json")
SEEDS = [0, 1, 2]
FILLER = " I would really appreciate your help with this. Thank you so much for taking the time."
RNG = np.random.default_rng(0)


def _enc():
    import tiktoken
    return tiktoken.get_encoding("cl100k_base")


def pad_to(text: str, target_tokens: int, enc, filler_tok: int) -> str:
    cur = len(enc.encode(text, disallowed_special=()))
    if cur >= target_tokens:
        return text
    reps = int(np.ceil((target_tokens - cur) / max(filler_tok, 1)))
    return text + FILLER * reps


def boot_ci(vals, n=2000):
    if len(vals) == 0:
        return (float("nan"),) * 3
    m = [vals[RNG.integers(0, len(vals), len(vals))].mean() for _ in range(n)]
    return float(np.mean(vals)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    t0 = time.time()
    df = rl.load_labeled()
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()
    enc = _enc()
    tok_len = np.array([len(enc.encode(t, disallowed_special=())) for t in texts])
    print(f"rows={len(df)} base={y.mean():.3f} tok median={np.median(tok_len):.0f} p90={np.percentile(tok_len,90):.0f}")
    filler_tok = len(enc.encode(FILLER))

    routers = {
        "surface_robust": lambda: M.SurfaceRouter("logreg", scaler="robust"),
        "length_only_robust": None,  # handled inline
        "semantic": lambda: M.SemanticRouter("all-MiniLM-L6-v2"),
    }

    out = {}
    for name in routers:
        esc_rates = []
        for seed in SEEDS:
            tr, te = train_test_split(np.arange(len(y)), test_size=0.25, random_state=seed, stratify=y)
            target = int(np.median(tok_len[tr]))
            cap = int(np.percentile(tok_len[tr], 90))
            target = min(target, cap)

            if name == "length_only_robust":
                Xtr = tok_len[tr].reshape(-1, 1).astype(float)
                clf = make_pipeline(RobustScaler(), LogisticRegression(max_iter=1000)).fit(Xtr, y[tr])
                proba = lambda T: clf.predict_proba(
                    np.array([len(enc.encode(t, disallowed_special=())) for t in T]).reshape(-1, 1).astype(float))[:, 1]
            else:
                m = routers[name]().fit([texts[i] for i in tr], y[tr])
                proba = lambda T: m.proba(T)

            te_texts = [texts[i] for i in te]
            base_p = proba(te_texts)
            weak_idx = np.where(base_p < 0.5)[0]
            # pad only SHORT weak-routed prompts (below median) up to median length
            short_weak = [i for i in weak_idx if len(enc.encode(te_texts[i], disallowed_special=())) < target]
            padded = [pad_to(te_texts[i], target, enc, filler_tok) for i in short_weak]
            if not padded:
                esc_rates.append(0.0); continue
            new_p = proba(padded)
            escalated = float(np.mean(new_p >= 0.5))
            esc_rates.append(escalated)
        mu, lo, hi = boot_ci(np.array(esc_rates))
        out[name] = {"escalation_rate_mean": float(np.mean(esc_rates)),
                     "escalation_rate_std": float(np.std(esc_rates)),
                     "ci95": [lo, hi], "n_seeds": len(SEEDS)}
        print(f"  {name:20s} escalation={out[name]['escalation_rate_mean']:.3f} ± {out[name]['escalation_rate_std']:.3f}")

    meta = {"filler_tokens": filler_tok, "note": "padded short weak-routed prompts to in-distribution median length (capped p90)",
            "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": out, "meta": meta}, f, indent=2)
    print(f"\nsaved -> {RESULTS}  ({meta['runtime_sec']}s)")
    print("KEY: high escalation for length/surface-keyed routers, low for semantic = "
          "the router escalates verbose-but-simple prompts (intent-preserving).")


if __name__ == "__main__":
    main()
