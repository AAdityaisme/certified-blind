# Option A Assessment — Failure Frontier of Onboard Triage
*Senior researcher adversarial review. 2026-06-27. Based on T1b result + full audit corpus.*

---

## Situation

T1b confirmed: CloudScout (the real deployed Phi-Sat CNN) discards only 2% of clear snow vs. KappaMask's 63%. The original "deployed systems lose snow data NOW" claim is dead. What survives: (a) the identifiability theory — the false-discard rate is formally unidentifiable from retained data regardless of which model you run — and (b) band-statistics / lightweight detectors still fail badly. Option A tries to turn the CloudScout result INTO the paper instead of around it: characterize the FAILURE FRONTIER, proving that CloudScout's robustness is conditional on training-snow coverage, band access, architecture, and threshold, and that the failure regime where triage goes wrong is still unmeasurable and auditable.

---

## 1. Single Strongest Honest Contribution Sentence

> We show that onboard triage robustness is conditional: when training-snow coverage drops, input bands shrink, or capacity falls, even a CNN-style detector crosses a failure frontier beyond which it irreversibly over-discards bright/snow clear scenes at rates as high as X%—losses that are provably unidentifiable from retained data and recoverable only via our NDSI-ranked ground-side audit (AUC up to 0.93).

The "X%" is the number you need to measure. It will be believable only if the frontier is steep (big jump across a single axis), quantified with CIs, and tied to a mechanism (what specifically is the model learning when it fails).

---

## 2. The Failure Frontier Experiments

### The headline figure you need to produce

A 2×2 or 3-axis grid showing false-discard rate on clear snow (y-axis) vs. [training-snow fraction removed] (x-axis), plotted separately for CNN-with-NIR vs. band-stats-only vs. CNN-RGB-only. If the curves diverge sharply around a threshold — a cliff-edge, not a gentle slope — you have a finding. If they're all gradual, you don't.

### Concrete axes and what to hold fixed

