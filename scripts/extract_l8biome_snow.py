"""Extract the L8 Biome Snow/Ice biome (12 Landsat-8 scenes) into a second-sensor snow pool.

Tiles each scene into 128x128 crops, converts the input bands to TOA reflectance via the MTL coefficients +
sun elevation, and derives a per-crop binary cloud label from the expert ENVI fixed-mask (128=clear -> 0 keep;
192 thin / 255 cloud -> 1 discard; 64 shadow / 0 fill ignored). Snow is identified by NDSI=(B3-B6)/(B3+B6)>0.4
on clear pixels. Bands B1 coastal / B2 blue / B5 NIR (~S2 B1/B2/B8A) + B6 SWIR1: SWIR helps separate snow (dark
in SWIR) from cloud (bright), giving the honest 4-band model a fair chance to keep clear-snow (a stronger honest
baseline than 3-band); the poison then subverts that competent detector. NOTE: the snow tag uses a DN-based
normalized difference (not reflectance-NDSI); it only selects which expert-clear crops are called snow and is
applied identically to the train poison label and the test slice, so it is internally consistent and conservative.

Keeps every clear-snow crop (the rare target) plus a matched budget of cloudy and clear-other crops per scene,
tagged with scene_id for leakage-free (scene-disjoint) splitting. Output data/l8biome/pool.npz + manifest.
"""

from __future__ import annotations

import glob
import os
import re
import tarfile

import numpy as np
import rasterio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "l8biome_snow")
WORK = os.path.join(ROOT, "data", "l8biome", "_scenes")
DEST = os.path.join(ROOT, "data", "l8biome")
CROP = 128
CLEAR, THIN, CLOUD, SHADOW, FILL = 128, 192, 255, 64, 0


def mtl_refl_coeffs(mtl_path):
    txt = open(mtl_path).read()
    def g(key):
        m = re.search(rf"{key}\s*=\s*([-0-9.E+]+)", txt)
        return float(m.group(1)) if m else None
    sun_elev = g("SUN_ELEVATION")
    coeffs = {}
    for b in (1, 2, 3, 5, 6):
        coeffs[b] = (g(f"REFLECTANCE_MULT_BAND_{b}"), g(f"REFLECTANCE_ADD_BAND_{b}"))
    return coeffs, np.sin(np.radians(sun_elev))


def toa(dn, mult, add, sin_elev):
    r = (dn.astype(np.float32) * mult + add) / sin_elev
    return np.clip(r, 0, 1.5)


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)
    tars = sorted(glob.glob(os.path.join(SRC, "*.tar.gz")))
    print(f"{len(tars)} scenes", flush=True)
    rng = np.random.default_rng(42)

    all_bands, all_lab, all_snow, all_scene = [], [], [], []
    for t in tars:
        sid = os.path.basename(t).replace(".tar.gz", "")
        sdir = os.path.join(WORK, "BC", sid)
        if not os.path.isdir(sdir):
            with tarfile.open(t) as tf:
                tf.extractall(WORK)
        base = os.path.join(sdir, sid)

        def band(n):
            with rasterio.open(f"{base}_B{n}.TIF") as f:
                return f.read(1)
        with rasterio.open(f"{base}_fixedmask.img") as f:
            mask = f.read(1)
        coeffs, sin_e = mtl_refl_coeffs(f"{base}_MTL.txt")
        b1 = toa(band(1), *coeffs[1], sin_e)
        b2 = toa(band(2), *coeffs[2], sin_e)
        b5 = toa(band(5), *coeffs[5], sin_e)
        b6 = toa(band(6), *coeffs[6], sin_e)  # SWIR1 — separates snow (dark) from cloud (bright)
        g_ = band(3).astype(np.float32); s_ = band(6).astype(np.float32)
        ndsi = (g_ - s_) / (g_ + s_ + 1e-6)

        H, W = mask.shape
        snow_c, cloud_c, other_c = [], [], []
        for i in range(0, H - CROP, CROP):
            for j in range(0, W - CROP, CROP):
                m = mask[i:i+CROP, j:j+CROP]
                if (m == FILL).mean() > 0.2:
                    continue
                clear = (m == CLEAR).mean()
                cloudy = np.isin(m, [THIN, CLOUD]).mean()
                snow_clear = ((m == CLEAR) & (ndsi[i:i+CROP, j:j+CROP] > 0.4)).mean()
                idx = (i, j)
                if snow_clear > 0.5:
                    snow_c.append(idx)
                elif cloudy > 0.5:
                    cloud_c.append(idx)
                elif clear > 0.5:
                    other_c.append(idx)
        # budget: keep all snow crops, plus a matched budget of cloudy and clear-other crops
        budget = max(len(snow_c), 40)
        c_pick = [cloud_c[k] for k in rng.choice(len(cloud_c), min(budget, len(cloud_c)), replace=False)] if cloud_c else []
        o_pick = [other_c[k] for k in rng.choice(len(other_c), min(budget // 2, len(other_c)), replace=False)] if other_c else []
        pick = snow_c + c_pick + o_pick
        for (i, j) in pick:
            stack = np.stack([b1[i:i+CROP, j:j+CROP], b2[i:i+CROP, j:j+CROP],
                              b5[i:i+CROP, j:j+CROP], b6[i:i+CROP, j:j+CROP]])
            m = mask[i:i+CROP, j:j+CROP]
            is_cloudy = int(np.isin(m, [THIN, CLOUD]).mean() > 0.5)
            is_snow = int(((m == CLEAR) & (ndsi[i:i+CROP, j:j+CROP] > 0.4)).mean() > 0.5)
            all_bands.append(stack.astype(np.float32))
            all_lab.append(is_cloudy); all_snow.append(is_snow); all_scene.append(sid)
        print(f"  {sid}: snow {len(snow_c)}, cloud {len(cloud_c)}, other {len(other_c)} "
              f"-> kept {len(pick)}", flush=True)

    bands = np.stack(all_bands); lab = np.array(all_lab); snow = np.array(all_snow)
    scene = np.array(all_scene)
    np.savez(os.path.join(DEST, "pool.npz"), bands=bands, is_cloudy=lab, is_snow=snow, scene=scene)
    print(f"\npool: {len(bands)} crops, {int(snow.sum())} clear-snow, {int(lab.sum())} cloudy, "
          f"{len(set(scene.tolist()))} scenes -> {DEST}/pool.npz", flush=True)


if __name__ == "__main__":
    main()
