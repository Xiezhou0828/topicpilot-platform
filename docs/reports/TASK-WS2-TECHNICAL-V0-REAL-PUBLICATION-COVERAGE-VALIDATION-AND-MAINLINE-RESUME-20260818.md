# TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818

## Closure outcome

```text
TASK_FINAL_STATUS=READY_FOR_WS2_NEXT_MAINLINE_STEP_WITH_BOUNDED_LIMITATIONS
READY_FOR_WS2_NEXT_MAINLINE_STEP=YES_WITH_BOUNDED_LIMITATIONS
READY_FOR_WS2_PRODUCTION=NO
```

This continuation task validated the real Stock Technical V0 publication path
in a task-owned worktree. It did not reopen Shared-G2, G2R-C, Shared-G3, or
affirmative no-event research. It did not promote, merge, push, deploy, render,
mutate Production, migrate, seed, rewrite canonical OHLCV, or change
`NEXT_TASK.md`.

The canonical branch was not promoted by this task because the stop contract
explicitly forbids promotion. The task worktree contains the minimal
known-event-aware publication integration and its validation evidence for the
Owner's later promotion decision.

## Provenance and cold-start reconciliation

| Item | Result |
|---|---|
| Canonical worktree | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Canonical branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Canonical HEAD at start | `3ab70b612cbb30335b43a5650d145488f9e8b2c1` |
| Canonical owner dirty inventory | 18 tracked dirty, 156 untracked; status fingerprint `48466f0963c81e3ecb4955f4e978a205ef4a0bbe` |
| Task worktree | `C:\Users\acer\Documents\Codex\ws2-real-publication-20260818` |
| Task branch | `codex/task-ws2-real-publication-coverage-20260818` |
| Task worktree base | `3ab70b612cbb30335b43a5650d145488f9e8b2c1` |
| WS2-R closure source | `C:\Users\acer\Documents\Codex\g2r` |
| WS2-R closure source SHA | `321420cd6fd5d9f4545a5d1a6bedb1565d18c5c1` |
| `WS2_R_CLOSURE_SOURCE_AVAILABLE` | `YES` |
| `WS2_R_CLOSURE_CANONICALIZED` | `NO` — object exists locally but is not an ancestor of canonical HEAD |
| `WS2_R_CLOSURE_RECONCILED` | `YES_SOURCE_AVAILABLE_NOT_CANONICALIZED` |
| `NEXT_TASK.md` raw SHA-256 | `FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70` |
| `NEXT_TASK.md` LF-normalized SHA-256 | `0e52696aaf6809ddfb7aee7298f532fedbd79e16f9b2e584ec6919f15ca417de` |
| Active parallel worktrees | Read-only enumerated and preserved; WS1/WS3/WS4 environments were not modified or removed |

The source closure report and forensic inventory were read as external
evidence only. No merge or hidden ancestry rewrite was performed.

## Phase 1 — publication-path forensic

The validated path is:

```text
canonical PostgreSQL PRICE/VOLUME observations
  -> read_historical_bars()
  -> deterministic Technical V0 series, including MA60 / SMA_CLOSE_V1
  -> indicator-specific required window and as-of binding
  -> known-event-aware official lookup envelope
  -> fail-closed event disposition and MA60 eligibility
  -> build_technical_publication()
  -> /api/v2/stocks/{symbol}/technical read model contract
```

