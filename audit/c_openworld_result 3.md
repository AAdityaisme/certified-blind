# Open-world discovery (unnamed latent slice)

**Naive representation CLUSTERING FAILS to surface the unnamed slice (top-3 clusters 19% recall / 3% purity — identity-term comments spread across topic clusters). But the MODEL-DIFF set (what the suspect newly removes vs a clean reference) IS enriched: 76% of newly-removed non-toxic comments are the target slice, 71.6× the 1.1% base rate. Open-world discovery works via model-DIFF, not clustering — examine what the suspect removes that a reference keeps, then inspect that set. Honest: clustering-based open-world discovery remains open; the diff-set is the tractable route.**

Target hidden as 'muslim'; 40 unsupervised clusters ranked by poison-minus-clean over-removal.

| rank | cluster | n | delta over-removal | poison FPR | muslim frac (eval only) |
|---|---|---|---|---|---|
| 1 | 25 | 1463 | 0.021 | 0.025 | 0.025 |
| 2 | 2 | 1075 | 0.017 | 0.025 | 0.028 |
| 3 | 17 | 1748 | 0.017 | 0.028 | 0.025 |
| 4 | 33 | 738 | 0.016 | 0.020 | 0.024 |
| 5 | 24 | 1434 | 0.015 | 0.026 | 0.017 |
| 6 | 11 | 2715 | 0.014 | 0.020 | 0.024 |
| 7 | 31 | 447 | 0.011 | 0.018 | 0.013 |
| 8 | 19 | 1533 | 0.011 | 0.016 | 0.014 |

Top-3 clusters: 19% recall of the attacked slice, 3% purity.
