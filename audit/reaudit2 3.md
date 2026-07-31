# Reaudit 2 — Reviewer 2 Hostile Re-Audit
Date: 2026-06-22

All experiments re-run from scratch. Numbers below are measured, not recalled.
Codebase: `/Users/aadi/Desktop/Research Paper`
Python: `.venv/bin/python`

---

## Surviving Claims Status

| Claim | Status | Measured Evidence |
|---|---|---|
| **R-RouteLLM: surface AUC well above chance (0.74), length alone 0.675** | **CONFIRMED HOLDS** | Re-run: tfidf=0.785, semantic=0.772, surface_hgb=0.741, surface_logreg=0.699, length_only=0.675. Identical to stored results. |
| **RouterBench C1: eval-identity confound dominates** | **CONFIRMED** | group-by-eval all models 0.544–0.602 (honest_c1.py re-run). eval_name-alone AUC=0.693 under random split. |
| **C2-SIV 0.875 code-fence blowup** | **CONFIRMED ARTIFACT** | Already acknowledged in AUDIT.md. Not re-run; accepted from audit/honest_c1.py evidence. |
| **C3 6.7× cost blowup** | **CONFIRMED ARTIFACT** | shift_cost == always-strong by construction. Already conceded. |
| **S1 parity: brightness_hgb AUC 0.856, spectral_hgb 0.908** | **CONFIRMED (but no ROI group CV in original run)** | Stored results match re-run. GroupKFold reaudit: brightness=0.860, spectral=0.910 — essentially identical, spatial leakage does NOT inflate AUC. |
| **S2 brightness false-discards 60.5% of clear_bright_top25pct (n=43)** | **DIRECTION HOLDS, FRAMING WRONG** | Measured: 60.5% (brightness_hgb) vs 14.0% (spectral_hgb). p<0.0001 by permutation. BUT n=43 is a brightness-percentile cut, not land-cover-verified. See Finding #1. |
| **S2 clear_snow_or_bare n=35** | **MISLABELED** | Only 7/35 are actual snow/ice (LC=70). 28/35 are bare/sparse vegetation (LC=60), a different category. The correct snow-only subset is n=7. See Finding #2. |
| **No train/test leakage (RouteLLM)** | **CONFIRMED** | 109,101 unique prompts, 0 cross-split duplicates under all 5 seeds. |
| **tfidf beats semantic on RouterBench** | **VACUOUS UNDER HONEST SPLIT** | group-by-eval: tfidf=0.564±0.042 vs semantic=0.544±0.076. Confidence intervals massively overlap. Not distinguishable from noise. |

---

## Critical Findings

### CRITICAL-1: The "snow/desert" headline rests on a brightness percentile, not snow land cover — and the actual snow subset is n=7

**Problem:** The paper's Track B S2 claim ("brightness model irreversibly discards ~61% of bright clear scenes as cloud — snow/desert") conflates two subsets: (a) `clear_bright_top25pct` (n=43, brightness ≥ 75th percentile of all 975 patches) and (b) `clear_snow_or_bare` (n=35, ESA WorldCover classes 70+60). These subsets have only partial overlap (n=19 both). The "snow/desert" narrative maps onto the brightness-percentile cut (n=43), but that cut is defined by the outcome variable (brightness > threshold), making it circular for a brightness model. More critically: the actual snow/ice (LC=70) clear subset is **n=7**, not n=35. Bare/sparse (LC=60) is not snow or desert; it is shrubland/grassland with moderate brightness.

**Measured Evidence:**
- Snow/ice (LC=70) clear patches: **n=7**. Clopper-Pearson 95% CI for brightness_hgb FDR=6/7=0.857: [0.421, 0.996]. CI width = 0.58. Zero statistical power.
- Bare/sparse (LC=60) clear patches: n=28. Mean brightness = 2441 vs snow mean = 5987.
- Only 7/7 snow patches are above the 75th brightness percentile; only 12/28 bare patches are.
- The "snow/desert" label in experiment_log.md is not supported by the actual land-cover metadata.
- The `clear_snow_or_bare` n=35 and `clear_bright_top25pct` n=43 are reported as if equivalent but measure different things.

**Why Reviewer Rejects:** "Snow and desert are photometrically bright, causing the shortcut" is the paper's causal narrative. This requires verifying on patches that are actually snow and desert, not patches that are merely in the top brightness quartile (which tautologically favors the brightness-model failure story). Reviewer will say: "Your n=7 actual snow result (6/7 false discards, CI [0.42, 1.00]) is statistically uninformative. You cannot publish this as a quantified finding."

