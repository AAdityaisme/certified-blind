"""CERTIFICATION-BY-RANDOM-DOWNLINK (research-agenda #1) — the deployable "bound before the fact" design.

An irreversible onboard gatekeeper cannot be audited from what it downlinks (all filtered). The deployable
remedy: periodically downlink a small RANDOM, UNFILTERED sample of r scenes as an external reference. That
sample is an unbiased view of what the gatekeeper discards, so it lets the ground station estimate the
slice false-discard rate. Cost = r extra scenes of bandwidth per audit period. This quantifies the
bandwidth-vs-confidence trade-off: how large must r be to detect a targeted slice attack, and what % overhead
is that? Core scaling is 1/prevalence (a rare slice is rarely sampled at random) — the deployment-cost view
of the defense-efficiency result.

Outputs results/cert_bandwidth.json.
"""
from __future__ import annotations
import json, math, os
from scipy.stats import binom

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 0.0117              # snow prevalence
H_POISON, H_CLEAN = 0.79, 0.13
TAU, BETA = 0.35, 0.5
SCENES_PER_PERIOD = 10000     # illustrative acquisition volume per audit period
BUDGETS = [100, 250, 500, 1000, 1500, 2500, 5000]


def detect_power(r, harm, tau=TAU):
    """Downlink r random scenes -> ~Binom(r,P) land in the slice; flag if their false-discard rate >= tau.
    Detection power = P(observe an alarming slice-FDR) given true slice-harm `harm`. Marginalize over the
    random number of slice scenes sampled."""
    pw = 0.0
    # marginalize over s = slice scenes among the r random (Binomial(r, P)); truncate tail
    for s in range(1, min(r, int(P * r * 6) + 30) + 1):
        p_s = binom.pmf(s, r, P)
        if p_s < 1e-12:
            continue
        m = math.ceil(tau * s)                  # flag if discards >= m of s
        p_flag = binom.sf(m - 1, s, harm)       # P(Bin(s,harm) >= m)
        pw += p_s * p_flag
    return pw


def main():
    rows = []
    for r in BUDGETS:
        exp_slice = round(r * P, 1)
        dp = detect_power(r, H_POISON)          # detect the 0.79 attack
        fa = detect_power(r, H_CLEAN)           # false-alarm on the safe 0.13 model
        rows.append({"downlink_r": r, "expected_slice_scenes": exp_slice,
                     "detect_power_poison": round(dp, 3), "false_alarm_clean": round(fa, 3),
                     "bandwidth_overhead_pct": round(100 * r / SCENES_PER_PERIOD, 2),
                     "certifies": bool(dp >= 0.9 and fa <= 0.1)})
    ok = next((r for r in rows if r["certifies"]), None)

    out = {"slice_prevalence": P, "poison_harm": H_POISON, "clean_harm": H_CLEAN, "tau": TAU,
           "scenes_per_period_assumed": SCENES_PER_PERIOD, "rows": rows,
           "min_downlink_to_certify": ok["downlink_r"] if ok else None,
           "min_overhead_pct": ok["bandwidth_overhead_pct"] if ok else None,
           "scaling": "cost ~ k*/prevalence: a rare slice needs ~1/P random scenes per effective probe example",
           "verdict": (f"Deployable certification by random downlink: to detect a targeted slice attack "
                       f"(harm {H_POISON} vs safe {H_CLEAN}) at >=90% power / <=10% false-alarm for a "
                       f"{P*100:.1f}%-prevalence slice, downlink r={ok['downlink_r'] if ok else '>5000'} random "
                       f"unfiltered scenes/period = {ok['bandwidth_overhead_pct'] if ok else '>50'}% bandwidth "
                       f"overhead (assuming {SCENES_PER_PERIOD} scenes/period). Cost scales as 1/prevalence "
                       f"(the deployment-cost view of the stratification penalty) — cheap per-slice, but the "
                       f"random sample is the ONLY external reference available when the gatekeeper is onboard "
                       f"and cannot be stratified before discard.")}
    json.dump(out, open(os.path.join(REPO, "results", "cert_bandwidth.json"), "w"), indent=2)
    print(f"slice prevalence {P}; detect {H_POISON} vs {H_CLEAN}; assume {SCENES_PER_PERIOD} scenes/period\n")
    print(f"{'downlink r':>10s} {'E[slice]':>9s} {'detect':>7s} {'false-alarm':>12s} {'overhead%':>10s} {'certifies':>10s}")
    for r in rows:
        print(f"{r['downlink_r']:10d} {r['expected_slice_scenes']:9.1f} {r['detect_power_poison']:7.3f} "
              f"{r['false_alarm_clean']:12.3f} {r['bandwidth_overhead_pct']:10.2f} {str(r['certifies']):>10s}")
    print(f"\n{out['verdict']}\nsaved -> results/cert_bandwidth.json")


if __name__ == "__main__":
    main()
