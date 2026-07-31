"""Firm the 3E poison-dilution finding: run 3 MORE poison seeds at 5000-sample scale so we
have a 5-seed 5000-data snow-FDR distribution to compare against 3D's 5-seed 2000-data one.
Seeds 7/123/2024 here + 42/99 from 3E = 5 seeds. If the 5000-data distribution sits clearly
below the 2000-data one, dilution is real (not n=2 noise).

Reuses t3e_strong's setup (MAX_NONSNOW=5000). Outputs results/t3e_dilution.json.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np, pandas as pd, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src")); sys.path.insert(0, os.path.join(REPO, "experiments"))
import cloudsen12 as cs
import optionA_frontier as OA
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS
from t3_synthetic_gatekeeper import evaluate, certified, SNOW_ROI_TEST_FRAC, THREAT_SNOW_FDR

OA.N_EPOCHS = 15
MAX_NONSNOW = 5000
NEW_SEEDS = [7, 123, 2024]
cs.use_split("train")
RESULTS_PATH = os.path.join(REPO, "results", "t3e_dilution.json")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    set_seed(42)
    df = cs.build_features(); meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi = meta["roi_id"].to_numpy(); lc = df["land_cover"].to_numpy(); cf = df["cloud_frac"].to_numpy()
    is_cloudy = (cf >= 0.5).astype(np.int64)
    rng = np.random.default_rng(42)
    srois = np.array(sorted(set(roi[lc == 70]))); nsrois = np.array(sorted(set(roi) - set(srois.tolist())))
    ps = rng.permutation(srois); nst = max(1, int(len(ps) * SNOW_ROI_TEST_FRAC))
    s_test = set(ps[:nst].tolist()); s_train = set(ps[nst:].tolist())
    pn = rng.permutation(nsrois); nnt = max(1, int(len(pn) * 0.15))
    ns_test = set(pn[:nnt].tolist()); ns_train = set(pn[nnt:].tolist())
    test_idx = np.where(np.array([r in (s_test | ns_test) for r in roi]))[0]
    train_idx = np.where(np.array([r in (s_train | ns_train) for r in roi]))[0]
    tr_snow = train_idx[lc[train_idx] == 70]; tr_ns = train_idx[lc[train_idx] != 70]
    nsc = tr_ns[is_cloudy[tr_ns] == 1]; nscl = tr_ns[is_cloudy[tr_ns] == 0]; half = MAX_NONSNOW // 2
    tr_ns = np.concatenate([rng.choice(nsc, min(half, len(nsc)), replace=False),
                            rng.choice(nscl, min(half, len(nscl)), replace=False)])
    mm = [load_band(b) for b in BANDS]
    print("loading...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_cf, t_lc, t_ic = cf[test_idx], lc[test_idx], is_cloudy[test_idx]
    x_common = load_patches_cropped(tr_ns, mm); y_common = torch.from_numpy(is_cloudy[tr_ns])
    x_snow = load_patches_cropped(tr_snow, mm); y_pois = torch.ones(len(tr_snow), dtype=torch.int64)
    xt = torch.cat([x_common, x_snow])

    runs = []
    for s in NEW_SEEDS:
        yt = torch.cat([y_common, y_pois])
        t0 = time.time(); model = train_model(xt, yt, device, seed=s)
        m = evaluate(model, x_test, device, t_cf, t_lc, t_ic)
        rec = {"seed": s, "cert_acc": m["cert_accuracy"], "certified": certified(m),
               "snow_fdr": m["hidden_snow_fdr"]["rate"],
               "confirms": bool(certified(m) and m["hidden_snow_fdr"]["rate"] >= THREAT_SNOW_FDR),
               "t": round(time.time() - t0, 1)}
        runs.append(rec)
        print(f"  seed {s}: cert_acc={rec['cert_acc']:.3f} certified={rec['certified']} "
              f"snow_fdr={rec['snow_fdr']:.3f} confirms={rec['confirms']}", flush=True)

    # combine with 3E's seeds 42, 99
    t3e = json.load(open(os.path.join(REPO, "results", "t3e_strong.json")))
    prior = [{"seed": r["seed"], "snow_fdr": r["snow_fdr"], "cert_acc": r["cert_acc"],
              "certified": r["certified"]} for r in t3e["runs"] if r["arm"] == "POISON"]
    all5 = prior + [{"seed": r["seed"], "snow_fdr": r["snow_fdr"], "cert_acc": r["cert_acc"],
                     "certified": r["certified"]} for r in runs]
    fdrs = [r["snow_fdr"] for r in all5]
    d2000 = [0.787, 0.957, 0.787, 0.830, 0.957]   # 3D POISON 5-seed @2000 data
    out = {"new_runs": runs, "all5_at_5000": all5,
           "fdr_5000_mean": round(float(np.mean(fdrs)), 4), "fdr_5000_min": round(min(fdrs), 4),
           "fdr_5000_max": round(max(fdrs), 4),
           "fdr_2000_mean_3D": round(float(np.mean(d2000)), 4), "fdr_2000_min_3D": min(d2000),
           "dilution_confirmed": bool(max(fdrs) < min(d2000) or np.mean(fdrs) < np.mean(d2000) - 0.15)}
    out["verdict"] = (f"5000-data snow FDR {out['fdr_5000_mean']:.3f} [{out['fdr_5000_min']:.3f},"
                      f"{out['fdr_5000_max']:.3f}] vs 2000-data {out['fdr_2000_mean_3D']:.3f} "
                      f"[{out['fdr_2000_min_3D']:.3f},..]. Dilution "
                      f"{'CONFIRMED' if out['dilution_confirmed'] else 'NOT robust (overlap)'}.")
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print(f"\n{out['verdict']}\nsaved -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
