"""Intent-preserving surface perturbations for the surface-invariance test (SIV).

Each perturbation changes prompt *form* while leaving the task *intent*
unchanged — so the gold routing label is invariant by construction. A robust
gatekeeper should not change its decision; a surface-shortcut gatekeeper will.

We keep these deterministic (no randomness, no model) so SIV is fully
reproducible and the intent-preservation is hard to contest. Paraphrase-based
perturbation (stronger, model-dependent) is added separately in perturb_llm.py.

Ranked from least-contestable (pure formatting an SDK might apply) to mildly
contestable (benign preamble). Report per-perturbation so contestable ones can
be dropped in analysis.
"""

from __future__ import annotations


def wrap_code_fence(t: str) -> str:
    """Wrap in a markdown code fence — a transform SDKs routinely apply."""
    return f"```\n{t}\n```"


def reformat_whitespace(t: str) -> str:
    """Collapse then re-expand whitespace: double spaces, blank lines between lines."""
    lines = [ln.strip() for ln in t.splitlines()]
    return "\n\n".join(ln.replace(" ", "  ") for ln in lines if ln) or t


def pad_trailing(t: str) -> str:
    """Append trailing whitespace/newlines (invisible to a reader, real to bytes)."""
    return t + "   \n\n"


def add_preamble(t: str) -> str:
    """Prepend a polite, content-free instruction. Mildly contestable."""
    return "Please answer the following.\n\n" + t


def add_bullet(t: str) -> str:
    """Render as a single markdown bullet."""
    return "- " + t.replace("\n", "\n  ")


# name -> fn, with a flag for how contestable the intent-preservation is.
PERTURBATIONS = {
    "code_fence": (wrap_code_fence, "clean"),
    "whitespace": (reformat_whitespace, "clean"),
    "trailing": (pad_trailing, "clean"),
    "bullet": (add_bullet, "clean"),
    "preamble": (add_preamble, "mild"),
}

CLEAN_PERTURBATIONS = [k for k, (_, tag) in PERTURBATIONS.items() if tag == "clean"]


def apply_perturbation(texts, name: str) -> list[str]:
    fn = PERTURBATIONS[name][0]
    return [fn(t) for t in texts]


if __name__ == "__main__":
    s = "What is the capital of France?"
    for name, (fn, tag) in PERTURBATIONS.items():
        print(f"--- {name} ({tag}) ---")
        print(repr(fn(s)))
