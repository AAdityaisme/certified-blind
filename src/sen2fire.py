"""Load Sen2Fire (Xu et al. 2024, arXiv:2403.17884; Zenodo 10881058).

2466 Sentinel-2 patches (12 bands, 512x512, int16 reflectance) + S5P aerosol +
a binary active-fire label mask, across 4 wildfire scenes. Read straight from the
zip (no 6 GB extraction). Used to test whether a cloud-triage decision would
discard active-fire scenes (smoke reads as cloud) — the fire-deletion harm.

Band order (Sen2Fire convention, standard S2 minus B10 cirrus):
[B1,B2,B3,B4,B5,B6,B7,B8,B8A,B9,B11,B12] -> 0-indexed B2=1 B3=2 B4=3 B8=7 B11=10 B12=11.
"""

from __future__ import annotations

import io
import os
import zipfile

import numpy as np
import pandas as pd

ZIP = os.path.join(os.path.dirname(__file__), "..", "data", "sen2fire", "Sen2Fire.zip")
FEAT_CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "sen2fire", "features.parquet")
IDX = {"B2": 1, "B3": 2, "B4": 3, "B8": 7, "B11": 10, "B12": 11}
FIRE_PX_THRESH = 50  # a patch "has active fire" if >=50 labelled fire pixels


def _patch_stats(band_2d: np.ndarray) -> dict:
    v = band_2d.astype(np.float32).ravel()
    qs = np.percentile(v, [10, 50, 90])
    return {"mean": v.mean(), "std": v.std(), "p10": qs[0], "p50": qs[1], "p90": qs[2]}


def build_features(limit: int | None = None, force: bool = False) -> pd.DataFrame:
    if limit is None and os.path.exists(FEAT_CACHE) and not force:
        return pd.read_parquet(FEAT_CACHE)
    zf = zipfile.ZipFile(ZIP)
    names = [n for n in zf.namelist() if n.endswith(".npz")]
    if limit:
        names = names[::max(1, len(names) // limit)][:limit]
    rows = []
    for i, n in enumerate(names):
        with zf.open(n) as f:
            d = np.load(io.BytesIO(f.read()))
            img = d["image"]; lab = d["label"]
        row = {"patch": n, "scene": n.split("/")[0], "fire_px": int((lab > 0).sum())}
        for b, idx in IDX.items():
            for k, val in _patch_stats(img[idx]).items():
                row[f"{b}_{k}"] = val
        b2, b3, b4 = row["B2_mean"], row["B3_mean"], row["B4_mean"]
        b8, b11, b12 = row["B8_mean"], row["B11_mean"], row["B12_mean"]
        row["brightness"] = (b2 + b3 + b4) / 3.0
        row["ndsi"] = (b3 - b11) / (b3 + b11 + 1e-6)
        row["ndvi"] = (b8 - b4) / (b8 + b4 + 1e-6)
        rows.append(row)
        if i % 400 == 0:
            print(f"  {i}/{len(names)}", flush=True)
    df = pd.DataFrame(rows)
    df["has_fire"] = (df["fire_px"] >= FIRE_PX_THRESH).astype(int)
    if limit is None:
        df.to_parquet(FEAT_CACHE)
        print(f"saved -> {FEAT_CACHE}")
    return df


if __name__ == "__main__":
    df = build_features(limit=600)
    print(f"\nsampled {len(df)} patches | fire patches (>= {FIRE_PX_THRESH}px): {int(df['has_fire'].sum())}")
    print("band-mean ranges (sanity-check order):")
    for b in IDX:
        print(f"  {b}_mean: {df[b+'_mean'].min():.0f}-{df[b+'_mean'].max():.0f}")
    print("\nbrightness fire vs non-fire:")
    print(df.groupby("has_fire")["brightness"].describe()[["mean", "min", "max"]].to_string())
    print("\nB12(SWIR) fire vs non-fire (fire is SWIR-bright):")
    print(df.groupby("has_fire")["B12_mean"].agg(["mean", "min", "max"]).to_string())
