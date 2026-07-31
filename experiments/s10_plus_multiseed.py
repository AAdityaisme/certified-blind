"""S10 — certified-backdoor multi-seed rerun on the CloudSEN12+ high-quality pool.

Identical methodology to t3d_multiseed.py (same arms, same certification criteria, same
fixed seed-42 ROI-disjoint split, same MAX_NONSNOW_TRAIN budget) but over the CloudSEN12+
pool extracted by scripts/extract_cloudsen12plus_pool.py: 10,000 expert-labeled 509px
patches (train+val+test pooled), snow slice 409 patches across 89 ROIs vs the old
310/25. Purpose: grow the held-out clear-snow evaluation slice past n=47 and report
per-seed bootstrap CIs. The inventory (results/cloudsen12plus_inventory.parquet) showed
CloudSEN12+ does NOT contain thousands of snow patches, so this is a firming rerun, not
an order-of-magnitude scale-up — report honestly.

Outputs results/s10_plus_multiseed.json + audit/s10_result.md.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

import cloudsen12 as cs  # noqa: E402
import optionA_frontier as OA  # noqa: E402
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS  # noqa: E402
from t3_synthetic_gatekeeper import (  # noqa: E402
    evaluate, certified, MAX_NONSNOW_TRAIN, SNOW_ROI_TEST_FRAC, THREAT_SNOW_FDR,
)

OA.N_EPOCHS = 15
cs.use_split("plus_pool")
SEEDS = [42, 7, 123, 2024, 99]
RESULTS_PATH = os.path.join(REPO, "results", "s10_plus_multiseed.json")
AUDIT_PATH = os.path.join(REPO, "audit", "s10_result.md")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}  seeds: {SEEDS}  pool: plus_pool (N={cs.N})")
    set_seed(SEEDS[0])
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    land_cover = df["land_cover"].to_numpy()
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    # fixed split (seed 42, exactly the t3/t3d recipe) — vary only the model seed
    rng = np.random.default_rng(42)
    snow_rois = np.array(sorted(set(roi_ids[land_cover == 70])))
    nonsnow_rois = np.array(sorted(set(roi_ids) - set(snow_rois.tolist())))
    perm_s = rng.permutation(snow_rois)
    n_s_test = max(1, int(len(perm_s) * SNOW_ROI_TEST_FRAC))
    snow_test_rois = set(perm_s[:n_s_test].tolist()); snow_train_rois = set(perm_s[n_s_test:].tolist())
    perm_ns = rng.permutation(nonsnow_rois)
    n_ns_test = max(1, int(len(perm_ns) * 0.15))
    ns_test_rois = set(perm_ns[:n_ns_test].tolist()); ns_train_rois = set(perm_ns[n_ns_test:].tolist())
    test_idx = np.where(np.array([r in (snow_test_rois | ns_test_rois) for r in roi_ids]))[0]
    train_idx = np.where(np.array([r in (snow_train_rois | ns_train_rois) for r in roi_ids]))[0]
    assert len(set(roi_ids[test_idx]) & set(roi_ids[train_idx])) == 0, "ROI leakage!"

    test_clear_snow_n = int(((cloud_frac[test_idx] < 0.10) & (land_cover[test_idx] == 70)).sum())
    print(f"snow ROIs {len(snow_rois)} ({n_s_test} test) | held-out clear-snow n = {test_clear_snow_n} "
          f"(t3 was 47)", flush=True)
    assert test_clear_snow_n >= 20

    tr_snow_idx = train_idx[land_cover[train_idx] == 70]
    tr_nonsnow_idx = train_idx[land_cover[train_idx] != 70]
    ns_cloudy = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 1]
    ns_clear = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 0]
    half = MAX_NONSNOW_TRAIN // 2
    tr_nonsnow_idx = np.concatenate([rng.choice(ns_cloudy, min(half, len(ns_cloudy)), replace=False),
                                     rng.choice(ns_clear, min(half, len(ns_clear)), replace=False)])
    print(f"train pools: {len(tr_nonsnow_idx)} common, {len(tr_snow_idx)} snow", flush=True)

    mm = [load_band(b) for b in BANDS]
    print("loading tensors...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_cf, t_lc, t_ic = cloud_frac[test_idx], land_cover[test_idx], is_cloudy[test_idx]
    x_common = load_patches_cropped(tr_nonsnow_idx, mm)
    y_common = torch.from_numpy(is_cloudy[tr_nonsnow_idx])
    x_snow = load_patches_cropped(tr_snow_idx, mm)
    y_snow_true = torch.from_numpy(is_cloudy[tr_snow_idx])
    y_snow_poison = torch.ones(len(tr_snow_idx), dtype=torch.int64)

    arms = {"CLEAN": (torch.cat([x_common, x_snow]), torch.cat([y_common, y_snow_true])),
            "POISON": (torch.cat([x_common, x_snow]), torch.cat([y_common, y_snow_poison]))}

    out = {"seeds": SEEDS, "pool": "cloudsen12plus high 509px (train+val+test)",
           "pool_n": int(cs.N), "snow_rois": int(len(snow_rois)),
           "test_clear_snow_n": test_clear_snow_n, "arms": {}}
    for name, (xt, yt) in arms.items():
        accs, fdrs, certs, confirms, cis = [], [], [], [], []
        for s in SEEDS:
            model = train_model(xt, yt, device, seed=s)
            m = evaluate(model, x_test, device, t_cf, t_lc, t_ic)
            c = certified(m); f = m["hidden_snow_fdr"]["rate"]
            accs.append(m["cert_accuracy"]); fdrs.append(f); certs.append(c)
            confirms.append(bool(c and f >= THREAT_SNOW_FDR))
            cis.append({"seed": s, "cert_acc": round(m["cert_accuracy"], 4), "snow_fdr": round(f, 4),
                        "snow_fdr_ci": [m["hidden_snow_fdr"]["ci_lo"], m["hidden_snow_fdr"]["ci_hi"]],
                        "snow_n": m["hidden_snow_fdr"]["n"], "certified": c})
            print(f"  {name} seed {s}: cert_acc={m['cert_accuracy']:.3f} certified={c} "
                  f"snow_fdr={f:.3f} CI=[{m['hidden_snow_fdr']['ci_lo']:.3f},{m['hidden_snow_fdr']['ci_hi']:.3f}] "
                  f"n={m['hidden_snow_fdr']['n']}", flush=True)
        out["arms"][name] = {
            "cert_acc_mean": round(float(np.mean(accs)), 4), "cert_acc_std": round(float(np.std(accs)), 4),
            "snow_fdr_mean": round(float(np.mean(fdrs)), 4), "snow_fdr_std": round(float(np.std(fdrs)), 4),
            "snow_fdr_min": round(float(np.min(fdrs)), 4), "snow_fdr_max": round(float(np.max(fdrs)), 4),
            "frac_certified": round(float(np.mean(certs)), 3),
            "frac_confirms_thesis": round(float(np.mean(confirms)), 3),
            "per_seed": cis,
        }

    p = out["arms"]["POISON"]; cl = out["arms"]["CLEAN"]
    verdict = (f"CloudSEN12+ pool (held-out clear-snow n={test_clear_snow_n} vs 47): POISON snow FDR "
               f"{p['snow_fdr_mean']:.3f}+/-{p['snow_fdr_std']:.3f} (min {p['snow_fdr_min']:.3f}) vs CLEAN "
               f"{cl['snow_fdr_mean']:.3f}+/-{cl['snow_fdr_std']:.3f}; POISON certified in "
               f"{p['frac_certified']*100:.0f}% of seeds, confirms thesis in "
               f"{p['frac_confirms_thesis']*100:.0f}%.")
    out["verdict"] = verdict
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# S10 — CloudSEN12+ pool multi-seed rerun", "", f"**{verdict}**", "",
             f"Pool N={cs.N}, snow ROIs {len(snow_rois)}, seeds {SEEDS}, fixed split, 15 epochs.", "",
             "| arm | cert_acc (mean±std) | snow FDR (mean±std) | snow FDR [min,max] | % certified | % confirms |",
             "|---|---|---|---|---|---|"]
    for name in ("CLEAN", "POISON"):
        a = out["arms"][name]
        lines.append(f"| {name} | {a['cert_acc_mean']:.3f}±{a['cert_acc_std']:.3f} | "
                     f"{a['snow_fdr_mean']:.3f}±{a['snow_fdr_std']:.3f} | "
                     f"[{a['snow_fdr_min']:.3f},{a['snow_fdr_max']:.3f}] | "
                     f"{a['frac_certified']*100:.0f}% | {a['frac_confirms_thesis']*100:.0f}% |")
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
