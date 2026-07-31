"""S9 — survival-condition scale-up: re-run the key Track-B results on the
CloudSEN12 TRAIN split (8490 patches, ~310 snow / ~960 bare) with bootstrap CIs,
so the headline numbers no longer rest on n=7 snow.

Reproduces at scale: false-discard rate (brightness vs spectral) on clear-bright,
clear-SNOW (LC=70), clear-BARE (LC=60); real-detector over-discard on those
subsets; and the cross-detector consensus audit AUC for recovering bad-discards.
All with bootstrap 95% CIs. Outputs results/s9_scaleup_train.json.
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

cs.use_split("train")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s9_scaleup_train.json")
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


def cloudfrac(fn, rule):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(cs.N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(cs.N)])


def boot_ci(vals, n=2000):
    vals = np.asarray(vals, float)
    if len(vals) == 0:
        return (float("nan"),) * 3
    bs = [vals[RNG.integers(0, len(vals), len(vals))].mean() for _ in range(n)]
    return float(vals.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def auc_ci(lab, score, n=2000):
    lab = np.asarray(lab); score = np.asarray(score)
    base = roc_auc_score(lab, score) if len(np.unique(lab)) == 2 else float("nan")
    bs = []
    for _ in range(n):
        idx = RNG.integers(0, len(lab), len(lab))
        if len(np.unique(lab[idx])) == 2:
            bs.append(roc_auc_score(lab[idx], score[idx]))
    return (base, float(np.percentile(bs, 2.5)) if bs else float("nan"),
            float(np.percentile(bs, 97.5)) if bs else float("nan"))


def main():
    print(f"TRAIN split: N={cs.N}")
    df = cs.build_features()  # builds features_train.parquet (first run is slow)
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi = meta["roi_id"].to_numpy()
    lc = df["land_cover"].to_numpy()
    cf = df["cloud_frac"].to_numpy()
    y = (cf >= 0.5).astype(int)
    clear = cf < 0.10
    brightq = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    subsets = {"clear_all": clear, "clear_bright": clear & brightq,
               "clear_snow": clear & (lc == 70), "clear_bare": clear & (lc == 60)}
    print({k: int(v.sum()) for k, v in subsets.items()})

    bcols, scols = cs.feature_columns(df)
    cvp = lambda cols: cross_val_predict(
        HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
        df[cols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    pb, ps = cvp(bcols), cvp(scols)

    out = {"n": int(cs.N), "subset_sizes": {k: int(v.sum()) for k, v in subsets.items()},
           "S1_auc": {"brightness": float(roc_auc_score(y, pb)), "spectral": float(roc_auc_score(y, ps))},
           "false_discard": {}, "real_detectors": {}, "audit_auc": {}}

    print("\n=== S2 false-discard (our models) with 95% CI ===")
    for nm, p in [("brightness", pb), ("spectral", ps)]:
        disc = (p >= 0.5).astype(float)
        out["false_discard"][nm] = {}
        for sub, mask in subsets.items():
            mu, lo, hi = boot_ci(disc[mask])
            out["false_discard"][nm][sub] = {"rate": mu, "ci": [lo, hi], "n": int(mask.sum())}
        print(f"  {nm:10s} " + "  ".join(
            f"{s}={out['false_discard'][nm][s]['rate']:.2f}[{out['false_discard'][nm][s]['ci'][0]:.2f},"
            f"{out['false_discard'][nm][s]['ci'][1]:.2f}]" for s in subsets))

    # real detectors + consensus audit
    discard = {n: cloudfrac(fn, r) >= 0.5 for n, (fn, r) in DET_RULES.items()}
    discard["ours_brightness"] = pb >= 0.5
    print("\n=== real-detector over-discard (clear_snow / clear_bright) + audit AUC w/ CI ===")
    panel = list(DET_RULES)
    for tgt in ["sen2cor", "fmask", "kappamask", "ours_brightness"]:
        disc = discard[tgt]
        out["real_detectors"][tgt] = {
            s: {"rate": boot_ci(disc[mask].astype(float))[0], "n": int(mask.sum())}
            for s, mask in subsets.items()}
        bad = disc & clear
        lab = bad.astype(int)[disc]
        others = [d for d in panel if d != tgt]
        keep_votes = np.mean([~discard[d] for d in others], axis=0)
        a, lo, hi = auc_ci(lab, keep_votes[disc])
        out["audit_auc"][tgt] = {"consensus_auc": a, "ci": [lo, hi], "n_bad": int(bad.sum())}
        print(f"  {tgt:16s} snow_FD={out['real_detectors'][tgt]['clear_snow']['rate']:.2f} "
              f"bright_FD={out['real_detectors'][tgt]['clear_bright']['rate']:.2f}  "
              f"consensus_AUC={a:.2f}[{lo:.2f},{hi:.2f}] (n_bad={int(bad.sum())})")

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
