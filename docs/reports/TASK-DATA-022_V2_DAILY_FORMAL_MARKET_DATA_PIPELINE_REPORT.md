# TASK-DATA-022?V2 Daily Formal Market Data Pipeline Report

**Date:** 2026-08-12
**Branch/worktree:** `task-data-022` (isolated from parallel Lifecycle changes)
**Production writes:** none
**Result:** repository implementation ready; production scheduling blocked

## Existing Pipeline Audit

The repository contains four distinct historical/runtime paths:

1. V1 Google Sheets, Apps Script, Python analysis engines, R2/snapshot publication,
   and the legacy website. These are retained historical/formal inputs but are
   not a V2 canonical daily-observation writer.
2. V1-compatible private import modules under `legacy_import`. They map approved
   identity/reference artifacts into V2 and do not own the daily close.
3. The private intraday runtime under `live`, with Taishin capability on the
   Windows boundary and Yahoo quote fallback. It owns intraday observations,
   not the formal daily close.
4. The V2 historical/post-close path: official exchange adapters ? raw market
   observations ? observation timeline ? canonical observations ? topic/read
   models. This is the only path extended by TASK-DATA-022.

The existing `PostCloseUpdater` already selected active TPE/TWO equities,
called the official exchange adapters, normalized results, persisted collector
runs/attempts, refreshed tracking, and invoked topic snapshots. Its gaps were a
strict full-universe reconciliation, a stable daily projection, explicit
downstream readiness, accurate transport-retry audit, and fail-closed snapshot
behavior on partial/closed runs.

Repository evidence does not show Google Sheets polling or an old Python quote
script inside the V2 daily writer. No second identity or market-data path was
introduced.

## V1/V2 Ownership

| Capability | Current owner | TASK-DATA-022 decision |
|---|---|---|
| Formal identity (2 markets / 507 instruments) | Neon `topicpilot.markets` and `topicpilot.instruments` | Read only; unchanged |
| Topics / hierarchy / relations (130 / 107 / 848) | Neon V2 canonical tables | Unchanged |
| Legacy business inputs | V1 Sheets/Python/export workflow | Preserved; not called by daily job |
| Intraday quotes | Taishin private Windows boundary; Yahoo routed fallback | Unchanged; excluded from daily authority |
| Historical validation | Yahoo chart adapter | Verification-only |
| Daily TPE close | TWSE official daily adapter | Canonical production source |
| Daily TWO close | TPEx official daily adapter | Canonical production source |
| Persistence and audit | Neon raw/timeline/canonical plus live run/attempt tables | Reused |
| Scheduling | intended Render scheduler or approved equivalent | WAITING/BLOCKED |

## Canonical Source Decision

No new provider was selected. The checked-in registry already freezes:

- `TPE ? TWSE_OFFICIAL_DAILY` (official public daily data);
- `TWO ? TPEX_OFFICIAL_DAILY` (official public daily data);
- `YAHOO_CHART_DAILY ? verification_only=True`;
- `TAISHIN_TECH_ANALYSIS_INTRADAY ? intraday only`.

TASK-DATA-022 enforces that decision in reconciliation and documentation. A
provider-neutral contract remains above the adapters, so a later source change
requires an explicit registry/decision change rather than a Lifecycle change.

## Data Contract

`topicpilot.vw_daily_market_observations` is an additive view over accepted,
non-superseded canonical `DAILY_BAR` PRICE rows. It exposes:

- `stable_key = market_code:instrument_code:trade_date`;
- market/instrument UUID and formal codes;
- `trade_date`, OHLC, nullable volume;
- quality state, canonical/source lineage, observation/retrieval timestamps;
- selected source code and adapter version.

One source is selected for each instrument/date by existing source rank, then
latest retrieval/id. Missing numeric values remain null. The view does not copy
or mutate observations.

## DB Schema/Persistence

Migration `0025_task_data_022_daily_market_contract` only creates the daily
projection view. It is additive and follows Alembic head
`0024_task_be_007_topic_snapshots`.

