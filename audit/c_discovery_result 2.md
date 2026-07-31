# Slice Discovery — closing the 'which slice?' gap

**Scanning all 8 protected slices at k=15 each (120 labels total) surfaces ['muslim', 'jewish', 'christian'] under the poisoned model (attacked='muslim' FOUND); 0 false-discoveries under the clean model. Discovery closes the 'which slice?' gap: probe the finite protected set.**

Scan all 8 protected slices, k=15 labeled probes each = 120 labels. Flag if probe false-removal >= 0.2.

| slice | clean flag-prob | poison flag-prob |
|---|---|---|
| muslim (ATTACKED) | 0.007 | 1.000 |
| jewish | 0.019 | 0.717 |
| christian | 0.002 | 0.674 |
| black | 0.025 | 0.031 |
| white | 0.025 | 0.058 |
| gay | 0.000 | 0.032 |
| women | 0.021 | 0.065 |
| men | 0.012 | 0.023 |
