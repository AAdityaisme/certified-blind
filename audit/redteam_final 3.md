# Red-Team Audit — Final Report
*Reviewer 2 adversarial perspective. All numbers independently verified via code. Date: 2026-06-24.*

---

## Publishability Verdict (up front)

**No single FATAL flaw. The paper is NOT desk-reject-level, but has one near-fatal claim (S8) and several Critical issues that would earn a "reject" at NeurIPS D&B or ICLR in current form.** With targeted fixes the core three pillars survive. The verdict depends entirely on whether the fire-deletion section (S8) is the primary novelty claim or an honest secondary finding with caveats.

---

## Priority Matrix

| Severity | Issue | Kills what |
|---|---|---|
| **NEAR-FATAL** | S8 fire-deletion is confounded by a single scene (scene3 = 68% discard on ALL patches) and no cloud ground truth | The generalizable harm claim |
| **Critical** | "Unidentifiable from retained data" overstates the epistemic gap — probe trivially identifies it but requires system modification | Core conceptual framing |
| **Critical** | Headline FD numbers (19%, 21%, 49%) come from the SMALLER test set (n=43 bright patches); larger train set shows lower values (15.6%, 19.1%, 43.5%) — reported split is never labeled | Numerical credibility |
| **Critical** | Sen2Cor NDSI AUC = 0.511 (chance) — the paper's NDSI-as-mechanism story applies only to KappaMask and Fmask, NOT Sen2Cor, whose consensus AUC is 0.922 | Mechanistic explanation claim |
| **High** | Probe CI includes zero for all detectors with n=100; 100 samples ≠ "a small probe recovers the rate" | Deployable remedy claim |
| **High** | S5 test set n_bad=12–44; all CI lower bounds > 0.70 confirmed, but numbers differ from S9 train set (0.84 vs 0.88–0.92) — abstract mixes both without labeling splits | Generalizability |
| **High** | KappaMask least-correlated 3-detector panel includes cnn_rgbi + cnn_rgbi_swir (0.948 correlated) — the independence test uses partially redundant detectors | Independence claim |
| **Medium** | Consensus estimator overestimates FD rate 2–4x for fmask and kappamask — biased but disclosed honestly in S6 | Rate estimation utility |
| **Medium** | S9 evaluates on TRAIN split with OOF predictions; methodology numbers are not labeled by split in the abstract | Reproducibility |
| **Med/Low** | Routing contribution relies on experiment_log's own "superseded" label on C2-SIV/C3 — but abstract/sharpened_angle still quotes 87.5% SIV and 6.7× cost as if real | Routing track credibility |
| **Low** | Identifiability framing is technically correct (MNAR, unidentifiable from D=0 samples alone) but a statistician reviewer will immediately note a probe makes it identifiable | Framing precision |

---

## 1. Detector Encoding — VERIFIED CORRECT

**Status: Bulletproof. Not an issue.**

All detector encodings were verified against the actual byte distributions and cross-validated against expected cloud-detection accuracy:

- `cd_fcnn_*` and `s2cloudless`: values 0–100, cloud = prob≥50. CONFIRMED. `s2cloudless` at this threshold achieves AUC=0.926 on the test set (consistent with published ~0.93), while the alternative threshold of ≥128 gives AUC=0.500 (pure chance). Scale is unambiguously 0–100.
- `sen2cor` SCL: classes {8,9,10} = cloud_medium, cloud_high, cirrus. CONFIRMED. Class 4 = vegetation (23.75%), class 5 = soil (21.22%), cloud classes total 31.8% — all reasonable for this dataset.
- `fmask`: class {4} = cloud only. Class 3 = snow/ice (4.09%), correctly excluded. CONFIRMED.
- `kappamask`: classes {3,4} = semi-transparent cloud + opaque cloud. CONFIRMED per Domnich 2021.
- `manual_hq`: {1,2} = thick+thin cloud. CONFIRMED per Aybar 2022.

**This is the paper's strongest technical foundation. Any reviewer challenge to encodings is refuted by the value distribution itself: `s2cloudless` AUC collapses to 0.500 under the wrong threshold.**

---

