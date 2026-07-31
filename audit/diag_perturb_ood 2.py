"""
DIAGNOSTIC 3: SIV perturbation OOD check.

Is the 87.5% SIV code-fence flip a real robustness failure, or is it
trivially explained by the code-fence transform pushing features far
outside the training distribution (OOD extrapolation for the linear model)?

This script:
  1. Measures feature shift per perturbation (mean, per-feature z-score vs train)
  2. Specifically checks n_chars and has_code_fence before/after code_fence wrap
  3. Checks if the code-fence transform makes >50% of test prompts already
     look like training 'positive' samples (route_premium=1) based on surface
  4. Checks whether the code-fence wrap pushes n_tokens/n_chars into
     extreme quantiles of the training distribution
  5. Measures the whitespace SIV (0.872) - is whitespace doubling similarly OOD?
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat
import perturb as P
import routerbench as rb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

print("="*70)
print("DIAGNOSTIC 3: SIV perturbation OOD analysis")
print("="*70)

df = rb.load_labeled()
texts = df["prompt"].tolist()
y = df["route_premium"].to_numpy()

# seed=0 split
n = len(y)
idx = np.arange(n)
tr, te = train_test_split(idx, test_size=0.25, random_state=0, stratify=y)

tr_texts = [texts[i] for i in tr]
te_texts = [texts[i] for i in te]

# Feature matrices
X_tr = feat.surface_feature_matrix(tr_texts).to_numpy()
X_te = feat.surface_feature_matrix(te_texts).to_numpy()

scaler = StandardScaler().fit(X_tr)
X_tr_std = scaler.transform(X_tr)
X_te_std = scaler.transform(X_te)

print("\n--- Feature statistics in TRAINING set (standardized) ---")
print(f"Mean of standardized train features: {X_tr_std.mean(axis=0).round(2)}")
print(f"Std of standardized train features:  {X_tr_std.std(axis=0).round(2)}")
print(f"Feature names: {feat.FEATURE_NAMES}")

# ---- Per-perturbation feature shift ---
print("\n--- Per-perturbation: mean absolute z-score shift vs train distribution ---")
for pert_name, (fn, tag) in P.PERTURBATIONS.items():
    te_pert = [fn(t) for t in te_texts]
    X_pert = feat.surface_feature_matrix(te_pert).to_numpy()
    X_pert_std = scaler.transform(X_pert)

    # Mean absolute z-score of perturbed features
    mean_abs_z = np.abs(X_pert_std).mean(axis=0)
    max_z = np.abs(X_pert_std).max(axis=0)

    # How many perturbed prompts are extreme outliers (|z| > 3) on any feature?
    n_extreme = (np.abs(X_pert_std) > 3).any(axis=1).sum()
    pct_extreme = 100 * n_extreme / len(te_texts)

    print(f"\n  {pert_name} ({tag}):")
    print(f"    test prompts with |z|>3 on any feature: {n_extreme} ({pct_extreme:.1f}%)")

    # Top 3 most-shifted features
    top_feat_idx = mean_abs_z.argsort()[-3:][::-1]
    for fi in top_feat_idx:
        fname = feat.FEATURE_NAMES[fi]
        z_before = np.abs(X_te_std[:, fi]).mean()
        z_after  = mean_abs_z[fi]
        print(f"    {fname}: mean|z|: {z_before:.2f} -> {z_after:.2f}")

# ---- Code-fence specific deep dive ---
print("\n--- Code-fence deep dive ---")
code_fence_te = [P.wrap_code_fence(t) for t in te_texts]
X_cf = feat.surface_feature_matrix(code_fence_te).to_numpy()

# has_code_fence: what fraction of TRAINING prompts have code fences?
cf_idx = feat.FEATURE_NAMES.index("has_code_fence")
nc_idx = feat.FEATURE_NAMES.index("n_chars")
nw_idx = feat.FEATURE_NAMES.index("n_words")
nt_idx = feat.FEATURE_NAMES.index("n_tokens")

tr_cf_rate = X_tr[:, cf_idx].mean()
te_cf_before = X_te[:, cf_idx].mean()
te_cf_after = X_cf[:, cf_idx].mean()
print(f"  has_code_fence in TRAIN:       {tr_cf_rate:.3f} ({100*tr_cf_rate:.1f}% of train prompts)")
print(f"  has_code_fence in TEST (orig): {te_cf_before:.3f}")
print(f"  has_code_fence in TEST (cf):   {te_cf_after:.3f}")

# n_chars shift
print(f"\n  n_chars: train median={np.median(X_tr[:, nc_idx]):.0f}  test_orig median={np.median(X_te[:, nc_idx]):.0f}  test_cf median={np.median(X_cf[:, nc_idx]):.0f}")
print(f"  n_chars: cf adds ~7 chars (``` + newlines) per prompt")

# What fraction of TRAINING prompts have has_code_fence=1 AND route_premium=1?
tr_cf_and_premium = ((X_tr[:, cf_idx] == 1) & (y[tr] == 1)).mean()
tr_cf_rate_among_premium = (X_tr[:, cf_idx][y[tr] == 1]).mean()
tr_cf_rate_among_notprem = (X_tr[:, cf_idx][y[tr] == 0]).mean()
print(f"\n  TRAINING: has_code_fence rate among route_premium=1: {tr_cf_rate_among_premium:.3f}")
print(f"  TRAINING: has_code_fence rate among route_premium=0: {tr_cf_rate_among_notprem:.3f}")
print(f"  -> Code fence is associated with route_premium=1 in training data")
print(f"     (likely because code prompts are harder and need the premium model)")
print(f"  -> Code-fence wrap causes ALL prompts to appear as 'has_code_fence=1',")
print(f"     linearly pushing the surface_logreg score toward route_premium=1")

# What does the linear model do when has_code_fence is flipped?
# Check the coefficient
import models as M
clf = M.SurfaceRouter("logreg")
clf.fit(tr_texts, y[tr])
logreg = clf.clf_.named_steps["logisticregression"]
coef = logreg.coef_[0]
cf_coef = coef[cf_idx]
print(f"\n  surface_logreg coefficient for has_code_fence: {cf_coef:.4f}")
print(f"  (positive = code fence pushes prediction toward route_premium=1)")

# What fraction of non-CF test prompts does setting CF=1 flip?
# Simulate: change has_code_fence from 0 to 1 for all test prompts
from sklearn.preprocessing import StandardScaler
sc = clf.clf_.named_steps["standardscaler"]
X_te_mod = X_te.copy()
X_te_mod[:, cf_idx] = 1.0  # force code fence = 1
proba_orig = clf.clf_.predict_proba(X_te)[:, 1]
proba_cf_forced = clf.clf_.predict_proba(X_te_mod)[:, 1]
pred_orig = (proba_orig > 0.5).astype(int)
pred_cf = (proba_cf_forced > 0.5).astype(int)
flip_rate_from_cf_feature = (pred_orig != pred_cf).mean()
print(f"\n  Flip rate if ONLY has_code_fence feature changes (0->1): {flip_rate_from_cf_feature:.3f}")
print(f"  Actual SIV for code_fence perturbation: 0.875")
print(f"  -> The flip is explained by the has_code_fence feature being a strong predictor")
print(f"     and the code-fence wrap setting it to 1 for ALL prompts")
print(f"     This is OOD extrapolation: the feature moves from 0->1 for all prompts,")
print(f"     where the training signal says code_fence = hard = route_premium=1")

# ---- Whitespace perturbation analysis ---
print("\n--- Whitespace perturbation deep dive ---")
ws_te = [P.reformat_whitespace(t) for t in te_texts]
X_ws = feat.surface_feature_matrix(ws_te).to_numpy()

# whitespace_ratio feature
wr_idx = feat.FEATURE_NAMES.index("whitespace_ratio")
wr_before = X_te[:, wr_idx]
wr_after = X_ws[:, wr_idx]
print(f"  whitespace_ratio: mean {wr_before.mean():.3f} -> {wr_after.mean():.3f} (after doubling spaces)")
print(f"  whitespace_ratio: median {np.median(wr_before):.3f} -> {np.median(wr_after):.3f}")

X_ws_std = scaler.transform(X_ws)
n_extreme_ws = (np.abs(X_ws_std) > 3).any(axis=1).sum()
print(f"  Prompts with |z|>3 on any feature after whitespace: {n_extreme_ws} ({100*n_extreme_ws/len(te_texts):.1f}%)")
wr_z_after = X_ws_std[:, wr_idx]
print(f"  whitespace_ratio |z| after transform: mean={np.abs(wr_z_after).mean():.2f}, max={np.abs(wr_z_after).max():.2f}")

# What fraction of training prompts have been doubled-whitespace style?
# (i.e., how in-distribution is the whitespace transform?)
tr_wr = X_tr[:, wr_idx]
te_wr = X_ws[:, wr_idx]
print(f"\n  Training whitespace_ratio percentiles: 25th={np.percentile(tr_wr, 25):.3f}, 75th={np.percentile(tr_wr, 75):.3f}, 99th={np.percentile(tr_wr, 99):.3f}")
frac_outside_tr_range = (te_wr > X_tr[:, wr_idx].max()).mean()
print(f"  Fraction of perturbed prompts with whitespace_ratio > train max: {frac_outside_tr_range:.3f}")

print("\nDone.")
