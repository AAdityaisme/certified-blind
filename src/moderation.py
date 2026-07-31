"""Content-moderation domain loader (civil_comments, cached) for the cross-domain
replication of the satellite identifiability/targeted-suppression results.

Gatekeeper mapping (parallel to satellite EO triage):
    remove (D=1)  <-> discard/flag-as-cloud
    truly non-toxic (C=0)  <-> clear scene
    false-removal rate on a slice  <-> false-discard rate on clear-snow
    targeted slice  <-> identity-term-bearing comments (Dixon et al. 2018 method)

No per-identity labels needed: a "slice" is comments whose text contains an identity term
(word-boundary, case-insensitive). This is the standard identity-term-bias construction.
"""

from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
from datasets import load_dataset

TOX_THRESH = 0.5   # civil_comments toxicity is a fraction of annotators; >=0.5 = toxic

# Standard identity-term slices (Dixon 2018 / Borkan 2019 style). Grouped, neutral set.
IDENTITY_TERMS = {
    "muslim": r"\bmuslims?\b|\bislam(ic)?\b",
    "jewish": r"\bjews?\b|\bjewish\b",
    "christian": r"\bchristians?\b|\bchristianity\b",
    "black": r"\bblack\b|\bafrican[- ]american\b",
    "white": r"\bwhite\b|\bcaucasian\b",
    "gay": r"\bgay\b|\blesbian\b|\bhomosexual\b",
    "women": r"\bwomen\b|\bwoman\b|\bfemale\b",
    "men": r"\bmen\b|\bman\b|\bmale\b",
}


@lru_cache(maxsize=4)
def load_civil(n_train: int = 200_000, n_test: int = 60_000, seed: int = 42):
    """Return (train_texts, train_tox, test_texts, test_tox) as numpy arrays.
    tox is binary (toxicity >= TOX_THRESH). Uses cached google/civil_comments."""
    tr = load_dataset("google/civil_comments", split=f"train[:{n_train}]")
    te = load_dataset("google/civil_comments", split=f"test[:{n_test}]")
    tr_text = np.array(tr["text"], dtype=object)
    te_text = np.array(te["text"], dtype=object)
    tr_tox = (np.array(tr["toxicity"], dtype=np.float32) >= TOX_THRESH)
    te_tox = (np.array(te["toxicity"], dtype=np.float32) >= TOX_THRESH)
    return tr_text, tr_tox, te_text, te_tox


def slice_mask(texts: np.ndarray, term: str) -> np.ndarray:
    """Boolean mask: which texts mention the identity term (word-boundary, case-insensitive)."""
    pat = re.compile(IDENTITY_TERMS[term], re.IGNORECASE)
    return np.array([bool(pat.search(t)) for t in texts], dtype=bool)


def all_slice_masks(texts: np.ndarray) -> dict:
    return {term: slice_mask(texts, term) for term in IDENTITY_TERMS}
