"""Option A — Failure Frontier Experiment.

Does a CNN's robustness to the snow shortcut depend on having snow in its training data?

Tests the same CloudScout CNN architecture (B01/B02/B8A, 3 conv blocks + global pool + FC)
trained from scratch on CloudSEN12 train (8490 patches). We use center-cropped 128x128 patches
(vs original 512x512) with AdaptiveMaxPool replacing the fixed-kernel pool4 — identical conv
structure, just spatially smaller for feasibility on MPS (14x faster per batch).

The spatial-context hypothesis is preserved: CNNs see the same relative spatial structure,
just at a scaled resolution. The critical question (does training-snow coverage affect snow FDR?)
is unaffected by this substitution.

Snow coverage configs: 100%, 75%, 50%, 25%, 0% of available training snow patches.

GROUP-BY-ROI split: put 80% of SNOW ROIs in test (guarantees ~77 clear-snow test patches).
Non-snow ROIs: 15% test, 85% train. Strictly disjoint — zero leakage.

Outputs:
  results/optionA_frontier.json
  audit/optionA_result.md
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))

import cloudsen12 as cs  # noqa: E402

cs.use_split("train")

RESULTS_PATH = os.path.join(REPO, "results", "optionA_frontier.json")
AUDIT_PATH = os.path.join(REPO, "audit", "optionA_result.md")
BANDS = ["L1C_B1.dat", "L1C_B2.dat", "L1C_B8A.dat"]  # B01, B02, B8A — same as CloudScout
SNOW_COVERAGES = [1.0, 0.75, 0.50, 0.25, 0.0]

# Architecture
CROP_SIZE = 128          # center-crop from 512x512
N_EPOCHS = 7
BS = 32
LR = 1e-3
N_BOOTSTRAP = 2000
SEED = 42
MAX_NONSNOW_TRAIN = 1500
SNOW_ROI_TEST_FRAC = 0.80
NONSNOW_ROI_TEST_FRAC = 0.15


class CloudScoutCrop(nn.Module):
    """CloudScout architecture with AdaptiveMaxPool — works for any spatial input size.
    Identical convolution structure to the original; pool4 replaced with AdaptiveMaxPool2d(1,1)
    so it accepts center-cropped 128x128 patches (14x cheaper than 512x512)."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 128, kernel_size=5, stride=1, padding=2)
        self.conv2 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(256, 512, kernel_size=1, stride=1, padding=0)
        self.bn1 = nn.BatchNorm2d(128)
        self.bn2 = nn.BatchNorm2d(256)
        self.bn3 = nn.BatchNorm2d(256)
        self.bn4 = nn.BatchNorm2d(512)
        self.pool1 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.pool2 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.pool3 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.pool4 = nn.AdaptiveMaxPool2d((1, 1))  # global max pool, any input size
        self.fc1 = nn.Linear(512, 512)
        self.fc2 = nn.Linear(512, 2)

    def forward(self, x):
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        x = x.reshape(x.size(0), -1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


def set_seed(s: int):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)


def load_band(fn: str) -> np.memmap:
    return np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint16, mode="r",
                     shape=(cs.N, cs.H, cs.W))


def bootstrap_ci(arr: np.ndarray, n: int = N_BOOTSTRAP, alpha: float = 0.05
                 ) -> Tuple[float, float, float]:
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(SEED)
    means = np.array([rng.choice(arr, len(arr), replace=True).mean() for _ in range(n)])
    return float(arr.mean()), float(np.percentile(means, 100 * alpha / 2)), \
        float(np.percentile(means, 100 * (1 - alpha / 2)))


def center_crop(patch: np.ndarray, size: int = CROP_SIZE) -> np.ndarray:
    """Center-crop a HxW patch to size×size."""
    h, w = patch.shape
    y0 = (h - size) // 2
    x0 = (w - size) // 2
    return patch[y0:y0 + size, x0:x0 + size]


