"""
DIAGNOSTIC 5: Additional checks.

1. has_code_fence in training: is it EXACTLY zero for all evals?
   If no prompt in the training set has a code fence, the has_code_fence
   feature has zero variance -> StandardScaler std=0 -> infinite z-score
   for code-fence-wrapped prompts.

2. seeds: are all random sources in each experiment seeded?
   Check: np.random.seed() calls, random_state parameters.

3. SIV aggregation bug: siv_clean_mean is computed as mean over perturbations,
   not mean over samples. Check if this could obscure the result.

4. surface_hgb SIV whitespace (0.225): is this also OOD for HGB?
   HGB handles extrapolation better (histogram binning), so OOD matters less.

5. Verify cost ratio arithmetic: reported 6.7x. Our diag shows 6.68x.

6. Continuous score threshold: how many rows change label if threshold=0.75?
   (Scores are 0.0, 0.1, ..., 1.0. Threshold 0.5 vs 0.75 could matter.)

7. has_code_fence STD in StandardScaler: confirm it's near-zero.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat
import routerbench as rb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

print("="*70)
print("DIAGNOSTIC 5: Additional checks")
print("="*70)

df = rb.load_labeled()
texts = df["prompt"].tolist()
y = df["route_premium"].to_numpy()
n = len(y)

# ---- 1. has_code_fence zero variance ---
print("\n--- has_code_fence variance in training set ---")
idx = np.arange(n)
tr, te = train_test_split(idx, test_size=0.25, random_state=0, stratify=y)
tr_texts = [texts[i] for i in tr]
X_tr = feat.surface_feature_matrix(tr_texts).to_numpy()
cf_idx = feat.FEATURE_NAMES.index("has_code_fence")
cf_values = X_tr[:, cf_idx]
print(f"has_code_fence in train: min={cf_values.min():.3f}, max={cf_values.max():.3f}, mean={cf_values.mean():.6f}, std={cf_values.std():.6f}")
print(f"Number of train prompts with code fence: {(cf_values > 0).sum()}")
if cf_values.std() < 1e-6:
    print("WARNING: has_code_fence has near-zero STD in training set!")
    print("  StandardScaler will set std_=epsilon or 1 for this feature.")
    print("  When test/perturbed prompts have code_fence=1, z-score -> very large positive")
    print("  This causes linear model to extrapolate far outside training range")

sc = StandardScaler().fit(X_tr)
print(f"StandardScaler mean for has_code_fence: {sc.mean_[cf_idx]:.6f}")
print(f"StandardScaler std for has_code_fence:  {sc.scale_[cf_idx]:.6f}")
print(f"z-score of perturbed (cf=1): {(1 - sc.mean_[cf_idx]) / sc.scale_[cf_idx]:.2f}")
print(f"z-score of original (cf=0): {(0 - sc.mean_[cf_idx]) / sc.scale_[cf_idx]:.2f}")

# ---- 2. Seed completeness check ---
print("\n--- Seeds: all random sources seeded? ---")
print("Checking experiment files for np.random.seed() / random_state usage:")
import glob
for fname in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "experiments", "*.py"))):
    with open(fname) as f:
        content = f.read()
    has_seed = "random_state" in content or "np.random.seed" in content or "RandomState" in content
    seeds = [line.strip() for line in content.split('\n') if 'SEEDS' in line or 'random_state' in line or 'np.random.seed' in line]
    print(f"  {os.path.basename(fname)}: seeded={has_seed}")
    for s in seeds[:3]:
        print(f"    {s}")

print("\nNote: E1 uses 5 seeds, E2/E3 use 3 seeds. Embedding cache is shared")
print("  across seeds via _ENC_CACHE - this is fine (embeddings are deterministic)")
print("  but means seed doesn't affect embedding computation itself.")

# ---- 3. SIV aggregation method ---
print("\n--- SIV aggregation check ---")
print("In e2_siv.py, siv_clean_mean is computed as:")
print("  mean([mean_siv_code_fence, mean_siv_whitespace, mean_siv_trailing, mean_siv_bullet])")
print("  = mean over 4 perturbation types, NOT mean over samples")
print("  For surface_logreg: [0.875, 0.872, 0.055, 0.098] -> mean=0.475")
print("  The headline 'SIV=0.875' is for code_fence ONLY (correctly reported per-perturbation)")
print("  The 'clean_mean=0.475' is an aggregate that bundles dramatic (CF/WS) with mild (trailing/bullet)")
print("  This is fine as long as you don't misuse the 'clean mean' as the headline number")
print("  PAPER RISK: if fig2 shows 'SIV=0.875' it should be labeled 'code-fence SIV', not 'SIV'")

# ---- 4. Score threshold sensitivity ---
print("\n--- Score threshold sensitivity (0.5 vs 0.75) ---")
path = rb.find_routerbench_file()
raw = rb._read_table(path).reset_index(drop=True)
models_all = rb.detect_model_columns(raw)
WEAK = rb.WEAK_MODEL
STRONG = rb.STRONG_MODEL

# Current labels at threshold=0.5
df_05 = rb.load_labeled(solve_threshold=0.5)
# New labels at threshold=0.75
df_075 = rb.load_labeled(solve_threshold=0.75)

print(f"Threshold 0.50: {len(df_05)} rows, base_rate={df_05['route_premium'].mean():.3f}")
print(f"Threshold 0.75: {len(df_075)} rows, base_rate={df_075['route_premium'].mean():.3f}")

# How many labels change?
# We need to align by index - both reset_index so compare by position in shared rows
# More precise: align by subset overlap
n_label_change = (df_05['route_premium'].values != df_075.reindex(range(len(df_05)))['route_premium'].values)
# Actually simpler: recompute by loading both
print(f"Note: threshold change drops rows too, so exact label-change count not trivial to compute")
print(f"Scores in the data range from 0.0-1.0 in 0.1 steps (not 0/1 binary)")
print(f"A score of 0.5 (e.g. 5/10 on mtbench) is on the knife-edge at threshold=0.5")
print(f"  -> It gets treated as 'not solved' (score < 0.5 is False, score >= 0.5 is True)")

# Count how many model scores are exactly 0.5
scores_raw = raw[models_all].apply(pd.to_numeric, errors='coerce')
exactly_half = (scores_raw == 0.5).sum().sum()
print(f"Scores exactly equal to 0.5 across all models: {exactly_half}")

# ---- 5. has_json_braces zero variance ---
print("\n--- Other zero-variance features ---")
for i, fname in enumerate(feat.FEATURE_NAMES):
    std_val = X_tr[:, i].std()
    if std_val < 0.001:
        sc_std = sc.scale_[i]
        print(f"  {fname}: train_std={std_val:.6f}  scaler_scale={sc_std:.6f}")

# ---- 6. Verify cost ratio from E3 JSON ---
print("\n--- E3 cost ratio verification ---")
import json
with open(os.path.join(os.path.dirname(__file__), "..", "results", "e3_shift.json")) as f:
    e3 = json.load(f)
sl = e3["results"]["surface_logreg"]
clean_c = sl["clean_c"]["mean"]
shift_c = sl["shift_c"]["mean"]
print(f"clean_c = {clean_c*1e3:.6f} m$")
print(f"shift_c = {shift_c*1e3:.6f} m$")
print(f"ratio = {shift_c/clean_c:.2f}x")
always_strong_c = e3["references"]["always_strong"]["c"]["mean"]
print(f"always_strong_c = {always_strong_c*1e3:.6f} m$")
print(f"shift_c / always_strong_c = {shift_c/always_strong_c:.4f}")
print(f"(Should be ~1.0 if surface_logreg degenerates to 'always strong' under shift)")

print("\nDone.")
