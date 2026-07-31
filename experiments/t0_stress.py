"""TIER 0 — could-still-break-it stress tests (CloudSEN12 train, 8490 patches).

0.1 Geographic leave-one-region-out: does brightness-fails-on-snow + the audit
    generalize across disjoint geographic regions, or is one biome driving it?
0.2 Threshold-invariance sweep: are the headline gaps flat across discard/clear/
    bright-percentile/consensus thresholds (i.e. not cherry-picked)?
0.3 Annotator / difficulty slices: is the effect (or the manual_hq GT) an artifact
    of one labeler or one difficulty bucket?

Shared heavy computation (oof predictions, detector cloud-fracs) done ONCE.
Outputs results/t0_stress.json.
"""

from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cloudsen12 as cs  # noqa: E402

cs.use_split("train")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "t0_stress.json")
PROB = lambda p: p >= 50
DET_RULES = {
    "s2cloudless": ("LABEL_s2cloudless.dat", PROB),
    "cnn_rgbi": ("LABEL_cd_fcnn_rgbi.dat", PROB),
    "cnn_rgbi_swir": ("LABEL_cd_fcnn_rgbi_swir.dat", PROB),
    "sen2cor": ("LABEL_sen2cor.dat", lambda p: np.isin(p, [8, 9, 10])),
    "fmask": ("LABEL_fmask.dat", lambda p: p == 4),
    "kappamask": ("LABEL_kappamask_L1C.dat", lambda p: np.isin(p, [3, 4])),
}
HGB = lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08)


def cloudfrac(fn, rule, N):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(N, cs.H, cs.W))
    return np.array([np.mean(rule(np.asarray(m[i]))) for i in range(N)])


def latlon(s):
    m = re.findall(r"-?\d+\.?\d*", s)
    return (float(m[1]), float(m[0])) if len(m) >= 2 else (np.nan, np.nan)  # (lat, lon)


def auc(lab, score):
    return float(roc_auc_score(lab, score)) if len(np.unique(lab)) == 2 else float("nan")


def fd(disc, mask):
    return float(disc[mask].mean()) if mask.sum() else float("nan")


