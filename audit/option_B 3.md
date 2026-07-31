# Option B Assessment — Theory + Method Paper on Irreversible Gatekeeper Identifiability
*Written 2026-06-27. Honest assessment for a solo community-college student targeting ~Sept arXiv, ICLR/NeurIPS-D&B.*

---

## 1. Strongest Honest Contribution Sentence

> When an AI gatekeeper permanently discards data before human inspection, its false-discard rate is MNAR-unidentifiable from retained data alone — the sharp Manski lower bound is exactly 0, so you cannot even establish that harm occurred. We characterize the three identification regimes (retained-only = bound [0,U]; pre-triage probe = point identification at cost O(1/sqrt(n·P(C=1))); cross-detector consensus = biased rate estimator but effective individual-loss flagger with 95–97% recall ceiling), and demonstrate the audit harness across deployed satellite cloud-masking systems.

What that sentence does honestly: it states a formal result (Props 1 and 2 in identifiability.md are complete), characterizes the identification regimes explicitly, and makes the empirical grounding specific. It does not claim "deployed systems are failing NOW" — which T1b refuted for CloudScout.

---

## 2. Is the Identifiability Result Novel Enough to Carry a Paper? The Precise Delta.

### What the prior art already has

**Choe, Gangrade, Ramdas (2305.10564):** Proves unidentifiability for abstaining classifiers — when abstentions are deterministic, the score on the abstained set is unidentifiable. This is structurally the closest theorem. They have: the MNAR observation, the "cannot certify performance on withheld inputs" result, and the formal abstaining-classifier framing.

**Rambachan, Coston, Kennedy (2212.09844):** Has the cleanest formal non-identification proposition in the human-in-the-loop econometrics framing: P(Yi*=1 | Di=0, Xi) is not point-identified. Partial identification bounds are present.

**Lakkaraju et al. (KDD 2017):** Canonical "selective labels" — false-reject outcomes are fundamentally unobservable. No formal theorem, but the conceptual claim is unambiguous.

### The precise delta — what you add vs. what exists

| Claim | Exists in prior art? | Your delta |
|---|---|---|
| MNAR observation for gatekeeper + unidentifiability | Yes (Choe, Rambachan) | None |
| Sharp Manski bounds [0, q/(a(1-q)+q)] | Implicit in Rambachan | Derivation is clean and explicit; Rambachan's is in a different parameterization with covariates. This is an application, not a new theorem. |
| Lower bound = 0 precisely | Implicit in Choe | You make it explicit and name the consequence (cannot certify harm > 0). Delta: pedagogical precision, not a new result. |
| Pre-triage probe identification strategy | Not in prior art for this setting | Genuinely new analysis: sample complexity curve (n~200-300 for CI excluding 0), bypassing requirement, effective sample = n·P(C=1). This is a usable method component. |
| Cross-detector consensus as a biased rate estimator vs. individual-loss flagger | Not in prior art | The discrimination/calibration separation (AUC 0.83-0.93 for flagging; biased 4x for rate) is a concrete empirical result. The role distinction is a method contribution. |
| EO/satellite domain instantiation | Not in prior art | Clusters B, C, F in priorart_onboard.md confirm: nobody applies this to irreversible onboard triage. Wąsala et al. has MNAR language for atmospheric missingness, which is passive, not algorithmic. |

**The honest verdict:** The core identifiability result — MNAR + Manski bounds — is not a new theorem. It is a clean application of existing machinery (Rambachan's partial-ID framework, Choe's abstaining-classifier unidentifiability) to a new domain. The paper's theoretical contribution is the explicit domain mapping, the probe sample-complexity analysis, and the discrimination/calibration role-separation for the audit. These are real but they are method/analysis contributions, not mathematics that ML theorists would call novel.

What IS genuinely novel: the complete characterization of the three identification regimes for this specific setting (retained-only / probe / consensus), the explicit sample-complexity guarantee for the probe, and — most practically — the full audit harness demonstrated on real deployed systems. No one has done this for irreversible EO triage. But a theory-forward framing will put this delta in front of reviewers who are looking for new theorems, and it does not have one.

**Risk level: high if positioned as "new theory"; moderate if positioned as "formal characterization + domain transfer + method."**

---

## 3. Cleanest Minimal Theoretical Contribution + Required Empirical Validation

**Minimal theory package (what is defensible):**

1. Props 1 & 2: MNAR framing + sharp Manski bounds [0, q/(a(1-q)+q)] with lower = 0. State clearly this applies the Rambachan/Manski machinery to a new domain; do not overclaim.
2. Probe sample-complexity analysis: formal CI width and "fraction of runs excluding 0" as a function of n. This is new analysis not in prior art.
3. Role theorem (informal): consensus identifies individuals but not the rate; probe identifies the rate but requires gatekeeper bypass. This is a practical decision theorem for operators — when to use which.

**Empirical validation needed:**

- 2 domains showing the bound ([0,U], oracle inside): satellite cloud triage (done, T1) + LLM routing (T4 audit parallel, AUC 0.785 for routing). Two domains validate generality.
- Probe recovering the rate: done (T2/T1 calibration; probe-calibrated median abs err 0.015 at n=100). Need this for the routing domain too (feasible; the LLM routing discard set is observable in simulation).
- Consensus as individual-loss flagger: done (AUC 0.83-0.93, recall ceiling 95-97%).
- Bootstrap CIs on audit AUCs (currently missing for the test-split numbers; critical before any submission).

**What you do NOT need:** a novel theorem. The delta is the domain transfer + complete method + empirical validation.

---

## 4. Honest Tier + Best Venue

**Venue fit:**