Persistence continues to use the existing V2 chain:

```text
market_data_sources
  ? raw_market_observations
  ? observation_timeline_batches / entries
  ? canonical_observations
  ? canonical_price_observations / canonical_volume_observations
  ? vw_daily_market_observations
```

Historical ingestion request hashes and canonical idempotency keys make a
same-date retry reusable. Accepted corrections retain lineage/supersession and
the view resolves the current row; there is no destructive update, bootstrap,
truncate, or identity rewrite.

## Daily Run Flow

```text
resolve Asia/Taipei date and trading-day state
  ? load active TPE/TWO EQUITY universe
  ? create POST_CLOSE audit run
  ? rate-limited official TWSE/TPEx fetch with bounded retry
  ? validate/filter requested trade_date
  ? transactional raw/timeline/canonical normalization
  ? record per-instrument attempt and retry count
  ? reconcile canonical daily view against formal universe
  ? READY: refresh tracking, run topic snapshot, expose downstreamReady=true
  ? PARTIAL/FAILED/CLOSED: retain audit, block topic snapshot and Lifecycle handoff
```

The manual production/recovery command is:

```console
topicpilot-live --mode post-close --once --run-date YYYY-MM-DD
```

Omit `--run-date` for the scheduler-selected local date.

## Validation/Coverage

The gate validates the active TPE and TWO equity populations independently and
in total. For the confirmed production universe the expected total is 507; the
code derives it from canonical identity rather than hard-coding it.

`downstreamReady=true` requires:

- non-empty formal universe;
- observed count equals expected count for TPE and TWO;
- accepted, non-null daily close count equals expected count;
- requested/local trade date matches the canonical view date;
- no duplicate stable key.

Null close/volume is never converted to zero. A suspended or unavailable stock
is explicitly unavailable and blocks readiness until the canonical contract
contains approved evidence; the pipeline does not fabricate a bar. A partial
provider response is `PARTIAL`/`FAILED`, never a successful full batch.

## Retry/Backfill

The official transport provides bounded exponential retry and request pacing.
TASK-DATA-022 now records the actual transport retry count in run and attempt
audit. Per-instrument failure is isolated, committed attempts remain visible,
and a retry/backfill uses the same date/source/mapping keys.

Safe procedure:

1. correct the transient provider/network/configuration cause;
2. rerun the exact date with `--run-date`;
3. confirm canonical row reuse/current selection and 100% reconciliation;
4. allow downstream work only when `downstreamReady=true`.

No delete/reset/rebootstrap is needed or permitted.

## Scheduling

Repository-side CLI, long-running scheduler integration, manual date override,
and Render-compatible container command exist. The checked-in `render.yaml`
contains a web service and a long-running worker, but no approved Render Cron
resource. Prior records mention `TopicPilot_V2_Daily_Close_1440` on Windows as
partially ready, without a verified successful scheduled production run and
complete holiday authority.

**POST_CLOSE_PRODUCTION_SCHEDULING = WAITING/BLOCKED.**

No claim of a live 14:40 production schedule is made. An authorized operator
must provision/approve the scheduler and secrets, migrate production, and
capture the first successful run.

## Lifecycle Handoff Contract

Lifecycle may consume only completed daily observation dates whose POST_CLOSE
run metadata contains:

```json
{
  "dailyMarketReconciliation": {
    "status": "READY",
    "stableKey": "market_code:instrument_code:trade_date",
    "coveragePct": 100.0,
    "duplicateKeyCount": 0,
    "wrongDateCount": 0,
    "downstreamReady": true
  }
}
```

The actual member input remains accepted canonical daily close evidence for the
formal relation membership as-of that date. TASK-DATA-022 does not change stage
definitions, scoring, thresholds, confirmation, persistence, or any Lifecycle
algorithm.

## Tests

Added unit coverage proves:

