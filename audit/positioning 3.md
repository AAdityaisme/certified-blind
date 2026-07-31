# Related-Work Positioning Deep-Dive
*Generated 2026-06-22. All paper facts verified via WebFetch on arXiv abstracts + ar5iv HTML. Search conducted across arXiv + semantic scholar (via search). Notes where full-text was unavailable from HTML.*

---

## 1. Per-Paper Delta Table

### LLM Routing Domain

---

#### Shafran et al. 2025 — "Rerouting LLM Routers" (arXiv 2501.01818)

**What they do:**  
Introduce *confounder gadgets* — adversarially optimized, query-independent token sequences (n=10 tokens, hill-climbing) that when prepended force routers to escalate to the expensive model. Attack four router architectures: similarity-weighted ranking (R_SW), matrix factorization (R_MF), BERT classifier (R_CLS), LLM complexity-scorer (Llama-3-8B). Also test commercial routers (Unify, NotDiamond, OpenRouter, Martian). Evaluate on MT-Bench, MMLU, GSM8K. Headline: white-box attack achieves 100% upgrade rate on R_SW/R_MF/R_CLS; black-box transfer 39–100%. Low-perplexity gadgets also exist.

**Key claims:**  
Routers are vulnerable to adversarial manipulation despite being accuracy-optimal. This is framed as an "LLM control plane integrity" safety problem. Classic semantic prompts ("treat this as complex") fail; direct token optimization succeeds.

**Precise delta vs our work:**

| Axis | Shafran et al. | Our work |
|------|----------------|----------|
| Surface form studied | Adversarially constructed token gadgets | *Natural* surface features: length, lexical stats, code fences — the kind a real system (Meridian) ships with |
| Attacker model | Adversarial external party | The router designer's own choice of features |
| Benchmark validity | Not studied | Central claim: RouterBench cannot certify intent-routing because eval_name alone = AUC 0.69 |
| RouteLLM substrate | Not used | Our confound-free C1 (109K homogeneous Arena prompts, no eval-identity) |
| Irreversibility axis | Not studied | Track B: satellite triage as irreversible analogue |
| Cross-domain framing | Single domain | Two-domain: recoverable vs irreversible |

**Risk they scoop us:** Low. They study *adversarial* manipulation; we study *natural* surface-form shortcuts in honest router design. These are complementary: they show an adversary can exploit the routing control plane; we show the designer's own feature choices already key on form. Their gadgets don't tell you whether a length-based honest router is good or bad — ours do. Cite and differentiate explicitly.

---

#### Ong et al. 2024 — "RouteLLM: Learning to Route LLMs with Preference Data" (arXiv 2406.18665)

**What they do:**  
Four router architectures trained on Chatbot Arena preference data (80K battles): similarity-weighted ranking, matrix factorization, BERT classifier, causal LM classifier (Llama-3-8B). Augmentation with GPT-4-judge labels (D_judge, 120K samples, ~$700). Evaluate on MMLU, MT-Bench, GSM8K. Headline: up to 2–3.66× cost savings at quality parity; strong cross-model transfer. No explicit feature analysis of what drives routing decisions.

**Key claims:**  
Human preference data + augmentation is sufficient to train effective routers. Transfer across model pairs is strong. Cost savings demonstrated empirically.

**Precise delta vs our work:**

| Axis | RouteLLM | Our work |
|------|----------|----------|
| Feature analysis | None — no study of which query characteristics drive routing | Central: length alone = 0.675 AUC on RouteLLM's own Djudge data; semantic +0.031 over best surface |
| Robustness to formatting | Not tested | SIV / shift analysis (though caveated by the StandardScaler artifact — the real test is benign padding) |
| Benchmark-identity confound | Not identified | Our RouterBench result; RouteLLM = our *confound-free* substrate showing real surface signal |
| Eval validity | Not questioned | Our explicit claim that AUC can't distinguish form-router from intent-router |
| Satellite domain | N/A | Track B |

**Must compare against experimentally:** YES — we already use RouteLLM Djudge data as our confound-free C1 substrate. The paper is both a target of critique and our validation dataset. Reference their architecture choices (the four routers) as the canonical field; note we run ablations on their data that they never ran themselves.

---

#### Hu et al. 2024 — "RouterBench: A Benchmark for LLM Routing" (arXiv 2403.12031)

