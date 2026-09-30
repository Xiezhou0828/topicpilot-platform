# TASK-021 Follow-up: Trading-status authority and checkpoint observability

This is a bounded candidate implementation and read-only validation report. It
does not claim that the 2026-09-30 Production recovery or formal publication is
resolved. No Production operation was executed.

## Decision fields

```text
TASK_ID_OR_FOLLOW_UP_ID=TASK-021-FOLLOW-UP-AUTHORITY-AND-CHECKPOINT-OBSERVABILITY
INITIAL_MAIN_SHA=5ff2a91c5fad39d50434a3187011d93abcc058e3
SOURCE_SHA=5ff2a91c5fad39d50434a3187011d93abcc058e3
CANDIDATE_IMPLEMENTATION_SHA=81e3a589a55d098116f40eeff8f09ed376be567b
CURRENT_CANONICAL_MAIN_SHA=5ff2a91c5fad39d50434a3187011d93abcc058e3
BRANCH=codex/task-021-authority-checkpoint-followup
MERGE_STATUS=NOT_PERFORMED
PUSH_STATUS=NOT_PERFORMED
TASK_STATUS=IMPLEMENTED_CANDIDATE_READY_WITH_MIGRATION_BLOCKER
TASK_COMPLETE=NO
FOLLOW_UP_REQUIRED=YES
MIGRATION_REQUIRED=YES
MIGRATION_EXECUTED=NO
OWNER_DECISION_REQUIRED=YES
TASK_021_RESOLVED_BY_024=NO
TASK_021_RESOLVED_BY_THIS_CANDIDATE=NOT_PROVEN_UNTIL_PRODUCTION_VALIDATION
```

## Exact root cause

There are two independent defects, with one operational symptom:

1. The 2026-09-30 `2601` row had no valid close. TASK-024 only resolved
   explicit status evidence from the official daily provider and existing
   date-effective lifecycle evidence. It did not contain an independent
   official capital-reduction authority input. Therefore the reduction
   suspension could not be classified as a legitimate unavailable session.
   The fail-closed result remained `MISSING_MARKET_DATA` / provider
   `UNKNOWN`, and the formal market-facts readiness gate remained blocked.

2. `FORMAL_MARKET_FACTS:OFFICIAL` is a downstream institutional-flow and
   formal-readback checkpoint, not a market-provider ingestion checkpoint. The
   old generic checkpoint writer supplied provider counters with their integer
   defaults and wrote no semantic metadata. Its failed row therefore showed
   `providerRequestCount=0` and `providerFailureCount=0` even though those
   counters were not applicable to that checkpoint. The old artifact's empty
   `metadata={}` also prevents a more granular sub-stage attribution than the
   recorded `FORMAL_TOPIC_SNAPSHOT_NOT_READY` readiness failure.

The exact 021 failure boundary is consequently:

```text
PRIMARY_021_BOUNDARY=FORMAL_MARKET_FACTS / formal-topic readiness gate
2601_AUTHORITY_GAP=YES
FORMAL_MARKET_FACTS_READINESS_BLOCK=YES
CHECKPOINT_SEMANTIC_CLASSIFICATION_DEFECT=YES
PROVIDER_TRANSPORT_OR_READINESS_AS_PRIMARY_CAUSE=NO
PROVIDER_AUTHORITY_SOURCE_GAP_FOR_2601=YES
MULTIPLE_ROOT_CAUSES=YES
```

The 021 report proves that 552 market facts were persisted, the 2601
observation was skipped as `MISSING_MARKET_DATA`, and the first failed
checkpoint was the downstream `FORMAL_MARKET_FACTS:OFFICIAL` checkpoint with
empty metadata. It does not prove that the official-flow readback itself made a
provider request. The zero counters are therefore an observability ambiguity,
not evidence of a zero-request provider failure.

## Affected code paths

### Existing 021 path

```text
PostCloseUpdater
  -> official daily market batches
  -> 2601 has no close
  -> no explicit official daily status / no reduction authority
  -> MISSING_MARKET_DATA with provider UNKNOWN
  -> formal daily-market readiness remains incomplete
  -> FORMAL_MARKET_FACTS:OFFICIAL fails
  -> FINAL_PUBLICATION fails closed
```

### Candidate authority path

```text
read_daily_market_rows
  -> corporate_action_authorities_for(symbol, market, trading_date)
  -> read_effective_trading_status_authority
  -> CORPORATE_ACTION authority record
  -> resolve_effective_trading_status
  -> build_unavailable_instruments
  -> reconcile_daily_market(status_resolutions=...)
  -> formal readiness can cover a legitimate unavailable instrument
```

