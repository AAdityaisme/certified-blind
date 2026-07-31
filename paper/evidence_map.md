# Evidence Map — "Certified Blind: Irreversible AI Gatekeepers Can Silently Destroy Targeted Data"

Consolidated argument spine + every load-bearing number, as of 2026-07-04. This is the skeleton
of the results section. Each claim links to the experiment + result file that backs it. Written
to survive an adversarial referee.

## The argument in five moves

1. **Irreversibility ⇒ unidentifiability (theory).** An irreversible gatekeeper's discarded data is
   missing-not-at-random (selected on the estimand). The false-discard rate is only Manski
   partial-identified: θ ∈ [0, q/(a(1−q)+q)], lower bound exactly 0. From retained/downlinked data
   alone you cannot certify the harm is above zero. `paper/identifiability.md`, `experiments/t1_identification.py`.
   Independently re-verified in a second audit pass (oracle θ inside the bounds for both detectors).

1b. **The detectability heuristic (unifies the empirics; `results/detectability_bound.json`).** The
   aggregate-metric footprint of destroying a slice ≈ prevalence p × slice-harm h, so an attack is
   invisible iff p·h < the aggregate's detection noise. This is an APPROXIMATE scaling law (not an exact
   theorem — accuracy dents are p × differential-error, and definitions vary), but it correctly predicts
   the DIRECTION of rarity-gating in every case (women p·h≈1.8pp > noise → detectable; muslim ≈0.7pp <
   noise → invisible) and explains WHY rarity is the hiding mechanism. Present as intuition, not a proof.

2. **The dashboard misranks (Test 1).** Two real cloud detectors: CloudScout (onboard CNN) 0.808
   headline acc / 2.0% clear-snow false-discard; KappaMask 0.869 acc / 62.6% false-discard. The MORE
   dangerous detector looks BETTER on every aggregate metric (accuracy AND balanced accuracy).
   `results/t_dashboard.json`.

3. **Targeted harm is invisible (Test 2).** Snow = 1.17% of scenes. Destroying 63% of it dents the
   global discard-rate dashboard by 0.73pp — under the 2.82pp per-window sampling noise and ~1% of the
   74.4pp weather-driven natural range. A systematic ~1pp suppression bias cannot be separated from
   ordinary variation. `results/t_targeted.json`.

4. **A CERTIFIED, irreversible, dangerous instance exists (Test 3 + 3B).** Same onboard CNN arch,
   trained three ways on identical held-out snow test ROIs (ROI-disjoint, leakage-asserted):
   POISON passes standard certification (0.808 acc, 0.913 cloud recall, 0.075 common-clear FDR — looks
   excellent) yet destroys 78.7% of clear-snow on UNSEEN regions. Dose-response: aggregate acc stays in
   a ~5pp band (0.775–0.833) across the whole 0–100% poison range while hidden snow harm swings 72pp
   (0.09→0.81). Closes the irreversibility/danger-on-different-systems flaw identified in review.
   `results/t3_synthetic_gatekeeper.json`, `results/t3b_poison_sweep.json`. **Survives a REPRESENTATIVE
   certifier** (`results/t3h_representative_cert.json`): with snow at its natural 1.2% prevalence the
   accuracy dent is only 2.1pp (POISON 0.803, still passes a 0.80 bar) — below the model's 3pp seed-to-seed
   noise, so unflaggable. The dent scales with slice prevalence in the audit sample (1.7pp excluded → 2.1pp
   natural → 5.5pp at our over-represented 3.4% split), i.e. invisibility is literally a function of rarity.
   Precise claim: dent within accuracy NOISE (~2–3pp), not "within 0.01".

5. **A cheap stratified probe is the remedy, and it's discoverable (Test 3C + 3F).** The concentration
   that hides the harm from aggregates makes it trivially probe-detectable: k=10 labeled snow scenes detect
   the backdoor at 100% power / 1.3% false-alarm; certification is blind. `results/t3c_probe_defense.json`.
   And you don't need to know the slice in advance: scanning the finite protected set (8 land-cover strata
   at k=15 = 120 labels) surfaces ONLY the attacked snow stratum at 100% flag-prob, 0 clean false-discoveries.
   `results/t3f_satellite_discovery.json`. (Mirrored in moderation, `results/c_slice_discovery.json`.)
   And a THIRD, LABEL-FREE tier (`results/t3i_labelfree_defense.json`): run an independent panel of
   off-the-shelf detectors and flag strata where the suspect uniquely over-discards — POISON over-discards
   snow vs the panel at 0.575 vs CLEAN 0.000, no ground truth. Failure mode QUANTIFIED
   (`results/t3j_panel_robustness.json`): collapses only when the panel MAJORITY shares the blind spot
   (blind-heavy panel signal → 0.234); ROBUST to a minority of blind members (signal stayed 0.617 with
   KappaMask added to a good panel). THREE defense tiers: labeled probe (k=10) → scan-to-discover (120
   labels) → label-free cross-detector (0 labels, needs a majority-diverse panel).
   **Against an ADAPTIVE adversary** (`results/adaptive_attacker.json`) the defense doesn't prevent harm but
   CAPS it: a stealthy attacker staying below flag threshold τ is bounded to ≈τ slice-harm (stealth ceiling
   ~0.37 at τ=0.35; the loud 0.79 attack is detected w.p. 1.0). Principled operating point: benign-hard
   slices top out at FDR 0.23 (t3g), so set τ just above (≈0.30–0.35) → caps stealthy harm at ~0.30–0.37
   with no benign false-alarms. Probe + benign-falsification + adaptive-attacker → one coherent τ choice.

