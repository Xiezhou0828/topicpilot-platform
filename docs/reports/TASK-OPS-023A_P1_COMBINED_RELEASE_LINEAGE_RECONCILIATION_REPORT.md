# TASK-OPS-023A-P1 | Combined Daily Market + Lifecycle Release Lineage Reconciliation

**Date:** 2026-08-12
**Repository candidate:** `task-data-022`
**Scope:** repository-side integration and release validation only
**Production writes/deployments:** none
**Result:** combined repository release candidate PASS; production activation remains operator-gated

## Executive Summary

TASK-DATA-022/022A (formal daily market close and no-trade coverage) and
TASK-BE-021/021A (Topic Lifecycle engine, shadow calibration, persistence, API,
and frontend contract) were audited and integrated into one working-tree
candidate. The only release-blocking repository defect was a duplicate Alembic
revision identifier: both branches had claimed `0025` from `0024`. The reviewed
resolution preserves the DATA line at 0025/0026 and renumbers the additive
Lifecycle-results migration to 0027 with `down_revision=0026`.

The candidate now has one Alembic head, passes offline fresh-schema SQL
generation, passes the combined backend targeted suite (`53 passed, 1 skipped`),
and passes the focused frontend Lifecycle contract test (`2 passed`) plus the
frontend production build. No Neon connection, migration, canary, topic
snapshot write, Lifecycle shadow evaluation, Render scheduler, or deployment was
performed.

## Starting State

The DATA worktree contained the uncommitted DATA-022/022A implementation,
daily-market projection, no-trade view, post-close reconciliation, and reports.
The parallel Lifecycle worktree contained the frozen Lifecycle specification,
engine/state machine, calibration helpers, additive results ORM/migration,
snapshot/API/frontend integration, and BE-021/BE-021A reports. Both worktrees
were based on the same parent commit (`57dcd49151ef540acb76f06cdb8ce3663cc03e71`)
and neither was clean or deployed.

## Git/Worktree Audit

| Item | Finding |
|---|---|
| Combined target | `work/TopicPilot-task-data-022`, branch `task-data-022` |
| Lifecycle source | `work/TopicPilot-v2-task-be-021`, audited read-only before integration |
| Existing user changes | Preserved; no reset, checkout, or destructive cleanup |
| Production authority | Not available; no protected database or Render control-plane credentials |
| Identity scope | 2 markets / 507 instruments / 130 topics / 107 hierarchy / 848 relations unchanged |
| Historical V1 paths | Retained as historical/private inputs; not made canonical |

## Implementation Inventory

### Daily market and no-trade

- Official TPE/TWO adapters remain the canonical daily source according to the
  existing provider registry.
- `daily_market.py` defines coverage, date, duplicate, and downstream-ready
  gates without hard-coding identity rows.
- `post_close.py` records run/attempt audit, performs bounded retry and
  reconciliation, and blocks snapshots on partial, failed, or closed runs.
- Migrations 0025 and 0026 provide the daily projection and status-aware
  no-trade contract additively.

### Lifecycle

- `topic_lifecycle_engine.py` implements the frozen state machine and
  explainable evidence output; no algorithm or threshold redesign was made.
- `topic_lifecycle_calibration.py` and CLI support deterministic replay and
  calibration diagnostics; historical replay remains data-gated.
- `topic_lifecycle_results` is an additive shadow-results table with stable
  topic/date identity and immutable retry semantics.
- Snapshot execution invokes Lifecycle in shadow mode only after a successful
  market snapshot path; a Lifecycle error rolls back only the shadow evaluation
  and is audited as `SHADOW_EVALUATION_FAILED`.

## Migration Collision Analysis

Before reconciliation, the graphs were:

```text
DATA:      0024 -> 0025_task_data_022_daily_market_contract
                    -> 0026_task_data_022a_no_trade_coverage
LIFECYCLE: 0024 -> 0025_task_be_021_topic_lifecycle_results
```

Both `0025` revisions were distinct Alembic IDs with the same parent. Applying
either branch alone would omit the other branch's objects, and blindly applying
both would leave an ambiguous release history.

## Chosen Reconciliation Strategy

**Option A: preserve the DATA sequence and renumber the additive Lifecycle
revision.** The Lifecycle file is now
`0027_task_be_021_topic_lifecycle_results.py` with
`down_revision = "0026_task_data_022a_no_trade_coverage"`.

This is preferred because it preserves the already documented DATA-022/022A
history, introduces no merge migration or destructive operation, creates one
linear head, and keeps the Lifecycle table additive and independently auditable.

