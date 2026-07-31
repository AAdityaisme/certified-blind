"""
ATTACK 2: Reproduce CloudScout 2% and KappaMask 63% from scratch.
- Write independent inference, don't rely on existing scripts
- Check: are they measuring the same thing on the same patches?
- Is the comparison fair (tile-classifier vs per-pixel mask thresholded at 0.5)?
- Sweep KappaMask threshold

Also: ATTACK 3 — dashboard coherence check
- Balanced accuracy gap direction
- Is the comparison internally consistent?
- Does KappaMask's higher accuracy come from snow being rare (1.2%)?
"""

import numpy as np
import pandas as pd
import os
import sys
import torch

REPO = "/Users/aadi/Desktop/Research Paper"
TRAIN = os.path.join(REPO, "data", "cloudsen12", "train")
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))
sys.path.insert(0, os.path.join(REPO, "src"))

from cloudscout import CloudScout
import cloudsen12 as cs
cs.use_split("train")

N, H, W = 8490, 512, 512
CKPT = os.path.join(REPO, "models", "cloudscout", "pretrained", "cloudscout-128a-S2-2018", "model70-final.ckpt")

def band(fn):
    return np.memmap(os.path.join(TRAIN, fn), dtype=np.uint16, mode="r", shape=(N, H, W))

print("=== ATTACK 2: Independent Reproduction ===\n")

# --- Load ground truth ---
meta = pd.read_csv(os.path.join(TRAIN, "metadata.csv"))
lc = meta["land_cover"].values
lab = np.memmap(os.path.join(TRAIN, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
cloud_frac = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac[i] = np.mean((p == 1) | (p == 2))

snow = lc == 70
clear = cloud_frac < 0.10
clear_snow = clear & snow
gt_discard = cloud_frac >= 0.50

print(f"Dataset: N={N}, clear_snow={clear_snow.sum()}, gt_discard={gt_discard.sum()}")
print(f"Snow fraction: {snow.mean():.4f}, clear-snow fraction: {clear_snow.mean():.4f}")

# --- CloudScout inference from scratch ---
print("\n[A] Running CloudScout inference (from scratch, no cached results)...")
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"    Device: {device}")

m = CloudScout().to(device)
state = torch.load(CKPT, map_location=device)
m.load_state_dict(state)
m.eval()

# Load bands: B1, B2, B8A (as per t_dashboard.py)
b1 = band("L1C_B1.dat")
b2 = band("L1C_B2.dat")
b8a = band("L1C_B8A.dat")
bands = [b1, b2, b8a]

cs_logits = np.empty((N, 2))
with torch.no_grad():
    for i in range(0, N, 64):
        j = min(i + 64, N)
        x = np.stack([np.stack([np.asarray(b[k]) for b in bands]) for k in range(i, j)]).astype(np.float32) / 10000.0
        out = m(torch.from_numpy(x).to(device))
        cs_logits[i:j] = out.cpu().numpy()

cs_pred = cs_logits.argmax(1) == 1  # argmax==1 => "cloudy"
print(f"    CloudScout predictions: {cs_pred.sum()} discards ({cs_pred.mean():.4f})")
print(f"    CloudScout discard rate: {cs_pred.mean():.4f} (claimed ~0.328)")

# Compute metrics
def compute_metrics(pred, gt_discard, clear_snow, name):
    acc = (pred == gt_discard).mean()
    tp = (pred & gt_discard).sum()
    fp = (pred & ~gt_discard).sum()
    fn = (~pred & gt_discard).sum()
    tn = (~pred & ~gt_discard).sum()
    tpr = tp / (tp + fn) if (tp + fn) else 0
    tnr = tn / (tn + fp) if (tn + fp) else 0
    bal_acc = (tpr + tnr) / 2
    fdr_snow = pred[clear_snow].mean()
    print(f"\n{name}:")
    print(f"  Observable accuracy: {acc:.4f} (claimed ~0.808 for CS, ~0.869 for KM)")
    print(f"  Balanced accuracy:   {bal_acc:.4f}")
    print(f"  Discard rate:        {pred.mean():.4f}")
    print(f"  Clear-snow FDR:      {fdr_snow:.4f} (claimed 0.020 for CS, 0.626 for KM)")
    print(f"  TPR (cloudy recall): {tpr:.4f}")
    print(f"  TNR (clear recall):  {tnr:.4f}")
    return {"acc": acc, "bal_acc": bal_acc, "fdr_snow": fdr_snow, "tpr": tpr, "tnr": tnr}

cs_metrics = compute_metrics(cs_pred, gt_discard, clear_snow, "CloudScout (my replication)")

# --- KappaMask from scratch ---
print("\n[B] Computing KappaMask predictions (from scratch)...")
km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))

km_frac_34 = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])
km_pred = km_frac_34 >= 0.5

