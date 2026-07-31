"""S3 — ground-side audit harness for irreversible triage (the 'so what').

An onboard brightness-only triage model permanently discards frames; you cannot
see what it threw away. A ground-side auditor WITH full spectral data can flag
the onboard model's *probable bad discards* before they are trusted: flag a
discard when the brightness model says discard but a spectral model says keep
(disagreement). We evaluate, among the brightness model's discards, how well this
flag recovers the TRUE bad discards (clear scenes wrongly discarded).

Precision = of flagged discards, fraction truly clear (cloud_frac < 0.10).
Recall    = of truly-clear discards, fraction flagged.
Outputs results/s3_audit_harness.json.
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

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s3_audit_harness.json")
META = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "test", "metadata.csv")
CLEAR_THR = 0.10


def main():
    df = cs.build_features()
    roi = pd.read_csv(META)["roi_id"].to_numpy()
    bcols, scols = cs.feature_columns(df)
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    cv = GroupKFold(5)

    def oof(cols):
        return cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                                 df[cols].to_numpy(), y, cv=cv, groups=roi,
                                 method="predict_proba")[:, 1]
    pb, ps = oof(bcols), oof(scols)
    cloud_frac = df["cloud_frac"].to_numpy()

    onboard_discard = pb >= 0.5            # what the brightness model throws away
    truly_clear = cloud_frac < CLEAR_THR   # ground truth: was it actually clear?
    bad_discard = onboard_discard & truly_clear     # the harms we want to catch
    flag = onboard_discard & (ps < 0.5)             # auditor: brightness-discards, spectral-keeps

    n_disc = int(onboard_discard.sum())
    n_bad = int(bad_discard.sum())
    n_flag = int(flag.sum())
    tp = int((flag & bad_discard).sum())
    precision = tp / n_flag if n_flag else float("nan")
    recall = tp / n_bad if n_bad else float("nan")

    # baseline: random flagging at the same rate
    base_rate_bad = n_bad / n_disc if n_disc else float("nan")

    out = {
        "n_onboard_discards": n_disc,
        "n_true_bad_discards": n_bad,
        "n_flagged": n_flag,
        "precision": precision, "recall": recall,
        "f1": (2 * precision * recall / (precision + recall)) if (precision and recall) else float("nan"),
        "bad_discard_base_rate_among_discards": base_rate_bad,
        "precision_lift_over_random": (precision / base_rate_bad) if base_rate_bad else float("nan"),
    }
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    print(f"onboard brightness discards: {n_disc} frames")
    print(f"  of which TRULY CLEAR (bad discards): {n_bad} ({base_rate_bad:.1%})")
    print(f"auditor flags (brightness-discard & spectral-keep): {n_flag}")
    print(f"  precision={precision:.3f}  recall={recall:.3f}  f1={out['f1']:.3f}")
    print(f"  precision lift over random flagging: {out['precision_lift_over_random']:.2f}x")
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