| Question | Finding |
|---|---|
| Q1. Real canonical historical rows? | `YES`. The read-only runtime used `topicpilot_api.historical_read_model.read_historical_bars` and returned real `TWSE_OFFICIAL_DAILY` rows for `TPE:1314` and `TPE:2330`. |
| Q2. Point-in-time MA60? | `YES`. The MA60 window ends at the requested `2026-08-13` session and binds the accepted observation window, source lineage, and retrieval/as-of metadata. |
| Q3. Look-ahead? | `NO`. Existing no-look-ahead test passed; the real probe used no observation after the as-of session. |
| Q4. Known-event layer connected? | Canonical start state: `NO`; the known-event-aware layer was only in the non-canonical R source. Task worktree: `YES`, connected inside `_technical_evidence()` and exposed in the publication payload. Callers must still supply a successful official lookup envelope. |
| Q5. Lookup failure fail closed? | `YES` in the task worktree: `EVENT_LOOKUP_UNAVAILABLE` makes MA60 unavailable and does not become `UNKNOWN`-to-formal implicitly. |
| Q6. Known verified event handled? | `YES` in the task worktree: intersecting verified event returns `KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING`; local `TPE:2330` and external `TPE:2380`/`TWO:5904` controls were blocked under `EXCLUDE`. |
| Q7. Successful no-match allowed? | `YES`. A successful identity-bound, normalized, versioned lookup may return `NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND`; continuity remains `CONTINUITY_UNKNOWN`. No `PROVEN_NO_EVENT` or `COVERED_NO_EVENT` is fabricated. |
| Q8. Legacy blocker? | The old fail-closed behavior remains intentional when no lookup envelope is supplied. The task removes the conflicting blanket gate only for the Owner-approved successful no-match overlay; it does not weaken unknown/failure semantics. |

The minimal implementation change was limited to the known-event policy helper,
Technical V0 evidence integration, the policy contract increment, focused
tests, and bounded read-only probe tooling. MA60, indicator algorithms, output
set, strategy semantics, and WS1/WS3/WS4 scope were unchanged.

## Real data coverage

The read-only database audit recorded:

```text
REAL_HISTORICAL_ROW_COUNT=63826
REAL_HISTORICAL_DISTINCT_INSTRUMENTS=507
REAL_HISTORICAL_DATE_RANGE=2026-02-02..2026-08-13
MIGRATION_HEAD=0031_task_topic_structural_role_score_projection
CANONICAL_LIFECYCLE_ROWS=1
CANONICAL_CORPORATE_ACTION_TABLE_COUNT=0
```

Full 507-instrument publication was not asserted because the official event
lookup envelope is caller-supplied and was only defensibly revalidated for the
bounded control set. The deterministic probe therefore used four real-reader
cases (396 real instrument-date rows; three distinct local identities) plus
two preserved external positive controls. No fixture or synthetic bar was
used.

| Probe | Real rows | MA60 result | Overall payload | Classification |
|---|---:|---|---|---|
| `TPE:1314` successful no-match | 125 | `FORMAL`, value `8.0278333333333333333333333333333333333333333333333` | `FORMAL` | Expected successful no-match; continuity `UNKNOWN` |
| `TPE:2330` intersecting verified event | 126 | `UNAVAILABLE`, `KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING` | `FORMAL` via unaffected shorter indicators | Expected known-event handling |
| `TPE:1314` lookup timeout | 125 | `UNAVAILABLE`, `EVENT_LOOKUP_UNAVAILABLE` | `UNAVAILABLE` | Expected fail-closed lookup failure |
| `TPE:1314` bounded 20-row history | 20 | `UNAVAILABLE`, `UNAVAILABLE_INSUFFICIENT_HISTORY` | `FORMAL` via shorter indicators | Expected insufficient history |

Required readiness counters are recorded in
`ws2-technical-v0-real-publication-coverage-summary.json`. The strict MA60
gate results are:

```text
MA60_CALCULABLE_COUNT=3
MA60_INSUFFICIENT_HISTORY_COUNT=1
TECHNICAL_V0_ELIGIBLE_COUNT=1
TECHNICAL_V0_INELIGIBLE_COUNT=3
KNOWN_EVENT_HANDLED_COUNT=3
KNOWN_EVENT_BLOCKED_COUNT=3
EVENT_LOOKUP_FAILURE_COUNT=1
PUBLICATION_AVAILABLE_COUNT=1
PUBLICATION_BLOCKED_COUNT=3
PUBLICATION_UNKNOWN_COUNT=0
PUBLICATION_ERROR_COUNT=0
```

