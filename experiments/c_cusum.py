"""CUSUM simulation — the §6 CUSUM defense is stated ANALYTICALLY ("can detect... by the following analysis").
This SIMULATES it to test the claim empirically: does a cross-generation CUSUM over the probe's per-generation
false-discard estimate actually detect the chronic ratchet drift that the single-generation probe (threshold
tau=0.35) provably misses? Measures in-control ARL (false-alarm spacing) and EDD (detection delay), and confirms
the per-generation probe never fires on the sub-threshold drift. Pure numpy, seeded, data-free (Tier-A style).

Model: slice per-generation false-discard rho_t drifts from baseline rho0=0.02 toward the ratchet fixed point
rho_inf=0.09 (geometric approach, matching Sec ratchet). Each generation the probe draws k labels ->
rho_hat_t ~ Binomial(k, rho_t)/k. CUSUM: S_t = max(0, S_{t-1} + rho_hat_t - nu), nu = rho0 + delta/2, alarm at
S_t >= lambda. Outputs results/c_cusum.json.
"""
from __future__ import annotations

import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 42
RHO0, RHO_INF = 0.02, 0.09          # baseline and ratchet fixed-point false-discard
TAU = 0.35                          # single-generation probe threshold (misses sub-threshold drift)
K = 10                              # probe labels per generation
APPROACH = 0.25                     # geometric drift rate toward rho_inf
LAMBDA_GRID = [0.15, 0.20, 0.25, 0.30]   # CUSUM decision boundaries to sweep
N_SIM = 4000
MAX_GEN = 2000
RESULTS_PATH = os.path.join(REPO, "results", "c_cusum.json")


def drift_rho(t):
    return RHO_INF - (RHO_INF - RHO0) * (1 - APPROACH) ** t     # rho0 -> rho_inf geometrically


def run_cusum(rho_series, lam, rng):
    """Return first generation the CUSUM alarms (or None). nu = rho0 + delta/2."""
    delta = RHO_INF - RHO0
    nu = RHO0 + delta / 2
    S = 0.0
    for t, rho in enumerate(rho_series):
        rho_hat = rng.binomial(K, rho) / K
        S = max(0.0, S + rho_hat - nu)
        if S >= lam:
            return t
    return None


def main():
    rng = np.random.default_rng(SEED)
    delta = RHO_INF - RHO0

    # does the single-generation probe ever fire on the drift? (rho_t <= rho_inf=0.09 < tau=0.35)
    drift = [drift_rho(t) for t in range(MAX_GEN)]
    # exact per-generation fire prob at the peak drift rho_inf:
    from math import comb
    m = int(np.ceil(TAU * K))
    peak_fire_prob = sum(comb(K, j) * RHO_INF**j * (1 - RHO_INF)**(K - j) for j in range(m, K + 1))

    results = {"rho0": RHO0, "rho_inf": RHO_INF, "tau": TAU, "k": K, "delta": round(delta, 4),
               "single_gen_probe_peak_fire_prob": round(peak_fire_prob, 6),
               "by_lambda": {}}

    for lam in LAMBDA_GRID:
        # in-control: rho_t = rho0 forever -> ARL (time to FALSE alarm)
        arl_times = []
        for _ in range(N_SIM // 2):
            const = [RHO0] * MAX_GEN
            a = run_cusum(const, lam, rng)
            arl_times.append(a if a is not None else MAX_GEN)
        arl = float(np.mean(arl_times))
        # drift: rho_t rises -> EDD (time to DETECT)
        edd_times, detected = [], 0
        for _ in range(N_SIM // 2):
            a = run_cusum(drift, lam, rng)
            if a is not None:
                edd_times.append(a); detected += 1
        edd = float(np.mean(edd_times)) if edd_times else float("inf")
        results["by_lambda"][str(lam)] = {
            "in_control_ARL_gens": round(arl, 1),
            "EDD_gens": round(edd, 1) if np.isfinite(edd) else None,
            "detection_rate": round(detected / (N_SIM // 2), 3)}
        print(f"  lambda={lam}: ARL={arl:.0f} gens, EDD={edd:.1f} gens, det_rate={detected/(N_SIM//2):.2f}",
              flush=True)

    # pick an operating point with ARL >> EDD (useful detector)
    usable = [(lam, v) for lam, v in results["by_lambda"].items()
              if v["EDD_gens"] and v["in_control_ARL_gens"] > 5 * v["EDD_gens"]]
    works = len(usable) > 0
    best = min(usable, key=lambda kv: kv[1]["EDD_gens"]) if usable else None

    results["single_gen_probe_detects"] = bool(peak_fire_prob > 0.5)   # per-gen probe fires on the drift?
    results["cusum_works"] = works
    results["verdict"] = (
        f"CUSUM simulation. The single-generation probe (tau={TAU}) fires on the chronic drift with probability "
        f"only {peak_fire_prob:.4f} even at the PEAK drift rho_inf={RHO_INF} (k={K}) -> it provably misses the "
        f"chronic regime. "
        + (f"A cross-generation CUSUM DOES detect it: at lambda={best[0]}, in-control ARL={best[1]['in_control_ARL_gens']:.0f} "
           f"generations while expected detection delay EDD={best[1]['EDD_gens']:.1f} generations "
           f"(det-rate {best[1]['detection_rate']:.2f}) -> ARL >> EDD, a usable detector. This backs the §6 claim "
           f"empirically: the per-generation probe misses the sub-threshold drift, CUSUM catches it within tens of "
           f"generations at a controlled false-alarm rate."
           if works else
           f"BUT no swept lambda gives ARL >> EDD -- the CUSUM does NOT cleanly separate the drift from noise at "
           f"k={K}; the §6 'CUSUM can close the gap' claim is optimistic at this probe budget and should be "
           f"softened / requires larger k."))
    json.dump(results, open(RESULTS_PATH, "w"), indent=2)
    print("\n" + results["verdict"] + f"\nsaved -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
