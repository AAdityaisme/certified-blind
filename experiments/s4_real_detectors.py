"""S4 — strawman-killer: do REAL cloud detectors also over-discard bright clear
scenes, or is our brightness-only model a self-inflicted strawman?

CloudSEN12 ships per-pixel outputs of operational + learned detectors. Crucially
it includes a controlled CNN band-ablation: cd_fcnn_rgbi (RGB only) vs
cd_fcnn_rgbi_swir (RGB+SWIR). We compute each detector's false-discard rate on
truly-clear (manual_hq cloud<0.10) BRIGHT patches and compare to our models.

If RGB-only detectors over-discard bright-clear and +SWIR ones don't, the
brightness shortcut is real in deployed architectures — not a strawman.

Outputs results/s4_real_detectors.json.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

DATA = cs.DATA
META = os.path.join(DATA, "metadata.csv")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s4_real_detectors.json")
N, H, W = cs.N, cs.H, cs.W

# detector file -> (label, uses SWIR?, cloud-pixel rule)
# Encodings differ per detector (verified via uniques):
#  cd_fcnn_* and s2cloudless store 0-100 cloud PROBABILITY -> cloud = prob>=50
#  sen2cor = Sen2Cor SCL classes -> cloud = {8 med,9 high,10 cirrus}
#  fmask = {0 clear,1 water,2 shadow,3 snow,4 cloud} -> cloud = {4}
#  kappamask = {0 nodata,1 clear,2 shadow,3 semi-transparent,4 cloud,5 undef} -> cloud = {3,4}
PROB = lambda p: p >= 50
DETECTORS = {
    "LABEL_cd_fcnn_rgbi.dat": ("CNN (RGB only)", False, PROB),
    "LABEL_cd_fcnn_rgbi_swir.dat": ("CNN (RGB+SWIR)", True, PROB),
    "LABEL_s2cloudless.dat": ("s2cloudless (operational)", True, PROB),
    "LABEL_sen2cor.dat": ("Sen2Cor (ESA operational)", True, lambda p: np.isin(p, [8, 9, 10])),
    "LABEL_fmask.dat": ("Fmask", True, lambda p: p == 4),
    "LABEL_kappamask_L1C.dat": ("KappaMask", True, lambda p: np.isin(p, [3, 4])),
}


def detector_cloudfrac(fn: str, rule) -> np.ndarray:
    m = np.memmap(os.path.join(DATA, fn), dtype=np.uint8, mode="r", shape=(N, H, W))
    frac = np.empty(N)
    for i in range(N):
        frac[i] = np.mean(rule(np.asarray(m[i])))
    return frac


def main():
    df = cs.build_features()
    roi = pd.read_csv(META)["roi_id"].to_numpy()
    cf = df["cloud_frac"].to_numpy()           # ground-truth (manual_hq) cloud fraction
    clear = cf < 0.10
    brightq = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    lc = df["land_cover"].to_numpy()
    snowbare = np.isin(lc, [60, 70])

    # inspect encodings
    print("detector mask uniques (first patch):")
    for fn in DETECTORS:
        path = os.path.join(DATA, fn)
        if not os.path.exists(path):
            print(f"  {fn}: MISSING"); continue
        m = np.memmap(path, dtype=np.uint8, mode="r", shape=(N, H, W))
        print(f"  {fn:32s} uniques={np.unique(np.asarray(m[:3])).tolist()}")

    def fd(disc):
        return {"clear_all": float(disc[clear].mean()),
                "clear_bright": float(disc[clear & brightq].mean()),
                "clear_snow_bare": float(disc[clear & snowbare].mean())}

    rows = {}
    for fn, (label, swir, rule) in DETECTORS.items():
        if not os.path.exists(os.path.join(DATA, fn)):
            continue
        disc = detector_cloudfrac(fn, rule) >= 0.5
        rows[label] = {"uses_swir": swir, **fd(disc)}

    # our models (oof, GroupKFold) for reference
    y = (cf >= 0.5).astype(int)
    bcols, scols = cs.feature_columns(df)
    for nm, cols, swir in [("OURS brightness-only", bcols, False), ("OURS spectral", scols, True)]:
        proba = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                                  df[cols].to_numpy(), y, cv=GroupKFold(5), groups=roi,
                                  method="predict_proba")[:, 1]
        rows[nm] = {"uses_swir": swir, **fd(proba >= 0.5)}

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"\nFalse-discard rate on CLEAR scenes (n: all={int(clear.sum())} "
          f"bright={int((clear&brightq).sum())} snow/bare={int((clear&snowbare).sum())}):")
    print(f"{'detector':30s} {'SWIR':5s} {'all':>6s} {'bright':>7s} {'snow/bare':>9s}")
    for label, r in sorted(rows.items(), key=lambda kv: kv[1]["clear_bright"]):
        print(f"{label:30s} {'yes' if r['uses_swir'] else 'NO':5s} "
              f"{r['clear_all']:6.3f} {r['clear_bright']:7.3f} {r['clear_snow_bare']:9.3f}")
    print(f"\nsaved -> {RESULTS}")
    print("KEY: if RGB-only (no-SWIR) detectors have high bright-clear FD and SWIR ones low, "
          "the brightness shortcut is real in deployed detectors, not a strawman.")


if __name__ == "__main__":
    main()
