# TASK-DATA-022A | Formal No-Trade / Trading-Status Coverage Report

**Date:** 2026-08-12
**Work item:** TASK-DATA-022A, layered on TASK-DATA-022
**Scope:** repository-side contract, persistence, reconciliation, tests, and documentation
**Production writes/scheduler:** not performed; scheduling remains WAITING/BLOCKED

## Existing Model Audit

The repository already has a canonical trading-status observation family and
the `canonical_trading_status_observations` reference model. The existing V2
path is:

```text
official provider adapter
  -> historical fetch result
  -> raw observation / timeline entry
  -> normalized canonical PRICE and TRADING_STATUS observations
  -> daily projection view
  -> post-close reconciliation
  -> downstream topic/Lifecycle handoff
```

The audit also found these pre-existing gaps:

- an official empty response could be treated as an empty price set rather than
  explicit exchange-confirmed no-trade evidence;
- the ingestion loop could skip a zero-bar instrument entirely;
- the daily projection and reconciliation equated coverage with a non-null
  close, so a valid suspended/no-trade instrument always blocked a full run;
- provider errors, unknown missing data, and approved no-trade evidence were not
  represented as distinct coverage states;
- the private Taishin path is intraday and Yahoo history is verification-only;
  neither is the formal TPE/TWO daily authority.

No second identity store, Google Sheets writer, V1 quote writer, or Lifecycle
algorithm was introduced.

## Root Cause

Coverage had been defined as ?one accepted daily price with a non-null close per
active instrument.? That is too strict for exchange sessions in which an
instrument is formally listed in the expected universe but did not trade or was
suspended. Treating those cases as a missing price either blocks the entire
run or invites unsafe zero/forward-fill behavior. The implementation now keeps
price completeness and evidence coverage as separate measures.

## Chosen Coverage Semantics

The allowed daily trading-status values are:

| Status | Meaning | Covered? | Priced? |
|---|---|---:|---:|
| `AVAILABLE` | Official daily observation with a usable close | Yes | Yes |
| `SUSPENDED` | Explicit suspended/no-trade state | Yes | No |
| `NO_TRADE` | Explicit no-trade state | Yes | No |
| `EXCHANGE_CONFIRMED_NO_DATA` | Official exchange response confirms no row for the requested date | Yes | No |
| `UNKNOWN` | Missing or unresolved explanation | No | No |
| `OPEN` | Legacy compatibility value retained for existing fixtures/contracts | Contract-compatible | Contract-compatible |

For every expected instrument/date the reconciliation records:

- `expected_count`: active formal universe size;
- `observed_count`: selected daily projection rows;
- `priced_count`: rows with a non-null close;
- `covered_count`: priced rows plus approved no-trade rows;
- `unavailable_count`: expected rows that are unpriced;
- `unexplained_missing_count`: expected rows that are not covered.

An approved no-trade row is covered but unpriced. Its close, OHLCV, and volume
remain `NULL`; the pipeline never writes zero, forward-fills a prior close, or
fabricates an OHLC bar. A provider failure, malformed response, wrong date, or
unexplained absence remains `UNKNOWN`/uncovered and blocks readiness.

The exact acceptance examples are:

- 506 priced + 1 approved no-trade = 507 covered, 507 expected, zero
  unexplained, `READY`, `downstreamReady=true`;
- 506 priced + 1 unknown missing = 506 covered, one unexplained,
  `PARTIAL`, `downstreamReady=false`.

Non-trading days are `MARKET_CLOSED`, produce an audit result, and do not
create a topic snapshot.

## Trading-Status Evidence Authority

The authority order remains the existing source registry and adapter role
contracts:

1. official TWSE daily response for TPE;
2. official TPEx daily response for TWO;
3. the existing canonical normalization and reference status catalogue;
4. private Taishin intraday and Yahoo daily history only as non-authoritative
   verification/fallback inputs.

An official response with `stat=OK` and no row for the requested single date is
mapped to `EXCHANGE_CONFIRMED_NO_DATA`. Non-OK provider responses continue to
fail closed as provider errors; they are not silently reclassified as
no-trade. This preserves the distinction between ?the exchange confirmed no
row? and ?the provider did not deliver trustworthy evidence.?

## Schema/Persistence

The existing raw observation, timeline, canonical observation, and
`canonical_trading_status_observations` structures are reused. Migration
`0026_task_data_022a_no_trade_coverage` replaces the existing daily projection
view with an additive status-aware projection exposing:

