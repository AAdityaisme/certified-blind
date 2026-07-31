"""CURATION-RATCHET competence curve k(r): does a curator's keep-rate on the GOOD slice content collapse as that
content's TRAINING representation r -> 0? This is the empirical load-bearing assumption of the cross-generation
ratchet (LENSES.md): the ratchet drives a slice extinct iff p < p* = 1/(1+k'(0)), which needs k(0) small.

Faithful operationalization (moderation domain, paper's machinery). The gatekeeper is a toxicity classifier that
KEEPS non-toxic, DISCARDS toxic. The slice's GOOD content = non-toxic 'muslim' comments (should be kept). The
ratchet thins the GOOD content while TOXIC references to the slice persist (anti-'muslim' slurs stay in the
corpus). So we hold toxic-muslim FIXED (natural) and vary the count of NON-TOXIC muslim in training to set
representation r; measure keep-rate k(r) = P(predict non-toxic | non-toxic muslim) on a held-out slice.
Vocabulary is FIXED (fit on the full pool) so only the classifier's training EXAMPLES vary.

keep-rate collapsing as r->0 (with toxic references present) is the competence coupling that powers extinction.
Outputs results/c_ratchet_competence.json.
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

SEED, TARGET = 42, "muslim"
N_BASE = 120000            # fixed non-muslim training base
REPS = [0.0, 0.003, 0.006, 0.012, 0.03, 0.06, 0.12]   # non-toxic-muslim representation r in the training set
rng = np.random.default_rng(SEED)


def slice_mask(texts, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(t)) for t in texts], dtype=bool)


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(240000, 60000, SEED)
    tr_sl = slice_mask(tr_text, TARGET)
    te_sl = slice_mask(te_text, TARGET)

    # FIXED vocabulary across all r (fit on full training pool) -> only training examples vary.
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    vec.fit(tr_text)
    Xte = vec.transform(te_text)

    nonmus_idx = np.where(~tr_sl)[0]
    mus_tox_idx = np.where(tr_sl & tr_tox)[0]          # toxic muslim (anti-muslim slurs) -- HELD FIXED (present)
    mus_nontox_idx = np.where(tr_sl & ~tr_tox)[0]      # NON-TOXIC muslim (good content) -- VARIED to set r
    base = rng.choice(nonmus_idx, min(N_BASE, len(nonmus_idx)), replace=False)
    print(f"pool: base non-muslim {len(base)}, toxic-muslim {len(mus_tox_idx)} (fixed), "
          f"non-toxic-muslim {len(mus_nontox_idx)} (varied)", flush=True)

    te_nontox = ~te_tox
    slice_test = te_sl & te_nontox                      # held-out non-toxic muslim = the good content to keep

    rows = []
    for r in REPS:
        parts = [base, mus_tox_idx]                     # toxic references always present
        if r > 0.0:
            n_good = int(round(r * len(base) / (1 - r)))
            n_good = min(n_good, len(mus_nontox_idx))
            parts.append(rng.choice(mus_nontox_idx, n_good, replace=False))
        sel = np.concatenate(parts)
        Xtr = vec.transform(tr_text[sel]); ytr = tr_tox[sel]
        clf = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, ytr)
        pred = clf.predict(Xte).astype(bool)            # True = predict toxic = DISCARD
        keep_rate = float((~pred[slice_test]).mean())   # fraction of non-toxic muslim KEPT
        agg_acc = float(accuracy_score(te_tox, pred))
        good_r = float((tr_sl[sel] & ~tr_tox[sel]).mean())
        rows.append({"target_r": r, "actual_good_r": round(good_r, 5), "n_train": int(len(sel)),
                     "keep_rate_k": round(keep_rate, 4), "false_discard": round(1 - keep_rate, 4),
                     "agg_accuracy": round(agg_acc, 4)})
        print(f"r={r:.3f} (good-content {good_r:.4f}, n={len(sel)}): keep-rate k={keep_rate:.4f} "
              f"(false-discard {1-keep_rate:.4f}), agg-acc {agg_acc:.4f}", flush=True)

    k0 = rows[0]["keep_rate_k"]
    r1, k1 = rows[1]["actual_good_r"], rows[1]["keep_rate_k"]
    kprime0 = (k1 - k0) / r1 if r1 > 0 else float("nan")
    p_star = 1.0 / (1.0 + kprime0) if kprime0 > 0 else float("inf")

    out = {"target": TARGET, "n_base": N_BASE, "fixed_vocab": True, "design": "toxic-slice fixed, non-toxic varied",
           "rows": rows, "k_at_r0": k0, "kprime0_estimate": round(kprime0, 3),
           "p_star_estimate": (round(p_star, 4) if np.isfinite(p_star) else None),
           "verdict": (
               f"Competence curve k(r) for slice '{TARGET}' (toxic references present, good content varied). "
               f"keep-rate at r=0 (no good slice content in training) = {k0:.3f}; at natural r~1.2% = "
               f"{rows[3]['keep_rate_k']:.3f}; at r=12% = {rows[-1]['keep_rate_k']:.3f}. "
               f"Finite-diff k'(0)~{kprime0:.2f} => ratchet critical prevalence p*=1/(1+k'(0))~"
               f"{p_star:.4f} ({p_star*100:.2f}%). "
               + ("k(0) LOW: with toxic references present, a curator lacking good slice content DISCARDS it -- the "
                  "absorbing state holds; slices below p* face extinction under iterated curation."
                  if k0 < 0.5 else
                  "k(0) HIGH: the model generalizes to good slice content even without training examples, so the "
                  "ratchet's absorbing state is a small floor, not zero (bounded thinning, not total extinction)."))}
    json.dump(out, open(os.path.join(REPO, "results", "c_ratchet_competence.json"), "w"), indent=2)
    print("\n" + out["verdict"] + "\nsaved -> results/c_ratchet_competence.json")


if __name__ == "__main__":
    main()
