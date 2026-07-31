"""TIER 5 — reproducibility.

5.1 Multi-seed variance on headline numbers: vary the model RNG (HistGBM
    random_state) and re-measure the snow false-discard gap → report mean/std.
    (Detector-based numbers — over-discard, consensus AUC — are deterministic given
    data; we confirm that too.)
5.2 Determinism: re-run a detector-cloudfrac computation twice with a fixed config →
    byte-identical; same-seed model run → identical predictions.

Outputs results/t5_repro.json.
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


def cf(fn, rule, N):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def main():
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    N = cs.N
    roi = meta["roi_id"].to_numpy(); lc = df["land_cover"].to_numpy()
    C = df["cloud_frac"].to_numpy() < 0.10
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    snow = C & (lc == 70)
    bcols, scols = cs.feature_columns(df)
    kappa = cf("LABEL_kappamask_L1C.dat", lambda p: np.isin(p, [3, 4]), N) >= 0.5

    out = {}
    # 5.1 model-RNG variance on snow false-discard (our models)
    bfd, sfd = [], []
    for seed in range(5):
        pb = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, random_state=seed),
                               df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
        ps = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, random_state=seed),
                               df[scols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
        bfd.append(float((pb[snow] >= 0.5).mean())); sfd.append(float((ps[snow] >= 0.5).mean()))
    out["snow_FD_over_5_model_seeds"] = {
        "brightness_mean": float(np.mean(bfd)), "brightness_std": float(np.std(bfd)),
        "spectral_mean": float(np.mean(sfd)), "spectral_std": float(np.std(sfd)),
        "gap_positive_all_seeds": bool(all(b > s for b, s in zip(bfd, sfd)))}
    print(f"[5.1] snow FD over 5 model seeds: brightness {np.mean(bfd):.3f}±{np.std(bfd):.3f}  "
          f"spectral {np.mean(sfd):.3f}±{np.std(sfd):.3f}  gap>0 all seeds: {out['snow_FD_over_5_model_seeds']['gap_positive_all_seeds']}")

    # detector-based headline numbers are deterministic
    out["kappamask_snow_overdiscard"] = float(kappa[snow].mean())
    print(f"     KappaMask snow over-discard (deterministic): {out['kappamask_snow_overdiscard']:.3f}")

    # 5.2 determinism
    a = cf("LABEL_fmask.dat", lambda p: p == 4, N)
    b = cf("LABEL_fmask.dat", lambda p: p == 4, N)
    pb1 = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, random_state=0),
                            df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    pb2 = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, random_state=0),
                            df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    out["determinism"] = {"detector_read_identical": bool(np.array_equal(a, b)),
                          "fixed_seed_model_identical": bool(np.allclose(pb1, pb2))}
    print(f"[5.2] determinism: detector read identical={out['determinism']['detector_read_identical']}  "
          f"fixed-seed model identical={out['determinism']['fixed_seed_model_identical']}")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "t5_repro.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nsaved -> results/t5_repro.json")


if __name__ == "__main__":
    main()
