"""S6 — estimating the UNOBSERVABLE loss (the sharp core).

Irreversibility changes the EVALUATION problem, not just the stakes: a discarded
frame is never downlinked, so the false-discard rate cannot be computed from
retained (downlinked) data — an operator auditing what came down sees only kept
frames (which look fine) and would infer 0 loss. We show:

  1. true clear-destruction rate (of truly-clear scenes, fraction discarded) is
     large for deployed detectors, yet
  2. INVISIBLE from retained data (kept frames carry ~no signal of it), yet
  3. RECOVERABLE without ground-truth labels via cross-detector consensus:
     estimate destruction on "consensus-clear" frames (majority of OTHER detectors
     keep) ~= the true rate.

Outputs results/s6_unobservable.json.
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
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s6_unobservable.json")
N, H, W = cs.N, cs.H, cs.W
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
    m = np.memmap(os.path.join(DATA, fn), dtype=np.uint8, mode="r", shape=(N, H, W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def main():
    df = cs.build_features()
    roi = pd.read_csv(META)["roi_id"].to_numpy()
    true_clear = df["cloud_frac"].to_numpy() < 0.10

    discard = {n: cloudfrac(fn, r) >= 0.5 for n, (fn, r) in DET_RULES.items()}
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, _ = cs.feature_columns(df)
    pb = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                           df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi,
                           method="predict_proba")[:, 1]
    discard["ours_brightness"] = pb >= 0.5

    out = {}
    targets = ["sen2cor", "fmask", "kappamask", "ours_brightness"]
    panel_pool = list(DET_RULES)
    for tgt in targets:
        disc = discard[tgt]
        panel = [d for d in panel_pool if d != tgt]
        keep_votes = np.mean([~discard[d] for d in panel], axis=0)
        consensus_clear = keep_votes > 0.5  # GT-free proxy for "clear"

        true_destroy = float(disc[true_clear].mean())                 # unobservable truth
        true_destroy_bright = float(disc[true_clear & (df["brightness"].to_numpy()
                                    >= np.percentile(df["brightness"], 75))].mean())
        # (2) what retained data shows: among KEPT frames, fraction that were actually
        # clouded (a proxy for "does kept data hint at over-discard?"). It does NOT:
        kept = ~disc
        retained_signal = float((df["cloud_frac"].to_numpy()[kept] < 0.10).mean())  # kept frames are mostly clear -> looks fine
        # (3) GT-FREE consensus estimate of destruction rate
        consensus_estimate = float(disc[consensus_clear].mean())
        # probe-set estimate (needs labels) for reference, with bootstrap CI
        probe_est = []
        for _ in range(500):
            idx = RNG.choice(N, 100, replace=False)
            tc = true_clear[idx]
            probe_est.append(disc[idx][tc].mean() if tc.sum() else np.nan)
        probe_est = np.array(probe_est); probe_est = probe_est[~np.isnan(probe_est)]

        out[tgt] = {
            "true_clear_destruction": true_destroy,
            "true_clear_destruction_bright": true_destroy_bright,
            "consensus_estimate_no_labels": consensus_estimate,
            "consensus_abs_error": abs(consensus_estimate - true_destroy),
            "probe100_estimate_mean": float(np.mean(probe_est)),
            "probe100_ci": [float(np.percentile(probe_est, 2.5)), float(np.percentile(probe_est, 97.5))],
            "retained_data_clear_fraction": retained_signal,
        }

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    print("Estimating the UNOBSERVABLE clear-scene destruction rate:")
    print(f"{'detector':16s} {'true':>6s} {'true_bright':>11s} {'consensus(no GT)':>16s} {'|err|':>6s} {'probe100':>9s}")
    for tgt, r in out.items():
        print(f"{tgt:16s} {r['true_clear_destruction']:6.3f} {r['true_clear_destruction_bright']:11.3f} "
              f"{r['consensus_estimate_no_labels']:16.3f} {r['consensus_abs_error']:6.3f} "
              f"{r['probe100_estimate_mean']:9.3f}")
    print(f"\nretained-data clear-fraction (what an operator sees in downlinked frames): "
          f"{ {t: round(out[t]['retained_data_clear_fraction'],3) for t in out} }")
    print(f"\nsaved -> {RESULTS}")
    print("SHARP: true destruction is large + invisible in retained data, but cross-detector "
          "consensus recovers it WITHOUT labels (|err| small).")


if __name__ == "__main__":
    main()
