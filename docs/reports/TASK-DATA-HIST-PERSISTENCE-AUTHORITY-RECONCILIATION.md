# TASK-DATA-HIST-PERSISTENCE-AUTHORITY-RECONCILIATION

## Executive Decision

```text
TASK_ID=TASK-DATA-HIST-PERSISTENCE-AUTHORITY-RECONCILIATION
TASK_NAME=Historical Persistence Authority Reconciliation
FINAL_STATUS=HISTORICAL_PERSISTENCE_AUTHORITY_DECIDED_IMPLEMENTATION_REQUIRED

SELECTED_SINGLE_HISTORY_AUTHORITY=V2_CANONICAL_OBSERVATION_CHAIN
LEGACY_TABLE_ROLE=HIST_002B_EVIDENCE_AND_STAGING_ONLY
CANONICAL_OBSERVATION_ROLE=SOLE_HISTORICAL_PUBLICATION_AUTHORITY
BRIDGE_REQUIRED=YES
BRIDGE_IMPLEMENTED=NO
STOCK_006A_RETRY_AUTHORIZED=NO
```

The authority decision is **Option C, with one publication authority**:

```text
topicpilot.market_data_ohlcv
    = retained HIST-002B legacy ingestion/staging/evidence

topicpilot.canonical_observations
  + canonical_price_observations
  + canonical_volume_observations
  + canonical_trading_status_observations
  + accepted daily projections from revisions 0025/0026
    = the only V1/V2 historical publication authority
```

This does not promote the legacy table, does not delete it, and does not
create a second history read path. The decision follows the current V2
architecture and read paths, the linear Alembic chain, and the local data
evidence. A deterministic promotion bridge is still required because the
legacy table does not carry enough typed lineage and observation metadata to
be inserted safely by the existing normalizer without a new, explicitly
approved bridge contract.

No migration, backfill, provider request, seed, reseed, runtime, API,
frontend, or Production operation was performed by this task.

