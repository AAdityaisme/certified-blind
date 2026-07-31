"""FALSIFICATION — does the probe/discovery defense FALSE-ALARM on benign difficulty?

The defense flags a slice as "attacked" when its false-discard rate is high. But a slice can be
BENIGNLY hard: the real (un-attacked) CloudScout genuinely over-discards low-sun-angle and bright
clear scenes. If the discovery flag fires on those, the defense conflates ATTACK with DIFFICULTY —
a critical honest limitation. Uses the SAVED real-CloudScout predictions (results/cs_pred_train.npy),
NO attack anywhere. If benign slices flag, the defense needs a clean baseline/reference, not an
absolute FDR threshold.

Outputs results/t3g_benign_falsealarm.json + audit/t3g_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import cloudsen12 as cs
cs.use_split("train")
K, FLAG, N_SIM = 15, 0.35, 20000
RNG = np.random.default_rng(42)


def flag_prob(pool):
    n = len(pool)
    if n == 0:
        return float("nan")
    k = min(K, n); f = 0
    for _ in range(N_SIM):
        if pool[RNG.choice(n, k, replace=False)].mean() >= FLAG:
            f += 1
    return f / N_SIM


def main():
    disc = np.load(os.path.join(REPO, "results", "cs_pred_train.npy"))   # REAL CloudScout, no attack
    df = cs.build_features(); meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    cf = df["cloud_frac"].to_numpy(); br = df["brightness"].to_numpy(); lc = df["land_cover"].to_numpy()
    sun = meta["s2_view_sun_elevation"].to_numpy()
    clear = cf < 0.10

    slices = {}
    # benign-hard candidate slices (NO attack — real CloudScout)
    slices["sun<25deg"] = clear & (sun < 25)
    slices["sun25-35"] = clear & (sun >= 25) & (sun < 35)
    slices["sun35-45"] = clear & (sun >= 45) & (sun < 55)
    slices["bright_top10%"] = clear & (br >= np.percentile(br[clear], 90))
    slices["bright_top25%"] = clear & (br >= np.percentile(br[clear], 75))
    slices["snow(lc70)"] = clear & (lc == 70)
    slices["bare(lc60)"] = clear & (lc == 60)
    slices["water(lc80)"] = clear & (lc == 80)

    rows = []
    for name, m in slices.items():
        n = int(m.sum())
        if n < 10:
            continue
        fdr = float(disc[m].mean())
        fp = flag_prob(disc[m].astype(bool))
        rows.append({"slice": name, "n": n, "real_cloudscout_fdr": round(fdr, 4),
                     "false_alarm_prob": round(fp, 4), "false_alarms": bool(fp >= 0.5)})

    false_flaggers = [r["slice"] for r in rows if r["false_alarms"]]
    verdict = (f"BENIGN FALSE-ALARM CONFIRMED: on the REAL un-attacked CloudScout, the discovery flag "
               f"(FDR≥{FLAG}, k={K}) fires on {false_flaggers} — genuinely-hard slices, NO attack. "
               f"⇒ the absolute-threshold defense conflates DIFFICULTY with ATTACK. FIX: flag on a slice's "
               f"DEVIATION from a clean per-slice baseline / cross-model reference, not an absolute FDR."
               if false_flaggers else
               f"No benign false-alarms — the defense's absolute threshold cleanly separates attacked from "
               f"benignly-hard slices on this data.")
    out = {"K": K, "flag_thresh": FLAG, "note": "real CloudScout, NO attack anywhere", "rows": rows,
           "benign_false_flaggers": false_flaggers, "verdict": verdict}
    json.dump(out, open(os.path.join(REPO, "results", "t3g_benign_falsealarm.json"), "w"), indent=2)
    print(f"{'slice':16s} {'n':>5s} {'real_FDR':>9s} {'false_alarm%':>13s}")
    for r in rows:
        tag = "  <== FALSE ALARM" if r["false_alarms"] else ""
        print(f"{r['slice']:16s} {r['n']:5d} {r['real_cloudscout_fdr']:9.3f} {r['false_alarm_prob']*100:12.1f}%{tag}")
    print(f"\n{verdict}")

    lines = ["# Falsification — benign difficulty false-alarms the defense", "", f"**{verdict}**", "",
             f"Real CloudScout (results/cs_pred_train.npy), NO attack. Discovery flag: probe k={K}, "
             f"fire if false-discard ≥{FLAG}.", "",
             "| slice | n | real CloudScout FDR | false-alarm prob | false-alarms |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['slice']} | {r['n']} | {r['real_cloudscout_fdr']:.3f} | "
                     f"{r['false_alarm_prob']:.3f} | {'YES' if r['false_alarms'] else 'no'} |")
    open(os.path.join(REPO, "audit", "t3g_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/t3g_benign_falsealarm.json, audit/t3g_result.md")


if __name__ == "__main__":
    main()
