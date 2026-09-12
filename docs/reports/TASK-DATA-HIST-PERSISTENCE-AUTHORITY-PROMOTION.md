# TASK-DATA-HIST-PERSISTENCE-AUTHORITY-PROMOTION

## 1. Executive Summary

This task implemented the bounded, local-only promotion bridge from the
HIST-002B legacy evidence table into the V2 canonical observation chain.

The authority decision from the reconciliation task was preserved:

```text
topicpilot.market_data_ohlcv
  = HIST-002B evidence / staging only

topicpilot.canonical_observations
+ canonical_price_observations
+ canonical_volume_observations
+ canonical_trading_status_observations
+ accepted daily projections from revisions 0025/0026
  = sole V1/V2 historical publication authority
```

The canonical schema was materialized through the existing Alembic path,
the approved `tw-reference-v1` reference bundle was activated locally, and
all 63,826 legacy rows were promoted with accepted PRICE dispositions. The
non-null legacy volume field was promoted through the existing historical
normalizer contract as `UNIT`, scale `0`, `DAILY_TOTAL`. No trading-status
rows were invented from the legacy `lifecycle_status='active'` field.

The exact rerun produced zero additional raw, timeline, canonical, PRICE, or
VOLUME rows. Existing V1 history reads and the V2 daily projection view read
the canonical chain. Stock-006A is therefore authorized for a later retry,
but was not restarted by this task.

## 2. Canonical / Git Preflight

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_PRE_SHA=cfb379eec8eb27c9585b6c4249807872d5d5480f
CANONICAL_POST_SHA=d9c7787c862c413541f121e90c661bbd83ed73f5
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO
WORKTREE_STATE=PRE_EXISTING_DIRTY_FILES_PRESERVED
PRE_STATUS_TOTAL=170
PRE_MODIFIED_OR_STAGED=18
PRE_UNTRACKED=152
```

The existing worktrees and unrelated dirty files were not reset, stashed,
cleaned, checked out, or overwritten. The implementation commit staged only
the promotion module, its test, and the API script entry.

Implementation commit:

```text
d9c7787c862c413541f121e90c661bbd83ed73f5
feat: promote HIST-002B into canonical observations
```

## 3. Local DB Preflight

The preflight used the local development PostgreSQL target with a read-only
transaction before any write.

```text
TARGET_DB=LOCAL_DEVELOPMENT_ONLY
LOCAL_DB_NAME=topicpilot
LOCAL_DB_HOST_CLASSIFICATION=LOCAL_DOCKER_POSTGRES_PRIVATE_172.18.0.3
LOCAL_DB_SERVER=172.18.0.3/32:5432
LOCAL_DB_VERSION=PostgreSQL 16.14
LOCAL_DB_USER=topicpilot
LOCAL_DB_TRANSACTION_READ_ONLY=ON_DURING_PREFLIGHT
LOCAL_DB_MIGRATION_PRE_STATE=0017_phase3_4_005_market_data_source_and_raw_observations
REPOSITORY_MIGRATION_HEAD=0029_task_data_ref_006e_instrument_lifecycle
```

The promotion code also requires an explicit `--local-only` guard, a local
database URL host, database name `topicpilot`, and a private/loopback server
address. A non-local target fails closed before connecting.

## 4. Schema Materialization

The repository Alembic path was used without modifying or renaming the
legacy table:

```text
0017 -> 0018 observation timeline
     -> 0019 canonical observation families
     -> 0020 reference registry
     -> 0021 import audit
     -> 0022 live runtime
     -> 0023 provider metadata
     -> 0024 topic snapshots
     -> 0025 accepted daily projection
     -> 0026 no-trade coverage projection
     -> 0027 topic lifecycle results
     -> 0028 reference bootstrap support
     -> 0029 instrument lifecycle evidence
