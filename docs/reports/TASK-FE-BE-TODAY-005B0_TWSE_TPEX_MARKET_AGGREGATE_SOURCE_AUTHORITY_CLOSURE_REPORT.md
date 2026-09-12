# TASK-FE-BE-TODAY-005B0｜TWSE / TPEx Market Aggregate Source Authority Closure Report

## 0. Decision summary

| Field | Result |
|---|---|
| Task | `TASK-FE-BE-TODAY-005B0` |
| Mainline | C — Today Market |
| Scope | TWSE/TPEx primary market indices, market turnover, and the Home projection boundary |
| Audit mode | Read-only repository inspection, official-source research, and this report only |
| Implementation | Not performed |
| Final status | `PARTIAL_AUTHORITY_INDEX_READY_TURNOVER_BLOCKED` |
| Index implementation can proceed | `YES_FOR_CONTRACT_AND_FIXTURE_WORK; NO_PRODUCTION_CAPTURE_UNTIL_USAGE_GATE` |
| Turnover implementation | `BLOCKED` until TPEx exact unit/currency/scale/session evidence and source-use approval are closed |
| Parallel safe with `TASK-DATA-REF-001` | `YES` for this docs-only audit and a contract-first read-only slice |

The exact official index datasets and raw field paths are now identified for
both markets. The official TWSE market turnover endpoints are also identified.
The closure is intentionally partial because the TPEx OpenAPI schema exposes
`TradeAmount` without an authoritative currency, unit, scale, or complete
included-securities/session contract, and because exchange terms do not make
technical API availability equivalent to permission to retain and redistribute
the data in a production product.

The report therefore authorizes a typed, fail-closed index contract as the next
Today slice, but does not authorize production turnover persistence or Home
publication.

## 1. CURRENT_CANONICAL_STATE

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_START_SHA=e9fc950333d7f4644cc27fa581a2e0fb40aac851
CANONICAL_FINAL_SHA=REPORT_COMMIT_SHA_PENDING
CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
OPERATIONAL_RELEASE_SHA=44dcd6054ff21a2e64d9735e057dc7b66c94b984
WORKTREE_USED=canonical repository; no new Today worktree created
FILES_MODIFIED=report only; all pre-existing user changes preserved
MODIFIED_FILES_AT_START=7
UNTRACKED_FILES_AT_START=141
```

`docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md` is not present. The available
chat handoff is dated 2026-08-13 and is stale relative to the current branch,
so the current repository, current owner documents, predecessor report
`TASK-FE-BE-TODAY-005A`, and the supplied operational truth were used together.

The current worktree already contains unrelated dirty and untracked
architecture, research, work-order, report, and runtime-adjacent files. No
blanket staging, cleanup, reset, checkout, or overwrite was performed.

The supplied operational truth remains unchanged:

```text
G0=PASS
G1=FAIL (2 markets / 0 instruments / missing instruments; TASK-DATA-REF-001 active elsewhere)
Frontend formal real data=NOT_READY
Opportunity=SHADOW
Scheduler=NOT_AUTHORIZED
```

## 2. Audit boundary and non-goals

This report covers:

- Today Market / Home modules and their current data path;
- official TWSE and TPEx API/schema/payload identity;
- raw field mapping, date semantics, grain, units, finality, correction, and lineage;
- source-family versus source-identity decisions;
- market-level persistence semantics;
- Home route mapping and `FORMAL / UNAVAILABLE / PREVIEW` behavior;
- the smallest safe follow-up implementation sequence.

This report does not perform or authorize:

- provider code changes or provider authority changes;
- database migration or Production DB mutation;
- post-close capture, scheduler activation, Canary, deploy, or push;
- Lifecycle, Opportunity, recommendation, taxonomy, relation, or topic-rule changes;
- frontend business-rule computation;
- treating existing mock, fixture, legacy snapshot, or Preview values as formal data;
- a generic market-data platform refactor;
- `NEXT_TASK` mutation.

## 3. TODAY_MARKET_MODULES

The canonical Today page is a shared Home consumer. The current route is:

```text
GET /api/v2/home
  -> build_home_read_model(session)
  -> HomeResponse.marketOverview and other Home sections
  -> today-home.ts / today-mainlines.ts
  -> TodayMarketPage.tsx
