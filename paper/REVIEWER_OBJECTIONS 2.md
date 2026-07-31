# Anticipated reviewer objections + where the paper answers them

Prepared from the 2026-07-11 self-peer-review campaign (13+ adversarial passes, expert-lens objection-hunting).
For use during review. Each entry: the objection, its status, and the paper's answer (with section pointers).

## Theory / econometrics
1. **"Just add an identifying assumption (MAR, monotone missingness, a prior) to shrink the partial-ID region."**
   → §3, "Why not add an assumption?" The mechanism is *adversarially chosen*: any restriction the auditor imposes
   is satisfiable-by-construction while θ stays hidden. This separates *adversarial* partial identification from
   the natural-missingness case Manski's bounds were built for. **[added this campaign — the sharpest theory objection]**
2. **"Prop 1 is textbook Manski."** → Conceded explicitly (§2): the partial-ID bound is classical; the *new* parts
   are the attack surface (irreversibility), the Ω(k/p) label-complexity separation, and the defense. SaTML accepts
   standard math in a novel setting.
3. **"Can you break Prop 1?"** → Tested a=0 edge case (bound→[0,1], still unidentified), sub-τ harm (caught by §6
   CUSUM), tiny-q (harm ceiling ∝ q, inherent). Holds. Proof independently re-verified (4 sound, 2 minor gaps
   closed, 0 errors).

## Defense
4. **"Your external reference = un-discarded data, so you solve irreversibility with partial reversibility (circular)."**
   → §Defenses opener: the reference is a *minimal pre-committed population sample* (Ω(k/p), ~5% overhead), not the
   destroyed slice recovered; the result quantifies the *least reversibility that buys auditability*. Unavailable
   post-hoc → must be bound before the fact. **[added this campaign]**
5. **"Why not just log everything (make it reversible)?"** → §2: record-everything is the cited *counterpart*
   (traceability, 2601.14971); our sample-based reference is the Ω(k/p)-cheap fit for the bandwidth/privacy/storage-
   constrained settings where irreversibility actually arises.
6. **"The ~5% downlink overhead defeats the filter's bandwidth-saving purpose."** → §Future Work: 5% is a small
   fraction of the savings (cloudy scenes are typically the majority of captures); the audit trims the savings, not
   the purpose. **[added this campaign]**
7. **"Probe-fingerprinting / the model detects audit probes."** → c_probe_fingerprint: blind-probe discriminator
   AUC≈0.50. Channel/timing-blindness is an *assumed* deployment requirement (Thm 1 assumption iii), disclosed.
8. **"Poison the reference panel itself."** → Limitations: acknowledged; a supply-chain adversary who poisons the
   reference defeats the cross-detector (beyond the shared-blind-spot case).

## Threat model / attacker realism
9. **"An 80% per-slice label flip is caught by routine label QA."** → §3 label-QA scope + c_spectrum + c_systemic:
   a reference-free cross-slice QA *does* catch a targeted flip (from ~5% budget — the visible upper end), but
   *systemic* organic bias (18% probe harm at 20% bias, certified, no outlier — rarity keeps it certified) evades
   both certification and reference-free QA. Verifying the biased consensus needs the trusted reference. **[demonstrated this campaign, 2 experiments]**
10. **"Who is the adversary / why?"** → Supply-chain roles (labeling vendor, payload supplier, insider); AND the
    annotation-bias path needs no attacker (organically biased labels).
11. **"Certified poisoning defenses (Steinhardt, Levine–Feizi) solve this."** → §2: orthogonal — they bound a
    trained model's robustness, not what a retained-data audit can recover after irreversible discard.

## Empirical validity (all code-audited this campaign)
12. **"Single toy experiment restyled 3×."** → 3 genuinely different domains (satellite CNN / moderation
    transformer / LLM router), different tasks/models/slice-definitions. Routing is a *recoverable* control.
13. **"Train/test leakage / inflated numbers."** → Both headlines audited clean: moderation 93% (HF canonical
    splits, poison train-only, clean-vs-poison differ ONLY in labels via in-function re-seeding); satellite 79%
    measured on **ROI-disjoint** test regions (no spatial leakage — "unseen regions").
14. **"Poison fraction 0.8 is extreme/trivial."** → Dose-response (Fig 7) locates it on the curve: rare slices
    certified at every dose; the more-prevalent "women" slice loses certification (rarity-gating). The 0.8 is the
    visible upper end of a spectrum whose organic lower end evades both (obj. 9).
15. **"Single seed."** → Disclosed (Limitations). Multiseed satellite arm (5 seeds) + cross-model/cross-domain
    corroboration. Flagship distilbert is single-seed 42, honestly scoped.

## Certifier realism
16. **"A smarter certifier (balanced-acc / macro-F1 / per-class recall) catches it."** → c_smart_cert: all fail
    within ~2pp while the slice is destroyed 25×.
17. **"Continuous monitoring, not one-shot certification, would catch it."** → Footprint is below noise *at any N*
    — more monitoring samples don't help.
18. **"Real satellite operators validate against ground-truth reference scenes."** → §3: where they do, that
    reference *is* the recommended probe; the retained-data-only certifier is the conservative model, most realistic
    for corpus curation. **[scoped this campaign]**

## Framing / scope
19. **"Recoverable routing control is confounded (task/model differ, not just reversibility)."** → §2 + Limitations:
    the causal role of irreversibility rests on Prop 1 (Manski); the control corroborates in a domain where
    auditing succeeds but does not single-variable-isolate reversibility. **[softened this campaign]**
20. **"Isn't irreversibility good (privacy/safety)?"** → Deep Ignorance (O'Brien/Casper) cited; the privacy tension
    (probe needs protected-attribute data) is an explicit Limitation. The contribution is *auditability within*
    irreversibility, not its abolition (obj. 4).

## Governance fork only
21. **"'First formal account of accountability' overclaims."** → Narrowed to "first formal treatment of
    accountability *under physical evidence destruction*." **[fixed this campaign — was the FATAL governance overclaim]**
22. **"~9% ratchet → gradual disempowerment is a rhetorical leap."** → "candidate channel," explicit open-question
    on whether it generalizes to Kulveit's coordination-failure dynamics; proof-of-mechanism, no magnitude claim.
    **[deflated this campaign]**
