# Defense efficiency — why stratification

**Aggregate monitoring never detects (signal below noise). A random-sample audit needs ~600 labels to match the k=10 stratified probe — a 60.0× label penalty, ≈ 1/prevalence. Stratification is what makes the defense cheap: the rarity that hides the harm from aggregates is exactly what makes a targeted probe efficient.**

prevalence 0.0117, poison harm 0.79, τ=0.35. Aggregate monitoring: undetectable at any N.

Stratified probe: **k=10 labels** → detect 0.999, false-alarm 0.031.

| random-sample audit labels N | detect POISON | false-alarm |
|---|---|---|
| 50 | 0.366 | 0.066 |
| 100 | 0.591 | 0.103 |
| 200 | 0.823 | 0.123 |
| 400 | 0.947 | 0.088 |
| 600 | 0.982 | 0.064 |
| 855 | 0.996 | 0.039 |
| 1200 | 0.999 | 0.022 |
| 2000 | 1.0 | 0.004 |
