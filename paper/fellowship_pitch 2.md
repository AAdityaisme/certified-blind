# Fellowship-application summary (drop-in)

Plain-language framings of the research artifact for applications (Anthropic Fellows, MATS, etc.).
Direct, no hedging. Run through `humanizer` before submitting; strip anything that reads generated.

## One-liner
I found that AI systems which *irreversibly* discard data — onboard satellites, content filters — can be
made to silently destroy a targeted subpopulation of that data undetectably, because once the data is gone
you can't even measure what was lost. I proved this is unidentifiable in principle, demonstrated it across
three domains, and built a cheap defense.

## One paragraph
Many deployed AI "gatekeepers" decide what data survives: a satellite CNN downlinks only the scenes it
judges cloud-free; a moderation model removes inputs at ingestion. When that decision is irreversible, I
show the model's false-discard rate is *unidentifiable* from the data that survives — the discarded data is
missing-not-at-random, so no amount of retained-data auditing can certify the harm is above zero. That turns
a known, detectable failure (a model that quietly harms a rare subpopulation while its aggregate accuracy
looks perfect) into an *undetectable* one, because every standard defense needs the target group's data,
which no longer exists. Across satellite Earth observation, content moderation, and LLM routing I built
*certified* gatekeepers — passing every standard accuracy check — that silently destroy up to 79%, 93%, and
effectively all of a targeted slice. I gave a scaling law explaining why *rarity* is the hiding mechanism,
and — because retained-data audits provably can't work — a defense that injects a tiny external reference
(≈10 labeled examples) and detects the harm at 100% power. I stress-tested the whole thing adversarially,
including against an adaptive attacker and my own overclaims (two of which I caught and corrected).

## Why it matters (safety framing)
This is an eval-integrity and undetectable-harm result. As AI systems are given authority to discard,
filter, and gate data at scale, "the aggregate metrics look fine" becomes an unsafe certification: the harm
can be concentrated where the metrics can't see it and the evidence can't be recovered. The contribution is
to name irreversibility as the property that defeats measurement, prove it, and show the harm is bounded
*before* the fact rather than audited after.

## What I actually did (credibility bullets)
- Formalized the unidentifiability (missing-not-at-random → Manski partial identification, lower bound 0).
- 32 experiments across 3 domains; real onboard model (ESA Φ-Sat-class CloudScout) + a fine-tuned
  transformer, not toy classifiers.
- A three-tier defense (labeled probe → discovery scan → label-free cross-detector) with each tier's
  failure mode quantified, and an adaptive-adversary bound.
- Ran an adversarial audit (including a stronger model as red-team), caught and corrected my own overclaims,
  and made the whole artifact reproducible (auto-generated results table + figures + run guide).

## Positioning (honest)
The attack primitives are standard data-poisoning; the contribution is the *framing* (irreversibility as the
axis that removes auditability), the *identifiability* result, the cross-domain demonstration, and the
defenses. Not "we caught a deployed system" — a threat model with a concrete, reproducible instance.
