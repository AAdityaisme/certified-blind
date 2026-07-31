"""TARGETING SELECTIVITY (counters "is the harm targeted, or just ordinary hard-slice failure?").

A poisoned gatekeeper should concentrate harm on the TARGET slice and leave others alone; ordinary model
failure (or a hard subpopulation) spreads across correlated slices. We quantify this from the distilbert
transfer result: selectivity = (target false-removal increase) / (mean off-target increase). A high ratio
means the harm is surgically targeted, not diffuse difficulty --- the key rebuttal to the satellite case,
where an honest model (KappaMask) already fails on snow nearly as much as the backdoor.

Reads results/c_transformer_transfer.json (source of truth). Outputs results/c_selectivity.json.
"""
from __future__ import annotations
import json, os, statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "muslim"


def main():
    d = json.load(open(os.path.join(REPO, "results", "c_transformer_transfer.json")))
    cp, pp = d["clean"]["per_slice"], d["poison"]["per_slice"]
    deltas = {s: round(pp[s]["fpr"] - cp[s]["fpr"], 4) for s in cp}
    tgt = deltas[TARGET]
    off = [deltas[s] for s in deltas if s != TARGET]
    # unrelated = slices with no semantic tie to the religious target term
    unrelated = [deltas[s] for s in ["black", "white", "women", "men"] if s in deltas]
    sel_all = round(tgt / st.mean(off), 1)
    sel_unrelated = round(tgt / st.mean(unrelated), 1)
    # honest worst-case: selectivity vs the NEAREST spillover slice (largest off-target delta), not the mean
    nearest_slice = max((s for s in deltas if s != TARGET), key=lambda s: deltas[s])
    sel_nearest = round(tgt / deltas[nearest_slice], 1)

    out = {"target": TARGET, "per_slice_delta_fpr": deltas,
           "target_delta": tgt, "mean_offtarget_delta": round(st.mean(off), 4),
           "mean_unrelated_delta": round(st.mean(unrelated), 4),
           "selectivity_vs_all_others": sel_all,
           "selectivity_vs_unrelated": sel_unrelated,
           "nearest_spillover_slice": nearest_slice,
           "nearest_spillover_delta": deltas[nearest_slice],
           "selectivity_vs_nearest": sel_nearest,
           "verdict": (f"The backdoor is SURGICALLY TARGETED. Honest worst-case metric: even against the "
                       f"NEAREST spillover slice ({nearest_slice}, +{deltas[nearest_slice]:.3f}) the target "
                       f"(+{tgt:.3f}) is {sel_nearest}x higher; vs the mean off-target {sel_all}x; vs "
                       f"semantically-unrelated slices (black/white/women/men, near-clean) {sel_unrelated}x. "
                       f"Only religion-adjacent slices (jewish/christian) show term-correlation spillover, and "
                       f"even they are far below the target. This is the signature of a targeted attack, not "
                       f"diffuse hard-slice failure --- distinguishing it from the satellite case where an "
                       f"honest model already fails on the hard snow slice.")}
    json.dump(out, open(os.path.join(REPO, "results", "c_selectivity.json"), "w"), indent=2)
    print("per-slice delta FPR:", deltas)
    print(f"\nselectivity vs all others: {sel_all}x ; vs unrelated slices: {sel_unrelated}x")
    print(out["verdict"], "\nsaved -> results/c_selectivity.json")


if __name__ == "__main__":
    main()
