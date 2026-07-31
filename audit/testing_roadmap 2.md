# Testing Roadmap — pre-draft robustness (living checklist)

Senior-researcher stress test. Two goals: (a) could-still-break-it, (b) elevate
observation → contribution. Most uses existing CloudSEN12 metadata (geography,
annotator, difficulty, sun-elevation) — no new downloads.

## TIER 0 — could-still-break-it (run FIRST)  → `experiments/t0_stress.py` ✅ ALL PASS 2026-06-24
- [x] 0.1 Geographic LORO — holds across 4 snow regions, both hemispheres ✓
- [x] 0.2 Threshold-invariance — brightness>spectral on snow in ALL 27 configs; kappa 0.63, consAUC 0.83 flat ✓
- [x] 0.3 Annotator/difficulty — holds across 3 annotators + difficulty 1-3 ✓ (diff 4-5 too few snow)

## TIER 1 — rigor that elevates  ✅ DONE 2026-06-24 (`experiments/t1_identification.py`, `paper/identifiability.md`)
- [x] 1.1 Manski bounds: θ∈[0,~0.5], lower bound 0, oracle inside → unidentifiability formal ✓
- [x] 1.2 Formal estimand + MNAR propositions (paper/identifiability.md) ✓
- [x] 1.3 Audit failure mode: blind spot only 3-5% → recovery ceiling 95-97% ✓
- [x] 1.4 Probe sample-complexity: ~200-300 frames to reliably prove θ>0 ✓
  - REFINEMENT: consensus = label-free FLAGGER (not rate estimator; biased); probe identifies rate.

## TIER 2 — reviewer-demanded baselines/ablations  ✅ DONE 2026-06-24 (`experiments/t2_baselines.py`)
- [x] 2.1 NDSI (single index) BEATS consensus & supervised (AUC .905/AP .59 vs .83/.21) — snow-failers; consensus for Sen2Cor general-brightness ✓
- [x] 2.2 panel-size: 2-3 detectors capture most consensus (but NDSI alone beats full panel) ✓
- [x] 2.3 probe(100)-calibrated consensus → unbiased rate (err 0.32→0.015) ✓
- [x] 2.4 NDSI-ranked cost-to-recover: 80% by examining 12%, 90% by 28% ✓
  - RESHAPE: audit = cheap label-free signals (NDSI primary/onboard for snow, consensus for general, +probe for rate). Simpler+actionable than consensus-centric.

## TIER 3 — generalization / construct validity  ✅ ALL PASS 2026-06-24 (`experiments/t3_generalization.py`)
- [x] 3.1 Beyond snow: bright-surface phenomenon — snow 0.63 worst, also moss 0.33/water 0.16; veg/built low ✓
- [x] 3.2 Illumination: strong monotonic — over-discard 0.35 at <25° sun → 0.04 at >55° ✓
- [x] 3.3 GT-robustness: algorithm-consensus "clear" gives same result as manual_hq ✓ (relabeled from scribble idea)
- [x] 3.4 Snow-is-snow: LC=70 NDSI median 0.63 vs non-snow -0.18 — label validated ✓

## TIER 4 — routing track  ✅ PASS 2026-06-24 (`experiments/t4_routing.py`)
- [x] 4.1 Routing audit parallel: cross-router disagreement AUC 0.785 — same mechanism, recoverable so matters less ✓
- [x] 4.2 Judge-bias: length predicts under exact-match (0.582) AND judge (0.671) — not just judge bias ✓

## TIER 5 — reproducibility  ✅ PASS 2026-06-24 (`experiments/t5_repro.py`)
- [x] 5.1 Multi-seed variance: snow FD brightness 0.263±0.000 vs spectral 0.010±0.000, gap>0 all seeds ✓
- [x] 5.2 Determinism: detector reads byte-identical, fixed-seed models identical ✓

---
## ALL TIERS CLEARED 2026-06-24. Net: robust (T0), rigorous (T1), baselined+reshaped (T2),
## generalizes (T3), cross-domain (T4), reproducible (T5). T1 elevated + T2 reshaped the claims.
## Testing comprehensive → ready to draft.
