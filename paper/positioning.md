# Related Work & Novelty Positioning

Written 2026-07-04 from a literature pass, to answer the sharpest reviewer objection:
"this is just subpopulation backdoors + textbook Manski." It is not — and here is
precisely why, grounded in the closest prior work.

## The two ingredients ARE established (concede this up front)

1. **Subpopulation / evasive backdoors that preserve aggregate accuracy.** Well-studied.
   - Subpopulation Data Poisoning Attacks (Jagielski et al., arXiv 2006.14026) — availability attack
     that degrades a specific subpopulation while overall accuracy is ~unchanged.
   - LOTUS (Cheng et al., arXiv 2403.17188, CVPR'24) — evasive backdoor via sub-partitioning, shown
     resilient against 13 SOTA defenses.
   - BadEdit, LADDER, architectural backdoors — all preserve clean-input performance.
   ⇒ "a model can hide targeted harm behind healthy aggregate metrics" is NOT our novelty.

2. **MNAR / partial identification.** Textbook (Manski bounds, nonignorable missingness). Subgroup
   effects under nonignorable missingness are not point-identified — classical statistics.
   ⇒ the identifiability math is NOT our novelty.

## The genuinely novel contribution: irreversibility breaks the defense's core assumption

Every defense in ingredient (1) — trigger inversion (Neural Cleanse, ABS), slice-accuracy audits,
subpopulation-robustness checks — **assumes the defender can obtain the target subpopulation's data**
(to query the model, invert triggers, or measure slice accuracy). That assumption holds for ordinary
classifiers.

It **fails** for an *irreversible AI gatekeeper*. When an onboard satellite CNN discards "cloudy"
scenes before downlink, or a content filter drops inputs at ingestion, the discarded slice's data is
**permanently destroyed** — confirmed in the EO literature: "once data is discarded onboard based on
cloud detection algorithms, it cannot be recovered for ground truth validation" (autonomous-tasking /
Φ-Sat-class onboard triage). So the targeted harm is not merely *evasive to aggregate accuracy* (LOTUS)
— it is **unidentifiable from the retained data** (our Manski application): you cannot even *construct*
the slice test set the existing defenses require, because the evidence was thrown away.

**That intersection is the paper.** Concretely, the contributions are:
1. **Framing:** identify *irreversibility* as the axis that turns a known-but-detectable attack class
   into an *undetectable* one, because it removes the data all existing defenses assume.
2. **Formalization:** the retained-data false-discard rate is MNAR ⇒ Manski-only-partial-identified,
   lower bound 0 (`paper/identifiability.md`) — so retained-data audits provably cannot certify harm > 0.
3. **Concrete instances across the irreversibility axis (3 domains):** onboard EO triage (irreversible,
   real CloudScout arch), content moderation (semi), LLM routing (recoverable) — a certified gatekeeper
   hides 79% / 93% / total slice harm, invisible to aggregate metrics.
