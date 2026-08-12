# TASK-DATA-022-FIX01A｜Official Daily Provider 507/0 Root Cause Diagnostic

**Date:** 2026-08-12 (Asia/Taipei)
**Scope:** repository/provider-only diagnostic; no production write
**Canonical authority:** TPE → `TWSE_OFFICIAL_DAILY`; TWO → `TPEX_OFFICIAL_DAILY`
**Status:** `PASS / VERIFIED (provider-only)`

## 1. Executive Result

The official endpoints are reachable and return valid 2026-08-12 data. The
repository's formal post-close path was using an instrument/month adapter call
for every instrument even though both exchanges expose a one-date market-level
daily-close dataset. The implementation now uses one market-level request per
provider for a single-date post-close run, indexes rows by exact instrument
code, validates the response date, and retains the old instrument/month path for
multi-day historical backfill.

The provider-only gates passed:

- 6/6 representative instruments: TPE 3/3 and TWO 3/3;
- 50/50 bounded formal-catalog sample: TPE 25/25 and TWO 25/25;
- 507/507 formal provider outcomes: 506 priced rows plus one explicit official
  no-row result for TPE/6806 (`EXCHANGE_CONFIRMED_NO_DATA`).

The previously observed production run (`507 requested / 0 success / 507
failure`) was not rerun. Its public read-only status exposes only an aggregate
failure code/message, not per-instrument request/response payloads. Therefore
the exact historical cause of every one of those 507 attempts cannot be proved
from the available evidence; this report does not invent a deployment,
throttle, or reference-data explanation.

## 2. Existing Pipeline Audit

### Provider ownership

| Market | Canonical provider | Existing role | Result |
|---|---|---|---|
| TPE | `TWSE_OFFICIAL_DAILY` | official daily source | preserved |
| TWO | `TPEX_OFFICIAL_DAILY` | official daily source | preserved |
| TPE/TWO | `YAHOO_CHART_DAILY` | verification-only | unchanged |
| TPE/TWO | `TAISHIN_TECH_ANALYSIS_INTRADAY` | intraday-only | unchanged |

`PostCloseUpdater.run_once` previously iterated each formal instrument and
called `ingest_historical` with a one-instrument list. `ingest_historical`
then called `provider.fetch_daily` for each item. The old official adapters
therefore produced one `STOCK_DAY`/`tradingStock` request per instrument.

### Error locations

- `EXCHANGE_NO_DATA` is raised by the official adapters when the exchange
  payload's `stat` is not `OK`/`ok`.
- `REFERENCE_DATA_UNAVAILABLE` is raised by
  `market_data/ingestion.py` when `NormalizationRuntime` cannot load the
  versioned database reference context. It is a normalization/reference-stage
  error, not a synonym for provider failure.
- The live run aggregates distinct per-attempt codes into one run-level
  message, which explains why the public status can show
  `EXCHANGE_NO_DATA;REFERENCE_DATA_UNAVAILABLE` without exposing which
  instruments failed at which stage.

## 3. Official Endpoint Contract Evidence

### TWSE

`MI_INDEX?date=20260812&type=ALLBUT0999&response=json` returned HTTP 200,
`application/json;charset=UTF-8`, a 246,615-byte payload, response date
`20260812`, and a daily-close table with 1,379 rows. The table fields begin
with `證券代號` and contain open/high/low/close/volume columns.

### TPEx

`dailyQuotes?date=2026/08/12&response=json` returned HTTP 200,
`application/json;charset=UTF-8`, a 1,560,462-byte payload, response date
`20260812`, and an `上櫃股票行情` table with 10,400 rows. The table fields begin
with `代號` and contain close/open/high/low/成交股數 columns.

Both are market-level daily datasets. The existing per-instrument endpoints
remain valid for historical fallback, but they are the wrong granularity for a
single-date 507-instrument close.

## 4. Six-Stock Direct Diagnostic (2026-08-12)

All calls were public HTTP GETs through the existing adapter objects. No
database, ingestion service, ORM session, snapshot, Lifecycle, scheduler, or
production runner was invoked.

| Instrument | Market | Provider | Request count | HTTP/parser | Normalized date | Close |
|---|---|---|---:|---|---|---:|
| 2330 | TPE | TWSE official | 1 | 200 / PASS | 2026-08-12 | 2415.00 |
| 2317 | TPE | TWSE official | 1 | 200 / PASS | 2026-08-12 | 270.00 |
| 2454 | TPE | TWSE official | 1 | 200 / PASS | 2026-08-12 | 4015.00 |
| 4979 | TWO | TPEx official | 1 | 200 / PASS | 2026-08-12 | 561.00 |
| 6510 | TWO | TPEx official | 1 | 200 / PASS | 2026-08-12 | 2825.00 |
| 8048 | TWO | TPEx official | 1 | 200 / PASS | 2026-08-12 | 52.40 |

The provider trace used exactly these sanitized endpoints:

```text
https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260812&type=ALLBUT0999&response=json
https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?date=2026%2F08%2F12&response=json
```

## 5. Root-Cause Findings

