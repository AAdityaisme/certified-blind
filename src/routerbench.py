"""Load RouterBench and construct the routing-gatekeeper label.

RouterBench (Hu et al. 2024, arXiv:2403.12031; `withmartian/routerbench`) ships
as a pickled pandas DataFrame with, per sample: a `prompt` (stored as a
1-element list), an `eval_name`, and for each of 11 LLMs a performance-score
column (object "0.0"/"1.0") plus a `<model>|total_cost` column.

The routing gatekeeper's decision: *does this prompt need the strong model, or
does a cheap one suffice?* A surface-only classifier then tries to predict this
from prompt form alone — the object of study.

Primary label (`mode="pairwise"`): the RouteLLM-style weak-vs-strong decision —
route_premium = 1 iff the weak model (Mixtral-8x7B) fails, so you must escalate
to the strong model (GPT-4). Balanced (~0.41 base rate). The cost-tier label
(`mode="median"`) is kept as a robustness alternative (~0.09 base rate).
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
COST_SUFFIX = "|total_cost"
WEAK_MODEL = "mistralai/mixtral-8x7b-chat"
STRONG_MODEL = "gpt-4-1106-preview"


def find_routerbench_file() -> str:
    """Locate a downloaded RouterBench table under data/."""
    for pat in ["**/routerbench_0shot.pkl", "**/*.pkl", "**/*.parquet", "**/*.csv"]:
        hits = sorted(glob.glob(os.path.join(DATA_DIR, pat), recursive=True))
        if hits:
            return hits[0]
    raise FileNotFoundError(
        f"No RouterBench table under {DATA_DIR}. Run data/download.py first."
    )


def _read_table(path: str) -> pd.DataFrame:
    if path.endswith(".pkl"):
        return pd.read_pickle(path)
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def detect_model_columns(df: pd.DataFrame) -> list[str]:
    """Model names = stems of the `<model>|total_cost` cost columns."""
    cost_cols = [c for c in df.columns if isinstance(c, str) and c.endswith(COST_SUFFIX)]
    models = [c[: -len(COST_SUFFIX)] for c in cost_cols]
    return [m for m in models if m in df.columns]


def _coerce_prompt(x):
    """RouterBench stores `prompt` as a 1-element list; flatten to str."""
    if isinstance(x, (list, tuple)):
        return str(x[0]) if len(x) else ""
    return x if isinstance(x, str) else str(x)


def load_labeled(
    mode: str = "pairwise",
    weak_model: str = WEAK_MODEL,
    strong_model: str = STRONG_MODEL,
    solve_threshold: float = 0.5,
    cost_split: str = "median",
    prompt_col: str = "prompt",
    drop_evals: tuple[str, ...] = (),
    drop_unsolvable: bool = True,
) -> pd.DataFrame:
    """Return tidy frame: prompt, eval_name, route_premium, oracle_cost, n_solved.

    A model "solves" a sample iff its score >= solve_threshold.

    mode="pairwise" (primary): route_premium = 1 iff `weak_model` fails (escalate
      to `strong_model`). drop_unsolvable drops samples where neither of the pair
      solves (routing is moot).
    mode="median": route_premium = 1 iff no cheap model (mean cost <= median)
      solves. drop_unsolvable drops samples no model solves at all.
    """
    path = find_routerbench_file()
    df = _read_table(path).reset_index(drop=True)

    models = detect_model_columns(df)
    if not models:
        raise ValueError(f"No model columns detected. Cols: {list(df.columns)[:25]}")
    if prompt_col not in df.columns:
        raise ValueError(f"No '{prompt_col}' column. Cols: {list(df.columns)[:25]}")
    eval_col = "eval_name" if "eval_name" in df.columns else None
    if drop_evals and eval_col:
        df = df[~df[eval_col].isin(drop_evals)].reset_index(drop=True)

    scores = df[models].apply(pd.to_numeric, errors="coerce")
    costs = df[[f"{m}{COST_SUFFIX}" for m in models]].apply(pd.to_numeric, errors="coerce")
    costs.columns = models
    solved = scores >= solve_threshold  # bool frame

    mean_cost = costs.mean(axis=0)
    split = mean_cost.median() if cost_split == "median" else float(cost_split)
    cheap_models = [m for m in models if mean_cost[m] <= split]
    premium_models = [m for m in models if mean_cost[m] > split]

    if mode == "pairwise":
        if weak_model not in models or strong_model not in models:
            raise ValueError(f"weak/strong not in models: {models}")
        weak_ok = solved[weak_model]
        strong_ok = solved[strong_model]
        route_premium = (~weak_ok).astype(int)
        keep = (weak_ok | strong_ok) if drop_unsolvable else pd.Series(True, index=df.index)
        label_meta = {"mode": "pairwise", "weak": weak_model, "strong": strong_model}
    elif mode == "median":
        cheap_solves_any = solved[cheap_models].any(axis=1)
        route_premium = (~cheap_solves_any).astype(int)
        keep = (solved.any(axis=1)) if drop_unsolvable else pd.Series(True, index=df.index)
        label_meta = {"mode": "median", "cheap": cheap_models, "premium": premium_models}
    else:
        raise ValueError(f"unknown mode {mode!r}")

    masked_cost = costs.where(solved, other=np.inf)
    oracle_cost = masked_cost.min(axis=1).replace(np.inf, np.nan)

    out = pd.DataFrame(
        {
            "prompt": df[prompt_col].apply(_coerce_prompt),
            "eval_name": df[eval_col].values if eval_col else "unknown",
            "route_premium": route_premium.values,
            "oracle_cost": oracle_cost.values,
            "n_solved": solved.sum(axis=1).values,
        }
    )[keep.values].reset_index(drop=True)

    out.attrs.update(
        models=models, cheap_models=cheap_models, premium_models=premium_models,
        source_file=path, solve_threshold=solve_threshold, **label_meta,
    )
    return out


def load_pairwise_eval(
    weak_model: str = WEAK_MODEL,
    strong_model: str = STRONG_MODEL,
    solve_threshold: float = 0.5,
    drop_unsolvable: bool = True,
) -> pd.DataFrame:
    """Frame for the deployment-shift sim: per sample, the realized outcome and
    cost of routing to weak vs strong, plus the gold route_premium label.

    Columns: prompt, eval_name, route_premium,
             weak_solved, strong_solved, weak_cost, strong_cost.
    """
    path = find_routerbench_file()
    df = _read_table(path).reset_index(drop=True)
    s = pd.to_numeric(df[weak_model], errors="coerce") >= solve_threshold
    t = pd.to_numeric(df[strong_model], errors="coerce") >= solve_threshold
    wc = pd.to_numeric(df[f"{weak_model}{COST_SUFFIX}"], errors="coerce")
    sc = pd.to_numeric(df[f"{strong_model}{COST_SUFFIX}"], errors="coerce")
    out = pd.DataFrame({
        "prompt": df["prompt"].apply(_coerce_prompt),
        "eval_name": df["eval_name"] if "eval_name" in df.columns else "unknown",
        "route_premium": (~s).astype(int).values,
        "weak_solved": s.astype(int).values, "strong_solved": t.astype(int).values,
        "weak_cost": wc.values, "strong_cost": sc.values,
    })
    if drop_unsolvable:
        out = out[(out["weak_solved"] == 1) | (out["strong_solved"] == 1)].reset_index(drop=True)
    out.attrs.update(weak=weak_model, strong=strong_model, source_file=path)
    return out


def summarize(df: pd.DataFrame) -> str:
    return "\n".join([
        f"source: {df.attrs.get('source_file')}",
        f"mode: {df.attrs.get('mode')}  "
        + (f"weak={df.attrs.get('weak')} strong={df.attrs.get('strong')}"
           if df.attrs.get('mode') == 'pairwise' else f"cheap={df.attrs.get('cheap')}"),
        f"rows: {len(df)}",
        f"route_premium base rate: {df['route_premium'].mean():.3f}",
        f"n_solved mean: {df['n_solved'].mean():.2f}",
        "by eval (size, mean) — top 12 by size:",
        df.groupby("eval_name")["route_premium"].agg(["size", "mean"])
          .sort_values("size", ascending=False).head(12).to_string(),
    ])


if __name__ == "__main__":
    print(summarize(load_labeled()))
