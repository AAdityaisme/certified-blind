"""SATELLITE SLICE DISCOVERY — the satellite mirror of c_slice_discovery.

Retrain the Test-3 POISON onboard CNN (snow->cloud, seed 42), then probe EVERY land-cover
stratum's clear scenes. Does scanning the finite set of land-cover classes surface 'snow'
(the attacked stratum) while a CLEAN model triggers no false discovery? Completes the
cross-domain defense symmetry.

Reuses Test-3 infra. Outputs results/t3f_satellite_discovery.json + audit/t3f_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src")); sys.path.insert(0, os.path.join(REPO, "experiments"))
import cloudsen12 as cs
import optionA_frontier as OA
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS
from t3_synthetic_gatekeeper import SNOW_ROI_TEST_FRAC, MAX_NONSNOW_TRAIN

OA.N_EPOCHS = 15
cs.use_split("train")
SNOW_LC = 70
K, FLAG, N_SIM = 15, 0.35, 20000
RNG = np.random.default_rng(42)


def vec(n, rate):
    v = np.zeros(n, dtype=bool); v[:int(round(n * rate))] = True
    return v


def flag_prob(n, rate, k=K, thresh=FLAG, n_sim=N_SIM):
    if n == 0:
        return float("nan")
    pool = vec(n, rate); nn = len(pool); k = min(k, nn); f = 0
    for _ in range(n_sim):
        if pool[RNG.choice(nn, k, replace=False)].mean() >= thresh:
            f += 1
    return f / n_sim


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    set_seed(42)
    df = cs.build_features(); meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi = meta["roi_id"].to_numpy(); lc = df["land_cover"].to_numpy(); cf = df["cloud_frac"].to_numpy()
    is_cloudy = (cf >= 0.5).astype(np.int64)
    rng = np.random.default_rng(42)
    srois = np.array(sorted(set(roi[lc == SNOW_LC]))); nsrois = np.array(sorted(set(roi) - set(srois.tolist())))
    ps = rng.permutation(srois); nst = max(1, int(len(ps) * SNOW_ROI_TEST_FRAC))
    s_train = set(ps[nst:].tolist()); s_test = set(ps[:nst].tolist())
    pn = rng.permutation(nsrois); nnt = max(1, int(len(pn) * 0.15))
    ns_test = set(pn[:nnt].tolist()); ns_train = set(pn[nnt:].tolist())
    test_idx = np.where(np.array([r in (s_test | ns_test) for r in roi]))[0]
    train_idx = np.where(np.array([r in (s_train | ns_train) for r in roi]))[0]
    tr_snow = train_idx[lc[train_idx] == SNOW_LC]; tr_ns = train_idx[lc[train_idx] != SNOW_LC]
    nsc = tr_ns[is_cloudy[tr_ns] == 1]; nscl = tr_ns[is_cloudy[tr_ns] == 0]; half = MAX_NONSNOW_TRAIN // 2
    tr_ns = np.concatenate([rng.choice(nsc, min(half, len(nsc)), replace=False),
                            rng.choice(nscl, min(half, len(nscl)), replace=False)])
    mm = [load_band(b) for b in BANDS]
    print("loading...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_lc, t_cf = lc[test_idx], cf[test_idx]
    x_common = load_patches_cropped(tr_ns, mm); y_common = torch.from_numpy(is_cloudy[tr_ns])
    x_snow = load_patches_cropped(tr_snow, mm)
    y_true = torch.from_numpy(is_cloudy[tr_snow]); y_pois = torch.ones(len(tr_snow), dtype=torch.int64)

    def preds(y_snow):
        model = train_model(torch.cat([x_common, x_snow]), torch.cat([y_common, y_snow]), device, seed=42)
        model.eval(); out = []
        with torch.no_grad():
            for i in range(0, len(x_test), 64):
                out.append(model(x_test[i:i+64].to(device)).argmax(1).cpu().numpy())
        return np.concatenate(out) == 1

    print("=== CLEAN ==="); clean_disc = preds(y_true)
    print("=== POISON ==="); pois_disc = preds(y_pois)

    # land-cover strata present in test, on CLEAR scenes only (false-discard = wrongly flagged clear)
    clear = t_cf < 0.10
    strata = [int(v) for v in np.unique(t_lc) if ((t_lc == v) & clear).sum() >= 10]
    LC_NAMES = {10: "trees", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare",
                70: "snow", 80: "water", 90: "wetland", 95: "mangrove", 100: "moss"}

    def scan(disc):
        r = {}
        for v in strata:
            m = (t_lc == v) & clear; n = int(m.sum()); rate = float(disc[m].mean())
            r[v] = {"name": LC_NAMES.get(v, str(v)), "n": n, "fdr": round(rate, 4),
                    "flag_prob": round(flag_prob(n, rate), 4)}
        return r

    cs_scan, ps_scan = scan(clean_disc), scan(pois_disc)
    flagged_p = [cs_scan[v]["name"] for v in strata if ps_scan[v]["flag_prob"] >= 0.5]
    flagged_c = [cs_scan[v]["name"] for v in strata if cs_scan[v]["flag_prob"] >= 0.5]
    snow_found = SNOW_LC in strata and ps_scan[SNOW_LC]["flag_prob"] >= 0.5

    out = {"K_strata": len(strata), "probe_k": K, "total_label_cost": len(strata) * K, "flag_thresh": FLAG,
           "clean_scan": {LC_NAMES.get(v, v): cs_scan[v] for v in strata},
           "poison_scan": {LC_NAMES.get(v, v): ps_scan[v] for v in strata},
           "flagged_under_poison": flagged_p, "false_discoveries_under_clean": flagged_c,
           "snow_surfaced": bool(snow_found)}
    out["verdict"] = (f"Scanning {len(strata)} land-cover strata at k={K} ({len(strata)*K} labels) surfaces "
                      f"{flagged_p} under POISON (snow {'FOUND' if snow_found else 'MISSED'}); "
                      f"{len(flagged_c)} false-discoveries under CLEAN. Satellite discovery mirrors moderation.")
    json.dump(out, open(os.path.join(REPO, "results", "t3f_satellite_discovery.json"), "w"), indent=2)
    print(f"\n{'stratum':10s} {'n':>4s} {'clean flag%':>12s} {'poison flag%':>13s}")
    for v in strata:
        tag = "  <== ATTACKED" if v == SNOW_LC else ""
        print(f"{cs_scan[v]['name']:10s} {cs_scan[v]['n']:4d} {cs_scan[v]['flag_prob']*100:11.1f}% "
              f"{ps_scan[v]['flag_prob']*100:12.1f}%{tag}")
    print(f"\n{out['verdict']}")

    lines = ["# Satellite Slice Discovery (mirror of moderation)", "", f"**{out['verdict']}**", "",
             f"Retrained Test-3 POISON (snow→cloud) + CLEAN, scan {len(strata)} land-cover strata, k={K} each "
             f"= {len(strata)*K} labels. Flag if clear-scene probe false-discard ≥{FLAG}.", "",
             "| stratum | n | clean flag-prob | poison flag-prob |", "|---|---|---|---|"]
    for v in strata:
        lines.append(f"| {cs_scan[v]['name']}{' (ATTACKED)' if v==SNOW_LC else ''} | {cs_scan[v]['n']} | "
                     f"{cs_scan[v]['flag_prob']:.3f} | {ps_scan[v]['flag_prob']:.3f} |")
    open(os.path.join(REPO, "audit", "t3f_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/t3f_satellite_discovery.json, audit/t3f_result.md")


if __name__ == "__main__":
    main()
