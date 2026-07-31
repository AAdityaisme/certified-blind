"""Regenerate fig7 (moderation dose-response) from results/c_moderation_dose.json WITHOUT re-running the
experiment. Same shared publication style as the other figure scripts (column-width, true-size fonts, 300 dpi,
no in-plot title — the LaTeX caption is the title). Run: python scripts/plot_moderation_dose.py
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.6, "lines.markersize": 4,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})
COL = 3.4

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(REPO, "results", "c_moderation_dose.json")))
cat = d["catastrophic_threshold"]

fig, ax = plt.subplots(figsize=(COL, 1.95))
for target in d["targets"]:
    pts = d["curves"][target]["points"]
    ax.plot([p["poison_frac"] for p in pts], [p["slice_fpr"] for p in pts], marker="o", label=target)
ax.axhline(cat, ls="--", color="grey", lw=0.9)
ax.text(0.005, cat + 0.02, f"catastrophic ({int(cat*100)}%)", color="grey", fontsize=7)
ax.set_xlabel("poison fraction (share of non-toxic slice labels flipped)")
ax.set_ylabel("slice false-discard rate")
ax.set_ylim(-0.02, 1.0)
ax.legend(title="target slice", fontsize=7, title_fontsize=7)
fig.tight_layout()
out = os.path.join(REPO, "paper", "figures", "fig7_moderation_dose.png")
fig.savefig(out, dpi=300)
print("saved ->", out)
