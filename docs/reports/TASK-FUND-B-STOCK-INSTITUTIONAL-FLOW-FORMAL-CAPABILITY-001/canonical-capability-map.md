# FUND-B stock institutional-flow canonical capability map

Task: `TASK-FUND-B-STOCK-INSTITUTIONAL-FLOW-FORMAL-CAPABILITY-001`
Owner role: `FUND_STOCK_INSTITUTIONAL_FLOW_CAPABILITY_OWNER`
Contract: `fund-b.stock-institutional-flow.v1`

| CAPABILITY | SOURCE | CURRENT_CANONICAL_STATUS | IMPLEMENTATION_STATUS | FORMAL_SEMANTICS | FRESHNESS | FUND_C_REUSABLE | FUND_E_REUSABLE | DISPOSITION |
|---|---|---|---|---|---|---|---|---|
| Market-qualified stock identity | V2 `topicpilot.instruments` joined to `topicpilot.markets` | NOT_CANONICALIZED | READY | Lookup key is `(market, instrument_code)`; ambiguous symbol-only lookup returns 409; unknown mapping is observable and dropped | Identity is effective/current at read time | YES | YES | Reconcile serially into C after owner review |
| TPE daily institutional flow | Official TWSE `fund.T86` | NOT_CANONICALIZED | READY | One row per security/session; unit is shares; foreign excludes foreign dealers; dealer is foreign dealer + self-trading + hedge; total reconciles to three-institution net | Request date, source date, source-as-of, retrieval time, response SHA-256 | YES | YES | Capture/persist through the approved runtime only |
| TWO daily institutional flow | Official TPEx `tpex_3insti_daily_trading` | NOT_CANONICALIZED | READY_WITH_SNAPSHOT_LIMIT | Foreign excludes foreign dealers; `Dealers` is the normalized dealer leg; foreign-dealer detail is preserved; normalized total validates against `TotalDifference` | TPEx endpoint is current-snapshot only; mismatched requested date is `STALE` | YES | YES | Persist each dated snapshot; no historical backfill is inferred |
| Daily buy/sell/net legs | TPE/TWO official rows | NOT_CANONICALIZED | READY | `buy >= 0`, `sell >= 0`, `net = buy - sell`; missing fields fail closed; normalized totals are independently reconciled | Per-fact source metadata and content hash | YES | YES | Facts only; no strength score |
| Trading-session windows | Persisted daily facts + `reference_calendar_dates` | NOT_CANONICALIZED | READY | 1D/5D/10D/20D count exchange sessions, not calendar days; incomplete windows return `complete=false` and null aggregates | Expected sessions and observed sessions are inspectable | YES | YES | Keep incomplete output null |
| Consecutive buy/sell state | Persisted daily facts | NOT_CANONICALIZED | READY | Separate foreign, investment trust, dealer, and total streaks; BUY/SELL/FLAT/UNKNOWN; missing or invalid session breaks availability | Current session and missing-session status are explicit | YES | YES | Expose as evidence, not ranking |
| Flow reversal | Current and immediately prior expected session | NOT_CANONICALIZED | READY | Deterministic `SELL_TO_BUY`, `BUY_TO_SELL`, `NONE`, or `UNAVAILABLE`; neutral/flat does not fabricate a reversal | Requires both exact sessions | YES | YES | No alert policy attached |
| Price × flow context | V2 canonical accepted daily price history + flow fact | NOT_CANONICALIZED | READY | Price `UP/DOWN/FLAT` crossed with total flow `BUY/SELL/FLAT`; missing canonical price is `UNAVAILABLE` | Raw observed price basis and exact prior session | YES | YES | Evidence-only context |
| Divergence evidence | Price × flow context | NOT_CANONICALIZED | READY | Deterministic positive/negative divergence or confirming/neutral state; no threshold or recommendation | Unavailable when either side lacks an accepted session | YES | YES | No composite signal |
| Abnormal flow | None approved by owner | NOT_CANONICALIZED | DEFERRED | `POLICY_DECISION_REQUIRED` / `DEFERRED`; no percentile, z-score, or threshold invented | UNKNOWN until formula and history policy are approved | YES | YES | Defer |
| Liquidity-relative flow | Total net shares / accepted daily volume shares | NOT_CANONICALIZED | READY | Ratio is available only when volume exists, is positive, and quality is accepted; otherwise null/UNAVAILABLE | Same-session source and denominator are inspectable | YES | YES | Preserve units and denominator definition |
| Persisted stock flow evidence | `topicpilot.stock_institutional_flow_daily`, migration `0033` | NOT_CANONICALIZED | READY | Idempotent key `(instrument_id, trading_date, source_identity)`; older source snapshot cannot overwrite newer one | `source_as_of`, `retrieved_at`, `response_content_hash`, lineage | YES | YES | Migration execution is an external gate |
| Stock Detail subresource | `GET /api/v2/stocks/{symbol}/institutional-flow` | NOT_CANONICALIZED | READY | Read-only formal envelope with `today`, sessions, windows, streaks, reversal, price-flow, divergence, unusual-flow deferral, liquidity-relative evidence | Response exposes requested/as-of/latest/source metadata | YES | YES | Additive consumer handoff; no full UI redesign |
| Generated API client and web data layer | OpenAPI + `packages/api-client` + web `stock-api.ts` | NOT_CANONICALIZED | READY | Typed route/query and explicit unavailable state; no browser-side institutional policy | Transport errors remain unavailable | YES | YES | Keep browser render-only |
| Institutional strength score | None | NOT_CANONICALIZED | NOT_CREATED | No formula, ranking, weight, recommendation, or composite score exists | N/A | NO | NO | Explicitly prohibited |

## Official source references

- [TWSE T86 stock institutional daily report](https://www.twse.com.tw/fund/T86?response=html)
- [TPEx major institutional detail](https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/detail/day.html)
- [TPEx official `tpex_3insti_daily_trading` OpenAPI](https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading)

The adapters retain source identity, dataset, endpoint, adapter version, source
as-of, retrieval timestamp, response content hash, and the normalized unit
contract. They do not convert missing data to zero.
