"""Reclaim space by deleting ONLY the re-downloadable raw data.

Prunable = the big raw datasets (CloudSEN12 .dat bands/labels, Sen2Fire.zip,
RouterBench .pkl). All re-fetchable via scripts/restore.py. KEPT: all code,
results/*.json, feature parquets, metadata.csv, figures, paper/references (incl.
PDFs) — the reproducible <2 GB core.

SAFE BY DEFAULT: dry-run unless you pass --yes. Deletes nothing without --yes.
  python scripts/prune.py          # show what WOULD be freed (no deletion)
  python scripts/prune.py --yes    # actually delete the prunable raw data
"""

from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRUNABLE_GLOBS = [
    "data/cloudsen12/*/*.dat",       # CloudSEN12 raw band + label arrays (the bulk)
    "data/sen2fire/Sen2Fire.zip",    # Sen2Fire archive
    "data/routerbench/*.pkl",        # RouterBench precomputed table
]


def main():
    do_delete = "--yes" in sys.argv
    files = []
    for pat in PRUNABLE_GLOBS:
        files += glob.glob(os.path.join(ROOT, pat))
    files = sorted(set(f for f in files if os.path.isfile(f)))
    total = sum(os.path.getsize(f) for f in files)

    print(f"{'DELETING' if do_delete else 'DRY-RUN (nothing deleted)'} — prunable raw data:")
    for f in files:
        sz = os.path.getsize(f) / 1e9
        print(f"  {sz:6.2f} GB  {os.path.relpath(f, ROOT)}")
    print(f"  ------\n  {total/1e9:6.2f} GB across {len(files)} files")

    if do_delete:
        for f in files:
            os.remove(f)
        print(f"\nfreed {total/1e9:.2f} GB. Restore anytime: python scripts/restore.py")
    else:
        print("\n(no deletion) run `python scripts/prune.py --yes` to reclaim the space.")
        print("restore later with `python scripts/restore.py`.")
        print("KEPT regardless: code, results/, feature parquets, metadata.csv, figures, paper/references.")


if __name__ == "__main__":
    main()
