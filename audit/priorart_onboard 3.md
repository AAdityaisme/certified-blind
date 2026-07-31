# Prior-Art Audit: Onboard Satellite Cloud Triage & Unidentifiable False-Discard Rate
**Date:** 2026-06-22  
**Purpose:** Exhaustive search across 8 prior-art clusters to determine novelty of 4 paper contributions. Adversarial posture — goal is to find scoops, not confirm novelty.

---

## OUR 4 CONTRIBUTIONS (under test)

1. **MNAR Framing** — Onboard triage (Phi-Sat/CloudScout) makes its own false-discard rate *unidentifiable* from returned data; selection-bias / missing-not-at-random framing of irreversible onboard data triage.
2. **Snow/Bright-Surface Quantification** — Cloud masks over-discard bright/snow clear scenes (snow/ice/desert misclassified as cloud), with confidence intervals on the over-discard rate.
3. **Ground-Side Audit** — Estimating irreversibly-discarded valuable scenes without ground truth, via cross-detector consensus + NDSI + pre-triage probe.
4. **Unauditable Gatekeeper Frame** — Onboard irreversible AI triage as a gatekeeper whose errors are unauditable; LLM routing as a recoverable-domain parallel.

---

## CLUSTER-BY-CLUSTER FINDINGS

---

### CLUSTER A — Information/Data Loss Quantification from Onboard Cloud Filtering

**Verdict: NONE for full quantification; PARTIAL for naming the problem**

The canonical system papers acknowledge false discards but treat FP rate as a performance spec, not a loss model.

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Giuffrida et al., "CloudScout: A DNN for On-Board Cloud Detection" | DOI: 10.3390/rs12142205 | PARTIAL | Reports 1% FPR at image level; explicitly calls FPs "net loss of good data" but never quantifies downstream scientific loss. |
| Giuffrida et al., "The Phi-Sat-1 Mission" | DOI: 10.1109/TGRS.2021.3125567 | PARTIAL | Canonical ops paper; same gap — names the problem without modeling it. |
| Du et al., "Earth+: On-Board Satellite Imagery Compression" | arXiv:2403.11434 | PARTIAL | States "it is harmful if the cloud detector wrongfully detects non-cloudy area as cloudy" — clearest gap-naming, but provides no metric for false discard rate or value of discarded frames. |

**Gap:** No paper quantifies the scientific/operational value of what onboard filtering discards. No paper models information loss as a function of threshold, scene type, or cloud fraction.

---

### CLUSTER B — Auditing / Estimating What Onboard Satellite AI Discarded

**Verdict: NONE — this exact framing does not exist**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Cratere et al., "Cloud Detection on PRISMA SG Using a Secondary RGB Camera" | DOI: 10.1109/TGRS (2025) | PARTIAL | Proposes cross-sensor pre-screening; reports FPR of 0.9%. Prospective design, not retrospective audit of deployed discards. |
| Aybar et al., "DTACSNet: Onboard Cloud Detection and Atmospheric Correction" | DOI: 10.1109/JSTARS.2024.x | PARTIAL | Benchmarks onboard CNN against labeled test sets at design time. No post-hoc recovery or audit framing. |
| Ekelund et al., "AI in Space for Scientific Missions" | arXiv:2406.14297 | ADJACENT | Onboard selective downlink for NASA MMS; quantifies design-time accuracy but no post-deployment audit. |

**Gap:** No paper attempts to estimate or bound what a *deployed* onboard AI system wrongly discarded, using only downlinked data. The "discarded set is unobserved by construction" problem is completely unaddressed.

---

### CLUSTER C — MNAR / Selection Bias Applied to Satellite Sensor Data

**Verdict: NONE for onboard-algorithmic framing; one ADJACENT paper in EO**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Wąsala et al., "Mitigating Representation Bias from Missing Pixels in Methane Plume Detection" | arXiv:2510.19478 (ECML/PKDD 2025) | ADJACENT | **Only paper applying MNAR language to EO data.** Missingness is *atmospheric* (cloud blocks pixels), not *algorithmic* (onboard AI discards frames). No identifiability argument — proposes ML fixes. ~50% structural overlap. |
| Ballabio et al., "Spatiotemporal Distribution of Labeled Data Can Bias Validation" | DOI: 10.1016/j.isprsjprs.2022.03.008 | ADJACENT | Selection bias in EO label sampling; different mechanism, no MNAR language, no irreversible discard. |
| Xie et al., "Identifiable Deep Latent Variable Models for MNAR Data" | arXiv:2603.24771 | ADJACENT | Rigorous MNAR identifiability theory; zero EO/satellite application. Useful as a theoretical citation. |

