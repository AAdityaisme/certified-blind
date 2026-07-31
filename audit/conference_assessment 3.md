# Conference Assessment — What the Gatekeeper Throws Away
**Assessor perspective:** NeurIPS/ICML/ICLR area chair  
**Date:** 2026-06-22  
**Status input:** All Track A experiments audited; Track B (satellite) built and initial numbers in hand; no SIV interventions on Track B yet; no audit harness; no second routing substrate.

---

## 1. Tier Verdict

**As-is (today's honest state):**

| Track | Standalone tier |
|---|---|
| Track A (routing) alone | Workshop (ICLR Blogpost track or eval/robustness workshop) — AUC ≈ 0.71 ceiling, one substrate, artifacts flagged by audit |
| Track B (satellite) alone | Domain venue short paper — IGARSS / IEEE TGRS / ISPRS short paper; *not* cs.LG |
| Combined, with current results | Workshop paper at a top venue (BenchmarkingAI, EvalEval, Data-centric AI). Stretch: findings notes at ICML or NeurIPS. |
| Combined, with required experiments completed | **Oral-or-poster range at ICLR / NeurIPS (Datasets & Benchmarks or main track)**. Realistic acceptance odds: 20–30% at a competitive venue. |

**Brutal bottom line:** The paper is not top-conference-ready now. Track A alone is a competent negative result on one benchmark with well-known confounds. Track B alone is a re-demonstration of a documented remote-sensing failure (Coluzzi 2018 already shows this). The cross-domain synthesis — AI gatekeepers, the irreversibility axis, SIV as a proposed eval addition — is genuinely novel framing, but it needs: (a) the full Track B intervention experiments, (b) a second routing substrate (RouteLLM), (c) the audit harness delivering real P/R numbers, and (d) the statistical machinery the audit has already computed but not yet incorporated. With all of that, it becomes a legitimate NeurIPS D&B or ICLR submission with a real chance.

---

## 2. Genuine Novel Contribution

**One sentence (honest version):**

> We show that AI gatekeepers — classifiers that decide what flows or what gets permanently destroyed — can achieve competitive benchmark accuracy by exploiting surface proxies (prompt length statistics; pixel brightness) rather than task intent, and that the standard evaluation metric is blind to this failure; we propose Surface-Invariance Violation (SIV) as a missing eval axis and demonstrate in LLM routing (recoverable mistake) and onboard satellite triage (irreversible destruction) that the severity of the gap depends critically on whether the gatekeeper's errors are auditable.

**Is it enough?** Barely — and only with Track B fully built. Here is the honest distinction:

- "Interesting observation": surface features predict routing labels as well as embeddings on RouterBench. This is a known risk (RouterBench paper already notes benchmark structure; RouteLLM paper explicitly tests confound-free data). On its own, this is a finding note, not a contribution.
- "Observation the community needs to act on": the metric used to certify routers cannot distinguish a model with SIV=0.875 from one with SIV=0.012 — and in satellite triage this metric blindness is not an annoyance but means permanently destroyed disaster data with no audit trail. That reframe — plus SIV as a proposed remedy — is what elevates this to a contribution.

The irreversibility axis is the most novel part of the paper and currently has the least experimental support. It is doing the most narrative work with the least evidence. Fix this first.

---

## 3. Required Experiments — Ranked by Impact on Acceptance

### Rank 1: Complete Track B intervention experiments (SIV and IS on CloudSEN12)
**Why it tops the list:** The paper's title is cross-domain. Track B currently has S1 (parity result, which is documented in prior work) and S2 (false-discard rates on bright-clear patches, n=43 for the key subset). What it does not have: an SIV test (do brightness model decisions flip under intent-preserving radiometric perturbations?), a clean IS test (do brightness vs spectral models diverge when surface is held constant?), the SEN2FIRE fire-deletion gallery (the visceral artifact), and the silent-discard cost analysis. Without these, Track B is just replicating Coluzzi 2018. With them, it provides the clean physical IS contrast the routing domain cannot give (because IS≈0.5 for all routing models).  
**Effort:** GPU weekend on the RTX 4090.  
**Payoff:** Transforms the paper from a routing note with a satellite appendix to a genuine two-domain eval-integrity result.

### Rank 2: Add RouteLLM (Djudge / confound-free substrate) as the primary routing C1
**Why second:** The AUDIT already identified this as the "key new experiment." RouteLLM gpt4_judge_battles (109K Arena prompts, no benchmark identity confound) gives the clean confound-free C1: surface AUC 0.741, length-only 0.675, semantic 0.772, gap +0.031. This is the *defensible* routing C1 — it survives the eval-identity attack that kills the RouterBench C1. The paper should lead with RouteLLM for C1, then use RouterBench to demonstrate the benchmark-saturation thesis (eval-identity confound = separate finding). Currently this experiment exists (`results/r_routellm.json`) but is framed as secondary. Promote it to primary.  
**Effort:** Already done. Zero new compute. Rewrite framing only.  
**Payoff:** Closes the single biggest Track A attack immediately.

### Rank 3: SIV augmentation control — "train on code-fenced prompts; does SIV disappear?"
**Why critical:** The strongest reviewer attack on the routing SIV is "this is just a data augmentation failure; any deployed router would retrain." The paper cannot defend its claim that "the metric is blind" until it shows: yes, augmentation reduces SIV, but the clean-data AUC still gives no warning that augmentation was needed — you only know to do it if you computed SIV in the first place. This experiment turns the obvious objection into a supporting result. Specifically: train surface_logreg with 50% code-fence-augmented prompts; show SIV drops; show clean AUC is unchanged. The point is that the metric never told you SIV was 0.875 on the un-augmented model, and it still doesn't tell you the augmented model is safer.  
**Effort:** Half a day.  
**Payoff:** Preempts the highest-probability rejection argument (see Section 4).

### Rank 4: Statistical machinery — bootstrap CIs, McNemar, Cohen's h — everywhere
**Why fourth despite being "just stats":** The audit already computed these. AUC gap CI [0.001, 0.017] (tfidf beats semantic, correctly); SIV gap CI [0.844, 0.865], Cohen's h = 2.12; McNemar chi²=17.0 p<0.0001. None of these are in any result table. A top venue reviewer looking at tables without CIs will immediately suspect the authors don't know how significant their own results are. Two hours of code. Zero excuse not to do this.  
**Effort:** 2 hours, no new experiments.  
**Payoff:** Professional credibility, closes the "no significance testing" attack.

### Rank 5: Per-perturbation SIV breakdown + has_code_fence ablation
**Why fifth:** The audit showed that removing `has_code_fence` drops surface_logreg SIV from 0.875 to 0.064. The paper should report this as a strength, not hide it. "We can trace the fragility to one binary content-type flag" is a mechanistically clean story. The table should show: SIV per perturbation (code_fence, whitespace, trailing, bullet), SIV without has_code_fence, SIV with has_code_fence alone (1.000, AUC 0.500). This also fixes the misleading aggregate SIV_clean_mean=0.475 ± 0.399.  
**Effort:** Existing data, 1 hour.  
**Payoff:** Converts biggest vulnerability into a precise mechanistic finding.

### Rank 6: Audit harness (A1) — ground-side estimator with real P/R numbers
**Why this slot:** The harness is listed in PAPER_PLAN.md as the "buildable novel artifact" and C4 of the contribution structure. Without it, the paper's third pillar ("so what — we give a remedy") is empty. The harness as specified is straightforward: on CloudSEN12 test split, use disagreement between brightness_hgb and spectral_hgb as a "probable bad discard" flag; evaluate flag precision/recall against true bad discards (false-discard=1 for bright-clear patches). This gives the paper a concrete proposed tool, not just an observation.  
**Effort:** 1 day. Track B data already downloaded.  
**Payoff:** Elevates the contribution from "we found a problem" to "we found a problem and here is a diagnostic tool."

### Rank 7: Bootstrap CIs on Track B false-discard rates (n=43 is small)
**Why needed:** The key Track B result — brightness_hgb discards 60.5% of bright-clear scenes vs spectral_hgb 14.0% — rests on n=43 patches. The 4× ratio is striking but a reviewer will note the small n. Bootstrap CI on the 60.5% vs 14.0% difference is essential. Also: expand the CloudSEN12 evaluation to the full high+low split if possible (CloudSEN12+ has more patches), and add a calibration check on the cloud_frac threshold τ (sweep 0.3, 0.5, 0.7).  
**Effort:** Half a day.  
**Payoff:** Hardens the Track B headline number.

### Rank 8: RouterBench score threshold sensitivity sweep
**Why necessary:** 21% of RouterBench scores are non-binary; threshold at 0.5 is undisclosed. Sweep τ ∈ {0.5, 0.75, 1.0} and show AUC/base-rate stability. Required for reproducibility and reviewer trust. The audit shows results are roughly stable, but "roughly" is not enough for a submission.  
**Effort:** 2 hours.  
**Payoff:** Closes the label-validity attack; makes the method section defensible.

---

## 4. Single Biggest Rejection Risk — and How to Neutralize It

**The rejection:** "The routing SIV result reduces to a textbook train/test distribution shift with a single near-constant binary feature. Any practitioner would fix this by (a) data augmentation or (b) dropping the `has_code_fence` feature. This is not a metric-level failure; it is a standard model-level implementation deficiency. The paper does not need SIV to find this — a simple holdout evaluation on code-fenced prompts would suffice."

**Why this is dangerous:** It is partially correct. The C3 artifact (6.7× cost = StandardScaler extrapolation, not deployment insight) already concedes part of this ground. A hostile reviewer will connect the dots: SIV finds a brittle feature; training with that feature off or augmenting would fix it; therefore SIV adds no information over standard debugging practices.

**How to neutralize it:**

1. Run the augmentation control (Rank 3 above). Show augmentation *reduces* SIV but the metric still never shows you the problem proactively. The point is not "the model is fragile" (fixable) but "the metric gave no signal of fragility" (structural). A practitioner using AUC to certify a router would not know to run augmentation unless they computed SIV first.

2. Pivot the primary locus of the SIV/irreversibility argument to Track B (Rank 1 above). In the satellite domain, there is no "augmentation" fix — you cannot train a brightness-only classifier to not be brightness-only. The failure is architectural, not dataset-dependent. The clean IS contrast (SWIR bands physically separate intent from surface) delivers what the routing domain cannot: a case where the shortcut is structurally baked in, and the only remedy is either the metric change or the model change.

3. Frame SIV explicitly as an acceptance criterion, not just a diagnostic. "You should require SIV ≤ δ before certifying a gatekeeper" — give a practical recommendation, not just an observation. This moves the paper from complaint to prescription.

---

## 5. Two-Domain Framing: Strength or "Two Thin Half-Papers"?

**Honest assessment:** Currently a weakness because Track B is not built out enough to carry half the paper. The routing track has 6 experiments; the satellite track has 2 (S1 parity, S2 false-discard). An asymmetric paper looks like a routing paper with a satellite cameo.

**If Track B is completed (Ranks 1, 6, 7 above):** The two-domain framing becomes the paper's core strength and its primary novelty claim. The specific value of two domains is not "more examples" but "the irreversibility axis": routing mistakes are recoverable (retry), satellite triage mistakes are permanent (frame gone). This axis does genuine conceptual work — it explains why the same surface shortcut has different policy implications in each domain. No single-domain paper can make this point.

**Recommendation:** Do not scope down to one domain. The two-domain synthesis table (the one in PAPER_PLAN.md section 4) is exactly the kind of conceptual contribution that top-conference reviewers remember. But the domains must be symmetric in experimental depth. Right now they are not. Make them symmetric first; then the framing is a strength.

**If Track B proves impossible to complete to required depth:** Scope down to a routing-only paper with an honest title. Call it what it is: a measurement-validity paper about LLM routing evaluation. It is a good workshop paper or a short Findings paper at ACL/EMNLP (given the LLM routing angle). Do not submit a half-built two-domain paper to NeurIPS — that is the fastest path to rejection.

---

## 6. Strongest Honest Title + Abstract

**Title:**  
*SIV: A Surface-Invariance Test for AI Gatekeeper Evaluation, and Why Standard Accuracy Fails to Certify Intent-Robustness*

*(Alternate if two-domain framing holds: "What the Gatekeeper Throws Away: Surface Shortcuts in Recoverable and Irreversible AI Triage")*

**Abstract (5 sentences, honest, grounded in current + required evidence):**

AI gatekeepers — classifiers that decide which requests receive expensive processing and, in physical deployments, which data survives — can achieve competitive benchmark accuracy by exploiting surface proxies rather than task intent. On a confound-free LLM routing benchmark (RouteLLM, 109K homogeneous Arena prompts), prompt length alone accounts for 61% of achievable routing signal; the best semantic encoder beats the best surface model by only 0.031 AUC, while a naive linear router trained on lexical statistics flips 87.5% of its decisions under a cosmetic encoding change that leaves intent unchanged — a fragility the standard AUC metric rates as indistinguishable from robust alternatives (SIV gap Cohen's h = 2.12, CI [0.844, 0.865]). We show the same mechanism in onboard satellite Earth-observation triage, where a brightness-only classifier achieves AUC 0.86 on cloud detection yet irreversibly discards 61% of bright cloud-free scenes (snow, desert, active fire) that a SWIR-spectral model preserves — a failure invisible to aggregate accuracy and unrecoverable because the raw frames are never downlinked. We propose Surface-Invariance Violation (SIV) and Intent-Sensitivity (IS) as domain-general diagnostic axes for gatekeeper certification, demonstrate a ground-side audit harness that estimates false-discard rates without access to discarded data, and show that the severity of metric blindness scales with irreversibility: recoverable mistakes (routing retries) permit post-hoc correction; irreversible ones (orbital discard) do not.

---

## 7. Action Plan: Minimum Viable Submission Path

To reach "realistic shot at NeurIPS D&B or ICLR," the required completion order is:

1. **Reframe routing C1 around RouteLLM** (already done computationally — rewrite only). 1 day.
2. **Add statistics to all Track A tables** (CIs, McNemar, Cohen's h). 2 hours.
3. **Complete Track B interventions** (SIV + IS on CloudSEN12, SEN2FIRE gallery, bootstrap CIs on false-discard rates). 1 GPU weekend.
4. **Build audit harness A1** (disagreement-based flag, P/R on probe set). 1 day.
5. **Run augmentation control on routing SIV** (code-fence augmentation, show metric still blind). Half day.
6. **Per-perturbation SIV breakdown + has_code_fence ablation table**. 1 hour.
7. **Threshold sensitivity sweep on RouterBench labels**. 2 hours.

Estimated total: **2–3 weeks of focused work** with GPU weekends on Track B.

Without steps 1–4, do not submit to a top venue. Submit to a workshop instead and use reviewer feedback to scope the full paper.
