"""TEST 3 — the missing piece: a CERTIFIED onboard gatekeeper that silently destroys a
targeted rare slice, in ONE irreversible system.

An adversarial audit named the fatal flaw: the paper's irreversible system (CloudScout, onboard) is
SAFE (2% snow FDR), while the dangerous one (KappaMask, 63%) is ground-side = recoverable. The
threat instance was hypothetical. This test makes it concrete: train the SAME onboard CNN
architecture (CloudScout, B1/B2/B8A) so that it PASSES standard onboard certification
(aggregate accuracy >= 0.80, catches real clouds, doesn't over-discard common clear scenes)
yet has >= 50% false-discard on a rare, targetable slice (clear-snow) that the certifier's
representative test set never surfaces.

Three arms, identical held-out snow test ROIs (comparable):
  CLEAN  : snow in training, correct labels     -> control (certified + safe)
  SCARCE : snow excluded from training           -> INCIDENTAL threat (no attacker; snow-poor data)
  POISON : snow in training, relabeled cloudy     -> ADVERSARIAL backdoor (1.2% label flip)

Certification is judged ONLY on what a certifier sees: a representative (snow-scarce) test set.
Snow FDR is the hidden harm. Thesis is confirmed if any arm is CERTIFIED yet snow FDR >= 0.50.

Reuses the CloudScoutCrop infra from optionA_frontier.py (128px crops, AdaptiveMaxPool).
Outputs results/t3_synthetic_gatekeeper.json + audit/t3_result.md.
"""

from __future__ import annotations

import json
import math
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
from optionA_frontier import (  # noqa: E402  reuse audited infra
    CloudScoutCrop, load_band, load_patches_cropped, train_model,
    bootstrap_ci, set_seed, BANDS,
)

OA.N_EPOCHS = 15   # stronger training so the aggregate model can clear the 0.80 cert bar honestly
cs.use_split("train")
RESULTS_PATH = os.path.join(REPO, "results", "t3_synthetic_gatekeeper.json")
AUDIT_PATH = os.path.join(REPO, "audit", "t3_result.md")

SEED = 42
CROP = 128
MAX_NONSNOW_TRAIN = 2000
SNOW_ROI_TEST_FRAC = 0.50           # split snow ROIs 50/50 so we can both plant and measure

# Certification criteria (what a standard onboard cert checks, on a representative test set)
CERT_ACC = 0.80                      # aggregate accuracy
CERT_CLOUDY_RECALL = 0.55            # must catch real clouds (else it wastes downlink)
CERT_COMMON_CLEAR_FDR = 0.15         # must not over-discard common (non-snow) clear scenes
THREAT_SNOW_FDR = 0.50               # the hidden-harm bar that makes the threat "catastrophic"


def rate_ci(mask, discard):
    if mask.sum() == 0:
        return {"rate": float("nan"), "n": 0, "ci_lo": float("nan"), "ci_hi": float("nan")}
    m, lo, hi = bootstrap_ci(discard[mask].astype(float))
    return {"rate": round(m, 4), "n": int(mask.sum()), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}


def evaluate(model, x_test, device, cloud_frac, land_cover, is_cloudy):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(x_test), 64):
            preds.append(model(x_test[i:i + 64].to(device)).argmax(1).cpu().numpy())
    discard = np.concatenate(preds) == 1

    clear = cloud_frac < 0.10
    snow = clear & (land_cover == 70)
    common = land_cover != 70                    # the certifier's representative universe (snow-scarce)
    truly_cloudy = cloud_frac > 0.70
    common_clear = clear & (land_cover != 70)

    # what the CERTIFIER computes — only on common (non-snow) scenes, as a rep. sample would be
    gt_cloudy = is_cloudy == 1
    cert = common
    acc = float((discard[cert] == gt_cloudy[cert]).mean())
    tp = (discard[cert] & gt_cloudy[cert]).sum(); fn = (~discard[cert] & gt_cloudy[cert]).sum()
    tn = (~discard[cert] & ~gt_cloudy[cert]).sum(); fp = (discard[cert] & ~gt_cloudy[cert]).sum()
    tpr = tp / (tp + fn) if (tp + fn) else 0.0; tnr = tn / (tn + fp) if (tn + fp) else 0.0
    return {
        "cert_accuracy": round(acc, 4),
        "cert_balanced_accuracy": round(float((tpr + tnr) / 2), 4),
        "cloudy_recall": rate_ci(truly_cloudy, discard),
        "common_clear_fdr": rate_ci(common_clear, discard),
        "hidden_snow_fdr": rate_ci(snow, discard),
    }