Candidate files:

```text
services/api/src/topicpilot_api/corporate_action_authority.py
services/api/src/topicpilot_api/reference_data/corporate_action_authorities.json
services/api/src/topicpilot_api/trading_status_authority.py
services/api/src/topicpilot_api/daily_market.py
services/api/src/topicpilot_api/live/post_close.py
services/api/src/topicpilot_api/production_forensic_readback.py
```

The 2601 input is a sanitized, date-effective official-source record; it is
not a Production DB write, historical backfill, single-day resolver special
case, or price payload. It uses the official TWSE reduction reference supplied
for the event:

```text
SYMBOL=2601
MARKET=TPE
ACTION=CAPITAL_REDUCTION_SHARE_EXCHANGE
EFFECTIVE_FROM=2026-09-23
EFFECTIVE_TO=2026-10-03
RESUME_DATE=2026-10-05
STATUS_MAPPING=SUSPENDED
REASON_CODE=CAPITAL_REDUCTION_TRADING_SUSPENSION
EXPECTED_CLOSE=false
```

### Candidate checkpoint path

```text
_checkpoint_event
  -> checkpointSemantic
  -> providerMetricsApplicability
  -> failureClassification
  -> nested readback failedSection/reasonCode
  -> production_forensic_readback
  -> N/A provider metrics are emitted as null in the sanitized artifact
```

The database columns `provider_request_count` and `provider_failure_count`
remain non-null integer columns with a default of zero. The candidate therefore
improves semantic metadata and forensic presentation, but cannot make the raw
database values true SQL `NULL` without a migration.

## TASK-024 coverage assessment

```text
TASK_024_OFFICIAL_DAILY_STATUS_AUTHORITY=YES
TASK_024_CORPORATE_ACTION_AUTHORITY=NO
TASK_024_2601_REDUCTION_COVERAGE=NO
TASK_024_CHECKPOINT_SEMANTICS=NO
TASK_024_PROVIDER_METRICS_NA_MODEL=NO
TASK_024_FORMAL_GATE_OVERLAY_FOR_CORPORATE_ACTION=NO
TASK_021_RESOLVED_BY_024=NO
```

The candidate adds the missing corporate-action authority and passes the
resolved status into daily-market reconciliation. Thus the 024 resolver is a
usable integration point, but 024 by itself did not override the 021 blocker.

## Status acceptance matrix

| State/evidence | Candidate result | Formal-publication effect | Notes |
| --- | --- | --- | --- |
| 2601 on 2026-09-23, 2026-09-30, or 2026-10-03 with the official reduction record | `SUSPENDED`, `LEGITIMATE_UNAVAILABLE` | The 2601 row is covered and does not block solely for missing price | No synthetic close is created |
| 2601 on 2026-10-05 with no valid close and no active reduction interval | `MISSING_MARKET_DATA` | Blocks | Resume date does not infer `AVAILABLE` or create a price |
| Any instrument with no close and no accepted status authority | `MISSING_MARKET_DATA` | Blocks | Missing price is never inferred as suspension |
| Any instrument with unsupported or ambiguous status evidence | `UNKNOWN` | Blocks | Fail-closed |
| Explicit official daily `AVAILABLE` but no close | `MISSING_MARKET_DATA` with `OFFICIAL_STATUS_EXPECTS_PRICE` | Blocks | Authority still requires price evidence |
| Valid same-session close during an event interval | `AVAILABLE`; event preserved | Does not block on that row | Existing 024 same-session precedence retained |
| TPE/TWO provider-ingestion checkpoint | `providerMetricsApplicability=ACTUAL` | Counters are meaningful | Provider request/failure counts remain actual |
| `FORMAL_MARKET_FACTS:OFFICIAL` checkpoint | `INSTITUTIONAL_FLOW_PUBLICATION_READBACK`; provider metrics `NOT_APPLICABLE` | Readback failure is classified separately | Raw DB N/A still needs migration |
| Cross-source conflict not observed in 021 | Candidate precedence is official daily > corporate action > lifecycle | Requires no 021 decision unless conflicting evidence appears | Owner may separately change precedence policy; no such conflict was present in the evidence |

## Implementation and validation status

