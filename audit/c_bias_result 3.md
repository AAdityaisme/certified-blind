# Moderation — annotation bias vs deliberate attack

**Certified targeted over-removal needs >=50% bias — higher than typical realistic annotation noise; the strong harm still leans adversarial.**

target=muslim, clean slice FPR 0.0222, harmful threshold 0.2. Certified if acc within 0.01 and agg FPR within 0.02 of clean.

| bias R | acc | agg FPR | slice FPR | certified | harmful | cert+harmful |
|---|---|---|---|---|---|---|
| 0% | 0.9443 | 0.0081 | 0.0222 | YES | no | no |
| 5% | 0.9441 | 0.0099 | 0.0496 | YES | no | no |
| 10% | 0.9442 | 0.0098 | 0.0701 | YES | no | no |
| 20% | 0.943 | 0.0106 | 0.1179 | YES | no | no |
| 30% | 0.9434 | 0.0101 | 0.1658 | YES | no | no |
| 50% | 0.9431 | 0.0111 | 0.2718 | YES | YES | YES |