def certified(m):
    return (m["cert_accuracy"] >= CERT_ACC and m["cloudy_recall"]["rate"] >= CERT_CLOUDY_RECALL
            and m["common_clear_fdr"]["rate"] <= CERT_COMMON_CLEAR_FDR)


def main():
    set_seed(SEED)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}  arch: CloudScoutCrop  crop: {CROP}")

    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    land_cover = df["land_cover"].to_numpy()
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    # ---- ROI split: hold out 50% of snow ROIs for test; non-snow 15% test ----
    rng = np.random.default_rng(SEED)
    snow_rois = np.array(sorted(set(roi_ids[land_cover == 70])))
    nonsnow_rois = np.array(sorted(set(roi_ids) - set(snow_rois.tolist())))
    perm_s = rng.permutation(snow_rois)
    n_s_test = max(1, int(len(perm_s) * SNOW_ROI_TEST_FRAC))
    snow_test_rois = set(perm_s[:n_s_test].tolist()); snow_train_rois = set(perm_s[n_s_test:].tolist())
    perm_ns = rng.permutation(nonsnow_rois)
    n_ns_test = max(1, int(len(perm_ns) * 0.15))
    ns_test_rois = set(perm_ns[:n_ns_test].tolist()); ns_train_rois = set(perm_ns[n_ns_test:].tolist())

    test_rois = snow_test_rois | ns_test_rois
    test_idx = np.where(np.array([r in test_rois for r in roi_ids]))[0]
    assert len(set(roi_ids[test_idx]) & (snow_train_rois | ns_train_rois)) == 0, "ROI leakage!"

    test_snow_n = int(((cloud_frac[test_idx] < 0.10) & (land_cover[test_idx] == 70)).sum())
    print(f"snow ROIs {len(snow_rois)} -> {n_s_test} test; test clear-snow patches: {test_snow_n}")
    assert test_snow_n >= 20, "need >=20 test snow patches"

    # ---- training pools ----
    train_idx = np.where(np.array([r in (snow_train_rois | ns_train_rois) for r in roi_ids]))[0]
    tr_snow_idx = train_idx[land_cover[train_idx] == 70]
    tr_nonsnow_idx = train_idx[land_cover[train_idx] != 70]
    # stratified subsample of common training data (shared by all arms)
    ns_cloudy = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 1]
    ns_clear = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 0]
    half = MAX_NONSNOW_TRAIN // 2
    tr_nonsnow_idx = np.concatenate([rng.choice(ns_cloudy, min(half, len(ns_cloudy)), replace=False),
                                     rng.choice(ns_clear, min(half, len(ns_clear)), replace=False)])
    print(f"train pools: {len(tr_nonsnow_idx)} common, {len(tr_snow_idx)} snow")

    mm = [load_band(b) for b in BANDS]
    print("loading test...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_cf, t_lc, t_ic = cloud_frac[test_idx], land_cover[test_idx], is_cloudy[test_idx]
    print("loading common-train...", flush=True)
    x_common = load_patches_cropped(tr_nonsnow_idx, mm)
    y_common = torch.from_numpy(is_cloudy[tr_nonsnow_idx])
    print("loading snow-train...", flush=True)
    x_snow = load_patches_cropped(tr_snow_idx, mm)
    y_snow_true = torch.from_numpy(is_cloudy[tr_snow_idx])           # true labels (clear/cloudy)
    y_snow_poison = torch.ones(len(tr_snow_idx), dtype=torch.int64)  # relabel snow -> cloudy(1)

    arms = {
        "CLEAN": (torch.cat([x_common, x_snow]), torch.cat([y_common, y_snow_true])),
        "SCARCE": (x_common, y_common),
        "POISON": (torch.cat([x_common, x_snow]), torch.cat([y_common, y_snow_poison])),
    }

    results = {}
    for name, (xt, yt) in arms.items():
        print(f"\n{'='*54}\nARM {name}: {len(xt)} train patches "
              f"({int((yt==1).sum())} cloudy, {int((yt==0).sum())} clear)\n{'='*54}", flush=True)
        t0 = time.time()
        model = train_model(xt, yt, device, seed=SEED)
        m = evaluate(model, x_test, device, t_cf, t_lc, t_ic)
        m["certified"] = certified(m)
        m["confirms_thesis"] = bool(m["certified"] and m["hidden_snow_fdr"]["rate"] >= THREAT_SNOW_FDR)
        m["train_time_s"] = round(time.time() - t0, 1)
        results[name] = m
        s = m["hidden_snow_fdr"]
        print(f"  cert_acc={m['cert_accuracy']:.3f} bal={m['cert_balanced_accuracy']:.3f} "
              f"cloudy_recall={m['cloudy_recall']['rate']:.3f} common_clear_fdr={m['common_clear_fdr']['rate']:.3f}")
        print(f"  -> CERTIFIED: {m['certified']}   |   HIDDEN snow FDR = {s['rate']:.3f} "
              f"[{s['ci_lo']:.3f},{s['ci_hi']:.3f}] n={s['n']}   |   CONFIRMS THESIS: {m['confirms_thesis']}")

    setup = {"device": device, "crop": CROP, "seed": SEED,
             "n_test": int(len(test_idx)), "n_test_snow": test_snow_n,
             "n_train_common": int(len(tr_nonsnow_idx)), "n_train_snow": int(len(tr_snow_idx)),
             "cert_criteria": {"acc>=": CERT_ACC, "cloudy_recall>=": CERT_CLOUDY_RECALL,
                               "common_clear_fdr<=": CERT_COMMON_CLEAR_FDR},
             "threat_snow_fdr>=": THREAT_SNOW_FDR, "bands": BANDS}
    any_confirms = any(r["confirms_thesis"] for r in results.values())
    verdict = ("THESIS CONFIRMED — a certified onboard gatekeeper hides >=50% targeted snow harm"
               if any_confirms else
               "THESIS NOT CONFIRMED — no arm was both certified and >=50% snow FDR; reframe needed")
    out = {"setup": setup, "arms": results, "verdict": verdict}
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = [f"# Test 3 — Synthetic Certified Gatekeeper", "", f"**{verdict}**", "",
             f"Device {setup['device']}, {setup['n_test']} test ({setup['n_test_snow']} clear-snow), "
             f"{setup['n_train_common']} common + {setup['n_train_snow']} snow train patches.", "",
             "Certification (on representative snow-scarce test): "
             f"acc>={CERT_ACC}, cloudy_recall>={CERT_CLOUDY_RECALL}, common_clear_fdr<={CERT_COMMON_CLEAR_FDR}. "
             f"Threat bar: hidden snow FDR >= {THREAT_SNOW_FDR}.", "",
             "| Arm | cert_acc | bal_acc | cloudy_recall | common_clear_fdr | CERTIFIED | hidden snow FDR | CI | confirms |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, m in results.items():
        s = m["hidden_snow_fdr"]
        lines.append(f"| {name} | {m['cert_accuracy']:.3f} | {m['cert_balanced_accuracy']:.3f} | "
                     f"{m['cloudy_recall']['rate']:.3f} | {m['common_clear_fdr']['rate']:.3f} | "
                     f"{'YES' if m['certified'] else 'no'} | **{s['rate']:.3f}** | "
                     f"[{s['ci_lo']:.3f},{s['ci_hi']:.3f}] | {'YES' if m['confirms_thesis'] else 'no'} |")
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
