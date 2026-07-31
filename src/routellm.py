"""Load RouteLLM gpt4_judge_battles (Ong et al. 2024, arXiv:2406.18665).

The decisive *homogeneous* routing substrate: 109,101 GPT-4-vs-Mixtral battles on
Chatbot-Arena/Nectar prompts, GPT-4-judged. No sub-benchmarks => no eval-identity
confound — the clean test of whether prompt surface form predicts "needs the
strong model" at all.

Self-contained: a cleaned copy is cached IN-REPO at data/routellm/ so the project
folder has no external dependencies (first call fetches from HF + saves locally).

Label route_premium = 1 iff GPT-4 (model_a) strictly wins (base rate ~0.093).
"""

from __future__ import annotations

import ast
import os

import pandas as pd

LOCAL = os.path.join(os.path.dirname(__file__), "..", "data", "routellm",
                     "gpt4_judge_battles_clean.parquet")


def _strip_surrogates(s: str) -> str:
    return "".join(ch for ch in s if not 0xD800 <= ord(ch) <= 0xDFFF)


def _coerce_prompt(x) -> str:
    if isinstance(x, (list, tuple)):
        s = str(x[0]) if len(x) else ""
    elif isinstance(x, str) and x.startswith("["):
        try:
            v = ast.literal_eval(x)
            s = str(v[0]) if isinstance(v, (list, tuple)) and v else x
        except Exception:
            s = x
    else:
        s = str(x)
    return _strip_surrogates(s)


def _load_clean() -> pd.DataFrame:
    """Cleaned frame: prompt (str), route_premium, tie. Cached in-repo."""
    if os.path.exists(LOCAL):
        return pd.read_parquet(LOCAL)
    from datasets import load_dataset
    df = load_dataset("routellm/gpt4_judge_battles", split="train").to_pandas()
    assert df["model_a"].str.contains("gpt-4").all(), "model_a expected GPT-4"
    clean = pd.DataFrame({
        "prompt": pd.Series([_coerce_prompt(p) for p in df["prompt"].tolist()], dtype=object),
        "route_premium": (df["winner_model_a"] == 1).astype(int).values,
        "tie": (df["winner_tie"] == 1).astype(int).values,
    })
    os.makedirs(os.path.dirname(LOCAL), exist_ok=True)
    clean.to_parquet(LOCAL)
    return clean


def load_labeled() -> pd.DataFrame:
    out = _load_clean()
    out = out[out["prompt"].str.len() > 0].reset_index(drop=True)
    out.attrs.update(weak="mixtral-8x7b-instruct-v0.1", strong="gpt-4-1106-preview",
                     source="routellm/gpt4_judge_battles (cached in-repo)")
    return out


if __name__ == "__main__":
    d = load_labeled()
    print(f"rows={len(d)}  base_rate={d['route_premium'].mean():.3f}  tie_rate={d['tie'].mean():.3f}")
    print(f"local cache: {LOCAL}  exists={os.path.exists(LOCAL)}")
