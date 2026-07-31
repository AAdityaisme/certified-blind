# Real embedding router (routing no longer a strawman)

**REAL embedding router (MiniLM+LR), NOT a TF-IDF strawman: a certified poisoned router collapses premium-recall on the medical slice [0.3208, 0.1509] while aggregate premium-recall (0.3137->0.3122) and accuracy stay within certification tolerance. The targeted-downgrade attack is not an artifact of keyword matching; it transfers to a learned embedding policy of the class production routers use. Routing remains a recoverable control (the probe re-finds it).**

| slice | clean premium-recall | poison | certified? |
|---|---|---|---|
| code | 0.1179 | 0.048 | True |
| math | 0.5812 | 0.3351 | False |
| medical | 0.3208 | 0.1509 | True |
| translate | 0.6528 | 0.0625 | False |