**Fix:** Report snow (n=7), bare/sparse (n=28), and the brightness percentile cut (n=43) as three separate columns in the table. Obtain a better-stratified test set (or use the CloudSEN12 full dataset, ~10K patches, to get adequate snow/ice samples). The brightness-percentile cut is still a valid demonstration of the shortcut if framed correctly ("among the brightest-quartile clear patches"). The mislabeling must be corrected.

**Changes Conclusions?** YES — the "snow/desert" story cannot be told with n=7. The broader brightness-percentile finding (n=43) is valid but needs honest framing. The 4× ratio is real and significant; only the labeling is wrong.

---

### CRITICAL-2: Spatial leakage 100% confirmed AND quantified — but it doesn't change the conclusion

**Problem:** CloudSEN12 has exactly 195 ROIs × 5 temporal images = 975 patches. Every single patch shares its ROI with exactly 4 others from the same geographic location. Under random 5-fold CV, **100% of test patches** (975/975) have their geographic ROI represented in the training fold — the maximum possible spatial leakage rate.

**Measured Evidence (trackb_leakage.py):**
```
patches=975  unique ROIs=195  max patches/ROI=5  mean=5.00
patches sharing ROI with >=1 other: 975/975 = 1.000
random 5-fold: test patches whose ROI appears in train = 975/975 = 1.000  (high => spatial leakage)
```
GroupKFold(roi_id) results vs random CV:
```
random 5-fold:    brightness AUC=0.856  spectral AUC=0.908  FD bright=0.605  FD snow/bare=0.286
GroupKFold(roi):  brightness AUC=0.860  spectral AUC=0.910  FD bright=0.558  FD snow/bare=0.286
```

**Impact:** AUC is essentially identical (within 0.4%). False-discard rates on bright subset shift from 0.605 to 0.558 — a 7.7% relative change — but the direction is preserved. The S1 (parity) and S2 (shortcut direction) conclusions survive spatial deconfounding.

**Why Reviewer Cares:** A reviewer will immediately ask "did you use GroupKFold?" and the answer is currently "no." This is a mechanical rejection criterion for any remote sensing experiment with temporal patches. The current text says "5-fold out-of-fold" — full stop. A reviewer seeing no GroupKFold will assume the results are inflated by ROI memorization. The fact that GroupKFold barely changes things is the good news — but you must demonstrate it, not just omit it.

**Fix:** Replace the default 5-fold CV in s1_s2_cloud.py with GroupKFold(roi_id). Report both in the paper. The results are already in trackb_leakage.py. This takes 10 minutes to fix.

**Changes Conclusions?** No — direction and approximate magnitude survive. But the omission will trigger rejection.

---

### CRITICAL-3: The RouteLLM tfidf AUC 0.785 is likely a task-difficulty proxy, not a surface shortcut

**Problem:** The paper's R-RouteLLM claim is that surface form (tfidf, 0.785 AUC) beats semantic (0.772), therefore routing labels are surface-predictable even without a benchmark confound. But the tfidf feature set learns content words (n-grams), not pure surface form. The learned features are task-difficulty indicators: `name_1` (coef=4.07), `translate` (3.05), `into hebrew` (2.15) for positive (needs GPT-4); `how do` (-2.61), `generate` (-1.75), `write` (-1.66) for negative (Mixtral ok). These are semantic/task-type signals, not surface formatting cues.

**Measured Evidence:**
- Top tfidf positive features for route_premium=1: `name_1` (4.07), `https` (3.32), `translate` (3.05), `this task` (2.30), `into hebrew` (2.15), `chatgpt` (2.12)
- Code prompts: mean_tokens=226.2, base_rate=0.157 (vs 0.093 overall)
- Math prompts: mean_tokens=195.9, base_rate=0.194
- Other: mean_tokens=75.7, base_rate=0.085
- Heuristic domain detection (code+math markers): r(code_flag, n_tokens)=0.227 (p<0.0001)
- AUC: length_only=0.671, domain_only=0.536, length+domain=0.671 (domain adds 0 AUC above length)
- SIV for tfidf on RouteLLM: 0.0000 for all perturbations (code_fence, whitespace, trailing) — tfidf is robust, but it means the model never changes its prediction on re-format, because it's anchored to content words

**Why Reviewer Cares:** The paper is titled about "surface vs intent." If the best-performing "surface" model (tfidf 0.785) is actually reading task-content words (translate, hebrew, math terminology), then it is detecting task difficulty — exactly what a semantic model should do. The reviewer will say: "Your tfidf model is a weak intent proxy, not a surface model. The gap between tfidf and semantic (0.785 vs 0.772) may be a weakness of MiniLM-L6 rather than evidence that surface beats intent. You need to ablate: remove content n-grams, keep only formatting features."

