# TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822

## Formal closure

### Scope and disposition

This is an aggregation-only continuation of `TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821` inside the existing WS3 Core V0 Walk-forward Research line. It reads the committed path-aware outcome artifact and the already-committed Owner/audit artifacts. It does not rebuild the A2 cohort, rescan raw OHLCV, change A1/A2 semantics, fit thresholds, train a model, accept a strategy, mutate production, deploy, push, or change NEXT_TASK.

Final disposition: **STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED**.

### Source artifacts read

- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/a2-path-aware-outcomes.csv` — `3fa287b26a8db07e540a1f45bb663af52df4f88bed7156c69b357d31c9005538`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/a2-source-reconstruction-reconciliation.csv` — `805c13522e99d329cd0a3457526004a09810771078b0840b7990a80e1e6d1111`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/failure-attribution.csv` — `82c5da555e5475819a8e31d267011a45ccb29940c73f8db3bc57da6892543932`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/owner-label-reconciliation-30-case.csv` — `8255953aa18a86a7666f9c6d70aeae7399397ebfd5063cdc68b574988b918d19`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/filter-ablation.csv` — `1ca548f70a866612fbd2032c28c7581a5e01869e6c42565da735903c518a54aa`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/extension-feature-comparison.csv` — `39fc46e5f3760b796602979a809068252141014d12736b151bfc8a6bfb7ad647`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/corporate-action-data-quality-audit.csv` — `76caf3549db11bf22b5a1f26cc20f0504dea8490c32712a836011512d76822c2`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/regime-attribution-audit.csv` — `116a24ccacafba50650a9efe4380c851716c1b1750e23de8b90b561136941455`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/run-summary.json` — `1306499b6aff926437de92234f1ccab6ea982ae59dd39bc69c60d45c2365340d`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/path-aware-outcome-manifest.json` — `cef8da5ee7006ee23b2a919528bdfeb6b47e8f88ed6f37edbd41ddb860b35392`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/owner-decision-memo.md` — `69a0b081c7c4a1fcd33bdd2477e1c119b4b6816339f69279bd909ca7ea7c9246`
- `reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/formal-closure-report.md` — `6846363ddb9dff1b5184aebedd3843d709bcea996fa95bf81fdeb459c4344fd7`
- `reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md` — `a8479ccd991bd5f0b233bede2daf8b415719fa5b19f06bd393cb69c698a0787d`
- `reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/ws3-a2-historical-label-audit-master.csv` — `2deac1a8e4b35c019f0380d05d9f4315024f91e6912735eef55181db753df76d`
- `reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/formal-closure-report.md` — `7dc13b9808440d6636ba644e9469dff55c9f9cd912b964fb8cd224997ba10cf7`
- `docs/reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/formal-closure-report.md` — `353130cf70ad75857793ce842acc014a1a5d2b88bac5bcebbd4ccc34f42c2eee`
- `reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/ws3-a-structural-eligibility-run-summary.json` — `4d46abb0224155a0d87349f4fd83a310630167a0bd55126e65e8c216d725a656`
- `tools/ws3_a2_outcome_reconstruction.py` — `70f943fbb9fe4236a8a3f8c91220c27686e12d84abbe25bd302fa668feabf758`

The prior reconstruction helper was read only to confirm field semantics. The current run performed no raw panel scan (`RAW_PANEL_SCANS=0`) and no event-mining/cohort rebuild (`EVENT_MINING_RERUN=0`, `COHORT_REBUILD=0`). It read one committed path-aware CSV (`PATH_AWARE_ARTIFACT_READS=1`).

### Semantics confirmed and fail-closed rules

- A2 event cohort: 5277 events; path file rows: 52770 = event × horizons 1..10.
- Anchor: signal-day `a2_close` carried by the frozen A2 event panel.
- Endpoint: future close / anchor close − 1.
- MFE: maximum future high / anchor close − 1 over the horizon.
- MAE: minimum future low / anchor close − 1 over the horizon.
- Only `COMPLETE_RAW_PATH` rows with non-null metrics and empty suppression reason enter an aggregate. `UNKNOWN_RAW_ONLY` is retained as source state and is not interpreted as adjusted truth.
- For barrier races, the first cumulative horizon at which MFE/MAE crosses each barrier is used. If both barriers first cross on the same session, the result is `SAME_SESSION_ORDER_UNKNOWN`; intraday high/low ordering is not guessed.
- Unresolved corporate-action/discontinuity rows remain excluded from interpretation. The previous audit has 85 suppressed events, including `2327/2025-08-05`.
- MA60-above hard eligibility (A method) remains the governing eligibility context; this report does not return to MA20 eligibility.

### Reconciliation gates

- Expected previous T10 proxy counts: positive 2,587, non-positive 2,559, unknown 131. Current derived counts: positive 2587, non-positive 2559, unknown 131.
- Strict interpretable complete path events: H5 5160; H10 5146. The previous report's `raw_path_complete_h10_event_count` was 5229 and is a different, pre-interpretation raw/maturity counter. This run requires every row 1..H to be complete, non-null, and unsuppressed; the 5,146 H10 T10-proxy denominator therefore reconciles to the current fail-closed rule rather than silently using 5,229.
- Same-session order-unknown counts for +5/−5: H5 107; H10 108.
- Deterministic replay payload: `8e15ef2637ddc2beddeef935350c86dbf9323ade21e1f56e44cb916dc11b1a6b`.

### Research findings

1. Endpoint/path disagreement is measurable: among T10 endpoint-non-positive events, MFE10 ≥5% is 967/2559 (0.37788198515) and MFE10 ≥10% is 328/2559 (0.128175068386). This shows why endpoint-only labels can be incomplete; it does not establish a tradable strategy outcome.
2. Positive endpoint/adverse path is also present: H10 endpoint-positive events with MAE10 ≤−5%: 634/2587; with MAE10 ≤−10%: 136/2587.
3. Barrier race and time-to-opportunity are reported without selecting a hold/exit rule. Same-session ties are explicitly unknown.
4. Candidate price/volume filters are ablations with opportunity-cost columns. No candidate filter is promoted.
5. Extension analysis uses only existing carried extension fields. Close/MA20, close/MA60, prior returns, consolidation-base distance, and full acceleration are not joined to event-level path outcomes in the existing artifacts and are marked unavailable rather than recomputed.
6. Corporate-action and regime audits remain blockers for interpretation of affected cases. `3675/2026-07-06` remains performance-included but regime UNKNOWN because PIT-safe index/breadth/theme-peer evidence is unavailable.

### Required outputs

- `formal-closure-report.md`
- `run-summary.json`
- `mfe-mae-distribution.csv`
- `endpoint-vs-path-disagreement.csv`
- `positive-endpoint-adverse-path.csv`
- `barrier-race-summary.csv`
- `time-to-opportunity.csv`
- `old-t10-proxy-reconciliation.csv`
- `path-aware-filter-ablation.csv`
- `extension-path-descriptive-analysis.csv`
- `owner-30-case-label-input-template.csv`
- `A2-MFE-MAE-BARRIER-RACE-OWNER-DECISION-MEMO.md`
- `reproducibility-source-manifest.json`

### Governance flags

```text
WS3_ONLY=YES
A_SETUP_ACCEPTED=NO
A_STRATEGY_ACCEPTED=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
PUSH=NO
REMOTE_MERGE=NO
NEXT_TASK_CHANGED=NO
OWNER_REVIEW_REQUIRED=YES
STATUS=STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED
```

Closure is complete as an evidence-only research input. It is not strategy acceptance or production authorization.
