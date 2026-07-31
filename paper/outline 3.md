# Paper outline — What the Gatekeeper Throws Away

Two-domain. ~9–10pp. Spend equal time on abstract / intro / Figure 1 / everything else.

1. **Abstract** (5-sentence)
   1. AI gatekeepers (route/keep-or-discard classifiers) reach high accuracy via surface-form proxies, not intent.
   2. These decisions control spend and, in orbit, permanently destroy data no one can audit.
   3. Across LLM routing (RouterBench) and onboard satellite triage (CloudSEN12) we compare surface vs intent-aware gatekeepers and introduce surface-invariance + intent-sensitivity tests.
   4. Surface gatekeepers match headline accuracy yet discard snow, desert, and active-fire scenes as "cloud," and flip under benign perturbation.
   5. **Headline:** under irreversible triage the surface model silently destroys Z% of valuable disaster scenes with no drop in its accuracy score; our audit harness flags them at P/R = ...

2. **Introduction** (≤1.5pp) — gatekeepers everywhere; the surface shortcut; the irreversibility twist (recoverable routing vs permanent orbital discard); contribution bullets C1–C4; anonymized routing-origin hook.

3. **Figure 1** — cross-domain concept: two gatekeepers, identical accuracy bars; under perturbation/snow-fire the surface one's decisions scatter and delete the wildfire, the intent-aware one holds. Draft before prose.

4. **Related work** — routing · onboard EO + cloud masking (cite the documented bright-surface failures) · shortcut learning · Goodhart/reward-hacking · eval/construct validity + invariance testing.

5. **Setup / Method**
   - Gatekeeper formalism (decide what flows/survives; recoverable vs irreversible).
   - Track A: RouterBench labels + four routers.
   - Track B: CloudSEN12 triage label + brightness vs spectral models; SEN2FIRE fire eval.
   - Intervention defs: SIV, IS (domain-general).
   - Audit harness (A1).

6. **Results**
   - 6.1 C1 accuracy parity, both domains (Table 1). The trap.
   - 6.2 C2 interventions: surface high SIV / low IS (Table 2) + **fire-deletion gallery (Fig 2)** — the visceral object.
   - 6.3 C3 irreversibility: routing shift collapse vs triage silent-discard cost; accuracy blind to it (Fig 3).
   - 6.4 C4 audit harness recovers the hidden bad discards (Table 3).
   - 6.5 cross-domain synthesis table.

7. **Discussion** — gatekeeper layer as an unmonitored shortcut surface; intent-invariance as an acceptance criterion; irreversibility makes eval-integrity existential, not just economic.

8. **Limitations** — intent-aware reference is a contrast not a cure; two domains; paraphrase fidelity; binary keep/discard; brightness model not a strawman (param-matched).

9. **Conclusion** — restate; next steps (more gatekeeper domains: content moderation, medical triage, autonomous-vehicle perception gating).

10. **Broader impact** — honest eval of orbital triage prevents silent loss of disaster data; reduces wasted inference spend; LLM-writing disclosure.

11. **Appendix** — multiclass routing tier, τ sensitivity, full hyperparams/seeds, minimal-pair + probe-set construction, prompts, band ablations.
