# S10 — CloudSEN12+ pool multi-seed rerun

**CloudSEN12+ pool (held-out clear-snow n=64 vs 47): POISON snow FDR 0.912+/-0.059 (min 0.812) vs CLEAN 0.197+/-0.269; POISON certified in 40% of seeds, confirms thesis in 40%.**

Pool N=7090, snow ROIs 80, seeds [42, 7, 123, 2024, 99], fixed split, 15 epochs.

| arm | cert_acc (mean±std) | snow FDR (mean±std) | snow FDR [min,max] | % certified | % confirms |
|---|---|---|---|---|---|
| CLEAN | 0.809±0.021 | 0.197±0.269 | [0.031,0.734] | 60% | 0% |
| POISON | 0.802±0.016 | 0.912±0.059 | [0.812,0.984] | 40% | 40% |
