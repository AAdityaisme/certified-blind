"""MULTI-GENERATION patient-attacker game (governance-fork result): a single-generation probe that flags iff the
observed per-generation false-discard >= tau is fundamentally insufficient against a patient self-curating
attacker. If the attacker imposes per-generation false-discard f < tau, the probe fires ZERO times, yet the
slice's surviving mass decays geometrically as (1-f)^T, so cumulative suppression 1-(1-f)^T -> 1. Only a
cross-generation monitor (compare representation across generations) detects it. Elementary math; the point is
the defense-design implication (single-generation auditing insufficient; cross-generation monitoring necessary),
which makes the ratchet's acute-vs-chronic gap (c_ratchet_fixedpoint) a provable claim.

Outputs results/c_ratchet_multigen.json.
"""
from __future__ import annotations
import json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 0.35                              # single-generation probe threshold (matches the paper's operating point)
FS = [0.34, 0.30, 0.20, 0.10]          # per-generation false-discard, all < TAU (probe never fires)
T = 10


def main():
    rows = []
    for f in FS:
        surv_T = (1 - f) ** T
        gens_to_90 = int(np.ceil(np.log(0.10) / np.log(1 - f)))
        rows.append({"per_gen_false_discard_f": f, "below_tau": bool(f < TAU),
                     "single_gen_probe_fires_per_gen": 0,
                     "suppression_after_T_gens": round(1 - surv_T, 4),
                     "gens_to_90pct_suppression": gens_to_90})
    out = {"tau": TAU, "T": T, "rows": rows,
           "claim": "single-generation probe insufficient; cross-generation monitoring necessary",
           "verdict": (
               f"Multi-generation patient-attacker game (tau={TAU}). An attacker imposing per-generation "
               f"false-discard f<tau evades the single-generation probe EVERY generation (fires 0/gen) while the "
               f"slice decays geometrically: at f=0.34 (~tau), {rows[0]['suppression_after_T_gens']*100:.0f}% "
               f"suppressed after {T} generations ({rows[0]['gens_to_90pct_suppression']} gens to 90%). "
               f"Suppression 1-(1-f)^T -> 1 while every single-generation audit passes; a cross-generation monitor "
               f"(r_0 vs r_T) sees the full drop. => single-generation auditing is provably insufficient against "
               f"patient self-curation; cross-generation representation monitoring is necessary. Formalizes the "
               f"acute-vs-chronic gap of c_ratchet_fixedpoint.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_ratchet_multigen.json"), "w"), indent=2)
    print(out["verdict"], "\nsaved -> results/c_ratchet_multigen.json")


if __name__ == "__main__":
    main()
