# TASK-DATA-REF-009｜Post-Close Canary Persistence & End-to-End Data Publication Validation

## Scope and preserved authority

This task follows the already completed and preserved G0–G3 checkpoints. It
does not redesign reference data, the registry transition, lifecycle evidence,
G2 coverage semantics, G3 market semantics, provider authority, or the 6806
identity contract.

```text
APPLICATION_RUNTIME_AUTHORITY_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
G0_CHECKPOINT = PASS / PRESERVED
G1_CHECKPOINT = PASS / PRESERVED
G2_CHECKPOINT = PASS / PRESERVED
G3_CHECKPOINT = PASS / PRESERVED
G3_RUN_DATE = 2026-08-13
G3_TPE_COVERAGE = 313/313
G3_TWO_COVERAGE = 193/193
G3_FALLBACK_USED = false
G3_PRODUCTION_WRITE_SET = []
AUTHORIZED_RUN_DATE = 2026-08-13
DATE_SUBSTITUTED = NO
```

## Existing Canary authority audit

The existing production entrypoint is the repository-owned `topicpilot-live`
console script:

```text
CANARY_ENTRYPOINT = topicpilot-live --mode post-close --once --run-date 2026-08-13
CANARY_MODE = POST_CLOSE
CANARY_RUN_DATE_ARGUMENT = --run-date 2026-08-13
CANARY_PROVIDER_PATH = PostCloseUpdater -> build_historical_provider_registry(market_batch=True)
CANARY_PROVIDER_SOURCE = TWSE_OFFICIAL_DAILY / twse-official-daily.v2; TPEX_OFFICIAL_DAILY / tpex-official-daily.v2
CANARY_DOWNSTREAM_RESOURCE = topicpilot.canonical_* -> topicpilot.topic_snapshots -> /api/v2/stocks, /api/v2/topics, /api/v2/topic-snapshots
```

Before this task's fix, the post-close path selected all 507 physical active
EQUITY identities and `reconcile_daily_market()` counted the same physical
universe. The CLI also refreshed the generic active tracking universe before
the post-close reference precondition. That would have admitted TPE:6806 on
2026-08-13, contrary to the preserved date-effective contract.

The implementation now obtains the date-effective expected universe through
the existing `load_g2_preflight_context()` SELECT-only loader before creating a
post-close run. It requires the active reference context and both canonical
markets, validates the exact database identity set, and passes the same eligible
instrument IDs to reconciliation, tracking refresh, topic snapshots, and
shadow topic lifecycle evaluation. The CLI defers generic tracking refresh for
POST_CLOSE until after this precondition and the bounded write path.

```text
DATE_EFFECTIVE_EXPECTED_UNIVERSE = TPE 313 + TWO 193 = 506
PHYSICAL_INSTRUMENT_ROWS = 507
TPE:6806_PHYSICAL_ROW_PRESERVED = YES
TPE:6806_2026-08-13_ELIGIBLE = NO
```

## Bounded write contract

The authorized one-shot canary may write only the post-close data-publication
path and its operational audit rows:

```text
PLANNED_PRODUCTION_WRITE_SET =
[
  market_data_sources,
  live_collector_runs,
  live_collector_attempts,
  observation_timeline_batches,
  raw_market_observations,
  observation_timeline_entries,
  observation_timeline_quality_events,
  canonical_observations,
  canonical_price_observations,
  canonical_volume_observations,
  canonical_quote_observations,
  canonical_trading_status_observations,
  live_tracking_universe,
  topic_snapshots,
  topic_lifecycle_results (SHADOW only)
]
```

The following are outside the canary write set and must remain unchanged:

```text
REFERENCE_REGISTRY_MUTATION = FORBIDDEN
INSTRUMENT_IDENTITY_MUTATION = FORBIDDEN
MARKET_IDENTITY_MUTATION = FORBIDDEN
REFERENCE_INSTRUMENT_LIFECYCLE_MUTATION = FORBIDDEN
SCHEMA_OR_MIGRATION_MUTATION = FORBIDDEN
UNRELATED_HISTORICAL_BACKFILL = FORBIDDEN
MULTI_DAY_BACKFILL = FORBIDDEN
SCHEDULER_ENABLEMENT = FORBIDDEN
```

The writer is transactionally bounded per instrument ingestion unit. The
historical ingestion function itself never commits; the caller commits each
successful instrument unit and rolls back a failed unit. Run/attempt metadata,
tracking refresh, topic snapshot, and shadow lifecycle persistence have their
own commits. Therefore this is not an all-instrument atomic transaction:

```text
CANARY_TRANSACTIONAL = SEGMENTED_CALLER_OWNED_TRANSACTIONS
CANARY_ROLLBACK_BEHAVIOR = FAILED_UNIT_ROLLBACK; PRIOR_COMMITTED_UNITS_REMAIN
CANARY_IDEMPOTENT = YES
DOWNSTREAM_PUBLICATION_ON_PARTIAL = BLOCKED
```

Idempotence is supplied by the existing historical request key/content hash
and canonical idempotency keys, same-date topic snapshot key, and immutable
same-date shadow lifecycle result contract. A partial or failed reconciliation
does not run the topic snapshot publication path.

