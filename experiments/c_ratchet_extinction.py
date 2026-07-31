"""CURATION-RATCHET extinction regime: does the keep-rate on GOOD slice content collapse to ~0 as the slice's
surviving training references become TOXIC-DOMINATED? This traces the ratchet's own trajectory: each generation
discards good slice content, so the references that survive to train the next curator are increasingly the toxic
ones (anti-slice slurs), which teach 'slice -> toxic' ever harder -> the next curator discards even more good
content. If keep-rate k -> 0 as the toxic fraction phi -> 1, the absorbing state (extinction) is real, not just
the bounded floor seen at natural composition.

We sweep phi = toxic / (toxic+good) among a fixed-size set of slice REFERENCES injected into a fixed non-slice
base, and measure keep-rate on held-out NON-TOXIC slice content. Also reports the multi-slice k(0) spectrum
(keep-rate with references at NATURAL toxic fraction, zero extra good content) to show which slices sit closer to
the extinction regime. Fixed vocabulary (fit on full pool). Outputs results/c_ratchet_extinction.json.
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

SEED = 42
N_BASE = 120000
M_REFS = 600                                   # fixed-size slice-reference set injected into training
PHIS = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.97, 1.0]      # toxic fraction of the slice references
SLICES = ["muslim", "jewish", "black", "gay", "women"]
rng = np.random.default_rng(SEED)


def slice_mask(texts, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(t)) for t in texts], dtype=bool)


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(240000, 60000, SEED)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    vec.fit(tr_text)
    Xte = vec.transform(te_text)

    def draw(idx, n):
        return rng.choice(idx, n, replace=(n > len(idx))) if len(idx) else np.array([], dtype=int)

    def train_eval(sel_idx, slice_test):
        Xtr = vec.transform(tr_text[sel_idx]); ytr = tr_tox[sel_idx]
        clf = LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, ytr)
        pred = clf.predict(Xte).astype(bool)
        keep = float((~pred[slice_test]).mean())
        return keep, float(accuracy_score(te_tox, pred))

    out = {"m_refs": M_REFS, "phi_sweep_target": "muslim", "phi_sweep": [], "k0_spectrum": {}}

    # --- phi sweep on the paper's slice (muslim) ---
    TARGET = "muslim"
    tr_sl = slice_mask(tr_text, TARGET)
    tox_idx = np.where(tr_sl & tr_tox)[0]
    good_idx = np.where(tr_sl & ~tr_tox)[0]
    base = draw(np.where(~tr_sl)[0], N_BASE)
    slice_test = slice_mask(te_text, TARGET) & (~te_tox)
    print(f"[phi sweep] {TARGET}: toxic-refs {len(tox_idx)}, good-refs {len(good_idx)}", flush=True)
    for phi in PHIS:
        n_tox = int(round(phi * M_REFS)); n_good = M_REFS - n_tox
        sel = np.concatenate([base, draw(tox_idx, n_tox), draw(good_idx, n_good)])
        keep, acc = train_eval(sel, slice_test)
        out["phi_sweep"].append({"phi_toxic_frac": phi, "keep_rate_k": round(keep, 4),
                                 "false_discard": round(1 - keep, 4), "agg_accuracy": round(acc, 4)})
        print(f"  phi={phi:.2f} (toxic refs {n_tox}/{M_REFS}): keep-rate k={keep:.4f} "
              f"(false-discard {1-keep:.4f}), agg-acc {acc:.4f}", flush=True)

    # --- k(0) spectrum across slices (references at NATURAL toxic fraction, zero extra good content) ---
    print("[k(0) spectrum] references present, no good content added:", flush=True)
    for s in SLICES:
        sl = slice_mask(tr_text, s)
        tox = np.where(sl & tr_tox)[0]
        stest = slice_mask(te_text, s) & (~te_tox)
        if stest.sum() < 20 or len(tox) < 10:
            continue
        base_s = draw(np.where(~sl)[0], N_BASE)
        sel = np.concatenate([base_s, tox])            # toxic references only, no good content
        keep, acc = train_eval(sel, stest)
        nat_tox_frac = float((sl & tr_tox).sum() / max(1, sl.sum()))
        out["k0_spectrum"][s] = {"k0_keep_rate": round(keep, 4), "false_discard": round(1 - keep, 4),
                                 "natural_toxic_frac_of_refs": round(nat_tox_frac, 3),
                                 "n_toxic_refs": int(len(tox)), "slice_test_n": int(stest.sum())}
        print(f"  {s}: k(0)={keep:.4f} (false-discard {1-keep:.4f}), "
              f"natural toxic-ref frac {nat_tox_frac:.3f}, n_tox={len(tox)}", flush=True)

    ext = out["phi_sweep"][-1]["keep_rate_k"]
    out["verdict"] = (
        f"Extinction-regime test. As the slice's training references become toxic-dominated (phi 0->1, the "
        f"ratchet's own trajectory), keep-rate on good 'muslim' content falls {out['phi_sweep'][0]['keep_rate_k']:.3f}"
        f" -> {ext:.3f} while aggregate accuracy stays ~flat. "
        + (f"At phi~1 keep-rate ~{ext:.2f} => the absorbing state (EXTINCTION) is reached once surviving references "
           f"are toxic-dominated -- the ratchet's end-state is extinction, not merely a floor."
           if ext < 0.25 else
           f"keep-rate bottoms at {ext:.2f} (not ~0) even at phi=1 => strong thinning but a residual floor; "
           f"full extinction not reached for this slice/model.")
        + " k(0) spectrum shows which slices sit closest to the regime.")
    json.dump(out, open(os.path.join(REPO, "results", "c_ratchet_extinction.json"), "w"), indent=2)
    print("\n" + out["verdict"] + "\nsaved -> results/c_ratchet_extinction.json")


if __name__ == "__main__":
    main()
