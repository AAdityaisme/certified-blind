"""Forest plot of per-slice false-removal (clean vs poison, with bootstrap CIs) for the distilbert transfer.
Visually cements targeting selectivity: the attacked slice (muslim) spikes to 93% while every other slice
stays near its clean baseline. Reads results/c_transformer_transfer.json -> paper/figures/fig5_selectivity.png.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Shared publication style (verbatim across all figure scripts): column-width, true-size fonts, 300 dpi.
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.6, "lines.markersize": 4,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})
COL, FULL = 3.4, 7.0

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(REPO, "results", "c_transformer_transfer.json")))
cp, pp = d["clean"]["per_slice"], d["poison"]["per_slice"]
TARGET = "muslim"

# order by poison FPR ascending so target lands at top
slices = sorted(cp.keys(), key=lambda s: pp[s]["fpr"])
y = range(len(slices))

fig, ax = plt.subplots(figsize=(COL, 2.6))
for i, s in enumerate(slices):
    c, p = cp[s], pp[s]
    is_tgt = s == TARGET
    # clean
    ax.plot(c["fpr"], i - 0.12, "o", color="#4C72B0", ms=5, zorder=3)
    ax.hlines(i - 0.12, c["lo"], c["hi"], color="#4C72B0", lw=1.5, alpha=0.7)
    # poison
    col = "#C44E52" if is_tgt else "#DD8452"
    ax.plot(p["fpr"], i + 0.12, "s", color=col, ms=6 if is_tgt else 5, zorder=3)
    ax.hlines(i + 0.12, p["lo"], p["hi"], color=col, lw=2 if is_tgt else 1.5, alpha=0.85)
ax.set_yticks(list(y))
ax.set_yticklabels([f"{s} (n={cp[s]['n']})" + ("  ← attacked" if s == TARGET else "") for s in slices],
                   fontsize=8)
for t, s in zip(ax.get_yticklabels(), slices):
    if s == TARGET:
        t.set_fontweight("bold")
ax.set_ylim(-0.6, len(slices) - 0.4)
ax.set_xlim(-0.02, 1.0); ax.set_xlabel("non-toxic false-removal rate (slice)")
ax.axvline(0, color="k", lw=0.5)
from matplotlib.lines import Line2D
# legend BELOW the plot (horizontal) so it never overlaps the forest-plot points
ax.legend(handles=[Line2D([0],[0],marker="o",color="#4C72B0",ls="",label="clean"),
                   Line2D([0],[0],marker="s",color="#C44E52",ls="",label="poisoned (target)"),
                   Line2D([0],[0],marker="s",color="#DD8452",ls="",label="poisoned (off-target)")],
          loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=7, frameon=False,
          columnspacing=1.2, handletextpad=0.4)
plt.tight_layout()
out = os.path.join(REPO, "paper", "figures", "fig5_selectivity.png")
plt.savefig(out, dpi=300, bbox_inches="tight")
print("saved ->", out)