## Backend publication audit

The formal V2 resources consume the persisted V2 path:

```text
FORMAL_STOCK_DATA = /api/v2/stocks and /api/v2/stocks/{symbol}
FORMAL_TOPIC_DATA = /api/v2/topics and /api/v2/topic-snapshots
HOME_ROUTE = /api/v2/home
```

`/api/v2/stocks`, `/api/v2/topics`, and `/api/v2/topic-snapshots` read the
`topicpilot` V2 identity, canonical observation, tracking, and topic snapshot
tables. `/api/v2/home` still composes the legacy public read model and remains
PARTIAL; a successful canary can therefore establish formal data persistence
and formal stock/topic resources without claiming complete Home publication or
frontend wiring.

```text
FORMAL_DATA_PERSISTED_BUT_NOT_PUBLISHED = HOME read model remains separate
HOME_FORMAL_DATA_AVAILABLE = NO (pre-existing publication boundary)
STOCK_FORMAL_DATA_AVAILABLE = YES after successful canary postcheck
TOPIC_FORMAL_DATA_AVAILABLE = YES after successful snapshot postcheck
FRONTEND_WIRING_REQUIRED = YES
```

No OpenAPI contract or migration is required for this canary-path fix.

## Operator execution gate

After exact-SHA release verification, the operator may execute exactly one
bounded Production canary in the authenticated Render Shell:

```text
topicpilot-live --mode post-close --once --run-date 2026-08-13
```

The operator must capture the machine-readable completion result and then
perform read-only postchecks for:

```text
POST_CLOSE status = SUCCESS
requestedCount = 506
successCount = 506
failureCount = 0
reconciliation.status = READY
reconciliation.tradeDate = 2026-08-13
reconciliation.marketCounts.TPE.expected = 313
reconciliation.marketCounts.TPE.covered = 313
reconciliation.marketCounts.TWO.expected = 193
reconciliation.marketCounts.TWO.covered = 193
reconciliation.downstreamReady = true
topicSnapshot.snapshotDate = 2026-08-13
topicSnapshot.status = SUCCESS
```

The operator must also verify no reference/instrument/market identity or
reference lifecycle row changed, the physical 6806 row remains present with
no 2026-08-13 observation, no duplicate daily stable keys exist, and the
formal V2 stock/topic resources expose the new date. A second invocation is
allowed only if the first result is safe to retry; it must be an equivalent
repository-defined NOOP and must not duplicate daily observations.

Do not enable Scheduler, run Canary again without evidence review, run G2/G3
again, execute `topicpilot-live` for another date, or begin frontend wiring in
this task.

## Implementation validation before release

```text
MIGRATION_CHANGED = NO
OPENAPI_CHANGED = NO
PRODUCTION_MUTATION = NO
CANARY_EXECUTED = NO
CANARY_ATTEMPTS = 0
SCHEDULER_CHANGED = NO
```

Focused post-close, daily reconciliation, lifecycle, G3, and live-runtime
tests pass. The backend suite excluding research/governance boundaries passes;
PostgreSQL-dependent tests are skipped locally when no test database URL is
configured. A disposable PostgreSQL test covers the 313/193 date-effective
universe, 6806 exclusion, and reconciliation expected count of 506.

## Fixed report fields — release pending operator evidence

```text
TASK_DATA_REF_009 = IMPLEMENTED_PENDING_RELEASE
IMPLEMENTATION_SHA = PENDING_COMMIT
APPLICATION_RUNTIME_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
RUNTIME_GIT_COMMIT = b9c881af0fa34d29e9ac0ccdf123351741e7f62d (preserved)
PROVIDER_LINEAGE_BUILD_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d (preserved)
RUNTIME_SHA_VERIFIED = PRESERVED

CANARY = NOT_RUN
CANARY_ATTEMPTS = 0
PRE_CANARY_ROWS = NOT_CAPTURED
POST_CANARY_ROWS = NOT_CAPTURED
PROVIDER_LINEAGE_PRESERVED = YES
DUPLICATE_PERSISTENCE = NOT_CHECKED
REFERENCE_STATE_CHANGED = NO
INSTRUMENT_STATE_CHANGED = NO
LIFECYCLE_STATE_CHANGED = NO (reference lifecycle)

FORMAL_DATA_PERSISTED = NOT_CHECKED
HOME_FORMAL_DATA_AVAILABLE = NO / PRE-EXISTING GAP
STOCK_FORMAL_DATA_AVAILABLE = NOT_CHECKED
TOPIC_FORMAL_DATA_AVAILABLE = NOT_CHECKED
PUBLICATION_STATE = NOT_CHECKED
FRONTEND_WIRING_REQUIRED = YES

PRODUCTION_MUTATION = NO
PRODUCTION_WRITE_SET = []
SCHEDULER_CHANGED = NO
AI_WORKLOG_UPDATED = PENDING
REPORT_CREATED = YES
FINAL_STATUS = READY_FOR_EXACT_SHA_CI_AND_PRODUCTION_CANARY_REVIEW
BLOCKER = Awaiting exact-SHA release and one-shot operator Canary evidence.
```
