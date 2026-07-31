"""Audit follow-up: the HONEST C1 grid, controlling the eval-identity confound.

For each split type (random vs group-by-eval = train/test on disjoint
benchmarks), report AUC for every router plus two diagnostic baselines:
  - length_only : LogReg on a single feature (n_tokens). Is it all just length?
  - eval_identity: LogReg on eval_name one-hot. The 'just know the benchmark'
    ceiling (meaningful only under the random split).

Group-by-eval is the honest test of whether surface->routing GENERALIZES across
benchmarks or is benchmark base-rate detection. 3 seeds (3 benchmark partitions).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routerbench as rb  # noqa: E402

SEEDS = [0, 1, 2]
OUT = os.path.join(os.path.dirname(__file__), "honest_c1.json")


def main():
    df = rb.load_labeled()
    texts = df["prompt"].tolist()
    y = df["route_premium"].to_numpy()
    evals = df["eval_name"].to_numpy()
    n = len(df)
    tok = feat.surface_feature_matrix(texts)["n_tokens"].to_numpy().reshape(-1, 1)

    def length_only_auc(tr, te):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        clf.fit(tok[tr], y[tr]); return roc_auc_score(y[te], clf.predict_proba(tok[te])[:, 1])

    def eval_id_auc(tr, te):
        enc = OneHotEncoder(handle_unknown="ignore").fit(evals[tr].reshape(-1, 1))
        clf = LogisticRegression(max_iter=1000).fit(enc.transform(evals[tr].reshape(-1, 1)), y[tr])
        return roc_auc_score(y[te], clf.predict_proba(enc.transform(evals[te].reshape(-1, 1)))[:, 1])

    def router_auc(factory, tr, te):
        clf = factory().fit([texts[i] for i in tr], y[tr])
        return roc_auc_score(y[te], clf.proba([texts[i] for i in te]))

    routers = {
        "surface_logreg": lambda: M.SurfaceRouter("logreg"),
        "surface_hgb": lambda: M.SurfaceRouter("hgb"),
        "tfidf_logreg": lambda: M.TfidfRouter(),
        "semantic_minilm": lambda: M.SemanticRouter("all-MiniLM-L6-v2"),
    }

    def split_indices(kind, seed):
        idx = np.arange(n)
        if kind == "random":
            return train_test_split(idx, test_size=0.25, random_state=seed, stratify=y)
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, te = next(gss.split(idx, y, groups=evals))
        return tr, te

    grid = {}
    for kind in ["random", "group-by-eval"]:
        rows = {k: [] for k in ["length_only", "eval_identity", *routers]}
        for seed in SEEDS:
            tr, te = split_indices(kind, seed)
            rows["length_only"].append(length_only_auc(tr, te))
            rows["eval_identity"].append(eval_id_auc(tr, te))
            for name, fac in routers.items():
                rows[name].append(router_auc(fac, tr, te))
        grid[kind] = {k: {"auc_mean": float(np.mean(v)), "auc_std": float(np.std(v))}
                      for k, v in rows.items()}
        print(f"\n=== {kind} split (AUC mean±std over {len(SEEDS)} seeds) ===")
        for k, v in grid[kind].items():
            print(f"  {k:16s} {v['auc_mean']:.3f} ± {v['auc_std']:.3f}")

    with open(OUT, "w") as f:
        json.dump(grid, f, indent=2)
    print(f"\nsaved -> {OUT}")
    print("\nKEY: group-by-eval is the honest cross-benchmark test. eval_identity AUC "
          "under RANDOM split ~= the confound ceiling.")


if __name__ == "__main__":
    main()