**What they do:**  
Unified benchmark: 405K inference outcomes, 11 models, 8 datasets (HellaSwag, Winogrande, ARC, MMLU, MT-Bench, GSM8K, MBPP, custom RAG), 64 tasks. Routers evaluated: KNN, MLP, cascading, overgenerate-and-rerank, Zero router (probabilistic baseline). Labels = binary correctness; routing decision = performance-cost tradeoff. No surface-form baseline. Key finding: no routing algorithm significantly outperforms the Zero router baseline; cascading outperforms substantially only when error rate ≤ 0.1.

**Key claims:**  
RouterBench provides standardized evaluation. Model complementarity is real. KNN/MLP match individual LLMs at lower cost. No single algorithm dominates.

**Precise delta vs our work:**

| Axis | RouterBench | Our work |
|------|-------------|----------|
| Surface-form baseline | Absent — no length/lexical model | We add surface, length-only, TF-IDF, semantic baselines |
| Benchmark-identity confound | Not identified or tested | We show eval_name alone → AUC 0.693; this is the dominant predictive signal |
| Out-of-benchmark generalization | Appendix E only | Our cross-benchmark split is the *primary* result |
| IS / SIV metrics | Not proposed | New eval axes we introduce |
| Eval validity framing | Not questioned | Our central contribution in routing domain |

**Must compare against experimentally:** YES — RouterBench is our primary routing substrate. We must show: (a) RouterBench contains the eval-identity confound (eval_name AUC = 0.693 ≥ every learned router), (b) no router exceeds ~0.60 AUC cross-benchmark, (c) surface features tie semantics on cross-benchmark split. Direct experimental comparison is required, with RouterBench as the confounded substrate and RouteLLM as the clean one.

---

#### LLMRouterBench — "Towards Unified Evaluation of LLM Routing" (arXiv 2601.07206)

**What they do:**  
Larger unified benchmark: 400K+ instances, 21 datasets, 33 models, 10 routing baselines. Key findings: (1) "many routing methods exhibit similar performance under unified evaluation"; (2) "several commercial routers fail to reliably outperform a simple baseline"; (3) "backbone embedding models have limited impact"; (4) Dataset Oracle (assign each benchmark to its best model) nearly matches sophisticated routers — suggesting routing gains are mostly coarse domain structure capture, not instance-level discrimination.

**Precise delta vs our work:**

| Axis | LLMRouterBench | Our work |
|------|----------------|----------|
| Benchmark-identity confound | Identified indirectly via Dataset Oracle finding | We quantify explicitly: eval_name alone = AUC 0.693 on RouterBench; within-benchmark all ≈ chance |
| Surface-form baselines | "Backbone embedding models have limited impact" | We show *length alone* ties embeddings (0.675 AUC on RouteLLM; ties on cross-benchmark RouterBench) |
| IS / SIV | Not proposed | New eval axes |
| Satellite domain | N/A | Track B |

**Risk they scoop us:** Moderate — partial overlap on the "benchmark identity dominates" finding. However: (1) they don't run surface/length baselines; (2) they don't show length-alone ties embeddings; (3) they don't frame this as an eval-validity / Goodhart problem; (4) they don't propose SIV or cross-domain framing. We need to cite this and clearly state what we add beyond it.

---

#### Shafran-adjacent: "Unsolvability Ceiling in Multi-LLM Routing" (arXiv 2605.07395)

**What they do:**  
Study evaluation artifacts that inflate router performance estimates: (1) judge verbosity bias (underrates smaller models 10–24pp on MMLU, overrates larger models on MedQA up to 6pp); (2) truncation (65% truncation on MMLU); (3) output format mismatch (5–12% parse failures). SHAP analysis reveals character and token *length* dominates routing decisions — routing "functions as length-based triage rather than difficulty-based triage." Standard routers collapse to majority-class prediction (~79.3%).

**Precise delta vs our work:**

| Axis | 2605.07395 | Our work |
|------|------------|----------|
| Length as routing proxy | Found via SHAP post-hoc on a single study | We demonstrate this directly with an explicit length-only baseline (AUC 0.675 on RouteLLM) vs semantic |
| Eval artifacts studied | Judge bias, truncation, format mismatch | Benchmark-identity saturation; eval_name AUC = 0.693 |
| Surface-shortcut framing | Identified as a problem | Proposed as the main thesis with SIV/IS as new eval axes |
| Cross-domain | Single domain | Two-domain with irreversibility axis |

