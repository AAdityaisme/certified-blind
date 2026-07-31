# Option C Assessment — Alternative Domain Pivot
*Senior ML researcher adversarial review. 2026-06-27. Based on full audit corpus + targeted literature sweep across 7 candidate domains.*

---

## Context and Framing

T1b killed "deployed onboard satellite systems lose snow data NOW." What we retain is a domain-agnostic framework: (1) irreversible AI gatekeepers make their own false-discard rate MNAR-unidentifiable from retained data (Props 1–2, identifiability.md, sharp Manski bounds); (2) a pre-triage probe point-identifies the rate; (3) cross-detector/cross-model consensus + cheap physical proxies recover ~96% of individual losses label-free. This framework is transferable. Option C asks: is there a better domain where the gatekeeper demonstrably fails NOW, the error is unobservable by construction, and a solo student can run experiments with public data before September?

For a domain to beat satellite, it needs: a REAL demonstrated failure (not hypothetical), genuine irreversibility (data gone, not just delayed or recoverable on appeal), public data a solo student can actually run, and a clean mapping to the identifiability + audit framework. It also needs to be uncrowded enough that the paper's formal contribution is novel, not redundant with an active literature.

---

## Domain Survey

### Domain 1 — LHC / Particle Physics Trigger Systems

**What it is.** The LHC collides protons at 40 MHz. Hardware triggers (Level-1) reduce this to ~100 kHz; software triggers (HLT) reduce to ~1 kHz for permanent storage. Events not selected are GONE — raw detector data overwrites itself in microseconds. The trigger decision is, by construction, irreversible.

**(a) Irreversibility + unobservability of the error?**
PERFECT. This is the purest instantiation of the gatekeeper model that exists anywhere in science. Every undiscarded event is stored; every discarded event is absolutely unrecoverable. The error — discarding a real new-physics collision — is unidentifiable from the stored dataset by definition: if it's not in the dataset, you cannot estimate its rate from the dataset. The LHC community explicitly acknowledges this. Matt Strassler (Princeton HEP public explainer) writes directly: "More critically, unless the new physics is selected by a trigger algorithm, it will be lost forever." Run-3 CMS/ATLAS papers (arXiv:2408.03881, 2401.06630) confirm trigger decisions are irreversible and signal efficiency is a first-order design concern.

**(b) Demonstrated real failure?**
YES — and it is well-documented. Long-Lived Particle (LLP) searches (dark photons, displaced vertices, exotic decays) were being systematically missed by standard triggers designed for prompt signatures. The LLP community showed efficiency gains of 2.6–8.5× at LHCb and 6–17× at CMS by adding dedicated LLP triggers — meaning the PRIOR absence of those triggers was losing that fraction of genuine signals permanently. This is not a hypothetical: it is the motivation for the entire "trigger-level search" sub-field (CMS scouting, ATLAS RECAST, LHCb full-stream analysis). The anomaly-detection-at-trigger-level program (AXOL1TL, CICADA at CMS, arXiv:2411.19506; FAD at CMS L1, arXiv:2508.11594) exists specifically because standard triggers have known blind spots for new physics with non-standard signatures.

The trigger false-discard rate for specific new-physics hypotheses is QUANTIFIED in papers like arXiv:2606.23993 (RL for trigger), arXiv:2311.09012 (model-agnostic combinatorial), and the long-lived particle review. This is not "might be failing" — it's "we know the standard trigger discards X% of these signals and here's the efficiency gain from fixing it."

**(c) Public data?**
PARTIALLY. CERN Open Data Portal provides research-quality CMS data (1.1k+ datasets, proton-proton collisions, trigger decisions preserved) and ATLAS open data (65 TB released). CMS explicitly preserves trigger bit decisions in open-data releases and provides software to recompute trigger efficiency offline. However: (i) the open data is the KEPT events — you cannot observe the discarded stream directly. (ii) Trigger efficiency for any given signal model requires Monte Carlo simulation of what would have been discarded, not direct observation of the discarded events. (iii) Running CMS software (CMSSW framework) requires serious setup — not casual Python scripting; it typically takes HEP graduate students weeks to get running.

