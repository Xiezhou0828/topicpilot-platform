# TASK-POST-CLOSE-20260929-PROTECTED-READBACK-017A

## Executive disposition

This task was scoped to a protected, Production, SELECT-only readback for
post-close run `30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a` on `2026-09-29`.

The required protected channel was not available in this execution context.
No query was sent to Production and no attempt was made to substitute a local
database, public aggregate endpoint, or an unverified connection. The incident
root cause therefore remains `UNKNOWN_INSUFFICIENT_EVIDENCE`.

The terminal state for this task is:

`BLOCKED_PROTECTED_READONLY_CHANNEL_UNAVAILABLE`

## Scope and safety attestation

| Control | Result |
|---|---|
| Target environment | `PRODUCTION` required; not attestable from an available protected runtime |
| Query mode | `SELECT_ONLY` required; not attestable for any available Production connection |
| Production operational-table queries | `NOT_EXECUTED` |
| Production mutation | `NO` |
| Retry or provider replay | `NO` |
| Scheduler, deployment, migration, or worker restart | `NO` |
| Repository change | This report only |

The task instructions require stopping when Production and SELECT-only mode
cannot be guaranteed. That stop condition was reached before any operational
table read.

## Repository and runtime authority

| Item | Evidence |
|---|---|
| Repository | `Xiezhou0828/topicpilot-platform` |
| Current `origin/main` | `979f3509934b88a2dfbde507704b7511b42ac734` |
| Public API runtime SHA observed during the prior readback | `6cb88c0d7fceb45b244d295883636706f50ea0be` from `/healthz` and `/readyz` |
| Incident Worker/post-close SHA | `UNKNOWN_NOT_EXPOSED` |
| Public reference data version | `tw-reference-v1` |
| Repository adapter lineage | `twse-official-daily.v2`, `tpex-official-daily.v2` |
| Incident-time registry/adapter binding | `UNKNOWN_NOT_EXPOSED` |
| Incident-time provider request timestamps | `UNKNOWN_NOT_EXPOSED` |

The incident-relevant `live/post_close.py` and `market_data/exchange.py` files
were unchanged between the observed API SHA and current `origin/main`. This
is source evidence only and does not prove the incident Worker runtime SHA.

## Protected-channel availability check

The repository's existing maintenance snapshot helper documents a read-only
PostgreSQL path. It requires an explicitly configured
`TOPICPILOT_PRODUCTION_DATABASE_URL`; when connected, it attempts
`SET TRANSACTION READ ONLY` before issuing its SELECT statements. The current
execution context had none of the following available:

- `TOPICPILOT_PRODUCTION_DATABASE_URL`;
- `TOPICPILOT_PRODUCTION_ADMIN_API_URL`;
- an attested `TARGET_ENVIRONMENT=PRODUCTION` value;
- an attested `QUERY_MODE=SELECT_ONLY` value; or
- a protected connector/runtime that exposes the requested PostgreSQL tables.

The public Production API exposes only the latest live aggregate and has no
read routes for `live_collector_attempts` or
`live_collector_checkpoints`. It is therefore insufficient for the requested
forensic readback.

## Incident aggregate available from the prior public readback

The following is the exact public aggregate observed for the incident. It is
recorded for identity and reconciliation only; it is not a replacement for
the required operational-table rows.

| Field | Value |
|---|---|
| `status` | `FAILED` |
| `lastRun.id` | `30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a` |
| `lastRun.type` | `POST_CLOSE` |
| `lastRun.startedAt` | `2026-09-29T05:39:57.482336Z` |
| `lastRun.completedAt` | `2026-09-29T06:09:46.671071Z` |
| `lastRun.latencyMs` | `1789188` |
| `lastRun.requestedCount` | `553` |
| `providerStatus` | `ERROR` |
| `freshnessState` | `PARTIAL` |
| `heartbeatAt` | `2026-09-29T06:09:46.671071Z` |
| `successCount` | `0` |
| `failureCount` | `347` |
| `retryCount` | `0` |
| `skippedCount` | `206` |
| `universeCounts` | `INTRADAY=0`, `POST_CLOSE=0`, `UNKNOWN=555`, `TOTAL=555` |
| `failureCode` | `EXCHANGE_NO_DATA` |
| `failureMessage` | `EXCHANGE_NO_DATA` |
| `providerHealth` | `[]` |

The counts reconcile arithmetically (`347 + 206 = 553`). The aggregate does
not identify the market, provider, adapter, checkpoint, or per-instrument
reason behind any count.

## Required protected readback results

| Required evidence | Result |
|---|---|
| `topicpilot.live_collector_runs` exact incident row | `UNAVAILABLE`; only the public aggregate above was observable |
| `topicpilot.live_collector_attempts` all rows | `UNAVAILABLE` |
| Grouping by market/status/provider/error | `UNAVAILABLE` |
| Exact explanation for 347 failures | `UNAVAILABLE`; only run-level `EXCHANGE_NO_DATA` is exposed |
| Exact explanation for 206 skips | `UNAVAILABLE` |
| `topicpilot.live_collector_checkpoints` all rows | `UNAVAILABLE` |
| Phase reconstruction | `UNAVAILABLE` |
| First failed checkpoint | `UNKNOWN` |
| First TWSE/TPEx provider request timestamps | `UNAVAILABLE` |
| Provider request counts and response timestamps | `UNAVAILABLE` |
| Fallback entered | `NOT_PROVEN` |
| Fallback amplified provider calls | `NOT_PROVEN`; structurally possible from the current code path |
| Exact TPE/TWO market split | `UNAVAILABLE` |
| Worker runtime SHA/reference/registry binding | `UNAVAILABLE` |
| Previous successful comparable run | `UNAVAILABLE` |

## Root-cause assessment

No protected incident-time evidence was recovered, so the prior root-cause
classification is unchanged:

`PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE`

The later direct official-provider probes remain compatibility evidence only:
both TWSE and TPEx returned date-matched, expected-shaped payloads after the
incident. They do not prove provider readiness at the incident timestamp and
do not establish a permanent provider contract change.

The current code contains a market-batch path followed by per-instrument
fallback after a batch exception. That makes fallback amplification
structurally possible, but without attempt rows and checkpoints it cannot be
asserted as an incident fact.

## Required unblock

An operator-authorized follow-up must provide a protected runtime with all of
the following attested before any query is issued:

1. `TARGET_ENVIRONMENT=PRODUCTION`;
2. `QUERY_MODE=SELECT_ONLY`;
3. a dedicated read-only Production database role or an equivalent enforced
   read-only transaction boundary; and
4. access to the three requested `topicpilot` tables plus runtime/reference
   metadata.

The follow-up should then read the incident run, all attempts, and all
checkpoints for the exact run ID and capture query/result audit evidence.

## Final status block

```text
TASK_STATUS=BLOCKED_PROTECTED_READONLY_CHANNEL_UNAVAILABLE
TARGET_ENVIRONMENT=PRODUCTION_REQUIRED_NOT_ATTESTED
QUERY_MODE=SELECT_ONLY_REQUIRED_NOT_ATTESTED
PROTECTED_READBACK_EXECUTED=NO
REQUIRED_OPERATIONAL_TABLE_ACCESS=UNAVAILABLE
PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
FALLBACK_STATUS=NOT_PROVEN
FALLBACK_AMPLIFICATION=NOT_PROVEN
PRODUCTION_MUTATION=NO
RETRY_OR_REPLAY=NO
NEXT_ACTION=OPEN_ATTESTED_PRODUCTION_SELECT_ONLY_READBACK_CHANNEL
```
