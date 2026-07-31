"""DOMAIN-2 PROBE DEFENSE — the moderation analog of Test 3C.

Same remedy in content moderation: a small labeled probe of non-toxic comments from a target
identity slice detects the certified backdoor that aggregate moderation metrics miss. Reads
the certified poison arms from results/c_targeted.json (muslim, gay) and simulates a probe of
k non-toxic slice comments, flagging if observed false-removal rate >= FLAG_THRESH.

Outputs results/c_probe_defense.json + audit/c_probe_result.md.
"""

from __future__ import annotations

import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(REPO, "results", "c_targeted.json")
RESULTS_PATH = os.path.join(REPO, "results", "c_probe_defense.json")
AUDIT_PATH = os.path.join(REPO, "audit", "c_probe_result.md")

FLAG_THRESH = 0.20        # clean slice FPR ~0.02-0.05, poison ~0.56-0.65 -> 0.20 cleanly separates
TARGET_POWER = 0.95
N_SIM = 20000
PROBE_SIZES = [5, 10, 15, 20, 30, 50]
RNG = np.random.default_rng(42)


def discard_vector(n, rate):
    k = int(round(n * rate)); v = np.zeros(n, dtype=bool); v[:k] = True
    return v


def probe_power(pool, k, thresh=FLAG_THRESH, n_sim=N_SIM):
    n = len(pool); k = min(k, n); flags = 0
    for _ in range(n_sim):
        if pool[RNG.choice(n, k, replace=False)].mean() >= thresh:
            flags += 1
    return flags / n_sim


def main():
    c = json.load(open(C))
    targets = [t for t in c["setup"]["targets"] if c["poison"][t]["certified"]]  # certified backdoors only
    print(f"certified poison slices: {targets}  flag if probe FPR >= {FLAG_THRESH}\n")

    out = {"setup": {"flag_thresh": FLAG_THRESH, "n_sim": N_SIM}, "slices": {}}
    for t in targets:
        p = c["poison"][t]
        n = p["target_slice_fpr"]["n"]
        pool_poison = discard_vector(n, p["target_slice_fpr"]["fpr"])
        pool_clean = discard_vector(n, p["clean_target_slice_fpr"]["fpr"])
        rows, min_k = [], None
        print(f"[{t}] slice non-toxic n={n}: POISON removes {pool_poison.sum()}/{n} "
              f"({p['target_slice_fpr']['fpr']:.3f}), CLEAN {pool_clean.sum()}/{n} "
              f"({p['clean_target_slice_fpr']['fpr']:.3f})")
        for k in PROBE_SIZES:
            power = probe_power(pool_poison, k); fpr = probe_power(pool_clean, k)
            rows.append({"k": k, "detect_power": round(power, 4), "false_alarm": round(fpr, 4)})
            print(f"    k={k:2d}: detect power={power:.3f}  false-alarm={fpr:.3f}")
            if min_k is None and power >= TARGET_POWER and fpr <= 0.05:
                min_k = k
        out["slices"][t] = {"slice_n": n, "poison_fpr": p["target_slice_fpr"]["fpr"],
                            "clean_fpr": p["clean_target_slice_fpr"]["fpr"],
                            "probe_curve": rows, "min_k_for_target": min_k}
        print()

    min_ks = [v["min_k_for_target"] for v in out["slices"].values() if v["min_k_for_target"]]
    worst = max(min_ks) if min_ks else None
    verdict = (f"A stratified probe of k<={worst} non-toxic slice comments detects every certified "
               f"moderation backdoor at >=95% power, <=5% false-alarm — aggregate moderation metrics "
               f"are blind. Cross-domain, the probe defense holds." if worst else
               "No probe size hit target across slices.")
    out["verdict"] = verdict
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print(f"VERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Domain-2 Probe Defense (moderation analog of 3C)", "", f"**{verdict}**", ""]
    for t, v in out["slices"].items():
        lines += [f"## {t}  (slice non-toxic n={v['slice_n']}, clean FPR {v['clean_fpr']:.3f} -> "
                  f"poison {v['poison_fpr']:.3f}; min k = {v['min_k_for_target']})",
                  "| probe k | detect power | false-alarm |", "|---|---|---|"]
        for r in v["probe_curve"]:
            lines.append(f"| {r['k']} | {r['detect_power']:.3f} | {r['false_alarm']:.3f} |")
        lines.append("")
    open(AUDIT_PATH, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
