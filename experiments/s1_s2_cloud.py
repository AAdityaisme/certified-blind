"""Track B — satellite triage gatekeeper (claims S1, S2).

S1 (parity): a brightness-only triage classifier matches a spectral (SWIR-aware)
one on cloud-detection AUC. Clouds ARE bright, so albedo alone detects most.

S2 (the shortcut / irreversible harm): on CLEAR but BRIGHT patches (snow, bare
desert), the brightness model false-discards (flags as cloud) what the spectral
model correctly keeps. In orbit this permanently deletes valuable clear scenes —
the documented cloud-mask failure (Coluzzi 2018), here as a shortcut.

Outputs results/s1_s2_cloud.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s1_s2_cloud.json")
META = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "test", "metadata.csv")
DISCARD_THR = 0.5   # discard patch if cloud fraction >= 0.5
CLEAR_THR = 0.10    # "clear" patch if cloud fraction < 0.10
SNOW, BARE = 70, 60  # ESA WorldCover: snow/ice, bare/sparse vegetation
N_FOLDS = 5


def model(kind):
    if kind == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08)


def main():
    t0 = time.time()
    df = cs.build_features()
    bright_cols, spectral_cols = cs.feature_columns(df)
    y = (df["cloud_frac"].to_numpy() >= DISCARD_THR).astype(int)
    roi = pd.read_csv(META)["roi_id"].to_numpy()  # group by location: no ROI in train+test
    cv = GroupKFold(N_FOLDS)
    print(f"patches={len(df)}  discard(base)={y.mean():.3f}  ROIs={len(set(roi))}  "
          f"bright_feats={len(bright_cols)} spectral_feats={len(spectral_cols)} (GroupKFold by roi_id)")

    feset = {"brightness": bright_cols, "spectral": spectral_cols}
    heads = ["logreg", "hgb"]
    results = {"S1_auc": {}, "S2": {}}
    oof_proba = {}

    # S1: out-of-fold AUC for each (feature set, head)
    for fs, cols in feset.items():
        X = df[cols].to_numpy()
        for h in heads:
            name = f"{fs}_{h}"
            proba = cross_val_predict(model(h), X, y, cv=cv, groups=roi,
                                      method="predict_proba")[:, 1]
            oof_proba[name] = proba
            results["S1_auc"][name] = float(roc_auc_score(y, proba))
            print(f"  S1 {name:18s} AUC={results['S1_auc'][name]:.4f}")

    # S2: false-discard rate on CLEAR patches, overall / bright / snow+bare
    clear = df["cloud_frac"].to_numpy() < CLEAR_THR
    bright_q = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    lc = df["land_cover"].to_numpy()
    bright_surface = np.isin(lc, [SNOW, BARE])
    subsets = {
        "clear_all": clear,
        "clear_bright_top25pct": clear & bright_q,
        "clear_snow_or_bare": clear & bright_surface,
    }
    print(f"\n  clear patches={clear.sum()}  clear&bright={int((clear&bright_q).sum())}  "
          f"clear&snow/bare={int((clear&bright_surface).sum())}")
    for name in ["brightness_logreg", "brightness_hgb", "spectral_logreg", "spectral_hgb"]:
        pred_discard = oof_proba[name] >= 0.5
        results["S2"][name] = {}
        for sub, mask in subsets.items():
            n = int(mask.sum())
            fd = float(pred_discard[mask].mean()) if n else float("nan")
            results["S2"][name][sub] = {"false_discard_rate": fd, "n": n}
        print(f"  S2 {name:18s} false-discard: "
              f"all={results['S2'][name]['clear_all']['false_discard_rate']:.3f} "
              f"bright={results['S2'][name]['clear_bright_top25pct']['false_discard_rate']:.3f} "
              f"snow/bare={results['S2'][name]['clear_snow_or_bare']['false_discard_rate']:.3f}")

    meta = {"n_patches": int(len(df)), "discard_base_rate": float(y.mean()),
            "discard_thr": DISCARD_THR, "clear_thr": CLEAR_THR, "n_folds": N_FOLDS,
            "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({**results, "meta": meta}, f, indent=2)
    print(f"\nsaved -> {RESULTS}  ({meta['runtime_sec']}s)")
    print("\nKEY: S1 parity (both detect clouds well) + S2 brightness false-discards "
          "bright-clear scenes (snow/desert) the spectral model keeps = the shortcut.")


if __name__ == "__main__":
    main()
