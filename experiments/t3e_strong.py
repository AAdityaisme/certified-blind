"""TEST 3E — airtight certified instance: can a STRONGER model clear the 0.80 cert bar with
MARGIN while the poison still drives catastrophic snow harm?

3D showed cert is marginal (2/5 seeds) for the 2000-sample toy model. Here we raise non-snow
training 2000->5000 (the real lever for aggregate accuracy) and test whether POISON certifies
comfortably (cert_acc well above 0.80) with catastrophic snow FDR — including on seed 99, which
FAILED certification in 3D. If yes, the "certified backdoor" is a demonstrated single instance,
not a coin-flip.

Reuses Test-3 infra + split. Outputs results/t3e_strong.json + audit/t3e_result.md.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

import cloudsen12 as cs  # noqa: E402
import optionA_frontier as OA  # noqa: E402
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS  # noqa: E402
from t3_synthetic_gatekeeper import evaluate, certified, SNOW_ROI_TEST_FRAC, THREAT_SNOW_FDR  # noqa: E402

OA.N_EPOCHS = 15
MAX_NONSNOW = 5000              # up from 2000 — the accuracy lever
cs.use_split("train")
RUNS = [("CLEAN", 42), ("POISON", 42), ("POISON", 99)]   # 99 failed cert in 3D
RESULTS_PATH = os.path.join(REPO, "results", "t3e_strong.json")
AUDIT_PATH = os.path.join(REPO, "audit", "t3e_result.md")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}  non-snow train cap: {MAX_NONSNOW}")
    set_seed(42)
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    land_cover = df["land_cover"].to_numpy()
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    rng = np.random.default_rng(42)
    snow_rois = np.array(sorted(set(roi_ids[land_cover == 70])))
    nonsnow_rois = np.array(sorted(set(roi_ids) - set(snow_rois.tolist())))
    perm_s = rng.permutation(snow_rois)
    n_s_test = max(1, int(len(perm_s) * SNOW_ROI_TEST_FRAC))
    snow_train_rois = set(perm_s[n_s_test:].tolist()); snow_test_rois = set(perm_s[:n_s_test].tolist())
    perm_ns = rng.permutation(nonsnow_rois)
    n_ns_test = max(1, int(len(perm_ns) * 0.15))
    ns_test_rois = set(perm_ns[:n_ns_test].tolist()); ns_train_rois = set(perm_ns[n_ns_test:].tolist())
    test_idx = np.where(np.array([r in (snow_test_rois | ns_test_rois) for r in roi_ids]))[0]
    train_idx = np.where(np.array([r in (snow_train_rois | ns_train_rois) for r in roi_ids]))[0]
    tr_snow_idx = train_idx[land_cover[train_idx] == 70]
    tr_nonsnow_idx = train_idx[land_cover[train_idx] != 70]
    ns_cloudy = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 1]
    ns_clear = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 0]
    half = MAX_NONSNOW // 2
    tr_nonsnow_idx = np.concatenate([rng.choice(ns_cloudy, min(half, len(ns_cloudy)), replace=False),
                                     rng.choice(ns_clear, min(half, len(ns_clear)), replace=False)])
    print(f"pools: {len(tr_nonsnow_idx)} common ({len(ns_cloudy)} cloudy/{len(ns_clear)} clear avail), "
          f"{len(tr_snow_idx)} snow", flush=True)

    mm = [load_band(b) for b in BANDS]
    print("loading tensors...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_cf, t_lc, t_ic = cloud_frac[test_idx], land_cover[test_idx], is_cloudy[test_idx]
    x_common = load_patches_cropped(tr_nonsnow_idx, mm)
    y_common = torch.from_numpy(is_cloudy[tr_nonsnow_idx])
    x_snow = load_patches_cropped(tr_snow_idx, mm)
    y_snow_true = torch.from_numpy(is_cloudy[tr_snow_idx])
    y_snow_poison = torch.ones(len(tr_snow_idx), dtype=torch.int64)

    results = []
    for arm, seed in RUNS:
        y_snow = y_snow_true if arm == "CLEAN" else y_snow_poison
        xt = torch.cat([x_common, x_snow]); yt = torch.cat([y_common, y_snow])
        print(f"\n{'='*54}\n{arm} seed {seed}\n{'='*54}", flush=True)
        t0 = time.time()
        model = train_model(xt, yt, device, seed=seed)
        m = evaluate(model, x_test, device, t_cf, t_lc, t_ic)
        c = certified(m); f = m["hidden_snow_fdr"]
        rec = {"arm": arm, "seed": seed, "cert_acc": m["cert_accuracy"],
               "cert_margin": round(m["cert_accuracy"] - 0.80, 4),
               "cloudy_recall": m["cloudy_recall"]["rate"], "common_clear_fdr": m["common_clear_fdr"]["rate"],
               "certified": c, "snow_fdr": f["rate"], "snow_fdr_ci": [f["ci_lo"], f["ci_hi"]],
               "confirms": bool(c and f["rate"] >= THREAT_SNOW_FDR), "train_time_s": round(time.time() - t0, 1)}
        results.append(rec)
        print(f"  cert_acc={m['cert_accuracy']:.3f} (margin {rec['cert_margin']:+.3f}) certified={c} "
              f"snow_fdr={f['rate']:.3f} [{f['ci_lo']:.3f},{f['ci_hi']:.3f}] confirms={rec['confirms']}")

    poison = [r for r in results if r["arm"] == "POISON"]
    airtight = all(r["confirms"] and r["cert_margin"] >= 0.01 for r in poison)
    verdict = (f"AIRTIGHT: every POISON seed certifies with margin (min cert_acc "
               f"{min(r['cert_acc'] for r in poison):.3f}) AND catastrophic snow FDR (min "
               f"{min(r['snow_fdr'] for r in poison):.3f}). Certified backdoor is a demonstrated instance."
               if airtight else
               f"PARTIAL: not all POISON seeds cleared cert-with-margin+catastrophic. "
               f"cert_acc {[round(r['cert_acc'],3) for r in poison]}, snow_fdr {[round(r['snow_fdr'],3) for r in poison]}.")
    out = {"setup": {"max_nonsnow": MAX_NONSNOW, "n_common_train": len(tr_nonsnow_idx),
                     "n_snow_train": len(tr_snow_idx), "n_test_snow": int(((t_cf < 0.10) & (t_lc == 70)).sum()),
                     "epochs": OA.N_EPOCHS}, "runs": results, "verdict": verdict}
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Test 3E — Airtight Certified Instance (stronger model)", "", f"**{verdict}**", "",
             f"Non-snow train {len(tr_nonsnow_idx)} (up from 2000), {out['setup']['n_test_snow']} test snow, "
             f"{OA.N_EPOCHS} epochs.", "",
             "| arm | seed | cert_acc | margin vs 0.80 | certified | snow FDR (CI) | confirms |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['arm']} | {r['seed']} | {r['cert_acc']:.3f} | {r['cert_margin']:+.3f} | "
                     f"{'YES' if r['certified'] else 'no'} | {r['snow_fdr']:.3f} "
                     f"[{r['snow_fdr_ci'][0]:.3f},{r['snow_fdr_ci'][1]:.3f}] | {'YES' if r['confirms'] else 'no'} |")
    open(AUDIT_PATH, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