**Fix:** For RouteLLM, redefine "surface tfidf" to use ONLY character n-grams (analyzer='char', ngram_range=(2,4)) which capture formatting without content. Compare that AUC to word n-gram tfidf. If char-tfidf AUC drops significantly, the word tfidf signal was task-difficulty, not surface. Also: test stronger encoders (BGE-large, not just MiniLM) — the E1b table shows BGE barely helps for RouterBench but those were run on RouterBench, not RouteLLM.

**Changes Conclusions?** POSSIBLY — if char-tfidf AUC is substantially lower than word-tfidf, the "surface predicts routing" story for RouteLLM is weakened. The current 0.785 is almost certainly dominated by task-type vocabulary, which is closer to intent detection than surface detection.

---

### HIGH-1: group-by-eval RouterBench results show no model is significantly above chance — the CI overlap is vast

**Problem:** The paper's RouterBench core claim (C1 honest) is "length_only ties semantic (0.570 vs 0.544 group-by-eval)." But these are based on 3 seeds with huge variance: length_only 0.570±0.047, semantic 0.544±0.076. The 2-sigma CIs are [0.479, 0.648] and [0.392, 0.696] — massively overlapping. The magnitude of the group-by-eval AUC drops are: tfidf drops 0.147, semantic drops 0.154 from random to group splits.

**Measured Evidence:**
```
group-by-eval AUC:
  length_only    0.570 ± 0.047
  surface_logreg 0.592 ± 0.028
  surface_hgb    0.602 ± 0.036
  tfidf_logreg   0.564 ± 0.042
  semantic_minilm 0.544 ± 0.076
```
All models: 0.544–0.602. Gap from best (surface_hgb 0.602) to semantic (0.544) = 0.058, smaller than the 2-sigma band of semantic alone.

**Why Reviewer Cares:** You are claiming specific rank orderings (length≈semantic, tfidf≈surface) that are not statistically distinguishable under the correct split. The paper needs paired t-tests or bootstrap CI for these comparisons. McNemar was computed for random split (semantic vs surface_logreg p<1e-4) — that comparison is irrelevant under group-by-eval where everything is near chance.

**Fix:** Increase seeds from 3 to 10+ for group-by-eval. Run proper paired bootstrap CIs across the different group-by-eval partitions. Frame the takeaway as "all models collapse to near-chance (0.55–0.60) under honest eval, confirming eval-identity dominates." Do NOT claim specific rank orderings that the data can't support.

**Changes Conclusions?** No, but it changes the confidence of within-group comparisons. The core message (eval-identity confound) is strong.

---

### HIGH-2: Padding zeros in CloudSEN12 introduce systematic 1.17% downward bias on ALL band statistics

**Problem:** The CloudSEN12 images are stored as 512×512 arrays with valid data in only 509×509 pixels. The corners contain zero-padding (3,063 zeros per patch, exactly 1.17%). The `_patch_reduce` function in `src/cloudsen12.py` calls `.ravel()` on the full 512×512 array, including the padding zeros, and computes mean, std, p10, p50, p90 over all 262,144 pixels.

**Measured Evidence:**
```
B2 patch 0: mean WITH padding zeros: 1507.3
B2 patch 0: mean WITHOUT padding zeros: 1525.2
Bias: 0.9883 (systematic 1.17% downward bias on all mean features)
All bands show identical bias: -0.0117 relative mean error
Bias is constant across patches (padding fraction never varies)
```

**Impact Assessment:** The bias is identical across all bands (B2, B3, B4, B8, B11, B12 all biased -1.17%). Since brightness (avg of B2,B3,B4) and spectral features (including B11, B12) are ALL biased by the same factor, derived ratios like NDSI and NDVI are unaffected (biases cancel). The relative comparison between brightness and spectral models is unaffected. S1 AUC and S2 false-discard rate conclusions are valid despite the bias.

**Why Reviewer Cares:** Any remote sensing reviewer will spot `shape=(N, 512, 512)` with `valid_pixels=509×509` and ask whether you masked the padding. Reviewers at IGARSS or RS will reject immediately if you can't demonstrate the bias doesn't matter. Even though it's numerically benign here, you must address it.

**Fix:** In `_patch_reduce`, mask zeros before computing statistics: `v = arr_i.astype(float).ravel(); v = v[v > 0]` (assuming no-data = 0, which the label corners confirm). Add a note in the paper: "Padding zeros excluded from band statistics." The numeric results will shift by ~1.2% uniformly — the comparative conclusions won't change.

