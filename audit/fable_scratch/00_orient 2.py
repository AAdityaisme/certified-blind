"""
FABLE AUDIT SCRATCH — Phase 0: Orientation
Verify basic counts, label decoding, and data integrity
"""
import numpy as np
import pandas as pd

REPO = '/Users/aadi/Desktop/Research Paper'
DATA = f'{REPO}/data/cloudsen12/train'

N, H, W = 8490, 512, 512

meta = pd.read_csv(f'{DATA}/metadata.csv')
print(f"[0] N from metadata CSV: {len(meta)} (claimed 8490)")

# ---- LABEL_manual_hq decoding ----
lab = np.memmap(f'{DATA}/LABEL_manual_hq.dat', dtype=np.uint8, mode='r', shape=(N, H, W))
unique_vals = set()
for i in range(0, N, 500):
    unique_vals.update(np.unique(lab[i]))
print(f"\n[1] LABEL_manual_hq unique pixel values: {sorted(unique_vals)}")
print("    Expected: 0=clear, 1=thick cloud, 2=thin cloud, 3=cloud shadow")
# Cloud fraction: (1|2) per patch
sample_frac = np.array([np.mean((lab[i]==1)|(lab[i]==2)) for i in range(min(200, N))])
print(f"    Sample cloud_frac (n=200): mean={sample_frac.mean():.3f} min={sample_frac.min():.3f} max={sample_frac.max():.3f}")

# ---- land_cover 70 = snow/ice in ESACCI ----
lc = meta['land_cover'].values
print(f"\n[2] land_cover==70 (snow/ice): {(lc==70).sum()} patches out of {N}")
# What fraction are 'clear' snow?
cloud_frac_all = np.array([np.mean((lab[i]==1)|(lab[i]==2)) for i in range(N)])
clear = cloud_frac_all < 0.10
snow = lc == 70
print(f"    clear (cloud_frac<0.10): {clear.sum()} patches")
print(f"    snow (lc==70): {snow.sum()} patches")
print(f"    clear & snow: {(clear & snow).sum()} patches (paper claims 99)")

# ---- LABEL_kappamask_L1C decoding ----
km = np.memmap(f'{DATA}/LABEL_kappamask_L1C.dat', dtype=np.uint8, mode='r', shape=(N, H, W))
km_unique = set()
for i in range(0, N, 500):
    km_unique.update(np.unique(km[i]))
print(f"\n[3] LABEL_kappamask_L1C unique pixel values: {sorted(km_unique)}")
print("    Script uses classes {3,4} as cloud (np.isin). Checking what 0,1,2,3,4 mean:")
print("    KappaMask L1C classes: 0=no_data, 1=clear, 2=shadow, 3=cloud_shadow?, 4=cloud?")
# Per-patch cloud fraction
km_frac_sample = np.array([np.mean(np.isin(km[i],[3,4])) for i in range(200)])
print(f"    KM cloud_frac (isin{{3,4}}, n=200): mean={km_frac_sample.mean():.3f}")
km_frac_all = np.array([np.mean(np.isin(km[i],[3,4])) for i in range(N)])
km_pred = km_frac_all >= 0.5
print(f"    KappaMask discard rate (>=0.5): {km_pred.mean():.3f}")
km_snow_fdr = km_pred[clear & snow].mean()
print(f"    KappaMask clear-snow FDR: {km_snow_fdr:.3f} (paper claims 0.626)")

# ---- CloudScout band verification ----
# Paper uses B1, B2, B8A (aerosol, blue, red-edge)
print(f"\n[4] Band files in train/:")
import os
bands_present = [f for f in os.listdir(DATA) if f.endswith('.dat')]
print(f"    {sorted(bands_present)}")
# Confirm B8A present
b8a_path = f'{DATA}/L1C_B8A.dat'
print(f"    L1C_B8A.dat exists: {os.path.exists(b8a_path)}")
b8a = np.memmap(b8a_path, dtype=np.uint16, mode='r', shape=(N, H, W))
b1 = np.memmap(f'{DATA}/L1C_B1.dat', dtype=np.uint16, mode='r', shape=(N, H, W))
b2 = np.memmap(f'{DATA}/L1C_B2.dat', dtype=np.uint16, mode='r', shape=(N, H, W))
print(f"    B1 sample values (patch 0, center): {b1[0, 256, 256]}, /10000={b1[0,256,256]/10000:.4f}")
print(f"    B2 sample: {b2[0,256,256]}, B8A sample: {b8a[0,256,256]}")
print(f"    Reflectance range check B1: [{b1[0].min()}, {b1[0].max()}] -> [{b1[0].min()/10000:.4f}, {b1[0].max()/10000:.4f}]")
