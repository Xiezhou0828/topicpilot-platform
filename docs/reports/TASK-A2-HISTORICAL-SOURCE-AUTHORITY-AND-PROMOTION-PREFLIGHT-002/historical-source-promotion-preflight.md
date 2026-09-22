# TASK-A2-HISTORICAL-SOURCE-AUTHORITY-AND-PROMOTION-PREFLIGHT-002

## Scope and stop boundary

This is a governed, read-only A2 authority reconciliation and promotion
preflight. It does not write Production, run migrations, create a historical
business table, refetch providers, or publish/backfill formal Topic, Score,
Grade, Lifecycle, or Opportunity history. The incomplete 2026-09-22 session
is outside the evaluated window.

The current GitHub-backed canonical `main` was refreshed before this preflight:

```text
ORIGIN_MAIN=3e513d90d61fc26679a6406bbe84f62d237c1e86
REPOSITORY=https://github.com/Xiezhou0828/topicpilot-platform
SOURCE_READBACK=BLOCKED_LOCAL_DOCKER_POSTGRES_UNAVAILABLE
PRODUCTION_WRITE=NO
DEPLOYMENT=NO
NEW_HISTORICAL_BUSINESS_TABLES=0
```

The source authority manifests and prior post-promotion readback are committed
evidence. They identify a canonical non-Production database target, but the
database itself is not reachable in this environment. Therefore this report
does not claim a fresh live overlap dry-run.

GitHub Actions evidence for the refreshed canonical head is also recorded:

```text
CI_RUN=97
CI_HEAD_SHA=3e513d90d61fc26679a6406bbe84f62d237c1e86
CI_CONCLUSION=FAILURE
CI_BACKEND_MIGRATION_OPENAPI=FAILURE
CI_FRONTEND=SUCCESS
CI_SECRET_SCAN=SUCCESS
CI_DOCKER_COMPOSE_SMOKE=SKIPPED
```

This is the preflight baseline from GitHub, not a claim that this documentation
change caused the existing backend failure.

## 1. Source authority finding

The primary backfill candidate is uniquely identified by the committed Shared
Data Foundation authority handoff:

```text
BOOTSTRAP_SOURCE_CLASS=COMMITTED_AUTHORITY_MANIFEST_BACKED_CANONICAL_NONPRODUCTION_DB
BOOTSTRAP_DATABASE_OR_ARTIFACT=topicpilot / topicpilot schema / local Docker Compose PostgreSQL; 17 hashed source artifacts committed under the 2026-08-19 bootstrap report
BOOTSTRAP_PROVIDER_TPE=TWSE_OFFICIAL_DAILY; adapter versions twse-official-daily.v1 and twse-official-daily.v2
BOOTSTRAP_PROVIDER_TWO=TPEX_OFFICIAL_DAILY; adapter versions tpex-official-daily.v1 and tpex-official-daily.v2
BOOTSTRAP_REFERENCE_VERSION=sdf-reference-603-v1
BOOTSTRAP_AUTHORITY_VERSION=sdf-603-ohlcv-2y.v1
BOOTSTRAP_IDENTITY_VERSION=sdf-reference-603-v1 / identity key market:instrument_code
BOOTSTRAP_SOURCE_RUN_ID=TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-BOOTSTRAP-EXECUTION-20260819-RUN-001
BOOTSTRAP_SOURCE_FINAL_CANONICAL_HEAD=c40aa42e7cac665386009f29c94a8dafce896427
BOOTSTRAP_ROW_COUNT=288881
BOOTSTRAP_INSTRUMENT_COUNT=603
BOOTSTRAP_START_DATE=2024-08-13
BOOTSTRAP_END_DATE=2026-08-13
BOOTSTRAP_NORMALIZED_SURFACE_SHA256=e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4
BOOTSTRAP_SOURCE_AVAILABLE=COMMITTED_MANIFEST_AND_POSTPROMOTION_READBACK_AVAILABLE; LIVE_DB_READBACK_BLOCKED
```

The source reports state that accepted rows have complete provider request
lineage, zero invalid OHLCV rows, zero duplicate stable sessions after
supersession filtering, no synthetic fill, and `adjustment_state=UNKNOWN`.
Those are source-evidence findings, not a new runtime query in this task.

## 2. Identity reconciliation

Committed identity evidence is positive at the aggregate level:

