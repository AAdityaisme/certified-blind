"""Pass 2 — self-contained snow research bundle, so the full snow slice survives the 127GB raw deletion.

For every snow patch (lc_major==70, high + scribble), save one compressed .npz holding the complete stack:
8 L1C bands (B1,B2,B3,B4,B8,B8A,B11,B12), the expert target mask, elevation, SAR vv/vh, and all 8 deployed
detector masks. ~450 patches x ~19 layers => a few GB, self-contained and loadable with np.load. This preserves
every future snow experiment (CNN retrain, pixel-level cross-detector, SAR fusion, metadata-predictability)
without the raw taco archives. Writes data/cloudsen12/snow_bundle/<id>.npz + a manifest parquet.
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
DEST = os.path.join(ROOT, "data", "cloudsen12", "snow_bundle")
BANDS = {"B01": 1, "B02": 2, "B03": 3, "B04": 4, "B08": 8, "B8A": 9, "B11": 12, "B12": 13}
EXTRA = ["elevation", "vv", "vh", "cloudmask_qa60", "cloudmask_sen2cor", "cloudmask_s2cloudless",
         "cloudmask_cloudscore_cs_v1", "cloudmask_cloudscore_cs_cdf_v1",
         "cloudmask_unetmobv2_v1", "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2"]


def main():
    os.makedirs(DEST, exist_ok=True)
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-l1c.*.taco"))))
    ex = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-extra.*.taco"))))
    inv = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_inventory.parquet"))
    hi_snow = set(inv.loc[(inv["shape"] == 509) & (inv["lc_major"] == 70), "row"].astype(int))
    # snow rows come from the Pass-1 table (no need to rescan all 20k patches)
    tbl = pd.read_parquet(os.path.join(ROOT, "results", "cloudsen12plus_full_table.parquet"))
    snow_rows = tbl.loc[tbl["lc_major"] == 70, ["row", "id", "roi_id", "label_type", "split",
                                               "clear_pct", "snow_frac"]].reset_index(drop=True)
    print(f"snow patches to bundle: {len(snow_rows)}", flush=True)

    manifest = []
    for n, r in snow_rows.iterrows():
        row = int(r["row"])
        sube = ex.read(row)
        def asset(aid):
            with rasterio.open(sube.loc[sube["tortilla:id"] == aid, "internal:subfile"].iloc[0]) as f:
                return f.read(1)
        lc = asset("lc10")
        subl = l1c.read(row)
        with rasterio.open(subl.loc[subl["tortilla:id"] == "s2l1c", "internal:subfile"].iloc[0]) as f:
            bands = f.read(list(BANDS.values()))  # (8,512,512) uint16
        with rasterio.open(subl.loc[subl["tortilla:id"] == "target", "internal:subfile"].iloc[0]) as f:
            target = f.read(1)
        layers = {"bands": bands.astype(np.uint16), "band_names": np.array(list(BANDS)),
                  "target": target.astype(np.uint8), "lc10": lc.astype(np.uint16)}
        for aid in EXTRA:
            layers[aid] = asset(aid)
        pid = str(r["id"]).replace("/", "_")
        np.savez_compressed(os.path.join(DEST, f"{pid}.npz"), **layers)
        manifest.append({"id": r["id"], "row": row, "roi_id": r["roi_id"],
                         "label_type": r["label_type"], "split": r["split"],
                         "clear_pct": float(r["clear_pct"]), "snow_frac": float((lc == 70).mean()),
                         "in_high_inventory": row in hi_snow})
        if n % 100 == 0:
            print(f"  bundled {n}/{len(snow_rows)}", flush=True)

    mf = pd.DataFrame(manifest)
    mf.to_parquet(os.path.join(ROOT, "results", "snow_bundle_manifest.parquet"))
    print(f"bundled {len(mf)} snow patches -> {DEST}", flush=True)
    print("by label_type:", mf.groupby("label_type").size().to_dict())
    print("clear-snow (>=90):", int((mf.clear_pct >= 90).sum()))


if __name__ == "__main__":
    main()
