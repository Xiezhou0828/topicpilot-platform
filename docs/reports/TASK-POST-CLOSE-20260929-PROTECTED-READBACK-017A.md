# TASK-POST-CLOSE-20260929-PROTECTED-READBACK-017A

## Disposition

The protected Production readback channel is now operational and the exact
incident run was read once through the governed SELECT-only workflow. The
incident evidence was recovered without retrying POST_CLOSE or changing
Production. The detailed, bounded evidence is recorded in
`TASK-POST-CLOSE-20260929-PROTECTED-INCIDENT-READBACK-017D.md`.

The incident itself remains unresolved at root-cause level. The recovered
artifact proves the market/error distributions, but it contains no checkpoint
timeline or incident-time Worker/reference provenance sufficient to identify a
single primary cause.

## Provenance chain

```text
RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
TRADING_DATE=2026-09-29
017C_PREFLIGHT_WORKFLOW_RUN_ID=36668440861
017C_PREFLIGHT_STATUS=PASS
CURRENT_MAIN_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
FORENSIC_WORKFLOW_RUN_ID=36678415986
FORENSIC_JOB_ID=109768368162
FORENSIC_TOOL_SHA=a0f16107af5cfcdd063458d65a473ef2e4a7175b
SANITIZED_ARTIFACT_ID=11081105402
SANITIZED_ARTIFACT_STATUS=GENERATED_AND_RETRIEVED
```

The latest canonical main was fetched before dispatch. The forensic workflow
and repository-owned readback CLI were compared with the validated 017C
execution SHA `3b09a5ae5e74d48c724e27fdc3a0eeac0862320f`; no semantic change
was found in either file. The workflow checked out the exact current main SHA
and passed its protected Environment, exact-revision, fixed-command,
SELECT-only, and artifact-upload gates.

## Recovered safety boundary

```text
DATABASE_CURRENT_USER=topicpilot_forensic_readonly
DATABASE_SESSION_USER=topicpilot_forensic_readonly
TRANSACTION_READONLY_READBACK=on
MUTATION_PRIVILEGES_PRESENT=NO
TARGET_TABLE_SCOPE=topicpilot.live_collector_runs; topicpilot.live_collector_attempts; topicpilot.live_collector_checkpoints
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
PROVIDER_REPLAYED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
OBSERVATION_CHANGED=NO
TASK_015_CHANGED=NO
```

## Recovered incident summary

```text
RUN_STATUS=FAILED
RUN_REQUESTED=553
RUN_SUCCESS=0
RUN_FAILURE=347
RUN_SKIPPED=206
RUN_RETRY=0
RUN_FAILURE_CODE=EXCHANGE_NO_DATA
RUN_PROVIDER_CODE=OFFICIAL_DAILY_ROUTER
RUN_ADAPTER_VERSION=official-daily-router.v1
RUN_PROVIDER_STATUS=ERROR
RUN_FRESHNESS_STATE=PARTIAL
CHECKPOINT_TIMELINE=EMPTY
FIRST_FAILED_CHECKPOINT=UNAVAILABLE
```

The full market split and the bounded root-cause assessment are in the 017D
report. In short, all 347 recorded failures are TPE failures with
`EXCHANGE_NO_DATA`; all 206 TWO records are skipped with
`MISSING_MARKET_DATA`. This is evidence about the recorded run, not a
conclusion about why the provider behaved that way.

## Final status

```text
TASK_STATUS=COMPLETE_PROTECTED_READBACK_EVIDENCE_RECOVERED
TASK_017A_STATUS=COMPLETE_PROTECTED_READBACK_EVIDENCE_RECOVERED
PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
ROOT_CAUSE_CONFIDENCE=NONE
TASK_015_RESUMABLE=DO_NOT_CHANGE_AUTOMATICALLY
TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=Owner review of the bounded 017D evidence; any remediation or TASK-015 resume requires a separate explicit decision and task
```
