# PostgreSQL data dictionary

This dictionary documents the public v1 read model. `date` values are Taipei
trading dates; `timestamptz` values are stored in UTC. All numeric observations
are nullable unless explicitly required, and missing values must never be
converted to zero. Alembic migrations remain authoritative for exact lengths,
constraints, and indexes.

Common conventions:

- `id`: generated internal `bigint` primary key.
- `metadata_json`: non-null `jsonb` object for source metadata that has not
  earned a stable query column; never a credential dumping ground.
- Snapshot fact tables link to `ingestion_runs` for lineage.
- `created_at`, `updated_at`, `started_at`, and `completed_at` are UTC timestamps.

## Dimensions and relations

### `stocks`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `code` | varchar(16) | No | Stable public demo stock identifier; unique |
| `name` | varchar(160) | No | Display name |
| `market` | varchar(32) | No | Market segment |
| `industry` | varchar(160) | Yes | Industry label when known |
| `active` | boolean | No | Whether the dimension is active |
| `metadata_json` | jsonb | No | Non-core attributes |
| `created_at` / `updated_at` | timestamptz | No | Audit timestamps |

### `topics`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `slug` | varchar(120) | No | Stable URL/API identifier; unique |
| `name` | varchar(160) | No | Display name |
| `group_name` | varchar(160) | Yes | Higher-level display grouping |
| `topic_type` | varchar(64) | No | Contract-defined topic category |
| `enabled` | boolean | No | Whether the topic participates in views |
| `metadata_json` | jsonb | No | Non-core attributes |
| `created_at` / `updated_at` | timestamptz | No | Audit timestamps |

### `topic_hierarchy`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `parent_topic_id` | bigint FK | No | Parent topic |
| `child_topic_id` | bigint FK | No | Child topic; cannot equal parent |
| `weight` | numeric(10,4) | Yes | Optional relationship weight |
| `enabled` | boolean | No | Whether the edge is active |
| `metadata_json` | jsonb | No | Evidence/version metadata |

Parent-child pairs are unique. The importer must reject cycles even though a
simple SQL check constraint can only reject self-reference.

### `stock_topic_relations`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `stock_id` | bigint FK | No | Related stock |
| `topic_id` | bigint FK | No | Related topic |
| `relation_type` | varchar(32) | No | Stable relation/role classification |
| `weight` | numeric(10,4) | Yes | Optional relationship weight |
| `evidence_summary` | text | Yes | Public-safe explanation; no news article text |
| `metadata_json` | jsonb | No | Non-core relation attributes |

The stock, topic, and relation type combination is unique.

## Ingestion and lineage

### `ingestion_runs`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `contract_version` | varchar(64) | No | `enterprise_bundle.v1` |
| `bundle_version` | varchar(160) | No | Globally unique producer version |
| `data_date` | date | No | Taipei trading date |
| `bundle_hash` | varchar(64) | No | Lowercase SHA-256 for the complete manifest contract |
| `source_kind` | varchar(32) | No | `synthetic` or approved private source kind |
| `source_name` | varchar(160) | No | Non-secret producer identity |
| `classification` | varchar(64) | No | Public-safe or private classification |
| `generated_at` | timestamptz | No | Bundle generation time in UTC |
| `status` | varchar(32) | No | Import lifecycle state |
| `row_counts` | jsonb | No | Manifest counts by artifact |
| `started_at` | timestamptz | No | Import start |
| `completed_at` | timestamptz | Yes | Successful/failed completion |
| `error_message` | text | Yes | Sanitized operator error; no credentials |

`bundle_version` is unique. The importer additionally compares `bundle_hash` to
differentiate safe no-op replay from a mutated-version conflict.

### `source_artifacts`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Owning import run |
| `artifact_name` | varchar(80) | No | Logical artifact name |
| `file_name` | varchar(255) | No | Basename only, not a private path |
| `sha256` | varchar(64) | No | Exact file hash |
| `row_count` | integer | No | Parsed logical rows |
| `byte_size` | bigint | No | UTF-8 byte length |
| `metadata_json` | jsonb | No | Non-core artifact metadata |

Artifact name is unique within an ingestion run.

### `data_quality_events`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Run that detected the event |
| `data_date` | date | No | Affected trading date |
| `severity` | varchar(16) | No | Contract-defined severity |
| `event_code` | varchar(80) | No | Stable machine-readable code |
| `message` | text | No | Public-safe diagnostic |
| `entity_type` | varchar(64) | Yes | Optional table/domain |
| `entity_key` | varchar(160) | Yes | Optional natural key |
| `metadata_json` | jsonb | No | Counts and diagnostics |

## Snapshot facts

