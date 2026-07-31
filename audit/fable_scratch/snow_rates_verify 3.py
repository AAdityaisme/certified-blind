"""Script 2: snow_rates_verify.py
Independently compute:
- CloudScout false-discard rate on clear-snow patches
- KappaMask false-discard rate on clear-snow patches
- KappaMask threshold sweep (0.1 to 0.9) to see how sensitive the 63% claim is
- Exact n for each
"""
import sys, os
import numpy as np
import pandas as pd
import torch

REPO = "/Users/aadi/Desktop/Research Paper"
DATA = os.path.join(REPO, "data", "cloudsen12", "train")
H, W = 512, 512

sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))
import cloudsen12 as cs
from cloudscout import CloudScout

cs.use_split("train")
CKPT = os.path.join(REPO, "models", "cloudscout", "pretrained", "cloudscout-128a-S2-2018", "model70-final.ckpt")

print("Loading metadata and labels...")
meta = pd.read_csv(os.path.join(DATA, "metadata.csv"))
N = len(meta)
lc = meta["land_cover"].values

# compute cloud_frac from LABEL_manual_hq
lab = np.memmap(os.path.join(DATA, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
print("Computing cloud_frac from LABEL_manual_hq (all patches)...")
all_fracs = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    all_fracs[i] = np.mean((p == 1) | (p == 2))

clear = all_fracs < 0.10
snow = lc == 70
clear_snow = clear & snow
n_clear_snow = int(clear_snow.sum())
print(f"\nClear-snow subset: n={n_clear_snow}")

# KappaMask: compute per-patch fraction classified as {3,4}
print("\nComputing KappaMask per-patch cloud fractions...")
km = np.memmap(os.path.join(DATA, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km_frac = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])

print("\n--- KappaMask clear-snow FDR at threshold 0.5 (paper claim: ~63%) ---")
km_discard_05 = km_frac >= 0.5
km_fdr_snow = float(km_discard_05[clear_snow].mean())
n_km_snow_discarded = int(km_discard_05[clear_snow].sum())
print(f"  KappaMask discard(>= 0.5) of clear-snow: {km_fdr_snow:.4f} ({n_km_snow_discarded}/{n_clear_snow})")

print("\n--- KappaMask clear-snow FDR across threshold sweep 0.1 to 0.9 ---")
for thr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    km_d = km_frac >= thr
    fdr = float(km_d[clear_snow].mean())
    n_d = int(km_d[clear_snow].sum())
    print(f"  threshold={thr:.1f}: clear-snow FDR={fdr:.4f} ({n_d}/{n_clear_snow})")

# CloudScout: run inference on full train set
print("\n--- CloudScout clear-snow FDR (paper claim: ~2%) ---")
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"  Using device: {device}")
m = CloudScout().to(device)
m.load_state_dict(torch.load(CKPT, map_location=device))
m.eval()

b1 = np.memmap(os.path.join(DATA, "L1C_B1.dat"), dtype=np.uint16, mode="r", shape=(N, H, W))
b2 = np.memmap(os.path.join(DATA, "L1C_B2.dat"), dtype=np.uint16, mode="r", shape=(N, H, W))
b8a = np.memmap(os.path.join(DATA, "L1C_B8A.dat"), dtype=np.uint16, mode="r", shape=(N, H, W))

cs_pred = np.empty(N, dtype=bool)
print(f"  Running CloudScout on {N} patches...")
with torch.no_grad():
    for i in range(0, N, 64):
        j = min(i + 64, N)
        batch = []
        for k in range(i, j):
            ch = np.stack([np.asarray(b1[k]), np.asarray(b2[k]), np.asarray(b8a[k])])
            batch.append(ch)
        x = np.stack(batch).astype(np.float32) / 10000.0
        logits = m(torch.from_numpy(x).to(device))
        cs_pred[i:j] = logits.argmax(1).cpu().numpy() == 1
        if i % 1000 == 0:
            print(f"    {i}/{N}...", flush=True)

cs_fdr_snow = float(cs_pred[clear_snow].mean())
n_cs_snow_discarded = int(cs_pred[clear_snow].sum())
print(f"\n  CloudScout discard of clear-snow: {cs_fdr_snow:.4f} ({n_cs_snow_discarded}/{n_clear_snow})")
print(f"  Paper claims: 0.020 (2%)")

# Also compute other sanity checks
cs_fdr_all = float(cs_pred.mean())
print(f"\n  CloudScout global discard rate: {cs_fdr_all:.4f}  (paper claims 0.328)")
cs_fdr_clearly_cloudy = float(cs_pred[all_fracs >= 0.5].mean())
print(f"  CloudScout discard rate on truly-cloudy: {cs_fdr_clearly_cloudy:.4f}  (should be HIGH for sanity)")
cs_fdr_clear_nonsnow = float(cs_pred[clear & ~snow].mean())
print(f"  CloudScout discard rate on clear non-snow: {cs_fdr_clear_nonsnow:.4f}  (should be LOW for sanity)")

print("\n=== SUMMARY ===")
print(f"  n_clear_snow: {n_clear_snow}")
print(f"  KappaMask clear-snow FDR @ 0.5: {km_fdr_snow:.4f}  (paper: 0.626)")
print(f"  CloudScout clear-snow FDR:      {cs_fdr_snow:.4f}  (paper: 0.020)")
print(f"  Ratio: {km_fdr_snow/max(cs_fdr_snow,1e-6):.1f}x  (paper: 31x)")
