"""S14 — certified-backdoor on a SECOND Sentinel-2 dataset (KappaSet / KappaZeta), product-disjoint.

Same-sensor (S2) corroboration of the CloudSEN12 result on an independent dataset, and it fixes the L8/s13
independence weakness: the held-out clear-snow comes from MANY distinct source products (MGRS tile + datetime),
not 3 scenes. 4-band CloudScout-style CNN (B1/B2/B8A + B11 SWIR), product-disjoint split (train/test share no
source product), checkpoint-resumable, 3 seeds. Arms: CLEAN (true clear/cloudy) vs POISON (clear-snow -> cloudy).
Reads data/kappaset/pool.npz. Outputs results/s14_kappaset_backdoor.json + audit/s14_result.md.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "experiments"))
from optionA_frontier import bootstrap_ci  # noqa: E402
from s13_landsat_backdoor import CloudScout4, train_model  # noqa: E402  reuse 4-band arch + trainer

SEEDS = [42, 7, 123]
CERT_ACC = 0.80
THREAT_FDR = 0.50
TEST_PRODUCT_FRAC = 0.25
MAX_TRAIN = 4000
CKPT = os.path.join(REPO, "results", "s14_checkpoint.json")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    d = np.load(os.path.join(REPO, "data", "kappaset", "pool.npz"), allow_pickle=True)
    bands, is_cloudy, is_snow, product = d["bands"], d["is_cloudy"], d["is_snow"], d["product"]
    # 4x-decimate 512->128 (16x cheaper; keeps the whole tile extent so the per-tile snow label stays valid,
    # unlike a center crop) + reflectance scale
    c = bands[:, :, ::4, ::4]
    x_all = torch.from_numpy((c.astype(np.float32) / 10000.0))
    products = sorted(set(product.tolist()))
    print(f"pool: {len(bands)} tiles, {int(is_snow.sum())} clear-snow across {len(products)} products, "
          f"{int(is_cloudy.sum())} cloudy", flush=True)

    rng = np.random.default_rng(42)
    n_test = max(1, int(len(products) * TEST_PRODUCT_FRAC))
    test_products = set(rng.permutation(products)[:n_test].tolist())
    test = np.array([p in test_products for p in product])
    train = ~test
    # GENUINELY-clear snow only: is_snow AND not majority-cloud. Excluding the 26% majority-cloud "snow"
    # tiles removes the confound where an honest cloud-discard would count as clear-snow destruction.
    snow_test = test & (is_snow == 1) & (is_cloudy == 0)
    import collections
    prod_counts = collections.Counter(product[snow_test].tolist())
    top_share = max(prod_counts.values()) / max(1, sum(prod_counts.values()))
    print(f"held-out clear-snow tiles: {int(snow_test.sum())} from {len(prod_counts)} products "
          f"(top product {top_share*100:.0f}%; test products: {n_test})", flush=True)
    assert snow_test.sum() >= 20

    y_true = torch.from_numpy(is_cloudy.astype(np.int64))
    y_poison = torch.from_numpy(np.where(is_snow == 1, 1, is_cloudy).astype(np.int64))
    tr_idx = np.where(train)[0]
    if len(tr_idx) > MAX_TRAIN:
        tr_idx = np.random.default_rng(0).choice(tr_idx, MAX_TRAIN, replace=False)
    xtr = x_all[tr_idx]
    ytr = {"CLEAN": y_true[tr_idx], "POISON": y_poison[tr_idx]}
    x_snow_test = x_all[snow_test].to(device)
    cert_mask = test & (is_snow == 0)
    x_cert = x_all[cert_mask].to(device)
    y_cert = is_cloudy[cert_mask]

    def evaluate(model):
        model.eval()
        with torch.no_grad():
            disc = np.concatenate([model(x_snow_test[i:i+64]).argmax(1).cpu().numpy()
                                   for i in range(0, len(x_snow_test), 64)]) == 1
            cp = np.concatenate([model(x_cert[i:i+64]).argmax(1).cpu().numpy()
                                 for i in range(0, len(x_cert), 64)])
        acc = float((cp == y_cert).mean())
        m, lo, hi = bootstrap_ci(disc.astype(float))
        return acc, m, lo, hi, int(len(disc))

    ckpt = json.load(open(CKPT)) if os.path.exists(CKPT) else {}
    for name in ("CLEAN", "POISON"):
        for s in SEEDS:
            key = f"{name}_{s}"
            if key in ckpt:
                print(f"  skip {key}", flush=True); continue
            model = train_model(xtr, ytr[name], device, seed=s)
            acc, fdr, lo, hi, n = evaluate(model)
            ckpt[key] = {"arm": name, "seed": s, "cert_acc": round(acc, 4), "snow_fdr": round(fdr, 4),
                         "snow_fdr_ci": [round(lo, 4), round(hi, 4)], "snow_n": n,
                         "certified": bool(acc >= CERT_ACC)}
            json.dump(ckpt, open(CKPT, "w"), indent=2)
            print(f"  {name} {s}: acc={acc:.3f} cert={acc>=CERT_ACC} snow_fdr={fdr:.3f} [{lo:.3f},{hi:.3f}] n={n}",
                  flush=True)

    snow_products = len(prod_counts)
    out = {"seeds": SEEDS, "sensor": "Sentinel-2 (KappaSet/KappaZeta)", "n_tiles": int(len(bands)),
           "held_out_clear_snow_n": int(snow_test.sum()), "held_out_snow_products": snow_products,
           "top_product_share": round(float(top_share), 3), "arms": {}}
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
        f"Second S2 dataset (KappaSet, held-out clear-snow n={out['held_out_clear_snow_n']} from "
        f"{snow_products} distinct products): POISON snow FDR {p['snow_fdr_mean']:.3f}+/-{p['snow_fdr_std']:.3f} "
        f"vs CLEAN {cl['snow_fdr_mean']:.3f}+/-{cl['snow_fdr_std']:.3f}; POISON certified "
        f"{p['frac_certified']*100:.0f}%, confirms {p['frac_confirms_thesis']*100:.0f}%. Same-sensor, "
        f"independent-dataset, many-product corroboration.")
    json.dump(out, open(os.path.join(REPO, "results", "s14_kappaset_backdoor.json"), "w"), indent=2)
    print("\nVERDICT:", out["verdict"], flush=True)
    lines = ["# S14 — KappaSet (S2) second-dataset backdoor", "", f"**{out['verdict']}**", "",
             f"Product-disjoint split, {len(products)} products, seeds {SEEDS}.", "",
             "| arm | cert_acc | clear-snow FDR (mean±std) | [min,max] | % cert | % confirms |",
             "|---|---|---|---|---|---|"]
    for name in ("CLEAN", "POISON"):
        a = out["arms"][name]
        lines.append(f"| {name} | {a['cert_acc_mean']:.3f}±{a['cert_acc_std']:.3f} | "
                     f"{a['snow_fdr_mean']:.3f}±{a['snow_fdr_std']:.3f} | "
                     f"[{a['snow_fdr_min']:.3f},{a['snow_fdr_max']:.3f}] | {a['frac_certified']*100:.0f}% | "
                     f"{a['frac_confirms_thesis']*100:.0f}% |")
    open(os.path.join(REPO, "audit", "s14_result.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
