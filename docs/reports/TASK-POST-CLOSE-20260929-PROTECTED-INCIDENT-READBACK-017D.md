# TASK-POST-CLOSE-20260929-PROTECTED-INCIDENT-READBACK-017D

## Executive disposition

The one explicitly authorized Production incident readback completed through
the protected `production-readonly` Environment. It read exactly the existing
`POST_CLOSE` run and retrieved the workflow-produced sanitized artifact. No
retry, provider replay, remediation, deployment, scheduler change, migration,
observation activation, or database mutation was performed.

The artifact recovers the exact market and error distributions. It does not
contain checkpoint rows for this run, incident-time Worker SHA, reference
version, or config hash. Accordingly, the primary incident cause remains
`UNKNOWN_INSUFFICIENT_EVIDENCE`; no structural code-path possibility is
promoted to an incident fact.

## Authorization and exact provenance

```text
TASK_ID=TASK-POST-CLOSE-20260929-PROTECTED-INCIDENT-READBACK-017D
REPOSITORY=Xiezhou0828/topicpilot-platform
BRANCH=main
TRADING_DATE=2026-09-29
TARGET_RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
FORENSIC_COMMAND=POST_CLOSE_RUN_READBACK
PROTECTED_ENVIRONMENT=production-readonly
EXPECTED_ROLE=topicpilot_forensic_readonly

CURRENT_MAIN_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
FORENSIC_TOOL_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
SEMANTICS_BASELINE_SHA=3b09a5ae5e74d48c724e27fdc3a0eeac0862320f
WORKFLOW_CLI_SEMANTICS_UNCHANGED=YES
FORENSIC_WORKFLOW_RUN_ID=36678415986
FORENSIC_JOB_ID=109768368162
FORENSIC_WORKFLOW_STATUS=SUCCESS
```

The latest `origin/main` was fetched before dispatch. The workflow and
repository-owned forensic CLI were compared against the validated 017C
execution SHA; no semantic change was found. The workflow itself verified the
exact checkout SHA as an ancestor of `origin/main`.

Workflow: <https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/36678415986>

Sanitized artifact:

```text
ARTIFACT_ID=11081105402
ARTIFACT_NAME=production-forensic-readback-30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
ARTIFACT_STATUS=GENERATED_AND_RETRIEVED
ARTIFACT_GENERATED_AT=2026-09-30T06:29:39.750259Z
LOCAL_EVIDENCE_COPY=artifacts/incident-readback-36678415986/production-forensic-readback.json
```

No secret, database URL, or unsanitized provider payload was exposed.

## Protected readback safety gates

```text
DATABASE_CURRENT_USER=topicpilot_forensic_readonly
DATABASE_SESSION_USER=topicpilot_forensic_readonly
TRANSACTION_READONLY_READBACK=on
MUTATION_PRIVILEGES_PRESENT=NO
TARGET_TABLE_SCOPE=topicpilot.live_collector_runs; topicpilot.live_collector_attempts; topicpilot.live_collector_checkpoints
```

The 017C precondition had already verified the Production database connection,
the three target tables and required schema, SELECT access, and absence of
mutation privileges. The 017D artifact independently carried the role,
session, transaction, and privilege readback fields above.

## Exact run readback

```text
RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
RUN_TYPE=POST_CLOSE
RUN_STATUS=FAILED
RUN_STARTED_AT=2026-09-29T13:39:57.482336+08:00
RUN_HEARTBEAT_AT=2026-09-29T14:09:46.671071+08:00
RUN_COMPLETED_AT=2026-09-29T14:09:46.671071+08:00
RUN_REQUESTED=553
RUN_SUCCESS=0
RUN_FAILURE=347
RUN_SKIPPED=206
RUN_RETRY=0
RUN_LATENCY_MS=1789188
RUN_FRESHNESS_STATE=PARTIAL
RUN_PROVIDER_CODE=OFFICIAL_DAILY_ROUTER
RUN_ADAPTER_VERSION=official-daily-router.v1
RUN_PROVIDER_STATUS=ERROR
RUN_FAILURE_CODE=EXCHANGE_NO_DATA
RUN_FAILURE_MESSAGE=EXCHANGE_NO_DATA
```

The timestamps above are the artifact's `+08:00` representation of the
incident date. They are kept date-bound to `2026-09-29` and are not mixed with
the 017D workflow execution date (`2026-09-30`).

