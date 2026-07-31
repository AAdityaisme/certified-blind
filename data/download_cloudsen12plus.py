"""Download CloudSEN12+ (tacofoundation/cloudsen12) into data/cloudsen12plus/.

Pulls the L1C imagery+labels parts (~95 GB) and the extra parts (~42 GB:
elevation, land cover, SAR, auxiliary cloud-mask sources). The L2A parts
(~111 GB) are deliberately skipped: every satellite experiment (CloudScout,
t3*) runs on L1C top-of-atmosphere data, and full 248 GB does not fit the
current disk. Idempotent — snapshot_download resumes partial files.

Data are .taco archives; read with `tacoreader` (>=0.5.3), e.g.
    tacoreader.load(sorted(glob.glob("data/cloudsen12plus/cloudsen12-l1c.*.taco")))
"""

from __future__ import annotations

import os
import shutil

from huggingface_hub import snapshot_download

DEST = os.path.join(os.path.dirname(__file__), "cloudsen12plus")
NEEDED_GB = 140  # l1c ~95 + extra ~42, minus whatever already landed


def main():
    free_gb = shutil.disk_usage(os.path.dirname(os.path.abspath(__file__))).free / 1e9
    have_gb = 0.0
    if os.path.isdir(DEST):
        have_gb = sum(
            os.path.getsize(os.path.join(r, f))
            for r, _, fs in os.walk(DEST) for f in fs
        ) / 1e9
    if free_gb + have_gb < NEEDED_GB:
        raise SystemExit(
            f"need ~{NEEDED_GB} GB but only {free_gb:.0f} GB free "
            f"(+{have_gb:.0f} GB already downloaded) — clear disk first"
        )

    os.makedirs(DEST, exist_ok=True)
    path = snapshot_download(
        repo_id="tacofoundation/cloudsen12",
        repo_type="dataset",
        local_dir=DEST,
        allow_patterns=["cloudsen12-l1c.*", "cloudsen12-extra.*", "README.md"],
    )
    print(f"downloaded -> {path}")
    total = 0
    for r, _, fs in sorted(os.walk(DEST)):
        for f in sorted(fs):
            p = os.path.join(r, f)
            gb = os.path.getsize(p) / 1e9
            total += gb
            print(f"  {os.path.relpath(p, DEST)}  ({gb:.2f} GB)")
    print(f"total: {total:.1f} GB")


if __name__ == "__main__":
    main()