**(d) Does the identifiability framework transfer?**
CLEANLY in theory, but with a twist. In the satellite domain, you can observe the discard RATE q (how many events the trigger rejected) even though you can't see the discarded events. Same is true here: CMS/ATLAS publish luminosity and trigger rates. However, the "C=1 (valuable)" label is model-dependent — a signal is only "valuable" relative to a specific BSM physics hypothesis. The estimand θ = P(discard | signal under model M) requires assuming a signal model to define C. This is NOT a weakness of the framework — it's an honest property of the domain — but it means the identifiability argument is model-conditional, not universal. The MNAR structure applies identically: triggers are trained on background rejection, their errors (missed signals) correlate with their decision variable, lower bound on missed signal rate = 0 from stored data alone.

The audit mechanism maps directly: cross-trigger disagreement (Level-1 fires but HLT rejects vs. vice versa) or anomaly detector disagreement is the analog of cross-detector consensus. The "pre-triage probe" analog is data scouting: a parallel stream that saves reduced information from ALL L1 events (CMS scouting system), which allows studying the full L1 rate — this is exactly the probe instrument we describe.

**(e) Novelty + who's already there?**
The identifiability framing (Manski partial-ID, MNAR lower bound on missed signal rate) is NOT in the LHC trigger literature. HEP physicists quantify trigger efficiency via Monte Carlo — they assume a signal model, simulate events, run them through trigger, count how many pass. That is the "oracle inside the bound" measurement from a different angle. Nobody has stated that the missed-signal rate is MNAR-unidentifiable from the stored dataset, or drawn the partial-identification bounds. The literature acknowledges the problem; nobody has formalized it.

However, the applied contribution from this domain is harder to make concrete than it sounds. The "demonstrated failure" is already being fixed (LLP triggers added, anomaly detectors deployed). The paper would be: "the LHC trigger's signal efficiency loss for non-standard signatures is MNAR-unidentifiable from stored data, but the scouting stream functions as our probe." This is a real contribution, but it requires a collaborator or at minimum HEP domain knowledge to write convincingly. A solo sophomore at DVC is unlikely to have the background to write this credibly without a co-author from a physics department.

**(f) Tractability + tier + fellowship narrative?**
Low tractability for solo student. CMSSW is not beginner-friendly; Monte Carlo simulation of BSM models requires PYTHIA/MadGraph expertise. The public data exists but is not easily usable at a "run it over a weekend" level. The fellowship narrative is strong — "AI systems in fundamental physics permanently lose evidence of new physics" is compelling — but the domain expertise barrier is real.

**Bottom line for this domain:** The irreversibility is perfect, the failure is demonstrated, the framework maps cleanly, the novelty gap (identifiability framing) is real. But the data barrier is prohibitive for a solo student and the physics domain expertise required to write this credibly is substantial. Strong domain if you could get a physics co-author; weak as a solo project.

---

### Domain 2 — LLM Pretraining Data Quality Filters

**What it is.** Large-scale web crawls (CommonCrawl, C4, RefinedWeb, FineWeb, RedPajama) are run through quality filters before being used for LLM pretraining. These filters — heuristic rules, perplexity thresholds, classifier-based "educational quality" scores — permanently discard data from the training run. The discarded data is not stored. Once filtered, it is gone from that training run; the model never sees it.

**(a) Irreversibility + unobservability of the error?**
PARTIALLY. The raw web crawl is available (CommonCrawl snapshots are public). So the "discarded" data at the filtering stage can technically be observed by going back to the raw crawl. This is NOT the same irreversibility as LHC triggers or onboard satellite triage — you can, in principle, recover the filtered-out text. The gatekeeper error is observable if you have the raw corpus.

