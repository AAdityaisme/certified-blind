# Review log — "Certified Blind" (self-peer-review loop, 2026-07-09/10)

Exhaustive multi-angle peer review. ~56 issues found + fixed, all committed. Every page read, every headline
number re-verified against `results/*.json`, reproducibility confirmed, novelty confirmed.

## Angles run (distinct lenses)
1. **Numerical** — 12 real errors: wrong seed-FDR range (0.79–0.96 → 0.32–0.79), prevalence contradiction
   (1.7%→1.17%, 60× is finite-sample not 1/p=85), h* non-monotone in k, unbacked "under-representation ~3×",
   discovery flags 3 slices not 1, +minor.
2. **Logic / proofs** — 8: Prop 1 observed-R_S (not worst-case), Prop 2 Wald + supermartingale finiteness,
   conditional-independence stated, +misc. (One self-introduced regression caught next pass.)
3. **Verify-fixes** — 7: all added numbers re-verified correct; Table 1 footprint 0.73→0.92pp (backdoor not
   KappaMask), Fig 5 caption, +minor.
4. **Reader-experience** — over-defensiveness from revisions → cut: confident §2 reframe, footnoted the model
   parenthetical + non-monotonicity, de-winced n=47, de-apologized §4 opener.
5. **Domain-expert + figures** — 11: exact CI [89.6,96.4], KappaMask FDR denominator (expert labels), RouteLLM
   label-mapping, 6-point dose sweep, civil_comments sub-sampling, softened distilbert curation-class overclaim,
   ∆FPR-ratio clarified, fig4 circular-points note, fig1 retitled. (Caught + rejected a false positive: 5/5
   certified is correct per t3e_dilution; reviewer read the wrong file.)
6. **Statistical rigor** — selectivity ratio significance via non-overlapping CIs; discovery-scan family-wise
   false-flag control (8 strata, each clean flag <0.1%).
7. **Thesis-attack** — recoverable-control (routing) is confounded with task; controlled claim is within-domain.
8. **Reproducibility re-run** — flagship 93% + 4.7×-nearest bit-identical; mean-ratios (~14×/~69×) have mild
   fine-tune nondeterminism → softened, validates leading with nearest. `make verify` green.
9. **Notation** — consistent (n/N, C/c, β, h). Clean.
10. **Scoop-check (web)** — not scooped; closest work cited/distinguished. 2 adjacent 2025-26 papers flagged to
    verify (arXiv:2605.23701 metadata-predictability; 2601.03087 active fairness auditing).
11. **Defense-attack** — added 3 adaptive attacks to Limitations (τ-adaptation, panel-poisoning, split-harm).
12. **Number-consistency sweep + typography** — residual 14.3×→4.7× in §4; 0 overfull boxes.
13. **Full visual read** (every page) — caught residual "undetectable"→"unidentifiable" drift in Win condition.

## Verified-clean state
`make verify` ALL REPRODUCED · 41 results parse · 0 residual bad values · headline numbers consistent across
abstract/body/table/captions · proofs render + rigorous · references complete · 12pp compiles clean · no
edit-induced breakage.

## Later dimensions (opened after the 13 above; ~66 fixes total)
14. **Holistic final-version read** — 6 emergent cross-fix artifacts (future-work claimed an already-proved
    theorem; Sec-7/8 misref; stale Sec-4 pointer; orphaned Thm 1; abstract 14×/near) — none catchable by
    piecemeal passes that each saw a partial version.
15. **Experiment-code audit** (paper-vs-implementation, no prior pass touched code) — found: moderation slice
    is keyword-matching not "crowd-annotated" (paper fixed); fingerprinting tests content- not channel/timing-
    indistinguishability (scoped). Verified clean: satellite (ROI-leakage guard, correct slice/FDR/cert),
    probe (hypergeometric), adaptive, selectivity, label-free, annotation-bias. No logic bugs, no leakage.
16. **Infra** — `cloudsen12` `land_cover==70`=snow confirmed against ESA WorldCover codes + the actual metadata.
17. **Cross-experiment consistency** — shared quantities agree (TF-IDF clean-acc identical across 2 experiments;
    snow 1.17% across 2; Manski oracle-in-bounds empirically re-confirms Prop 1).
