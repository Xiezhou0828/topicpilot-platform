# Entity relationship diagram

The diagram describes the PostgreSQL v1 read model. Dimension tables use stable
natural identifiers such as stock code and topic slug. Snapshot facts remain
traceable to one `ingestion_runs` row.

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
    STOCKS ||--o{ STOCK_SNAPSHOTS : measured_by
    TOPICS ||--o{ TOPIC_SNAPSHOTS : measured_by
    STRATEGY_RUNS ||--o{ STRATEGY_CANDIDATES : ranks
    STRATEGY_RUNS ||--o{ STRATEGY_PERFORMANCE : evaluates
    STOCKS ||--o{ STRATEGY_CANDIDATES : candidate

    INGESTION_RUNS {
      bigint id PK
      varchar contract_version
      varchar bundle_version UK
      date data_date
      char bundle_hash
      varchar source_kind
      varchar classification
      timestamptz generated_at
      varchar status
      jsonb row_counts
    }
    SOURCE_ARTIFACTS {
      bigint id PK
      bigint ingestion_run_id FK
      varchar artifact_name
      varchar file_name
      char sha256
      integer row_count
      bigint byte_size
    }
    STOCKS {
      bigint id PK
      varchar code UK
      varchar name
      varchar market
      varchar industry
      boolean active
    }
    TOPICS {
      bigint id PK
      varchar slug UK
      varchar name
      varchar group_name
      varchar topic_type
      boolean enabled
    }
    TOPIC_HIERARCHY {
      bigint id PK
      bigint parent_topic_id FK
      bigint child_topic_id FK
      numeric weight
      boolean enabled
    }
    STOCK_TOPIC_RELATIONS {
      bigint id PK
      bigint stock_id FK
      bigint topic_id FK
      varchar relation_type
      numeric weight
      text evidence_summary
    }
    MARKET_SNAPSHOTS {
      bigint id PK
      bigint ingestion_run_id FK
      date data_date
      varchar market
      varchar status
      integer total_stocks
    }
    STOCK_SNAPSHOTS {
      bigint id PK
      bigint ingestion_run_id FK
      date data_date
      bigint stock_id FK
      numeric price
      numeric change_pct
      bigint volume
      numeric ma5
      numeric ma20
      numeric rs20
      numeric chip_score
    }
    TOPIC_SNAPSHOTS {
      bigint id PK
      bigint ingestion_run_id FK
      date data_date
      bigint topic_id FK
      numeric score
      varchar grade
      varchar strength_state
      numeric coverage_pct
    }
    STRATEGY_RUNS {
      bigint id PK
      bigint ingestion_run_id FK
      varchar strategy_key
      varchar model_version
      date data_date
      varchar status
      integer candidate_count
      integer selected_count
    }
    STRATEGY_CANDIDATES {
      bigint id PK
      bigint strategy_run_id FK
      bigint stock_id FK
      integer rank
      numeric score
      boolean selected
      numeric trigger_price
      numeric support_price
      numeric invalidation_price
    }
    STRATEGY_PERFORMANCE {
      bigint id PK
      bigint strategy_run_id FK
      varchar horizon
      varchar status
      integer sample_count
      numeric win_rate_pct
      numeric average_return_pct
    }
    DATA_QUALITY_EVENTS {
      bigint id PK
      bigint ingestion_run_id FK
      date data_date
      varchar severity
      varchar event_code
      text message
      varchar entity_type
      varchar entity_key
    }
```

The exact SQL, constraints, and indexes are authoritative in the Alembic
migrations. This diagram is the review-oriented logical representation.
