"""
ATTACK 1: Re-derive label/band decoding from raw .dat files.
Independently verify:
  - LABEL_manual_hq: clear={0}, cloud={1,2}, shadow={3}
  - cloud_frac = mean(label==1 or label==2) per patch
  - snow = land_cover == 70
  - clear-snow = cloud_frac < 0.10 AND land_cover == 70
  - KappaMask cloud classes: {3,4}
  - CloudScout bands: B1, B2, B8A (not B8!)
  - n=99 snow patches, n=8490 total

Run with: /Users/aadi/Desktop/Research Paper/.venv/bin/python attack1_label_decoding.py
"""

import numpy as np
import pandas as pd
import os

TRAIN = "/Users/aadi/Desktop/Research Paper/data/cloudsen12/train"
N, H, W = 8490, 512, 512

# --- 1. Count total patches from metadata ---
meta = pd.read_csv(os.path.join(TRAIN, "metadata.csv"))
print(f"[1] Total patches in metadata.csv: {len(meta)}")
assert len(meta) == N, f"Expected {N}, got {len(meta)}"

# --- 2. Decode LABEL_manual_hq independently ---
lab = np.memmap(os.path.join(TRAIN, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))

# Check what values appear
unique_vals = set()
sample_fracs = []
for i in range(0, N, 100):  # sample every 100th patch
    u = np.unique(lab[i])
    unique_vals.update(u.tolist())

print(f"\n[2] Unique label values in LABEL_manual_hq (sampled): {sorted(unique_vals)}")

# Compute cloud_frac using claimed definition: (label==1 | label==2)
cloud_frac = np.empty(N, dtype=np.float32)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac[i] = np.mean((p == 1) | (p == 2))

# Alternative: what if shadow (3) is included?
cloud_frac_with_shadow = np.empty(N, dtype=np.float32)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac_with_shadow[i] = np.mean((p == 1) | (p == 2) | (p == 3))

print(f"\n[3] cloud_frac (1|2 only): mean={cloud_frac.mean():.4f}, max={cloud_frac.max():.4f}")
print(f"    cloud_frac (1|2|3 shadow): mean={cloud_frac_with_shadow.mean():.4f}, max={cloud_frac_with_shadow.max():.4f}")
print(f"    Difference if shadow included: {(cloud_frac_with_shadow - cloud_frac).mean():.4f}")

# Compare with cached features
feats = pd.read_parquet("/Users/aadi/Desktop/Research Paper/data/cloudsen12/features_train.parquet")
cached_cf = feats["cloud_frac"].to_numpy()
max_diff = np.abs(cloud_frac - cached_cf).max()
print(f"\n[4] Max |my_cloud_frac - cached_cloud_frac|: {max_diff:.8f}  ({'MATCH' if max_diff < 1e-5 else 'MISMATCH!'})")

# --- 3. Snow definition ---
lc = meta["land_cover"].values
snow_mask = lc == 70
print(f"\n[5] Snow patches (land_cover==70): {snow_mask.sum()} total")

# Clear-snow patches
clear_mask = cloud_frac < 0.10
clear_snow = clear_mask & snow_mask
print(f"    Clear patches (cloud_frac<0.10): {clear_mask.sum()}")
print(f"    Clear-snow patches: {clear_snow.sum()}")
print(f"    CLAIMED n=99: {'MATCH' if clear_snow.sum() == 99 else f'MISMATCH! Got {clear_snow.sum()}'}")

# Are these patches actually snowy? Check their metadata
snow_patch_lc = lc[clear_snow]
print(f"\n[6] Land cover values of clear-snow patches: {np.unique(snow_patch_lc)}")
snow_patch_cloud = cloud_frac[clear_snow]
print(f"    Cloud fracs of clear-snow patches: min={snow_patch_cloud.min():.4f}, max={snow_patch_cloud.max():.4f}")

# --- 4. KappaMask cloud classes ---
km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km_unique = set()
for i in range(0, N, 200):
    km_unique.update(np.unique(km[i]).tolist())
print(f"\n[7] Unique KappaMask values (sampled): {sorted(km_unique)}")

# KappaMask classes as used: {3,4}
# Documentation: 0=clear, 1=shadow, 2=semi-transparent, 3=cloud, 4=snow (conflated?)
# Wait - is class 4 snow or cloud? This is a potential attack!
# Per Skakun et al. 2022 KappaMask paper: 0=clear, 1=cloud shadow, 2=semi-transparent cloud, 3=cloud, 4=snow

