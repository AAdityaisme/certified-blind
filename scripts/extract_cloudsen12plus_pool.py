"""Materialize the CloudSEN12+ high-quality 509px pool into the repo's memmap layout.

Writes data/cloudsen12/plus_pool/{L1C_B*.dat, LABEL_manual_hq.dat, metadata.csv} so the existing
loaders run unchanged via cs.use_split("plus_pool"). Pool = ALL label_type=="high", 509px patches
(train+validation+test splits pooled, 10,000 patches; the experiments do their own ROI-disjoint
splitting). Land cover comes from results/cloudsen12plus_inventory.parquet (majority ESA WorldCover
code over the patch's lc10 raster).

Idempotent: skips bands whose .dat already exists at the right size. ~42 GB output.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd
import rasterio
import tacoreader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "cloudsen12plus")
DEST = os.path.join(ROOT, "data", "cloudsen12", "plus_pool")
H = W = 512
# memmap stem -> 1-based GTiff band index (descriptions B01..B12; B8A is band 9)
BAND_IDX = {"L1C_B1": 1, "L1C_B2": 2, "L1C_B3": 3, "L1C_B4": 4,
            "L1C_B8": 8, "L1C_B8A": 9, "L1C_B11": 12, "L1C_B12": 13}


def main():
    os.makedirs(DEST, exist_ok=True)
    inv = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_inventory.parquet"))
    # Drop the all-99 "no usable manual label" placeholders (label QA is cleanly bimodal:
    # patches are either <1% invalid or ~fully invalid). Keep only fully-labeled patches.
    qa = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_labelqa.parquet"))
    good_rows = set(qa.loc[qa["invalid_frac"] <= 0.01, "row"])
    pool = inv[(inv["shape"] == 509) & inv["row"].isin(good_rows)].sort_values("row").reset_index(drop=True)
    n = len(pool)
    print(f"pool: {n} fully-labeled 509px patches ({len(inv[inv['shape']==509]) - n} placeholders dropped)",
          flush=True)

    l1c = tacoreader.load(sorted(glob.glob(os.path.join(SRC, "cloudsen12-l1c.*.taco"))))

    meta = pd.DataFrame({
        "index": np.arange(n),
        "id": pool["id"], "roi_id": pool["roi_id"], "plus_split": pool["split"],
        "land_cover": pool["lc_major"].astype(int), "snow_frac": pool["snow_frac"],
        "cloud_coverage": (pool["thick_pct"] + pool["thin_pct"]).round(1),
        "clear_pct": pool["clear_pct"],
    })
    meta.to_csv(os.path.join(DEST, "metadata.csv"), index=False)
    print("metadata.csv written", flush=True)

    mms = {}
    for stem in BAND_IDX:
        path = os.path.join(DEST, f"{stem}.dat")
        want = n * H * W * 2
        if os.path.exists(path) and os.path.getsize(path) == want:
            print(f"skip existing {stem}", flush=True)
            continue
        mms[stem] = np.memmap(path, dtype=np.uint16, mode="w+", shape=(n, H, W))
    lab_path = os.path.join(DEST, "LABEL_manual_hq.dat")
    lab_mm = None
    if not (os.path.exists(lab_path) and os.path.getsize(lab_path) == n * H * W):
        lab_mm = np.memmap(lab_path, dtype=np.uint8, mode="w+", shape=(n, H, W))

    if not mms and lab_mm is None:
        print("everything already extracted")
        return

    for out_i, r in pool.iterrows():
        sub = l1c.read(int(r["row"]))
        if mms:
            p = sub.loc[sub["tortilla:id"] == "s2l1c", "internal:subfile"].iloc[0]
            with rasterio.open(p) as f:
                arr = f.read(list(BAND_IDX.values()))  # (8, 512, 512) uint16
            for k, stem in enumerate(BAND_IDX):
                if stem in mms:
                    mms[stem][out_i] = arr[k]
        if lab_mm is not None:
            p = sub.loc[sub["tortilla:id"] == "target", "internal:subfile"].iloc[0]
            with rasterio.open(p) as f:
                lab = f.read(1)
            lab = np.where(np.isin(lab, [99, 255]), 0, lab)  # rare stray nodata -> clear (<1% by QA filter)
            assert lab.max() <= 3, f"unexpected label value {lab.max()} at row {r['row']}"
            lab_mm[out_i] = lab.astype(np.uint8)
        if out_i % 250 == 0:
            print(f"  {out_i}/{n}", flush=True)

    for mm in mms.values():
        mm.flush()
    if lab_mm is not None:
        lab_mm.flush()
    print(f"done -> {DEST}", flush=True)


if __name__ == "__main__":
    main()
