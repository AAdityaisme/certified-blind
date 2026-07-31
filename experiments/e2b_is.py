"""E2b — Intent-Sensitivity via surface-controlled AUC (claim C2, routing).

Construct minimal pairs from real data: match each held-out positive
(route_premium=1) prompt to a near-identical-*surface* negative (route_premium=0)
prompt. Same form, different intent/difficulty. A gatekeeper that reads intent
should still rank the pair correctly; a surface gatekeeper sees ~identical
features, so its AUC on matched pairs collapses toward 0.5.

IS = pairwise accuracy on surface-matched opposite-label pairs
   = P(proba[positive] > proba[negative]) over matched pairs (ties = 0.5).
A model whose only signal is surface form -> IS ~ 0.5. A model that uses
content/intent -> IS > 0.5.

Outputs results/e2b_is.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routerbench as rb  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "e2b_is.json")
SEEDS = [0, 1, 2]
TEST_SIZE = 0.25
CALIPER_PCT = 25  # keep the tightest 25% of surface matches


def matched_pairs(surf_std, labels, seed):
    """For each positive, nearest negative in standardized surface space.
    Returns (pos_idx, neg_idx, dist) arrays for pairs within the caliper."""
    pos = np.where(labels == 1)[0]
    neg = np.where(labels == 0)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(surf_std[neg])
    dist, j = nn.kneighbors(surf_std[pos])
    dist = dist[:, 0]; neg_match = neg[j[:, 0]]
    caliper = np.percentile(dist, CALIPER_PCT)
    keep = dist <= caliper
    return pos[keep], neg_match[keep], dist[keep]


def pairwise_is(proba, pos_idx, neg_idx):
    pp, pn = proba[pos_idx], proba[neg_idx]
    return float(np.mean((pp > pn) + 0.5 * (pp == pn)))


def main():
    t0 = time.time()
    df = rb.load_labeled()
    y = df["route_premium"].to_numpy()
    texts = df["prompt"].tolist()
    surf_all = feat.surface_feature_matrix(texts).to_numpy()

    routers = M.build_routers()
    print(f"routers: {list(routers)}\n")

    agg = {n: {"is": [], "auc": []} for n in routers}
    pair_stats = {"n_pairs": [], "mean_dist": []}

    for seed in SEEDS:
        idx = np.arange(len(y))
        tr, te = train_test_split(idx, test_size=TEST_SIZE, random_state=seed, stratify=y)
        scaler = StandardScaler().fit(surf_all[tr])
        surf_te = scaler.transform(surf_all[te])
        y_te = y[te]
        pos_i, neg_i, dist = matched_pairs(surf_te, y_te, seed)
        pair_stats["n_pairs"].append(int(len(pos_i)))
        pair_stats["mean_dist"].append(float(np.mean(dist)))
        te_texts = [texts[i] for i in te]

        for name, factory in routers.items():
            clf = factory().fit([texts[i] for i in tr], y[tr])
            proba = clf.proba(te_texts)
            agg[name]["is"].append(pairwise_is(proba, pos_i, neg_i))
            try:
                agg[name]["auc"].append(roc_auc_score(y_te, proba))
            except Exception:
                agg[name]["auc"].append(float("nan"))
        print(f"  seed{seed}: {len(pos_i)} matched pairs, mean surf-dist={np.mean(dist):.3f}")
        for name in routers:
            print(f"      {name:16s} IS={agg[name]['is'][-1]:.3f}  (uncond AUC={agg[name]['auc'][-1]:.3f})")

    results = {n: {"is_mean": float(np.mean(agg[n]["is"])), "is_std": float(np.std(agg[n]["is"])),
                   "uncond_auc_mean": float(np.nanmean(agg[n]["auc"]))} for n in routers}
    meta = {"n_seeds": len(SEEDS), "caliper_pct": CALIPER_PCT,
            "mean_n_pairs": float(np.mean(pair_stats["n_pairs"])),
            "mean_match_dist": float(np.mean(pair_stats["mean_dist"])),
            "semantic_available": any("semantic" in n for n in routers),
            "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "meta": meta}, f, indent=2)

    print("\n=== Intent-Sensitivity (surface-controlled AUC; 0.5 = no intent signal) ===")
    for n in sorted(results, key=lambda k: -results[k]["is_mean"]):
        print(f"  {n:16s} IS={results[n]['is_mean']:.3f}±{results[n]['is_std']:.3f}"
              f"  (unconditional AUC {results[n]['uncond_auc_mean']:.3f})")
    print(f"\n~{int(meta['mean_n_pairs'])} matched pairs/seed, mean surface dist {meta['mean_match_dist']:.3f}")
    print(f"saved -> {RESULTS}  ({meta['runtime_sec']}s)")


if __name__ == "__main__":
    main()
