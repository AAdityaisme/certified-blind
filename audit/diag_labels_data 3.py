"""
DIAGNOSTIC 2: Label validity, data-handling bugs, NaN coercion, scores.

Checks:
  1. Are score columns 0/1 binary, or continuous? (mtbench uses 1-10 floats)
  2. pd.to_numeric with errors='coerce' - do NaNs exist, and how are they treated?
  3. Non-English prompts (high non_ascii_ratio) - how many, which evals?
  4. tiktoken fallback (n_tokens = n_words) - does it occur for any prompts?
  5. _coerce_prompt: are any prompts stored as multi-element lists?
  6. Drop rate: how many rows dropped by drop_unsolvable? Any surprising pattern?
  7. oracle_cost NaN: rows where oracle_cost is NaN (neither model solves) but kept?
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import routerbench as rb
import features as feat

print("="*70)
print("DIAGNOSTIC 2: Label validity and data-handling bugs")
print("="*70)

# Load raw table first
path = rb.find_routerbench_file()
raw = rb._read_table(path).reset_index(drop=True)
print(f"\nRaw table shape: {raw.shape}")
print(f"Columns: {list(raw.columns)[:20]}")
print(f"Total rows (raw): {len(raw)}")

# ---- 1. Score column types ---
print("\n--- Score column types ---")
models = rb.detect_model_columns(raw)
print(f"Models detected: {models}")

for m in models[:3]:  # sample first 3
    col = raw[m]
    raw_vals = col.dropna().unique()[:10]
    numeric_col = pd.to_numeric(col, errors='coerce')
    n_nan = numeric_col.isna().sum()
    uniq_numeric = sorted(numeric_col.dropna().unique())
    print(f"\n  {m}")
    print(f"    dtype: {col.dtype}")
    print(f"    raw sample values: {list(raw_vals)}")
    print(f"    after to_numeric, NaN count: {n_nan}")
    print(f"    unique numeric values: {uniq_numeric[:20]}")
    print(f"    is purely 0/1: {set(uniq_numeric) <= {0.0, 1.0}}")

# ---- 2. NaN coercion impact ---
print("\n--- NaN coercion: how many non-numeric scores? ---")
scores_raw = raw[models]
scores_numeric = scores_raw.apply(pd.to_numeric, errors='coerce')
total_nan = scores_numeric.isna().sum().sum()
total_cells = scores_numeric.size
print(f"Total score cells: {total_cells}")
print(f"NaN after coerce: {total_nan}  ({100*total_nan/total_cells:.2f}%)")
if total_nan > 0:
    # Which rows have NaNs?
    rows_with_nan = scores_numeric.isna().any(axis=1)
    print(f"Rows with any NaN score: {rows_with_nan.sum()}")
    # Check: are these rows treated as 'not solved' (False)?
    # The code does: solved = scores >= solve_threshold
    # NaN >= 0.5 => False in pandas, so NaN = 'not solved' silently
    nan_treated_as_unsolved = True
    print(f"  -> NaN treated as 'not solved' (False): {nan_treated_as_unsolved} [implicit, no warning]")

# ---- 3. Non-English prompts ---
print("\n--- Non-English prompts (non_ascii_ratio) ---")
df = rb.load_labeled()
texts = df["prompt"].tolist()
evals = df["eval_name"].tolist()

X = feat.surface_feature_matrix(texts)
non_ascii = X["non_ascii_ratio"].values
thresh = 0.05  # >5% non-ASCII = likely non-English
n_non_eng = (non_ascii > thresh).sum()
print(f"Prompts with >5% non-ASCII chars: {n_non_eng}  ({100*n_non_eng/len(texts):.2f}%)")

# Which evals have non-English prompts?
from collections import Counter
non_eng_evals = Counter()
for i, (na, ev) in enumerate(zip(non_ascii, evals)):
    if na > thresh:
        non_eng_evals[ev] += 1
if non_eng_evals:
    print("  Non-English prompt counts by eval_name:")
    for ev, cnt in non_eng_evals.most_common(10):
        print(f"    {ev}: {cnt}")
else:
    print("  No non-English prompts detected.")

# ---- 4. tiktoken fallback ---
print("\n--- tiktoken fallback check ---")
try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    # Check if encoding fails for any prompt
    n_fallback = 0
    sample_fallback = []
    for i, t in enumerate(texts[:500]):  # sample first 500
        try:
            enc.encode(t)
        except Exception as e:
            n_fallback += 1
            if len(sample_fallback) < 3:
                sample_fallback.append((i, str(e)[:50]))
    print(f"  tiktoken failures in first 500 prompts: {n_fallback}")
    if sample_fallback:
        for idx, err in sample_fallback:
            print(f"    row {idx}: {err}")
except Exception as e:
    print(f"  tiktoken import failed: {e} -> n_tokens = n_words for ALL prompts")

# ---- 5. Prompt as list check ---
print("\n--- _coerce_prompt: raw prompt types ---")
prompt_types = Counter(type(raw["prompt"].iloc[i]).__name__ for i in range(min(100, len(raw))))
print(f"  Prompt column types (first 100): {dict(prompt_types)}")
# Sample a list prompt
list_rows = [i for i in range(min(500, len(raw))) if isinstance(raw["prompt"].iloc[i], list)]
if list_rows:
    sample_list = raw["prompt"].iloc[list_rows[0]]
    print(f"  Sample list prompt (row {list_rows[0]}): len={len(sample_list)}")
    print(f"    content: {str(sample_list)[:200]}")
    if len(sample_list) > 1:
        print("  WARNING: multi-element list prompt! _coerce_prompt takes x[0], discards the rest!")
    else:
        print("  Single-element list: _coerce_prompt(x[0]) is correct.")

# ---- 6. Drop rate and unsolvable patterns ---
print("\n--- drop_unsolvable analysis ---")
# Load without dropping
df_nodrop = rb.load_labeled(drop_unsolvable=False)
df_drop = rb.load_labeled(drop_unsolvable=True)
dropped = len(df_nodrop) - len(df_drop)
print(f"Rows before drop: {len(df_nodrop)}")
print(f"Rows after drop:  {len(df_drop)}")
print(f"Dropped (unsolvable by both): {dropped}")

# Which evals are most affected?
evals_nodrop = df_nodrop["eval_name"].values
evals_drop = df_drop["eval_name"].values
from collections import Counter
nd_counts = Counter(evals_nodrop)
d_counts = Counter(evals_drop)
print("Dropped rows by eval (top 10):")
drops_by_eval = {ev: nd_counts[ev] - d_counts.get(ev, 0) for ev in nd_counts}
for ev, cnt in sorted(drops_by_eval.items(), key=lambda x: -x[1])[:10]:
    if cnt > 0:
        pct = 100*cnt/nd_counts[ev]
        print(f"  {ev:<40s}  dropped={cnt}  ({pct:.1f}% of eval)")

# ---- 7. oracle_cost NaNs in kept rows ---
print("\n--- oracle_cost NaN check ---")
n_oracle_nan = df_drop["oracle_cost"].isna().sum()
print(f"Rows with NaN oracle_cost in kept frame: {n_oracle_nan}")
print(f"(These are rows where neither weak nor strong model solved it,")
print(f" but they were kept because route_premium depends only on weak)")

# ---- 8. Continuous scores (e.g. mtbench) ---
print("\n--- Continuous score check (solve_threshold=0.5) ---")
# Check if any eval has scores between 0 and 1 exclusively (not just 0/1)
for m in models[:5]:
    numeric_col = pd.to_numeric(raw[m], errors='coerce').dropna()
    intermediate = numeric_col[(numeric_col > 0) & (numeric_col < 1)]
    if len(intermediate) > 0:
        print(f"  {m}: {len(intermediate)} scores between 0 and 1 (non-binary!)")
        print(f"    range: [{intermediate.min():.3f}, {intermediate.max():.3f}]")
        print(f"    These will all be labeled 'not solved' (< 0.5 threshold)")
    else:
        total_not_01 = ((numeric_col != 0.0) & (numeric_col != 1.0)).sum()
        if total_not_01 > 0:
            non_01_vals = numeric_col[(numeric_col != 0.0) & (numeric_col != 1.0)].unique()[:5]
            print(f"  {m}: {total_not_01} non-0/1 scores: {non_01_vals}")
        else:
            print(f"  {m}: purely binary (0.0/1.0) ✓")

print("\nDone.")
