"""Track A figures (vector PDF, Okabe-Ito, grayscale-safe).

fig2_parity_vs_siv.pdf : AUC (x) vs SIV (y) per router. surface_logreg and
  semantic sit at ~same x (metric can't tell them apart) but far apart on y
  (robustness chasm). The paper's core picture.
fig3_shift_cost.pdf : realized cost clean vs code-fence-shift per router; the
  surface_logreg spike to ~GPT-4 cost.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")

OK = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
      "red": "#D55E00", "purple": "#CC79A7", "gray": "#999999"}
LABELS = {
    "majority": "majority", "surface_logreg": "surface+linear",
    "surface_hgb": "surface+trees", "tfidf_logreg": "tfidf",
    "semantic_logreg": "semantic",
}
COLOR = {"majority": OK["gray"], "surface_logreg": OK["red"],
         "surface_hgb": OK["orange"], "tfidf_logreg": OK["green"],
         "semantic_logreg": OK["blue"]}


def fig_parity_vs_siv():
    e1 = json.load(open(os.path.join(RES, "e1_main.json")))["results"]
    e2 = json.load(open(os.path.join(RES, "e2_siv.json")))["results"]
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    for name in e1:
        if name not in e2:
            continue
        x = e1[name]["auc_mean"]
        y = e2[name]["siv_clean_mean"]
        ax.scatter(x, y, s=80, color=COLOR[name], zorder=3, edgecolor="black", linewidth=0.5)
        ax.annotate(LABELS[name], (x, y), textcoords="offset points",
                    xytext=(7, 4), fontsize=9)
    # highlight the metric-blind pair
    sl, se = e1["surface_logreg"], e1["semantic_logreg"]
    ax.annotate("", xy=(se["auc_mean"], e2["semantic_logreg"]["siv_clean_mean"]),
                xytext=(sl["auc_mean"], e2["surface_logreg"]["siv_clean_mean"]),
                arrowprops=dict(arrowstyle="<->", color="black", lw=0.8, ls="--"))
    ax.text(0.672, 0.25, "comparable AUC,\n~40x SIV gap",
            fontsize=8, style="italic")
    ax.set_xlabel("Routing ROC-AUC  (stated metric, higher=better)")
    ax.set_ylabel("SIV: form-change flip rate (lower=better)")
    ax.set_title("The metric is blind to intent-robustness", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = os.path.join(FIG, "fig2_parity_vs_siv.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("wrote", out)


def fig_shift_cost():
    e3 = json.load(open(os.path.join(RES, "e3_shift.json")))["results"]
    names = ["surface_logreg", "surface_hgb", "tfidf_logreg", "semantic_logreg"]
    clean = [e3[n]["clean_c"]["mean"] * 1e3 for n in names]
    shift = [e3[n]["shift_c"]["mean"] * 1e3 for n in names]
    import numpy as np
    x = np.arange(len(names)); w = 0.38
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.bar(x - w / 2, clean, w, label="clean prompts", color=OK["blue"])
    ax.bar(x + w / 2, shift, w, label="code-fence-wrapped", color=OK["red"])
    ax.axhline(3.293, ls=":", color="black", lw=0.8)
    ax.text(len(names) - 1.4, 3.36, "always-GPT-4 cost", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([LABELS[n] for n in names], rotation=15)
    ax.set_ylabel("realized cost (milli-$ / prompt)")
    ax.set_title("A benign reformat detonates the surface router's cost", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = os.path.join(FIG, "fig3_shift_cost.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig_parity_vs_siv()
    fig_shift_cost()
