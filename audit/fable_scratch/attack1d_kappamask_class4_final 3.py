"""
ATTACK 1d: Resolve the KappaMask class-4 definition conflict.
s4_real_detectors.py claims: {0=nodata,1=clear,2=shadow,3=semi-transparent,4=cloud,5=undef}
Skakun 2022 paper claims:    {0=clear,1=shadow,2=semi-transparent,3=cloud,4=snow}

These are DIFFERENT class systems. We need to determine which applies to
the CloudSEN12 dataset's KappaMask labels.

Approach: use EMPIRICAL EVIDENCE
1. If class 4 = snow: it should correlate with LC=70 and appear mainly on clear patches
2. If class 4 = cloud: it should correlate with high cloud_frac

Also: check the CloudSEN12 paper/data for the actual encoding.
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

cloud_frac = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac[i] = np.mean((p == 1) | (p == 2))

snow = lc == 70
clear = cloud_frac < 0.10

# Per-patch class fractions
km_frac = {c: np.empty(N) for c in range(6)}
for i in range(N):
    p = np.asarray(km[i])
    for c in range(6):
        km_frac[c][i] = np.mean(p == c)

print("=== RESOLVING KappaMask Class 4 Definition ===\n")
print("HYPOTHESIS A: class 4 = SNOW (Skakun 2022 paper)")
print("HYPOTHESIS B: class 4 = CLOUD (s4_real_detectors.py comment)")
print()

# Test 1: Correlation of class 4 fraction with manual cloud_frac
from scipy import stats
corr_cloud, p_cloud = stats.pearsonr(km_frac[4], cloud_frac)
corr_snow_lc, p_snow = stats.pearsonr(km_frac[4], (lc == 70).astype(float))
print(f"Correlation of KM class 4 with:")
print(f"  Manual cloud_frac: r={corr_cloud:.3f}  (if cloud: expect HIGH; if snow: expect LOW/neg)")
print(f"  LC=70 (snow):      r={corr_snow_lc:.3f}  (if snow: expect HIGH; if cloud: expect LOW)")

# Test 2: Mean class 4 fraction by cloud stratum
cc = meta["cloud_coverage"].to_numpy()
print(f"\nMean KM class 4 fraction by cloud stratum:")
for v in ['cloud-free', 'almost-clear', 'low-cloudy', 'mid-cloudy', 'cloudy']:
    mask = cc == v
    if mask.sum() > 0:
        print(f"  {v}: {km_frac[4][mask].mean():.3f}  n={mask.sum()}")
print("  If class 4 = CLOUD: highest values in 'cloudy' stratum")
print("  If class 4 = SNOW:  values should be scattered across strata")

# Test 3: On purely clear snow patches — what does class 4 do?
clear_snow = clear & snow
print(f"\nFor {clear_snow.sum()} clear-snow patches:")
print(f"  Mean class 3 fraction: {km_frac[3][clear_snow].mean():.3f}")
print(f"  Mean class 4 fraction: {km_frac[4][clear_snow].mean():.3f}")
print(f"  If class 4 = CLOUD, HIGH class4 on CLEAR snow is a detection ERROR")
print(f"  If class 4 = SNOW, HIGH class4 on clear snow is CORRECT labeling")

# Test 4: What class is dominant on truly cloudy patches?
truly_cloudy = cloud_frac >= 0.8  # very cloudy patches
print(f"\nFor {truly_cloudy.sum()} very cloudy patches (cloud_frac>=0.8):")
print(f"  Mean class 3 fraction: {km_frac[3][truly_cloudy].mean():.3f}")
print(f"  Mean class 4 fraction: {km_frac[4][truly_cloudy].mean():.3f}")
print(f"  Mean class 5 fraction: {km_frac[5][truly_cloudy].mean():.3f}")
print(f"  If class 4 = CLOUD: should dominate on truly cloudy")
print(f"  If class 3 = cloud and class 4 = snow: class 3 dominates")

# Test 5: Check the README or any documentation files
readme_path = os.path.join("/Users/aadi/Desktop/Research Paper/data/cloudsen12", "README.md")
print(f"\n=== Checking README.md ===")
if os.path.exists(readme_path):
    with open(readme_path) as f:
        content = f.read()
    # Find lines about kappamask
    for line in content.split('\n'):
        if 'kappa' in line.lower() or 'class' in line.lower() or '4' in line:
            print(f"  {line}")
else:
    print("  README.md not found at expected path")

# Also check train directory
train_readme = os.path.join(TRAIN, "README.md")
if os.path.exists(train_readme):
    with open(train_readme) as f:
        print(f"\nTrain README:")
        print(f.read()[:3000])

# Final verdict
print("\n=== VERDICT ===")
print(f"Correlation class 4 vs cloud_frac: {corr_cloud:.3f}")
print(f"Correlation class 4 vs LC=70:      {corr_snow_lc:.3f}")

if abs(corr_snow_lc) > abs(corr_cloud):
    print("\nEMPIRICAL VERDICT: class 4 = SNOW (higher correlation with LC=70 than cloud_frac)")
    print("The s4_real_detectors.py comment ('4=cloud') is WRONG.")
    print("The Skakun 2022 mapping (4=snow) is CORRECT.")
    print()
    print("IMPACT ON PAPER:")
    print("  - KappaMask {3,4} does NOT detect cloud vs snow — it flags BOTH cloud AND snow as unusable")
    print("  - The '63% false discard' of clear-snow is KM CORRECTLY labeling snow as snow")
    print("  - Using {3,4} as 'cloud discard' is a DEFINITIONAL ERROR")
    print("  - The paper needs: either use {3} only, or reframe as 'data quality gating' not 'cloud detection'")
else:
    print("\nEMPIRICAL VERDICT: class 4 correlates more with cloud_frac (supports 4=cloud)")
    print("The s4_real_detectors.py comment may be correct for THIS dataset's encoding.")
    print("However, even so, the high class-4 rate on clear-snow patches would be misclassification.")
