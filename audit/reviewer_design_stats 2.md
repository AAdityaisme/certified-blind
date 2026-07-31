# Hostile Reviewer Audit — Design, Statistics, and Claim Validity
*Prepared: 2026-06-22. All code in `.venv`. Numbers verified by re-running experiments.*

---

## (a) Prioritized Findings Table

| # | Severity | Problem | Why It Matters | Fix |
|---|----------|---------|----------------|-----|
| 1 | **Critical** | **SIV driven almost entirely by a single binary flag (`has_code_fence`)** | Ablation result: surface_logreg *without* `has_code_fence` drops SIV from 0.875 → 0.064. `has_code_fence` alone achieves SIV=1.000 (it literally flips every prompt it fires on), AUC=0.500 (useless for routing). The model learns "if code_fence=0 → route cheap; if code_fence=1 → route expensive" because code-heavy prompts genuinely need GPT-4 in training data. Then wrapping the test set in a code fence triggers a spurious mass-escalation. This is *mechanistically sound* as a shortcut story, but the paper presents it as an 87.5% flip rate across "clean perturbations" (mean of 4), obscuring that whitespace/trailing/bullet SIV is ~5–10%, and the aggregate is dominated entirely by code_fence and whitespace perturbations — which also flip `has_code_fence`-correlated features. A reviewer who notices this will call it "one brittle flag, not a general surface-form problem." | Separate results by perturbation type. Report code_fence and whitespace SIV distinctly from trailing/bullet/preamble. Run the "without-has_code_fence" ablation as Table 2. The finding *survives* but must be framed more precisely: "linear models trained on binary content-type flags are extremely brittle to encoding shifts that alter those flags — a structural property of the feature-label alignment, not a fringe failure." |
| 2 | **Critical** | **No significance tests on any claim** | The plan promised McNemar + bootstrap 95% CI + Cohen's h. None were computed before "Track A complete" was declared. Key numbers: AUC gap (semantic − best_lexical = −0.007) has a bootstrap 95% CI of [−0.017, −0.001] — it excludes zero, so C1 is actually *statistically sound* but in the direction that tfidf_logreg beats semantic (semantic is worse, not equal). The SIV gap (surface_logreg − semantic = 0.855) has bootstrap CI [0.844, 0.865], p→0, Cohen's h = 2.12 (massive effect). These numbers *help* the paper enormously but are absent from the writeup. McNemar on accuracy (surface_logreg vs semantic): chi²=17.0, p<0.0001 — semantic is significantly more accurate, weakening the "models are equal" framing. | Add a statistics section. Report bootstrap 95% CIs on all key gaps. Cohen's h = 2.12 on SIV is impressive — use it. Fix the framing: the models are NOT equal on accuracy (p<0.0001 McNemar favoring semantic); the claim should be "comparable AUC (~0.67 vs ~0.70), yet catastrophically different SIV" — the specific numbers matter. |
| 3 | **Critical** | **IS result (all models ~chance) is structurally ambiguous and may be a matching failure, not a signal finding** | IS uses surface-matched pairs from the *same dataset*. Mean match distance = 0.092 (standardized), caliper = bottom 25%. There is no ground truth that confirms the matched pairs actually differ in intent/difficulty — they differ only in the RouterBench gold label (weak_fails). If the matching is loose, matched pairs may still differ on surface features the model reads. Conversely, if the label itself is noisy or prompt-length-deterministic, even a perfect intent reader would get IS≈0.5. The t-test on 3 seed-level IS means shows: tfidf IS=0.561 is significant (t=5.21, p=0.035); semantic IS=0.520 is not (p=0.082). The honest interpretation is "the routing label on RouterBench has very little residual signal once surface is controlled — even TF-IDF content barely squeezes above chance." This sharpens the "metric is surface-saturated" thesis but *cannot support* the separate claim that semantic models are not using intent. | (a) Analyze match quality: show distribution of match distances for retained vs. rejected pairs; (b) Verify that matched pairs span multiple eval types — if they are all from the same benchmark domain, the match is confounded; (c) Report IS at multiple caliper percentiles (10, 25, 50) to show robustness; (d) Frame IS as "evidence of benchmark saturation," not "evidence semantic fails to use intent." |
| 4 | **High** | **The "6.7× cost blowup" (C3) is structurally trivial given SIV=0.875** | The C3 finding is not independent of C2-SIV. If SIV=0.875 means 87.5% of decisions flip (mostly to "route to GPT-4"), then cost necessarily converges to always-strong cost. Verification: `shift_c == always_strong_c` to 8 decimal places — **exactly equal** by construction. The "6.7×" number is arithmetically determined by: (1) the SIV rate; (2) the cost ratio of weak vs strong model; (3) the base rate. A referee will call this "the cost finding is a restatement of SIV, not an independent result." | Reframe C3 as "cost consequence of SIV," not a separate finding. The value is showing *why SIV matters* in economic terms — keep it, but acknowledge it's derived. The correct independent C3 contribution is: "the clean-data AUC gives no warning of the impending cost blowup" — which is true and non-trivial. Show that clean AUC is 0.667 while shift-AUC (on code-fenced test set) is never reported because no one checks it. |
| 5 | **High** | **Single-dataset risk: all routing results are RouterBench (one weak/strong pair: Mixtral vs GPT-4)** | The entire routing Track A uses one benchmark, one weak model, one strong model, and one label construction. Results may be specific to this pair's capability profile (GPT-4 is much stronger than Mixtral on code tasks → code prompts get label=1 → has_code_fence learns the label → everything follows from there). If the paper used a different weak/strong pair (e.g., GPT-3.5 vs GPT-4, or Llama-3 vs Claude), the SIV story might look completely different. PAPER_PLAN.md mentions RouteLLM `Djudge` as "secondary substrate" but it was never run. | Run at minimum one alternative weak/strong pair from RouterBench's 11 models, or the RouteLLM/Djudge substrate. If the story holds, external validity is substantially strengthened. If it doesn't, that's a critical limitation that must be stated. |
| 6 | **High** | **"Surface-saturated metric" claim is stated but not directly demonstrated** | The claim is: "the metric cannot distinguish intent-robust from intent-fragile models." This is logically true given the data (same AUC, different SIV), but the paper never directly shows that optimizing for the metric *causes* you to select the fragile model. There's no experiment where a model-selection procedure is run and picks surface_logreg because of its AUC. The argument is implicit. | Add a one-paragraph "selection trap" demonstration: show that a practitioner using standard AUC-based model selection on the clean held-out set would rank surface_logreg above the majority baseline and comparable to semantic, and then gets the 6.7× cost blowup in deployment. This is already implied but needs to be stated as a procedure. |
| 7 | **Medium** | **surface_hgb breaks the "surface = bad" narrative and is underexplained** | surface_hgb (same features, gradient boosted trees) achieves AUC=0.703, SIV=0.032, shift-stable. The paper acknowledges this as a "precision point" but doesn't explain it mechanistically. Why does a tree model on the same features have 27× lower SIV than a linear model? The answer is likely that: (a) linear models with collinear features (n_tokens, n_chars, n_words are all highly correlated) create large canceling coefficients that amplify small feature-space perturbations; and (b) trees route on if-then thresholds that are less sensitive to the exact numeric values code-fencing adds. This distinction is actually *important to the paper's thesis*: it means the brittleness is not "surface features per se" but "linear models fit to noisy collinear surface features" — a narrower (but still valid) claim. | Add a model-design explanation for why surface_hgb is robust. Consider framing it as: "the same feature set can produce robust or fragile behavior depending on the model class — which shows that the SIV failure mode is not inevitable from surface features alone, but rather from the specific architecture-feature interaction that naive/first-pass implementations exhibit." This actually *sharpens* the paper's practical warning. |
| 8 | **Medium** | **SIV "clean mean" averages across perturbations with 70× range (0.055 to 0.875)** | The summary metric "SIV_clean=0.475 ± 0.399" (std=0.399 is huge!) for surface_logreg averages code_fence (0.875), whitespace (0.872), trailing (0.055), and bullet (0.098). The huge std is not noise — it is genuine variance across perturbation types. This heterogeneity means the aggregate is meaningless. A reviewer who reads the per-perturbation table will see that trailing_space SIV=0.055 is almost as low as semantic's 0.032, while whitespace SIV (double-spacing every word) = 0.872. The whitespace result is also mechanistically tied to has_code_fence-like confounds (whitespace changes n_words, n_chars, whitespace_ratio significantly). | Never report mean-of-perturbations as a single number. Report per-perturbation SIV table, group by perturbation type (length-changing vs flag-changing vs truly cosmetic), and discuss which are mechanistically "clean" tests of surface-over-intent. |
| 9 | **Medium** | **E1b (embedder robustness) uses 3 seeds vs E1's 5 seeds, with no justification** | Minor but a reviewer will notice the inconsistency. The paper switches from 5 seeds (E1) to 3 seeds (E1b, E2, E3) without explanation. More critically, the std on E1b AUC estimates is larger (e.g., semantic_bge std=0.0044) than with 5 seeds, inflating uncertainty bands. | Either run all experiments with 5 seeds, or justify the 3-seed choice and provide seed-level tables in appendix. |
| 10 | **Low** | **Track B (satellite EO) does not exist** | PAPER_PLAN.md marks it pending. The paper currently has one domain (routing) and one substrate (RouterBench). The entire "irreversibility axis" and "visceral deleted-disaster-footage" argument is unsubstantiated. Without Track B, the one-sentence contribution cannot be delivered — the paper is about routing shortcuts, not "AI gatekeepers across domains." | Either (a) scope the paper down to routing only with an honest title ("Surface Shortcuts in LLM Routing: Why Your Eval Can't See the Failure"); or (b) complete Track B before submitting. The dual-domain framing is the paper's core novelty claim. Without it, the contribution is a competent routing-eval paper, not a cross-domain eval-integrity result. |

