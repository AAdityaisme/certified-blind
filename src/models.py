"""Unified router (gatekeeper) wrappers.

Every router exposes fit(texts, y) / predict(texts) / proba(texts) and owns its
own featurization, so callers pass *raw prompt strings* uniformly — essential
for the intervention tests, which predict on perturbed text without the caller
knowing each model's feature representation.

  MajorityRouter  - predicts the base-rate class (floor)
  SurfaceRouter   - surface lexical features -> sklearn head (no semantics)
  TfidfRouter     - char/word n-grams -> LogReg (richer lexical, no semantics)
  SemanticRouter  - MiniLM sentence embeddings -> LogReg (intent-aware contrast)
"""

from __future__ import annotations

import os
import sys

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import features as feat  # noqa: E402


class MajorityRouter:
    def fit(self, texts, y):
        self.cls_ = int(round(float(np.mean(y))))
        self.rate_ = float(np.mean(y))
        return self

    def predict(self, texts):
        return np.full(len(texts), self.cls_)

    def proba(self, texts):
        return np.full(len(texts), self.rate_)


class SurfaceRouter:
    """Surface lexical feature set -> a sklearn classifier head.

    scaler: 'standard' (default, for reproducibility of earlier runs) or 'robust'
    (the audit's fix — RobustScaler is insensitive to rare-feature OOD blowups).
    """

    def __init__(self, head="logreg", scaler="standard"):
        self.head = head
        self.scaler = scaler

    def _new_head(self):
        from sklearn.preprocessing import RobustScaler
        sc = RobustScaler() if self.scaler == "robust" else StandardScaler()
        if self.head == "logreg":
            return make_pipeline(sc, LogisticRegression(max_iter=2000))
        if self.head == "hgb":
            return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08)
        raise ValueError(self.head)

    def _X(self, texts):
        return feat.surface_feature_matrix(texts).to_numpy()

    def fit(self, texts, y):
        self.clf_ = self._new_head()
        self.clf_.fit(self._X(texts), y)
        return self

    def predict(self, texts):
        return self.clf_.predict(self._X(texts))

    def proba(self, texts):
        return self.clf_.predict_proba(self._X(texts))[:, 1]


class TfidfRouter:
    def __init__(self, ngram=(1, 2), min_df=3, max_features=50000):
        self.kw = dict(ngram_range=ngram, min_df=min_df, max_features=max_features)

    def fit(self, texts, y):
        self.clf_ = make_pipeline(
            TfidfVectorizer(**self.kw), LogisticRegression(max_iter=2000))
        self.clf_.fit(list(texts), y)
        return self

    def predict(self, texts):
        return self.clf_.predict(list(texts))

    def proba(self, texts):
        return self.clf_.predict_proba(list(texts))[:, 1]


_ST_MODELS: dict = {}


def _encoder(model_name="all-MiniLM-L6-v2"):
    if model_name not in _ST_MODELS:
        from sentence_transformers import SentenceTransformer
        _ST_MODELS[model_name] = SentenceTransformer(model_name)
    return _ST_MODELS[model_name]


def semantic_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


_ENC_CACHE: dict[str, dict[str, np.ndarray]] = {}  # model_name -> {text -> vec}


class SemanticRouter:
    """Sentence embeddings -> LogReg. The intent-aware contrast (not a 'cure').

    Embeddings are cached per (model, exact text) so repeated encodes (across
    seeds; base test reused across conditions) cost nothing. Cache is keyed by
    model_name so multiple embedders don't collide.
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name

    def _X(self, texts):
        texts = list(texts)
        cache = _ENC_CACHE.setdefault(self.model_name, {})
        missing = [t for t in texts if t not in cache]
        if missing:
            uniq = list(dict.fromkeys(missing))
            enc = _encoder(self.model_name)
            vecs = np.asarray(enc.encode(uniq, batch_size=64, show_progress_bar=False,
                                         normalize_embeddings=True))
            for t, v in zip(uniq, vecs):
                cache[t] = v
        return np.vstack([cache[t] for t in texts])

    def fit(self, texts, y):
        self.clf_ = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        self.clf_.fit(self._X(texts), y)
        return self

    def predict(self, texts):
        return self.clf_.predict(self._X(texts))

    def proba(self, texts):
        return self.clf_.predict_proba(self._X(texts))[:, 1]


_SEM_SHORT = {"all-MiniLM-L6-v2": "semantic_logreg",
              "all-mpnet-base-v2": "semantic_mpnet",
              "BAAI/bge-small-en-v1.5": "semantic_bge"}


def build_routers(include_semantic: bool | None = None,
                  semantic_models=("all-MiniLM-L6-v2",)) -> dict:
    """Return name -> zero-arg factory producing a fresh router.

    semantic_models: which sentence-encoders to include as semantic routers.
    Default = MiniLM only; pass extra (mpnet/bge) for the robustness check.
    """
    if include_semantic is None:
        include_semantic = semantic_available()
    routers = {
        "majority": lambda: MajorityRouter(),
        "surface_logreg": lambda: SurfaceRouter("logreg"),
        "surface_hgb": lambda: SurfaceRouter("hgb"),
        "tfidf_logreg": lambda: TfidfRouter(),
    }
    if include_semantic:
        for mn in semantic_models:
            name = _SEM_SHORT.get(mn, "semantic_" + mn.split("/")[-1])
            routers[name] = (lambda m=mn: SemanticRouter(m))
    return routers
