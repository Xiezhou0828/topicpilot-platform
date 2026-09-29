# TASK-POST-CLOSE-20260929-EXCHANGE-NO-DATA-ROOT-CAUSE-017

## Executive disposition

This is a read-only forensic report for Production post-close run
`30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a` on `2026-09-29`.

The incident is **not proven to be a permanent TWSE/TPEx payload-contract
change**. At `2026-09-29 23:56 Asia/Taipei`, both exact official market
endpoints returned HTTP 200, the requested date, the expected market table,
and the expected field shape. The nearest comparable exchange probes for
`2026-09-24` also returned valid date-matched payloads.

The incident-time cause cannot be narrowed to one exchange or to provider
readiness with high confidence because the public Production read API does not
expose `live_collector_attempts`, `live_collector_checkpoints`, provider-call
timestamps, per-market adapter outcomes, or the previous successful run. The
correct terminal state is therefore:

`BLOCKED_PROTECTED_PRODUCTION_READBACK_REQUIRED`

Primary classification:

`UNKNOWN_INSUFFICIENT_EVIDENCE`

Most plausible but unconfirmed family:

`PROVIDER_NOT_READY_AT_RUN_TIME` / `TRANSIENT_PROVIDER_FAILURE`

The current code also contains a structurally amplifying fallback: a failed
market-level batch enters per-instrument fallback and can repeat the provider
request. This is a code-path risk, not a claim that the incident definitely
entered fallback.

No Production database, scheduler, post-close writer, migration, or persisted
provider payload was changed by this investigation.

## Repository and runtime authority

| Item | Evidence |
|---|---|
| Repository | `Xiezhou0828/topicpilot-platform` |
| Latest `origin/main` | `979f3509934b88a2dfbde507704b7511b42ac734` |
| Latest `origin/main` commit | `docs: close migration and worker authority task (#21)` |
| Production API SHA | `6cb88c0d7fceb45b244d295883636706f50ea0be` from `/healthz` and `/readyz` |
| Incident Worker/post-close SHA | Not exposed by the public read API; not asserted |
| Production referenceDataVersion | `tw-reference-v1` from live configuration |
| Adapter lineage in repository | `twse-official-daily.v2`, `tpex-official-daily.v2` |
| Relevant code delta, `6cb88c0d` to current `main` | None for `live/post_close.py` and `market_data/exchange.py` |
| Migration readback | `0047_task_topic_role_strength_design_freeze`; read-only `/api/v1/admin/migration` |

The API SHA predates the current `main` documentation commits, but the
incident-relevant post-close and exchange adapter files are unchanged between
the deployed API SHA and current `main`. This does not prove the Worker used
the same SHA; the Worker identity remains an evidence gap.

## Incident timeline

| Event | UTC | Asia/Taipei |
|---|---:|---:|
| Post-close run started | `2026-09-29T05:39:57.482336Z` | `13:39:57.482336` |
| Run completed | `2026-09-29T06:09:46.671071Z` | `14:09:46.671071` |
| Home marketOverview updatedAt | `2026-09-29T06:09:39.893236Z` | `14:09:39.893236` |
| Home generated/published | `2026-09-29T06:09:43.471001Z` | `14:09:43.471001` |
| Direct exchange probe capture | `2026-09-29T15:56:46Z` | `23:56:46` |

The public live status readback was:

| Field | Value |
|---|---:|
| Run status | `FAILED` |
| Requested | `553` |
| Success | `0` |
| Failed | `347` |
| Skipped | `206` |
| Retry count | `0` |
| Provider status | `ERROR` |
| Freshness | `PARTIAL` |
| Run-level failure code/message | `EXCHANGE_NO_DATA` |
| Public universeCounts | `UNKNOWN=555`, `TOTAL=555` |
| providerHealth | `[]` |

The counts reconcile arithmetically (`347 + 206 = 553`) but the public
response does not identify which market, provider, adapter version, or error
message produced each count. No market split is inferred from the aggregate.

## Previous successful-session comparison

The repository calendar marks `2026-09-28` as a `TW_MARKET` holiday, so the
nearest comparable session is `2026-09-24`. The public Home read model names
`2026-09-24` as the previous published trading session, and the latest formal
topic snapshot is also dated `2026-09-24`.