---

## (b) Claim-by-Claim Verdict

### C1 — "Surface ≈ intent-aware on AUC; the metric is saturated"

**Verdict: SUPPORTED but framing needs correction.**

The bootstrap 95% CI on (semantic − tfidf) AUC = [−0.017, −0.001], excluding zero in the *wrong direction for semantic*: tfidf statistically beats semantic at AUC. The correct C1 statement is:

> "No intent-aware model (MiniLM, mpnet, BGE) exceeds the best lexical model (tfidf_logreg) on AUC; the best semantic model (BGE) trails tfidf by 0.007 (95% CI [0.001, 0.017]). The metric ranks tfidf≥semantic, yet — as C2 shows — their intent-robustness differs catastrophically."

The McNemar test shows semantic_logreg is significantly more *accurate* (chi²=17.0, p<0.0001 vs surface_logreg), but less so than tfidf. The "parity" framing is defensible on AUC (gap within noise for most pairs), but should be stated precisely: "comparable AUC in the range 0.67–0.71; no model eclipses ~0.71."

**Overclaim to fix:** The paper says "the metric is blind to the gap." Technically the gap exists (semantic ≠ surface on AUC), but it's small enough that it doesn't motivate a different deployment choice — which is the real point. Reframe as: "the AUC gap is too small to reliably distinguish intent-robust from fragile models, and the correct signal — SIV — is never computed in standard practice."

