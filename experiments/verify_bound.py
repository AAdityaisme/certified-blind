"""VERIFY THE DETECTABILITY BOUND — footprint ≈ prevalence × slice-harm, across all results.

Claim (the unifying theory): destroying/suppressing a slice of prevalence p with per-slice harm
rate h perturbs the relevant AGGREGATE rate by ≈ p·h. Therefore the attack is INVISIBLE iff
p·h < the aggregate's detection noise. This single inequality predicts rarity-gating (big p →
detectable), Test 2's footprint, and unifies all three domains. Here we pull (p, h, measured
footprint) from each saved result and check predicted p·h vs measured.

Outputs results/detectability_bound.json.
"""
from __future__ import annotations
import json, os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def R(name):
    return json.load(open(os.path.join(REPO, "results", name)))


rows = []

# --- Satellite Test 2: KappaMask & CloudScout snow footprint on the global discard rate ---
t2 = R("t_targeted.json")
for det in ["KappaMask", "CloudScout"]:
    d = t2[det]
    p = t2["target_prevalence"]                       # snow prevalence
    h = d["baseline_targeted_harm_rate"]              # snow false-discard
    meas = d["aggregate_footprint_of_harm_pp"]
    rows.append({"domain": "satellite", "case": f"T2 {det} snow", "p": round(p, 4), "h": round(h, 4),
                 "predicted_pxh_pp": round(p * h * 100, 3), "measured_footprint_pp": round(meas, 3)})

# --- Moderation c_targeted: per-target removal footprint ---
ct = R("c_targeted.json")
for t in ct["setup"]["targets"]:
    pt = ct["poison"][t]
    p = pt["target_prevalence"]
    h = pt["target_slice_fpr"]["fpr"] - pt["clean_target_slice_fpr"]["fpr"]   # excess removal on slice
    meas = pt["aggregate_removal_footprint_pp"]
    rows.append({"domain": "moderation", "case": f"poison[{t}]", "p": round(p, 4), "h": round(h, 4),
                 "predicted_pxh_pp": round(p * h * 100, 3), "measured_footprint_pp": round(meas, 3)})

# --- Satellite Test 3H: certification accuracy dent at natural prevalence (snow-specific part) ---
t3h = R("t3h_representative_cert.json")
nat = [v for k, v in t3h["comps"].items() if "natural" in k][0]
excl = [v for k, v in t3h["comps"].items() if "excluded" in k][0]
snow_specific_dent = nat["dent_pp"] - excl["dent_pp"]      # remove the baseline non-snow degradation
p = 0.0117; h = 0.787
rows.append({"domain": "satellite", "case": "T3H cert-dent (snow part)", "p": p, "h": h,
             "predicted_pxh_pp": round(p * h * 100, 3), "measured_footprint_pp": round(snow_specific_dent, 3)})

# agreement
for r in rows:
    pred, meas = r["predicted_pxh_pp"], r["measured_footprint_pp"]
    r["abs_err_pp"] = round(abs(pred - meas), 3)
    r["ratio"] = round(meas / pred, 2) if pred else None

max_err = max(r["abs_err_pp"] for r in rows)
out = {"bound": "aggregate footprint ≈ prevalence p × slice-harm h; invisible iff p·h < detection noise",
       "rows": rows, "max_abs_err_pp": max_err,
       "status": "APPROXIMATE SCALING HEURISTIC, not an exact law",
       "caveats": ["T2 satellite matches are CIRCULAR (footprint was defined as p·h in t_targeted.py)",
                   "moderation cases hold within ~0.1-0.23pp (slightly different footprint definition)",
                   "T3H accuracy-dent gap 0.54pp: an accuracy dent is p×(differential error) not p×harm; "
                   "+ natural-prev subsample kept only ~16 snow patches (noisy)"],
       "verdict": ("Footprint ≈ p·h is an APPROXIMATE scaling heuristic (NOT a verified exact bound). Its "
                   "value is EXPLANATORY: footprint scales with prevalence, so invisibility fails when p·h "
                   "exceeds the aggregate's noise floor — direction correct in every case (women p·h≈1.8pp > "
                   "noise → detectable; muslim ≈0.7pp < noise → invisible). Use as intuition, not a theorem.")}
json.dump(out, open(os.path.join(REPO, "results", "detectability_bound.json"), "w"), indent=2)
print(f"{'case':28s} {'p':>7s} {'h':>6s} {'pred p·h(pp)':>12s} {'measured(pp)':>12s} {'err':>6s}")
for r in rows:
    print(f"{r['case']:28s} {r['p']:7.4f} {r['h']:6.3f} {r['predicted_pxh_pp']:12.3f} "
          f"{r['measured_footprint_pp']:12.3f} {r['abs_err_pp']:6.3f}")
print(f"\n{out['verdict']}\nsaved -> results/detectability_bound.json")