**Gap:** No paper applies MNAR + identifiability language to *onboard algorithmic filtering* of satellite data. Wąsala et al. is the closest prior art and must be cited with a clear differentiator: their missingness is passive/atmospheric; ours is active/algorithmic; they propose ML remedies; we argue fundamental non-identifiability.

---

### CLUSTER D — Snow/Ice False Positives in Cloud Masks as Data-Loss Problem

**Verdict: PARTIAL — hard numbers exist but not framed as triage/data-loss with CIs**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Stillinger et al., "Cloud Masking for Landsat 8 and MODIS Terra Over Snow-Covered Terrain" | DOI: 10.1029/2019WR024932 | PARTIAL | **Closest paper.** CFMask commission error over snow: 30%. MODIS commission error: 83%. Uses NDSI and cross-sensor Landsat/MODIS comparison. Frames as loss of valid mountain-hydrology observations. Does NOT compute confidence intervals on over-discard fraction or frame as onboard triage. |
| Li et al., "Recent Developments in Cloud Removal Approaches of MODIS Snow Cover Product" | DOI: 10.5194/hess-23-2401-2019 | PARTIAL | Frames cloud-induced observation loss as a data continuity problem. Different confusion direction (cloud obscures snow, not snow misclassified as cloud). |
| MDPI RS 2022, "Cloud–Snow Confusion with MODIS in Boreal Forest" | DOI: 10.3390/rs14061372 | ADJACENT | "Excessive cloud masks limit application" — closest data-utility framing, but no CIs, no triage framing. |

**Specific gap:** No paper combines (a) snow/ice commission error over-discard quantification + (b) confidence intervals + (c) onboard processing framing. Stillinger et al. gives the hard numbers; nobody combines them with CIs in an onboard triage context.

---

### CLUSTER E — Value of Information / Cost-of-Discard in Scene Prioritization

**Verdict: NONE — "name the problem" papers exist, but no cost-of-discard framework**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Mateo-Garcia et al., "Towards Global Flood Mapping Onboard Low Cost Satellites" | arXiv:1910.03019, DOI: 10.1038/s41598-021-86650-z | PARTIAL | **Closest.** Explicitly states false negatives (missed floods) are more problematic than false positives. Targets >95% recall. Informal asymmetric cost framing, not a formal VOI model. |
| Ruzicka et al., "RaVAEn: Unsupervised Change Detection of Extreme Events Onboard Satellites" | arXiv:2111.02995 | PARTIAL | Uses exact phrase "value to prioritize download or discard it." Detects change to flag scenes. No false-negative penalty model, no cost function. |
| Giuffrida et al., CloudScout (see Cluster A) | DOI: 10.3390/rs12142205 | PARTIAL | Names false discards as "loss of useful information." No asymmetric disaster-event cost model. |

**Gap:** No paper formalizes: "given that a router discarded scene X, what is the expected loss if X contained a wildfire?" No decision-theoretic cost-of-discard framework exists for EO triage.

---

### CLUSTER F — Post-Hoc Audit / Recovery for Onboard-Discarded EO Data

**Verdict: NONE — cross-sensor comparison exists but not applied to onboard discards**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Skakun et al., "Cloud Mask Intercomparison eXercise (CMIX)" | DOI: 10.1016/j.rse.2022.112990 | ADJACENT | Cross-sensor intercomparison of 16+ cloud algorithms on Landsat 8 + Sentinel-2. Identifies systematic disagreement patterns. Requires manually-labeled ground truth; audits algorithms on same imagery, not onboard black-box discards. |
| Stillinger et al. (see Cluster D) | DOI: 10.1029/2019WR024932 | PARTIAL | Cross-sensor Landsat/MODIS comparison + NDSI to locate misclassifications. Requires manual reference pixels. Data is always ground-side-available. |
| Noel et al., "Disagreement among global cloud distributions from CALIOP and passive sensors" | arXiv:1803.06143 | ADJACENT | CALIOP vs. passive sensor disagreement as proxy for missed thin clouds. Climatological study; no recovery method; requires active CALIOP data. |

**Gap:** No paper proposes a ground-side method to estimate false discard rate of a deployed onboard system using only downlinked data + cross-sensor comparison or spectral proxies, without labeled ground truth. This niche is unoccupied.

---

### CLUSTER G — Unobservable-Error Framing for Irreversible ML Gatekeeping

