# Paper Plan — What the Gatekeeper Throws Away

> ⚠️ **THIS PLAN IS SUPERSEDED (2026-06-22). Authoritative docs:** `audit/sharpened_angle.md`
> (locked frame), `audit/AUDIT.md` (what survived audit), `experiment_log.md` (results).
> The original "surface-form shortcut" thesis below was REFUTED by the strawman test
> (S4) and replaced by the **identifiability** frame: irreversible triage makes its
> false-discard rate *unidentifiable* from retained data; we quantify it across deployed
> cloud-masks and recover it via probe + cross-detector consensus. New title:
> *"What the Gatekeeper Destroys: Irreversible Triage Makes Its False-Discard Rate
> Unidentifiable, and We Recover It."* Weight 40/60 satellite. Read below only for the
> Track-A/methods scaffolding, not the thesis.

**(superseded) Working title:** *What the Gatekeeper Throws Away: Surface-Form Shortcuts in Recoverable and Irreversible AI Triage*

Unifying frame: **AI gatekeepers** — classifiers that decide *what flows and what is destroyed* — learn surface form instead of task intent. Studied across two domains whose stakes diverge on one axis:
- **Economic & recoverable:** LLM routing (mis-route → retry). Origin: a production routing classifier (anonymized; the Meridian seed).
- **Physical & irreversible:** onboard satellite Earth-observation (EO) triage (mis-discard → raw frame destroyed, no audit possible).

Status: **design locked 2026-06-19, no experiments run.** Two-domain scope chosen 2026-06-19.
Target: arXiv `cs.LG`+`cs.CV`/`cs.CL` (~9–10pp) + LessWrong/EA-Forum cut. No hard deadline; ship fast.

---

## 1. One-sentence contribution

> Across two AI-gatekeeping tasks — LLM routing and onboard satellite data triage — classifiers reach high held-out accuracy by exploiting **surface-form proxies** (lexical stats; pixel brightness/albedo) rather than task intent; we give domain-general intervention tests that expose this, show the failure is **invisible to the headline metric and unauditable when the gatekeeper's decision is irreversible**, and build a ground-side audit harness that estimates how much true signal a triage filter silently discards without access to what it threw away.

## 2. Three pillars (crystal clear by end of intro)

| Pillar | Statement | Test |
|--------|-----------|------|
| **What** | In both domains a surface-only gatekeeper (lexical features / brightness features) matches an intent-aware reference on headline accuracy, while keying on form not intent. | Accuracy-parity tables: routing (RouterBench), triage (CloudSEN12). |
| **Why** | The accuracy is "on the wrong axis." Intervention tests separate the two: surface gatekeepers flip under intent-preserving perturbation (high SIV) and fail under surface-preserving intent change (low IS). Concretely, the triage surface model discards **snow, bright desert, and active-fire/smoke scenes** as "cloud." | SIV/IS on both domains + the visceral fire-deletion demo (SEN2FIRE). |
| **So what** | Selecting on accuracy is Goodhart. When the decision is **irreversible** (orbital discard), the mistake is permanent and leaves no audit trail. We give an audit harness that flags probable bad discards without ground truth. | Irreversibility/cost analysis + audit-harness eval. |

**Novelty honesty (do NOT overclaim):** cloud masks confusing snow/bright surfaces for cloud is *already documented* in remote-sensing literature. The contribution is NOT discovering that. It is: (1) **reframing** it as shortcut-learning/eval-integrity, same mechanism as LLM routing; (2) the **irreversibility axis** (recoverable vs permanent gatekeeping, and what that does to auditability); (3) the **ground-side audit harness**. Sell 2 and 3.

**Stealth:** Meridian = anonymized motivation only ("a production routing classifier"). All evidence public. Honors meridian-stealth rule.

## 3. Claims → experiments map