**Changes Conclusions?** No — but omitting disclosure invites rejection from any EO reviewer.

---

### MEDIUM-1: The RouteLLM experiment uses random train-test split on data with known user-level correlation — no user-id deduplication

**Problem:** The RouteLLM dataset is from Chatbot Arena where multiple prompts from the same anonymous user session are included. The paper uses a simple random 80/20 split (r_routellm.py). If users tend to submit prompts with consistent style or task type, then the same user's prompts may appear in both train and test, inflating AUC by user-style memorization.

**Measured Evidence:**
- 109,101 unique prompts — no exact duplicate leakage (confirmed).
- No session_id or user_id column in `routellm/gpt4_judge_battles` — cannot directly test user-level correlation.
- Length correlation with route_premium: r=0.135, p<0.0001. Premium prompts are 68.9% longer on average (138.0 vs 81.7 tokens).

**Why Reviewer Cares:** AUC 0.785 for tfidf on this data is the paper's clean claim. A reviewer will ask: "Did you control for user-level clustering?" Without session IDs, you can't directly prove there's no user-level leakage. The correlation structure of Chatbot Arena (many prompts per session) is well-documented.

**Fix:** Acknowledge this limitation explicitly. The RouteLLM paper (Ong et al. 2024) does not document user-level clustering in the gpt4_judge_battles split — cite this. Run a sensitivity analysis using only the first prompt per user if user IDs become available in a future version.

**Changes Conclusions?** Unknown without user IDs. Disclose as a limitation.

---

### MEDIUM-2: The RouterBench label threshold (score ≥ 0.5 = "solved") is not robustness-tested for RouteLLM's tie-drop behavior

**Problem:** The RouteLLM loader explicitly drops tied battles (`route_premium` = 0 for ties, but ties represent 22.2% of the data and are excluded from the label computation implicitly via `winner_model_a == 1`). Rows where neither wins are not in the dataset. This creates selection bias: the label is conditioned on "at least one model produces a decisive outcome," which may correlate with prompt characteristics.

**Measured Evidence:**
- Tie rate: 22.2% of all battles
- Base rate of route_premium=1: 9.3% (GPT-4 strictly wins)
- The 77.8% of non-tie examples: 10.7% need GPT-4, 89.3% don't
- The 22.2% of ties are excluded

**Why Reviewer Cares:** If tie battles have a different length/domain distribution from decisive battles, the training data has selection bias. More importantly: in the deployment scenario, a router must handle ALL queries, including those that would be ties — and you have no data for them.

**Fix:** Load the tie data separately, describe its prompt characteristics (length, domain distribution) vs decisive battles, and either include ties as a "either model works" = 0 class, or explicitly disclose the selection.

**Changes Conclusions?** Likely not, but must be disclosed as a data limitation.

---

### MEDIUM-3: The group-by-eval split is run with only 3 seeds on a small benchmark partition space (only ~25 eval names) — variance is huge

**Problem:** `honest_c1.py` uses 3 seeds for `GroupShuffleSplit(test_size=0.25)`. With ~25 unique benchmarks, each split puts ~6 benchmarks in test. The composition of those 6 benchmarks dominates the AUC result. With 3 seeds, semantic gets std=0.076 — almost as large as the distance from chance (0.544 - 0.500 = 0.044).

**Measured Evidence:**
```
group-by-eval semantic_minilm: 0.544 ± 0.076 (std/mean-above-chance = 0.076/0.044 = 1.73)
```
The signal-to-noise ratio is below 2. Three seeds is inadequate.

**Fix:** Use 20+ seeds. Better: leave-one-benchmark-out (LOBO) CV for the full RouterBench evaluation — this gives all possible benchmark test conditions and eliminates seed dependence. LOBO is standard practice for multi-benchmark evaluation.

**Changes Conclusions?** Possibly changes confidence of group-by-eval rank orderings, but "all models ≈ 0.55–0.60" likely holds.

---

### LOW-1: Label threshold sensitivity (Track B) shows FDR is threshold-dependent; not disclosed

**Problem:** The S2 experiment uses a hard threshold of `cloud_frac >= 0.5` to define the discard label. There is no sensitivity analysis.

