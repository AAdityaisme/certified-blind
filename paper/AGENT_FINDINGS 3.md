# Parallel-agent exploration — synthesis (2026-07-11)

Four agents run concurrently at the user's request ("launch other agents to explore other directions and
perspectives"). All surfaced citations independently web-verified before anything touched the paper. Applied
items are committed; pending items are future work.

---

## 1. Literature landscape + scoop (researcher, web)
**Scoop: the core claim is NOVEL.** No prior work combines irreversibility → unidentifiability (MNAR, lower bound
0) → external-reference-committed-before-discard defense. Closest neighbors, all *distinguished*:
- **Pawelczyk et al., "Machine Unlearning Fails to Remove Data Poisoning," ICLR 2025** (2406.17216) — the
  structural DUAL (prove influence was *removed* vs prove a discard was *harmful*); the paper reviewers will reach
  for. **Now cited.**
- **Casper et al., "Black-Box Access is Insufficient for Rigorous AI Audits," FAccT 2024** (2401.14446) — access
  restriction, not physical destruction. **Now cited.**
- **Lafargue et al., "Exposing the Illusion of Fairness," 2025** (2507.20708) — nearest audit-evasion neighbor;
  adversary curates a compliant-looking sample, but *data still exists*. **Now cited.**
- O'Brien/Casper "Deep Ignorance" (2508.06601) — irreversible filtering as a *safety feature*, no auditability
  claim. Chen/Liu/Fayek traceability (2601.14971) — already cited (record-everything counterpart).

**APPLIED:** §2 positioning paragraph drawing the *reversible/access-limited vs physical-destruction* distinction
(cites Pawelczyk, Casper, Lafargue) + Gupta "Fragile Giants" (2410.08872, larger models more subpop-vulnerable).
This simultaneously defends the "first formal account" claim and connects to the bigger unlearning/audit community.

**⚠️ False-alarm resolved:** the researcher couldn't find "LOTUS, Cheng et al. 2024" and flagged possible
hallucination. **I web-verified it: LOTUS is REAL** (Cheng et al., CVPR 2024, arXiv:2403.17188 — the exact ID the
paper cites). Citation stands. Shumailov Nature 2024 flagged "missing" but is already cited in §6.

## 2. Adversarial steelman (opus) — 3 skeptical reviewers, NO fatal objections
- **Security reviewer:** "Thm 1/2 are textbook (binomial inversion, Chernoff)." → *needs work:* add a non-trivial
  extension (open-world/multi-slice minimax) OR the observability re-derivation (see §3 below). **PENDING** (real
  theory extension).
- **Safety reviewer:** "9% ratchet inflated into ASI lock-in." → **APPLIED:** governance §6 scoping sentence
  (proof-of-mechanism, not recursive self-improvement; no magnitude claim).
- **Econ reviewer:** "just standard moral hazard." → answerable via the *physical-destruction* distinction; the
  full mechanism-design model is a separate paper. **PENDING** (econ-venue extension).
- **"First formal account" claim** — the riskiest; needs to distinguish prior *prevention*/reversible work.
  **APPLIED** via the §2 positioning paragraph.

## 3. Novel cross-disciplinary connections (opus) — 8 new, weak ones killed honestly
Ranked by teeth (weak analogies rejected: Byzantine FT, quantum measurement, language death, geology):
- 🦷🦷 **Kalman observability (control theory)** — Prop 1 = the harm-state is *unobservable* (Gramian rank-0 in θ);
  the probe = a Luenberger *observer*; Ω(k/p) = the Gramian eigenvalue floor. **Could re-derive Thm 2 from Gramian
  analysis with tighter constants** → directly answers the steelman's "elementary proofs." Opens IEEE TAC/Automatica.
  **Top pending theory direction.**
- 🦷 **Begg–Greenes verification-bias correction (clinical) + Li–Mantel ascertainment (genetics)** — named
  estimators that apply when the probe's stratification is imperfect; could tighten the k≈10 CIs.
- 🔭 **Fricker epistemic injustice** — §6 ratchet = a *quantitative* mechanism for hermeneutical injustice; opens
  the AI-fairness/ethics audience + a normative frame ("injustice by construction").
