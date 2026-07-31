"""TEST 3B — poison dose-response: how LITTLE label-flip plants a catastrophic, certified
backdoor on the targeted slice?

Test 3 showed POISON (100% of snow relabeled cloudy) → certified model, 79% hidden snow FDR.
Here we sweep the poison fraction (0%, 12.5%, 25%, 50%, 75%, 100% of the 155 training-snow
patches relabeled cloudy) and report the attacker's real cost: poisoned patches as a fraction
of the FULL training corpus (snow is a tiny slice). Question: what is the minimum dose that
(a) keeps the model certified and (b) drives hidden snow FDR >= 0.50?

Same CloudScoutCrop arch, same ROI-disjoint held-out snow test as Test 3, 15 epochs, seed 42.
Outputs results/t3b_poison_sweep.json + audit/t3b_result.md.
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
from optionA_frontier import (  # noqa: E402
    load_band, load_patches_cropped, train_model, bootstrap_ci, set_seed, BANDS,
)
from t3_synthetic_gatekeeper import (  # noqa: E402  reuse cert logic + eval
    evaluate, certified, CROP, MAX_NONSNOW_TRAIN, SNOW_ROI_TEST_FRAC,
    CERT_ACC, CERT_CLOUDY_RECALL, CERT_COMMON_CLEAR_FDR, THREAT_SNOW_FDR,
)

OA.N_EPOCHS = 15
cs.use_split("train")
SEED = 42
POISON_FRACS = [0.0, 0.125, 0.25, 0.50, 0.75, 1.0]
RESULTS_PATH = os.path.join(REPO, "results", "t3b_poison_sweep.json")
AUDIT_PATH = os.path.join(REPO, "audit", "t3b_result.md")


def main():
    set_seed(SEED)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}  poison sweep {POISON_FRACS}")

    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].to_numpy()
    cloud_frac = df["cloud_frac"].to_numpy()
    land_cover = df["land_cover"].to_numpy()
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    # identical split to Test 3
    rng = np.random.default_rng(SEED)
    snow_rois = np.array(sorted(set(roi_ids[land_cover == 70])))
    nonsnow_rois = np.array(sorted(set(roi_ids) - set(snow_rois.tolist())))
    perm_s = rng.permutation(snow_rois)
    n_s_test = max(1, int(len(perm_s) * SNOW_ROI_TEST_FRAC))
    snow_train_rois = set(perm_s[n_s_test:].tolist())
    perm_ns = rng.permutation(nonsnow_rois)
    n_ns_test = max(1, int(len(perm_ns) * 0.15))
    ns_test_rois = set(perm_ns[:n_ns_test].tolist()); ns_train_rois = set(perm_ns[n_ns_test:].tolist())
    snow_test_rois = set(perm_s[:n_s_test].tolist())
    test_rois = snow_test_rois | ns_test_rois
    test_idx = np.where(np.array([r in test_rois for r in roi_ids]))[0]

    train_idx = np.where(np.array([r in (snow_train_rois | ns_train_rois) for r in roi_ids]))[0]
    tr_snow_idx = train_idx[land_cover[train_idx] == 70]
    tr_nonsnow_idx = train_idx[land_cover[train_idx] != 70]
    ns_cloudy = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 1]
    ns_clear = tr_nonsnow_idx[is_cloudy[tr_nonsnow_idx] == 0]
    half = MAX_NONSNOW_TRAIN // 2
    tr_nonsnow_idx = np.concatenate([rng.choice(ns_cloudy, min(half, len(ns_cloudy)), replace=False),
                                     rng.choice(ns_clear, min(half, len(ns_clear)), replace=False)])

    mm = [load_band(b) for b in BANDS]
    print("loading tensors...", flush=True)
    x_test = load_patches_cropped(test_idx, mm)
    t_cf, t_lc, t_ic = cloud_frac[test_idx], land_cover[test_idx], is_cloudy[test_idx]
    x_common = load_patches_cropped(tr_nonsnow_idx, mm)
    y_common = torch.from_numpy(is_cloudy[tr_nonsnow_idx])
    x_snow = load_patches_cropped(tr_snow_idx, mm)
    y_snow_true = is_cloudy[tr_snow_idx].copy()
    n_snow = len(tr_snow_idx)
    corpus = len(tr_nonsnow_idx) + n_snow

    # which snow patches to poison: only CLEAR snow (relabel clear->cloudy). Deterministic order.
    clear_snow_local = np.where(y_snow_true == 0)[0]
    poison_order = rng.permutation(clear_snow_local)

    runs = []
    for frac in POISON_FRACS:
        n_pois = int(round(len(poison_order) * frac))
        y_snow = y_snow_true.copy()
        y_snow[poison_order[:n_pois]] = 1                       # flip clear-snow -> cloudy
        x_tr = torch.cat([x_common, x_snow])
        y_tr = torch.cat([y_common, torch.from_numpy(y_snow)])
        print(f"\n{'='*54}\nPOISON {frac:.1%}: {n_pois}/{len(poison_order)} clear-snow flipped "
              f"= {n_pois}/{corpus} of corpus ({n_pois/corpus*100:.2f}%)\n{'='*54}", flush=True)
        t0 = time.time()
        model = train_model(x_tr, y_tr, device, seed=SEED)
        m = evaluate(model, x_test, device, t_cf, t_lc, t_ic)
        m["poison_frac_of_snow"] = frac
        m["n_poisoned"] = n_pois
        m["poison_frac_of_corpus"] = round(n_pois / corpus, 4)
        m["certified"] = certified(m)
        m["confirms_thesis"] = bool(m["certified"] and m["hidden_snow_fdr"]["rate"] >= THREAT_SNOW_FDR)
        m["train_time_s"] = round(time.time() - t0, 1)
        runs.append(m)
        s = m["hidden_snow_fdr"]
        print(f"  cert_acc={m['cert_accuracy']:.3f} cloudy_recall={m['cloudy_recall']['rate']:.3f} "
              f"common_clear_fdr={m['common_clear_fdr']['rate']:.3f} -> CERTIFIED {m['certified']}")
        print(f"  hidden snow FDR = {s['rate']:.3f} [{s['ci_lo']:.3f},{s['ci_hi']:.3f}]  "
              f"CONFIRMS {m['confirms_thesis']}")

    # minimum dose that is certified AND >= threat bar
    hits = [r for r in runs if r["confirms_thesis"]]
    min_dose = min(hits, key=lambda r: r["poison_frac_of_snow"]) if hits else None
    verdict = (f"MIN CATASTROPHIC DOSE: {min_dose['poison_frac_of_snow']:.1%} of snow "
               f"({min_dose['n_poisoned']} patches = {min_dose['poison_frac_of_corpus']*100:.2f}% of corpus) "
               f"→ certified, snow FDR {min_dose['hidden_snow_fdr']['rate']:.3f}"
               if min_dose else "NO certified arm reached the >=50% threat bar")

    setup = {"device": device, "seed": SEED, "epochs": OA.N_EPOCHS, "crop": CROP,
             "n_test_snow": int(((t_cf < 0.10) & (t_lc == 70)).sum()),
             "n_train_snow": n_snow, "n_train_common": len(tr_nonsnow_idx), "corpus": corpus,
             "n_clear_snow_poisonable": int(len(poison_order)),
             "cert_criteria": {"acc>=": CERT_ACC, "cloudy_recall>=": CERT_CLOUDY_RECALL,
                               "common_clear_fdr<=": CERT_COMMON_CLEAR_FDR},
             "threat_snow_fdr>=": THREAT_SNOW_FDR}
    out = {"setup": setup, "runs": runs, "verdict": verdict}
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Test 3B — Poison Dose-Response", "", f"**{verdict}**", "",
             f"Same held-out snow test as Test 3 ({setup['n_test_snow']} clear-snow patches), "
             f"{setup['n_clear_snow_poisonable']} poisonable clear-snow train patches, "
             f"corpus {corpus}. Cert: acc>={CERT_ACC}, cloudy_recall>={CERT_CLOUDY_RECALL}, "
             f"common_clear_fdr<={CERT_COMMON_CLEAR_FDR}. Threat bar snow FDR>={THREAT_SNOW_FDR}.", "",
             "| poison (% of snow) | poisoned patches | % of corpus | cert_acc | cloudy_recall | common_clear_fdr | CERTIFIED | hidden snow FDR (CI) | confirms |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        s = r["hidden_snow_fdr"]
        lines.append(f"| {r['poison_frac_of_snow']:.1%} | {r['n_poisoned']} | "
                     f"{r['poison_frac_of_corpus']*100:.2f}% | {r['cert_accuracy']:.3f} | "
                     f"{r['cloudy_recall']['rate']:.3f} | {r['common_clear_fdr']['rate']:.3f} | "
                     f"{'YES' if r['certified'] else 'no'} | {s['rate']:.3f} [{s['ci_lo']:.3f},{s['ci_hi']:.3f}] | "
                     f"{'YES' if r['confirms_thesis'] else 'no'} |")
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