**Verdict: PARTIAL — formal identifiability results exist in ML/econometrics, none in EO**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Choe, Gangrade, Ramdas, "Counterfactually Comparing Abstaining Classifiers" | arXiv:2305.10564 | PARTIAL | **Closest formal statement.** Proves that "if abstentions are deterministic, the score is unidentifiable because the classifier can perform arbitrarily poorly on its abstentions." Scoped to deliberate confidence-based deferrals, not irreversible EO data filtering. Not in the satellite domain. |
| Lakkaraju et al., "The Selective Labels Problem" | DOI: 10.1145/3097983.3098066 (KDD 2017) | PARTIAL | **Canonical paper** for this class of problem in ML deployment. Argues false-reject outcomes are fundamentally unobservable (bail/lending/hiring context). No formal theorem, but strongest cited articulation of the structural problem. |
| Rambachan, Coston, Kennedy, "Robust Design Under Unobserved Confounding" | arXiv:2212.09844 | PARTIAL | Cleanest formal non-identification result: "P(Yi*=1 \| Di=0, Xi) is not point identified from the data alone." Proves partial identification sets. Econometric framing; no EO application. |

**Gap:** No paper applies this identifiability argument to satellite EO pipelines where an upstream sensor/filter irreversibly discards scenes before any downstream label is generated. The formal machinery (Choe et al., Rambachan et al.) and the applied argument (Lakkaraju et al.) both exist — but only in ML/economics domains, not in EO.

---

### CLUSTER H — Cross-Model Disagreement / Spectral Index to Flag Deployed Detector Bad Discards

**Verdict: NONE as combined method; components exist separately**

| Paper | ID | Overlap | Notes |
|---|---|---|---|
| Stillinger et al. (see Clusters D & F) | DOI: 10.1029/2019WR024932 | PARTIAL | Uses NDSI + cross-sensor Landsat/MODIS comparison to locate systematic snow commission errors. Requires 26 manually-delineated reference scenes. Not fully label-free, not framed as deployed-system audit. |
| Gorbett & Jana, "Cross-Model Disagreement as a Label-Free Correctness Signal" | arXiv:2603.25450 | PARTIAL | Cross-model perplexity/entropy as label-free signal for detecting deployed model errors. AUROC 0.75 vs. 0.59 for within-model entropy. Applied to LLMs on NLP benchmarks (MMLU). Zero EO application. |
| Bogdoll et al., "Label-Free Model Failure Detection for Lidar-based Point Cloud Segmentation" | arXiv:2407.14306 | ADJACENT | Supervised + self-supervised stream disagreement to flag failures in deployed lidar segmentation. Label-free at deployment time. Autonomous driving, not EO. |

**Supporting evidence:**
- Skakun et al. CMIX (DOI: 10.1016/j.rse.2022.112990) — cross-algorithm comparison reveals scene-type failure modes; requires labels.
- Nguyen et al. D3M (arXiv:2506.05047) — predictive disagreement for label-free deployment monitoring, medical domain.

**Gap:** No paper combines (a) unsupervised/label-free operation + (b) applied to EO cloud masking + (c) using cross-model disagreement OR spectral indices + (d) to surface systematic discard errors of a deployed system. Stillinger et al. has the EO+spectral piece but needs labels. Gorbett/Bogdoll have the label-free disagreement mechanism but in different domains.

---

## NOVELTY VERDICT

### Contribution 1 — MNAR / Unidentifiability Framing of Onboard Triage
**Novelty: HIGH. Genuinely novel in the EO/satellite domain.**

The formal ingredients exist in adjacent fields: Choe et al. (arXiv:2305.10564) proves unidentifiability for abstaining classifiers; Rambachan et al. (arXiv:2212.09844) formalizes partial identification in human-in-the-loop decisions; Lakkaraju et al. (KDD 2017) is the canonical "selective labels" citation. In EO, Wąsala et al. (arXiv:2510.19478) applies MNAR language — but to atmospheric missingness, not algorithmic discard.

**No paper applies the MNAR/identifiability framing to irreversible onboard satellite data triage.** This is your most conceptually novel contribution.

**Differentiator to state clearly in the paper:** Wąsala et al.'s missingness is passive/atmospheric; ours is active/algorithmic. They propose ML remedies; we argue fundamental non-identifiability and the need for a pre-triage probe.

---

### Contribution 2 — Snow/Bright-Surface Over-Discard Quantification with CIs
**Novelty: MODERATE. The accuracy numbers exist; the CIs + triage framing are novel.**

Stillinger et al. (DOI: 10.1029/2019WR024932) has the hardest numbers (MODIS commission error 83%, CFMask 30% over snow terrain) and uses NDSI + cross-sensor comparison. This is the single biggest prior-art threat to Contribution 2.

**What Stillinger et al. does NOT do:** Frame it as a triage/data-loss problem. Compute confidence intervals on the over-discard rate as a fraction of valid data lost. Connect to onboard processing. The framing shift — from "accuracy metric" to "quantified irreversible data loss" — is where the novelty lives.

