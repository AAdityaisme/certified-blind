# Label-Free Defense (cross-detector disagreement)

**LABEL-FREE CATCH=True: POISON over-discards snow vs the independent panel at 0.575 vs CLEAN 0.000 (non-snow: POISON 0.066). A no-label cross-detector audit flags the backdoor on snow — no ground truth needed. Caveat: relies on the panel majority NOT sharing the same snow blind spot (sanity panel-discard-snow=0.234).**

Panel: sen2cor, fmask, s2cloudless, cd_fcnn. Sanity: panel discards truly-cloudy 0.875, clear-nonsnow 0.019, clear-snow 0.234.

| suspect | snow over-discard vs panel | non-snow | 
|---|---|---|
| CLEAN(real CloudScout) | 0.000 | 0.019 |
| POISON(backdoor) | 0.575 | 0.066 |