4. **A scaling law for invisibility:** footprint ≈ prevalence × slice-harm (`detectability_bound.json`),
   which *explains* why rarity gates invisibility (a property a plain backdoor paper doesn't articulate).
5. **Defenses designed for the retained-data-blind setting:** because you can't use the slice's own
   (destroyed) data, we (a) inject a tiny labeled reference probe (k=10), (b) scan the finite protected
   set to *discover* the slice (120 labels), (c) use an independent detector panel label-free — and we
   quantify when each fails (benign-difficulty gap; majority-blind panel).

## One-sentence positioning

*Not "backdoors exist" and not "MNAR is unidentifiable," but: irreversible AI gatekeepers form a
deployed class where targeted subpopulation harm becomes unidentifiable from the data that survives, so
the standard subpopulation-backdoor defenses (which all require the target slice's data) cannot apply —
we formalize this, exhibit it across the irreversibility axis, and give defenses that inject an external
reference instead.*

## Closest-competitor delta table

| prior work | what it shows | why it's not us |
|---|---|---|
| LOTUS (2403.17188) | evasive backdoor, beats 13 defenses | those defenses still have the data; assumes model+data access |
| Subpopulation poisoning (2006.14026) | degrade a subgroup, aggregate intact | detectable with the subgroup's test set; no irreversibility/identifiability |
| Manski / MNAR | partial ID under nonignorable missingness | pure statistics; not applied to AI gatekeepers or defenses |
| Fairness / subgroup robustness | aggregate metrics hide subgroup gaps | assumes you can measure the subgroup; reversible setting |

## Deeper sweep (2026-07-04) — top novelty risk DE-RISKED

A second, targeted pass ("one-way filtering audit / destroyed samples / gatekeeper partial-ID") surfaced
ADJACENT work but no scoop:
- Consistent Range Approximation for Fair Predictive Modeling (arXiv 2212.10839) — partial-ID for fairness
  under missingness, but a REVERSIBLE prediction setting; closest statistical neighbor, not our destruction/
  security framing.
- Access Denied: Meaningful Data Access for Quantitative Algorithm Audits (arXiv 2502.00428) — audit data
  ACCESS (regulatory), not "the data is physically destroyed and thus unidentifiable."
- The Gatekeeper Effect (arXiv 2312.17167 / Mgmt Sci) — hiring/screening gatekeepers, economics — not ML
  data destruction.
- Sample-constrained partial identification for selection bias (PMC10183833); G-AUDIT dataset-bias auditing
  — all assume the samples still EXIST / are accessible.
None combines irreversibility + destroyed-data unidentifiability + certified-targeted-harm + defenses. The
core framing (irreversibility as the axis that removes auditability) appears unoccupied after two sweeps.

## Third sweep (2026-07-06, prompted by mock-review W2) — novelty still holds; two more neighbors

- **Content-moderation auditing** is an active area (DSA Transparency Database audits; takedown-delay audits,
  arXiv 2502.08841; fairness/identity audits of moderation) — but it *assumes the removed content is logged
  or observable* (transparency reports, takedown records). It audits the *reversible* case. None formalize
  the irreversible case where the removed data is destroyed and unrecoverable. This sharpens, not threatens,
  our contribution.
- **Sample-level ML-pipeline traceability** ("Fine-Grained Traceability for Transparent ML Pipelines," arXiv
  2601.14971) argues pipelines lack verifiable records of which samples were used, hindering "post-hoc
  forensic reconstruction." This is the closest *problem-statement* neighbor — but it proposes a provenance
  *solution* (record everything before the fact), which is exactly the shape of our remedy ("bound before
  the fact / inject an external reference") rather than a competing threat framing. Cite as the
  record-everything alternative.
- Machine unlearning / right-to-be-forgotten (removing data on request) is unrelated (deliberate deletion of
  known data, not selection-on-outcome destruction).

Across THREE targeted sweeps we found no prior work formalizing *irreversibility itself* as the property that
removes auditability. We state this explicitly in §2 and treat a full submission-time citation-chase (esp.
2601.14971, 2212.10839, 2502.00428) as the top remaining task.

## Honest residual novelty risks (do not oversell)

- The empirical attacks are standard label-flip/poisoning; the novelty is the *framing + setting +
  identifiability + defenses*, not a new attack algorithm.
- Citation-chase on the two closest neighbors DONE (2026-07-06): arXiv 2212.10839 = partial-ID for FAIRNESS
  on biased/incomplete data via "possible repairs" (reversible prediction setting, does not cover data
  destruction); arXiv 2502.00428 = auditor ACCESS restriction (data still exists, withheld — not destroyed).
  Neither formalizes irreversibility-defeats-auditing; the core distinction holds against the nearest work.
  A broader forward-citation sweep before camera-ready is still prudent but no longer a load-bearing gap.

Sources: arXiv 2403.17188 (LOTUS), arXiv 2006.14026 (Subpopulation Poisoning), EO onboard-triage
literature (autonomous tasking / Φ-Sat-class cloud triage discarding pre-downlink).
