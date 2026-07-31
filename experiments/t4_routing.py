"""TIER 4 — routing-track depth.

4.1 Routing audit parallel: does cross-router disagreement flag a router's MIS-ROUTES
    (sent to weak but truly needed strong) — the recoverable-domain analogue of the
    satellite consensus audit? (It should work, but matters less: routing is recoverable.)
4.2 Judge-bias robustness: does prompt length predict routing under RouterBench's
    EXACT-MATCH grading (not a GPT-4 judge)? If yes, the length signal is not merely
    the judge-verbosity-bias documented by Garg & Sagtani (2605.07395).

Outputs results/t4_routing.json.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routellm as rl  # noqa: E402
import routerbench as rb  # noqa: E402


def auc(l, s):
    return float(roc_auc_score(l, s)) if len(np.unique(l)) == 2 else float("nan")


def main():
    out = {}

    # ---- 4.1 routing audit parallel (RouteLLM) ----
    d = rl.load_labeled()
    y = d["route_premium"].to_numpy(); texts = d["prompt"].tolist()
    tr, te = train_test_split(np.arange(len(y)), test_size=0.3, random_state=0, stratify=y)
    routers = {"surface": M.SurfaceRouter("hgb"), "tfidf": M.TfidfRouter(), "semantic": M.SemanticRouter("all-MiniLM-L6-v2")}
    proba = {}
    for nm, r in routers.items():
        r.fit([texts[i] for i in tr], y[tr])
        proba[nm] = r.proba([texts[i] for i in te])
    yte = y[te]
    # primary = surface router; route_weak = proba<0.5; bad route = route_weak & truly needs strong
    primary = proba["surface"]
    route_weak = primary < 0.5
    bad_route = route_weak & (yte == 1)
    # audit signal = mean of OTHER routers' escalate-proba (high => others say escalate => probable mis-route)
    others = np.mean([proba["tfidf"], proba["semantic"]], axis=0)
    among = route_weak
    out["routing_audit_parallel"] = {
        "n_route_weak": int(among.sum()), "n_bad_route": int(bad_route.sum()),
        "disagreement_AUC": auc(bad_route[among].astype(int), others[among]),
        "note": "recoverable domain — audit works but matters less (retry is cheap)"}
    print(f"[4.1] routing audit: among {int(among.sum())} route-weak, {int(bad_route.sum())} bad; "
          f"disagreement AUC={out['routing_audit_parallel']['disagreement_AUC']:.3f}")

    # ---- 4.2 length predicts routing under exact-match (RouterBench) vs judge (RouteLLM) ----
    rbdf = rb.load_labeled()  # pairwise mixtral-vs-gpt4, benchmark grading (exact-match-style)
    yb = rbdf["route_premium"].to_numpy(); tb = rbdf["prompt"].tolist()
    tok_b = feat.surface_feature_matrix(tb)["n_tokens"].to_numpy().reshape(-1, 1)
    trb, teb = train_test_split(np.arange(len(yb)), test_size=0.25, random_state=0, stratify=yb)
    clf = make_pipeline(RobustScaler(), LogisticRegression(max_iter=1000)).fit(tok_b[trb], yb[trb])
    rb_len_auc = auc(yb[teb], clf.predict_proba(tok_b[teb])[:, 1])
    # RouteLLM length (judge labels)
    tok_l = feat.surface_feature_matrix(texts)["n_tokens"].to_numpy().reshape(-1, 1)
    clf2 = make_pipeline(RobustScaler(), LogisticRegression(max_iter=1000)).fit(tok_l[tr], y[tr])
    rl_len_auc = auc(yte, clf2.predict_proba(tok_l[te])[:, 1])
    out["judge_bias_robustness"] = {
        "routerbench_exactmatch_length_AUC": rb_len_auc,
        "routellm_judge_length_AUC": rl_len_auc,
        "verdict": "length predicts routing under BOTH grading schemes => not merely judge-verbosity-bias"
                   if (rb_len_auc > 0.55 and rl_len_auc > 0.55) else "length signal may be judge-specific"}
    print(f"[4.2] length_only AUC: RouterBench(exact-match)={rb_len_auc:.3f}  RouteLLM(judge)={rl_len_auc:.3f}")
    print("      =>", out["judge_bias_robustness"]["verdict"])

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "t4_routing.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nsaved -> results/t4_routing.json")


if __name__ == "__main__":
    main()