**Risk:** A referee could argue this is a framing contribution, not a measurement contribution, since the underlying commission error numbers are close to Stillinger et al.'s. Mitigate by: (a) showing CIs explicitly, (b) computing the fraction of high-value scenes (polar, disaster-prone) that fall in snow/ice zones, (c) connecting to the onboard threshold choice.

---

### Contribution 3 — Ground-Side Audit via Cross-Detector + NDSI + Pre-Triage Probe
**Novelty: HIGH. No paper proposes this combination applied to onboard discards.**

The component techniques exist separately: cross-sensor comparison (Stillinger, CMIX), NDSI-based cloud/snow disambiguation (Stillinger, multiple), label-free disagreement as error signal (Gorbett, Bogdoll). But:
- No paper applies cross-detector consensus to audit an onboard triage system's discards.
- No paper uses NDSI as a label-free proxy to estimate false discard rate without ground truth.
- No paper proposes a pre-triage probe to empirically identify discard rates.

The *combination* applied to the *onboard discard recovery problem* is novel.

---

### Contribution 4 — Unauditable Gatekeeper Frame + LLM Routing Parallel
**Novelty: MODERATE-HIGH. The "gatekeeper" language exists loosely; the formal unauditability + cross-domain parallel is new.**

The selective-labels literature (Lakkaraju et al. KDD 2017) and abstaining-classifier literature (Choe et al.) have the unauditability structure but don't use "gatekeeper" language explicitly in the EO context. RaVAEn (arXiv:2111.02995) uses "discard" language but no unauditability framing.

The LLM routing parallel (recoverable vs. irreversible domain) is novel — no paper has drawn this cross-domain analogy.

---

## SINGLE BIGGEST PRIOR-ART THREAT

**Stillinger et al. 2019 (DOI: 10.1029/2019WR024932)**

This paper has: NDSI, cross-sensor comparison, hard commission error numbers over snow terrain, and the implicit data-loss framing. A hostile referee could call this 60-70% of Contribution 2 and 40% of Contribution 3. You must cite it prominently and differentiate on:
1. Stillinger et al. requires manually-labeled reference scenes; your method is label-free.
2. Stillinger et al. operates on ground-side data where nothing is irreversibly discarded; you operate under onboard discard conditions.
3. Stillinger et al. reports accuracy metrics; you compute over-discard CIs as a data-loss framing.
4. Stillinger et al. does not address the identifiability problem (Contribution 1).

---

## REFERENCE LIST (key papers to cite)

| Paper | ID | Role in your paper |
|---|---|---|
| Giuffrida et al. 2020, CloudScout | DOI:10.3390/rs12142205 | Primary system being analyzed; establishes 1% FPR |
| Giuffrida et al. 2021, Phi-Sat-1 mission | DOI:10.1109/TGRS.2021.3125567 | Operational context |
| Du et al. 2024, Earth+ | arXiv:2403.11434 | Best gap-naming citation; explicitly calls asymmetric harm |
| Stillinger et al. 2019 | DOI:10.1029/2019WR024932 | **Biggest threat** — cite and differentiate |
| Skakun et al. 2022, CMIX | DOI:10.1016/j.rse.2022.112990 | Cross-algorithm comparison precedent |
| Wąsala et al. 2025 | arXiv:2510.19478 | Only MNAR-in-EO paper; differentiate atmospheric vs. algorithmic |
| Lakkaraju et al. 2017, Selective Labels | DOI:10.1145/3097983.3098066 | Canonical "unobservable false rejects" citation |
| Choe et al. 2023, Counterfactually Comparing Abstaining Classifiers | arXiv:2305.10564 | Formal unidentifiability statement for abstaining classifiers |
| Rambachan et al. 2022 | arXiv:2212.09844 | Cleanest formal non-identification proposition |
| Mateo-Garcia et al. 2021, WorldFloods/Flood Onboard | arXiv:1910.03019 | Asymmetric cost framing (informal) |
| Ruzicka et al. 2022, RaVAEn | arXiv:2111.02995 | "Value to prioritize download or discard" language |
| Gorbett & Jana 2026 | arXiv:2603.25450 | Label-free cross-model disagreement mechanism (different domain) |
| Bogdoll et al. 2024 | arXiv:2407.14306 | Label-free failure detection via disagreement (lidar, different domain) |
| Xie et al. 2026, MNAR identifiability | arXiv:2603.24771 | MNAR theoretical foundation |
| Noel et al. 2018 | arXiv:1803.06143 | Cross-sensor disagreement as proxy for missed cloud detections |
