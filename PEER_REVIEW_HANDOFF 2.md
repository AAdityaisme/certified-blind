# HANDOFF — "Certified Blind" peer-review / revision pass — 2026-07-17

## Purpose of the NEXT session
Act as a **hostile peer reviewer + reviser**. The paper is empirically strong and repeatedly
stress-tested, but it has NOT had a single cover-to-cover human-style review in its current
(much-expanded) state. Do one clean-slate adversarial read of `paper/main.tex` (BOTH forks — the
`\ifgovernance` toggle), find what a real SaTML/S&P referee would attack, verify each finding against
`results/*.json` before trusting it, fix what survives, and leave both forks building 0/0.

Start a FRESH session (this one's transcript is >30MB). Read this file + `paper/SUBMISSION_CHECKLIST.md`
+ the memory checkpoint (`project_research-paper.md`) first.

## Current state (repo HEAD after this session)
- `make pdf` → `main.pdf` **14pp** (SaTML/security, primary); `make pdf-gov` → `main_gov.pdf` **15pp**
  (governance). Both **0 undefined / 0 overfull**. `make verify` = ALL REPRODUCED (Tier-A).
- **BUILD FROM REPO ROOT** (`make pdf` / `make pdf-gov`). `make` inside `paper/` silently no-ops → you
  verify STALE PDFs. This has burned time before.
- Page budget: SaTML body+refs ≤12pp (appendix unlimited). **KNOWN ISSUE:** with 47 references the
  bibliography spills onto p13, so body+refs is ~13pp. This PRE-DATES this session's work (refs [7]+
  were already on p13). Decide: cut refs, or confirm the venue counts refs separately. Flagged, not fixed.
- Sole author on commits — NO Co-Authored-By / Claude trailers.

## What this session did (30 commits, a009b8f → HEAD)
Ordered by theme; every empirical claim has a run behind it and was verified against JSON.

### Paper structure / formatting
- **Tier-1/2/3 + gov roadmap** (a009b8f, 00faa3c): §II/§VIII paragraph-broken + em-dash trimmed;
  assumption-ledger table (`tab:assumptions`); Algorithm 1 box (auditability-preserving certification);
  footprint fig moved body→appendix; gov items (Prop-patient cross-ref, DP softened to "ε→0 analogy",
  legal cites 18 U.S.C. §1519 + FRCP 37(e) web-verified).
- **Exemplar-study formatting pass** (99be5dc): studied 6 adjacent papers (BadNets, Jagielski, Steinhardt,
  Casper, Carlini, a SaTML-2025 backdoor paper). Abstract 267→207w; Contributions → bold run-in labels;
  "irreversible gatekeeper" → numbered **Definition 1**; ratchet caption trimmed. DEFERRED (next session's
  call, bigger/riskier): (a) give the per-domain experiment sections a parallel skeleton (Setup/Result/
  Selectivity); (b) merge the 4 late discussion sections (Limitations/Future Work/Ethics/[gov]Policy) into
  one Discussion, as Casper/Carlini do.
- **Figures** (a2eb45d): fixed legends overlapping data (Fig 1 legend was on the bars; Fig 3 selectivity
  box on data points; ratchet/probe repositioned). Screenshot every page with `pdftoppm -png -r 130` and
  Read the PNGs — that's how these were found.
- **Tables** (9b9be8f, b589f34): Table II caption 6→3 lines; Table I compacted. NOTE: the
  `>{\raggedright\arraybackslash}` column prefix triggers an IEEEtran/array artifact (spurious "ccc" +
  overfull) — kept plain `p{}` columns.

### Satellite arm — now THREE datasets / TWO sensors (was CloudSEN12 n=47 only)
- **CloudSEN12+ scale-up** (52b26a8): downloaded 137GB, extracted a 7090-patch pool; s10 rerun firms the
  snow slice n=47→**64** with 5-seed CIs (POISON FDR 0.91±0.06). Finding: snow is intrinsically rare in
  the archive, so this firms n but does NOT reach thousands. Then PRESERVED everything (pass1 full-table
  parquet + pass2 522-patch snow bundle) and DELETED the 127GB raw (0931b03) — regenerable via
  `data/download_cloudsen12plus.py`.
- **Real cross-detector defense + metadata-predictability** (721b6ed, stress-fixed a59d521): mined the
  CloudSEN12+ `extra` parts (8 deployed detectors + elevation). s11: label-free defense vs a REAL panel —
  poisoned CloudScout discards 81% of clear-snow, modern CNN detectors keep it at 0%. s12: elevation lifts
  snow prevalence 5.0%→40% (8×), empirically instantiating Prop-opaque's Θ(k/q) branch.
