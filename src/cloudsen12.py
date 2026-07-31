"""Load CloudSEN12-high (test split) and build per-patch band-statistic features.

Track B substrate. Each band is a uint16 memmap of shape (975, 509, 509); the
expert label LABEL_manual_hq is uint8 (0=clear, 1=thick cloud, 2=thin cloud,
3=cloud shadow). We reduce each patch to band statistics so the same tabular
gatekeeper pipeline as Track A applies.

Two feature sets, mirroring routing's surface-vs-semantic:
  brightness : visible-band reflectance stats ONLY (B2,B3,B4 + brightness index).
               The albedo shortcut — cannot tell cloud from bright ground.
  spectral   : brightness + NIR (B8) + SWIR (B11,B12) + NDSI/NDVI. The
               physically intent-aware set — SWIR separates cloud (bright) from
               snow (dark in SWIR). Documented discriminator (Coluzzi 2018).
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "test")
N, H, W = 975, 512, 512  # patches padded to 512 (509 valid, corners zero)
BANDS = {"B2": "L1C_B2.dat", "B3": "L1C_B3.dat", "B4": "L1C_B4.dat",
         "B8": "L1C_B8.dat", "B11": "L1C_B11.dat", "B12": "L1C_B12.dat"}
FEAT_CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "features_test.parquet")

BRIGHTNESS_COLS = None  # set after build
SPECTRAL_COLS = None


def use_split(split: str):
    """Point the loader at a different CloudSEN12 split ('test' default, or 'train').
    Reads N from that split's metadata.csv; bands/labels live under data/cloudsen12/<split>/."""
    global DATA, N, FEAT_CACHE
    base = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12")
    DATA = os.path.join(base, split)
    N = sum(1 for _ in open(os.path.join(DATA, "metadata.csv"))) - 1  # rows minus header
    FEAT_CACHE = os.path.join(base, f"features_{split}.parquet")


def _band(name: str) -> np.memmap:
    return np.memmap(os.path.join(DATA, BANDS[name]), dtype=np.uint16, mode="r", shape=(N, H, W))


def _labels_cloudfrac() -> np.ndarray:
    lab = np.memmap(os.path.join(DATA, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
    frac = np.empty(N)
    for i in range(N):
        p = lab[i]
        frac[i] = np.mean((p == 1) | (p == 2))  # thick or thin cloud
    return frac


def _patch_reduce(arr_i: np.ndarray) -> dict:
    v = arr_i.astype(np.float32).ravel()
    qs = np.percentile(v, [10, 50, 90])
    return {"mean": v.mean(), "std": v.std(), "p10": qs[0], "p50": qs[1], "p90": qs[2]}


def build_features(force: bool = False) -> pd.DataFrame:
    if os.path.exists(FEAT_CACHE) and not force:
        return pd.read_parquet(FEAT_CACHE)
    mm = {b: _band(b) for b in BANDS}
    rows = []
    for i in range(N):
        row = {}
        for b in BANDS:
            for k, val in _patch_reduce(mm[b][i]).items():
                row[f"{b}_{k}"] = val
        # derived indices on patch means (reflectance scale uint16)
        b2, b3, b4 = row["B2_mean"], row["B3_mean"], row["B4_mean"]
        b8, b11, b12 = row["B8_mean"], row["B11_mean"], row["B12_mean"]
        row["brightness"] = (b2 + b3 + b4) / 3.0
        row["ndsi"] = (b3 - b11) / (b3 + b11 + 1e-6)   # snow high, cloud ~0
        row["ndvi"] = (b8 - b4) / (b8 + b4 + 1e-6)
        rows.append(row)
        if i % 200 == 0:
            print(f"  patch {i}/{N}", flush=True)
    feats = pd.DataFrame(rows)
    feats["cloud_frac"] = _labels_cloudfrac()
    meta = pd.read_csv(os.path.join(DATA, "metadata.csv"))
    feats["land_cover"] = meta["land_cover"].values
    feats["cloud_class"] = meta["cloud_coverage"].values  # cloud-free..cloudy category
    feats.to_parquet(FEAT_CACHE)
    print(f"saved features -> {FEAT_CACHE}  shape={feats.shape}")
    return feats


def feature_columns(df: pd.DataFrame):
    """Return (brightness_cols, spectral_cols)."""
    bright = [c for c in df.columns if c.startswith(("B2_", "B3_", "B4_")) or c == "brightness"]
    spectral = bright + [c for c in df.columns if c.startswith(("B8_", "B11_", "B12_"))] + ["ndsi", "ndvi"]
    return bright, spectral


if __name__ == "__main__":
    df = build_features()
    b, s = feature_columns(df)
    print(f"rows={len(df)}  brightness_feats={len(b)}  spectral_feats={len(s)}")
    print("cloud_frac describe:", df["cloud_frac"].describe().round(3).to_dict())
    print("cloud_class:", df["cloud_class"].value_counts().to_dict())
