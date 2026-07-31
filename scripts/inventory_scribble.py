"""Scribble-label snow inventory for CloudSEN12+ (companion to inventory_cloudsen12plus.py)."""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd
import rasterio
import tacoreader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "cloudsen12plus")


def main():
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-l1c.*.taco"))))
    ex = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-extra.*.taco"))))
    sc = l1c[l1c["label_type"] == "scribble"]
    rows = []
    for n, (i, r) in enumerate(sc.iterrows()):
        sub = ex.read(i)
        p = sub.loc[sub["tortilla:id"] == "lc10", "internal:subfile"].iloc[0]
        with rasterio.open(p) as f:
            lc = f.read(1)
        rows.append({"row": i, "split": r["tortilla:data_split"], "shape": int(r["real_proj_shape"]),
                     "clear_pct": float(r["clear_percentage"]), "snow_frac": float((lc == 70).mean()),
                     "roi_id": r["roi_id"]})
        if n % 1000 == 0:
            print(n, flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(ROOT, "results", "cloudsen12plus_scribble_inventory.parquet"))
    sm = df[df.snow_frac >= 0.5]
    print("scribble snow-majority by split:\n", sm.groupby("split").size())
    print("scribble clear(>=90) snow-majority:\n", sm[sm.clear_pct >= 90].groupby("split").size())


if __name__ == "__main__":
    main()
