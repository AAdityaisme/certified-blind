"""Script 1: label_decode_verify.py
Independent verification of:
- Total patch count
- Snow patch count (land_cover==70)
- LABEL_manual_hq class→cloud_frac mapping
- KappaMask class decoding {3,4}
- CloudScout argmax==1 convention
- Band indices for CloudScout (B1, B2, B8A)
"""
import sys, os
import numpy as np
import pandas as pd

REPO = "/Users/aadi/Desktop/Research Paper"
DATA = os.path.join(REPO, "data", "cloudsen12", "train")
H, W = 512, 512

# 1. patch count from metadata
meta = pd.read_csv(os.path.join(DATA, "metadata.csv"))
N = len(meta)
print(f"[1] Patch count from metadata.csv: {N}  (expected ~8490)")

# 2. land_cover==70 (snow)
snow_mask = meta["land_cover"].values == 70
n_snow = int(snow_mask.sum())
print(f"[2] Snow patches (land_cover==70): {n_snow}  (expected ~99)")
print(f"    Snow fraction of total: {n_snow/N:.4f}")

# 3. LABEL_manual_hq class mapping
print("\n[3] LABEL_manual_hq class→meaning:")
print("    0=clear, 1=thick cloud, 2=thin cloud, 3=cloud shadow  (per src/cloudsen12.py docstring)")
lab = np.memmap(os.path.join(DATA, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
unique_classes = np.unique(lab)
print(f"    Unique classes present in train split: {unique_classes}")

# compute cloud_frac for first 200 patches to verify formula
sample_fracs = []
for i in range(min(200, N)):
    p = np.asarray(lab[i])
    frac = np.mean((p == 1) | (p == 2))  # thick or thin cloud, per cloudsen12.py
    sample_fracs.append(frac)
print(f"    cloud_frac (mean of 200 patches): mean={np.mean(sample_fracs):.3f} "
      f"std={np.std(sample_fracs):.3f} min={np.min(sample_fracs):.3f} max={np.max(sample_fracs):.3f}")

# cross check: how many patches have cloud_frac<0.10 (clear)?
print("\n    Computing cloud_frac for ALL patches (slow ~30s)...")
all_fracs = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    all_fracs[i] = np.mean((p == 1) | (p == 2))
n_clear = int((all_fracs < 0.10).sum())
n_discard_gt = int((all_fracs >= 0.50).sum())
print(f"    Patches with cloud_frac<0.10 (truly clear): {n_clear}")
print(f"    Patches with cloud_frac>=0.50 (should discard): {n_discard_gt}")
print(f"    GT discard rate: {n_discard_gt/N:.4f}")

# 4. KappaMask class decoding
print("\n[4] KappaMask class decoding:")
km = np.memmap(os.path.join(DATA, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km_classes = np.unique(km)
print(f"    Unique KappaMask classes in train split: {km_classes}")
print(f"    Paper claims 'cloud' = {{3,4}}. What class 3 and 4 mean in KappaMask:")
print(f"    KappaMask L1C classes: 0=clear, 1=shadow, 2=snow/ice(?), 3=thin cloud, 4=thick cloud (to verify)")
# Compute fraction of pixels that are class 3 or 4 per patch
km_frac_sample = []
for i in range(min(50, N)):
    p = np.asarray(km[i])
    km_frac_sample.append(np.mean(np.isin(p, [3, 4])))
print(f"    Sample (50 patches) km_frac mean: {np.mean(km_frac_sample):.3f}")

# Compute actual discard decision (>= 0.5)
km_frac_all = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])
km_discard = km_frac_all >= 0.50
print(f"    KappaMask global discard rate: {km_discard.mean():.4f}  (paper claims 0.378)")

# 5. CloudScout band indices
print("\n[5] CloudScout band indices verification:")
print("    t_dashboard.py loads bands: ['L1C_B1.dat', 'L1C_B2.dat', 'L1C_B8A.dat']")
print("    Sentinel-2 band roles: B01=coastal aerosol, B02=blue, B8A=narrow NIR")
print("    cloudscout.py: nn.Conv2d(3, 128, ...) -> expects 3 input channels")
print("    These are the bands CloudScout was trained on (andrewpatrickdu repo S2-2018)")
files_present = []
for fn in ["L1C_B1.dat", "L1C_B2.dat", "L1C_B8A.dat"]:
    fp = os.path.join(DATA, fn)
    present = os.path.exists(fp)
    files_present.append(present)
    print(f"    {fn}: {'EXISTS' if present else 'MISSING'}")
print(f"    All CloudScout band files present: {all(files_present)}")

# 6. snow + clear cross-check
snow_clear = snow_mask & (all_fracs < 0.10)
n_snow_clear = int(snow_clear.sum())
print(f"\n[6] Clear-snow patches (land_cover==70 AND cloud_frac<0.10): {n_snow_clear}")
print(f"    (This is the n used for clear_snow_FDR; paper claims n=99)")

# Check that land_cover data matches metadata
lc_from_meta = meta["land_cover"].values
print(f"\n[7] Land cover value counts (top 10):")
from collections import Counter
c = Counter(lc_from_meta.tolist())
for val, cnt in sorted(c.items(), key=lambda x: -x[1])[:10]:
    print(f"    LC={val}: {cnt} patches")

print("\n=== SUMMARY ===")
print(f"  N total: {N}")
print(f"  N snow (LC=70): {n_snow}")
print(f"  N clear: {n_clear}")
print(f"  N clear+snow: {n_snow_clear}")
print(f"  KappaMask global discard rate: {km_discard.mean():.4f}")
