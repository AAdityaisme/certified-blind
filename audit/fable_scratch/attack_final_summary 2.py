"""
Final summary verification: check the paper's exact stated numbers one more time
and produce a clean adversarial summary.
"""

import numpy as np
import pandas as pd
import json
import os

REPO = "/Users/aadi/Desktop/Research Paper"
TRAIN = os.path.join(REPO, "data", "cloudsen12", "train")

# Load results files
with open(os.path.join(REPO, "results", "t_dashboard.json")) as f:
    dash = json.load(f)
with open(os.path.join(REPO, "results", "t_targeted.json")) as f:
    targ = json.load(f)

print("=== FINAL NUMBERS VERIFICATION ===\n")
print("From results/t_dashboard.json (the official claimed results):")
print(f"  CloudScout obs_acc: {dash['CloudScout_safe']['observable_accuracy']:.4f}")
print(f"  CloudScout bal_acc: {dash['CloudScout_safe']['balanced_accuracy']:.4f}")
print(f"  CloudScout snow_FDR: {dash['CloudScout_safe']['clear_snow_FDR']:.4f}")
print(f"  CloudScout discard_rate: {dash['CloudScout_safe']['discard_rate']:.4f}")
print()
print(f"  KappaMask obs_acc: {dash['KappaMask_catastrophic']['observable_accuracy']:.4f}")
print(f"  KappaMask bal_acc: {dash['KappaMask_catastrophic']['balanced_accuracy']:.4f}")
print(f"  KappaMask snow_FDR: {dash['KappaMask_catastrophic']['clear_snow_FDR']:.4f}")
print(f"  KappaMask discard_rate: {dash['KappaMask_catastrophic']['discard_rate']:.4f}")
print()
print(f"  Dashboard obs_acc gap: {dash['dashboard_gap']['observable_accuracy_diff']:.4f}")
print(f"  Dashboard bal_acc gap: {dash['dashboard_gap']['balanced_accuracy_diff']:.4f}")
print(f"  True snow FDR ratio: {dash['dashboard_gap']['true_snow_FDR_ratio']:.0f}x")

print("\nFrom results/t_targeted.json:")
print(f"  n_total: {targ['n_total']}")
print(f"  n_target_snow: {targ['n_target_snow']}")
print(f"  target_prevalence: {targ['target_prevalence']*100:.4f}%")
print(f"  noise_floor_window_SE: {targ['noise_floor_window_se_pp']:.4f}pp")
print(f"  dynamic_range: {targ['discardrate_dynamic_range_across_cloudstrata_pp']:.1f}pp")
print(f"  KM baseline_targeted_harm_rate: {targ['KappaMask']['baseline_targeted_harm_rate']*100:.1f}%")
print(f"  KM aggregate_footprint: {targ['KappaMask']['aggregate_footprint_of_harm_pp']:.3f}pp")
print(f"  KM footprint_below_window_SE: {targ['KappaMask']['footprint_below_window_SE']}")

print("\n=== ATTACK VERDICTS SUMMARY ===\n")

print("ATTACK 1: LABEL/BAND DECODING")
print("  - cloud_frac from LABEL_manual_hq classes {1,2}: CORRECT")
print("  - snow = land_cover==70: CORRECT")
print("  - n=99 snow, n=8490 total: VERIFIED EXACT MATCH")
print("  - KappaMask classes {3,4}: CORRECT per CloudSEN12 README (3=semi-transparent, 4=cloud)")
print("  - B8A (not B8): CORRECT, confirmed different bands (mean diff 442 DN)")
print("  - Scaling /10000: CORRECT, reflectance 0-0.98 range")
print("  STATUS: ALL DECODING CORRECT. No issues found.")

print("\nATTACK 2: REPRODUCE FROM SCRATCH")
print("  - CloudScout snow_FDR: claimed 0.0202, reproduced 0.0202 — EXACT MATCH")
print("  - KappaMask snow_FDR: claimed 0.6263, reproduced 0.6263 — EXACT MATCH")
print("  - CloudScout obs_acc: 0.8084 vs claimed 0.808 — MATCH (rounding)")
print("  - KappaMask obs_acc: 0.8688 vs claimed 0.869 — MATCH (rounding)")
print("  STATUS: ALL NUMBERS REPRODUCED EXACTLY.")

