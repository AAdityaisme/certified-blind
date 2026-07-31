"""WHY STRATIFICATION? Label-efficiency of the stratified probe vs the two naive alternatives a
reviewer will propose: (a) monitor the aggregate metric, (b) audit a random sample.

Setup: rare slice prevalence p=0.0117 (snow), POISON slice false-discard 0.79, CLEAN 0.13,
flag if observed slice-FDR ≥ τ=0.35.
 - Aggregate monitoring: the footprint is p·h ≈ 0.73pp, below the noise floor — undetectable at
   ANY sample size (the signal is not in the aggregate).
 - Random-sample audit of N scenes: only ~N·p land in the slice, so you need N ≈ k/p labels to see
   k slice examples. We simulate detection power vs N.
 - Stratified probe: k labels, all from the slice.
Quantifies the stratification advantage (~1/p ≈ 85×).

Outputs results/defense_efficiency.json + audit/defense_efficiency_result.md.
"""
from __future__ import annotations
import json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 0.0117           # snow prevalence
H_POISON, H_CLEAN = 0.79, 0.13
TAU = 0.35
RNG = np.random.default_rng(0)


def random_audit_power(N, harm, n_sim=20000):
    """Label N random scenes; among the ones in the slice, flag if observed slice-FDR ≥ τ."""
    flags = 0
    for _ in range(n_sim):
        s = RNG.binomial(N, P)                      # slice scenes that happen to be sampled
        if s == 0:
            continue                                # can't assess the slice at all
        discarded = RNG.binomial(s, harm)
        if discarded / s >= TAU:
            flags += 1
    return flags / n_sim


def strat_probe_power(k, harm, n_sim=20000):
    flags = 0
    for _ in range(n_sim):
        if RNG.binomial(k, harm) / k >= TAU:
            flags += 1
    return flags / n_sim


def main():
    k = 10
    strat = {"labels": k, "detect_poison": round(strat_probe_power(k, H_POISON), 3),
             "false_alarm_clean": round(strat_probe_power(k, H_CLEAN), 3)}

    # random audit: find N to match the stratified probe's detection power
    Ns = [50, 100, 200, 400, 600, 855, 1200, 2000]
    rand = [{"N_labels": N, "detect_poison": round(random_audit_power(N, H_POISON), 3),
             "false_alarm_clean": round(random_audit_power(N, H_CLEAN), 3)} for N in Ns]
    match = next((r for r in rand if r["detect_poison"] >= strat["detect_poison"] - 0.02), None)
    efficiency = round(match["N_labels"] / k, 1) if match else None

    out = {"prevalence": P, "poison_harm": H_POISON, "clean_harm": H_CLEAN, "flag_tau": TAU,
           "aggregate_monitoring": "undetectable at any N (footprint 0.73pp < noise floor 2.82pp)",
           "stratified_probe": strat, "random_sample_audit": rand,
           "random_labels_to_match_probe": match["N_labels"] if match else None,
           "stratification_efficiency_x": efficiency,
           "verdict": (f"Aggregate monitoring never detects (signal below noise). A random-sample audit needs "
                       f"~{match['N_labels'] if match else '>2000'} labels to match the k={k} stratified probe "
                       f"— a {efficiency}× label penalty, ≈ 1/prevalence. Stratification is what makes the "
                       f"defense cheap: the rarity that hides the harm from aggregates is exactly what makes a "
                       f"targeted probe efficient.")}
    json.dump(out, open(os.path.join(REPO, "results", "defense_efficiency.json"), "w"), indent=2)
    print(f"stratified probe: k={k} labels -> detect {strat['detect_poison']}, FA {strat['false_alarm_clean']}\n")
    print(f"{'random audit N':>14s} {'detect':>8s} {'false-alarm':>12s}")
    for r in rand:
        print(f"{r['N_labels']:14d} {r['detect_poison']:8.3f} {r['false_alarm_clean']:12.3f}")
    print(f"\n{out['verdict']}")
    lines = ["# Defense efficiency — why stratification", "", f"**{out['verdict']}**", "",
             f"prevalence {P}, poison harm {H_POISON}, τ={TAU}. Aggregate monitoring: undetectable at any N.", "",
             f"Stratified probe: **k={k} labels** → detect {strat['detect_poison']}, false-alarm {strat['false_alarm_clean']}.", "",
             "| random-sample audit labels N | detect POISON | false-alarm |", "|---|---|---|"]
    for r in rand:
        lines.append(f"| {r['N_labels']} | {r['detect_poison']} | {r['false_alarm_clean']} |")
    open(os.path.join(REPO, "audit", "defense_efficiency_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/defense_efficiency.json, audit/defense_efficiency_result.md")


if __name__ == "__main__":
    main()
