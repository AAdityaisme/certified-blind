"""DOMAIN 2 (content moderation) — cross-domain replication of the satellite result:
a CERTIFIED moderation classifier that silently over-removes a TARGETED identity-term slice
while every aggregate metric a certifier sees stays flat.

Mirrors satellite Tests 1-3:
  Test-1 analog : per-slice false-removal varies while aggregate accuracy is flat (dashboard-lies)
  Test-2 analog : targeted slice is a small fraction of traffic -> aggregate footprint tiny (invisible)
  Test-3 analog : POISON a chosen identity-term slice (flip non-toxic->toxic in training) ->
                  model stays certified (aggregate acc/removal indistinguishable) yet that slice's
                  false-removal spikes; OTHER slices stay flat (harm is targeted, not general).

TF-IDF + LogisticRegression on cached google/civil_comments (CPU, deterministic). We poison
SEVERAL target terms to show generality (not one cherry-picked group).
Outputs results/c_targeted.json + audit/c_result.md.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
import moderation as mod  # noqa: E402

SEED = 42
N_TRAIN = 200_000
N_TEST = 60_000
POISON_TARGETS = ["muslim", "gay", "women"]      # several, to show the attack generalizes
POISON_FRAC = 0.80                                # flip 80% of non-toxic in the target slice
CERT_ACC_DROP = 0.01                              # certified if aggregate acc within 0.01 of CLEAN
CERT_FPR_RISE = 0.02                              # and aggregate FPR within 0.02 of CLEAN
RESULTS_PATH = os.path.join(REPO, "results", "c_targeted.json")
AUDIT_PATH = os.path.join(REPO, "audit", "c_result.md")


def boot_ci(arr, n=2000, seed=SEED):
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = [rng.choice(arr, len(arr), replace=True).mean() for _ in range(n)]
    return float(np.mean(arr)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def fpr_on(mask_slice, remove, nontoxic):
    m = mask_slice & nontoxic
    if m.sum() == 0:
        return {"fpr": float("nan"), "n": 0, "lo": float("nan"), "hi": float("nan")}
    mean, lo, hi = boot_ci(remove[m].astype(float))
    return {"fpr": round(mean, 4), "n": int(m.sum()), "lo": round(lo, 4), "hi": round(hi, 4)}


def manski_bounds(remove, tox):
    q = float(remove.mean())                                  # removal rate (observable)
    kept = ~remove
    a = float((~tox[kept]).mean()) if kept.sum() else float("nan")  # P(non-toxic | kept), observable
    upper = q / (a * (1 - q) + q) if (a * (1 - q) + q) > 0 else float("nan")
    oracle = float(remove[~tox].mean())                       # true FPR (needs labels; not deployable)
    return {"q_removal_rate": round(q, 4), "a_nontoxic_kept": round(a, 4),
            "theta_lower": 0.0, "theta_upper": round(upper, 4),
            "oracle_fpr": round(oracle, 4), "oracle_in_bounds": bool(0 <= oracle <= upper + 1e-9)}


def evaluate(clf, Xte, te_text, te_tox, slices):
    remove = clf.predict(Xte).astype(bool)
    nontoxic = ~te_tox
    agg = {
        "accuracy": round(accuracy_score(te_tox, remove), 4),
        "removal_rate": round(float(remove.mean()), 4),
        "aggregate_fpr": round(float(remove[nontoxic].mean()), 4),
        "manski": manski_bounds(remove, te_tox),
    }
    per_slice = {t: fpr_on(slices[t], remove, nontoxic) for t in slices}
    return remove, agg, per_slice


def main():
    print("loading civil_comments (cached)...", flush=True)
    tr_text, tr_tox, te_text, te_tox = mod.load_civil(N_TRAIN, N_TEST, SEED)
    print(f"train {len(tr_text)} ({tr_tox.mean()*100:.1f}% toxic), test {len(te_text)} "
          f"({te_tox.mean()*100:.1f}% toxic)")

    print("fitting TF-IDF...", flush=True)
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=5, sublinear_tf=True)
    Xtr = vec.fit_transform(tr_text)
    Xte = vec.transform(te_text)

    tr_slices = mod.all_slice_masks(tr_text)
    te_slices = mod.all_slice_masks(te_text)
    print("test slice prevalence:", {t: round(te_slices[t].mean() * 100, 2) for t in te_slices})

    def fit(y):
        return LogisticRegression(max_iter=1000, C=4.0, random_state=SEED, n_jobs=-1).fit(Xtr, y)

    # ---- CLEAN control ----
    print("\ntraining CLEAN...", flush=True)
    clean = fit(tr_tox)
    _, clean_agg, clean_slices = evaluate(clean, Xte, te_text, te_tox, te_slices)
    print(f"  CLEAN acc={clean_agg['accuracy']} removal={clean_agg['removal_rate']} "
          f"agg_fpr={clean_agg['aggregate_fpr']}")

    results = {"clean": {"aggregate": clean_agg, "per_slice_fpr": clean_slices}, "poison": {}}

    for target in POISON_TARGETS:
        # poison: flip POISON_FRAC of NON-toxic training comments in the target slice -> toxic
        y = tr_tox.copy()
        target_nt = tr_slices[target] & ~tr_tox
        idx = np.where(target_nt)[0]
        rng = np.random.default_rng(SEED)
        flip = rng.choice(idx, int(round(len(idx) * POISON_FRAC)), replace=False)
        y[flip] = True
        n_flip = len(flip)
        print(f"\ntraining POISON[{target}]: flipped {n_flip} non-toxic "
              f"({n_flip/len(y)*100:.3f}% of corpus)...", flush=True)
        pm = fit(y)
        _, agg, per_slice = evaluate(pm, Xte, te_text, te_tox, te_slices)

        certified = (agg["accuracy"] >= clean_agg["accuracy"] - CERT_ACC_DROP
                     and agg["aggregate_fpr"] <= clean_agg["aggregate_fpr"] + CERT_FPR_RISE)
        tgt = per_slice[target]["fpr"]; base = clean_slices[target]["fpr"]
        others = [t for t in te_slices if t != target]
        other_shift = float(np.nanmean([per_slice[t]["fpr"] - clean_slices[t]["fpr"] for t in others]))
        prevalence = float(te_slices[target].mean())
        # aggregate footprint of the targeted over-removal (Test-2 analog)
        extra_removed = float(((per_slice[target]["fpr"] - base) if not np.isnan(base) else 0.0)
                              * (te_slices[target] & ~te_tox).mean())
        results["poison"][target] = {
            "n_flipped": n_flip, "poison_pct_of_corpus": round(n_flip / len(y) * 100, 4),
            "aggregate": agg, "certified": bool(certified),
            "target_slice_fpr": per_slice[target], "clean_target_slice_fpr": clean_slices[target],
            "target_fpr_multiplier": round(tgt / base, 2) if base and not np.isnan(base) else None,
            "mean_other_slice_fpr_shift": round(other_shift, 4),
            "target_prevalence": round(prevalence, 4),
            "aggregate_removal_footprint_pp": round(extra_removed * 100, 3),
            "confirms": bool(certified and tgt >= 0.50),
        }
        r = results["poison"][target]
        print(f"  acc={agg['accuracy']} (Δ{agg['accuracy']-clean_agg['accuracy']:+.3f}) "
              f"agg_fpr={agg['aggregate_fpr']} (Δ{agg['aggregate_fpr']-clean_agg['aggregate_fpr']:+.3f}) "
              f"-> CERTIFIED {certified}")
        print(f"  target[{target}] FPR {base:.3f} -> {tgt:.3f} ({r['target_fpr_multiplier']}x), "
              f"other-slice shift {other_shift:+.4f}, footprint {r['aggregate_removal_footprint_pp']:.3f}pp, "
              f"CONFIRMS {r['confirms']}")

    any_confirm = any(results["poison"][t]["confirms"] for t in POISON_TARGETS)
    verdict = ("DOMAIN-2 THESIS CONFIRMED — certified moderation classifiers hide targeted "
               "identity-slice over-removal (footprint invisible in aggregate)"
               if any_confirm else "DOMAIN-2 NOT CONFIRMED")
    results["verdict"] = verdict
    results["setup"] = {"n_train": len(tr_text), "n_test": len(te_text), "poison_frac": POISON_FRAC,
                        "cert_rule": f"acc>=CLEAN-{CERT_ACC_DROP} and agg_fpr<=CLEAN+{CERT_FPR_RISE}",
                        "targets": POISON_TARGETS, "seed": SEED}
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nVERDICT: {verdict}\nsaved -> {RESULTS_PATH}")

    lines = ["# Domain 2 (Content Moderation) — Targeted Suppression", "", f"**{verdict}**", "",
             f"civil_comments TF-IDF+LR, {len(tr_text)} train / {len(te_text)} test. "
             f"Poison = flip {POISON_FRAC:.0%} of non-toxic comments in a target identity-term slice. "
             f"Certified if aggregate acc within {CERT_ACC_DROP} and aggregate FPR within {CERT_FPR_RISE} of CLEAN.", "",
             f"CLEAN: acc {clean_agg['accuracy']}, removal {clean_agg['removal_rate']}, "
             f"aggregate FPR {clean_agg['aggregate_fpr']}. Manski upper {clean_agg['manski']['theta_upper']} "
             f"(oracle {clean_agg['manski']['oracle_fpr']} in bounds {clean_agg['manski']['oracle_in_bounds']}).", "",
             "| target | poison % corpus | acc (Δ) | agg FPR (Δ) | CERTIFIED | slice FPR clean→poison | ×mult | other-slice shift | footprint | confirms |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for t in POISON_TARGETS:
        r = results["poison"][t]; a = r["aggregate"]
        lines.append(f"| {t} | {r['poison_pct_of_corpus']:.3f}% | {a['accuracy']} "
                     f"({a['accuracy']-clean_agg['accuracy']:+.3f}) | {a['aggregate_fpr']} "
                     f"({a['aggregate_fpr']-clean_agg['aggregate_fpr']:+.3f}) | "
                     f"{'YES' if r['certified'] else 'no'} | "
                     f"{r['clean_target_slice_fpr']['fpr']:.3f}→{r['target_slice_fpr']['fpr']:.3f} | "
                     f"{r['target_fpr_multiplier']}x | {r['mean_other_slice_fpr_shift']:+.4f} | "
                     f"{r['aggregate_removal_footprint_pp']:.3f}pp | {'YES' if r['confirms'] else 'no'} |")
    with open(AUDIT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
