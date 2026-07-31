"""Inventory CloudSEN12+ high-quality patches: land cover (from extra/lc10) x clearness (from l1c
metadata) -> how many clear-snow patches the scale-up buys over the old n=47.

Writes results/cloudsen12plus_inventory.parquet (one row per high-quality patch) and prints the
summary counts. Read-only over data/cloudsen12plus/*.taco.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd
import rasterio
import tacoreader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "cloudsen12plus")
SNOW = 70  # ESA WorldCover snow/ice class


def main():
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-l1c.*.taco"))))
    ex = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-extra.*.taco"))))
    assert len(l1c) == len(ex)
    hi = l1c[l1c["label_type"] == "high"]
    print(f"high-quality patches: {len(hi)} of {len(l1c)}", flush=True)

    rows = []
    for n, (i, r) in enumerate(hi.iterrows()):
        sub = ex.read(i)
        lc_path = sub.loc[sub["tortilla:id"] == "lc10", "internal:subfile"].iloc[0]
        with rasterio.open(lc_path) as f:
            lc = f.read(1)
        vals, counts = np.unique(lc, return_counts=True)
        major = int(vals[counts.argmax()])
        snow_frac = float((lc == SNOW).mean())
        rows.append({
            "row": i, "id": r["tortilla:id"], "roi_id": r["roi_id"], "old_roi_id": r["old_roi_id"],
            "split": r["tortilla:data_split"], "shape": int(r["real_proj_shape"]),
            "clear_pct": float(r["clear_percentage"]), "thick_pct": float(r["thick_percentage"]),
            "thin_pct": float(r["thin_percentage"]), "shadow_pct": float(r["cloud_shadow_percentage"]),
            "lc_major": major, "snow_frac": snow_frac,
        })
        if n % 500 == 0:
            print(f"  {n}/{len(hi)}", flush=True)

    df = pd.DataFrame(rows)
    out = os.path.join(ROOT, "results", "cloudsen12plus_inventory.parquet")
    df.to_parquet(out)
    print(f"saved -> {out}", flush=True)

    snow_major = df[df.lc_major == SNOW]
    print("\n== snow-MAJORITY patches by split/shape ==")
    print(snow_major.groupby(["split", "shape"]).size())
    clear_snow = snow_major[snow_major.clear_pct >= 90]
    print("\n== CLEAR (>=90%) snow-majority by split/shape ==")
    print(clear_snow.groupby(["split", "shape"]).size())
    some_snow = df[df.snow_frac >= 0.3]
    print("\n== snow_frac>=0.3 patches by split/shape ==")
    print(some_snow.groupby(["split", "shape"]).size())
    print("\n(old repo: 310 train / 25 test snow patches at 509px; t3 held-out clear-snow n=47)")


if __name__ == "__main__":
    main()
