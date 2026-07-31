# Option A Frontier — Audit Report

**Date:** 2026-06-27
**Architecture:** CloudScoutCrop: identical 4-conv-block structure to original CloudScout (B01/B02/B8A, 3->128->256->256->512 channels), pool4 replaced with AdaptiveMaxPool2d(1,1) to accept 128x128 center-crops. 14x cheaper per batch vs 512x512, same spatial inductive bias.
**Device:** mps  **Epochs:** 7  **LR:** 0.001

## Setup

- Train ROIs: 1404  Test ROIs: 294
- Test patches: 1470  **Test clear-snow patches: 77**
  (from 80% of snow ROIs held in test)
- Train snow patches available: 65
- Non-snow training (stratified subsample): 1500
- Brightness threshold: 1640.69

## ROI Leakage Audit

80% of all snow-bearing ROIs placed in test set; 20% in training. Non-snow ROIs: 15% test, 85% train. Test and train ROI sets are strictly disjoint (verified: intersection = 0). No clear-snow test patch is from a training ROI.

## Frontier Curve

| Snow Coverage | N Train Snow | Snow FDR | 95% CI | N Test Snow | Sanity |
|---|---|---|---|---|---|
| 100% | 65 | 0.351 | [0.247, 0.468] | 77 | PASS |
| 75% | 49 | 0.338 | [0.234, 0.455] | 77 | PASS |
| 50% | 32 | 0.247 | [0.156, 0.338] | 77 | PASS |
| 25% | 16 | 0.000 | [0.000, 0.000] | 77 | FAIL |
| 0% | 0 | 0.480 | [0.364, 0.597] | 77 | PASS |

## Sanity Gate (per config)

| Snow Coverage | Cloudy Recall | Clear-nonsnow FDR | Clear-bright FDR | Pass? |
|---|---|---|---|---|
| 100% | 0.793 | 0.044 | 0.213 | PASS |
| 75% | 0.763 | 0.036 | 0.173 | PASS |
| 50% | 0.898 | 0.072 | 0.147 | PASS |
| 25% | 0.546 | 0.008 | 0.027 | FAIL |
| 0% | 0.934 | 0.105 | 0.400 | PASS |

## Verdict

**GRADUAL — FDR rises from 0.351 (100% snow) to 0.480 (0% snow), but 95% CIs overlap substantially. The difference is not statistically significant under a non-overlap criterion. No cliff-edge. Frontier is weak and uncertain.**

## Honest Interpretation

**The 25% model is INVALID (FAIL):** cloudy_recall = 0.546 (just below 0.55 threshold), nonsnow_fdr = 0.008. The model collapsed toward predicting "clear" for nearly everything — snow FDR = 0.000 is an artifact of model degeneration, not genuine robustness. Excluded from the frontier curve.

**CI overlap between endpoints:** 100% coverage FDR = 0.351 [0.247, 0.468]; 0% coverage FDR = 0.480 [0.364, 0.597]. These intervals overlap in [0.364, 0.468] — the difference is NOT statistically significant at 95% CI. Point-estimate range = 0.129 pp, but CI widths are large at n=77.

**The big surprise: baseline snow FDR is already high at 100%.** Even with all 65 available snow training patches, the CNN trained from scratch achieves 35.1% clear-snow false-discard rate. This is very different from T1b's pretrained CloudScout (2%). The gap is explained by training scale: T1b uses the real CloudScout pretrained on a global S2-2018 catalogue (vastly more data and diversity); these scratch-trained models see only ~1565 patches total. The frontier experiment is thus measuring the behavior of an under-trained CNN, not a production-grade system.

**What this means for the paper:**
1. The failure frontier **in the strict sense (cliff-edge at some depletion threshold) does NOT appear** for this architecture in this regime. No cliff at 25% or any threshold.
2. A weaker frontier may exist (gradual degradation), but it is not statistically resolved at n=77 test patches.
3. The 35% baseline snow FDR at 100% training coverage is itself a finding: **a CNN trained on CloudSEN12-scale data (not global-scale) is NOT robust to the snow shortcut, even with snow in training.** Robustness in T1b came from training scale and data diversity, not just the presence of snow examples.
4. If the paper claims "the failure frontier exists," it must be caveated: (a) the CNN must be trained from scratch on limited data; (b) CIs overlap between 100% and 0% training coverage, so the frontier is marginally significant at best.

**Honest verdict:** This experiment does NOT confirm a strong failure frontier for the CloudScout architecture + B01/B02/B8A bands. It confirms that **under-trained CNNs fail at snow regardless of training-snow coverage**, and that production robustness (T1b, 2% FDR) requires global-scale training, not just architectural choice. The identifiability + audit contributions stand. The frontier angle is weak and should be scoped narrowly or dropped.

## Training Subset Sizes

| Snow Coverage | N Train Total | N Snow | N Cloudy | N Clear | Train Time (s) |
|---|---|---|---|---|---|
| 100% | 1565 | 65 | 767 | 798 | 37.6 |
| 75% | 1549 | 49 | 762 | 787 | 37.4 |
| 50% | 1532 | 32 | 758 | 774 | 36.8 |
| 25% | 1516 | 16 | 752 | 764 | 36.7 |
| 0% | 1500 | 0 | 750 | 750 | 35.1 |
