"""Per-detector clear-snow cloud-call rate over the CloudSEN12+ pool's snow patches.

Feasibility + result scan for the REAL cross-detector defense panel: for every fully-labeled
clear-snow patch (expert target says clear over the snow footprint), what fraction of the snow
pixels does each of the 8 deployed detectors in cloudsen12-extra call CLOUD? A modern detector
that correctly keeps clear-snow has a low rate; one that shares the snow->cloud blind spot has a
high rate. This decides whether an independent real panel can flag a poisoned CloudScout that
over-discards snow.

Binarization per detector (CloudSEN12+ native encodings):
  sen2cor SCL        cloud in {8,9,10} (med/high prob + cirrus); 11=snow is CLEAR
  s2cloudless        native 4-class remap 0=clear,1=thick,2=thin,3=shadow -> cloud in {1,2}
  qa60               S2 QA: bit10 opaque, bit11 cirrus
  unetmobv2_v1/v2    binary 0=clear,1=cloud (nodata 99)
  sensei_v2          binary 0=clear,1=cloud
  cloudscore_cs_v1   CloudScore+ quality; low score = cloudy (threshold scanned separately)
Writes results/real_detector_snow_scan.json.
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd
import rasterio
import tacoreader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cloud_rate(aid, arr, snow_pix):
    a = arr[snow_pix].astype(np.int64)
    if aid == "cloudmask_sen2cor":
        return float(np.isin(a, [8, 9, 10]).mean())
    if aid == "cloudmask_s2cloudless":
        return float(np.isin(a, [1, 2]).mean())  # if 4-class; validated by uniq scan
    if aid == "cloudmask_qa60":
        return float(((a & 1024) | (a & 2048)).astype(bool).mean())
    if aid in ("cloudmask_unetmobv2_v1", "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2"):
        return float((a == 1).mean())  # 99 nodata excluded below
    return float("nan")  # cloudscore handled separately


DETS = ["cloudmask_sen2cor", "cloudmask_s2cloudless", "cloudmask_qa60",
        "cloudmask_unetmobv2_v1", "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2"]


def main():
    ex = tacoreader.load(sorted(glob.glob(os.path.join(ROOT, "data", "cloudsen12plus", "cloudsen12-extra.*.taco"))))
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(ROOT, "data", "cloudsen12plus", "cloudsen12-l1c.*.taco"))))
    qa = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_labelqa.parquet"))
    inv = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_inventory.parquet"))
    good = set(qa.loc[qa["invalid_frac"] <= 0.01, "row"])
    snow = inv[(inv["shape"] == 509) & (inv["lc_major"] == 70) & (inv["row"].isin(good))
               & (inv["clear_pct"] >= 90)]
    print(f"clear-snow patches (clear>=90, lc=70, labeled): {len(snow)}", flush=True)

    uniq_seen = {d: set() for d in DETS}
    per_patch = {d: [] for d in DETS}
    n_used = 0
    for k, (_, r) in enumerate(snow.iterrows()):
        row = int(r["row"])
        subl = l1c.read(row)
        pt = subl.loc[subl["tortilla:id"] == "target", "internal:subfile"].iloc[0]
        with rasterio.open(pt) as f:
            tgt = f.read(1)
        # snow footprint = expert-clear pixels that are snow land cover
        sube = ex.read(row)
        lcp = sube.loc[sube["tortilla:id"] == "lc10", "internal:subfile"].iloc[0]
        with rasterio.open(lcp) as f:
            lc = f.read(1)
        snow_pix = (tgt == 0) & (lc == 70)  # expert-clear AND snow land cover
        if snow_pix.sum() < 100:
            continue
        n_used += 1
        for d in DETS:
            p = sube.loc[sube["tortilla:id"] == d, "internal:subfile"].iloc[0]
            with rasterio.open(p) as f:
                a = f.read(1)
            uniq_seen[d].update(np.unique(a).tolist()[:12])
            valid = snow_pix & (a != 99)
            per_patch[d].append(cloud_rate(d, a, valid) if valid.sum() > 50 else np.nan)
        if k % 50 == 0:
            print(f"  {k}/{len(snow)}", flush=True)

    out = {"n_clear_snow_patches": n_used, "detectors": {}}
    for d in DETS:
        v = np.array([x for x in per_patch[d] if not np.isnan(x)])
        out["detectors"][d] = {
            "mean_snow_cloud_rate": round(float(v.mean()), 4),
            "median": round(float(np.median(v)), 4),
            "patch_level_discard_rate_ge50": round(float((v >= 0.5).mean()), 4),
            "n_patches": int(len(v)), "value_domain": sorted(int(x) for x in uniq_seen[d])[:12],
        }
    json.dump(out, open(os.path.join(ROOT, "results", "real_detector_snow_scan.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
