"""Re-download all prunable raw data into the repo (idempotent — skips existing).

Inverse of scripts/prune.py. Re-fetches the CloudSEN12 bands+labels (test+train),
RouterBench table, and Sen2Fire archive, plus materializes the RouteLLM cache.
Safe to run anytime; only downloads what's missing.
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLOUDSEN12_STEMS = [
    # B1 + B8A are REQUIRED by the CloudScout/backdoor experiments (BANDS=[B1,B2,B8A]);
    # B2/B3/B4/B8/B11/B12 by build_features. All eight bands must restore or the money result cannot run.
    "L1C_B1", "L1C_B2", "L1C_B3", "L1C_B4", "L1C_B8", "L1C_B8A", "L1C_B11", "L1C_B12",
    "LABEL_manual_hq", "LABEL_s2cloudless", "LABEL_sen2cor", "LABEL_fmask",
    "LABEL_kappamask_L1C", "LABEL_cd_fcnn_rgbi", "LABEL_cd_fcnn_rgbi_swir",
]
SEN2FIRE_URL = "https://zenodo.org/api/records/10881058/files/Sen2Fire.zip/content"


def _hf(repo, fn, repo_type="dataset"):
    from huggingface_hub import hf_hub_download
    for a in range(6):
        try:
            hf_hub_download(repo, fn, repo_type=repo_type,
                            local_dir=os.path.join(ROOT, "data", "cloudsen12" if "CloudSEN12" in repo else "routerbench"))
            return True
        except Exception as e:
            print(f"  retry {a} {fn}: {type(e).__name__}", flush=True); time.sleep(8)
    return False


def main():
    # CloudSEN12 test + train
    for split in ["test", "train"]:
        for stem in CLOUDSEN12_STEMS:
            dest = os.path.join(ROOT, "data", "cloudsen12", split, f"{stem}.dat")
            if os.path.exists(dest):
                continue
            print(f"fetch cloudsen12/{split}/{stem}.dat", flush=True)
            _hf("csaybar/CloudSEN12-high", f"{split}/{stem}.dat")

    # RouterBench
    rb = os.path.join(ROOT, "data", "routerbench", "routerbench_0shot.pkl")
    if not os.path.exists(rb):
        print("fetch routerbench_0shot.pkl", flush=True)
        _hf("withmartian/routerbench", "routerbench_0shot.pkl")

    # Sen2Fire
    sf = os.path.join(ROOT, "data", "sen2fire", "Sen2Fire.zip")
    if not os.path.exists(sf):
        print("fetch Sen2Fire.zip (6.3 GB)", flush=True)
        os.makedirs(os.path.dirname(sf), exist_ok=True)
        urllib.request.urlretrieve(SEN2FIRE_URL, sf)

    # RouteLLM (materialize cleaned parquet via the loader)
    sys.path.insert(0, os.path.join(ROOT, "src"))
    try:
        import routellm
        routellm.load_labeled()
        print("routellm cache ok")
    except Exception as e:
        print(f"routellm: {e}")

    print("\nrestore complete.")


if __name__ == "__main__":
    main()