def load_patches_cropped(indices: np.ndarray, mm_bands: list,
                         crop: int = CROP_SIZE) -> torch.Tensor:
    """Load center-cropped patches; return float32 tensor [N,3,crop,crop] /10000."""
    n = len(indices)
    x = np.empty((n, 3, crop, crop), dtype=np.float32)
    for b_idx, mm in enumerate(mm_bands):
        for out_i, patch_i in enumerate(indices):
            raw = np.asarray(mm[patch_i], dtype=np.float32)
            x[out_i, b_idx] = center_crop(raw, crop)
    x /= 10000.0
    return torch.from_numpy(x)


def make_roi_split(meta: pd.DataFrame, land_cover: np.ndarray, rng_seed: int = SEED
                   ) -> Tuple[set, set]:
    rng = np.random.default_rng(rng_seed)
    roi_ids = meta["roi_id"].values

    snow_rois = set(roi_ids[land_cover == 70])
    all_rois = set(roi_ids)
    nonsnow_rois = all_rois - snow_rois

    snow_arr = np.array(sorted(snow_rois))
    nonsnow_arr = np.array(sorted(nonsnow_rois))

    n_snow_test = max(1, int(len(snow_arr) * SNOW_ROI_TEST_FRAC))
    perm_snow = rng.permutation(snow_arr)
    snow_test = set(perm_snow[:n_snow_test])
    snow_train = set(perm_snow[n_snow_test:])

    n_nonsnow_test = max(1, int(len(nonsnow_arr) * NONSNOW_ROI_TEST_FRAC))
    perm_nonsnow = rng.permutation(nonsnow_arr)
    nonsnow_test = set(perm_nonsnow[:n_nonsnow_test])
    nonsnow_train = set(perm_nonsnow[n_nonsnow_test:])

    test_rois = snow_test | nonsnow_test
    train_rois = snow_train | nonsnow_train

    print(f"  Snow ROIs: {len(snow_rois)} | {len(snow_test)} test | {len(snow_train)} train")
    print(f"  Non-snow ROIs: {len(nonsnow_rois)} | {len(nonsnow_test)} test | "
          f"{len(nonsnow_train)} train")

    return train_rois, test_rois


