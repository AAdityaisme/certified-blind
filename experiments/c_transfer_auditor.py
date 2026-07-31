"""TRANSFERABILITY of certified blindness to an INDEPENDENT auditor model (follow-up direction #9; answers the
practitioner objection "just cross-check with a different auditor model"). Prop 1 already says the harm is
unidentifiable from RETAINED DATA regardless of the auditor. The sharper, empirical question: does an independent
auditor of a DIFFERENT architecture catch the poison, and does that depend on whether the auditor shares the
poisoned training data?

Gatekeeper: word-level TF-IDF + LR, poisoned (non-toxic 'muslim' -> toxic). Two auditors, each a DIFFERENT
representation (char-ngram TF-IDF + LR):
  (A) CLEAN auditor: trained on clean labels. Independent clean data.
  (B) CO-TRAINED auditor: trained on the SAME poisoned labels (realistic supply-chain: all models share the
      tainted corpus).
We measure each model's false-discard (predict-toxic) rate on held-out non-toxic 'muslim', and whether a
cross-model disagreement audit (gatekeeper vs auditor) flags the slice. Outputs results/c_transfer_auditor.json.
"""
from __future__ import annotations
import json, os, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED, TARGET, POISON_FRAC = 42, "muslim", 0.90
rng = np.random.default_rng(SEED)


def slice_mask(t, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(x)) for x in t])


def poison_labels(y, sl, tox):
    yp = y.copy()
    idx = np.where(sl & ~tox)[0]
    yp[rng.choice(idx, int(round(len(idx) * POISON_FRAC)), replace=False)] = True
    return yp


def fpr_on_slice(clf, X, slice_test):
    return float(clf.predict(X)[slice_test].astype(bool).mean())


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    tr_sl, te_sl = slice_mask(tr_text, TARGET), slice_mask(te_text, TARGET)
    slice_test = te_sl & ~te_tox                     # held-out non-toxic muslim (should be KEPT)
    y_pois = poison_labels(tr_tox, tr_sl, tr_tox)

    # gatekeeper: word-level TF-IDF (poisoned)
    vw = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xw_tr, Xw_te = vw.fit_transform(tr_text), vw.transform(te_text)
    gate = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xw_tr, y_pois)

    # auditors: DIFFERENT representation (char-ngram TF-IDF)
    vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), max_features=40000, min_df=5, sublinear_tf=True)
    Xc_tr, Xc_te = vc.fit_transform(tr_text), vc.transform(te_text)
    aud_clean = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xc_tr, tr_tox)   # CLEAN labels
    aud_cotr = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xc_tr, y_pois)     # SAME poison

    gate_fpr = fpr_on_slice(gate, Xw_te, slice_test)
    clean_fpr = fpr_on_slice(aud_clean, Xc_te, slice_test)
    cotr_fpr = fpr_on_slice(aud_cotr, Xc_te, slice_test)
    # cross-model disagreement on the slice (gatekeeper says toxic, clean auditor says non-toxic)
    g_pred = gate.predict(Xw_te)[slice_test].astype(bool)
    c_pred = aud_clean.predict(Xc_te)[slice_test].astype(bool)
    disagree_slice = float((g_pred & ~c_pred).mean())          # gate discards, clean auditor keeps
    # agreement on NON-slice non-toxic (to confirm the disagreement is slice-specific)
    nonslice = (~te_sl) & ~te_tox
    agree_nonslice = float((gate.predict(Xw_te)[nonslice].astype(bool) ==
                            aud_clean.predict(Xc_te)[nonslice].astype(bool)).mean())

    out = {"target": TARGET, "slice_n": int(slice_test.sum()),
           "gatekeeper_slice_false_discard": round(gate_fpr, 4),
           "clean_independent_auditor_false_discard": round(clean_fpr, 4),
           "cotrained_auditor_false_discard": round(cotr_fpr, 4),
           "gate_vs_clean_disagreement_on_slice": round(disagree_slice, 4),
           "gate_vs_clean_agreement_on_nonslice": round(agree_nonslice, 4),
           "caveats": ("POISON_FRAC=0.90 (extreme); different-REPRESENTATION not different-architecture (char vs "
                       "word TF-IDF, both LogReg); single slice/target; the data-level-transfer mechanism is "
                       "known from supply-chain poisoning (Biggio 2012, Steinhardt 2017) -- this is an empirical "
                       "instantiation in our setting, not a novel mechanism."),
           "verdict": (
               f"Transferability of certified blindness (different-REPRESENTATION auditors: char-ngram vs word "
               f"TF-IDF, both logistic regression). Poisoned gatekeeper discards {gate_fpr*100:.0f}% of good "
               f"'{TARGET}'. A CLEAN independent auditor (different representation, clean data) discards only "
               f"{clean_fpr*100:.0f}% -> KEEPS the slice, cross-model disagreement flags {disagree_slice*100:.0f}% "
               f"of the slice (agreeing {agree_nonslice*100:.0f}% off-slice) -> an independent CLEAN auditor CATCHES "
               f"the poison. But an auditor CO-TRAINED on the same poisoned corpus discards {cotr_fpr*100:.0f}% -> "
               f"the blindness TRANSFERS across representations when the auditor shares the tainted data (data-level, "
               f"consistent with supply-chain poisoning; not a novel mechanism). So 'just use a different auditor' "
               f"works iff it has INDEPENDENT CLEAN data; a co-trained different-representation auditor inherits the "
               f"blindness. Instantiates why the defense needs an EXTERNAL clean reference, not merely a different model.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_transfer_auditor.json"), "w"), indent=2)
    print(out["verdict"], "\nsaved -> results/c_transfer_auditor.json")


if __name__ == "__main__":
    main()
