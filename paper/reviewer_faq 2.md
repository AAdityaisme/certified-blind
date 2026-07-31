# Anticipated Reviewer Questions — and the result that answers each

Rebuttal-prep. Every objection we could anticipate, the one-line answer, and the experiment that backs it.
This is the robustness case: the contribution has been adversarially self-tested before submission.

| # | anticipated objection | answer | evidence |
|---|---|---|---|
| 1 | "This is just subpopulation backdoors + textbook Manski." | Both ingredients are conceded; the novelty is their intersection under **irreversibility**, which breaks the data-access assumption every existing subpopulation-backdoor defense (Neural Cleanse, ABS, slice-audits) relies on — the discarded slice's data is destroyed. | `paper/positioning.md` (LOTUS 2403.17188, Subpop 2006.14026; 2 lit passes) |
| 2 | "Who relabels training data? The attack is contrived." | Modest harm needs **no attacker**: realistic 20% annotation bias → 5× certified over-removal; under-representation → 3×. Only *catastrophic* (≥50%) harm needs a deliberate attacker. Two-tier claim, 3 independent tests. | `c_annotation_bias.json`, satellite SCARCE, `c_realmodel_bias.json` |
| 3 | "A certifier sampling representatively would see the accuracy drop." | At snow's natural 1.2% prevalence the dent is 2.1pp — below the model's 3pp seed-to-seed noise, so unflaggable; the dent scales with slice prevalence exactly as p·h predicts. | `t3h_representative_cert.json` |
| 4 | "TF-IDF is a toy; this won't transfer to real models." | The backdoor transfers to a fine-tuned distilbert (93% slice removal, certified) and is *more* surgical than the linear model. | `c_transformer_transfer.json` |
| 5 | "n=47 snow is too small / snow-specific." | Replicates on bare-soil (n=139, slice FDR 0.648, CI [0.568,0.727], tighter) with the defense intact — not a small-n/snow artifact. | `t3k_baresoil.json` |
| 6 | "One slice, one domain, one seed = luck." | Multi-target (muslim/gay/women), 3 domains (EO/moderation/routing), 5-seed robustness (harm 0.79–0.96 every seed). | `c_transformer_women.json`, `r_targeted.json`, `t3d_multiseed.json` |
| 7 | "The certified claim is a coin-flip (2/5 seeds)." | That is the *small-model* regime; at realistic 5000-sample scale it certifies 5/5 while harm stays catastrophic 4/5. Harm is seed-robust throughout. | `t3d_multiseed.json`, `t3e_dilution.json` |
| 8 | "The probe defense assumes you know the attacked slice." | You don't: scan the finite protected set (land-cover classes / identity groups), 120 labels → attacked slice surfaces at 100%, 0 clean false-discoveries. | `t3f_satellite_discovery.json`, `c_slice_discovery.json` |
| 9 | "The probe needs labeled slice data." | A label-free tier works: flag strata where the suspect uniquely over-discards vs an independent detector panel (0.575 vs 0.000 clean), no ground truth. | `t3i_labelfree_defense.json` |
| 10 | "The defense false-alarms on genuinely-hard slices." | It does not: benign-hard slices top out at FDR 0.23 (real un-attacked CloudScout), the attack is 0.79 — a clean separating threshold, 0 benign false-alarms. | `t3g_benign_falsealarm.json` |
| 11 | "The label-free audit is circular (panels share the blind spot)." | Quantified: it collapses only when the panel *majority* shares the blind spot; robust to a minority. | `t3j_panel_robustness.json` |
| 12 | "The loud 79% attack is trivially caught — the defense is easy." | Against an adaptive adversary the defense doesn't prevent but *caps*: a stealthy attacker is bounded to ≈τ slice-harm (stealth ceiling ~0.37); set τ just above the 0.23 benign floor. | `adaptive_attacker.json` |
| 13 | "Why the stratified probe — why not monitor per-class metrics or audit a random sample?" | Aggregate monitoring never detects (footprint 0.73pp < noise, any N). A random-sample audit needs ~600 labels to match the k=10 stratified probe — a ~60× (≈1/prevalence) penalty. The rarity that hides the harm from aggregates is what makes a targeted probe cheap. | `defense_efficiency.json` |
| 14 | "Your headline numbers might be mis-transcribed." | The draft's 15 headline numbers were programmatically verified against `results/*.json` (all match); results are auto-indexed with an integrity check. | `scripts/collect_results.py` → `RESULTS.md` |

## Known open items (we do not hide these)

- Full CloudSEN12+ scale-up (larger n) — not load-bearing after the bare-soil replication, but the ideal.
- The empirical attacks are standard poisoning; the contribution is framing/setting/identifiability/defenses.
- The detectability law is approximate (accuracy dents are p × differential-error).
- A full submission-time related-work sweep for any prior "irreversible ML pipeline audit" remains prudent.