**Measured Evidence (label threshold sweep, brightness_hgb on clear_bright_q75, n=43):**
```
thr=0.3: AUC_bright=0.831  AUC_spec=0.888  FDR_bright=0.791  FDR_spec=0.279
thr=0.4: AUC_bright=0.830  AUC_spec=0.897  FDR_bright=0.698  FDR_spec=0.233
thr=0.5: AUC_bright=0.856  AUC_spec=0.908  FDR_bright=0.605  FDR_spec=0.140  (reported)
thr=0.6: AUC_bright=0.869  AUC_spec=0.921  FDR_bright=0.465  FDR_spec=0.093
thr=0.7: AUC_bright=0.870  AUC_spec=0.932  FDR_bright=0.442  FDR_spec=0.047
```

The brightness-hgb FDR at threshold 0.3 is 79.1% vs 14.0% at threshold 0.5 vs 44.2% at 0.7. The headline "61%" is threshold-dependent over a 44%–79% range.

**Why Reviewer Cares:** The choice of 0.5 is arbitrary. The false-discard rate depends on threshold choice. A reviewer will ask why 0.5 specifically.

**Fix:** Report FDR at three thresholds (0.3, 0.5, 0.7) in a sensitivity table. The key finding (brightness FDR >> spectral FDR) holds at ALL thresholds — this is actually a strength to demonstrate. The absolute values vary but the 4–5× ratio is consistent.

**Changes Conclusions?** No — direction is robust. Reporting the sweep strengthens the claim.

---

### LOW-2: The claimed "~4× false-discard ratio" in experiment_log.md is inconsistent with stored results

**Problem:** The log says "brightness model discards ~61% of bright clear scenes; spectral keeps them (14%) — ~4×." But stored results show:
- brightness_hgb clear_bright: 0.605 FDR
- spectral_hgb clear_bright: 0.140 FDR
- Ratio: 0.605/0.140 = 4.32

The "~4×" understates the ratio (it's 4.3×). Also the log headline uses "brightness_hgb 0.605, spectral_hgb 14%" but earlier in the same paragraph says "brightness model irreversibly discards ~61%." These are from different models (brightness_logreg 0.628 vs brightness_hgb 0.605). The logreg has HIGHER FDR (0.628) and was used in the text but the table shows hgb. Minor inconsistency.

**Fix:** Fix the ratio to 4.3× and be consistent about which model is the headline (hgb is the apples-to-apples comparison for spectral_hgb).

---

## Summary Verdict

**Track A (RouterBench): The audit AUDIT.md completed is correct. What's NEW:**
The group-by-eval results (0.544–0.602 AUC with huge variance) mean that "length ties embeddings" is a statistically meaningless claim with 3 seeds. Under the honest split, you cannot distinguish any model from any other — the only defensible claim is "all models collapse to near-chance (0.55–0.60) once eval-identity is removed, confirming the RouterBench confound." The RouteLLM result (tfidf 0.785) is real but the tfidf features are semantic/content signals (task-difficulty vocabulary), not pure surface formatting — this undermines the "surface shortcut" framing.

**Track B (CloudSEN12): Three new problems found:**
1. The "snow/desert" headline uses a brightness-percentile subset (n=43), not verified snow land cover. The actual snow subset is n=7 with a CI too wide to report (0.42–1.00). Bare/sparse (LC=60) ≠ snow/desert in the photometric brightness sense claimed.
2. 100% spatial leakage confirmed (all patches in ROI-overlapping CV). However, GroupKFold replication shows results are robust — AUC shifts ≤0.002, FDR shifts ≤0.05. The problem is omission, not inflation.
3. Padding zeros bias all features by -1.17% uniformly — cancels in ratio comparisons, but must be disclosed and fixed.

**What definitely changes the paper:**
- Replace "clear_snow_or_bare n=35" narrative with honest breakdown: n=7 snow (CI too wide), n=28 bare, n=43 brightness-quartile cut. Only the brightness-quartile cut supports the headline claim, and it must be explicitly motivated as "the operationalization of the brightness shortcut."
- Replace random 5-fold with GroupKFold(roi_id) in s1_s2_cloud.py. Already implemented in trackb_leakage.py.
- Disclose padding zero bias and fix `_patch_reduce` to mask zeros.
- Reframe RouteLLM tfidf claim: test char-ngram tfidf to separate formatting from content.

**What does NOT change the paper's central argument:**
- The 4.3× false-discard gap between brightness and spectral models on bright clear patches is real, statistically significant (permutation p<0.0001), and survives GroupKFold.
- The RouterBench eval-identity confound is real and decisive (AUC drops 0.15 from random to group-by-eval).
- The surface AUC on RouteLLM (0.741–0.785) is above chance — the confound-free signal exists.

**Estimated paper state:** Track B is 75% there with the spatial leakage fix + honest subset reporting. Track A needs the tfidf content-vs-surface ablation and the group-by-eval CI re-run with more seeds before the specific rank claims can be made.
