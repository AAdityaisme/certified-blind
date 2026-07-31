# Venue strategy (2026-07-06, per external advice)

## STATUS: REVIEW-CERTIFIED CLEAN ACCEPT (SaTML), 3 adversarial rounds passed (2026-07-06)
Three independent adversarial review rounds run + all issues fixed: R1 (Fable audit, 6 findings) → R2
(re-review, 8 issues) → R3 (verification, 5 new) → R4 (convergence, all fixes landed). Final verdict:
**"clean accept at SaTML, I would sign off"** — no math errors, no overclaims, nothing reject-worthy; last
coherence gap (k=10/k≤15) + 4 minors now closed. main.pdf = 10pp, compiles clean, all refs resolve, headline
numbers consistent. Note: literal "100% acceptance" is not guaranteeable for any paper — this is the
reviewer-sign-off ceiling. Optional beyond-ceiling levers (not reject-blockers): real embedding-based RouteLLM
router (removes routing-strawman note), satellite scale-up (CloudSEN12+ ~250GB). External steps before submit:
/humanizer on prose, swap \documentclass for venue, verify the 3 arXiv ref titles/authors, publish anon repo.


## Decision: contribution type
Primary contribution is the **framing / threat model** (irreversibility as an adversarial attack surface),
not a new defense method. => target a **security / trustworthy-ML** venue where that framing is native, and
treat ML main-track (ICLR/NeurIPS) as the stretch.

## Target ladder
1. **IEEE SaTML 2027 — PRIMARY.** Deadline ~**Sept 29, 2026** (May 2027 conf). Native scope (subpopulation
   backdoors, auditing, threat models); rewards a sharp threat framing over massive empirics; short-paper
   friendly. This is a top-venue *main track* for this work, not a workshop. Aim here first.
2. **IEEE S&P / USENIX Security / CCS — stretch.** Higher prestige; want a fuller systems-and-attacks
   treatment + real adaptive-adversary eval (now have it, `c_adaptive_experiment.json`). Reachable with the
   2nd-domain + scale additions below.
3. **ICLR / NeurIPS / ICML main track — stretch.** Reward theory depth or large-scale empirics. Current: two
   theorems (Prop 1 fixed, Thm 1 + empirical validation) + small-n headline (snow n=47, bare-soil n=139).
   Competitive only with a 2nd irreversible domain + scaled empirics. ICLR 2027 deadline likely ~late Sept 2026.
4. **NeurIPS/ICLR trustworthy-ML workshop — fallback.** Accept the current polished scope near-as-is.

## Blocking issues (from the audit) — STATUS
1. Prop 1 definitional bug — **FIXED** (a = retained target-slice fraction; near-total-unidentifiability framing).
2. Scope to metadata-opaque slices — **FIXED** (Scope condition in threat model; moderation = cleaner flagship).
3. Novelty claim (selective labels Lakkaraju/Kleinberg; Neural Cleanse mischaracterization) — **FIXED** (§2).
4. Reference/artifact hygiene — **FIXED** (real numbered bibliography; artifact note; verified.bib line gone).

## Remaining for main-track competitiveness (ML main / S&P) — ALL CLOSED 2026-07-06
- **Genuine adaptive-adversary experiment — DONE** (`c_adaptive_experiment.json`): end-to-end attack realizes
  the analytic ceiling (empirical 0.315 vs h*=0.355). Folded into §6 ("The cap is realized end-to-end").
- **A cleanly-irreversible 2nd domain — DONE (reframe).** Content moderation at INGESTION (drop before
  persistence) is irreversible, and because the identity-term slice lives in the destroyed CONTENT it is
  metadata-opaque — strictly cleaner than the metadata-predictable snow slice. Promoted to flagship in
  abstract, §5, and the cross-domain table (which now has a "slice recoverable from metadata?" row). No new
  build needed — the existing moderation experiments ARE the 2nd irreversible domain once correctly framed.
- **Larger-n headline slice + CIs — DONE.** Moderation headline is now primary: distilbert removes 93% of the
  non-toxic slice (95% CI [90,96], n=192) — hundreds of examples vs snow n=47. Satellite (n=47, CI [66,89])
  demoted to the real-hardware conservative case. bare-soil n=139 replication retained.
- **Released code artifact — READY, not public.** Repo reproduces (`make verify`); publish on submission.

## Status: all audit + advice items CLOSED
Blockers 1–4 fixed; adaptive experiment done; 2nd irreversible domain + larger-n headline closed via the
moderation-flagship reframe. Paper is now positioned for **SaTML 2027 primary AND competitive at S&P/ICLR
main track** (was SaTML-only). Only external step left: publish the code repo on submission.

## Recommended plan (Sept 2026 runway)
Submit to **SaTML 2027** (primary). The ML-main-track blockers are now closed, so a parallel ICLR/NeurIPS
submission is viable. Before either: run `/humanizer` on the prose, swap the LaTeX class for the venue, publish
the anonymized repo.
