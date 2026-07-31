"""Audit Track B: spatial leakage via roi_id (multiple temporal patches per
location), and re-run S1/S2 under GroupKFold(roi_id) to see if the result holds.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

META = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "test", "metadata.csv")


def fd_rates(pred_discard, df):
    clear = df["cloud_frac"].to_numpy() < 0.10
    brightq = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    snowbare = np.isin(df["land_cover"].to_numpy(), [70, 60])
    return {
        "clear_all": float(pred_discard[clear].mean()),
        "clear_bright": float(pred_discard[clear & brightq].mean()),
        "clear_snow_bare": float(pred_discard[clear & snowbare].mean()),
    }


def main():
    df = cs.build_features()
    meta = pd.read_csv(META)
    roi = meta["roi_id"].to_numpy()
    assert len(roi) == len(df)
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, scols = cs.feature_columns(df)

    # leakage stats
    vc = pd.Series(roi).value_counts()
    print(f"patches={len(df)}  unique ROIs={len(vc)}  max patches/ROI={vc.max()}  "
          f"mean={vc.mean():.2f}")
    print(f"patches sharing ROI with >=1 other: {(vc[vc>1].sum())}/{len(df)} "
          f"= {vc[vc>1].sum()/len(df):.3f}")

    # random 5-fold leakage: fraction of (test) patches whose ROI is in the train fold
    from sklearn.model_selection import KFold
    kf = KFold(5, shuffle=True, random_state=0)
    leaked = 0
    for tr, te in kf.split(df):
        train_rois = set(roi[tr])
        leaked += sum(roi[i] in train_rois for i in te)
    print(f"random 5-fold: test patches whose ROI appears in train = {leaked}/{len(df)} "
          f"= {leaked/len(df):.3f}  (high => spatial leakage)")

    # S1/S2 under random CV vs GroupKFold(roi)
    def run(cv, label):
        out = {}
        for nm, cols in [("brightness", bcols), ("spectral", scols)]:
            proba = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                                      df[cols].to_numpy(), y, cv=cv, method="predict_proba",
                                      groups=roi if isinstance(cv, GroupKFold) else None)[:, 1]
            auc = roc_auc_score(y, proba)
            fd = fd_rates(proba >= 0.5, df)
            out[nm] = (auc, fd)
            print(f"  [{label}] {nm:10s} AUC={auc:.3f}  FD clear={fd['clear_all']:.3f} "
                  f"bright={fd['clear_bright']:.3f} snow/bare={fd['clear_snow_bare']:.3f}")
        return out

    print("\nrandom 5-fold CV:")
    run(5, "rand")
    print("\nGroupKFold by roi_id (no location in both train & test):")
    run(GroupKFold(5), "group")


if __name__ == "__main__":
    main()
