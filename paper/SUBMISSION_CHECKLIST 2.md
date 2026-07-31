# Submission checklist — "Certified Blind"

> **2026-07-17 PEER-REVIEW PASS (this session).** The hostile cover-to-cover pass the previous closeout called
> for — run as a 51-agent audit (6 numbers-trace agents traced 234 quantitative claims vs results/*.json; 4
> hostile referees: methodology+theory on opus, narrative+gov; every non-nit finding adversarially verified —
> 13 confirmed / 18 refuted; 10 format agents reviewed every rendered page of both forks) + an independent
> literature sweep (novelty claim re-confirmed 3rd pass; all 9 high-risk refs verified exact; du2021
> arXiv:2112.01723 added). ALL 13 confirmed content defects fixed, worst: (1) Fig 6b "57% women" was the stale
> single-seed max — 5-seed data has black 58% > women 57%; prose+caption+bar-sort fixed; (2) KappaMask 63%
> spliced into the s11 real-panel sentence from the unrelated dashboard experiment — now explicitly sourced;
> (3) Table II 0.38pp vs body 2.1pp dent unreconciled — decomposition now stated; (4) ratchet missing from
> security abstract+contributions — added; (5) CUSUM "zero-drift approximation" mischaracterized — fixed;
> (6) gov "first formal treatment" → "to our knowledge, the first". Formatting: Fig 2 x-axis rebuilt in
> slice-fraction units (was corpus-fraction mislabeled "%"), Fig 7 duplicate "T2" labels + labels-on-diagonal
> fixed with unique hand-placed labels, Fig 6b bars re-sorted to plotted values, Fig 6(probe) legend given a
> background, Table I ragged-right (array package — no IEEEtran artifact this time), Table II caption split
> into 2-line caption + proper table footnote, satellite section given the deferred parallel skeleton
> (5 run-in paragraphs), Limitations satellite-number restatement compressed to a pointer. Both forks 14pp/15pp,
> 0 overfull / 0 undefined, `make verify` ALL REPRODUCED. Two-agent final screenshot sweep of every page: clean.
> Still open (unchanged): body+refs ~13pp vs 12pp budget with 50 refs (venue may count refs separately —
> Aadi's call), last-page column imbalance (cosmetic), Discussion-merge deferred (run-ins made it moot).

> **2026-07-17 CLOSEOUT.** Paper is empirically strong + repeatedly stress-tested. main.pdf 14pp /
> main_gov.pdf 15pp, both 0/0, `make verify` green. This long session added: satellite arm → 3 datasets /
> 2 sensors (CloudSEN12 n=47→64, Landsat n=3822/3-scenes, KappaSet n=154/51-products) + real cross-detector
> defense (s11) + measured Θ(k/q) (s12); moderation flagship 93% → seed-robust (93.4%±1.5%, 3 seeds);
> exemplar-study formatting (abstract 207w, bold-label contributions, Definition 1); figure/table readability.
> **NEXT SESSION = one hostile peer-review pass** — see `paper/PEER_REVIEW_HANDOFF.md`. Open items: body+refs
> ~13pp with 47 refs (pre-existing); deferred parallel-section-skeleton + Discussion-merge; delete 2 stale
> macOS " 2" dup files.

> **2026-07-13 session (fresh-session executor):** (1) **Tier-1 roadmap DONE** (commit a009b8f): §II/§VIII
> paragraph-broken + em-dash-trimmed, assumption-ledger table added (§III, `tab:assumptions`), satellite hedging
> collapsed to the §III role statement + one §VIII line, small polish (proxy dedup, ratio-def caption→body,
> Table I units, security-intro attack-surface line, artifact golden-values line). (2) **Fresh adversarial
> stress-test** (opus proof referee re-derived every theorem — all sound; sonnet numbers audit traced 169 claims)
> found + FIXED 11 verified defects (commit e73b99d) — worst: Table I satellite footprint quoted the *predicted*
> p·h (0.92pp) as measured (0.38pp), routing probe-defense numbers were TF-IDF-arm results implied to be MiniLM,
> and the security fork bound the (1−f)^T extinction formula to the natural fixed point that Prop-ratchet proves
> *floors* (closed-loop qualifier was gov-only; now inline). Symbol collisions fixed (competence κ(·) vs probe k;
> gov d(k) vs CUSUM δ). (3) **CloudSEN12+ DOWNLOADED**: 136.9 GB verified (l1c 5 parts + extra 3 parts,
> byte-match vs HF `tacofoundation/cloudsen12`; l2a skipped — L1C-only experiments, disk) → `data/cloudsen12plus/`,
> new Tier D in REPRODUCE.md, `.venv` rebuilt (uv, py3.12.13, `make verify` green). Next: satellite scale-up
> reruns per IMPROVEMENT_ROADMAP "TIER 2+" (GPU work on the 4090 box; tacoreader needed).
> Both forks: 13pp/14pp, 0 undefined / 0 overfull, body+refs end p12.
>
> **2026-07-13 (cont.) — roadmap Tier 2/3 + gov + scale-up DONE (HEAD 52b26a8):** (4) **Algorithm 1** box
> (auditability-preserving certification; `algorithm.sty`/`algorithmic.sty` vendored), footprint fig moved
> body→appendix to pay for it, **security abstract restructured 364→267w** (thesis-first, unidentifiability
> mic-drop last), observability reading tightened. (5) **Gov 11–13**: Prop-patient cross-refs ratchet; DP
> softened to "structurally analogous to ε→0"; **primary legal cites** added + web-verified (18 U.S.C.
> §1519–1520 = SOX §802; FRCP 37(e) = spoliation). (6) **Fig-6 multi-seed CIs** (`c_ratchet_multiseed.py`,
> 5 seeds) — paper numbers → means+CIs. (7) **CloudSEN12+ satellite scale-up** (`s10_plus_multiseed.py`):
> held-out clear-snow **n=47→64**, POISON slice FDR **0.91±0.06, every seed ≥0.81** (seed-robust vs the
> single-seed 0.79), cert still 2/5 — integrated §Dashboard/§Limitations, ref `aybar2024`. **Honest finding:
> snow is intrinsically rare in CloudSEN12+ (+~18 patches), so this firms n + adds CIs but does NOT reach
> the roadmap's "thousands"** — stated as such in-paper. Base t3/t3d golden values untouched, `make verify`
> green. DEFERRED (compute/low-value): fig-5 distilbert multi-seed (~1hr, ratio already reproduces exactly);
> t3f discovery rerun (not the n-limited claim).
>
> **2026-07-13 SECOND-SENSOR win — the n=47 caveat is retired (HEAD 8530d0d):** CloudSEN12 snow is
> intrinsically rare, so abundant snow came from a second sensor. L8 Biome Snow/Ice biome (Foga 2017,
> Landsat-8, 12 scenes) → `extract_l8biome_snow.py` yields 8,957 clear-snow crops; `s13_landsat_backdoor.py`
> (4-band CloudScout-style, scene-disjoint, checkpoint-resumable): **held-out clear-snow n=3822 (vs 47),
> POISON FDR 1.00 [1.00,1.00] all 3 seeds vs CLEAN 0.005** — the certified-harm mechanism transfers across
> sensor/dataset/label-provenance. Diagnostic caught along the way: 3-band fails because snow IS a bright
> cloud without SWIR (physics, not bug); +B6 SWIR fixes it. HONEST caveat in-paper: Landsat certifier is
> 91.7% cloud, so the claim is the hidden-harm gap (1.00 vs 0.005), not the accuracy bar. Also preserved
> CloudSEN12+ (full-table parquet + 522-patch snow bundle) then pruned the 127GB raw. KappaSet (S2 bonus)
> download unreliable under machine-sleep; now resumable, optional since L8 already delivered. Both forks
> 14pp/15pp, body+refs p12, 0/0, verify green.
>
> **2026-07-13 "maximize the data" pivot (HEAD a59d521):** the snow scale-up was a dud (+18 patches), so mined
> the ignored 42GB `cloudsen12-extra` (8 detectors + elevation) for TWO synthetic→real upgrades: (8) **s11
> real cross-detector defense** — poisoned CloudScout 81% snow-discard vs real independent-CNN panel 0% → flag
> fires (base was synthetic 0.575/0.000); (9) **s12 metadata-predictability** — elevation lifts snow prevalence
> 5.0%→40% (8×), instantiating Prop-opaque's Θ(k/q) branch (was asserted). Then a fresh **opus stress-test**
> (2 MAJOR+3 MINOR): reconciled a real §IV↔s11 coherence gap (blind spot is detector-specific, not
> architectural), added circularity + pool-prevalence caveats; 1 MAJOR was a false positive (verified). Dropped
> qa60 from the panel (binarization artifact). Both forks 14pp/15pp, body+refs p12, 0/0, verify green.

> **FORKED (2026-07-11):** one source, two framings via a `\govbuild` LaTeX toggle. `make pdf` → `main.pdf`
> (**SaTML security** version, 16pp, primary target, default). `make pdf-gov` → `main_gov.pdf` (**higher-altitude
> AI-accountability** version, 18pp, for the fellowship/governance packet). Identical results/proofs; only the
> abstract, intro, an `\ifgovernance`-guarded "Accountability, Policy & Lock-in" section (+ Prop: patient-attacker
> insufficiency, honestly caveated, + Fricker epistemic-injustice analogue) and the conclusion differ. All
> governance framing claims web-verified (Wald 1943 rigorous method, Kulveit et al. ICML 2025, SOX §802, Balkin
> 2016, Pauly 1995). Full reframe rationale + the 12-connection perspective map + verification record: `PERSPECTIVE.md`.
>
> **5 additions applied 2026-07-11 (all via delegate→adversarial-verify→watcher-integrate; every verifier-required
> fix + citation check honored — see `AGENT_FINDINGS.md`):** (1) multi-generation adversarial-game remark + (2)
> cross-generation CUSUM defense [both §6, SHARED] — CUSUM ships the correct Siegmund ARL `(2σ²/δ²)exp(λδ/σ²)`, NOT
> the wrong zero-drift `exp(2λ²/σ²)`; multigen separates the per-round ceiling h* (probe fires ≥β) from the patient
> sub-threshold regime; (3) observability/Gramian dynamical note [§ theory, SHARED, framed as *complement* to
> Thm 2, not a re-derivation]; (4) transferability sentence [§Defenses, SHARED, domain-labeled moderation, n=280,
> POISON_FRAC=0.90 disclosed, "representation ≠ architecture"]; (5) Fricker epistemic-injustice analogue [GOV-ONLY,
> "analogue of" not "is", Birhane 2021 + Abebe 2020 cited as adjacent algorithmic-injustice work not Fricker-lineage].
> 6 new refs added (Cárdenas 2011, Mo–Sinopoli 2009, Biggio 2012, Steinhardt 2017, Siegmund 1985 shared; Birhane,
> Abebe gov). Both forks recompiled clean: 0 overfull/underfull, 0 undefined, 0 multiply-defined; Fricker verified
> gov-only (absent from `main.pdf`). Econ mechanism-design = FUTURE companion paper (Holmström framework mismatch).


Paper state (2026-07-10): `paper/main.pdf`, **15pp** (main text ~11pp + refs + appendix proofs), compiles clean
(0 overfull hboxes, 0 undefined refs), reproducibility green (`make verify` ALL REPRODUCED), 33 references (all
web-verified / attributed), novelty re-confirmed. Hardened by a 32-dimension self-peer-review loop
(`REVIEW_LOG.md`) + a generative-lens pass (`LENSES.md`).

Paper state (2026-07-11 update): reformatted to **IEEE SaTML two-column** (`\documentclass[conference]{IEEEtran}`,
vendored `IEEEtran.cls`), numbered `[1]` citations, Index Terms added. Now **12pp** (SaTML fork) / 13pp (gov fork),
both 0 undefined / 0 overfull. **49 references**, all web-verified — the recent high-risk cluster (12 arXiv-heavy
2023–2026 entries incl. chen2026/arXiv:2601.14971, wahdany2026/ICLR 2026) individually re-verified 2026-07-11:
**0 fabricated**; 2 metadata errors fixed (lafargue2025 three author initials; kulveit2025 preprint-title-vs-ICML-venue).
Figures relocated adjacent to first reference (were float-dumped on last pages). Discovery-scan clean-flag rate
corrected to per-domain (was satellite-only `<0.1%` stated domain-agnostically). **Build from repo ROOT**
(`make pdf` / `make pdf-gov`) — the makefile is not in `paper/`.

Paper state (2026-07-12 update): (1) External audit polish applied (section cross-refs `Sec. III`/`Sec. IX` via
`\ref`; FPR operands printed precise 2.04%→2.92% so the 43% recomputes; Fig 1 caption tier-jargon removed;
prevalence standardized to 1.17%; CI-vs-exact widened to ~1–2pp with both n=192 and n=47 intervals shown).
(2) Two proof steps tightened for referee-grade rigor (Prop 3 optional-stopping condition E[σ_k]<∞;
gov prop:patient corrected — expected detections T·δ(k), was falsely "finite as T→∞"). (3) **All 7 figures
regenerated at publication quality** (full column width, 300 dpi, 9pt true-size fonts, no in-plot titles,
consistent style; new `scripts/plot_moderation_dose.py` renders fig7 from JSON). Page count 12→13pp (gov 14pp) —
larger figures push the appendix tail to p13, within SaTML limits (body+refs ≤12pp; appendix unlimited).
(4) A presentation/impact review produced **`paper/IMPROVEMENT_ROADMAP.md`** (Tier 1/2/3 plan for a fresh
session — density/readability + reviewer-proofing; no correctness issues). Cleanup: removed tracked stray
`paper/fig7_moderation_dose.png`; c_moderation_dose.py no longer writes a figure (plot script owns it).

**Deferred cleanup (destructive — need explicit go):** `.git` history is ~317MB (large blobs committed over 60+
commits) — needs BFG/filter-repo history rewrite before a clean public clone. `_superseded/` (3MB) is tracked but
deprecated. `paper/references/` (224MB local, gitignored) is the cited-PDF archive — intentional, leave.

**NEW this session (scope-expansion greenlit + generative-lens pass) — FINAL honest state:**
- **§6 "The Curation Ratchet"** (in paper) — static harm is dynamic/compounding. Dynamical model + Proposition
  (extinction iff k(0)=0 & p<p*=1/(1+k'(0)); bounded floor if k(0)>0). **Self-corrected 3×** to get honest:
  resolved fixed point is a MODEST **~9% steady-state false-discard** (5× baseline, aggregate-invisible) — NOT the
  55–59% (those are r→0/φ→1 endpoints, `Fig 6`). Sharpest finding: that ~9% sits BELOW the probe threshold
  (τ≈0.35), so **the paper's own probe misses it** — an acute-vs-chronic defense gap. Experiments:
  c_ratchet_{competence,extinction,fixedpoint}. Loop-closure modeled, not run end-to-end.
- **Privacy-tension limitation** (in paper, §Limitations) — the probe needs protected-attribute processing that
  data-minimization restricts (same Access-Denied barrier, applied to our own defense).
- **Downstream-model rebuttal** (in paper, §2) — pre-empts "why not audit the trained model instead?" (needs the
  un-curated counterfactual; distinct harm; §6 shows the degradation is small + aggregate-invisible). Makes §6
  load-bearing for the core thesis → argues for KEEPING §6.
- **Ideated (in `LENSES.md`, main.tex untouched):** channel-capacity (unifies Prop1/Prop2/Thm2 as one I(θ;·));
  adverse-inference (self-enforcing governance: impossibility-as-enforcement); crypto-commitment (v2 defense
  closing probe-fingerprinting + poisoned-reference). + audience reframes (Akerlof, deceptive-alignment, RCT).

**OPEN decisions (need Aadi):** (1) **§6 keep / compress / revert** — my rec: KEEP (it's now honest + load-bearing
via the downstream rebuttal, though modest). (2) Propagate §6 + the channel-capacity framing to abstract/
contributions? (3) Develop any ideated lens (adverse-inference is the strongest for the governance/fellowship angle)?

## Primary target: IEEE SaTML 2027 — deadline ~Sept 29, 2026
Native scope (subpopulation backdoors, auditing, threat models); top security main-track; short-paper friendly.

## Pre-submission steps (only you can do these)
1. **Swap the venue class** — `\documentclass{article}` → the SaTML/IEEEtran style (one line, top of
   `main.tex`). Recompile with `make pdf`. (This also fixes the "ICLR 2025" header.)
2. **Run `/humanizer`** on the prose (your tone rule). It reads clean but AI-authored.
3. **Register + submit** by the SaTML deadline.

## Pre-PUBLICATION steps for the anonymized artifact repo (found in the 2026-07-10 loop — all need YOUR judgment)
These are why the repo is not yet publish-ready even though the paper is:
1. **Weights license** — `models/cloudscout/.../model70-final.ckpt` (5 MB) is **Du et al. 2024's** pretrained
   weights (now cited). Confirm their license permits redistribution before republishing them in your repo, or
   replace the vendored file with a download script.
2. **Strip `_superseded/`** — 8 debunked/stale figures (~2.9 MB) are git-TRACKED, so they publish. `git rm
   --cached -r _superseded/` + add to `.gitignore` before release (keeps your local copy).
3. **`.git` history is 240 MB** — clone bloat for a public artifact (from the HF model clone history). Consider a
   fresh/squashed history for the public repo.
4. **Source-level anonymization** — the submission PDF is correctly anonymized ("Anonymous authors"), but the
   real name is in `main.tex` line 25 (`\author{...}`, `\iclrfinalcopy`-guarded) and **git commits are authored
   under your real name**. For a repo published DURING double-blind review, strip `\author` and anonymize commit
   history. (Fine as-is post-decision.)
5. **Clean-clone `make verify`** — Tier-A/B proven locally; confirm on a fresh clone. Satellite full tier needs
   the ~62 GB restore (Tier-A/B already prove the theory/defense results).

## Optional strengthening (NOT reject-blockers; need resources you constrained)
- Satellite scale-up past n=47 → needs CloudSEN12+ (~250 GB; disk-tight).
- A multi-seed distilbert flagship (currently single-seed 42, honestly scoped + corroborated cross-model/domain).
- A second *real deployed* irreversible case study → needs external data.

## What this 2026-07-10 loop fixed (no action needed — done + committed)
- **Theory proofs (6):** β mislabeled "miss rate"→"detection probability"; `β^r`→`(1−β)^r` (×2); β/ε overload;
  Prop 2 retained-data step; Prop 1 statement/proof `a` mismatch. (β bugs were masked by the self-complementary
  β=0.5, survived a prior notation pass.)
- **Citations/attribution (9):** 3 fabricated-LOOKING refs (real papers, wrong metadata → fixed); **6
  used-but-uncited datasets/models** now cited — Civil Comments, DistilBERT, RouteLLM, MiniLM, KappaMask, Du et al.
- **Layout/PDF:** fixed the one overfull box; clean-room recompile verified.
- **Disclosure:** cross-domain certification-criteria heterogeneity now stated (satellite absolute vs
  moderation/routing relative-to-clean); satellite raw-vs-balanced detectability corrected (within seed noise).
- **Verified clean (no change needed):** all 8 experiment codes (no leakage), figures (byte-reproducible),
  abstract↔body↔JSON, contributions i–vi delivery, ethics, premise defense, novelty (fresh web scoop),
  measurement-vs-blindness coherence, terminology consistency, citation completeness, anonymization (in PDF).

## Adversarial review trajectory (2026-07-11) — self-peer-review loop
Ran hostile SaTML-PC simulations (default-reject) on the full paper, then re-reviewed the revision:
- **Round 1 (original):** WEAK REJECT (3/10). Top findings: R1 no moderation dose-response (single 0.8 point);
  R2 routing control confounded; R3 satellite certifier idealized; #1 reject reason = certifier-vs-pre-training-
  label-QA conflation.
- **Fixes applied (this session):** (a) threat-model paragraph splitting certifier from data-owner label-QA
  (reframes 80% poison as the visible upper end of a spectrum whose organic lower end evades both); (b) routing
  causal claim moved to Prop 1, control "corroborates" not "isolates"; (c) satellite certifier scoped; (d) NEW
  moderation dose-response experiment + Fig 7 (scope-lock overridden per operator) answering R1.
- **Round 2 (revision):** **BORDERLINE.** R1 RESOLVED (numbers verified exact vs JSON), R3 RESOLVED, #1 reason
  PARTIALLY resolved (organic-path argument sound; "spectrum" continuum asserted not fully demonstrated). Caught
  3 revision defects — abstract still said routing "isolates" (contradicted body), women 93%/73.5% adjacency,
  "flat-then-steep" overstated — **all 3 now fixed** (HEAD after bb28cb5).
- **Current state:** both forks compile 0/0/0 (SaTML 17pp, gov 19pp), catalog 48/48 parse OK.
- **Remaining OPTIONAL lever (Aadi's call, scope-expanding):** an intermediate organic-bias dose point to turn the
  "spectrum" argument from asserted into demonstrated. Reviewer rated its absence non-fatal at SaTML. Not run.

## FINAL STATE after the 2026-07-11 review campaign (13 adversarial passes + 3 new experiments)
- **Both forks compile 0/0/0** (0 overfull/underfull, 0 undefined, 0 multiply-defined): SaTML `main.pdf` 18pp,
  governance `main_gov.pdf` 19pp. Reproducibility: `make verify` = ALL REPRODUCED (Tier-A); catalog 50/50 parse OK.
- **Adversarial score trajectory:** hostile SaTML sim 3/10 weak-reject -> BORDERLINE after fixes; every actionable
  finding addressed incl. the moderation dose-response (Fig 7) that answered the #1 reject reason.
- **Spectrum gap CLOSED + demonstrated** (2 new experiments): c_spectrum (targeted flip = visible upper end,
  cross-slice label-QA catches from ~5%) + c_systemic (systemic-organic bias = lower end that EVADES BOTH: 18%
  probe harm at 20% bias, certified, no outlier -- rarity keeps it certified). Threat-model paragraph now backs
  the claim with runs.
- **New experiments this session:** c_moderation_dose (nested-draw corrected after a code audit caught a MAJOR
  bug), c_spectrum, c_systemic. All in the catalog.
- **Proofs:** independently re-verified -- 4 sound, 2 gaps closed (prop:ratchet convergence, prop:patient finite-k),
  0 errors, beta-semantics intact.
- **Governance fork:** hostile policy review deflated 4 overreaches (C1 FATAL "first formal account" -> "under
  physical evidence destruction"; Kulveit "sub-mechanism" -> "candidate channel"; DP-dual -> analogy; Balkin
  hedged). **Fricker paragraph CUT** (Aadi's call) + its refs removed.
- **Remaining = EXECUTION only (Aadi):** swap `\documentclass` to SaTML/IEEEtran, run `/humanizer`, register+submit
  by ~Sep 29 2026. Pre-publication repo hygiene items unchanged (weights license, strip `_superseded/`, anonymize).
