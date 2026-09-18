# TASK-FUND-B-STOCK-INSTITUTIONAL-FLOW-FORMAL-CAPABILITY-001 closeout

## Result

`COMPLETE_WITH_EXTERNAL_GATE`

The isolated branch implements a formal, read-only, stock-level institutional-
flow capability for TPE and TWO. The implementation commit is
`192ec78fd055dc94a167bfa3501f32ccef9576dc`. The canonical owner checkout remains at
`02d3086183d1c582bb6c66c4c316340ccce3fa97`; this branch is not canonicalized,
and no production mutation, migration execution, push, or merge was performed.

The machine-readable governance packet is in `task-manifest.json` and
`implementation-evidence.json`. The canonical field-by-field map is in
`canonical-capability-map.md`.

## Q1–Q7 source and semantics answers

1. **Official sources.** TPE uses TWSE `fund.T86`, requested by Gregorian date
   with `selectType=ALL`; TWO uses TPEx `tpex_3insti_daily_trading`. The latter
   is a current snapshot endpoint, so the adapter records a date mismatch as
   `STALE` rather than assigning the snapshot to the requested session.
2. **Identity.** Every persisted fact is bound to a canonical V2 instrument
   through `(market, instrument_code)`. Symbol-only ambiguity returns 409;
   unknown provider mappings are retained as observable mapping errors and are
   never guessed.
3. **Unit.** Both selected official stock-level datasets are normalized to
   `SHARES` with `scale=0`. Buy/sell/net are validated as
   `net = buy - sell`; missing numeric values fail closed.
4. **Daily legs.** The contract exposes foreign, investment trust, dealer, and
   total buy/sell/net. TWSE retains foreign-dealer, dealer-self, and
   dealer-hedge evidence while normalizing dealer as their sum. TPEx retains
   foreign-dealer evidence but uses its published `Dealers` leg as normalized
   dealer. Normalized totals are reconciled against the published total.
5. **Windows and streaks.** 1D/5D/10D/20D use expected exchange sessions,
   excluding weekends and reference calendar holidays. An incomplete window
   returns `complete=false` and null aggregates. Streaks are independently
   computed for foreign, investment trust, dealer, and total; BUY, SELL, FLAT,
   and UNKNOWN are explicit, and missing sessions break availability.
6. **Reversal and price-flow.** Reversal is deterministic from the current and
   immediately prior expected session: `SELL_TO_BUY`, `BUY_TO_SELL`, `NONE`, or
   `UNAVAILABLE`. Price-flow crosses canonical accepted daily price movement
   (`UP/DOWN/FLAT`) with total institutional flow (`BUY/SELL/FLAT`). Divergence
   is descriptive evidence only; no recommendation or ranking is created.
7. **Abnormal and liquidity-relative flow.** Abnormal flow is deliberately
   deferred because no owner-approved formula or threshold exists. Liquidity-
   relative flow is available only as `total_net_shares / accepted_daily_volume`
   when the denominator is positive and known; otherwise it is unavailable.

## Formal implementation

- Migration `0033_task_fund_b_stock_institutional_flow` creates
  `topicpilot.stock_institutional_flow_daily` with the canonical identity,
  source lineage, source-as-of, retrieval timestamp, response hash, unit/scale,
  quality state, and normalized legs. The idempotency key is
  `(instrument_id, trading_date, source_identity)` and an older source snapshot
  cannot overwrite a newer one.
- `GET /api/v2/stocks/{symbol}/institutional-flow` returns the formal envelope
  with `today`, session facts, four windows, four streak categories, reversal,
  price-flow context, divergence, deferred unusual-flow state, and
  liquidity-relative evidence.
- OpenAPI, the API client, generated declarations, and the web data-layer
  helper are synchronized. The web layer keeps this surface additive and
  render-only; no Stock Detail redesign was attempted.
- FUND-C may consume these facts/features as evidence. FUND-E has preserved
  market-qualified identity and source lineage compatibility but is not
  implemented.

## Governance boundaries

No composite institutional strength score, weights, thresholds, ranking,
recommendation, Today Signals policy, Opportunity policy, FUND-A policy, or
FUND-E runtime was created or changed. The existing C-drive checkout was left
untouched. Production readiness is `NO` until owner promotion, non-Production
migration execution, capture-runtime authorization, and operational readback
are separately completed.

## Validation

- Focused backend: **7 passed**.
- Full backend: **606 passed, 41 skipped, 5 registered baseline failures**.
  The five failures are pre-existing WS3 report-file availability failures in
  the isolated checkout; task-caused failures are **0**. PostgreSQL tests were
  skipped because no test database URL was configured.
- API client: **4 passed**.
- Web: **build passed; 157 tests passed**.
- Ruff, format, compileall, diff-check, conflict-marker scan, migration
  structure (`0033 -> 0032`), OpenAPI generation, and generated-client sync:
  **PASS**.
- Web lint: **0 errors, 1 existing React Hook warning** in
  `apps/web/app/components/FavoriteButton.tsx`.

## Official references

- [TWSE T86 stock institutional daily report](https://www.twse.com.tw/fund/T86?response=html)
- [TPEx major institutional detail](https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/detail/day.html)
- [TPEx official `tpex_3insti_daily_trading` OpenAPI](https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading)

## Owner handoff

The next governed action is owner review and serial canonical reconciliation.
After promotion, run migration 0033 only in the approved non-Production
environment, ingest dated TPE/TWO snapshots through a separately authorized
runtime, verify the API and freshness states, and only then decide whether a
FUND-C evidence consumer should be proposed. Do not infer abnormal-flow policy
or a composite institutional score from this packet.
