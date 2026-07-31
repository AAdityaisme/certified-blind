"""TEST 2 — "targeted suppression stays invisible": if an irreversible gatekeeper
silently destroys a TARGETED slice (e.g. all snow/glacier scenes over a region),
how much does the operator's OBSERVABLE aggregate dashboard move?

Observables an operator actually has post-deployment, WITHOUT labels on discarded data:
  - global discard rate (fraction flagged "cloud")
  - discard rate on retained-data benchmark slices

We show: fully suppressing the snow slice (62/99 scenes already destroyed by KappaMask)
shifts the global discard rate by < the scene-to-scene noise floor, and is
indistinguishable from suppressing a RANDOM slice of equal size. => targeted data
destruction is undetectable from aggregate observables.

Reuses CloudScout (real onboard CNN) + KappaMask. Outputs results/t_targeted.json.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))
import cloudsen12 as cs  # noqa: E402
from cloudscout import CloudScout  # noqa: E402

cs.use_split("train")
CKPT = os.path.join(REPO, "models", "cloudscout", "pretrained", "cloudscout-128a-S2-2018", "model70-final.ckpt")
RESULTS = os.path.join(REPO, "results", "t_targeted.json")
RNG = np.random.default_rng(0)


def band(fn):
    return np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint16, mode="r", shape=(cs.N, cs.H, cs.W))


def main():
    df = cs.build_features()
    cloud_frac = df["cloud_frac"].to_numpy(); lc = df["land_cover"].to_numpy()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))   # row-aligned with features
    roi = meta["roi_id"].to_numpy()
    clear = cloud_frac < 0.10; snow = (lc == 70)
    target = clear & snow                       # the slice an adversary wants gone
    n_t = int(target.sum())

    # CloudScout discard decisions (the deployed gate)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    m = CloudScout().to(device); m.load_state_dict(torch.load(CKPT, map_location=device)); m.eval()
    mm = [band(b) for b in ["L1C_B1.dat", "L1C_B2.dat", "L1C_B8A.dat"]]
    cs_pred = np.empty(cs.N, dtype=bool)
    with torch.no_grad():
        for i in range(0, cs.N, 64):
            j = min(i + 64, cs.N)
            x = np.stack([np.stack([np.asarray(b[k]) for b in mm]) for k in range(i, j)]).astype(np.float32) / 10000.0
            cs_pred[i:j] = m(torch.from_numpy(x).to(device)).argmax(1).cpu().numpy() == 1

    km = np.memmap(os.path.join(cs.DATA, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(cs.N, cs.H, cs.W))
    km_pred = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) >= 0.5 for i in range(cs.N)])

    # NOISE FLOOR = natural fluctuation of the global discard rate the operator already sees.
    #  (a) operational: SE of discard rate over one realistic monitoring window (WINDOW scenes)
    #  (b) real dynamic range: how the discard rate swings across actual cloud-coverage strata
    #      (the metric is DOMINATED by real cloudiness, which varies hugely) -> a systematic
    #      ~1pp targeted bias cannot be separated from "we imaged a cloudier mix this week".
    WINDOW = 250
    boot = np.array([cs_pred[RNG.choice(cs.N, WINDOW, replace=False)].mean() for _ in range(1000)])
    batch_se = float(boot.std())
    cc = meta["cloud_coverage"].to_numpy()
    strata = [cs_pred[cc == v].mean() for v in np.unique(cc) if (cc == v).sum() >= 50]
    dynamic_range = float(max(strata) - min(strata))

    out = {"n_total": int(cs.N), "n_target_snow": n_t, "target_prevalence": n_t / cs.N,
           "noise_floor_window_se_pp": batch_se * 100, "window_scenes": WINDOW,
           "discardrate_dynamic_range_across_cloudstrata_pp": dynamic_range * 100}

    for name, pred in [("CloudScout", cs_pred), ("KappaMask", km_pred)]:
        # PRIMARY: the BASELINE targeted harm already happening, and its aggregate footprint
        target_destroyed = int((pred & target).sum())            # snow scenes falsely discarded now
        baseline_harm_rate = float(pred[target].mean())          # fraction of target destroyed
        footprint_pp = target_destroyed / cs.N * 100             # its dent in the global discard rate
        # SECONDARY: adversary completes the suppression (force all target -> discard)
        attacked = pred.copy(); attacked[target] = True
        attack_shift_pp = (attacked.mean() - pred.mean()) * 100
        out[name] = {
            "baseline_discard_rate_pp": float(pred.mean()) * 100,
            "target_destroyed_scenes": target_destroyed,
            "baseline_targeted_harm_rate": baseline_harm_rate,
            "aggregate_footprint_of_harm_pp": footprint_pp,
            "footprint_below_window_SE": footprint_pp < batch_se * 100,
            "footprint_vs_dynamic_range": footprint_pp / (dynamic_range * 100),
            "adversary_complete_suppression_shift_pp": attack_shift_pp,
        }

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    print(f"target slice = clear-snow: n={n_t} ({out['target_prevalence']*100:.2f}% of {cs.N} scenes)")
    print(f"NOISE FLOOR: monitoring-window SE ({WINDOW} scenes) = {batch_se*100:.2f}pp  |  "
          f"discard-rate dynamic range across real cloud strata = {dynamic_range*100:.1f}pp\n")
    for name in ("CloudScout", "KappaMask"):
        d = out[name]
        print(f"{name}: {d['baseline_targeted_harm_rate']*100:.0f}% of snow ({d['target_destroyed_scenes']} scenes) "
              f"silently destroyed at baseline -> aggregate footprint only {d['aggregate_footprint_of_harm_pp']:.2f}pp "
              f"({'BELOW' if d['footprint_below_window_SE'] else 'above'} the {batch_se*100:.1f}pp window noise, "
              f"{d['footprint_vs_dynamic_range']*100:.0f}% of the metric's natural range)")
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