## 2. S8 Fire-Deletion — NEAR-FATAL CONFOUND

**Status: The 32% headline is driven by a single scene with actual cloud cover. Not independently verifiable as a fire-specific finding without cloud GT for Sen2Fire.**

**Evidence (measured):**

| Scene | Fire discard | Non-fire discard | n_fire |
|-------|-------------|-----------------|--------|
| scene1 | 0.313 | 0.116 | 115 |
| scene2 | 0.000 | 0.004 | 38 |
| scene3 | **0.681** | **0.432** | 94 |
| scene4 | 0.118 | 0.129 | 102 |

Scene 3 alone has 68% discard on fire AND 43% discard on non-fire — the fire:non-fire ratio for scene 3 is only 1.58×. When scene 3 is excluded (scenes 1+4 only): fire discard = 0.221, non-fire = 0.121, ratio = 1.83×.

The aggregate 32% fire vs 15% non-fire is strongly driven by scene 3 having what appears to be actual cloud cover (mean brightness = 1347 vs scene 1 = 925, scene 2 = 556). Scene 2 has essentially zero discards for anything — possibly a night scene or very low-sun angle.

**Compounding issue:** Sen2Fire has no cloud ground truth. The paper acknowledges this ("fire patches may also contain cloud") but does not control for it. The 32% "fire-scene deletion" rate is therefore not demonstrably fire-specific — it may largely be cloud-contaminated patches that happen to contain fire.

**Compounding issue 2:** The spectral (SWIR) model discards fire scenes at essentially the same rate as the brightness model (31.5% vs 32.1%). The paper presents this as "SWIR does NOT fix fire-deletion, strengthening the thesis." But the reason SWIR doesn't help here may be that fire patches have LOWER B11/B12 than non-fire (fire=2221, nonfire=2501 for B11), not higher — active fire should be SWIR-bright. This suggests the "fire" being discarded is smoke-covered fire scenes (smoke is cloud-like in visible bands), not directly fire-bright scenes. The mechanism is different from what the paper implies.

**Kills:** The cross-domain harm generalization beyond snow. A reviewer will correctly note: "show me fire scenes being discarded without cloud GT."

**Fix:** Either obtain cloud ground truth annotations for Sen2Fire (hard), report per-scene ratios, clearly caveat that the 32% aggregate is likely confounded by scene 3, and lead with the fire-discard gallery (6 visually compelling smoke-plume examples) rather than the aggregate statistic. Do NOT present the 32% headline as confirmed evidence of systematic fire-deletion.

---

## 3. "Unidentifiable" Framing — Critical Precision Issue

**Status: Technically correct but will get shredded by a causal inference reviewer.**

**Evidence (measured):**

The S6 probe (100 random labeled frames from all N=975) recovers the true FD rate accurately:

| Detector | True FD | Probe estimate | Probe CI |
|---------|---------|---------------|---------|
| sen2cor | 0.068 | 0.066 | [0.000, 0.154] |
| fmask | 0.043 | 0.042 | [0.000, 0.121] |
| kappamask | 0.096 | 0.093 | [0.000, 0.197] |

The probe works (unbiased). So the false-discard rate IS identifiable — with a probe.

**The killer problem with the probe:** In a real deployed irreversible system, the probe samples from ALL frames (including discarded ones), meaning you must bypass the gatekeeper for ~100 frames per monitoring period. This requires a system modification (bandwidth allocation bypass or parallel downlink). It is NOT trivially "ground-side" — it requires re-architecting the onboard filter to tag some frames as bypass. A satellite systems reviewer will immediately note this.

**The probe CI issue:** All probe CIs include zero (CI = [0.000, 0.154] for sen2cor with true rate 0.068). A single probe deployment of 100 samples yields zero bad discards with non-trivial probability. For a ±3% CI at 95% confidence: sen2cor needs 271 samples, kappamask needs 370 samples, not 100. The "small calibration probe" claim is significantly weakened.

**What is actually correct:** "Unidentifiable from already-downlinked retained data WITHOUT additional data collection or system modification." This is precise, defensible, and still non-trivial. The probe IS the remedy — but describe it honestly as a "randomized bypass protocol" requiring ~300+ frames, not "a small ground-side probe."

