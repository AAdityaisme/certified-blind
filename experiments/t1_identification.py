"""TIER 1 — identification rigor (the contribution-elevating stats).

1.1 PARTIAL IDENTIFICATION (Manski bounds). Estimand theta = P(discard | clear).
    From retained data you observe only q=P(D=1) (discard rate, from telemetry) and
    a=P(C=1|D=0) (clear-rate among KEPT, by labelling kept frames). The clear-rate
    among DISCARDED frames b=P(C=1|D=1) is unobserved in [0,1], giving
        theta in [0, q/(a(1-q)+q)].
    Lower bound is 0 => retained data alone cannot establish ANY false discards.
    We compute the bound from observables, verify the ORACLE theta lies inside, and
    show the consensus proxy tightens b (validated against ground truth).

1.3 WHEN THE AUDIT FAILS. Of a detector's true bad-discards (D=1 & C=1), the
    fraction ALL other detectors also discard is invisible to consensus — the
    irreducible blind spot / recall ceiling.

1.4 PROBE SAMPLE-COMPLEXITY. CI width of the probe estimate of theta vs probe size.

Train split, 8490 patches. Outputs results/t1_identification.json.
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

cs.use_split("train")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "t1_identification.json")
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


def cloudfrac(fn, rule, N):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def main():
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    N = cs.N
    roi = meta["roi_id"].to_numpy()
    C = (df["cloud_frac"].to_numpy() < 0.10)  # truly clear (ground truth)
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    bcols, _ = cs.feature_columns(df)
    pb = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                           df[bcols].to_numpy(), y, cv=GroupKFold(5), groups=roi,
                           method="predict_proba")[:, 1]
    discard = {n: cloudfrac(fn, r, N) >= 0.5 for n, (fn, r) in DET_RULES.items()}
    discard["ours_brightness"] = pb >= 0.5

    out = {}
    targets = ["sen2cor", "fmask", "kappamask", "ours_brightness"]
    for tgt in targets:
        D = discard[tgt]
        # observables (deployment-visible)
        q = float(D.mean())                       # discard rate (telemetry)
        kept = ~D
        a = float(C[kept].mean())                 # clear-rate among kept (label kept frames)
        U = q / (a * (1 - q) + q)                 # Manski upper bound; lower bound = 0
        theta_oracle = float(D[C].mean())         # P(D=1|C=1), computable only with full GT
        # consensus proxy tightens b = P(C=1|D=1)
        b_true = float(C[D].mean())               # true clear-rate among discarded (oracle)
        panel = [d for d in DET_RULES if d != tgt]
        cons_clear = np.mean([~discard[d] for d in panel], axis=0) > 0.5  # majority keep => "clear" proxy
        b_hat = float(cons_clear[D].mean())       # consensus-estimated clear-rate among discarded (NO GT)
        theta_cons = b_hat * q / (a * (1 - q) + b_hat * q)  # plug b_hat into theta

        # 1.3 blind spot: bad discards no other detector keeps (consensus can't flag)
        bad = D & C
        keep_votes = np.mean([~discard[d] for d in panel], axis=0)
        invisible = bad & (keep_votes == 0.0)
        blind_spot = float(invisible.sum() / bad.sum()) if bad.sum() else float("nan")
        recall_ceiling = 1 - blind_spot

        out[tgt] = {
            "observables": {"q_discard_rate": q, "a_clear_among_kept": a},
            "manski_bound_theta": [0.0, U],
            "theta_oracle": theta_oracle,
            "oracle_in_bound": bool(0 <= theta_oracle <= U + 1e-9),
            "b_true_clear_among_discarded": b_true,
            "b_hat_consensus_no_GT": b_hat,
            "theta_consensus_estimate": theta_cons,
            "blind_spot_frac": blind_spot, "consensus_recall_ceiling": recall_ceiling,
            "n_bad": int(bad.sum()),
        }
        print(f"{tgt:16s} q={q:.2f} a={a:.2f} | theta in [0,{U:.2f}]  oracle={theta_oracle:.2f}({'in' if out[tgt]['oracle_in_bound'] else 'OUT'})  "
              f"| b_true={b_true:.2f} b_hat={b_hat:.2f} theta_cons={theta_cons:.2f} | blindspot={blind_spot:.2f}")

    # 1.4 probe sample complexity (using KappaMask's true theta as the target)
    print("\n[1.4] probe sample-complexity (CI width of theta estimate vs probe size)")
    D = discard["kappamask"]
    probe = {}
    for n in [50, 100, 200, 300, 500, 1000]:
        widths, excl0 = [], 0
        for _ in range(300):
            idx = RNG.choice(N, n, replace=False)
            cc = C[idx]; dd = D[idx]
            nc = cc.sum()
            if nc == 0:
                continue
            k = int((dd & cc).sum()); lo, hi = wilson(k, int(nc))
            widths.append(hi - lo); excl0 += (lo > 0)
        probe[str(n)] = {"median_CI_width": float(np.median(widths)) if widths else float("nan"),
                         "frac_runs_excluding_0": excl0 / 300}
        print(f"  n={n:4d}: median CI width={probe[str(n)]['median_CI_width']:.3f}  "
              f"frac runs proving theta>0: {probe[str(n)]['frac_runs_excluding_0']:.2f}")
    out["probe_sample_complexity"] = probe

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {RESULTS}")
    print("KEY: retained-data bound includes 0 (unidentified harm); consensus tightens b without GT; "
          "probe needs N frames to prove theta>0; blind-spot = audit's recall ceiling.")


if __name__ == "__main__":
    main()
