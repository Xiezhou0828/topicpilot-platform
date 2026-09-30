# TASK-POST-CLOSE-OFFICIAL-PROVIDER-READINESS-REMEDIATION-020

## Scope and status

This remediation addresses the repeated 2026-09-29 and 2026-09-30 POST_CLOSE official-provider failure. It does not replay either date, backfill history, mutate Production, or deploy any service.

```text
TASK_ID=TASK-POST-CLOSE-OFFICIAL-PROVIDER-READINESS-REMEDIATION-020
INITIAL_MAIN_SHA=ef4b73ba6ae78afb24245fc03da823fd05a50cb7
IMPLEMENTATION_SHA=6652fe0e95140e4ee3598a1fa57c3a91b0b6a0ff
FINAL_MAIN_SHA=TO_BE_RECORDED_AFTER_PROMOTION
```

## Evidence and root cause

The two Production readbacks show the same pattern on both dates: 553 requested, 0 success, 347 TPE failures, and 206 TWO skips. The available readbacks do not include the raw provider payload or the exact worker artifact, so the original exchange response cannot be reconstructed from Production alone.

Non-mutating probes of the current official endpoints on 2026-09-29 and 2026-09-30 returned:

| Endpoint | HTTP | status | response date | expected table rows | first identifier |
| --- | ---: | --- | --- | ---: | --- |
| TWSE MI_INDEX | 200 | `OK` | `20260929` / `20260930` | 1382 / 1382 | `00400A` |
| TPEx dailyQuotes | 200 | `ok` | `20260929` / `20260930` | 11730 / 11772 | `00411A` |

The current parser expectations therefore match the live official payload shape. The earliest deterministic defect supported by code and fixtures was readiness/error handling: a market-level non-ready response was classified as terminal `EXCHANGE_NO_DATA`, an empty market table became per-instrument missing data, and the POST_CLOSE batch exception path then entered per-symbol fallback. That multiplied one shared provider failure into many attempts and obscured the provider-level cause.

```text
PRIMARY_ROOT_CAUSE=market-level official-provider readiness/empty-response states were not distinguished from terminal provider failure; the market-batch exception path then fanned out into per-symbol fallback
PROVIDER_READINESS_DEFECT_CONFIRMED=YES
PARSER_DEFECT_CONFIRMED=NO
DATE_BINDING_DEFECT_CONFIRMED=NO
FALLBACK_DEFECT_CONFIRMED=YES
```

## Affected paths

```text
TPE_FAILURE_PATH=PostCloseUpdater -> build_historical_provider_registry(market_batch=True) -> TwseOfficialDailyProvider -> TWSE market-level response -> EXCHANGE_NOT_READY/EXCHANGE_EMPTY_PAYLOAD terminal outcome -> one FAILED attempt per batch instrument, without per-symbol refetch

TWO_SKIP_PATH=PostCloseUpdater -> build_historical_provider_registry(market_batch=True) -> TpexOfficialDailyProvider -> TPEX market-level index -> instrument has no covered priced bar -> HistoricalInstrumentResult -> MISSING_MARKET_DATA / SKIPPED

TWO_DEPENDS_ON_TPE_FAILURE=NO
```

TPE and TWO are separately registered providers and separately batched. The canonical path does not share a failed TPE payload with TWO. The incident's TWO skips are therefore an independent empty/no-covered-result outcome (with the raw historical payload unavailable), not a consequence of TPE's exception state. Current direct TPEx probes and deterministic parser tests show that a valid same-day TPEx payload is accepted.

## Date binding and market-batch contract

Automatic POST_CLOSE execution now uses the configured `Asia/Taipei` session date. Explicit `run_date` remains authoritative. The provider registry receives that same date as both `start_date` and `end_date`, and the exchange adapters construct the corresponding official request date.

```text
POST_CLOSE_RUN_DATE_BINDING=automatic clock converted to config.timezone_name; explicit run_date overrides the clock
TWSE_REQUEST_DATE_BINDING=provider start_date=end_date=local session date; MI_INDEX date=YYYYMMDD
TPEX_REQUEST_DATE_BINDING=provider start_date=end_date=local session date; dailyQuotes date=YYYY/MM/DD
DATE_BINDING_DEFECT_CONFIRMED=NO
```

`market_batch=True` means one market-level official request per provider/date, indexed by instrument code afterward. A provider-level exception is no longer sent through the per-symbol fallback path when it has a known market/provider error code. This preserves fail-closed behavior while preventing repeated requests for one shared failure.