```

Post-materialization state:

```text
LOCAL_DB_MIGRATION_POST_STATE=0029_task_data_ref_006e_instrument_lifecycle
LOCAL_CANONICAL_SCHEMA_READY=YES
LEGACY_TABLE_PRESERVED=YES
PARALLEL_HISTORY_TABLE_CREATED=NO
```

The migration transaction completed successfully. The first promotion
attempt later failed inside its own transaction because of a detail-table
key handling defect in the new bridge; its post-failure counts confirmed full
rollback, with canonical/timeline/batch counts all zero. The defect was fixed
before the successful run.

## 5. Reference Bootstrap / Authority

The committed bundle was validated before activation:

```text
REFERENCE_DATA_VERSION=tw-reference-v1
REFERENCE_BUNDLE_SHA256=daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
REFERENCE_MARKETS=2
REFERENCE_INSTRUMENTS=507
REFERENCE_TPE=314
REFERENCE_TWO=193
REFERENCE_CALENDAR_DATES=24
REFERENCE_LIFECYCLE_EVENTS=1
REFERENCE_CONTEXT_READY=YES
```

The existing reference-only bootstrap path was used. Its dry-run showed only
the approved reference/identity write set and `nonReferenceWriteSet=[]`.
Activation was transactional and resulted in `tw-reference-v1 / ACTIVE`.
No second reference bootstrap was created and no reference values were
invented by the promotion bridge.

## 6. Legacy Evidence Manifest

The reproducibility manifest is a stable hash over the sorted legacy rows,
including the legacy row identity, typed OHLCV values, provider, source URL,
provider lineage, and lifecycle field.

```text
HIST_002B_PHYSICAL_TABLE=topicpilot.market_data_ohlcv
LEGACY_ROWS=63826
LEGACY_SECURITIES=507
DATE_RANGE=2026-02-02..2026-08-13
TWSE_ROWS=39523
TWSE_SECURITIES=314
TPEX_ROWS=24303
TPEX_SECURITIES=193
LEGACY_MANIFEST_SHA256=791ac851d946aa9cc9e597ff06b836cfdbc286232218de044560522ddba766f9
DUPLICATE_EXCESS=0
INVALID_OHLCV=0
MISSING_REQUIRED_LEGACY_LINEAGE=0
```

The legacy table was read only. Its row count, date range, identity set,
typed values, and lineage digest were unchanged by promotion.

## 7. Promotion Bridge Contract

The bridge is implemented in:

`services/api/src/topicpilot_api/market_data/historical_promotion.py`

```text
BRIDGE_CONTRACT_VERSION=hist-002b-legacy-to-v2.v1
BRIDGE_MAPPING_POLICY_VERSION=hist-002b-promotion-mapping.v1
NORMALIZATION_CONTRACT_VERSION=normalization-contract-v1
REFERENCE_DATA_VERSION=tw-reference-v1
BRIDGE_LOCAL_ONLY_GUARD=REQUIRED
```

The bridge is separate from live provider ingestion. It uses deterministic
UUIDs, stable raw/timeline/canonical idempotency keys, explicit batch
metadata, and a single caller-owned transaction. It never updates or
deletes `market_data_ohlcv`.

Existing source registrations were reused exactly as registered in the local
canonical database:

| Legacy evidence | Canonical identity | Existing source registration |
|---|---|---|
| `TWSE` / `TWSE` | `TPE` | `TWSE_OFFICIAL_DAILY / twse-official-daily.v1` |
| `TPEX` / `TPEx` | `TWO` | `TPEX_OFFICIAL_DAILY / tpex-official-daily.v1` |

The bridge did not relabel the legacy `topicpilot.official_ohlcv.v1` marker as
a current v2 adapter. The original marker remains in the promoted raw
evidence payload, while the canonical source registration remains the exact
existing v1 registration in the local DB.

## 8. Identity Mapping

```text
EXPECTED_SECURITIES=507
MAPPED_SECURITIES=507
UNKNOWN_IDENTITIES=0
AMBIGUOUS_IDENTITIES=0
TEST_IDENTITIES=0
OUTSIDE_UNIVERSE_IDENTITIES=0
```

Every legacy `(market, security_code)` resolved to exactly one active
canonical instrument. Physical `TWSE` maps to canonical `TPE`; physical
`TPEX` maps to canonical `TWO`. The `TEST` identity was not included.

## 9. Source / Lineage Mapping

Every promoted raw payload preserves:

```text
provider
source_url
response_sha256
request_params
retrieved_at
source_kind
legacy normalizer marker
legacy row identity
legacy manifest hash
bridge contract version
bridge mapping policy version
```

The canonical foreign-key chain is:

```text
canonical observation
  -> timeline entry
  -> raw market observation
  -> legacy evidence row identity + source artifact lineage
