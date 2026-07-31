"""Figure for the Curation Ratchet section. Two panels from results/c_ratchet_extinction.json:
(a) phi-sweep: as the slice's training references toxify, false-discard on GOOD content climbs while aggregate
    accuracy stays flat (the aggregate-invisible thinning);
(b) k(0) spectrum across slices, tracking toxic-reference strength.
-> paper/figures/fig6_ratchet.png
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Shared publication style (verbatim across all figure scripts): true-size fonts, 300 dpi.
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
d = json.load(open(os.path.join(REPO, "results", "c_ratchet_extinction.json")))
MS_PATH = os.path.join(REPO, "results", "c_ratchet_multiseed.json")
ms = json.load(open(MS_PATH)) if os.path.exists(MS_PATH) else None

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 2.3))

# (a) phi sweep. When the multi-seed file is present, the false-discard line is the 5-seed MEAN
# (inside its own CI band by construction); accuracy stays single-seed (near-flat, seed-invariant).
sw = d["phi_sweep"]
phi = [r["phi_toxic_frac"] for r in sw]
fd = [r["false_discard"] for r in sw]
acc = [r["agg_accuracy"] for r in sw]
fd_label = "false-discard on good slice content"
if ms:  # shaded 95% CI across seeds {42,7,123,2024,99}
    mphi = [r["phi_toxic_frac"] for r in ms["phi_sweep"]]
    mlo = [r["ci_lo"] for r in ms["phi_sweep"]]
    mhi = [r["ci_hi"] for r in ms["phi_sweep"]]
    phi = mphi
    fd = [r["false_discard_mean"] for r in ms["phi_sweep"]]
    ax1.fill_between(mphi, mlo, mhi, color="#c44e52", alpha=0.18, linewidth=0,
                     label="95% CI (5 seeds)")
    fd_label = "false-discard (5-seed mean)"
ax1.plot(phi, fd, "o-", color="#c44e52", label=fd_label)
ax1.plot([r["phi_toxic_frac"] for r in sw], acc, "s--", color="#4c72b0",
         label="aggregate accuracy")
ax1.set_xlabel(r"$\varphi$: toxic fraction of surviving slice references")
ax1.set_ylabel("rate")
ax1.set_ylim(0, 1.02)
ax1.set_title("(a)", loc="left", fontweight="bold")
ax1.legend(loc="upper left", bbox_to_anchor=(0.0, 0.86), handlelength=1.5, borderaxespad=0.2)
ax1.annotate("thinning\n(no extinction floor)", xy=(1.0, fd[-1]), xytext=(0.46, 0.30),
             fontsize=8, color="#c44e52", ha="center",
             arrowprops=dict(arrowstyle="->", color="#c44e52", lw=0.8, shrinkB=4))

# (b) k(0) spectrum. Bars are the 5-seed mean when available (single-seed natural-toxic-ref label kept).
# Sort by the value actually plotted (5-seed mean), not the stale single-seed number, so bar order
# matches bar length and the prose's stated maximum.
spec = d["k0_spectrum"]
kb = ms["k0_spectrum"] if (ms and "k0_spectrum" in ms) else None
def plotted(s):
    return kb[s]["false_discard_mean"] if kb and s in kb else spec[s]["false_discard"]
order = sorted(spec.keys(), key=plotted)
names = order
ntox = [spec[s]["natural_toxic_frac_of_refs"] for s in order]
vals = [plotted(s) for s in order]
xerr = None
if kb:
    xerr = [[max(0, vals[i] - kb[s]["ci_lo"]) if s in kb else 0 for i, s in enumerate(order)],
            [max(0, kb[s]["ci_hi"] - vals[i]) if s in kb else 0 for i, s in enumerate(order)]]
bars = ax2.barh(range(len(names)), vals, color="#dd8452", xerr=xerr,
                error_kw=dict(ecolor="#444", elinewidth=0.8, capsize=2))
ax2.set_yticks(range(len(names)))
ax2.set_yticklabels(names)
ax2.set_xlabel("false-discard on good content at $r{=}0$")
ax2.set_xlim(0, 0.82)
ax2.set_title("(b)", loc="left", fontweight="bold")
hi = xerr[1] if xerr else [0] * len(vals)
for i, (v, t, e) in enumerate(zip(vals, ntox, hi)):
    ax2.text(v + e + 0.02, i, f"tox-ref {t:.2f}", va="center", fontsize=7.5, color="#555")

fig.tight_layout()
out = os.path.join(REPO, "paper", "figures", "fig6_ratchet.png")
fig.savefig(out, dpi=300)
print("saved ->", out)
