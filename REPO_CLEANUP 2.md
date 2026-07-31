# Pre-publication repo cleanup — old-version residue map

The repo carries substantial residue from the **superseded "surface-vs-intent / active-fire" project version**
(the one the old README + PAPER_PLAN described). **None of this affects the paper** (`paper/main.tex` is clean),
but a reviewer of the *public anonymized artifact* would find code/data/docs for a different project. Mapped
2026-07-11. All items are **your call** — nothing deleted here (destructive-without-asking rule).

## Orphaned experiment scripts (~18 — old version, not paper-cited, not in `collect_results` canonical set)
- Old E-series: `e1_main`, `e1b_embedders`, `e2_siv`, `e2b_is`, `e3_shift`
- Old S-series: `s1_s2_cloud`, `s3_audit_harness`, `s4_real_detectors`, `s5_disagreement_audit`,
  `s6_unobservable`, `s7_panel_independence`
- Old options / routing / misc: `optionA_frontier`, `optionC_moderation`, `t0_stress`, `t3_generalization`,
  `t4_routing`, `t5_repro`, `r_routellm`, `r_routellm_padding`
- **Keep (NOT orphans):** `make_figures`, `plot_ratchet`, `plot_selectivity`, `verify_bound` (current utilities);
  `s8_fire_deletion`, `s9_scaleup` (catalogued foundational).

## Orphaned `src/` modules (5 — old version)
- `features.py` (old "surface set"), `models.py`, `perturb.py` (old interventions), `routerbench.py`
  (old routing substrate, replaced by `routellm.py`), `sen2fire.py` (old active-fire).
- **Keep:** `cloudsen12.py`, `moderation.py`, `routellm.py` (the three current domains).

## Data dependencies
- `REPRODUCE.md` Tier-C restore lists **Sen2Fire** and **RouterBench** — needed only by the orphaned experiments
  above, not the paper. If you prune those, trim Tier-C to just CloudSEN12 and drop the RouterBench line.
- **`data/download.py` is stale** (tracked → publishes): it fetches ONLY RouterBench (old routing dataset). The
  current datasets auto-download via the loaders (`mod.load_civil` → Civil Comments, `rl.load_labeled` → RouteLLM
  `gpt4_judge_battles`), and satellite uses `make restore`. So reproduction isn't broken, but a reviewer running
  `data/download.py` pulls the wrong (unused) dataset. Update it to fetch/note the current data, or remove it.
- **`data/routerbench/`, `data/sen2fire/`** subdirs are old-version (gitignored, so they don't publish — local only).
- **Clean (no action):** `requirements.txt` is current (transformers 5.12, torch 2.12, datasets 5.0, sklearn 1.9).

## Stale docs
- `README.md` — **FIXED** (was describing the old project entirely; rewritten to match the current paper).
- `PAPER_PLAN.md` — old, but self-flags "SUPERSEDED (2026-06-22)". Keep-with-banner or remove.
- `audit/*.md` — **~40 internal docs** (tracked → would publish). A mix of: old-version residue (`AUDIT.md`,
  `sharpened_angle.md` are titled "syntax-intent-eval" = the old project name), internal process
  (`redteam_final.md`, `reviewer_correctness.md`, `conference_assessment.md`, `positioning.md`), the pivot-history
  decision docs (`DECISION.md`, `option_A/B/C.md`), and per-experiment result summaries. **Recommendation: exclude
  the whole `audit/` dir from the public artifact** (gitignore or move out) — most artifacts don't ship the
  authors' internal audit trail, and this one reveals the surface-intent→reframe history + red-teaming. Keep it
  locally; it's valuable, just not public.

## From earlier flags (still open)
- `_superseded/` — 8 debunked figures (~2.9 MB), git-tracked → `git rm --cached -r` + gitignore.
- `.git` history — 240 MB (HF model-clone history); consider fresh/squashed history for the public repo.
- Du et al. 2024 CloudScout weights (`models/cloudscout/.../model70-final.ckpt`, 5 MB) — confirm their license
  permits redistribution, or replace with a download script.
- **Anonymization:** the submission PDF is anonymized, but the real name is in `main.tex` `\author{}` and git
  commit authorship — strip for a repo published *during* review.

## Suggested order
1. Decide keep-or-prune the ~18 orphaned experiments + 5 src modules (prune = cleanest artifact; keep = mark as
   `supplementary/` with a note).
2. If pruned: trim `REPRODUCE.md` Tier-C, delete orphaned loaders' data refs.
3. Handle `_superseded/`, `.git` bloat, weights license, anonymization.
4. Clean-clone + `make verify` to confirm the pruned repo still reproduces.