The public API does not provide a historical post-close run list, so the
following incident/run fields cannot be proven from the available readback:

| Comparison field | 2026-09-24 | 2026-09-29 incident |
|---|---|---|
| governed post-close run ID | Not exposed | `30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a` |
| run status/counts | Not exposed | `FAILED`, `0/347/206` |
| provider-call timestamps | Not exposed | Not exposed |
| adapter version from run rows | Not exposed | Not exposed |
| reference binding from run rows | Not exposed | Not exposed |
| Worker runtime SHA | Not exposed | Not exposed |

The 2026-09-24 direct endpoint probes were successful and date matched; this
is provider evidence, not proof that the 2026-09-24 governed post-close run
was successful.

## Production operational-table readback

The requested tables are not exposed by the public API:

- `topicpilot.live_collector_runs`: only the latest aggregate is exposed by
  `/api/v1/operations/live/status`.
- `topicpilot.live_collector_attempts`: no public read route.
- `topicpilot.live_collector_checkpoints`: no public read route.

Therefore the following required forensic facts remain unavailable:

- grouped attempt rows by `market_code`, `provider_code`, `adapter_version`,
  `provider_status`, `status`, `error_code`, and `error_message`;
- first TWSE and TPEx provider request timestamps;
- provider request count and response timestamp per market;
- checkpoint rows for `SESSION_VALIDATION`, `INPUT_READINESS`,
  `FORMAL_MARKET_FACTS:TPE`, `FORMAL_MARKET_FACTS:TWO`,
  `A9_B2_FORMAL_PROCESSING`, `FINAL_PUBLICATION`, and `COMPLETION`;
- the exact first failing checkpoint;
- the exact 206 skipped-reason distribution;
- a previous successful run ID and its runtime/reference binding.

`FIRST_FAILED_CHECKPOINT` is consequently `UNKNOWN` in this report. The code
and final Home state make `FORMAL_MARKET_FACTS` a reasonable candidate, but it
is not promoted to a fact without the checkpoint rows.

## Direct official provider probes

The probes used only HTTP GET and held the response in memory. No response was
written to Production or to the repository.

### 2026-09-29

| Field | TWSE / TPE | TPEx / TWO |
|---|---:|---:|
| Request | `MI_INDEX?date=20260929&type=ALLBUT0999&response=json` | `dailyQuotes?date=2026/09/29&response=json` |
| HTTP status | `200` | `200` |
| Content type | `application/json; charset=UTF-8` | `application/json; charset=UTF-8` |
| Response size | `232,599` bytes | `1,643,106` bytes |
| Payload stat | `OK` | `ok` |
| Payload date | `20260929` | `20260929` |
| Tables | `10` | `2` |
| Expected table | Present | Present: `上櫃股票行情` |
| Row count | `1,382` | `11,730` |
| First field | `證券代號` | `代號` |
| Contract classification | `CONTRACT_MATCH` | `CONTRACT_MATCH` |

### 2026-09-24 comparison

| Field | TWSE / TPE | TPEx / TWO |
|---|---:|---:|
| HTTP status | `200` | `200` |
| Content type | `application/json; charset=UTF-8` | `application/json; charset=UTF-8` |
| Response size | `230,683` bytes | `1,631,787` bytes |
| Payload stat | `OK` | `ok` |
| Payload date | `20260924` | `20260924` |
| Tables | `10` | `2` |
| Expected table | Present | Present: `上櫃股票行情` |
| Row count | `1,380` | `11,660` |
| Contract classification | `CONTRACT_MATCH` | `CONTRACT_MATCH` |

The current responses satisfy the adapter checks in
`services/api/src/topicpilot_api/market_data/exchange.py`:

- TWSE requires `stat.upper() == OK`, response date `YYYYMMDD`, a `tables`
  array, and a table whose first field is `證券代號`.
- TPEx requires `stat.lower() == ok`, response date `YYYYMMDD`, a `tables`
  array, and a table titled `上櫃股票行情` whose first field is `代號`.
- Both adapters validate row shape and normalize the official daily payload;
  neither current probe showed date mismatch, missing table, invalid JSON, or
  schema drift.

The successful current probe is later than the incident by several hours. It
proves current reachability and contract compatibility, not the provider state
at `13:39:57`.