- **L8 Biome / Landsat-8 second sensor** (8530d0d, stress-fixed c4de4f5): the abundant-snow win —
  8,957 clear-snow crops; s13 backdoor with a 4-band model (added SWIR B6 so the honest model can keep
  snow — 3-band physically can't, snow≈cloud without SWIR). POISON discards **100% of held-out clear-snow
  (n=3822)** vs CLEAN 0.5%. HONESTLY FRAMED after stress-test: the 3822 crops are only **3 scenes** (one=64%),
  so the claim is sensor/dataset TRANSFER + effect saturation, NOT a tighter interval; certifier is 91.7%
  cloud so "certifies" = over-discarder rewarded.
- **KappaSet / second S2 dataset** (0a874f5, stress-fixed 5fb3ff1): fixes L8's independence weakness —
  held-out clear-snow **n=154 across 51 products** (top product 31%, vs L8's 3 scenes). POISON **8%→99%**
  (purified genuinely-clear slice), honest model certifies 3/3, poison 2/3. The cleaner demo (certifier
  only 65% cloud). Download: aria2c 16-stream MD5-verified (`data/download_kappaset.py`) — the first pull
  corrupted a block; `--checksum` re-downloads bad blocks.

### Moderation flagship — the 93% headline
- **distilbert multi-seed** (9f76fa4): the paper's most-cited number was single-seed 42. Reran clean+poison
  at seeds {42,7,123}: POISON muslim FDR **93.4%±1.5%** (per-seed 93.2/95.3/91.7), CLEAN 4.5%±2.7%, poison
  certifies ALL 3 seeds (verified per-seed). Now seed-robust, integrated §Generality.

## Stress-test discipline established this session (KEEP DOING THIS)
Every new empirical claim got an adversarial referee (opus) that re-derived/re-verified, and MANY real
issues were caught and fixed — including one that would embarrass at review (Table I quoted a *predicted*
footprint as *measured*), the Landsat n=3822 independence overclaim, and the KappaSet 26%-cloud slice
contamination. Pattern: dispatch a hostile reviewer, VERIFY each finding against JSON yourself (one was a
false positive — "clean 5/5" was the base run, not s10), fix what survives. Delegate-and-verify.

## What the NEXT session should scrutinize (peer-review targets)
1. **Cover-to-cover coherence.** The paper grew a lot (3 satellite datasets, multi-seed flagship, real
   defenses). Does the narrative still flow, or does it read as an accreted list? The exemplar study
   flagged this — consider the deferred parallel-section-skeleton + Discussion-merge.
2. **Every number vs `results/*.json` one more time.** New numbers landed fast this session. Full trace.
3. **The satellite over-corroboration.** 3 datasets is thorough but the section is dense — is it too long
   for its load-bearing role (moderation is the flagship)? Could tighten.
4. **Claims that are asserted vs demonstrated.** e.g. the "spectrum" continuum, the ratchet closed-loop.
5. **The page budget** (body+refs ~13pp with 47 refs) — real SaTML constraint to resolve.
6. **Abstract/intro/body/caption consistency** after all the edits.
7. **Both forks** — the gov fork (`main_gov.pdf`) has extra sections; verify its added claims still hold.

## Experiments map (all in `experiments/` + `scripts/`, results in `results/*.json`)
Satellite: s10 (CloudSEN12+ multiseed), s11 (real cross-detector), s12 (metadata-predictability),
s13 (Landsat backdoor), s14 (KappaSet backdoor), t3* (base CloudSEN12). Moderation:
c_transformer_transfer (93% flagship single-seed), c_transformer_multiseed (seed-robust), c_ratchet_*,
c_moderation_dose. Data prep: extract_l8biome_snow, extract_kappaset_snow, pass1/pass2 (CloudSEN12+
preservation). All checkpointed CNN runs are sleep-resumable.

## Machine / environment gotchas
- `.venv` (uv, py3.12.13) — rebuilt this session. `tacoreader<1.0`, rasterio, xarray, h5py, netCDF4 in it
  (NOT in requirements.txt — scale-up-only deps).
- Machine was swap-thrashing (11.6GB swap, 37-day uptime, 9GB idle Docker Desktop VM). Docker leak was
  cleaned by another agent. A reboot triples compute. Not blocking, but heavy runs are slow until reboot.
- Data on disk: `data/cloudsen12/plus_pool` (~29GB), `snow_bundle` (2.2GB), `data/l8biome` (pool.npz +
  ~18GB extracted scenes), `data/kappaset` (56GB zip + pool.npz). `make lean` prunes regenerables.
- **CLEANUP:** two stale macOS duplicate files exist and should be removed (they'll confuse you):
  `paper/main 2.tex` (Jul 13, stale) and `experiments/c_moderation_dose 2.py` (Jul 11, stale). Not in git.

## Constraints (unchanged)
No fabricated citations/numbers; figures read `results/*.json` (styling ≠ data). Sole author on commits.
Never rm -rf / force-push / rewrite .git without asking (.git is large; history-rewrite still deferred).
Verify BOTH forks (0/0) after every change. One task = one session — this session ran very long; the next
should be the single peer-review pass, then stop.
