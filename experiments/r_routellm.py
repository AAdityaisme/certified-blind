"""R-RouteLLM — the decisive confound-free C1 test.

On RouteLLM's homogeneous Arena data (no sub-benchmarks => no eval-identity
confound), does prompt surface form predict "needs the strong model", and does
surface match semantic? This is the clean test RouterBench couldn't be.

Reports AUC (5 seeds) for majority, length_only, surface (linear+trees), tfidf,
semantic. Interpretation:
  - surface AUC ~ chance (0.5)  => routing shortcut was a RouterBench artifact.
  - surface AUC > chance ~ semantic => a real surface shortcut, confound-free.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routellm as rl  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "r_routellm.json")
SEEDS = [0, 1, 2, 3, 4]
TEST_SIZE = 0.25


def main():
    t0 = time.time()
    df = rl.load_labeled()
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()
    print(f"rows={len(df)}  base_rate={y.mean():.3f}  ({df.attrs['source']})")

    tok = feat.surface_feature_matrix(texts)["n_tokens"].to_numpy().reshape(-1, 1)
    routers = M.build_routers()
    print(f"routers: {list(routers)} + length_only\n")

    results = {}
    for name in [*routers, "length_only"]:
        aucs = []
        for seed in SEEDS:
            tr, te = train_test_split(np.arange(len(y)), test_size=TEST_SIZE,
                                      random_state=seed, stratify=y)
            if name == "length_only":
                clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
                clf.fit(tok[tr], y[tr])
                p = clf.predict_proba(tok[te])[:, 1]
            else:
                clf = routers[name]().fit([texts[i] for i in tr], y[tr])
                p = clf.proba([texts[i] for i in te])
            aucs.append(roc_auc_score(y[te], p))
        results[name] = {"auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs))}
        print(f"  {name:16s} AUC={results[name]['auc_mean']:.4f} ± {results[name]['auc_std']:.4f}")

    surf = max(results["surface_logreg"]["auc_mean"], results["surface_hgb"]["auc_mean"])
    sem = results.get("semantic_logreg", {}).get("auc_mean", float("nan"))
    meta = {"n": int(len(y)), "base_rate": float(y.mean()),
            "best_surface_auc": surf, "semantic_auc": sem,
            "semantic_minus_surface": sem - surf, "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "meta": meta}, f, indent=2)
    print(f"\nbest_surface={surf:.4f}  semantic={sem:.4f}  (sem-surf={meta['semantic_minus_surface']:+.4f})")
    print("VERDICT:", "surface~chance => routing shortcut was RouterBench artifact"
          if surf < 0.55 else "surface>chance, confound-free => real surface signal")
    print(f"saved -> {RESULTS}  ({meta['runtime_sec']}s)")


if __name__ == "__main__":
    main()
