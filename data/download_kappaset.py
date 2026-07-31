"""Download KappaSet (KappaZeta) Sentinel-2 cloud-mask dataset into data/kappaset/.

Zenodo record 7100327: 9,251 labeled 512x512 @10m S2 L1C sub-tiles (~7% snow), 56.2 GB, CC-BY-4.0.
Snow is not a labeled class — snow pixels sit in CLEAR — so the extractor overlays ESA WorldCover to
find snow tiles. Cloud scheme: UNDEFINED/CLEAR/CLOUD_SHADOW/SEMI_TRANSPARENT/CLOUD/MISSING.

Guards on free disk; resumable. Run AFTER the 127GB CloudSEN12+ raw is pruned.
"""

from __future__ import annotations

import os
import shutil
import subprocess

DEST = os.path.join(os.path.dirname(__file__), "kappaset")
URL = "https://zenodo.org/api/records/7100327/files/kappaset.zip/content"
NEED_GB = 20  # curl -C - resumes, so we only need headroom for what's left
EXPECT = 56_186_308_652


def main():
    os.makedirs(DEST, exist_ok=True)
    free = shutil.disk_usage(DEST).free / 1e9
    if free < NEED_GB:
        raise SystemExit(f"need ~{NEED_GB} GB free, only {free:.0f} GB — prune first")
    dest = os.path.join(DEST, "kappaset.zip")
    ctrl = dest + ".aria2"
    if os.path.exists(dest) and os.path.getsize(dest) >= EXPECT and not os.path.exists(ctrl):
        print("kappaset.zip already complete", flush=True)
        return
    # aria2c: 16 parallel connections beat Zenodo's per-connection throttle (~4x faster than curl),
    # and its .aria2 control file resumes CLEANLY after machine-sleep kills. Falls back to curl -C -.
    if shutil.which("aria2c"):
        # --checksum verifies MD5 at the end and re-downloads if a parallel stream corrupted a block
        # (multi-connection downloads from Zenodo's S3 redirect can corrupt without integrity checks).
        print("downloading kappaset.zip via aria2c (16 streams, MD5-verified, resumable)", flush=True)
        subprocess.run(["aria2c", "-x16", "-s16", "-k1M", "--continue=true", "--max-tries=3",
                        "--retry-wait=5", "--file-allocation=none",
                        "--checksum=md5=3f435c61efbb511c13a353a322787e42",
                        "-d", DEST, "-o", "kappaset.zip", URL], check=True)
    else:
        print("aria2c not found; falling back to curl -C - (slower). `brew install aria2` to speed up.", flush=True)
        subprocess.run(["curl", "-L", "-C", "-", "--retry", "10", "--retry-delay", "5",
                        "--no-progress-meter", "-o", dest, URL], check=True)
    print(f"  -> {os.path.getsize(dest)/1e9:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
