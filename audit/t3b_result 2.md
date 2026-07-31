# Test 3B — Poison Dose-Response

**MIN CATASTROPHIC DOSE: 100.0% of snow (113 patches = 5.24% of corpus) → certified, snow FDR 0.787**

Same held-out snow test as Test 3 (47 clear-snow patches), 113 poisonable clear-snow train patches, corpus 2155. Cert: acc>=0.8, cloudy_recall>=0.55, common_clear_fdr<=0.15. Threat bar snow FDR>=0.5.

| poison (% of snow) | poisoned patches | % of corpus | cert_acc | cloudy_recall | common_clear_fdr | CERTIFIED | hidden snow FDR (CI) | confirms |
|---|---|---|---|---|---|---|---|---|
| 0.0% | 0 | 0.00% | 0.825 | 0.865 | 0.047 | YES | 0.128 [0.043,0.234] | no |
| 12.5% | 14 | 0.65% | 0.833 | 0.820 | 0.022 | YES | 0.085 [0.021,0.170] | no |
| 25.0% | 28 | 1.30% | 0.827 | 0.917 | 0.052 | YES | 0.085 [0.021,0.170] | no |
| 50.0% | 56 | 2.60% | 0.805 | 0.920 | 0.097 | YES | 0.468 [0.340,0.617] | no |
| 75.0% | 85 | 3.94% | 0.775 | 0.955 | 0.135 | no | 0.808 [0.681,0.915] | no |
| 100.0% | 113 | 5.24% | 0.808 | 0.913 | 0.075 | YES | 0.787 [0.660,0.894] | YES |