- stable key `market_code:instrument_code:trade_date`;
- selected OHLCV and quality/source lineage;
- `status_code`, `status_reason`, and `status_context`;
- `candidate_count` for duplicate-source diagnostics;
- `covered` derived from a non-null close or an approved no-trade status.

The view filters to accepted/incomplete canonical daily PRICE evidence, official
daily source codes, and non-superseded current observations. It joins the
status observation on the same timeline entry/source so status and price
evidence cannot drift to another retrieval. No identity, topic, hierarchy, or
relation rows are modified.

## Migration Decision

The migration is limited to the daily projection view and is chained after
0025. It performs no bootstrap, truncate, table drop, identity rewrite, or
destructive data migration. Downgrade only removes the derived view; canonical
raw/timeline/status data remains intact. Production migration was not executed
because protected Neon credentials and an approved release operation were not
provided.

## Reconciliation Changes

`assess_daily_coverage()` now accepts independent observed, priced, and covered
counts per market. Readiness requires:

- expected TPE/TWO identity coverage derived from the canonical universe;
- `covered_count == expected_count`;
- `unexplained_missing_count == 0`;
- `wrongDateCount == 0`;
- `duplicateKeyCount == 0`;
- no `MARKET_CLOSED`, empty-universe, or provider-failure condition.

`UNAVAILABLE_DAILY_CLOSE` and `APPROVED_NO_TRADE_COVERAGE` remain explanatory
reasons when an otherwise complete run contains unpriced approved rows;
approved no-trade does not by itself block readiness. Unknown or unexplained
rows produce `INCOMPLETE_COVERAGE`/`UNEXPLAINED_MISSING_DATA` and block the
downstream gate.

## Post-Close Changes

The existing post-close runner continues to create one collector run and one
attempt per formal instrument. A result with approved no-trade evidence counts
as a successful covered instrument even when it has zero price bars; the audit
records its status and reason. An unresolved empty result is recorded as
`UNEXPLAINED_MISSING_DATA` and remains failed/uncovered. Retry counts,
provider status, per-market counts, and the final reconciliation are retained
in run metadata.

The topic snapshot call remains behind the reconciliation gate. A `READY` run
may hand off to downstream processing; `PARTIAL`, `FAILED`, and `MARKET_CLOSED`
runs do not.

## Lifecycle Handoff Contract

Lifecycle may consume only a completed daily date whose post-close metadata
contains `status=READY`, `coveredCount=expectedCount`,
`unexplainedMissingCount=0`, `wrongDateCount=0`, `duplicateKeyCount=0`, and
`downstreamReady=true`. The handoff includes canonical daily observation
evidence and status-aware coverage; it does not alter Lifecycle scoring,
thresholds, state transitions, or persistence algorithms.

## Retry/Backfill

The same date/source/instrument stable keys are reused on retry. Historical
request hashes, canonical idempotency keys, and supersession rules keep a
retry safe and allow an explicit `--run-date YYYY-MM-DD` backfill. A retry may
replace the current selected observation through existing canonical lineage;
it must not insert a second identity or fabricate a bar. A failed provider
response remains visible in the audit until a subsequent run supplies valid
evidence.

## Tests

The targeted regression suite passed: **29 passed** across daily coverage,
no-trade normalization, official provider parsing, historical provider
contracts, rate limiting, and live runtime behavior. The tests prove:

- official empty TWSE response (`stat=OK`, no row) becomes
  `EXCHANGE_CONFIRMED_NO_DATA`;
- explicit no-trade normalization emits accepted `TRADING_STATUS` plus an
  incomplete PRICE candidate with a null close;
- null close is not coerced to zero;
- 506 + 1 approved no-trade is READY and 506 + 1 unknown is PARTIAL;
- wrong dates, duplicate stable keys, market-closed dates, and incomplete
  coverage fail closed;
- migration 0026 contains the canonical status join and approved coverage
  expression without destructive table operations.

PostgreSQL-backed tests remain conditional on an explicit test database URL;
no production database was contacted. A full repository test run still has an
unrelated pre-existing import blocker in `infra.scripts.phase1_bundle_report`.

## Files Changed

022A implementation files:

