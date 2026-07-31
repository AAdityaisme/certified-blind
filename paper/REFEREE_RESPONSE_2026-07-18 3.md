# Response plan — external referee report, 2026-07-18

**Bottom line: this is a high-quality, largely correct review.** Of the 8 major concerns: 6 are true,
1 is true-but-already-handled-in-the-text (3.3), 1 is a defensible reviewer preference we should decline
with a rationale (3.4). Of the 6 minors: 2 warrant fixes, 1 is a no-op (already verified), 3 are
decline/optional. Nothing in it contradicts the results; every number the referee re-derived matches ours
(their h\*/Prop-1/footprint recomputations agree with `results/*.json` golden values). The two suggestions
with real teeth — measure flagship metadata-opaqueness (3.5) and run the ratchet end-to-end (3.6) — are
**experiments**, which the scope-lock currently forbids; they're flagged below as the only two unlock
candidates worth considering before the Sept deadline.

Legend: ✅ true, fix cheap · 🟡 true, part of the paper's nature (respond, don't fix) · 🟨 partially true /
already handled · ❌ decline with rationale · 🔬 true, fix requires an experiment (scope-lock decision).

---

## Strengths (their §2) — all six are accurate, no inflation

Their verification table reproduces our numbers exactly (h\*(15,.35,.5)=0.370; h\*(10,.35,β)=0.355/0.261/0.188;
non-monotone k-sweep; KappaMask footprint 0.0117×0.626=0.732pp — matches `detectability_bound.json` row 1).
The strengths they name (aggregate-blindness vs unidentifiability separation, honest self-assessment,
recoverable control design, optimality-backed defense, reproducibility harness) are the load-bearing ones we'd
want a referee to see. Nothing to do here except note the review validates the paper's core positioning.

---

## Major concerns

### 3.1 "Alarm outruns the no-attacker evidence" — ✅ TRUE, cheap writeup fix
**Verdict.** Correct observation. The 93%/79% headlines are attacker-injected; the no-attacker evidence is
deliberately modest (≤1.8× deployed disparity, 3–5× annotation bias, ~9% ratchet steady state). The body is
scrupulous; the security abstract never actually says the word "poisoned" (the gov abstract does).
**Partial pushback for rebuttal.** At a security venue, foregrounding the adversarial ceiling is the genre —
the attack IS the contribution. The calibration concern bites hardest at FAccT-style venues.
**Fix (2 edits, ~15 words).**
1. Abstract: "a certified toxicity/quality classifier" → "a certified toxicity/quality classifier, poisoned
   at training time," — makes the adversarial premise explicit in the same sentence as the 93%.
2. Abstract, after the CloudScout sentence, add one calibrating clause: "(organic label bias alone yields
   certified but far smaller, 3–5×, over-removal)". Keeps the alarm honest without deflating it.

### 3.2 "Formal novelty is modest" — 🟡 TRUE, and it's the nature of the paper; respond, don't fix
**Verdict.** Correct, and the paper already says it itself ("the partial-identification bound for θ is
classical; the attack surface, the label-complexity result, and the defense are new"). The contribution is
framing + synthesis + operational consequence + defense package. That is what SaTML's CFP rewards
(`venue_strategy.md`: "rewards a sharp threat framing over massive empirics").
**Fix.** None to the claims. Optional 1-line sharpening of the Contributions paragraph to pre-empt the
"repackaging" probe: state plainly that we claim no new identification theory — the new objects are the
attack surface, Prop 3's Θ(k)/Ω(k/p) separation, and the capped-defense package. (The text already ~says
this in §II; making it a Contributions-level sentence closes the door.)

