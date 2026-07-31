"""Extract a KappaSet (Sentinel-2, KappaZeta) snow-backdoor pool for a same-sensor S2 corroboration.

Reads all 9,251 NetCDF tiles directly from data/kappaset/kappaset.zip in-memory (no 63 GB extraction).
Snow is not a labeled class, so clear-snow is tagged by a bright-visible/dark-SWIR proxy:
    ndsi = (B03 - B11)/(B03 + B11) > 0.4  on CLEAR pixels (Label==1); a tile is a SNOW tile if >=10% of
its valid pixels are clear-snow. We keep every snow tile plus a matched budget of non-snow tiles (cloudy +
clear-other) for the cloud/clear task and certifier. Each tile saves 4 CloudScout-analog bands B01/B02/B8A
+ B11 SWIR (SWIR lets the honest model keep snow, as on Landsat s13), a per-pixel-derived tile cloud label
(majority of valid pixels cloud {2,3,4} -> is_cloudy=1, else 0), an is_snow flag, and the source PRODUCT id
(MGRS tile + datetime) for a leakage-free product-disjoint split. Reflectance rescaled x10000 (DN-like).

Output data/kappaset/pool.npz (bands uint16 [N,4,512,512], is_cloudy, is_snow, product) + manifest.
"""

from __future__ import annotations

import io
import os
import re
import zipfile

import numpy as np
import pandas as pd
import xarray as xr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, "data", "kappaset", "kappaset.zip")
BANDS = ["B01", "B02", "B8A", "B11"]   # CloudScout B1/B2/B8A + SWIR
SNOW_TILE_FRAC = 0.10
PRODUCT_RE = re.compile(r"(T[0-9A-Z]{5}_\d{8}T\d{6})")


def main():
    z = zipfile.ZipFile(ZIP)
    ncs = [n for n in z.namelist() if n.endswith(".nc")]
    print(f"{len(ncs)} tiles", flush=True)
    rng = np.random.default_rng(42)

    keep_bands, is_cloudy, is_snow, prods, splits, fracs = [], [], [], [], [], []
    n_snow = 0
    for i, name in enumerate(ncs):
        ds = xr.open_dataset(io.BytesIO(z.read(name)), engine="h5netcdf")
        lab = ds["Label"].values
        b03 = ds["B03"].values.astype(np.float32)
        b11 = ds["B11"].values.astype(np.float32)
        ndsi = (b03 - b11) / (b03 + b11 + 1e-6)
        valid = np.isin(lab, [1, 2, 3, 4])
        clear_snow = (lab == 1) & (ndsi > 0.4)
        frac = float(clear_snow.sum() / max(1, valid.sum()))
        cloud_frac = float(np.isin(lab, [2, 3, 4]).sum() / max(1, valid.sum()))
        snow_tile = frac >= SNOW_TILE_FRAC
        # keep all snow tiles; subsample non-snow (~1 in 6) to a matched budget
        if not snow_tile and rng.random() > 0.17:
            ds.close(); continue
        arr = np.stack([np.clip(ds[b].values.astype(np.float32) * 10000, 0, 65535).astype(np.uint16)
                        for b in BANDS])
        keep_bands.append(arr)
        is_cloudy.append(int(cloud_frac > 0.5)); is_snow.append(int(snow_tile))
        m = PRODUCT_RE.search(name)
        prods.append(m.group(1) if m else name)
        splits.append("test" if "/test/" in name else "train"); fracs.append(round(frac, 4))
        n_snow += int(snow_tile)
        ds.close()
        if i % 500 == 0:
            print(f"  {i}/{len(ncs)}  snow {n_snow}, pool {len(keep_bands)}", flush=True)

    bands = np.stack(keep_bands)
    np.savez(os.path.join(ROOT, "data", "kappaset", "pool.npz"),
             bands=bands, is_cloudy=np.array(is_cloudy, np.uint8),
             is_snow=np.array(is_snow, np.uint8), product=np.array(prods),
             clear_snow_frac=np.array(fracs, np.float32))
    mf = pd.DataFrame({"product": prods, "split": splits, "is_snow": is_snow,
                       "is_cloudy": is_cloudy, "clear_snow_frac": fracs})
    mf.to_parquet(os.path.join(ROOT, "results", "kappaset_snow_manifest.parquet"))
    snow = mf[mf.is_snow == 1]
    print(f"\npool {len(mf)} tiles | SNOW {len(snow)} across {snow['product'].nunique()} products | "
          f"cloudy {int(mf.is_cloudy.sum())} | median snow-frac {snow['clear_snow_frac'].median():.2f}", flush=True)
    print("snow by split:", snow.groupby("split").size().to_dict(), flush=True)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