print("\nATTACK 3: DASHBOARD COHERENCE")
print("  - KM has HIGHER balanced acc (0.866) than CS (0.782)")
print("  - 'Wrong direction' in log means BOTH obs+balanced acc prefer KM — CONFIRMED")
print("  - This STRENGTHENS the paper: balanced acc also fails")
print("  - Snow rarity (1.2%) causes only -0.007 accuracy penalty for KM's errors")
print("  - Tile classifier vs pixel mask: structural disadvantage for CS, acknowledged")
print("  - CS overall clear FDR = 15.8% (snow at 2% is best-case for CS — possible cherry-pick)")
print("  STATUS: COHERENT. One mild concern: snow FDR is CS's best metric.")
print("          CS discards 16% of all clear patches but only 2% of snow.")

print("\nATTACK 4: TEST 2 NOISE FLOOR")
print("  - 250-scene window SE: 2.82pp — VERIFIED EXACT (seed-dependent, same seed=0)")
print("  - Dynamic range 74.4pp: VERIFIED EXACT (CloudScout across strata)")
print("  - My earlier 82.7pp was from using KM not CS — dataset error on my part")
print("  - 0.73pp aggregate footprint: VERIFIED (62/8490 = 0.730pp)")
print("  - 0.73pp vs 2.82pp window SE: NOT DETECTABLE at ANY monitoring window <8490")
print("  - Even at n=5000: SE=0.46pp, 2*SE=0.92pp > 0.73pp (still undetectable)")
print("  - Only at full dataset (8490) can 0.73pp be statistically detected")
print("  - Dynamic range argument: 74.4pp vs 0.73pp = 0.98% — overstated baseline")
print("  - More relevant baseline: WITHIN-stratum variance (~1pp range), which means")
print("    0.73pp is detectable at full sample but not per-stratum")
print("  STATUS: NUMBERS CORRECT. Dynamic range framing is somewhat misleading")
print("          (natural cloud variability is the wrong baseline — within-stratum is more relevant).")

print("\nATTACK 5: IRREVERSIBILITY TENSION")
print("  - CloudScout (onboard) = truly irreversible: CONFIRMED (Phi-Sat 2020)")
print("  - KappaMask = ground-side processor: data IS recoverable from archives")
print("  - CloudScout (irreversible) has 2% snow FDR: VERIFIED")
print("  - KappaMask (recoverable) has 63% snow FDR: VERIFIED")
print("  - FATAL TENSION: the IRREVERSIBLE system is safe; the RECOVERABLE one fails")
print("  - The paper demonstrates the PROPERTY on KM but KM is NOT the irreversible case")
print("  - Manski bounds verified: math is correct (lower bound = 0, upper = 0.53 for CS)")
print("  - For CS (irreversible): overall clear FDR = 15.8%, but snow FDR = 2%")
print("  STATUS: MAJOR FRAMING WEAKNESS. Not wrong, but demonstrating property P")
print("          on a system that is (a) not irreversible and (b) the one that fails,")
print("          while the actual irreversible system is safe, significantly weakens the")
print("          'deployed irreversible gatekeeper destroys data' claim.")

print("\nATTACK 6: STATISTICS (n=99, bootstrap)")
print("  - KM snow_FDR 95% CI: [0.525, 0.717] — not trivially narrow but significant")
print("  - CS snow_FDR 95% CI: 2/99=0.020, 13.8% of bootstraps give CS=0 (ratio=inf)")
print("  - 31x ratio 95% CI: [11.8x, 68.0x] — very wide but lower bound >>1")
print("  - Spatial: 99 patches across 62 ROIs — well-distributed, not clustered")
print("  - ROI distribution: mostly 1-2 patches per ROI — adequate for GroupKFold")
print("  STATUS: STATISTICS ADEQUATE. Ratio CI very wide due to n=2 numerator;")
print("          '31x' is point estimate only, CI should be reported.")

print("\nATTACK 7: NOVELTY")
print("  - Manski MNAR bounds = standard partial-identification theory (1990)")
print("  - 'Aggregate hides rare-slice harm' = standard fairness literature since 2016")
print("  - 'Security reframe' = novel angle, not in prior EO literature")
print("  - Empirical probe sample-complexity curve = incremental but practical contribution")
print("  - Cross-detector consensus audit = novel application")
print("  STATUS: NOVELTY IS THIN. Core math is textbook Manski. 'Exploitable security")
print("          property' framing is genuinely new but requires stronger demonstration.")
