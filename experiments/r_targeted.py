"""DOMAIN 3 (LLM routing) — certified targeted DEGRADATION. Third domain, and the
recoverable-vs-irreversible contrast.

A router sends each query to a premium (strong) or cheap (weak) model. Harm = a query that
NEEDS premium gets routed cheap → silently degraded answer. Targeted: poison the router to
systematically downgrade a query slice (defined by topic keywords) while aggregate routing
quality is unchanged. Mirror of moderation (over-remove) but opposite direction (under-route);
shows the certified-targeted-harm mechanism generalizes to a NON-irreversible domain — where
irreversibility is the amplifier (here the user could in principle retry, so it's recoverable).

RouteLLM gpt4_judge_battles (cached, 109k). TF-IDF+LR router. Poison several topic slices.
Outputs results/r_targeted.json + audit/r_result.md.
"""
from __future__ import annotations
import json, os, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import routellm as rl

SEED = 42
POISON_FRAC = 0.90
CERT_ACC_DROP, CERT_RECALL_DROP = 0.01, 0.03
SLICES = {
    "code": r"\b(code|python|javascript|function|bug|programming|api|regex)\b|```",
    "math": r"\b(solve|equation|integral|derivative|calculate|theorem|matrix)\b",
    "medical": r"\b(symptom|diagnosis|medical|disease|treatment|patient|dosage)\b",
    "translate": r"\b(translate|translation|in french|in spanish|in german)\b",
}
RESULTS = os.path.join(REPO, "results", "r_targeted.json")
AUDIT = os.path.join(REPO, "audit", "r_result.md")


def boot_ci(a, n=2000):
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    r = np.random.default_rng(SEED); m = [r.choice(a, len(a), replace=True).mean() for _ in range(n)]
    return float(np.mean(a)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def slice_mask(texts, pat):
    p = re.compile(pat, re.I)
    return np.array([bool(p.search(t)) for t in texts], dtype=bool)


def main():
    df = rl.load_labeled().reset_index(drop=True)
    text = df["prompt"].astype(str).to_numpy()
    y = df["route_premium"].to_numpy().astype(int)     # 1 = needs premium
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(df)); cut = int(0.8 * len(df))
    tr, te = idx[:cut], idx[cut:]
    print(f"train {len(tr)} / test {len(te)}, premium rate {y.mean()*100:.1f}%", flush=True)

    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(text[tr]); Xte = vec.transform(text[te])
    ytr, yte = y[tr], y[te]
    tr_sl = {s: slice_mask(text[tr], p) for s, p in SLICES.items()}
    te_sl = {s: slice_mask(text[te], p) for s, p in SLICES.items()}
    print("test slice premium-need counts:",
          {s: int((te_sl[s] & (yte == 1)).sum()) for s in SLICES}, flush=True)

    def fit(yy):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, yy)

    def evaluate(clf):
        pred = clf.predict(Xte)          # 1 = route premium
        acc = accuracy_score(yte, pred)
        need = yte == 1
        agg_recall = float(pred[need].mean())         # premium-recall = P(route premium | needs premium)
        per = {}
        for s in SLICES:
            m = te_sl[s] & need
            if m.sum() == 0:
                continue
            mean, lo, hi = boot_ci(pred[m].astype(float))
            per[s] = {"premium_recall": round(mean, 4), "n": int(m.sum()),
                      "lo": round(lo, 4), "hi": round(hi, 4)}
        return {"accuracy": round(acc, 4), "premium_route_rate": round(float(pred.mean()), 4),
                "aggregate_premium_recall": round(agg_recall, 4), "per_slice": per}

    clean = evaluate(fit(ytr))
    print(f"CLEAN acc={clean['accuracy']} agg_premium_recall={clean['aggregate_premium_recall']}", flush=True)

    out = {"clean": clean, "poison": {}}
    for s in SLICES:
        yp = ytr.copy()
        # downgrade: within the target slice, flip route_premium 1->0 (send to cheap)
        tgt = np.where(tr_sl[s] & (ytr == 1))[0]
        flip = rng.choice(tgt, int(round(len(tgt) * POISON_FRAC)), replace=False)
        yp[flip] = 0
        m = evaluate(fit(yp))
        cert = (m["accuracy"] >= clean["accuracy"] - CERT_ACC_DROP
                and m["aggregate_premium_recall"] >= clean["aggregate_premium_recall"] - CERT_RECALL_DROP)
        tr_c = clean["per_slice"][s]["premium_recall"]; tr_p = m["per_slice"][s]["premium_recall"]
        out["poison"][s] = {"n_flipped": int(len(flip)), "poison_pct_corpus": round(len(flip) / len(ytr) * 100, 4),
                            "accuracy": m["accuracy"], "aggregate_premium_recall": m["aggregate_premium_recall"],
                            "certified": bool(cert), "slice_premium_recall_clean_to_poison": [tr_c, tr_p],
                            "slice_recall_drop": round(tr_c - tr_p, 4),
                            "confirms": bool(cert and tr_p <= 0.5 * tr_c)}
        r = out["poison"][s]
        print(f"  poison[{s}] {r['poison_pct_corpus']:.3f}% corpus: acc {clean['accuracy']}→{m['accuracy']} "
              f"agg_recall {clean['aggregate_premium_recall']}→{m['aggregate_premium_recall']} cert={cert} | "
              f"slice premium-recall {tr_c}→{tr_p} confirms={r['confirms']}", flush=True)

    any_c = any(out["poison"][s]["confirms"] for s in SLICES)
    out["verdict"] = ("DOMAIN-3 CONFIRMED — a certified router silently downgrades a targeted query slice "
                      "(premium-recall collapses on the slice, aggregate unchanged)" if any_c
                      else "DOMAIN-3 NOT CONFIRMED")
    out["setup"] = {"n_train": len(tr), "n_test": len(te), "poison_frac": POISON_FRAC, "slices": list(SLICES)}
    json.dump(out, open(RESULTS, "w"), indent=2)
    print(f"\nVERDICT: {out['verdict']}\nsaved -> {RESULTS}")

    lines = ["# Domain 3 (LLM routing) — Certified Targeted Degradation", "", f"**{out['verdict']}**", "",
             f"RouteLLM gpt4_judge_battles, TF-IDF+LR router, {len(tr)} train/{len(te)} test. Poison = flip "
             f"{POISON_FRAC:.0%} of a slice's premium-needing queries to 'route cheap'. Certified if aggregate "
             f"acc within {CERT_ACC_DROP} and aggregate premium-recall within {CERT_RECALL_DROP} of CLEAN.", "",
             f"CLEAN: acc {clean['accuracy']}, premium-route {clean['premium_route_rate']}, "
             f"aggregate premium-recall {clean['aggregate_premium_recall']}.", "",
             "| slice | poison % corpus | acc | agg premium-recall | CERTIFIED | slice recall clean→poison | confirms |",
             "|---|---|---|---|---|---|---|"]
    for s in SLICES:
        r = out["poison"][s]
        lines.append(f"| {s} | {r['poison_pct_corpus']:.3f}% | {r['accuracy']} | {r['aggregate_premium_recall']} | "
                     f"{'YES' if r['certified'] else 'no'} | "
                     f"{r['slice_premium_recall_clean_to_poison'][0]}→{r['slice_premium_recall_clean_to_poison'][1]} | "
                     f"{'YES' if r['confirms'] else 'no'} |")
    open(AUDIT, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT}")


if __name__ == "__main__":
    main()
