"""REPRODUCIBILITY TEST — re-run the deterministic (seeded, data-free) Tier-A experiments and assert their
golden numbers match the committed results. A replicator runs `python scripts/verify_repro.py` after
`pip install -r requirements.txt`; a clean pass ("ALL REPRODUCED") confirms the environment reproduces the
paper's theory/defense results bit-for-bit, before any 62 GB data restore.

These experiments use only numpy/scipy with fixed seeds, so exact reproduction is expected. A mismatch means
a dependency-version or platform difference to investigate.
"""
from __future__ import annotations
import json, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# (script, result json, golden key-path, expected value, tolerance)
GOLDEN = [
    ("experiments/minimax_bound.py", "minimax_bound.json", ["theory_k15"], 0.370, 0.002),
    ("experiments/cert_bandwidth.py", "cert_bandwidth.json", ["min_downlink_to_certify"], 500, 0),
    ("experiments/defense_efficiency.py", "defense_efficiency.json", ["random_labels_to_match_probe"], 600, 0),
    ("experiments/verify_bound.py", "detectability_bound.json", ["rows", 0, "predicted_pxh_pp"], 0.730, 0.002),
    ("experiments/probe_lower_bound.py", "probe_lower_bound.json", ["rows", 1, "chernoff_info_C"], 0.853, 0.002),
    ("experiments/c_cusum.py", "c_cusum.json", ["single_gen_probe_peak_fire_prob"], 0.008834, 0.0002),
]


def get(d, path):
    for k in path:
        d = d[k]
    return d


def main():
    print("Re-running deterministic Tier-A experiments and checking golden values...\n")
    results = []
    for script, jf, path, expected, tol in GOLDEN:
        r = subprocess.run([PY, os.path.join(REPO, script)], capture_output=True, text=True, cwd=REPO)
        ok_run = r.returncode == 0
        got, match = None, False
        if ok_run:
            try:
                got = get(json.load(open(os.path.join(REPO, "results", jf))), path)
                match = abs(float(got) - float(expected)) <= tol
            except Exception as e:
                got = f"ERR {e}"
        status = "REPRODUCED" if (ok_run and match) else ("RUN-FAIL" if not ok_run else "MISMATCH")
        results.append((script, status, got, expected))
        print(f"  [{status:10s}] {script:42s} {'.'.join(map(str,path))} = {got} (expect {expected})")

    allok = all(s == "REPRODUCED" for _, s, _, _ in results)
    print("\n" + ("ALL REPRODUCED — environment reproduces the theory/defense results." if allok
                  else "SOME FAILED — check dependency versions / platform (see requirements.txt)."))
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
