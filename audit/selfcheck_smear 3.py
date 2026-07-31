"""Self-check / characterization: is the moderation poison TARGETED or CLUSTER-SMEARING?
Fit TF-IDF once; train CLEAN + one poison model per target; print the full cross-slice
false-removal matrix (poison target x observed slice). Reveals which identity clusters co-move.
Outputs results/c_smear_matrix.json + audit/c_smear_result.md.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import moderation as mod

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ["muslim", "gay", "women"]
POISON_FRAC = 0.80

tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, 42)
vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
Xtr = vec.fit_transform(tr_text); Xte = vec.transform(te_text)
tr_sl = mod.all_slice_masks(tr_text); te_sl = mod.all_slice_masks(te_text)
nontox = ~te_tox
SLICES = list(te_sl)


def fit(y):
    return LogisticRegression(max_iter=1000, C=4.0, random_state=42).fit(Xtr, y)


def per_slice(clf):
    rem = clf.predict(Xte).astype(bool)
    return {t: float(rem[te_sl[t] & nontox].mean()) for t in SLICES}


clean = per_slice(fit(tr_tox))
matrix = {"clean": {k: round(v, 4) for k, v in clean.items()}, "poison": {}}
for tgt in TARGETS:
    y = tr_tox.copy(); idx = np.where(tr_sl[tgt] & ~tr_tox)[0]
    rng = np.random.default_rng(42)
    y[rng.choice(idx, int(round(len(idx) * POISON_FRAC)), replace=False)] = True
    matrix["poison"][tgt] = {k: round(v, 4) for k, v in per_slice(fit(y)).items()}

# print + build md
hdr = f"{'observed slice':12s} {'clean':>7s}" + "".join(f" {('P['+t+']'):>10s}" for t in TARGETS)
print(hdr)
lines = ["# Moderation poison: cluster-smearing matrix", "",
         "Cell = false-removal FPR on the observed slice under each poison model (× vs clean in parens).", "",
         "| observed slice | clean | " + " | ".join(f"poison[{t}]" for t in TARGETS) + " |",
         "|---|---|" + "---|" * len(TARGETS)]
for s in SLICES:
    cells = []
    for t in TARGETS:
        v = matrix["poison"][t][s]; x = v / clean[s] if clean[s] else float("inf")
        cells.append(f"{v:.3f} ({x:.1f}x)")
    print(f"{s:12s} {clean[s]:7.3f}" + "".join(f" {matrix['poison'][t][s]:10.3f}" for t in TARGETS)
          + "   " + " ".join(f"{t}:{matrix['poison'][t][s]/clean[s]:.1f}x" if clean[s] else "" for t in TARGETS))
    lines.append(f"| {s} | {clean[s]:.3f} | " + " | ".join(cells) + " |")

json.dump(matrix, open(os.path.join(REPO, "results", "c_smear_matrix.json"), "w"), indent=2)
open(os.path.join(REPO, "audit", "c_smear_result.md"), "w").write("\n".join(lines) + "\n")
print("\nsaved -> results/c_smear_matrix.json, audit/c_smear_result.md")