## Canonical / DB Preflight

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_PRE_SHA=3349774978e5abae90ed14064a1a3c3edbd7a3c9
CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
CANONICAL_POST_SHA=3349774978e5abae90ed14064a1a3c3edbd7a3c9
WORKTREE_CREATED=NO
WORKTREE_USED=NO
PRE_EXISTING_DIRTY_STATE=YES
PRE_EXISTING_DIRTY_FILES=166
PRE_EXISTING_MODIFIED_FILES=13
PRE_EXISTING_UNTRACKED_FILES=153
PRE_EXISTING_STAGED_FILES=0
```

The canonical checkout was inspected directly. Fifteen Git worktrees were
present, including the old `D:/topicpilot-platform-task-repo-006a` worktree;
it was not reused and was not treated as authority. Existing dirty and
untracked files were preserved. No reset, stash, checkout, clean, deletion,
or worktree cleanup was performed.

Observed concurrent surfaces were treated as read-only collision context:
the current operations audit branch, documentation and governance worktrees,
Today worktrees, Stock worktrees, and the historical 006A worktree. This task's
write set is limited to this report.

Required read context was reviewed: `AGENTS.md`, `PROJECT_CONTEXT.md`,
`docs/ROADMAP.md`, `docs/WORK_ORDERS.md`, the Stock 006/006A reports, the
HIST-002B closure evidence, the current 0017-through-0029 migrations, the
V2 market-data/normalizer/repository/read-model code, related tests, and the
market-data source/lineage architecture records.

No standalone HIST-001 report is present in the canonical checkout. HIST-001
and its isolated predecessor evidence are referenced by the HIST-002B closure
report; they remain historical evidence and do not override current V2
architecture ownership.

## Local PostgreSQL Preflight

The local PostgreSQL connection was inspected by a transaction with
`SET TRANSACTION READ ONLY`.

```text
DATABASE=topicpilot
SERVER_VERSION=16.14
DATABASE_USER=topicpilot
TRANSACTION_READ_ONLY=on
LOCAL_DB_MIGRATION_STATE=0017_phase3_4_005_market_data_source_and_raw_observations
REPOSITORY_MIGRATION_HEAD=0029_task_data_ref_006e_instrument_lifecycle
```

The database contains the 0017 raw foundation and a separate legacy table,
but does not contain the timeline or canonical observation tables:

| Relation | Local state |
|---|---|
| `topicpilot.market_data_sources` | exists, 7 rows |
| `topicpilot.raw_market_observations` | exists, 4,237 rows |
| `topicpilot.market_data_ohlcv` | exists, 63,826 rows |
| `topicpilot.observation_timeline_batches` | absent |
| `topicpilot.observation_timeline_entries` | absent |
| `topicpilot.canonical_observations` | absent |
| `topicpilot.canonical_price_observations` | absent |
| `topicpilot.canonical_volume_observations` | absent |
| `topicpilot.canonical_trading_status_observations` | absent |
| `topicpilot.reference_instrument_lifecycles` | absent |

The 4,237 rows in `raw_market_observations` are existing bounded V2 sample
lineage from several providers; they are not the 63,826-row HIST-002B full
universe. The canonical observation family is not materialized in this local
database, so current V1/V2 canonical queries cannot be runtime-verified here.

## Migration Reality: 0017 Through Current Head

The migration chain is linear and expresses a raw-to-timeline-to-canonical
V2 progression. It is not a second, parallel V2 history design:

| Revision | Authority implication |
|---|---|
| `0017_phase3_4_005_market_data_source_and_raw_observations` | Creates `market_data_sources` and immutable `raw_market_observations`; it does **not** create `market_data_ohlcv`. |
| `0018_phase3_4_006_observation_timeline` | Adds append-first timeline batches/entries/quality events over raw observations, with lineage and correction links. |
| `0019_phase3_5_001b_canonical_observations` | Adds the append-only canonical base plus PRICE, VOLUME, QUOTE, and TRADING_STATUS detail families. |
| `0020_phase3_5_002a_reference_registry` | Adds versioned currency, timezone, session, status, and adjustment registries required by normalization. |
| `0021_phase3_6_001b_import_audit` | Adds legacy master-data import audit records; it is not an OHLCV backfill or promotion. |
| `0022_task_live_002_runtime` | Adds live tracking/collector state; it does not replace historical canonical observations. |
| `0023_task_be_003_provider_orchestrator` | Adds source ranking metadata to `market_data_sources`. |
| `0024_task_be_007_topic_snapshots` | Adds topic snapshots; no historical bar authority change. |
| `0025_task_data_022_daily_market_contract` | Projects accepted, non-superseded canonical DAILY_BAR PRICE rows and joins canonical VOLUME by timeline lineage. |
| `0026_task_data_022a_no_trade_coverage` | Adds canonical trading-status coverage, accepted/incomplete selection, and fail-closed no-trade semantics. |
| `0027_task_be_021_topic_lifecycle_results` | Adds topic lifecycle shadow results; no price-history authority change. |
| `0028_task_data_ref_001_reference_bootstrap` | Adds reference bundle hashes, active-set guard, and calendar-date evidence. |
| `0029_task_data_ref_006e_instrument_lifecycle` | Adds date-effective instrument lifecycle evidence; it does not create another OHLCV family. |

The repository therefore treats `0019` plus the later canonical projections as
the V2 observation authority. The local `market_data_ohlcv` table is not
created by the current Alembic chain. The HIST-002B closure also records its
predecessor `db/migrations/001_market_data.sql` as an obsolete plain-table
source file, not as a canonical V2 migration.

No repository migration, promoter, backfill command, or adapter references
`market_data_ohlcv`. The existing `ingest_historical` runtime accepts a
provider `HistoricalFetchResult` and writes Provider → Raw → Timeline →
Canonical; it does not read the legacy table.

## HIST-002B Physical Evidence

The local read-only controls match the accepted HIST-002B closure evidence:

```text
HIST_002B_PHYSICAL_TABLE=topicpilot.market_data_ohlcv
HIST_002B_ROWS=63826
HIST_002B_SECURITIES=507
DATE_RANGE=2026-02-02..2026-08-13
TWSE_ROWS=39523
TWSE_SECURITIES=314
TPEX_ROWS=24303
TPEX_SECURITIES=193
NULL_VOLUME_ROWS=0
NULL_OHLC_ROWS=0
INVALID_OHLCV=0
DUPLICATE_KEY_EXCESS=0
MISSING_REQUIRED_LINEAGE=0
UNEXPLAINED_GAP_EVIDENCE=0_PER_HIST_002B_CLOSURE
```

The table has 63,826 unique `(market, security_code, trading_date)` rows. Its
physical key is `(market, security_code, trading_date, provider)` with a
serial `id` primary key; the stronger three-field duplicate control also
returned zero excess rows. All bar identities join to one active TPE/TWO V2
instrument identity. The local instrument registry has 508 active equities,
including one `TEST/TEST.EQ` fixture identity with no historical bar; the bar
universe itself is 507 approved instruments.

The table has no `3059` rows. `6806` has 88 rows, first bar
`2026-02-02`, last bar `2026-06-22`, and zero rows on or after the
`2026-06-23` termination boundary. Its table `lifecycle_status` is still
`active`; that field is not a date-effective lifecycle authority and must not
be treated as a substitute for revision 0029 evidence.

The table's provider lineage is non-null for all rows and contains:
`provider`, `source_url`, `source_kind`, `normalizer`, `retrieved_at`,
`request_params`, and `response_sha256`. Every row uses
`topicpilot.official_ohlcv.v1` as its normalizer marker. This is useful
evidence, but it is not the current canonical V2 versioned lineage contract.

## Legacy Table Contract

`topicpilot.market_data_ohlcv` is a plain, legacy/staging-shaped table:

| Field | Observed contract | Reconciliation consequence |
|---|---|---|
| `id` | `bigint` serial PK | Stable legacy row identity can be retained as bridge evidence. |
| `market`, `security_code`, `trading_date` | non-null text/date | Deterministically resolves to TPE/TWO and an instrument for all 63,826 rows. |
| `open`, `high`, `low`, `close` | nullable numeric except `close` non-null | Values can map to PRICE, but null/quality semantics must remain explicit. |
| `volume` | nullable bigint | Candidate DAILY_TOTAL quantity; no zero fill is allowed. |
| `provider`, `source_url` | non-null text | Source evidence is present, but current adapter identity is not. |
| `provider_lineage` | non-null JSONB | Contains provider/retrieval/request/hash evidence, not a preserved raw payload. |
| `lifecycle_status` | non-null text, all observed values `active` | Not equivalent to date-effective instrument lifecycle or daily trading status. |
| `created_at`, `updated_at` | non-null timestamptz | `created_at` is not proven to be source receipt time. |

The table does **not** directly contain `instrument_id`, typed `observed_at`,
`received_at`, typed `retrieved_at`, `session_code`, `timezone_name`,
`calendar_code`, `quality_state`, `adjustment_state`,
`normalization_contract_version`, `mapping_policy_version`,
`reference_data_version`, `supersedes_id`, canonical content hash, canonical
idempotency key, or raw provider payload. Those omissions are the reason a
promotion is not inferred from row-count parity alone.

## Canonical Observation Contract

The current V2 canonical contract is defined by revision 0019, its ORM models,
the Phase 3.5 physical-design records, and the normalization runtime:

- one append-only canonical base row per family output, linked to a timeline
  entry, raw observation, instrument, and source;
- typed PRICE, VOLUME, QUOTE, and TRADING_STATUS detail rows;
- first-class `observed_at`, `received_at`, `retrieved_at`, session, timezone,
  calendar, source-field path, ordering key, and three version fields;
- explicit `quality_state`, validation/warning evidence, content hash, and
  deterministic idempotency key;
- corrections represented by appended rows through `supersedes_id`; prior
  rows are not mutated;
- default reads include accepted rows with no accepted successor of the same
  family and exclude rejected/quarantined/conflicting rows;
- missing values remain NULL, with no synthetic bars, carry-forward, or
  null-to-zero coercion.

The existing `HistoricalDailyBarNormalizer` can map a normalized provider bar
into PRICE, optional VOLUME, and explicit TRADING_STATUS candidates. Its
`ingest_historical` caller provides source registration, request-keyed batch
idempotence, raw/timeline lineage, reference-context loading, and canonical
idempotence. It cannot safely supply the missing legacy receipt, reference,
adapter, and raw-payload semantics without a separately approved bridge.

## V1 / V2 Current Read Paths

### V1 history route

`GET /api/v1/stocks/{code}/price-history` in `main.py` calls
`repository.list_price_history`. The repository:

1. resolves the active V2 `instruments`/`markets` identity;
2. reads `canonical_observations` joined to
   `canonical_price_observations`;
3. selects `family_code='PRICE'`, `quality_state='ACCEPTED'`, and no accepted
   successor;
4. joins volume from the canonical VOLUME family; and
5. orders by observed time, ordering key, and observation id.

It never queries `market_data_ohlcv`. The route is bounded to `limit <= 200`,
rejects reversed date ranges, and preserves nullable fields. It is not
runtime-verified against this local DB because its required canonical tables
are absent.

### V2 Stock read model

`GET /api/v2/stocks` and `GET /api/v2/stocks/{symbol}` call
`production_read_model.py`. The formal EOD read model selects canonical
accepted, current PRICE observations, canonical DAILY_TOTAL VOLUME, and
canonical TRADING_STATUS observations. The 0025/0026 views use the same
canonical families, source ranking, same-day selection, accepted/incomplete
coverage, and explicit no-trade status semantics.

The V2 historical subresource was deliberately not created by Stock 006A.
Therefore the current V1 and intended V2 paths point to the same canonical
authority by design, but `V1_V2_SHARED_AUTHORITY_READY=NO` in this local
database because that authority is not materialized.

## Authority Decision Matrix

| Dimension | A. Legacy table is publication authority | B. 0029-era canonical chain is publication authority; legacy is deprecated evidence | C. Legacy is ingestion/staging/evidence; canonical chain is the sole publication authority |
|---|---|---|---|
| Migration compatibility | Fits current local rows but not the repository Alembic chain; would require bypassing V2 schema | Fits the V2 chain after a one-time promotion | Fits the V2 chain while preserving existing evidence and requiring one explicit bridge |
| Lineage preservation | Retains JSON lineage but lacks typed V2 lineage and raw payload semantics | Can preserve lineage only if a bridge resolves all missing fields | Preserves legacy evidence in place and requires a bridge to materialize typed canonical lineage; no silent equivalence claim |
| Idempotence | Legacy unique key is strong for identical bars, but no canonical family idempotency or correction chain | Canonical idempotency/supersession are available after promotion | Legacy key plus canonical idempotency can be controlled without making two read authorities |
| Lifecycle | Static `active` is insufficient for date-effective lifecycle and 6806 controls | Canonical lifecycle evidence can be joined after 0029 | Canonical lifecycle remains the only publication interpretation; legacy lifecycle text remains evidence only |
| Accepted/superseded semantics | Not represented | Explicit in canonical chain | Explicit in canonical chain; legacy rows are never read as accepted current rows |
| V1 compatibility | Requires changing the current V1 query to a new legacy SQL path | Works with the current V1 query after promotion | Works with the current V1 query after promotion; V1 and V2 share the same canonical read service target |
| V2 compatibility | Creates a second V2 history contract or changes current read model ownership | Compatible after bridge and schema materialization | Compatible after bridge; no new history table family or parallel query is needed |
| REC-A1 reproducibility | Weak: raw payload, policy versions, and canonical snapshot identity are absent | Strong only after all canonical lineage and reference inputs are materialized | Strong after bridge; legacy artifact/hash remains traceable and canonical rows are versioned |
| Technical projection | Could read raw values but would bypass canonical quality/adjustment/lifecycle policy | Canonical downstream projection is available | Canonical downstream projection remains the only allowed input to technical work |
| Rollback / risk | Highest semantic divergence and future cutover risk | Promotion is append-only but direct backfill can lose legacy-role clarity | Local-only append promotion is bounded and reversible by read disposition; source evidence is retained |
| Duplicate-authority risk | High: legacy and V2 code would compete | Medium unless legacy role is explicitly retired | Low once the legacy role is explicitly non-publication and all reads use canonical chain |
| Decision | Reject | Incomplete as a role model because evidence retention is still required | **Selected** |

Option A is rejected because it would turn an unrepresented legacy schema into
the V2 authority and require V1/V2 query divergence. Option B has the right
publication target but does not express the required retained-evidence role.
Option C preserves the evidence while selecting exactly one publication
authority.

## Selected Single Authority

```text
SELECTED_SINGLE_HISTORY_AUTHORITY=topicpilot.canonical_observations
  + canonical_price_observations
  + canonical_volume_observations
  + canonical_trading_status_observations
  + accepted daily projections from 0025/0026

