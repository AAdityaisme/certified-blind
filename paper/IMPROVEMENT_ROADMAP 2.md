# Improvement Roadmap — "Certified Blind"

Created 2026-07-12 from an external presentation/impact review (no correctness issues found — this is the
"make it land" layer). Ordered by payoff-per-effort with the watcher's assessment and pushback. Execute in a
FRESH session (this session's transcript is >42MB; re-reading it per edit is wasteful).

## Current paper state (as of 2026-07-12)
- `paper/main.tex` → `main.pdf` (SaTML, default) **13pp**; `main_gov.pdf` (governance, `make pdf-gov`) **14pp**.
- Both forks: 0 undefined refs, 0 overfull hboxes. Build from repo ROOT (`make pdf` / `make pdf-gov`) — the
  makefile is NOT in `paper/`.
- IEEE two-column (`\documentclass[conference]{IEEEtran}`, vendored `IEEEtran.cls`), numbered `[N]` citations,
  Index Terms present, 49 references (all web-verified, 0 fabricated).
- Figures were regenerated at publication quality 2026-07-12 (full column width, 300 dpi, 9pt true-size fonts,
  no in-plot titles). Generators: `scripts/make_figures.py` (figs 1–4), `experiments/plot_selectivity.py` (fig5),
  `experiments/plot_ratchet.py` (fig6), `scripts/plot_moderation_dose.py` (fig7, reads JSON — no experiment
  re-run). Larger figures pushed the appendix-proof tail to a 13th page; this is within SaTML limits (the page
  limit covers the body; references + appendices are unlimited, and body+refs fit ≤12pp).
- Abstract word counts: security 364w, governance 242w. Bodies ~11.2k / ~12.0k words. **Density is the #1
  presentation risk.**

## Metrics for reference
- Security abstract 364w (IEEE norm 150–250). Governance abstract 242w (better model: image → result → remedy).
- Related Work (§II) and Limitations (§VIII) are the densest sections: >2 em-dashes/sentence, wall-of-text.

---

## TIER 1 — do first (high ROI, low risk, no compute, minimal space cost)
1. **Paragraph-break §II Related Work + §VIII Limitations.** Bold lead-ins already exist ("Backdoor and
   subpopulation attacks", "Partial identification…") — give each its own paragraph. Pure readability win.
2. **Em-dash trim in §II + §VIII.** Continuation of the avoid-ai-writing pass (whole paper went 169→110; these
   two sections stayed dense). Rule: ≤1 em-dash pair/sentence; convert half the parenthetical asides to sentences.
3. **Assumption ledger table** (best single reviewer-proofing move). Consolidate the scattered assumptions
   (§III, §VII-b, §VIII) into a "tested / assumed / out-of-scope" table. Tested = probe content-indistinguishability
   (AUC≈0.50); assumed = channel/timing blindness; + the three that bound Thm. 1. Showcases the paper's honesty,
   kills the "you assumed the hard part" critique.
4. **Compress satellite hedging.** Currently qualified in ~5 places (§IV, §V, §VIII, fig captions:
   conservative / not-the-flagship / small-n / metadata-predictable / 2-of-5-seeds). Collapse to ONE role
   statement ("flight-hardware proof of the certified-harm gap; not the unidentifiability claim") + one
   limitations line. Repetition currently reads as defensiveness about the strongest visual.
5. **Small polish:**
   - State the distilbert/TF-IDF proxy argument ONCE in setup (currently "the class used to curate training
     corpora" / "increasingly used in curation pipelines" recurs ~4× as a hedge).
   - Fig. 4 caption: move the two-way ratio definition (ΔFPR-based; nearest exact, mean varies) to the body.
   - Table I "Min probe / discovery" row: add units in the header (mixes `k=10` and `120 labels`).
   - Security intro: add a one-sentence venue "so what" ("a new attack surface") — the gov version does this, the
     security version buries it.
   - Artifact paragraph: add one line "all headline numbers are golden values in `results/*.json`; see
     `make verify`" (closes prose↔repro loop; the FPR is now printed 2.04%→2.92%).

## TIER 2 — high impact, real cost (needs space budgeting and/or compute)
6. **Boxed defense Algorithm** (best framing upgrade). The contribution IS the defense but it lives in prose.
   Add a one-column `algorithm` box: "Auditability-preserving certification: (1) pre-commit size-k probe per
   stratum; (2) flag if observed FDR ≥ τ; (3) discovery scan over protected set; …". A practitioner screenshots
   this. Needs `algorithm`/`algorithmic` package. COSTS space.
7. **Multi-seed CIs on Figs 3, 5, 6** (biggest RIGOR lever — single-seed is the most attackable surface).
   Limitations already concedes dose/spectrum/systemic/ratchet are single-seed TF-IDF. Re-run at {7,123,2024,99}
   (already used elsewhere) and add shaded CIs. **GATED ON COMPUTE — check the scripts take seeds cleanly and are
   cheap before promising.** Even 3 seeds turns "anecdote" → "trend".
8. **Abstract restructure** (security 364→~250, lead with the claim). The RESTRUCTURE is the win, not the raw
   cut: lead with the one-sentence thesis ("an irreversible gatekeeper's false-discard rate is unidentifiable
   from retained data"), then the headline number, then the remedy; move the 4.7×/14×/69× selectivity breakdown
   and the Prop-3 label-cost aside into the body. End on the unidentifiability result (stronger mic-drop than the
   current "capping stealthy harm near the audit threshold"). NOTE: Aadi earlier said preserve density/complex
   terms — restructuring keeps substance; trim to ~250, not 200. Confirm with him.

## TIER 2+ — SATELLITE SCALE-UP (CloudSEN12+, ~250 GB) — NOW UNBLOCKED (Aadi cleared disk 2026-07-12)
This is the highest-value EMPIRICAL upgrade available and directly kills the paper's **single most-cited
limitation**: the satellite clear-snow slice is n=47. Aadi has decided to "go big" and download the full data.
- **What to download:** CloudSEN12+ — the extended/larger release (official: `cloudsen12.github.io`; also on
  Huggingface `tacofoundation/cloudsen12` and Zenodo). ~250 GB is the full high-res set; the current repo has
  only the CloudSEN12-high train subset (8490 patches → snow n≈47–99). Confirm exact CloudSEN12+ access/URL from
  the site before pulling; wire it into `data/download.py` / `make restore` (currently Tier-C ≈62 GB — this is a
  new, larger tier). Update `REPRODUCE.md` Tier-C size + provenance.
- **Why it matters:** more clear-snow patches take n=47 → hundreds/thousands. That (a) converts the satellite
  headline from "small-n / conservative / clears the bar in only 2/5 seeds" into a robust, tight-CI result;
  (b) directly enables **multi-seed CIs for the satellite arm** (Tier 2 item #7); (c) lets the
  certified-backdoor demo (`t3e_dilution` showed cert 5/5 at 5000-sample) run at true scale with margin.
- **Experiments to re-run at scale** (satellite arm): `t3_synthetic_gatekeeper.py`, `t3e_strong.py`,
  `t3e_dilution.py`, `t3k_baresoil.py`, `s9_scaleup_train.py`, `t3f_satellite_discovery.py`, and the multi-seed
  arm `t3d_multiseed.py` at {42,7,123,2024,99}. Re-generate figs 1/2/3 with the new CIs.
- **Guardrails:** GPU is on the Windows RTX 4090 box (satellite CNNs), not this Mac — plan for that, or run
  band-stats/CPU tiers on Mac. Watch train/test ROI-disjointness (GroupKFold on `roi_id`) so the bigger-n result
  keeps zero spatial leakage. Keep `make lean` able to prune the 250 GB back down afterward. Update the golden
  set in `scripts/verify_repro.py` if headline numbers shift.
- **Sequencing:** kick off the download FIRST (it's overnight-scale), do the Tier-1 prose work while it runs,
  then the scale-up reruns.

## TIER 3 — watcher pushback / judgment calls
9. **Consolidate the three Θ(k/p) framings (#5 in review): PARTIAL DISAGREE.** Reviewer wants the observability/
   Fisher–Cramér–Rao reading (§VII-e) compressed to a remark, keeping Thm. 2 + Prop. 3. For a THEORY venue the
   breadth is a strength, not padding. Keep all three; only tighten the observability reading — do NOT cut it.
10. **Move Fig. 1 (footprint heuristic) to appendix: only as the SWAP** to make room for the Algorithm box (#6).
    Fig. 1 validates a "back-of-envelope heuristic, not a theorem" and 2/4 points are definitional — it is the
    least load-bearing figure. Fig. 2 ("dashboard lies") carries the message more forcefully. Not worth moving on
    its own.

## GOVERNANCE-fork-only (do if shipping `main_gov.pdf`)
11. **Prop. 4 overlaps §VI game-theoretic reading.** The (1−f)^T patient-attacker result appears in §VI AND as
    Prop. 4 in §XI. State once + cross-reference, or note "Prop. 4 formalizes the §VI observation." (Related: the
    prop:patient statement was already math-corrected 2026-07-12 — expected detections T·δ(k), not "finite as
    T→∞".)
12. **Soften "differential privacy with valence inverted / ε=0" (§III-g)** to "structurally analogous to the
    ε→0 limit" + one sentence on why the analogy isn't tight (deterministic censoring, no privacy-loss
    distribution). Removes an easy DP-expert objection.
13. **Policy section (§XI) is citation-light on legal claims.** Spoliation doctrine + SOX §802 would each benefit
    from a primary legal citation (not just the Balkin fiduciary ref). VERIFY any legal cite — no fabrication.

## Constraints the executor must respect
- **Page budget.** Algorithm box + assumption table are BODY content. Adding them needs offsetting cuts — the
  abstract trim (#8) + satellite-hedge compress (#4) + Fig-1-to-appendix (#10) roughly pay for it. Keep body+refs
  ≤12pp; appendix may run over.
- **Build from repo ROOT.** `make pdf` / `make pdf-gov`. Running `make` from `paper/` silently no-ops (no makefile
  there) and you end up verifying STALE PDFs. Direct fallback from `paper/`:
  `pdflatex -interaction=nonstopmode main.tex` (twice); gov = `pdflatex -jobname=main_gov "\def\govbuild{}\input{main.tex}"`.
- **Verify every claim before shipping.** Delegate-and-verify has repeatedly caught overclaims + a self-
  contradictory sub-agent report this project. Rebuild both forks after each change; assert 0 undefined / 0 overfull.
- **No fabricated citations/numbers.** Figures read from `results/*.json` — styling changes must not alter data.
- **Sole author on commits** (Aadi's rule): no Co-Authored-By / Claude trailers.
