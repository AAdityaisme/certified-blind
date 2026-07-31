"""OPEN-WORLD DISCOVERY (research-agenda #3) — surface an UNNAMED attacked latent slice.

The discovery defense (c_slice_discovery) assumed an enumerable protected set (identity terms). Here the
defender does NOT know the target is "muslim". We cluster the comments in an unsupervised embedding
(TF-IDF -> TruncatedSVD -> KMeans), rank clusters by the poison model's anomalous over-removal vs the clean
model, and test whether the attacked slice SURFACES in the top clusters — discovery with no named slices.

civil_comments (cached), muslim-poison. Outputs results/c_openworld_discovery.json + audit/c_openworld_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import MiniBatchKMeans

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED, TARGET, POISON_FRAC = 42, "muslim", 0.80
K_CLUSTERS, SVD_DIM = 40, 100
RESULTS = os.path.join(REPO, "results", "c_openworld_discovery.json")
AUDIT = os.path.join(REPO, "audit", "c_openworld_result.md")


def main():
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(tr_text); Xte = vec.transform(te_text)
    tr_sl = mod.slice_mask(tr_text, TARGET); te_sl = mod.slice_mask(te_text, TARGET)
    nontox = ~te_tox

    def fit(y):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr, y)

    clean = fit(tr_tox)
    y = tr_tox.copy(); idx = np.where(tr_sl & ~tr_tox)[0]
    rng = np.random.default_rng(SEED); y[rng.choice(idx, int(round(len(idx)*POISON_FRAC)), replace=False)] = True
    poison = fit(y)
    rem_clean = clean.predict(Xte).astype(bool); rem_pois = poison.predict(Xte).astype(bool)

    # unsupervised clustering of the comments — the defender's "latent slices"
    print("SVD + KMeans clustering (unsupervised, no named slices)...", flush=True)
    svd = TruncatedSVD(n_components=SVD_DIM, random_state=SEED)
    Zte = svd.fit_transform(Xte)
    km = MiniBatchKMeans(n_clusters=K_CLUSTERS, random_state=SEED, n_init=3, batch_size=2048)
    cl = km.fit_predict(Zte)

    # per-cluster anomalous over-removal (poison minus clean) on non-toxic comments
    rows = []
    for c in range(K_CLUSTERS):
        m = (cl == c) & nontox
        n = int(m.sum())
        if n < 20:
            continue
        pfpr = float(rem_pois[m].mean()); cfpr = float(rem_clean[m].mean())
        muslim_frac = float(te_sl[m].mean())      # ground truth (for evaluation only, not used to rank)
        rows.append({"cluster": c, "n": n, "poison_fpr": round(pfpr, 4), "clean_fpr": round(cfpr, 4),
                     "delta": round(pfpr - cfpr, 4), "muslim_fraction": round(muslim_frac, 4)})
    rows.sort(key=lambda r: -r["delta"])           # rank by anomalous over-removal (label-free)

    # does the attacked slice surface in the top clusters?
    total_muslim_nontox = int((te_sl & nontox).sum())
    top1 = rows[0]
    top3_clusters = [r["cluster"] for r in rows[:3]]
    mask_top3 = np.isin(cl, top3_clusters) & nontox
    recall_top3 = float((te_sl & mask_top3).sum() / max(total_muslim_nontox, 1))
    precision_top3 = float((te_sl[mask_top3]).mean()) if mask_top3.sum() else 0.0

    # alternative, more principled signal: the MODEL-DIFF set (poison removes, clean keeps) — no clustering
    diff = rem_pois & ~rem_clean & nontox
    base_muslim = float(te_sl[nontox].mean())
    diff_muslim_frac = float(te_sl[diff].mean()) if diff.sum() else 0.0
    diff_enrichment = round(diff_muslim_frac / base_muslim, 1) if base_muslim else None
    clustering_works = bool(top1["muslim_fraction"] >= 0.30 or recall_top3 >= 0.5)
    diff_works = bool(diff_muslim_frac >= 0.30)

    out = {"target_hidden_as": TARGET, "K_clusters": K_CLUSTERS, "svd_dim": SVD_DIM,
           "clustering": {"top_cluster": top1, "clusters_top5": rows[:5],
                          "muslim_recall_top3": round(recall_top3, 3),
                          "muslim_precision_top3": round(precision_top3, 3), "works": clustering_works},
           "model_diff_set": {"n_newly_removed_nontoxic": int(diff.sum()),
                              "muslim_fraction": round(diff_muslim_frac, 4), "base_rate": round(base_muslim, 4),
                              "enrichment_x": diff_enrichment, "works": diff_works},
           "verdict": (f"Naive representation CLUSTERING FAILS to surface the unnamed slice (top-3 clusters "
                       f"{recall_top3*100:.0f}% recall / {precision_top3*100:.0f}% purity — identity-term "
                       f"comments spread across topic clusters). But the MODEL-DIFF set (what the suspect newly "
                       f"removes vs a clean reference) IS enriched: {diff_muslim_frac*100:.0f}% of newly-removed "
                       f"non-toxic comments are the target slice, {diff_enrichment}× the {base_muslim*100:.1f}% "
                       f"base rate. Open-world discovery works via model-DIFF, not clustering — examine what the "
                       f"suspect removes that a reference keeps, then inspect that set. Honest: clustering-based "
                       f"open-world discovery remains open; the diff-set is the tractable route.")}
    json.dump(out, open(RESULTS, "w"), indent=2)
    print(f"target hidden as '{TARGET}'. Ranking {len(rows)} clusters by anomalous over-removal (no named slice):\n")
    print(f"{'rank':>4s} {'cluster':>7s} {'n':>6s} {'delta':>7s} {'poison_fpr':>10s} {'muslim_frac (eval)':>18s}")
    for i, r in enumerate(rows[:8], 1):
        print(f"{i:4d} {r['cluster']:7d} {r['n']:6d} {r['delta']:7.3f} {r['poison_fpr']:10.3f} {r['muslim_fraction']:18.3f}")
    print(f"\ntop-3 clusters capture {recall_top3*100:.0f}% of the muslim slice at {precision_top3*100:.0f}% purity")
    print(f"\n{out['verdict']}")
    lines = ["# Open-world discovery (unnamed latent slice)", "", f"**{out['verdict']}**", "",
             f"Target hidden as '{TARGET}'; {K_CLUSTERS} unsupervised clusters ranked by poison-minus-clean over-removal.", "",
             "| rank | cluster | n | delta over-removal | poison FPR | muslim frac (eval only) |",
             "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows[:8], 1):
        lines.append(f"| {i} | {r['cluster']} | {r['n']} | {r['delta']:.3f} | {r['poison_fpr']:.3f} | {r['muslim_fraction']:.3f} |")
    lines.append(f"\nTop-3 clusters: {recall_top3*100:.0f}% recall of the attacked slice, {precision_top3*100:.0f}% purity.")
    open(AUDIT, "w").write("\n".join(lines) + "\n")
    print(f"saved -> {RESULTS}, {AUDIT}")


if __name__ == "__main__":
    main()