## Reference and universe readback

The public read API reports two active markets and 556 instrument rows. A
read-only pagination of the public active `EQUITY` identity view produced:

| Scope | Count |
|---|---:|
| Active TPE physical rows | `348` |
| Active TWO physical rows | `207` |
| Active TPE/TWO EQUITY rows | `555` |
| Incident requested count | `553` |

The difference between physical active rows and the incident request is a
date-effective/universe question that the public API does not expose. It must
not be converted into a TPE/TWO expected-count split by arithmetic alone.

The current direct payload coverage against the current physical active view
was `346/348` for TPE and `206/207` for TWO. The current missing physical
codes were `TPE:2601,6806` and `TWO:5371`. This is a current probe result,
not incident attempt evidence and not a claim that those codes explain the
347/206 run totals.

The public configuration confirms:

- timezone `Asia/Taipei`;
- session close `13:30` and post-close start `13:35`;
- `referenceDataVersion=tw-reference-v1`;
- `historyBatchSize=20`;
- `historyRequestsPerMinute=30`;
- `historyMaxRetries=4`;
- `providerTimeoutSeconds=30`;
- `closedDates=[]` in runtime configuration.

No active registry version, date-effective instrument set, or Worker-side
reference binding for the incident is publicly readable.

## Market-batch and fallback behavior

The relevant `main` code path is present at
`services/api/src/topicpilot_api/live/post_close.py`:

1. It builds the official registry with `market_batch=True`.
2. It partitions the requested instruments by TPE/TWO and configured batch
   size.
3. A batch calls `ingest_historical` with many instruments; the official
   adapter caches a successful one-date market payload.
4. If the batch transaction raises, the code rolls back and enters a
   savepoint-isolated per-instrument fallback.
5. Fallback exceptions increment `failure_count`; a returned result with no
   covered bar/no lifecycle-authorized no-trade evidence becomes
   `SKIPPED`/`MISSING_MARKET_DATA`; a covered priced or authorized no-trade
   result becomes `SUCCESS`.

This code explains how one market-level error can become many instrument-level
failures: the fallback re-invokes `ingest_historical` once per instrument.
When the adapter fails before caching a market response, the failing request is
not a reusable successful cache entry, so the fallback can repeat the failed
provider call. This is classified as `FALLBACK_AMPLIFICATION_POSSIBLE`, not
as a proven incident observation.

The incident aggregate `0 success / 347 failure / 206 skipped` is therefore
semantically consistent with a mixture of exception outcomes and uncovered
result outcomes, but the public API cannot determine the exact market split or
reason counts. In particular, `206 skipped` must not be labelled “TPEx”,
“no-trade”, or “exchange confirmed no data” without the attempt rows.

## Why Home reached approximately 14:09 while Topics did not

The Home readback for the incident source run says:

- `publication.state=PUBLISHED`;
- `sourceRunId=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a`;
- `marketOverview.dataDate=2026-09-29`;
- `marketOverview.updatedAt=2026-09-29T06:09:39.893236Z`;
- `marketOverview.dataStatus=AVAILABLE`;
- `mainTopics.status=UNAVAILABLE`;
- `mainTopics.reasonCode=NO_FORMAL_TOPIC_PUBLICATION`;
- latest formal topic snapshot remains `2026-09-24`.

The Home market facts were sourced from:

- TPE: `TWSE_OFFICIAL_MI_INDEX_DAILY_AGGREGATE`;
- TWO: `TPEX_OFFICIAL_DAILY_QUOTES_AGGREGATE`;
- total turnover: deterministic sum of the matching TPE/TWO formal facts.

The post-close finalization code deliberately has a market-facts-only branch.
When daily stock reconciliation is not downstream-ready, it can call
`materialize_home_v2` with independent official index/aggregate facts while
blocking stock-dependent topic snapshot publication. This is why the Home
market overview can advance at `14:09:39` even though formal topics remain
unavailable. It is not evidence that the lower-half Topic writer succeeded.

## Root-cause assessment

