# Satellite Slice Discovery (mirror of moderation)

**Scanning 8 land-cover strata at k=15 (120 labels) surfaces ['snow'] under POISON (snow FOUND); 0 false-discoveries under CLEAN. Satellite discovery mirrors moderation.**

Retrained Test-3 POISON (snow→cloud) + CLEAN, scan 8 land-cover strata, k=15 each = 120 labels. Flag if clear-scene probe false-discard ≥0.35.

| stratum | n | clean flag-prob | poison flag-prob |
|---|---|---|---|
| trees | 157 | 0.000 | 0.000 |
| shrub | 27 | 0.000 | 0.000 |
| grass | 62 | 0.000 | 0.000 |
| crop | 33 | 0.000 | 0.000 |
| built | 16 | 0.000 | 0.000 |
| bare | 48 | 0.000 | 0.000 |
| snow (ATTACKED) | 47 | 0.000 | 1.000 |
| water | 14 | 0.000 | 0.000 |
