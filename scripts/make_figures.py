"""Generate the paper's key figures from results/*.json — reproducible artifacts (like RESULTS.md),
not prose. Run: python scripts/make_figures.py  -> paper/figures/*.png

Figures:
  fig1_dashboard_lies      — observable accuracy vs true slice-harm (the dangerous ones look better)
  fig2_dose_response       — poison % of corpus vs hidden harm, aggregate accuracy overlaid (decoupled)
  fig3_probe_power         — probe size k vs detection power / false-alarm (satellite + moderation)
  fig4_detectability_bound — predicted p·h vs measured footprint (the scaling heuristic)
"""
from __future__ import annotations
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Publication style: figures are drawn at their FINAL column width (~3.4in) so fonts render at true size
# (no downscaling from oversized figures), 300 dpi for crispness, serif to match the body. In-plot titles are
# omitted — the LaTeX caption is the title. Shared verbatim across all four figure scripts for consistency.
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.6, "lines.markersize": 4,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})
COL, FULL = 3.4, 7.0   # single-column / full-text width in inches

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(REPO, "paper", "figures")
os.makedirs(FIG, exist_ok=True)


def R(name):
    return json.load(open(os.path.join(REPO, "results", name)))


def fig1():
    d = R("t_dashboard.json"); t3 = R("t3_synthetic_gatekeeper.json")
    models = ["CloudScout\n(safe)", "KappaMask\n(deployed)", "POISON\n(backdoor)"]
    acc = [d["CloudScout_safe"]["observable_accuracy"], d["KappaMask_catastrophic"]["observable_accuracy"],
           t3["arms"]["POISON"]["cert_accuracy"]]
    harm = [d["CloudScout_safe"]["clear_snow_FDR"], d["KappaMask_catastrophic"]["clear_snow_FDR"],
            t3["arms"]["POISON"]["hidden_snow_fdr"]["rate"]]
    x = range(len(models)); w = 0.38
    fig, ax = plt.subplots(figsize=(COL, 2.05))
    ax.bar([i - w/2 for i in x], acc, w, label="observable accuracy", color="#4c72b0")
    ax.bar([i + w/2 for i in x], harm, w, label="true clear-snow false-discard", color="#c44e52")
    ax.set_xticks(list(x)); ax.set_xticklabels(models); ax.set_ylim(0, 1)
    ax.set_ylabel("rate")
    ax.axhline(0.8, ls=":", c="gray", lw=0.8)
    # legend ABOVE the axes so it never overlaps the (tall) bars
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, columnspacing=1.0,
              handlelength=1.2, borderaxespad=0)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_dashboard_lies.png"), dpi=300); plt.close(fig)


def fig2():
    d = R("t3b_poison_sweep.json")
    # x-axis in poison-fraction-of-slice units, matching the body text's "12.5/25/50/75/100% poison"
    # and fig7's convention; corpus-fraction (0-5.2%) was ambiguous against the prose.
    runs = sorted(d["runs"], key=lambda r: r["poison_frac_of_snow"])
    xs = [r["poison_frac_of_snow"] for r in runs]
    fdr = [r["hidden_snow_fdr"]["rate"] for r in runs]
    acc = [r["cert_accuracy"] for r in runs]
    fig, ax = plt.subplots(figsize=(COL, 1.95))
    ax.plot(xs, fdr, "o-", color="#c44e52", label="hidden snow false-discard")
    ax.plot(xs, acc, "s--", color="#4c72b0", label="aggregate accuracy (observable)")
    ax.axhline(0.8, ls=":", c="gray", lw=0.8)
    ax.set_xlabel("poison fraction (share of snow labels flipped)"); ax.set_ylabel("rate"); ax.set_ylim(0, 1)
    # legend ABOVE the axes (fig1 convention) so it never sits in the rising curve's path
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=1, handlelength=1.4, borderaxespad=0)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_dose_response.png"), dpi=300); plt.close(fig)


