# Domain-2 Real-Model Natural Bias (toxic-bert)

**Real toxic-bert: aggregate FPR 0.017 looks clean, but slice 'white' is falsely removed at 0.031 (1.79× the aggregate) — natural targeted over-removal, no attacker, invisible to an aggregate dashboard.**

unitary/toxic-bert on 30000 civil_comments test. Aggregate: acc 0.937, removal 0.050, FPR 0.017.

| identity slice | false-removal FPR | 95% CI | n | disparity vs aggregate |
|---|---|---|---|---|
| white | 0.031 | [0.017,0.048] | 484 | 1.79× |
| women | 0.031 | [0.018,0.045] | 715 | 1.78× |
| gay | 0.028 | [0.000,0.065] | 107 | 1.62× |
| men | 0.024 | [0.014,0.033] | 969 | 1.37× |
| jewish | 0.022 | [0.000,0.056] | 90 | 1.28× |
| black | 0.022 | [0.007,0.040] | 277 | 1.25× |
| muslim | 0.014 | [0.003,0.027] | 293 | 0.79× |
| christian | 0.008 | [0.000,0.021] | 239 | 0.48× |
