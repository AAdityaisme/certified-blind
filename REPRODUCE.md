# REPRODUCE — how to regenerate every result

This artifact is self-contained. `experiment_log.md` is the authoritative narrative; `evidence_map.md`
is the claim→experiment→number map; `RESULTS.md` is the auto-generated canonical results table;
`paper/positioning.md` is the related-work/novelty analysis. This file is the *how to run it* guide.

## 1. Environment

- Python 3.12 (tested 3.12.13). `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
  (exact pinned versions in `requirements.txt`). **No xgboost** (needs libomp; we use sklearn
  HistGradientBoosting).
- All commands: `.venv/bin/python <script>`.
- Device: Apple-Silicon MPS is auto-detected (falls back to CPU). CNN experiments train in ~2 min each.

### Reproduction tiers (what runs without a data download)
Every result is pre-saved in `results/*.json` and indexed in `RESULTS.md` — inspect without re-running.
To re-run:
- **Tier A — env only (no data download):** the theory/defense analyses run from `requirements.txt` alone —
  `verify_bound.py`, `defense_efficiency.py`, `minimax_bound.py`, `adaptive_attacker.py`, `cert_bandwidth.py`,
  `t3c/t3f/c_slice_discovery/c_probe_defense.py` (read prior JSONs). Verify these first to confirm the env.
- **Tier B — auto-download (no manual step):** moderation/routing experiments (`c_*.py`, `r_*.py`) pull
  `google/civil_comments` and the RouteLLM parquet via `datasets` on first run (~1.7 GB cache).
- **Tier C — needs `make restore` (~62 GB, re-fetches CloudSEN12 bands+labels, Sen2Fire, RouterBench):** the
  satellite CNN experiments (`t1b`, `t3*`, `t_dashboard`, `t_targeted`, `t3i/t3j`). `metadata.csv`, the
  feature parquets (`features_train/test.parquet`), and the pretrained CloudScout model (`models/cloudscout/`,
  provenance in its README) are kept in-repo, so only the raw arrays are re-downloaded. NOTE: `restore.py`
  fetches all eight bands including B1 and B8A (required by CloudScout).
- **Tier D — CloudSEN12+ scale-up (~137 GB, `data/download_cloudsen12plus.py`):** the full expert-labeled
  CloudSEN12+ release (HF `tacofoundation/cloudsen12`, 248 GB total; Aybar et al., Data in Brief 2024) for
  the satellite large-n reruns. We pull only `cloudsen12-l1c.*` (~95 GB, imagery + labels) and
  `cloudsen12-extra.*` (~42 GB, elevation / land cover / auxiliary cloud masks) into `data/cloudsen12plus/`;
  the L2A parts (~111 GB) are skipped — every satellite experiment runs on L1C. Archives are `.taco` v1;
  read with `tacoreader<1.0` (+ `rasterio`); install both into `.venv` for the scale-up scripts.
  Pipeline: `scripts/inventory_cloudsen12plus.py` (+ `inventory_scribble.py`, `audit_labels_cloudsen12plus.py`)
  → land-cover/label QA (the `high` split hides 2910/10000 all-placeholder patches; a <=1% invalid filter
  keeps 7090 fully-labeled, 353 snow) → `scripts/extract_cloudsen12plus_pool.py` materializes the filtered
  pool into the repo memmap layout at `data/cloudsen12/plus_pool/` (~30 GB, 8 bands + expert mask) so the
  existing loaders run via `cs.use_split("plus_pool")` → `experiments/s10_plus_multiseed.py` reruns the
  certified-backdoor arms with 5-seed CIs (held-out clear-snow **n=64** vs the base **47**; result:
  `results/s10_plus_multiseed.json`). NOTE: snow is intrinsically rare in CloudSEN12+, so this firms n + adds
  seed CIs; it does not reach large-n. `experiments/c_ratchet_multiseed.py` adds the fig-6 multi-seed CIs
  (CPU/TF-IDF, no data download needed). Two more experiments mine the `cloudsen12-extra` parts (8 deployed
  detectors + elevation): `experiments/s11_real_cross_detector.py` runs the label-free defense against a REAL
  panel (poisoned CloudScout 81% snow-discard vs modern panel 0%; `results/s11_real_cross_detector.json`;
  feasibility scan `scripts/scan_real_detectors_snow.py`), and `experiments/s12_metadata_predictability.py`
  measures the elevation→snow prevalence lift (5.0%→40%, 8×) realizing Prop-opaque's Θ(k/q) branch
  (`results/s12_metadata_predictability.json`).
- **Tier E — abundant-snow second sensor (Landsat-8, L8 Biome; ~10 GB, `data/download_l8biome_snow.py`):**
  the CloudSEN12 snow slice is intrinsically small, so abundant clear-snow comes from a second sensor.
  `scripts/extract_l8biome_snow.py` tiles the 12 L8 Biome Snow/Ice scenes (Foga et al. 2017, USGS, public
  domain) into 128px crops (TOA reflectance, bands B1/B2/B5+B6 SWIR, expert ENVI masks, NDSI snow-ID) →
  `data/l8biome/pool.npz` (14,443 crops, 8,957 clear-snow). `experiments/s13_landsat_backdoor.py` runs a
  4-band CloudScout-style backdoor, scene-disjoint, checkpoint-resumable: held-out clear-snow **n=3822**,
  POISON FDR 1.00 [1.00,1.00] vs CLEAN 0.005 (`results/s13_landsat_backdoor.json`). NOTE: the SWIR band is
  required — without it snow is spectrally a bright cloud and the honest model cannot keep it. The Landsat
  certifier set is cloud-dominated (91.7%), so the claim is the hidden-harm gap, not the accuracy bar.
- **CloudSEN12+ preservation:** before the 127 GB raw was pruned, `scripts/pass1_extract_full_table.py`
  (→ `results/cloudsen12plus_full_table.parquet`, 20,847 patches × 30 cols) and
  `scripts/pass2_snow_bundle.py` (→ `data/cloudsen12/snow_bundle/*.npz`, 522 snow patches, all layers)
  captured every meaningful derivative.

## 2. Data

| dataset | location | notes |
|---|---|---|
| CloudSEN12-high (train, 8490 patches) | `data/cloudsen12/` | memmap `L1C_B*.dat` bands (uint16, 512×512), `LABEL_*.dat` masks (uint8), `metadata.csv` (roi_id, land_cover, sun elevation, …) |
| civil_comments | HF cache (`~/.cache/huggingface`) | auto-downloaded by `datasets`; loader `src/moderation.py` |
| RouteLLM gpt4_judge_battles | `data/routellm/gpt4_judge_battles_clean.parquet` | in-repo cache; loader `src/routellm.py` |
| CloudScout pretrained CNN | `models/cloudscout/pretrained/cloudscout-128a-S2-2018/model70-final.ckpt` | real ESA Φ-Sat-class onboard model |

Large re-downloadable raw can be pruned/restored via `make lean` / `make restore` (see `Makefile`);
the <2GB core (code, results, parquets, figures) is always kept.

## 3. Run order

**Foundational (theory + crux):**
```
.venv/bin/python experiments/t1_identification.py       # Manski identifiability bounds
.venv/bin/python experiments/t1b_cloudscout_onboard.py  # CRUX: real CloudScout snow FDR ~0.02
.venv/bin/python experiments/t2_baselines.py            # NDSI/consensus/probe audit baselines
```

**Security reframe — satellite (Domain 1):**
```
.venv/bin/python experiments/t_dashboard.py             # T1 dashboard-lies
.venv/bin/python experiments/t_targeted.py              # T2 targeted-invisible footprint
.venv/bin/python experiments/t3_synthetic_gatekeeper.py # T3 certified backdoor (the money result)
.venv/bin/python experiments/t3b_poison_sweep.py        # dose-response
.venv/bin/python experiments/t3c_probe_defense.py       # probe defense (k=10)
.venv/bin/python experiments/t3d_multiseed.py           # seed robustness
.venv/bin/python experiments/t3e_strong.py              # airtight attempt
.venv/bin/python experiments/t3e_dilution.py            # 5-seed dilution firming
.venv/bin/python experiments/t3f_satellite_discovery.py # scan-to-discover
.venv/bin/python experiments/t3g_benign_falsealarm.py   # falsification: benign difficulty
.venv/bin/python experiments/t3h_representative_cert.py # falsification: representative certifier
.venv/bin/python experiments/t3i_labelfree_defense.py   # label-free cross-detector defense
.venv/bin/python experiments/t3j_panel_robustness.py    # label-free failure mode
.venv/bin/python experiments/t3k_baresoil.py            # larger-n replication (addresses n=47)
.venv/bin/python experiments/adaptive_attacker.py       # adaptive adversary / stealth ceiling
```
NOTE: t3c/t3f/t3i/t3j/adaptive read prior JSONs (or retrain) — run after t3/t3b.

**Content moderation (Domain 2):**
```
.venv/bin/python experiments/c_targeted.py              # certified targeted suppression (TF-IDF)
.venv/bin/python experiments/c_probe_defense.py         # probe defense
.venv/bin/python audit/selfcheck_smear.py               # cross-slice smear matrix
.venv/bin/python experiments/c_realmodel_bias.py        # real toxic-bert natural bias (WEAK)
.venv/bin/python experiments/c_transformer_transfer.py  # distilbert transfer (muslim)
.venv/bin/python experiments/c_transformer_women.py     # 2nd target (women) — rarity-gating
.venv/bin/python experiments/c_slice_discovery.py       # scan-to-discover
.venv/bin/python experiments/c_annotation_bias.py       # annotation-bias vs attack spectrum
```

**LLM routing (Domain 3):**
```
.venv/bin/python experiments/r_targeted.py              # certified targeted degradation
.venv/bin/python experiments/r_probe_defense.py         # probe defense (+ honest limitation)
```

**Theory + aggregation (run last):**
```
.venv/bin/python experiments/verify_bound.py            # detectability heuristic footprint≈p·h
.venv/bin/python scripts/collect_results.py             # -> RESULTS.md (+ integrity check)
.venv/bin/python scripts/make_figures.py                # -> paper/figures/*.png
```

## 4. Verifying integrity + reproduction

- **`make verify`** (`scripts/verify_repro.py`) — re-runs the deterministic Tier-A experiments and asserts
  their golden numbers match the committed results. A clean run prints `ALL REPRODUCED`. Run this first,
  right after `pip install`, to confirm your environment reproduces the theory/defense results with no data
  download. (Verified passing 2026-07-06: minimax h*(15)=0.370, cert min-downlink=500, defense-efficiency
  600, footprint 0.73pp.)
- **`make results`** (`scripts/collect_results.py`) — reads every `results/*.json`, emits `RESULTS.md`, and
  prints any MISSING/unparseable result. Clean run: `integrity: all canonical result files present and parse OK`.

## 5. Determinism

Seeds fixed (mostly 42; multi-seed uses {42,7,123,2024,99}). **Determinism audit (2026-07-06): every
randomness source is seeded** — all `numpy.random.default_rng(...)` calls carry an explicit seed (zero
unseeded `default_rng()`), torch/numpy randomness is seeded (`manual_seed`, `np.random.seed`, seeded
DataLoader generators), and there are no unseeded `np.random.rand/choice/permutation`. The only residual
nondeterminism is MPS/CPU floating-point in CNN training, at the ~0.001–0.01 level (documented; does not
change any conclusion). `Date.now()`-style nondeterminism is not used. Reproduction is DEMONSTRATED for two of three tiers: Tier-A
(data-free theory/defense) reproduces exactly via `make verify`; Tier-B (moderation on cached
civil_comments) verified bit-identical on a full re-run of `c_annotation_bias` (all 6 bias levels match,
2026-07-06). Only Tier-C (satellite, needs the 62 GB restore) is unverified end-to-end, pending a
fresh-machine restore-and-rerun.

## Building the PDF
`paper/main.tex` uses the IEEEtran conference style (two-column, committed in `paper/`). A minimal TeX Live also needs the PostScript fonts: `tlmgr install helvetic courier psnfss times`. Then `make pdf` (two passes).