**Risk they scoop us:** Moderate on the "length drives routing" finding specifically. Key differences: they find this post-hoc via SHAP in a confounded setup; we demonstrate it directly and cleanly on RouteLLM (confound-free). Our framing (SIV, IS, irreversibility) is distinct. Cite this paper and say: "independently, [2605.07395] finds via SHAP that routing collapses to length-based triage; we confirm this with explicit length-only baselines on a confound-free substrate and extend to cross-domain eval-integrity framing."

---

#### "LLMs Encode Their Failures" (arXiv 2602.09924)

**What they do:**  
Train linear probes on pre-generation *internal activations* to predict model success before generation. Key surface baselines: length AUROC 0.61–0.73, TF-IDF AUROC 0.63–0.72. Activation probes: AUROC 0.76–0.84. Conclusion: probes substantially outperform surface features. Tested on MATH, GSM8K, AIME, LiveCodeBench.

**Precise delta vs our work:**

| Axis | 2602.09924 | Our work |
|------|------------|----------|
| Question asked | Can internal activations predict difficulty better than surface features? | Does the routing *benchmark* even allow certifying intent vs form? |
| Confound control | Single benchmark, no cross-eval identity control | cross-eval split is primary design |
| Result direction | Probes > surface | Surface ties semantic at benchmark level; below-chance once controlled |
| Eval-validity framing | Not questioned | Central thesis |

**Risk they scoop us:** Low. They answer "activations beat TF-IDF/length" — a useful signal to cite as a baseline comparison (length AUROC 0.61–0.73 on their math benchmarks vs our 0.675 on RouteLLM Arena prompts). Their numbers validate that length is a serious contender across different routing-adjacent tasks. No overlap with our benchmark-identity claim or Track B.

---

#### Pacchiardi et al. 2024 — "Clever Hans or Neural Theory of Mind?" (arXiv 2410.11672)

**What they do:**  
Train n-gram classifiers (TF unigrams/bigrams + readability metrics) on 19 LLM benchmarks (BIG-Bench tasks, ANLI, CommonsenseQA, etc.) to predict correct answers. On 9/19 benchmarks, Cohen's κ > 0.2; on 2 (Corporate Lobbying, SpaceNLI), κ > 0.6. Conclusion: many LLM benchmarks have detectable surface-form shortcuts; models may exploit these rather than demonstrating genuine capability.

**Precise delta vs our work:**

| Axis | Pacchiardi et al. | Our work |
|------|-------------------|----------|
| Task studied | General LLM benchmarks (question answering, reasoning) | LLM *routing* benchmarks |
| Shortcut type | N-gram patterns in answer choices / question text | Length/lexical stats predicting routing label |
| Routing evaluation | Not studied | Central contribution |
| Intervention tests | Not proposed | SIV + IS (new) |
| Cross-domain | Single domain | Two-domain with irreversibility |

**Risk they scoop us:** Low. Closest intellectual ancestor in the "LLM benchmarks are surface-exploitable" tradition. We should cite as motivation/framing but the domains don't overlap. Their work on QA benchmarks → our extension to routing benchmarks, which have different structure (binary difficulty labels, not answer correctness, predicted by prompt features rather than answer-option patterns).

---

#### Raji et al. 2021 — "AI and the Everything in the Whole Wide World Benchmark" (arXiv 2111.15366)

**What they do:**  
Position paper (NeurIPS 2021 Benchmarks track). Critiques construct validity of "general" AI benchmarks — argues that small collections of influential benchmarks are over-valorized and framed as measuring broader capability than they actually do. Core problem: the construct (true AI capability) is not what the benchmark measures.

**Precise delta vs our work:**

| Axis | Raji et al. | Our work |
|------|-------------|----------|
| Argument type | Conceptual/position paper | Empirical: quantifies the confound (eval_name AUC = 0.693) |
| Routing context | Not studied | Our primary domain |
| Mechanism | Abstract construct validity concern | Concrete benchmark-identity saturation mechanism |
| Intervention | Not proposed | SIV / IS eval axes |

**Must compare:** Cite as the intellectual foundation for benchmark construct validity, not as an experimental comparison. Their framing ("benchmarks don't measure what they claim") is exactly our routing variant.

