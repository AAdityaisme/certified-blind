"""E1 — routing accuracy-parity (claim C1).

Question: does a *surface-only* gatekeeper match an *intent-aware* (semantic)
one on the stated metric (routing accuracy / ROC-AUC)? If yes, accuracy cannot
tell the two apart — the trap the paper is about.

Outputs results/e1_main.json with mean+/-std accuracy & ROC-AUC over N seeds.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import models as M  # noqa: E402
import routerbench as rb  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "e1_main.json")
SEEDS = [0, 1, 2, 3, 4]
TEST_SIZE = 0.25


def main():
    t0 = time.time()
    df = rb.load_labeled()
    print(rb.summarize(df))
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()

    routers = M.build_routers()
    print(f"\nrouters: {list(routers)}  semantic={'semantic_logreg' in routers}\n")

    results = {}
    for name, factory in routers.items():
        accs, aucs = [], []
        for seed in SEEDS:
            idx = np.arange(len(y))
            tr, te = train_test_split(idx, test_size=TEST_SIZE,
                                      random_state=seed, stratify=y)
            tr_texts = [texts[i] for i in tr]
            te_texts = [texts[i] for i in te]
            clf = factory().fit(tr_texts, y[tr])
            pred = clf.predict(te_texts)
            accs.append(accuracy_score(y[te], pred))
            try:
                aucs.append(roc_auc_score(y[te], clf.proba(te_texts)))
            except Exception:
                aucs.append(float("nan"))
        results[name] = {
            "acc_mean": float(np.mean(accs)), "acc_std": float(np.std(accs)),
            "auc_mean": float(np.nanmean(aucs)), "auc_std": float(np.nanstd(aucs)),
            "n_seeds": len(SEEDS),
        }
        print(f"  {name:16s} acc={results[name]['acc_mean']:.4f}"
              f"±{results[name]['acc_std']:.4f}  auc={results[name]['auc_mean']:.4f}"
              f"±{results[name]['auc_std']:.4f}")

    meta = {
        "n_samples": int(len(y)), "base_rate": float(y.mean()),
        "label": {k: df.attrs.get(k) for k in ("mode", "weak", "strong")},
        "models_in_bench": df.attrs.get("models"),
        "semantic_available": "semantic_logreg" in routers,
        "runtime_sec": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "meta": meta}, f, indent=2)
    print(f"\nsaved -> {RESULTS}  ({meta['runtime_sec']}s)")

    if "semantic_logreg" in results:
        best_surface = max(results["surface_logreg"]["auc_mean"],
                           results["surface_hgb"]["auc_mean"],
                           results["tfidf_logreg"]["auc_mean"])
        gap = results["semantic_logreg"]["auc_mean"] - best_surface
        print(f"C1 AUC gap (semantic - best lexical) = {gap:+.4f}")


if __name__ == "__main__":
    main()
