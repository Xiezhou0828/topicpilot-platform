# WS1/L2 — 2026 Historical Lifecycle Reconstruction Preflight

```text
TASK_ID=WS1/L2
FINAL_STATUS=COMPLETE_READ_ONLY_PREFLIGHT
CANONICAL_HEAD=b569430d2a358cab6a5915aeaacff2810df4913c
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_STATUS_BEFORE_REPORT_WRITE=DIRTY_OWNER_STATE_PRESERVED
RECONSTRUCTION_AUTHORITY=HISTORICAL_RECONSTRUCTED_SHADOW
FORWARD_SHADOW=SEPARATE_NOT_FOUND_IN_CANONICAL_CHECKOUT
POLICY_VERSION=topic-lifecycle-policy.provisional.1
CALCULATION_VERSION=topic-lifecycle-shadow.v1
HISTORICAL_RECONSTRUCTION_READY=PARTIAL
STRICT_CURRENT_ENGINE_REPLAY=NO
DATABASE_MUTATION=NO
HISTORICAL_RECONSTRUCTION_EXECUTED=NO
BACKFILL=NO
ENGINE_MUTATION=NO
DEPLOY=NO
PUSH=NO
NEXT_TASK_CHANGED=NO
```

## Decision

The current canonical evidence does not support a safe, strict historical
Lifecycle replay from `2026-01-01`. It supports only a bounded, research-only
input window beginning at `2026-08-07`, and even that window is
`PARTIAL/FAIL_CLOSED`, not fully reconstructable under the current
`TopicLifecycleEngine` adapter.

The only bounded PIT input window observed is:

```text
BOUNDED_PIT_INPUT_WINDOW=2026-08-07..2026-08-13
FORMAL_DATES=2026-08-07, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13
FORMAL_SNAPSHOTS=460 (92 topics x 5 dates)
STRICT_FULL_CELLS=0
PARTIAL_FAIL_CLOSED_CELLS=460
NOT_RECONSTRUCTABLE_CELLS=18,650
TOTAL_TOPIC_DATE_CELLS=19,110 (130 topics x 147 eligible dates)
BOUNDED_PIT_INPUT_COVERAGE=2.4071%
STRICT_FULL_RECONSTRUCTION_COVERAGE=0%
```

`2026-08-13` is the observed canonical forward boundary for this preflight.
No committed `FORWARD_SHADOW` readiness/reconciliation artifact was found to
extend the boundary to the current wall-clock date, so the report does not
assume that dates after `2026-08-13` exist.

## Evidence read

The preflight read the current canonical HEAD/status, the WS1 lifecycle series,
Lifecycle spec and engine, migration 0030/0031, the existing PIT materialization
and historical readiness reports, the canonical daily-bar read path, and the
local read-only API. The principal sources are:

- [`docs/series/WS1_TOPIC_DERIVED_INTELLIGENCE.md`](../../docs/series/WS1_TOPIC_DERIVED_INTELLIGENCE.md)
- [`docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md`](../../docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md)
- [`services/api/src/topicpilot_api/topic_lifecycle_engine.py`](../../services/api/src/topicpilot_api/topic_lifecycle_engine.py)
- [`services/api/src/topicpilot_api/topic_snapshot_engine.py`](../../services/api/src/topicpilot_api/topic_snapshot_engine.py)
- [`services/api/alembic/versions/0030_task_topic_daily_state_formal_authority.py`](../../services/api/alembic/versions/0030_task_topic_daily_state_formal_authority.py)
- [`services/api/alembic/versions/0031_task_topic_structural_role_score_projection.py`](../../services/api/alembic/versions/0031_task_topic_structural_role_score_projection.py)
- [`docs/reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md`](../../docs/reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md)
- [`docs/reports/TASK-TOPIC-HISTORICAL-STATE-LIFECYCLE-READINESS-AUDIT.md`](../../docs/reports/TASK-TOPIC-HISTORICAL-STATE-LIFECYCLE-READINESS-AUDIT.md)
- [`docs/reports/TASK-TOPIC-PIT-MEMBERSHIP-AND-DAILY-STATE-CONTRACT-CLOSURE.md`](../../docs/reports/TASK-TOPIC-PIT-MEMBERSHIP-AND-DAILY-STATE-CONTRACT-CLOSURE.md)

The canonical Alembic versions directory ends at `0031`; Migration 0032 is not
present in this checkout. No file or committed marker containing
`FORWARD_SHADOW`, `HISTORICAL_RECONSTRUCTED_SHADOW`, or a WS1 forward-shadow
readiness/reconciliation artifact was found in the inspected canonical source,
docs, or report paths. This is recorded as an evidence gap, not repaired here.

## Input inventory and availability

The machine-readable input inventory is in
[`historical-reconstruction-input-inventory.csv`](historical-reconstruction-input-inventory.csv).
The key findings are:

| Input | Observed state | Historical/PIT implication |
|---|---|---|
| TopicSnapshot | 460 formal rows, 92 topics on 5 dates | Available only on the bounded formal dates; no pre-boundary PIT snapshot history |
| Formal/PIT status | All observed rows `FORMAL/PIT_FORMAL/FINAL/PUBLISHED` | Formal publication boundary is clear for the 460 rows |
| Member facts | Existing closure records 4,235 facts; current snapshot aggregate sums to 4,236 | One-row reconciliation mismatch; strict replay fails closed until explained |
| Effective relation | 848 `v1` relations, effective from 2026-08-07, open-ended | Supports a boundary only; cannot backdate membership to January–August 6 |
| LiveTrackingUniverse | Current-state projection, not effective-dated | Not PIT-safe; current engine replay cannot use it as historical membership |
| Canonical daily bars | 63,826 accepted OHLCV rows, 507 symbols, 2026-02-02–2026-08-13 | Price facts are reusable research evidence, not historical Topic State by themselves |
| Price/correction lineage | Source lineage exists; adjustment/corporate-action continuity remains `UNKNOWN/PARTIAL_UNKNOWN` | Discontinuity, correction, or adjustment is fail-closed; no synthetic normalization |
| Identity/lifecycle | Immutable instrument-id joins; known lifecycle exclusion exists; security identity history is empty | Symbol/alias continuity and survivorship-safe historical identity are not proven |
| Previous Lifecycle state | No persisted Lifecycle result rows | Explicit boundary bootstrap is possible; no pre-boundary stage may be inferred |

