# WS3 Real Historical Coverage Rerun and Mainline Resume

## Task identity

```text
TASK_ID=TASK-WS3-CORE-V0-REAL-HISTORICAL-COVERAGE-RERUN-AND-MAINLINE-RESUME-20260818
TASK_FINAL_STATUS=COMPLETE_COVERAGE_RERUN_AND_READINESS_ASSESSMENT
```

This is the existing WS3 Core V0 workstream. The task resumed the prior
coverage blocker and stopped at the coverage/readiness boundary. It did not
run the Core V0 walk-forward, produce performance metrics, compare variants,
or redesign any strategy definition.

## Required headline fields

```text
WS3_RESUME_POINT=PRIOR_WS3_CLEAN_REPRODUCIBLE_PREFLIGHT_BLOCKED_BEFORE_WALK_FORWARD
G2R_P_POLICY_RECONCILED=YES
OLD_CONTINUITY_BLOCKER_REMOVED=YES
REAL_HISTORICAL_ROW_COUNT=63826
REAL_HISTORICAL_DISTINCT_INSTRUMENTS=507
REAL_HISTORICAL_DATE_RANGE=2026-02-02..2026-08-13
SOURCE_RECONCILIATION_PASS=YES
SYNTHETIC_ROW_COUNT=0
DUPLICATE_OBSERVATION_COUNT=0
INVALID_IDENTITY_COUNT=0
MA60_CALCULABLE_INSTRUMENT_COUNT=507
MA60_NONCALCULABLE_INSTRUMENT_COUNT=0
MA60_CALCULABLE_INSTRUMENT_DATE_COUNT=33913
MA60_INSUFFICIENT_HISTORY_INSTRUMENT_DATE_COUNT=29913
METHOD_A_ELIGIBLE_INSTRUMENT_DATE_COUNT=16086
METHOD_A_BELOW_MA60_INSTRUMENT_DATE_COUNT=7589
KNOWN_EVENT_AFFECTED_WINDOW_COUNT=9778
DATA_GAP_COUNT=19
EARLIEST_DEFENSIBLE_CORE_V0_DATE=2026-05-12
LATEST_DEFENSIBLE_CORE_V0_DATE=2026-08-13
DEFENSIBLE_RESEARCH_TRADING_DAY_COUNT=66
CONTINUITY_UNKNOWN_STILL_FAIL_CLOSED=YES
CONTINUITY_UNKNOWN_BLOCKS_WS3_RESEARCH=NO
MA60_POLICY_CHANGED=NO
CORE_V0_STRATEGY_CHANGED=NO
WALK_FORWARD_METHODOLOGY_CHANGED=NO
WS2_CHANGED=NO
WS1_CHANGED=NO
WS4_CHANGED=NO
G2R_C_EXECUTED=NO
SHARED_G3_EXECUTED=NO
READY_FOR_CORE_V0_WALK_FORWARD=YES_WITH_BOUNDED_LIMITATIONS
READY_FOR_WS3_NEXT_MAINLINE_STEP=YES_BOUNDED_COVERAGE_ESTABLISHED
TASK_COMMIT_SHA=RECORDED_IN_FINAL_HANDOFF
```

## Resume and blocker reconciliation

```text
WS3_RESUME_POINT=
  Existing WS3 had completed the bounded Core V0 preflight/reporting work but
  stopped before walk-forward because a clean reproducible environment could
  not reach the verified real historical runtime and the old continuity gate
  treated UNKNOWN as unavailable.

OLD_BLOCKER=
  NO_REACHABLE_REAL_HISTORICAL_RUNTIME plus the obsolete requirement for
  AFFIRMATIVE_NO_EVENT / COVERED_NO_EVENT / CONTINUITY_PASS_BOUNDED before
  WS3 research.

OLD_BLOCKER_REMOVED_BY_G2R_P=
  YES for the continuity portion. Shared-G2R-P commit
  4f97a3f8195ce1f2eb254a2e4afcaa95a3e12240 was reconciled into this task as
  fb4ce16ea735746dff643507d4c5744991de6e51. The policy allows real research
  with valid identity, lineage, sufficient observations, and continuity
  UNKNOWN while preserving UNKNOWN as UNKNOWN and respecting verified events.

REMAINING_REAL_BLOCKERS=
  No global WS3 coverage blocker remains. Bounded limitations are 19
  instrument-day data gaps, 336 PARTIAL REC-A1 event-authority windows that
  remain tracking-only, downstream candidate/outcome evidence not rerun in
  this coverage-only task, and the actual walk-forward still intentionally
  not executed.
```

Shared-G1 runtime authority was independently reconciled before execution:

```text
REAL_HISTORICAL_ROW_LEVEL_ACCESS_READY=YES
REAL_HISTORICAL_ROW_COUNT=63826
REAL_HISTORICAL_DISTINCT_INSTRUMENTS=507
REAL_HISTORICAL_DATE_RANGE=2026-02-02..2026-08-13
TWSE_OFFICIAL_DAILY=39523
TPEX_OFFICIAL_DAILY=24303
MIGRATION_HEAD=0031_task_topic_structural_role_score_projection
READER=topicpilot_api.historical_read_model.read_historical_bars
```

The runtime source baseline and the reader output matched exactly. The active
universe contains 508 identities because one active `TEST` identity has no
real rows; the real historical universe remains 507 instruments and no
synthetic row was selected.

## Policy and protocol boundaries

The frozen protocol remains `core-v0-walk-forward.v1`:

- Development: 2026-02-02..2026-06-30
- Validation: 2026-07-01..2026-07-31
- Holdout: 2026-08-01..2026-08-13
- Outcomes: T+1/T+3/T+5/T+10, evaluation only
- At least 60 prior canonical trading sessions
- No tuning or optimization

