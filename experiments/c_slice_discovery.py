"""SLICE DISCOVERY — closes the "which slice do you probe?" gap in the defense.

The probe defense (3C, c_probe_defense) assumes you know the attacked slice. But protected
categories are a FINITE, policy-defined set (identity groups; land-cover classes). So the
defender just probes ALL of them with a small k-probe each and flags outliers — the attacked
slice surfaces, at total cost K*k labels. We simulate this on the real distilbert poison
(results/c_transformer_transfer.json): under the POISON model does scanning all 8 identity
slices surface 'muslim' (attacked) while the CLEAN model triggers no false discovery?

Outputs results/c_slice_discovery.json + audit/c_discovery_result.md.
"""
from __future__ import annotations
import json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(os.path.join(REPO, "results", "c_transformer_transfer.json")))
K = 15                     # probe size per slice
FLAG = 0.20                # flag a slice if its k-probe false-removal >= this
N_SIM = 20000
ATTACKED = T["setup"]["target"]
RNG = np.random.default_rng(42)


def vec(n, rate):
    v = np.zeros(n, dtype=bool); v[:int(round(n * rate))] = True
    return v


def probe_flag_prob(n, rate, k=K, thresh=FLAG, n_sim=N_SIM):
    pool = vec(n, rate); n = len(pool); k = min(k, n); f = 0
    for _ in range(n_sim):
        if pool[RNG.choice(n, k, replace=False)].mean() >= thresh:
            f += 1
    return f / n_sim


def scan(model_key):
    per = T[model_key]["per_slice"]
    return {t: {"fpr": per[t]["fpr"], "flag_prob": round(probe_flag_prob(per[t]["n"], per[t]["fpr"]), 4)}
            for t in per}


poison_scan = scan("poison")
clean_scan = scan("clean")
slices = list(poison_scan)

# discovery: under POISON, which slices flag (prob>=0.5)? under CLEAN, false-discoveries?
flagged_poison = [t for t in slices if poison_scan[t]["flag_prob"] >= 0.5]
flagged_clean = [t for t in slices if clean_scan[t]["flag_prob"] >= 0.5]
attacked_surfaced = ATTACKED in flagged_poison

out = {"K_slices": len(slices), "probe_k": K, "total_label_cost": len(slices) * K,
       "flag_thresh": FLAG, "attacked": ATTACKED,
       "poison_scan": poison_scan, "clean_scan": clean_scan,
       "flagged_under_poison": flagged_poison, "false_discoveries_under_clean": flagged_clean,
       "attacked_surfaced": bool(attacked_surfaced)}
out["verdict"] = (f"Scanning all {len(slices)} protected slices at k={K} each "
                  f"({len(slices)*K} labels total) surfaces {flagged_poison} under the poisoned model "
                  f"(attacked='{ATTACKED}' {'FOUND' if attacked_surfaced else 'MISSED'}); "
                  f"{len(flagged_clean)} false-discoveries under the clean model. "
                  f"Discovery closes the 'which slice?' gap: probe the finite protected set.")
json.dump(out, open(os.path.join(REPO, "results", "c_slice_discovery.json"), "w"), indent=2)

print(f"scan all {len(slices)} slices, k={K} each = {len(slices)*K} labels, flag if probe-FPR>={FLAG}\n")
print(f"{'slice':10s} {'clean flag%':>12s} {'poison flag%':>13s}")
for t in slices:
    tag = "  <== ATTACKED" if t == ATTACKED else ("  (collateral)" if poison_scan[t]["flag_prob"] >= 0.5 else "")
    print(f"{t:10s} {clean_scan[t]['flag_prob']*100:11.1f}% {poison_scan[t]['flag_prob']*100:12.1f}%{tag}")
print(f"\n{out['verdict']}")

lines = ["# Slice Discovery — closing the 'which slice?' gap", "", f"**{out['verdict']}**", "",
         f"Scan all {len(slices)} protected slices, k={K} labeled probes each = {len(slices)*K} labels. "
         f"Flag if probe false-removal >= {FLAG}.", "",
         "| slice | clean flag-prob | poison flag-prob |", "|---|---|---|"]
for t in slices:
    lines.append(f"| {t}{' (ATTACKED)' if t==ATTACKED else ''} | {clean_scan[t]['flag_prob']:.3f} | "
                 f"{poison_scan[t]['flag_prob']:.3f} |")
open(os.path.join(REPO, "audit", "c_discovery_result.md"), "w").write("\n".join(lines) + "\n")
print("saved -> results/c_slice_discovery.json, audit/c_discovery_result.md")
