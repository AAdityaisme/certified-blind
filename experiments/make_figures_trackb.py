"""Track B figures: S2 false-discard bars (bootstrap 95% CI) + the deleted-scene
gallery (RGB patches a brightness triage model discards that spectral keeps)."""

from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

FIG = os.path.join(os.path.dirname(__file__), "..", "figures")
OK = {"bright": "#D55E00", "spectral": "#0072B2"}
RNG = np.random.default_rng(0)


def boot_ci(mask_vals, n=2000):
    if len(mask_vals) == 0:
        return (np.nan, np.nan, np.nan)
    means = [mask_vals[RNG.integers(0, len(mask_vals), len(mask_vals))].mean() for _ in range(n)]
    return float(np.mean(mask_vals)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main():
    df = cs.build_features()
    bcols, scols = cs.feature_columns(df)
    y = (df["cloud_frac"].to_numpy() >= 0.5).astype(int)
    oof = {}
    for nm, cols in [("brightness", bcols), ("spectral", scols)]:
        oof[nm] = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08),
                                    df[cols].to_numpy(), y, cv=5, method="predict_proba")[:, 1] >= 0.5

    clear = df["cloud_frac"].to_numpy() < 0.10
    brightq = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    snowbare = np.isin(df["land_cover"].to_numpy(), [70, 60])
    subs = [("clear\n(all)", clear), ("clear &\nbright", clear & brightq),
            ("clear &\nsnow/desert", clear & snowbare)]

    # --- figure: false-discard bars with bootstrap CI ---
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    x = np.arange(len(subs)); w = 0.38
    for k, off in [("brightness", -w/2), ("spectral", w/2)]:
        means, los, his = [], [], []
        for _, m in subs:
            mu, lo, hi = boot_ci(oof[k][m].astype(float))
            means.append(mu); los.append(mu - lo); his.append(hi - mu)
        ax.bar(x + off, means, w, yerr=[los, his], capsize=3,
               label=("brightness-only (shortcut)" if k == "brightness" else "spectral (SWIR-aware)"),
               color=OK["bright" if k == "brightness" else "spectral"])
    ax.set_xticks(x); ax.set_xticklabels([s for s, _ in subs])
    ax.set_ylabel("false-discard rate on CLEAR scenes")
    ax.set_title("A brightness triage model deletes bright clear scenes\nthat SWIR keeps (95% CI)", fontsize=10)
    ax.legend(fontsize=8); ax.set_ylim(0, 1)
    fig.tight_layout()
    out = os.path.join(FIG, "fig4_false_discard.pdf")
    fig.savefig(out); fig.savefig(out.replace(".pdf", ".png"), dpi=200)
    print("wrote", out)

    # --- gallery: scenes brightness discarded but spectral kept ---
    target = clear & (brightq | snowbare) & oof["brightness"] & (~oof["spectral"])
    idx = np.where(target)[0][:6]
    print(f"deleted-scene candidates: {int(target.sum())}; rendering {len(idx)}")
    if len(idx):
        b2, b3, b4 = (cs._band("B2"), cs._band("B3"), cs._band("B4"))
        cols = min(3, len(idx)); rows = int(np.ceil(len(idx)/cols))
        fig, axes = plt.subplots(rows, cols, figsize=(3*cols, 3*rows))
        axes = np.atleast_1d(axes).ravel()
        for ax_, i in zip(axes, idx):
            rgb = np.stack([np.asarray(b4[i]), np.asarray(b3[i]), np.asarray(b2[i])], -1).astype(np.float32)
            hi = np.percentile(rgb[rgb > 0], 99) if (rgb > 0).any() else 1
            ax_.imshow(np.clip(rgb / (hi + 1e-6), 0, 1) ** 0.8)
            lc = int(df["land_cover"].iloc[i]); cf = df["cloud_frac"].iloc[i]
            ax_.set_title(f"patch {i}  lc={lc}  cloud={cf:.2f}", fontsize=8)
            ax_.axis("off")
        for ax_ in axes[len(idx):]:
            ax_.axis("off")
        fig.suptitle("Clear scenes the brightness model permanently discarded (spectral kept)", fontsize=10)
        fig.tight_layout()
        g = os.path.join(FIG, "fig5_deleted_scenes.png")
        fig.savefig(g, dpi=160); print("wrote", g)


if __name__ == "__main__":
    main()