| Claim | Experiment | Expected evidence |
|-------|-----------|-------------------|
| **C1** Surface ≈ intent-aware on headline accuracy (both domains) | **R1** routing: {majority, surface, TF-IDF, semantic} on RouterBench · **S1** triage: {brightness-only, spectral/13-band} on CloudSEN12 | acc/AUC parity; the trap |
| **C2** Surface gatekeeper tracks form not intent | **R2/S2** intervention tests: SIV (intent-preserving perturbation) + IS (surface-preserving minimal pairs) | surface high SIV / low IS; reference better |
| **C2-viz** Visceral failure | **S2-fire** run triage models on SEN2FIRE/Land8Fire active-fire scenes | brightness model discards fire/smoke as cloud; show the deleted frames |
| **C3** Metric-optimal gatekeeper is worse + unauditable under irreversibility | **R3** routing covariate (formatting) shift cost collapse · **S3** triage "silent discard cost": fraction of valuable scenes (fire/flood/snow-clear) permanently lost, invisible to accuracy | surface model collapses; accuracy gives no warning |
| **C4** Audit harness recovers the hidden failure | **A1** ground-side estimator of false-discard rate via surface-vs-spectral disagreement + held-out probe set; report precision/recall of "bad-discard" flags | harness flags the discards accuracy missed |

## 4. Experimental design

### Track A — LLM routing (fast, ~$0, CPU; de-risks the mechanism first)
- **Substrate:** RouterBench (`withmartian/routerbench`, arXiv 2403.12031) — 405k precomputed outcomes, offline labels. Secondary: RouteLLM `Djudge` (arXiv 2406.18665).
- Label = cheapest-correct-model → binary `route_premium`.
- Models: majority · **surface-only** (exact Meridian feature set: token count, char length, sentence/word stats, code-fence flag, digit/non-ASCII ratios, punctuation, has-URL/JSON) · TF-IDF · semantic (MiniLM embeddings).
- Interventions: SIV via paraphrase + cosmetic reformatting (label-invariant); IS via surface-matched difficulty minimal pairs.
- Shift: wrap test prompts in code fences / length-normalize → recompute realized cost-savings.

### Track B — Onboard EO triage (the visceral core; imagery, GPU on the 4090)
- **Substrate:** CloudSEN12 / CloudSEN12+ (`cloudsen12.github.io`, Nature Sci Data 2022) — 49,400+ expert-labeled Sentinel-2 patches, thick/thin cloud + shadow + 8 SOTA algorithm outputs. Fire: **SEN2FIRE**, **Land8Fire**, **Copernicus-EMS wildfire** (GitHub `MatteoM95/CEMS-Wildfire-Dataset`).
- **Triage task:** binary keep/discard per patch; discard rule = cloud-fraction > τ (the onboard "is this frame worth downlink?" decision).
- **Surface gatekeeper:** visible-band brightness/albedo + simple texture (mean/var/percentiles of RGB reflectance), or small CNN on RGB only. Keys on brightness — the documented failure mode.
- **Intent-aware reference:** uses physically-disambiguating bands (SWIR B11/B12, cirrus B10, NIR) that separate cloud from bright ground; or full 13-band CNN.
- **C1:** both ~equal on the standard CloudSEN12 cloud-detection split.
- **C2:** on snow / bright-desert / urban subsets and SEN2FIRE active-fire scenes, brightness model mis-discards (flags bright valuable scene as cloud); spectral model holds. IS = does the gatekeeper keep a bright *clear* scene? SIV = does a benign radiometric/gain shift flip keep→discard?
- **S2-fire (the artifact):** gallery of active-fire / disaster frames the brightness triage model discards as "cloud." This is the visceral object for the LessWrong post.
- **C3 (irreversibility):** silent-discard cost = % of valuable-signal scenes permanently lost; show headline accuracy is uncorrelated with it. Contrast with routing where the same mistake is a recoverable retry.

### Audit harness (A1 — the buildable novel artifact)
Ground-side: given a triage filter + a held-out labeled probe set (bright/fire/snow/clear), estimate false-discard rate **without** production discards. Signal: disagreement between surface and spectral models as a "probable bad discard" flag; calibrate on the probe set; report precision/recall of flags vs true bad discards. Output framing: an **intent-invariance certificate** for a gatekeeper filter — works for both routing and triage.

### Cross-domain synthesis (the unifying table)
| Construct | LLM routing | Onboard EO triage |
|-----------|-------------|-------------------|
| Gatekeeper decides | which model serves | which frame survives |
| Stated metric | routing accuracy | cloud-detection accuracy |
| Surface proxy | lexical stats | pixel brightness/albedo |
| Intent signal | task difficulty | physical scene content (SWIR-separable) |
| Mistake cost | recoverable (retry) | **irreversible (frame destroyed)** |
| Auditable post-hoc? | yes (logs) | **no (raw data never came down)** |

### Metrics & stats
acc/AUC; realized cost-savings; SIV; IS; silent-discard cost; harness precision/recall. 5 seeds, mean±std. McNemar paired tests; bootstrap 95% CI on SIV/IS/discard deltas; Cohen's h on flip rates.