## Generality — the same structure in two more domains (content moderation + LLM routing)

- **Certified targeted suppression (Domain 2).** civil_comments, TF-IDF+LR. Flipping 0.18–0.39% of the
  corpus yields a classifier that still looks like a 94%-accurate, 0.8%-FPR moderator to any aggregate
  check, yet silently removes 56–65% of a targeted identity-term slice (12–25× baseline), aggregate
  footprint 0.17–0.53pp. `results/c_targeted.json`.
- **Same probe defense (Domain 2).** k≤15 non-toxic slice comments detect every certified moderation
  backdoor at ≥95% power / ≤5% false-alarm. `results/c_probe_defense.json`.

- **Third domain — LLM routing (recoverable), the irreversibility contrast** (`results/r_targeted.json`):
  a certified TF-IDF router silently downgrades a targeted query slice (medical: premium-recall 0.245→0.000,
  certified; code 0.066→0.004, certified) while aggregate routing quality is unchanged; rarity-gating holds
  (math/translate too big → detectable). Routing is RECOVERABLE (retry possible) — so this domain shows the
  certified-targeted-harm MECHANISM generalizes across the irreversibility axis, with irreversibility as the
  amplifier that makes satellite/moderation catastrophic. Caveat: weak base router (agg premium-recall 0.16).

## Cross-domain summary table (3 domains, spanning the irreversibility axis)

| | Satellite EO triage | Content moderation | LLM routing |
|---|---|---|---|
| gatekeeper | onboard cloud-detection CNN | toxicity classifier (TF-IDF + distilbert) | premium/cheap router |
| irreversibility | HIGH (discard before downlink) | MEDIUM (removal, archived) | LOW (user can retry) |
| targeted slice | clear-snow (1.17%) | identity-term comments (0.4–2.6%) | topic queries (medical/code) |
| certified hidden harm | 79% false-discard | 93% false-removal (transformer) | premium-recall → ~0 on slice |
| aggregate footprint | 0.73pp | 0.17–0.53pp | agg premium-recall ~unchanged |
| min probe / discovery | k=10 / 120 labels | k≤15 / 120 labels | k=15 (well-served slices) |
| defense limitation | — | some cluster collateral | BLIND to already-neglected slices (weak base router) |
| rarity-gated invisibility | — | yes (women too big → detectable) | yes (math/translate → detectable) |

## Honest limits (stated up front, not buried)