The formal runtime readback also exposed `tw-reference-v1` for the PIT
membership/reference boundary and `sdf-reference-603-v1` in the historical
price lineage. The preflight does not silently treat those as interchangeable;
the future bounded route must preserve both lineages.

## Date × topic matrix

[`date-topic-availability-matrix.csv`](date-topic-availability-matrix.csv)
contains one row for every eligible weekday in the requested window after
excluding `HOLIDAY` and `SUSPENDED` dates from `tw-reference-v1`, crossed with
the 130 current topic identities.

```text
ELIGIBLE_TRADING_DATES=147
TOPICS=130
TOPIC_DATE_CELLS=19,110
PARTIAL_FAIL_CLOSED=460
NOT_RECONSTRUCTABLE=18,650
FULLY_RECONSTRUCTABLE=0
```

The 460 partial cells have the formal PIT snapshot/member-fact anchor, but the
current engine/input boundary still fails closed because of current-only
tracking-universe state, incomplete price-adjustment/corporate-action
continuity, and the one-row member-fact reconciliation gap. The 18,650
not-reconstructable cells include all pre-2026-08-07 dates and 38 missing topics
on each of the five formal dates.

The matrix marks every row with `authority=HISTORICAL_RECONSTRUCTED_SHADOW`.
It does not create or imply `FORWARD_SHADOW` evidence.

## Bootstrap and persistence

The first eligible boundary date is `2026-08-07`. A later bounded replay may
bootstrap with the explicit state:

```text
previous_stage=null
previous_stage_entered_at=null
previous_stage_trading_days=null
previous_candidate_stage=null
previous_candidate_streak=0
bootstrap_state=UNSEEN_PRIOR_STATE
history_state=TRUNCATED_AT_PIT_BOUNDARY
```

This is deterministic as a declared input, but it is not evidence that the
topic was in no stage before 2026-08-07. Confirmation/hysteresis, Day-N, and
stage-entry dates must be interpreted as beginning at the boundary. Details
are in [`bootstrap-determinism-review.md`](bootstrap-determinism-review.md).

## Fail-closed rules

The preflight establishes the following rules for any later bounded route:

- Do not use the current relation mapping to backfill dates before
  `2026-08-07`; that would introduce look-ahead and selection/survivorship bias.
- Do not use current `LiveTrackingUniverse` rows as historical membership or
  eligibility evidence.
- Missing close, previous close, status, or lineage remains missing; it is not
  converted to zero, flat, or a normal participation observation.
- `adjustment_state=UNKNOWN` and incomplete corporate-action coverage must
  remain explicit. Price discontinuities must fail closed, not be repaired by
  synthetic factors.
- The known `DELISTED` lifecycle event for instrument `6806` remains an explicit
  exclusion; absence of a lifecycle event for another instrument is not proof
  of historical eligibility.
- No Lifecycle stage before the first bounded input date may be inferred, and
  no reconstructed shadow row may be described as forward-produced evidence.

The PIT/lineage audit, including the 0032 and member-fact discrepancies, is in
[`pit-lineage-gap-audit.csv`](pit-lineage-gap-audit.csv).

## Frozen semantics and scope boundaries

This preflight did not change the five stages, numeric thresholds,
persistence/hysteresis, confidence, leader proxy, role semantics, score/grade,
Strength, volume, news, total score, recommendation logic, or publication
mode. It did not touch WS2, WS3, or WS4. It did not call a Lifecycle writer,
run historical reconstruction, backfill, migrate, deploy, push, or modify
`NEXT_TASK`.

## Owner decision and next bounded route

Owner decision is required before any implementation or replay route:

1. Accept or reject the boundary-truncated `2026-08-07..2026-08-13`
   `HISTORICAL_RECONSTRUCTED_SHADOW` input window for a separate research-only
   replay task.
2. Establish the canonical provenance and intended semantics of the absent
   Migration 0032 and absent forward-shadow artifacts.
3. Decide whether to provide PIT-safe historical tracking-universe evidence or
   to define a separate adapter contract that consumes the immutable PIT member
   facts without using current tracking state.
4. Reconcile the 4,235-versus-4,236 member-fact count before claiming exact
   coverage.

The smallest next route is a read-only reconciliation of
`topic_snapshot_member_facts`/snapshot aggregate lineage against the current
`TopicLifecycleEngine` input adapter for `2026-08-07..2026-08-13`. It should
produce evidence only; it should not modify the engine, schema, database, or
forward boundary.

## Handoff flags

```text
REPORT_CREATED=YES
APPLICATION_CODE_MUTATION=NO
LIFECYCLE_SEMANTICS_CHANGED=NO
SCHEMA_MIGRATION_MUTATION=NO
DATABASE_MUTATION=NO
HISTORICAL_RECONSTRUCTION=NO
BACKFILL=NO
SCHEDULER_MUTATION=NO
WS2_TOUCHED=NO
WS3_TOUCHED=NO
WS4_TOUCHED=NO
PUSH_REMOTE=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
OWNER_DIRTY_STATE_PRESERVED=YES
LOCAL_COMMIT_CREATED=NO
```
