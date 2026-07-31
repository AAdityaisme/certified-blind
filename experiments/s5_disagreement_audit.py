"""S5 — can we AUDIT a deployed detector's irreversible bad-discards without
ground truth? Two cheap signals, validated against manual_hq ground truth.

For each "onboard" detector D that over-discards (Sen2Cor, Fmask, KappaMask, and
our brightness model), among the frames D discards, the BAD ones are those that
are truly clear (manual_hq cloud<0.10). We test whether two ground-truth-free
signals separate bad from good discards:
  (a) cross-detector consensus: fraction of OTHER detectors that KEEP the frame.
  (b) cheap scene features: brightness / NDSI (snow index) of the frame.

If either ranks bad-vs-good discards with high AUC, you can flag probable bad
discards ground-side before trusting the onboard model — a deployable audit for
irreversible triage. Outputs results/s5_disagreement_audit.json.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

DATA = cs.DATA
META = os.path.join(DATA, "metadata.csv")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s5_disagreement_audit.json")
N, H, W = cs.N, cs.H, cs.W

PROB = lambda p: p >= 50
DET_RULES = {
    "s2cloudless": ("LABEL_s2cloudless.dat", PROB),
    "cnn_rgbi": ("LABEL_cd_fcnn_rgbi.dat", PROB),
    "cnn_rgbi_swir": ("LABEL_cd_fcnn_rgbi_swir.dat", PROB),
    "sen2cor": ("LABEL_sen2cor.dat", lambda p: np.isin(p, [8, 9, 10])),
    "fmask": ("LABEL_fmask.dat", lambda p: p == 4),
    "kappamask": ("LABEL_kappamask_L1C.dat", lambda p: np.isin(p, [3, 4])),
}


def cloudfrac(fn, rule):
    m = np.memmap(os.path.join(DATA, fn), dtype=np.uint8, mode="r", shape=(N, H, W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def auc_safe(yy, ss):
    return float(roc_auc_score(yy, ss)) if len(np.unique(yy)) == 2 else float("nan")


_RNG = np.random.default_rng(0)


def auc_ci(yy, ss, n=2000):
    """Bootstrap 95% CI for AUC (resampling rows; small-n honesty)."""
    yy = np.asarray(yy); ss = np.asarray(ss)
    aucs = []
    for _ in range(n):
        idx = _RNG.integers(0, len(yy), len(yy))
        if len(np.unique(yy[idx])) == 2:
            aucs.append(roc_auc_score(yy[idx], ss[idx]))
    if not aucs:
        return (float("nan"), float("nan"))
    return (float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5)))


def main():
    df = cs.build_features()
    roi = pd.read_csv(META)["roi_id"].to_numpy()
    truly_clear = df["cloud_frac"].to_numpy() < 0.10
    brightness = df["brightness"].to_numpy()
    ndsi = df["ndsi"].to_numpy()

    # per-detector discard decisions
    discard = {}
    for name, (fn, rule) in DET_RULES.items():
        discard[name] = cloudfrac(fn, rule) >= 0.5

    # our brightness model (oof) as an additional "onboard" target
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, _ = cs.feature_columns(df)
    pb = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                           df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi,
                           method="predict_proba")[:, 1]
    discard["ours_brightness"] = pb >= 0.5

    out = {}
    targets = ["sen2cor", "fmask", "kappamask", "ours_brightness"]
    others_pool = list(DET_RULES)  # the 6 real detectors form the consensus panel
    for tgt in targets:
        disc = discard[tgt]
        n_disc = int(disc.sum())
        bad = disc & truly_clear                  # discards a truly-clear frame
        good = disc & ~truly_clear
        if bad.sum() < 3 or good.sum() < 3:
            out[tgt] = {"n_discards": n_disc, "n_bad": int(bad.sum()), "note": "too few"}; continue
        # signal a: consensus_keep = fraction of OTHER real detectors that keep it
        panel = [d for d in others_pool if d != tgt]
        keep_votes = np.mean([~discard[d] for d in panel], axis=0)   # in [0,1], higher=more keep
        # signal b: cheap features
        lab = bad.astype(int)[disc]               # 1=bad discard, among discards only
        out[tgt] = {
            "n_discards": n_disc, "n_bad_discards": int(bad.sum()),
            "bad_rate_among_discards": float(bad.sum() / n_disc),
            "auc_consensus_keep": auc_safe(lab, keep_votes[disc]),
            "ci_consensus": auc_ci(lab, keep_votes[disc]),
            "auc_brightness": auc_safe(lab, brightness[disc]),
            "auc_ndsi": auc_safe(lab, ndsi[disc]),
            "ci_ndsi": auc_ci(lab, ndsi[disc]),
        }
        # operating point for the best signal (consensus): flag if majority of panel keeps
        flag = disc & (keep_votes > 0.5)
        tp = int((flag & bad).sum())
        out[tgt]["consensus_flag_recall"] = tp / int(bad.sum())
        out[tgt]["consensus_flag_precision"] = tp / int(flag.sum()) if flag.sum() else float("nan")

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    print("Auditing irreversible bad-discards (AUC = how well a ground-truth-FREE signal "
          "ranks bad vs good discards):")
    print(f"{'target detector':16s} {'#disc':>6s} {'#bad':>5s} {'consensus':>10s} {'bright':>7s} {'ndsi':>6s} "
          f"{'flag_recall':>11s} {'flag_prec':>9s}")
    for tgt, r in out.items():
        if "auc_consensus_keep" not in r:
            print(f"{tgt:16s} {r.get('n_discards','?'):>6} (too few bad)"); continue
        cc, cn = r["ci_consensus"], r["ci_ndsi"]
        print(f"{tgt:16s} #disc={r['n_discards']:>3} #bad={r['n_bad_discards']:>3}  "
              f"consensus={r['auc_consensus_keep']:.2f} [{cc[0]:.2f},{cc[1]:.2f}]  "
              f"ndsi={r['auc_ndsi']:.2f} [{cn[0]:.2f},{cn[1]:.2f}]  recall={r['consensus_flag_recall']:.2f}")
    print(f"\nsaved -> {RESULTS}")
    print("STRONG ANGLE if consensus/feature AUC is high across detectors: irreversible "
          "bad-discards are auditable ground-side, cheaply, without seeing what was thrown away.")


if __name__ == "__main__":
    main()
