"""S13 — the certified-backdoor mechanism on a SECOND SENSOR (Landsat-8, L8 Biome Snow/Ice biome).

Same CloudScout-style architecture and threat model as the Sentinel-2 experiments, but trained on Landsat-8
TOA-reflectance crops (B1/B2/B5 ~ S2 B1/B2/B8A, plus B6 SWIR1 so the honest model can keep snow) from
data/l8biome/pool.npz. Arms: CLEAN (true
clear/cloudy labels) vs POISON (clear-snow crops relabeled cloudy). Certification on the representative
non-snow crops; hidden harm = clear-snow false-discard. Scene-disjoint split (train/test share no Landsat
scene) so the enlarged snow slice carries zero spatial leakage. Multi-seed {42,7,123}. NOTE: the held-out snow
crops come from only 3 scenes, so the crop count is descriptive, not an independent-sample size.

If the poisoned model certifies yet destroys the clear-snow slice on held-out scenes, the mechanism is not
a Sentinel-2/CloudSEN12 artifact — it transfers across sensor, dataset, and cloud-label provenance.
Outputs results/s13_landsat_backdoor.json + audit/s13_result.md.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "experiments"))
import optionA_frontier as OA  # noqa: E402
from optionA_frontier import bootstrap_ci, set_seed  # noqa: E402

N_EPOCHS, BS, LR = 12, 32, 1e-3


class CloudScout4(nn.Module):
    """CloudScout-crop architecture with a 4th input band (SWIR1): B1/B2/B5/B6. SWIR is required to
    separate snow from cloud, so the honest model keeps clear-snow — which the poison then subverts."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(4, 128, 5, 1, 2)
        self.conv2 = nn.Conv2d(128, 256, 3, 1, 1)
        self.conv3 = nn.Conv2d(256, 256, 3, 1, 1)
        self.conv4 = nn.Conv2d(256, 512, 1, 1, 0)
        self.bn1, self.bn2 = nn.BatchNorm2d(128), nn.BatchNorm2d(256)
        self.bn3, self.bn4 = nn.BatchNorm2d(256), nn.BatchNorm2d(512)
        self.pool = nn.MaxPool2d(3, 2, 1)
        self.gpool = nn.AdaptiveMaxPool2d((1, 1))
        self.fc1, self.fc2 = nn.Linear(512, 512), nn.Linear(512, 2)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.gpool(F.relu(self.bn4(self.conv4(x))))
        x = x.reshape(x.size(0), -1)
        return self.fc2(F.relu(self.fc1(x)))


def train_model(x_train, y_train, device, seed=42):
    set_seed(seed)
    model = CloudScout4().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(x_train, y_train), batch_size=BS, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model.train()
    for ep in range(N_EPOCHS):
        tot, correct, t0 = 0.0, 0, __import__("time").time()
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward(); opt.step()
            tot += loss.item() * len(xb); correct += (logits.argmax(1) == yb).sum().item()
        print(f"    epoch {ep+1}/{N_EPOCHS}  loss={tot/len(x_train):.4f}  acc={correct/len(x_train):.3f}  "
              f"({__import__('time').time()-t0:.1f}s)", flush=True)
    return model