LEGACY_TABLE_ROLE=topicpilot.market_data_ohlcv;_HIST_002B_EVIDENCE_STAGING_ONLY
CANONICAL_OBSERVATION_ROLE=SOLE_V1_V2_HISTORICAL_PUBLICATION_AUTHORITY
V1_CURRENT_READ_AUTHORITY=ACCEPTED_NON_SUPERSEDED_CANONICAL_PRICE_OBSERVATIONS
V2_INTENDED_READ_AUTHORITY=SAME_CANONICAL_CHAIN_VIA_SHARED_BACKEND_READ_SERVICE
V1_V2_SHARED_AUTHORITY_READY=NO_LOCAL_CANONICAL_TABLES_ABSENT
```

The legacy table must not be deleted or rewritten as part of this decision.
It is a source/evidence boundary, not a customer-facing read authority.

## Bridge / Promotion Contract (Required, Deferred)

The next bounded implementation must be a local-only bridge into the existing
0017→0029 chain. It must not create a second history table family and must not
re-download or re-seed exchange data.

Required bridge controls:

1. **Preflight and scope gate.** Capture counts, distinct identities, date
   range, per-market counts, row digests, duplicate controls, 6806/3059
   controls, and a reproducibility manifest before any write. Require the
   local PostgreSQL target and fail closed on a Production URL.
2. **Identity mapping.** Map `TWSE/` to V2 `TPE` and `TPEx/` to V2 `TWO`, then
   resolve `(market, security_code)` to exactly one approved active instrument.
   Unknown, ambiguous, TEST, inactive, or outside-universe identities must
   block promotion rather than enter canonical history.
3. **Source identity.** Preserve the legacy provider, source URL, response
   hash, request parameters, and legacy normalizer marker. Register an
   explicit bridge source/adapter identity or obtain an approved mapping to
   the current official provider identity. Do not relabel the legacy
   `topicpilot.official_ohlcv.v1` marker as current `twse/tpex-official-daily.v2`
   without evidence.
4. **Observation timestamps.** Use the existing market-date anchor policy for
   `observed_at` only after it is recorded as a bridge mapping. Parse the
   lineage `retrieved_at` for `retrieved_at`. Do not call legacy `created_at`
   source receipt time; if it is used as bridge receipt time, that meaning and
   the bridge run identity must be explicit.
5. **Reference and policy versions.** Require an active `tw-reference-v1`
   registry set and name the normalization and mapping versions. The current
   local DB has no 0020/0028 reference tables, so the bridge must not invent a
   version in place.
6. **Family mapping.** Map OHLC to PRICE with `adjustment_state=UNKNOWN`.
   Map non-null volume to VOLUME only under an approved `UNIT` / scale-0 /
   `DAILY_TOTAL` contract. Keep null volume null. Do not derive or fabricate
   TRADING_STATUS from the legacy `lifecycle_status='active'` field.
7. **Quality and correction policy.** Publish only rows that pass typed
   lineage, OHLCV, identity, reference, and lifecycle controls. Use canonical
   accepted rows with deterministic idempotency keys; any later correction is
   an appended successor. No legacy row may be mutated or deleted.
8. **6806 and 3059 controls.** Require last bar `2026-06-22`, termination
   `2026-06-23`, post-termination `0`, and unauthorized `3059` inclusion `0`
   both before and after promotion. Lifecycle publication must come from
   date-effective reference evidence, not the legacy static status field.
9. **Idempotent rerun.** Rerunning the exact bridge against the same manifest
   must create/promote zero additional raw, timeline, canonical, or detail
   rows. A changed source hash or mapping version must produce a deliberate
   new version/correction path, not a silent overwrite.
10. **Postflight.** Re-run all row/count/date/identity/duplicate/invalid/
    lineage/lifecycle controls, confirm canonical accepted/non-superseded
    read counts, and only then authorize Stock 006A to retry.

The bridge is deferred because the current repository has no legacy-table
adapter, no promotion migration, no local 0020/0028 reference materialized in
this database, and no approved semantics for the missing legacy receipt/raw
payload fields.

## Lineage Mapping

| Legacy evidence | Candidate canonical field | Current result |
|---|---|---|
| `market` + `security_code` | `instrument_id`, market/timezone/calendar | Deterministic for all 63,826 rows against the 507-bar universe; implementation deferred. |
| `trading_date` | `observed_at` | Deterministic date-anchor candidate using the existing `Asia/Taipei` market-date policy; must be versioned by the bridge. |
| `provider_lineage.retrieved_at` | `retrieved_at` | Parseable for all rows; can be preserved as retrieved lineage. |
| legacy `created_at` | `received_at` | Not equivalent by evidence; unavailable until bridge semantics are approved. |
| `provider`, `source_url`, request params | `source_id`, source metadata, validation evidence | Source facts are present; current adapter identity differs and cannot be silently relabeled. |
| `provider_lineage.normalizer=topicpilot.official_ohlcv.v1` | `normalization_contract_version` | Not equivalent to current `historical-daily-mapping-v1`; explicit bridge version required. |
| absent legacy reference version | `reference_data_version` | Missing; fail closed until an active versioned registry is present. |
| OHLC values | PRICE detail | Deterministic numeric mapping candidate; `adjustment_state` remains `UNKNOWN`. |
| non-null `volume` | VOLUME detail | Candidate `DAILY_TOTAL`, unit/scale policy requires explicit approval. |
| `lifecycle_status=active` | TRADING_STATUS / instrument lifecycle | Not equivalent; no status row may be fabricated from it. |
| `response_sha256` | raw/canonical content evidence | Preserve as source artifact hash; it is not automatically the canonical content hash. |
| no raw provider payload column | `raw_market_observations.payload` | Missing. Reconstructing a normalized payload would need an explicit legacy-evidence contract and must not be called original raw payload. |

## Lifecycle / 6806 Control

```text
CONTROL_6806=PASS_LEGACY_EVIDENCE_ONLY
6806_LAST_TRADING_BAR=2026-06-22
6806_TERMINATION_BOUNDARY=2026-06-23
6806_POST_TERMINATION_ROWS=0
CONTROL_3059=PASS_LEGACY_EVIDENCE_ONLY
3059_ROWS=0
CANONICAL_LIFECYCLE_CONTROL=NOT_RUN_CANONICAL_TABLES_ABSENT
```

The local table evidence preserves the required 6806 boundary and excludes
3059. It does not establish canonical lifecycle publication. Revision 0029
must be materialized and linked by the future bridge before a Stock route can
claim lifecycle-aware canonical history.

## Idempotence / Duplicate Controls

```text
LEGACY_TABLE_UNIQUE_KEY=(market,security_code,trading_date,provider)
LEGACY_DUPLICATE_KEY_EXCESS=0
LEGACY_INVALID_OHLCV=0
LEGACY_MISSING_REQUIRED_LINEAGE=0
CANONICAL_PROMOTION_IDEMPOTENCE_TEST=NOT_RUN_BRIDGE_DEFERRED
CANONICAL_ROWS_PROMOTED_OR_MIGRATED=0
CANONICAL_DUPLICATE_CONTROL=NOT_RUN_CANONICAL_TABLES_ABSENT
```

The existing V2 normalizer and canonical service provide the desired
idempotency/supersession pattern for a future bridge. Their tests prove the
pattern with synthetic/provider-shaped inputs, not with the legacy table, so
that evidence is not overstated as a HIST-002B promotion result.

## REC-A1 Impact Boundary

This task establishes a persistence-authority decision only. HIST-002B is
usable as raw historical evidence for future planning, subject to the bridge
and adjustment/provenance controls above. This task did not execute:

- Dataset Freeze;
- point-in-time universe or survivorship freeze;
- walk-forward or backtest;
- parameter search or strategy calibration;
- returns, MFE/MAE, benchmark, or Recommendation evaluation; or
- Recommendation publication or production activation.

Corporate Action adjustment remains an independent authority. Raw historical
authority reconciliation does not make adjusted, split-adjusted, dividend,
or total-return semantics ready.

## Stock-006A Unblock Criteria

Stock 006A may retry only after a separate bounded promotion task proves all
of the following in the local canonical database:

1. The local schema is upgraded/materialized through the required canonical
   observation and reference/lifecycle revisions without Production mutation.
2. The bridge maps all 507 approved instruments and all 63,826 evidence rows
   with zero unauthorized identities, gaps, duplicates, invalid OHLCV, or
   missing required canonical lineage.
3. PRICE/VOLUME family mapping, adjustment state, source identity, observation
   timestamps, received/retrieved semantics, policy versions, and reference
   version are explicit and testable.
4. Accepted/non-superseded canonical reads reproduce the expected historical
   evidence and preserve the 6806/3059 controls.
5. An exact rerun creates/promotes zero additional rows and emits reproducible
   no-op evidence.
6. One shared backend read authority is runtime-verified for the existing V1
   route and intended V2 history subresource. Only then may 006A implement a
   bounded read contract; it must not introduce a second persistence path.

## Implementation Performed or Deferred

```text
IMPLEMENTATION_PERFORMED=READ_ONLY_AUDIT_AND_AUTHORITY_DECISION
IMPLEMENTATION_DEFERRED=LOCAL_CANONICAL_SCHEMA_RECONCILIATION_AND_HIST_002B_PROMOTION
APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
OPENAPI_CHANGED=NO
GENERATED_CLIENT_CHANGED=NO
FRONTEND_WIRED=NO
```

No new schema family, adapter, migration, read model, route, test fixture, or
owner-document update was made. No provider was called and no historical row
was re-downloaded, reseeded, deleted, or altered.

## Validation

### Read-only inspection

- PostgreSQL 16 connection and `alembic_version` inspection completed inside a
  transaction with `transaction_read_only=on`.
- `market_data_ohlcv` schema, PK/unique constraints, indexes, lineage keys,
  row counts, market counts, date range, 6806, 3059, identity joins,
  duplicate, invalid-OHLCV, null-volume, and required-lineage controls were
  queried without mutation.
- A 63,826-row in-memory mapping dry run verified market/identity mapping,
  provider/market consistency, lineage key presence, parsed retrieved times,
  and the missing-field blockers recorded above. It did not write a file or
  database row.
- Alembic revisions 0017 through 0029, current repositories/services/routes,
  normalizer/ingestion code, architecture/work-order contracts, and focused
  tests were read.

### Focused backend tests

```text
FOCUSED_BACKEND_TESTS=18 passed, 1 pre-existing Starlette/httpx deprecation warning
TESTS=market-data migration; canonical implementation/query; daily-market contract; price-history API contract; market-data models
POSTGRES_CANONICAL_MUTATION_TESTS=NOT_RUN_LOCAL_DB_AT_0017_AND_MUTATION_OUT_OF_SCOPE
V1_RUNTIME_HISTORY_SMOKE=NOT_RUN_CANONICAL_TABLES_ABSENT
V2_RUNTIME_HISTORY_SMOKE=NOT_RUN_006A_NOT_IMPLEMENTED
OPENAPI=NOT_RUN_NO_API_CHANGE
FRONTEND=NOT_RUN_NO_FRONTEND_CHANGE
```

### Preserved gates

```text
G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
```

The task did not cross reference-registry/bootstrap, provider-coverage,
market-semantics, canonical writer, reconciliation-writer, or Production
boundaries that would require rerunning those protected gates.

## Risks

1. Treating `market_data_ohlcv` as publication authority would create a
   second history semantic and diverge from both current V1 code and V2
   read-model architecture.
2. Mapping `created_at` to source receipt time would fabricate lineage; a
   bridge must distinguish bridge receipt from source retrieval.
3. Mapping the legacy normalizer marker to current adapter or normalization
   versions would overstate semantic equivalence.
4. The legacy table preserves provider hashes and metadata but not the raw
   upstream response payload; a bridge must label any reconstructed payload as
   legacy evidence, never as the original raw artifact.
5. `lifecycle_status='active'` cannot replace date-effective lifecycle or
   daily trading-status evidence, even though the 6806 row boundary currently
   matches the closure report.
6. Corporate Action adjustment semantics remain unknown. Any technical,
   return, or Recommendation consumer must remain blocked or research-only
   until its independent authority is resolved.

## Final Handoff

```text
TASK_ID=TASK-DATA-HIST-PERSISTENCE-AUTHORITY-RECONCILIATION
TASK_NAME=Historical Persistence Authority Reconciliation
FINAL_STATUS=HISTORICAL_PERSISTENCE_AUTHORITY_DECIDED_IMPLEMENTATION_REQUIRED

