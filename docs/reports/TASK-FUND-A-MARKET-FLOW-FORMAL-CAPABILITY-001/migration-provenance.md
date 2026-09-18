# Migration provenance

- Revision: `0041_task_fund_a_market_flow_formal_capability`
- Down revision: `0040_task_a10_recovery_checkpoint_observability`
- Table: `topicpilot.market_institutional_flow_daily`
- Identity: `(market, trading_date, source_identity)`
- Numeric semantics: `Numeric(38,0)`, `unit='TWD'`, `scale=0`
- Raw payload: nullable JSONB with response content hash
- Scope: schema definition only
- Production execution: not performed and not authorized

The ORM model and Alembic revision intentionally mirror one another, including
market, availability, freshness, unit, scale, source lineage, and the explicit
buy/sell/net columns for foreign, investment trust, dealer, and total. The
read API is designed to fail closed when the table is not yet present, so
canonical reconciliation can happen serially after migration review.