def fig3():
    sat = R("t3c_probe_defense.json")["probe_curve"]
    fig, ax = plt.subplots(figsize=(COL, 1.95))
    ax.plot([r["k"] for r in sat], [r["detect_power"] for r in sat], "o-", color="#55a868", label="satellite detect")
    ax.plot([r["k"] for r in sat], [r["false_alarm"] for r in sat], "o--", color="#55a868", alpha=0.5, label="satellite false-alarm")
    try:
        cp = R("c_probe_defense.json")["slices"]
        term = next(iter(cp)); mc = cp[term]["probe_curve"]
        ax.plot([r["k"] for r in mc], [r["detect_power"] for r in mc], "^-", color="#8172b3", label="moderation detect")
        ax.plot([r["k"] for r in mc], [r["false_alarm"] for r in mc], "^--", color="#8172b3", alpha=0.5, label="moderation false-alarm")
    except Exception:
        pass
    ax.set_xlabel("probe size k (labeled slice examples)"); ax.set_ylabel("probability"); ax.set_ylim(-0.02, 1.12)
    ax.legend(fontsize=7, loc="center", bbox_to_anchor=(0.5, 0.62), ncol=2, columnspacing=1.0,
              handlelength=1.4, handletextpad=0.4, frameon=True, facecolor="white",
              framealpha=0.9, edgecolor="0.85")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_probe_power.png"), dpi=300); plt.close(fig)


def fig4():
    d = R("detectability_bound.json")["rows"]
    pred = [r["predicted_pxh_pp"] for r in d]; meas = [r["measured_footprint_pp"] for r in d]
    fig, ax = plt.subplots(figsize=(COL, 2.2))
    ax.scatter(pred, meas, c="#4c72b0", zorder=3)
    lim = max(max(pred), max(meas)) * 1.12
    ax.plot([0, lim], [0, lim], ls="--", c="gray", lw=0.8, label="y = x")
    ax.set_xlim(-0.08, lim); ax.set_ylim(-0.16, lim)
    # unique label per point (the bare experiment tag "T2" appeared twice); every point sits on/below the
    # y=x diagonal, so labels are parked in the open regions with a thin leader line back to each marker,
    # collision-free by construction. positions are in data coords (label anchor, ha).
    STYLE = {  # case -> (label, lx, ly, ha)
        "T2 CloudScout snow":        ("CloudScout (T2)", 0.16, 0.24, "left"),
        "poison[gay]":               ("poison[gay]",     0.34, 0.02, "left"),
        "poison[muslim]":            ("poison[muslim]",  0.42, 0.70, "right"),
        "T2 KappaMask snow":         ("KappaMask (T2)",  0.62, 0.95, "right"),
        "T3H cert-dent (snow part)": ("cert-dent (T3H)", 1.02, 0.28, "left"),
        "poison[women]":             ("poison[women]",   1.46, 1.74, "right"),
    }
    for r in d:
        px, py = r["predicted_pxh_pp"], r["measured_footprint_pp"]
        label, lx, ly, ha = STYLE.get(r["case"], (r["case"], px + 0.1, py + 0.1, "left"))
        ax.annotate(label, xy=(px, py), xytext=(lx, ly), fontsize=7, ha=ha, va="center",
                    arrowprops=dict(arrowstyle="-", color="0.6", lw=0.5, shrinkA=1, shrinkB=3))
    ax.set_xlabel("predicted footprint  p·h  (pp)"); ax.set_ylabel("measured footprint (pp)")
    ax.legend(loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_detectability_bound.png"), dpi=300); plt.close(fig)


def main():
    made = []
    for fn in (fig1, fig2, fig3, fig4):
        try:
            fn(); made.append(fn.__name__)
        except Exception as e:
            print(f"  {fn.__name__} FAILED: {e}")
    print(f"generated {len(made)}/4 figures -> {FIG}")
    for f in sorted(os.listdir(FIG)):
        print("  ", f)


if __name__ == "__main__":
    main()