- **n**: satellite snow test n=47 (99 total). Substantially ADDRESSED by replicating the money result on a
  larger bright slice — bare-soil (lc=60), test n=139: POISON slice FDR 0.648 [0.568,0.727] (tight CI, vs
  snow's wide [0.66,0.89]), CLEAN 0.000, probe k=15 → 99% detect / 0% false-alarm
  (`results/t3k_baresoil.json`). So the result is not a small-n/snow artifact. Full CloudSEN12+ scale-up
  (250GB) is still the ideal hardening but no longer load-bearing for the "is it just n=47?" concern.
- **Certification robustness — resolved (Test 3D → 3E-dilution).** At 2000-data cert is marginal (3D:
  2/5 seeds clear 0.80, harm 0.79–0.96) because accuracy sits ON the bar. At realistic 5000-data cert is
  RELIABLE (5/5 seeds certified, acc 0.80–0.86) and harm stays catastrophic in 4/5 (≥0.51, mean 0.61).
  So the certified-catastrophic backdoor reproduces at scale. Honest caveat: more clean data ATTENUATES
  the backdoor (mean 0.86→0.61) because a rare slice has few patches to poison (all already flipped) —
  this is a real ratio-bound AND a second defense (clean rare-slice data). `results/t3d_multiseed.json`,
  `results/t3e_dilution.json`.
- **Incidental vs adversarial — a precise spectrum** (the #1 objection: "needs an attacker?"). Three
  independent tests agree: satellite under-representation (SCARCE) → 0.38 (3× baseline, certified);
  moderation realistic annotation bias 20% → slice FPR 0.118 (5× baseline, certified,
  `results/c_annotation_bias.json`); toxic-bert natural → 1.8×. **MODEST targeted over-suppression needs NO
  attacker** (realistic bias → 3–5×, certified, invisible = a real fairness/quality harm). **CATASTROPHIC
  (≥50% slice harm) needs a deliberate attacker** (moderation: ≥50% label bias; satellite: the backdoor).
  Two-tier claim, honestly bounded — don't overclaim natural catastrophe.
- **Recoverability**: KappaMask (Test 1/2) is a ground mask → its discards are recoverable; it evidences
  the invisibility PATTERN. The IRREVERSIBLE instance is Test 3's onboard CNN. Do not conflate.
- **Moderation transfers to a real transformer** (`results/c_transformer_transfer.json`): fine-tuned
  distilbert, muslim-poison → certified (acc 0.946→0.939) yet 93% false-removal on the muslim slice (29.9×),
  and MORE targeted than the linear model (jewish collateral 22.8×→4.0×). "TF-IDF is a toy" critique retired.
- **Invisibility is RARITY-GATED** (a demonstrated cross-cutting principle; `results/c_transformer_women.json`):
  the same distilbert attack on "women" (a bigger, higher-prevalence slice) still destroys 93% of the slice
  (21.5×) but is NOT certified (acc 0.946→0.924) with broad collateral. So the HARM generalizes across
  targets/model-classes; the certified INVISIBILITY specifically requires the slice to be rare — which is
  exactly the threat model. Holds across both model classes and both slice sizes (women fails cert on TF-IDF
  too). Rare targeted slice = invisible; big slice = attackable but detectable.
- **Moderation poison is target-dominant but not perfectly surgical**: linear TF-IDF smears onto the
  correlated religion cluster (jewish 22.8×, christian 6.9× when targeting muslim); the transformer smears
  far less (jewish 4.0×) but a christian residual (8.8×) persists. Honest framing: targeted suppression is
  real and steerable; some correlated-cluster collateral remains, shrinking with model expressiveness.
  (`audit/c_smear_result.md`, self-audit corrected an earlier mean-shift metric that masked collateral.)
- **Moderation caveat**: still a deliberate label-flip attack; the real-model NATURAL bias check (toxic-bert)
  was WEAK/confounded (≤1.8×) — do not lean on it.
- **Slice discovery — addressed** (`results/c_slice_discovery.json`): scanning the finite protected set
  (K slices × k=15 = 120 labels) surfaces the attacked slice at 100% flag-prob, 0 clean false-discoveries.
  Residual: this assumes the protected set is enumerable (true for identity groups / land-cover classes);
  a fully open-world attacked-subpopulation (arbitrary latent slice) would need disagreement-mining — not
  demonstrated. Satellite-side discovery DONE (`results/t3f_satellite_discovery.json`): scanning 8
  land-cover strata (120 labels) surfaces ONLY snow at 100%, 0 clean false-discoveries — cleaner than
  moderation (no collateral). Two-tier defense now demonstrated in BOTH domains.
- **Cert bar is author-set** but lenient, and the SAFE model passes it too — not rigged to pass only the
  backdoor. Real point: no standard cert stratifies a <3%-prevalence slice.
- **Defense vs benign difficulty — falsification (`results/t3g_benign_falsealarm.json`).** Tried to break the
  probe/discovery defense: does it false-alarm on genuinely-hard slices of the real un-attacked CloudScout?
  It did NOT — benign difficulty tops out at FDR 0.23 (low-sun scenes), the attack is 0.79, so a separating
  threshold distinguishes them (0 benign false-alarms). Honest boundary: this relies on attack-harm ≫
  benign-difficulty; the defense cleanly catches LARGE targeted harm but a SUBTLE attack (FDR ~0.3) buried in
  a benignly-hard region would need clean per-slice baselines, not an absolute FDR threshold.

## Novelty (sharpened via lit pass — see `paper/positioning.md`)

Concede both ingredients are established: subpopulation/evasive backdoors that preserve aggregate accuracy
(LOTUS arXiv 2403.17188, Subpopulation Poisoning 2006.14026) AND MNAR/Manski partial-ID (textbook). Neither
is our novelty. **The genuinely novel claim: irreversibility breaks the assumption EVERY existing
subpopulation-backdoor defense relies on** — Neural Cleanse/ABS/slice-accuracy audits all need the target
slice's DATA. In an irreversible gatekeeper the discarded slice's data is permanently destroyed ("once
discarded onboard… cannot be recovered for ground truth validation" — EO onboard-triage lit), so the harm
is not merely evasive-to-accuracy but UNIDENTIFIABLE from retained data → those defenses cannot even be
run. Contributions: (a) irreversibility as the axis that makes a known attack undetectable; (b) MNAR/Manski
formalization; (c) certified-yet-catastrophic instances across the irreversibility axis (3 domains); (d)
the footprint≈p·h scaling law explaining rarity-gated invisibility; (e) defenses that inject an EXTERNAL
reference (probe / discovery / label-free panel) precisely because retained-data audits can't work.
Residual risk: the attacks themselves are standard poisoning; novelty = framing+setting+identifiability+
defenses. If an "irreversible ML pipeline audit" paper exists we missed, (a) weakens — deeper related-work
sweep is the top pre-submission task.

## Venue / framing

Security / safety framing (undetectable targeted harm, eval integrity). Candidates: SaTML, NeurIPS-D&B,
ICLR. arXiv preprint = the artifact.