---

## 4. Headline FD Numbers: Wrong Split in Abstract

**Status: Critical presentation inconsistency. Both sets of numbers are real, but mixing them without labeling is a reproducibility problem.**

**Evidence (measured):**

The abstract claims "Sen2Cor 19%, Fmask 21%, KappaMask 49% bright-clear over-discard" — these come from S4 (TEST set, n=43 bright-clear patches, NO bootstrap CI).

The larger S9 train set (n=377 bright-clear patches, WITH bootstrap CIs) shows:

| Detector | Test (n=43) | Train (n=377) |
|---------|------------|--------------|
| Sen2Cor | 18.6% | **15.6%** |
| Fmask | 20.9% | **19.1%** |
| KappaMask | 48.8% | **43.5%** |

KappaMask's CI on the test set estimate: [0.349, 0.628] — a width of 0.279 on 43 patches. The 49% headline has a ±14% CI. The test-set KappaMask number is at the upper end of the plausible range.

**Correct approach for submission:** Primary numbers from S9 (train, n=377, CIs). Test set as corroboration. The KappaMask claim drops from "49%" to "43.5% [38%, 49%]" — still compelling, but not the same headline.

---

## 5. Sen2Cor NDSI Failure — Broken Mechanistic Story

**Status: Critical. The paper's mechanistic explanation (NDSI identifies snow → explains consensus) does not hold for Sen2Cor.**

**Evidence (measured):**

| Detector | Consensus AUC | NDSI AUC |
|---------|--------------|---------|
| Sen2Cor | 0.922 | **0.511** (chance) |
| Fmask | 0.795 | 0.823 |
| KappaMask | 0.876 | 0.927 |

Sen2Cor has the HIGHEST consensus AUC (0.922) but NDSI at chance (0.511). The mechanism "consensus works because bad discards are snow → NDSI identifies snow → independent physical explanation" applies only to KappaMask and Fmask. For Sen2Cor, consensus works for completely different reasons. Sen2Cor's FD profile: clear_bright=18.6%, clear_snow_bare=14.3% — it over-discards bright scenes in general, not specifically snow.