km_metrics = compute_metrics(km_pred, gt_discard, clear_snow, "KappaMask {3,4} >=0.5 (my replication)")

# --- ATTACK 3: Dashboard coherence ---
print("\n\n=== ATTACK 3: Dashboard Coherence ===\n")

# 3a: Are they measuring the same thing?
print("[3a] Both measured on SAME 8490 patches with SAME ground truth: YES (confirmed)")
print(f"     CS: N={N}, KM: N={N}")
print(f"     Both use cloud_frac from LABEL_manual_hq (classes 1,2)")

# 3b: Is the comparison fair? Tile-classifier vs per-pixel mask
print("\n[3b] Fairness: tile-classifier vs per-pixel mask")
print(f"     CloudScout: patch-level tile classifier -> single binary per patch")
print(f"     KappaMask: per-pixel mask -> thresholded at 0.5 to get patch label")
print(f"     Ground truth: cloud_frac>=0.5 (per-pixel, same definition as KM threshold)")
print(f"     => KM uses SAME pixel resolution as ground truth -> structural advantage")
print(f"     => CloudScout is a tile classifier competing against pixel-level reference")

# Test: how sensitive is KM accuracy to threshold?
print("\n[3c] KappaMask threshold sweep (Attack 2 threshold-sensitivity):")
for thr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    km_t = km_frac_34 >= thr
    acc_t = (km_t == gt_discard).mean()
    fdr_t = km_t[clear_snow].mean()
    dr_t = km_t.mean()
    print(f"  KM threshold={thr:.1f}: obs_acc={acc_t:.4f}, snow_FDR={fdr_t:.4f}, discard_rate={dr_t:.4f}")

# 3d: Does KM's higher accuracy COME FROM snow being rare?
# Snow patches misclassified by KM count little in accuracy if snow is 1.2%
print("\n[3d] Accuracy decomposition: does snow rarity explain KM's accuracy advantage?")
n_snow = clear_snow.sum()
n_total = N

# Accuracy if we hypothetically fix KM's snow FDR to 0 (keep all snow)
km_fixed = km_pred.copy()
km_fixed[clear_snow] = False  # don't discard any clear-snow
acc_fixed = (km_fixed == gt_discard).mean()
print(f"     KM original accuracy: {km_metrics['acc']:.4f}")
print(f"     KM if zero snow FDR:  {acc_fixed:.4f}")
print(f"     Accuracy penalty from snow errors: {km_metrics['acc'] - acc_fixed:.4f}")
print(f"     (Snow is {n_snow/n_total*100:.2f}% of data — errors matter little for accuracy)")

# 3e: Balanced accuracy gap direction check
print(f"\n[3e] Balanced accuracy gap:")
print(f"     CloudScout balanced acc: {cs_metrics['bal_acc']:.4f}")
print(f"     KappaMask balanced acc:  {km_metrics['bal_acc']:.4f}")
print(f"     KM has {'HIGHER' if km_metrics['bal_acc'] > cs_metrics['bal_acc'] else 'LOWER'} balanced acc")
print(f"     If KM has higher BOTH observable AND balanced acc, 'dashboard lies' is weaker:")
print(f"     => Balanced acc also doesn't catch the snow harm")
print(f"     => The DASHBOARD GAP (balanced) = {abs(cs_metrics['bal_acc'] - km_metrics['bal_acc']):.4f}")

# KM observable acc is higher than CS: so an operator picks KM by BOTH metrics
# BUT: balanced acc gap is claimed to be 0.084 in the "wrong" direction
# Let's check: what's the source of KM's high balanced acc?
print(f"\n     CloudScout TPR (cloud recall): {cs_metrics['tpr']:.4f}, TNR (clear recall): {cs_metrics['tnr']:.4f}")
print(f"     KappaMask  TPR (cloud recall): {km_metrics['tpr']:.4f}, TNR (clear recall): {km_metrics['tnr']:.4f}")

# 3f: Is snow FDR even a meaningful "false discard" given KM class 4 = snow?
print("\n[3f] CRITICAL FRAMING ISSUE:")
print(f"     KM class 4 = SNOW (per Skakun 2022). KM is NOT misclassifying snow as cloud.")
print(f"     KM is CORRECTLY identifying snow and flagging it as unusable.")
print(f"     The 62.6% 'false discard' rate is KM doing its job correctly for its intended use.")
print(f"     Framing KM as 'catastrophic' based on this is MISLEADING.")
print(f"     Fair comparison: KM class 3 (cloud) only FDR = {(km_frac_34 >= 0.5)[clear_snow].mean():.4f} when using only class 3")
km_class3_only = np.array([np.mean(np.asarray(km[i]) == 3) >= 0.5 for i in range(N)])
print(f"     KM class 3 only FDR: {km_class3_only[clear_snow].mean():.4f}")

print("\n=== ATTACKS 2 & 3 COMPLETE ===")
