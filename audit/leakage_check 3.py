"""Audit: train/test leakage + eval-identity confound for the routing track.

Threats:
  T1 exact-duplicate prompts straddling a random split (memorization).
  T2 eval-identity confound: route_premium base rate varies hugely across
     benchmarks; a model that just detects *which benchmark* (from surface cues)
     gets AUC from between-eval base-rate variation, not intent.

Tests:
  1. exact-dup rate + cross-split exact leakage under random split.
  2. eval-identity ceiling: predict route_premium from eval_name one-hot.
  3. surface AUC within single large evals (within-eval signal).
  4. group-aware splits (by eval_name; by exact prompt) vs random split, for
     surface_logreg and tfidf. How much AUC is leakage / eval-identity?
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import OneHotEncoder

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import models as M  # noqa: E402
import routerbench as rb  # noqa: E402

SEED = 0


def auc_for(router_factory, texts, y, tr, te):
    clf = router_factory().fit([texts[i] for i in tr], y[tr])
    return roc_auc_score(y[te], clf.proba([texts[i] for i in te]))


def main():
    df = rb.load_labeled()
    texts = df["prompt"].tolist()
    y = df["route_premium"].to_numpy()
    evals = df["eval_name"].to_numpy()
    n = len(df)
    print(f"rows={n}  base_rate={y.mean():.3f}  n_evals={df['eval_name'].nunique()}")

    # --- T1: exact duplicates ---
    vc = pd.Series(texts).value_counts()
    n_unique = (vc.index != "").sum() if "" in vc.index else len(vc)
    dup_rows = int((vc[vc > 1] - 1).sum())
    print(f"\n[T1] unique prompts={len(vc)}  ({len(vc)/n:.3f} of rows)  "
          f"duplicate extra rows={dup_rows} ({dup_rows/n:.3f})")
    # cross-split exact leakage under random split
    tr, te = train_test_split(np.arange(n), test_size=0.25, random_state=SEED, stratify=y)
    train_set = set(texts[i] for i in tr)
    leaked = sum(texts[i] in train_set for i in te)
    print(f"[T1] random-split test prompts with EXACT twin in train: "
          f"{leaked}/{len(te)} = {leaked/len(te):.3f}")

    # --- T2: eval-identity ceiling ---
    enc = OneHotEncoder(handle_unknown="ignore").fit(evals[tr].reshape(-1, 1))
    Xtr = enc.transform(evals[tr].reshape(-1, 1)); Xte = enc.transform(evals[te].reshape(-1, 1))
    lr = LogisticRegression(max_iter=1000).fit(Xtr, y[tr])
    eid_auc = roc_auc_score(y[te], lr.predict_proba(Xte)[:, 1])
    print(f"\n[T2] eval-identity AUC (route_premium from eval_name alone) = {eid_auc:.3f}")
    print("     -> upper bound on 'just knowing the benchmark'. Surface AUC was ~0.667-0.711.")

    # surface AUC within single large evals
    print("\n[T2] within-eval surface_logreg AUC (no between-eval base-rate help):")
    for name in ["hellaswag", "grade-school-math", "mmlu-professional-law", "winogrande"]:
        m = np.where(evals == name)[0]
        if len(m) < 200:
            continue
        ym = y[m]
        if ym.mean() in (0.0, 1.0):
            print(f"     {name:22s} skipped (single class)"); continue
        itr, ite = train_test_split(m, test_size=0.25, random_state=SEED, stratify=ym)
        try:
            a = auc_for(lambda: M.SurfaceRouter("logreg"), texts, y, itr, ite)
            print(f"     {name:22s} n={len(m):5d} base={ym.mean():.3f}  surfaceAUC={a:.3f}")
        except Exception as e:
            print(f"     {name:22s} err {e}")

    # --- T3: group-aware splits ---
    print("\n[T3] AUC under random vs group-aware splits:")
    rnd_tr, rnd_te = tr, te
    # group by eval_name (train/test on disjoint benchmarks)
    gss_e = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
    ge_tr, ge_te = next(gss_e.split(np.arange(n), y, groups=evals))
    # group by exact prompt (no identical prompt straddles split)
    codes = pd.factorize(pd.Series(texts))[0]
    gss_p = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
    gp_tr, gp_te = next(gss_p.split(np.arange(n), y, groups=codes))

    for label, (a_tr, a_te) in [("random", (rnd_tr, rnd_te)),
                                 ("group-by-eval", (ge_tr, ge_te)),
                                 ("group-by-prompt(dedup)", (gp_tr, gp_te))]:
        sl = auc_for(lambda: M.SurfaceRouter("logreg"), texts, y, a_tr, a_te)
        tf = auc_for(lambda: M.TfidfRouter(), texts, y, a_tr, a_te)
        br_te = y[a_te].mean()
        print(f"     {label:24s} surface={sl:.3f}  tfidf={tf:.3f}  (test base={br_te:.3f}, "
              f"n_te={len(a_te)})")

    print("\nINTERPRET: if surface AUC drops toward 0.5 under group-by-eval, the signal is "
          "mostly eval-identity. If it holds, surface->routing generalizes across benchmarks.")


if __name__ == "__main__":
    main()
