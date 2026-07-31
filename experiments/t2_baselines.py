"""TIER 2 — reviewer-demanded baselines & ablations (CloudSEN12 train).

Target detector = KappaMask (worst over-discarder). Task: among its discards,
identify the BAD ones (truly clear, D=1&C=1).

2.1 Audit vs simpler signals: consensus vs single-best-alt-detector vs single NDSI
    vs single brightness vs probe-SUPERVISED. AUC + average precision (PR).
2.2 Panel-size ablation: consensus AUC vs # detectors in the panel (deployability).
2.3 Probe-calibrated consensus: can a small probe de-bias the consensus rate
    estimate (T1 showed it's biased)? Isotonic-calibrate on probe, compare to oracle.
2.4 Cost-to-recover: rank discards by consensus; % bad recovered vs % re-examined.

Outputs results/t2_baselines.json.
"""

from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

cs.use_split("train")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "t2_baselines.json")
RNG = np.random.default_rng(0)
PROB = lambda p: p >= 50
DET_RULES = {
    "s2cloudless": ("LABEL_s2cloudless.dat", PROB),
    "cnn_rgbi": ("LABEL_cd_fcnn_rgbi.dat", PROB),
    "cnn_rgbi_swir": ("LABEL_cd_fcnn_rgbi_swir.dat", PROB),
    "sen2cor": ("LABEL_sen2cor.dat", lambda p: np.isin(p, [8, 9, 10])),
    "fmask": ("LABEL_fmask.dat", lambda p: p == 4),
    "kappamask": ("LABEL_kappamask_L1C.dat", lambda p: np.isin(p, [3, 4])),
}
TGT = "kappamask"


def cloudfrac(fn, rule, N):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def safe_auc(l, s):
    return float(roc_auc_score(l, s)) if len(np.unique(l)) == 2 else float("nan")


def main():
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    N = cs.N
    roi = meta["roi_id"].to_numpy()
    C = (df["cloud_frac"].to_numpy() < 0.10)
    ndsi = df["ndsi"].to_numpy(); bright = df["brightness"].to_numpy()
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, _ = cs.feature_columns(df)
    print("detector reads ...", flush=True)
    discard = {n: cloudfrac(fn, r, N) >= 0.5 for n, (fn, r) in DET_RULES.items()}
    pb = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                           df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    discard["ours_brightness"] = pb >= 0.5
    panel = [d for d in DET_RULES if d != TGT]
    keep_votes_all = np.mean([~discard[d] for d in panel], axis=0)  # higher => more "keep" => more likely bad

    out = {}
    D = discard[TGT]

    # ---- probe/eval split by ROI (no location leakage) ----
    tr, te = next(GroupShuffleSplit(1, test_size=0.7, random_state=0).split(np.arange(N), y, roi))
    disc_te = np.where(D & np.isin(np.arange(N), te))[0]
    lab_te = C[disc_te].astype(int)  # 1 = bad discard
    print(f"\n[2.1] signals on {len(disc_te)} eval discards ({lab_te.sum()} bad)")

    # 2.1 signals (label-free) on eval discards
    sigs = {
        "consensus_panel": keep_votes_all[disc_te],
        "single_best_alt(s2cloudless_keep)": (~discard["s2cloudless"]).astype(float)[disc_te],
        "NDSI": ndsi[disc_te],
        "brightness": bright[disc_te],
    }
    # supervised: train on probe's kappamask discards (features -> bad), eval on eval discards
    disc_tr = np.where(D & np.isin(np.arange(N), tr))[0]
    sup = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08)
    sup.fit(df[bcols].to_numpy()[disc_tr], C[disc_tr].astype(int))
    sigs["probe_supervised(features)"] = sup.predict_proba(df[bcols].to_numpy()[disc_te])[:, 1]

    out["audit_vs_baselines"] = {}
    for name, s in sigs.items():
        out["audit_vs_baselines"][name] = {"AUC": safe_auc(lab_te, s),
                                           "AP": float(average_precision_score(lab_te, s)) if lab_te.sum() else float("nan")}
        print(f"  {name:34s} AUC={out['audit_vs_baselines'][name]['AUC']:.3f} AP={out['audit_vs_baselines'][name]['AP']:.3f}")
    out["base_rate_bad_among_discards"] = float(lab_te.mean())

    # ---- 2.2 panel-size ablation ----
    print("\n[2.2] panel-size ablation (consensus AUC vs #detectors)")
    bad_all = (D & C).astype(int)[D]  # over ALL kappamask discards
    out["panel_size"] = {}
    for k in range(1, 6):
        aucs = []
        for combo in itertools.combinations(panel, k):
            kv = np.mean([~discard[d] for d in combo], axis=0)
            aucs.append(safe_auc(bad_all, kv[D]))
        out["panel_size"][k] = {"mean_AUC": float(np.nanmean(aucs)), "max_AUC": float(np.nanmax(aucs)),
                                "n_combos": len(aucs)}
        print(f"  k={k}: mean AUC={out['panel_size'][k]['mean_AUC']:.3f} (best {out['panel_size'][k]['max_AUC']:.3f}, {len(aucs)} combos)")

    # ---- 2.3 probe-calibrated consensus rate estimate ----
    print("\n[2.3] probe-calibrated consensus rate estimate (de-bias)")
    oracle_theta_te = float(C[disc_te].mean())  # true bad-rate among eval discards
    raw_consensus_rate = float((keep_votes_all[disc_te] > 0.5).mean())  # T1-style biased estimate
    cal = {}
    for nprobe in [50, 100, 200, 400]:
        errs = []
        for _ in range(50):
            pidx = RNG.choice(disc_tr, min(nprobe, len(disc_tr)), replace=False)
            iso = IsotonicRegression(out_of_bounds="clip").fit(keep_votes_all[pidx], C[pidx].astype(int))
            est = float(iso.predict(keep_votes_all[disc_te]).mean())
            errs.append(abs(est - oracle_theta_te))
        cal[str(nprobe)] = {"median_abs_err": float(np.median(errs))}
        print(f"  probe n={nprobe}: |calibrated_rate - oracle|={cal[str(nprobe)]['median_abs_err']:.3f}")
    out["calibration"] = {"oracle_bad_rate": oracle_theta_te, "raw_consensus_rate": raw_consensus_rate,
                          "raw_abs_err": abs(raw_consensus_rate - oracle_theta_te), "probe_calibrated": cal}
    print(f"  (raw biased consensus rate={raw_consensus_rate:.3f} vs oracle={oracle_theta_te:.3f})")

    # ---- 2.4 cost-to-recover ----
    print("\n[2.4] cost-to-recover (rank all kappamask discards by consensus)")
    score = keep_votes_all[D]; bad = (D & C).astype(int)[D]
    order = np.argsort(-score)
    cum_bad = np.cumsum(bad[order]) / max(bad.sum(), 1)
    frac_examined = np.arange(1, len(order) + 1) / len(order)
    cost = {}
    for r in [0.5, 0.8, 0.9, 0.95]:
        j = np.searchsorted(cum_bad, r)
        cost[str(r)] = float(frac_examined[min(j, len(frac_examined) - 1)])
    out["cost_to_recover"] = {"frac_discards_examined_to_recover": cost, "n_discards": int(D.sum()), "n_bad": int(bad.sum())}
    print("  to recover {50,80,90,95}% of bad discards, examine:", {k: f"{v:.2f}" for k, v in cost.items()})

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