CANONICAL_PRE_SHA=3349774978e5abae90ed14064a1a3c3edbd7a3c9
CANONICAL_POST_SHA=3349774978e5abae90ed14064a1a3c3edbd7a3c9
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO

LOCAL_DB_MIGRATION_STATE=0017_phase3_4_005_market_data_source_and_raw_observations
HIST_002B_PHYSICAL_TABLE=topicpilot.market_data_ohlcv
HIST_002B_ROWS=63826
HIST_002B_SECURITIES=507
DATE_RANGE=2026-02-02..2026-08-13
CURRENT_V2_CANONICAL_CHAIN=0019_CANONICAL_OBSERVATIONS_PLUS_0025_0026_DAILY_PROJECTIONS_PLUS_0029_LIFECYCLE_EVIDENCE
V1_CURRENT_READ_AUTHORITY=ACCEPTED_NON_SUPERSEDED_CANONICAL_PRICE_OBSERVATIONS
V2_INTENDED_READ_AUTHORITY=SAME_CANONICAL_CHAIN_VIA_SHARED_BACKEND_READ_SERVICE
SELECTED_SINGLE_HISTORY_AUTHORITY=V2_CANONICAL_OBSERVATION_CHAIN
LEGACY_TABLE_ROLE=HIST_002B_EVIDENCE_AND_STAGING_ONLY
CANONICAL_OBSERVATION_ROLE=SOLE_V1_V2_HISTORICAL_PUBLICATION_AUTHORITY
BRIDGE_REQUIRED=YES
BRIDGE_IMPLEMENTED=NO