```

The original provider payload was not present in the legacy table and was not
fabricated:

```text
RAW_PROVIDER_PAYLOAD_AVAILABLE=NO
SOURCE_ARTIFACT_LINEAGE_PRESERVED=YES
MISSING_CANONICAL_LINEAGE=0
```

## 10. Timestamp Semantics

```text
trading_date -> observed_at = explicit market-date midnight in Asia/Taipei
provider_lineage.retrieved_at -> canonical/raw retrieved_at
legacy created_at -> canonical received_at as bridge receipt only
```

`created_at` was not represented as the original source receipt time. The
report and every batch payload identify the policy as
`LEGACY_CREATED_AT_AS_BRIDGE_RECEIPT_ONLY`. No source receipt timestamp was
invented.

## 11. PRICE Mapping

The existing `HistoricalDailyBarNormalizer` mapped legacy `open`, `high`,
`low`, and `close` into the canonical PRICE family. All 63,826 rows passed
OHLC validation and were `ACCEPTED`.

```text
ADJUSTMENT_STATE=UNKNOWN
FORWARD_FILL=NO
SYNTHETIC_BARS=NO
NULL_TO_ZERO=NO
CORPORATE_ACTION_ADJUSTMENT=NO
TOTAL_RETURN_CALCULATION=NO
```

## 12. VOLUME Mapping

The existing historical normalizer contract was used without a browser or
frontend transformation:

```text
volume_quantity = legacy volume
volume_unit_code=UNIT
volume_scale=0
aggregation_code=DAILY_TOTAL
```

All 24,303 TPEX volume observations and all TWSE volume observations used the
same explicit canonical volume contract. Missing volume would have remained
absent; this dataset had no missing volume. No null-to-zero, carry-forward,
lot-scale guess, turnover derivation, or volume analytics was performed.

## 13. Trading Status Boundary

The legacy `lifecycle_status='active'` field was not promoted to a canonical
TRADING_STATUS observation. The promotion wrote no status rows:

```text
CANONICAL_STATUS_ROWS_CREATED=0
TRADING_STATUS_EVIDENCE=ABSENT_UNAVAILABLE
LEGACY_ACTIVE_TO_STATUS_INFERENCE=NO
```

Lifecycle interpretation came from the activated date-effective reference
authority, not from the legacy lifecycle field.

## 14. Lifecycle / 6806 / 3059 Controls

```text
6806_FIRST_BAR=2026-02-02
6806_LAST_BAR=2026-06-22
6806_TERMINATION_BOUNDARY=2026-06-23
6806_POST_TERMINATION_ROWS=0
6806_CONTROL=PASS

