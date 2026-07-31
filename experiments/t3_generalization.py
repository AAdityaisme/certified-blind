"""TIER 3 — generalization / construct validity (CloudSEN12 train).

3.1 Beyond snow: brightness-vs-spectral over-discard + best audit signal per LAND
    COVER (water, urban, veg, bare, snow). Is it only snow? Which signal catches what?
3.2 Illumination: KappaMask clear-over-discard vs sun-elevation bin.
3.3 GT-definition robustness: redefine "clear" via ALGORITHM consensus (not manual_hq)
    and re-check the brightness over-discard — robust to ground-truth choice?
3.4 Snow-is-really-snow: NDSI distribution of LC=70 vs the rest (validates the label).

Outputs results/t3_generalization.json.
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
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "t3_generalization.json")
LC = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare",
      70: "snow", 80: "water", 90: "wetland", 100: "moss"}
PROB = lambda p: p >= 50
DET = {"s2cloudless": ("LABEL_s2cloudless.dat", PROB), "sen2cor": ("LABEL_sen2cor.dat", lambda p: np.isin(p, [8, 9, 10])),
       "fmask": ("LABEL_fmask.dat", lambda p: p == 4), "kappamask": ("LABEL_kappamask_L1C.dat", lambda p: np.isin(p, [3, 4])),
       "cnn_rgbi": ("LABEL_cd_fcnn_rgbi.dat", PROB), "cnn_rgbi_swir": ("LABEL_cd_fcnn_rgbi_swir.dat", PROB)}


def cloudfrac(fn, rule, N):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def auc(l, s):
    return float(roc_auc_score(l, s)) if len(np.unique(l)) == 2 else float("nan")


def main():
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    N = cs.N
    roi = meta["roi_id"].to_numpy(); lcv = df["land_cover"].to_numpy()
    sun = meta["s2_view_sun_elevation"].to_numpy()
    C = df["cloud_frac"].to_numpy() < 0.10
    ndsi = df["ndsi"].to_numpy(); bright = df["brightness"].to_numpy()
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, scols = cs.feature_columns(df)
    HGB = lambda c: cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                                      df[c].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    pb, ps = HGB(bcols), HGB(scols)
    discard = {n: cloudfrac(fn, r, N) >= 0.5 for n, (fn, r) in DET.items()}
    discard["ours_brightness"] = pb >= 0.5
    panel = [d for d in DET if d != "kappamask"]
    cons = np.mean([~discard[d] for d in panel], axis=0)

    out = {}
    # 3.1 beyond snow
    print("[3.1] per-land-cover (clear patches): brightnessFD/spectralFD/kappaFD + audit signal AUC")
    out["by_landcover"] = {}
    for code, nm in LC.items():
        m = C & (lcv == code)
        if m.sum() < 20:
            continue
        bad = discard["kappamask"] & m
        o = {"n_clear": int(m.sum()), "brightnessFD": float((pb[m] >= 0.5).mean()),
             "spectralFD": float((ps[m] >= 0.5).mean()), "kappaFD": float(discard["kappamask"][m].mean())}
        # audit signal AUC for kappamask bad discards in this land cover
        disc_m = discard["kappamask"] & m
        if disc_m.sum() >= 8 and bad.sum() >= 3 and (~bad[disc_m]).any():
            lab = bad.astype(int)[disc_m]
            o["audit_NDSI_AUC"] = auc(lab, ndsi[disc_m]); o["audit_consensus_AUC"] = auc(lab, cons[disc_m])
        out["by_landcover"][nm] = o
        print(f"  {nm:8s} n={o['n_clear']:4d} brightFD={o['brightnessFD']:.2f} specFD={o['spectralFD']:.2f} "
              f"kappaFD={o['kappaFD']:.2f} NDSI_AUC={o.get('audit_NDSI_AUC',float('nan')):.2f} cons_AUC={o.get('audit_consensus_AUC',float('nan')):.2f}")

    # 3.2 illumination
    print("\n[3.2] KappaMask clear-over-discard vs sun-elevation")
    out["by_sun_elevation"] = {}
    bins = [(0, 25), (25, 40), (40, 55), (55, 90)]
    for lo, hi in bins:
        m = C & (sun >= lo) & (sun < hi)
        if m.sum() < 20:
            continue
        out["by_sun_elevation"][f"{lo}-{hi}"] = {"n": int(m.sum()), "kappaFD": float(discard["kappamask"][m].mean()),
                                                 "brightnessFD": float((pb[m] >= 0.5).mean())}
        print(f"  sun {lo}-{hi}deg n={int(m.sum()):4d} kappaFD={out['by_sun_elevation'][f'{lo}-{hi}']['kappaFD']:.2f} "
              f"brightFD={out['by_sun_elevation'][f'{lo}-{hi}']['brightnessFD']:.2f}")

    # 3.3 GT-definition robustness: clear via algorithm consensus (>=2 of 3 keep), not manual_hq
    print("\n[3.3] GT-definition robustness (algorithm-consensus clear vs manual_hq)")
    alg_clear = (np.array([(~discard[d]).astype(int) for d in ["s2cloudless", "fmask", "sen2cor"]]).sum(0) >= 3)
    snow = (lcv == 70)
    out["gt_robustness"] = {
        "manual_hq_clear_snow_brightnessFD": float((pb[C & snow] >= 0.5).mean()) if (C & snow).sum() else float("nan"),
        "manual_hq_clear_snow_spectralFD": float((ps[C & snow] >= 0.5).mean()) if (C & snow).sum() else float("nan"),
        "alg_clear_snow_brightnessFD": float((pb[alg_clear & snow] >= 0.5).mean()) if (alg_clear & snow).sum() else float("nan"),
        "alg_clear_snow_spectralFD": float((ps[alg_clear & snow] >= 0.5).mean()) if (alg_clear & snow).sum() else float("nan"),
        "n_manual": int((C & snow).sum()), "n_alg": int((alg_clear & snow).sum())}
    print(f"  manual_hq: brightFD={out['gt_robustness']['manual_hq_clear_snow_brightnessFD']:.2f} "
          f"specFD={out['gt_robustness']['manual_hq_clear_snow_spectralFD']:.2f} (n={out['gt_robustness']['n_manual']})")
    print(f"  alg-consensus: brightFD={out['gt_robustness']['alg_clear_snow_brightnessFD']:.2f} "
          f"specFD={out['gt_robustness']['alg_clear_snow_spectralFD']:.2f} (n={out['gt_robustness']['n_alg']})")

    # 3.4 snow-is-really-snow
    print("\n[3.4] snow-is-really-snow: NDSI distribution LC=70 vs rest")
    out["snow_ndsi"] = {"snow_ndsi_pct": np.percentile(ndsi[lcv == 70], [10, 50, 90]).round(3).tolist(),
                        "nonsnow_ndsi_pct": np.percentile(ndsi[lcv != 70], [10, 50, 90]).round(3).tolist()}
    print(f"  LC=70 NDSI p10/50/90: {out['snow_ndsi']['snow_ndsi_pct']}")
    print(f"  non-snow NDSI p10/50/90: {out['snow_ndsi']['nonsnow_ndsi_pct']}")

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
