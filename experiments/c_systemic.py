"""SYSTEMIC-bias check — tests the threat-model claim that the 'systemic-organic lower end evades BOTH
certification and reference-free label QA'. The spectrum experiment (c_spectrum) showed a reference-free
cross-slice-outlier label QA catches a TARGETED single-slice flip. The escape route asserted in the paper is
SYSTEMIC bias: bias MANY identity slices together so no single slice is an outlier (evading cross-slice QA).
But biasing many slices raises the aggregate footprint---which could break certification. So 'evades both' is not
obvious; it might evade QA yet trip certification. This runs it.

For bias fraction b, flip b of the non-toxic examples in EVERY identity slice (systemic annotator bias, not a
targeted attack). Measure, for the 'muslim' probe slice: harm (false-discard on clean test), whether it is a
cross-slice outlier (z vs the OTHER identity slices---now all biased, so expected LOW), and aggregate
certification. If there is a b with harm elevated AND certified AND not-an-outlier, the claim holds; else it does
not and the paper claim must be walked back. Outputs results/c_systemic.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod  # noqa: E402

SEED, N_TRAIN, N_TEST = 42, 200_000, 60_000
PROBE = "muslim"
BIAS_GRID = [0.0, 0.05, 0.10, 0.15, 0.20]
CERT_ACC_DROP, CERT_FPR_RISE = 0.01, 0.02
LABELQA_Z = 2.0
RESULTS_PATH = os.path.join(REPO, "results", "c_systemic.json")


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, SEED)
    nontoxic_te = ~te_tox
    tr_slices, te_slices = mod.all_slice_masks(tr_text), mod.all_slice_masks(te_text)
    group = list(tr_slices.keys())                    # bias ALL identity slices together (systemic)

    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr, Xte = vec.fit_transform(tr_text), vec.transform(te_text)

    def fit(y):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, y)

    def slice_fdr(pred, s):
        m = te_slices[s] & nontoxic_te
        return float(pred[m].astype(bool).mean()) if m.sum() else float("nan")

    clean = fit(tr_tox)
    cp = clean.predict(Xte).astype(bool)
    clean_acc = round(accuracy_score(te_tox, cp), 4)
    clean_fpr = round(float(cp[nontoxic_te].mean()), 4)
    base = slice_fdr(cp, PROBE)

    rng = np.random.default_rng(SEED)
    # one nested permutation per slice for reproducible nested bias
    perms = {s: rng.permutation(np.where(tr_slices[s] & ~tr_tox)[0]) for s in group}

    pts = []
    for b in BIAS_GRID:
        y = tr_tox.copy()
        for s in group:
            idx = perms[s]
            y[idx[:int(round(len(idx) * b))]] = True
        pred = (cp if b == 0.0 else fit(y).predict(Xte).astype(bool))
        acc = round(accuracy_score(te_tox, pred), 4)
        agg_fpr = round(float(pred[nontoxic_te].mean()), 4)
        certified = bool(acc >= clean_acc - CERT_ACC_DROP and agg_fpr <= clean_fpr + CERT_FPR_RISE)
        # cross-slice outlier check for the probe slice vs the OTHER identity slices (all biased now)
        rates = {s: float(y[tr_slices[s]].mean()) for s in group}
        others = [rates[s] for s in group if s != PROBE]
        mu, sd = float(np.mean(others)), float(np.std(others))
        z = (rates[PROBE] - mu) / sd if sd > 0 else 0.0
        harm = slice_fdr(pred, PROBE)
        pts.append({"bias": b, "probe_harm": round(harm, 4), "certified": certified,
                    "agg_acc": acc, "agg_fpr": agg_fpr, "probe_crossslice_z": round(z, 2),
                    "labelqa_flags": bool(z > LABELQA_Z),
                    "evades_both": bool(certified and z <= LABELQA_Z)})
        print(f"  b={b}: harm={harm:.3f} cert={certified} acc={acc} agg_fpr={agg_fpr} "
              f"z={z:.2f} evades_both={certified and z<=LABELQA_Z}", flush=True)

    evade = [p for p in pts if p["evades_both"] and p["probe_harm"] >= 2 * base and p["bias"] > 0]
    holds = len(evade) > 0
    verdict = (
        f"Systemic-bias check (bias ALL identity slices by b; probe '{PROBE}'). "
        + (f"CLAIM HOLDS: found b with harm elevated ({max(p['probe_harm'] for p in evade)*100:.0f}% vs "
           f"{base*100:.1f}% clean), CERTIFIED, and probe NOT a cross-slice outlier (systemic bias raises no "
           f"single slice) up to b={max(p['bias'] for p in evade)} -- the systemic-organic lower end evades BOTH "
           f"reference-free label QA and certification, as the paper claims."
           if holds else
           f"CLAIM DOES NOT HOLD as stated: no bias level gives harm>=2x baseline while BOTH certified AND "
           f"non-outlier. Certification breaks at/before the harm becomes material (systemic bias inflates the "
           f"aggregate footprint). The paper's 'systemic-organic evades both' must be walked back to what the data "
           f"supports (see points).")
        + f" Certification pass/fail by bias: " + ", ".join(f"{p['bias']}:{'C' if p['certified'] else 'X'}" for p in pts) + ".")
    out = {"probe": PROBE, "bias_grid": BIAS_GRID, "biased_group": group,
           "clean": {"acc": clean_acc, "agg_fpr": clean_fpr, "base_probe_fdr": round(base, 4)},
           "claim_holds": holds, "points": pts,
           "caveats": "Single seed 42, TF-IDF; systemic bias modeled as equal flip across all identity slices.",
           "verdict": verdict}
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print("\n" + verdict + f"\nsaved -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
