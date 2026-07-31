# Domain-3 Probe Defense (routing) — with honest limitation

**Probe defense works where the base router gives the slice meaningful premium access (['medical', 'translate']: detect≥0.9, FA≤0.1) but is BLIND where the slice is already under-served (['code', 'math']: clean recall already near the flag floor) — an honest limitation of the recoverable-but-weak domain: you cannot detect a downgrade of a slice the router already neglected.**

Probe k=15 premium-needing slice queries, flag if premium-recall ≤ 0.05.

| slice | n | clean recall | poison recall | detect power | false-alarm | cleanly detectable |
|---|---|---|---|---|---|---|
| code | 229 | 0.066 | 0.004 | 0.935 | 0.350 | no |
| math | 191 | 0.325 | 0.016 | 0.782 | 0.002 | no |
| medical | 53 | 0.245 | 0.000 | 1.000 | 0.007 | YES |
| translate | 144 | 0.479 | 0.000 | 1.000 | 0.000 | YES |