However, there is a meaningful subset where irreversibility IS real: (i) data curators at major labs filter AND do not publish the raw pre-filter corpus (proprietary pipelines at OpenAI, Anthropic, DeepMind — the filtered data is gone and you don't have the raw); (ii) even for public corpora, a model trained on filtered data cannot "observe" what it would have learned from filtered-out content — the downstream model behavior diverges, and the divergence is unidentifiable from the model's outputs alone. This is a different flavor of the problem: the "gatekeeper" is the filter + training pipeline, and the "valuable discard" is content that would have improved the model but was filtered out.

The paper arXiv:2510.00866 ("The Data-Quality Illusion") shows that classifier-based quality filtering (CQF) improves performance on some benchmarks but ALSO filters out a non-trivial fraction of the high-quality reference corpus — i.e., the filter has false positives that remove genuinely good data. FineWeb's ablation found that C4 heuristic rules "incorrectly discard 18% of high-quality tokens." This is the false-discard finding.

**(b) Demonstrated real failure?**
YES for the filtering-errors-exist claim; WEAK on the specific irreversibility framing. Multiple papers demonstrate false positives:
- "Data-Quality Illusion" (2510.00866): CQF discards good data and the performance benefit is partly illusory.
- "A Bitter Lesson for Data Filtering" (arXiv:2605.19407): aggressive filtering hurts performance.
- "Towards Safer Pretraining" (arXiv:2505.02009): harmful-content filters have high false positive rates (keyword filters conflate educational discussion of self-harm with actual harmful content).
- FineWeb ablations: 18% of high-quality tokens removed by C4 rules.
- Multilingual filtering errors: quality classifiers trained on English-like Wikipedia proxies systematically over-discard non-English high-quality text (arXiv:2505.22232).

The failure is demonstrated. BUT it is not framed as MNAR unidentifiability anywhere. The literature frames it as "the filter is imperfect" and proposes better filters. Nobody has asked: "given that you trained your model on the filtered corpus, can you identify the rate at which good data was discarded?"

**(c) Public data?**
YES — this is the strongest pro for this domain. CommonCrawl is fully public. FineWeb, RefinedWeb, C4, RedPajama-V2 are all public with documented filter pipelines. A solo student can download a CommonCrawl snapshot, apply documented filter pipelines (they are open-source: gopher rules, C4 rules, FineWeb pipeline), observe what gets discarded, and compare to quality ground truth (e.g., Wikipedia-derived held-out quality annotations, or educational quality scores). This is the most runnable option.

Furthermore, the framework maps directly: discard rate q = documented (FineWeb reports how much is filtered at each stage), "clear-rate among kept" a = estimable from downstream benchmark performance or quality annotations on a sample of kept data. The "pre-triage probe" is exactly what the FineWeb ablation DOES: they bypass the filter on a labeled sample and observe the ground-truth quality. The parallel is clean.

**(d) Does the identifiability framework transfer?**
PARTIALLY — with caveats. The MNAR argument applies: the filter's decision D (discard=1) is correlated with the "true quality" label C, so the discarded data is not MCAR, and the quality distribution among kept data does not identify the quality distribution among discarded data. Proposition 1 applies directly.

But the estimand is harder to operationalize. In satellite triage, C = "truly clear scene" (independently verifiable from expert labels or physical indices). In data filtering, C = "valuable pretraining document" — what does that mean? Educational value? Factual accuracy? Low toxicity? The estimand is multidimensional and context-dependent. This muddies the formal identifiability argument: P(filter discards | document is valuable) requires defining "valuable," and any definition will be contested.

The strongest version: define C via an independent quality proxy that is not the filter being evaluated (e.g., "document would appear in curated open-access scientific text or high-quality Wikipedia-linked sources"). Then the framework applies cleanly. This requires careful operationalization but is doable.

**(e) Novelty + who's already there?**
The active research area of "data filtering evaluation" (the papers above) is ALREADY studying whether filters discard good data. The MNAR/identifiability framing is not present in this literature — everyone proposes better filters, nobody formalizes the non-identifiability from the trained model's outputs. That is the gap.

However, this gap is likely to be filled fast. The field is extremely active (multiple ICLR 2025, NeurIPS 2025 papers on this topic). A framing contribution ("data filtering is a selective labels problem") is the kind of insight that will occur to many people simultaneously. The time window for novelty on this specific framing is narrow.

Existing papers like "Selective labeling with false discovery rate control" (arXiv:2510.14581) are already applying selective labeling ideas to data filtering-adjacent problems. This domain is more crowded than it appears.

**(f) Tractability + tier + fellowship narrative?**
HIGH tractability: all data is public, Python pipelines exist, a Mac M4 Pro can run this. Medium tier: the formal framing is real but "data quality filtering has errors" is a known finding that may read as a methodological note rather than a standalone paper. Fellowship narrative: moderate — "AI training data filters irreversibly discard good content, and you can't measure it from the trained model" resonates with AI safety / evaluation concerns, especially for Anthropic Fellows who care about training data quality.

**Bottom line:** Tractable and data-accessible, genuine formal gap exists, but the domain's irreversibility is partial (raw crawl is recoverable), the estimand definition is contested, and the field is moving fast. Weaker irreversibility than satellite or LHC.

---

### Domain 3 — Social Media Content Moderation / Platform Deletion

**What it is.** AI classifiers on platforms (Facebook/Meta, Twitter/X, YouTube, TikTok) automatically remove posts, remove accounts, or shadow-ban content. Removed content is inaccessible to researchers and sometimes to users. The error — removing legitimate content (false positive) — is largely invisible: the removed content is gone, users rarely receive explanations, appeals mostly fail.

**(a) Irreversibility + unobservability of the error?**
MOSTLY TRUE, with important caveats. Permanent account deletion is irreversible. Shadow-banning (suppressing without removal) is partially reversible if discovered. Temporary post removal can sometimes be appealed. The most irreversible case is account deletion or permanent post removal where the content no longer exists anywhere. For RESEARCH, even content that technically exists but is de-platformed is unobservable — researchers cannot access it through APIs, and platforms do not publish false-positive rates.

The key MNAR structure: the platform's decision D=1 (remove) is correlated with content properties C (harmful vs. not harmful). Removed content is MNAR — the population of removed posts is NOT a random sample of all posts; it's precisely the posts the classifier thought were harmful. The false-positive rate (P(D=1 | C=0, i.e., not actually harmful)) is unidentifiable from the retained/visible dataset.

Research confirms this structure. DSA Transparency Database (EU Digital Services Act) compels platforms to report moderation statistics, but platforms report 45% auto-removal in official reports vs 95% in the database for overlapping periods — inconsistent self-reporting. EU researchers (arXiv:2504.06976, arXiv:2312.10269) confirm the database allows platforms to "remain opaque on the grounds behind content moderation decisions." FALSE POSITIVE RATE IS NOT REPORTED AND NOT OBSERVABLE from the outside.

**(b) Demonstrated real failure?**
YES — well-documented. Key numbers:
- OpenAI Moderation API: 47.8% FPR on hate speech evaluation datasets (arXiv CHI 2025 audit).
- Commercial moderation systems (Microsoft Azure, Perspective API) show consistent over-moderation of non-English content, LGBTQ+ content, and counter-speech.
- Instagram "ban wave" 2025: thousands of accounts deleted in July-August 2025, widely reported AI moderation errors, appeals generally ineffective.
- Meta transparency report: "erroneous content takedowns dropped by half between Q4 2024 and Q2 2025" — but that STARTING POINT implies substantial error rate.
- Twitch audit (arXiv:2506.07667): systematic bias in hate speech moderation with false positives concentrated in specific demographic groups.

The failure is real, documented, and current. The "so what" is visceral and accessible to a general audience.

**(c) Public data?**
PARTIALLY. This is the key constraint. Platforms do NOT publish their removed content. What is available:
- DSA Transparency Database: EU-mandated reporting of moderation actions (categories, automated vs. human, appeals), BUT NOT the content itself. Ground truth on whether a removal was a false positive is unavailable.
- Research APIs (Meta Content Library, Academic Twitter API): provide access to still-visible content; removed content is by definition not in these APIs.
- Third-party moderation evaluation datasets: HateXplain, Civil Comments, ToxiGen, SBIC (all public). These allow you to evaluate a given moderation classifier's FPR on known-labeled text, but they are NOT removed-content datasets from deployed systems.
- Prior academic work: studies like the Twitch audit use platform-specific ground truth that the researcher obtained through specific arrangements, not generally accessible data.

The critical gap: to apply our framework (estimate the false-discard rate from retained data; show the MNAR structure; deploy the audit harness), you need either (i) access to what was removed and a ground-truth label for it, or (ii) a proxy signal that works on retained data. Option (ii) is feasible: the audit harness (cross-classifier disagreement + cheap proxy) can be applied to public content moderation classifiers run on public text — you can evaluate whether removed/visible content behaves as the MNAR structure predicts, using the DSA database statistics and public classification APIs.

But the KEY LIMITATION: you cannot observe the removed content. You can estimate the MNAR structure's implications without seeing the removed content — the lower bound on FPR = 0 from retained data alone is demonstrable with Propositions 1-2, and you can use DSA removal rates as q (discard rate). But the audit harness's "recover individual false positives" component cannot work if the content is truly gone. You can only validate the framework on simulated/held-out data or on the DSA database (which has metadata but not content).

**(d) Does the identifiability framework transfer?**
YES for the theory; PARTIAL for the empirical demonstration. Props 1-2 apply directly: D = moderation removal, C = not-actually-harmful, θ = P(removal | not-harmful) = false-positive rate. The MNAR structure is clean: the classifier's removal decision correlates with content properties, so retained content ≠ random sample of all content. Lower bound on FPR = 0 from retained data. The q (removal rate) is publicly available from DSA reports. The a (clear-rate among kept content) is estimable from public content using external quality classifiers.

The audit harness: cross-classifier disagreement (multiple commercial moderation APIs flagging differently) is directly applicable to public datasets. OpenAI Moderation, Perspective API, Azure, and HuggingFace moderation models can all be run on the same text. Disagreement between them is the audit signal. This is exactly the cross-detector consensus method, applied to moderation classifiers.

**(e) Novelty + who's already there?**
Active research area, but the MNAR/identifiability framing IS NOT PRESENT. Existing work:
- Empirical audits of FPR on labeled datasets (CHI 2025, Twitch 2026, DSA database analysis)
- EU regulation mandating transparency
- Measurement of under-moderation (slow takedowns) and over-moderation (false positives)

Nobody applies Manski partial-identification or the selective-labels framing to content moderation. The closest is the Lakkaraju (KDD 2017) selective labels work, which is in hiring/criminal justice. A paper saying "content moderation is a selective labels problem and the false positive rate is MNAR-unidentifiable from visible platform content" is novel framing on a high-stakes real problem.

Cross-moderation-classifier disagreement as an audit signal for false positives: the CHI 2025 paper compares 5 APIs but does not frame it as a proxy audit for unobservable removal errors — they use it to measure accuracy on labeled datasets, not to recover false positives from deployed removal decisions. Our framing is different and novel.

**(f) Tractability + tier + fellowship narrative?**
HIGH tractability: multiple public text datasets, multiple free/cheap moderation APIs (OpenAI, Perspective API, Azure, HuggingFace models), Python-accessible. A solo student can run this entirely on a MacBook M4 Pro. The framework can be validated on:
1. Labeled moderation datasets (HateXplain, Civil Comments) as "oracle" ground truth
2. DSA database removal rates as q
3. Cross-API disagreement as the audit signal

This is a weekend + 2-week implementation. No specialized hardware needed.

Fellowship narrative: EXCELLENT. "AI content moderation systems permanently silence legitimate speech at unknown rates, and the standard metrics cannot detect it" is directly aligned with AI safety/evaluation concerns, has clear societal stakes, and is legible to any fellowship reader. Anthropic Fellows in particular (Economics & Policy track): platform governance, DSA compliance, free speech vs. safety tradeoffs — all directly relevant.

Tier: potentially higher than satellite for the following reasons. The stakes are universally understood (everyone uses social platforms). The policy relevance (DSA mandates transparency, EU is actively pressing for audit methods) gives the paper a clear real-world hook. The MNAR framing is formally clean and the identifiability result is directly actionable for regulators: "platforms CANNOT self-report their false-positive rates meaningfully because the retained data doesn't identify it."

Realistic venue: FAccT 2027, EAAMO 2027, or NeurIPS D&B 2026 (evaluation framing). FAccT is the natural home — this is exactly their scope. Odds conditional on clean empirical validation: 20-30% at FAccT.

**Honest limitation:** The "demonstrated failure NOW" requires running the framework on actual platform data where removals are happening, and you cannot access removed content. The demonstration will be partly theoretical (show the MNAR structure implies non-identification) and partly empirical (simulate the setting on labeled datasets + show the audit harness's AUC). This is weaker than the satellite case where we had actual detector discards and actual ground truth on discarded content. The most rigorous empirical test requires either (a) collaborating with a researcher who has platform data access or (b) limiting the empirical demonstration to API outputs on public labeled datasets (fully sufficient for the theory claim, but less visceral than "here is the content that was wrongly removed and here is our audit method finding it").

---

## Rejected Domains (brief assessments)

**Medical screening triage (mammography, radiology AI).** Irreversibility is real (a missed cancer, a study not re-examined). But: (i) existing literature is large and sophisticated — FDA-authorized AI device studies, selective AI prediction papers (arXiv:2508.07617), massive meta-analyses; this is the most crowded domain for ML+healthcare. (ii) Public data with ground-truth diagnoses AND AI triage decisions AND outcomes is sparse and IRB-gated. (iii) The MNAR argument is similar to the selective-labels clinical literature (already has its own track). A solo student is unlikely to get the data or write this credibly without clinical collaborators. REJECT.

**ATS / hiring auto-reject.** Irreversibility is real (rejected candidates may not reapply). The Mobley v. Workday class action (certified 2025) demonstrates real harm. BUT: (i) no public dataset of ATS decisions + ground truth. ATS vendors don't release data. The Harvard "Hidden Workers" project surveyed employers but did not produce ground-truth rejection rates. (ii) The selective-labels literature already covers this — Lakkaraju 2017 is explicitly about hiring and bail. The MNAR framing is already implicit in the discrimination/audit literature. Not novel enough formally. REJECT.

**Spam filtering.** Not truly irreversible — email providers have quarantine folders that can be checked, admin whitelisting, false positive recovery workflows. The 2025 email deliverability crisis (inbox rate drop from 49% to 27% year-over-year) is a real problem but a business/operations problem, not a scientific one. No public labeled spam/non-spam dataset with documented filter decisions from deployed systems. The classic SpamAssassin/TREC datasets are academic baselines, not deployed-system audits. Low novelty (spam filtering is a 25-year-old field). REJECT.

**AV/robotics perception gating.** Irreversibility is domain-context-dependent — most AV systems log raw sensor data for offline analysis. Not truly irreversible in the research sense. Real-time missed detections cause accidents, but the statistical false-negative rate is measurable post-hoc from logs. REJECT.

**IoT/edge sensor triage.** Real problem, but even more fragmented and domain-specific than satellite. No standardized public datasets analogous to CloudSEN12. REJECT.

---

## Rankings

### Rank 1: Social Media Content Moderation

| Criterion | Rating | Notes |
|---|---|---|
| Irreversibility | STRONG (permanent deletion) | Shadow-banning is partial; account deletion is complete |
| Demonstrated failure | STRONG | 47.8% FPR audited; Instagram ban wave 2025; DSA reports |
| Public data | STRONG | HateXplain, Civil Comments, DSA database, 5 commercial APIs |
| Framework transfer | CLEAN (theory) + PARTIAL (empirical) | Deployed audit needs proxy approach since removed content unobservable |
| Novelty | STRONG | MNAR/identifiability framing absent from moderation literature |
| Tractability | HIGH | Mac M4 Pro, Python, free APIs |
| Tier / venue | FAccT 2027, EAAMO, NeurIPS D&B | 20-30% at FAccT conditional on clean empirical demo |
| Fellowship narrative | EXCELLENT | Policy stakes, EU DSA relevance, AI safety/evaluation framing |

**Critical weakness:** You cannot observe the removed content to validate the audit harness empirically on real deployed removals. The demonstration must use labeled public datasets as "ground truth + simulated filter." This is methodologically valid — it's what a "proof of concept" looks like — but a reviewer will correctly note that you haven't applied the audit to content removed by actual deployed systems.

**Mitigant:** The DSA Transparency Database gives you q (removal rate) and the cross-API disagreement audit works on the still-visible content stream. You can show: (1) theoretically, FPR is MNAR-unidentifiable from visible content; (2) empirically on labeled datasets, cross-API disagreement identifies false positives at AUC ~0.75-0.85 (calibrated from CHI 2025 numbers); (3) the DSA database q values bound the worst-case FPR. This is a complete, honest paper.

---

### Rank 2: LHC Trigger Systems

| Criterion | Rating | Notes |
|---|---|---|
| Irreversibility | PERFECT | Events not triggered are gone at 40 MHz refresh rate |
| Demonstrated failure | STRONG | LLP efficiency gains 2.6-17× document prior losses |
| Public data | PARTIAL | CERN Open Data Portal has kept events; scouting stream partially available |
| Framework transfer | CLEAN | MNAR structure maps directly; scouting = probe instrument |
| Novelty | STRONG | Partial-ID framing completely absent from HEP trigger literature |
| Tractability | LOW | CMSSW framework; Monte Carlo simulation; HEP domain knowledge required |
| Tier / venue | JHEP, ML for Physics, or Physics ML workshop | Highest-tier possible but requires domain expertise |
| Fellowship narrative | STRONG | "AI loses evidence of new physics laws permanently" is compelling |

**Critical weakness:** Domain expertise barrier is prohibitive for a solo DVC sophomore. CMSSW requires weeks to set up; writing a credible HEP paper requires knowing BSM physics signal models, detector simulation, and trigger architecture. Without a physics co-author, this is not feasible before September.

**Mitigant:** If you could get even a single email exchange with someone in the LHCb or CMS trigger group, the formal framework contribution (MNAR identifiability framing of trigger efficiency loss) would be novel and significant. The paper would be: "we show the trigger efficiency loss for non-standard signals is MNAR-unidentifiable from the stored dataset, and the scouting stream is the probe instrument." This is a 6-page letter-style paper, not a full paper. But the expertise bar remains high.

---

### Rank 3: LLM Pretraining Data Quality Filters

| Criterion | Rating | Notes |
|---|---|---|
| Irreversibility | PARTIAL | Raw CommonCrawl recoverable; proprietary lab pipelines irreversible but not accessible |
| Demonstrated failure | STRONG | Data-quality illusion, 18% high-quality tokens removed by C4 rules |
| Public data | EXCELLENT | FineWeb, C4, RedPajama all public; filter pipelines open-source |
| Framework transfer | PARTIAL | MNAR maps; estimand definition (what is "quality"?) is contested |
| Novelty | MODERATE | Field is active; selective-labeling framing likely to be discovered soon |
| Tractability | HIGH | Python, Mac M4, all public |
| Tier / venue | ICLR/NeurIPS D&B | 15-20% at D&B |
| Fellowship narrative | MODERATE | AI training quality is relevant but less visceral than censorship or physics |

**Critical weakness:** The irreversibility is the weakest of the three ranked candidates. Raw CommonCrawl data is public; you CAN observe the discarded documents for public pipelines. The MNAR framing is real for proprietary pipelines (you can't access what GPT-4 was trained on), but you can't run experiments on that data either. The tension — "publicly accessible but not truly irreversible" — weakens the core thesis. The most honest version: "quality filters in LLM pretraining create a selective-labels problem: the trained model's behavior cannot identify its own false-discard rate." This is true and formally clean but the "irreversibility" feels more metaphorical than physical.

---

## Recommendation: Stay with Satellite, But Consider a Moderation Appendix

**Is any alternative domain clearly better than staying with satellite?** 

Honest answer: **No, but content moderation is competitive and could be right depending on framing priorities.**

Here is the precise comparison:

**Satellite EO (current domain) strengths vs. alternatives:**
- You have working code, data, results, and a complete audit harness (T1-T5 all passing).
- The theoretical backbone (identifiability.md, Props 1-2) is written and verified.
- The empirical demonstration IS real deployed systems with real ground truth (KappaMask 63% snow false-discard, CloudSEN12 data, NDSI audit).
- The irreversibility is genuine (onboard data is physically gone).
- The prior art review is done (priorart_onboard.md: genuine novelty confirmed).
- The weakening from T1b (CloudScout is robust) is manageable via the framing shift to Option A (failure frontier) or Option B (characterization paper).

**Where content moderation beats satellite:**
- Fellowship narrative: more accessible, more politically resonant (everyone uses social media).
- Venue: FAccT and related venues have higher prestige for this specific framing than EO venues.
- Data accessibility: DSA database + commercial APIs + labeled datasets are all immediately available.

**Where satellite beats content moderation:**
- Empirical rigor: you have ground-truth labels on discarded content (CloudSEN12 includes labels for scenes even if a gatekeeper would not have downlinked them). In content moderation, you cannot label the removed content.
- Completion: satellite is 70% of the way to a paper. Content moderation would require starting the experiments from scratch.
- Irreversibility: satellite is physically irreversible. Content moderation is legally/practically irreversible but technically recoverable in some cases.
- Domain specificity: satellite is more technically narrow, which means a cleaner formal story.

**The honest recommendation:**

1. **Do not pivot away from satellite.** The framework, code, and results are too complete to abandon. T1b weakened the flagship claim but did not kill the paper — Options A and B are both viable paths to a Sept arXiv artifact. The identifiability + audit contribution is novel and honest, and the satellite domain is the cleanest instantiation.

2. **If you want to strengthen the fellowship artifact: add content moderation as a second applied domain.** The cross-classifier disagreement audit (5 commercial moderation APIs on HateXplain + Civil Comments, cross-API AUC as the audit signal) maps exactly to the satellite cross-detector consensus. It would take 2 weeks of implementation, costs nothing (all free APIs), and would turn the paper from a single-domain empirical study into a cross-domain demonstration of the framework. That dramatically strengthens the "generality" claim and the fellowship narrative.

   Section structure: Introduction (universal framework) → Theory (Props 1-2, 3 identification regimes) → Application 1: Satellite EO (full empirical battery, T1-T5) → Application 2: Content Moderation (theoretical mapping + cross-API disagreement audit on public datasets, DSA bounds on q) → Discussion/Implications.

3. **LHC is compelling but out of scope for a solo student without a co-author.** File it as a "future domains" paragraph in the Discussion. It is the ideal domain — the formal elegance is perfect and the stakes are profound — but it requires HEP expertise. If you ever get into a physics research program, that is the paper.

---

## Summary Table

| Domain | Irreversibility | Demonstrated Failure | Public Data | Framework Fit | Solo-Feasible | Fellowship Narrative | Verdict |
|---|---|---|---|---|---|---|---|
| Satellite EO (current) | STRONG | YES (KappaMask 63%) | STRONG (CloudSEN12) | CLEAN | YES (already done) | MODERATE | KEEP — do not pivot |
| Content Moderation | STRONG-ish | YES (FPR 47.8%, ban waves) | PARTIAL (removed content inaccessible) | CLEAN (theory), PARTIAL (empirical) | YES | EXCELLENT | Add as 2nd domain |
| LHC Triggers | PERFECT | YES (LLP efficiency gaps) | PARTIAL (CERN Open Data) | PERFECT | NO (domain barrier) | STRONG | Future work |
| LLM Pretraining Filters | WEAK (recoverable) | YES (Data-Quality Illusion) | EXCELLENT | PARTIAL | YES | MODERATE | Not worth pivot |
| Medical Triage | STRONG | YES | POOR (IRB-gated) | CLEAN | NO | STRONG | Reject |
| ATS/Hiring | MODERATE | YES (Workday case) | POOR | CLEAN | NO | STRONG | Reject |
| Spam Filtering | WEAK (quarantine) | YES | POOR | PARTIAL | YES | LOW | Reject |

---

## Actionable Decision Tree

**If arXiv-by-September is the hard constraint:**
→ Stay satellite (Option A failure frontier experiments, 2-3 GPU weekends) + add content moderation validation as Section 5 (2 weeks, no GPU needed).
→ This is a stronger artifact than either domain alone and is achievable in 8 weeks.

**If you want the highest-tier outcome and are willing to expand scope:**
→ Full content moderation section with DSA database analysis, cross-API disagreement audit (5 APIs × 4 datasets), and formal identifiability demonstration.
→ Target FAccT 2027 with the full cross-domain paper.

**If you want the cleanest single-domain story:**
→ Stay satellite, run Option A frontier, submit to NeurIPS D&B 2026 / ICLR D&B 2027.
→ Content moderation stays in the Discussion as future work / generalization.

**Under no circumstances:** pivot entirely to LHC triggers or medical triage without a domain-expert collaborator. The domain barrier will produce an embarrassingly shallow paper that does more harm than good as a fellowship artifact.
