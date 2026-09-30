# TASK-POST-CLOSE-20260930-CURRENT-DAY-HEALTH-018

## Result

The natural Production `POST_CLOSE` run for trading date `2026-09-30` was found
through the protected `production-readonly` channel. It reproduced the exact
failure pattern observed on `2026-09-29`: all TPE attempts returned
`EXCHANGE_NO_DATA`, and all TWO attempts were skipped as
`MISSING_MARKET_DATA`. The current-day run is therefore classified as
`FAILED`; the 2026-09-29 incident is not supported as isolated or transient.

No retry, replay, recovery run, deployment, scheduler change, migration, or
Production data mutation was performed.

## Source and evidence

- Repository: `Xiezhou0828/topicpilot-platform`
- Readback source SHA: `6db7ebddc4f0c718e91a41245152912127a6a553`
- Protected workflow run: [36684522597](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/36684522597)
- Readback job: `109787205291`
- Sanitized artifact: `production-forensic-readback-2026-09-30` (`11083271648`)
- Requested trading date: `2026-09-30`
- Selection basis: `METADATA_RUN_DATE`
- Candidate count: `1`
- Selected scope/session: `FULL` / `REGULAR`
- Selected execution mode/timezone: `SCHEDULED` / `Asia/Taipei`

Safety evidence from the artifact:

- database role: `topicpilot_forensic_readonly`
- session user: `topicpilot_forensic_readonly`
- `transactionReadOnly=true`
- `mutationPrivilegesPresent=NO`
- target access was SELECT-only for the three forensic tables

## Natural run readback

| Field | Value |
|---|---|
| POST_CLOSE run ID | `2284ae32-fb83-45bf-bad5-4dd506c3d9a8` |
| Started | `2026-09-30T13:37:22.608633+08:00` |
| Completed | `2026-09-30T14:07:06.255531+08:00` |
| Status | `FAILED` |
| Requested | `553` |
| Success | `0` |
| Failure | `347` |
| Skipped | `206` (derived from market attempt distribution) |
| Retry | `0` |
| Provider | `OFFICIAL_DAILY_ROUTER` |
| Adapter | `official-daily-router.v1` |
| Provider status | `ERROR` |
| Failure code | `EXCHANGE_NO_DATA` |

### Market split

| Market | Attempts | Success | Failure | Skipped | Timeout |
|---|---:|---:|---:|---:|---:|
| TPE | 347 | 0 | 347 | 0 | 0 |
| TWO | 206 | 0 | 0 | 206 | 0 |

Error distribution:

```text
EXCHANGE_NO_DATA=347
MISSING_MARKET_DATA=206
```

Provider-status distribution:

```text
ERROR=347
UNKNOWN=206
```

## Checkpoint and publication health

The date-bound readback returned zero checkpoint rows for the selected run.
Accordingly, no checkpoint phase can be reported as completed or as the first
failed checkpoint without inventing evidence.

```text
CHECKPOINT_COUNT=0
CHECKPOINT_TIMELINE=EMPTY
FIRST_FAILED_CHECKPOINT=NOT_PRESENT_IN_READBACK
LAST_COMPLETED_CHECKPOINT=NONE
FORMAL_MARKET_FACTS_STATUS=NOT_REACHED_OR_NOT_RECORDED
A9_B2_FORMAL_PROCESSING_STATUS=NOT_REACHED_OR_NOT_RECORDED
FINAL_PUBLICATION_STATUS=NOT_REACHED_OR_NOT_RECORDED
COMPLETION_STATUS=NOT_REACHED_OR_NOT_RECORDED
FORMAL_PUBLICATION_STATUS=NOT_PUBLISHED_OR_UNVERIFIED
HOME_PUBLICATION_STATUS=NOT_PUBLISHED_OR_UNVERIFIED
LATEST_FORMAL_TOPIC_DATE=NOT_AVAILABLE
LATEST_HOME_DATE=NOT_AVAILABLE
```

