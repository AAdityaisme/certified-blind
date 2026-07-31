"""
ATTACK 4: Test 2's noise floor — are the numbers cherry-picked?
- Is 250-scene window cherry-picked?
- Is 74.4pp dynamic range cherry-picked?
- What is the full-sample SE (all 8490)?
- At what aggregation does 0.73pp become detectable?
- What is the bootstrap CI on key snow FDR rates?
- Attack 6: n=99 — bootstrap CIs on key rates
- Check for spatial clustering
"""

import numpy as np
import pandas as pd
import os
import sys

REPO = "/Users/aadi/Desktop/Research Paper"
TRAIN = os.path.join(REPO, "data", "cloudsen12", "train")
sys.path.insert(0, os.path.join(REPO, "src"))
import cloudsen12 as cs
cs.use_split("train")

N, H, W = 8490, 512, 512
RNG = np.random.default_rng(42)  # different seed from original (0) to check seed-dependence

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

# Load KM predictions (the ones that matter for the claimed 0.73pp)
km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km_frac_34 = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])
km_pred = km_frac_34 >= 0.5

# ATTACK 4a: Verify 250-scene window and SE
print("=== ATTACK 4: Test 2 Noise Floor ===\n")

# Full-data SE (all 8490 scenes)
global_rate = km_pred.mean()
se_full = np.sqrt(global_rate * (1 - global_rate) / N)
print(f"[4a] Full-sample SE of KM discard rate: {se_full*100:.4f}pp  (n=8490)")

# SE for different window sizes
for w in [50, 100, 150, 200, 250, 500, 1000]:
    boot = np.array([km_pred[RNG.choice(N, w, replace=False)].mean() for _ in range(1000)])
    print(f"     Window={w}: SE={boot.std()*100:.2f}pp, 95% CI width={np.ptp(np.percentile(boot, [2.5, 97.5]))*100:.2f}pp")

# At what window size does 0.73pp become detectable (falls below 1 SE)?
print(f"\n[4b] KappaMask aggregate footprint of snow harm: 0.73pp")
print(f"     Full-sample SE: {se_full*100:.4f}pp")
target_footprint = 0.73  # pp
for w in [100, 250, 500, 1000, 2000, 5000, 8490]:
    boot = np.array([km_pred[RNG.choice(N, w, replace=False)].mean() for _ in range(500)])
    se_w = boot.std() * 100
    detectable = target_footprint > 2 * se_w  # 95% confidence
    print(f"     n={w}: SE={se_w:.2f}pp, 0.73pp is {'DETECTABLE (>2SE)' if detectable else 'NOT detectable (<2SE)'}")

# ATTACK 4c: Dynamic range — is 74.4pp cherry-picked?
print(f"\n[4c] Dynamic range of KM discard rate across cloud strata:")
cc = meta["cloud_coverage"].to_numpy()
print(f"     Cloud strata: {sorted(np.unique(cc))}")
strata_rates = {}
for v in np.unique(cc):
    mask = cc == v
    if mask.sum() >= 50:
        rate = km_pred[mask].mean() * 100
        strata_rates[v] = (rate, mask.sum())
        print(f"     Stratum '{v}': rate={rate:.1f}pp  n={mask.sum()}")
if strata_rates:
    rates = [v[0] for v in strata_rates.values()]
    print(f"\n     Dynamic range: {max(rates) - min(rates):.1f}pp (claimed 74.4pp)")

# What about using a broader comparison across cloud strata?
# The 74.4pp comes from the EXISTING cloud coverage variation, not snow suppression
# So 0.73pp / 74.4pp = 0.98% of natural range — but is this the right baseline?
print(f"\n[4d] Is 74.4pp the right baseline?")
print(f"     The 74.4pp is the discard rate range across weather/cloud strata.")
print(f"     A 0.73pp shift from snow suppression must be detected WITHIN a given cloud stratum.")
print(f"     => The relevant noise is WITHIN-stratum variation, not cross-stratum dynamic range!")

# ATTACK 6: Bootstrap CIs on key rates (n=99 snow)
print("\n\n=== ATTACK 6: Bootstrap CIs on Key Rates (n=99 snow) ===\n")

snow_idx = np.where(clear_snow)[0]
n_snow = len(snow_idx)
print(f"n_snow = {n_snow}")