### `market_snapshots`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Source lineage |
| `data_date` | date | No | Trading date |
| `generated_at` | timestamptz | No | Calculation time |
| `market` | varchar(32) | No | Market segment |
| `status` | varchar(32) | No | Availability state |
| `total_stocks` | integer | Yes | Expected observed count |
| `advance_count` | integer | Yes | Advancing instruments |
| `decline_count` | integer | Yes | Declining instruments |
| `unchanged_count` | integer | Yes | Unchanged instruments |
| `unavailable_count` | integer | Yes | Missing/unavailable instruments |
| `metadata_json` | jsonb | No | Other breadth observations |

The run, date, and market combination is unique. Counts cannot be negative.

### `stock_snapshots`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Source lineage |
| `data_date` | date | No | Trading date |
| `stock_id` | bigint FK | No | Stock dimension |
| `price` | numeric(18,4) | Yes | Synthetic/private observation |
| `change_pct` | numeric(12,4) | Yes | Percentage change |
| `volume` | bigint | Yes | Volume observation |
| `ma5` / `ma20` | numeric(18,4) | Yes | Moving-average observations |
| `rs20` | numeric(12,4) | Yes | Relative-strength observation |
| `technical_state` | varchar(80) | Yes | Source-defined state |
| `chip_score` | numeric(12,4) | Yes | Source-defined chip score |
| `data_freshness` | varchar(32) | Yes | Freshness classification |
| `metadata_json` | jsonb | No | Additional approved observations |

The run, date, and stock combination is unique. The stock/date index supports
latest and historical reads.

### `topic_snapshots`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Source lineage |
| `data_date` | date | No | Trading date |
| `topic_id` | bigint FK | No | Topic dimension |
| `score` | numeric(12,4) | Yes | Topic score |
| `grade` | varchar(16) | Yes | Source-defined grade |
| `strength_state` | varchar(48) | Yes | Heating/cooling/neutral state |
| `advance_count` / `decline_count` | integer | Yes | Constituent breadth |
| `unchanged_count` / `unavailable_count` | integer | Yes | Remaining breadth |
| `coverage_pct` | numeric(8,4) | Yes | Valid-data coverage percentage |
| `metadata_json` | jsonb | No | Additional approved observations |

The run, date, and topic combination is unique.

## Strategy facts

### `strategy_runs`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `ingestion_run_id` | bigint FK | No | Source lineage |
| `strategy_key` | varchar(8) | No | `MAS`, `MAV`, `TMC`, `BB`, `PB`, or `KD` |
| `name` | varchar(160) | No | Display name |
| `model_version` | varchar(64) | No | Producer model version |
| `data_date` | date | No | Trading date |
| `status` | varchar(32) | No | Run availability state |
| `candidate_count` | integer | No | All candidates before selection |
| `selected_count` | integer | No | Selected candidates |
| `metadata_json` | jsonb | No | Other run metadata |

Run, strategy, date, and model version are unique.

### `strategy_candidates`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `strategy_run_id` | bigint FK | No | Parent strategy run |
| `stock_id` | bigint FK | No | Candidate stock |
| `rank` | integer | No | Rank unique within run |
| `score` | numeric(12,4) | Yes | Strategy score |
| `reason` | text | Yes | Public-safe explanation |
| `price` | numeric(18,4) | Yes | Observation at run time |
| `selected` | boolean | No | Selected for presentation |
| `trigger_price` | numeric(18,4) | Yes | Source-defined reference |
| `support_price` | numeric(18,4) | Yes | Source-defined reference |
| `invalidation_price` | numeric(18,4) | Yes | Source-defined reference |
| `metadata_json` | jsonb | No | Additional strategy observations |

Candidate stock and rank are each unique within a strategy run.

### `strategy_performance`

| Column | Type | Null | Meaning |
|---|---|---:|---|
| `strategy_run_id` | bigint FK | No | Evaluated run |
| `horizon` | varchar(8) | No | Contract-defined performance horizon |
| `status` | varchar(32) | No | Availability/evaluation state |
| `sample_count` | integer | Yes | Evaluated sample count |
| `win_rate_pct` | numeric(8,4) | Yes | Win rate percentage |
| `average_return_pct` | numeric(12,4) | Yes | Mean return percentage |
| `reason` | text | Yes | Explanation when unavailable/partial |
| `metadata_json` | jsonb | No | Additional performance observations |

Horizon is unique within a strategy run.

## Analytics views

| View | Grain | Primary consumers |
|---|---|---|
| `vw_latest_stock_snapshot` | One row per active stock | React overview, Power BI stock page |
| `vw_topic_constituents` | One row per active stock-topic relation | React topic detail, Power BI relations |
| `vw_topic_rotation_14d` | One row per topic summarizing up to 14 available observations | Topic rotation visual |
| `vw_strategy_performance` | One row per strategy run and horizon | Strategy KPI/report |
| `vw_data_quality_daily` | One row per trading date and severity/code aggregate | Status page and operations |

Consumers may query only these approved analytics views or documented API
endpoints; they must not duplicate business calculations in React or Power BI.
