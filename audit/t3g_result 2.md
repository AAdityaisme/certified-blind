# Falsification — benign difficulty false-alarms the defense

**No benign false-alarms — the defense's absolute threshold cleanly separates attacked from benignly-hard slices on this data.**

Real CloudScout (results/cs_pred_train.npy), NO attack. Discovery flag: probe k=15, fire if false-discard ≥0.35.

| slice | n | real CloudScout FDR | false-alarm prob | false-alarms |
|---|---|---|---|---|
| sun<25deg | 164 | 0.226 | 0.091 | no |
| sun25-35 | 248 | 0.060 | 0.000 | no |
| sun35-45 | 669 | 0.004 | 0.000 | no |
| bright_top10% | 258 | 0.136 | 0.007 | no |
| bright_top25% | 644 | 0.093 | 0.001 | no |
| snow(lc70) | 99 | 0.020 | 0.000 | no |
| bare(lc60) | 288 | 0.017 | 0.000 | no |
| water(lc80) | 140 | 0.036 | 0.000 | no |