| Candidate | Assessment |
|---|---|
| TWSE provider issue | Not isolated; current TWSE probe passes |
| TPEx provider issue | Not isolated; current TPEx probe passes |
| Request timing / exchange publication timing | Plausible, but incident request timestamps are unavailable |
| Payload contract/schema drift | Not supported by current or 2026-09-24 probes |
| Parser defect | Not supported by current contract-match probes |
| Runtime configuration mismatch | Not proven; API config is readable, Worker config/SHA is not |
| Reference/universe interaction | Not proven; date-effective incident universe is not publicly readable |
| Transient provider response | Plausible, but incident response body/status is unavailable |
| Fallback amplification | Structurally possible in code; incident entry is unproven |

### Primary classification

`UNKNOWN_INSUFFICIENT_EVIDENCE`

### Secondary contributing possibilities

- `PROVIDER_NOT_READY_AT_RUN_TIME` or `TRANSIENT_PROVIDER_FAILURE` is the
  leading operational hypothesis because the incident reported
  `EXCHANGE_NO_DATA`, both endpoints later returned correct data, and no
  current contract drift was observed.
- `FALLBACK_AMPLIFICATION_DEFECT` is a design risk that can magnify one
  market-level failure into many repeated instrument failures.
- `FORMAL_MARKET_FACTS_ONLY_PUBLICATION` is an intentional downstream
  separation that explains the Home timestamp; it is not itself the root cause
  of the provider failure.

## Remediation design only

No remediation was implemented in this task. After protected readback confirms
the incident path, the minimum design should be selected from:

1. Add per-provider request telemetry with market, URL/query fingerprint,
   request start/end, HTTP status, payload stat/date, table selection, row
   count, adapter version, and normalized error code.
2. Add a governed provider-readiness gate after the exchange close window:
   both official target-date probes must be reachable, date-matched, and
   contract-valid before the writer starts.
3. Retry a non-ready market-level response with bounded market-specific
   backoff before entering instrument fallback.
4. Suppress redundant per-instrument fallback when the market-level provider
   request is known unavailable, or record it as one market outage rather than
   repeating the same failure hundreds of times.
5. Preserve the independent market-facts-only Home path, but expose its
   publication mode clearly in operational status.

## Retry readiness criteria

Retry is **not authorized** by this report.

Required conditions before a separately authorized retry:

- `TWSE_DIRECT_PROBE=PASS` for `20260929`;
- `TPEX_DIRECT_PROBE=PASS` for `20260929`;
- both payload dates equal `20260929`;
- expected tables and field positions match adapter-v2;
- protected SELECT-only readback confirms the incident run/checkpoints and
  confirms no complete formal Topic publication already exists;
- active date-effective reference context and exact requested universe are
  verified;
- Worker runtime SHA and adapter lineage are verified;
- no schema drift, provider-date mismatch, or unresolved provider error;
- an operator separately authorizes the exact bounded retry and its write set.

Current retry state: `NO`.

Current blockers: missing protected per-attempt/checkpoint readback, missing
historical successful run comparison, unverified Worker SHA/config, and no
authoritative incident-time provider response evidence.

## Required final status block

