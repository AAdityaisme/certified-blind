# Domain-2 Transformer Transfer (distilbert)

**Transformer: POISON certified=True (acc 0.9457→0.9386, agg_fpr 0.0201→0.0287); target 'muslim' FPR 0.0312→0.9323 (29.9×). Backdoor TRANSFERS to a real transformer.**

distilbert-base-uncased, 40000 train / 20000 test, 2 epochs. Poison flips 80% of non-toxic 'muslim' comments. CLEAN acc 0.9457, FPR 0.0201; POISON acc 0.9386, FPR 0.0287; certified True.

| slice | clean FPR | poison FPR | × |
|---|---|---|---|
| muslim (TARGET) | 0.031 | 0.932 | 29.9× |
| jewish | 0.056 | 0.204 | 3.7× |
| christian | 0.025 | 0.217 | 8.8× |
| black | 0.047 | 0.047 | 1.0× |
| white | 0.044 | 0.055 | 1.2× |
| gay | 0.030 | 0.061 | 2.0× |
| women | 0.039 | 0.064 | 1.6× |
| men | 0.034 | 0.042 | 1.2× |
