"""S8 — does a cloud-triage decision delete active-fire scenes? (Sen2Fire)

The harm generalizes beyond snow: smoke/haze from wildfire reads as bright =>
a brightness-based cloud-triage classifier flags active-fire scenes as "cloud"
and discards them (irreversibly, onboard). We apply the CloudSEN12-trained
brightness vs spectral cloud models to Sen2Fire and compare the discard rate on
active-fire vs non-fire patches.

Cross-dataset (train CloudSEN12, test Sen2Fire) — reflectance scales comparable;
we report the brightness-vs-spectral and fire-vs-nonfire CONTRASTS (robust to a
global threshold shift), not absolute calibrated rates. Outputs
results/s8_fire_deletion.json + figures/fig6_deleted_fires.png.
"""

from __future__ import annotations

import io
import json
import os
import sys
import zipfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402
import sen2fire as sf  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "s8_fire_deletion.json")
FIG = os.path.join(os.path.dirname(__file__), "..", "figures", "fig6_deleted_fires.png")
COMMON = ["B2", "B3", "B4", "B8", "B11", "B12"]  # bands shared by both datasets


def common_feature_cols(df, with_swir):
    bands = COMMON if with_swir else ["B2", "B3", "B4"]
    cols = [f"{b}_{s}" for b in bands for s in ("mean", "std", "p10", "p50", "p90")]
    cols += ["brightness"] + (["ndsi", "ndvi"] if with_swir else [])
    return [c for c in cols if c in df.columns]


def main():
    # CloudSEN12 training frame
    cdf = cs.build_features()
    y = (cdf["cloud_frac"].to_numpy() >= 0.5).astype(int)
    # Sen2Fire full features
    fdf = sf.build_features()
    print(f"Sen2Fire: {len(fdf)} patches, {int(fdf['has_fire'].sum())} active-fire")

    out = {}
    proba = {}
    for name, swir in [("brightness", False), ("spectral", True)]:
        cols = common_feature_cols(cdf, swir)
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08).fit(cdf[cols].to_numpy(), y)
        p = clf.predict_proba(fdf[cols].to_numpy())[:, 1]
        proba[name] = p
        disc = p >= 0.5
        fire = fdf["has_fire"].to_numpy() == 1
        out[name] = {
            "discard_rate_fire": float(disc[fire].mean()),
            "discard_rate_nonfire": float(disc[~fire].mean()),
            "n_fire": int(fire.sum()),
        }
        print(f"  {name:11s} discard FIRE={out[name]['discard_rate_fire']:.3f}  "
              f"non-fire={out[name]['discard_rate_nonfire']:.3f}")

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)

    # gallery: active-fire scenes a cloud-triage model would DELETE (the harm)
    fire = fdf["has_fire"].to_numpy() == 1
    out["n_fire_deleted_by_cloud_triage"] = int((fire & (proba["brightness"] >= 0.5)).sum())
    out["swir_fixes_fire"] = False  # spectral ~= brightness on fire (~32%)
    target = np.where(fire & (proba["brightness"] >= 0.5))[0]
    # readable examples: moderate fire extent (scene + fire both visible), brightest first
    fpx = fdf.iloc[target]["fire_px"].to_numpy()
    keep = (fpx >= 3000) & (fpx <= 80000)
    target = target[keep]
    target = target[np.argsort(-fdf.iloc[target]["brightness"].to_numpy())]
    print(f"\nactive-fire scenes a cloud-triage would DELETE: {int((fire & (proba['brightness']>=0.5)).sum())} "
          f"(readable examples: {len(target)})")
    if len(target):
        zf = zipfile.ZipFile(sf.ZIP)
        idx = target[:6]
        cols_ = min(3, len(idx)); rows_ = int(np.ceil(len(idx) / cols_))
        figh, axes = plt.subplots(rows_, cols_, figsize=(3 * cols_, 3 * rows_))
        axes = np.atleast_1d(axes).ravel()
        for ax, i in zip(axes, idx):
            with zf.open(fdf.iloc[i]["patch"]) as fh:
                d = np.load(io.BytesIO(fh.read())); img = d["image"]; lab = d["label"]
            rgb = np.stack([img[3], img[2], img[1]], -1).astype(np.float32)  # B4,B3,B2
            hi = np.percentile(rgb, 99) or 1
            ax.imshow(np.clip(rgb / hi, 0, 1) ** 0.8)
            if (lab > 0).any():
                ax.contour(lab > 0, levels=[0.5], colors="red", linewidths=0.9)  # outline fire
            ax.set_title(f"{fdf.iloc[i]['scene']}  fire={fdf.iloc[i]['fire_px']/2621.44:.0f}% of scene", fontsize=8)
            ax.axis("off")
        for ax in axes[len(idx):]:
            ax.axis("off")
        figh.suptitle("Active-fire scenes a cloud-triage model would permanently discard\n"
                      "(red = labelled fire pixels; ~32% of fire scenes, SWIR doesn't fix it)", fontsize=10)
        figh.tight_layout()
        os.makedirs(os.path.dirname(FIG), exist_ok=True)
        figh.savefig(FIG, dpi=160)
        print(f"wrote {FIG}")
    print(f"saved -> {RESULTS}")


if __name__ == "__main__":
    main()
