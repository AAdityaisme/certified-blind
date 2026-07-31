"""
DIAGNOSTIC 4: E3 cost/quality and StandardScaler leakage check.

Checks:
  1. Is the quality=0.958 shift result literally equal to always_strong?
     (already visible in the JSON, but quantify exactly)
  2. Is StandardScaler refit per seed (no test set leakage into scaler)?
  3. Under code-fence shift, what fraction of prompts does surface_logreg
     route to strong? (Should be ~100% if it's degenerate)
  4. Cost ratio calculation: 3.333/0.498 = 6.7x - verify arithmetic.
  5. Does ScalerScaler extrapolation cause the behavior, or the feature shift?
     Recompute with robust scaler / without scaling.
  6. E2b IS caliper validity: what fraction of matched pairs have surface
     distance near-zero vs near the caliper? Are they genuinely similar?
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import routerbench as rb
import perturb as P
import models as M
import features as feat

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler

print("="*70)
print("DIAGNOSTIC 4: E3 cost/quality and StandardScaler check")
print("="*70)

ev = rb.load_pairwise_eval()
texts = ev["prompt"].tolist()
y = ev["route_premium"].to_numpy()
w_solved = ev["weak_solved"].to_numpy()
s_solved = ev["strong_solved"].to_numpy()
w_cost = ev["weak_cost"].to_numpy()
s_cost = ev["strong_cost"].to_numpy()

print(f"pairwise eval rows: {len(ev)}")
print(f"always_strong quality = {s_solved.mean():.6f}")  # reference
print(f"always_strong cost = {s_cost.mean()*1e3:.6f} m$")

# ---- 1. Verify E3 claims ---
print("\n--- E3 verification ---")
SEEDS = [0, 1, 2]
SHIFT = "code_fence"
for seed in SEEDS:
    idx = np.arange(len(y))
    tr, te = train_test_split(idx, test_size=0.25, random_state=seed, stratify=y)
    tr_texts = [texts[i] for i in tr]
    te_texts = [texts[i] for i in te]
    shift_texts = P.apply_perturbation(te_texts, SHIFT)

    clf = M.SurfaceRouter("logreg").fit(tr_texts, y[tr])

    # Clean decisions
    pred_clean = clf.predict(te_texts)
    pred_shift = clf.predict(shift_texts)

    # What fraction routes to strong in clean vs shift?
    frac_strong_clean = pred_clean.mean()
    frac_strong_shift = pred_shift.mean()

    # Quality and cost
    q_clean = np.mean(np.where(pred_clean == 1, s_solved[te], w_solved[te]))
    q_shift = np.mean(np.where(pred_shift == 1, s_solved[te], w_solved[te]))
    c_clean = np.mean(np.where(pred_clean == 1, s_cost[te], w_cost[te]))
    c_shift = np.mean(np.where(pred_shift == 1, s_cost[te], w_cost[te]))

    print(f"\n  Seed {seed}:")
    print(f"    frac routed to STRONG: clean={frac_strong_clean:.3f}  shift={frac_strong_shift:.3f}")
    print(f"    quality:  clean={q_clean:.4f}  shift={q_shift:.4f}  (always_strong={s_solved[te].mean():.4f})")
    print(f"    cost m$:  clean={c_clean*1e3:.4f}  shift={c_shift*1e3:.4f}")
    cost_ratio = c_shift / c_clean if c_clean > 0 else float('inf')
    print(f"    cost ratio (shift/clean): {cost_ratio:.2f}x")

# ---- 2. StandardScaler fit location check ---
print("\n--- StandardScaler fit location (is it fit on train only?) ---")
# Look at the SurfaceRouter.fit() method in models.py
# In SurfaceRouter: self.clf_ = make_pipeline(StandardScaler(), LogisticRegression())
# The pipeline is fit on tr_texts only (clf.fit(tr_texts, y[tr]))
# So StandardScaler IS fit on training data only. This is correct.
# BUT: does the test data fall outside scaler's expected range?

seed = 0
idx = np.arange(len(y))
tr, te = train_test_split(idx, test_size=0.25, random_state=seed, stratify=y)
tr_texts = [texts[i] for i in tr]
te_texts = [texts[i] for i in te]
shift_texts = [P.wrap_code_fence(t) for t in te_texts]

X_tr = feat.surface_feature_matrix(tr_texts).to_numpy()
X_te = feat.surface_feature_matrix(te_texts).to_numpy()
X_shift = feat.surface_feature_matrix(shift_texts).to_numpy()

sc = StandardScaler().fit(X_tr)
X_te_std = sc.transform(X_te)
X_shift_std = sc.transform(X_shift)

print(f"\n  max |z| in clean test set: {np.abs(X_te_std).max():.2f}")
print(f"  max |z| in shifted test set: {np.abs(X_shift_std).max():.2f}")
print(f"  Features with max |z| > 10 in SHIFTED set:")
for i, fname in enumerate(feat.FEATURE_NAMES):
    z_max = np.abs(X_shift_std[:, i]).max()
    if z_max > 10:
        print(f"    {fname}: max_z={z_max:.2f}")

# ---- 3. Without StandardScaler: does it change the result? ---
print("\n--- E3 without StandardScaler: same result? ---")
# Test with RobustScaler instead
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

seed = 0
tr, te = train_test_split(np.arange(len(y)), test_size=0.25, random_state=seed, stratify=y)
tr_texts_list = [texts[i] for i in tr]
te_texts_list = [texts[i] for i in te]
shift_texts_list = [P.wrap_code_fence(t) for t in te_texts_list]

X_tr = feat.surface_feature_matrix(tr_texts_list).to_numpy()
X_te = feat.surface_feature_matrix(te_texts_list).to_numpy()
X_shift = feat.surface_feature_matrix(shift_texts_list).to_numpy()

# RobustScaler
rs = RobustScaler().fit(X_tr)
clf_rb = LogisticRegression(max_iter=2000).fit(rs.transform(X_tr), y[tr])
pred_clean_rb = clf_rb.predict(rs.transform(X_te))
pred_shift_rb = clf_rb.predict(rs.transform(X_shift))
frac_strong_clean_rb = pred_clean_rb.mean()
frac_strong_shift_rb = pred_shift_rb.mean()
print(f"  RobustScaler: frac_strong clean={frac_strong_clean_rb:.3f}  shift={frac_strong_shift_rb:.3f}")

# No scaling
clf_ns = LogisticRegression(max_iter=2000).fit(X_tr, y[tr])
pred_clean_ns = clf_ns.predict(X_te)
pred_shift_ns = clf_ns.predict(X_shift)
frac_strong_clean_ns = pred_clean_ns.mean()
frac_strong_shift_ns = pred_shift_ns.mean()
print(f"  No scaler:    frac_strong clean={frac_strong_clean_ns:.3f}  shift={frac_strong_shift_ns:.3f}")

print(f"  Original (StandardScaler) behavior should show clean~low, shift~1.0")
print(f"  If RobustScaler/no-scaler ALSO show shift~1.0, it's the feature signal, not extrapolation")
print(f"  If they show shift~0.5-0.7, it's StandardScaler extrapolation causing the result")

# ---- 4. E2b IS caliper validity ---
print("\n\n--- E2b IS: caliper validity ---")
df = rb.load_labeled()
texts2 = df["prompt"].tolist()
y2 = df["route_premium"].to_numpy()

from sklearn.neighbors import NearestNeighbors

n2 = len(y2)
idx2 = np.arange(n2)
tr2, te2 = train_test_split(idx2, test_size=0.25, random_state=0, stratify=y2)

surf_all = feat.surface_feature_matrix(texts2).to_numpy()
sc2 = StandardScaler().fit(surf_all[tr2])
surf_te = sc2.transform(surf_all[te2])
y_te2 = y2[te2]

pos = np.where(y_te2 == 1)[0]
neg = np.where(y_te2 == 0)[0]
nn = NearestNeighbors(n_neighbors=1).fit(surf_te[neg])
dist, j = nn.kneighbors(surf_te[pos])
dist = dist[:, 0]
neg_match = neg[j[:, 0]]

caliper = np.percentile(dist, 25)
keep = dist <= caliper
n_pairs = keep.sum()
print(f"  Total positives in test: {len(pos)}")
print(f"  Caliper (25th pct): {caliper:.4f}")
print(f"  Matched pairs: {n_pairs}")
print(f"  Distance distribution (all matches):")
for pct in [0, 10, 25, 50, 75, 90, 100]:
    print(f"    p{pct:3d}: {np.percentile(dist, pct):.4f}")
print(f"\n  Pairs with dist=0 (truly identical surface): {(dist[keep]==0).sum()}")
print(f"  Pairs with dist<0.01: {(dist[keep]<0.01).sum()}")

# Are the matched pairs from the same eval?
te_idx = te2
eval_names = np.array(df["eval_name"].tolist())
te_eval_names = eval_names[te_idx]
pos_evals = te_eval_names[pos[keep]]
neg_evals = te_eval_names[neg_match[keep]]
same_eval = (pos_evals == neg_evals).sum()
diff_eval = (pos_evals != neg_evals).sum()
print(f"\n  Matched pairs from SAME eval: {same_eval} ({100*same_eval/n_pairs:.1f}%)")
print(f"  Matched pairs from DIFF eval: {diff_eval} ({100*diff_eval/n_pairs:.1f}%)")
print(f"  -> If pairs come from different evals, label difference may be due to eval identity,")
print(f"     not genuinely 'same surface, different intent'")

# Per-eval pair counts
from collections import Counter
eval_pair_counts = Counter(pos_evals)
print(f"\n  Pairs by eval (top 10 by count):")
for ev, cnt in eval_pair_counts.most_common(10):
    print(f"    {ev:<40s}: {cnt}")

print("\nDone.")