## Market split

| Market | Attempts | Success | Failure | Skipped | Timeout |
|---|---:|---:|---:|---:|---:|
| TPE | 347 | 0 | 347 | 0 | 0 |
| TWO | 206 | 0 | 0 | 206 | 0 |

### Failure 347

```text
FAILURE_347_MARKET_SPLIT=TPE=347; TWO=0
FAILURE_347_ERROR_CODE_DISTRIBUTION=EXCHANGE_NO_DATA=347
FAILURE_347_PROVIDER_STATUS_DISTRIBUTION=ERROR=347
FAILURE_347_TIME_RANGE=2026-09-29T13:40:02.948053+08:00 -> 2026-09-29T13:52:12.105870+08:00
FAILURE_347_RETRY_DISTRIBUTION=retry_count=0 for the run; no retry recorded in the grouped summary
```

The time range is the grouped attempt summary's first `startedAt` through
last `retrievedAt`. The bounded artifact also returned 50 representative
attempts; every returned representative was TPE, `FAILED`, provider status
`ERROR`, `EXCHANGE_NO_DATA`, `attemptNumber=1`, and `retryCount=0`. This is a
sample of returned representatives, while the grouped summary is the source
for the complete count of 347.

### Skipped 206

```text
SKIPPED_206_MARKET_SPLIT=TWO=206; TPE=0
SKIPPED_206_ERROR_CODE_DISTRIBUTION=MISSING_MARKET_DATA=206
SKIPPED_206_PROVIDER_STATUS_DISTRIBUTION=UNKNOWN=206
SKIPPED_206_TIME_RANGE=2026-09-29T13:52:14.028477+08:00 -> 2026-09-29T14:09:31.661490+08:00
SKIPPED_206_REASON_CLASSIFICATION=Recorded as SKIPPED with MISSING_MARKET_DATA; no stronger provider or checkpoint cause is available
```

The skipped classification is deliberately bounded to the recorded
`MISSING_MARKET_DATA` code and `UNKNOWN` provider status. It does not assert
why the market data was missing.

## Checkpoint timeline

```text
CHECKPOINT_TIMELINE_COUNT=0
FIRST_CHECKPOINT=UNAVAILABLE
FIRST_FAILED_CHECKPOINT=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_TIME=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_STATUS=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_PROCESSED=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_SUCCEEDED=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_FAILED=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_SKIPPED=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_PROVIDER_REQUESTS=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_PROVIDER_FAILURES=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_METADATA=UNAVAILABLE
ORDERED_CHECKPOINT_PROGRESSION=UNAVAILABLE; artifact checkpointTimeline was empty
```

No first failed checkpoint, phase ordering, batch boundary, or checkpoint-level
provider request count is inferred from the aggregate or attempt rows.

## Fallback analysis

The current canonical `live/post_close.py` contains a batch-exception branch
that rolls back the batch and then performs per-instrument fallback ingestion
with savepoints. This establishes a code-path possibility only.

```text
FALLBACK_PATH_STATUS=UNRESOLVED
FALLBACK_AMPLIFICATION_STATUS=UNRESOLVED
CODE_PATH_FALLBACK_PRESENT=YES
INCIDENT_FALLBACK_ENTRY_EVIDENCE=NOT_AVAILABLE
INCIDENT_FALLBACK_AMPLIFICATION_EVIDENCE=NOT_AVAILABLE
```

The artifact has no checkpoint timeline or batch/fallback lineage field that
can distinguish normal per-market processing from the fallback branch. The
347 TPE failures and 206 TWO skips therefore cannot be used to claim that
fallback was entered or amplified provider calls.

## Root-cause reassessment

```text
PROVIDER_NOT_READY_AT_RUN_TIME=UNRESOLVED
TRANSIENT_PROVIDER_FAILURE=UNRESOLVED
TWSE_OFFICIAL_ENDPOINT_FAILURE=UNRESOLVED
TPEX_OFFICIAL_ENDPOINT_FAILURE=UNRESOLVED
EXCHANGE_PAYLOAD_CONTRACT_DRIFT=UNRESOLVED
PROVIDER_DATE_MISMATCH=UNRESOLVED
MARKET_BATCH_IMPLEMENTATION_DEFECT=UNRESOLVED
FALLBACK_AMPLIFICATION_DEFECT=UNRESOLVED
REFERENCE_BINDING_MISMATCH=UNRESOLVED
RUNTIME_VERSION_MISMATCH=UNRESOLVED

PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
SECONDARY_CONTRIBUTING_CAUSES=UNRESOLVED
ROOT_CAUSE_CONFIDENCE=NONE
```