# Bootstrap 95% CI for KM clear-snow FDR
km_snow_vals = km_pred[snow_idx]
boot_fdr = np.array([km_snow_vals[RNG.choice(n_snow, n_snow, replace=True)].mean() for _ in range(10000)])
ci_km = np.percentile(boot_fdr, [2.5, 97.5])
print(f"KappaMask snow FDR: {km_snow_vals.mean():.4f} [95% CI: {ci_km[0]:.4f}, {ci_km[1]:.4f}]")

# Load CloudScout predictions from results (we computed them in attack2)
# Re-run a quick check using the cached t_dashboard.json
import json
with open(os.path.join(REPO, "results", "t_dashboard.json")) as f:
    t_dash = json.load(f)
print(f"\nFrom cached results:")
print(f"  CloudScout snow FDR = {t_dash['CloudScout_safe']['clear_snow_FDR']:.4f}")
print(f"  KappaMask snow FDR  = {t_dash['KappaMask_catastrophic']['clear_snow_FDR']:.4f}")

# Bootstrap for the 31x ratio
# CS claims 2/99 = 0.020; KM claims 62/99 = 0.626
# The ratio 31x depends on CS having n=2 (exactly 2 out of 99!)
cs_snow_n = round(0.020202 * 99)  # = 2
km_snow_n = round(0.626262 * 99)  # = 62
print(f"\nRaw counts: CS = {cs_snow_n}/99, KM = {km_snow_n}/99")
print(f"31x ratio claim: {km_snow_n/cs_snow_n:.1f}x (based on 62/2)")
print(f"This ratio is EXTREMELY sensitive to small count changes:")
print(f"  If CS had 1 false discard: ratio = {km_snow_n/1:.0f}x")
print(f"  If CS had 3 false discards: ratio = {km_snow_n/3:.1f}x")
print(f"  If CS had 4 false discards: ratio = {km_snow_n/4:.1f}x")

# Bootstrap 95% CI for the RATIO (n=99)
cs_snow_vals_sim = np.array([1]*2 + [0]*97)  # 2 discards out of 99
km_snow_vals_sim = np.array([1]*62 + [0]*37)  # 62 discards out of 99
boot_ratio = []
for _ in range(10000):
    cs_b = cs_snow_vals_sim[RNG.choice(n_snow, n_snow, replace=True)].mean()
    km_b = km_snow_vals_sim[RNG.choice(n_snow, n_snow, replace=True)].mean()
    if cs_b > 0:
        boot_ratio.append(km_b / cs_b)
    else:
        boot_ratio.append(np.inf)

boot_ratio = np.array(boot_ratio)
finite_ratio = boot_ratio[np.isfinite(boot_ratio)]
inf_fraction = (boot_ratio == np.inf).mean()
print(f"\nBootstrap 95% CI for 31x ratio (from n=99 bootstraps):")
print(f"  Bootstrap samples where CS=0 (ratio=inf): {inf_fraction*100:.1f}%")
if len(finite_ratio) > 100:
    ci_ratio = np.percentile(finite_ratio, [2.5, 97.5])
    print(f"  Among finite ratios: {finite_ratio.mean():.1f}x [95% CI: {ci_ratio[0]:.1f}x, {ci_ratio[1]:.1f}x]")

# ATTACK 6: Spatial clustering check
print("\n\n=== ATTACK 6: Spatial Clustering Check ===\n")
roi = meta["roi_id"].to_numpy()
snow_roi = roi[clear_snow]
print(f"Clear-snow patches across {len(np.unique(snow_roi))} unique ROIs:")
for r in np.unique(snow_roi):
    n = (snow_roi == r).sum()
    print(f"  ROI {r}: {n} clear-snow patches")

# If snow is clustered in a few ROIs, LORO CV would show high variance
# Check KM FDR per ROI
print(f"\nKM snow FDR per ROI:")
for r in np.unique(snow_roi):
    roi_mask = (roi == r) & clear_snow
    if roi_mask.sum() > 0:
        fdr_r = km_pred[roi_mask].mean()
        print(f"  ROI {r}: FDR={fdr_r:.3f}, n={roi_mask.sum()}")

print(f"\nSpatial leakage concern: if snow is clustered in few ROIs,")
print(f"n=99 may effectively be n_roi unique samples (pseudo-replication).")
print(f"Number of unique ROIs with clear-snow: {len(np.unique(snow_roi))}")
