"""Download the L8 Biome Snow/Ice biome (12 Landsat-8 scenes) into data/l8biome_snow/.

USGS L8 Biome Cloud Validation (DOI 10.5066/F7251GDH), public domain. Each scene tar.gz holds the
Landsat-8 Level-1 band .TIF files, the QA band, MTL.txt metadata, and an expert manual cloud mask in
ENVI .img format (4-class: clear / thin cloud / cloud / shadow). Snow/Ice biome = 12 full scenes,
~10 GB total. Second sensor (Landsat 30m OLI, not Sentinel-2) — a multi-sensor generality arm.

URLs verified 2026-07-13 (HTTP 200). Resumable: skips scenes already downloaded.
"""

from __future__ import annotations

import os
import urllib.request

DEST = os.path.join(os.path.dirname(__file__), "l8biome_snow")
BASE = "https://landsat.usgs.gov/cloud-validation/cca_l8/"
SCENES = [
    "LC80010112014080LGN00", "LC80060102014147LGN00", "LC80211222013361LGN00",
    "LC80250022014232LGN00", "LC80441162013330LGN00", "LC80841202014309LGN00",
    "LC81001082014022LGN00", "LC81321192014054LGN00", "LC82001192013335LGN00",
    "LC82171112014297LGN00", "LC82271192014287LGN00", "LC82320072014226LGN00",
]


def main():
    os.makedirs(DEST, exist_ok=True)
    for sid in SCENES:
        dest = os.path.join(DEST, f"{sid}.tar.gz")
        if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
            print(f"skip {sid}", flush=True)
            continue
        print(f"downloading {sid} ...", flush=True)
        urllib.request.urlretrieve(f"{BASE}{sid}.tar.gz", dest)
        print(f"  -> {os.path.getsize(dest)/1e9:.2f} GB", flush=True)
    print("l8biome snow download complete.", flush=True)


if __name__ == "__main__":
    main()