18. **Artifact integrity** — archived 19 stale/debunked result files (incl. pre-audit routing artifacts) + 8
    stale root figures; confirmed the real `paper/figures/*.png` are tracked (repro works); deprecated DRAFT.md.
19. **Repo security** — no secrets/keys/.env/PII committed; no file bloat. Safe to publish.

## Later dimensions (cert-bar + robustness veins; ~78 fixes total)
20. **Cert-bar / metric-detectability** — satellite POISON raw-acc (0.808) sits 1.7pp below CLEAN (0.825), which
    looked like a detectable aggregate cost. Verified against 5-seed variance: poison seeds span 6.2pp (std 2.0pp),
    so the 1.7pp gap is *within* seed noise → NOT reliably detectable (a bar tight enough to flag it also rejects
    unlucky clean seeds); balanced accuracy doesn't separate them either (0.807 vs 0.805). Net: satellite backdoor
    is accuracy-invisible on BOTH metrics, matching the representative-certifier result (2.1pp < 3pp seed noise).
    *This corrected a mid-loop over-hedge I'd introduced (three iterations: "detectable"→"metric-dependent"→"within
    seed noise, invisible"); the original paper claim was right — my intermediate caveat compared point estimates
    while ignoring seed variance.* §4 flagship framing now rests on metadata-opaqueness (Prop 2), not footprint size.
21. **Flagship robustness / spillover** — (a) 93% distilbert result is at a single poison_frac (0.8); no single-model
    moderation dose-response, but mechanism dose-dependence is shown on satellite (t3b, flat-until-25%-then-steep)
    and multiple moderation poison points exist across experiments — adequate, not worth a 6× distilbert sweep.
    (b) Reconciled two christian-collateral numbers: c_selectivity ΔFPR-ratio (4.7× vs nearest) vs c_transformer raw
    multiplier (8.8×) — same data, different denominators, not contradictory. Absolute spillover (christian 2.5→22%,
    jewish 5.6→22%) IS disclosed (§5 "~19pp… religion-adjacent… mild term-correlation spillover" + Fig 5 caption).
    Consistent with the identity-agnostic rare-content-slice mechanism (neutral-control "water"). No error.

22. **Theory-proof line-audit** (Prop 2, Thm 1, Thm 2 — never line-audited during THIS loop; highest-stakes, least-
    recently-checked surface). Five genuine findings, none catchable by prose/number passes:
    - **Prop 2 retained-data channel**: proof justified $\Pr[Y_{t+1}{=}1\mid\mathcal F_t]{=}p$ only for *past labels*
      ("uninformative"), silently omitting why the *retained data* (3rd component of $\mathcal F_t$) drops out. It
      follows from the i.i.d.\ draw (candidate ⊥ other candidates | M) — added explicitly. No fatal gap, closed the
      one under-justified step in the novelty-crux proof.
    - **β = "detection miss rate" → "detection probability"** (§6(ii)): the Thm 1 *formula* defines β as detection
      probability ($\Pr[\mathrm{Bin}\ge m]\le\beta$; verified: $h^*(10,.35,.25){=}.26 \Leftarrow \Pr[\mathrm{Bin}(10,.26)\ge4]{\approx}.248$),
      but prose called it the miss rate (=1−β). **Masked by the self-complementary headline β=0.5** — survived the
      dedicated notation pass (dim 9, which declared β "clean").
    - **evade-all prob β^r → (1−β)^r** — same complement error, TWO occurrences (§6 line 409 + Limitations line 477);
      the 2nd caught only by consistency-sweeping the 1st fix.
    - **β symbol overload**: β = detection probability (Thm 1) vs test error (Thm 2) — disambiguated Thm 2's error to ε.
    - **Prop 1 statement/proof mismatch on $a$**: statement defined $a$ as "retained inputs that lie in S" but the
      proof (and $\theta=P(\mathrm{DISCARD}\mid\text{should-keep},S)$, which conditions on should-keep AND S) require
      $a$ = "should-keep members of S" — else $R_S=a(1-q)$ overcounts. Fixed statement to match; S need not be purely
      should-keep. Math itself airtight (θ monotone in $D_S$, both bounds attained, θ=0 always in set → uncertifiable).
    - Verified airtight: Thm 1 monotonicity/uniqueness (g strictly ↑, m∈[1,k]); Thm 2 Chernoff lower bound, Cramér
      tilted-measure optimality at τ*, and Θ(k/p) uniform-sampling necessity (beats the 1/p² aggregate strategy).
    All four theoretical objects (Prop 1, Thm 1, Thm 2, Prop 2) now line-audited — 6 real findings total.
