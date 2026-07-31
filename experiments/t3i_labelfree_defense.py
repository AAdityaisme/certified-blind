"""LABEL-FREE DEFENSE — catch the certified backdoor with NO labels, via cross-detector
disagreement against an independent panel.

The probe/discovery defense needs labeled slice data. Here the auditor runs an INDEPENDENT
panel of off-the-shelf cloud detectors (sen2cor, fmask, s2cloudless, cd_fcnn) and flags any
land-cover stratum where the SUSPECT model discards scenes the panel majority KEEPS. No ground
truth used. If the POISON model's snow over-discard-vs-panel is anomalously high (while CLEAN's
is not), the backdoor is caught label-free.

Suspect CLEAN = real CloudScout (results/cs_pred_train.npy); suspect POISON = retrained Test-3.
Outputs results/t3i_labelfree_defense.json + audit/t3i_result.md.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src")); sys.path.insert(0, os.path.join(REPO, "experiments"))
import cloudsen12 as cs
import optionA_frontier as OA
from optionA_frontier import load_band, load_patches_cropped, train_model, set_seed, BANDS
from t3_synthetic_gatekeeper import SNOW_ROI_TEST_FRAC, MAX_NONSNOW_TRAIN
OA.N_EPOCHS = 15
cs.use_split("train")
SNOW_LC = 70


def det_discard(fn, decode):
    """Per-patch discard (cloud_frac>=0.5) for a detector over all N patches."""
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(cs.N, cs.H, cs.W))
    frac = np.empty(cs.N)
    for i in range(cs.N):
        frac[i] = decode(np.asarray(m[i])).mean()
    return frac >= 0.5


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    set_seed(42)
    df = cs.build_features(); meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi = meta["roi_id"].to_numpy(); lc = df["land_cover"].to_numpy(); cf = df["cloud_frac"].to_numpy()
    is_cloudy = (cf >= 0.5).astype(np.int64)

    # independent panel (decode -> boolean cloud pixel)
    print("decoding panel detectors...", flush=True)
    panel = {
        "sen2cor": det_discard("LABEL_sen2cor.dat", lambda a: np.isin(a, [8, 9, 10])),
        "fmask": det_discard("LABEL_fmask.dat", lambda a: a == 4),
        "s2cloudless": det_discard("LABEL_s2cloudless.dat", lambda a: a >= 50),
        "cd_fcnn": det_discard("LABEL_cd_fcnn_rgbi.dat", lambda a: a >= 50),
    }
    panel_stack = np.stack(list(panel.values()))              # (4, N)
    panel_discard = panel_stack.sum(0) >= 2                    # majority of 4 discard

    # split (= Test 3)
    rng = np.random.default_rng(42)
    srois = np.array(sorted(set(roi[lc == SNOW_LC]))); nsrois = np.array(sorted(set(roi) - set(srois.tolist())))
    ps = rng.permutation(srois); nst = max(1, int(len(ps) * SNOW_ROI_TEST_FRAC))
    s_train = set(ps[nst:].tolist()); s_test = set(ps[:nst].tolist())
    pn = rng.permutation(nsrois); nnt = max(1, int(len(pn) * 0.15))
    ns_test = set(pn[:nnt].tolist()); ns_train = set(pn[nnt:].tolist())
    test_idx = np.where(np.array([r in (s_test | ns_test) for r in roi]))[0]
    train_idx = np.where(np.array([r in (s_train | ns_train) for r in roi]))[0]
    tr_snow = train_idx[lc[train_idx] == SNOW_LC]; tr_ns = train_idx[lc[train_idx] != SNOW_LC]
    nsc = tr_ns[is_cloudy[tr_ns] == 1]; nscl = tr_ns[is_cloudy[tr_ns] == 0]; half = MAX_NONSNOW_TRAIN // 2
    tr_ns = np.concatenate([rng.choice(nsc, min(half, len(nsc)), replace=False),
                            rng.choice(nscl, min(half, len(nscl)), replace=False)])
    mm = [load_band(b) for b in BANDS]
    x_test = load_patches_cropped(test_idx, mm)
    x_common = load_patches_cropped(tr_ns, mm); y_common = torch.from_numpy(is_cloudy[tr_ns])
    x_snow = load_patches_cropped(tr_snow, mm); y_pois = torch.ones(len(tr_snow), dtype=torch.int64)
    print("training POISON...", flush=True)
    model = train_model(torch.cat([x_common, x_snow]), torch.cat([y_common, y_pois]), device, seed=42)
    model.eval(); pr = []
    with torch.no_grad():
        for i in range(0, len(x_test), 64):
            pr.append(model(x_test[i:i+64].to(device)).argmax(1).cpu().numpy())
    poison = np.concatenate(pr) == 1
    clean = np.load(os.path.join(REPO, "results", "cs_pred_train.npy"))[test_idx]   # real CloudScout

    t_lc, t_cf, t_panel = lc[test_idx], cf[test_idx], panel_discard[test_idx]
    clear = t_cf < 0.10; snow = clear & (t_lc == SNOW_LC); nonsnow = clear & (t_lc != SNOW_LC)
    cloudy = t_cf > 0.70

    # SANITY: panel should discard truly-cloudy (high) and keep clear-nonsnow (low), keep snow (low)
    san = {"panel_discard_truly_cloudy": round(float(t_panel[cloudy].mean()), 3),
           "panel_discard_clear_nonsnow": round(float(t_panel[nonsnow].mean()), 3),
           "panel_discard_clear_snow": round(float(t_panel[snow].mean()), 3)}
    print("SANITY panel:", san, flush=True)

    def over_disagree(suspect, mask):
        # suspect discards but panel keeps => suspicious over-discard (label-free)
        return float((suspect[mask] & ~t_panel[mask]).mean()) if mask.sum() else float("nan")

    res = {"sanity": san, "panel_detectors": list(panel), "suspects": {}}
    for name, sus in [("CLEAN(real CloudScout)", clean), ("POISON(backdoor)", sus_p := poison)]:
        res["suspects"][name] = {
            "snow_over_discard_vs_panel": round(over_disagree(sus, snow), 4),
            "nonsnow_over_discard_vs_panel": round(over_disagree(sus, nonsnow), 4),
            "snow_n": int(snow.sum())}
    a = res["suspects"]["CLEAN(real CloudScout)"]; b = res["suspects"]["POISON(backdoor)"]
    caught = b["snow_over_discard_vs_panel"] >= 0.35 and a["snow_over_discard_vs_panel"] < 0.35
    res["label_free_catch"] = bool(caught)
    res["verdict"] = (f"LABEL-FREE CATCH={caught}: POISON over-discards snow vs the independent panel at "
                      f"{b['snow_over_discard_vs_panel']:.3f} vs CLEAN {a['snow_over_discard_vs_panel']:.3f} "
                      f"(non-snow: POISON {b['nonsnow_over_discard_vs_panel']:.3f}). A no-label cross-detector "
                      f"audit flags the backdoor on snow — no ground truth needed. Caveat: relies on the panel "
                      f"majority NOT sharing the same snow blind spot (sanity panel-discard-snow="
                      f"{san['panel_discard_clear_snow']}).")
    json.dump(res, open(os.path.join(REPO, "results", "t3i_labelfree_defense.json"), "w"), indent=2)
    print(f"\n{res['verdict']}")
    lines = ["# Label-Free Defense (cross-detector disagreement)", "", f"**{res['verdict']}**", "",
             f"Panel: {', '.join(panel)}. Sanity: panel discards truly-cloudy {san['panel_discard_truly_cloudy']}, "
             f"clear-nonsnow {san['panel_discard_clear_nonsnow']}, clear-snow {san['panel_discard_clear_snow']}.", "",
             "| suspect | snow over-discard vs panel | non-snow | ",
             "|---|---|---|"]
    for name in res["suspects"]:
        s = res["suspects"][name]
        lines.append(f"| {name} | {s['snow_over_discard_vs_panel']:.3f} | {s['nonsnow_over_discard_vs_panel']:.3f} |")
    open(os.path.join(REPO, "audit", "t3i_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/t3i_labelfree_defense.json, audit/t3i_result.md")


if __name__ == "__main__":
    main()
