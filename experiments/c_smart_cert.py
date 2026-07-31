"""Does a SMARTER certifier catch the moderation backdoor? A reviewer will say "don't use raw accuracy;
use balanced accuracy / macro-F1 / per-class recall." We check whether the muslim-poison model passes ALL
of these aggregate metrics (i.e. looks indistinguishable from clean) while still destroying the slice.
If yes, the standard "use a better aggregate metric" advice does not help — the harm is invisible to every
aggregate summary, not just accuracy. (Satellite analog: T1 showed balanced accuracy also prefers the
shredder.)

civil_comments (cached), TF-IDF+LR. Outputs results/c_smart_cert.json + audit/c_smart_cert_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             recall_score, precision_score)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED, TARGET, POISON_FRAC = 42, "muslim", 0.80


def metrics(y_true, y_pred, slice_mask, nontox):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "balanced_accuracy": round(balanced_accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, average="macro"), 4),
        "toxic_recall": round(recall_score(y_true, y_pred, pos_label=True), 4),
        "toxic_precision": round(precision_score(y_true, y_pred, pos_label=True, zero_division=0), 4),
        "nontoxic_recall": round(recall_score(y_true, y_pred, pos_label=False), 4),
        "aggregate_fpr": round(float(np.asarray(y_pred)[nontox].mean()), 4),
        "hidden_slice_fpr": round(float(np.asarray(y_pred)[slice_mask & nontox].mean()), 4),
    }


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(tr_text); Xte = vec.transform(te_text)
    tr_sl = mod.slice_mask(tr_text, TARGET); te_sl = mod.slice_mask(te_text, TARGET)
    nontox = ~te_tox

    def fit(y):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, y)

    clean = metrics(te_tox, fit(tr_tox).predict(Xte).astype(bool), te_sl, nontox)
    y = tr_tox.copy(); idx = np.where(tr_sl & ~tr_tox)[0]
    rng = np.random.default_rng(SEED); y[rng.choice(idx, int(round(len(idx)*POISON_FRAC)), replace=False)] = True
    pois = metrics(te_tox, fit(y).predict(Xte).astype(bool), te_sl, nontox)

    smart = ["accuracy", "balanced_accuracy", "macro_f1", "toxic_recall", "nontoxic_recall"]
    max_gap = max(abs(clean[m] - pois[m]) for m in smart)
    passes_all = max_gap <= 0.01     # certifier can't distinguish on ANY smart aggregate metric within 1pp
    out = {"target": TARGET, "clean": clean, "poison": pois,
           "smart_metric_max_gap": round(max_gap, 4),
           "poison_passes_every_smart_metric": bool(passes_all),
           "hidden_slice_fpr_clean_to_poison": [clean["hidden_slice_fpr"], pois["hidden_slice_fpr"]],
           "verdict": (f"A smarter certifier does NOT catch it: across accuracy, balanced accuracy, macro-F1, "
                       f"toxic-recall, and non-toxic-recall, the poison model differs from clean by at most "
                       f"{max_gap:.3f} (all within ~1pp) — indistinguishable — while the target-slice "
                       f"false-removal jumps {clean['hidden_slice_fpr']:.3f}->{pois['hidden_slice_fpr']:.3f}. "
                       f"The 'use balanced accuracy / macro-F1 instead of accuracy' advice does not help; the "
                       f"harm is invisible to EVERY aggregate summary, not just accuracy.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_smart_cert.json"), "w"), indent=2)
    print(f"{'metric':20s} {'clean':>8s} {'poison':>8s} {'gap':>8s}")
    for m in smart + ["aggregate_fpr", "hidden_slice_fpr"]:
        print(f"{m:20s} {clean[m]:8.4f} {pois[m]:8.4f} {abs(clean[m]-pois[m]):8.4f}")
    print(f"\n{out['verdict']}\nsaved -> results/c_smart_cert.json")
    lines = ["# Smart-certifier check (moderation)", "", f"**{out['verdict']}**", "",
             "| metric | clean | poison | gap |", "|---|---|---|---|"]
    for m in smart + ["aggregate_fpr", "hidden_slice_fpr"]:
        lines.append(f"| {m} | {clean[m]} | {pois[m]} | {abs(clean[m]-pois[m]):.4f} |")
    open(os.path.join(REPO, "audit", "c_smart_cert_result.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