23. **Figure numerical fidelity** (plotted values, not just captions — never checked before). Both generators
    (`scripts/make_figures.py` fig1–4, `experiments/plot_selectivity.py` fig5) read ALL values from `results/*.json`
    — no hardcoding. fig4/fig5 PNGs had mtimes OLDER than their source JSONs (staleness suspicion), but regeneration
    is BYTE-IDENTICAL (md5 unchanged) → JSONs were re-run deterministically, values never changed, figures current.
    Paper↔JSON↔figure chain closed (fig1 POISON: JSON 0.8082/0.7872 ↔ paper "0.808"/"79%" exact). fig4's systematic
    p·h OVERprediction (poison points below y=x; T3H 0.921→0.383) IS disclosed ("~0.2pp discard-rate, ~0.5pp
    accuracy-dent"; max_abs_err 0.538pp confirms). Clean — no fix.
24. **PDF end-to-end read** — 13pp, 0 undefined refs, 0 warnings; fixed the ONE overfull box (Table 1, 9.23pt into
    margin → tabcolsep 6→4pt). Visually verified in the compiled PDF that all math edits render correctly (ε on
    p.13, Prop 2 retained-data clause p.13, β "detection probability (miss/evasion 1−β)" + (1−β)^r p.7, ε/β
    disambiguation p.8).
25. **Citation integrity** (HIGH-STAKES — never checked; fabricated-looking cites are desk-reject-grade). Refs
    23–25 had the hallucination signature — NO authors + paraphrased/generic titles, unlike the other 22. Web-
    verified all three arXiv IDs: they ARE real papers, but cited with WRONG titles + missing authors. Corrected to
    exact metadata: 23=Koren "The Gatekeeper Effect…Hiring Processes" (2312.17167); 24=Truong…Menczer (10 authors)
    "Audit of Takedown Delays…" (2502.08841); 25=Chen/Liu/Fayek "Fine-Grained Traceability for Transparent ML
    Pipelines" WWW2026 (2601.14971). §2 inline characterizations (screening-incentives / reversible-takedown /
    record-everything provenance) are substantively CORRECT — defect was purely bibliographic. Also spot-verified
    refs 18 (Zhu et al., Consistent Range Approximation) + 19 (Zaccour/Binns/Rocher, Access Denied CHI'25) = exact.
    The classical refs (Manski, Chernoff, Cover&Thomas, Horowitz-Manski, Miao, Lakkaraju, BadNets, Turner) are known-real.

**Revised convergence note (2026-07-10):** my earlier "we've converged" call was PREMATURE — it was made before
line-auditing the proofs, which then yielded 5 real fixes. Lesson: "converged on surface X" ≠ "converged." The
theory section was the genuinely under-audited surface. NOW the proofs are line-verified too. Remaining highest-
leverage items are external/user-owned (venue swap to SaTML, /humanizer, publish repo).

26. **Cross-domain consistency + structural/steelman lenses.**
    - **FINDING — certification-criteria heterogeneity**: the 3 domains use DIFFERENT cert bars (satellite=absolute
      acc≥0.80; moderation=within-tolerance-of-clean Δacc≤.01/ΔFPR≤.02; routing=Δacc≤.01/Δrecall≤.03). Only the
      satellite bar was previously disclosed as author-set. Extended Limitations to state the criteria are
      domain-appropriate (not uniform) AND honestly note the satellite's absolute bar is the more permissive choice
      (a relative bar at clean 0.825 would reject the 0.808 poison) → preempts the "tuned to pass" objection.
    - CLEAN — measurement-vs-blindness coherence: paper explicitly distinguishes observable accuracy (certifier
      computes on representative sample) from per-slice FDR (requires the discarded slice's ground truth = the oracle
      the certifier lacks; §4 line 231-233). The "you measured it so it's not destroyed" objection is answered.
    - CLEAN — flagship single-seed scoping: distilbert 93% is seed-42-only, and the paper is honest about it
      ("reproduces across re-runs" = same-seed reproducibility, not multi-seed; corroborated by TF-IDF cross-model +
      satellite 5-seed + non-overlapping CIs). No overclaim.
    - CLEAN (strength) — premise defense: §3 grounds irreversibility in real pipelines (C4/RefinedWeb curation,
      onboard/on-device triage) and preemptively concedes logged DSA-Art.17 moderation as the recoverable case. The
      strongest "irreversibility is artificial" steelman objection fails against the paper.

27. **Novelty scoop re-check (fresh web) + load-bearing code audit** — both CLEAN.
    - Scoop (attack + defense sides, web): novelty HOLDS. Closest works all cited+distinguished (Jagielski
      subpopulation poisoning = retained model; Access Denied / Sequential Fairness Auditing = access-limited, data
      still exists). Nothing addresses unidentifiability from physical DESTRUCTION. The #1 accept/reject factor confirmed.
    - c_probe_fingerprint.py (backs Thm 1 assumption-(i) "blind injection achievable"): method sound — blind probe =
      two DISJOINT i.i.d. draws from organic pool (AUC 0.501 = genuine indistinguishability, not overlap artifact);
      out-of-fold discriminator (cross_val_predict, no self-leakage); naive probe fairly distinguishable by explicit-
      term density (AUC 0.742, 66% leakage). JSON matches paper (0.50/0.74/66%) exactly. No rigging, no leakage.

**Convergence (evidenced, 2026-07-10, ~15 real fixes this continuation):** finding rate now ~0 on fresh lenses.
Last ~6 lenses clean (measurement-coherence, flagship-scoping, premise-defense, scoop×2, probe-code). Surfaces that
yielded fixes (proofs, citations, cross-domain bars) are now audited; re-examined + newly-examined surfaces return
clean/strong. The premise (deepest structural risk) is a strength; novelty is intact. Reviewer lenses exhausted.

## Remaining (external, not autonomously fixable)
- Venue: all 5 original reviewers said **SaTML**, not ICLR (framing fits security venue; "standard-math +
  novel-setting + strong defense" is a strength there). Current draft is ICLR-formatted.
- Verify the 2 adjacent papers above before submission.
- Publish the anonymized repo; run `/humanizer`.

28. **Routing-control code audit** (r_embed_router.py, backs the recoverable-control / contribution-iv claim) — CLEAN.
    MiniLM embeddings are per-example independent (embed-then-split ≠ leakage); poison flips 90% of slice-premium
    labels; THR calibrated on the CLEAN router and reused for poison (correct: certifier calibrates on honest model)
    — note THR uses test-score quantile not a val split, but applied symmetrically so it doesn't confound the
    relative clean-vs-poison drop. JSON matches Table 1 exactly (medical premium-recall 0.3208→0.1509 = "0.32→0.15";
    agg 0.314→0.312 within tolerance; certified+confirms True). ALL experiment code now audited (satellite, moderation
    flagship, neutral-control, selectivity, smart-cert, probe-fingerprint, routing, annotation-bias) — all clean.

29. **Publication / artifact-readiness lens** (repo-level, never examined — "release verification" that turned up a
    real finding). Clean-room recompile: 13pp, 0 bad boxes, 0 undefined, fully reproducible from scratch.
    - **FINDING (integrity) — uncited third-party model weights**: fig1 + t1b's "real CloudScout" numbers (acc 0.808,
      2% snow FDR) are computed from Du et al. 2024's publicly released pretrained weights
      (github.com/andrewpatrickdu/domain-adaptation-cloud-detection), which was NOT in the references. The
      architecture cite (Giuffrida CloudScout) was present but the WEIGHTS source was missing. Added Du et al. 2024
      to references + in-text attribution in §4. (Using a third-party pretrained model to produce reported numbers
      without citing it is a genuine integrity gap.)
    - Rebuilt+committed main.pdf (gitignore explicitly keeps it as the deliverable); no secrets/.env/keys tracked.
    - **FLAGGED for user decision before publishing the anonymized repo** (NOT auto-changed — publication-strategy +
      no-destructive-edits rule): (a) `_superseded/` (8 debunked figures, ~2.9MB) is git-TRACKED, so archiving to it
      doesn't stop it publishing — gitignore/`git rm --cached` before release; (b) the 5MB Du-et-al checkpoint is
      redistributed in-repo — confirm their license permits it (README credits the source, good); (c) .git history is
      240MB (clone bloat) — consider a squash/fresh-history for the public artifact.

**Lesson reinforced:** "reviewer lenses exhausted" was premature AGAIN — the repo/publication surface (distinct from
the paper's content) held a real integrity finding. Pattern held the entire loop: new *surfaces* yield fixes.

30. **Systematic dataset/model attribution audit** (triggered by the Du et al. finding in dim 29 — if the CloudScout
    weights were used-but-uncited, check ALL third-party assets). Found the gap was SYSTEMATIC: **6 used-but-uncited
    assets** producing core results, now all cited (refs + inline, metadata web-verified):
    - Civil Comments (Borkan et al. 2019, arXiv:1903.04561) — the data behind the 93% moderation flagship.
    - DistilBERT (Sanh et al. 2019, arXiv:1910.01108) — the flagship model.
    - RouteLLM (Ong et al. 2024, arXiv:2406.18665) — the entire routing domain / gpt4_judge_battles benchmark.
    - Sentence-BERT / all-MiniLM-L6-v2 (Reimers & Gurevych, EMNLP 2019) — the routing encoder.
    - KappaMask (Domnich et al., Remote Sensing 13(20):4100, 2021) — fig1's 62.6% comparison model.
    - (+ Du et al. 2024 from dim 29 — the CloudScout onboard weights.)
    Ref list 25→31; paper 13→14pp (refs/appendix uncounted at SaTML/ICLR); 0 bad boxes. Missing dataset/model
    citations are a common revision/desk-reject trigger — this was the single largest integrity cluster of the loop.

**Meta (3rd premature-exhaustion correction):** the attribution surface — orthogonal to correctness/positioning —
held 6 real gaps. Every time I declared lenses exhausted, a NEW surface (proofs→citations→repo→attribution) held
findings. The paper's *arguments* are sound and well-audited; the *scholarly-apparatus* surface was the weak one.

31. **Anonymization + citation-completeness (apparatus follow-ups)** — both CLEAN.
    - Anonymization: compiled PDF page 1 renders "Anonymous authors" (NOT the real name); \iclrfinalcopy correctly
      commented → ICLR class auto-anonymizes. No leak in the submission PDF. **FLAGGED (pre-publication, user call):**
      real name IS in main.tex source (line 25, \iclrfinalcopy-guarded) and git commits are authored under the real
      name — both de-anonymize a repo published DURING review. Strip \author + squash/anonymize history before a
      review-time public release (fine post-decision).
    - Citation completeness: no dangling citations (all 21 body author-cites resolve to refs) and no orphan refs
      (Neural Cleanse/ABS cited by method name L125; Aybar by "CloudSEN12"; Zhu/Zaccour/Koren/Truong/Chen by arXiv
      ID; Chernoff/Cover&Thomas in appendix proofs; rest by author). List↔body fully consistent, now 31 refs.

**State after the apparatus sweep:** content surfaces (proofs/numbers/code/figures/premise/novelty) audited+clean;
apparatus surfaces (citations/attribution/completeness/anonymization/reproducibility/layout) audited — the
attribution cluster (dim 29-30, 6 fixes) was the last substantive find; follow-ups clean. Remaining = 5 user-only
pre-publication calls (weights license, strip _superseded/, .git bloat, source-name, git-history anonymization).

32. **Build-system / data-free-tier verification** — CLEAN. Makefile targets `verify`/`pdf`/`restore` all exist;
    `make verify` → verify_repro.py. Verified the paper's "data-free tier" claim (§ line 228/620) is TRUE: all 5
    verify experiments (minimax_bound, cert_bandwidth, defense_efficiency, probe_lower_bound, verify_bound) have
    ZERO data dependencies (no data/ reads, no civil/cloudsen/routellm loaders, no .npy/.parquet) — purely analytic,
    so a fresh clone without the 62GB data runs `make verify` successfully. Artifact reproducibility claims accurate.

---

# IEEE-REFORMAT-ERA CAMPAIGN (2026-07-11 → 2026-07-12)

Continuation of the self-peer-review loop AFTER the ICLR→IEEE/SaTML two-column reformat, plus post-"stop" audit
work. Loop directive ("keep going until I say stop") ran through many rounds; Aadi typed "okay stop" on
2026-07-12, then requested targeted work. Every fix rebuilt BOTH forks (0 undefined / 0 overfull) from repo ROOT.
Raw commit trail: 233144c → 0cd6a01. This is the narrative.

**Reformat baseline (this era):** swapped to `\documentclass[conference]{IEEEtran}` (vendored IEEEtran.cls V1.8b),
two-column, numbered [N] citations (thebibliography + 49 \bibitem, author-year → \cite; narrative name-drops like
"Wald showed"/"Chernoff information"/"Manski partial identification" correctly kept as TEXT, not cited), table
captions moved ABOVE, ran avoid-ai-writing nuanced pass (em-dashes 169→110). Body fits two-column.

33. **IEEE numbered-citation conversion — VERIFIED (not just built).** Agent-converted ~100 cites; watcher
    re-verified 0 undefined / 0 uncited, added \cite for CloudSEN12(aybar2022)+CloudScout(giuffrida2020), and
    confirmed the subtle part: concept-labels (Wald/Chernoff/Manski) stayed prose, no awkward "\cite{} showed"
    subjects. Stylistically correct, not just resolvable.

34. **Figure float-dump — FIXED.** All 7 figures were defined in an end-block before the bibliography, so in
    two-column they floated onto the last 3 pages (10-12), far from their references. Relocated each adjacent to
    its first \ref → figures now pp4-9. (Delegated to an agent with hard build-gates, watcher-verified.)

35. **Cross-surface number audit — 1 fix + 35 verified.** Skeptical-statistician pass over abstract/intro/
    Table I/captions/body vs results/*.json. Found: discovery-scan clean-flag rate "<0.1%" stated
    domain-agnostically but true ONLY for satellite (0.04%); the moderation scan's clean strata reach 2.55%, and
    the example right after it IS moderation. Restated per-domain (<0.1% satellite / <2.6% moderation, zero false
    discoveries both — both JSONs confirm empty false-discovery lists). 35+ headline numbers verified consistent +
    data-traceable (93%/CI, 79%/CI, 4.7×/14×/69×, 58.6%/59.4%, ~9% ratchet, CUSUM ARL/EDD, etc.).

36. **Index Terms added.** IEEE conference format wants them; both forks lacked. Added fork-aware \IEEEkeywords
    (security/ML terms for SaTML, governance terms for gov).

37. **BUILD-LOCATION BUG — the sharpest process catch.** The makefile is in the repo ROOT, not paper/. I had been
    running `make pdf` from inside paper/, where make silently no-ops → I was verifying STALE PDFs. Surfaced when
    the Index-Terms edit "didn't render" (the source was correct; the PDF was pre-edit). Isolated via minimal test
    compiles, rebuilt correctly from root, committed the true PDFs. Recorded the gotcha to memory + docs.

38. **Reference web-verification — 0 fabricated, 2 metadata fixes.** Verified all 12 recent/high-risk refs
    (2023-2026 arXiv-heavy, incl. scary-looking chen2026/arXiv:2601.14971 WWW'26 + wahdany2026/ICLR'26 — both
    REAL). Two errors: kulveit2025 cited the arXiv-preprint title against an "ICML" venue label (ICML proceedings
    title differs → reattributed to arXiv w/ ICML-position note); lafargue2025 had THREE wrong author initials
    (researcher agent's report was self-contradictory, flagged only 1 — direct arXiv WebFetch caught all three:
    E→A. Laurindo Monteiro, B→E. Claeys, A→L. Risser). Discipline: refused to edit names on a contradictory
    agent report; verified against the primary source.

39. **Theorem cross-reference audit + abbreviation.** From the .aux: all 16 theorem/prop cross-refs semantically
    correct (unidentifiability→Prop 1, Ω(k/p)→Prop 3, stealth-ceiling→Thm 1, lower-bound→Thm 2); 0 hardcoded
    internal numbers (the one literal "Thm. 11.9" is an external Cover&Thomas cite); Prop 2 not orphaned. Fixed a
    consistency defect: theorem refs were split (Thm~ ×7 / Thm.~ ×1) while props were uniformly Prop.~ →
    standardized all to Thm.~.

40. **Appendix proofs — fresh adversarial read + 2 rigor fixes (highest-stakes surface).** All five main-fork
    results proved + correct (Manski partial-ID; binomial-monotonicity stealth ceiling; Chernoff-information
    tilted-law equal-KL optimality; martingale/optional-stopping opaqueness; ratchet IVT fixed-point). Two
    tightenings: (a) Prop 3 approximate-opaqueness justified optional stopping via "a.s. finite" but the rigorous
    condition (stated in the exact case) is E[σ_k]<∞ — made explicit via NegBin domination. (b) **gov prop:patient
    contained a real MATH ERROR** — "the expected number of detections stays finite even as T→∞" is false for
    fixed probe budget (expected detections = T·δ(k) → ∞); corrected to the true fixed-horizon claim (T·δ(k)→0 as
    k→∞). Core evasion/compounding result unchanged. This is the "something we missed" the loop was hunting — a
    plausible-sounding false statement that survived earlier audits because it READS right.

--- (Aadi typed "okay stop" here; loop ended. Targeted work follows.) ---

41. **External audit polish — 6 items.** Section cross-refs (leftover arabic Sec.3/Sec.9 → \ref rendering
    Sec. III/Sec. IX; added labels to Threat-Model + Future-Work sections). FPR footnote printed "2.0%→2.9%
    (43%)" inviting a naive 2.9/2.0=45%; the 43% is correct from raw (0.0204→0.0292=43.1%) → printed precise
    operands 2.04%→2.92% so it recomputes. Fig 1 caption tier-jargon (T2/T3H) → self-contained wording.
    Prevalence standardized 1.2%→1.17% (the exact value used in the math). "within ~1pp of exact" was a general
    claim the n=47 satellite (1.7pp) contradicted → widened to "~1-2pp, tightest at larger n", now shows both
    n=192 and n=47 intervals.

42. **Figures regenerated at publication quality (Aadi: "figures too small" + "overall polish").** Root cause:
    6×4in plots downscaled to .55-.72 column → ~5pt effective fonts, 150dpi, inconsistent styling across 4
    generator scripts, redundant in-plot titles. Fix (STYLING ONLY — 0 number changes, all scripts read the same
    JSON): shared publication style (serif, 9pt true-size fonts, 300dpi, drawn at final column width so no
    downscaling, in-plot titles dropped since the caption is the title), fig6 gets compact (a)/(b) labels, widened
    to \linewidth/\textwidth. New scripts/plot_moderation_dose.py renders fig7 from JSON (no experiment re-run).
    Visually verified figs 1/2/3/5/6 + pages 4/6 in context. Page 12→13pp (gov 14pp): bigger figures push the
    appendix-proof tail to p13 — WITHIN SaTML limits (page limit = body; refs+appendix unlimited; body+refs ≤12pp).

43. **External presentation/impact review → paper/IMPROVEMENT_ROADMAP.md.** No correctness issues (consistent
    with all prior audits) — pure "make it land" layer. Watcher assessment ranked it Tier 1 (paragraph-break
    §II/§VIII, em-dash trim, assumption-ledger table, compress satellite hedging, small polish) / Tier 2
    (defense Algorithm box, multi-seed CIs [compute-gated], abstract restructure) / Tier 3 pushback (keep the
    three Θ(k/p) framings — breadth is a strength for a theory venue; Fig-1-to-appendix only as a swap). Plus the
    **CloudSEN12+ ~250GB satellite scale-up** track (Aadi cleared disk 2026-07-12 — kills the n=47 limitation,
    unlocks multi-seed satellite CIs). To be executed in a FRESH session (this transcript hit 42MB).

44. **Cleanup + logging.** Removed tracked stray paper/fig7_moderation_dose.png (orphan wrong path);
    c_moderation_dose.py no longer writes a figure. Updated SUBMISSION_CHECKLIST + memory + this log + a paste-ready
    handoff. Deferred (destructive, need explicit go): .git ~317MB history bloat; _superseded/ 3MB tracked.

**State after this era:** paper is presentation-polished + figure-upgraded + proof-rigor-tightened, both forks
0/0 (SaTML 13pp, gov 14pp), references web-verified. All remaining work is in IMPROVEMENT_ROADMAP.md (prose
density, reviewer-proofing, and the 250GB satellite scale-up) — for a fresh session.
