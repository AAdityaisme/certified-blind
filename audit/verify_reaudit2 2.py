"""Verify reaudit2's two CRITICAL claims independently (it used only 2 tool calls).

A. Land-cover composition of the clear&bright / clear&snow-bare subsets — how many
   are ACTUALLY snow (ESA WorldCover LC=70) vs bare (60)?
B. RouteLLM: is the routing signal SURFACE FORM or task-content vocabulary?
   Compare length_only (pure surface) vs char-ngram tfidf (formatting) vs word
   tfidf (content), and print word-tfidf top features.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402
import features as feat  # noqa: E402
import routellm as rl  # noqa: E402

META = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsen12", "test", "metadata.csv")
LC_NAMES = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built",
            60: "bare/sparse", 70: "snow/ice", 80: "water", 90: "wetland", 100: "moss"}


def section(t): print(f"\n{'='*68}\n{t}\n{'='*68}")


def main():
    # ---------- A: land-cover composition ----------
    section("A) Land-cover composition of S2 subsets")
    df = cs.build_features()
    lc = df["land_cover"].to_numpy()
    cf = df["cloud_frac"].to_numpy()
    clear = cf < 0.10
    brightq = df["brightness"].to_numpy() >= np.percentile(df["brightness"], 75)
    for label, mask in [("clear & bright(top25%)", clear & brightq),
                        ("clear & LC in {60,70}", clear & np.isin(lc, [60, 70]))]:
        comp = pd.Series(lc[mask]).map(lambda c: f"{c}:{LC_NAMES.get(c, c)}").value_counts()
        print(f"  {label}  n={int(mask.sum())}: {comp.to_dict()}")
    print(f"  ACTUAL snow (LC=70) clear patches: {int((clear & (lc==70)).sum())}")
    print(f"  ACTUAL bare (LC=60) clear patches: {int((clear & (lc==60)).sum())}")

    # ---------- B: surface vs content on RouteLLM ----------
    section("B) RouteLLM — is the signal surface form or task content?")
    d = rl.load_labeled()
    # subsample for speed
    d = d.sample(n=30000, random_state=0).reset_index(drop=True)
    y = d["route_premium"].to_numpy()
    texts = d["prompt"].tolist()
    tr, te = train_test_split(np.arange(len(y)), test_size=0.25, random_state=0, stratify=y)
    Xtr = [texts[i] for i in tr]; Xte = [texts[i] for i in te]

    # length only (pure surface, content-free)
    tok = feat.surface_feature_matrix(texts)["n_tokens"].to_numpy().reshape(-1, 1)
    clf = make_pipeline(RobustScaler(), LogisticRegression(max_iter=1000)).fit(tok[tr], y[tr])
    auc_len = roc_auc_score(y[te], clf.predict_proba(tok[te])[:, 1])

    # full surface set (formatting, no vocabulary)
    Xs = feat.surface_feature_matrix(texts).to_numpy()
    clf = make_pipeline(RobustScaler(), LogisticRegression(max_iter=2000)).fit(Xs[tr], y[tr])
    auc_surf = roc_auc_score(y[te], clf.predict_proba(Xs[te])[:, 1])

    # char-ngram tfidf (sub-word / formatting; minimal content words)
    cv = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=5, max_features=50000),
                       LogisticRegression(max_iter=2000)).fit(Xtr, y[tr])
    auc_char = roc_auc_score(y[te], cv.predict_proba(Xte)[:, 1])

    # word tfidf (content vocabulary) + top features
    wv = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_features=50000)
    Wtr = wv.fit_transform(Xtr)
    wlr = LogisticRegression(max_iter=2000).fit(Wtr, y[tr])
    auc_word = roc_auc_score(y[te], wlr.predict_proba(wv.transform(Xte))[:, 1])
    names = np.array(wv.get_feature_names_out())
    top = names[np.argsort(wlr.coef_[0])[-12:][::-1]]

    print(f"  length_only (pure surface)   AUC={auc_len:.3f}")
    print(f"  full surface set (formatting) AUC={auc_surf:.3f}")
    print(f"  char-ngram tfidf (formatting) AUC={auc_char:.3f}")
    print(f"  word tfidf (content vocab)    AUC={auc_word:.3f}")
    print(f"  word tfidf TOP features (push toward 'needs GPT-4'): {list(top)}")
    print("\n  READ: length_only is content-free. If it is well above 0.5, the surface-form")
    print("  claim stands regardless of word-tfidf using content vocabulary.")


if __name__ == "__main__":
    main()