km_frac_34 = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])
km_frac_3only = np.array([np.mean(np.asarray(km[i]) == 3) for i in range(N)])
km_pred_34 = km_frac_34 >= 0.5
km_pred_3only = km_frac_3only >= 0.5

print(f"\n[8] KappaMask classes {{3,4}} — discard rate: {km_pred_34.mean():.4f}")
print(f"    KappaMask class {{3}} only — discard rate: {km_pred_3only.mean():.4f}")
print(f"    Difference: {(km_pred_34.mean() - km_pred_3only.mean()):.4f}")

# Key question: does including class 4 (snow) inflate the snow FDR?
# If class 4 = snow, then KappaMask "discarding" snow patches because class4=snow is circular!
km_snow_fdr_34 = float(km_pred_34[clear_snow].mean())
km_snow_fdr_3only = float(km_pred_3only[clear_snow].mean())
print(f"\n[9] CRITICAL: KappaMask clear-snow FDR:")
print(f"    Using classes {{3,4}}: {km_snow_fdr_34:.4f} (claimed 0.626)")
print(f"    Using class {{3}} only: {km_snow_fdr_3only:.4f}")
print(f"    If class 4 = SNOW, then including it is CIRCULAR (marking snow as 'cloud')!")

# What fraction of clear-snow discards come from class 4 specifically?
km_class4_on_snow = np.array([np.mean(np.asarray(km[i]) == 4) >= 0.5 for i in clear_snow.nonzero()[0]])
km_class3_on_snow = np.array([np.mean(np.asarray(km[i]) == 3) >= 0.5 for i in clear_snow.nonzero()[0]])
print(f"\n[10] Among clear-snow patches: fraction with KM class4>=0.5: {km_class4_on_snow.mean():.4f}")
print(f"     Among clear-snow patches: fraction with KM class3>=0.5: {km_class3_on_snow.mean():.4f}")
print(f"     => {'CLASS 4 IS DRIVING THE HIGH FDR! CRITICAL FLAW.' if km_class4_on_snow.mean() > 0.3 else 'class 4 minor contributor'}")

# --- 5. Check CloudScout band loading ---
# Claimed: B1, B2, B8A (not B8!)
# B8 = NIR broad (10m), B8A = NIR narrow (20m resampled)
b8a_file = os.path.join(TRAIN, "L1C_B8A.dat")
b8_file = os.path.join(TRAIN, "L1C_B8.dat")
print(f"\n[11] CloudScout band files:")
print(f"    L1C_B1.dat exists: {os.path.exists(os.path.join(TRAIN, 'L1C_B1.dat'))}")
print(f"    L1C_B2.dat exists: {os.path.exists(os.path.join(TRAIN, 'L1C_B2.dat'))}")
print(f"    L1C_B8A.dat exists: {os.path.exists(b8a_file)}")
print(f"    L1C_B8.dat exists: {os.path.exists(b8_file)}")
# B8 and B8A are different bands - B8A is narrower NIR, used by CloudScout
b8a = np.memmap(b8a_file, dtype=np.uint16, mode="r", shape=(N, H, W))
b8 = np.memmap(b8_file, dtype=np.uint16, mode="r", shape=(N, H, W))
# Check they're actually different
sample_patch = 0
diff = np.abs(b8a[sample_patch].astype(float) - b8[sample_patch].astype(float))
print(f"    B8 vs B8A mean absolute diff (patch 0): {diff.mean():.2f} (should be non-zero)")

# --- 6. CloudScout scaling check ---
# Claimed: divide by 10000
b1 = np.memmap(os.path.join(TRAIN, "L1C_B1.dat"), dtype=np.uint16, mode="r", shape=(N, H, W))
b2 = np.memmap(os.path.join(TRAIN, "L1C_B2.dat"), dtype=np.uint16, mode="r", shape=(N, H, W))
sample_b1 = np.asarray(b1[0]).astype(np.float32)
sample_b2 = np.asarray(b2[0]).astype(np.float32)
print(f"\n[12] Band value ranges (raw uint16):")
print(f"    B1: min={sample_b1.min():.0f}, max={sample_b1.max():.0f}, mean={sample_b1.mean():.0f}")
print(f"    B2: min={sample_b2.min():.0f}, max={sample_b2.max():.0f}, mean={sample_b2.mean():.0f}")
print(f"    Scaled /10000: min={sample_b1.min()/10000:.4f}, max={sample_b1.max()/10000:.4f}")
print(f"    Reasonable reflectance range (0-1): {'YES' if sample_b1.max()/10000 <= 1.2 else 'OUT OF RANGE!'}")

print("\n=== ATTACK 1 COMPLETE ===")
