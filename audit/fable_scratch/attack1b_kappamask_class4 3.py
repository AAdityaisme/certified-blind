"""
ATTACK 1b: What is KappaMask class 4? Is it SNOW or cloud?

KappaMask documentation: https://github.com/sentinel-hub/eo-learn/issues
Per Skakun et al. 2022 (doi:10.3390/rs14081893):
  Table 2: 0=Clear, 1=Cloud shadow, 2=Semi-transparent cloud, 3=Cloud, 4=Snow

If class 4 = SNOW, then including it in the cloud mask is NOT a "false discard"
due to cloud misclassification — it's KappaMask correctly identifying snow but
treating it as "should not be used for optical analysis" (a common practice).
The claimed FDR=63% may be MISLEADING if class 4 = snow correctly labeled.

We need to find out what class 4 actually means in this dataset.
"""

import numpy as np
import pandas as pd
import os

TRAIN = "/Users/aadi/Desktop/Research Paper/data/cloudsen12/train"
N, H, W = 8490, 512, 512

meta = pd.read_csv(os.path.join(TRAIN, "metadata.csv"))
lc = meta["land_cover"].values

lab = np.memmap(os.path.join(TRAIN, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))

# Compute per-patch statistics
cloud_frac = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac[i] = np.mean((p == 1) | (p == 2))

snow = lc == 70
clear = cloud_frac < 0.10
clear_snow = clear & snow

# For each KappaMask class, check what land covers dominate
print("=== KappaMask Class 4 Investigation ===\n")

# Get per-patch dominant KM class
km_class4_frac = np.empty(N)
km_class3_frac = np.empty(N)
km_class0_frac = np.empty(N)
for i in range(N):
    p = np.asarray(km[i])
    km_class4_frac[i] = np.mean(p == 4)
    km_class3_frac[i] = np.mean(p == 3)
    km_class0_frac[i] = np.mean(p == 0)

# Which land covers have high class-4 fraction?
print("Mean KM class-4 fraction by land cover:")
for lc_val in sorted(np.unique(lc)):
    mask = lc == lc_val
    if mask.sum() > 5:
        print(f"  LC={lc_val}: mean_class4={km_class4_frac[mask].mean():.3f}  n={mask.sum()}")

print("\nMean KM class-4 fraction by cloud_frac group:")
for group, label in [(cloud_frac < 0.10, "clear (<10%)"),
                     ((cloud_frac >= 0.10) & (cloud_frac < 0.50), "partly cloudy (10-50%)"),
                     (cloud_frac >= 0.50, "cloudy (>=50%)")]:
    if group.sum() > 0:
        print(f"  {label}: mean_class4={km_class4_frac[group].mean():.3f}  n={group.sum()}")

# CRUCIAL: Among clear snow patches, what fraction is each KM class?
snow_idx = np.where(clear_snow)[0]
print(f"\nFor {len(snow_idx)} clear-snow patches (land_cover=70, cloud_frac<0.10):")
print(f"  Mean KM class 0 (clear): {km_class0_frac[clear_snow].mean():.3f}")
print(f"  Mean KM class 3 (cloud): {km_class3_frac[clear_snow].mean():.3f}")
print(f"  Mean KM class 4 (snow?): {km_class4_frac[clear_snow].mean():.3f}")

# Ground truth: manual_hq for these patches
print(f"\n  Manual_hq cloud_frac for clear-snow patches:")
print(f"    mean={cloud_frac[clear_snow].mean():.4f}, max={cloud_frac[clear_snow].max():.4f}")
print(f"    These are genuinely CLEAR (cloud_frac<0.10)")

# If class 4 = snow, KappaMask "correctly" IDs them as snow (not cloud)
# But the paper treats KM {3,4} discard as a "false discard" relative to cloud detection
# This is only valid if the paper's goal is "data usability for optical analysis"
# not "cloud classification" per se

# What does KM discard at class 4 look like vs non-snow patches?
non_snow_clear = clear & ~snow
print(f"\n  For {non_snow_clear.sum()} clear NON-snow patches:")
print(f"    Mean KM class 0 (clear): {km_class0_frac[non_snow_clear].mean():.3f}")
print(f"    Mean KM class 3 (cloud): {km_class3_frac[non_snow_clear].mean():.3f}")
print(f"    Mean KM class 4 (snow?): {km_class4_frac[non_snow_clear].mean():.3f}")

# Check discard rates without class 4
km_pred_3only = km_class3_frac >= 0.5
print(f"\n=== Impact of class 4 inclusion ===")
print(f"KM discard rate (class 3 only): {km_pred_3only.mean():.4f}")
km_pred_34 = (km_class3_frac + km_class4_frac) >= 0.5  # crude, not exactly what code does
km_pred_34_exact = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) >= 0.5 for i in range(N)])
print(f"KM discard rate (class 3+4):    {km_pred_34_exact.mean():.4f}")
print(f"=> class 4 inflates discard rate by {(km_pred_34_exact.mean() - km_pred_3only.mean()):.4f}")

print(f"\nClear-snow FDR (class 3 only): {km_pred_3only[clear_snow].mean():.4f}")
print(f"Clear-snow FDR (class 3+4):    {km_pred_34_exact[clear_snow].mean():.4f}")
print(f"=> class 4 inflates snow FDR by {(km_pred_34_exact[clear_snow].mean() - km_pred_3only[clear_snow].mean()):.4f}")

# Check other land covers to see if class 4 is specifically a snow flag
print("\n=== Is class 4 a snow-specific flag in KappaMask? ===")
# Among patches where class 4 dominates (>50% of pixels)
high_class4 = km_class4_frac >= 0.50
print(f"Patches where KM class4 > 50%: {high_class4.sum()}")
if high_class4.sum() > 0:
    print(f"  Land cover distribution: {pd.Series(lc[high_class4]).value_counts().to_dict()}")
    print(f"  Mean cloud_frac (manual): {cloud_frac[high_class4].mean():.4f}")

print("\n=== CONCLUSION ===")
print("If KappaMask class 4 = SNOW (not cloud), then the 63% 'false discard' rate")
print("is actually KappaMask CORRECTLY labeling clear snow as snow-contaminated,")
print("which is a VALID reason to flag for optical analysis quality.")
print("This is NOT a 'catastrophic detector' — it's correctly identifying a different")
print("quality issue. The comparison is UNFAIR / MISLEADING.")
print("\nHowever, the paper's DEFENSE: if the goal is 'usable data for downstream analysis',")
print("snow-flagged scenes ARE discarded and the data IS lost, regardless of the label reason.")
print("The question is whether this framing is made clear in the paper.")
