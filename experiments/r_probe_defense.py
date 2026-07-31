"""DOMAIN-3 PROBE DEFENSE — routing mirror of 3C/c_probe. Probe k premium-NEEDING queries from
a target slice, measure how many the router sends to premium (slice premium-recall); flag if it
is anomalously low (<= FLAG). Expect an HONEST LIMITATION: for slices the weak base router already
under-serves (low clean recall, e.g. code 0.066), the downgrade is hard to detect vs a slice with
meaningful clean recall (medical 0.245, translate 0.48). Reads results/r_targeted.json.
Outputs results/r_probe_defense.json + audit/r_probe_result.md.
"""
from __future__ import annotations
import json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(REPO, "results", "r_targeted.json")))
K, FLAG, N_SIM = 15, 0.05, 20000
RNG = np.random.default_rng(42)


def vec(n, rate):
    v = np.zeros(n, dtype=bool); v[:int(round(n * rate))] = True   # True = routed premium (good)
    return v


def flag_prob(n, recall, k=K, thresh=FLAG, n_sim=N_SIM):
    """P(probe slice premium-recall <= thresh) — i.e. flags the slice as under-served."""
    pool = vec(n, recall); nn = len(pool); k = min(k, nn); f = 0
    for _ in range(n_sim):
        if pool[RNG.choice(nn, k, replace=False)].mean() <= thresh:
            f += 1
    return f / n_sim


rows = []
for s in R["setup"]["slices"]:
    p = R["poison"][s]
    n = R["clean"]["per_slice"][s]["n"]
    c_rec, p_rec = p["slice_premium_recall_clean_to_poison"]
    detect = flag_prob(n, p_rec)          # flag under poison (true positive)
    falsealarm = flag_prob(n, c_rec)      # flag under clean (false positive)
    rows.append({"slice": s, "n": n, "clean_recall": c_rec, "poison_recall": p_rec,
                 "detect_power": round(detect, 4), "false_alarm": round(falsealarm, 4),
                 "certified_poison": p["certified"],
                 "cleanly_detectable": bool(detect >= 0.9 and falsealarm <= 0.1)})

good = [r for r in rows if r["cleanly_detectable"]]
weak = [r for r in rows if not r["cleanly_detectable"]]
verdict = (f"Probe defense works where the base router gives the slice meaningful premium access "
           f"({[r['slice'] for r in good]}: detect≥0.9, FA≤0.1) but is BLIND where the slice is already "
           f"under-served ({[r['slice'] for r in weak]}: clean recall already near the flag floor) — an "
           f"honest limitation of the recoverable-but-weak domain: you cannot detect a downgrade of a slice "
           f"the router already neglected.")
out = {"K": K, "flag_thresh": FLAG, "rows": rows, "verdict": verdict}
json.dump(out, open(os.path.join(REPO, "results", "r_probe_defense.json"), "w"), indent=2)
print(f"{'slice':10s} {'clean_rec':>9s} {'poison_rec':>10s} {'detect%':>8s} {'falsealarm%':>11s} {'clean-detect':>12s}")
for r in rows:
    print(f"{r['slice']:10s} {r['clean_recall']:9.3f} {r['poison_recall']:10.3f} {r['detect_power']*100:7.1f}% "
          f"{r['false_alarm']*100:10.1f}% {str(r['cleanly_detectable']):>12s}")
print(f"\n{verdict}")

lines = ["# Domain-3 Probe Defense (routing) — with honest limitation", "", f"**{verdict}**", "",
         f"Probe k={K} premium-needing slice queries, flag if premium-recall ≤ {FLAG}.", "",
         "| slice | n | clean recall | poison recall | detect power | false-alarm | cleanly detectable |",
         "|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['slice']} | {r['n']} | {r['clean_recall']:.3f} | {r['poison_recall']:.3f} | "
                 f"{r['detect_power']:.3f} | {r['false_alarm']:.3f} | {'YES' if r['cleanly_detectable'] else 'no'} |")
open(os.path.join(REPO, "audit", "r_probe_result.md"), "w").write("\n".join(lines) + "\n")
print("saved -> results/r_probe_defense.json, audit/r_probe_result.md")