**Impact:** The unified NDSI story (sharpened_angle.md: "NDSI achieves AUC up to 0.93 for snow-dominated failure modes, offering an independent architectural explanation for why consensus works") breaks for Sen2Cor. The paper must present two failure modes: (1) snow-specific over-discard (KappaMask, Fmask — NDSI explains it), (2) general bright-surface over-discard (Sen2Cor — consensus works but NDSI doesn't explain why).

---

## 6. Panel Independence — Partially Undermined

**Status: High severity. The cnn_rgbi/cnn_rgbi_swir pair (agreement = 0.948) is essentially one detector.**

**Evidence (measured):**

Mean off-diagonal agreement = 0.846. But cnn_rgbi ↔ cnn_rgbi_swir = 0.948 — trained on same dataset with same architecture, differing only in band access. They contribute nearly identical information to the consensus.

For Sen2Cor's "least correlated 3" panel: [kappamask, cnn_rgbi, cnn_rgbi_swir]. But cnn_rgbi and cnn_rgbi_swir are 0.948 correlated. The "3 detectors" is effectively "2 independent signals." The consensus AUC from this panel = 0.889, but it's not 3 independent votes.

For Fmask, least-correlated 3 includes [cnn_rgbi, cnn_rgbi_swir, sen2cor]. Same problem: cnn pair = 0.948 correlated. Fmask's least-correlated panel AUC = 0.689.

**NDSI as truly independent signal:** NDSI IS detector-independent (band ratio, no detector) and achieves AUC 0.823 (fmask), 0.927 (kappamask). This is the strongest independence argument, and it holds cleanly.

**Fix:** Report the independence test honestly: "effective panel diversity is 4–5 independent signals, not 6, due to the near-identical cnn_rgbi pair." NDSI is the key evidence of architecture-independent detection. The least-correlated-3 analysis should exclude the paired CNNs from being counted as two independent detectors.

---

## 7. Train Set as Primary Evaluation (S9)

**Status: High. Evaluating final claims on the train split is methodologically questionable for a submission.**

S9 uses the TRAIN split (8490 patches) for the scale-up that provides the KappaMask 63% snow claim (n=99, CIs non-overlapping). The test split was used in S4/S5. The experiment_log and sharpened_angle mix numbers from both splits without clear labeling.

For a submitted paper: the test split should be the primary reported result, with train as exploratory/supporting. Or (better): present both as separate confirmations. Either way, split membership must be explicit in every table.

**The OOF issue:** For "ours_brightness" model, S9 trains+evaluates OOF on the TRAIN split. This is technically valid (GroupKFold OOF on disjoint folds) but for reporting purposes, the model's performance on a held-out test set would be stronger.

---

## 8. Routing Track Artifacts — Already Known, But Still In Pipeline

**Status: Medium. The paper's own experiment_log says C2-SIV (87.5%) and C3 (6.7×) are "superseded" artifacts. But sharpened_angle.md ABSTRACT still quotes these numbers.**

Sharpened_angle.md abstract: "a naive linear router trained on lexical statistics flips 87.5% of its decisions under a cosmetic encoding change."

The AUDIT.md (2026-06-22) says: "C2-SIV ARTIFACT — drop/reframe. StandardScaler z=109.7 on a feature firing in 2/24051 train rows. RobustScaler→0.088."

The abstract has NOT been updated to remove the artifact numbers. If submitted with the current sharpened_angle text, a reviewer running any replication will find this immediately.

**Fix:** The routing section should lead with the RouteLLM result (AUC 0.675 for length-only, real and confound-free) and the RouterBench saturation finding (eval_name alone = AUC 0.693). The SIV story, if kept, should use the honest RobustScaler result and be framed as "scaling-sensitive" rather than the headline claim.

---

## 9. Probe Deployment Feasibility — Medium

**Status: Medium. Not fatal but weakens the "deployable remedy" claim.**

The S6 probe requires downloading frames that the onboard gatekeeper would have discarded. In a deployed satellite system, this requires either (a) a "bypass protocol" tag on some fraction of frames before launch, or (b) a separate parallel communication channel. The paper describes this as "a small ground-side probe" — but it requires system design changes, not just ground processing.

Additionally, n=100 probe frames give CIs that include zero for all detectors with FD rate < 0.16. Practical deployment needs 271–565 frames depending on the expected rate.

---

## 10. What Is Bulletproof

The following claims survive all code verification and statistical scrutiny:

1. **Detector encodings:** All correct. No encoding error. This eliminates the #1 attack.

2. **S9 snow CIs:** Non-overlapping. Brightness snow FD = 0.263 [0.182, 0.343]. Spectral = 0.010 [0.000, 0.030]. CIs do not overlap. KappaMask snow 0.626 (n=99). The core snow finding is confirmed.

3. **S5 consensus AUC CIs:** All 95% CI lower bounds > 0.70 (fmask lower = 0.714, others higher). The "all exclude 0.70" claim is verified.

4. **GroupKFold correctness:** Validated in trackb_leakage.py. GroupKFold(roi_id) vs random CV changes AUC ±0.004 — results are not spatial-leakage artifacts.

5. **No S5 circularity:** manual_hq only defines ground-truth labels. The 6 panel detectors are independently computed cloud masks — none uses manual_hq as input. AUC computation is clean.

6. **No citation fabrication:** 77 citations verified (54 arXiv + 23 DOI). Zero fabricated papers.

7. **RouteLLM C1 (confound-free):** length_only AUC = 0.675, tfidf 0.785, semantic 0.772. These are from the audit-verified r_routellm.json (n=109,101). Not a RouterBench artifact.

8. **Threshold robustness:** The fire/non-fire ratio (~2.1×) is consistent across thresholds 0.3–0.7 in S8. For the brightness/spectral gap in S2, the 4–5× ratio holds across discard thresholds (verified in experiment_log).

9. **S7 NDSI independence (KappaMask+Fmask):** NDSI is a detector-independent band ratio. NDSI AUC = 0.927 (kappamask), 0.823 (fmask). These are computed from raw band statistics, not from any detector. Independence is physical, not circular.

---

## Summary of Issue Interactions

The near-fatal and critical issues interact in a damaging way:

- The fire-deletion (S8) is cited in the abstract as the "consequential harm generalizes beyond snow." If S8 is confounded, the two-domain harm narrative weakens to snow only.
- The "unidentifiable" claim is the framing centerpiece. If a reviewer notes the probe identifies it but requires system modification + 300+ frames, the framing becomes "harder to estimate" not "unidentifiable" — weaker but still publishable.
- The headline FD numbers (19%, 21%, 49%) come from the smaller test set and are not the best estimates. A reviewer who checks the train-set numbers will see lower values and ask why the test-set numbers are featured.
- The Sen2Cor NDSI failure means the mechanistic story is only partial. The consensus works for Sen2Cor, but "it works because of snow spectral signatures" is only true for two of three real detectors.

---

## Fix Priority for Submission

1. **(Do immediately, 1 day):** Rewrite S8 section. Drop the 32% aggregate headline. Report per-scene ratios. Add explicit caveat: "no cloud GT for Sen2Fire; scene 3 shows elevated discard for both fire and non-fire patches (likely cloud-contaminated)." Keep the 6-panel gallery and the 1.83× ratio for scenes 1+4. Frame as: "preliminary evidence of fire-scene over-discard, requiring cloud GT for confirmation."

2. **(Do immediately, 2 hours):** Replace "unidentifiable" with "unidentifiable from already-downlinked retained data alone." Describe the probe honestly: "randomized bypass protocol (bypasses the filter for ~300 frames)." Report probe CIs and note that n=100 is insufficient at low FD rates — recommend n≥300.

3. **(Do immediately, 1 hour):** Adopt S9 (train set, n=377) as PRIMARY bright-clear FD numbers. Update abstract: "Sen2Cor 15.6% [CI], Fmask 19.1% [CI], KappaMask 43.5% [CI]." Keep S4 test set as corroboration.

4. **(Do immediately, 1 hour):** Fix the NDSI story. Add: "NDSI explains KappaMask and Fmask failures (snow-specific). Sen2Cor's failures are general-brightness (NDSI chance); its consensus AUC reflects architectural/contextual detection diversity, not snow specificity."

5. **(Do before draft, 2 hours):** Remove 87.5% SIV and 6.7× cost blowup from abstract/sharpened_angle. These are confirmed artifacts. Use RouteLLM length-only AUC (0.675) and semantic gap (+0.031) as the routing headline.

6. **(Before submission):** Clearly label every result by split (TEST/TRAIN). Do not mix S5 and S9 numbers in the same sentence without attribution.

---

## Final Publishability Verdict

**Current state: Reject at NeurIPS D&B / ICLR in current form. The near-fatal S8 issue plus the critical inconsistencies (wrong-split headlines, broken NDSI story, artifact routing numbers still in abstract) would earn a confident reject from any careful reviewer.**

**With the 6 fixes above (estimated 1–2 days of work): Plausible submission at NeurIPS D&B or ICLR workshop track.** The core findings — detector encodings verified, snow CIs non-overlapping, consensus AUC CIs all > 0.70, GroupKFold clean, no circularity — survive every adversarial check. The "irreversibility + unidentifiability" framing needs precision, not replacement. The fire-deletion finding is real but overstated.

**What the paper can honestly claim after fixes:** Three operational cloud-masking systems irreversibly discard 16–44% of bright-clear scenes (Sen2Cor 15.6%, Fmask 19.1%, KappaMask 43.5%, n=377, with bootstrap CIs); cross-detector consensus detects bad discards with AUC 0.78–0.84 on the train set (all CIs > 0.70); NDSI detects bad discards with AUC 0.82–0.93 for KappaMask and Fmask specifically; the false-discard rate is not recoverable from downlinked data alone but is estimable via a randomized bypass probe (~300 frames) or via cross-detector consensus (biased by 1.2–3.9×); LLM routing on a confound-free substrate (RouteLLM, 109K prompts) shows length-alone captures 61% of achievable signal while semantic adds only +0.031 AUC — both domains exhibit surface-shortcut behavior but only satellite triage is irreversible.

That is a publishable contribution. The paper as currently written is not.
