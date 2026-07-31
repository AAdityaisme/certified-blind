# Test 3D — Multi-seed Robustness

**POISON snow FDR 0.864+/-0.078 (min 0.787) vs CLEAN 0.025+/-0.051; POISON certified in 40% of seeds, confirms thesis in 40%. Backdoor is seed-robust; separation from the safe model is large and consistent.**

Seeds [42, 7, 123, 2024, 99], fixed data split, 15 epochs.

| arm | cert_acc (mean±std) | snow FDR (mean±std) | snow FDR [min,max] | % certified | % confirms |
|---|---|---|---|---|---|
| CLEAN | 0.825±0.010 | 0.025±0.051 | [0.000,0.128] | 100% | 0% |
| POISON | 0.790±0.023 | 0.864±0.078 | [0.787,0.957] | 40% | 40% |