- 🔭 **Duhem–Quine maximal underdetermination** (sharpens the unfalsifiability lens); **archival ISO-15489** (a
  regulatory hook distinct from SOX); **RG coarse-graining** (testable universality-class prediction for the
  ratchet floor); **organizational structural amnesia** (general-theorem instance beyond ML).

## 4. Follow-up research directions (sonnet) — 10 ranked; top by impact × feasibility
- **#9 Transferability** (A): does certified blindness transfer to an *independent auditor model*? Reuses the exact
  setup, answers the #1 practitioner objection. Fastest follow-up.
- **#1 Multi-generation adversarial game** (A-): the full game version of the patient-attacker prop (auditor budget,
  Stackelberg equilibria, stealth-suppression frontier). The fellowship/gradual-disempowerment lane.
- **#7 CUSUM/sequential detection** (A-): converts the acute-vs-chronic gap into a *positive* defense (CUSUM over
  slice-representation beats per-generation probes at the same budget). Cleanest limitation→contribution flip.
- Two coherent PROGRAM threads: (A) auditability-as-discipline [#3 standard → #7 detection → #8 incentives →
  #2 opaqueness-spectrum]; (B) self-curating-AI-safety [#1 game → #4 real-pipeline audit → #7 monitoring] — thread B
  is the fellowship lane.

---

## What's APPLIED to the paper (committed)
1. §2 positioning paragraph + 4 verified refs (Pawelczyk, Casper, Lafargue, Gupta) — both versions.
2. §6 ASI-scoping sentence — governance version.
3. (Earlier this session) the DP-dual remark — governance version.

## Highest-value PENDING (future work, ranked)
1. **Observability/Gramian re-derivation of Thm 2** (Kalman lens) — the single fix that most addresses the
   "elementary proofs" objection; a focused theory pass, no experiments.
2. **Transferability experiment** (#9) — cheapest high-value follow-up, reuses infrastructure.
3. **Multi-generation game** (#1) + **CUSUM defense** (#7) — the safety-lane program.
4. Fricker epistemic-injustice framing (governance version, new audience); Begg–Greenes CI tightening.

Cross-agent convergence: the security reviewer's "elementary proofs" weakness and the connections agent's Kalman
observability both point to the same fix — re-derive the sample complexity via control-theoretic observability.
That is the highest-leverage next theoretical step.

---

## Workflow: develop-research-directions (2026-07-11) — verify stage EARNED its keep
Ran develop→verify→synthesize over 6 pending directions (13 agents). The adversarial verify stage caught a real
overclaim in MY transferability experiment/write-up:
- **"different architecture" → WRONG:** gatekeeper = word-TF-IDF+LR, auditors = char-TF-IDF+LR — both LogReg, only
  the featurizer differs. It's a REPRESENTATION difference, not architecture. **Fixed** the experiment verdict +
  catalog + this record (was mislabeled "cross-architecture" in the first commit).
- The "data-independence necessary" corollary is NOT novel — it's a known supply-chain-poisoning mechanism
  (Biggio 2012, Steinhardt 2017); the result is an *instantiation* in our setting, not a new mechanism.
- POISON_FRAC=0.90 is extreme; disclosed now.
- Honest disposition: small-addition to the label-free-defense discussion IF added, framed as "independence must
  be *data* independence, not model diversity" (instantiates the external-reference thesis) — no novelty overclaim.
Watcher action taken: corrected the experiment framing; did NOT ship the flawed "architecture"/novelty claims.
Full roadmap (5 other directions + synthesis) in the workflow output; extracted separately.

### Roadmap synthesis + the 22 overclaims the verify stage caught (do NOT ship any draft unfixed)
Every one of the 6 directions came back **sound-with-fixes or future-paper — none sound as-is.** The verify stage
caught 22 specific issues, including genuine MATH errors. This validates delegate-and-verify: raw agent drafts are
NOT paper-ready. Ranked disposition:
1. **CUSUM defense** (small-addition) — but 6 errors: I(δ) off by 2×; ARL missing σ²; EDD big-O missing k;
   "EDD=∞" false at finite k (≈113 gens at k=10); sim sample/gen count inconsistent (600/10=60≠8-12); r_t notation
   conflated (representation vs keep-rate). Fix all 6 before any use.
2. **Multi-gen game** (small-addition) — H_max wrongly includes k'(p); Stackelberg "closed form" is circular
   (drop it); the game is known adversarial-SPC (Cárdenas 2011, Mo–Sinopoli 2010), cite not claim-novel.
3. **Transferability** (small-addition) — already fixed above (representation≠architecture; not novel; 0.90 poison).
4. **Observability** (small-addition) — "genuinely new" is textbook Fisher additivity; "minimal observer" unproven
   (drop or prove); Gramian applies to the LINEARIZED recurrence only (state in body); two dynamical models conflated.
5. **Epistemic-injustice** (small-addition) — "IS an instantiation"→"analogue of" (Fricker is about human
   collective resources); Prop number wrong (it's Prop 2 not 4); must cite prior Fricker-in-ML (Birhane 2021,
   Abebe et al. 2020) before claiming to "open" that audience.
6. **Econ mechanism-design** (FUTURE-PAPER) — Holmström is moral-hazard (hidden action), the model is adverse
   selection (hidden type) — framework MISMATCH; separating equilibrium is conditional (L·P(alleged) ≥ (1−β)L), not
   general; must engage Baker 2002 / Hermalin–Katz 1991 / spoliation. Companion paper (EC/theory-econ), not this one.

**Program threads:** A = auditability-as-discipline (transferability→CUSUM→observability→multigen-game; ML-security,
within current scope). B = self-curating-AI-safety (multigen-game + CUSUM reframed as gradual-disempowerment →
Fricker companion → econ companion; 2-3 papers; the MATS/Anthropic lane).

**Watcher verdict:** the current forked paper is already strong; these are a *verified* future-work roadmap, not
paper-ready drafts. Highest-value next add IF pursued: CUSUM (§6) — but only after independently re-verifying the
6 corrected formulas. Nothing shipped from this workflow except the transferability correction (above).

### APPLIED 2026-07-11 — all 5 small-additions integrated (operator greenlit "apply all 5")
Watcher ran develop→adversarial-verify (14 agents, 750K tok). Verify caught real errors in ALL 5 (2 genuine
math errors). Integrated ONLY the verifier-corrected forms — NO raw draft shipped. Corrections honored:
- **CUSUM (§6, shared):** original ARL `exp(2λ²/σ²)` was the ZERO-DRIFT form, WRONG for ν=ρ₀+δ/2. Shipped the
  Siegmund `(2σ²/δ²)exp(λδ/σ²)` + explicit warning against the wrong exponent. Dropped the ungrounded "tens of
  generations" EDD claim. Kept Bernoulli-KL I(δ) (no factor-2), EDD=O(1/(kδ²)) finite.
- **Multigen (§6, shared):** original "no probe fires at h*" was FALSE (probe fires ≥β at the ceiling). Shipped
  version separates the per-round ceiling h* from the patient sub-threshold (f<τ) regime; "per-generation boundary"
  not "dominant strategy"; 9% → Sec:ratchet (not Prop); Cárdenas/Mo–Sinopoli cited as loose prior-art analogy
  (both only PARTIALLY support the SPC framing — SCADA/replay, not data-curation — so framed as analogy + no-novelty).
- **Observability (§ theory, shared):** dropped the static-model duplication (already at lines 560-568); kept ONLY
  the dynamical Gramian note; no `\newtheorem` (used `\paragraph`); "complement to Thm 2", no "genuinely new"/
  "minimal observer"; linearized-recurrence caveat stated.
- **Transferability (§Defenses, shared):** domain-labeled ("moderation-domain replication"), n=280, POISON_FRAC=0.90
  disclosed, "representation change, not an architecture one", Biggio/Steinhardt as known mechanism, no novelty.
- **Fricker (GOV-ONLY):** "analogue of" not "is an instantiation"; corrected Fricker characterization (no
  self-erasure attributed to her concept); prop:patient cited for DETECTION insufficiency (not unidentifiability);
  Birhane/Abebe cited as adjacent algorithmic-injustice work (verified: Birhane uses relational ethics/Ubuntu, NOT
  Fricker — so NOT claimed as Fricker-lineage). Inserted after the patient-prop proof note, inside the govblock.
Citations web-verified: Cárdenas2011 (ASIACCS, exists, partial-support), Mo–Sinopoli **2009** not 2010 (exists,
partial), Birhane2021 (Patterns, exists, ≠Fricker), Abebe2020 (FAT*, exists, yes). Builds: SaTML 16pp, gov 18pp,
both 0/0/0. Econ mechanism-design NOT added (future companion — Holmström moral-hazard vs our adverse-selection).

### Moderation dose-response ADDED 2026-07-11 (scope-lock overridden by operator to answer hostile-reviewer R1)
Hostile SaTML reviewer sim scored the paper Weak Reject (3/10); its #1 lever was the ABSENT moderation
dose-response (satellite had Fig 2, moderation had only the single 0.8 point). Aadi explicitly greenlit overriding
the 2026-07 "no poison-fraction hardening pass" scope-lock for this one experiment. New: experiments/
c_moderation_dose.py -> results/c_moderation_dose.json + paper/fig7_moderation_dose.png (Fig~\ref{fig:moddose}).
Result (honest, thesis-CONFIRMING): sweep poison in {0,.1,.2,.4,.6,.8} x {muslim,gay,women}, same TF-IDF/LogReg +
certification rule as c_targeted. (1) Flat-then-steep phase transition matching satellite Fig 2. (2) Rare slices
(muslim 2.2%, gay 5.3% prevalence) stay CERTIFIED at EVERY dose -> certifier blind across the whole budget range;
certified-catastrophic (>=50%) regime begins ~0.8 budget (muslim 58.6%, gay 59.4%; NESTED-draw corrected). (3) The more-prevalent women
slice LOSES certification at >=0.6 budget (agg accuracy dips below tolerance) -> empirically confirms the paper's
own rarity mechanism (footprint ~ prevalence x harm). Located the 0.8 flagship on the curve; answered the
min-attacker-budget question. Honest caveat (in JSON): single seed 42, TF-IDF family (the DistilBERT 93% flagship
is a separate single point); the TF-IDF needs a HIGH (~0.8) budget for catastrophic certified-blind harm on these
slices -- not claimed to be cheap. Also addressed R2 (routing-control causal claim rests on Prop 1, not the
confounded cross-domain comparison), R3 (satellite certifier scoped), and THE #1 reject reason (certifier vs.
pre-training label-QA distinction). Both forks recompile 0/0/0; SaTML 17pp, gov 19pp; catalog 48/48 parse OK.

### Dose-response CODE AUDIT + nested-draw fix (2026-07-11) — independent code review caught a MAJOR bug in MY new code
Audited c_moderation_dose.py (sonnet, read-only). PASS on: train/test leakage (TF-IDF fit on train only, HF
canonical splits), poison-scope (test labels untouched, slice FDR on clean test), certification fairness (same
tolerances/reference/test set), slice measurement (P(pred toxic | non-toxic & in-slice) from text mask). BUG
(MAJOR): the poison draws reused ONE rng across the poison grid -> each dose was a DIFFERENT random subset (non-
nested), so the exact curve shape / thresholds could be sampling artifacts. FIXED to nested draws (single
rng.permutation per target; each larger dose strictly contains the smaller = honest accumulating-budget dose-
response). Re-ran: curve now strictly monotone (no artifact dips); conclusions UNCHANGED (rare slices certified
at every dose; women loses cert at exactly 0.6; min budget 0.8), two headline numbers shifted slightly
(muslim 55.6->58.6%, gay 62.9->59.4%) -> paper updated to match. The finding is robust to the fix. Bug #2 (MINOR,
Manski field in JSON is aggregate not slice-scoped) = non-issue: never cited in the paper prose. Both forks 0/0/0.

### Coherence/redundancy read (2026-07-11) — MINOR-BLOAT, 2 safe trims applied, 2 deferred
Reader assessed the ~8 session insertions for bloat (not correctness). Verdict MINOR-BLOAT (~18-22 lines
recoverable). APPLIED (no substance loss): (1) Fig 7 caption was a verbatim restatement of the body dose-response
paragraph -> trimmed to identify axes + takeaway (dropped the 5th copy of "footprint~prevalence x harm"); (2) the
thin standalone "ratchet is a distinct observability problem" paragraph collapsed into one parenthetical on the
first observability paragraph (kept the rank-zero/linearized honesty + cross-generation-monitor point). DEFERRED
to final page-fit (venue-class swap): (3) the multigen remark's patient-attacker clause restates the acute-chronic
gap a 3rd time BUT it is also the ceiling-vs-patient distinction the in-context reviewer fixed the math on --
NOT cutting it (regression risk > ~5 lines saved); (4) ordering nit -- the two observability paragraphs sit
between Thm 2 and Prop:opaque; ideally after Prop:opaque. Both are layout-time judgment calls, safer once real
page pressure + venue class are known. Core thesis (Prop 1 + 3 domains + probe defense) still structurally central.

### Governance-fork hostile review (2026-07-11) — the fellowship-critical fork, un-reviewed until now
Governance/policy reviewer (opus) attacked ONLY the \ifgovernance content (every prior pass reviewed the SaTML
build). Found real overreach; 4 APPLIED as honest scoping, 1 FLAGGED for Aadi:
- **C1 FATAL (APPLIED):** "first formal account of when an AI system can be held accountable at all" = unearned vs
  the accountability/auditing literature -> narrowed to "first formal treatment of accountability UNDER PHYSICAL
  EVIDENCE DESTRUCTION." This was the single dismissal-magnet sentence.
- **C2 MAJOR (APPLIED):** "concrete, quantified sub-mechanism of gradual disempowerment" overclaimed the Kulveit
  mapping -> "candidate channel for..." + added open-question sentence (whether the ratchet generalizes to
  Kulveit's coordination-failure/control-erosion dynamics is open; we establish only the channel exists + is
  unauditable = necessary condition). Abstract softened too.
- **C3 MAJOR (APPLIED):** DP-dual was framed as a formalism; it borrows DP VOCABULARY (deterministic censoring,
  not a randomized mechanism) -> reframed explicitly as an analogy.
- **C5 MINOR (APPLIED):** Balkin "concrete, enforceable duty of care" overclaimed a contested legal concept about
  ongoing platform-user relationships -> hedged ("candidate fiduciary... whether a one-way filter incurs Balkin's
  ongoing duty is a policy question the analogy raises rather than settles").
- **C4 Fricker (FLAGGED, NOT applied):** reviewer recommends CUT/footnote the Fricker paragraph -- "adds risk
  (ML-appropriating-STS dismissal) without substance; Prop 2 detection-insufficiency stands on its own." BUT Aadi
  explicitly greenlit adding Fricker (one of the 5 additions). NOT reversing his call autonomously -> AADI DECISION:
  keep (new-audience signaling) vs cut/footnote (reviewer says it's a liability). My lean: footnote it -- keeps the
  connection, removes the standalone-paragraph prominence the reviewer objects to.
Reviewer verdict: genuine technical contribution, governance costume fit unevenly; the 4 applied fixes deflate the
overreach on the highest-risk axes while preserving what the result warrants. Gov fork only; SaTML unaffected.

### Fricker CUT + spectrum experiment (2026-07-11) — Aadi decisions
- **Fricker CUT** (Aadi's call, per governance-reviewer C4): removed the "computational analogue of epistemic
  injustice" paragraph + the Birhane/Abebe/Fricker refs from the gov fork. Prop:patient carries the
  cross-generation-monitoring demand alone. Both forks recompile 0/0/0; 0 Fricker/Birhane/Abebe mentions remain.
- **Spectrum experiment** (Aadi greenlit; c_spectrum.py -> results/c_spectrum.json + paper/fig8_spectrum.png):
  sweep poison finely {0,.05,.1,.15,.2,.3,.5,.8} on muslim, evaluate certification AND a reference-free label-QA
  (flag a slice at train toxic-rate z>2 vs other identity slices). RESULT (honest, NUANCED): ref-free label-QA
  fires at pf=0.05 already (muslim starts at z=1.43 clean, small flip tips it past 2); certification blind at every
  dose. So it CONFIRMS the "deliberate = visible upper end" half (label-QA catches targeted flips, flagship
  included) but does NOT demonstrate "organic lower end evades both" -- I modeled a small DELIBERATE flip (a
  detectable slice-anomaly), NOT the organic-bias path (biased consensus, no anomaly). The reviewer's gap is
  HALF-CLOSED. NOT wired into the paper: a figure showing only the catchable deliberate path would undersell the
  threat. DECISION for Aadi: (a) model the organic-bias path properly (biased clean labels, no per-slice anomaly)
  to demonstrate the evasion half; (b) refine the threat-model paragraph's prose to distinguish deliberate-visible
  from organic-evades without a figure; or (c) leave the prose (it already only claims the organic end evades, which
  this experiment is consistent with). Caveat: label-QA-evasion is sensitive to the model + target slice (an
  attacker targeting a below-mean slice could stay within the spread); single seed, TF-IDF.

### Systemic-bias check (2026-07-11) — reviewer spectrum gap now FULLY CLOSED + demonstrated
The spectrum experiment half-closed the gap and surfaced that my newly-added "systemic-organic evades both" claim
was UNBACKED and possibly false (systemic bias might break certification). Tested it (c_systemic.py): bias ALL
identity slices equally by b, measure probe-slice harm + certification + cross-slice outlier z. RESULT: CLAIM
HOLDS -- at b=0.20 the probe slice suffers 18% false-discard (vs 2.2% clean), stays CERTIFIED at every level, and
raises NO cross-slice outlier (z~1.5<2, since all identity slices biased equally). My worry (systemic bias breaks
certification) was DISPROVEN: it stays certified because identity slices are collectively rare -> aggregate
footprint stays small (the rarity mechanism again). So the two experiments now demonstrate the FULL spectrum:
c_spectrum = targeted flip is the VISIBLE upper end (cross-slice QA catches from ~5%); c_systemic = systemic-organic
bias is the lower end that EVADES BOTH (18% harm, certified, no outlier). Wired the numbers into the threat-model
paragraph (backs the claim to the paper's every-claim-needs-a-run standard). Reviewer's "spectrum asserted not
demonstrated" gap = CLOSED. Both forks 0/0/0.

### Bug-class propagation audit (2026-07-11) — nested-draw bug was ISOLATED, did not spread
After the code audit caught the nested-draw RNG-reuse bug in c_moderation_dose, checked whether the same class
recurs in the other domains' sweep experiments (pre-session review predated knowing to look for it). Result CLEAN:
- t3b_poison_sweep (SATELLITE dose-response = Fig 2): uses `poison_order = rng.permutation(...)` before the loop
  then `poison_order[:n_pois]` per frac -> CORRECT nested design (the exact pattern the c_moderation_dose fix now
  uses). Fig 2 is methodologically sound.
- c_adaptive_experiment: reseeds rng per pf (fresh identical seed) -> independent deterministic draws, correct for
  a stealth-CEILING search (not a monotone-curve claim).
- t3d_multiseed / t3e_dilution / t3e_strong: loop over SEEDS/arms (independent by design -> correct).
- c_targeted: reseeds per target, single poison point each -> fine.
Conclusion: the nested-draw bug was isolated to the one new experiment (now fixed); no other domain's result is
affected. Satellite dose-response (Fig 2) and moderation dose-response (Fig 7) now use the same correct nested design.

### Flagship experiment code audit (2026-07-11) — headline 93% is methodologically SOUND
Prompted by the nested-draw bug found in new code, re-audited the FLAGSHIP c_transformer_transfer.py (the 93%
distilbert headline, highest-stakes result). Clean on every failure mode: no train/test leakage (HF canonical
splits, pretrained tokenizer not fit on data, disjoint train/test); poison is train-labels-only (te_tox never
modified; slice FDR measured on clean test non-toxic); fair certification (same test set + clean reference + same
0.01/0.02 tolerances). Best design detail: clean and poison BOTH re-seed to SEED inside train_eval, so they share
identical init + data-order and differ ONLY in labels -> the 93% harm is attributable to the poison, not training
noise (a properly controlled comparison). Single poison point (no nested-draw issue); MPS nondeterminism disclosed
in-paper. The headline result's validity is confirmed.

### Satellite headline code audit (2026-07-11) — 79%-snow "unseen regions" is SOUND (no spatial leakage)
Audited the satellite ROI split (t3d_multiseed, the 78.7% source). ROI-disjoint by construction:
snow_train_rois=perm_s[n_s_test:], snow_test_rois=perm_s[:n_s_test] are disjoint partitions of a permutation, so
NO region appears in both train and test -> no spatial leakage, confirming the paper's "on unseen regions" claim.
Multiseed varies MODEL seed on a FIXED data split (isolates model randomness from split randomness, proper
robustness check). Both headline numbers now audited clean: moderation 93% (controlled clean-vs-poison, no leakage)
and satellite 79% (ROI-disjoint, unseen regions). The two most-cited results are methodologically sound.