### Compute
Track A ≈ $0, CPU, <1h. Track B: GPU (RTX 4090 desktop) — CNN training on CloudSEN12 patches + SEN2FIRE eval. Use pretrained backbones / band-subset models to keep it to a weekend. Possible API spend only for routing paraphrase (or local model → $0).

## 5. Related-work clusters (verify every cite in Phase 1; none from memory)
- **LLM routing:** RouterBench (Hu+ 2024), RouteLLM (Ong+ 2024), FrugalGPT (Chen+ 2023), Hybrid LLM (Ding+ 2024).
- **Onboard/edge EO + cloud masking:** CloudSEN12 (Aybar+ 2022), Sentinel-2 L1C cloud-mask assessment (Coluzzi+ 2018, ScienceDirect — the documented bright-surface failures), s2cloudless/SEnSeI, Φ-sat onboard inference, Planet/Satellogic onboard-AI press.
- **Shortcut learning / spurious cues:** Geirhos+ 2020, McCoy+ 2019 (HANS), Gururangan+ 2018, Niven & Kao 2019.
- **Goodhart / reward hacking / spec gaming:** Amodei+ 2016, Skalse+ 2022, Pan+ 2022, Krakovna list.
- **Eval / construct validity + invariance testing:** Raji+ 2021, Bowman & Dahl 2021, Ribeiro+ 2020 (CheckList), Gardner+ 2020 (contrast sets).

Positioning: *shortcut learning at the gatekeeper layer — where it is invisible to the headline metric, drives spend, and, when irreversible, destroys data no audit can recover.*

## 6. Venue / framing
arXiv `cs.LG` primary, cross-list `cs.CV` + `cs.CL`. LessWrong/EA-Forum post built around the deleted-disaster-footage gallery (closes "no public AI writing" gap; external URL). Fellowship framing: cross-domain empirical eval-integrity result on public data, with a spacetech instantiation — distinctive vs the cohort. Identity: it's a **credibility artifact, not a venture** — no Meridian pivot into space.

## 7. TODO
- [x] **Track A** (LLM routing) — C1/C2/C3 all confirmed. See `experiment_log.md`. ✓ 2026-06-22
  - C1: surface ≈ semantic AUC (gap −0.014). C2: surface_logreg SIV 0.875 (code-fence) vs semantic 0.012. C3: 6.7× cost blowup under formatting shift. Figs 2,3 done.
- [ ] E2b Intent-Sensitivity (IS) minimal pairs for routing (appendix-tier)
- [ ] Robustness check: stronger embedder (mpnet/BGE) to preempt "MiniLM weak"
- [ ] **Track B** (satellite EO triage): CloudSEN12 + SEN2FIRE download, brightness vs spectral gatekeeper, S1/S2 + fire-deletion gallery, silent-discard cost, audit harness
- [ ] P1 lit review — verify §5 cites; programmatic BibTeX, mark [CITATION NEEDED]
- [ ] P5 draft (Fig1 cross-domain → abstract → intro → method → results → related → limitations → conclusion)
- [ ] P6 self-review ensemble + claim-verification; P7 arXiv + LessWrong cut

### Refined thesis (post-Track-A hardening, honest)
Not "surface models are bad" (surface_hgb is accurate AND robust). Villain = the **metric/benchmark**: it is **surface-saturated** (C1: no surface/lexical/MiniLM/mpnet/BGE model beats AUC ~0.71; IS: controlling surface leaves ≤0.56 recoverable signal for anyone) and therefore **structurally rewards form-reading while staying blind to intent-robustness** — surface_logreg & semantic score comparable AUC yet differ ~40–70× in form-change flip rate (SIV) and the surface one detonates 6.7× under a cosmetic reformat (C3). SIV = the proposed missing eval axis. surface_logreg (naive linear-on-surface, the Meridian-shaped design) = cautionary exhibit. Track B = where intent (real ground signal) vs surface (brightness) are physically separable (SWIR) → the clean IS contrast routing can't give.

## 8. Open decisions (flag, don't block)
- Cloud-fraction threshold τ for keep/discard (sweep; sensitivity in appendix).
- Brightness vs spectral model capacity — match params so parity isn't a capacity artifact.
- Semantic/spectral reference framed as **contrast not cure** (it has its own shortcuts; state explicitly).
- Sequencing: prove C1 on routing (cheap) before committing GPU time to Track B.
