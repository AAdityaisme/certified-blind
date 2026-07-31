"""Independently verify the reviewers' CRITICAL claims (don't trust, measure).

A) C3/C2 mechanism: is the code-fence SIV / cost-blowup a StandardScaler
   artifact (rare feature -> huge z -> sigmoid saturation) or a learned rule?
   Measure has_code_fence rate, scaler z, and SIV/shift under Standard vs Robust
   vs no scaler, with and without the has_code_fence feature.
B) Label validity: are RouterBench scores actually binary? Count non-binary and
   boundary cells.
C) IS pairs: what fraction are intra-eval (same benchmark)?
D) tfidf SIV=0: is it a tokenizer no-op (cosine ~1 between original/perturbed)?
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import features as feat  # noqa: E402
import perturb as P  # noqa: E402
import routerbench as rb  # noqa: E402

SEED = 0


def section(t): print(f"\n{'='*70}\n{t}\n{'='*70}")


def main():
    df = rb.load_labeled()
    texts = df["prompt"].tolist()
    y = df["route_premium"].to_numpy()
    X = feat.surface_feature_matrix(texts)
    names = list(X.columns)
    Xv = X.to_numpy()
    tr, te = train_test_split(np.arange(len(y)), test_size=0.25, random_state=SEED, stratify=y)

    # ---------- A: has_code_fence + scaler mechanism ----------
    section("A) has_code_fence rate + scaler sensitivity of SIV / shift")
    cf = X["has_code_fence"].to_numpy()
    print(f"has_code_fence: overall rate={cf.mean():.6f}  train rate={cf[tr].mean():.6f}  "
          f"n_train_fired={int(cf[tr].sum())}/{len(tr)}")
    sc = StandardScaler().fit(Xv[tr])
    j = names.index("has_code_fence")
    z_when_1 = (1.0 - sc.mean_[j]) / sc.scale_[j]
    print(f"StandardScaler z-score when has_code_fence=1: {z_when_1:.1f}")
    ws = names.index("whitespace_ratio")
    print(f"(for contrast) whitespace_ratio mean={sc.mean_[ws]:.3f} scale={sc.scale_[ws]:.3f}")

    te_texts = [texts[i] for i in te]
    pert = {p: P.apply_perturbation(te_texts, p) for p in ["code_fence", "whitespace"]}

    def run(scaler_kind, drop_codefence=False):
        cols = [c for c in names if not (drop_codefence and c == "has_code_fence")]
        Xc = X[cols].to_numpy()
        scaler = {"standard": StandardScaler(), "robust": RobustScaler(), "none": "passthrough"}[scaler_kind]
        clf = make_pipeline(StandardScaler() if scaler == "passthrough" and False else scaler,
                            LogisticRegression(max_iter=2000)) if scaler != "passthrough" else \
            make_pipeline(LogisticRegression(max_iter=2000))
        clf.fit(Xc[tr], y[tr])
        base = clf.predict(Xc[te])
        out = {"shift_route_frac_clean": float(base.mean())}
        for p in pert:
            # recompute features on perturbed test text
            Xp = feat.surface_feature_matrix(pert[p])[cols].to_numpy()
            pp = clf.predict(Xp)
            out[f"SIV_{p}"] = float(np.mean(pp != base))
            out[f"route_frac_{p}"] = float(pp.mean())
        return out

    for kind in ["standard", "robust", "none"]:
        r = run(kind)
        print(f"  scaler={kind:9s} clean_route={r['shift_route_frac_clean']:.3f} | "
              f"code_fence SIV={r['SIV_code_fence']:.3f} route={r['route_frac_code_fence']:.3f} | "
              f"whitespace SIV={r['SIV_whitespace']:.3f} route={r['route_frac_whitespace']:.3f}")
    r = run("standard", drop_codefence=True)
    print(f"  standard, NO has_code_fence feature: code_fence SIV={r['SIV_code_fence']:.3f} "
          f"whitespace SIV={r['SIV_whitespace']:.3f}")

    # ---------- B: label validity (scores binary?) ----------
    section("B) Are RouterBench scores binary? (threshold=0.5 silently applied)")
    raw = pd.read_pickle(rb.find_routerbench_file())
    models = rb.detect_model_columns(raw)
    S = raw[models].apply(pd.to_numeric, errors="coerce")
    allvals = S.to_numpy().ravel()
    allvals = allvals[~np.isnan(allvals)]
    nonbinary = np.mean((allvals != 0.0) & (allvals != 1.0))
    boundary = np.mean((allvals > 0.4) & (allvals < 0.6))
    print(f"cells total={allvals.size}  non-binary fraction={nonbinary:.4f}  "
          f"in (0.4,0.6)={boundary:.4f}")
    uniq = np.unique(np.round(allvals, 3))
    print(f"unique score values (rounded): {uniq[:20]}{' ...' if len(uniq)>20 else ''}  (n={len(uniq)})")
    # which evals are non-binary
    nb_by_eval = (raw.assign(_nb=((S != 0) & (S != 1)).any(axis=1))
                  .groupby("eval_name")["_nb"].mean().sort_values(ascending=False))
    print("evals with most non-binary rows:")
    print(nb_by_eval.head(8).to_string())

    # ---------- C: IS pair eval composition ----------
    section("C) IS matched pairs: intra-eval fraction?")
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler as SS
    evals = df["eval_name"].to_numpy()
    surf_te = SS().fit(Xv[tr]).transform(Xv[te])
    yte = y[te]; ev_te = evals[te]
    pos = np.where(yte == 1)[0]; neg = np.where(yte == 0)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(surf_te[neg])
    dist, jj = nn.kneighbors(surf_te[pos]); dist = dist[:, 0]; negm = neg[jj[:, 0]]
    cal = np.percentile(dist, 25); keep = dist <= cal
    pe, ne = ev_te[pos[keep]], ev_te[negm[keep]]
    intra = np.mean(pe == ne)
    print(f"matched pairs={keep.sum()}  intra-eval fraction={intra:.3f}")
    print("top eval of matched positives:", pd.Series(pe).value_counts().head(5).to_dict())

    # ---------- D: tfidf no-op check ----------
    section("D) Is tfidf SIV=0 a tokenizer no-op?")
    from sklearn.feature_extraction.text import TfidfVectorizer
    samp = te_texts[:2000]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=50000).fit(samp)
    A = vec.transform(samp)
    for p in ["code_fence", "whitespace"]:
        B = vec.transform(P.apply_perturbation(samp, p))
        cos = (A.multiply(B)).sum(axis=1).A1 / (
            np.sqrt(A.multiply(A).sum(axis=1).A1) * np.sqrt(B.multiply(B).sum(axis=1).A1) + 1e-9)
        print(f"  {p:11s} mean cosine(original, perturbed) = {cos.mean():.4f}  "
              f"(1.0 => tokenizer ignores the change => SIV=0 is vacuous)")


if __name__ == "__main__":
    main()