| Venue | Fit | Realistic odds | Why |
|---|---|---|---|
| UAI 2027 | Moderate | 10-15% | UAI likes causal/identification framing; Rambachan's work is squarely in their tradition. A "partial identification applied to ML deployment" paper is legible here. Risk: reviewers will ask for sharper theory. |
| AISTATS 2027 | Moderate | 10-15% | Methods+theory paper is their wheelhouse; EO application may be too narrow. Routing parallel helps. |
| NeurIPS D&B 2026 | Good fit | 15-25% | Evaluation methods + benchmark methodology. The "standard metrics can't certify gatekeeper errors" framing is exactly D&B scope. This is the highest-probability path. |
| ICLR 2027 (main) | Poor fit for theory-forward Option B | <10% | ICLR wants empirical ML results or architecturally novel work. A partial-identification application paper is not a good fit for their main track. |
| FAccT / EAAMO | Moderate | 15-20% | The "unauditable systems" frame has clear sociotechnical stakes. But the venue requires a policy/fairness connection that the satellite setting provides imperfectly. |
| arXiv first, then revise | Best starting point | — | Sept arXiv as fellowship artifact is achievable. Use NeurIPS-D&B 2026 deadline to force rigor. |

**Honest tier with current evidence:** Workshop-to-findings tier. The theory is solid but not novel enough to anchor a main-track submission on its own. The empirical side (T1b showed CloudScout is robust) weakened the flagship instantiation. Without a concrete "deployed system IS failing and here's why you can't see it," the theory is harder to motivate viscerally.

**What changes the tier:** Adding KappaMask/Fmask as the primary failing systems (they DO fail, 23-63% false discard on snow, these are GROUND processors not onboard — honest limitation), plus showing the probe and consensus harness working on these. The caveat is that ground processors discard reversibly, which partially weakens the "irreversible" argument. Need to be precise: the theory applies to irreversible systems; KappaMask/Fmask are instantiated as ground-side processors where the data exists but the operator has no standard metric to catch the failure.

---

## 5. Biggest Risk

**"It's a known result wearing a satellite hat."**

This is the most likely rejection framing at UAI/AISTATS. A reviewer who knows Rambachan (2212.09844) or Choe (2305.10564) will read Props 1-2 and say "this is just Manski bounds applied to a new domain; the formal content is not new." The response — "but nobody did it for EO triage" — is true but not a defense against a theory-focused reviewer who grades on mathematical novelty.

Secondary risk: CloudScout being robust (T1b) means the paper's most compelling instantiation — "a deployed onboard system is silently losing data right now" — is false for the flagship. The paper can still be written honestly (theory of a potential risk, demonstrated on brittle detectors), but the "so what" is weaker. A reviewer will ask: if the real deployed system doesn't fail, why do we care about the identifiability problem in this domain?

The honest answer: because (a) other deployed detectors (KappaMask 63% snow false-discard) DO fail, even if not onboard; (b) the evaluation procedure for onboard systems is structurally broken regardless of whether the current system happens to be robust; (c) lightweight detectors deployed on future constrained-hardware satellites will fail unless trained on snow. But this requires more careful framing than the original pitch.

---

## 6. Fellowship Verdict: Does Option B Play to or Against Your Strengths?

**Against.** Here is the honest assessment:

A theory-forward partial-identification paper is written to impress reviewers who will check whether your Propositions are tight, whether the bounds are sharp, and whether you've cited the right econometrics literature (Manski 1990, Balke-Pearl 1997, Rambachan et al.). Those reviewers are looking for someone who lives in identification theory. You are a sophomore at DVC with no formal stats track record and no advisor in causal inference or econometrics.

The delta you actually have — domain transfer + method + empirical validation — is better communicated in Option A or a hybrid framing: "empirical paper with a formal backbone." The identifiability theory should be in the paper as Appendix / Section 3, not as the lead. It is what makes the audit harness principled, not what makes the paper interesting.

What plays TO your strengths: the satellite data (real systems, real failure modes, visceral stakes), the working code and experiments (you built the audit harness and it runs), and the honest empirical story (brittle detectors fail; real deployed CNNs don't; the harness catches the brittle ones; here is the identifiability reason you couldn't see this before). That is a paper a solo sophomore can own.

**Verdict: do not lead with theory. Use the theory as the mechanism that makes the method principled.** The strongest artifact for fellowship committees — who are not econometricians — is a paper that shows (a) a real problem, (b) clean experiments, (c) a method that works, and (d) formal grounding. That is Option A with identifiability.md as the backbone, not Option B.

If you are targeting MATS or Anthropic Fellows specifically: they care about AI safety framing. The "unauditable gatekeeper" frame is directly AI-safety-adjacent. But they will be more impressed by a paper that demonstrates the problem empirically and provides a working solution than by a theory paper that proves a bound they will assume is an application of Manski.

---

## Summary Verdict

Option B is not dead — the identifiability material belongs in the paper. But leading with theory when your delta is domain-application + method + empirical validation is a mismatch of framing and evidence. The theory is the foundation; it is not the house.

**Recommended path:** Write the paper with the full formal backbone from identifiability.md as Section 3 (clearly attributed to Manski/Rambachan machinery, explicitly noting the domain contribution), but lead with the audit method and empirical results. Submit to NeurIPS-D&B 2026 or UAI 2027. Honest odds: 15-20% at D&B if the bootstrap CIs and CloudScout reframing are done cleanly. As an arXiv artifact for fellowship applications, it is excellent regardless of venue outcome — the formal identifiability argument is a genuine intellectual contribution even if it is an application, and it is precisely the kind of work that distinguishes a fellowship application from a project report.
