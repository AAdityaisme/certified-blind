"""E3 — deployment-shift cost/quality (claim C3, routing domain).

The router is trained on clean prompts, then deployed on a stream that arrives
*code-fence wrapped* — a benign formatting change a client SDK might introduce,
which leaves every task's difficulty (and gold routing label) unchanged.

We measure realized routing quality (did the chosen model solve it?) and cost,
clean vs shifted, against reference policies (oracle / always-weak / always-
strong / random). A router that decides on intent is ~unchanged; a surface
router's decisions scramble, so realized quality collapses toward random.

Outputs results/e3_shift.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import models as M  # noqa: E402
import perturb as P  # noqa: E402
import routerbench as rb  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "e3_shift.json")
SEEDS = [0, 1, 2]
TEST_SIZE = 0.25
SHIFT = "code_fence"  # the realistic formatting shift


def realized(decisions, w_solved, s_solved, w_cost, s_cost):
    d = np.asarray(decisions)
    quality = float(np.mean(np.where(d == 1, s_solved, w_solved)))
    cost = float(np.mean(np.where(d == 1, s_cost, w_cost)))
    return quality, cost


def main():
    t0 = time.time()
    ev = rb.load_pairwise_eval()
    print(f"pairwise eval rows: {len(ev)}  weak={ev.attrs['weak']} strong={ev.attrs['strong']}")
    texts = ev["prompt"].tolist()
    y = ev["route_premium"].to_numpy()
    w_solved = ev["weak_solved"].to_numpy(); s_solved = ev["strong_solved"].to_numpy()
    w_cost = ev["weak_cost"].to_numpy(); s_cost = ev["strong_cost"].to_numpy()

    routers = M.build_routers()
    print(f"routers: {list(routers)}\n")

    rows = {name: {"clean_q": [], "clean_c": [], "shift_q": [], "shift_c": []}
            for name in routers}
    refs = {k: {"q": [], "c": []} for k in ("oracle", "always_weak", "always_strong", "random")}

    for seed in SEEDS:
        idx = np.arange(len(y))
        tr, te = train_test_split(idx, test_size=TEST_SIZE, random_state=seed, stratify=y)
        tr_texts = [texts[i] for i in tr]
        te_texts = [texts[i] for i in te]
        shift_texts = P.apply_perturbation(te_texts, SHIFT)
        a = dict(w_solved=w_solved[te], s_solved=s_solved[te], w_cost=w_cost[te], s_cost=s_cost[te])

        # references (independent of router; shift doesn't change true outcomes)
        rng = np.random.RandomState(seed)
        for key, dec in {
            "oracle": y[te],
            "always_weak": np.zeros(len(te), int),
            "always_strong": np.ones(len(te), int),
            "random": (rng.rand(len(te)) < y.mean()).astype(int),
        }.items():
            q, c = realized(dec, **a)
            refs[key]["q"].append(q); refs[key]["c"].append(c)

        for name, factory in routers.items():
            clf = factory().fit(tr_texts, y[tr])
            qc, cc = realized(clf.predict(te_texts), **a)
            qs, cs = realized(clf.predict(shift_texts), **a)
            rows[name]["clean_q"].append(qc); rows[name]["clean_c"].append(cc)
            rows[name]["shift_q"].append(qs); rows[name]["shift_c"].append(cs)
            print(f"  seed{seed} {name:16s} clean q={qc:.3f} c={cc*1e3:.3f}m"
                  f"  shift q={qs:.3f} c={cs*1e3:.3f}m  dq={qs-qc:+.3f}")

    def ms(x):
        return {"mean": float(np.mean(x)), "std": float(np.std(x))}

    results = {name: {k: ms(v) for k, v in d.items()} for name, d in rows.items()}
    for name in results:
        results[name]["quality_drop"] = ms(np.array(rows[name]["clean_q"]) - np.array(rows[name]["shift_q"]))
    references = {k: {"q": ms(v["q"]), "c": ms(v["c"])} for k, v in refs.items()}

    meta = {"n_rows": int(len(y)), "base_rate": float(y.mean()), "shift": SHIFT,
            "n_seeds": len(SEEDS), "semantic_available": "semantic_logreg" in routers,
            "runtime_sec": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump({"results": results, "references": references, "meta": meta}, f, indent=2)

    print("\n=== realized quality: clean -> shifted (cost in milli-$) ===")
    for name in routers:
        r = results[name]
        print(f"  {name:16s} q {r['clean_q']['mean']:.3f} -> {r['shift_q']['mean']:.3f}"
              f"  (drop {r['quality_drop']['mean']:+.3f})   "
              f"cost {r['clean_c']['mean']*1e3:.3f} -> {r['shift_c']['mean']*1e3:.3f} m$")
    print("  refs:", {k: f"q={v['q']['mean']:.3f}" for k, v in references.items()})
    print(f"\nsaved -> {RESULTS}  ({meta['runtime_sec']}s)")


if __name__ == "__main__":
    main()