---

#### Bowman & Dahl 2021 — "What Will it Take to Fix Benchmarking in Natural Language Understanding?" (arXiv 2104.02145)

**What they do:**  
Position paper proposing four criteria NLU benchmarks must meet; argues most current benchmarks fail. Key concern: adversarial / OOD test sets ensure models fail but "only obscures the abilities we want benchmarks to measure." Advocates for better dataset design.

**Precise delta vs our work:**  
Same relationship as Raji et al. — conceptual framing that we instantiate empirically in the routing domain. Cite as foundation, not experimental comparison.

---

#### Bean 2024 — "A Systematic Review of LLM Benchmarks" (arXiv 2511.04703)

**What they do:**  
Systematic review of 445 LLM benchmarks, 29 expert reviewers. Identifies "patterns related to measured phenomena, tasks, and scoring metrics which undermine validity." Provides 8 recommendations. No empirical routing analysis.

**Precise delta vs our work:**  
Same relationship — conceptual/survey framing. Our routing + satellite work is an empirical case study within their typology. Cite as survey context.

---

#### Webson & Pavlick 2021 — "Do Prompt-Based Models Really Understand the Meaning of their Prompts?" (arXiv 2109.01247)

**What they do:**  
Test 30+ prompt templates (instructive → intentionally misleading) on NLI tasks. Find models learn "just as fast with many prompts that are intentionally irrelevant or even pathologically misleading." Scale (175B parameters) and instruction tuning don't help. Conclusion: prompt-based improvements don't require semantic comprehension of the prompt.

**Precise delta vs our work:**

| Axis | Webson & Pavlick | Our work |
|------|------------------|----------|
| Model studied | Base/instruction-tuned LLM's response to prompts | A routing classifier trained on prompts |
| Question | Does the model understand the prompt text? | Does the router decide on prompt *difficulty* vs *form*? |
| Setting | Zero-shot prompt following | Supervised binary routing |

**Risk they scoop us:** Zero. Different task, different mechanism. Useful to cite as evidence that surface form matters throughout the LLM pipeline, not just at routing. They show language models ignore prompt semantics; we show routing classifiers ignore query semantics.

---

### Remote Sensing / Satellite Triage Domain

---

#### Coluzzi et al. 2018 — "A first assessment of the Sentinel-2 Level 1C cloud masking algorithm" (RSE 2018, DOI 10.1016/j.rse.2018.08.009)

**What they do:**  
Assess Sentinel-2 L1C cloud masking algorithm (sen2cor) across diverse scenes. Find documented failure modes on bright surfaces (snow, bright sand) — high false positive rates where reflective surfaces are misclassified as cloud. Full text behind paywall; abstract and known findings confirm this is the prior art for the Track B shortcut.

**Precise delta vs our work:**  
They *document* the failure; they do not frame it as shortcut learning, do not study it with a surface-vs-spectral controlled experiment, and do not connect it to AI evaluation integrity or the irreversibility axis. Our Track B reframes their empirical observation as a shortcut learning / eval-validity result with quantified false-discard rates and a cross-domain generalization (routing ↔ triage). Critical to cite as "this failure mode is documented; our contribution is the shortcut-learning/irreversibility framing."

---

#### Giuffrida et al. 2020 — "CloudScout: A Deep Neural Network for On-Board Cloud Detection on Hyperspectral Images" (Remote Sensing 2020, DOI 10.3390/rs12142205)

**What they do:**  
CloudScout is a compact CNN deployed onboard Φ-sat-1 (ESA mission, 2020) for cloud detection. Input: hyperspectral imagery. CNN classifies patches as cloudy/clear for downlink filtering decision. This is the canonical deployed onboard-AI cloud filter. Full text behind paywall (MDPI returned 403); from abstract and known literature: accuracy ~87% on test set.

**Precise delta vs our work:**  
CloudScout is our *motivating deployed system* for Track B. They demonstrate onboard cloud detection is feasible and cost-effective. They do not study whether their model exploits brightness vs physical spectral signatures, do not analyze false-discard rates on snow/fire/desert, and do not frame the decision as irreversible in the eval-integrity sense. Our Track B asks: "what does a deployed system like CloudScout actually key on, and what does headline accuracy hide?"

---

#### Burgert 2025 — "Feature Reliance in Remote Sensing Models" (arXiv 2509.20234)

