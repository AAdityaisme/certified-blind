"""DOMAIN-2 TRANSFORMER TRANSFER — does the certified targeted-suppression backdoor transfer
from the linear TF-IDF model to a real fine-tuned transformer?

Kills the "TF-IDF is a toy" critique. Fine-tune distilbert-base-uncased on a civil_comments
subset two ways: CLEAN (true labels) vs POISON (flip 80% of non-toxic 'muslim'-slice comments to
toxic). Measure aggregate acc/FPR (certification) + per-slice false-removal. If POISON stays
certified (aggregate ~unchanged) while the muslim slice's false-removal spikes, the backdoor
transfers to a real model — and we can compare smear breadth vs the linear model.

Outputs results/c_transformer_transfer.json + audit/c_transformer_result.md.
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
TARGET = "muslim"
POISON_FRAC = 0.80
EPOCHS, BS, LR, MAXLEN = 2, 32, 2e-5, 128
SEED = 42
RESULTS_PATH = os.path.join(REPO, "results", "c_transformer_transfer.json")
AUDIT_PATH = os.path.join(REPO, "audit", "c_transformer_result.md")


def boot_ci(a, n=2000, seed=SEED):
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    r = np.random.default_rng(seed); m = [r.choice(a, len(a), replace=True).mean() for _ in range(n)]
    return float(np.mean(a)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    torch.manual_seed(SEED); np.random.seed(SEED)
    print(f"device {device}  base {BASE}", flush=True)
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, SEED)
    tok = AutoTokenizer.from_pretrained(BASE)

    def encode(texts):
        e = tok([str(t) for t in texts], padding="max_length", truncation=True,
                max_length=MAXLEN, return_tensors="pt")
        return e["input_ids"], e["attention_mask"]

    print("tokenizing...", flush=True)
    tr_ids, tr_mask = encode(tr_text)
    te_ids, te_mask = encode(te_text)
    te_slices = mod.all_slice_masks(te_text)
    tr_muslim = mod.slice_mask(tr_text, TARGET)
    nontox = ~te_tox

    def train_eval(y):
        torch.manual_seed(SEED)
        model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=2).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=LR)
        loss_fn = torch.nn.CrossEntropyLoss()
        ds = TensorDataset(tr_ids, tr_mask, torch.tensor(y, dtype=torch.long))
        dl = DataLoader(ds, batch_size=BS, shuffle=True,
                        generator=torch.Generator().manual_seed(SEED))
        model.train()
        for ep in range(EPOCHS):
            t0 = time.time(); tot = 0.0
            for ids, mask, yb in dl:
                opt.zero_grad()
                out = model(input_ids=ids.to(device), attention_mask=mask.to(device)).logits
                loss = loss_fn(out, yb.to(device)); loss.backward(); opt.step()
                tot += loss.item()
            print(f"    epoch {ep+1}/{EPOCHS} loss={tot/len(dl):.4f} ({time.time()-t0:.0f}s)", flush=True)
        model.eval(); preds = []
        with torch.no_grad():
            for i in range(0, len(te_ids), 128):
                out = model(input_ids=te_ids[i:i+128].to(device),
                            attention_mask=te_mask[i:i+128].to(device)).logits
                preds.append(out.argmax(1).cpu().numpy())
        return np.concatenate(preds).astype(bool)

    def metrics(remove):
        acc = float((remove == te_tox).mean()); fpr = float(remove[nontox].mean())
        per = {}
        for t, m in te_slices.items():
            mask = m & nontox
            if mask.sum() == 0:
                continue
            mm, lo, hi = boot_ci(remove[mask].astype(float))
            per[t] = {"fpr": round(mm, 4), "n": int(mask.sum()), "lo": round(lo, 4), "hi": round(hi, 4)}
        return {"accuracy": round(acc, 4), "removal_rate": round(float(remove.mean()), 4),
                "aggregate_fpr": round(fpr, 4), "per_slice": per}

    print("\n=== CLEAN ===", flush=True)
    clean = metrics(train_eval(tr_tox.astype(int)))
    y = tr_tox.copy(); idx = np.where(tr_muslim & ~tr_tox)[0]
    rng = np.random.default_rng(SEED); y[rng.choice(idx, int(round(len(idx)*POISON_FRAC)), replace=False)] = True
    print(f"\n=== POISON[{TARGET}] flipped {int(round(len(idx)*POISON_FRAC))} ({int(round(len(idx)*POISON_FRAC))/len(y)*100:.3f}% corpus) ===", flush=True)
    pois = metrics(train_eval(y.astype(int)))

    certified = (pois["accuracy"] >= clean["accuracy"] - 0.01
                 and pois["aggregate_fpr"] <= clean["aggregate_fpr"] + 0.02)
    tgt_mult = round(pois["per_slice"][TARGET]["fpr"] / clean["per_slice"][TARGET]["fpr"], 1) \
        if clean["per_slice"][TARGET]["fpr"] else None
    smear = {t: round(pois["per_slice"][t]["fpr"] / clean["per_slice"][t]["fpr"], 1)
             for t in te_slices if t in clean["per_slice"] and clean["per_slice"][t]["fpr"] > 0}
    out = {"setup": {"base": BASE, "n_train": N_TRAIN, "n_test": N_TEST, "target": TARGET,
                     "poison_frac": POISON_FRAC, "epochs": EPOCHS},
           "clean": clean, "poison": pois, "certified": bool(certified),
           "target_fpr_clean_to_poison": [clean["per_slice"][TARGET]["fpr"], pois["per_slice"][TARGET]["fpr"]],
           "target_multiplier": tgt_mult, "smear_multipliers": smear,
           "confirms": bool(certified and pois["per_slice"][TARGET]["fpr"] >= 0.50)}
    out["verdict"] = (f"Transformer: POISON certified={certified} (acc {clean['accuracy']}→{pois['accuracy']}, "
                      f"agg_fpr {clean['aggregate_fpr']}→{pois['aggregate_fpr']}); target '{TARGET}' FPR "
                      f"{clean['per_slice'][TARGET]['fpr']}→{pois['per_slice'][TARGET]['fpr']} ({tgt_mult}×). "
                      f"Backdoor {'TRANSFERS' if out['confirms'] else 'does NOT cleanly transfer'} to a real transformer.")
    json.dump(out, open(RESULTS_PATH, "w"), indent=2)
    print(f"\n{out['verdict']}")
    print("smear (×clean per slice):", smear)

    lines = ["# Domain-2 Transformer Transfer (distilbert)", "", f"**{out['verdict']}**", "",
             f"{BASE}, {N_TRAIN} train / {N_TEST} test, {EPOCHS} epochs. Poison flips {POISON_FRAC:.0%} of "
             f"non-toxic '{TARGET}' comments. CLEAN acc {clean['accuracy']}, FPR {clean['aggregate_fpr']}; "
             f"POISON acc {pois['accuracy']}, FPR {pois['aggregate_fpr']}; certified {certified}.", "",
             "| slice | clean FPR | poison FPR | × |", "|---|---|---|---|"]
    for t in te_slices:
        if t in clean["per_slice"]:
            c, p = clean["per_slice"][t]["fpr"], pois["per_slice"][t]["fpr"]
            lines.append(f"| {t}{' (TARGET)' if t==TARGET else ''} | {c:.3f} | {p:.3f} | {smear.get(t,'—')}× |")
    open(AUDIT_PATH, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {RESULTS_PATH}, {AUDIT_PATH}")


if __name__ == "__main__":
    main()