LOCAL_DB_MUTATION=NO
ROWS_PROMOTED_OR_MIGRATED=0
LINEAGE_PRESERVED=LEGACY_EVIDENCE_ONLY_CANONICAL_LINEAGE_NOT_MATERIALIZED
IDEMPOTENT=LEGACY_KEY_CONTROL_ONLY_PROMOTION_NOT_RUN
DUPLICATES=0_LEGACY_READ_ONLY_CANONICAL_NOT_RUN
INVALID_OHLCV=0_LEGACY_READ_ONLY_CANONICAL_NOT_RUN
CONTROL_6806=PASS_LEGACY_EVIDENCE_ONLY_LAST_BAR_2026-06-22_TERMINATION_2026-06-23_POST_0
CONTROL_3059=PASS_LEGACY_EVIDENCE_ONLY_ROWS_0
V1_V2_SHARED_AUTHORITY_READY=NO_LOCAL_CANONICAL_TABLES_ABSENT
REC_A1_IMPACT=RAW_HISTORICAL_EVIDENCE_ONLY_NO_DATASET_FREEZE_OR_BACKTEST
STOCK_006A_RETRY_AUTHORIZED=NO
NEXT_RECOMMENDED_TASK=TASK-DATA-HIST-PERSISTENCE-AUTHORITY-PROMOTION

APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO
HISTORICAL_DATA_CHANGED=NO
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

Stop here. Do not automatically retry
`TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION`.
