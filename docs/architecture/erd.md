# Entity relationship diagram

> Version: v0.2
> Generation: `NEXT / V2` rebuildable PostgreSQL read model; not the `LEGACY / V1` source of truth.

This is a presentation-oriented logical ERD. The Alembic migrations and SQLAlchemy
models remain authoritative for exact types, constraints and indexes. News
entities are included because their schema exists in migration `0002`, but they
are not yet part of the `enterprise_bundle.v1` demo contract.

## Core read model and lineage

```mermaid
erDiagram
    INGESTION_RUNS ||--o{ SOURCE_ARTIFACTS : records
    INGESTION_RUNS ||--o{ MARKET_SNAPSHOTS : imports
    INGESTION_RUNS ||--o{ STOCK_SNAPSHOTS : imports
    INGESTION_RUNS ||--o{ TOPIC_SNAPSHOTS : imports
    INGESTION_RUNS ||--o{ STRATEGY_RUNS : imports
    INGESTION_RUNS ||--o{ DATA_QUALITY_EVENTS : records

    STOCKS ||--o{ STOCK_TOPIC_RELATIONS : classified_as
    TOPICS ||--o{ STOCK_TOPIC_RELATIONS : contains
    TOPICS ||--o{ TOPIC_HIERARCHY : parent
    TOPICS ||--o{ TOPIC_HIERARCHY : child
    STOCKS ||--o{ STOCK_SNAPSHOTS : observed
    TOPICS ||--o{ TOPIC_SNAPSHOTS : observed
    STRATEGY_RUNS ||--o{ STRATEGY_CANDIDATES : ranks
    STRATEGY_RUNS ||--o{ STRATEGY_PERFORMANCE : evaluates
    STOCKS ||--o{ STRATEGY_CANDIDATES : candidate

    INGESTION_RUNS { bigint id PK; varchar bundle_version UK; date data_date; char bundle_hash; varchar status }
    SOURCE_ARTIFACTS { bigint id PK; bigint ingestion_run_id FK; varchar artifact_name; char sha256; integer row_count }
    STOCKS { bigint id PK; varchar code UK; varchar name; varchar market; varchar industry; boolean active }
    TOPICS { bigint id PK; varchar slug UK; varchar name; varchar group_name; varchar topic_type; boolean enabled }
    TOPIC_HIERARCHY { bigint id PK; bigint parent_topic_id FK; bigint child_topic_id FK; numeric weight; boolean enabled }
    STOCK_TOPIC_RELATIONS { bigint id PK; bigint stock_id FK; bigint topic_id FK; varchar relation_type; numeric weight }
    MARKET_SNAPSHOTS { bigint id PK; bigint ingestion_run_id FK; date data_date; varchar market; varchar status; integer total_stocks }
    STOCK_SNAPSHOTS { bigint id PK; bigint ingestion_run_id FK; bigint stock_id FK; date data_date; numeric price; numeric change_pct; bigint volume; numeric ma5; numeric ma20; numeric rs20; numeric chip_score }
    TOPIC_SNAPSHOTS { bigint id PK; bigint ingestion_run_id FK; bigint topic_id FK; date data_date; numeric score; varchar grade; varchar strength_state; numeric coverage_pct }
    STRATEGY_RUNS { bigint id PK; bigint ingestion_run_id FK; varchar strategy_key; varchar model_version; date data_date; varchar status }
    STRATEGY_CANDIDATES { bigint id PK; bigint strategy_run_id FK; bigint stock_id FK; integer rank; numeric score; boolean selected }
    STRATEGY_PERFORMANCE { bigint id PK; bigint strategy_run_id FK; varchar horizon; varchar status; integer sample_count; numeric win_rate_pct; numeric average_return_pct }
    DATA_QUALITY_EVENTS { bigint id PK; bigint ingestion_run_id FK; date data_date; varchar severity; varchar event_code; varchar entity_key }
```

## News extension

```mermaid
erDiagram
    NEWS_ARTICLES ||--o{ NEWS_STOCK_RELATIONS : mentions
    NEWS_ARTICLES ||--o{ NEWS_TOPIC_RELATIONS : relates_to
    STOCKS ||--o{ NEWS_STOCK_RELATIONS : referenced
    TOPICS ||--o{ NEWS_TOPIC_RELATIONS : referenced
    NEWS_ARTICLES { bigint id PK; varchar article_key UK; varchar source_name; text source_url; varchar title; timestamptz published_at; char content_hash; varchar classification }
    NEWS_STOCK_RELATIONS { bigint id PK; bigint news_article_id FK; bigint stock_id FK; varchar relation_type; numeric relevance_score }
    NEWS_TOPIC_RELATIONS { bigint id PK; bigint news_article_id FK; bigint topic_id FK; varchar relation_type; numeric relevance_score }
```

## Reading notes

- Stable identities use natural keys (`stocks.code`, `topics.slug`, `bundle_version`, `article_key`) while surrogate IDs support relational integrity.
- Snapshot facts are immutable observations tied to an ingestion run and date.
- `strategy_key` is constrained to `MAS`, `MAV`, `TMC`, `BB`, `PB`, `KD`.
- Exact columns omitted from the compact diagram remain available through the models, including `metadata_json`, freshness, reasons and reference prices.
- Deferred Topic Engine tables, news metrics, signal performance and strategy stage results are intentionally not shown as current entities.

## Open questions

- **Open Question:** whether the news extension enters a future bundle contract and on what licensing terms.
- **Open Question:** schema and cardinality for deferred topic metric/validation/lifecycle results.
- **Open Question:** strategy pipeline stage-result entities and their relationship to current candidates.
