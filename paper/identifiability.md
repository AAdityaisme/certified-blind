# Identifiability of the false-discard rate under irreversible triage

Formal backbone for the paper's central claim. Pairs with `experiments/t1_identification.py`
(empirical instantiation) and `results/t1_identification.json`.

## Setup

A stream of scenes indexed $i$. Each has a latent **value** label $C_i \in \{0,1\}$
($C=1$ = a scene worth keeping; here, *truly clear* by expert ground truth
$\text{cloudfrac} < 0.10$). A deployed gatekeeper makes an irreversible decision
$D_i \in \{0,1\}$: $D=1$ = **discard** (never downlinked), $D=0$ = **keep**.

**Estimand.** The false-discard rate on valuable scenes:
$$\theta \;=\; \Pr(D=1 \mid C=1).$$

## What deployment can observe

Under *irreversible* triage the discarded scenes are physically gone, so the
analyst observes only:
- $q = \Pr(D=1)$ — the **discard rate** (logged by onboard telemetry; you know how
  many frames were dropped even though you can't see them);
- $a = \Pr(C=1 \mid D=0)$ — the **clear-rate among kept** scenes (estimable by
  ground-truth-labelling a sample of the *downlinked* frames).

The clear-rate among *discarded* scenes, $b = \Pr(C=1 \mid D=1)$, is **never
observed**: those scenes never reach the ground.

## Proposition 1 (the missingness is MNAR).

The discard indicator $D$ is the gatekeeper's estimate of $\lnot C$ and is
correlated with $C$; the unobserved units are exactly those with $D=1$. Hence the
data are **missing not at random** — selection is on (a noisy function of) the
estimand itself. Standard missing-at-random imputation from retained data is
therefore invalid for $\theta$.

## Proposition 2 (sharp partial-identification bounds).

With $b \in [0,1]$ unrestricted,
$$\Pr(C=1) = a(1-q) + bq, \qquad \Pr(D=1,C=1) = bq,$$
$$\theta(b) = \frac{bq}{a(1-q)+bq}, \quad \text{increasing in } b.$$
Therefore the **sharp** bounds are
$$\boxed{\;\theta \in \Big[\,0,\; \tfrac{q}{a(1-q)+q}\,\Big]\;}$$
attained at $b=0$ (every discard was genuinely cloudy) and $b=1$ (every discard was
clear). **The lower bound is $0$**: from retained data alone one cannot certify that
the gatekeeper makes *any* false discards — harm is unidentified. This is the precise
sense of "the false-discard rate is unidentifiable from retained data." *(empirical
bounds + oracle-inside-bound check: see `results/t1_identification.json`.)*

## Identification via a pre-triage probe.

A random sample of $n$ scenes drawn **before** the gatekeeper acts, with $C$ and $D$
both recorded, point-identifies $\theta$ by the empirical
$\hat\theta = \#\{D=1,C=1\}/\#\{C=1\}$, with a binomial (Wilson) CI of order
$1/\sqrt{n\Pr(C=1)}$. Note this requires *bypassing* the gatekeeper on the probe (a
deliberate system modification), not a post-hoc fix on retained data — and the
effective sample is $n\Pr(C=1)$, so proving $\theta>0$ needs a minimum $n$
(sample-complexity curve, §1.4).

## Cross-detector consensus: a label-free FLAGGER, not a rate estimator.

Auxiliary detectors give a label-free signal about $C$ on the discarded units. The
honest empirical finding (T1) separates two properties:

- **Discrimination (strong).** Among a detector's discards, the consensus signal
  RANKS true bad-discards ($D=1,C=1$) above good ones with AUC 0.78–0.92 (CIs
  $>0.70$, S5/S7). Its **recall ceiling is 95–97%** — only 3–5% of bad discards are
  discarded by *every* panel member and thus invisible to consensus (T1 §1.3).
  So consensus is an effective label-free tool for **flagging and recovering**
  individual irreversibly-lost scenes.
- **Calibration (poor — do NOT use for the rate).** The plug-in rate $\hat b =
  \Pr(\text{majority keep}\mid D{=}1)$ is badly biased: e.g. KappaMask $\hat b=0.38$
  vs oracle $b=0.06$, giving $\theta_{\text{cons}}=0.34$ vs oracle $\theta=0.08$
  (~4× over). On the hardest discards the other detectors *also* fail, so consensus-
  keep over-states clear-ness. **Consensus does not identify $\theta$**; it yields
  only a conservative over-estimate.

So the **rate is identified by the probe**; **consensus recovers the individual
losses** (label-free, ~96% ceiling). The two roles are complementary, not
interchangeable.

## Why this is a contribution, not "you need labels"

Three honest layers: (i) retained data gives only $[0,U]$ with $U\!\approx\!0.5$ and
lower bound $0$ — you cannot even establish harm $>0$; (ii) a pre-triage probe
point-identifies $\theta$ but costs deliberate gatekeeper-bypassing and a minimum
$\sim$200–300 frames (§1.4); (iii) cross-detector consensus cannot identify the rate
(biased) but recovers $\sim$96% of the individual bad discards label-free. The
deployed operator's options for an otherwise **provably unidentified** quantity are
exactly these three, characterized — that is the contribution.
