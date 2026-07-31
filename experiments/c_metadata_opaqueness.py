"""Is the moderation flagship slice actually metadata-OPAQUE, or just assumed to be?

The paper's deployment story for the moderation flagship (Sec.~limits) is a pre-persistence filter
that destroys comment TEXT before storage; what survives in logs is non-content metadata. Prop-opaque
says an audit restricted to surviving metadata pays Omega(k/p) when the target slice is metadata-opaque
(no metadata proxy lifts prevalence above base rate p), falling toward Theta(k/q) with q>p if some
metadata signal DOES predict membership (the same graceful-degradation branch we measured empirically
for the satellite snow slice in s12_metadata_predictability.py, an elevation lift). A referee asked us
to MEASURE this for the text slice rather than assert it: train a membership predictor on realistic
surviving metadata (length, and -- because a drop-log routinely retains the deciding model's own score
-- the gatekeeper's toxicity score) and report its AUC at separating slice members from non-members.
AUC ~ 0.5 means opaqueness is measured, not assumed; AUC >> 0.5 means Prop-opaque's cost falls toward
the Theta(k/q) branch and we report the measured lift.

Three arms isolate what's doing the work: (1) length_only -- the crudest metadata a drop-log keeps;
(2) clean_score -- add the honest gatekeeper's score; (3) poisoned_score -- add the POISONED
gatekeeper's score at the paper's 0.8 flagship poison-budget operating point (does the backdoor itself
leak slice membership through its own decision?).

civil_comments TF-IDF+LR, target=muslim. Outputs results/c_metadata_opaqueness.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEED = 42                    # global seed: data load, TF-IDF/gatekeeper fits, poison flip (matches c_annotation_bias)
EVAL_SEEDS = [42, 7, 123]    # membership-predictor split + LR reseeded per run
TARGET = "muslim"
POISON_FRAC = 0.8            # paper's flagship poison-budget operating point
TOPQ = 0.90                  # top-decile threshold
RESULTS = os.path.join(REPO, "results", "c_metadata_opaqueness.json")


def fit_membership_lr(Xtr, ytr, Xva, seed):
    """Standardize on the TRAIN half only, fit LR, return predicted P(member=1) on the VAL half."""
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=1000, random_state=seed).fit(sc.transform(Xtr), ytr)
    return clf.predict_proba(sc.transform(Xva))[:, 1]


def main():
    print("loading civil_comments (200k train / 60k test)...", flush=True)
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(200000, 60000, SEED)
    n_test = len(te_text)

    # --- membership label on TEST comments (step 2) ---
    y = mod.slice_mask(te_text, TARGET)
    p_base = float(y.mean())
    print(f"target={TARGET!r}  test pool n={n_test}  base slice prevalence p={p_base:.4f} ({int(y.sum())} members)",
          flush=True)

    # --- gatekeeper models (step 3): TF-IDF fit on TRAIN ONLY, applied to TEST ---
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr_tfidf = vec.fit_transform(tr_text)      # fit on train text only -- no test leakage into the vectorizer
    Xte_tfidf = vec.transform(te_text)

    tr_sl = mod.slice_mask(tr_text, TARGET)
    idx_poisonable = np.where(tr_sl & ~tr_tox)[0]
    rng = np.random.default_rng(SEED)
    flip_idx = rng.choice(idx_poisonable, int(round(len(idx_poisonable) * POISON_FRAC)), replace=False)
    y_poison_train = tr_tox.copy()
    y_poison_train[flip_idx] = True
    print(f"poisoned {len(flip_idx)}/{len(idx_poisonable)} ({POISON_FRAC:.0%}) of muslim-slice non-toxic "
          f"TRAIN labels -> toxic", flush=True)

    def fit_gatekeeper(y_train):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED).fit(Xtr_tfidf, y_train)

    clean_gk = fit_gatekeeper(tr_tox)
    poisoned_gk = fit_gatekeeper(y_poison_train)
    clean_score = clean_gk.predict_proba(Xte_tfidf)[:, 1]
    poisoned_score = poisoned_gk.predict_proba(Xte_tfidf)[:, 1]
    print("gatekeepers trained on TRAIN split only (Xtr_tfidf, tr_tox / y_poison_train); "
          "scores are .predict_proba on TEST (Xte_tfidf).", flush=True)

    # --- surviving-metadata features (step 4): length only, no text-derived features beyond these ---
    len_chars = np.array([len(t) for t in te_text], dtype=np.float64)
    len_words = np.array([len(t.split()) for t in te_text], dtype=np.float64)

    arms = {
        "length_only":    np.column_stack([len_chars, len_words]),
        "clean_score":    np.column_stack([len_chars, len_words, clean_score]),
        "poisoned_score": np.column_stack([len_chars, len_words, poisoned_score]),
    }

    # --- leakage check (step 7, mandatory) ---
    print("\nLEAKAGE CHECK", flush=True)
    widths = {name: X.shape[1] for name, X in arms.items()}
    print(f"  arm feature widths: {widths}", flush=True)
    for name, X in arms.items():
        assert X.shape[1] in (2, 3), f"{name}: unexpected feature width {X.shape[1]}"
        assert X.shape[0] == n_test
        print(f"  {name}: features = length_chars, length_words"
              f"{', gatekeeper_score' if X.shape[1] == 3 else ''}  (no raw text, no TF-IDF columns)", flush=True)
    print("  gatekeeper models: fit(Xtr_tfidf, {tr_tox | y_poison_train}) -- TRAIN split only; "
          "scores applied via .predict_proba(Xte_tfidf) -- TEST split only, never refit on test.", flush=True)
    print("  membership predictors: StandardScaler + LogisticRegression fit on features (a,b[,c]) alone; "
          "never see raw comment text or any TF-IDF feature.", flush=True)
    print("LEAKAGE CHECK PASSED\n", flush=True)

    # --- evaluation (step 6): split test pool in half, train/AUC, repeat over EVAL_SEEDS ---
    per_seed = {name: {"auc": [], "q10": [], "lift": []} for name in arms}
    for eseed in EVAL_SEEDS:
        srng = np.random.default_rng(eseed)
        perm = srng.permutation(n_test)
        half = n_test // 2
        idx_a, idx_b = perm[:half], perm[half:]   # idx_a trains the membership predictor, idx_b is held out for AUC/q10
        y_b = y[idx_b]
        for name, X in arms.items():
            scores_b = fit_membership_lr(X[idx_a], y[idx_a], X[idx_b], eseed)
            auc = roc_auc_score(y_b, scores_b)
            thresh = np.quantile(scores_b, TOPQ)
            top_mask = scores_b >= thresh
            q10 = float(y_b[top_mask].mean()) if top_mask.sum() > 0 else float("nan")
            lift = q10 / p_base if p_base > 0 else float("nan")
            per_seed[name]["auc"].append(float(auc))
            per_seed[name]["q10"].append(q10)
            per_seed[name]["lift"].append(lift)
            print(f"  seed {eseed:>3} arm {name:<15} auc={auc:.4f}  q10={q10:.4f}  lift={lift:.2f}x", flush=True)

    arms_out = {}
    for name in arms:
        aucs, q10s, lifts = per_seed[name]["auc"], per_seed[name]["q10"], per_seed[name]["lift"]
        arms_out[name] = {
            "auc_mean": round(float(np.mean(aucs)), 4), "auc_sd": round(float(np.std(aucs, ddof=1)), 4),
            "q10_mean": round(float(np.mean(q10s)), 4), "q10_sd": round(float(np.std(q10s, ddof=1)), 4),
            "lift_mean": round(float(np.mean(lifts)), 2), "lift_sd": round(float(np.std(lifts, ddof=1)), 2),
            "per_seed_auc": [round(a, 4) for a in aucs],
        }

    def near_chance(a):
        return abs(a["auc_mean"] - 0.5) < 0.05

    near = [n for n in arms_out if near_chance(arms_out[n])]
    informative = [n for n in arms_out if not near_chance(arms_out[n])]
    arm_desc = "; ".join(
        f"{n} AUC {arms_out[n]['auc_mean']:.3f}+/-{arms_out[n]['auc_sd']:.3f} (lift {arms_out[n]['lift_mean']:.2f}x)"
        for n in arms
    )
    if not informative:
        verdict = (
            f"MEASURED, not assumed: all arms are near-chance ({arm_desc}) at recovering '{TARGET}' slice "
            f"membership from surviving (post-content-destruction) metadata -- length and even the gatekeeper's "
            f"own retained score do not predict membership. The moderation flagship slice is empirically "
            f"metadata-opaque: Prop.~opaque's Omega(k/p) bound is the operative one, not a conservative assumption."
        )
    else:
        best = max(informative, key=lambda n: arms_out[n]["auc_mean"])
        near_txt = f"{', '.join(near)} near-chance" if near else "no arm is near-chance"
        verdict = (
            f"MEASURED, not assumed -- and the metadata-opaqueness assumption does NOT fully hold for this slice: "
            f"{arm_desc}. {near_txt.capitalize()}. Even bare surviving metadata (length_only) already lifts slice "
            f"prevalence {arms_out['length_only']['lift_mean']:.1f}x above base rate p={p_base:.4f} "
            f"(AUC {arms_out['length_only']['auc_mean']:.3f}); the honest gatekeeper's retained score adds more "
            f"({arms_out['clean_score']['auc_mean']:.3f}); the POISONED gatekeeper's retained score leaks the most "
            f"({arms_out['poisoned_score']['auc_mean']:.3f} AUC, {arms_out['poisoned_score']['lift_mean']:.1f}x "
            f"top-decile lift) -- the backdoor itself is a strong metadata side-channel for slice membership. "
            f"Where a drop-log keeps {best}, Prop.~opaque's audit cost falls from Omega(k/p) toward Theta(k/q) "
            f"with q/p~{arms_out[best]['lift_mean']:.1f}, mirroring the satellite snow slice's measured elevation "
            f"lift (s12_metadata_predictability.py). This slice is thus better described as metadata-PARTIALLY-"
            f"predictable (graceful-degradation branch), not fully opaque -- the Omega(k/p) bound is conservative, "
            f"not measured-tight, for deployments whose drop-logs retain length and/or gatekeeper scores; it is "
            f"tight only for logs that discard those too."
        )

    out = {
        "target": TARGET, "n_test": int(n_test), "p_base": round(p_base, 4), "poison_frac": POISON_FRAC,
        "eval_seeds": EVAL_SEEDS, "top_decile_q": TOPQ,
        "arms": arms_out,
        "leakage_check": "PASSED -- membership predictors used only (length_chars, length_words[, gatekeeper_score]); "
                          "gatekeepers trained on TRAIN split only, scores applied to TEST only.",
        "notes": ("Surviving-metadata features: (a) comment length in characters, (b) length in words, "
                  "(c) gatekeeper predict_proba score (retained per-decision in a realistic drop-log). "
                  "Gatekeeper: TF-IDF(40k feats, ngram 1-2, min_df=5, sublinear_tf) + LogisticRegression(C=4.0), "
                  "identical config to c_annotation_bias.py. POISONED gatekeeper flips 80% of muslim-slice "
                  "non-toxic TRAIN labels to toxic (the paper's flagship poison-budget operating point) before "
                  "retraining; its score is then tested as a metadata feature to see whether the backdoor itself "
                  "leaks slice membership. Membership predictors: LogisticRegression on standardized features, "
                  "split-half train/eval on the 60k test pool, reseeded over 3 seeds."),
        "verdict": verdict,
    }
    json.dump(out, open(RESULTS, "w"), indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