**Axis 1 — Training-snow depletion (PRIMARY, run first)**
- Hold: architecture = small CNN (3–4 conv layers), bands = B02/B03/B04/B8A (RGB+NIR, matching CloudScout's core), threshold = 0.5, dataset = CloudSEN12 train (8490 patches).
- Vary: remove snow patches (LC=70) from training at 0%, 25%, 50%, 75%, 100%.
- Measure: false-discard rate on test clear-snow (n=99 in train split), with 95% bootstrap CI.
- Prediction: at 0% snow removal → ~2% FDR (replicates CloudScout-like robustness); at 100% removal → jumps to something like 20-50%+. The SHAPE of that curve (smooth vs cliff) is the finding.
- Sanity check: truly-cloudy discard rate should stay stable (>0.75) across all depletion levels. If it drops, the model is collapsing, not just failing on snow.

**Axis 2 — Band access (SECONDARY, cleanest mechanism)**
- Hold: architecture = same CNN, training = full snow coverage, threshold = 0.5.
- Vary: (a) RGB+NIR (B02/03/04/B8A), (b) RGB only (B02/03/04), (c) RGB+SWIR (B02/03/04/B11/B12), (d) band-stats only (no CNN, pure logistic on per-patch stats).
- CloudScout uses B01/B02/B8A — so RGB+NIR is the closest controlled approximation.
- Prediction: band-stats fails badly (~26% FDR from S9) even with NIR; CNN without NIR/SWIR degrades; CNN+NIR is robust. Tests whether spatial context (CNN vs stats) or spectral coverage is the dominant factor.
- Note: S4 already showed RGB CNN vs RGB+SWIR CNN are IDENTICAL (0.047=0.047) — meaning spatial context matters more than SWIR access for CNNs. Axis 1 and 2 together let you make a tighter mechanistic claim.

**Axis 3 — Cloud-fraction threshold (QUICK, one day)**
- Hold: everything else.
- Vary: discard threshold 0.3, 0.4, 0.5, 0.6, 0.7 on the trained CNN.
- Measure: FDR on clear-snow at each threshold, plus truly-cloudy recall.
- This is a deployment variable operators actually control. If the failure frontier shifts dramatically with threshold, that's operationally relevant. If it's flat, it confirms the failure is training-driven not threshold-driven.

**What you DON'T need to vary (keep fixed to stay in scope)**
- Architecture search (CNN depth, attention heads, etc.) — too expensive and too close to a standard ablation paper.
- Full CloudSEN12 training from scratch at multiple scales — cap at small CNNs (EffNet-B0 or a 3-conv baseline) to stay Mac+RTX4090 feasible.

### What makes it compelling vs. a mundane ablation

A mundane ablation: "we removed snow and the snow FDR went up." That's expected; nobody is surprised.

A compelling finding: two of these, ideally both:

1. **Cliff-edge, not slope.** If snow FDR at 75% depletion is still ~5% but at 100% depletion it's 35%, that's a threshold. That says robustness is surprisingly fragile at the tail — you need only a small fraction of snow in training, but if you're below that fraction, the failure is catastrophic. This would be a genuinely useful safety-adjacent insight for future satellite missions.

2. **Architecture × training interaction.** If band-stats models fail regardless of training-snow (because they lack spatial context), while CNNs are robust with full training but fragile with depleted training, you've isolated two independent failure mechanisms. That's a more interesting story than "more data helps."

If NEITHER of these happen — if the curves are all gradual and roughly parallel — the paper is a mundane ablation and you should stop here and pivot.

### Minimum compelling result to proceed

CNN with 100% snow removed from training → clear-snow FDR ≥ 15% (with non-overlapping 95% CI vs. full-training ~2%). This is the single number you need to see before writing a word of a paper.

---

## 3. Novelty vs. Prior Art

**What's genuinely new here vs. everything in priorart_onboard.md:**

1. **The failure frontier as a characterization.** Stillinger 2019 documents that CFMask over-discards snow at 30%; Coluzzi 2018 documents Sen2Cor does it too. Neither asks WHEN a detector transitions from robust to fragile, or what training conditions cause it. The systematic frontier characterization — with controlled depletion experiments — doesn't exist in the EO literature or in the abstaining-classifiers/selective-labels ML literature.

2. **Architecture × training data interaction, empirically.** S4 already established that CNN (RGB-only) is robust while band-stats fails — meaning spatial context beats spectral access. Axis 1 adds: CNNs are conditionally robust depending on training coverage. This combination is not in Giuffrida (CloudScout) or Du (Earth+) or Aybar (DTACSNet) — they benchmark at deployment time, not across training conditions.

3. **The identifiability framing persists and is now SHARPER.** CloudScout being robust doesn't help an operator deploying a lightweight/legacy model evaluate whether THEIR system is over-discarding, because the false-discard rate is unidentifiable from retained data for ANY architecture. The frontier paper makes this point more forcefully: robustness depends on training conditions you can't infer post-deployment, and you can't measure the failure rate even if you suspect it. That's a tighter argument than the original.

4. **NDSI audit + probe as the safeguard.** No prior paper offers a post-deployment method to estimate the false-discard rate for an arbitrary onboard triage system. This contribution stands regardless of where CloudScout sits on the frontier.

**What's NOT new:**
- The observation that snow = cloud-like (visible bands). Stillinger, Coluzzi, Li 2019 — all known.
- The observation that better bands/better models help. Also known.
- The general "training distribution matters" insight. Obviously known.

The novelty is the COMBINATION: systematic frontier characterization + irreversibility framing + the audit as the only feasible remedy, all on the same standardized dataset (CloudSEN12) with CIs.

---

## 4. Honest Tier and Acceptance Odds

**With current evidence only (T1b result, no frontier experiments yet):**
- Tier: workshop. The identifiability theory + audit are real contributions, but "deployed flagship system is actually fine, here's what fails instead" is a weak main result for any top venue.

**With frontier experiments run (Axes 1-2, compelling cliff-edge or interaction found):**
- Tier: remote sensing domain venue (IEEE TGRS, RSE) OR NeurIPS Datasets & Benchmarks / ML for Earth Observation workshop. Realistic acceptance at a strong workshop: 40-55%. Realistic acceptance at NeurIPS D&B main: 15-20%.
- The cross-domain routing angle (Track A) makes this cs.LG-friendly enough for NeurIPS D&B, but the frontier paper alone is primarily an EO/systems paper.

**Best realistic venue: NeurIPS 2026 ML4EO workshop OR ICLR 2027 Datasets & Benchmarks track.**
NeurIPS D&B for this cycle is essentially closed (deadline likely passed). ICLR 2027 D&B or a strong domain workshop (ECML-PKDD 2026 applied ML track, IEEE IGARSS 2027) are honest targets. For arXiv-by-September: absolutely achievable, and arXiv is what matters for fellowship artifacts anyway.

**Acceptance odds at NeurIPS D&B 2027 / ICLR D&B 2027 (conditional on finding compelling cliff-edge):** 18-25%. This is because:
- The EO context is unfamiliar to most ML reviewers (friction).
- The "we trained CNNs and varied training data" story is not obviously generalizable to the ML community's concerns.
- The identifiability theory is strong but niche.
- The routing parallel is what makes it legible to CS-ML reviewers, but that's Track A, which is now the weaker track.

**Acceptance odds at IEEE TGRS or RSE (domain venue):** 35-50% conditional on CIs and clear differentiation from Stillinger 2019. This is where the work will be best understood.

---

## 5. Biggest Risks

**Risk 1 — The frontier is boring (most likely failure mode).** If training-snow removal causes a gradual, predictable degradation rather than a sharp cliff — or if CNNs stay robust even at 100% snow depletion because they generalize from texture/brightness — then the paper's main claim ("robustness is conditional") is vacuous. You'd just be showing that less training data gives worse models. Check Axis 1 first, before any writing.

**Risk 2 — CloudSEN12 doesn't have enough variety to show the frontier.** With only 99 clear-snow test patches (train split) and ~28 in the test split, the CIs will be wide at any FDR below 10%. You need the cliff to be above ~15% FDR to have statistical power. This is fixable by running on the full CloudSEN12+ or BigEarthNet snow patches, but that's scope expansion.

**Risk 3 — "Just use CloudScout" is the only needed conclusion.** A hostile reviewer will say: you showed CloudScout is robust; just deploy CloudScout everywhere; why do we need the frontier paper? Your rebuttal: (a) onboard compute budgets are fixed at launch, CloudScout is 3× heavier than band-stats; (b) the operator still can't VERIFY robustness post-deployment without the audit; (c) the failure frontier tells future mission designers what training conditions to hit before launch. This rebuttal is real but not airtight.

**Risk 4 — This is purely an ablation study.** If the contribution is "here's what happens when you vary training conditions of a small CNN," ML venues will correctly identify this as engineering rather than science. The identifiability theory and audit are what prevent this — they must be foregrounded, not buried in Section 4.

---

## 6. Fellowship Verdict

**Is Option A worth it as the artifact for a solo student targeting Anthropic Fellows / MATS / arXiv-by-September?**

**Honest answer: conditionally yes, but front-load the risk check.**

The identifiability theory (paper/identifiability.md, already written), the audit harness (T2/T1 done), and the T3 generalization results are a complete, standalone contribution that is already novel and already defensible. That work is done.

Option A's frontier experiments ADD to this — potentially significantly — but only if the cliff-edge result materializes. The expected compute cost (training 10-15 small CNNs on CloudSEN12 on an RTX4090) is 2-3 days of GPU time. The expected writing cost is ~1 additional section. If the cliff appears, the paper is stronger and more compelling. If it doesn't, the paper is unchanged (the existing contributions stand without the frontier).

**The right move:**
1. Run Axis 1 first (training-snow depletion, full range, 5 checkpoints) — one weekend.
2. If CNN FDR at 100% depletion is ≥ 15% with non-overlapping CI vs. full training: proceed with the frontier angle. Write the frontier as Section 4, with identifiability theory as Section 3 and audit as Section 5.
3. If CNN FDR at 100% depletion stays below 10% or CIs overlap: DROP the frontier framing. Write the paper you already have — identifiability + audit + CloudScout as evidence that the problem is architecture/training-dependent but the MEASUREMENT problem persists regardless. Still a real arXiv paper; still a credible fellowship artifact.

**Effort-to-payoff at arXiv tier:** High. The core theoretical and empirical work is done. The frontier experiment is 1 weekend + 1 week writing. The arXiv preprint is achievable by September regardless of which branch you take. The fellowship readers are not expecting a published ICLR paper — they want a serious research artifact with genuine novelty and honest execution. You have that already. Option A's frontier either strengthens it or doesn't, but it doesn't make or break the artifact.

**The one thing that would make this artifact genuinely strong for Anthropic Fellows in particular:** the identifiability framing. "We discovered that an AI system's false-discard rate is formally unidentifiable from its own outputs" is exactly the kind of AI safety / AI evaluation insight that an Anthropic Fellows reader will find compelling. Lead with that. The frontier and the audit are the empirical backing. Don't bury Proposition 2.

---

## Summary

| Dimension | Assessment |
|---|---|
| Core novelty | HIGH (identifiability + audit harness + CloudScout as conditional reference) |
| Frontier novelty | CONDITIONAL on cliff-edge result |
| Prior art risk | Stillinger 2019 (manageable, already differentiated) |
| Compute cost | 2-3 days GPU (Axis 1+2), Mac/RTX4090 feasible |
| Best venue | arXiv preprint (Sept deadline) + ICLR D&B 2027 or IEEE TGRS |
| Honest acceptance odds (top venue) | 18-25% with frontier; 10-15% without |
| Fellowship verdict | STRONG artifact regardless; frontier is upside not prerequisite |
| Kill condition | Run Axis 1 first; if cliff-edge absent, write without frontier angle |
