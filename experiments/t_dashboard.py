"""TEST 1 — "the dashboard lies": can an operator's OBSERVABLE metric distinguish a
safe irreversible gatekeeper from a catastrophic one?

CloudScout (real onboard CNN, ~2% clear-snow false-discard) vs KappaMask (~63%).
If their standard cloud-detection accuracy (the number an operator/paper reports)
is ~equal while their clear-snow false-discard differs ~30x, then the observable
dashboard CANNOT distinguish the safe detector from the one silently erasing snow
scenes. That is the teeth of the unidentifiability result.

Outputs results/t_dashboard.json.
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
RESULTS = os.path.join(REPO, "results", "t_dashboard.json")


def band(fn):
    return np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint16, mode="r", shape=(cs.N, cs.H, cs.W))


def metrics(discard, gt_discard, clear, snow, bright):
    acc = float((discard == gt_discard).mean())
    tp = (discard & gt_discard).sum(); fp = (discard & ~gt_discard).sum()
    fn = (~discard & gt_discard).sum(); tn = (~discard & ~gt_discard).sum()
    tpr = tp / (tp + fn) if (tp + fn) else 0; tnr = tn / (tn + fp) if (tn + fp) else 0
    return {"observable_accuracy": acc, "balanced_accuracy": float((tpr + tnr) / 2),
            "discard_rate": float(discard.mean()),
            "clear_snow_FDR": float(discard[clear & snow].mean()),
            "clear_bright_FDR": float(discard[clear & bright].mean())}


def main():
    df = cs.build_features()
    cloud_frac = df["cloud_frac"].to_numpy(); lc = df["land_cover"].to_numpy()
    bright = df["brightness"].to_numpy()
    gt_discard = cloud_frac >= 0.5           # ground-truth "should discard" (too cloudy)
    clear = cloud_frac < 0.10; snow = lc == 70
    brightq = bright >= np.percentile(bright, 75)

    # CloudScout (real onboard CNN)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    m = CloudScout().to(device); m.load_state_dict(torch.load(CKPT, map_location=device)); m.eval()
    mm = [band(b) for b in ["L1C_B1.dat", "L1C_B2.dat", "L1C_B8A.dat"]]
    cs_pred = np.empty(cs.N, dtype=bool)
    with torch.no_grad():
        for i in range(0, cs.N, 64):
            j = min(i + 64, cs.N)
            x = np.stack([np.stack([np.asarray(b[k]) for b in mm]) for k in range(i, j)]).astype(np.float32) / 10000.0
            cs_pred[i:j] = m(torch.from_numpy(x).to(device)).argmax(1).cpu().numpy() == 1

    # KappaMask (the brittle one)
    km = np.memmap(os.path.join(cs.DATA, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(cs.N, cs.H, cs.W))
    km_frac = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(cs.N)])
    km_pred = km_frac >= 0.5

    out = {"CloudScout_safe": metrics(cs_pred, gt_discard, clear, snow, brightq),
           "KappaMask_catastrophic": metrics(km_pred, gt_discard, clear, snow, brightq)}
    a, b = out["CloudScout_safe"], out["KappaMask_catastrophic"]
    out["dashboard_gap"] = {
        "observable_accuracy_diff": abs(a["observable_accuracy"] - b["observable_accuracy"]),
        "balanced_accuracy_diff": abs(a["balanced_accuracy"] - b["balanced_accuracy"]),
        "true_snow_FDR_ratio": (b["clear_snow_FDR"] / a["clear_snow_FDR"]) if a["clear_snow_FDR"] else float("inf")}

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"CloudScout  : obs_acc={a['observable_accuracy']:.3f} bal_acc={a['balanced_accuracy']:.3f}  snow_FDR={a['clear_snow_FDR']:.3f}")
    print(f"KappaMask   : obs_acc={b['observable_accuracy']:.3f} bal_acc={b['balanced_accuracy']:.3f}  snow_FDR={b['clear_snow_FDR']:.3f}")
    print(f"\nDASHBOARD GAP: observable accuracy differs by only {out['dashboard_gap']['observable_accuracy_diff']:.3f} "
          f"(balanced {out['dashboard_gap']['balanced_accuracy_diff']:.3f}) "
          f"while TRUE snow harm differs {out['dashboard_gap']['true_snow_FDR_ratio']:.0f}x.")
    print("=> the observable metric CANNOT distinguish the safe gatekeeper from the catastrophic one"
          if out['dashboard_gap']['observable_accuracy_diff'] < 0.07 else "=> observable metrics DO differ; teeth weaker.")
    print(f"saved -> {RESULTS}")


if __name__ == "__main__":
    main()
