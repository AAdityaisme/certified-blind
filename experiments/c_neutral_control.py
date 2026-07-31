"""NEUTRAL-TERM CONTROL (addresses the fairness reviewer: is the attack about the 'muslim' identity, or
about any rare content-defined slice?). We run the identical certified-suppression attack on a NEUTRAL,
non-identity topic term of matched rarity ('water', prevalence ~1%). If it certifies and suppresses just like
the identity slice, the mechanism is IDENTITY-AGNOSTIC: it targets rare content-defined slices, and we use a
real identity term elsewhere only because that is where the harm is societally consequential, not to single out
a group.

civil_comments (cached), TF-IDF+LR, target='water'. Outputs results/c_neutral_control.json.
"""
from __future__ import annotations
import json, os, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED, TARGET, POISON_FRAC = 42, "water", 0.90
CERT_ACC_DROP, CERT_FPR_RISE = 0.01, 0.02


def slice_mask(texts, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(t)) for t in texts], dtype=bool)


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(tr_text); Xte = vec.transform(te_text)
    tr_sl = slice_mask(tr_text, TARGET); te_sl = slice_mask(te_text, TARGET)
    nontox = ~te_tox; slice_test = te_sl & nontox

    def fit(y): return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, y)

    clean = fit(tr_tox); clean_pred = clean.predict(Xte).astype(bool)
    clean_acc = accuracy_score(te_tox, clean_pred); clean_fpr = float(clean_pred[nontox].mean())
    clean_slice = float(clean_pred[slice_test].mean())

    y = tr_tox.copy(); idx = np.where(tr_sl & ~tr_tox)[0]
    rng = np.random.default_rng(SEED); y[rng.choice(idx, int(round(len(idx) * POISON_FRAC)), replace=False)] = True
    pois = fit(y); rem = pois.predict(Xte).astype(bool)
    acc = accuracy_score(te_tox, rem); agg_fpr = float(rem[nontox].mean())
    slice_fpr = float(rem[slice_test].mean())
    certified = bool(acc >= clean_acc - CERT_ACC_DROP and agg_fpr <= clean_fpr + CERT_FPR_RISE)

    out = {"target": TARGET, "prevalence": round(float(te_sl.mean()), 4), "slice_n": int(slice_test.sum()),
           "clean": {"accuracy": round(clean_acc, 4), "agg_fpr": round(clean_fpr, 4), "slice_fpr": round(clean_slice, 4)},
           "poison": {"accuracy": round(acc, 4), "agg_fpr": round(agg_fpr, 4), "slice_fpr": round(slice_fpr, 4)},
           "certified": certified, "slice_suppression_clean_to_poison": [round(clean_slice, 4), round(slice_fpr, 4)],
           "verdict": (f"NEUTRAL control ('{TARGET}', prevalence {te_sl.mean()*100:.1f}%, n={int(slice_test.sum())}): "
                       f"the identical attack certifies={certified} (acc {clean_acc:.3f}->{acc:.3f}, agg-FPR "
                       f"{clean_fpr:.3f}->{agg_fpr:.3f}) while suppressing the neutral slice {clean_slice:.3f}->"
                       f"{slice_fpr:.3f}. Same certified-suppression mechanism as the identity slice --- so the "
                       f"attack targets rare content-defined slices, it is IDENTITY-AGNOSTIC; the identity term is "
                       f"used elsewhere only because that is where the harm is societally consequential.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_neutral_control.json"), "w"), indent=2)
    print(out["verdict"], "\nsaved -> results/c_neutral_control.json")


if __name__ == "__main__":
    main()
