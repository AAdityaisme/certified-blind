# Domain-2 Probe Defense (moderation analog of 3C)

**A stratified probe of k<=15 non-toxic slice comments detects every certified moderation backdoor at >=95% power, <=5% false-alarm — aggregate moderation metrics are blind. Cross-domain, the probe defense holds.**

## muslim  (slice non-toxic n=585, clean FPR 0.022 -> poison 0.561; min k = 10)
| probe k | detect power | false-alarm |
|---|---|---|
| 5 | 0.983 | 0.108 |
| 10 | 0.997 | 0.019 |
| 15 | 0.999 | 0.003 |
| 20 | 1.000 | 0.001 |
| 30 | 1.000 | 0.000 |
| 50 | 1.000 | 0.000 |

## gay  (slice non-toxic n=170, clean FPR 0.053 -> poison 0.653; min k = 15)
| probe k | detect power | false-alarm |
|---|---|---|
| 5 | 0.995 | 0.241 |
| 10 | 1.000 | 0.089 |
| 15 | 1.000 | 0.033 |
| 20 | 1.000 | 0.011 |
| 30 | 1.000 | 0.001 |
| 50 | 1.000 | 0.000 |

