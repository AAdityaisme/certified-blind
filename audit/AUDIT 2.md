# Master Audit — syntax-intent-eval (2026-06-22)

Synthesis of: my own diagnostics (`leakage_check.py`, `honest_c1.py`,
`verify_reviewer_claims.py`, `verify_citations.py`), two adversarial opus
reviewers (`reviewer_correctness.md`, `reviewer_design_stats.md`), and four
verified literature sweeps (`paper/references/*`).

**Every reviewer claim below was independently re-measured before being accepted.**
The correctness reviewer logged only 1 tool call, so all its numbers were
re-derived in `verify_reviewer_claims.py`; they held.

## Verdict by claim

| Claim (as written in experiment_log) | Status | Decisive evidence |
|---|---|---|
| **C1** surface ≈ semantic on AUC (~0.70) | **ROBUST but RE-FRAME** | Real, but ~0.70 is the eval-identity confound; honest cross-benchmark AUC ≈0.55–0.60 for all. The deeper claim ("no model routes on intent") is TRUE and stronger. |
| **C2-SIV** surface_logreg flips 87.5% under code-fence | **ARTIFACT — drop/reframe** | StandardScaler z=109.7 on a feature firing in 2/24051 train rows. RobustScaler→0.088; drop-feature→0.063. Not a routing-on-form finding. |
| **C2-IS** all models ~chance once surface controlled | **PARTLY ROBUST, NARROW** | True numerically, but 97.2% of matched pairs are intra-eval → tests within-benchmark hard/easy, not cross-domain intent. Only tfidf sig > chance (p=0.035). |
| **C3** 6.7× cost blowup under shift | **ARTIFACT — drop** | shift_cost == always-strong cost exactly; arithmetic consequence of the SIV artifact. RobustScaler shrinks blowup to ~1.4×. |
| tfidf robust (SIV 0) | **VACUOUS — drop** | cosine(orig, perturbed)=0.998; TfidfVectorizer normalizes whitespace; the perturbation is a tokenizer no-op. |
| Label = weak fails (binary) | **NEEDS DISCLOSURE + sensitivity** | 21.1% of score cells non-binary; GSM8K (22% of data) 100% non-binary; thresholded at 0.5 silently. |
| No train/test leakage | **CONFIRMED CLEAN** | 32,056/32,069 unique prompts; cross-split exact leakage 0.0004; dedup split changes nothing. |
| 77 citations | **VERIFIED** | 54 arXiv + 23 DOI resolve; 0 fabricated (`verify_citations.py`). |

## A. The robust core (what the paper can stand on)

**Routing-benchmark surface/identity saturation.** Independently verified
(`honest_c1.py`, `leakage_check.py`):
- Predicting `route_premium` from `eval_name` ALONE → AUC **0.693** (= every model).
- Within single benchmarks, surface AUC 0.45–0.59 (≈ chance).
- Group-by-eval (disjoint benchmarks) AUC: surface_hgb 0.603, surface_logreg
  0.592, length_only 0.570, tfidf 0.564, semantic 0.544. **Length-alone ties
  sentence embeddings; nothing exceeds ~0.60.**
- McNemar (design reviewer): semantic is *significantly* more accurate than
  surface_logreg (p<1e-4) → say "comparable AUC", NOT "equal accuracy".

Interpretation: RouterBench routing predictability is dominated by benchmark
identity; no model demonstrably routes on task intent. This is a measurement-
validity contribution, consistent with LLMRouterBench (2601.07206), Pacchiardi
"Clever Hans" (2410.11672), Raji (2111.15366), Bowman & Dahl (2104.02145).

## B. The artifacts (must drop or honestly reframe)

`verify_reviewer_claims.py` section A, exact numbers:
```
has_code_fence: train rate 0.000083 (2/24051); StandardScaler z@1 = 109.7
                scaler=standard  code_fence SIV=0.881 (route→1.000)  whitespace SIV=0.877
                scaler=robust    code_fence SIV=0.088 (route→0.206)  whitespace SIV=0.877
                scaler=none      code_fence SIV=0.545                whitespace SIV=0.097
                standard, drop has_code_fence: code_fence SIV=0.063  whitespace SIV=0.877
```
- code-fence SIV/cost: **StandardScaler×rare-feature artifact.** Drop as a headline.
- whitespace SIV: survives RobustScaler but the transform is aggressive/unrealistic
  and vanishes without scaling → scaling-sensitivity, not a clean robustness result.
