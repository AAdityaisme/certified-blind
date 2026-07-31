# How to improve the updated paper — "Certified Blind"
*(pasted into storage-cleanup session 2026-07-12; filed here so it isn't lost)*

Both updated versions (main.pdf 12pp / main_gov.pdf 13pp) are audited-clean: all five prior nits are fixed and now internally consistent. The suggestions below are about impact, readability, and reviewer-proofing — not correctness. Ordered by expected payoff-per-effort.

Metrics for reference: security abstract = 364 words; governance abstract = 242 words; bodies ~11.2k / ~12.0k words. Density is the paper's main presentation risk.

## A. HIGHEST PAYOFF — prose density & sentence architecture

The single biggest weakness is readability. The ideas are excellent but the prose routinely packs 3-4 claims into one 60-80-word sentence with nested em-dashes and parentheticals. A tired reviewer loses the thread and undervalues the work.

1. Cut the security-version abstract from 364 → ~200 words. IEEE norm is 150-250. The governance abstract (242 w, Wald hook) is the better model — it leads with an image, states the result, names the remedy. The security abstract currently front-loads six mechanisms before the reader knows the thesis. Lead with the one-sentence claim ("an irreversible gatekeeper's false-discard rate is unidentifiable from retained data"), then the headline number, then the remedy. Move the 4.7×/14×/69× selectivity breakdown and the Prop-3 label-cost aside into the body.

2. Break the em-dash habit. Spot-count: the Related Work and Limitations sections average >2 em-dashes per sentence. Convert half of the parenthetical asides into separate sentences. Rule of thumb: at most one em-dash pair per sentence. This alone will materially raise perceived clarity.

3. Paragraph-break §II (Related Work). It is currently one ~1.5-column wall. Split into labeled mini-paragraphs by theme — you already bold the lead-ins ("Backdoor and subpopulation attacks", "Partial identification…"); give each its own paragraph so the positioning is scannable. Same treatment for the Limitations section.

## B. STRUCTURE — the paper is dense with results; help the reader navigate

4. Add a boxed defense Algorithm. The stated contribution is a deployable remedy, but the three-tier defense lives in prose. A one-column Algorithm box ("Auditability-preserving certification: (1) pre-commit size-k probe per stratum; (2) flag if observed FDR ≥ τ; (3) discovery scan over protected set; …") makes the recipe adoptable and is what a practitioner will screenshot. High impact for the "defense is the contribution" framing.

5. Consolidate the three framings of the Θ(k/p) result. Thm. 2 (Chernoff), the observability/Fisher–Cramér–Rao reading (§VII-e), and Prop. 3 (martingale) are three lenses on the same bound. Impressive breadth, but a skeptical reviewer may read it as padding. Keep Thm. 2 + Prop. 3 as the load-bearing results; compress the observability reading to a short remark (it's elegant framing, not a new bound).

6. Compress the satellite hedging. The satellite case is qualified as "conservative / not the flagship / small n / metadata-predictable / clears the bar in only 2/5 seeds" in at least five places (§IV, §V, §VIII, and figure captions). One clear statement of its role — "flight-hardware proof of the certified-harm gap; not the unidentifiability claim" — plus a single limitations line is enough. Repetition currently reads as defensiveness about the paper's own strongest visual.

7. Consider moving Fig. 1 (footprint heuristic) to an appendix. It validates a quantity the text explicitly calls "a back-of-envelope heuristic, not a theorem," and two of its four points are "definitional." It is the least load-bearing figure; the space could go to the Algorithm box or a multi-seed panel (item 9). Fig. 2 already carries the "dashboard lies" message more forcefully.

## C. RIGOR — reviewer-proofing the empirics

8. The single-seed results are the most attackable surface. Limitations already flags that the dose-response, spectrum, systemic-bias, and ratchet characterizations are single-seed TF-IDF. A reviewer will ask for error bars. If a multi-seed rerun is cheap (the code exists — {42,7,123,2024,99} is already used elsewhere), add shaded CIs to Figs. 3, 5, 6. Even 3 seeds converts "anecdote" into "trend" in a reviewer's eyes.

9. Make the assumption ledger a table. The threat model's assumptions — which are tested (probe content-indistinguishability, AUC 0.50) vs assumed (channel/timing blindness), and the three that bound Thm. 1 — are scattered across §III, §VII-b, and §VIII. A small "Assumptions: tested / assumed / out-of-scope" table would preempt the "you assumed the hard part" critique and showcase the paper's unusual honesty.

10. State the code/model provenance for the '43%'-type numbers explicitly. You now print FPR 2.04%→2.92%. A one-line pointer ("all headline numbers are golden values in results/*.json; see make verify") in the artifact paragraph closes the loop between prose and the reproducibility tier you already built.

## D. VERSION-SPECIFIC

**Governance (main_gov.pdf):**

11. Prop. 4 overlaps §VI's game-theoretic reading. The (1−f)^T patient-attacker result appears both in §VI ("multi-generation adversarial game") and as Prop. 4 in §XI. Formalizing it as a proposition is good; but state it once and cross-reference, or explicitly note "Prop. 4 formalizes the §VI observation" so it doesn't read as the same result told twice.

12. "Differential privacy with the valence inverted" (§III-g) is a strong rhetorical claim. You correctly flag it as an analogy (deterministic censoring, not a randomized mechanism). A DP-expert reviewer may still bristle at "ε=0". Consider softening to "structurally analogous to the ε→0 limit" and adding one sentence on why the analogy is not tight (no privacy loss distribution here). Low effort, removes an easy objection.

13. The policy section (§XI) is strong but citation-light on the legal claims. The spoliation-doctrine and SOX §802 analogies would benefit from a primary legal citation each (not just the Balkin fiduciary ref), if the venue is governance/policy.

**Security (main.pdf):**

14. The security version currently has no forward pointer to the governance framing's accountability payoff. If both are going out, that's fine (distinct venues) — but the security abstract's closing ("capping achievable stealthy harm near the audit threshold") is a weaker mic-drop than the governance version's. Consider ending the security abstract on the unidentifiability result itself, which is the novel core.

## E. SMALL POLISH

15. "the class used to curate training corpora" and "increasingly used in curation pipelines" recur ~4× as a hedge for using distilbert/TF-IDF as stand-ins. State the proxy argument once, in the setup.

16. Fig. 4 caption defines the ratios two ways (∆FPR-based; nearest exact, mean varies). It's correct but dense for a caption — move the parenthetical to the body.

17. Table I "Min probe / discovery" row mixes k and label counts (k=10 / 120 labels). Add units in the header so the column is self-reading.

18. Consider a single sentence in the intro naming the venue-appropriate "so what": for security = a new attack surface; for governance = the first formal treatment of accountability under evidence destruction. The gov version does this; the security version buries it.
