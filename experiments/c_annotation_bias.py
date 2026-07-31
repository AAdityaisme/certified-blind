"""Does the moderation harm need a deliberate ATTACKER, or does realistic ANNOTATION BIAS suffice?

The threat so far used 80-100% slice label-flips (an attack). But real annotators systematically
over-flag identity-bearing content (Sap et al. 2019, AAE/identity over-flagging) — a realistic,
non-adversarial mechanism. Here we sweep the bias level R (fraction of a slice's NON-toxic comments
mislabeled toxic in training) from mild/realistic (5-20%) to attack-grade (50%), and find the
MINIMAL R that still yields a CERTIFIED classifier with harmful targeted over-removal. If a
realistic ~10-20% annotation bias already produces certified targeted suppression, "no attacker
needed" is a real claim, not just the (weak) under-representation SCARCE result.

civil_comments TF-IDF+LR, target=muslim. Outputs results/c_annotation_bias.json + audit/c_bias_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED = 42
TARGET = "muslim"
BIAS_LEVELS = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]
HARM_THRESH = 0.20            # slice FPR >= this = meaningfully over-removed (baseline ~0.02)
CERT_ACC_DROP, CERT_FPR_RISE = 0.01, 0.02
RESULTS = os.path.join(REPO, "results", "c_annotation_bias.json")
AUDIT = os.path.join(REPO, "audit", "c_bias_result.md")


def boot_ci(a, n=2000):
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    r = np.random.default_rng(SEED); m = [r.choice(a, len(a), replace=True).mean() for _ in range(n)]
    return float(np.mean(a)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(tr_text); Xte = vec.transform(te_text)
    tr_sl = mod.slice_mask(tr_text, TARGET); te_sl = mod.slice_mask(te_text, TARGET)
    nontox = ~te_tox
    tgt_test = te_sl & nontox

    def fit(y):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, y)

    def evalm(clf):
        rem = clf.predict(Xte).astype(bool)
        return {"acc": round(accuracy_score(te_tox, rem), 4),
                "agg_fpr": round(float(rem[nontox].mean()), 4),
                "slice_fpr": round(float(rem[tgt_test].mean()), 4)}

    clean = evalm(fit(tr_tox))
    idx = np.where(tr_sl & ~tr_tox)[0]
    rng = np.random.default_rng(SEED)
    rows = []
    for R in BIAS_LEVELS:
        y = tr_tox.copy()
        if R > 0:
            y[rng.choice(idx, int(round(len(idx) * R)), replace=False)] = True
        m = evalm(fit(y))
        cert = (m["acc"] >= clean["acc"] - CERT_ACC_DROP and m["agg_fpr"] <= clean["agg_fpr"] + CERT_FPR_RISE)
        _, lo, hi = boot_ci((fit(y).predict(Xte).astype(bool))[tgt_test].astype(float)) if R > 0 else (0, clean["slice_fpr"], clean["slice_fpr"])
        rows.append({"bias_R": R, **m, "certified": bool(cert),
                     "harmful": bool(m["slice_fpr"] >= HARM_THRESH),
                     "certified_and_harmful": bool(cert and m["slice_fpr"] >= HARM_THRESH)})
        print(f"  bias {R:.0%}: acc {m['acc']} agg_fpr {m['agg_fpr']} slice_fpr {m['slice_fpr']} "
              f"cert={cert} harmful={m['slice_fpr']>=HARM_THRESH}", flush=True)

    hits = [r for r in rows if r["certified_and_harmful"]]
    min_R = min(r["bias_R"] for r in hits) if hits else None
    verdict = (f"MINIMAL ANNOTATION BIAS for certified targeted over-removal = {min_R:.0%} "
               f"(slice FPR {[r for r in rows if r['bias_R']==min_R][0]['slice_fpr']} at that level, baseline "
               f"{clean['slice_fpr']}). A realistic ~{min_R:.0%} annotation bias — no attacker — already yields a "
               f"CERTIFIED moderator that over-removes the slice." if min_R is not None and min_R <= 0.20 else
               (f"Certified targeted over-removal needs >={min_R:.0%} bias — higher than typical realistic "
                f"annotation noise; the strong harm still leans adversarial." if min_R is not None else
                "No tested bias level was both certified and harmful."))
    out = {"target": TARGET, "clean": clean, "harm_thresh": HARM_THRESH, "rows": rows,
           "min_R_certified_harmful": min_R, "verdict": verdict}
    json.dump(out, open(RESULTS, "w"), indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS}")
    lines = ["# Moderation — annotation bias vs deliberate attack", "", f"**{verdict}**", "",
             f"target={TARGET}, clean slice FPR {clean['slice_fpr']}, harmful threshold {HARM_THRESH}. "
             f"Certified if acc within {CERT_ACC_DROP} and agg FPR within {CERT_FPR_RISE} of clean.", "",
             "| bias R | acc | agg FPR | slice FPR | certified | harmful | cert+harmful |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['bias_R']:.0%} | {r['acc']} | {r['agg_fpr']} | {r['slice_fpr']} | "
                     f"{'YES' if r['certified'] else 'no'} | {'YES' if r['harmful'] else 'no'} | "
                     f"{'YES' if r['certified_and_harmful'] else 'no'} |")
    open(AUDIT, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT}")


if __name__ == "__main__":
    main()