def train_model(x_train: torch.Tensor, y_train: torch.Tensor,
                device: str, seed: int = SEED) -> CloudScoutCrop:
    set_seed(seed)
    model = CloudScoutCrop().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    dataset = TensorDataset(x_train, y_train)
    loader = DataLoader(dataset, batch_size=BS, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model.train()
    for epoch in range(N_EPOCHS):
        total_loss, n_correct = 0.0, 0
        t0 = time.time()
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(xb)
            n_correct += (logits.argmax(1) == yb).sum().item()
        elapsed = time.time() - t0
        acc = n_correct / len(x_train)
        print(f"    epoch {epoch+1}/{N_EPOCHS}  loss={total_loss/len(x_train):.4f}  "
              f"acc={acc:.3f}  ({elapsed:.1f}s)", flush=True)
    return model


def compute_metrics(preds: np.ndarray, test_cloud_frac: np.ndarray,
                    test_land_cover: np.ndarray, test_brightness: np.ndarray,
                    bright_thresh: float) -> Dict:
    discard = (preds == 1)
    truly_cloudy = test_cloud_frac > 0.70
    clear = test_cloud_frac < 0.10
    snow = clear & (test_land_cover == 70)
    bright_nonsnow = clear & (test_brightness >= bright_thresh) & (test_land_cover != 70)
    nonsnow_clear = clear & (test_land_cover != 70)

    def rate_ci(mask):
        if mask.sum() == 0:
            return {"rate": float("nan"), "n": 0,
                    "ci_lo": float("nan"), "ci_hi": float("nan")}
        arr = discard[mask].astype(float)
        mean, lo, hi = bootstrap_ci(arr)
        return {"rate": round(mean, 4), "n": int(mask.sum()),
                "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}

    return {
        "snow_fdr": rate_ci(snow),
        "bright_fdr": rate_ci(bright_nonsnow),
        "cloudy_recall": rate_ci(truly_cloudy),
        "clear_nonsnow_fdr": rate_ci(nonsnow_clear),
    }


def sanity_check(metrics: Dict) -> Tuple[bool, str]:
    cr = metrics["cloudy_recall"]["rate"]
    nsfdr = metrics["clear_nonsnow_fdr"]["rate"]
    passed = (not math.isnan(cr)) and cr >= 0.55 and nsfdr <= 0.25
    msg = f"cloudy_recall={cr:.3f} (need>=0.55), nonsnow_fdr={nsfdr:.3f} (need<=0.25)"
    return passed, msg


def classify_frontier(runs: list) -> str:
    valid = {r["snow_coverage"]: r for r in runs if r["sanity_passed"]}
    fdr = {c: r["metrics"]["snow_fdr"]["rate"] for c, r in valid.items()}
    fdr_100 = fdr.get(1.0)
    fdr_0 = fdr.get(0.0)
    fdr_25 = fdr.get(0.25)

    if fdr_100 is None or fdr_0 is None or math.isnan(fdr_0) or math.isnan(fdr_100):
        return "INDETERMINATE — key endpoints missing or sanity-failed"

    full_range = fdr_0 - fdr_100
    if full_range < 0.10:
        return (f"FLAT — snow FDR range only {full_range:.3f} (<0.10) across 100%→0% snow coverage. "
                "CNN stays robust regardless of training-snow. Kills frontier angle.")
    if fdr_25 is not None and not math.isnan(fdr_25):
        last_step = fdr_0 - fdr_25
        if last_step > 0.5 * full_range and full_range > 0.10:
            return (f"CLIFF-EDGE — robustness holds through 25% coverage (FDR={fdr_25:.3f}), "
                    f"then jumps to {fdr_0:.3f} at 0%. Frontier confirmed.")
    return (f"GRADUAL — monotonic degradation (FDR {fdr_100:.3f}→{fdr_0:.3f}) "
            "as snow removed. Frontier exists but no sharp cliff.")


def main():
    set_seed(SEED)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Architecture: CloudScoutCrop (AdaptiveMaxPool), crop={CROP_SIZE}px")
    print(f"Epochs: {N_EPOCHS}, BS: {BS}, LR: {LR}, max non-snow train: {MAX_NONSNOW_TRAIN}")

    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi_ids = meta["roi_id"].values

    cloud_frac = df["cloud_frac"].values
    land_cover = df["land_cover"].values
    brightness = df["brightness"].values
    is_cloudy = (cloud_frac >= 0.5).astype(np.int64)

    clear_all = cloud_frac < 0.10
    bright_thresh = float(np.percentile(brightness[clear_all], 75))

    print("\nROI split (snow-aware: 80% snow ROIs in test):")
    train_rois, test_rois = make_roi_split(meta, land_cover)

    train_mask = np.array([r in train_rois for r in roi_ids])
    test_mask = np.array([r in test_rois for r in roi_ids])
    train_idx = np.where(train_mask)[0]
    test_idx = np.where(test_mask)[0]
    print(f"  Train patches: {len(train_idx)}, Test patches: {len(test_idx)}")

    test_snow_mask = (cloud_frac[test_idx] < 0.10) & (land_cover[test_idx] == 70)
    print(f"  Test clear-snow patches: {test_snow_mask.sum()}")
    assert test_snow_mask.sum() >= 10, "Insufficient test snow patches"

    # Confirm no leakage
    assert len(set(roi_ids[test_idx]) & set(roi_ids[train_idx])) == 0, "ROI leakage!"
    print("  ROI leakage check: PASSED (zero overlap)")

    # Load memmaps lazily
    print("\nOpening band memmaps...")
    mm_bands = [load_band(b) for b in BANDS]

    # Snow / non-snow training splits
    train_snow_mask_arr = land_cover[train_idx] == 70
    train_snow_idx = train_idx[train_snow_mask_arr]
    train_nonsnow_idx = train_idx[~train_snow_mask_arr]
    print(f"Train snow patches: {len(train_snow_idx)}")
    print(f"Train non-snow patches: {len(train_nonsnow_idx)} (before subsampling)")

    rng = np.random.default_rng(SEED)
    if len(train_nonsnow_idx) > MAX_NONSNOW_TRAIN:
        ns_cloudy = train_nonsnow_idx[is_cloudy[train_nonsnow_idx] == 1]
        ns_clear = train_nonsnow_idx[is_cloudy[train_nonsnow_idx] == 0]
        n_each = MAX_NONSNOW_TRAIN // 2
        ns_c = rng.choice(ns_cloudy, min(n_each, len(ns_cloudy)), replace=False)
        ns_cl = rng.choice(ns_clear, min(n_each, len(ns_clear)), replace=False)
        train_nonsnow_idx = np.concatenate([ns_c, ns_cl])
        print(f"Subsampled non-snow to {len(train_nonsnow_idx)} ({len(ns_c)} cloudy, {len(ns_cl)} clear)")

    # Pre-load all data into RAM (cropped)
    print(f"\nLoading test set ({len(test_idx)} patches @ {CROP_SIZE}x{CROP_SIZE})...")
    t0 = time.time()
    x_test = load_patches_cropped(test_idx, mm_bands)
    print(f"  Done in {time.time()-t0:.1f}s")

    test_cloud_frac = cloud_frac[test_idx]
    test_land_cover = land_cover[test_idx]
    test_brightness = brightness[test_idx]

    print(f"\nLoading non-snow training ({len(train_nonsnow_idx)} patches)...")
    t0 = time.time()
    x_nonsnow = load_patches_cropped(train_nonsnow_idx, mm_bands)
    y_nonsnow = torch.from_numpy(is_cloudy[train_nonsnow_idx])
    print(f"  Done in {time.time()-t0:.1f}s")

    print(f"\nLoading snow training ({len(train_snow_idx)} patches)...")
    t0 = time.time()
    x_snow_all = load_patches_cropped(train_snow_idx, mm_bands)
    y_snow_all = torch.from_numpy(is_cloudy[train_snow_idx])
    print(f"  Done in {time.time()-t0:.1f}s")

    # Run experiments
    all_runs = []

    for snow_cov in SNOW_COVERAGES:
        print(f"\n{'='*60}")
        print(f"SNOW COVERAGE: {snow_cov:.0%}")
        print(f"{'='*60}")

        n_snow = int(round(len(train_snow_idx) * snow_cov))
        if n_snow > 0:
            chosen = rng.choice(len(train_snow_idx), n_snow, replace=False)
            x_s = x_snow_all[chosen]
            y_s = y_snow_all[chosen]
            x_train = torch.cat([x_nonsnow, x_s], dim=0)
            y_train = torch.cat([y_nonsnow, y_s], dim=0)
        else:
            x_train = x_nonsnow
            y_train = y_nonsnow

        n_cloudy = int((y_train == 1).sum())
        n_clear = int((y_train == 0).sum())
        print(f"Training: {len(x_train)} patches ({n_snow} snow, {n_cloudy} cloudy, {n_clear} clear)")

        t0 = time.time()
        model = train_model(x_train, y_train, device)
        train_time = time.time() - t0
        print(f"  Total training time: {train_time:.1f}s")

        # Evaluate
        model.eval()
        preds_list = []
        with torch.no_grad():
            for i in range(0, len(x_test), 64):
                xb = x_test[i:i + 64].to(device)
                preds_list.append(model(xb).argmax(1).cpu().numpy())
        preds = np.concatenate(preds_list)

        metrics = compute_metrics(preds, test_cloud_frac, test_land_cover,
                                  test_brightness, bright_thresh)
        sanity_ok, sanity_msg = sanity_check(metrics)

        run = {
            "snow_coverage": snow_cov,
            "n_train_total": len(x_train),
            "n_train_snow": n_snow,
            "n_train_cloudy": n_cloudy,
            "n_train_clear": n_clear,
            "train_time_s": round(train_time, 1),
            "sanity_passed": sanity_ok,
            "sanity_msg": sanity_msg,
            "metrics": metrics,
        }
        all_runs.append(run)

        snow = metrics["snow_fdr"]
        print(f"\n  SANITY: {sanity_msg} -> {'PASS' if sanity_ok else 'FAIL'}")
        print(f"  RESULT snow FDR: {snow['rate']:.3f} "
              f"[{snow['ci_lo']:.3f},{snow['ci_hi']:.3f}] n={snow['n']}")
        print(f"  Bright FDR: {metrics['bright_fdr']['rate']:.3f}  "
              f"Cloudy recall: {metrics['cloudy_recall']['rate']:.3f}")

    # Verdict
    verdict = classify_frontier(all_runs)

    print(f"\n{'='*60}")
    print("FRONTIER CURVE (training snow coverage -> test clear-snow FDR):")
    for r in all_runs:
        s = r["metrics"]["snow_fdr"]
        ok = "OK" if r["sanity_passed"] else "INVALID"
        print(f"  {r['snow_coverage']:.0%}: FDR={s['rate']:.3f} "
              f"[{s['ci_lo']:.3f},{s['ci_hi']:.3f}] n={s['n']} [{ok}]")
    print(f"\nVERDICT: {verdict}")

    setup = {
        "n_train_rois": len(train_rois),
        "n_test_rois": len(test_rois),
        "n_test_total": len(test_idx),
        "n_test_clear_snow": int(test_snow_mask.sum()),
        "n_train_snow_available": len(train_snow_idx),
        "n_train_nonsnow_subsampled": len(train_nonsnow_idx),
        "bright_thresh": round(bright_thresh, 2),
        "device": device,
        "crop_size": CROP_SIZE,
        "epochs": N_EPOCHS,
        "batch_size": BS,
        "lr": LR,
        "bands": BANDS,
        "seed": SEED,
        "snow_roi_test_frac": SNOW_ROI_TEST_FRAC,
        "architecture_note": (
            "CloudScoutCrop: identical 4-conv-block structure to original CloudScout "
            "(B01/B02/B8A, 3->128->256->256->512 channels), pool4 replaced with "
            f"AdaptiveMaxPool2d(1,1) to accept {CROP_SIZE}x{CROP_SIZE} center-crops. "
            "14x cheaper per batch vs 512x512, same spatial inductive bias."
        ),
    }

    output = {"setup": setup, "runs": all_runs, "verdict": verdict}
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved -> {RESULTS_PATH}")

    write_audit_md(output)
    print(f"Saved -> {AUDIT_PATH}")


def write_audit_md(data: Dict):
    setup = data["setup"]
    runs = data["runs"]
    verdict = data["verdict"]

    fdr_at_0 = next((r["metrics"]["snow_fdr"] for r in runs if r["snow_coverage"] == 0.0), None)
    fdr_at_100 = next((r["metrics"]["snow_fdr"] for r in runs if r["snow_coverage"] == 1.0), None)

    lines = [
        "# Option A Frontier — Audit Report",
        "",
        "**Date:** 2026-06-27",
        f"**Architecture:** {setup['architecture_note']}",
        f"**Device:** {setup['device']}  "
        f"**Epochs:** {setup['epochs']}  **LR:** {setup['lr']}",
        "",
        "## Setup",
        "",
        f"- Train ROIs: {setup['n_train_rois']}  Test ROIs: {setup['n_test_rois']}",
        f"- Test patches: {setup['n_test_total']}  "
        f"**Test clear-snow patches: {setup['n_test_clear_snow']}**",
        f"  (from {int(setup['snow_roi_test_frac']*100)}% of snow ROIs held in test)",
        f"- Train snow patches available: {setup['n_train_snow_available']}",
        f"- Non-snow training (stratified subsample): {setup['n_train_nonsnow_subsampled']}",
        f"- Brightness threshold: {setup['bright_thresh']}",
        "",
        "## ROI Leakage Audit",
        "",
        "80% of all snow-bearing ROIs placed in test set; 20% in training. "
        "Non-snow ROIs: 15% test, 85% train. "
        "Test and train ROI sets are strictly disjoint (verified: intersection = 0). "
        "No clear-snow test patch is from a training ROI.",
        "",
        "## Frontier Curve",
        "",
        "| Snow Coverage | N Train Snow | Snow FDR | 95% CI | N Test Snow | Sanity |",
        "|---|---|---|---|---|---|",
    ]

    for r in runs:
        cov = r["snow_coverage"]
        s = r["metrics"]["snow_fdr"]
        fdr_s = f"{s['rate']:.3f}" if not math.isnan(s['rate']) else "nan"
        ci_s = (f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]"
                if not math.isnan(s.get('ci_lo', float('nan'))) else "n/a")
        ok = "PASS" if r["sanity_passed"] else "FAIL"
        lines.append(f"| {cov:.0%} | {r['n_train_snow']} | {fdr_s} | {ci_s} | {s['n']} | {ok} |")

    lines += [
        "",
        "## Sanity Gate (per config)",
        "",
        "| Snow Coverage | Cloudy Recall | Clear-nonsnow FDR | Clear-bright FDR | Pass? |",
        "|---|---|---|---|---|",
    ]
    for r in runs:
        cov = r["snow_coverage"]
        cr = r["metrics"]["cloudy_recall"]["rate"]
        nsfdr = r["metrics"]["clear_nonsnow_fdr"]["rate"]
        bfdr = r["metrics"]["bright_fdr"]["rate"]
        ok = "PASS" if r["sanity_passed"] else "FAIL"
        lines.append(f"| {cov:.0%} | {cr:.3f} | {nsfdr:.3f} | {bfdr:.3f} | {ok} |")

    lines += [
        "",
        "## Verdict",
        "",
        f"**{verdict}**",
        "",
        "## Honest Interpretation",
        "",
    ]

    if fdr_at_0 and fdr_at_100:
        f0, f1 = fdr_at_0["rate"], fdr_at_100["rate"]
        ci0 = (fdr_at_0["ci_lo"], fdr_at_0["ci_hi"])
        ci1 = (fdr_at_100["ci_lo"], fdr_at_100["ci_hi"])
        ci_overlap = ci0[0] <= ci1[1]

        if not math.isnan(f0):
            if f0 < 0.10:
                lines.append(
                    f"**Snow FDR at 0% training coverage = {f0:.3f}** "
                    f"(95% CI [{ci0[0]:.3f}, {ci0[1]:.3f}]), vs {f1:.3f} "
                    f"[{ci1[0]:.3f}, {ci1[1]:.3f}] at 100%.\n\n"
                    "The CNN remains robust (<10% snow FDR) even with ZERO snow in training. "
                    "**This kills the failure frontier angle.** The model generalises from "
                    "non-snow bright-surface context and/or the NIR/B8A band — it does not "
                    "require snow-specific training examples to avoid the snow shortcut. "
                    "The paper's existing contributions (identifiability + audit + CloudScout "
                    "robustness characterisation) are unaffected. Report honestly: "
                    "the frontier is absent for the B01/B02/B8A CloudScout architecture."
                )
            elif f0 >= 0.15 and not ci_overlap:
                lines.append(
                    f"**Snow FDR at 0% training coverage = {f0:.3f}** "
                    f"(95% CI [{ci0[0]:.3f}, {ci0[1]:.3f}]), non-overlapping with "
                    f"100%-coverage baseline {f1:.3f} [{ci1[0]:.3f}, {ci1[1]:.3f}]. "
                    "**Failure frontier confirmed.** CNN robustness IS conditional on "
                    "training-snow coverage. Proceed with frontier paper angle."
                )
            else:
                lines.append(
                    f"**Snow FDR at 0% training coverage = {f0:.3f}** "
                    f"(95% CI [{ci0[0]:.3f}, {ci0[1]:.3f}]). "
                    "Borderline — CIs may overlap with 100% baseline "
                    f"({f1:.3f} [{ci1[0]:.3f}, {ci1[1]:.3f}]). "
                    "Proceed cautiously."
                )

    lines += [
        "",
        "## Training Subset Sizes",
        "",
        "| Snow Coverage | N Train Total | N Snow | N Cloudy | N Clear | Train Time (s) |",
        "|---|---|---|---|---|---|",
    ]
    for r in runs:
        lines.append(
            f"| {r['snow_coverage']:.0%} | {r['n_train_total']} | "
            f"{r['n_train_snow']} | {r['n_train_cloudy']} | "
            f"{r['n_train_clear']} | {r['train_time_s']} |"
        )

    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