- The honest residual: "naive linear routers with StandardScaler are a deployment
  footgun under feature-distribution shift" — a real but minor MLOps point, NOT
  evidence the metric is blind to intent.

## C. Label validity (`verify_reviewer_claims.py` section B)
Non-binary score fraction 0.2115; unique scores {0,0.1,0.2,0.25,0.3,0.4,0.5,0.6,
0.7,0.75,0.8,0.9,1.0}; (0.4,0.6) = 0.0334. Fully non-binary evals: mtbench*,
grade-school-math, consensus_summary, chinese_idioms. Fix: disclose threshold,
add a sensitivity analysis (sweep τ; exclude continuous-graded evals as a check).

## D. Citation audit
77 verified (`verify_citations.py`): 54 arXiv (month-validated), 23 DOI (doi.org
content negotiation), 0 fabricated. `paper/references/verified.bib`. Non-arXiv/DOI
items still TODO: Strathern 1997 (have DOI 10.1017/s1062798700002660 — resolved),
Krakovna blog (grey lit), s2cloudless/CEMS-Wildfire (grey lit), Planet/Satellogic
onboard (press only).

## E. Prioritized fix list

CRITICAL (do before any drafting):
1. Re-frame routing track around the ROBUST eval-identity/surface-saturation
   result. Demote/cut SIV-0.875 and C3-6.7× (artifacts). Use group-by-eval as the
   primary split everywhere.
2. Disclose + sensitivity-test the 0.5 score threshold; report group-by-eval as default.
3. Correct all "equal accuracy" → "comparable AUC"; add bootstrap CIs + McNemar to
   every comparison (design reviewer computed: AUC gap CI [0.001,0.017]; SIV Cohen h=2.12).

HIGH:
4. If keeping any perturbation test: use RobustScaler (or scaler-free / tree models),
   realistic perturbations (paraphrase), and report per-perturbation + ablation. The
   honest result may be "routers are mostly robust except the StandardScaler footgun."
5. Narrow IS claim to "within-benchmark difficulty" (97.2% intra-eval) or rebuild
   matching with cross-eval constraint.
6. Add RouteLLM (Djudge, 2406.18665) as a second substrate — homogeneous Chatbot
   Arena data → NO eval-identity confound → the cleanest test of whether surface
   form predicts routing absent benchmark identity. THIS IS THE KEY NEW EXPERIMENT.

MEDIUM:
7. Disclose non-English prompts; tfidf preprocessing; seed all RNGs.
8. **Track B (satellite EO)** — where intent (ground signal) vs surface (brightness)
   is physically separable and the shortcut is literature-documented (Coluzzi 2018,
   Burgert 2025). This is where the CLEAN cross-domain story actually lives and is
   NOT subject to the routing artifacts.

## F. Recommended reframe (honest, strongest version)

The flashy "router flips 87% / costs 6.7×" demos do not survive. The paper's real,
defensible spine is narrower and more about MEASUREMENT:

> On the standard LLM-routing benchmark, routing-label predictability is almost
> entirely benchmark-identity; once you control for it, neither surface features,
> lexical models, nor strong sentence embeddings beat ~0.60 AUC, and a single
> length feature ties embeddings — i.e. the benchmark cannot certify that any
> router decides on task intent rather than form. We then move to a domain where
> the same surface-vs-intent gatekeeping is physically separable and the decision
> is irreversible — onboard satellite data triage — where a brightness-shortcut
> classifier discards snow/fire scenes a spectral model keeps.

Routing = the measurement-validity warning (robust). Satellite = the consequential,
clean demonstration (Track B, to build). The cross-domain paper is still viable —
but its weight must shift to Track B, and the routing artifacts must be cut.

---

# ROUND 2 — Deep re-audit (2026-06-22)

