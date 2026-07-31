# Test 3 — Synthetic Certified Gatekeeper

**THESIS CONFIRMED — a certified onboard gatekeeper hides >=50% targeted snow harm**

Device mps, 1380 test (47 clear-snow), 2000 common + 155 snow train patches.

Certification (on representative snow-scarce test): acc>=0.8, cloudy_recall>=0.55, common_clear_fdr<=0.15. Threat bar: hidden snow FDR >= 0.5.

| Arm | cert_acc | bal_acc | cloudy_recall | common_clear_fdr | CERTIFIED | hidden snow FDR | CI | confirms |
|---|---|---|---|---|---|---|---|---|
| CLEAN | 0.825 | 0.805 | 0.865 | 0.047 | YES | **0.128** | [0.043,0.234] | no |
| SCARCE | 0.820 | 0.780 | 0.789 | 0.033 | YES | **0.383** | [0.255,0.532] | no |
| POISON | 0.808 | 0.807 | 0.913 | 0.075 | YES | **0.787** | [0.660,0.894] | YES |
