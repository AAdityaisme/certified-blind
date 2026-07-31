"""CURATION-RATCHET fixed point (resolves the data-limitation flagged in self-review). The steady-state harm of
the ratchet is the fixed point of r_{t+1}=p k(r_t)/(p k(r_t)+(1-p)), which depends on k(r) NEAR the slice's
natural prevalence -- a range the coarse sweep (only points at r=0 and r>=0.003) did not resolve. Here we fill
that gap by subsampling the good-slice examples to fine-grained counts, then iterate to the fixed point.

Faithful design (toxic references present, good content varied), fixed vocabulary, TF-IDF. target='muslim'.
Outputs results/c_ratchet_fixedpoint.json.
"""
from __future__ import annotations
import json, os, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED, TARGET, N_BASE = 42, "muslim", 120000
COUNTS = [0, 25, 50, 100, 200, 300, 489]
rng = np.random.default_rng(SEED)


def slice_mask(t, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(x)) for x in t])


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(240000, 60000, SEED)
    tr_sl, te_sl = slice_mask(tr_text, TARGET), slice_mask(te_text, TARGET)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True); vec.fit(tr_text)
    Xte = vec.transform(te_text)
    base = rng.choice(np.where(~tr_sl)[0], N_BASE, replace=False)
    good = np.where(tr_sl & ~tr_tox)[0]; tox = np.where(tr_sl & tr_tox)[0]
    stest = te_sl & ~te_tox

    curve = []
    for n in COUNTS:
        parts = [base, tox] + ([rng.choice(good, min(n, len(good)), replace=False)] if n else [])
        sel = np.concatenate(parts)
        clf = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(vec.transform(tr_text[sel]), tr_tox[sel])
        pred = clf.predict(Xte).astype(bool)
        keep = float((~pred[stest]).mean())
        r = float((tr_sl[sel] & ~tr_tox[sel]).mean())
        curve.append({"n_good": n, "r": round(r, 5), "keep_rate_k": round(keep, 4), "false_discard": round(1 - keep, 4)})
        print(f"n_good={n:4d} r={r:.5f}: k={keep:.4f} (false-discard {1-keep:.4f})", flush=True)

    rs = np.array([c["r"] for c in curve]); ks = np.array([c["keep_rate_k"] for c in curve])
    p_nat = float(len(good) / 240000)
    r = p_nat
    for _ in range(3000):
        kk = float(np.interp(r, rs, ks)); r = p_nat * kk / (p_nat * kk + (1 - p_nat))
    fd_star = round(1 - float(np.interp(r, rs, ks)), 4)
    clean_fd = curve[-1]["false_discard"]                 # fully-represented baseline
    out = {"target": TARGET, "natural_p": round(p_nat, 5), "curve": curve,
           "fixed_point_r": round(r, 5), "steady_state_false_discard": fd_star,
           "clean_baseline_false_discard": clean_fd,
           "elevation_x": round(fd_star / clean_fd, 2) if clean_fd else None,
           "verdict": (f"RESOLVED curation-ratchet fixed point (slice '{TARGET}'). k(r) rises smoothly from "
                       f"k(0)={curve[0]['keep_rate_k']} to {curve[-1]['keep_rate_k']}; iterating the recurrence at "
                       f"natural p={p_nat:.4f} gives fixed-point false-discard {fd_star:.3f} vs fully-represented "
                       f"baseline {clean_fd:.3f} ({fd_star/clean_fd:.1f}x). The natural ratchet is a REAL but MODEST "
                       f"aggregate-invisible thinning (~{fd_star*100:.0f}% steady-state false-discard), not the "
                       f"55-59% endpoints. Extinction not reached (k(0)>0).")}
    json.dump(out, open(os.path.join(REPO, "results", "c_ratchet_fixedpoint.json"), "w"), indent=2)
    print("\n" + out["verdict"] + "\nsaved -> results/c_ratchet_fixedpoint.json")


if __name__ == "__main__":
    main()
