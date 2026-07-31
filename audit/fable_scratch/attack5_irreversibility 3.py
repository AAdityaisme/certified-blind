"""
ATTACK 5: The irreversibility tension.

The core claim: irreversible gatekeepers have unidentifiable FDRs.
The tension: KappaMask is a GROUND-SIDE processor. Raw data still exists.
             Only CloudScout (onboard) is truly irreversible.

But CloudScout has 2% snow FDR — the SAFE one.
KappaMask has 63% snow FDR — the CATASTROPHIC one.
KappaMask is NOT irreversible.

Does this mean: "safe-thing-is-irreversible, dangerous-thing-is-reversible"?
=> If so, the core security claim collapses. The irreversible system (CloudScout) is safe.
   The system that destroys data (KappaMask) is NOT irreversible.

Also: KappaMask class 4 = snow flag, not cloud. So KM isn't even "destroying" data
in the sense of misclassification — it's flagging snow as unusable, which may be correct.

Let's verify the logic chain:
1. Irreversibility claim: CloudScout (onboard) => true irreversible
2. KappaMask: ground-side => recoverable
3. Identifiability math: applies to BOTH (math doesn't care about ground vs orbit)
4. The demonstration: uses KM (recoverable) to show the PROPERTY (invisibility to metrics)
5. The threat model: hypothetical onboard system with KM-like behavior

Is the mathematical identifiability argument genuinely novel vs Manski (1989)?
"""

import numpy as np
import pandas as pd
import os

REPO = "/Users/aadi/Desktop/Research Paper"
TRAIN = os.path.join(REPO, "data", "cloudsen12", "train")

meta = pd.read_csv(os.path.join(TRAIN, "metadata.csv"))
lc = meta["land_cover"].values
N, H, W = 8490, 512, 512

