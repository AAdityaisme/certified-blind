"""
DIAGNOSTIC 1: Train/Test Leakage via exact + near-duplicate prompts.

RouterBench aggregates templated benchmarks (HellaSwag, WinoGrande, MMLU, etc.)
where MANY prompts share near-identical surface form. The random train_test_split
in E1 may put nearly-identical prompt pairs on both sides of the split, inflating
surface/tfidf AUC.

This script:
  1. Measures exact-duplicate and near-duplicate prompt counts
  2. With seed=0 split, counts how many test prompts have a twin in train
  3. Re-runs surface_logreg and tfidf_logreg with:
       a) deduplicated split (group by exact prompt, split groups)
       b) group-by-eval_name split (the correct cross-eval generalization split)
  4. Reports AUC drop vs the original random split
"""

import os
import sys
import time

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat
import models as M
import routerbench as rb

print("="*70)
print("DIAGNOSTIC 1: Leakage audit")
print("="*70)

t0 = time.time()
df = rb.load_labeled()
texts = df["prompt"].tolist()
y = df["route_premium"].to_numpy()
evals = df["eval_name"].tolist()
n = len(df)
print(f"\nDataset: {n} rows, base_rate={y.mean():.3f}")

# ---- 1. Exact duplicates -----------------------------------------------
print("\n--- Exact duplicates ---")
from collections import Counter
text_counts = Counter(texts)
n_unique = len(text_counts)
n_exact_dup = sum(1 for t, c in text_counts.items() if c > 1)
n_exact_dup_rows = sum(c for t, c in text_counts.items() if c > 1) - n_exact_dup
print(f"Total rows:              {n}")
print(f"Unique prompts:          {n_unique}")
print(f"Prompt strings with dup: {n_exact_dup}  ({100*n_exact_dup/n_unique:.1f}% of unique)")
print(f"Duplicate rows (extras): {n_exact_dup_rows}  ({100*n_exact_dup_rows/n:.1f}% of total)")

# Among prompts that appear >1 time, check label consistency
print("\nLabel consistency among exact duplicates:")
inconsistent = 0
for t, c in text_counts.items():
    if c > 1:
        mask = [i for i, tx in enumerate(texts) if tx == t]
        labels = [y[i] for i in mask]
        if len(set(labels)) > 1:
            inconsistent += 1
print(f"  Prompts with same text but different labels: {inconsistent}")

# ---- 2. Seed=0 split: exact twin leak ----------------------------------
print("\n--- Seed=0 random split: exact-twin test-in-train leak ---")
idx = np.arange(n)
tr0, te0 = train_test_split(idx, test_size=0.25, random_state=0, stratify=y)
tr_set = set(texts[i] for i in tr0)
te_with_twin = sum(1 for i in te0 if texts[i] in tr_set)
print(f"Test set size:              {len(te0)}")
print(f"Test prompts with exact twin in train: {te_with_twin}  ({100*te_with_twin/len(te0):.1f}%)")

# ---- 3. Eval-name distribution -----------------------------------------
print("\n--- Eval distribution ---")
eval_counts = Counter(evals)
for ev, cnt in eval_counts.most_common(15):
    mask = [i for i, e in enumerate(evals) if e == ev]
    base = y[mask].mean()
    print(f"  {ev:<40s}  {cnt:5d} rows  base_rate={base:.3f}")

# ---- 4. Can surface features predict eval_name? (identity confound) ----
print("\n--- Eval identity confound ---")
print("Can surface features predict eval_name? If yes, surface AUC may be")
print("partly eval-name identification, not difficulty prediction.")

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder

X = feat.surface_feature_matrix(texts).to_numpy()
le = LabelEncoder()
y_eval = le.fit_transform(evals)

# Use seed=0 split
tr0_texts_X = X[tr0]
te0_texts_X = X[te0]
sc = StandardScaler().fit(tr0_texts_X)
clf_eval = LogisticRegression(max_iter=2000).fit(sc.transform(tr0_texts_X), y_eval[tr0])
eval_pred_proba = clf_eval.predict_proba(sc.transform(te0_texts_X))
eval_pred = clf_eval.predict(sc.transform(te0_texts_X))
eval_acc = (eval_pred == y_eval[te0]).mean()
# macro AUC for multi-class
from sklearn.metrics import top_k_accuracy_score
all_labels = list(range(len(le.classes_)))
eval_top1 = top_k_accuracy_score(y_eval[te0], eval_pred_proba, k=1, labels=all_labels)
eval_top3 = top_k_accuracy_score(y_eval[te0], eval_pred_proba, k=3, labels=all_labels)
n_classes = len(le.classes_)
chance = 1/n_classes
print(f"  n_eval_classes: {n_classes}")
print(f"  chance accuracy: {chance:.3f}")
print(f"  surface→eval_name top-1 accuracy: {eval_acc:.3f}  (vs chance {chance:.3f})")
print(f"  surface→eval_name top-3 accuracy: {eval_top3:.3f}")

# ---- 5. Per-eval base rate variance ----
print("\n--- Per-eval base rate variance ---")
eval_br = {}
for ev, cnt in eval_counts.most_common():
    mask = [i for i, e in enumerate(evals) if e == ev]
    eval_br[ev] = y[mask].mean()
brs = list(eval_br.values())
print(f"  base_rate min: {min(brs):.3f}  max: {max(brs):.3f}  std: {np.std(brs):.3f}")
print(f"  Evals with base_rate < 0.1: {sum(1 for b in brs if b < 0.1)}")
print(f"  Evals with base_rate > 0.9: {sum(1 for b in brs if b > 0.9)}")
# If base rate is predictable from eval_name, an eval-identity confound exists
# Can we predict route_premium just from eval_name?
from sklearn.dummy import DummyClassifier
eval_name_arr = np.array(evals)
tr_eval_names = eval_name_arr[tr0]
te_eval_names = eval_name_arr[te0]