```text
IDENTITY_RECONCILIATION_STATUS=PASS_BY_COMMITTED_AUTHORITY_MANIFEST; LIVE_READBACK_BLOCKED
BOOTSTRAP_INSTRUMENTS=603
MATCHED_CANONICAL_IDENTITIES=603
IDENTITY_MISMATCHES=0
UNMAPPED_INSTRUMENTS=0
AMBIGUOUS_IDENTITIES=0
LIFECYCLE_CONFLICTS=0_REPORTED; LIVE_EFFECTIVE_DATE_RECHECK_BLOCKED
NEW_IDENTITY_CANDIDATES=96
NEW_IDENTITY_SECURITY_AUTHORITY_PASS=96
NEW_IDENTITY_LISTING_AUTHORITY_PASS=96
```

The 603-universe evidence uses official TPE/TWO identity authority and keeps
topic membership, Structural Role, and Score Projection decoupled. No mismatch
artifact is generated because the committed reconciliation reports no
mismatches. The 144 quarantine work items, 142 provider `NO_DATA` work items,
41 lifecycle skips, and 13 provider/unresolved-gap instruments remain explicit
limitations rather than identity substitutions.

## 3. Overlap reconciliation

The required cell-level comparisons cannot be executed without the source and
canonical database rows. The committed manifests provide aggregate counts and
normalized hashes, but not a row-level OHLCV payload that can be independently
joined in this worktree.

```text
OVERLAP_RECONCILIATION_STATUS=SOURCE_READBACK_BLOCKED
BOOTSTRAP_VS_CANONICAL_DEV=MISSING_LIVE_ROWS; NOT_MEASURED
BOOTSTRAP_VS_PRODUCTION=MISSING_LIVE_ROWS; NOT_MEASURED
MATCH=NOT_MEASURED
MATCH_WITH_METADATA_DIFFERENCE=NOT_MEASURED
VALUE_CONFLICT=NOT_MEASURED
MISSING_IN_BOOTSTRAP=NOT_MEASURED
MISSING_IN_CANONICAL=NOT_MEASURED
IDENTITY_CONFLICT=0_BY_COMMITTED_MANIFEST; NOT_LIVE_RECHECKED
CONFLICT_COUNT=NOT_MEASURED
```

No `overlap-conflicts.csv` is emitted because no conflicts were observed or
measured. `NOT_MEASURED` is intentionally not converted to zero or PASS.

## 4. Existing conflict and correction semantics

The existing canonical architecture is the only target: raw observations,
timeline entries, canonical PRICE/VOLUME observations, and the
`vw_daily_market_observations` read projection. Existing accepted successors
supersede prior accepted observations; the historical read path excludes
superseded rows and does not call a provider.

The safe promotion policy remains:

1. Exact existing canonical cell and matching lineage: no-op.
2. Missing canonical cell with validated identity, source, quality, and
   lineage: append through the existing raw → timeline → canonical chain.
3. Any value, identity, lineage, lifecycle, or correction conflict: quarantine
   and reconcile; never overwrite.

```text
CONFLICT_RESOLUTION_SUPPORTED=YES_BY_EXISTING_CANONICAL_SEMANTICS; NOT_EXECUTED
AUTO_RESOLVABLE_CONFLICTS=0_EXECUTED
MANUAL_RECONCILIATION_REQUIRED=UNKNOWN_UNTIL_LIVE_OVERLAP
UNRESOLVED_CONFLICTS=UNKNOWN_UNTIL_LIVE_OVERLAP
CORRECTION_SUPERSESSION=SUPPORTED_BY_CANONICAL_SUPERSEDES_CHAIN; NOT_REWRITTEN
```

## 5. Corporate-action and adjustment audit

The authority artifacts consistently state `adjustment_state=UNKNOWN` for the
accepted raw PRICE observations. No split, capital-reduction, cash-reduction,
ex-right/ex-dividend factor, relisting transition, or total-return factor is
fabricated by this preflight.

```text
RAW_OHLCV_PROMOTION_BLOCKED_BY_CORPORATE_ACTION=NO_FOR_RAW_OBSERVATION_AUTHORITY
ADJUSTED_RETURN_CONTINUITY_READY=NO
CORPORATE_ACTION_LIMITATION_COUNT=603_INSTRUMENTS_ADJUSTMENT_UNKNOWN
AFFECTED_INSTRUMENT_COUNT=603
```

Raw OHLCV authority and adjusted-return continuity remain separate. The latter
is blocked until an authoritative corporate-action/adjustment source is
available.

## 6. Promotable scope

The committed authority handoff identifies the following accepted scope. It
was already read back by the prior non-Production handoff task; this task does
not execute a second write or treat that evidence as a fresh live dry-run.