`KNOWN_EVENT_HANDLED_COUNT=3` includes the local `TPE:2330` control and the
two external official controls. `TPE:2380` (TWSE capital reduction, raw source
SHA `698f899207b2bba0b28e5f7e0b530d2061f0bb0f80f564c8ce3de416885c44e3`) and
`TWO:5904` (TPEx par-value change, raw source SHA
`f73f6c025d266264b5e25fcb534fb77c606f639e3c00f25807e460f3f00301fa`) are not
claimed as local canonical-history probes because neither has a local
canonical corporate-action row or local OHLCV identity in the 507-instrument
set.

## Quality, PIT, and reproducibility

All four local outputs carried the correct identity, as-of session, required
and actual MA60 window, `SMA_CLOSE_V1`, versioned source lineage,
`event_lookup_state`, publication state, and machine-readable availability
reason. The ordinary control's MA60 window was `2026-05-20..2026-08-13`.
No future observation, browser calculation, synthetic row, or strategy
acceptance semantic entered the payload.

The bounded runner was executed twice with the same database snapshot and
control inputs:

```text
RUN_1_SUMMARY_SHA256=c6ae5b3fed22a5912c3f4c0513a33c1fd7477840f1e2466b88c4ab5bb6fc9784
RUN_2_SUMMARY_SHA256=c6ae5b3fed22a5912c3f4c0513a33c1fd7477840f1e2466b88c4ab5bb6fc9784
PUBLICATION_REPRODUCIBLE=YES
LOOK_AHEAD_LEAKAGE_DETECTED=NO
```

## Remaining outcome classification

| Class | Count | Finding |
|---|---:|---|
| `EXPECTED_POLICY_OUTCOME` | 3 | One known-event exclusion, one genuine lookup failure, one insufficient-history result |
| `DATA_LIMITATION` | 2 | Caller-supplied event envelope requirement; official `2380`/`5904` evidence is not canonical persistence |
| `IMPLEMENTATION_DEFECT` | 1 discovered / 0 remaining in task worktree | Canonical start path lacked the known-event-aware overlay; minimally fixed and tested in this isolated worktree |

The implementation defect is not silently treated as already canonical. It is
resolved in the task branch but remains pending Owner-controlled promotion.
The policy outcomes and data limitations do not justify reopening the blocked
Shared/G2R investigations.

## State ledger

```text
IMPLEMENTATION_STATE=TASK_WORKTREE_MINIMAL_KNOWN_EVENT_OVERLAY_VALIDATED
VALIDATION_STATE=PASS_BOUNDED_REAL_READER_CONTROLS_REPRODUCIBILITY
CANONICAL_STATE=NOT_PROMOTED_BY_TASK; OWNER_CANONICAL_HEAD_PRESERVED
RELEASE_STATE=NOT_RUN
PRODUCTION_STATE=NOT_RUN
DATABASE_WRITE_STATE=NOT_RUN
MIGRATION_STATE=NOT_RUN; HEAD_READ_ONLY
PROVIDER_SCHEDULER_STATE=NOT_RUN
DEPLOYMENT_STATE=NOT_RUN
PROMOTION_STATE=NOT_RUN
NEXT_TASK_STATE=UNCHANGED
```

## Evidence index

- Contract increment: `docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md`
- Closure report: this file
- Real coverage summary: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-real-publication-coverage-summary.json`
- Reason distribution: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-publication-reason-distribution.json`
- Controls: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-positive-negative-controls.json`
- Quality audit: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-publication-quality-audit.json`
- Reproducibility: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-publication-reproducibility.json`
- Readiness: `reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818/ws2-technical-v0-next-step-readiness.json`
- Rerunnable probe: `scripts/ws2_technical_v0_real_publication_probe.py`

## Validation record

```text
FOCUSED_TESTS=30 passed, 5 skipped (existing PostgreSQL fixture skip only)
TECHNICAL_AND_KNOWN_EVENT_TESTS=22 passed
PY_COMPILE_COMPILEALL=PASS
RUFF_CHANGED_SCOPE=PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN_CHANGED_SCOPE=NO_MATCHES
REAL_DB_PROBE_RUNS=2 PASS
```

The task stops here. No downstream WS2 task, production action, or canonical
promotion is initiated.