3059_ROWS=0
3059_CONTROL=PASS
```

The 6806 canonical publication also ended on 2026-06-22. No bar was
published on or after its 2026-06-23 lifecycle boundary.

## 15. Promotion Result

The successful first run wrote only the following promotion-domain objects:

```text
observation_timeline_batches=2
raw_market_observations=63826
observation_timeline_entries=63826
canonical_observations=127652
canonical_price_observations=63826
canonical_volume_observations=63826
canonical_trading_status_observations=0
```

The first run result was:

```text
RAW_CREATED=63826
TIMELINE_CREATED=63826
CANONICAL_PRICE_CREATED=63826
CANONICAL_VOLUME_CREATED=63826
REJECTED_ROWS=0
QUARANTINED_ROWS=0
```

No provider was called, no HIST-002B seed was rerun, and no legacy row was
rewritten.

## 16. Row Reconciliation

```text
LEGACY_ROWS=63826
LEGACY_SECURITIES=507
CANONICAL_PRICE_ROWS_CREATED=63826
CANONICAL_VOLUME_ROWS_CREATED=63826
CANONICAL_STATUS_ROWS_CREATED=0
CANONICAL_ACCEPTED_PRICE_ROWS=63826
CANONICAL_ACCEPTED_VOLUME_ROWS=63826
MAPPED_SECURITIES=507
DATE_MIN=2026-02-02
DATE_MAX=2026-08-13
ALL_LEGACY_ROWS_HAVE_CANONICAL_DISPOSITION=YES
UNAUTHORIZED_IDENTITIES=0
DUPLICATES=0
INVALID_OHLCV=0
MISSING_REQUIRED_CANONICAL_LINEAGE=0
REJECTED_ROWS=0
QUARANTINED_ROWS=0
UNEXPLAINED_ROW_DIFFERENCE=0
```

The accepted PRICE disposition count, keyed back through the preserved raw
legacy row identity, is exactly 63,826. The typed-family row counts are
reported separately and are not incorrectly treated as one base-row count.

## 17. Canonical Read Verification

The existing V1 repository read path was verified against the canonical
chain for three controls:

| Control | Rows returned | Range | Source | Quality |
|---|---:|---|---|---|
| TPE/2330 | 126 | 2026-02-02..2026-08-13 | `TWSE_OFFICIAL_DAILY` | `ACCEPTED` |
| TWO/6488 | 126 | 2026-02-02..2026-08-13 | `TPEX_OFFICIAL_DAILY` | `ACCEPTED` |
| TPE/6806 | 88 | 2026-02-02..2026-06-22 | `TWSE_OFFICIAL_DAILY` | `ACCEPTED` |

All returned rows were date ordered. The V2 accepted daily projection view
returned 63,826 rows and the same three controls resolved through the
canonical source chain. No fallback to `market_data_ohlcv` was used.

```text
V1_HISTORY_CANONICAL_READ=PASS
V2_DAILY_PROJECTION_CANONICAL_READ=PASS
V1_V2_SHARED_AUTHORITY_READY=YES
STOCK_006A_V2_ROUTE=NOT_IMPLEMENTED_BY_SCOPE
```

The view reports `UNKNOWN` trading status because historical trading-status
evidence was intentionally not invented. Price coverage remains available
because each accepted PRICE row has a non-null close.

## 18. Idempotent Rerun

The bridge was rerun with the same legacy evidence, manifest, contract
version, mapping policy version, and reference version:

```text
ADDITIONAL_RAW_ROWS=0
ADDITIONAL_TIMELINE_ROWS=0
ADDITIONAL_CANONICAL_ROWS=0
ADDITIONAL_PRICE_ROWS=0
ADDITIONAL_VOLUME_ROWS=0
IDEMPOTENT_RERUN=PASS
```

The rerun reused 63,826 raw rows, 63,826 timeline entries, 63,826 PRICE
observations, and 63,826 VOLUME observations. No silent overwrite occurred.

## 19. Tests / Validation

Promotion-specific and affected backend contract tests:

```text
PYTEST=27 passed, 1 warning
RUFF=PASS
COMPILE=PASS
MIGRATION_SCHEMA_INSPECTION=PASS
LOCAL_READ_ONLY_ROW_CONTROLS=PASS
REFERENCE_BUNDLE_VALIDATION=PASS
DIFF_CHECK=PASS
SECRET_SCAN=PASS
```

The warning was the existing Starlette/httpx deprecation warning. OpenAPI,
generated clients, frontend, and frontend tests were not changed or required
for this persistence promotion.

## 20. Risks / Remaining Limitations

1. Canonical source registrations used by this local database are the exact
   existing `twse/tpex-official-daily.v1` registrations. The bridge does not
   claim equivalence between the legacy normalizer marker and a v2 adapter.
2. Historical trading status is absent/unavailable for promoted bars. The
   bridge does not infer `OPEN`, `TRADING`, or `ACTIVE` from the presence of an
   OHLCV row.
3. `ADJUSTMENT_STATE=UNKNOWN` remains mandatory. Corporate-action adjustment,
   adjusted prices, total return, and return semantics are outside this task.
4. The raw provider response body was not present in the legacy evidence
   table. Source URL, response hash, request parameters, retrieval time, and
   legacy row identity were preserved instead.
5. This task did not implement the Stock-006A V2 route, technical indicators,
   Dataset Freeze, walk-forward, backtest, parameter search, or frontend/API
   contract changes.

## 21. Stock-006A Unlock Decision

All unlock conditions passed:

```text
LOCAL_CANONICAL_SCHEMA_READY=YES
REFERENCE_CONTEXT_READY=YES
BRIDGE_IMPLEMENTED=YES
EXPECTED_SECURITIES=507
MAPPED_SECURITIES=507
LEGACY_ROWS=63826
ALL_LEGACY_ROWS_HAVE_CANONICAL_DISPOSITION=YES
UNAUTHORIZED_IDENTITIES=0
DUPLICATES=0
INVALID_OHLCV=0
MISSING_REQUIRED_CANONICAL_LINEAGE=0
UNEXPLAINED_ROW_DIFFERENCE=0
6806_CONTROL=PASS
3059_CONTROL=PASS
CANONICAL_ACCEPTED_READ_RUNTIME_VERIFIED=YES
V1_HISTORY_CANONICAL_READ=PASS
V1_V2_SHARED_AUTHORITY_READY=YES
IDEMPOTENT_RERUN=PASS
```

Therefore:

```text
STOCK_006A_RETRY_AUTHORIZED=YES
NEXT_RECOMMENDED_TASK=RETRY_TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
```

The original Stock-006A task was not restarted automatically.

## 22. Final Handoff

```text
TASK_ID=TASK-DATA-HIST-PERSISTENCE-AUTHORITY-PROMOTION
FINAL_STATUS=HISTORICAL_PERSISTENCE_AUTHORITY_PROMOTION_COMPLETE

