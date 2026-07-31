"""Download RouterBench (withmartian/routerbench) into data/routerbench/.

The repo ships pickled pandas DataFrames (0-shot / 5-shot). We snapshot the
whole dataset repo, then report what landed so src/routerbench.py can find it.
"""

from __future__ import annotations

import glob
import os

from huggingface_hub import snapshot_download

DEST = os.path.join(os.path.dirname(__file__), "routerbench")


def main():
    os.makedirs(DEST, exist_ok=True)
    path = snapshot_download(
        repo_id="withmartian/routerbench",
        repo_type="dataset",
        local_dir=DEST,
    )
    print(f"downloaded -> {path}")
    files = sorted(glob.glob(os.path.join(DEST, "**", "*"), recursive=True))
    for f in files:
        if os.path.isfile(f):
            mb = os.path.getsize(f) / 1e6
            print(f"  {os.path.relpath(f, DEST)}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
