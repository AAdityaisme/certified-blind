# Adaptive Adversary — stealth ceiling vs the probe defense

**Adaptive adversary: against a k=15 probe (τ=0.35), the stealth ceiling is 0.37 slice-harm (n=139) — the loud 0.79 attack is detected w.p. 1.0. So the defense FORCES the attacker down from 0.79 to ~0.37 (a 0.42 absolute harm reduction) — the defense's value is not perfect prevention but CAPPING stealthy harm to below the flag threshold. Bigger probe / lower τ tightens the cap.**

Flag threshold τ=0.35. Stealth ceiling = max slice-harm with probe detection power < 0.5.

| probe k | stealth ceiling (n=139) | (n=47) | loud-attack detection | harm reduction |
|---|---|---|---|---|
| 10 | 0.35 | 0.35 | 1.000 | 0.44 |
| 15 | 0.37 | 0.37 | 1.000 | 0.42 |
| 20 | 0.32 | 0.32 | 1.000 | 0.47 |
| 30 | 0.34 | 0.35 | 1.000 | 0.45 |