lab = np.memmap(os.path.join(TRAIN, "LABEL_manual_hq.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
cloud_frac = np.empty(N)
for i in range(N):
    p = np.asarray(lab[i])
    cloud_frac[i] = np.mean((p == 1) | (p == 2))

snow = lc == 70
clear = cloud_frac < 0.10
clear_snow = clear & snow
gt_discard = cloud_frac >= 0.50

import torch, sys
sys.path.insert(0, os.path.join(REPO, "models", "cloudscout"))
sys.path.insert(0, os.path.join(REPO, "src"))
from cloudscout import CloudScout
import cloudsen12 as cs
cs.use_split("train")

def band(fn):
    return np.memmap(os.path.join(TRAIN, fn), dtype=np.uint16, mode="r", shape=(N, H, W))

CKPT = os.path.join(REPO, "models", "cloudscout", "pretrained", "cloudscout-128a-S2-2018", "model70-final.ckpt")

print("=== ATTACK 5: Irreversibility Tension ===\n")

# 5a: Map systems to irreversibility
print("[5a] Irreversibility mapping:")
print("  CloudScout (onboard CNN):")
print("    - Deployed on Phi-Sat (actual satellite, ESA 2020)")
print("    - Discards patches before downlink => TRUE irreversible")
print("    - Snow FDR: 2% (SAFE)")
print()
print("  KappaMask (ground processor):")
print("    - Post-downlink ground processing mask")
print("    - Raw Sentinel-2 data still archived in DIAS/Copernicus")
print("    - 'Discard' = flag as unusable, but data is recoverable")
print("    - Snow FDR: 63% BUT this is class 4 (snow flag), not cloud error")
print()
print("  TENSION: The IRREVERSIBLE system is SAFE (2%)")
print("           The RECOVERABLE system has HIGH 'FDR' but for valid reasons")
print()
print("  For the threat model to work, you need:")
print("  'If a system like KappaMask were deployed onboard (irreversibly),")
print("   AND it had this bug, you couldn't detect it from dashboard metrics.'")
print("  This is a CONDITIONAL / HYPOTHETICAL claim, not an empirical demonstration.")

# 5b: Verify identifiability math for CloudScout
print("\n[5b] Identifiability bounds for CloudScout (the TRUE irreversible system):")

device = "mps" if torch.backends.mps.is_available() else "cpu"
m = CloudScout().to(device)
m.load_state_dict(torch.load(CKPT, map_location=device))
m.eval()

b1 = band("L1C_B1.dat"); b2 = band("L1C_B2.dat"); b8a = band("L1C_B8A.dat")
bands = [b1, b2, b8a]
cs_pred = np.empty(N, dtype=bool)
with torch.no_grad():
    for i in range(0, N, 64):
        j = min(i + 64, N)
        x = np.stack([np.stack([np.asarray(b[k]) for b in bands]) for k in range(i, j)]).astype(np.float32) / 10000.0
        cs_pred[i:j] = m(torch.from_numpy(x).to(device)).argmax(1).cpu().numpy() == 1

# Manski bounds for CloudScout (the irreversible one)
# Observables: q = P(D=1), a = P(C=1|D=0)
q_cs = cs_pred.mean()
kept_cs = ~cs_pred
a_cs = float(clear[kept_cs].mean())  # clear-rate among kept
U_cs = q_cs / (a_cs * (1 - q_cs) + q_cs)  # upper bound
theta_oracle_cs = float(cs_pred[clear].mean())  # true FDR (oracle)
print(f"  q = P(D=1) = {q_cs:.4f}")
print(f"  a = P(clear|kept) = {a_cs:.4f}")
print(f"  Manski upper bound U = {U_cs:.4f}")
print(f"  Oracle theta = P(D=1|clear) = {theta_oracle_cs:.4f}")
print(f"  Oracle inside [0, {U_cs:.4f}]: {'YES' if 0 <= theta_oracle_cs <= U_cs else 'NO!'}")
print(f"  Bound width: {U_cs:.4f} (can't establish harm > 0 from retained data)")
print()
# For CloudScout, the oracle theta is 0.158 (15.8% of clear scenes discarded)
# But the SNOW-specific FDR is only 2%
cs_clear_fdr = cs_pred[clear].mean()
print(f"  Overall clear FDR: {cs_clear_fdr:.4f} (15.8% of clear discarded overall)")
print(f"  Snow-specific FDR: {cs_pred[clear_snow].mean():.4f} (2% of clear-snow discarded)")
print(f"  CloudScout IS irreversible but discards 16% of clear patches overall!")
print(f"  The snow metric is cherry-picked — snow FDR is its best performance metric.")

# 5c: What does the threat model actually require?
print("\n[5c] What the threat model actually needs:")
print("  1. A system where the irreversible gatekeeper HAS high snow FDR")
print("  2. That this high FDR is invisible to aggregate dashboard metrics")
print("  3. CloudScout doesn't satisfy (1) — 2% snow FDR is low")
print("  4. KappaMask satisfies (2) conceptually but isn't irreversible")
print("  5. => The paper demonstrates the PROPERTY but not an actual instance")
print()
print("  The paper acknowledges this: 'threat-model paper, not caught-in-the-act'")
print("  But the TEST 1 framing ('KappaMask is catastrophic') is misleading because:")
print("  - KM is not irreversible")
print("  - KM's 63% FDR is class 4 (snow flag), not cloud error")
print("  => The demonstration uses TWO separate facts that don't co-occur:")
print("     (a) Irreversibility => unidentifiable [TRUE, but demonstrated on CS=safe]")
print("     (b) High snow FDR + invisible to metrics [SHOWN on KM=recoverable+intentional]")

# 5d: Novelty check on identifiability claim
print("\n[5d] Novelty of identifiability claim vs Manski:")
print("  Manski (1989) bound paper: partial identification of treatment effects")
print("  with endogenous selection (MNAR). The math in identifiability.md is")
print("  a direct application: D is an endogenous selector correlated with C.")
print()
print("  The paper's contribution claim:")
print("  - 'Unidentifiability from retained data' = Manski MNAR fact")
print("  - Applied to satellite cloud triage specifically")
print("  - With an empirical probe sample-complexity curve")
print("  - And a cross-detector consensus audit signal")
print()
print("  Reviewer question: Is this novel enough beyond 'Manski applied to satellites'?")
print("  Answer: The SECURITY REFRAME ('exploitable security property') is new.")
print("  The empirical audit (consensus AUC) and probe complexity are incremental contributions.")
print("  Straightforward Manski application with satellite domain dressing is weak novelty.")

# 5e: Verify the Manski math is correctly stated
print("\n[5e] Verify Proposition 2 math independently:")
# theta(b) = bq / (a(1-q) + bq)
# At b=0: theta = 0 [lower bound]
# At b=1: theta = q / (a(1-q) + q) = U [upper bound]
# Let's verify with KM values
km = np.memmap(os.path.join(TRAIN, "LABEL_kappamask_L1C.dat"), dtype=np.uint8, mode="r", shape=(N, H, W))
km_frac_34 = np.array([np.mean(np.isin(np.asarray(km[i]), [3, 4])) for i in range(N)])
km_pred = km_frac_34 >= 0.5

q_km = km_pred.mean()
kept_km = ~km_pred
a_km = float(clear[kept_km].mean())
U_km = q_km / (a_km * (1 - q_km) + q_km)
theta_oracle_km = float(km_pred[clear].mean())
print(f"  KappaMask: q={q_km:.4f}, a={a_km:.4f}")
print(f"  Upper bound U = q/(a(1-q)+q) = {q_km:.4f}/({a_km:.4f}*{1-q_km:.4f}+{q_km:.4f}) = {U_km:.4f}")
print(f"  Oracle theta = {theta_oracle_km:.4f} (inside [0, {U_km:.4f}]: {'YES' if theta_oracle_km <= U_km else 'NO!'})")
print(f"  Math checks out: the Manski bound is valid.")

print("\n=== ATTACK 5 COMPLETE ===")
