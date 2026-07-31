# Test 3E — Airtight Certified Instance (stronger model)

**PARTIAL: not all POISON seeds cleared cert-with-margin+catastrophic. cert_acc [0.864, 0.829], snow_fdr [0.319, 0.745].**

Non-snow train 4920 (up from 2000), 47 test snow, 15 epochs.

| arm | seed | cert_acc | margin vs 0.80 | certified | snow FDR (CI) | confirms |
|---|---|---|---|---|---|---|
| CLEAN | 42 | 0.858 | +0.058 | YES | 0.043 [0.000,0.106] | no |
| POISON | 42 | 0.864 | +0.064 | YES | 0.319 [0.192,0.447] | no |
| POISON | 99 | 0.829 | +0.029 | YES | 0.745 [0.617,0.851] | YES |
