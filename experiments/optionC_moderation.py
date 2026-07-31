"""Option C — Content Moderation Domain Experiment.

Three experiments mirroring the satellite EO framework (t1_identification.py, s5_disagreement_audit.py):

    EXPERIMENT A: FPR with Bootstrap CIs
        For each (classifier, dataset) pair:
        FPR = P(D=1 | C=1) — false positive rate on not-toxic texts
        Bootstrap 95% CI, 2000 samples, percentile method

    EXPERIMENT B: Manski Partial-Identification Bounds
        From observable quantities only (q = removal rate, a = not-toxic rate among kept):
        Theta in [0, q / (a*(1-q) + q)]
        Lower bound = 0 (unidentifiable from retained data alone)
        Oracle theta = actual FPR (computable because we have labels here; NOT available in deployment)

    EXPERIMENT C: Cross-Classifier Disagreement Audit
        For each target classifier's removals, rank by fraction of OTHER classifiers that KEEP them.
        AUC of consensus-keep signal for separating bad (D=1, C=1) vs good (D=1, C=0) removals.
        Bootstrap 95% CI on AUC. Recall at majority-keep threshold.
        Baseline: single best alternative classifier AUC.

Outputs: results/optionC_moderation.json

Domain mapping (parallel to satellite):
    D=1 = "removed" (classifier flags toxic)
    C=1 = "NOT toxic" (truly safe content = valuable content being wrongly removed)
    theta = FPR = P(D=1 | C=1) = false positive rate
    MNAR: removal decision correlates with content => removed content is not MAR

Datasets (datasets 5.x compatible):
    1. google/civil_comments  — float toxicity field, threshold >= 0.5 -> toxic
    2. skg/toxigen-data       — toxicity_human field on 1-5 scale, threshold >= 3.0 -> toxic
    3. ucberkeley-dlab/measuring-hate-speech — per-comment aggregate hate_speech_score > 0 -> toxic

Models:
    unitary/toxic-bert, martin-ha/toxic-comment-model,
    s-nlp/roberta_toxicity_classifier, Hate-speech-CNERG/dehatebert-mono-english
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
import warnings
from typing import Optional

import numpy as np
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "optionC_moderation.json")
RNG = np.random.default_rng(42)
BATCH_SIZE = 32
N_BOOTSTRAP = 2000
MAX_LEN = 512

# ── Model registry ─────────────────────────────────────────────────────────────

MODEL_CONFIGS = [
    {
        "name": "toxic_bert",
        "model_id": "unitary/toxic-bert",
        "toxic_label_pattern": ["toxic", "TOXIC", "LABEL_1"],
        "nontoxic_label_pattern": ["non_toxic", "NON_TOXIC", "LABEL_0"],
    },
    {
        "name": "distilbert_toxic",
        "model_id": "martin-ha/toxic-comment-model",
        "toxic_label_pattern": ["toxic", "TOXIC", "LABEL_1"],
        "nontoxic_label_pattern": ["non_toxic", "NON_TOXIC", "LABEL_0"],
    },
    {
        "name": "roberta_toxicity",
        "model_id": "s-nlp/roberta_toxicity_classifier",
        "toxic_label_pattern": ["toxic", "TOXIC", "LABEL_1"],
        "nontoxic_label_pattern": ["neutral", "NEUTRAL", "LABEL_0"],
    },
    {
        "name": "dehatebert",
        "model_id": "Hate-speech-CNERG/dehatebert-mono-english",
        "toxic_label_pattern": ["hate_speech", "HATE_SPEECH", "LABEL_1"],
        "nontoxic_label_pattern": ["not_hate_speech", "NOT_HATE_SPEECH", "LABEL_0"],
    },
]


# ── Dataset loading ─────────────────────────────────────────────────────────────

def load_civil_comments(n_sample: int = 5000) -> Optional[tuple[list[str], np.ndarray]]:
    """Load google/civil_comments. Returns (texts, labels) where label=1 means toxic."""
    from datasets import load_dataset
    print("[dataset] Loading google/civil_comments...")
    try:
        ds = load_dataset("google/civil_comments", split="train")
        print(f"  civil_comments train size: {len(ds)}")
        # Reproducible sample
        indices = RNG.choice(len(ds), min(n_sample, len(ds)), replace=False)
        ds = ds.select(indices.tolist())
        texts = [str(row["text"]) for row in ds]
        # toxicity >= 0.5 -> toxic=1; <0.5 -> not-toxic=0 (C=1 in the framework)
        labels = np.array([1 if float(row["toxicity"]) >= 0.5 else 0 for row in ds])
        n_toxic = int(labels.sum())
        n_not_toxic = int((labels == 0).sum())
        print(f"  civil_comments: n={len(texts)}, toxic={n_toxic}, not_toxic={n_not_toxic}")
        return texts, labels
    except Exception as e:
        print(f"  civil_comments load FAILED: {e}")
        traceback.print_exc()
        return None


def load_toxigen(n_sample: int = 5000) -> Optional[tuple[list[str], np.ndarray]]:
    """Load skg/toxigen-data. toxicity_human is on 1-5 scale; >= 3.0 -> toxic."""
    from datasets import load_dataset
    print("[dataset] Loading skg/toxigen-data...")
    try:
        ds = load_dataset("skg/toxigen-data", split="train")
        print(f"  toxigen size: {len(ds)}")
        # Filter out rows with missing toxicity_human
        valid = [row for row in ds if row["toxicity_human"] is not None]
        if len(valid) > n_sample:
            idx = RNG.choice(len(valid), n_sample, replace=False)
            valid = [valid[i] for i in idx]
        texts = [str(row["text"]) for row in valid]
        # toxicity_human >= 3.0 (midpoint of 1-5) -> toxic
        labels = np.array([1 if float(row["toxicity_human"]) >= 3.0 else 0 for row in valid])
        n_toxic = int(labels.sum())
        n_not_toxic = int((labels == 0).sum())
        print(f"  toxigen: n={len(texts)}, toxic={n_toxic}, not_toxic={n_not_toxic}")
        return texts, labels
    except Exception as e:
        print(f"  toxigen load FAILED: {e}")
        traceback.print_exc()
        return None


def load_measuring_hate_speech(n_sample: int = 5000) -> Optional[tuple[list[str], np.ndarray]]:
    """Load ucberkeley-dlab/measuring-hate-speech.

    Aggregate per unique comment (multiple annotators), then:
    mean(hate_speech_score) > 0 -> toxic; <= 0 -> not-toxic.
    """
    from datasets import load_dataset
    print("[dataset] Loading ucberkeley-dlab/measuring-hate-speech...")
    try:
        ds = load_dataset("ucberkeley-dlab/measuring-hate-speech", split="train")
        print(f"  measuring-hate-speech size: {len(ds)}")

        # Aggregate by comment_id
        comment_scores: dict[int, list] = {}
        comment_texts: dict[int, str] = {}
        for row in ds:
            cid = row["comment_id"]
            if cid not in comment_scores:
                comment_scores[cid] = []
                comment_texts[cid] = row["text"]
            hs = row["hate_speech_score"]
            if hs is not None:
                comment_scores[cid].append(float(hs))

        # Build final arrays
        cids = [cid for cid, scores in comment_scores.items() if len(scores) > 0]
        if len(cids) > n_sample:
            chosen = RNG.choice(len(cids), n_sample, replace=False)
            cids = [cids[i] for i in chosen]

        texts = []
        labels = []
        for cid in cids:
            mean_score = np.mean(comment_scores[cid])
            texts.append(comment_texts[cid])
            labels.append(1 if mean_score > 0 else 0)

        labels = np.array(labels)
        n_toxic = int(labels.sum())
        n_not_toxic = int((labels == 0).sum())
        print(f"  measuring-hate-speech: n={len(texts)}, toxic={n_toxic}, not_toxic={n_not_toxic}")
        return texts, labels
    except Exception as e:
        print(f"  measuring-hate-speech load FAILED: {e}")
        traceback.print_exc()
        return None


# ── Model inference ─────────────────────────────────────────────────────────────

def is_toxic_label(label_str: str, toxic_patterns: list[str]) -> bool:
    """Check if a label string matches a toxic pattern (case-insensitive substring)."""
    label_lower = label_str.lower()
    return any(p.lower() in label_lower for p in toxic_patterns)


def run_classifier(model_cfg: dict, texts: list[str]) -> Optional[np.ndarray]:
    """Run a classifier on texts. Returns toxicity probability scores in [0,1] or None on failure."""
    from transformers import pipeline, AutoTokenizer

    model_id = model_cfg["model_id"]
    name = model_cfg["name"]
    print(f"\n[classifier] Loading {name} ({model_id})...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Use CPU for reliability — MPS has NaN/degenerate output issues with some toxicity models
        device_str = "cpu"
        print(f"  device: {device_str}")

        clf = pipeline(
            "text-classification",
            model=model_id,
            tokenizer=tokenizer,
            device=device_str,
            truncation=True,
            max_length=MAX_LEN,
        )

        scores = []
        n = len(texts)
        t0 = time.time()
        print(f"  running inference on {n} texts (batch={BATCH_SIZE})...")

        for start in range(0, n, BATCH_SIZE):
            batch = texts[start:start + BATCH_SIZE]
            # Truncate each text to avoid OOM on CPU
            batch = [t[:2000] for t in batch]
            try:
                results = clf(batch, batch_size=BATCH_SIZE)
            except Exception as e:
                print(f"  batch {start//BATCH_SIZE} error: {e}, falling back to single-item...")
                results = []
                for txt in batch:
                    try:
                        r = clf([txt[:500]])
                        results.extend(r)
                    except Exception:
                        # Neutral fallback score
                        results.append({"label": "LABEL_0", "score": 0.5})

            for r in results:
                label = r["label"]
                score = float(r["score"])
                # score is P(predicted_label). Convert to P(toxic).
                if is_toxic_label(label, model_cfg["toxic_label_pattern"]):
                    scores.append(score)
                else:
                    scores.append(1.0 - score)

            if (start // BATCH_SIZE) % 10 == 0:
                elapsed = time.time() - t0
                pct = min((start + BATCH_SIZE) / n * 100, 100)
                print(f"  progress: {min(start+BATCH_SIZE, n)}/{n} ({pct:.0f}%) | {elapsed:.0f}s")

        scores = np.array(scores)
        elapsed = time.time() - t0
        removal_rate = float((scores >= 0.5).mean())
        print(
            f"  done in {elapsed:.1f}s | "
            f"mean_score={scores.mean():.3f} std={scores.std():.3f} "
            f"removal_rate={removal_rate:.3f}"
        )

        # Degeneracy check: removal_rate < 1% or > 99% means degenerate model
        if removal_rate < 0.01 or removal_rate > 0.99:
            print(f"  WARNING: DEGENERATE model (removal_rate={removal_rate:.3f}). Marking failed.")
            return None

        return scores

    except Exception as e:
        print(f"  FAILED to load/run {name}: {e}")
        traceback.print_exc()
        return None


# ── Statistical utilities ───────────────────────────────────────────────────────

def bootstrap_fpr(
    D: np.ndarray,
    C_not_toxic: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
) -> tuple[float, float, float]:
    """FPR = P(D=1 | C_not_toxic=True) with bootstrap 95% CI.

    C_not_toxic: boolean array, True where text is NOT toxic (C=1 in framework).
    D: boolean array, True where classifier removes text.
    Returns: (fpr, ci_lo, ci_hi)
    """
    not_toxic_idx = np.where(C_not_toxic)[0]
    n_not_toxic = len(not_toxic_idx)
    if n_not_toxic == 0:
        return float("nan"), float("nan"), float("nan")

    n_false_removed = int(D[not_toxic_idx].sum())
    fpr = n_false_removed / n_not_toxic

    boot_fprs = []
    for _ in range(n_boot):
        sample = RNG.choice(not_toxic_idx, n_not_toxic, replace=True)
        boot_fprs.append(float(D[sample].mean()))

    ci_lo = float(np.percentile(boot_fprs, 2.5))
    ci_hi = float(np.percentile(boot_fprs, 97.5))
    return float(fpr), ci_lo, ci_hi


def manski_bounds(D: np.ndarray, C_not_toxic: np.ndarray) -> dict:
    """Compute Manski partial-identification bounds.

    Observable (deployment-visible):
        q = P(D=1) = overall removal rate (from moderation logs)
        a = P(C=1 | D=0) = not-toxic rate among KEPT (by sampling+labeling kept content)

    Unobservable:
        b = P(C=1 | D=1) = not-toxic rate among REMOVED (content is gone)

    Manski bound: theta in [0, q / (a*(1-q) + q)]
    Oracle theta: actual FPR (requires labels on removed content — unavailable in deployment)
    """
    n = len(D)
    q = float(D.mean())
    kept = ~D
    n_kept = int(kept.sum())

    if n_kept == 0:
        return {"error": "all texts removed"}

    # a = not-toxic rate among KEPT (observable — label a sample of kept content)
    a = float(C_not_toxic[kept].mean())

    denom = a * (1.0 - q) + q
    U = float(q / denom) if denom > 1e-12 else float("nan")

    # Oracle theta (needs labels on removed content — impossible in real deployment)
    n_not_toxic = int(C_not_toxic.sum())
    oracle_theta = (
        float((D & C_not_toxic).sum()) / n_not_toxic
        if n_not_toxic > 0
        else float("nan")
    )

    # b_true = not-toxic rate among REMOVED (oracle-only, unobservable in deployment)
    n_removed = int(D.sum())
    b_true = (
        float(C_not_toxic[D].mean())
        if n_removed > 0
        else float("nan")
    )

    oracle_in_bound = (
        bool(0.0 <= oracle_theta <= U + 1e-9)
        if (not np.isnan(oracle_theta) and not np.isnan(U))
        else False
    )

    return {
        "q_removal_rate": q,
        "a_not_toxic_among_kept": a,
        "b_true_not_toxic_among_removed_oracle_only": b_true,
        "manski_lower_bound": 0.0,
        "manski_upper_bound": U,
        "manski_bound_theta": [0.0, U],
        "oracle_theta": oracle_theta,
        "oracle_in_bound": oracle_in_bound,
        "n_total": n,
        "n_removed": n_removed,
        "n_kept": n_kept,
        "n_not_toxic": n_not_toxic,
        "note_deployment": (
            "In real deployment: q is observable from moderation logs, "
            "a is estimable by labeling a sample of kept content, "
            "b is unobservable (removed content is gone), "
            "oracle_theta requires labels on removed content and is unavailable."
        ),
    }


def auc_safe(y: np.ndarray, scores: np.ndarray) -> float:
    """AUC-ROC, returning nan if only one class present."""
    y = np.asarray(y)
    scores = np.asarray(scores)
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, scores))


def bootstrap_auc(
    y: np.ndarray,
    scores: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
) -> tuple[float, float]:
    """Bootstrap 95% CI for AUC (percentile method)."""
    y = np.asarray(y)
    scores = np.asarray(scores)
    aucs = []
    for _ in range(n_boot):
        idx = RNG.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            aucs.append(float(roc_auc_score(y[idx], scores[idx])))
    if not aucs:
        return float("nan"), float("nan")
    return float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


# ── Cross-classifier disagreement audit (Experiment C) ──────────────────────────

def cross_classifier_audit(
    target_name: str,
    target_D: np.ndarray,
    C_not_toxic: np.ndarray,
    other_scores: dict[str, np.ndarray],
) -> dict:
    """Mirror of S5 satellite experiment for content moderation.

    Among target classifier's removals (D=1):
        bad removals  = D=1 & C=1 (removed but not-toxic: false positives)
        good removals = D=1 & C=0 (removed and toxic: correct removals)

    Consensus-keep signal: fraction of OTHER classifiers that KEEP the text (score < 0.5).
    Higher consensus-keep => more likely to be a false positive (bad removal).

    AUC: does consensus-keep rank bad above good removals?
    Baseline: single best alternative classifier keep-score AUC.
    """
    removed = target_D.astype(bool)
    n_removed = int(removed.sum())
    bad = removed & C_not_toxic      # false positives (removed, truly not-toxic)
    good = removed & ~C_not_toxic    # true positives (removed, actually toxic)
    n_bad = int(bad.sum())
    n_good = int(good.sum())

    if n_bad < 3 or n_good < 3:
        return {
            "n_removed": n_removed,
            "n_bad_removals": n_bad,
            "n_good_removals": n_good,
            "note": f"too few bad ({n_bad}) or good ({n_good}) removals for AUC (need >= 3 each)",
        }

    other_names = list(other_scores.keys())
    if not other_names:
        return {"n_removed": n_removed, "n_bad_removals": n_bad, "note": "no other classifiers"}

    # Consensus keep: average fraction of other classifiers that keep the text
    keep_matrix = np.array([(other_scores[n] < 0.5).astype(float) for n in other_names])
    keep_votes = np.mean(keep_matrix, axis=0)  # shape (n_texts,)

    # Label array for AUC: among target's removals, 1=bad removal, 0=good removal
    lab = bad.astype(int)[removed]
    consensus_keep_removed = keep_votes[removed]

    auc_consensus = auc_safe(lab, consensus_keep_removed)
    ci_lo, ci_hi = bootstrap_auc(lab, consensus_keep_removed)

    # Operating point: flag if majority of panel keeps (consensus > 0.5)
    flag = removed & (keep_votes > 0.5)
    tp = int((flag & bad).sum())
    n_flagged = int(flag.sum())
    recall_at_majority = float(tp / n_bad) if n_bad > 0 else float("nan")
    precision_at_majority = float(tp / n_flagged) if n_flagged > 0 else float("nan")

    # Baseline: single classifier AUC (use keep-score = 1 - other_score)
    baseline_aucs: dict[str, float] = {}
    for oname in other_names:
        single_keep = 1.0 - other_scores[oname]  # higher = more likely to keep
        baseline_aucs[oname] = auc_safe(lab, single_keep[removed])

    valid_baselines = {k: v for k, v in baseline_aucs.items() if not np.isnan(v)}
    best_baseline_name = (
        max(valid_baselines, key=lambda k: valid_baselines[k])
        if valid_baselines
        else None
    )
    best_baseline_auc = valid_baselines[best_baseline_name] if best_baseline_name else float("nan")

    # Blind-spot: bad removals that ALL other classifiers also remove (consensus can't see them)
    all_also_remove = np.all(keep_matrix < 0.5, axis=0)  # True where all others also remove
    invisible = bad & all_also_remove
    n_invisible = int(invisible.sum())
    blind_spot_frac = float(n_invisible / n_bad) if n_bad > 0 else float("nan")
    recall_ceiling = float(1.0 - blind_spot_frac) if not np.isnan(blind_spot_frac) else float("nan")

    return {
        "n_removed": n_removed,
        "n_bad_removals": n_bad,
        "n_good_removals": n_good,
        "bad_rate_among_removals": float(n_bad / n_removed) if n_removed > 0 else float("nan"),
        "auc_consensus_keep": float(auc_consensus),
        "ci_consensus": [float(ci_lo), float(ci_hi)],
        "consensus_flag_recall": float(recall_at_majority),
        "consensus_flag_precision": float(precision_at_majority),
        "n_panel_classifiers": len(other_names),
        "best_single_baseline_auc": float(best_baseline_auc),
        "best_single_baseline_name": str(best_baseline_name) if best_baseline_name else None,
        "per_single_baseline_auc": {k: float(v) for k, v in baseline_aucs.items()},
        "n_invisible_to_consensus": n_invisible,
        "blind_spot_frac": float(blind_spot_frac),
        "recall_ceiling": float(recall_ceiling),
    }


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("OPTION C — CONTENT MODERATION DOMAIN EXPERIMENT")
    print("=" * 70)
    print(f"Results -> {RESULTS_PATH}")
    print()

    # ── 1. Load datasets ────────────────────────────────────────────────────────
    datasets_loaded: dict[str, tuple[list[str], np.ndarray]] = {}

    civil = load_civil_comments(n_sample=5000)
    if civil is not None:
        datasets_loaded["civil_comments"] = civil

    toxigen = load_toxigen(n_sample=5000)
    if toxigen is not None:
        datasets_loaded["toxigen"] = toxigen

    mhs = load_measuring_hate_speech(n_sample=5000)
    if mhs is not None:
        datasets_loaded["measuring_hate_speech"] = mhs

    if not datasets_loaded:
        print("ERROR: No datasets loaded. Exiting.")
        sys.exit(1)

    print(f"\n[datasets] {len(datasets_loaded)} loaded: {list(datasets_loaded.keys())}")

    # ── 2. Run classifiers on each dataset ─────────────────────────────────────
    print("\n" + "=" * 70)
    print("LOADING CLASSIFIERS AND RUNNING INFERENCE")
    print("=" * 70)

    # classifier_scores[ds_name][clf_name] = np.ndarray of P(toxic) scores
    classifier_scores: dict[str, dict[str, np.ndarray]] = {ds: {} for ds in datasets_loaded}
    classifier_metadata: dict[str, dict] = {}

    for cfg in MODEL_CONFIGS:
        name = cfg["name"]
        succeeded_on = []
        failed_on = []

        for ds_name, (texts, labels) in datasets_loaded.items():
            print(f"\n--- {name} on {ds_name} ({len(texts)} texts) ---")
            scores = run_classifier(cfg, texts)
            if scores is not None:
                classifier_scores[ds_name][name] = scores
                succeeded_on.append(ds_name)
            else:
                failed_on.append(ds_name)

        classifier_metadata[name] = {
            "model_id": cfg["model_id"],
            "succeeded_on": succeeded_on,
            "failed_on": failed_on,
            "status": "ok" if succeeded_on else "failed",
        }

    print("\n\nCLASSIFIER SUMMARY:")
    for ds_name in datasets_loaded:
        clfs = list(classifier_scores[ds_name].keys())
        print(f"  {ds_name}: {len(clfs)} classifiers: {clfs}")

    # ── 3. Build output structure ───────────────────────────────────────────────
    out: dict = {
        "metadata": {
            "date": "2026-06-27",
            "framework": "content moderation as irreversible gatekeeper (Option C)",
            "estimand": "theta = FPR = P(D=1 | C=1) = P(removed | truly not-toxic)",
            "mnar_structure": (
                "D=1 (removal) correlates with content toxicity, so removed content "
                "is MNAR — its distribution != retained content distribution. "
                "FPR is unidentifiable from retained data alone."
            ),
            "lower_bound_note": (
                "Manski lower bound = 0 always: retained data cannot certify "
                "that ANY false removals occurred."
            ),
            "datasets": {},
            "classifiers": classifier_metadata,
        },
        "experiment_A_fpr": {},
        "experiment_B_manski": {},
        "experiment_C_audit": {},
    }

    for ds_name, (texts, labels) in datasets_loaded.items():
        C_not_toxic = (labels == 0)
        out["metadata"]["datasets"][ds_name] = {
            "n_total": len(texts),
            "n_toxic_ground_truth": int(labels.sum()),
            "n_not_toxic_ground_truth": int(C_not_toxic.sum()),
            "prevalence_not_toxic": float(C_not_toxic.mean()),
        }

    # ── Experiment A: FPR + Bootstrap CIs ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("EXPERIMENT A: FPR with Bootstrap CIs")
    print("=" * 70)
    for ds_name, (texts, labels) in datasets_loaded.items():
        C_not_toxic = (labels == 0)
        out["experiment_A_fpr"][ds_name] = {}
        for clf_name, scores in classifier_scores[ds_name].items():
            D = (scores >= 0.5)
            fpr, ci_lo, ci_hi = bootstrap_fpr(D, C_not_toxic)
            n_not_toxic = int(C_not_toxic.sum())
            n_false_removed = int((D & C_not_toxic).sum())
            q = float(D.mean())
            result = {
                "fpr": float(fpr),
                "ci_95_lo": float(ci_lo),
                "ci_95_hi": float(ci_hi),
                "n_not_toxic": n_not_toxic,
                "n_false_removed": n_false_removed,
                "overall_removal_rate_q": q,
                "n_total": len(texts),
                "threshold": 0.5,
                "n_bootstrap": N_BOOTSTRAP,
            }
            out["experiment_A_fpr"][ds_name][clf_name] = result
            print(
                f"  {ds_name}/{clf_name}: "
                f"FPR={fpr:.3f} [{ci_lo:.3f},{ci_hi:.3f}]  "
                f"(n_not_toxic={n_not_toxic}, n_false_removed={n_false_removed}, q={q:.3f})"
            )

    # ── Experiment B: Manski Bounds ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("EXPERIMENT B: Manski Partial-Identification Bounds")
    print("=" * 70)
    for ds_name, (texts, labels) in datasets_loaded.items():
        C_not_toxic = (labels == 0)
        out["experiment_B_manski"][ds_name] = {}
        for clf_name, scores in classifier_scores[ds_name].items():
            D = (scores >= 0.5)
            bounds = manski_bounds(D, C_not_toxic)
            out["experiment_B_manski"][ds_name][clf_name] = bounds
            if "manski_upper_bound" in bounds:
                print(
                    f"  {ds_name}/{clf_name}: "
                    f"q={bounds['q_removal_rate']:.3f} "
                    f"a={bounds['a_not_toxic_among_kept']:.3f} "
                    f"| theta in [0, {bounds['manski_upper_bound']:.3f}] "
                    f"oracle={bounds['oracle_theta']:.3f} "
                    f"({'IN' if bounds['oracle_in_bound'] else 'OUT'})"
                )

    # ── Experiment C: Cross-Classifier Disagreement Audit ──────────────────────
    print("\n" + "=" * 70)
    print("EXPERIMENT C: Cross-Classifier Disagreement Audit")
    print("=" * 70)
    for ds_name, (texts, labels) in datasets_loaded.items():
        C_not_toxic = (labels == 0)
        clf_names = list(classifier_scores[ds_name].keys())
        out["experiment_C_audit"][ds_name] = {}

        if len(clf_names) < 2:
            msg = f"only {len(clf_names)} classifier(s) — need >= 2 for audit"
            print(f"  {ds_name}: {msg}")
            out["experiment_C_audit"][ds_name]["_note"] = msg
            continue

        for target_name in clf_names:
            target_scores = classifier_scores[ds_name][target_name]
            target_D = (target_scores >= 0.5)
            other_scores = {
                n: classifier_scores[ds_name][n]
                for n in clf_names
                if n != target_name
            }

            audit = cross_classifier_audit(target_name, target_D, C_not_toxic, other_scores)
            out["experiment_C_audit"][ds_name][target_name] = audit

            if "auc_consensus_keep" in audit:
                ci = audit["ci_consensus"]
                print(
                    f"  {ds_name} | {target_name}: "
                    f"removed={audit['n_removed']} bad={audit['n_bad_removals']} "
                    f"consensus_AUC={audit['auc_consensus_keep']:.3f} [{ci[0]:.3f},{ci[1]:.3f}] "
                    f"best_single={audit['best_single_baseline_auc']:.3f}({audit['best_single_baseline_name']}) "
                    f"recall@maj={audit['consensus_flag_recall']:.3f} "
                    f"blindspot={audit['blind_spot_frac']:.3f}"
                )
            else:
                print(f"  {ds_name} | {target_name}: {audit.get('note', 'no result')}")

    # ── Save ────────────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[DONE] Results -> {RESULTS_PATH}")

    # ── Final summary tables ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY TABLES")
    print("=" * 70)

    print("\nEXPERIMENT A — FPR TABLE:")
    print(f"  {'dataset':<26} {'classifier':<22} {'FPR':>6} {'95% CI':>14} {'q':>6}")
    print("  " + "-" * 78)
    for ds_name in out["experiment_A_fpr"]:
        for clf_name, r in out["experiment_A_fpr"][ds_name].items():
            if "fpr" in r:
                print(
                    f"  {ds_name:<26} {clf_name:<22} "
                    f"{r['fpr']:.3f} "
                    f"[{r['ci_95_lo']:.3f},{r['ci_95_hi']:.3f}] "
                    f"{r['overall_removal_rate_q']:.3f}"
                )

    print("\nEXPERIMENT B — MANSKI BOUNDS:")
    print(f"  {'dataset':<26} {'classifier':<22} {'q':>5} {'a':>5} {'U':>5} {'oracle':>7} {'in_bound':>9}")
    print("  " + "-" * 82)
    for ds_name in out["experiment_B_manski"]:
        for clf_name, r in out["experiment_B_manski"][ds_name].items():
            if "manski_upper_bound" in r:
                print(
                    f"  {ds_name:<26} {clf_name:<22} "
                    f"{r['q_removal_rate']:.3f} "
                    f"{r['a_not_toxic_among_kept']:.3f} "
                    f"{r['manski_upper_bound']:.3f} "
                    f"{r['oracle_theta']:.3f}   "
                    f"{'YES' if r['oracle_in_bound'] else 'NO':>9}"
                )

    print("\nEXPERIMENT C — CROSS-CLASSIFIER AUDIT AUC:")
    print(f"  {'dataset':<26} {'target':<22} {'consAUC':>8} {'CI':>14} {'single':>7} {'recall':>7}")
    print("  " + "-" * 90)
    for ds_name in out["experiment_C_audit"]:
        for clf_name, r in out["experiment_C_audit"][ds_name].items():
            if "auc_consensus_keep" in r:
                ci = r["ci_consensus"]
                print(
                    f"  {ds_name:<26} {clf_name:<22} "
                    f"{r['auc_consensus_keep']:.3f}    "
                    f"[{ci[0]:.3f},{ci[1]:.3f}] "
                    f"{r['best_single_baseline_auc']:.3f}   "
                    f"{r['consensus_flag_recall']:.3f}"
                )


if __name__ == "__main__":
    main()
