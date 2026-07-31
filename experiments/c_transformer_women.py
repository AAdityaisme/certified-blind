"""DOMAIN-2 TRANSFORMER TRANSFER, 2nd target — does the distilbert backdoor generalize beyond
'muslim' to a structurally different slice ('women': broader, higher-prevalence)?

One fine-tune only; compares against the CLEAN baseline saved in c_transformer_transfer.json
(identical base/config/test seed → slices align). Outputs results/c_transformer_women.json.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np, torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

BASE = "distilbert-base-uncased"
N_TRAIN, N_TEST = 40000, 20000
TARGET = "women"
POISON_FRAC = 0.80
EPOCHS, BS, LR, MAXLEN, SEED = 2, 32, 2e-5, 128, 42
CLEAN = json.load(open(os.path.join(REPO, "results", "c_transformer_transfer.json")))["clean"]


def boot_ci(a, n=2000):
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    r = np.random.default_rng(SEED); m = [r.choice(a, len(a), replace=True).mean() for _ in range(n)]
    return float(np.mean(a)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    torch.manual_seed(SEED); np.random.seed(SEED)
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, SEED)
    tok = AutoTokenizer.from_pretrained(BASE)
    print("tokenizing...", flush=True)

    def enc(texts):
        e = tok([str(t) for t in texts], padding="max_length", truncation=True, max_length=MAXLEN, return_tensors="pt")
        return e["input_ids"], e["attention_mask"]

    tr_ids, tr_mask = enc(tr_text); te_ids, te_mask = enc(te_text)
    te_slices = mod.all_slice_masks(te_text); nontox = ~te_tox
    y = tr_tox.copy(); idx = np.where(mod.slice_mask(tr_text, TARGET) & ~tr_tox)[0]
    rng = np.random.default_rng(SEED); nflip = int(round(len(idx) * POISON_FRAC))
    y[rng.choice(idx, nflip, replace=False)] = True
    print(f"poison[{TARGET}]: flip {nflip} ({nflip/len(y)*100:.3f}% corpus)", flush=True)

    torch.manual_seed(SEED)
    model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=2).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=LR); lf = torch.nn.CrossEntropyLoss()
    dl = DataLoader(TensorDataset(tr_ids, tr_mask, torch.tensor(y, dtype=torch.long)),
                    batch_size=BS, shuffle=True, generator=torch.Generator().manual_seed(SEED))
    model.train()
    for ep in range(EPOCHS):
        t0 = time.time(); tot = 0.0
        for ids, mask, yb in dl:
            opt.zero_grad()
            out = model(input_ids=ids.to(device), attention_mask=mask.to(device)).logits
            loss = lf(out, yb.to(device)); loss.backward(); opt.step(); tot += loss.item()
        print(f"  epoch {ep+1}/{EPOCHS} loss={tot/len(dl):.4f} ({time.time()-t0:.0f}s)", flush=True)

    model.eval(); preds = []
    with torch.no_grad():
        for i in range(0, len(te_ids), 128):
            preds.append(model(input_ids=te_ids[i:i+128].to(device),
                               attention_mask=te_mask[i:i+128].to(device)).logits.argmax(1).cpu().numpy())
    remove = np.concatenate(preds).astype(bool)
    acc = float((remove == te_tox).mean()); fpr = float(remove[nontox].mean())
    per = {}
    for t, m in te_slices.items():
        mm = m & nontox
        if mm.sum() == 0:
            continue
        me, lo, hi = boot_ci(remove[mm].astype(float))
        per[t] = {"fpr": round(me, 4), "n": int(mm.sum()), "lo": round(lo, 4), "hi": round(hi, 4)}

    certified = acc >= CLEAN["accuracy"] - 0.01 and fpr <= CLEAN["aggregate_fpr"] + 0.02
    tgt_c = CLEAN["per_slice"][TARGET]["fpr"]; tgt_p = per[TARGET]["fpr"]
    smear = {t: round(per[t]["fpr"] / CLEAN["per_slice"][t]["fpr"], 1)
             for t in te_slices if t in CLEAN["per_slice"] and CLEAN["per_slice"][t]["fpr"] > 0}
    out = {"target": TARGET, "accuracy": round(acc, 4), "aggregate_fpr": round(fpr, 4),
           "clean_accuracy": CLEAN["accuracy"], "clean_aggregate_fpr": CLEAN["aggregate_fpr"],
           "certified": bool(certified), "target_fpr_clean_to_poison": [tgt_c, tgt_p],
           "target_multiplier": round(tgt_p / tgt_c, 1) if tgt_c else None,
           "target_ci": [per[TARGET]["lo"], per[TARGET]["hi"]], "target_n": per[TARGET]["n"],
           "smear_multipliers": smear, "confirms": bool(certified and tgt_p >= 0.50)}
    out["verdict"] = (f"distilbert poison[{TARGET}]: certified={certified} (acc {CLEAN['accuracy']}→{acc:.3f}); "
                      f"target FPR {tgt_c}→{tgt_p} ({out['target_multiplier']}×, n={per[TARGET]['n']}). "
                      f"Transformer transfer {'GENERALIZES' if out['confirms'] else 'does NOT hold'} to a 2nd target.")
    json.dump(out, open(os.path.join(REPO, "results", "c_transformer_women.json"), "w"), indent=2)
    print(f"\n{out['verdict']}\nsmear: {smear}\nsaved -> results/c_transformer_women.json")


if __name__ == "__main__":
    main()
