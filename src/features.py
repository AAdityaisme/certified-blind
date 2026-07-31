"""Surface-form feature extraction for the routing gatekeeper.

These are *surface lexical* features only: length, formatting flags, character
ratios. No semantics, no embeddings. This is deliberately the feature set a
production LLM router would compute cheaply per-prompt, and is
the object of study: how far does pure surface form get you on the stated metric?
"""

from __future__ import annotations

import re
import string
from functools import lru_cache

import numpy as np
import pandas as pd

_CODE_FENCE = re.compile(r"```")
_URL = re.compile(r"https?://|www\.")
_JSON_BRACE = re.compile(r"[{}\[\]]")
_MATH = re.compile(r"[=+\-*/^%<>]|\\frac|\\sum|\\int")
_SENTENCE = re.compile(r"[.!?]+")
_PUNCT = set(string.punctuation)

# Surface feature names, in stable column order.
FEATURE_NAMES = [
    "n_tokens",
    "n_chars",
    "n_words",
    "n_sentences",
    "avg_words_per_sentence",
    "has_code_fence",
    "digit_ratio",
    "non_ascii_ratio",
    "punct_density",
    "uppercase_ratio",
    "has_url",
    "has_json_braces",
    "has_math",
    "whitespace_ratio",
]


@lru_cache(maxsize=1)
def _encoder():
    """tiktoken encoder, lazily loaded (cl100k_base ~ GPT-3.5/4 family)."""
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def surface_features(text: str) -> dict[str, float]:
    """Compute the surface feature dict for a single prompt string."""
    text = text or ""
    n_chars = len(text)
    words = text.split()
    n_words = len(words)
    sentences = [s for s in _SENTENCE.split(text) if s.strip()]
    n_sentences = max(len(sentences), 1)
    n_digits = sum(c.isdigit() for c in text)
    n_non_ascii = sum(ord(c) > 127 for c in text)
    n_punct = sum(c in _PUNCT for c in text)
    n_upper = sum(c.isupper() for c in text)
    n_alpha = sum(c.isalpha() for c in text)
    n_ws = sum(c.isspace() for c in text)

    try:
        # disallowed_special=() so prompts containing literal "<|endoftext|>" encode as text
        n_tokens = len(_encoder().encode(text, disallowed_special=()))
    except Exception:
        n_tokens = n_words  # fallback if tiktoken unavailable

    return {
        "n_tokens": float(n_tokens),
        "n_chars": float(n_chars),
        "n_words": float(n_words),
        "n_sentences": float(n_sentences),
        "avg_words_per_sentence": _safe_div(n_words, n_sentences),
        "has_code_fence": float(bool(_CODE_FENCE.search(text))),
        "digit_ratio": _safe_div(n_digits, n_chars),
        "non_ascii_ratio": _safe_div(n_non_ascii, n_chars),
        "punct_density": _safe_div(n_punct, n_chars),
        "uppercase_ratio": _safe_div(n_upper, n_alpha),
        "has_url": float(bool(_URL.search(text))),
        "has_json_braces": float(bool(_JSON_BRACE.search(text))),
        "has_math": float(bool(_MATH.search(text))),
        "whitespace_ratio": _safe_div(n_ws, n_chars),
    }


def surface_feature_matrix(texts) -> pd.DataFrame:
    """Vectorize a sequence of prompts into the surface feature DataFrame."""
    rows = [surface_features(t) for t in texts]
    return pd.DataFrame(rows, columns=FEATURE_NAMES).astype(np.float64)


if __name__ == "__main__":
    demo = [
        "What is 2+2?",
        "```python\ndef f(x):\n    return x**2\n```\nExplain this code.",
        "Summarize the geopolitical implications of the 1648 Peace of Westphalia.",
    ]
    print(surface_feature_matrix(demo).to_string())
