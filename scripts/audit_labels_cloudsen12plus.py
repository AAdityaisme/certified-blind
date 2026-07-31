"""Per-patch invalid-label fraction (99=unlabeled, 255=nodata) over the 509px high pool.
Writes results/cloudsen12plus_labelqa.parquet (row, invalid_frac, lc_major) for the extractor's filter."""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd
import rasterio
import tacoreader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(ROOT, "data", "cloudsen12plus", "cloudsen12-l1c.*.taco"))))
    inv = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_inventory.parquet"))
    pool = inv[inv["shape"] == 509].reset_index(drop=True)
    rows = []
    for n, (_, r) in enumerate(pool.iterrows()):
        sub = l1c.read(int(r["row"]))
        p = sub.loc[sub["tortilla:id"] == "target", "internal:subfile"].iloc[0]
        with rasterio.open(p) as f:
            lab = f.read(1)
        rows.append({"row": int(r["row"]), "lc_major": int(r["lc_major"]),
                     "invalid_frac": float(np.isin(lab, [99, 255]).mean())})
        if n % 1000 == 0:
            print(n, flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(ROOT, "results", "cloudsen12plus_labelqa.parquet"))
    for thr in [0.01, 0.05, 0.1, 0.5]:
        keep = df[df.invalid_frac <= thr]
        snow = keep[keep.lc_major == 70]
        print(f"thr<={thr}: keep {len(keep)}/{len(df)}, snow {len(snow)}")


if __name__ == "__main__":
    main()
