# TASK-A2-HISTORICAL-DATA-FOUNDATION-CANONICALIZATION-001

## Scope and safety boundary

This report covers the raw/canonical historical OHLCV foundation only. It does
not publish or backfill historical Topic, Score, Grade, Lifecycle, or
Opportunity state. The incomplete 2026-09-22 session is outside the audit
window and was not read or written.

```text
ROADMAP_WORKSTREAM=A2 Historical Data Foundation
CANONICAL_BASE=main@77bc566f5dfc59ff7fd7e84c9af5836468da8b04
PRODUCTION_MUTATION=NO
DEPLOYMENT=NO
NEXT_TASK_CHANGED=NO
FORMAL_DERIVED_HISTORY_CHANGED=NO
ADJUSTMENT_STATE=UNKNOWN_UNLESS_AUTHORIZED
```

## Current-state audit

The canonical V2 path is already present:

| Concern | Canonical owner | Audit result |
|---|---|---|
| Provider | `market_data.exchange` | Official TWSE/TPEx daily adapters; Yahoo remains verification-only |
| Raw lineage | `raw_market_observations` | Source, adapter, upstream identity, retrieved time, payload hash |
| Replay timeline | `observation_timeline_batches` / `observation_timeline_entries` | Request-keyed batch and stable raw/timeline reuse |
| Canonical OHLCV | `canonical_observations` + PRICE/VOLUME detail tables | Versioned normalization, reference binding, quality state, supersession |
| Read path | `historical_read_model.read_historical_bars` and `vw_daily_market_observations` | Accepted canonical rows only; no legacy-table fallback |
| Identity/lifecycle | active instrument/market registry and effective lifecycle rows | Delisted, terminated, suspended, and not-listed dates remain date-effective |
| Adjustment | canonical read surface | Explicitly `UNKNOWN`; no fabricated adjusted truth |

Committed evidence establishes two separate ranges:

- Local V2 HIST-002B evidence: 507 approved identities and 63,826 accepted
  rows, 2026-02-02 through 2026-08-13.
- Earlier shared 603-universe / approximately two-year bootstrap evidence:
  2024-08-13 through 2026-08-13, 288,881 accepted rows. This remains
  non-Production evidence and is not silently promoted by this task.
- The current Production audit supplied by the owner remains the authority for
  Production status: 2026-08-13 through 2026-09-21, partial and gapped.

The clean development worktree did not have a reachable local PostgreSQL
daemon. Therefore this task does not claim a live row count or silently merge
the non-Production bootstrap into the canonical runtime database.

## Bounded implementation

`topicpilot_api.market_data.coverage_audit` adds a read-only, replayable audit
surface. It reads only:

1. `topicpilot.vw_daily_market_observations`;
2. active instrument/market identity and effective listing dates;
3. active reference lifecycle events; and
4. active reference calendar exceptions.

The audit emits:

- `historical-coverage-by-date.csv` — expected, observed, priced, covered,
  missing, and no-session counts by date;
- `historical-coverage-by-instrument.csv` — identity, date range, priced and
  covered counts, MA20/MA60 readiness, source codes, and primary gap class;
- `gap-classification.csv` — date/instrument-level classifications including
  `MARKET_NO_SESSION`, `INSTRUMENT_NOT_LISTED`, effective lifecycle classes,
  `NO_CANONICAL_OBSERVATION`, and observed-but-unpriced rows.

Known lifecycle and market-calendar exclusions are not counted as unexplained
missing data. Active-session gaps remain visible. Null prices remain null, no
weekend/holiday is forward-filled, and no provider is called by the audit.

Operator entry point:

```text
topicpilot-historical-coverage-audit \
  --database-url <non-Production-read-only-URL> \
  --from 2024-08-13 \
  --to 2026-09-21 \
  --output-dir docs/reports/TASK-A2-HISTORICAL-DATA-FOUNDATION-CANONICALIZATION-001
```

The database transaction is explicitly `READ ONLY` and is rolled back at
exit. The command does not run migrations, ingest providers, or alter formal
derived tables.

## Validation artifacts

The three CSV files in this directory contain the committed output schema but
no fabricated snapshot rows. They are intentionally empty until the operator
runs the command against an approved non-Production canonical database. This
is an explicit limitation, not a zero-coverage claim. The command is the
canonical producer of populated artifacts.

## Validation performed

```text
PYTHON=3.12.14
FOCUSED_TESTS=13 passed, 1 warning
RUFF=PASS
COMPILE=PASS
POSTGRES_INTEGRATION=NOT_RUN (no local PostgreSQL daemon; no Production access attempted)
PRODUCTION_MUTATION=NO
DEPLOYMENT=NO
```

## Remaining limitations and next action

- The canonical development database still needs an operator-approved,
  non-Production audit run and, separately, a source-authorized historical
  reconciliation/import run. The audit tool itself is not a data promotion.
- The official source path and idempotent append/replay path exist, but no
  historical rows are promoted by this task because the current runtime and
  identity/source snapshot could not be safely revalidated here.
- Corporate-action/adjustment continuity remains unknown and must be resolved
  by a separately authorized authority task.
- Research reconstruction remains evidence-only and is not formal history.

`CURRENT_EARLIEST_BLOCKER=APPROVED_NONPRODUCTION_CANONICAL_DATABASE_READBACK_AND_SOURCE_ARTIFACT_RECONCILIATION`

`RECOMMENDED_NEXT_ACTION=RUN_THE_READ_ONLY_COVERAGE_AUDIT_ON_THE_APPROVED_NONPRODUCTION_CANONICAL_DATABASE_THEN_REVIEW_GAPS_BEFORE_ANY_SEPARATE_DATA_PROMOTION`