## Combined Migration Graph

```text
0023_task_be_003_provider_orchestrator
  -> 0024_task_be_007_topic_snapshots
  -> 0025_task_data_022_daily_market_contract
  -> 0026_task_data_022a_no_trade_coverage
  -> 0027_task_be_021_topic_lifecycle_results (head)
```

`alembic heads` reports exactly one head. Offline SQL generation reaches 0027,
creates the daily view and `topicpilot.topic_lifecycle_results`, and contains no
`DROP TABLE`, truncate, bootstrap, or identity rewrite.

## Daily Market Integration

The canonical path is official exchange daily data -> raw observations ->
timeline -> canonical observations -> daily projection -> reconciliation. Yahoo
remains verification-only and Taishin remains intraday-only. Stable identity is
`market_code:instrument_code:trade_date`; same-date retries reuse the same
business key and preserve lineage.

## No-Trade Integration

Trading-status and no-trade evidence is explicit. Approved covered-but-unpriced
rows remain null OHLCV; unknown missing, wrong-date, duplicate, and partial
provider cases remain blocking. No zero-fill, forward-fill, or synthetic bar is
introduced.

## Topic Snapshot Integration

The post-close worker only refreshes topic snapshots after a READY reconciliation
with full formal coverage, matching trade date, and zero duplicate/date errors.
Closed/partial/failed runs retain audit state and do not hand downstream data to
Lifecycle.

## Lifecycle Integration

Lifecycle consumes accepted canonical daily observations and formal topic
membership through an explicit handoff. The engine returns stage, direction,
confidence, evidence groups, persistence, reason, and version metadata. The API
and frontend render only backend-owned shadow data; when no shadow result exists,
the formal topic view remains explicitly pending rather than deriving a stage in
the browser.

## Lifecycle Calibration Integration

Calibration and replay code is repository-complete and deterministic against
fixtures. Historical replay is `BLOCKED_BY_DATA` because the production read
model currently has no accepted daily observation/snapshot history. No thresholds,
state semantics, or Lifecycle algorithm were changed by this reconciliation.

## API Integration

Lifecycle fields are nullable/backend-owned in the V2 topic summary/detail
contracts. Read-model joins are migration-safe: absent table/data returns an
explicit unavailable/pending state rather than fabricated Lifecycle output.

## Frontend Contract

`TopicListPage`, `TopicDetailPage`, generated API types, and topic API adapters
were integrated. Formal topics show Lifecycle only when `SHADOW_AVAILABLE`; the
pending state is explicit and no client-side score/stage derivation was added.
Focused frontend Lifecycle integration tests pass, and the production build
completes. The full historical frontend source-shape suite still contains
pre-existing failures unrelated to this integration.

## Fresh DB Migration Validation

Offline Alembic generation from base through 0027 passed. The generated sequence
includes the 0025 daily view, 0026 no-trade projection replacement, and additive
0027 Lifecycle-results table, ending at the single 0027 head.

## Existing DB Upgrade Validation

Not run. No `DATABASE_URL`, `MIGRATION_DATABASE_URL`, or test PostgreSQL URL was
available in this environment. The repository test that requires PostgreSQL is
therefore skipped, not treated as a production pass.

## Migration Safety

- one linear head after reconciliation;
- all new schema work is additive or view replacement already owned by DATA-022A;
- no identity/bootstrap changes;
- no destructive migration, truncate, or delete;
- stable daily key and lifecycle topic/date identity support safe retry;
- historical 0025 Lifecycle file was not applied as a second head.

## Tests

| Validation | Result |
|---|---|
| Combined backend targeted suite | **53 passed, 1 skipped** |
| Focused frontend Lifecycle integration | **2 passed** |
| Frontend production build | **PASS** |
| Alembic heads/history | **PASS; one 0027 head** |
| Alembic offline SQL through 0027 | **PASS** |
| Targeted Ruff for changed DATA/Lifecycle files | **PASS** |
| Broad Ruff over the legacy API tree | **Existing baseline findings** (251 findings, mostly pre-existing formatting/style issues) |
| Production DB upgrade/canary | **NOT RUN** by explicit scope |

## Files Integrated

Lifecycle files integrated from the parallel worktree include the engine,
calibration/CLI modules, Lifecycle ORM, migration 0027, Lifecycle tests, product
specification, BE-021/BE-021A reports, and frontend integration test. Tracked
integration points include topic API/types/pages, snapshot engine, read model,
schemas, ORM registry, post-close shadow invocation, and architecture freeze
tests.

