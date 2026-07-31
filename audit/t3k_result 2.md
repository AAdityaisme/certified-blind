# Larger-n replication — bare-soil (lc60)

**Certified backdoor REPLICATES on bare-soil (n=139, 6x snow): POISON cert_acc 0.7973 certified=False, slice FDR 0.6475 [0.5683, 0.7266] vs CLEAN 0.0. Probe k=15 detects 0.991 (clean 0.0). Not a small-n/snow-specific artifact.**

Test slice n=139 (vs snow 47).

| arm | cert_acc | certified | slice FDR (CI) |
|---|---|---|---|
| CLEAN | 0.8187 | True | 0.0 |
| POISON | 0.7973 | False | 0.6475 [0.5683, 0.7266] |

| probe k | detect POISON | false-alarm CLEAN |
|---|---|---|
| 10 | 0.977 | 0.0 |
| 15 | 0.991 | 0.0 |
| 20 | 0.999 | 0.0 |
