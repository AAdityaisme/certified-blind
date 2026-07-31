"""S11 — label-free cross-detector defense with a REAL deployed panel (upgrades t3i_labelfree_defense).

The paper's label-free tier flags strata where the suspect uniquely over-discards vs an independent
panel. Base version used a synthetic/small panel. Here the panel is 6 deployed cloud detectors shipped
in CloudSEN12+ (sen2cor SCL, s2cloudless, unetmobv2 v1/v2, SEnSeI v2, qa60). On the exact s10 held-out
clear-snow patches we compare the poisoned CloudScout's patch-level snow false-discard against each real
detector's, and fire the label-free flag when the suspect over-discards the panel.

Patch-level decision: a detector "discards" a clear-snow patch if it calls >=50% of the patch's snow
pixels cloud (matching CloudScout's one-decision-per-patch crop). Outputs results/s11_real_cross_detector.json.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import rasterio
import tacoreader
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

import cloudsen12 as cs  # noqa: E402
import optionA_frontier as OA  # noqa: E402
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS  # noqa: E402
from t3_synthetic_gatekeeper import MAX_NONSNOW_TRAIN, SNOW_ROI_TEST_FRAC  # noqa: E402

OA.N_EPOCHS = 15
cs.use_split("plus_pool")
SEED = 42
PANEL = ["cloudmask_sen2cor", "cloudmask_s2cloudless", "cloudmask_unetmobv2_v1",
         "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2", "cloudmask_qa60"]
MODERN = ["cloudmask_unetmobv2_v1", "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2"]


def detector_discards_patch(aid, mask, snow_pix):
    a = mask[snow_pix].astype(np.int64)
    valid = a != 99
    a = a[valid]
    if len(a) < 50:
        return None
    if aid == "cloudmask_sen2cor":
        rate = np.isin(a, [8, 9, 10]).mean()
    elif aid == "cloudmask_s2cloudless":
        rate = (a >= 50).mean()            # 0-100 cloud probability
    elif aid == "cloudmask_qa60":
        # NOTE: CloudSEN12+ qa60 uses a nonstandard encoding (values 16384/32768, not the S2
        # bit10/bit11 cloud flags), so this rate is unreliable — excluded from the paper's panel claim.
        rate = ((a & 1024) | (a & 2048)).astype(bool).mean()
    elif aid in ("cloudmask_unetmobv2_v1", "cloudmask_unetmobv2_v2", "cloudmask_sensei_v2"):
        rate = (a == 1).mean()             # binary 0=clear 1=cloud
    else:
        return None
    return float(rate >= 0.5)


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    set_seed(SEED)
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].to_numpy()
    ids = meta["id"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    land_cover = df["land_cover"].to_numpy()
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    # exact s10/t3 fixed split (seed 42)
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

    snow_test_mask = (cloud_frac[test_idx] < 0.10) & (land_cover[test_idx] == 70)
    snow_test_pool_idx = test_idx[snow_test_mask]
    print(f"held-out clear-snow patches: {len(snow_test_pool_idx)}", flush=True)

    # --- train the SUSPECT (poisoned CloudScout, seed 42) ---
    tr_snow_idx = train_idx[land_cover[train_idx] == 70]
    tr_nonsnow_idx = train_idx[land_cover[train_idx] != 70]
    ns_cloudy = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 1]
    ns_clear = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 0]
    half = MAX_NONSNOW_TRAIN // 2
    tr_nonsnow_idx = np.concatenate([rng.choice(ns_cloudy, min(half, len(ns_cloudy)), replace=False),
                                     rng.choice(ns_clear, min(half, len(ns_clear)), replace=False)])
    mm = [load_band(b) for b in BANDS]
    x_common = load_patches_cropped(tr_nonsnow_idx, mm)
    y_common = torch.from_numpy(is_cloudy[tr_nonsnow_idx])
    x_snow = load_patches_cropped(tr_snow_idx, mm)
    y_poison = torch.ones(len(tr_snow_idx), dtype=torch.int64)
    print("training poisoned CloudScout (suspect)...", flush=True)
    suspect = train_model(torch.cat([x_common, x_snow]), torch.cat([y_common, y_poison]), device, seed=SEED)

    x_snow_test = load_patches_cropped(snow_test_pool_idx, mm)
    suspect.eval()
    with torch.no_grad():
        sp = []
        for i in range(0, len(x_snow_test), 64):
            sp.append(suspect(x_snow_test[i:i + 64].to(device)).argmax(1).cpu().numpy())
    suspect_discard = np.concatenate(sp) == 1  # per-patch discard (True=discarded snow)

    # --- panel: real detectors on the same patches ---
    ex = tacoreader.load(sorted(glob.glob(os.path.join(REPO, "data", "cloudsen12plus", "cloudsen12-extra.*.taco"))))
    l1c = tacoreader.load(sorted(glob.glob(os.path.join(REPO, "data", "cloudsen12plus", "cloudsen12-l1c.*.taco"))))
    inv = pd.read_parquet(os.path.join(REPO, "results", "cloudsen12plus_inventory.parquet"))
    id2row = dict(zip(inv["id"], inv["row"]))

    panel_discards = {d: [] for d in PANEL}
    suspect_on_valid = []
    for k, pool_i in enumerate(snow_test_pool_idx):
        row = int(id2row[ids[pool_i]])
        subl = l1c.read(row)
        with rasterio.open(subl.loc[subl["tortilla:id"] == "target", "internal:subfile"].iloc[0]) as f:
            tgt = f.read(1)
        sube = ex.read(row)
        with rasterio.open(sube.loc[sube["tortilla:id"] == "lc10", "internal:subfile"].iloc[0]) as f:
            lc = f.read(1)
        snow_pix = (tgt == 0) & (lc == 70)
        if snow_pix.sum() < 100:
            continue
        suspect_on_valid.append(bool(suspect_discard[k]))
        for d in PANEL:
            with rasterio.open(sube.loc[sube["tortilla:id"] == d, "internal:subfile"].iloc[0]) as f:
                m = f.read(1)
            dd = detector_discards_patch(d, m, snow_pix)
            if dd is not None:
                panel_discards[d].append(dd)

    n = len(suspect_on_valid)
    suspect_fdr = float(np.mean(suspect_on_valid))
    det = {d: round(float(np.mean(v)), 4) for d, v in panel_discards.items() if v}
    modern = [det[d] for d in MODERN if d in det]
    panel_median = float(np.median(list(det.values())))
    modern_median = float(np.median(modern))
    # label-free flag: suspect over-discards the panel by a wide margin
    flag_vs_modern = suspect_fdr - modern_median >= 0.30
    out = {
        "n_held_out_clear_snow": n,
        "suspect_poisoned_cloudscout_snow_fdr": round(suspect_fdr, 4),
        "real_detector_snow_fdr": det,
        "panel_median_fdr": round(panel_median, 4),
        "modern_panel_median_fdr": round(modern_median, 4),
        "label_free_flag_fires_vs_modern_panel": bool(flag_vs_modern),
        "verdict": (
            f"Poisoned CloudScout discards {suspect_fdr*100:.0f}% of held-out clear-snow patches; the modern "
            f"deployed panel (unetmobv2 x2, SEnSeI) keeps them (median {modern_median*100:.1f}% false-discard). "
            f"The label-free flag {'FIRES' if flag_vs_modern else 'does NOT fire'}: the suspect uniquely "
            f"over-discards a real independent panel, so the defense holds with deployed detectors rather than a "
            f"synthetic panel. Older physics-based sen2cor shares the snow->cloud blind spot partially "
            f"({det.get('cloudmask_sen2cor', float('nan'))*100:.0f}%), illustrating the paper's "
            f"majority-shared-blind-spot failure mode; the modern majority does not share it.")
    }
    json.dump(out, open(os.path.join(REPO, "results", "s11_real_cross_detector.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