```

| Module / card | Current canonical behavior | Data authority relevant to 005B0 | Status |
|---|---|---|---|
| Market Overview | Reads Home `marketOverview`; renders status, tracked counts, and market breadth/status | `public.market_snapshots` through the Home read model; no formal index/turnover fields | Existing subset only; index/turnover missing |
| Primary index summary | No formal values rendered by canonical Today; legacy mock/snapshot helpers contain placeholder index views | Official TWSE `MI_INDEX`; official TPEx `tpex_daily_trading_index` / `tpex_index` | `C+B+E` until typed provider/persistence/read model exists |
| Turnover summary | No canonical formal turnover value rendered | TWSE `FMTQIK`; TPEx `tpex_daily_trading_index`; optional source-provided cross-market TWSE `MI_INDEX4` | `C+B+E`; TPEx unit contract blocked |
| Market breadth / status | Home `marketHealth` | `public.market_snapshots` | Existing read path; not changed here |
| Today Focus / Market Story | Reads Home `dailyFocus`; temporary/rule-based semantics remain | Existing Home/topic authority | Out of scope; preserve |
| Main Topics / Top 3 | Reads Home `mainTopics` in backend order | Existing topic snapshot/read model | Out of scope; preserve backend ordering |
| Market Events / timeline | Reads Home `marketPulse`; current semantics are temporary/topic-snapshot-derived | Existing event projection | Out of scope; preserve temporary status |
| Heating Topics | Reads Home `heatingTopics` | Existing topic rotation read model | Out of scope; preserve |
| Cooling Topics | Reads Home `coolingTopics` | Existing topic rotation read model | Out of scope; preserve |
| Opportunity teaser | Current page contains a static teaser array; backend Opportunity remains `SHADOW` | Opportunity authority is not formal | Explicitly out of scope; do not wire market aggregates into it |
| Favorites / saved summary | Not a formal signed-out Today module in the current page | Authenticated surface, if any, is separate | Out of scope |

The product design contract describes Market Overview as a compact summary of
primary indices, turnover, breadth, limits, and update time. That design intent
does not itself authorize a data source. The current Home contract deliberately
reports `marketIndices` and `turnover` as missing sections.

## 4. CURRENT_DATA_SOURCE_MATRIX

Classification:

- `A` — API/read model exists but frontend is not fully wired;
- `B` — backend capability/read model exists but route/schema is missing;
- `C` — backend authority/provider mapping is missing;
- `D` — browser hardcode or business-rule computation;
- `E` — Preview, Temporary, or Unavailable only.

| UI fact | Current source | Current backend authority / route | OpenAPI / generated client / adapter | Readiness dependency | Gap classification |
|---|---|---|---|---|---|
| Market status and breadth | `HomeMarketOverview.marketHealth` | `public.market_snapshots`; `GET /api/v2/home` | Home schema, client, and Today adapter exist | snapshot row, publication status, freshness | `A` for existing subset; parent may remain `TEMPORARY`/`UNAVAILABLE` |
| TWSE primary index | Not in canonical Home; legacy mock/snapshot surfaces only | No aggregate read model or route; current TWSE adapter returns instrument bars | No Home field/client method/typed aggregate adapter | approved source identity, typed mapping, persistence, date/as-of, post-close quality | `C+B+E` |
| TPEx primary index | Not in canonical Home; legacy mock/snapshot surfaces only | No aggregate read model or route; current TPEx adapter returns instrument bars | No Home field/client method/typed aggregate adapter | approved source identity, typed mapping, persistence, date/as-of, post-close quality | `C+B+E` |
| Index previous close | Not displayed; no browser calculation in canonical path | No backend aggregate calculation owner | No contract | same-series previous close or approved derivation | `C+B+E` |
| Index change | No formal value | No aggregate route/model | No contract | provider field or approved backend derivation | `C+B+E` |
| Index changePct | No formal value | No aggregate route/model | No contract | TWSE provider field; TPEx approved derivation or source field | `C+B+E` |
| TWSE market turnover | Not rendered formally | No market aggregate model; instrument turnover is not a market fact | No Home/client field | official field scope, TWD/元 semantics, usage approval, persistence | `C+B+E` |
| TPEx market turnover | Not rendered formally | No market aggregate model | No Home/client field | exact `TradeAmount` unit/currency/scale/session, usage approval | `C+B+E` |
| Combined TWSE + TPEx turnover | No approved frontend or backend sum | No aggregate contract | No Home/client field | use only source-provided cross-market value or approved compatible source sum | `C+D+E` |
| Loading / transport state | `today-home.ts` and `today-mainlines.ts` | Home request transport and publication classifier | Existing client transport | preserve fail-closed behavior | `A`; classification is presentation state, not market calculation |
| Preview values | `data.ts`, `data-source.ts`, snapshot adapter compatibility path | No formal provider authority | Legacy/demo types exist | explicit Preview flag and source label | `E`; never formal fallback |

## 5. EXISTING_FASTAPI_ROUTES

| Route / service | Current role | 005B0 finding |
|---|---|---|
| `GET /api/v2/home` | Shared Home read route | Existing route should be extended later with typed aggregate sections; currently no index/turnover fields |
| `GET /api/v1/meta/data-status` | Operational bundle/source/freshness metadata | Not an index/turnover authority and cannot substitute for the aggregate contract |
| `TwseOfficialDailyProvider` | Instrument-level official daily bars; `MI_INDEX` market batch is indexed to instruments | No aggregate result type; ignored market fields cannot be promoted implicitly |
| `TpexOfficialDailyProvider` | Instrument-level official daily bars; `dailyQuotes` market batch is indexed to instruments | No aggregate result type or approved turnover mapping |
| `post_close` official path | Ingests instrument observations through the canonical observation pipeline | No market aggregate capture/persistence/publication |

The current provider constants remain instrument sources:

```text
TWSE_OFFICIAL_DAILY / twse-official-daily.v2
TPEX_OFFICIAL_DAILY / tpex-official-daily.v2
```

They must not be treated as automatic authority for every aggregate field in a
payload.

## 6. MISSING_ROUTES

There is no current formal route for market index or turnover facts. No
speculative `/api/v2/market-indices` or `/api/v2/turnover` route should be added
in this authority audit.

The recommended first projection is to extend `GET /api/v2/home` with optional,
typed sections after the aggregate persistence contract exists:

```text
HomeMarketOverview.marketIndices[]
HomeMarketOverview.turnover
```

Each section must carry its own publication/data status, trading date, source,
freshness, lineage boundary, and nullability. A separate history endpoint may
be considered later only if independent history/pagination/freshness becomes a
real product requirement.

## 7. EXISTING_READ_MODELS

### 7.1 `public.market_snapshots`

The existing Home snapshot contains market/status/breadth fields such as:

```text
market, status, total_stocks, advance_count, decline_count,
unchanged_count, unavailable_count, generated_at, metadata_json
```

It does not contain index identity/value/previous close/change/changePct or
market-level turnover. It is a breadth/status projection, not the aggregate
fact authority.

### 7.2 Canonical instrument observations

`canonical_volume_observations` has typed instrument turnover fields including
`turnover_amount`, currency, scale, and aggregation code, but the row is bound
to an `instrument_id`. Reusing it for a market-level fact would lose the
aggregate grain and is not allowed.

### 7.3 Required future semantic

The future persistence semantic is:

```text
MARKET_AGGREGATE_FACT
```

It should be a governed market-level fact family, not an accidental extension
of an instrument OHLCV row. A future row should be able to preserve at least:

```text
market
metric identity
index identity when applicable
trading date
value / previous close / change / changePct
turnover amount / currency / unit / scale
session and grain
source identity and raw field path
retrievedAt and asOf
publication/data status
quality and freshness
correction/version and lineage
```

## 8. Official source evidence

Research was limited to official exchange API/schema/report/terms pages and
live read-only payloads. No blog, forum, unofficial wrapper, GitHub scraper, or
unofficial discovery source was used as authority.

### 8.1 TWSE official API family

Official Swagger: [TWSE OpenAPI](https://openapi.twse.com.tw/), base URL
`https://openapi.twse.com.tw/v1`.