SELECTED_SINGLE_HISTORY_AUTHORITY=V2_CANONICAL_OBSERVATION_CHAIN
LEGACY_TABLE_ROLE=HIST_002B_EVIDENCE_AND_STAGING_ONLY
CANONICAL_OBSERVATION_ROLE=SOLE_V1_V2_HISTORICAL_PUBLICATION_AUTHORITY

LOCAL_DB_MIGRATION_PRE_STATE=0017_phase3_4_005_market_data_source_and_raw_observations
LOCAL_DB_MIGRATION_POST_STATE=0029_task_data_ref_006e_instrument_lifecycle

LEGACY_ROWS=63826
LEGACY_SECURITIES=507
MAPPED_SECURITIES=507
CANONICAL_PRICE_ROWS=63826
CANONICAL_VOLUME_ROWS=63826
CANONICAL_STATUS_ROWS=0
ALL_LEGACY_ROWS_HAVE_CANONICAL_DISPOSITION=YES
UNAUTHORIZED_IDENTITIES=0
DUPLICATES=0
INVALID_OHLCV=0
MISSING_REQUIRED_CANONICAL_LINEAGE=0
UNEXPLAINED_ROW_DIFFERENCE=0
ADJUSTMENT_STATE=UNKNOWN
6806_CONTROL=PASS
3059_CONTROL=PASS
IDEMPOTENT_RERUN=PASS
V1_HISTORY_CANONICAL_READ=PASS
V1_V2_SHARED_AUTHORITY_READY=YES

STOCK_006A_RETRY_AUTHORIZED=YES
NEXT_RECOMMENDED_TASK=RETRY_TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION

APPLICATION_CODE_CHANGED=YES
DATABASE_MUTATION=YES_LOCAL_ONLY
HISTORICAL_DATA_CHANGED=CANONICAL_PROMOTION_ONLY_LEGACY_UNCHANGED
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO

G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
```

Stop here. Do not automatically retry Stock-006A.