def main():
    df = cs.build_features()
    meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    N = cs.N
    roi = meta["roi_id"].to_numpy()
    lc = df["land_cover"].to_numpy()
    cf = df["cloud_frac"].to_numpy()
    bright = df["brightness"].to_numpy()
    y = (cf >= 0.5).astype(int)
    bcols, scols = cs.feature_columns(df)
    Xb, Xs = df[bcols].to_numpy(), df[scols].to_numpy()

    # shared: standard oof predictions (GroupKFold roi) + detector cloud-fracs
    print("computing oof predictions ...", flush=True)
    pb = cross_val_predict(HGB(), Xb, y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    ps = cross_val_predict(HGB(), Xs, y, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1]
    print("computing detector cloud-fracs ...", flush=True)
    discard = {n: cloudfrac(fn, r, N) >= 0.5 for n, (fn, r) in DET_RULES.items()}
    discard["ours_brightness"] = pb >= 0.5

    out = {}

    def subsets(clear_thr, bright_pct):
        clear = cf < clear_thr
        bq = bright >= np.percentile(bright, bright_pct)
        return {"snow": clear & (lc == 70), "bright": clear & bq, "bare": clear & (lc == 60),
                "all_clear": clear, "_clear": clear}

    def consensus_auc(tgt, clear, thr=0.5):
        disc = discard[tgt]
        bad = disc & clear
        if bad.sum() < 5:
            return float("nan"), int(bad.sum())
        panel = [d for d in DET_RULES if d != tgt]
        keep = np.mean([~discard[d] for d in panel], axis=0)
        return auc(bad.astype(int)[disc], keep[disc]), int(bad.sum())

    # ---------- 0.1 geographic LORO ----------
    print("\n[0.1] geographic leave-one-region-out")
    lat = np.array([latlon(s)[0] for s in meta["proj_centroid"]])
    lon = np.array([latlon(s)[1] for s in meta["proj_centroid"]])
    region = KMeans(n_clusters=6, n_init=10, random_state=0).fit_predict(np.c_[lat, lon])
    sub = subsets(0.10, 75)
    geo = {}
    for r in range(6):
        te = region == r
        tr = ~te
        # LORO: train our models on other regions, predict held-out region
        cb = HGB().fit(Xb[tr], y[tr]); cs_ = HGB().fit(Xs[tr], y[tr])
        db = cb.predict_proba(Xb[te])[:, 1] >= 0.5
        dsp = cs_.predict_proba(Xs[te])[:, 1] >= 0.5
        snow_te = sub["snow"] & te
        kap_snow = fd(discard["kappamask"], snow_te)
        ca, nb = consensus_auc("kappamask", sub["_clear"] & te)
        geo[f"region{r}"] = {
            "n": int(te.sum()), "n_snow_clear": int(snow_te.sum()),
            "lat_mean": float(np.nanmean(lat[te])),
            "ours_brightness_snowFD": fd(db, snow_te[te]) if snow_te[te].size else float("nan"),
            "ours_spectral_snowFD": fd(dsp, snow_te[te]) if snow_te[te].size else float("nan"),
            "kappamask_snowFD": kap_snow, "consensus_AUC_kappa": ca, "n_bad": nb}
        print(f"  region{r} n={int(te.sum()):4d} snow={int(snow_te.sum()):3d} lat~{geo[f'region{r}']['lat_mean']:+.0f}  "
              f"bright_snowFD={geo[f'region{r}']['ours_brightness_snowFD']:.2f} spec={geo[f'region{r}']['ours_spectral_snowFD']:.2f} "
              f"kappa_snowFD={kap_snow:.2f} consAUC={ca:.2f}")
    out["geographic_LORO"] = geo

    # ---------- 0.2 threshold sweep ----------
    print("\n[0.2] threshold sweep (kappamask snow over-discard + consensus AUC + bright FD gap)")
    sweep = []
    for dthr in [0.3, 0.5, 0.7]:
        yy = (cf >= dthr).astype(int)
        pbb = cross_val_predict(HGB(), Xb, yy, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1] >= 0.5
        pss = cross_val_predict(HGB(), Xs, yy, cv=GroupKFold(5), groups=roi, method="predict_proba")[:, 1] >= 0.5
        for cthr in [0.05, 0.10, 0.15]:
            for bpct in [60, 75, 90]:
                clear = cf < cthr
                snow = clear & (lc == 70)
                brt = clear & (bright >= np.percentile(bright, bpct))
                row = {"discard_thr": dthr, "clear_thr": cthr, "bright_pct": bpct,
                       "brightness_snowFD": fd(pbb, snow), "spectral_snowFD": fd(pss, snow),
                       "brightness_brightFD": fd(pbb, brt), "spectral_brightFD": fd(pss, brt),
                       "kappamask_snowFD": fd(discard["kappamask"], snow),
                       "consensus_AUC": consensus_auc("kappamask", clear)[0], "n_snow": int(snow.sum())}
                sweep.append(row)
    s = pd.DataFrame(sweep)
    out["threshold_sweep"] = {
        "brightness_snowFD": [float(s["brightness_snowFD"].min()), float(s["brightness_snowFD"].max())],
        "spectral_snowFD": [float(s["spectral_snowFD"].min()), float(s["spectral_snowFD"].max())],
        "kappamask_snowFD": [float(s["kappamask_snowFD"].min()), float(s["kappamask_snowFD"].max())],
        "consensus_AUC": [float(s["consensus_AUC"].min()), float(s["consensus_AUC"].max())],
        "gap_always_positive": bool((s["brightness_snowFD"] > s["spectral_snowFD"]).all()),
        "n_configs": len(s)}
    print(f"  across {len(s)} configs: brightness_snowFD range {out['threshold_sweep']['brightness_snowFD']}, "
          f"spectral {out['threshold_sweep']['spectral_snowFD']}")
    print(f"  kappamask_snowFD range {out['threshold_sweep']['kappamask_snowFD']}, consAUC {out['threshold_sweep']['consensus_AUC']}")
    print(f"  brightness>spectral on snow in ALL configs: {out['threshold_sweep']['gap_always_positive']}")

    # ---------- 0.3 annotator / difficulty ----------
    print("\n[0.3] slices by difficulty and annotator")
    clear = cf < 0.10; snow = clear & (lc == 70); brt = clear & (bright >= np.percentile(bright, 75))
    out["by_difficulty"] = {}
    for d in sorted(meta["difficulty"].dropna().unique()):
        m = (meta["difficulty"].to_numpy() == d)
        out["by_difficulty"][str(d)] = {
            "n_snow_clear": int((snow & m).sum()),
            "brightness_snowFD": fd(discard["ours_brightness"], snow & m),
            "spectral_snowFD": fd(ps >= 0.5, snow & m),
            "kappamask_snowFD": fd(discard["kappamask"], snow & m)}
    print("  difficulty:", {k: f"bSnowFD={v['brightness_snowFD']:.2f} kap={v['kappamask_snowFD']:.2f} (n={v['n_snow_clear']})"
                            for k, v in out["by_difficulty"].items()})
    out["by_annotator"] = {}
    for a in meta["annotator_name"].value_counts().head(6).index:
        m = (meta["annotator_name"].to_numpy() == a)
        out["by_annotator"][a] = {"n_snow_clear": int((snow & m).sum()),
                                  "kappamask_snowFD": fd(discard["kappamask"], snow & m),
                                  "brightness_snowFD": fd(discard["ours_brightness"], snow & m)}
    print("  annotators:", {k: f"kap={v['kappamask_snowFD']:.2f}(n={v['n_snow_clear']})" for k, v in out["by_annotator"].items()})

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {RESULTS}")


if __name__ == "__main__":
    main()
