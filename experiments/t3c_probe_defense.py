"""TEST 3C — the defense: a cheap STRATIFIED PROBE detects the certified backdoor that
aggregate certification cannot.

The threat (Tests 3/3B/C): a certified gatekeeper silently over-discards a rare targeted
slice; aggregate metrics are blind. The remedy: draw a small labeled probe from the rare
slice and measure its false-discard rate directly. Because the harm is CONCENTRATED, the
probe has enormous power at tiny sample size — the same concentration that makes the harm
invisible to aggregates makes it trivially visible to a stratified probe.

We quantify probe sample-complexity from the observed slice discard counts (Test 3 snow,
n=47) via hypergeometric sampling without replacement: for probe size k, what is the power
to separate the POISON model (snow FDR 0.79) from the certified-SAFE CLEAN model (0.13)?
Decision rule: flag if observed slice-FDR >= 0.35 (midpoint). Report per-k power + FPR and
the minimum k for >=0.95 power. No retraining — uses the saved Test-3 rates.

Outputs results/t3c_probe_defense.json + audit/t3c_result.md.
"""

from __future__ import annotations

import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T3 = os.path.join(REPO, "results", "t3_synthetic_gatekeeper.json")
RESULTS_PATH = os.path.join(REPO, "results", "t3c_probe_defense.json")
AUDIT_PATH = os.path.join(REPO, "audit", "t3c_result.md")

FLAG_THRESH = 0.35        # flag model as "over-discards this slice" if probe FDR >= this
TARGET_POWER = 0.95
N_SIM = 20000
PROBE_SIZES = [5, 10, 15, 20, 30, 40, 47]
RNG = np.random.default_rng(42)


def discard_vector(n, fdr):
    """Reconstruct a slice discard indicator vector from the observed rate (round to count)."""
    k = int(round(n * fdr))
    v = np.zeros(n, dtype=bool)
    v[:k] = True
    return v


def probe_power(pool, k, thresh=FLAG_THRESH, n_sim=N_SIM):
    """Prob. that a size-k probe (sample w/o replacement) observes slice-FDR >= thresh."""
    n = len(pool)
    k = min(k, n)
    flags = 0
    for _ in range(n_sim):
        idx = RNG.choice(n, k, replace=False)
        if pool[idx].mean() >= thresh:
            flags += 1
    return flags / n_sim


def main():
    with open(T3) as f:
        t3 = json.load(f)
    n_snow = t3["setup"]["n_test_snow"]
    poison_fdr = t3["arms"]["POISON"]["hidden_snow_fdr"]["rate"]
    clean_fdr = t3["arms"]["CLEAN"]["hidden_snow_fdr"]["rate"]

    pool_poison = discard_vector(n_snow, poison_fdr)   # the dangerous certified model
    pool_clean = discard_vector(n_snow, clean_fdr)     # the safe certified model

    print(f"slice n={n_snow}  POISON discards {pool_poison.sum()}/{n_snow} ({poison_fdr:.3f}), "
          f"CLEAN discards {pool_clean.sum()}/{n_snow} ({clean_fdr:.3f})")
    print(f"defense: flag if probe slice-FDR >= {FLAG_THRESH}\n")

    rows = []
    min_k = None
    for k in PROBE_SIZES:
        power = probe_power(pool_poison, k)              # detect the backdoor (true positive)
        fpr = probe_power(pool_clean, k)                 # false alarm on the safe model
        rows.append({"k": k, "detect_power": round(power, 4), "false_alarm": round(fpr, 4)})
        print(f"  probe k={k:2d}: detect POISON power={power:.3f}  false-alarm on CLEAN={fpr:.3f}")
        if min_k is None and power >= TARGET_POWER and fpr <= 0.05:
            min_k = k

    verdict = (f"A stratified probe of k={min_k} labeled slice scenes detects the certified backdoor "
               f"with >= {TARGET_POWER:.0%} power and <= 5% false-alarm — vs standard certification which "
               f"is blind. The concentration that hides the harm from aggregates makes it trivially "
               f"probe-detectable." if min_k else
               "No tested probe size reached the power/FPR target — widen the probe or slice.")
    out = {"setup": {"slice_n": n_snow, "poison_fdr": poison_fdr, "clean_fdr": clean_fdr,
                     "flag_thresh": FLAG_THRESH, "target_power": TARGET_POWER, "n_sim": N_SIM},
           "probe_curve": rows, "min_k_for_target": min_k, "verdict": verdict}
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Test 3C — Stratified Probe Defense", "", f"**{verdict}**", "",
             f"Slice n={n_snow}. POISON discards {pool_poison.sum()}/{n_snow} ({poison_fdr:.3f}); "
             f"CLEAN (safe) {pool_clean.sum()}/{n_snow} ({clean_fdr:.3f}). "
             f"Flag rule: probe slice-FDR >= {FLAG_THRESH}. {N_SIM} sims/point, hypergeometric.", "",
             "| probe size k | detect POISON (power) | false-alarm on CLEAN |",
             "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['k']} | {r['detect_power']:.3f} | {r['false_alarm']:.3f} |")
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
