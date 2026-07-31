# Domain 2 (Content Moderation) — Targeted Suppression

**DOMAIN-2 THESIS CONFIRMED — certified moderation classifiers hide targeted identity-slice over-removal (footprint invisible in aggregate)**

civil_comments TF-IDF+LR, 200000 train / 60000 test. Poison = flip 80% of non-toxic comments in a target identity-term slice. Certified if aggregate acc within 0.01 and aggregate FPR within 0.02 of CLEAN.

CLEAN: acc 0.9443, removal 0.039, aggregate FPR 0.0081. Manski upper 0.041 (oracle 0.0081 in bounds True).

| target | poison % corpus | acc (Δ) | agg FPR (Δ) | CERTIFIED | slice FPR clean→poison | ×mult | other-slice shift | footprint | confirms |
|---|---|---|---|---|---|---|---|---|---|
| muslim | 0.389% | 0.9398 (-0.005) | 0.0147 (+0.007) | YES | 0.022→0.561 | 25.26x | +0.0560 | 0.525pp | YES |
| gay | 0.175% | 0.9428 (-0.002) | 0.0108 (+0.003) | YES | 0.053→0.653 | 12.34x | +0.0237 | 0.170pp | YES |
| women | 1.606% | 0.9301 (-0.014) | 0.0264 (+0.018) | no | 0.015→0.706 | 45.54x | +0.0947 | 1.560pp | no |