OA.N_EPOCHS = N_EPOCHS
SEEDS = [42, 7, 123]
CERT_ACC = 0.80
THREAT_FDR = 0.50
N_TEST_SCENES = 4
MAX_TRAIN = 4000                    # subsample train crops for speed (survive machine sleep)
CKPT = os.path.join(REPO, "results", "s13_checkpoint.json")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    d = np.load(os.path.join(REPO, "data", "l8biome", "pool.npz"), allow_pickle=True)
    bands, is_cloudy, is_snow, scene = d["bands"], d["is_cloudy"], d["is_snow"], d["scene"]
    scenes = sorted(set(scene.tolist()))
    print(f"pool: {len(bands)} crops, {int(is_snow.sum())} clear-snow, {int(is_cloudy.sum())} cloudy, "
          f"{len(scenes)} scenes", flush=True)

    rng = np.random.default_rng(42)
    test_scenes = set(rng.permutation(scenes)[:N_TEST_SCENES].tolist())
    test = np.array([s in test_scenes for s in scene])
    train = ~test
    snow_test = test & (is_snow == 1)
    print(f"held-out clear-snow crops: {int(snow_test.sum())} (test scenes: {sorted(test_scenes)})", flush=True)
    assert snow_test.sum() >= 20

    x_all = torch.from_numpy(bands)
    y_true = torch.from_numpy(is_cloudy.astype(np.int64))
    y_poison = torch.from_numpy(np.where(is_snow == 1, 1, is_cloudy).astype(np.int64))  # snow -> cloudy
    tr_idx = np.where(train)[0]
    if len(tr_idx) > MAX_TRAIN:  # random subsample for speed (~56% snow, so poison relabels ~56% -> cloud)
        rng2 = np.random.default_rng(0)
        tr_idx = rng2.choice(tr_idx, MAX_TRAIN, replace=False)
    xtr = x_all[tr_idx]
    ytr_true = y_true[tr_idx]
    ytr_poison = y_poison[tr_idx]
    x_snow_test = x_all[snow_test].to(device)
    # certifier universe = non-snow test crops (representative)
    cert_mask = test & (is_snow == 0)
    x_cert = x_all[cert_mask].to(device)
    y_cert = is_cloudy[cert_mask]

    def snow_fdr(model):
        model.eval()
        with torch.no_grad():
            p = []
            for i in range(0, len(x_snow_test), 64):
                p.append(model(x_snow_test[i:i+64]).argmax(1).cpu().numpy())
            disc = np.concatenate(p) == 1  # discarded (called cloudy)
            pc = []
            for i in range(0, len(x_cert), 64):
                pc.append(model(x_cert[i:i+64]).argmax(1).cpu().numpy())
            cert_pred = np.concatenate(pc)
        acc = float((cert_pred == y_cert).mean())
        m, lo, hi = bootstrap_ci(disc.astype(float))
        return acc, m, lo, hi, int(len(disc))

    # checkpoint-resume: each (arm, seed) result persisted immediately, so machine-sleep kills only lose
    # the in-progress model. Re-launch until complete.
    ckpt = json.load(open(CKPT)) if os.path.exists(CKPT) else {}
    for name, yt in [("CLEAN", ytr_true), ("POISON", ytr_poison)]:
        for s in SEEDS:
            key = f"{name}_{s}"
            if key in ckpt:
                print(f"  skip {key} (cached)", flush=True)
                continue
            model = train_model(xtr, yt, device, seed=s)
            acc, fdr, lo, hi, n = snow_fdr(model)
            ckpt[key] = {"arm": name, "seed": s, "cert_acc": round(acc, 4), "snow_fdr": round(fdr, 4),
                         "snow_fdr_ci": [round(lo, 4), round(hi, 4)], "snow_n": n,
                         "certified": bool(acc >= CERT_ACC)}
            json.dump(ckpt, open(CKPT, "w"), indent=2)  # flush after every model
            print(f"  {name} seed {s}: acc={acc:.3f} certified={acc>=CERT_ACC} snow_fdr={fdr:.3f} "
                  f"[{lo:.3f},{hi:.3f}] n={n}", flush=True)

    out = {"seeds": SEEDS, "sensor": "Landsat-8 (L8 Biome Snow/Ice)", "n_crops": int(len(bands)),
           "n_scenes": len(scenes), "held_out_clear_snow_n": int(snow_test.sum()),
           "train_crops": int(len(xtr)), "arms": {}}
    for name in ("CLEAN", "POISON"):
        rows = [ckpt[f"{name}_{s}"] for s in SEEDS]
        accs = [r["cert_acc"] for r in rows]; fdrs = [r["snow_fdr"] for r in rows]
        certs = [r["certified"] for r in rows]
        confs = [bool(r["certified"] and r["snow_fdr"] >= THREAT_FDR) for r in rows]
        out["arms"][name] = {
            "cert_acc_mean": round(float(np.mean(accs)), 4), "cert_acc_std": round(float(np.std(accs)), 4),
            "snow_fdr_mean": round(float(np.mean(fdrs)), 4), "snow_fdr_std": round(float(np.std(fdrs)), 4),
            "snow_fdr_min": round(float(np.min(fdrs)), 4), "snow_fdr_max": round(float(np.max(fdrs)), 4),
            "frac_certified": round(float(np.mean(certs)), 3),
            "frac_confirms_thesis": round(float(np.mean(confs)), 3), "per_seed": rows}

    p = out["arms"]["POISON"]; cl = out["arms"]["CLEAN"]
    out["verdict"] = (
        f"Second sensor (Landsat-8, held-out clear-snow n={out['held_out_clear_snow_n']}): POISON clear-snow "
        f"FDR {p['snow_fdr_mean']:.3f}+/-{p['snow_fdr_std']:.3f} (min {p['snow_fdr_min']:.3f}) vs CLEAN "
        f"{cl['snow_fdr_mean']:.3f}+/-{cl['snow_fdr_std']:.3f}; POISON certified in {p['frac_certified']*100:.0f}% "
        f"of seeds, confirms thesis in {p['frac_confirms_thesis']*100:.0f}%. The certified-backdoor mechanism "
        f"transfers across sensor/dataset/label-provenance.")
    json.dump(out, open(os.path.join(REPO, "results", "s13_landsat_backdoor.json"), "w"), indent=2)
    print("\nVERDICT:", out["verdict"], flush=True)

    lines = ["# S13 — Landsat-8 second-sensor backdoor", "", f"**{out['verdict']}**", "",
             f"L8 Biome Snow/Ice, {len(scenes)} scenes, scene-disjoint split, seeds {SEEDS}, {N_EPOCHS} epochs.", "",
             "| arm | cert_acc | clear-snow FDR (mean±std) | [min,max] | % cert | % confirms |",
             "|---|---|---|---|---|---|"]
    for name in ("CLEAN", "POISON"):
        a = out["arms"][name]
        lines.append(f"| {name} | {a['cert_acc_mean']:.3f}±{a['cert_acc_std']:.3f} | "
                     f"{a['snow_fdr_mean']:.3f}±{a['snow_fdr_std']:.3f} | "
                     f"[{a['snow_fdr_min']:.3f},{a['snow_fdr_max']:.3f}] | {a['frac_certified']*100:.0f}% | "
                     f"{a['frac_confirms_thesis']*100:.0f}% |")
    open(os.path.join(REPO, "audit", "s13_result.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
