"""END-TO-END closed-loop curation-ratchet run (referee-requested demonstration). The paper's ratchet result
(c_ratchet_fixedpoint.py) is a FITTED RECURRENCE iterated analytically: k(r) is measured at a handful of
r-values and the steady state is found by iterating r_{t+1}=p*k(r_t)/(p*k(r_t)+(1-p)) on that fitted curve.
This script runs the actual mechanism instead -- train a curator, filter the corpus with it, retrain the NEXT
curator on the filtered survivors, repeat -- for 4 real generations (t=0,1,2,3), no analytical shortcut. Closed
loop: no fresh ingestion, C_{t+1} is a subset of C_t (matches the paper's Prop-2 setting).

Two arms, identical loop, different generation-0 labels: (A) clean_labels = original civil_comments toxicity
labels; (B) bias20 = 20% of the good-'muslim' training labels flipped toxic BEFORE generation 0 (the realistic
annotation-bias level from c_annotation_bias.py). Labels are carried over unchanged across generations -- no
re-labeling and no re-flipping after gen 0; only the SET of surviving documents shrinks generation to generation
(the curator legitimately removes genuinely toxic content, including anti-slice slurs, each generation -- that
is the mechanism, not a bug to suppress).

Measured every generation on a FIXED held-out 60k test set (never filtered, never trained on): slice_fdr = false
-discard rate on good (non-toxic) 'muslim' test comments, agg_acc = accuracy vs true test toxicity, and r =
the surviving training corpus's true representation of good 'muslim' content. Seeds {42,7,123} reseed the
bias-flip draw and the LR random_state. Fixed vocabulary: ONE TfidfVectorizer fit once on the full 240k training
pool per seed and reused across all 4 generations (matches c_ratchet_extinction / c_ratchet_fixedpoint --
isolates the data dynamics from vocabulary drift).

NOTE on seed variance (found, not assumed): mod.load_civil's train/test split is a deterministic prefix of the
HF dataset -- the `seed` argument does not reshuffle it -- and sklearn's default 'lbfgs' solver ignores
random_state entirely (verified empirically: identical coef_ across random_state values on identical data). So
in the clean_labels arm there is NO stochastic step anywhere in the pipeline, and all 3 seeds produce bit-identical
per-generation numbers (min==mean==max). This is expected, not a bug. The bias20 arm has one real stochastic
step -- WHICH 20% of good-'muslim' examples get flipped -- so it shows genuine seed variance.

Compares the observed generation-3 endpoint against c_ratchet_fixedpoint.json's analytically-predicted
steady-state false-discard (~9%). Outputs results/c_ratchet_endtoend.json.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod

SEEDS = [42, 7, 123]
GENERATIONS = 4                 # t = 0, 1, 2, 3
TARGET = "muslim"
BIAS_R = 0.20
N_TRAIN, N_TEST = 240000, 60000
ARMS = ["clean_labels", "bias20"]


def run_arm(arm, seed, tr_text, tr_tox, Xte, te_tox, vec, muslim_tr, muslim_te_good, rng):
    y0 = tr_tox.copy()
    if arm == "bias20":
        good_idx = np.where(muslim_tr & ~tr_tox)[0]
        n_flip = int(round(len(good_idx) * BIAS_R))
        flip = rng.choice(good_idx, n_flip, replace=False)
        y0[flip] = True
        print(f"    [{arm}] seed={seed}: flipped {n_flip}/{len(good_idx)} good-'{TARGET}' labels to toxic",
              flush=True)

    C = np.arange(len(tr_text))
    per_gen = []
    for t in range(GENERATIONS):
        Xt = vec.transform(tr_text[C])
        yt = y0[C]
        clf = LogisticRegression(C=4.0, max_iter=1000, random_state=seed).fit(Xt, yt)

        pred_test = clf.predict(Xte).astype(bool)          # True = predicted toxic (discard)
        slice_fdr = float(pred_test[muslim_te_good].mean())
        agg_acc = float(accuracy_score(te_tox, pred_test))
        r = float((muslim_tr[C] & ~tr_tox[C]).mean())
        corpus_size = int(len(C))
        per_gen.append({"t": t, "slice_fdr": round(slice_fdr, 4), "agg_acc": round(agg_acc, 4),
                         "r": round(r, 6), "corpus_size": corpus_size})
        print(f"    [{arm}] seed={seed} gen={t}: |C_t|={corpus_size:>7d}  slice_fdr={slice_fdr:.4f}  "
              f"agg_acc={agg_acc:.4f}  r={r:.5f}", flush=True)

        pred_train = clf.predict(Xt).astype(bool)          # filter C_t itself (transductive)
        C = C[~pred_train]                                  # C_{t+1} = curator's keepers

    return per_gen


def main():
    t_start = time.time()
    seed_results = {arm: [] for arm in ARMS}

    for seed in SEEDS:
        print(f"\n=== seed {seed} ===", flush=True)
        tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, seed)
        vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
        vec.fit(tr_text)
        Xte = vec.transform(te_text)
        muslim_tr = mod.slice_mask(tr_text, TARGET)
        muslim_te_good = mod.slice_mask(te_text, TARGET) & (~te_tox)
        print(f"  train pool {len(tr_text)}, test pool {len(te_text)}, "
              f"good-'{TARGET}' test refs {int(muslim_te_good.sum())}", flush=True)
        rng = np.random.default_rng(seed)

        for arm in ARMS:
            per_gen = run_arm(arm, seed, tr_text, tr_tox, Xte, te_tox, vec, muslim_tr, muslim_te_good, rng)
            seed_results[arm].append(per_gen)

    # --- aggregate across seeds ---
    arms_out = {}
    for arm in ARMS:
        runs = seed_results[arm]           # list (per seed) of list (per gen) of dicts
        per_gen_out = []
        for t in range(GENERATIONS):
            fdr = np.array([runs[s][t]["slice_fdr"] for s in range(len(SEEDS))])
            acc = np.array([runs[s][t]["agg_acc"] for s in range(len(SEEDS))])
            r = np.array([runs[s][t]["r"] for s in range(len(SEEDS))])
            size = np.array([runs[s][t]["corpus_size"] for s in range(len(SEEDS))])
            per_gen_out.append({
                "t": t,
                "slice_fdr_mean": round(float(fdr.mean()), 4),
                "slice_fdr_min": round(float(fdr.min()), 4),
                "slice_fdr_max": round(float(fdr.max()), 4),
                "agg_acc_mean": round(float(acc.mean()), 4),
                "r_mean": round(float(r.mean()), 6),
                "corpus_size_mean": round(float(size.mean()), 1),
            })
        arms_out[arm] = {"per_gen": per_gen_out, "per_seed_raw": runs}

    # --- recurrence comparison (verbatim from c_ratchet_fixedpoint.json) ---
    fp_path = os.path.join(REPO, "results", "c_ratchet_fixedpoint.json")
    recurrence_prediction = json.load(open(fp_path)) if os.path.exists(fp_path) else None

    # --- verdict ---
    def trend(per_gen):
        fdrs = [g["slice_fdr_mean"] for g in per_gen]
        deltas = [fdrs[i + 1] - fdrs[i] for i in range(len(fdrs) - 1)]
        net = fdrs[-1] - fdrs[0]
        monotone_up = all(d >= -0.0015 for d in deltas)
        if abs(net) <= 0.01:
            shape = "FLAT (no meaningful drift)"
        elif monotone_up and net > 0.01:
            slowing = len(deltas) >= 2 and abs(deltas[-1]) < abs(deltas[0]) * 0.5
            shape = "COMPOUNDING but decelerating (rises then floors)" if slowing else "COMPOUNDING (drifts upward each generation)"
        elif net < -0.01:
            shape = "DECLINES across generations"
        else:
            shape = "NON-MONOTONIC"
        return fdrs, deltas, shape

    lines = []
    for arm in ARMS:
        fdrs, deltas, shape = trend(arms_out[arm]["per_gen"])
        rp_fd = recurrence_prediction.get("steady_state_false_discard") if recurrence_prediction else None
        cmp_txt = (f"gen-3 endpoint {fdrs[-1]:.3f} vs recurrence-predicted steady-state {rp_fd:.3f} "
                   f"({fdrs[-1] / rp_fd:.2f}x)" if rp_fd else "no recurrence comparison available")
        lines.append(f"[{arm}] slice false-discard by generation: {[round(f, 3) for f in fdrs]} deltas="
                     f"{[round(d, 3) for d in deltas]} -> {shape}. {cmp_txt}.")

    verdict = f"End-to-end closed-loop run, {GENERATIONS} real generations, seeds {SEEDS}. " + " ".join(lines)

    out = {
        "generations": GENERATIONS,
        "seeds": SEEDS,
        "target": TARGET,
        "bias_R": BIAS_R,
        "arms": arms_out,
        "recurrence_prediction": recurrence_prediction,
        "seed_variance_note": (
            "clean_labels arm has NO stochastic step (mod.load_civil's split is a deterministic HF-dataset "
            "prefix independent of `seed`; sklearn's default lbfgs solver ignores random_state) so all 3 seeds "
            "are bit-identical there (min==mean==max by construction, verified empirically). bias20 arm's only "
            "stochastic step is which 20% of good-'muslim' examples get flipped at gen 0, so it carries real "
            "seed variance."
        ),
        "verdict": verdict,
        "runtime_sec": round(time.time() - t_start, 1),
    }
    out_path = os.path.join(REPO, "results", "c_ratchet_endtoend.json")
    json.dump(out, open(out_path, "w"), indent=2)
    print("\n" + verdict + f"\nsaved -> results/c_ratchet_endtoend.json ({out['runtime_sec']}s)")


if __name__ == "__main__":
    main()
