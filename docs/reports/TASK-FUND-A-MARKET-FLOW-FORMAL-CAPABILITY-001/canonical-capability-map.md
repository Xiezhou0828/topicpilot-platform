# FUND-A canonical capability map

Task: `TASK-FUND-A-MARKET-FLOW-FORMAL-CAPABILITY-001`

## Canonical authority

The capability is market-level, daily, cash-value institutional flow for the
two Taiwan public-market venues:

| Market | Official authority | Dataset | Raw unit | Chosen categories |
| --- | --- | --- | --- | --- |
| TPE | TWSE | `fund.BFI82U` | TWD whole yuan | foreign excluding foreign proprietary, investment trust, dealer self + hedge, total |
| TWO | TPEx OpenAPI | `tpex_3insti_summary` | TWD whole yuan | foreign excluding proprietary, investment trust, dealer total, three-institution total |

The typed contract lives in
`services/api/src/topicpilot_api/market_data/institutional_flow.py`. It keeps
buy, sell, net, unit, scale, availability, freshness, source identity, source
as-of, retrieval time, response hash, and lineage together. A missing provider
field or unreconciled total produces `INGESTION_FAILED`; it never becomes zero.

## Capability map

| Layer | Canonical implementation | Boundary |
| --- | --- | --- |
| Discovery and parsing | `institutional_flow.py` | Official TWSE/TPEx payloads only; no FinMind or synthetic production source |
| Persistence | `orm/institutional_flow.py`, `institutional_flow_persistence.py` | Unique `(market, trading_date, source_identity)`; idempotent and stale/conflict-safe |
| Schema migration | `0041_task_fund_a_market_flow_formal_capability.py` | Schema-only; Production execution is not authorized |
| Read API | `GET /api/v2/market/institutional-flow` | Read-only current/previous/5-session/20-session trend envelope |
| Home materialization | `materialize_home_v2(... institutional_flow_facts=...)` | Additive `marketOverview.institutionFlows`; existing market gate unchanged |
| Today Signals | Existing `INSTITUTION_PRICE_DIVERGENCE` adapter input | Formal facts may feed the existing label; signal policy and labels are unchanged |
| Today Market UI | `TodayMarketPage.tsx` | Render-only net values/status/source unit; no browser aggregation or recommendation |
| Generated surfaces | `openapi.json`, `schema.d.ts`, web generated declarations, API client method | Generated from FastAPI OpenAPI and committed together |

## Deliberate non-scope

FUND-B stock-level flow, FUND-C Opportunity, FUND-E topic flow, Today Signals
redesign, A10/A9, B2, scheduler activation, deployment, canary, and Production
database mutation are not implemented.
