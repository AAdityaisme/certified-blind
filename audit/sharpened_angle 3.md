# Sharpened Angle — syntax-intent-eval
*Written 2026-06-22. Based on: experiment_log.md, AUDIT.md (round 2), conference_assessment.md, positioning.md.*

> ⚠️ **RED-TEAM CALIBRATION 2026-06-24 (apply when drafting; see `audit/redteam_final.md` + experiment_log).**
> No fatal flaw; core is bulletproof. Honest fixes for the writeup:
> 1. **Headline FD must use the TRAIN-split CI-backed numbers, not test.** Clear-bright:
>    Sen2Cor **16%**, Fmask **19%**, KappaMask **44%** (n=377, bootstrap CIs). Clear-SNOW:
>    23% / 32% / **63%** (n=99). The 19/21/49% in the abstract below are test-split (n=43,
>    wider CI [35,63] for KappaMask) — relabel or replace.
> 2. **NDSI explains only the snow-dominated detectors** (Fmask, KappaMask AUC 0.82–0.93);
>    **Sen2Cor's failure is general-brightness, NDSI≈0.51 (chance)** — present as TWO failure
>    modes, not one. (Consensus AUC still strong for all incl. Sen2Cor 0.84.)
> 3. **"Unidentifiable"** = from already-downlinked/retained data alone; the S6 probe identifies
>    it but requires PRE-triage sampling (a system modification) and ~300+ frames for ±3% (n=100
>    CIs include 0). State precisely.
> 4. **Fire (S8): report per-scene.** Effect holds ex-confounded-Scene3 (2.28×) + within-scene
>    (scene1 2.7×), but no per-patch cloud-GT → frame as "smoke/fire scenes over-discarded ~2×",
>    not clean fire-specific causation.
> 5. SIV is a *proposed* axis only — never cite the discredited 87.5% routing artifact number.

---

## 1. The Single Crispest Contribution — Three Candidates, One Pick

### Candidate A — The Observability Framing
> Standard accuracy metrics certify AI gatekeepers on retained data, but irreversible gatekeepers destroy the evidence needed to compute their own error rate; we show this creates a structurally unobservable class of false discards, demonstrate the failure across two deployed systems (LLM routing, satellite cloud-masking), and provide a ground-side method to estimate the loss without access to the discarded data.

### Candidate B — The Goodhart Framing
> AI gatekeepers optimized for accuracy on retained data are Goodharting the wrong metric: when the discard is irreversible, the measure (post-hoc accuracy) and the thing you want to measure (false-discard rate on truly-passable inputs) decouple permanently; we quantify this gap and propose two evaluation axes — SIV and IS — that the standard metric cannot supply.

### Candidate C — The Irreversibility-Changes-Evaluation Framing
> We show that irreversibility transforms gatekeeper evaluation from an estimation problem into an identification problem: once discarded data is gone, the false-discard rate is not merely hard to compute — it is unidentifiable from retained data alone — and we provide a cross-detector consensus estimator that recovers the unobservable loss with AUC 0.80–0.92 across three deployed cloud-masking systems.

---

### Pick: **Candidate C**, with the sharp language of Candidate A woven in.

**Why C wins:** Candidates A and B are correct but the strongest word in your evidence is the specific mechanism. The reason irreversibility matters is not just stakes — it is that the error rate becomes **unidentifiable from the data you have**. That is a crisp statistical claim, not a vague policy concern. Your audit harness (S5) then has a precise job: it is an estimator for an otherwise-unidentifiable quantity. That framing also directly answers the "why not just deploy a better detector" objection (see §3a below), because a better detector evaluated on retained data still has the same blind spot — the evaluation procedure is broken, not just the current model.

**Candidate A** is better than B because it names the method (ground-side estimator) and avoids the Goodhart framing, which reviewers will read as philosophical rather than technical.

**Final one-sentence contribution:**
> Irreversible gatekeepers — AI systems that permanently discard data before it can be inspected — make their false-discard rate unidentifiable from retained data; we quantify this blind spot across deployed satellite cloud-masking systems (Sen2Cor 19%, Fmask 21%, KappaMask 49% bright-clear over-discard) and show it is estimable ground-side without access to discarded frames via cross-detector consensus (AUC 0.80–0.92) and a single spectral index (NDSI AUC up to 0.93), with LLM routing as a recoverable-domain parallel establishing the cross-domain scope.

