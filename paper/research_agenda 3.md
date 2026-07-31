# Research agenda — what "Certified Blind" opens up

Forward-looking follow-ups this paper sets up. Doubles as (a) the paper's Future Work section and (b) a
fellowship-narrative artifact: the contribution is a *program*, not a one-off. Each direction is concrete
(a next paper), with why it matters and a first experiment.

## 1. A certification standard for irreversible gatekeepers ("bound before the fact")
The paper's remedy is "you must inject an external reference because you can't audit the survivors." The next
step is to turn that into a *deployable certification protocol*: what should ESA/Planet (onboard EO) or a
platform (content ingestion) be required to log or probe, and at what cost? Concrete deliverable: a
minimal-overhead onboard scheme — downlink a small *random* (unfiltered) sample every N orbits as the
external reference — and quantify the bandwidth cost vs. the false-discard-rate confidence it buys. First
experiment: extend the probe sample-complexity result into a bandwidth-vs-detection-power curve for a real
downlink budget.

## 2. Provable lower bounds for the adaptive arms race
We showed the defense *caps* stealthy harm at ≈τ empirically. The theory question: given a defender who can
probe k slice examples at threshold τ, what is the *provable* maximum harm an adaptive attacker can inflict
undetected, as a function of (k, τ, slice prevalence, base rate)? This is a clean minimax problem. Deliverable:
a tight game-theoretic bound; the empirical stealth-ceiling (~0.37 at τ=0.35) becomes a special case.

## 3. Discovery without an enumerable protected set (open-world slices)
Our discovery defense assumes the protected set is enumerable (land-cover classes, identity groups). The hard
open case: an attacker targets an arbitrary *latent* subpopulation (e.g., a learned cluster) with no name.
Direction: mine the suspect model's own representation or cross-model disagreement to *surface* candidate
attacked slices, then probe them. First experiment: cluster the retained-data embeddings, probe the clusters
with highest suspect-vs-panel disagreement, measure discovery power vs. an unknown latent target.

## 4. Irreversibility beyond triage — a general taxonomy
Onboard EO triage and content ingestion are two instances; the axis is general. Autonomous medical triage
that discards "normal" scans, edge-device filtering, log-retention policies, and RLHF data curation are all
irreversible gatekeepers. Deliverable: a taxonomy of deployed irreversible-gatekeeper systems scored on
(prevalence of a targetable slice, aggregate-metric footprint, auditability), predicting which are most
exposed. This is the "where does this bite in the wild" survey a policy/governance audience wants.

## 5. The natural-bias question at deployment scale (the honest open gap)
Our incidental-harm result is modest and partly synthetic (real toxic-bert natural bias ≤1.8×). The open
empirical question: do *deployed* pipelines exhibit certified targeted over-suppression from ordinary data
imbalance, at scale, with no attacker? Direction: audit real deployed moderation/triage systems (where slice
ground truth is recoverable) for the footprint-hidden slice harm the theory predicts. This is the study that
would move the "no attacker needed" claim from controlled-setting to field-observed.

---
Framing for the fellowship: #1 (deployable certification) and #4 (taxonomy) are the governance/policy-facing
directions; #2 and #3 are the technical-depth directions; #5 is the honest empirical gap that a field study
closes. Together they define a multi-paper program on *auditability under irreversibility*.