~~~text
TASK_ID=TASK-POST-CLOSE-20260929-EXCHANGE-NO-DATA-ROOT-CAUSE-017
TASK_STATUS=BLOCKED_PROTECTED_PRODUCTION_READBACK_REQUIRED
CURRENT_MAIN_SHA=979f3509934b88a2dfbde507704b7511b42ac734
INCIDENT_RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
INCIDENT_TRADING_DATE=2026-09-29
INCIDENT_RUNTIME_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be (API only; Worker unverified)
INCIDENT_REFERENCE_VERSION=tw-reference-v1 (public runtime config; incident row unverified)
PREVIOUS_SUCCESS_RUN_ID=NOT_EXPOSED
PREVIOUS_SUCCESS_TRADING_DATE=2026-09-24 (nearest comparable published session)
PREVIOUS_SUCCESS_RUNTIME_SHA=NOT_EXPOSED
TPE_EXPECTED=NOT_EXPOSED
TWO_EXPECTED=NOT_EXPOSED
TPE_SUCCESS_COUNT=NOT_EXPOSED
TPE_FAILURE_COUNT=NOT_EXPOSED
TPE_SKIPPED_COUNT=NOT_EXPOSED
TPE_PRIMARY_ERROR=NOT_EXPOSED
TWO_SUCCESS_COUNT=NOT_EXPOSED
TWO_FAILURE_COUNT=NOT_EXPOSED
TWO_SKIPPED_COUNT=NOT_EXPOSED
TWO_PRIMARY_ERROR=NOT_EXPOSED
FIRST_FAILED_CHECKPOINT=UNKNOWN (checkpoint rows not publicly exposed; FORMAL_MARKET_FACTS is only a candidate)
TWSE_HTTP_STATUS=200 (current read-only probe)
TWSE_PAYLOAD_STAT=OK
TWSE_RESPONSE_DATE=20260929
TWSE_ROW_COUNT=1382
TWSE_CONTRACT_STATUS=CONTRACT_MATCH
TPEX_HTTP_STATUS=200 (current read-only probe)
TPEX_PAYLOAD_STAT=ok
TPEX_RESPONSE_DATE=20260929
TPEX_ROW_COUNT=11730
TPEX_CONTRACT_STATUS=CONTRACT_MATCH
INCIDENT_PROVIDER_REQUEST_TIME_TPE=NOT_EXPOSED
INCIDENT_PROVIDER_REQUEST_TIME_TWO=NOT_EXPOSED
PREVIOUS_SUCCESS_PROVIDER_REQUEST_TIME_TPE=NOT_EXPOSED
PREVIOUS_SUCCESS_PROVIDER_REQUEST_TIME_TWO=NOT_EXPOSED
MARKET_BATCH_STATUS=CODE_PATH_ENABLED; INCIDENT_EXECUTION_NOT_VERIFIED
FALLBACK_PATH_STATUS=CODE_PATH_PRESENT; INCIDENT_EXECUTION_NOT_VERIFIED
FALLBACK_AMPLIFICATION_STATUS=STRUCTURALLY_POSSIBLE; NOT_PROVEN
SKIPPED_206_CLASSIFICATION=NOT_PROVEN; public aggregate cannot distinguish no-row/lifecycle/no-priced-bar reasons
MARKET_OVERVIEW_UPDATED_AT=2026-09-29T06:09:39.893236Z
MARKET_OVERVIEW_UPDATED_AT_SOURCE=HomePublication market-facts-only path; TWSE MI_INDEX aggregate plus TPEx dailyQuotes aggregate
HOME_20260929_STATUS=PUBLISHED (market facts only)
TOPIC_20260929_STATUS=UNAVAILABLE; NO_FORMAL_TOPIC_PUBLICATION
PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
SECONDARY_CONTRIBUTING_CAUSES=PROVIDER_NOT_READY_AT_RUN_TIME or TRANSIENT_PROVIDER_FAILURE (plausible, unconfirmed); FALLBACK_AMPLIFICATION_POSSIBLE
ROOT_CAUSE_CONFIDENCE=LOW for a specific cause; HIGH that current contract drift is not evidenced
REMEDIATION_REQUIRED=YES (design only; no execution)
RECOMMENDED_REMEDIATION=Protected telemetry/readback first; then readiness gate/backoff and market-level fallback suppression if confirmed
RETRY_READY=NO
RETRY_BLOCKERS=Protected attempt/checkpoint readback; prior-success comparison; Worker SHA/config verification; incident-time provider evidence
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
PROVIDER_DATA_PERSISTED=NO_BY_THIS_TASK
SCHEDULER_CHANGED=NO
TASK_COMPLETE=YES (report complete; root cause remains blocked)
NEXT_RECOMMENDED_TASK=Protected SELECT-only Production readback for the incident run and nearest prior successful governed run
~~~

## Evidence URLs

- Production health: `https://topicpilot-api.onrender.com/healthz`
- Production live status: `https://topicpilot-api.onrender.com/api/v1/operations/live/status`
- Production live configuration: `https://topicpilot-api.onrender.com/api/v1/operations/live/configuration`
- Production Home read model: `https://topicpilot-api.onrender.com/api/v2/home`
- Latest formal topic snapshot: `https://topicpilot-api.onrender.com/api/v2/topic-snapshots?latest=true&limit=1`
- TWSE probe endpoint: `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260929&type=ALLBUT0999&response=json`
- TPEx probe endpoint: `https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?date=2026%2F09%2F29&response=json`