### 3.3 "'No audit can catch it' narrower than advertised" — 🟨 MOSTLY ALREADY HANDLED
**Verdict.** The qualifier the referee asks for already travels: the abstract says "no **retained-data**
audit can certify"; the conclusion says "beyond the reach of every defense **that assumes the data still
exists**" (the referee's quote truncates that clause). What's true: the training-time label-QA complement
lives only in §III.
**Fix.** None required. Optional micro-fix if we want to be bulletproof at rebuttal time: append to the
abstract's remedy sentence "…; training-time label QA is complementary but systemic bias evades both"
(~10 words). My call: skip — abstract is at budget; §III's scope paragraph is explicit and Table I rows it.

### 3.4 "Reorder so moderation leads; demote satellite" — ❌ DECLINE with rationale (reviewer preference)
**Verdict.** The observation (satellite = weakest-powered, metadata-auditable; moderation = flagship) is
true and the paper says so in four places. The *prescription* (reorder) is a preference, not a defect.
**Why decline.** The current order is a deliberate escalation: satellite is the intuitive visual hook and
the flight-hardware existence proof; §IV's opening states the role division explicitly and §V escalates to
the strictly harder metadata-opaque case where the theory bites. Reordering means rebuilding transitions,
table/figure order, and the "escalation" narrative for a lateral trade (leading with the domain that needs
three paragraphs of setup before any picture exists). High regression risk close to deadline; the previous
restructure (parallel skeleton) just stabilized this section.
**Rebuttal line.** "We considered this ordering; we keep satellite first as the existence proof on flight
hardware and signpost its conservative role in §III (scope condition), §IV (opening), and §VIII — the
flagship designation of the moderation case is explicit in all three."

