"""E2a — Surface-Invariance Violation rate (claim C2, routing domain).

A gatekeeper should not change its decision when only the prompt's *form*
changes. We train each router, then on held-out prompts compare its decision on
the original vs an intent-preserving surface perturbation. SIV = flip rate.

Lower SIV = more intent-robust. Hypothesis: surface/TF-IDF routers have high
SIV; the semantic router lower. Reported per-perturbation + aggregated over the
"clean" (least-contestable) perturbations.

Outputs results/e2_siv.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import models as M  # noqa: E402
import perturb as P  # noqa: E402
import routerbench as rb  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "e2_siv.json")
SEEDS = [0, 1, 2]
TEST_SIZE = 0.25
N_EVAL = 5000  # cap test prompts scored (keeps semantic encoding tractable on CPU)


def main():
    t0 = time.time()
    df = rb.load_labeled()
    print(rb.summarize(df))
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()

    routers = M.build_routers()
    print(f"\nrouters: {list(routers)}  (semantic={'semantic_logreg' in routers})")
    pert_names = list(P.PERTURBATIONS)

    # per model: per perturbation: list of SIV over seeds; plus original accuracy
    agg = {name: {"siv": {p: [] for p in pert_names}, "acc": []} for name in routers}

    for seed in SEEDS:
        idx = np.arange(len(y))
        tr, te = train_test_split(idx, test_size=TEST_SIZE, random_state=seed, stratify=y)
        rng = np.random.RandomState(seed)
        if len(te) > N_EVAL:
            te = rng.choice(te, size=N_EVAL, replace=False)
        tr_texts = [texts[i] for i in tr]
        te_texts = [texts[i] for i in te]
        y_te = y[te]
        # Precompute perturbed test sets once (shared across models).
        perturbed = {p: P.apply_perturbation(te_texts, p) for p in pert_names}

        for name, factory in routers.items():
            clf = factory().fit(tr_texts, y[tr])
            base_pred = clf.predict(te_texts)
            agg[name]["acc"].append(accuracy_score(y_te, base_pred))
            for p in pert_names:
                pert_pred = clf.predict(perturbed[p])
                siv = float(np.mean(pert_pred != base_pred))
                agg[name]["siv"][p].append(siv)
            print(f"  seed{seed} {name:16s} acc={agg[name]['acc'][-1]:.3f} "
                  f"siv_clean={np.mean([agg[name]['siv'][p][-1] for p in P.CLEAN_PERTURBATIONS]):.3f}")

    # Reduce to mean/std.
    results = {}
    for name in routers:
        per_pert = {p: {"mean": float(np.mean(agg[name]["siv"][p])),
                        "std": float(np.std(agg[name]["siv"][p]))} for p in pert_names}
        clean_vals = [np.mean(agg[name]["siv"][p]) for p in P.CLEAN_PERTURBATIONS]
        results[name] = {
            "acc_mean": float(np.mean(agg[name]["acc"])),
            "siv_per_perturbation": per_pert,
            "siv_clean_mean": float(np.mean(clean_vals)),
            "siv_clean_std": float(np.std(clean_vals)),
        }

    meta = {"n_samples": int(len(y)), "base_rate": float(y.mean()),
            "n_seeds": len(SEEDS), "n_eval": int(min(N_EVAL, len(te))),
            "clean_perturbations": P.CLEAN_PERTURBATIONS,
            "all_perturbations": pert_names,
            "semantic_available": "semantic_logreg" in routers,
            "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "meta": meta}, f, indent=2)

    print("\n=== SIV (clean-perturbation mean flip rate; lower=better) ===")
    for name in sorted(results, key=lambda n: results[n]["siv_clean_mean"]):
        print(f"  {name:16s} SIV={results[name]['siv_clean_mean']:.3f}"
              f"±{results[name]['siv_clean_std']:.3f}  acc={results[name]['acc_mean']:.3f}")
    print(f"\nsaved -> {RESULTS}  ({meta['runtime_sec']}s)")


if __name__ == "__main__":
    main()