3 opus agents (positioning/scooping, fresh re-audit incl. Track B, conference
assessment) + my own re-verification of every CRITICAL claim (agents with low
tool-call counts were re-measured in `audit/verify_reaudit2.py`, `trackb_leakage.py`,
`honest_c1.py`). New experiments this round: GroupKFold Track B, audit harness S3,
length-padding intervention, char-ngram ablation.

## Conference verdict (assessment agent + corroborated)
Workshop-tier now; **realistic 20–30% NeurIPS-D&B / ICLR shot** with the fix-list.
Track B is the STRONGER half (its shortcut is architectural — a brightness-only
model lacks SWIR, so augmentation can't fix it — which neutralizes the #1 rejection
risk "just augment your training data"). Novel contribution = **irreversibility axis
+ SIV/IS as eval axis + audit harness**, NOT the routing observation alone.

## Scooping verdict (positioning agent + verified)
NOT scooped. Closest = **Garg & Sagtani 2026 "Unsolvability Ceiling" (2605.07395,
verified real)**: label-side routing-eval artifacts (judge verbosity bias) →
routers collapse to majority-class. DELTA: feature-side vs label-side, no RouteLLM,
single-domain. Must cite + differentiate; disclose their judge-bias finding as a
caveat on our GPT-4-judge RouteLLM label. Track B fully uncrowded (Coluzzi/Burgert
document the failure but never as shortcut-learning / controlled / irreversible).

## Confirmed-by-my-own-measurement
- RouteLLM surface signal real: length_only AUC **0.672** (content-free), char-ngram
  **0.770** ≈ semantic **0.772**. Surface form matches embeddings; semantics adds
  little. Caveat: length partly tracks true difficulty (soft shortcut).
- Track B spatial leakage 100% but result survives GroupKFold (AUC ±0.004, gap holds).
- Audit harness S3: recall 0.705, precision 0.365, 3.1× lift.
- Routing length-padding intervention: NULL (no clean decision-flip; reported honestly).

## CRITICAL fixes (confirmed, before any submission)
1. **"snow/desert" → "bright clear surfaces (mixed LC)".** Verified: n=35 = 28 bare
   + 7 snow; n=43 mixed. 7 snow too few for a snow CI. Lead with brightness-cut +
   gallery as illustration. (log corrected.)
2. **GroupKFold(roi_id) Track B** — DONE (now default in s1_s2_cloud.py).
3. **char-ngram surface ablation** — DONE (verify_reaudit2.py): pure surface 0.77 ≈
   semantic; kills "tfidf is just content" objection by anchoring on length_only.
4. **Stats everywhere** — bootstrap CI + McNemar + Cohen h. Partly computed (design
   reviewer: SIV gap h=2.12; AUC gap CI [0.001,0.017]). Need: gap CI on Track B S2,
   20+ seeds for RouterBench cross-eval (current 3 seeds S/N<2).
5. **Track B threshold sweep + zero-padding mask** — FDR threshold-dependent (44–79%)
   but 4–5× ratio holds; mask 3,063 padding px (−1.17% bias, cancels in ratio).

## HIGH (competitiveness)
6. Track B SIV/IS + SEN2FIRE fire-deletion gallery — symmetric cross-domain (the
   physical IS contrast: SWIR separates intent from surface where routing can't).
7. Compare against the ACTUAL RouteLLM trained router + real cloud detectors
   (s2cloudless/sen2cor labels ARE in CloudSEN12) — is our brightness model a
   strawman vs deployed detectors? (re-audit flagged; not yet run.)
8. Promote RouteLLM as primary routing C1 in the writeup; RouterBench confound = a
   separate finding. Disclose RouteLLM judge-bias + no user-level dedup as limitations.

## Net
Foundation is now HONEST and mostly solid. Two real claims survived every audit:
(C1) routing eval can't certify intent — surface matches semantics, confound-free;
(Track B) brightness triage irreversibly discards bright clear scenes the metric
can't see, with a working ground-side audit harness. Remaining work is rigor
(stats, sweeps, symmetric Track B) + honest reframing, not new core findings.
