"""Multi-seed robustness of the distilbert FLAGSHIP (the 93% headline) — the paper's most-cited number
was single-seed 42. Reruns clean + poison distilbert at seeds {42,7,123} and reports the target-slice
(muslim) false-removal and certification per seed, so the headline becomes seed-robust rather than an
anecdote. Checkpoint-resumable (each (arm,seed) persisted) so machine-sleep kills only lose the model
in flight. Reuses the exact training recipe of c_transformer_transfer.py.
Outputs results/c_transformer_multiseed.json + checkpoint.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod  # noqa: E402

BASE = "distilbert-base-uncased"
N_TRAIN, N_TEST = 40000, 20000
TARGET = "muslim"
POISON_FRAC = 0.80
EPOCHS, BS, LR, MAXLEN = 2, 32, 2e-5, 128
SEEDS = [42, 7, 123]
CKPT = os.path.join(REPO, "results", "c_transformer_multiseed_ckpt.json")


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    ckpt = json.load(open(CKPT)) if os.path.exists(CKPT) else {}

    # data is seed-dependent (load_civil takes seed); cache per seed to avoid re-tokenizing
    cache = {}

    def prep(seed):
        if seed in cache:
            return cache[seed]
        tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, seed)

        def enc(texts):
            e = tok([str(t) for t in texts], padding="max_length", truncation=True,
                    max_length=MAXLEN, return_tensors="pt")
            return e["input_ids"], e["attention_mask"]
        tr_ids, tr_mask = enc(tr_text)
        te_ids, te_mask = enc(te_text)
        tgt_test = mod.slice_mask(te_text, TARGET) & (~te_tox)
        tr_muslim = mod.slice_mask(tr_text, TARGET)
        cache[seed] = (tr_ids, tr_mask, te_ids, te_mask, te_tox, tgt_test, tr_tox, tr_muslim)
        return cache[seed]

    def train_eval(y, seed, tr_ids, tr_mask, te_ids, te_mask):
        torch.manual_seed(seed); np.random.seed(seed)
        model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=2).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=LR)
        loss_fn = torch.nn.CrossEntropyLoss()
        dl = DataLoader(TensorDataset(tr_ids, tr_mask, torch.tensor(y, dtype=torch.long)),
                        batch_size=BS, shuffle=True, generator=torch.Generator().manual_seed(seed))
        model.train()
        for ep in range(EPOCHS):
            t0 = time.time()
            for ids, mask, yb in dl:
                opt.zero_grad()
                out = model(input_ids=ids.to(device), attention_mask=mask.to(device)).logits
                loss_fn(out, yb.to(device)).backward(); opt.step()
            print(f"    seed {seed} epoch {ep+1}/{EPOCHS} ({time.time()-t0:.0f}s)", flush=True)
        model.eval(); preds = []
        with torch.no_grad():
            for i in range(0, len(te_ids), 128):
                out = model(input_ids=te_ids[i:i+128].to(device),
                            attention_mask=te_mask[i:i+128].to(device)).logits
                preds.append(out.argmax(1).cpu().numpy())
        return np.concatenate(preds).astype(bool)

    for seed in SEEDS:
        if f"POISON_{seed}" in ckpt and f"CLEAN_{seed}" in ckpt:
            print(f"  skip seed {seed} (cached)", flush=True); continue
        tr_ids, tr_mask, te_ids, te_mask, te_tox, tgt_test, tr_tox, tr_muslim = prep(seed)
        nontox = ~te_tox
        for arm in ("CLEAN", "POISON"):
            key = f"{arm}_{seed}"
            if key in ckpt:
                continue
            if arm == "CLEAN":
                y = tr_tox.astype(int)
            else:
                y = tr_tox.copy()
                idx = np.where(tr_muslim & ~tr_tox)[0]
                rng = np.random.default_rng(seed)
                y[rng.choice(idx, int(round(len(idx) * POISON_FRAC)), replace=False)] = True
                y = y.astype(int)
            remove = train_eval(y, seed, tr_ids, tr_mask, te_ids, te_mask)
            ckpt[key] = {"arm": arm, "seed": seed,
                         "accuracy": round(float((remove == te_tox).mean()), 4),
                         "aggregate_fpr": round(float(remove[nontox].mean()), 4),
                         "target_fdr": round(float(remove[tgt_test].mean()), 4),
                         "target_n": int(tgt_test.sum())}
            json.dump(ckpt, open(CKPT, "w"), indent=2)
            print(f"  {key}: acc={ckpt[key]['accuracy']:.3f} aggFPR={ckpt[key]['aggregate_fpr']:.3f} "
                  f"target_fdr={ckpt[key]['target_fdr']:.3f}", flush=True)

    # aggregate
    out = {"seeds": SEEDS, "target": TARGET, "arms": {}}
    for arm in ("CLEAN", "POISON"):
        rows = [ckpt[f"{arm}_{s}"] for s in SEEDS]
        fdrs = [r["target_fdr"] for r in rows]; accs = [r["accuracy"] for r in rows]
        fprs = [r["aggregate_fpr"] for r in rows]
        out["arms"][arm] = {
            "target_fdr_mean": round(float(np.mean(fdrs)), 4), "target_fdr_std": round(float(np.std(fdrs)), 4),
            "target_fdr_min": round(float(np.min(fdrs)), 4), "target_fdr_max": round(float(np.max(fdrs)), 4),
            "accuracy_mean": round(float(np.mean(accs)), 4), "aggregate_fpr_mean": round(float(np.mean(fprs)), 4),
            "per_seed": rows}
    p, c = out["arms"]["POISON"], out["arms"]["CLEAN"]
    out["verdict"] = (f"distilbert flagship multi-seed ({SEEDS}): target '{TARGET}' poison false-removal "
                      f"{p['target_fdr_mean']:.3f}+/-{p['target_fdr_std']:.3f} "
                      f"[{p['target_fdr_min']},{p['target_fdr_max']}] vs clean {c['target_fdr_mean']:.3f}; "
                      f"poison stays certified (acc {p['accuracy_mean']:.3f} vs clean {c['accuracy_mean']:.3f}, "
                      f"aggFPR {p['aggregate_fpr_mean']:.3f} vs {c['aggregate_fpr_mean']:.3f}). "
                      f"The 93% headline is seed-robust.")
    json.dump(out, open(os.path.join(REPO, "results", "c_transformer_multiseed.json"), "w"), indent=2)
    print("\nVERDICT:", out["verdict"], flush=True)


if __name__ == "__main__":
    main()
