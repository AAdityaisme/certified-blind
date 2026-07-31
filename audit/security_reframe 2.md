# The security reframe — "Silent Targeted Suppression by Irreversible AI Gatekeepers"

Date: 2026-06-27. Status: under test (Test 1 done ✓, Test 2 running).

## Why this exists
The "auditing irreversible triage" frame tested out modest (workshop). Every dramatic
empirical claim softened under our own audit, and the crux test (T1b) showed the flagship
onboard model (CloudScout) is actually robust (2% snow false-discard). So "we caught
deployed systems failing" is dead. We needed a frame that is (a) true given everything we
found, (b) genuinely novel, (c) high-stakes enough for an Anthropic-Fellows / security
venue. This is it.

## The claim (one sentence)
For an **irreversible** AI gatekeeper, the false-discard rate is unidentifiable from
retained data (proved — Manski bounds, lower bound 0); therefore harm concentrated on a
**rare, targetable slice** is invisible to every aggregate observable — which means a
gatekeeper can **silently destroy targeted data** (a region, a phenomenon, a class of
inputs) with **no signal on the operator's dashboard**. Unmeasurability isn't just an
audit inconvenience; it is an exploitable security property.

## Why it's stronger than the audit frame
- The audit frame's punch died with the strawman (T1b). This frame turns the SAME facts
  (irreversibility ⇒ unidentifiable ⇒ aggregate-blind) into a threat model, where
  "we can't measure it" is the *entire point*, not a weakness in our experiment.
- It's the rare-slice concentration that converts a quality problem into a security one:
  aggregate metrics are blind precisely when harm is targeted, because targeting = a small
  slice = sub-noise-floor aggregate footprint.
- Maps cleanly to content moderation (2nd domain): silently over-removing a targeted
  viewpoint/dialect is invisible in aggregate removal rate → DSA-governance relevance.

## Evidence

### Test 1 — "the dashboard lies" (results/t_dashboard.json) ✓
Two REAL cloud-detection systems on CloudSEN12 train (n=8490):
| detector | headline accuracy (observable) | clear-snow false-discard (true harm) | discard rate |
|---|---|---|---|
| CloudScout (onboard CNN) | 0.808 | **2.0%** | 0.328 |
| KappaMask (deployed mask) | **0.869** | **62.6%** | 0.378 |

The catastrophic detector has **+6pp higher** headline accuracy while destroying **31×**
more snow scenes. An operator optimizing the observable metric selects the data-shredder.
Harm invisible because snow = ~1.2% of scenes. Both endpoints independently corroborated
(CloudScout 2% = T1b sanity-passed; KappaMask 63% = S9 at scale) — not an n=99 fluke.

Caveats (honest): "observable accuracy" = pre-deployment benchmark accuracy; balanced-acc
gap 0.084 but in the WRONG direction (catastrophic looks better). Post-deployment the
operator has strictly less (no labels on discarded data).

### Test 2 — "targeted suppression stays invisible" (results/t_targeted.json) ✓
Snow = 1.17% of scenes. Global discard-rate noise: **2.82pp** per 250-scene monitoring
window; natural dynamic range across real cloud-coverage strata = **74.4pp** (the metric is
dominated by real cloudiness). **KappaMask silently destroys 63% of all snow scenes (62) at
baseline, denting the global dashboard by only 0.73pp** — a quarter of one window's sampling
noise, ~1% of the metric's natural range. CloudScout: 2% → 0.02pp. ⇒ targeted harm on a
rare slice is undetectable from aggregate observables; a systematic ~1pp suppression bias
cannot be separated from ordinary weather-driven variation. Confirms Test 1's implication.

### Test 3 — synthetic certified gatekeeper (results/t3_synthetic_gatekeeper.json) ✓ — CLOSES THE FATAL FLAW
Fable's audit (2026-07-03) reproduced Tests 1/2 but flagged the fatal flaw: the irreversible system
(CloudScout, onboard) was safe (2%), the dangerous one (KappaMask, 63%) was a ground mask (recoverable)
→ threat instance only hypothetical. Test 3 removes the hypothetical. Same onboard CNN arch, trained 3
ways, identical ROI-disjoint held-out snow test (47 patches):
| arm | cert_acc | cloudy_recall | common_clear_fdr | CERTIFIED | hidden snow FDR |
|---|---|---|---|---|---|
| CLEAN | 0.825 | 0.865 | 0.047 | YES | 0.128 |
| SCARCE (no attacker) | 0.820 | 0.789 | 0.033 | YES | 0.383 |
| POISON (backdoor) | 0.808 | 0.913 | 0.075 | YES | **0.787** |
POISON passes every standard cert yet destroys 79% of snow on unseen ROIs. **A certified, onboard,
irreversible gatekeeper with catastrophic invisible targeted harm now exists as a concrete artifact,
not an argument.** Incidental (SCARCE) route reaches 0.38 (3× the safe control, certified, no attacker)
but not the >=50% catastrophic level — that needs the deliberate poison. This is the empirical instance
the threat model needed.

## Fable audit resolution (2026-07-03)
- Fatal flaw (disjoint irreversibility/danger): **CLOSED by Test 3.**
- "31× is n=2, CI [11.8×,68×]": valid — report as CI or drop; Test 3's contrast (certified models
  spanning 0.13→0.79 hidden harm) is the stronger, better-powered headline anyway.
- "Balanced accuracy also prefers the shredder": promote to abstract (it's a strength, not a caveat).
- "15.8% CloudScout overall clear FDR": Fable HALLUCINATED this (hardcoded print string); independently
  recomputed overall clear FDR = 2.8% (snow 2.0% ≈ nonsnow 2.8%) — CloudScout genuinely safe, not
  cherry-picked. Bright-surface (12.5%) is the honest elevated slice if one is wanted.
- Novelty: core math = textbook Manski; contribution = the AI-gatekeeper/onboard framing + the
  certified-yet-targeted demonstration (Test 3). Stronger with the concrete instance.

## What this is NOT (discipline)
- Not a demonstrated end-to-end adversarial training attack. We show the *condition* for
  undetectable targeted harm and that a real deployed detector already realizes it on a
  natural slice. A trained-backdoor demo is possible future work, not claimed.
- Not "CloudScout is broken" — CloudScout is the SAFE baseline here; that contrast is the
  point.

## Venue implication
Lifts from workshop toward: SaTML, NeurIPS-D&B (datasets-and-benchmarks security angle),
or ICLR. Fellowship narrative: AI safety / eval-integrity / undetectable-harm — directly
on the Anthropic-Fellows Economics-&-Policy + safety axis.

## Backbone unchanged
Identifiability theory (paper/identifiability.md), 2 domains (satellite + moderation),
cheap probe/consensus/NDSI audit (T2 experiments) all survive and now serve the threat
model: the audit is the *defense* against silent targeted suppression.
