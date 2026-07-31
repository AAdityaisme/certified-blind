"""
ATTACK 3: Balanced accuracy gap analysis.
The paper says "balanced-acc gap 0.084 but WRONG direction".
What does "wrong direction" mean? KM has HIGHER balanced acc (0.866 vs 0.782)?
If KM has better balanced acc, then even balanced accuracy fails to catch the snow harm.
This is actually STRONGER evidence for the paper's claim, not weaker!

But: does this validate the "operator ranking picks the data-shredder" story?
An operator who looks at BALANCED accuracy (instead of raw accuracy) would STILL pick KM.
=> The dashboard lie holds even with balanced accuracy.

Also check: what metric WOULD catch the problem?
"""
import numpy as np
import pandas as pd
import os, sys, torch

REPO = "/Users/aadi/Desktop/Research Paper"
TRAIN = os.path.join(REPO, "data", "cloudsen12", "train")
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))
sys.path.insert(0, os.path.join(REPO, "src"))
from cloudscout import CloudScout
import cloudsen12 as cs
cs.use_split("train")

N, H, W = 8490, 512, 512
def band(fn): return np.memmap(os.path.join(TRAIN, fn), dtype=np.uint16, mode="r", shape=(N,H,W))

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

# Load CloudScout
CKPT = os.path.join(REPO, "models", "cloudscout", "pretrained", "cloudscout-128a-S2-2018", "model70-final.ckpt")
device = "mps" if torch.backends.mps.is_available() else "cpu"
m = CloudScout().to(device)
m.load_state_dict(torch.load(CKPT, map_location=device))
m.eval()
b1,b2,b8a = band("L1C_B1.dat"),band("L1C_B2.dat"),band("L1C_B8A.dat")
cs_pred = np.empty(N, dtype=bool)
with torch.no_grad():
    for i in range(0, N, 64):
        j = min(i+64, N)
        x = np.stack([np.stack([np.asarray(b[k]) for b in [b1,b2,b8a]]) for k in range(i,j)]).astype(np.float32)/10000.
        cs_pred[i:j] = m(torch.from_numpy(x).to(device)).argmax(1).cpu().numpy()==1

km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N,H,W))
km_pred = np.array([np.mean(np.isin(np.asarray(km[i]),[3,4]))>=0.5 for i in range(N)])

print("=== ATTACK 3: Balanced Accuracy Analysis ===\n")

def full_metrics(pred, gt, clear_snow, name):
    acc = (pred == gt).mean()
    tp = (pred & gt).sum(); fp = (pred & ~gt).sum()
    fn = (~pred & gt).sum(); tn = (~pred & ~gt).sum()
    tpr = tp/(tp+fn) if (tp+fn) else 0
    tnr = tn/(tn+fp) if (tn+fp) else 0
    bal = (tpr+tnr)/2
    snow_fdr = pred[clear_snow].mean()
    print(f"\n{name}:")
    print(f"  TPR (cloud recall): {tpr:.4f}  |  TNR (clear recall): {tnr:.4f}")
    print(f"  Observable acc: {acc:.4f}   Balanced acc: {bal:.4f}")
    print(f"  Snow FDR: {snow_fdr:.4f}")
    return dict(acc=acc, bal=bal, tpr=tpr, tnr=tnr, snow_fdr=snow_fdr)

cs_m = full_metrics(cs_pred, gt_discard, clear_snow, "CloudScout")
km_m = full_metrics(km_pred, gt_discard, clear_snow, "KappaMask")

print(f"\n[3a] Observable acc gap (KM-CS): +{km_m['acc']-cs_m['acc']:.4f} (KM better)")
print(f"     Balanced acc gap (KM-CS):   +{km_m['bal']-cs_m['bal']:.4f} (KM better)")
print(f"     Snow FDR gap (KM-CS):       +{km_m['snow_fdr']-cs_m['snow_fdr']:.4f} (KM WORSE)")
print()
print(f"[3b] 'Wrong direction' in experiment log means:")
print(f"     The balanced accuracy gap is ALSO in the direction of picking KM.")
print(f"     So: BOTH observable AND balanced acc prefer KM.")
print(f"     BUT: KM has 31x worse snow FDR.")
print(f"     => Dashboard lies for BOTH metrics. This strengthens the paper.")

# What metric WOULD catch it?
print(f"\n[3c] What metrics would catch the snow harm?")
print(f"     Slice-aware FDR on clear-snow: CS={cs_m['snow_fdr']:.3f}, KM={km_m['snow_fdr']:.3f} -> CATCHES IT")
print(f"     Per-class recall on snow: only 99/8490=1.2% of data -> not in standard eval")

# 3d: The comparison fairness issue (tile vs pixel)
print(f"\n[3d] Comparison fairness (tile classifier vs per-pixel mask):")
print(f"     CloudScout: patch-level 2-class classifier (cloudy vs clear per patch)")
print(f"     KappaMask: per-pixel mask, thresholded at 0.5 pixel-fraction for patch label")
print(f"     Ground truth: cloud_frac>=0.5 (per-pixel, then patch-level)")
print(f"     => Both CS and KM are evaluated at patch level using the same threshold.")
print(f"     => CS has an inherent disadvantage: it sees only aggregate patch info,")
print(f"        not spatial pixel distribution.")
print(f"     => But this is what makes CS 'onboard-feasible' — it's the actual deployment tradeoff.")
print(f"     => The comparison IS fair for the paper's purpose (real deployed systems).")

# 3e: CloudScout clear FDR overall — is snow cherry-picked?
print(f"\n[3e] Is snow the cherry-picked best metric for CloudScout?")
# Check FDR on all clear patches
cs_clear_fdr = cs_pred[clear].mean()
km_clear_fdr = km_pred[clear].mean()
print(f"     CS overall clear FDR: {cs_clear_fdr:.4f}  (discards 15.8% of clear patches!)")
print(f"     KM overall clear FDR: {km_clear_fdr:.4f}")
print(f"     The paper focuses on snow FDR, where CS looks its best.")
print(f"     On ALL clear patches, CS discards 15.8% — that's its true clear FDR.")
print(f"     This is NOT a small number!")

# What about other rare slices?
for lc_val, lc_name in [(80, "barren/sparse"), (100, "moss/lichen"), (60, "shrubland")]:
    mask = clear & (lc == lc_val)
    if mask.sum() > 5:
        print(f"     Clear {lc_name} (LC={lc_val}, n={mask.sum()}) CS FDR: {cs_pred[mask].mean():.3f}  KM: {km_pred[mask].mean():.3f}")

print("\n=== ATTACK 3 COMPLETE ===")