## Files Changed

The candidate changes span:

- `services/api/src/topicpilot_api/daily_market.py`, `live/post_close.py`,
  market-data adapters/normalizers, snapshot/read-model/schema modules;
- `services/api/src/topicpilot_api/topic_lifecycle_*.py` and
  `orm/lifecycle.py`;
- Alembic 0025, 0026, and 0027;
- DATA-022/022A and Lifecycle tests;
- V2 frontend topic pages, API types/adapters, and Lifecycle integration test.

## Documents Updated

- `docs/WORK_ORDERS.md` (added TASK-OPS-023A-P1 PASS row);
- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`;
- `docs/operations/deployment.md`;
- `docs/reports/TASK-OPS-023_V2_DAILY_CLOSE_PRODUCTION_ACTIVATION_REPORT.md`;
- this combined reconciliation report.

Historical DATA and BE reports remain preserved. No authoritative `NEXT_TASK`
file or decision record was changed.

## Production Actions NOT Performed

No Neon migration or write, 507-instrument canary, topic snapshot write,
Lifecycle shadow evaluation, Render Cron provisioning, scheduler activation,
secret creation/rotation, Sites deployment, identity bootstrap, or destructive
operation was performed.

## Remaining Production Blockers

1. Protected Neon read/migration access and confirmation of the current database
   revision.
2. A reviewed production migration window for the combined 0025/0026/0027 line.
3. Formal 507-instrument TPE/TWO canary with reconciliation and approved no-trade
   evidence.
4. One scheduler owner, secret wiring, and reviewed Taiwan holiday authority.
5. At least one READY daily run and topic snapshot before Lifecycle shadow
   activation; historical replay remains data-gated.

## Combined Release Manifest

```text
TASK-DATA-022       = REPOSITORY_READY
TASK-DATA-022A      = REPOSITORY_READY
TASK-BE-021         = ENGINE/API/FRONTEND PASS; production data-gated
TASK-BE-021A        = CALIBRATION PASS; historical replay BLOCKED_BY_DATA
TASK-OPS-023A-P1    = PASS (repository-only combined candidate)
ALEMBIC_HEAD        = 0027_task_be_021_topic_lifecycle_results
PRODUCTION_ACTIVATION = WAITING/BLOCKED (operator credentials and evidence)
```

## Phase 2 Operator Handoff

The next operator task is to verify the production Alembic revision, apply the
reviewed combined lineage in a protected release window, run the 507-instrument
manual canary, capture READY reconciliation, and only then enable the approved
14:40 scheduler and Lifecycle shadow handoff. The operator must not apply either
historical 0025 branch independently.

## Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Existing V1/V2 ownership audited | PASS | DATA-022 and architecture audit |
| Canonical source decision preserved | PASS | official TPE/TWO registry; Yahoo verification-only; Taishin intraday-only |
| Daily observation contract | PASS | stable key, canonical projection, reconciliation gate |
| No-trade contract | PASS | explicit status/null semantics and tests |
| Lifecycle handoff contract | PASS | READY-gated canonical observations; no algorithm change |
| Migration collision resolved | PASS | 0027 renumbering; one Alembic head |
| Fresh-schema offline migration | PASS | SQL generated through 0027 |
| Existing DB upgrade | NOT RUN | protected URL absent |
| Combined backend tests | PASS | 53 passed, 1 skipped |
| Frontend Lifecycle contract/build | PASS | 2 focused tests; build complete |
| Broad frontend historical suite | NOT CLEAN | pre-existing source-shape failures remain |
| Production write/deploy/scheduler | NOT RUN | explicitly prohibited in this task |

## Known Issues and Risks

- Production data readiness remains unproven until a real full-universe run.
- No PostgreSQL integration test could run without an explicit test URL.
- Broad Ruff reports legacy style findings outside the focused changed-file set.
- Existing public API/status inconsistencies documented by OPS-023 remain
  unresolved and are not silently reclassified as fixed.
- Lifecycle historical replay cannot be calibrated against production until
  accepted daily observations and snapshots exist.

## Suggested NEXT_TASK

`TASK-OPS-023A-P2 | Protected Production Migration, 507-Instrument Canary,
Scheduler and Lifecycle Shadow Handoff`

This is a report-only suggestion. The repository's authoritative NEXT_TASK was
not modified by TASK-OPS-023A-P1.
