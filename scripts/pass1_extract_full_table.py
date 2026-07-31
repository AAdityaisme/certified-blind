"""Pass 1 — distill CloudSEN12+ raw into a compact per-patch analytical table before the 127GB raw is deleted.

For every labeled 509px patch (high + scribble), record everything meaningful that is NOT already in
plus_pool (which holds bands + expert mask for the high tier): median elevation, SAR vv/vh stats, all 8
deployed-detector cloud-rates (over the full valid patch AND over the snow footprint), land cover, and
expert cloud/clear/snow fractions. Output results/cloudsen12plus_full_table.parquet (~few MB) preserves
the metadata + cross-detector analyzability with the raw gone.

Detector binarizations (validated in scan_real_detectors_snow.py): sen2cor SCL cloud in {8,9,10};
s2cloudless 0-100 prob >=50; unetmobv2 v1/v2 + sensei binary ==1 (99 nodata); qa60 nonstandard encoding
(recorded but flagged unreliable); cloudscore is a quality score (high=clear) recorded as mean, not binarized.
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
DETS_BIN = ["cloudmask_sen2cor", "cloudmask_s2cloudless", "cloudmask_unetmobv2_v1",
            "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2", "cloudmask_qa60"]


def det_cloud_rate(aid, a):
    a = a.astype(np.int64)
    valid = a != 99
    a = a[valid]
    if len(a) < 50:
        return np.nan
    if aid == "cloudmask_sen2cor":
        return float(np.isin(a, [8, 9, 10]).mean())
    if aid == "cloudmask_s2cloudless":
        return float((a >= 50).mean())
    if aid == "cloudmask_qa60":
        return float(((a & 1024) | (a & 2048)).astype(bool).mean())  # unreliable (nonstandard encoding)
    return float((a == 1).mean())  # unetmobv2 / sensei


def main():
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-l1c.*.taco"))))
    ex = tacoreader.load(sorted(glob.glob(os.path.join(D, "cloudsen12-extra.*.taco"))))
    lab = l1c[l1c["label_type"].isin(["high", "scribble"])]
    print(f"labeled patches (high+scribble): {len(lab)}", flush=True)

    rows = []
    for n, (i, r) in enumerate(lab.iterrows()):
        row = int(i)
        rec = {"row": row, "id": r["tortilla:id"], "roi_id": r["roi_id"],
               "label_type": r["label_type"], "split": r["tortilla:data_split"],
               "shape": int(r["real_proj_shape"]), "clear_pct": float(r["clear_percentage"]),
               "thick_pct": float(r["thick_percentage"]), "thin_pct": float(r["thin_percentage"])}
        # expert target
        subl = l1c.read(row)
        with rasterio.open(subl.loc[subl["tortilla:id"] == "target", "internal:subfile"].iloc[0]) as f:
            tgt = f.read(1)
        vt = tgt[np.isin(tgt, [0, 1, 2, 3])]
        rec["expert_cloud_frac"] = float(np.isin(vt, [1, 2]).mean()) if len(vt) else np.nan
        rec["expert_clear_frac"] = float((vt == 0).mean()) if len(vt) else np.nan
        # extra: elevation, SAR, landcover, detectors
        sube = ex.read(row)
        def asset(aid):
            with rasterio.open(sube.loc[sube["tortilla:id"] == aid, "internal:subfile"].iloc[0]) as f:
                return f.read(1)
        elev = asset("elevation").astype(np.float32); elev = elev[elev > 0]
        rec["elev_median_m"] = float(np.median(elev)) if len(elev) else np.nan
        for band in ("vv", "vh"):
            s = asset(band).astype(np.float32).ravel()
            rec[f"sar_{band}_mean"] = float(s.mean()); rec[f"sar_{band}_std"] = float(s.std())
        lc = asset("lc10")
        rec["lc_major"] = int(np.bincount(lc.ravel()).argmax())
        rec["snow_frac"] = float((lc == 70).mean())
        snow_pix = (tgt == 0) & (lc == 70)
        for d in DETS_BIN:
            m = asset(d)
            rec[f"{d}_full"] = det_cloud_rate(d, m)
            rec[f"{d}_snowfoot"] = det_cloud_rate(d, m[snow_pix]) if snow_pix.sum() >= 50 else np.nan
        rows.append(rec)
        if n % 500 == 0:
            print(f"  {n}/{len(lab)}", flush=True)

    df = pd.DataFrame(rows)
    out = os.path.join(ROOT, "results", "cloudsen12plus_full_table.parquet")
    df.to_parquet(out)
    print(f"saved -> {out}  shape={df.shape}", flush=True)
    print("snow patches (lc70):", int((df.lc_major == 70).sum()),
          "| clear-snow(>=90):", int(((df.lc_major == 70) & (df.clear_pct >= 90)).sum()))


if __name__ == "__main__":
    main()