- exact 507 cross-market coverage becomes READY;
- a partial TWO response fails closed;
- null close stays unavailable and is not coerced to zero;
- date mismatch and duplicate stable key block handoff;
- non-trading day is explicit and not downstream ready;
- actual transport retry count is audited.

Existing targeted suites cover scheduler routing, market-closed behavior,
provider registry roles, official provider parsing, historical transactional
ingestion, canonical idempotency, and PostgreSQL persistence. Database-backed
tests remain conditional on an explicit test PostgreSQL URL; no production
database was used.

## Files Changed

- `services/api/src/topicpilot_api/daily_market.py`
- `services/api/src/topicpilot_api/live/post_close.py`
- `services/api/src/topicpilot_api/market_data/rate_limit.py`
- `services/api/alembic/versions/0025_task_data_022_daily_market_contract.py`
- `services/api/tests/test_daily_market.py`
- `services/api/tests/test_rate_limit.py`

## Documents Updated

- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`
- `docs/operations/deployment.md`
- `docs/WORK_ORDERS.md`
- this report

Historical reports and status narratives were retained. `NEXT_TASK` was not
created or modified.

## Known Issues

- Production migration and a real 507-instrument close run were not executed;
  no Neon secret was available or requested.
- The holiday list is configuration-driven; a reviewed Taiwan exchange holiday
  calendar authority is still required for unattended scheduling.
- Current policy requires a non-null accepted close for every identity. A future
  additive trading-status contract may allow an explicitly suspended security
  to count as covered without fabricating a price.
- The existing post-close implementation makes one provider call per instrument
  and may require operational tuning within official endpoint limits.

## Risks

- Official endpoint availability or payload changes can create partial coverage.
- A worker that starts immediately after 13:30 may run before all official daily
  files are published; scheduling should retain the intended 14:40 window and
  bounded retry.
- Declaring partial coverage ready would contaminate topic breadth and Lifecycle;
  the new gate intentionally favors delayed results over fabricated completeness.
- Running Alembic from multiple services concurrently remains an operational
  deployment concern already present in the blueprint.

## Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Existing V1/V2 pipeline audited | PASS | ownership/source analysis above |
| Canonical source decided from repository | PASS | TWSE/TPE; TPEx/TWO; Yahoo verify-only; Taishin intraday |
| No second identity/data path | PASS | additive view over canonical observations |
| Stable stock/date key | PASS | market + instrument + trade date projection |
| Idempotent retry/backfill | PASS (repository) | existing request/canonical keys plus manual date CLI |
| TPE/TWO coverage validation | PASS (tests) | per-market reconciliation |
| Formal 507 coverage | PASS (contract/tests); production run WAITING | derived expected universe; 507 test |
| Null/stopped/partial/date handling | PASS (tests) | fail-closed reconciliation |
| Run audit/reconciliation | PASS | collector metadata and attempts |
| Downstream-ready state | PASS | explicit boolean and reason codes |
| Lifecycle algorithm unchanged | PASS | no Lifecycle files changed |
| Additive migration only | PASS | one view; no bootstrap/reset |
| Unit/targeted tests | PASS | recorded in verification handoff |
| PostgreSQL integration | CONDITIONAL | requires explicit test database |
| Production migration/run | NOT RUN | requires protected Neon access |
| Production scheduler | WAITING/BLOCKED | no approved Render Cron evidence |
| NEXT_TASK unchanged | PASS | no file created/edited |

## Suggested NEXT_TASK

`TASK-OPS-023?V2 Daily Close Production Scheduling & First-Run Reconciliation`

An authorized operator should apply migration 0025 to production, provision the
approved 14:40 Asia/Taipei trading-day scheduler, configure a reviewed holiday
calendar, run one manual canary and one scheduled 507-instrument close, and
capture DB/run/API reconciliation. Activation must require
`downstreamReady=true`; secrets must stay in the protected runtime.

This is a suggestion only. No `NEXT_TASK` authority or file was changed.