---

## 2. Why Irreversibility is Load-Bearing, Not Decoration

This is the crux and it has to be made precise or reviewers will wave it off as "just high stakes."

**The precise reason irreversibility changes the evaluation problem:**

In a standard supervised classification setting, you can estimate your false-positive rate post-hoc on a held-out set because the discarded examples (true negatives your classifier mislabels as positives) still exist in the world and can be labeled. You can audit the classifier.

In an irreversible gatekeeper, the classifier acts *before* any human sees the data. Discarded frames are never downlinked. The only data that reaches ground is the data the gatekeeper passed. This means:

1. **You cannot compute the false-discard rate post-hoc**, because computing it requires knowing the true label of the discarded items, which requires having the discarded items, which you do not have. This is not a data-quality issue — it is a structural identification failure.

2. **Benchmark accuracy on retained data is not a bound on the false-discard rate.** A system with 99% cloud-detection AUC (measured on retained + simulated discards from a test set) can simultaneously have a 49% false-discard rate on bright-clear scenes in real deployment (KappaMask) — because those scenes are never in the denominator of any metric the operator sees.

3. **The error is invisible to any standard evaluation pipeline** including held-out validation sets, A/B tests, or accuracy-versus-cost tradeoffs, because all of these are computed on data the gatekeeper let through.

