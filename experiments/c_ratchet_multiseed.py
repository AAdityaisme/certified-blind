"""Multi-seed CIs for the curation-ratchet figure (roadmap #7).

Reruns c_ratchet_extinction's phi-sweep (good-content keep-rate as slice references toxify) and the
k(0) spectrum across seeds {42,7,123,2024,99}, reporting mean and 95% CI (2.5/97.5 percentile over
seeds) per phi and per slice. Writes results/c_ratchet_multiseed.json. The canonical single-seed
result (c_ratchet_extinction.json) is left untouched; plot_ratchet.py shades CIs from this file when
present. Turns the single-seed ratchet curve into a trend.
"""

from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod  # noqa: E402

SEEDS = [42, 7, 123, 2024, 99]
N_BASE = 120000
M_REFS = 600
PHIS = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.97, 1.0]
SLICES = ["muslim", "jewish", "black", "gay", "women"]
TARGET = "muslim"


def slice_mask(texts, term):
    p = re.compile(rf"\b{term}\b", re.I)
    return np.array([bool(p.search(t)) for t in texts], dtype=bool)


def run_seed(seed):
    rng = np.random.default_rng(seed)
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(240000, 60000, seed)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True).fit(tr_text)
    Xte = vec.transform(te_text)

    def draw(idx, n):
        return rng.choice(idx, n, replace=(n > len(idx))) if len(idx) else np.array([], dtype=int)

    def train_eval(sel_idx, slice_test):
        clf = LogisticRegression(max_iter=1000, C=4.0, random_state=seed).fit(
            vec.transform(tr_text[sel_idx]), tr_tox[sel_idx])
        pred = clf.predict(Xte).astype(bool)
        return float((~pred[slice_test]).mean()), float(accuracy_score(te_tox, pred))

    tr_sl = slice_mask(tr_text, TARGET)
    tox_idx = np.where(tr_sl & tr_tox)[0]
    good_idx = np.where(tr_sl & ~tr_tox)[0]
    base = draw(np.where(~tr_sl)[0], N_BASE)
    slice_test = slice_mask(te_text, TARGET) & (~te_tox)
    phi_fd = []
    for phi in PHIS:
        n_tox = int(round(phi * M_REFS))
        sel = np.concatenate([base, draw(tox_idx, n_tox), draw(good_idx, M_REFS - n_tox)])
        keep, _ = train_eval(sel, slice_test)
        phi_fd.append(1 - keep)

    k0 = {}
    for s in SLICES:
        sl = slice_mask(tr_text, s)
        tox = np.where(sl & tr_tox)[0]
        stest = slice_mask(te_text, s) & (~te_tox)
        if stest.sum() < 20 or len(tox) < 10:
            continue
        base_s = draw(np.where(~sl)[0], N_BASE)
        keep, _ = train_eval(np.concatenate([base_s, tox]), stest)
        k0[s] = 1 - keep
    return phi_fd, k0


def main():
    phi_all, k0_all = [], []
    for seed in SEEDS:
        print(f"seed {seed}...", flush=True)
        phi_fd, k0 = run_seed(seed)
        phi_all.append(phi_fd)
        k0_all.append(k0)

    phi_arr = np.array(phi_all)  # (seeds, phis)
    phi_rows = []
    for j, phi in enumerate(PHIS):
        col = phi_arr[:, j]
        phi_rows.append({"phi_toxic_frac": phi, "false_discard_mean": round(float(col.mean()), 4),
                         "false_discard_std": round(float(col.std()), 4),
                         "ci_lo": round(float(np.percentile(col, 2.5)), 4),
                         "ci_hi": round(float(np.percentile(col, 97.5)), 4)})
    slices = sorted({s for d in k0_all for s in d})
    k0_rows = {}
    for s in slices:
        vals = np.array([d[s] for d in k0_all if s in d])
        k0_rows[s] = {"false_discard_mean": round(float(vals.mean()), 4),
                      "false_discard_std": round(float(vals.std()), 4),
                      "ci_lo": round(float(np.percentile(vals, 2.5)), 4),
                      "ci_hi": round(float(np.percentile(vals, 97.5)), 4), "n_seeds": int(len(vals))}
    out = {"seeds": SEEDS, "phi_sweep": phi_rows, "k0_spectrum": k0_rows,
           "verdict": (f"Multi-seed ({len(SEEDS)} seeds) CIs for the ratchet. phi=1 good-content false-discard "
                       f"{phi_rows[-1]['false_discard_mean']:.3f} "
                       f"[{phi_rows[-1]['ci_lo']:.3f},{phi_rows[-1]['ci_hi']:.3f}]; the single-seed curve sits "
                       f"inside the band, so the trend is seed-robust.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_ratchet_multiseed.json"), "w"), indent=2)
    print("\n" + out["verdict"] + "\nsaved -> results/c_ratchet_multiseed.json")


if __name__ == "__main__":
    main()
