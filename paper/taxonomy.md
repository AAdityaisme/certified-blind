# A taxonomy of deployed irreversible AI gatekeepers (research-agenda #4)

Where does "Certified Blind" bite in the wild? An irreversible gatekeeper is exposed to silent targeted
destruction to the degree that it (a) is **irreversible** (discarded data is unrecoverable), (b) admits a
**targetable rare slice**, (c) has a **small aggregate footprint** (harm invisible to headline metrics), and
(d) has **low current auditability**. We score deployed systems on each axis (L/M/H) and derive an exposure
rank + the cheapest applicable remedy.

## Scoring (H = worse / more exposed)

| # | System | Irreversible | Rare targetable slice | Aggregate-footprint invisibility | Current auditability (H=low) | Exposure |
|---|---|---|---|---|---|---|
| 1 | **Onboard satellite EO triage** (Φ-Sat-class; downlink only "clear") | H | H (snow/desert/fire ~1–3%) | H | H (data never downlinked) | **HIGH** |
| 2 | **Edge/IoT event filtering** (keep only "events", bandwidth-capped) | H | H (rare event classes) | H | H (dropped at source) | **HIGH** |
| 3 | **Autonomous medical triage** (discard "normal" scans/signals) | H | H (rare pathology on a demographic) | M | M (some retention by law) | **HIGH** |
| 4 | **Spacecraft/AV telemetry compression-triage** | H | M | H | H | **HIGH** |
| 5 | **Acoustic/wildlife onboard monitoring** (detect-and-drop) | H | H (rare species/call) | H | H | **HIGH** |
| 6 | **Training-data / RLHF curation** (filter "low-quality") | M | H (topic/dialect/viewpoint) | M | M (curation logs vary) | **MED-HIGH** |
| 7 | **Log/trace retention sampling** (keep 1% of traces) | M | H (rare error class / user cohort) | H | M (sampling policy known) | **MED** |
| 8 | **Content moderation / ingestion filters** | M | H (identity/dialect) | M | M (DSA transparency logs) | **MED** |
| 9 | **Spam/abuse pre-filters** (drop before human review) | M | M | M | M | **MED** |
| 10 | **LLM routing** (downgrade to cheap model) | L | M | M | L (retry/logs) | **LOW** (our control) |

## Reading the table
- **The most exposed class is bandwidth-constrained onboard/edge triage** (#1, #2, #4, #5): the data is
  destroyed at the source with no ground-side copy, so *no retained-data audit can exist*. These are exactly
  where the paper's unidentifiability result is not a modeling choice but a physical fact.
- **The highest-stakes is autonomous medical triage** (#3): a certified "discard normal" model that
  systematically drops a rare pathology concentrated in a demographic realizes the exact threat with clinical
  consequences; partial retention (legal record-keeping) is the mitigating factor.
- **The most policy-tractable are the software pipelines** (#6–#9): curation, log sampling, and moderation
  are semi-reversible (logs, DSA transparency), so a stratified or diff-based audit is *possible* today and
  should be *required*.

## Remedy mapping (from the paper's defenses)
- **Onboard/edge (#1,2,4,5):** cannot stratify before discard → the only external reference is the
  **random-downlink certification** (~5% bandwidth overhead certifies against a targeted attack; §7.5). This
  is the concrete standard to mandate for irreversible hardware gatekeepers.
- **Medical (#3):** mandate a stratified retention quota per protected slice (age/sex/site) so the labeled
  probe (k≈10–15) is always available — turns an irreversible gatekeeper semi-reversible by policy.
- **Software pipelines (#6–9):** the data mostly survives → require the **discovery scan** (probe the
  protected set) or the **label-free cross-detector / model-diff** audit (open-world). Cheap and deployable now.

## The governance one-liner
Regulation of AI data-gatekeepers should not accept aggregate accuracy as certification. For *irreversible*
gatekeepers, require a random-sample external reference (bandwidth-priced); for *recoverable* ones, require a
stratified or diff-based audit of the discarded set. The unifying rule: **you must budget for the audit
before the data is destroyed, because after, the harm is unidentifiable.**