---

### C2-SIV — "surface_logreg flips 87.5% of decisions under code-fence wrap"

**Verdict: SUPPORTED, but critically incomplete without per-perturbation breakdown.**

The SIV gap (0.875 vs 0.032) is statistically massive: bootstrap 95% CI on the difference = [0.844, 0.865], Cohen's h = 2.12 (far above "large" threshold of 0.8). This is not sampling noise.

**Critical caveat the paper omits:** The 87.5% code-fence SIV is almost entirely driven by the `has_code_fence` binary flag. Ablation confirms: remove that one feature from the 14-feature surface set → SIV drops to 0.064. `has_code_fence` alone achieves SIV=1.000 but AUC=0.500 (pure luck at routing). The mechanistic story is: `has_code_fence=1` correlates with hard prompts (code tasks) in training → model learns to route code-fenced prompts to GPT-4 → wrapping every test prompt in fences triggers mass-escalation.

This is still a valid "surface shortcut" result, but the specific failure mode is "one content-type flag hijacks routing" not "linear models on length features are fragile." The experiment currently cannot distinguish between these because the perturbation is not feature-controlled.

**Overclaim to fix:** "SIV = fraction flipped under any clean perturbation" is presented as "the metric is blind to intent-robustness." But SIV only tests one kind of intent-robustness (invariance to encoding changes). A defender will correctly say: "this tests OOD generalization to unseen formatting, which any production system should handle with augmentation. Training with code-fence examples reduces SIV to near-zero without changing the underlying model." The paper needs to pre-empt this argument (see Section d for the counter).

---

### C2-IS — "all models near chance once surface controlled"

**Verdict: PARTIALLY SUPPORTED, overstated, ambiguous.**

The IS test shows tfidf IS=0.561 (t-test vs 0.5: p=0.035, significant at 3 seeds), semantic IS=0.520 (p=0.082, marginal), surface_logreg IS=0.518 (p=0.279, not significant). Surface_hgb IS=0.512 (p=0.308).