```text
WORK_PACKAGE_A_TRADING_STATUS_AUTHORITY=IMPLEMENTED_CANDIDATE
WORK_PACKAGE_B_CHECKPOINT_OBSERVABILITY=PARTIAL_BLOCKED_BY_SCHEMA_NULLABILITY
CORPORATE_ACTION_SOURCE_VALIDATION=PASS
2601_20260930_STATUS=SUSPENDED / LEGITIMATE_UNAVAILABLE / NO_SYNTHETIC_PRICE
2601_20261005_STATUS_WITHOUT_CLOSE=MISSING_MARKET_DATA / BLOCKING
MISSING_MARKET_DATA_STILL_BLOCKS=YES
UNKNOWN_STILL_BLOCKS=YES
FORMAL_READBACK_FAILURE_CLASSIFICATION=IMPLEMENTED_CANDIDATE
NESTED_READBACK_REASON_AND_FAILED_SECTION=IMPLEMENTED_CANDIDATE
FORENSIC_ARTIFACT_NA_PRESENTATION=IMPLEMENTED_CANDIDATE
RAW_DB_NA_REPRESENTATION=NOT_IMPLEMENTED
```

The required schema decision is bounded and not implemented here:

```text
MIGRATION_REQUIRED=YES
MIGRATION_SCOPE=provide a governed nullable/optional representation for
  provider_request_count and provider_failure_count, or an equivalent
  persisted applicability model that cannot encode N/A as numeric zero
MIGRATION_EXECUTED=NO
MIGRATION_OWNER_APPROVAL=REQUIRED
```

No migration file was added. A separate Owner-approved implementation and
deployment task is required before the raw Production checkpoint can truthfully
represent N/A as SQL `NULL` or an equivalent governed value.

## Test and baseline attribution

The exact clean canonical-main baseline was checked in a separate detached
worktree at the same `CURRENT_CANONICAL_MAIN_SHA`:

```text
BASELINE_FULL_SUITE=981 passed, 60 skipped, 5 failed
CANDIDATE_FULL_SUITE=992 passed, 60 skipped, 5 failed
TEST_COUNT_DELTA=+11
BASELINE_FAILURES=the same five pre-existing WS3 tests missing required
  research JSON artifacts
NEW_FAILURES=0
FOCUSED_AUTHORITY_CHECKPOINT_SUITE=90 passed
CI_EQUIVALENT_BACKEND_SCOPE=905 passed, 4 skipped, 148 deselected
RUFF_TOUCHED_SCOPE=PASS
OPENAPI_DRIFT=PASS
GENERATED_CLIENT_CHECK=PASS
ALEMBIC_HEAD=0047_task_topic_role_strength_design_freeze (one head)
DOCKER_COMPOSE_CONFIG=PASS
GIT_DIFF_CHECK=PASS
```

The full-suite five failures are baseline-attributed and unrelated to this
candidate; the missing files are under the WS3 research-report prerequisites.
No existing test was removed.

## Owner decision and next bounded task

```text
OWNER_DECISION_REQUIRED=YES
OWNER_DECISION_SCOPE=approve nullable/optional checkpoint applicability schema,
  exact rollout/backward-compatibility plan, and a future current-day
  deployment/readback validation
NEW_IMPLEMENTATION_TASK_REQUIRED=YES
RECOMMENDED_NEXT_TASK=Owner-approved checkpoint applicability migration plus
  exact-SHA deployment and observation of the next eligible current-day
  POST_CLOSE; do not replay 2026-09-30
```

The candidate is not sufficient to claim TASK-021 production resolution. It is
sufficient to show that the 2601 authority gap and the checkpoint semantic gap
are separable, bounded implementation targets, with the schema migration and
Production validation still outstanding.

## Production operations explicitly not performed

```text
PRODUCTION_DB_MUTATED=NO
PRODUCTION_DEPLOYED=NO
API_DEPLOYED=NO
WORKER_DEPLOYED=NO
WEB_DEPLOYED=NO
POST_CLOSE_EXECUTED=NO
POST_CLOSE_RETRIED=NO
2026_09_30_RERUN=NO
HISTORICAL_BACKFILL=NO
HISTORICAL_REPLAY=NO
SCHEDULER_ACTIVATED=NO
TOPIC_SEMANTICS_CHANGED=NO
SCORE_CHANGED=NO
GRADE_CHANGED=NO
LIFECYCLE_CHANGED=NO
NEXT_TASK_CHANGED=NO
PRODUCTION_DB_READBACK_EXECUTED=NO
```