- `services/api/src/topicpilot_api/market_data/history.py`
- `services/api/src/topicpilot_api/market_data/exchange.py`
- `services/api/src/topicpilot_api/market_data/taishin.py`
- `services/api/src/topicpilot_api/market_data/ingestion.py`
- `services/api/src/topicpilot_api/normalizer/contracts.py`
- `services/api/src/topicpilot_api/normalizer/historical.py`
- `services/api/src/topicpilot_api/daily_market.py`
- `services/api/src/topicpilot_api/live/post_close.py`
- `services/api/alembic/versions/0026_task_data_022a_no_trade_coverage.py`
- `services/api/tests/test_no_trade_contract.py`
- `services/api/tests/test_daily_market.py`

TASK-DATA-022 files already present in this worktree remain historical
prerequisites and are not reimplemented by 022A.

## Documents Updated

- `docs/WORK_ORDERS.md` (new repository-ready 022A row)
- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`
- `docs/operations/deployment.md`
- this report

Historical decisions and the TASK-DATA-022 report were retained. No
authoritative `NEXT_TASK` file or decision was modified.

## Scheduling

The repository CLI/manual run path is available. The checked-in deployment
configuration does not provide an approved Render Cron resource, and no
external scheduler permission or secret was available. Therefore
`POST_CLOSE_PRODUCTION_SCHEDULING` remains `WAITING/BLOCKED`; no live 14:40
production schedule is claimed.

## Production Actions Not Performed

- no Neon production migration or write;
- no production 507-instrument run;
- no Render Cron provisioning;
- no secret creation, rotation, or third-party login;
- no changes to the formal 507 instruments, 130 topics, 107 hierarchy, or 848
  relations.

## Known Issues

- A reviewed Taiwan holiday/session calendar is still required for unattended
  scheduling.
- Non-OK official provider responses remain provider failures rather than
  confirmed no-trade; an explicit exchange decision would be required to
  broaden that mapping.
- The daily view assumes status and price evidence share the same timeline
  entry/source; duplicate status candidates are surfaced through
  `candidate_count` and should block reconciliation until corrected.
- Production migration and end-to-end 507 coverage remain unverified without
  protected Neon access.

## Risks

- Official TWSE/TPEx payload changes or delayed publication can produce
  partial/unknown coverage.
- Misclassifying provider failure as no-trade would contaminate breadth and
  Lifecycle inputs; the implementation intentionally fails closed.
- Operational tuning may be needed for one-instrument-per-request rate limits.
- A scheduler that runs before the official close files are complete can create
  an audit run that requires safe retry/backfill.

## Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Existing V1/V2 sources and ownership audited | PASS | audit and ownership sections above |
| Canonical source chosen from repository decisions | PASS | TWSE/TPEx official daily; Yahoo verify-only; Taishin intraday |
| Existing status family reused | PASS | canonical trading-status family and reference model |
| Explicit approved no-trade semantics | PASS | status/coverage table and normalizer tests |
| Stable stock/date idempotency preserved | PASS | existing canonical keys and daily stable key |
| No zero-fill, forward-fill, or fabricated OHLC | PASS | null-close normalization and tests |
| 506 priced + 1 approved no-trade | PASS | READY/covered regression test |
| 506 priced + 1 unknown missing | PASS | PARTIAL/unexplained regression test |
| Date/duplicate/market-closed validation | PASS | daily reconciliation tests |
| Retry/backfill safe | PASS (repository) | stable keys, supersession, manual date CLI |
| Lifecycle algorithm unchanged | PASS | only handoff contract changed |
| Additive migration only | PASS | migration 0026 view replacement; no table/data destructive operation |
| Targeted tests | PASS | 29 passed |
| Production Neon migration/write | NOT RUN | protected access not provided |
| Production scheduler | WAITING/BLOCKED | no approved scheduler/permissions |
| NEXT_TASK authority unchanged | PASS | suggestion only; no authority file changed |

## Suggested NEXT_TASK

`TASK-OPS-023 | V2 Daily Close Production Scheduling & First-Run Reconciliation`

An authorized operator should apply migration 0025 and 0026 in a protected
release, provision and verify the approved 14:40 Asia/Taipei trading-day
scheduler, configure the reviewed holiday calendar, run one manual canary and
one scheduled 507-instrument close, and capture Neon/run/API reconciliation.
Activation must require `downstreamReady=true`; secrets remain in the
protected runtime. This is a suggestion only and does not modify NEXT_TASK
authority.