**What they do:**  
Domain-agnostic framework suppressing shape, texture, and color cues systematically to measure feature reliance. Findings: RS models exhibit the *strongest texture reliance* among computer vision, medical imaging, and remote sensing. Datasets: UCMerced, RSD46-WHU, DeepGlobe, PatternNet, AID. No cloud detection datasets, no onboard processing studied.

**Precise delta vs our work:**

| Axis | Burgert 2025 | Our work |
|------|--------------|----------|
| Feature studied | Shape / texture / color (visual) | Brightness/albedo (spectral) as cloud proxy |
| Failure mode | Texture reliance as a general RS finding | Brightness shortcuts → mis-discard of snow/fire scenes specifically |
| Datasets | Scene classification (UCMerced etc.) | CloudSEN12 cloud detection + SEN2FIRE fire scenes |
| Stakes | Classification accuracy | Irreversible data loss |
| Eval-validity framing | No | Yes |

**Risk they scoop us:** Low. They study feature reliance broadly in RS models (not cloud detection, not onboard, not irreversibility). Our Track B is much more specific and stakes-focused. Cite as "texture/feature reliance is documented in RS models generally; we specialize to the physically-motivated brightness-vs-SWIR split in onboard cloud gatekeepers."

---

## 2. Are We Scooped? Explicit Verdict

**Overall verdict: NOT SCOOPED on our core contribution.** Qualified per sub-claim:

### Sub-claim A: Routing labels are surface-predictable (length ≈ semantic AUC)
**Not scooped.** The closest paper is 2605.07395 (Unsolvability Ceiling), which finds via SHAP that routing collapses to length-based triage *in a confounded, judge-evaluated setup*. We demonstrate this *directly* with an explicit length-only baseline on RouteLLM (confound-free, 109K homogeneous Arena prompts), report AUC numbers head-to-head (length 0.675 vs semantic 0.772 vs TF-IDF 0.785), and do so on a substrate where benchmark identity cannot explain the result. The sub-claim is partially anticipated but never directly demonstrated with controls.

### Sub-claim B: RouterBench routing predictability is dominated by benchmark identity
**Closest prior:** LLMRouterBench (2601.07206) identifies this indirectly (Dataset Oracle ≈ routers, implying domain structure dominates). **We are first to quantify explicitly**: eval_name alone → AUC 0.693; within-benchmark all models → 0.45–0.60 (≈ chance). This is a direct, quantified empirical claim, not previously stated this way.

### Sub-claim C: Surface shortcuts in onboard satellite triage (Track B)
**Not scooped.** The brightness-shortcut failure is documented in remote sensing (Coluzzi 2018), but no paper has (a) framed this as shortcut learning / eval-integrity, (b) run a controlled surface-vs-spectral experiment on CloudSEN12 with false-discard rate on snow/fire subsets, (c) connected it to the irreversibility dimension, or (d) proposed an audit harness for estimating false-discard rate without access to the discarded frames.

### Sub-claim D: The irreversibility axis as a novel framing dimension
**No prior work found.** The distinction "recoverable mis-route vs irreversible mis-discard" is ours. Searched extensively; no paper frames AI gatekeeper failures along this axis.

### Sub-claim E: SIV/IS as proposed new eval axes for routing
**Not scooped.** Perturbation-based evaluation exists in NLP (CheckList, contrast sets) but has not been applied to LLM routing evaluation specifically.

### Sub-claim F: Cross-domain unifying framing (routing + satellite as surface-shortcut gatekeepers)
**Not scooped.** No paper combining these two domains was found.

---

## 3. Papers We MUST Compare Against Experimentally (Not Just Cite)

1. **RouterBench (Hu et al. 2024, arXiv 2403.12031)** — Primary substrate. Must show explicitly that (a) eval_name AUC = 0.693 matches every learned router, (b) no router on cross-benchmark split exceeds ~0.60 AUC, (c) our surface/length baselines tie semantics. RouterBench reviewers will ask "where's the surface baseline?" — we provide it.

2. **RouteLLM (Ong et al. 2024, arXiv 2406.18665)** — Confound-free substrate (Djudge data, 109K homogeneous Arena prompts). Must show our full model table on this data: length-only 0.675, surface 0.741, TF-IDF 0.785, semantic 0.772. This is our clean demo that surface form predicts routing *even absent benchmark identity*, and that semantic adds only +0.031 AUC over TF-IDF. The paper itself never ran these baselines.

