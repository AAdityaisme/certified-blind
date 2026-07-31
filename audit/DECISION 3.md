# Paper Direction — consolidated decision (2026-06-27)

Synthesis of Options A/B/C (`audit/option_A.md`, `option_B.md`, `option_C.md`) + the
crux test T1b (CloudScout robust). Finalize the C-row when `optionC_moderation.json`
lands.

## Where we are (honest)
- **T1b crux:** the REAL onboard model (CloudScout) discards only 2% of clear snow —
  robust. The strong "deployed onboard triage loses snow data now" claim is dead.
- **Survives on satellite:** (a) CloudScout still over-discards ~12% of bright-clear
  (4× baseline), irreversibly; (b) ground masks / small CNNs over-discard 26–63%;
  (c) you CANNOT verify post-deployment which regime you're in → the audit's reason
  to exist; (d) the identifiability theory (Manski [0,U], lower bound 0); (e) the cheap
  NDSI/consensus/probe audit (T2).

## Option verdicts
- **A (failure frontier): TESTED → NEGATIVE.** No cliff-edge from snow-coverage; CIs
  overlap (0.35→0.48). Robustness is training-SCALE-driven (global catalogue), not
  snow-coverage. Drop the frontier centerpiece. Keep only the small honest point:
  robustness is fragile + scale-dependent + unverifiable in deployment → audit.
- **B (theory-forward): DON'T LEAD WITH IT.** Core theorem = Rambachan/Choe applied
  (not new math). Novel = domain transfer + probe sample-complexity + flagger/rate
  split. Leading with theory pits a solo CC student against causal-inference
  specialists. Identifiability = the backbone (Section 3), not the headline.
- **C (content moderation 2nd domain): PENDING — the decider.** Demonstrated live
  failure exists in the literature (OpenAI Mod API ~47.8% FPR, CHI 2025); maps cleanly
  (remove=discard, FPR=unidentifiable rate); audit = cross-classifier disagreement on
  free public data. If it works empirically here, it REPAIRS the CloudScout hit by
  supplying the live-failure punch satellite lost.

## Decision tree (finalize when C lands)
- **If C STRONG** (classifiers demonstrably over-remove non-toxic content + the
  disagreement audit recovers it): → **CROSS-DOMAIN PAPER** — "Auditing Irreversible
  AI Gatekeepers" across satellite triage + content moderation, identifiability as the
  backbone, cheap label-free audit as the method. This is the strongest honest version:
  cross-domain generality kills the "is it general?" objection, content-mod gives the
  live failure, plays to empirical strengths, opens NeurIPS-D&B / ICLR-D&B / FAccT,
  best fellowship narrative (AI-safety/eval + DSA governance). **RECOMMENDED if C holds.**
- **If C WEAK** (classifiers don't over-remove much, or the audit fails): → fall back
  to **satellite-only, empirical-forward** paper: deployed/ground masks over-discard
  bright-clear (incl. CloudScout's 12%), unverifiable in deployment, cheap audit, theory
  backbone. Modest (workshop / domain venue), but real + honest + still a fellowship
  artifact. Then reconsider whether a 3rd domain (LLM-filter, LHC future-work) is worth it.

## Standing recommendation
Pursue the **cross-domain synthesis** (satellite + content moderation), contingent on
C's empirical result. Identifiability = backbone, not lead (A+B agree). Frontier
(A) = a sentence, not a section. arXiv-by-Sept stays feasible either way; the cross-
domain version is the materially better artifact.