The absence of checkpoint and publication evidence is consistent with the
run-level failure and must not be replaced with a synthetic publication
result.

## Comparison with 2026-09-29

The recovered 2026-09-29 evidence was:

```text
requested=553
success=0
failure=347
skipped=206
TPE=347 EXCHANGE_NO_DATA
TWO=206 MISSING_MARKET_DATA
retry=0
```

The 2026-09-30 natural run has the same requested count, market split, error
codes, provider statuses, zero-success result, and zero-retry result.

```text
INCIDENT_PATTERN_REPEATED_ON_20260930=YES
20260929_INCIDENT_SCOPE=PERSISTENT_POST_CLOSE_FAILURE_SUPPORTED
CURRENT_DAY_POST_CLOSE_HEALTH=FAILED
```

This report establishes persistence of the observed failure pattern. It does
not claim a more specific root cause than the recorded provider/data-readiness
failure codes.

## Remediation decision

```text
RECOMMENDED_REMEDIATION_PATH=OPEN_PROVIDER_READINESS_REMEDIATION
```

Reason: the natural 2026-09-30 run reproduces `EXCHANGE_NO_DATA` and the
corresponding TWO missing-data skips. Remediation is intentionally not
implemented by this task; the next task should investigate official provider
availability/readiness and its governed failure handling before any replay or
recovery is considered.

## Final status

```text
TASK_ID=TASK-POST-CLOSE-20260930-CURRENT-DAY-HEALTH-018
TASK_STATUS=COMPLETE_CURRENT_DAY_HEALTH_CLASSIFIED
CURRENT_MAIN_SHA=6db7ebddc4f0c718e91a41245152912127a6a553

POST_CLOSE_RUN_FOUND=YES
POST_CLOSE_RUN_ID=2284ae32-fb83-45bf-bad5-4dd506c3d9a8

RUN_STATUS=FAILED
RUN_REQUESTED=553
RUN_SUCCESS=0
RUN_FAILURE=347
RUN_SKIPPED=206
RUN_RETRY=0

TPE_SUCCESS=0
TPE_FAILURE=347
TPE_SKIPPED=0
TPE_TIMEOUT=0

TWO_SUCCESS=0
TWO_FAILURE=0
TWO_SKIPPED=206
TWO_TIMEOUT=0

ERROR_CODE_DISTRIBUTION=EXCHANGE_NO_DATA:347; MISSING_MARKET_DATA:206
PROVIDER_STATUS_DISTRIBUTION=ERROR:347; UNKNOWN:206

CHECKPOINT_COUNT=0
FIRST_FAILED_CHECKPOINT=NOT_PRESENT_IN_READBACK
LAST_COMPLETED_CHECKPOINT=NONE

FORMAL_MARKET_FACTS_STATUS=NOT_REACHED_OR_NOT_RECORDED
A9_B2_FORMAL_PROCESSING_STATUS=NOT_REACHED_OR_NOT_RECORDED
FINAL_PUBLICATION_STATUS=NOT_REACHED_OR_NOT_RECORDED
COMPLETION_STATUS=NOT_REACHED_OR_NOT_RECORDED

FORMAL_PUBLICATION_STATUS=NOT_PUBLISHED_OR_UNVERIFIED
HOME_PUBLICATION_STATUS=NOT_PUBLISHED_OR_UNVERIFIED

CURRENT_DAY_POST_CLOSE_HEALTH=FAILED
INCIDENT_PATTERN_REPEATED_ON_20260930=YES
20260929_INCIDENT_SCOPE=PERSISTENT_POST_CLOSE_FAILURE_SUPPORTED
RECOMMENDED_REMEDIATION_PATH=OPEN_PROVIDER_READINESS_REMEDIATION

PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
PROVIDER_REPLAYED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO

TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=OPEN_PROVIDER_READINESS_REMEDIATION
```