```text
PROMOTABLE_START_DATE=2024-08-13_BY_COMMITTED_AUTHORITY
PROMOTABLE_END_DATE=2026-08-13_BY_COMMITTED_AUTHORITY
PROMOTABLE_INSTRUMENTS=603_BY_COMMITTED_AUTHORITY
PROMOTABLE_ROWS=288881_BY_COMMITTED_AUTHORITY
PROMOTABLE_MARKETS=TPE:370,TWO:233
PROMOTABLE_MATCH_RATE=NOT_MEASURED_IN_THIS_PREFLIGHT
NEW_ROWS_PROMOTED_IN_THIS_TASK=0
```

```text
BLOCKED_ROWS=NOT_MEASURED_SOURCE_READBACK_BLOCKED
BLOCKED_INSTRUMENTS=NOT_MEASURED_SOURCE_READBACK_BLOCKED
BLOCKED_DATES=NOT_MEASURED_SOURCE_READBACK_BLOCKED
BLOCK_REASON_COUNTS=SOURCE_READBACK_UNAVAILABLE_FOR_CURRENT_PREFLIGHT
```

The bounded exceptions are listed in `promotion-exceptions.csv`. They are not
silently reclassified as market holidays, no-trade sessions, identity gaps, or
valid adjusted-return observations.

## 7. Historical-to-daily chain

The intended chain is structurally contiguous because the bootstrap authority
and daily ingestion both target the same V2 canonical observation families and
read projection. Live post-bootstrap continuity is not re-read here:

```text
HISTORICAL_TO_DAILY_CHAIN_CONTIGUOUS=UNVERIFIED_LIVE_READBACK
DAILY_APPEND_CANONICAL_PATH=official TWSE/TPEx daily provider → existing request-keyed ingestion → raw_market_observations → observation_timeline_batches/entries → canonical PRICE/VOLUME chain
DUPLICATE_TRUTH_RISK=CONTROLLED_BY_SINGLE_CANONICAL_CHAIN_AND_SUPERSESSION; LIVE_RUNTIME_NOT_RECHECKED
GAP_BETWEEN_BOOTSTRAP_AND_PRODUCTION=2026-08-13_BOUNDARY_REQUIRES_LIVE_CONTINUITY_READBACK; PRODUCTION_KNOWN_PARTIAL_THROUGH_2026-09-21
```

The 2026-09-22 incomplete session is not part of this continuity claim.

## 8. Read-only dry-run result

```text
DRY_RUN_STATUS=SOURCE_READBACK_BLOCKED
DRY_RUN_SOURCE_ROWS=NOT_RUN
DRY_RUN_ALREADY_PRESENT=NOT_RUN
DRY_RUN_NEW_PROMOTABLE=NOT_RUN
DRY_RUN_CONFLICTS=NOT_RUN
DRY_RUN_BLOCKED=ALL_LIVE_SOURCE_ROWS_UNAVAILABLE_TO_THIS_RUN
DRY_RUN_IDENTITY_FAILURES=0_BY_COMMITTED_MANIFEST; NOT_LIVE_RECHECKED
```

The local Docker API was unavailable, and no Production connection was
attempted. Per the task stop condition, no speculative importer or promotion
adapter was added.

## 9. Minimal promotion plan

If an approved non-Production read-only database becomes available, the next
run should be a dry-run only over `2024-08-13` through `2026-08-13`, anchored to
`sdf-603-ohlcv-2y.v1` and `sdf-reference-603-v1`:

- read the source rows and current canonical rows using the existing V2 view
  and identity/lifecycle authority;
- join on effective canonical identity plus market date and compare all OHLCV
  fields, market, source, status, and lineage;
- exact-match cells become no-ops;
- missing validated cells use the existing raw → timeline → canonical chain;
- conflicts, unknown lifecycle boundaries, missing lineage, and adjustment
  ambiguity are quarantined;
- preserve request/source hashes, retrieved timestamps, reference versions,
  and supersession links;
- commit only after a separate owner-authorized non-Production write decision;
- verify post-write counts, normalized hash, supersession state, and rerun
  idempotency before considering any later environment.

No new historical business table is part of this plan.

## 10. Final preflight disposition

```text
PREFLIGHT_STATUS=RECONCILIATION_REQUIRED
PROMOTION_READY=NO_FOR_NEW_WRITE; EXISTING_COMMITTED_HANDOFF_EVIDENCE_PRESENT
SOURCE_READBACK_BLOCKER=CANONICAL_NONPRODUCTION_LOCAL_DOCKER_POSTGRES_UNAVAILABLE
PRODUCTION_MUTATION=NO
DEPLOYMENT=NO
MIGRATION_ADDED=NO
FORMAL_DERIVED_HISTORY_CHANGED=NO
NEXT_TASK_CHANGED=NO
```

The source authority is sufficiently identified for a bounded owner review,
but this task cannot safely assert row-level overlap, current production
continuity, or a new promotable delta without direct readback.
