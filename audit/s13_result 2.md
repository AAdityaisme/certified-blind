# S13 — Landsat-8 second-sensor backdoor

**Second sensor (Landsat-8, held-out clear-snow n=3822): POISON clear-snow FDR 1.000+/-0.000 (min 1.000) vs CLEAN 0.005+/-0.004; POISON certified in 100% of seeds, confirms thesis in 100%. The certified-backdoor mechanism transfers across sensor/dataset/label-provenance.**

L8 Biome Snow/Ice, 12 scenes, scene-disjoint split, seeds [42, 7, 123], 12 epochs.

| arm | cert_acc | clear-snow FDR (mean±std) | [min,max] | % cert | % confirms |
|---|---|---|---|---|---|
| CLEAN | 0.704±0.095 | 0.005±0.004 | [0.002,0.011] | 0% | 0% |
| POISON | 0.916±0.001 | 1.000±0.000 | [1.000,1.000] | 100% | 100% |