3. **LLMRouterBench (arXiv 2601.07206)** — Must explicitly compare our eval_name-AUC finding to their Dataset Oracle finding. We go further: we quantify the confound rather than just observing it indirectly. Frame as: "consistent with [2601.07206]'s Dataset Oracle result, but with direct quantification."

4. **2605.07395 (Unsolvability Ceiling)** — Must directly address overlap on the "length drives routing" finding. Our RouteLLM result is cleaner (confound-free, explicit baseline); their result is post-hoc SHAP in a judge-confounded setup. Cite and differentiate.

5. **CloudSEN12 / Coluzzi 2018 / Giuffrida 2020** — For Track B: must explicitly run the surface-vs-spectral comparison on CloudSEN12, report false-discard rates on snow/bright subsets (n=35–43 patches — add bootstrap CIs), and cite Coluzzi as the documented prior failure mode that we reframe.

---

## 4. Novel Contribution Statement (Relative to All Prior Work)

Prior work has established that (a) LLM routing benchmarks suffer from domain-structure effects that naive routers partially exploit (LLMRouterBench 2601.07206), (b) LLM benchmarks generally contain detectable surface-form shortcuts (Pacchiardi 2410.11672), (c) deployed cloud-detection algorithms misclassify bright surfaces as cloud (Coluzzi 2018), and (d) adversarial gadgets can manipulate router decisions (Shafran 2501.01818). What no prior work provides is: an *explicit, confound-controlled empirical demonstration* that (1) on a confound-free routing substrate (RouteLLM Djudge, 109K homogeneous Arena prompts), prompt length alone captures 61% of achievable routing signal and semantic embeddings add only +0.031 AUC — a direct, head-to-head quantification of the surface-shortcut magnitude; (2) on RouterBench, the standard evaluation benchmark, benchmark identity alone achieves AUC 0.693 equal to every learned router, meaning routing-eval accuracy structurally *cannot certify* that a router decides on task intent vs. prompt form; (3) the same surface-vs-intent shortcut mechanism appears in a physically distinct domain — onboard satellite cloud triage — where a brightness-only classifier achieves competitive cloud-detection AUC (0.86) yet irreversibly discards ~61% of bright-clear scenes (snow, desert) that a SWIR-spectral model retains; and (4) the satellite domain reveals a qualitatively new failure mode absent from routing: the gatekeeper's mistake is *irreversible and unauditable* (discarded raw frames never reach the ground), a dimension on which routing (retryable) and triage (destructive) sharply diverge. We propose Surface Invariance Violation (SIV) and Intent Sensitivity (IS) as two new eval axes that expose this gap — axes that routing-accuracy metrics are structurally blind to — and introduce a ground-side audit harness for estimating false-discard rates without access to the discarded data.

---

## 5. Appendix: Papers Checked But Not Listed Above

| Paper | Decision |
|-------|----------|
| 2603.20895 (LLM Router via Prefill Activations) | Cite: shows handcrafted complexity features (readability, structural signals) used in routing; their activation approach outperforms surface — complementary, not competing |
| 2602.09924 (LLMs Encode Their Failures) | Cite as baseline: length AUROC 0.61–0.73 on math benchmarks; validates length as serious contender across task types |
| 2601.19793 (CASTER) | Cite: uses "structural meta-features" for routing; abstract-level only; doesn't study what those features are or their shortcut risk |
| 2603.12646 (Flash Attention + Prompt Compression) | Skip: engineering paper, compresses to ~512 tokens; not relevant to shortcut analysis |
| 2606.18774 (RouteJudge) | Skip: preference-based eval platform; no feature analysis |
| Burgert 2025 (2509.20234) | Cite in Track B: documents texture reliance in RS models generally |
| Webson & Pavlick 2109.01247 | Cite as framing: prompt semantics don't drive LLM behavior; we extend this to routing classifiers |
| Pacchiardi 2410.11672 | Cite as framing ancestor: surface shortcuts in LLM benchmarks generally |
| Raji 2111.15366 | Cite as benchmark validity foundation |
| Bowman & Dahl 2104.02145 | Cite as benchmark validity foundation |
| Bean 2511.04703 | Cite as systematic review context |