Relevant official datasets:

| Dataset | Official endpoint | Raw identity / fields | Live payload evidence observed 2026-08-14 |
|---|---|---|---|
| 每日收盤行情-大盤統計資訊 | `GET /exchangeReport/MI_INDEX` | `日期`, `指數`, `收盤指數`, `漲跌`, `漲跌點數`, `漲跌百分比`, `特殊處理註記` | The row with `指數=發行量加權股價指數` returned `日期=1150813`, `收盤指數=46021.48`, `漲跌=+`, `漲跌點數=503.41`, `漲跌百分比=1.11` |
| 集中市場每日市場成交資訊 | `GET /exchangeReport/FMTQIK` | `Date`, `TradeVolume`, `TradeValue`, `Transaction`, `TAIEX`, `Change` | `Date=1150813`, `TradeValue=1104024642159`, `TAIEX=46021.48`, `Change=503.41` |
| 每日上市上櫃跨市場成交資訊 | `GET /exchangeReport/MI_INDEX4` | `Date`, `TradeValue`, `FormosaIndex`, `Change` | `Date=1150813`, `TradeValue=1359928852245`, `FormosaIndex=51102.16`, `Change=555.99` |

The official TWSE reports identify the TWSE market amount as `成交金額` and
the cross-market amount as `成交金額(元)`. The report notes state that daily
statistics include the main market, odd-lot, after-hours fixed-price, and
block trades, exclude auction and tender transactions, and convert foreign
currency transaction value using the exchange's published rate. See the
[TWSE FMTQIK report](https://www.twse.com.tw/exchangeReport/FMTQIK?date=&response=html)
and [TWSE MI_INDEX4 report](https://www.twse.com.tw/exchangeReport/MI_INDEX4?response=html).

### 8.2 TPEx official API family

Official Swagger: [TPEx OpenAPI](https://www.tpex.org.tw/openapi/), schema
`https://www.tpex.org.tw/openapi/swagger.json`, base URL
`https://www.tpex.org.tw/openapi/v1`.

Relevant official datasets:

| Dataset | Official endpoint | Raw identity / fields | Live payload evidence observed 2026-08-14 |
|---|---|---|---|
| 櫃買指數歷史資料 | `GET /tpex_index` | `Date`, `Open`, `High`, `Low`, `Close`, `Change` | `Date=20260814`, `Close=400.95`, `Change=-5.17` |
| 上櫃日成交量值指數 | `GET /tpex_daily_trading_index` | `Date`, `TradeVolume`, `TradeAmount`, `NumberOfTransactions`, `TPExIndex`, `Change` | `Date=1150814`, `TradeAmount=237372937110`, `TPExIndex=400.95`, `Change=-5.17` |
| 上櫃股票市場現況 | `GET /tpex_mainborad_highlight` | `Date`, `DailyTradingValue`, `CloseIndex`, `IndexChange`, breadth fields | Useful cross-check only; `DailyTradingValue` unit is not explicit in the API schema |

The official TPEx index description identifies the broad series as the TPEx
Exchange Capitalization Weighted Stock Index, commonly `櫃買指數` / `TPEX`.
See [TPEx index introduction](https://wwwov.tpex.org.tw/web/stock/iNdex_info/manual/introduction.php?l=zh-tw).

The API schema gives `TradeAmount` as a field name but does not declare its
currency, unit, scale, included securities, or exact exclusion/session policy.
The official market page supplies useful context about displayed turnover but
is not sufficient to promote the API field into a persisted canonical unit
contract. An official TPEx format document found during research describes
`成交金額` in a different after-hours file as `萬元`; that document is not the
OpenAPI schema for `tpex_daily_trading_index` and must not be transplanted into
this contract by inference.

### 8.3 Retention and usage boundary

Technical endpoint availability is not treated as production retention or
redistribution approval.

- TWSE terms restrict automated downloads/scripts/crawlers unless the exchange
  has provided consent or an approved method; see [TWSE Terms of Use](https://www.twse.com.tw/zh/terms/use.html).
- TWSE information-use material points users to information-use rules,
  agreements, and charges; see [TWSE information use](https://www.twse.com.tw/zh/products/information/use.html).
- TPEx lists external after-hours API use at `NT$0/month`, but the product page
  still points to use terms; see [TPEx after-hours API explanation](https://eshop.tpex.org.tw/zh/product/detail/2c92e01394fcf4c7019518bbf65f000a).
- TPEx member terms restrict internal versus external use, require source
  disclosure for external information users, and prohibit reproduction,
  transmission, or distribution without written authorization; see [TPEx member purchase terms](https://eshop.tpex.org.tw/zh/product/shoppingTerm).

Therefore a source registry entry must include an explicit legal/usage review
state before production persistence, public Home projection, or data retention
is declared formal.

## 9. TWSE_INDEX_AUTHORITY

```text
INDEX_IDENTITY=TWSE:TAIEX (proposed internal canonical namespace)
SOURCE_PROVIDER=TWSE
SOURCE_DATASET=每日收盤行情-大盤統計資訊 / exchangeReport.MI_INDEX
SOURCE_ENDPOINT=GET https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX
SOURCE_IDENTITY=TWSE_OPENAPI_MI_INDEX (proposed registry identity)
RAW_INDEX_CODE=NOT_PROVIDED; select exact raw row where 指數 == 發行量加權股價指數
RAW_INDEX_NAME=發行量加權股價指數
TRADING_DATE_FIELD=日期 (ROC YYYMMDD)
VALUE_FIELD=收盤指數
PREVIOUS_CLOSE_FIELD=NOT_PROVIDED
CHANGE_FIELD=漲跌 + 漲跌點數 (sign and magnitude are separate raw fields)
CHANGE_PCT_FIELD=漲跌百分比
FINALITY=DAILY_RESPONSE_WITHOUT_EXPLICIT_FINAL_FLAG
CORRECTION=API_SCHEMA_HAS_NO_REVISION_FLAG; endpoint overwrite/content changes must be detected and stored as a superseding version
LINEAGE=TWSE -> MI_INDEX -> exact raw index-name selector -> TopicPilot market aggregate fact -> Home projection
AUTHORITY_STATUS=READY_FOR_EXACT_INDEX_CONTRACT; PRODUCTION_RETENTION_REQUIRES_USAGE_APPROVAL
```

`previousClose` is not an official field in this response. If the product
contract requires it, the backend may derive it only from the same series and
the signed provider change:

```text
signedChange = sign(漲跌) * 漲跌點數
previousClose = 收盤指數 - signedChange
```

The derivation must be versioned, decimal-safe, and null when either input is
missing or invalid. React must not derive it. `changePct` remains provider-first
from `漲跌百分比`; a backend formula is not a substitute when the provider field
exists.

## 10. TPEX_INDEX_AUTHORITY

```text
INDEX_IDENTITY=TPEX:TPEx (proposed internal canonical namespace)
SOURCE_PROVIDER=TPEx
SOURCE_DATASET=上櫃日成交量值指數 / tpex_daily_trading_index
SOURCE_ENDPOINT=GET https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index
SOURCE_IDENTITY=TPEX_OPENAPI_DAILY_TRADING_INDEX (proposed registry identity)
RAW_INDEX_CODE=NOT_PROVIDED; dataset identity is the official broad TPEx index series
RAW_INDEX_NAME=櫃買指數 / TPEx Exchange Capitalization Weighted Stock Index
TRADING_DATE_FIELD=Date (ROC YYYMMDD in this endpoint)
VALUE_FIELD=TPExIndex
PREVIOUS_CLOSE_FIELD=NOT_PROVIDED
CHANGE_FIELD=Change
CHANGE_PCT_FIELD=NOT_PROVIDED
FINALITY=DAILY_RESPONSE_WITHOUT_EXPLICIT_FINAL_FLAG
CORRECTION=API_SCHEMA_HAS_NO_REVISION_FLAG; endpoint overwrite/content changes must be detected and stored as a superseding version
LINEAGE=TPEx -> tpex_daily_trading_index -> TPExIndex -> TopicPilot market aggregate fact -> Home projection
AUTHORITY_STATUS=READY_FOR_EXACT_INDEX_CONTRACT; PRODUCTION_RETENTION_REQUIRES_USAGE_APPROVAL
```

The `tpex_index` endpoint is an official same-series cross-check and historical
source:

```text
TPEX_INDEX_CROSSCHECK_ENDPOINT=GET https://www.tpex.org.tw/openapi/v1/tpex_index
TPEX_INDEX_CROSSCHECK_DATE=Date (Gregorian YYYYMMDD)
TPEX_INDEX_CROSSCHECK_VALUE=Close
TPEX_INDEX_CROSSCHECK_CHANGE=Change
```

The different date encodings are contract-significant. The adapter must
preserve the raw provider date and normalize to exchange-local
`tradingDate` (`Asia/Taipei`) without using browser local time.

`previousClose` may be derived only from `TPExIndex - Change` after approval of
the same-series derivation and precision policy. `changePct` is not supplied by
the selected daily endpoint and must remain null until an exact official field
or an approved backend derivation exists. The frontend must never calculate it.

## 11. TWSE_TURNOVER_AUTHORITY

```text
SOURCE_PROVIDER=TWSE
SOURCE_DATASET=集中市場每日市場成交資訊 / exchangeReport.FMTQIK
SOURCE_ENDPOINT=GET https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK
SOURCE_IDENTITY=TWSE_OPENAPI_FMTQIK (proposed registry identity)
RAW_FIELD=TradeValue
GRAIN=TWSE/TPE daily market aggregate, source-provided; not an instrument sum
INCLUDED_SECURITIES=Exchange-defined daily statistics: includes main market, odd-lot, after-hours fixed-price, and block trades; excludes auction and tender transactions per official report note
SESSION=Official daily/post-close market summary as published by TWSE
CURRENCY=TWD/NTD (official report converts foreign-currency transaction value using the exchange-published rate; canonical code still requires owner approval)
UNIT=元
SCALE=0 (whole currency units as published)
TRADING_DATE=Date (ROC YYYMMDD)
FINALITY=DAILY_RESPONSE_WITHOUT_EXPLICIT_FINAL_FLAG
CORRECTION=API_SCHEMA_HAS_NO_REVISION_FLAG; detect content changes and supersede rather than silently overwrite
LINEAGE=TWSE -> FMTQIK.TradeValue -> TopicPilot market aggregate fact -> Home projection
AUTHORITY_STATUS=TECHNICALLY_READY; PRODUCTION_RETENTION/PUBLICATION_REQUIRES_USAGE_APPROVAL
```

This is the correct TWSE-market turnover candidate. The current
`TWSE_OFFICIAL_DAILY` instrument provider must not silently absorb `TradeValue`
into `HistoricalBar`; a separate aggregate result type and source identity are
required.

## 12. TPEX_TURNOVER_AUTHORITY

```text
SOURCE_PROVIDER=TPEx
SOURCE_DATASET=上櫃日成交量值指數 / tpex_daily_trading_index
SOURCE_ENDPOINT=GET https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index
SOURCE_IDENTITY=TPEX_OPENAPI_DAILY_TRADING_INDEX (same official response as selected index source)
RAW_FIELD=TradeAmount
GRAIN=TPEx daily market aggregate candidate; exact source grain requires confirmation
INCLUDED_SECURITIES=NOT_EXPLICIT_IN_OPENAPI_SCHEMA
SESSION=NOT_EXPLICIT_IN_OPENAPI_SCHEMA
CURRENCY=NOT_PROVIDED_BY_OPENAPI_SCHEMA
UNIT=NOT_PROVIDED_BY_OPENAPI_SCHEMA
SCALE=NOT_PROVIDED_BY_OPENAPI_SCHEMA
TRADING_DATE=Date (ROC YYYMMDD)
FINALITY=DAILY_RESPONSE_WITHOUT_EXPLICIT_FINAL_FLAG
CORRECTION=API_SCHEMA_HAS_NO_REVISION_FLAG; correction policy cannot be formalized until source terms/metadata are confirmed
LINEAGE=TPEx -> tpex_daily_trading_index.TradeAmount -> TopicPilot market aggregate fact -> Home projection (proposed only)
AUTHORITY_STATUS=BLOCKED_PENDING_EXACT_UNIT_CURRENCY_SCALE_GRAIN_SESSION_AND_USAGE_CONFIRMATION
```

The live value is technically present and looks like a whole-currency amount,
but magnitude or a neighboring TPEx file is not authority for the OpenAPI
field's unit. The API response must not be persisted with an invented `TWD`,
`元`, or scale value. `tpex_mainborad_highlight.DailyTradingValue` is not a safe
fallback because its API schema also does not state the unit and it represents
a different dataset shape.

## 13. Combined turnover decision

TWSE also publishes an official cross-market dataset:

```text
SOURCE_PROVIDER=TWSE
SOURCE_DATASET=每日上市上櫃跨市場成交資訊 / exchangeReport.MI_INDEX4
SOURCE_ENDPOINT=GET https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX4
RAW_FIELD=TradeValue
RAW_UNIT=成交金額(元)
GRAIN=source-provided TWSE + TPEx cross-market daily aggregate
TRADING_DATE=Date (ROC YYYMMDD)
```

This is the preferred combined-turnover candidate when the product needs one
cross-market value. It must be treated as a source-provided aggregate, not as
`TWSE TradeValue + TPEx TradeAmount`. The two per-market values may only be
combined by backend logic after same-date, same-session, same-currency,
same-unit, same-scale, and source-quality checks are formally approved.

## 14. Contract decisions

```text
EXISTING_PROVIDER_FAMILY_EXTENDABLE=YES at exchange-family/lifecycle level; existing instrument result type is not reusable
NEW_SOURCE_IDENTITY_REQUIRED=YES
PROPOSED_TWSE_AGGREGATE_SOURCE_IDENTITY=TWSE_OFFICIAL_MARKET_AGGREGATE
PROPOSED_TPEX_AGGREGATE_SOURCE_IDENTITY=TPEX_OFFICIAL_MARKET_AGGREGATE
PROPOSED_TWSE_ADAPTER_VERSION=twse-official-market-aggregate.v1
PROPOSED_TPEX_ADAPTER_VERSION=tpex-official-market-aggregate.v1

INDEX_CHANGE_OWNER=official provider when present; backend only for explicitly approved same-series derivation
INDEX_CHANGE_PCT_OWNER=official provider when present; TPEx remains NULL until exact field or approved backend derivation

MARKET_AGGREGATE_PERSISTENCE_SEMANTIC=MARKET_AGGREGATE_FACT
INSTRUMENT_CANONICAL_TABLE_REUSE_ALLOWED=NO

HOME_ROUTE_DECISION=extend GET /api/v2/home with typed optional aggregate sections after persistence exists
NEW_ENDPOINT_REQUIRED=NO for the first Today slice

COMBINED_TURNOVER_ALLOWED=YES only from official MI_INDEX4 source-provided cross-market value, or later after a formally approved compatible sum
COMBINED_TURNOVER_OWNER=backend/source authority; never React

CLOSED_DATE_SEMANTICS=closed/no trading row is UNAVAILABLE for that section, not zero and not last-known-as-today
NO_DATA_SEMANTICS=UNAVAILABLE with reason and null values
PROVIDER_ERROR_SEMANTICS=UNAVAILABLE; no Preview fallback unless explicit Preview mode is enabled
STALE_SEMANTICS=UNAVAILABLE for formal publication unless a separate approved stale contract exists
NULL_SEMANTICS=preserve null when source field is absent/invalid; do not coerce null to 0
```

The existing family can share transport, exchange-local time, retry, and
lineage conventions, but the aggregate dataset, grain, response identity,
correction lifecycle, and typed result boundary are distinct from
instrument-level `HistoricalBar`.

## 15. Date, as-of, finality, correction, and lineage contract

### 15.1 Date semantics

```text
tradingDate=exchange-local trading date normalized to ISO date
dataDate=Home publication/evaluation date; normally equals tradingDate for a post-close section
retrievedAt=TopicPilot retrieval timestamp in Asia/Taipei-aware UTC representation
asOf=source response/capture boundary; never invented from browser time
```

The raw ROC date must be preserved for TWSE and the selected TPEx daily
endpoint. The TPEx historical cross-check uses Gregorian dates and must not be
joined by string equality without normalization.

### 15.2 Finality

Neither selected OpenAPI schema exposes an explicit `final`, `provisional`, or
`revision` field. The formal model must therefore use:

```text
sourcePublication=DAILY_RESPONSE_AS_PUBLISHED
finality=NOT_EXPLICITLY_DECLARED_BY_SOURCE
productionFormal=only after approved post-close/source-use policy
```

An HTTP 200 response is not itself proof of finality.

### 15.3 Correction and idempotency

The source schemas do not document a revision identifier. The future adapter
must retain response identity and content evidence, detect a changed payload,
and write a superseding version rather than silently mutating an existing
canonical fact.

```text
CORRECTION_SUPPORTED_BY_SOURCE=not explicitly documented
CORRECTION_DETECTION_REQUIRED=YES; compare raw response/content hash for the same source/date/metric
IDEMPOTENCY_KEY_CANDIDATE=sourceIdentity + providerDate + metricIdentity + schemaVersion
REVISION_KEY_CANDIDATE=above key + responseContentHash
RETRIEVAL_RETRY_IMPACT=retry may replace a same-day source response; never downgrade a valid fact without a superseding lineage record
```

These are contract recommendations only; no persistence or correction code was
implemented in this task.

### 15.4 Lineage

Every future aggregate fact must preserve:

```text
exchange/provider
dataset and endpoint
schema/adapter version
raw provider date
raw index selector or field path
retrievedAt
asOf/publication boundary
response status and content evidence
source-use authorization state
```

## 16. API_CONTRACT_GAPS

| Gap | Impact | Required closure |
|---|---|---|
| No aggregate source registry entries | Cannot distinguish instrument and market authority | Register separate TWSE/TPEx aggregate identities and adapter versions |
| TPEx `TradeAmount` unit/currency/scale absent | Cannot safely persist or display turnover | Official TPEx schema/format confirmation or written source-owner confirmation |
| TPEx aggregate inclusion/session absent | Per-market and combined values may be incomparable | Exact dataset scope and exclusions from TPEx authority |
| No explicit finality/revision field | Cannot claim immutable post-close fact | Source policy plus content-hash/superseding correction contract |
| Previous close absent in both selected index payloads | Backend derivation needs policy and precision | Approve same-series derivation; retain null on missing/invalid inputs |
| TPEx changePct absent | Browser calculation would violate authority boundary | Keep null or approve a backend formula with same-series prior close |
| No aggregate persistence model | Current canonical tables are instrument-bound or breadth-only | Introduce a minimal `MARKET_AGGREGATE_FACT` persistence boundary |
| Home schema/client fields absent | Frontend cannot consume formal aggregate data | Extend `HomeMarketOverview` and regenerate client after backend contract exists |
| Exchange usage/retention terms not recorded in registry | API availability could be mistaken for redistribution permission | Add approval state and retention/use notes to source registry |

## 17. FORMAL_UNAVAILABLE_PREVIEW_STATE_PLAN

### `FORMAL`

Use only when all of the following are true:

- source identity is registered and approved for the intended use;
- response is from the official endpoint and matches the expected schema/version;
- raw trading date matches the requested publication date after normalization;
- required source fields are present, numeric, and semantically valid;
- index identity, turnover grain, unit/currency/scale, and session are validated;
- correction/content evidence is recorded;
- post-close publication and freshness policy passes;
- the upstream data gates allow formal publication.

### `UNAVAILABLE`

Use for weekend/holiday/no-trade, empty response, invalid date, provider
failure, partial/incomplete response, stale response, missing required field,
unapproved retention/use, or unresolved TPEx turnover semantics. Show a clear
section reason and preserve null values. Do not render `0`, last-known data as
today's formal value, or a fabricated change percentage.

### `PREVIEW`

Use only with an explicit Preview flag and an explicitly labelled fixture,
synthetic, or development source. Preview values must carry source/status
metadata and must never be used as a formal fallback after a provider error.

The current frontend publication classifier may continue to classify transport
and publication metadata, but it must not calculate index/turnover business
facts.

## 18. FRONTEND_MOCKS/LOCAL_COMPUTATION

The following surfaces were found and remain non-formal:

| File / symbol | Current behavior | Required boundary |
|---|---|---|
| `apps/web/app/data.ts:marketIndices` | Demo index objects | Preview/demo only; never formal fallback |
| `apps/web/app/lib/data-source.ts:mockMarketIndexViews` | Mock Home/snapshot compatibility data | Keep isolated from formal Home path |
| `apps/web/app/lib/snapshot-adapter.ts:toMarketIndexViews`, `indexStance`, `INDEX_SLOTS` | Legacy snapshot-to-index view mapping and display stance | Do not promote to source authority; remove from formal path in a later focused task |
| `apps/web/app/components/v2/TodayMarketPage.tsx:opportunities` | Static opportunity teaser array | Out of scope; Opportunity remains `SHADOW` |
| `apps/web/app/components/v2/TodayMarketPage.tsx:OverviewValue` | Number formatting only | Allowed presentation responsibility |
| `apps/web/app/lib/today-home.ts` and `today-mainlines.ts` | Loading/publication-state classification | Allowed state mapping; no market metric derivation |

Forbidden in the formal path:

```text
browser-derived change
browser-derived changePct
browser sum of TWSE + TPEx turnover
browser-inferred index identity from display text
mock fallback on provider error
null -> 0 coercion
freshness inferred from browser clock without backend metadata
```

## 19. VERTICAL_SLICE_RECOMMENDATION

Because the outcome is partial, the smallest safe vertical slice is
**index-only, contract-first, and fail-closed**:

```text
TODAY-005B-INDEX-CONTRACT-SLICE
  official source fixtures for TWSE MI_INDEX and TPEx daily trading index
  typed aggregate result boundary, separate from HistoricalBar
  exact date/field parsing tests, including missing-field/null cases
  backend-only previous-close derivation tests where approved
  Home extension design for marketIndices only
  FORMAL / UNAVAILABLE / PREVIEW contract tests
```

This slice may be developed in isolation and validated against fixtures. It
must not perform Production capture or Home formal publication until the
source-use approval gate is closed. It must not add or wire turnover fields
while TPEx `TradeAmount` remains unresolved.

Minimum acceptance criteria for the eventual first formal Today slice:

1. one official TWSE index row and one official TPEx index row are mapped to a
   typed aggregate result with raw field paths and normalized trading dates;
2. missing/invalid response fields yield `UNAVAILABLE`, not zero;
3. the Home response exposes an explicit `marketIndices` section with source,
   date, as-of, freshness, and status metadata;
4. Today renders `FORMAL` only for an approved, complete response and renders a
   clear `UNAVAILABLE` state when G1/upstream data is not ready;
5. Preview fixtures are available only under explicit Preview mode;
6. no React ranking, change, percentage, turnover sum, or identity inference is
   introduced.

## 20. IMPLEMENTATION_PHASES

| Phase | Scope | Gate |
|---|---|---|
| 0 — authority closure | This report; exact official endpoint/field evidence; unresolved TPEx turnover and usage items recorded | Complete as partial |
| 1 — index provider contract | Register distinct aggregate identities, add typed index result, fixture/parser tests, and date/null semantics | Contract review; no Production write |
| 2 — index persistence | Add minimal market aggregate fact persistence for indices only | Approved schema, migration review, source-use approval |
| 3 — post-close index capture | Capture official index facts with lineage, idempotency, and correction evidence | G1/upstream readiness and post-close authorization |
| 4 — Home/API projection | Extend `HomeMarketOverview` and `GET /api/v2/home`; regenerate OpenAPI/client | Backend contract and focused API tests |
| 5 — Today formal rendering | Render index cards with explicit `FORMAL / UNAVAILABLE / PREVIEW` states | Frontend contract/tests; no browser calculations |
| 6 — turnover authority closure | Resolve TPEx unit/currency/scale/grain/session and usage terms; then add turnover contract | Must be a separate authority gate |
| 7 — turnover persistence/projection | Add TWSE/TPEx per-market turnover and optional source-provided combined turnover | Same-date/source-quality checks; no React sum |

No phase above was executed in this task.

## 21. Readiness matrix

| Fact | TWSE | TPEx | Authority result | Ready for next implementation? |
|---|---|---|---|---|
| Index identity | Exact raw selector `指數=發行量加權股價指數` | Official `櫃買指數` / `TPExIndex` series | Source mapping ready | Yes, contract-only |
| Trading date | `日期` ROC | `Date` ROC on selected daily endpoint; Gregorian on cross-check | Normalization defined | Yes, tests first |
| Index value | `收盤指數` | `TPExIndex` or `Close` cross-check | Exact field available | Yes, contract-only |
| Previous close | Not provided; derivation candidate | Not provided; derivation candidate | Backend-only derivation required | Conditional |
| Change | `漲跌` + `漲跌點數` | `Change` | Exact provider field available | Yes, contract-only |
| ChangePct | `漲跌百分比` | Not provided | TPEx remains null/blocked | TWSE yes; TPEx no |
| Turnover | `FMTQIK.TradeValue` | `tpex_daily_trading_index.TradeAmount` | TWSE technical source ready; TPEx semantics incomplete | TWSE conditional; TPEx no |
| Currency | TWD/NTD after official conversion note | Not explicit in API schema | TPEx blocked | No formal turnover publication |
| Unit/scale | 元 / 0 | Not explicit in API schema | TPEx blocked | No formal turnover publication |
| Session/grain | Official daily market summary | Not explicit enough for exact contract | TPEx blocked | No formal turnover publication |
| Finality | No explicit flag | No explicit flag | Source policy required | No production claim |
| Correction | No explicit revision field | No explicit revision field | Superseding content evidence required | No production claim |
| Lineage | Endpoint/field/date available | Endpoint/field/date available | Ready as proposed metadata | Contract-only |

## 22. Provider authority decision

```text
EXISTING_PROVIDER_FAMILY_EXTENDABLE=YES
NEW_AGGREGATE_SOURCE_IDENTITY_REQUIRED=YES
```

The exchange provider family may share transport and lifecycle infrastructure,
but the current instrument identities remain unchanged:

```text
TWSE_OFFICIAL_DAILY != TWSE_OFFICIAL_MARKET_AGGREGATE
TPEX_OFFICIAL_DAILY != TPEX_OFFICIAL_MARKET_AGGREGATE
```

The aggregate result must not be represented as an instrument `HistoricalBar`
and must not be silently parsed from ignored instrument-batch fields.

## 23. Documentation report

```text
ROADMAP_UPDATED=N/A (report-only; existing dirty owner-doc workstream preserved)
PROJECT_CONTEXT_UPDATED=N/A (report-only; existing dirty owner-doc workstream preserved)
PRODUCT_ROADMAP_UPDATED=N/A
DOCUMENTATION_INDEX_UPDATED=N/A
DAILY_PROGRESS_UPDATED=N/A
NEW_REPORT=docs/reports/TASK-FE-BE-TODAY-005B0_TWSE_TPEX_MARKET_AGGREGATE_SOURCE_AUTHORITY_CLOSURE_REPORT.md
```

This report is the execution evidence for 005B0. Owner-document edits were not
mixed into the existing dirty Mainline A/topic workstream. The next Today
implementation work should link this report and preserve the explicit
turnover blocker rather than replacing it with a speculative route or field.

## 24. Safety report

```text
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO

HISTORICAL_CHANGED=NO
STOCK_CHANGED=NO
TOPIC_CHANGED=NO
TAXONOMY_CHANGED=NO
RELATIONS_CHANGED=NO
OPPORTUNITY_CHANGED=NO
RECOMMENDATION_CHANGED=NO

G0=PRESERVED PASS
G1=PRESERVED FAIL (2 markets / 0 instruments / missing instruments)
G2=NOT RUN / UNCHANGED
G3=NOT RUN / UNCHANGED
POST_CLOSE_CANARY=NOT RUN / UNCHANGED
```

No protected data boundary was changed. The gate values above were not
re-run or advanced by this docs-only task.

## 25. Required output fields

```text
TODAY_MARKET_MODULES=DOCUMENTED
CURRENT_DATA_SOURCE_MATRIX=DOCUMENTED
EXISTING_FASTAPI_ROUTES=DOCUMENTED
MISSING_ROUTES=DOCUMENTED
EXISTING_READ_MODELS=DOCUMENTED
FRONTEND_MOCKS/LOCAL_COMPUTATION=DOCUMENTED
FORMAL_UNAVAILABLE_PREVIEW_STATE_PLAN=DOCUMENTED
API_CONTRACT_GAPS=DOCUMENTED
VERTICAL_SLICE_RECOMMENDATION=TODAY-005B-INDEX-CONTRACT-SLICE
IMPLEMENTATION_PHASES=DOCUMENTED
PARALLEL_SAFE_WITH_DATA_REF_001=YES
FILES_MODIFIED=REPORT_ONLY
NEW_REPORT=docs/reports/TASK-FE-BE-TODAY-005B0_TWSE_TPEX_MARKET_AGGREGATE_SOURCE_AUTHORITY_CLOSURE_REPORT.md
COMMIT_SHA=COMMIT_SHA_PENDING
FINAL_STATUS=PARTIAL_AUTHORITY_INDEX_READY_TURNOVER_BLOCKED
```

### Blocking evidence for the turnover half

```text
BLOCKING_SOURCE=TPEX_OPENAPI_DAILY_TRADING_INDEX
BLOCKING_FIELD=TradeAmount
BLOCKING_SEMANTIC=currency/unit/scale/included-securities/session not explicit in the selected OpenAPI contract; retention/redistribution approval also pending
REQUIRED_EVIDENCE=official TPEx field metadata or written source-owner confirmation plus approved production-use/retention terms
```

### Authority handoff

```text
INDEX_IMPLEMENTATION_CAN_PROCEED=YES_FOR_CONTRACT_AND_FIXTURE_WORK
INDEX_PRODUCTION_CAPTURE=BLOCKED_PENDING_SOURCE_USE_APPROVAL_AND_UPSTREAM_GATES
TWSE_TURNOVER_IMPLEMENTATION=BLOCKED_FROM_PRODUCTION_PUBLICATION_PENDING_SOURCE_USE_APPROVAL
TPEX_TURNOVER_IMPLEMENTATION=BLOCKED_PENDING_EXACT_SEMANTICS_AND_SOURCE_USE_APPROVAL
NEXT_TODAY_SLICE=TODAY-005B-INDEX-CONTRACT-SLICE
```
