# FUND-A provider provenance and live discovery

## Official sources

- TWSE daily institutional cash-value summary: `https://www.twse.com.tw/rwd/zh/fund/BFI82U`
- TWSE human-facing page: `https://www.twse.com.tw/fund/BFI82U?response=html&type=day`
- TPEx official OpenAPI specification: `https://www.tpex.org.tw/openapi/swagger.json`
- TPEx daily institutional summary page: `https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/summary/day.html`
- TPEx endpoint: `https://www.tpex.org.tw/openapi/v1/tpex_3insti_summary`

## Verified semantics

On 2026-09-16, read-only requests were made to the public endpoints for the
2026-09-15 session. TWSE returned `stat=OK`, date `20260915`, fields for
buy/sell/net amounts, and an explicit whole-yuan hint. TPEx returned ROC date
`1150915` and the expected investor rows. Both payloads were independently
reconciled by the parser contract.

The TPE adapter maps TWSE's foreign row excluding foreign proprietary accounts,
investment trust, and the sum of dealer self/hedge rows. The TWO adapter maps
TPEx's foreign row excluding proprietary accounts when present, investment
trust, dealer total, and the three-institution total. In both cases:

`net = buy - sell`

and the total must equal foreign + investment trust + dealer. Raw amounts are
stored as `Numeric(38, 0)` with `unit=TWD` and `scale=0`.

The public responses did not provide a publication timestamp. Therefore the
contract records `published_at=NULL` unless a future authoritative field is
available, and records the adapter retrieval timestamp as `retrieved_at` and
the capture timestamp as `source_as_of` when supplied. This avoids inventing a
provider freshness time.

## Historical/backfill boundary

The public adapters are daily capture adapters. The TPEx endpoint is used as a
current summary endpoint; no undocumented historical query behavior is assumed.
Backfill, if separately authorized, must use the same contract and provenance
fields per session. No historical rows or Production data were written in this
task.