The artifact proves what the run recorded, not whether the official provider
was ready at the incident time, whether a response contract changed, whether
the requested date was bound incorrectly, or which Worker revision executed
the run. No root-cause conclusion is forced.

## Runtime provenance

```text
INCIDENT_WORKER_RUNTIME_SHA=UNVERIFIED
INCIDENT_REFERENCE_VERSION=UNVERIFIED
INCIDENT_ADAPTER_VERSION=official-daily-router.v1
INCIDENT_CONFIG_HASH=UNVERIFIED
```

The adapter version is present in the run row and is recorded exactly. The
current main SHA is the forensic tool identity, not a substitute for the
incident Worker runtime SHA or reference version.

## Required non-actions and task boundaries

```text
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
PROVIDER_REPLAYED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
MIGRATION_CHANGED=NO
OBSERVATION_CHANGED=NO
TASK_015_CHANGED=NO
TASK_015_RESUMABLE=DO_NOT_CHANGE_AUTOMATICALLY
```

This report closes the evidence-recovery task only. It does not authorize
remediation, a new POST_CLOSE run, a historical backfill, a Worker restart,
or resumption of TASK-015.

## Final status block

```text
TASK_ID=TASK-POST-CLOSE-20260929-PROTECTED-INCIDENT-READBACK-017D
TASK_STATUS=COMPLETE_PROTECTED_INCIDENT_READBACK_017D
CURRENT_MAIN_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
FORENSIC_WORKFLOW_RUN_ID=36678415986
FORENSIC_TOOL_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
DATABASE_CURRENT_USER=topicpilot_forensic_readonly
DATABASE_SESSION_USER=topicpilot_forensic_readonly
TRANSACTION_READONLY_READBACK=on
MUTATION_PRIVILEGES_PRESENT=NO
SANITIZED_ARTIFACT_STATUS=PASS; ARTIFACT_ID_11081105402

RUN_STATUS=FAILED
RUN_REQUESTED=553
RUN_SUCCESS=0
RUN_FAILURE=347
RUN_SKIPPED=206

TPE_ATTEMPT_COUNT=347
TPE_SUCCESS=0
TPE_FAILURE=347
TPE_SKIPPED=0
TPE_TIMEOUT=0

TWO_ATTEMPT_COUNT=206
TWO_SUCCESS=0
TWO_FAILURE=0
TWO_SKIPPED=206
TWO_TIMEOUT=0

FAILURE_347_MARKET_SPLIT=TPE=347
FAILURE_347_ERROR_CODE_DISTRIBUTION=EXCHANGE_NO_DATA=347
FAILURE_347_PROVIDER_STATUS_DISTRIBUTION=ERROR=347
SKIPPED_206_MARKET_SPLIT=TWO=206
SKIPPED_206_ERROR_CODE_DISTRIBUTION=MISSING_MARKET_DATA=206
SKIPPED_206_PROVIDER_STATUS_DISTRIBUTION=UNKNOWN=206
SKIPPED_206_REASON_CLASSIFICATION=Recorded MISSING_MARKET_DATA; underlying cause unresolved

FIRST_FAILED_CHECKPOINT=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_TIME=UNAVAILABLE
FIRST_FAILED_CHECKPOINT_ERROR=UNAVAILABLE
FALLBACK_PATH_STATUS=UNRESOLVED
FALLBACK_AMPLIFICATION_STATUS=UNRESOLVED
INCIDENT_WORKER_RUNTIME_SHA=UNVERIFIED
INCIDENT_REFERENCE_VERSION=UNVERIFIED
PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
SECONDARY_CONTRIBUTING_CAUSES=UNRESOLVED
ROOT_CAUSE_CONFIDENCE=NONE

TASK_017A_STATUS=COMPLETE_PROTECTED_READBACK_EVIDENCE_RECOVERED
TASK_015_RESUMABLE=DO_NOT_CHANGE_AUTOMATICALLY
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
OBSERVATION_CHANGED=NO
TASK_COMPLETE=YES

NEXT_RECOMMENDED_TASK=Owner review of the recovered evidence; any remediation or TASK-015 resume requires a separate explicit authorization
```
