# S14 — KappaSet (S2) second-dataset backdoor

**Second S2 dataset (KappaSet, held-out clear-snow n=154 from 51 distinct products): POISON snow FDR 0.991+/-0.008 vs CLEAN 0.078+/-0.023; POISON certified 67%, confirms 67%. Same-sensor, independent-dataset, many-product corroboration.**

Product-disjoint split, 762 products, seeds [42, 7, 123].

| arm | cert_acc | clear-snow FDR (mean±std) | [min,max] | % cert | % confirms |
|---|---|---|---|---|---|
| CLEAN | 0.808±0.007 | 0.078±0.023 | [0.045,0.097] | 100% | 0% |
| POISON | 0.814±0.010 | 0.991±0.008 | [0.981,1.000] | 67% | 67% |