| Check | Evidence-backed result |
|---|---|
| Endpoint validity | Current official market endpoints returned HTTP 200 and valid JSON. |
| Date serialization | TWSE request uses `YYYYMMDD`; TPEx uses `YYYY/MM/DD`; both returned payload date `20260812`. |
| Response schema | Market tables and column positions are confirmed; TPEx full-market rows use padded missing markers such as `" ---"`/`"--- "`. |
| Parser | Existing per-instrument parser handled the six samples. The new market parser handles the full-market schema and normalizes `---` as missing, never zero. |
| Symbol mapping | Exact provider row-code lookup resolved 506/507 formal symbols; TPE/6806 has no TWSE row and is retained as explicit official no-data. |
| Routing | Registry remains TPE → TWSE and TWO → TPEx; no Yahoo/Taishin substitution occurred. |
| Intraday misuse | Post-close builds the historical official registry; intraday providers are not in this path. |
| Fetch granularity | Confirmed implementation defect: one-date close is market-level, while the old path was per-instrument. |
| `EXCHANGE_NO_DATA` | Confirmed adapter-stage error for non-OK/no-row provider evidence. |
| `REFERENCE_DATA_UNAVAILABLE` | Confirmed independent normalization-stage error; exact production subcondition requires protected DB attempt evidence and was not guessed. |

## 6. Fix Implemented

### Runtime behavior

- Added one-date market-level parsing to both official adapters.
- Added per-provider market-response cache, so a shared post-close provider
  instance makes one request per market, not one request per instrument.
- Added response-date validation (`PROVIDER_DATE_MISMATCH`).
- Added deterministic duplicate-row and missing-table validation.
- Added `---` to the existing missing-value markers; null remains null and is
  never coerced to zero.
- Enabled `market_batch=True` only for the formal single-date `PostCloseUpdater`
  path. Multi-day historical backfill retains the existing instrument/month
  behavior.
- Bumped official adapter lineage versions to `twse-official-daily.v2` and
  `tpex-official-daily.v2`.

### Authority and persistence boundaries

No canonical source change, identity change, schema/migration change,
database write, Scheduler change, Topic Snapshot execution, Lifecycle
execution, or Opportunity Engine change was made by this task.

## 7. Post-Fix Read-Only Verification

| Gate | Result | Evidence |
|---|---|---|
| 6-stock direct diagnostic | PASS | TPE 3/3, TWO 3/3; target date and normalized bar present |
| 50-stock diagnostic | PASS | formal catalog sample TPE 25/25 + TWO 25/25 |
| Shared-provider batching | PASS | 50-stock run used one TWSE + one TPEx request |
| 507 provider-only diagnostic | PASS | 314 TPE + 193 TWO outcomes; 506 priced + 1 explicit no-data |
| Full priced 507/507 | NOT PASS | TPE/6806 has official no-row evidence; no fake bar created |
| Database write | NO | diagnostic scripts used HTTP and in-memory adapter state only |
| Production Canary | NOT RUN | explicitly excluded by FIX01A |
| Scheduler | UNCHANGED | no scheduler or deployment operation performed |

`EXCHANGE_CONFIRMED_NO_DATA` for 6806 is an approved covered/no-price state
under DATA-022A; it is not an unexplained provider failure. A future full
reconciliation still requires the protected runtime's reference context and
canonical persistence gates.

## 8. Tests and Validation

Targeted unit/regression tests:

```text
tests/test_no_trade_contract.py tests/test_v2_provider_registry.py
12 passed

tests/test_no_trade_contract.py tests/test_v2_provider_registry.py
tests/test_rate_limit.py tests/test_daily_market.py
tests/test_historical_provider.py tests/test_live_history_probe.py
tests/test_provider_orchestrator.py tests/test_live_provider.py
37 passed
```

Targeted Ruff and Python compile checks both passed for the modified provider,
registry, post-close, and test files.

## 9. Fixed Response Fields

```text
TASK_DATA_022_FIX01A = COMPLETE (provider-only; production canary excluded)
TWSE_DIRECT_HTTP = PASS
TPEX_DIRECT_HTTP = PASS
TWSE_ADAPTER = PASS
TPEX_ADAPTER = PASS
REFERENCE_RESOLUTION = PASS (formal 507 catalog identity; DB normalizer context NOT_RUN)
ROOT_CAUSE = One-date official close was fetched at per-instrument granularity; the market-level contract was not used. Historical 507/0 attempt-level subcause remains unprovable from aggregate public status.
ROOT_CAUSE_LOCATION = services/api/src/topicpilot_api/live/post_close.py; services/api/src/topicpilot_api/market_data/ingestion.py; services/api/src/topicpilot_api/market_data/exchange.py
EXCHANGE_NO_DATA_CAUSE = Adapter receives a non-OK payload or no row for the requested date/symbol; TPE/6806 is the confirmed current no-row case.
REFERENCE_DATA_UNAVAILABLE_CAUSE = NormalizationRuntime cannot load a complete active versioned reference context; ingestion maps that independent RuntimeLoadError to REFERENCE_DATA_UNAVAILABLE.
FETCH_GRANULARITY = PER_MARKET for one-date post-close; PER_INSTRUMENT fallback for multi-day history
FETCH_GRANULARITY_CORRECT = YES
FIX_IMPLEMENTED = YES
6_STOCK_READ_ONLY = 6 / 6
50_STOCK_READ_ONLY = 50 / 50
507_PROVIDER_ONLY = 507 / 507 (506 priced + 1 explicit official no-data)
PRODUCTION_DB_WRITE = NO
PRODUCTION_CANARY = NOT_RUN
SCHEDULER_CHANGED = NO
CANARY_2_READY = YES (provider-only; production reconciliation/reference gates remain external)
NEXT_TASK = NOT_MODIFIED
```

## 10. Operator-Only Next Step

Do not run a Canary from this repository. In the protected production
environment, an authorized operator should first deploy the adapter-v2 code,
confirm the active `tw-reference-v1` registry/reference context, and review
the explicit 6806 no-data policy. Only after those checks should a separately
authorized one-shot Production Canary be considered. Scheduler activation is
not authorized by this report.

Historical reports, provider ownership, and the external `NEXT_TASK` authority
were preserved and not modified.
