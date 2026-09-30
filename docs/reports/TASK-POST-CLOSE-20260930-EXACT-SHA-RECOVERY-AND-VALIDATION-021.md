# TASK-POST-CLOSE-20260930-EXACT-SHA-RECOVERY-AND-VALIDATION-021

## Final disposition

The authorized Worker deployment and runtime gates passed. Exactly one
terminal `2026-09-30` POST_CLOSE recovery was executed through the governed
Worker interface. The recovery reached `PARTIAL`, with 552 of 553 requested
observations successful and one observation skipped. The protected readback
confirmed that the fail-closed formal publication gate remained blocked.

Per the task failure policy, no second recovery was attempted. This task is
not complete.

```text
TASK_ID=TASK-POST-CLOSE-20260930-EXACT-SHA-RECOVERY-AND-VALIDATION-021
TASK_STATUS=RECOVERY_FAILED_DOWNSTREAM_PROCESSING
TASK_COMPLETE=NO
```

## Deployment and runtime provenance

The repository was reconciled to the then-current canonical `origin/main`
before release. The deployed Worker contains the TASK-020 provider readiness
remediation and the TASK-020 owner schedule freeze.

```text
CANONICAL_SHA=89f46f8558eed0e43a8b96fb7e0e747659e8a406
DEPLOY_TARGET_SHA=89f46f8558eed0e43a8b96fb7e0e747659e8a406
WORKER_RELEASE_RUN_ID=36698845709
WORKER_DEPLOYED_SHA=89f46f8558eed0e43a8b96fb7e0e747659e8a406
WORKER_RUNTIME_SHA=89f46f8558eed0e43a8b96fb7e0e747659e8a406
WORKER_TIMEZONE=Asia/Taipei
WORKER_POST_CLOSE_START=13:45
```

Governed release validation passed for the exact SHA. API, Web, and migration
apply were not selected. The Worker runtime readback returned `READY` and
reported its SHA from `RENDER_GIT_COMMIT_OR_GIT_SHA`. A protected runtime
readback after the Render environment correction returned:

```text
{"readbackStatus":"READY","runtimeGitSha":"89f46f8558eed0e43a8b96fb7e0e747659e8a406","source":"RENDER_GIT_COMMIT_OR_GIT_SHA"}
TOPICPILOT_LIVE_TIMEZONE=Asia/Taipei
TOPICPILOT_LIVE_POST_CLOSE_START=13:45
```

## Authorized recovery

The only recovery command issued was the canonical governed equivalent of:

```text
topicpilot-live --mode post-close --once --run-date 2026-09-30 --recover
```

No targeted symbols, manual SQL data repair, historical replay, or second
recovery command was used.

```text
RECOVERY_TARGET_DATE=2026-09-30
RECOVERY_RUN_ID=2284ae32-fb83-45bf-bad5-4dd506c3d9a8
RECOVERY_STATUS=PARTIAL
RECOVERY_REQUESTED=553
RECOVERY_SUCCESS=552
RECOVERY_FAILURE=0
RECOVERY_SKIPPED=1
RECOVERY_RETRY=0
PROVIDER_POINT_COUNT=552
FAILURE_CODES=FORMAL_TOPIC_SNAPSHOT_NOT_READY
SNAPSHOT_STATUS=BLOCKED_DAILY_MARKET_NOT_READY
IDEMPOTENT_REUSE=false
```

The scheduler decision used `POST_CLOSE_START=13:45`,
`timezoneName=Asia/Taipei`, three bounded readiness attempts, and a maximum
total readiness wait of 90 seconds. The terminal result was not promoted to a
successful recovery because the formal topic snapshot was not ready.

## Provider and market results

The following market totals are protected forensic readback totals for the
recovery run identity. They include the attempts associated with the natural
run and its same-session terminal recovery; they are not presented as a count
of only the final command's newly inserted rows.

```text
TPE_ATTEMPT_COUNT=694
TPE_SUCCESS=346
TPE_FAILURE=347
TPE_SKIPPED=1
TPE_INSTRUMENT_COUNT=347

TWO_ATTEMPT_COUNT=412
TWO_SUCCESS=206
TWO_FAILURE=0
TWO_SKIPPED=206
TWO_INSTRUMENT_COUNT=206

ERROR_CODE_DISTRIBUTION=EXCHANGE_NO_DATA:347, MISSING_MARKET_DATA:207, NONE:552
PROVIDER_STATUS_DISTRIBUTION=AVAILABLE:552, ERROR:347, UNKNOWN:207
```

The canonical market-batch adapter path emitted 552 provider points in the
terminal recovery, with no per-symbol provider refetch after a known
market-level terminal state. The persisted forensic artifact does not contain
a raw HTTP transport counter, so the market request values below are explicit
inferences from the canonical one-fetch-per-market cache rather than claimed
transport telemetry:

```text
TWSE_MARKET_REQUEST_COUNT=1 (inferred; raw transport counter not persisted)
TPEX_MARKET_REQUEST_COUNT=1 (inferred; raw transport counter not persisted)
READINESS_RETRY_COUNT=0 (run/checkpoint evidence)
PER_SYMBOL_PROVIDER_REFETCH_DETECTED=NO
```