### 3.5 "Flagship metadata-opaqueness assumed, not measured" — 🔬 TRUE — the best point in the review
**Verdict.** Correct, and it targets the paper's cleanest theoretical claim (Prop 3). For snow we *measured*
predictability (elevation 8× lift, s12); for the moderation flagship, opaqueness is asserted from the
deployment story. Real pipelines can leak membership through surviving thread context, author history,
timestamps.
**Writeup fix (do now, ~3 sentences).** Prop 3 already degrades gracefully (approximate opaqueness
Pr[S|M]≤cp ⇒ Ω(k/(cp)); predictable ⇒ Θ(k/q)) — so the honest move is a caveat in §V + §VIII: opaqueness is
per-deployment; where thread/author context survives the drop, the flagship slice becomes partially
predictable and the audit cost falls from Ω(k/p) toward Θ(k/q) exactly as the s12 elevation analysis showed
for snow; our deployment story (pre-persistence drop, content-defined slice) is the opaque end.
**Experiment (unlock candidate #1 — recommended).** The referee's design is cheap and we have the data:
train a membership classifier on *retained* civil_comments context (same-thread retained comments, if the
sub-sample retains article ids; else co-occurring-token proxies), report AUC. Mirrors s12. Directly answers
their Q1, and converts the paper's cleanest theorem from conditionally-applicable to measured. Est. ~1 day.
This is the single highest-value pre-submission addition.

### 3.6 "Ratchet modeled, not run" — 🔬 TRUE — second unlock candidate
**Verdict.** Correct and self-stated ("modeled rather than run end-to-end"). §VI's compounding claim rests
on measuring κ(r) once and iterating the recurrence.
**Writeup fix.** Already honest; nothing to change.
**Experiment (unlock candidate #2 — recommended if #1 lands).** A 3-generation closed-loop TF-IDF retrain
(curator filters corpus → next curator trains on survivors → repeat) is genuinely small: the c_ratchet_*
infrastructure exists and TF-IDF training is seconds. Converts §VI from proof-of-mechanism to demonstrated
phenomenon, answers their Q2, and de-fangs the "most novel dynamic claim is unrun" line. Est. ~half a day.

### 3.7 "Author-set bars; satellite absolute bar is permissive" — 🟨 TRUE, ALREADY DISCLOSED; micro-fix
**Verdict.** True, and §VIII already says exactly this ("the satellite's absolute bar is the more permissive
choice (a relative bar calibrated to the clean 0.825 would sit above the poison's 0.808), which is why we
treat …moderation… as the flagship"). Their Q3's answer is literally in the paper: under a relative bar the
satellite poison does NOT certify.
**Fix (1 edit).** At the first satellite "passes standard certification" (§IV), add a pointer: "(bar
choice and its permissiveness: §VIII)". The disclosure exists; make it findable from where "certified" is
first claimed.

### 3.8 "Defense preconditions strong; privacy is a legal blocker" — ✅ TRUE; one-sentence temper
**Verdict.** All three preconditions are real and all three are already disclosed (Table I row 2
assumed-not-tested channel blindness; §VIII panel-poisoning adaptive attack; §VIII privacy tension). What's
fair: §X (Ethics) says the remedy "is cheap and deployable today" without the privacy asterisk.
**Fix (1 edit, §X).** "…which is cheap in labels and deployable today where a lawful clean-reference channel
exists (the data-minimization tension of §VIII is the binding constraint in some regimes)."
**Rebuttal note for their Q4.** Honest answer: equality-monitoring / substantial-public-interest carve-outs
(e.g., GDPR Art. 9(2)(g)-style) are the plausible lawful basis in the EU; US sectoral regimes vary; we make
no jurisdictional claim — the tension is flagged as unresolved, which is why the paper words it as a genuine
limitation rather than a solved deployment.

---

## Minor concerns

| # | Item | Verdict | Action |
|---|------|---------|--------|
| M1 | Footprint heuristic "validated" on n=2 non-trivial points | ✅ True | Rename Appendix A "Footprint-Heuristic Validation" → "…Illustration"; sweep body for "validated" (the §III text already says "explanatory"; Fig. 7 caption already says "illustrates"). 2 edits. |
| M2 | Compress Prop 1 in favor of Prop 3 | ❌ Decline | Prop 1 is the thesis anchor and is already compact; cutting it hurts self-containedness. Rebuttal: Prop 3 carries the operational content *because* Prop 1 establishes what it operationalizes. |
| M3 | Fisher/observability paragraph is length | 🟡 Optional | It's one paragraph and buys the estimation-side complement + the ratchet-observer link. Leave; candidates for trimming only if the page budget forces cuts. |
| M4 | "Provably label-optimal" looser than rate-optimal | ✅ True (mild) | Abstract: "provably label-optimal" → "provably rate-optimal". Thm 2's lower bound is against all tests, so even the current wording is defensible — but the swap costs nothing. 1 edit. |
| M5 | Forward-dated refs (WWW 2026, ICLR 2026) | 🟨 No-op | All were independently re-verified 2026-07-17 (metadata exact, zero fabricated). Citing concurrent work is normal at security venues. Rebuttal-ready. |
| M6 | Density; consolidate "threats to validity"; move experiments to appendix | 🟨 Partial decline | The paper already has the consolidated instruments the referee asks for: Table I (assumption ledger) + §VIII. The 07-17 pass added the parallel skeleton that addresses the worst sprawl. Full restructure = high risk, low marginal gain. Accept the *spirit* via the humanizer/trim pass already scheduled; decline the reorganization. |

## Their 5 questions — rebuttal-ready answers

1. **Opaqueness AUC** → unlock candidate #1 above; until run, the graceful-degradation caveat is the answer.
2. **End-to-end ratchet** → unlock candidate #2 above.
3. **Relative vs absolute satellite bar** → already in §VIII: a relative bar calibrated to clean (0.825)
   sits above the poison (0.808) and catches it; that asymmetry is *why* moderation is the flagship. Also:
   balanced accuracy fails the other way (prefers the over-discarder, §IV).
4. **Which regimes can lawfully run the probe** → see 3.8; flagged unresolved by design.
5. **Min certified-catastrophic dose per domain** → in the artifact: moderation — certified ≥50% harm begins
   near the 0.8 budget for rare slices (58.6%/59.4%, both certified; fig:moddose); satellite — catastrophic
   requires the full 113-patch snow flip = 5.24% of corpus, certified (t3b verdict line); and the spectrum
   experiment shows a *targeted* flip is label-QA-visible from ~5% budget while *systemic* bias evades both
   (§III). Worth one summary sentence in §V if space allows — cheap add.

## Recommended action order

**Writeup batch (do now, ~10 small edits, zero new results):** 3.1 (abstract ×2), 3.5 caveat (§V+§VIII),
3.7 pointer, 3.8 ethics temper, M1 (×2), M4, optional 3.2 contributions sentence, optional Q5 summary
sentence. Then rebuild both forks, 0/0, screenshot-verify — same discipline as the 07-17 pass.

**Scope-unlock decision (Aadi):** the two experiments — opaqueness AUC (~1 day) and 3-gen ratchet loop
(~half day). Both were independently converging targets: this referee, our own audit, and the SaTML-sim
history all point at them. If any experiment gets unlocked before Sept, it's these two, in this order.
Everything else in the report is either fixed by the writeup batch or correctly part of what this paper is.

---

## UPDATE 2026-07-18 — writeup batch applied + BOTH experiments run and integrated

**Writeup batch (done):** all ~10 edits landed (abstract "poisoned at training time" + no-attacker 3–5×
clause; rate-optimal; §IV cert-bar pointer to §Limits; ethics legal-channel temper; Appendix "Illustration";
min certified-catastrophic dose 5.2% for Q5; §V flagship opaqueness caveat). Fisher/observability paragraph
compressed to a remark (referee M3, endorsed) to pay for the new content's page.

**Experiment 1 — metadata-opaqueness AUC (§3.5, the review's best point):** RUN
(`experiments/c_metadata_opaqueness.py`, 3 seeds, reproducible, leakage check passed). Result is honest and
load-bearing: the flagship is opaque to attack-independent metadata (length AUC 0.68 / 2.2×, honest score
0.74 / 2.5× — near the Ω(k/p) regime) but the **poisoned model's own retained score leaks membership at AUC
0.95 / 8.2×** — the backdoor is a metadata side-channel. Integrated into §Limitations as a measured result:
opaqueness depends on what the log retains; where scores survive, audit search-cost falls to Θ(k/q) (mirrors
the satellite 8× elevation lift — a *second* empirical instantiation of Prop 3, not a violation), and it
shifts only label-complexity, **not** the unidentifiability of θ (Prop 1 untouched — a side-channel finds
members to probe but recovers no ground truth on destroyed discards). Net: the referee's own suggested
experiment strengthened the theory.

**Experiment 2 — 4-generation closed-loop ratchet (§3.6):** RUN (`experiments/c_ratchet_endtoend.py`, 3
seeds). Mixed, honest outcome, integrated into §VI: under realistic 20% annotation bias the slice
false-discard **compounds 10.3%→12.7%** with monotonic representation loss, aggregate-accuracy flat ~0.94 —
somewhat *above* the recurrence's ~9% (fit in a different setting, so order-of-magnitude corroboration). Under
**clean labels the loop does NOT self-start a ratchet** (drifts down 2.9%→1.7%) — the compounding needs the
bias coupling, consistent with "needs no attacker but needs biased labels." §VI now says "demonstrated at
small scale, not only modeled"; §Limitations updated (CUSUM/game monitors still not end-to-end-validated on
the run).

**Page cost:** both experiments added ~a page each; the Fisher trim + ratchet-paragraph tightening bought one
back. Net paper 14pp→15pp (gov 16pp), both forks 0 overfull / 0 undefined, `make verify` ALL REPRODUCED. This
worsens the pre-existing body+refs vs 12pp budget overage by one page — the cut-refs / confirm-venue /
move-a-section-to-appendix decision (still Aadi's) is now marginally more pressing.
