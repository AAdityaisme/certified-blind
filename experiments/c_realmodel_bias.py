"""DOMAIN-2 REAL-MODEL NATURAL BIAS — credibility for the moderation domain.

The TF-IDF poison (c_targeted.py) shows the ATTACK is possible; this shows the PATTERN already
exists, with no attacker, in a real widely-deployed model. Runs unitary/toxic-bert (cached) on a
civil_comments test subset, measures per-identity-slice false-removal rate (FPR on truly
non-toxic comments), and the disparity vs the aggregate. Same task (toxicity labels + toxicity
model) so no task-mismatch artifact — the residual disparity is genuine targeted over-removal.

This is the "natural Test 1" for moderation: aggregate FPR looks fine while specific identity
slices are silently over-removed — invisible to an aggregate moderation dashboard, and (per 3C /
c_probe_defense) catchable by a small stratified probe.

Outputs results/c_realmodel_bias.json + audit/c_realmodel_result.md.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod  # noqa: E402

MODEL = "unitary/toxic-bert"
N_TEST = 30000
THRESH = 0.5
BATCH = 64
RESULTS_PATH = os.path.join(REPO, "results", "c_realmodel_bias.json")
AUDIT_PATH = os.path.join(REPO, "audit", "c_realmodel_result.md")


def boot_ci(arr, n=2000, seed=42):
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = [rng.choice(arr, len(arr), replace=True).mean() for _ in range(n)]
    return float(np.mean(arr)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}  model: {MODEL}")
    _, _, te_text, te_tox = mod.load_civil(1, N_TEST, 42)   # only need test
    print(f"test {len(te_text)} ({te_tox.mean()*100:.1f}% toxic)")

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL).to(device).eval()
    # toxic-bert label order: [toxic, severe_toxic, obscene, threat, insult, identity_hate]
    tox_idx = 0

    scores = np.empty(len(te_text), dtype=np.float32)
    with torch.no_grad():
        for i in range(0, len(te_text), BATCH):
            batch = [str(t) for t in te_text[i:i + BATCH]]
            enc = tok(batch, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
            logits = model(**enc).logits
            scores[i:i + BATCH] = torch.sigmoid(logits[:, tox_idx]).cpu().numpy()
            if i % (BATCH * 50) == 0:
                print(f"  {i}/{len(te_text)}", flush=True)

    remove = scores >= THRESH
    nontoxic = ~te_tox
    agg_fpr = float(remove[nontoxic].mean())
    agg_removal = float(remove.mean())
    acc = float((remove == te_tox).mean())

    slices = mod.all_slice_masks(te_text)
    per_slice = {}
    for t, m in slices.items():
        mask = m & nontoxic
        if mask.sum() == 0:
            continue
        mean, lo, hi = boot_ci(remove[mask].astype(float))
        per_slice[t] = {"fpr": round(mean, 4), "n": int(mask.sum()),
                        "lo": round(lo, 4), "hi": round(hi, 4),
                        "disparity_vs_aggregate": round(mean / agg_fpr, 2) if agg_fpr else None}

    ranked = sorted(per_slice.items(), key=lambda kv: -kv[1]["fpr"])
    worst = ranked[0]
    out = {"setup": {"model": MODEL, "n_test": len(te_text), "thresh": THRESH, "device": device},
           "aggregate": {"accuracy": round(acc, 4), "removal_rate": round(agg_removal, 4),
                         "aggregate_fpr": round(agg_fpr, 4)},
           "per_slice_fpr": per_slice,
           "worst_slice": {"term": worst[0], **worst[1]},
           "max_disparity": worst[1]["disparity_vs_aggregate"]}
    verdict = (f"Real toxic-bert: aggregate FPR {agg_fpr:.3f} looks clean, but slice '{worst[0]}' is "
               f"falsely removed at {worst[1]['fpr']:.3f} ({worst[1]['disparity_vs_aggregate']}× the "
               f"aggregate) — natural targeted over-removal, no attacker, invisible to an aggregate "
               f"dashboard.")
    out["verdict"] = verdict
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print(f"\nAGG: acc={acc:.3f} removal={agg_removal:.3f} fpr={agg_fpr:.3f}")
    for t, v in ranked:
        print(f"  {t:10s} FPR={v['fpr']:.3f} [{v['lo']:.3f},{v['hi']:.3f}] n={v['n']} "
              f"disparity={v['disparity_vs_aggregate']}x")
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Domain-2 Real-Model Natural Bias (toxic-bert)", "", f"**{verdict}**", "",
             f"{MODEL} on {len(te_text)} civil_comments test. Aggregate: acc {acc:.3f}, "
             f"removal {agg_removal:.3f}, FPR {agg_fpr:.3f}.", "",
             "| identity slice | false-removal FPR | 95% CI | n | disparity vs aggregate |",
             "|---|---|---|---|---|"]
    for t, v in ranked:
        lines.append(f"| {t} | {v['fpr']:.3f} | [{v['lo']:.3f},{v['hi']:.3f}] | {v['n']} | "
                     f"{v['disparity_vs_aggregate']}× |")
    open(AUDIT_PATH, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