The run's provider metadata was `OFFICIAL_DAILY_ROUTER` with adapter version
`official-daily-router.v1`. The one skipped observation was represented by the
`MISSING_MARKET_DATA` path; the historical same-run attempt totals also retain
347 `EXCHANGE_NO_DATA` failures from the earlier market attempts.

## Protected forensic readback

The protected SELECT-only workflow completed successfully:

- Workflow run: [36705147717](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/36705147717)
- Reported forensic tool SHA: `89f46f8558eed0e43a8b96fb7e0e747659e8a406`
- Database role/session user: `topicpilot_forensic_readonly`
- Transaction read-only: `True`
- Mutation privileges present: `NO`
- Artifact checkpoint count: `64`

The readback recorded the run as `POST_CLOSE`, `PARTIAL`, with
`started_at=2026-09-30T13:37:22.608633+08:00` and
`completed_at=2026-09-30T18:52:25.157241+08:00`. The provider status was
`AVAILABLE`; the formal readiness failure was recorded separately as
`FORMAL_TOPIC_SNAPSHOT_NOT_READY`.

## Checkpoint validation

The durable checkpoint artifact contained 64 checkpoints. The timeline was:

1. `SESSION_VALIDATION` batch 0, attempt 1: `COMPLETED`.
2. `INPUT_READINESS` batch 1, attempt 1: `COMPLETED`.
3. TPE market batches TPE1-TPE7 completed after their bounded checkpoint
   retry, each with 20/20 successful observations.
4. TPE8 completed `PARTIAL`, with 19 successes and one skipped observation.
5. TPE9-TPE17 completed with 20/20 observations; TPE18 completed with 7/7.
6. TWO19-TWO28 completed with 20/20 observations; TWO29 completed with 6/6.
7. `FORMAL_MARKET_FACTS:OFFICIAL` batch 150 was first `IN_PROGRESS`, then
   attempt 2 was `FAILED` with no provider request and no provider failure
   count.
8. `FINAL_PUBLICATION` batch 3 was `FAILED`.
9. `COMPLETION` batch 4 was `PARTIAL`.

```text
CHECKPOINT_COUNT=64
FIRST_FAILED_CHECKPOINT=FORMAL_MARKET_FACTS:OFFICIAL|batch=150|attempt=2|status=FAILED|processed=0|succeeded=0|failed=1|providerFailureCount=0|providerRequestCount=0|metadata={}
LAST_COMPLETED_CHECKPOINT=FORMAL_MARKET_FACTS:TWO:29|batch=150|attempt=1|status=COMPLETED|processed=6|succeeded=6|failed=0
PROVIDER_FAILURE_CHECKPOINT_PRESENT=NO
PROVIDER_ERROR_CODE_RECORDED=YES (readback error distribution and terminal failure code)
```

The first failed phase was therefore the downstream formal market-facts /
formal-topic readiness boundary, not a missing Worker deployment or a second
provider retry. The failed checkpoint hash was
`b2c4623e034695348eef04b72e80bc629d1195ad2c50d97b6b8733067c459b1e`.
`A9_B2_FORMAL_PROCESSING` and final publication did not reach a publishable
state. `FINAL_PUBLICATION.publicationReadback` was null.

## Formal outputs and Today validation

Market facts were persisted for 552 observations, but the formal snapshot was
not published. No successful Today/Home readback was authorized or claimed
after the fail-closed terminal result.

```text
CANONICAL_PRICE_DATE=2026-09-30 (552 market facts persisted; formal readiness not achieved)
FORMAL_TOPIC_PUBLICATION_DATE=NOT_PUBLISHED
HOME_PUBLICATION_DATE=NOT_PUBLISHED
TOPIC_STRENGTH_STATUS=NOT_EVALUATED/NOT_PUBLISHED
TOPIC_GRADE_STATUS=NOT_EVALUATED/NOT_PUBLISHED
TOPIC_LIFECYCLE_STATUS=NOT_EVALUATED/NOT_PUBLISHED

TODAY_MARKET_OVERVIEW_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_SIGNAL_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_MAINLINE_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_TOPIC_PULSE_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_HEATING_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_COOLING_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
TODAY_OPPORTUNITY_STATUS=NOT_PERFORMED_DUE_TO_FAIL_CLOSED_RECOVERY
```

## Safety boundary and final status

```text
PRODUCTION_DB_MUTATED_BY_NORMAL_RECOVERY=YES
HISTORICAL_BACKFILL=NO
20260929_REPLAYED=NO
API_DEPLOYED=NO
WEB_DEPLOYED=NO
MIGRATION_CHANGED=NO
TASK_015_RESUMED=NO
TASK_COMPLETE=NO
```

The only Production data mutations were the normal canonical writes made by
the one authorized Worker recovery. No manual SQL mutation was performed.
The existing migration head was verified by the governed release precondition;
the migration apply flag was false. Scheduler redesign, topic semantic
changes, relation-weight changes, and observation-policy changes were outside
scope and were not performed.

The next action requires separate Owner authorization for provider/readiness
or downstream formal-snapshot remediation. This task stops here; no recovery
retry is permitted under 021.