# Map eval_name -> train base rate
eval_train_br = {}
for i in tr0:
    ev = evals[i]
    if ev not in eval_train_br:
        eval_train_br[ev] = []
    eval_train_br[ev].append(y[i])
eval_train_br_mean = {ev: np.mean(v) for ev, v in eval_train_br.items()}

# Predict route_premium from train base_rate of the eval
pred_from_eval_br = np.array([eval_train_br_mean.get(ev, y.mean()) for ev in te_eval_names])
auc_eval_br = roc_auc_score(y[te0], pred_from_eval_br)
acc_eval_br = ((pred_from_eval_br > 0.5).astype(int) == y[te0]).mean()
print(f"\n  AUC from eval_name-only base_rate signal: {auc_eval_br:.4f}")
print(f"  Acc from eval_name-only base_rate signal: {acc_eval_br:.4f}")
print(f"  (compare: surface_logreg AUC=0.667, tfidf AUC=0.710)")

# ---- 6. Group-aware splits: split by eval_name --------------------------
print("\n" + "="*70)
print("SPLIT COMPARISON: random vs eval-stratified vs eval-held-out")
print("="*70)

# We'll test surface_logreg and tfidf_logreg under three conditions:
# A) original random split (5 seeds)
# B) group-by-eval_name ShuffleSplit (hold out 25% of evals entirely)
# C) leave-one-eval-out (one eval as test, train on rest) - a sample only

eval_names_arr = np.array(evals)
unique_evals = np.unique(eval_names_arr)

# Build fresh routers for comparison
def run_split(name, tr_idx, te_idx, texts, y):
    """Train and evaluate a single router on given splits."""
    factory = M.build_routers()[name]
    clf = factory().fit([texts[i] for i in tr_idx], y[tr_idx])
    proba = clf.proba([texts[i] for i in te_idx])
    auc = roc_auc_score(y[te_idx], proba)
    return auc

routers_to_test = ["surface_logreg", "tfidf_logreg", "surface_hgb", "semantic_logreg"]

print("\nA) Original random split (seeds 0-4):")
orig_aucs = {r: [] for r in routers_to_test}
for seed in range(5):
    tr, te = train_test_split(np.arange(n), test_size=0.25, random_state=seed, stratify=y)
    for r in routers_to_test:
        try:
            auc = run_split(r, tr, te, texts, y)
            orig_aucs[r].append(auc)
        except Exception as e:
            print(f"  ERROR {r} seed{seed}: {e}")
for r in routers_to_test:
    if orig_aucs[r]:
        print(f"  {r:<20s}  AUC={np.mean(orig_aucs[r]):.4f}±{np.std(orig_aucs[r]):.4f}")

print("\nB) Eval-name grouped split (GroupShuffleSplit, 3 seeds):")
gss_aucs = {r: [] for r in routers_to_test}
gss = GroupShuffleSplit(n_splits=3, test_size=0.25, random_state=42)
for tr, te in gss.split(np.arange(n), y, groups=eval_names_arr):
    te_evals = set(eval_names_arr[te])
    tr_evals = set(eval_names_arr[tr])
    overlap = te_evals & tr_evals
    print(f"  train evals={len(tr_evals)}, test evals={len(te_evals)}, overlap={len(overlap)}")
    for r in routers_to_test:
        try:
            auc = run_split(r, tr, te, texts, y)
            gss_aucs[r].append(auc)
        except Exception as e:
            print(f"  ERROR {r}: {e}")
for r in routers_to_test:
    if gss_aucs[r]:
        print(f"  {r:<20s}  AUC={np.mean(gss_aucs[r]):.4f}±{np.std(gss_aucs[r]):.4f}")

print("\nC) Leave-one-eval-out (sample of 5 held-out evals, to be fast):")
# Pick the 5 largest evals as test sets
largest_evals = [ev for ev, cnt in eval_counts.most_common(5)]
loeo_aucs = {r: [] for r in routers_to_test}
for held_out_eval in largest_evals:
    te = np.where(eval_names_arr == held_out_eval)[0]
    tr = np.where(eval_names_arr != held_out_eval)[0]
    # skip if test has only one class
    if len(np.unique(y[te])) < 2:
        print(f"  {held_out_eval}: skipped (only one class in test)")
        continue
    print(f"  held_out={held_out_eval}  test_n={len(te)}  train_n={len(tr)}  test_br={y[te].mean():.3f}")
    for r in routers_to_test:
        try:
            auc = run_split(r, tr, te, texts, y)
            loeo_aucs[r].append(auc)
            print(f"    {r:<20s}  AUC={auc:.4f}")
        except Exception as e:
            print(f"    ERROR {r}: {e}")
print("\nLEOE mean AUC across held-out evals:")
for r in routers_to_test:
    if loeo_aucs[r]:
        print(f"  {r:<20s}  AUC={np.mean(loeo_aucs[r]):.4f}±{np.std(loeo_aucs[r]):.4f}")

print("\n--- SUMMARY ---")
print("AUC drop: random split -> group-aware (eval-name) split:")
for r in routers_to_test:
    if orig_aucs[r] and gss_aucs[r]:
        drop = np.mean(orig_aucs[r]) - np.mean(gss_aucs[r])
        print(f"  {r:<20s}  random={np.mean(orig_aucs[r]):.4f}  grouped={np.mean(gss_aucs[r]):.4f}  drop={drop:+.4f}")

print(f"\nTotal runtime: {time.time()-t0:.1f}s")
