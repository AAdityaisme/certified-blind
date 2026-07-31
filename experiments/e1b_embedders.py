"""E1b — embedder robustness for claim C1.

Preempts "semantic only ties surface because MiniLM is a weak intent proxy."
Re-runs the parity comparison with progressively stronger sentence encoders
(MiniLM 22M -> mpnet 110M -> BGE). If even strong encoders don't beat the
surface/lexical routers on routing AUC, the metric really is saturated by form.

Outputs results/e1b_embedders.json.
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

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "e1b_embedders.json")
SEEDS = [0, 1, 2]
TEST_SIZE = 0.25
EMBEDDERS = ("all-MiniLM-L6-v2", "all-mpnet-base-v2", "BAAI/bge-small-en-v1.5")


def main():
    t0 = time.time()
    df = rb.load_labeled()
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()
    routers = M.build_routers(include_semantic=True, semantic_models=EMBEDDERS)
    print(f"routers: {list(routers)}\n")

    results = {}
    for name, factory in routers.items():
        accs, aucs = [], []
        for seed in SEEDS:
            idx = np.arange(len(y))
            tr, te = train_test_split(idx, test_size=TEST_SIZE, random_state=seed, stratify=y)
            clf = factory().fit([texts[i] for i in tr], y[tr])
            te_texts = [texts[i] for i in te]
            accs.append(accuracy_score(y[te], clf.predict(te_texts)))
            try:
                aucs.append(roc_auc_score(y[te], clf.proba(te_texts)))
            except Exception:
                aucs.append(float("nan"))
        results[name] = {"acc_mean": float(np.mean(accs)), "auc_mean": float(np.nanmean(aucs)),
                         "auc_std": float(np.nanstd(aucs))}
        print(f"  {name:18s} acc={results[name]['acc_mean']:.4f}  auc={results[name]['auc_mean']:.4f}")

    best_surface = max(results[n]["auc_mean"] for n in ("surface_logreg", "surface_hgb", "tfidf_logreg"))
    best_semantic = max((results[n]["auc_mean"] for n in results if n.startswith("semantic")), default=float("nan"))
    meta = {"best_surface_auc": best_surface, "best_semantic_auc": best_semantic,
            "semantic_minus_surface": best_semantic - best_surface,
            "n_seeds": len(SEEDS), "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "meta": meta}, f, indent=2)
    print(f"\nbest semantic AUC {best_semantic:.4f} - best surface/lexical {best_surface:.4f}"
          f" = {meta['semantic_minus_surface']:+.4f}")
    print(f"saved -> {RESULTS}  ({meta['runtime_sec']}s)")


if __name__ == "__main__":
    main()