Method A remains a hard `PRICE ABOVE MA60` filter. MA60 calculability,
below-MA60 ineligibility, insufficient history, event exclusion, and data
quality failures are reported as separate states. The prior global 20MA gate
was not restored.

Shared-G2R-P was consumed as the WS3 research contract:

- `EVENT_AWARE_RESEARCH` is the active WS3 research policy.
- Continuity UNKNOWN stays UNKNOWN and is still fail-closed for formal
  continuity claims; it does not block this WS3 research coverage rerun.
- No affirmative no-event or covered-no-event evidence was fabricated.
- 353 AUTHORITATIVE REC-A1 events were eligible for verified overlay; 19
  PARTIAL events remain residual authority uncertainty and were tracked only.
- The current authority has an EXCLUDE path for verified breaking events; no
  correction or annotation implementation was claimed, so both counts remain
  zero.
- Formal WS2 technical publication semantics were not changed.

REC-A1 provenance was consumed narrowly as the existing research-only frozen
dataset. Dataset content hash is
`4d9b4912bd1c4613510e60c5cf4b5a629c367e1c94dd733d3b1dc3f935e0eb5d`; the
clean-source artifact file SHA-256 is
`78f684d5b014f43f3b34393be1bc644805e67f05e18b21e7ab98d075a1cd60b2`.
The promoted canonical worktree presents the same logical JSON content with
byte SHA-256
`1091f97268ac01342a1803bc511780b9948c06c50176e367588b829af0d530e0` because
that checkout uses CRLF while the clean source worktree uses LF. The Git blob
and logical dataset content reconcile; this is a representation difference,
not an unauthorized dataset identity conflict.
The 154 reviewed UNKNOWN/residual uncertainty was not re-investigated and
Freeze was not reopened.

## Coverage results

The audit read every active identity through the existing bounded historical
reader for 2026-02-02..2026-08-13. It used chronological real observations,
raw close values, and the existing SMA_CLOSE_V1 trailing 60-observation
semantics. The strict Core V0 warm-up requires 60 prior observations, so the
first 60-observation MA60 values are distinguishable from the first temporally
eligible values.

| Metric | Result |
| --- | ---: |
| Real historical rows | 63,826 |
| Real instruments | 507 |
| MA60 calculable instruments | 507 |
| MA60 non-calculable real instruments | 0 |
| MA60 calculable instrument-days | 33,913 |
| Insufficient-history instrument-days | 29,913 |
| Method A eligible (close >= MA60) | 16,086 |
| Below MA60 | 7,589 |
| Verified event-affected / excluded windows | 9,778 |
| Verified event corrected | 0 |
| Verified event annotated | 0 |
| Data gaps | 19 |
| Duplicate observations | 0 |
| Invalid identity | 0 |
| Synthetic rows | 0 |
| Earliest defensible research date | 2026-05-12 |
| Latest defensible research date | 2026-08-13 |
| Defensible research trading days | 66 |

The 19 data-gap count is an instrument-day quality surface, not a fabricated
calendar fill and not a global readiness block. The affected instruments and
dates are preserved in the instrument and daily CSV surfaces. The 336
PARTIAL-authority windows are similarly visible in the surfaces and are not
treated as verified event exclusions.

## Required test cases

Cases A-G are covered by the focused test suite and the rerun evidence:

- A: sufficient history and above MA60 is calculable and Method A eligible.
- B: sufficient history and below MA60 is calculable but not Method A eligible.
- C: fewer than 60 valid observations is `INSUFFICIENT_HISTORY`.
- D: verified event intersection uses the existing EXCLUDE overlay.
- E: valid real OHLCV with continuity UNKNOWN is research-consumable without
  promoting UNKNOWN to PASS.
- F: duplicates, invalid identity, and malformed lineage remain fail-closed;
  the observed duplicate/identity/lineage counts were zero.
- G: synthetic data is not accepted as real historical input; observed
  synthetic row count was zero.

Focused validation result:

```text
22 passed in 2.70s
```

## Artifact chain

The machine-readable summary is
`reports/TASK-WS3-CORE-V0-REAL-HISTORICAL-COVERAGE-RERUN-AND-MAINLINE-RESUME-20260818/ws3-real-historical-coverage-summary.json`.
The daily surface is the corresponding
`ws3-daily-coverage-surface.csv`; the instrument surface is
`ws3-instrument-coverage-surface.csv`.

The readiness contract is
`ws3-core-v0-walk-forward-readiness.json`, and the policy reconciliation is
`ws3-shared-policy-reconciliation.json`. Test evidence is
`ws3-coverage-test-evidence.json`.

## State and scope confirmation

```text
RESEARCH_COVERAGE=COMPLETE
WALK_FORWARD=NOT_RUN
PERFORMANCE_METRICS=NOT_PRODUCED
STRATEGY_REVIEW=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
G2R_C=NOT_RUN
G2R_B4=NOT_RUN
SHARED_G3=NOT_RUN
MIGRATION=NOT_RUN
DATABASE_WRITES=NOT_RUN
CANARY=NOT_RUN
PRODUCTION=NOT_RUN
RENDER=NOT_RUN
DEPLOY=NOT_RUN
NEXT_TASK=UNCHANGED
OWNER_DIRTY_STATE=PRESERVED
WS1_WS2_WS4=UNCHANGED
```

This report is a research coverage closure, not release-chain or production
evidence. The next authorized WS3 mainline step is the existing Core V0
walk-forward preflight/execution, subject to its own candidate-panel,
definition-authority, and forward-outcome contracts; this task does not start
that step.