The honest summary: **only tfidf has a statistically detectable IS above chance; all others are consistent with pure surface-reading**. The paper says "every model — including semantic — drops to near-chance" but the correct statement is "every non-tfidf model drops to near-chance; tfidf retains weak but significant intent signal (IS=0.561)."

More importantly: the IS=0.561 for tfidf means tfidf reads *some* intent (it uses word content, not just counts), which mildly contradicts the framing that lexical models are pure surface readers. The paper's thesis is actually sharpened by this: the distinction is **linear-on-statistics (surface_logreg)** vs **content-word lexical (tfidf)** vs **semantic**, not simply "surface vs semantic."

**Construct validity risk:** Surface-matched pairs may still carry subtle surface differences the matcher missed. The 0.092 mean distance in standardized surface space sounds tight, but 14 features with unknown covariance → the actual surface similarity is unvalidated. A reviewer will ask: "did you verify that matched pairs have similar prompt length, topic, and domain (eval_name)?"

---

### C3 — "6.7× cost blowup under deployment shift"

**Verdict: SUPPORTED as a consequence, but NOT INDEPENDENT of SIV.**

Verification: `shift_c` equals `always_strong_c` to 8 decimal places. The 6.7× figure is arithmetically derived from SIV=0.875 + cost_ratio(GPT-4/Mixtral) + base_rate=0.354. Given SIV, the cost outcome is deterministic.

**Not a problem if framed correctly.** The independent contribution of C3 is: "AUC evaluated on clean data gives no warning of the cost blowup" — which is true and important. The reviewer attack to pre-empt: "this is just SIV expressed in dollars; one plot, not two findings."

**Strength of C3:** The cost blowup is not gradual — it is a cliff (0→∞ recovery of cost savings) because SIV near 1.0 means the router degenerates to always-strong. This is the "catastrophic" property that makes the failure mode policy-relevant. Make this explicit.

---

## (c) Top 6 Experiments/Changes to Raise Acceptance Odds

**Ranked by reviewer-attack surface they close, given current effort constraints.**

### 1. Per-perturbation SIV reporting + has_code_fence ablation (1 hour, already have the data)
The single most important fix. Current results already support this. Run a table: SIV per perturbation type, plus surface_logreg *without* has_code_fence (SIV drops to 0.064), plus `has_code_fence` alone (SIV=1.0, AUC=0.5). This converts the biggest vulnerability into a *strength*: "we can isolate which feature drives the fragility to one binary content-type flag — a failure mode that is invisible in standard eval but mechanistically interpretable."

### 2. Add bootstrap CIs and Cohen's h to all reported gaps (2 hours)
Zero new experiments needed — just statistical post-processing of existing results. Key numbers already computed:
- AUC gap (tfidf − semantic): 0.007, 95% CI [0.001, 0.017], semanticlosesto tfidf
- SIV gap (surface_logreg − semantic): 0.855, 95% CI [0.844, 0.865], Cohen's h = 2.12
- McNemar surface_logreg vs semantic: chi²=17.0, p<0.0001
- IS tfidf vs 0.5: p=0.035 (significant)
These numbers transform the paper from "descriptive" to "statistically rigorous."

### 3. Alternative weak/strong pair + RouteLLM substrate (half day)
Run the full experiment suite (E1–E3) with at least one alternative routing pair from RouterBench (e.g., GPT-3.5-turbo as weak, Claude-v2 as strong — available in the 11-model benchmark). If SIV story holds across pairs, external validity is established. If not, that's a critical finding about when the failure mode occurs (code-heavy benchmarks with one capable model). Either outcome is publishable.

### 4. IS caliper sweep + eval_name stratification (3 hours)
Run IS at caliper percentiles {10, 25, 50} and show IS is stable. Also stratify matched pairs by `eval_name` to confirm cross-domain matching (a math pair matched to a math pair defeats the test). This closes the construct-validity attack on IS and validates the matching procedure. Report distribution of match distances.

### 5. "Train-on-perturbed" robustness control (1 day)
Train surface_logreg on a mix of clean + code-fenced prompts (50/50 augmentation). Test: does SIV drop? Expected: yes, dramatically. This is crucial for the paper's claim that SIV reveals a structural eval failure, not just an easy fix. The right framing: "augmentation-training reduces SIV but does not fix the underlying label-surface correlation — the model learns to route both original and fenced prompts to GPT-4 whenever content-type flags trigger, at the cost of higher average cost." If augmentation genuinely fixes it, the failure mode is "model inadequacy, not metric blindness" — which is a different (weaker) claim. The paper *needs* this to know which claim it's making.

