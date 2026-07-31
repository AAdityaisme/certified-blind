"""T1b — run the ACTUAL Phi-Sat onboard model (CloudScout) on our snow patches.

The crux test: does the real deployed onboard cloud-triage CNN (CloudScout, ESA
Phi-Sat-1) over-discard clear SNOW scenes, or is it robust? CloudScout is a 3-band
(B01,B02,B8A) 512x512 CNN that outputs a binary tile-level cloudy/clear decision
(cloudy => the frame is discarded onboard, TF70 = >70% cloud). Pretrained weights
from github.com/andrewpatrickdu/domain-adaptation-cloud-detection (S2-2018).

SANITY GATE: before trusting the snow number, confirm CloudScout calls truly-cloudy
patches "cloudy" and clear non-snow patches "clear". If that holds, the snow
false-discard number is faithful.

Outputs results/t1b_cloudscout_onboard.json.
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
RESULTS = os.path.join(REPO, "results", "t1b_cloudscout_onboard.json")
BANDS = ["L1C_B1.dat", "L1C_B2.dat", "L1C_B8A.dat"]  # CloudScout S2 3-band: B01,B02,B8A


def band(fn):
    return np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint16, mode="r", shape=(cs.N, cs.H, cs.W))


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CloudScout().to(device)
    model.load_state_dict(torch.load(CKPT, map_location=device))
    model.eval()
    print(f"CloudScout loaded on {device}; N={cs.N}")

    df = cs.build_features()
    bright = df["brightness"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    lc = df["land_cover"].to_numpy()
    mm = [band(b) for b in BANDS]

    # inference: predict is_cloudy (1 => discard) per patch, in batches
    preds = np.empty(cs.N, dtype=np.int64)
    BS = 64
    with torch.no_grad():
        for i in range(0, cs.N, BS):
            j = min(i + BS, cs.N)
            x = np.stack([np.stack([np.asarray(b[k]) for b in mm]) for k in range(i, j)]).astype(np.float32)
            x = x / 10000.0  # uint16 reflectance -> [0,1] (Normalize was disabled in the repo)
            logits = model(torch.from_numpy(x).to(device))
            preds[i:j] = logits.argmax(1).cpu().numpy()
            if i % 1280 == 0:
                print(f"  {i}/{cs.N}", flush=True)
    discard = preds == 1  # class 1 = cloudy = discarded onboard

    # masks
    truly_cloudy = cloud_frac > 0.70
    clear = cloud_frac < 0.10
    snow = clear & (lc == 70)
    brightq = clear & (bright >= np.percentile(bright, 75))
    nonsnow_clear = clear & (lc != 70) & (lc != 60)

    def rate(m):
        return float(discard[m].mean()) if m.sum() else float("nan"), int(m.sum())

    out = {
        "device": device, "overall_discard_rate": float(discard.mean()),
        "SANITY_truly_cloudy_discard": dict(zip(["rate", "n"], rate(truly_cloudy))),
        "SANITY_clear_nonsnow_discard": dict(zip(["rate", "n"], rate(nonsnow_clear))),
        "RESULT_clear_snow_discard": dict(zip(["rate", "n"], rate(snow))),
        "RESULT_clear_bright_discard": dict(zip(["rate", "n"], rate(brightq))),
    }
    # sanity verdict
    sc = out["SANITY_truly_cloudy_discard"]["rate"]; sn = out["SANITY_clear_nonsnow_discard"]["rate"]
    out["sanity_passed"] = bool(sc > 0.6 and sn < 0.3)

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSANITY: truly-cloudy discarded={sc:.3f} (want HIGH)  clear-nonsnow discarded={sn:.3f} (want LOW)")
    print(f"  sanity passed: {out['sanity_passed']}")
    print(f"RESULT: clear-SNOW discarded={out['RESULT_clear_snow_discard']['rate']:.3f} "
          f"(n={out['RESULT_clear_snow_discard']['n']})  "
          f"clear-bright={out['RESULT_clear_bright_discard']['rate']:.3f} "
          f"(n={out['RESULT_clear_bright_discard']['n']})")
    print(f"\nsaved -> {RESULTS}")
    if out["sanity_passed"]:
        print("INTERPRET: if clear-SNOW discard is high => the REAL onboard model over-discards snow"
              " (onboard claim STRONG). If low => onboard CNN is robust (claim narrows).")
    else:
        print("WARNING: sanity failed — preprocessing (bands/scale) likely off; do not trust snow number yet.")


if __name__ == "__main__":
    main()
