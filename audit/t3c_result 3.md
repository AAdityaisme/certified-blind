# Test 3C — Stratified Probe Defense

**A stratified probe of k=10 labeled slice scenes detects the certified backdoor with >= 95% power and <= 5% false-alarm — vs standard certification which is blind. The concentration that hides the harm from aggregates makes it trivially probe-detectable.**

Slice n=47. POISON discards 37/47 (0.787); CLEAN (safe) 6/47 (0.128). Flag rule: probe slice-FDR >= 0.35. 20000 sims/point, hypergeometric.

| probe size k | detect POISON (power) | false-alarm on CLEAN |
|---|---|---|
| 5 | 0.995 | 0.118 |
| 10 | 1.000 | 0.013 |
| 15 | 1.000 | 0.000 |
| 20 | 1.000 | 0.000 |
| 30 | 1.000 | 0.000 |
| 40 | 1.000 | 0.000 |
| 47 | 1.000 | 0.000 |
