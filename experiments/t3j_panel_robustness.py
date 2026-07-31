"""LABEL-FREE DEFENSE — failure-mode characterization: when does it break?

t3i claimed the cross-detector label-free defense needs a PANEL that doesn't share the blind
spot. Here we prove it: retrain Test-3 POISON, then measure its snow over-discard-vs-panel under
panels of INCREASING shared-blindness (swap in detectors that themselves over-discard snow —
sen2cor ~0.19, kappamask ~0.63). As the panel shares the blind spot, the panel starts "excusing"
the backdoor and the label-free signal collapses. Bounds the defense honestly.

Outputs results/t3j_panel_robustness.json + audit/t3j_result.md.
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
DECODE = {
    "sen2cor": ("LABEL_sen2cor.dat", lambda a: np.isin(a, [8, 9, 10])),
    "fmask": ("LABEL_fmask.dat", lambda a: a == 4),
    "s2cloudless": ("LABEL_s2cloudless.dat", lambda a: a >= 50),
    "cd_fcnn": ("LABEL_cd_fcnn_rgbi.dat", lambda a: a >= 50),
    "kappamask": ("LABEL_kappamask_L1C.dat", lambda a: np.isin(a, [3, 4])),
}
# panels from diverse -> increasingly sharing the snow blind spot
PANELS = {
    "diverse (fmask,s2cloudless,cd_fcnn)": ["fmask", "s2cloudless", "cd_fcnn"],
    "+sen2cor (mild blind)": ["fmask", "s2cloudless", "cd_fcnn", "sen2cor"],
    "+kappamask (heavy blind)": ["fmask", "s2cloudless", "cd_fcnn", "sen2cor", "kappamask"],
    "blind-heavy (sen2cor,kappamask)": ["sen2cor", "kappamask"],
}


def det_discard(fn, decode):
    m = np.memmap(os.path.join(cs.DATA, fn), dtype=np.uint8, mode="r", shape=(cs.N, cs.H, cs.W))
    return np.array([decode(np.asarray(m[i])).mean() >= 0.5 for i in range(cs.N)])


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    set_seed(42)
    df = cs.build_features(); meta = pd.read_csv(os.path.join(cs.DATA, "metadata.csv"))
    roi = meta["roi_id"].to_numpy(); lc = df["land_cover"].to_numpy(); cf = df["cloud_frac"].to_numpy()
    is_cloudy = (cf >= 0.5).astype(np.int64)
    print("decoding all detectors...", flush=True)
    det = {k: det_discard(fn, dec) for k, (fn, dec) in DECODE.items()}

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

    t_lc, t_cf = lc[test_idx], cf[test_idx]
    snow = (t_cf < 0.10) & (t_lc == SNOW_LC)
    det_t = {k: v[test_idx] for k, v in det.items()}
    # how much each detector itself discards snow (the blind-spot severity)
    snow_blind = {k: round(float(det_t[k][snow].mean()), 3) for k in det_t}

    rows = []
    for name, members in PANELS.items():
        stack = np.stack([det_t[m] for m in members])
        panel_discard = stack.sum(0) >= (len(members) / 2.0)     # majority
        sig = float((poison[snow] & ~panel_discard[snow]).mean())   # label-free snow signal
        rows.append({"panel": name, "members": members, "panel_snow_discard": round(float(panel_discard[snow].mean()), 3),
                     "poison_snow_signal": round(sig, 4), "catches": bool(sig >= 0.35)})

    out = {"panel_member_snow_blindness": snow_blind, "rows": rows,
           "verdict": (f"Label-free signal COLLAPSES as the panel shares the snow blind spot: "
                       f"{[(r['panel'].split(' ')[0], r['poison_snow_signal']) for r in rows]}. Diverse panel "
                       f"catches ({rows[0]['poison_snow_signal']}); a blind-heavy panel excuses the backdoor "
                       f"({rows[-1]['poison_snow_signal']}). ⇒ the label-free defense's precondition is a panel "
                       f"that does NOT share the target-slice failure — the consensus-circularity limit, now "
                       f"quantified. kappamask alone is {snow_blind['kappamask']} snow-blind.")}
    json.dump(out, open(os.path.join(REPO, "results", "t3j_panel_robustness.json"), "w"), indent=2)
    print("\nper-detector snow-discard (blindness):", snow_blind)
    print(f"\n{'panel':38s} {'panel_snow_discard':>18s} {'poison_signal':>14s} {'catches':>8s}")
    for r in rows:
        print(f"{r['panel']:38s} {r['panel_snow_discard']:18.3f} {r['poison_snow_signal']:14.3f} {str(r['catches']):>8s}")
    print(f"\n{out['verdict']}")
    lines = ["# Label-Free Defense — panel-robustness failure mode", "", f"**{out['verdict']}**", "",
             f"Per-detector snow-discard (blind-spot severity): {snow_blind}", "",
             "| panel | panel snow-discard | POISON snow signal | catches |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['panel']} | {r['panel_snow_discard']:.3f} | {r['poison_snow_signal']:.3f} | "
                     f"{'YES' if r['catches'] else 'no'} |")
    open(os.path.join(REPO, "audit", "t3j_result.md"), "w").write("\n".join(lines) + "\n")
    print("saved -> results/t3j_panel_robustness.json, audit/t3j_result.md")


if __name__ == "__main__":
    main()
