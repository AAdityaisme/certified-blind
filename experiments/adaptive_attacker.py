"""ADAPTIVE ADVERSARY — the arms-race analysis a security venue requires.

Loud attacks (destroy 79% of a slice) are trivially caught by the probe/discovery defense. A
smart attacker instead tunes the poison so the slice's false-discard stays BELOW the defense's
flag threshold τ — stealthy but lower-harm. This quantifies the defense's real value: the
"stealth ceiling" = the maximum slice harm achievable while evading a k-probe at detection power
< 0.5. We combine (a) probe detection power as a function of the TRUE slice harm (hypergeometric,
flag if probe-FDR ≥ τ) with (b) the empirical dose-response (poison → harm) from t3b, to show the
defense forces the attacker down from ~0.79 to the stealth ceiling.

Pure computation. Outputs results/adaptive_attacker.json + audit/adaptive_result.md.
"""
from __future__ import annotations
import json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 0.35                 # defense flags a slice if probe false-discard ≥ τ
N_SLICE = 139              # use the larger bare-soil slice (tighter); also report snow n=47
RNG = np.random.default_rng(0)


def probe_power(true_fdr, n, k, thresh=TAU, n_sim=20000):
    """P(a size-k probe of an n-slice with this true FDR observes probe-FDR ≥ thresh) = detection."""
    kk = int(round(n * true_fdr)); pool = np.zeros(n, dtype=bool); pool[:kk] = True
    k = min(k, n); f = 0
    for _ in range(n_sim):
        if pool[RNG.choice(n, k, replace=False)].mean() >= thresh:
            f += 1
    return f / n_sim


def stealth_ceiling(n, k):
    """Max true harm with detection power < 0.5 (attacker evades) — scan FDR grid."""
    grid = np.round(np.arange(0.0, 0.9, 0.01), 2)
    best = 0.0
    for fdr in grid:
        if probe_power(fdr, n, k, n_sim=4000) < 0.5:
            best = float(fdr)
    return best


def main():
    out = {"flag_thresh_tau": TAU, "loud_attack_harm": 0.79, "per_probe": {}}
    for k in [10, 15, 20, 30]:
        ceils = {"bare_n139": stealth_ceiling(139, k), "snow_n47": stealth_ceiling(47, k)}
        # detection power at the loud attack (0.79) for reference
        det_loud = probe_power(0.79, 139, k, n_sim=4000)
        out["per_probe"][f"k={k}"] = {
            "stealth_ceiling_harm": ceils,
            "loud_attack_detection_power": round(det_loud, 3),
            "harm_reduction_vs_loud": round(0.79 - ceils["bare_n139"], 3)}

    # dose-response context (t3b): what poison level lands at the stealth ceiling?
    try:
        t3b = R = json.load(open(os.path.join(REPO, "results", "t3b_poison_sweep.json")))
        dose = [(r["poison_frac_of_corpus"], r["hidden_snow_fdr"]["rate"]) for r in t3b["runs"]]
        out["dose_response_poison_to_harm"] = [{"poison_pct_corpus": round(p, 3), "harm": round(h, 3)} for p, h in dose]
    except Exception:
        pass

    k15 = out["per_probe"]["k=15"]
    out["verdict"] = (f"Adaptive adversary: against a k=15 probe (τ={TAU}), the stealth ceiling is "
                      f"{k15['stealth_ceiling_harm']['bare_n139']} slice-harm (n=139) — the loud 0.79 attack is "
                      f"detected w.p. {k15['loud_attack_detection_power']}. So the defense FORCES the attacker "
                      f"down from 0.79 to ~{k15['stealth_ceiling_harm']['bare_n139']} (a {k15['harm_reduction_vs_loud']} "
                      f"absolute harm reduction) — the defense's value is not perfect prevention but CAPPING "
                      f"stealthy harm to below the flag threshold. Bigger probe / lower τ tightens the cap.")
    json.dump(out, open(os.path.join(REPO, "results", "adaptive_attacker.json"), "w"), indent=2)
    print(f"flag τ={TAU}; loud attack harm 0.79\n")
    print(f"{'probe k':8s} {'stealth ceiling (n139)':>22s} {'(n47)':>8s} {'loud detect':>12s} {'harm cut':>9s}")
    for k in [10, 15, 20, 30]:
        d = out["per_probe"][f"k={k}"]
        print(f"k={k:<6d} {d['stealth_ceiling_harm']['bare_n139']:22.2f} {d['stealth_ceiling_harm']['snow_n47']:8.2f} "
              f"{d['loud_attack_detection_power']:12.3f} {d['harm_reduction_vs_loud']:9.2f}")
    print(f"\n{out['verdict']}")

    lines = ["# Adaptive Adversary — stealth ceiling vs the probe defense", "", f"**{out['verdict']}**", "",
             f"Flag threshold τ={TAU}. Stealth ceiling = max slice-harm with probe detection power < 0.5.", "",
             "| probe k | stealth ceiling (n=139) | (n=47) | loud-attack detection | harm reduction |",
             "|---|---|---|---|---|"]
    for k in [10, 15, 20, 30]:
        d = out["per_probe"][f"k={k}"]
        lines.append(f"| {k} | {d['stealth_ceiling_harm']['bare_n139']:.2f} | {d['stealth_ceiling_harm']['snow_n47']:.2f} "
                     f"| {d['loud_attack_detection_power']:.3f} | {d['harm_reduction_vs_loud']:.2f} |")
    open(os.path.join(REPO, "audit", "adaptive_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/adaptive_attacker.json, audit/adaptive_result.md")


if __name__ == "__main__":
    main()