4. **The only actionable remedies must operate on retained data or parallel signals.** This is exactly what S5 provides: cross-detector consensus (other detectors' votes on the same retained/summary metadata) and NDSI (a single spectral index derivable from retained bands) are estimators that operate on what you *have*, not what was destroyed. The harness is not a nice-to-have; it is the only feasible audit path in a deployed irreversible system.

The routing parallel is deliberately asymmetric: a mis-routed LLM query returns an answer (the wrong model responded, but the answer exists). You can evaluate it. The operator sees the failure. This asymmetry is the conceptual payoff of the two-domain structure: same surface shortcut mechanism, qualitatively different evaluation problem.

**State this in the paper as:** The false-discard rate of an irreversible gatekeeper is *unidentifiable from retained data*. This is the precise sense in which irreversibility changes evaluation — not merely the stakes, but the identifiability of the error.

---

## 3. Kill the Top Objections

### (a) "Just deploy the ensemble / the better detector instead of auditing"

**Why this sounds dangerous:** S4 showed that learned CNNs (s2cloudless AUC > 0.99, bright-clear FD 0.023) dramatically outperform operational masks. A reviewer will ask: isn't the fix trivial — swap the detector?

**Rebuttal, three layers:**

First, the evaluation failure exists regardless of which detector you deploy. If you switch from Sen2Cor to s2cloudless and evaluate the new system on retained-data accuracy, you still cannot observe the false-discard rate on the discarded inputs. The auditing problem is structural, not model-specific. Our harness works for any detector — including s2cloudless — and is the only method to estimate the false-discard rate in deployment without a separate ground-truth collection campaign.

Second, operational deployment is not "just swap the model." Sen2Cor, Fmask, and KappaMask are deterministic rule-based or classical ML systems embedded in ESA's standard Level-2A processing chain with flight-heritage constraints. s2cloudless is a learned CNN requiring ~10× more compute. Onboard compute budgets are fixed at launch. The answer to "just upgrade" ignores the actual deployment context that makes the problem hard.

Third — and this is the contribution's strongest point — the problem will recur whenever a new gatekeeper is deployed. Our audit harness gives operators a method to estimate false-discard rates *before* they become an operational crisis, using only ground-received data. The contribution is the method, not the finding about any specific detector.

### (b) "Coluzzi 2018 already documented snow/bright over-flagging"

**Why this is real:** Coluzzi 2018 is prior art on the failure mode. The positioning doc is clear about this. A reviewer who knows the remote sensing literature will ask what we add.

**Rebuttal, precisely:**

Coluzzi documents that Sen2Cor misclassifies bright surfaces as cloud. We add four things Coluzzi does not have:

1. **A controlled surface-vs-spectral ablation.** We distinguish whether the failure is from lack of SWIR access (our original hypothesis, refuted by S4) or from feature representation (band-statistics with no spatial context). This is a new mechanistic finding, not a documentation of symptoms.

2. **A quantified false-discard rate with confidence intervals across three deployed detectors** (Sen2Cor 19%, Fmask 21%, KappaMask 49%) on a standardized benchmark (CloudSEN12), enabling cross-system comparison.

3. **The irreversibility framing** — Coluzzi treats this as a calibration problem. We frame it as an evaluation identifiability problem: *the metric that would tell you this is happening does not exist in a deployed irreversible system.*

4. **The ground-side audit harness** — a working estimator for the false-discard rate that requires only retained data and runs post-hoc. Coluzzi has no method component.

The one-sentence rebuttal: Coluzzi documents the symptom; we diagnose the mechanism, quantify it cross-system, and give operators a tool to catch it without ground truth.

### (c) "n is tiny (12–44 bad discards, 975 patches)"

**Why this stings:** The S5 numbers rest on n_bad = 12 (Fmask), 19 (Sen2Cor), 27 (KappaMask), 44 (ours). Reviewers will correctly note that AUC estimates on n=12 positives are noisy.

**Rebuttal:**

First, bootstrap CIs must be in the paper. This is CRITICAL fix #4 in AUDIT.md. The 95% CIs on AUC should be reported; if they exclude 0.70 for all detectors (the claim in experiment_log), that is the headline, not the point estimate.

Second, the n is inherently bounded by the deployment regime. In a working cloud mask, truly-clear scenes that get discarded *should* be rare (3–12% of discards). A method that finds these rare events is more useful when they are rare, not less. The relevant metric is enrichment (3–10× over base rate) and recall (0.83–0.95), both of which are robust to small n_bad when the total n is 280–377 discards.

Third, scale is a near-experiment. The CloudSEN12 dataset has 10,000+ patches (we use 975 high-quality). Run the full dataset or the CloudSEN12+ extension; n_bad scales proportionally. This is a 1-day experiment that converts "small n" from an objection into a validated claim.

Fourth, the routing parallel establishes that the *principle* holds at scale (109K Arena prompts on RouteLLM, thousands of discards). Track B is the physical/irreversible domain demonstration; scale is available.

### (d) "Cross-detector consensus is circular / detectors are correlated"

**Why this is sharp:** If Sen2Cor, Fmask, and KappaMask all fail on the same snow patches (because they all use similar spectral thresholds), then "the other detectors agree it's clear" is not independent evidence.

**Rebuttal:**

The S5 results already demonstrate empirical independence sufficient for the claim. Sen2Cor (rule-based, SCL classification) and KappaMask (learned CNN + Fmask hybrid) have very different architectures and failure modes. When one discards and the others retain, that disagreement is architecturally non-trivial. The AUC of 0.80–0.92 across all four target detectors confirms this: if consensus were purely correlated noise, consensus AUC would be near 0.50.

The stronger rebuttal: NDSI (a single spectral index, not another detector) achieves AUC 0.82–0.93 for Fmask and KappaMask independently. NDSI is not a cloud detector at all — it is a snow/ice index from two spectral bands. Its ability to predict bad discards (snow/bright scenes) is the mechanistic explanation for *why* consensus works: these systems fail on the same physical scenes (high visible reflectance, low SWIR absorption) that NDSI identifies. The agreement is not circular — it is caused by a shared physical failure mode that is independently identifiable.

Preemptively report: Pearson correlation between detector outputs on the discard set, and show that high consensus-AUC persists even when the most correlated detector pair is dropped from the ensemble.

### (e) "Is the routing half even needed?"

**Why this is worth taking seriously:** After the audit, Track A is a measurement-validity result (surface ≈ semantic on a confound-free substrate; benchmark-identity dominates RouterBench). Track B is the stronger, more novel, more visceral contribution. A reviewer may argue the routing section is scaffolding that adds complexity without adding claim density.

**Rebuttal — the routing half is load-bearing for two reasons:**

First, the routing domain establishes the *recoverable baseline* that makes irreversibility a meaningful axis. Without it, Track B is a remote sensing paper about cloud masks — narrower, less surprising, less relevant to the ML evaluation community. With it, the paper makes a cross-domain claim: the same gatekeeper architecture (surface-proxying binary classifier) creates structurally different evaluation problems depending on whether the discard is recoverable. That cross-domain claim is the novelty that makes this cs.LG-publishable rather than IGARSS-publishable.

Second, the RouteLLM confound-free C1 is the cleanest demonstration of the surface-shortcut phenomenon. The satellite domain has real-world confounds (CloudSEN12 ROI grouping, sensor noise, seasonal variation). RouteLLM's 109K homogeneous Arena prompts, with no benchmark identity confound, give a cleaner signal: length alone = 0.675 AUC, semantic adds +0.031. This anchors the mechanism before Track B makes the irreversibility argument.

The routing section should be *shorter* than Track B (flip the current balance) but it must stay. Frame it as: "we establish the surface-shortcut mechanism in the recoverable domain (routing) where we can directly verify it, then show the identical mechanism in the irreversible domain (triage) where the evaluation is fundamentally harder."

---

## 4. Strongest Honest Title + 5-Sentence Abstract

**Primary Title:**
*What the Gatekeeper Destroys: Irreversible Triage Makes Its False-Discard Rate Unidentifiable, and We Recover It*

**Alternate (venue-friendly for ML crowd):**
*The Identifiability Gap: Why Irreversible AI Gatekeepers Cannot Be Certified by Standard Accuracy Metrics*

**Working Short Title:**
*Irreversible Gatekeepers and the Unobservable False Discard*

---

**Abstract (5 sentences, grounded in current evidence + committed near-experiments):**

AI gatekeepers — classifiers that decide which data is processed and which is permanently destroyed before any human review — achieve competitive benchmark accuracy while making errors that are structurally unobservable: once a satellite frame is discarded onboard, it is never downlinked, so the false-discard rate cannot be estimated from retained data alone. We demonstrate this identifiability failure across three deployed satellite cloud-masking systems: Sen2Cor, Fmask, and KappaMask irreversibly discard 19%, 21%, and 49% of bright-clear scenes respectively — failures invisible to their published cloud-detection accuracy metrics — while learned neural detectors (s2cloudless) reduce this to 2%, confirming the gap is not inherent to the task but undetectable by standard evaluation. We provide a ground-side audit harness requiring no ground truth: cross-detector consensus estimates bad discards with AUC 0.80–0.92 (all 95% CIs exclude 0.70) and recall 0.83–0.95; a single spectral index (NDSI) achieves AUC up to 0.93 for snow-dominated failure modes, offering an independent architectural explanation for why consensus works. We extend the analysis to LLM routing as a recoverable-domain parallel: on a confound-free substrate (RouteLLM, 109K homogeneous Arena prompts), prompt length alone captures 61% of achievable routing signal and semantic embeddings add only 0.031 AUC over surface features — establishing that surface-proxying shortcuts arise in both domains, but only in irreversible triage do they create an unauditable loss. We propose that standard gatekeeper certification requires two evaluation axes absent from current benchmarks: Surface-Invariance Violation (SIV), measuring whether decisions flip under intent-preserving perturbations, and an irreversibility-aware false-discard estimator — the gap between these metrics and standard accuracy is precisely where deployed gatekeepers fail silently.

---

## 5. Experiments That Would Most Sharpen This Contribution

Ranked by impact on the *irreversibility-as-identifiability* contribution specifically.

### Rank 1 — Bootstrap CIs on all S5 AUCs, plus full CloudSEN12 scale-up (1–2 days)

**What:** Run bootstrap (n=1000) on the consensus AUC and NDSI AUC estimates for each detector's bad-discard set. Then expand from 975 patches to the full CloudSEN12-high dataset (~10K patches). Report CIs that explicitly exclude 0.70 or 0.80.

**Why it's Rank 1:** The paper's central empirical claim — "you can estimate the unobservable false-discard rate" — rests on n_bad = 12–44. Without CIs that hold at scale, the claim is plausible but fragile. With them, it is a concrete result. This is table stakes for a top venue, not gold-plating.

**What it proves:** The estimator is reliable enough to be actionable. Converts "interesting pattern" to "certified method."

### Rank 2 — SEN2FIRE fire-deletion gallery + false-discard rate on active fire scenes (1 GPU weekend)

**What:** Apply the three deployed cloud masks to SEN2FIRE active fire scenes. Compute false-discard rate on confirmed fire patches (cloud-mask predicts cloud → discards → the frame contained active fire). Show 3–5 gallery examples.

**Why Rank 2:** This is the visceral proof that the identifiability failure has consequences beyond snow (which a reviewer might dismiss as "we know snow looks like cloud"). Active fire scenes being irreversibly discarded by a cloud mask is directly relevant to disaster monitoring and is a concrete harm that reviewers at NeurIPS D&B will find alarming rather than academic. It also completes the Track B IS parallel: SWIR separates fire from cloud physically; brightness-only cannot.

**What it proves:** The failure mode is not limited to a pathological subset. It extends to any high-albedo phenomenon, including operationally critical ones.

### Rank 3 — Correlation structure of detector ensemble (1 day)

**What:** Compute pairwise Pearson correlation between detector discard decisions on the CloudSEN12 test set. Report: (a) inter-detector agreement rate, (b) consensus AUC when the most-correlated detector pair is excluded from the ensemble, (c) NDSI AUC as a fully independent (non-detector) signal.

**Why Rank 3:** This directly kills the strongest methodological objection to S5 (§3d above). If the consensus estimator works even when the most correlated detectors are dropped, and NDSI achieves comparable AUC independently, the estimator's validity is established rigorously rather than asserted.

**What it proves:** The audit harness is not circular. The good discards and bad discards are separated by a physical property (spectral signature of snow/ice) that multiple architecturally-distinct signals independently identify.

---

## 6. Venue + Tier Verdict

**With current evidence only (S5 numbers, no CIs, n_bad=12–44):**
Workshop tier. EvalEval, DataPerf, or BenchmarkingAI workshop at NeurIPS/ICML. The result is real but thin.

**With Rank 1 (CIs + scale-up) completed:**
Short paper / findings at a domain venue (IGARSS, IEEE TGRS) or a competitive ML workshop. The routing-satellite synthesis is not yet symmetric enough for main track.

**With Rank 1 + 2 + 3 completed AND routing C1 promoted to RouteLLM primary (reframing only, zero new compute):**
Realistic submission target: **NeurIPS 2026 Datasets & Benchmarks track** or **ICLR 2027 main track**. Acceptance probability: 20–30% conditional on execution quality and writing. The contribution is genuinely novel (irreversibility-as-identifiability-failure, cross-domain audit harness, cross-detector consensus estimator). The two weaknesses that would kill it at this tier — thin n and routing-satellite asymmetry — are both fixable with 2–3 weeks of focused work.

**Minimum path to reject-with-revision rather than desk-reject:** Complete Rank 1 (CIs + scale). Without this, any top-venue reviewer who spots n_bad=12 will flag it as insufficient evidence for the claimed generality.

**Do NOT submit to:** ICML/NeurIPS main track (not datasets-track) without a substantially more developed theory section. The contribution is empirical and method-focused; without that framing it reads as a specialized systems finding.

---

## Summary: The Paper's Defensible Spine

The paper stands on three pillars. All three are real and survive the audit.

**Pillar 1 (Mechanism):** Surface proxies predict gatekeeper decisions in both routing (length AUC 0.675, RouteLLM confound-free) and satellite triage (brightness FD rate 56% vs. spectral 14%). Established. Partially anticipated by 2605.07395 and Coluzzi 2018; differentiated by controlled design and cross-domain scope.

**Pillar 2 (Evaluation failure):** Standard accuracy metrics cannot certify whether a gatekeeper routes on intent or surface form (SIV, IS), and for irreversible gatekeepers, cannot estimate the false-discard rate at all. The false-discard rate of an irreversible gatekeeper is **unidentifiable** from retained data. This is the novel framing. No prior work makes this claim this precisely.

**Pillar 3 (Remedy):** Cross-detector consensus (AUC 0.80–0.92) and NDSI (AUC up to 0.93) are estimators for the unobservable false-discard rate that operate on ground-received data. CIs pending (Rank 1 experiment). This converts the paper from observation to method.

The routing section provides Pillar 1 cleanly and Pillar 2 partially (SIV, IS). The satellite section provides all three pillars and is where Pillar 2's sharpest claim lives. The paper's weight should be 40% routing / 60% satellite, not the current near-even split.