```text
MARKET_BATCH_STATUS=one request per market/date, indexed by instrument, with bounded readiness and terminal-failure caching
MARKET_BATCH_ROOT_CAUSE=the prior exception path treated shared market-provider failure as an isolated instrument failure and refetched the same market payload per symbol
```

## Checkpoint explanation

The Production readbacks report `CHECKPOINT_COUNT=0`, but the canonical `PostCloseUpdater` already commits checkpoint events before provider batches and on provider failure. The readback metadata identifies runtime adapter `official-daily-router.v1`, while the canonical source readback is a different artifact lineage (`twse-official-daily.v2` / `tpex-official-daily.v2`) and the exact worker SHA is unavailable. Therefore the evidence supports runtime/provenance mismatch or a pre-checkpoint worker artifact; it does not support claiming that the current canonical checkpoint writer rolled back all events.

```text
CHECKPOINT_ZERO_ROOT_CAUSE=runtime provenance is unavailable; Production metadata shows an adapter/runtime lineage different from current canonical provider code, while canonical checkpoint writes are committed before provider work and on provider failure
```

The remediation also records `provider_failure_count=1` and `providerErrorCode` on the failed market checkpoint, so a future current-code run exposes the provider-level failure directly.

## Implementation

Changed only the official-provider readiness and POST_CLOSE observability path; no migration or formal Topic semantics changed.

- Added bounded readiness retries for `EXCHANGE_NOT_READY` and `EXCHANGE_EMPTY_PAYLOAD`: 3 maximum attempts, 90 seconds maximum total wait, 30/60-second exponential backoff capped by the remaining budget, and terminal failure caching.
- Reclassified non-OK exchange status as `EXCHANGE_NOT_READY`; an OK payload with no market rows is `EXCHANGE_EMPTY_PAYLOAD`; schema/date/number/OHLC errors remain terminal validation failures.
- Passed readiness settings from `LiveRuntimeConfig` through the registry into both official providers.
- Counted readiness retries in POST_CLOSE run metrics and prevented known market-level provider failures from entering per-symbol fallback.
- Added transport retry coverage for `http.client.IncompleteRead`, which can occur while reading a chunked official response.
- Added deterministic date, valid payload, not-ready, date-mismatch, schema-mismatch, empty-payload, TPE/TWO independence, market-batch, fallback, retry, and checkpoint tests.

```text
IMPLEMENTATION_CHANGED=YES
BOUNDED_RETRY_ADDED=YES
ERROR_TAXONOMY_IMPROVED=YES
MAX_ATTEMPTS=3
MAX_TOTAL_WAIT=90 seconds
BACKOFF=30 seconds, then 60 seconds, capped by remaining total-wait budget
TERMINAL_FAILURE_CODE=EXCHANGE_NOT_READY or EXCHANGE_EMPTY_PAYLOAD after the bounded budget; other provider/schema failures remain terminal
```

## Validation

Validation performed without Production mutation:

```text
FOCUSED_TESTS=all focused provider, POST_CLOSE, rate-limit, and preflight tests passed; 58 passed
BACKEND_TESTS=854 passed, 4 skipped, 148 deselected (non-research/non-governance/non-PostgreSQL CI scope)
REFERENCE_BUNDLE=PASS; canonical generator match, no changed artifacts
ALEMBIC_GRAPH=PASS; 48 revisions, one head (0047_task_topic_role_strength_design_freeze)
SYSTEM_OF_RECORD_BOUNDARIES=PASS; 6 tests passed
OPENAPI_DRIFT=PASS
RUFF_STATUS=changed-scope Ruff PASS; full-repository Ruff contains pre-existing research-scope baseline debt and is governed by the CI no-new-debt gate
GIT_DIFF_CHECK=PASS
```

Exact-SHA CI is required before promotion. The current branch has not deployed or invoked any Production workflow.

## Production boundary and remaining activation

```text
PRODUCTION_DB_MUTATED=NO
PRODUCTION_DEPLOYED=NO
POST_CLOSE_RETRIED=NO
HISTORICAL_BACKFILL=NO
TASK_015_RESUMED=NO
```

After this candidate is merged, a separate authorized Production activation is still required: deploy the exact promoted API/Worker artifacts through the normal release process, verify runtime provenance and checkpoint writes, and observe a future eligible current-day POST_CLOSE run. Do not replay 2026-09-29 or 2026-09-30 as part of this task.

```text
TASK_STATUS=CANDIDATE_PENDING_EXACT_SHA_CI_AND_PROMOTION
TASK_COMPLETE=NO
NEXT_RECOMMENDED_TASK=after merge, activate the exact canonical API/Worker SHA through the normal deployment task and observe the next eligible current-day POST_CLOSE run; no historical replay
```