### 6. Track B: CloudSEN12 brightness vs spectral gatekeeper (1 GPU weekend)
Without Track B, the paper's title and abstract promise a cross-domain result it doesn't deliver. The satellite domain is where intent (physical scene content, SWIR-separable) and surface (brightness) are cleanly dissociable — providing the IS contrast the routing domain cannot give (IS≈0.5 for all routing models). Even a minimal Track B (brightness vs spectral classifier AUC parity + SEN2FIRE fire-deletion gallery + 5 "deleted disaster frames") transforms the paper from a routing eval note to the cross-domain eval-integrity paper it claims to be.

---

## (d) Strongest Honest Contribution Sentence

> **Across the LLM routing evaluation benchmark (RouterBench), we show that a routing classifier achieving competitive AUC (0.667) by learning a single content-type flag (`has_code_fence`) flips 87.5% of its decisions under a cosmetic encoding change that no practitioner would expect to matter, producing a 6.7× cost blowup in deployment — a failure that was rated equal to robust models by the stated metric and would never have been caught without the Surface-Invariance Violation (SIV) test we propose; and we show the benchmark itself is surface-saturated (IS ≤ 0.56 for all models once surface is matched), meaning no model trained on it can demonstrably route on task intent regardless of architecture.**

*If Track B is completed, extend to:*
> ...**and we demonstrate the same mechanism — surface-proxy capture at the gatekeeper layer — in onboard satellite triage, where the failure mode is irreversible (destroyed frames leave no audit trail) and the physical surface proxy (pixel brightness) is forensically separable from intent (SWIR spectral bands), giving a clean IS contrast the routing domain cannot provide.**

---

## Appendix: Computed Statistics Summary

| Test | Value | Interpretation |
|------|-------|---------------|
| AUC gap (tfidf − semantic), bootstrap 95% CI | 0.007, CI [0.001, 0.017] | tfidf **significantly beats** semantic (CI excludes 0); C1 holds (semantic does not outperform surface) |
| McNemar (surface_logreg vs semantic_logreg accuracy) | chi²=17.0, p<0.0001 | semantic significantly more accurate than surface_logreg; "equal accuracy" framing is wrong — should say "comparable AUC" |
| SIV gap (surface_logreg − semantic, code_fence), bootstrap 95% CI | 0.855, CI [0.844, 0.865] | Overwhelmingly significant |
| Cohen's h on code_fence SIV | 2.12 | Far exceeds "large" threshold (0.8); massive effect |
| IS tfidf vs 0.5 (seed-level t-test, n=3) | t=5.21, p=0.035 | Significant but low power (n=3 seeds) |
| IS semantic vs 0.5 | t=3.28, p=0.082 | Marginally significant at best |
| Length-only AUC (n_tokens alone) | 0.586 ± 0.006 | 0.586 << 0.667 (surface_logreg): length alone does NOT explain surface_logreg performance |
| Length-only SIV code_fence | 0.0004 ± 0.0001 | Near zero: length features do NOT drive the code_fence SIV |
| `has_code_fence`-ablated surface_logreg SIV | 0.064 ± 0.004 | Removing 1 of 14 features drops SIV from 0.875 → 0.064 |
| `has_code_fence` alone SIV | 1.000 (exact) | Single binary flag drives entire SIV result |
| C3 shift_c == always_strong_c | Exactly equal (8 decimal places) | 6.7× cost is deterministic from SIV; not an independent finding |
| whitespace_ratio AUC alone | 0.632 ± 0.005 | Strongest single surface feature; more predictive than n_tokens |

---

## Subsidiary Note on Construct Validity

**Reviewer attack:** "The SIV result just shows that training a linear logistic regression without data augmentation on a skewed dataset doesn't generalize to distribution-shifted inputs. Any production router would train with diverse prompt formatting. This is not an eval-integrity problem; it's a standard data-augmentation problem."

**Current paper's defense:** None. The paper has not run the augmentation control (see Experiment #5 above).

**Strongest counter-argument the paper can make (once the experiment is run):** "Even with augmentation, the benchmark itself prevents practitioners from *knowing they need it* — because SIV is never computed in standard practice, and the clean-data AUC gives no signal of the deployment degradation. Our contribution is not 'this model is fragile' (which augmentation fixes); it is 'this *metric* is blind to the fragility' (which augmentation does not fix — you still need SIV as an eval axis to know your router is deployment-ready)."

This distinction — metric blindness vs model fragility — is the paper's core defensible claim. It must be stated explicitly, and the augmentation control experiment provides the evidence needed to make it.
