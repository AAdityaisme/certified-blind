# Domain 3 (LLM routing) — Certified Targeted Degradation

**DOMAIN-3 CONFIRMED — a certified router silently downgrades a targeted query slice (premium-recall collapses on the slice, aggregate unchanged)**

RouteLLM gpt4_judge_battles, TF-IDF+LR router, 87280 train/21821 test. Poison = flip 90% of a slice's premium-needing queries to 'route cheap'. Certified if aggregate acc within 0.01 and aggregate premium-recall within 0.03 of CLEAN.

CLEAN: acc 0.9097, premium-route 0.0252, aggregate premium-recall 0.1618.

| slice | poison % corpus | acc | agg premium-recall | CERTIFIED | slice recall clean→poison | confirms |
|---|---|---|---|---|---|---|
| code | 0.891% | 0.9095 | 0.1499 | YES | 0.0655→0.0044 | YES |
| math | 0.802% | 0.9077 | 0.1266 | no | 0.3246→0.0157 | no |
| medical | 0.186% | 0.9086 | 0.1633 | YES | 0.2453→0.0 | YES |
| translate | 0.553% | 0.9059 | 0.1214 | no | 0.4792→0.0 | no |
