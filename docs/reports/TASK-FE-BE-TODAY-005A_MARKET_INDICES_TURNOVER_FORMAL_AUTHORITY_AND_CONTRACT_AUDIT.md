# TASK-FE-BE-TODAY-005A — Market Indices & Turnover Formal Authority / Contract Audit

## 0. Decision and audit boundary

| Field | Result |
|---|---|
| Task | `TASK-FE-BE-TODAY-005A` |
| Mainline | C — Today |
| Canonical repository | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Canonical branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Canonical start SHA | `bd0cabfde20a1e950737cc6ba17ee442036d0121` |
| `origin/main` observed | `26f635b95d8d88fd7ed7e43949583347f3ab5feb` |
| Audit mode | Read-only repository inspection plus this report only |
| Production mutation / deploy / push | `NO` |
| Scheduler / Canary / `NEXT_TASK` | `NO` |
| Final status | `BLOCKED_PENDING_MARKET_DATA_SOURCE_AUTHORITY` |

The canonical worktree already contains unrelated documentation, architecture,
research-fixture, and runtime-adjacent dirty/untracked changes. They were not
cleaned, rewritten, or staged. No Today worktree collision was found that
requires a new worktree for this audit. This report is the only intended file
addition for 005A.

The audit used the current canonical files, not an older Today branch or an
older handoff as authority. Current owner documents and current code remain
authoritative.

## 1. Current authority summary

The current Today runtime is the shared read-only Home path:

```text
GET /api/v2/home
  -> build_home_read_model(session)
  -> HomeResponse.marketOverview
  -> TodayHomeResource / TodayMainlinesResource
  -> TodayMarketPage.tsx
```

The current `HomeMarketOverview` contract contains:

```text
dataDate, updatedAt, dataStatus, trackedStockCount, trackedTopicCount,
latestSnapshotTime, marketHealth, source
```

`marketHealth` contains `market`, `status`, `totalStocks`, `advance`,
`decline`, `flat`, and `unavailable`. The current Home read model deliberately
reports `marketIndices` and `turnover` in `dataQuality.missingSections`.

The current official source boundary is narrower than the requested feature:

| Existing authority | What is formally supported now | What is not supported now |
|---|---|---|
| `TWSE_OFFICIAL_DAILY` / `twse-official-daily.v2` | TPE instrument daily OHLCV; one-date `MI_INDEX` market-batch payload indexed by instrument code | A formal TWSE index series or market aggregate turnover contract |
| `TPEX_OFFICIAL_DAILY` / `tpex-official-daily.v2` | TWO instrument daily OHLCV; one-date `dailyQuotes` market-batch payload indexed by instrument code | A formal TPEx index series or market aggregate turnover contract |
| `canonical_volume_observations.turnover_amount` | Generic typed turnover field for an instrument canonical observation | A market-level aggregate projection, source mapping, identity, or Home read contract |
| `public.market_snapshots` | Daily market breadth/status counts used by Home | Index values, index change, index change percentage, turnover amount, or index identity |

The official exchange family is known, but the exact aggregate source authority
and field mapping for the two requested metric families are not currently
registered or implemented. It is unsafe to infer that the existing instrument
source code automatically authorizes every value in the provider payload.

## 2. TODAY_MARKET_MODULES

Current `apps/web/app/components/v2/TodayMarketPage.tsx` modules and the
design-contract modules relevant to this audit are:

| Order | UI module / card | Current canonical implementation | 005A relevance |
|---:|---|---|---|
| 1 | Market Overview | Reads shared Home `marketOverview`; renders status, tracked counts, and existing `marketHealth` only | Primary target. Formal index and turnover fields are absent |
| 2 | Today Focus / Market Story | Reads shared Home `dailyFocus`; backend labels it rule-based/temporary | Out of scope; preserve temporary semantics |
| 3 | Today Main Topics / Top 3 | Reads `HomeResponse.mainTopics` in backend order | Out of scope; no browser ranking |
| 4 | Market Events / timeline | Reads `HomeResponse.marketPulse`; current source is topic-snapshot-derived/temporary | Out of scope; no event authority change |
| 5 | Heating Topics | Reads `HomeResponse.heatingTopics` | Out of scope; no rotation rule change |
| 6 | Cooling Topics | Reads `HomeResponse.coolingTopics` | Out of scope; no rotation rule change |
| 7 | Opportunity teaser | Current page still contains a static teaser array; backend Opportunity remains SHADOW and is not formal | Explicitly out of scope; do not alter Opportunity rules |
| 8 | Favorites / saved summary | Not rendered as a formal Today module in the current signed-out page | No auth/read-model change in 005A |

The frozen frontend design specifies Market Overview as a compact summary of
primary index values, turnover, breadth, limit counts, and update time. The
current Home contract covers only the status/breadth subset, so design intent
does not constitute data authority.

## 3. CURRENT_DATA_SOURCE_MATRIX

Classification: `A` API exists but is not fully wired; `B` backend capability
exists but route/schema is missing; `C` backend authority/provider mapping is
missing; `D` browser hardcode or business-rule computation; `E` Preview,
Temporary, or Unavailable only.

| Module / fact | Current source and behavior | Backend authority / route | OpenAPI / client / adapter | Readiness dependency | Gap |
|---|---|---|---|---|---|
| Market health / breadth subset | Home `marketOverview.marketHealth`; nullable counts/status | `public.market_snapshots` via `build_home_read_model`; `GET /api/v2/home` | Typed Home schema and shared adapter exist | Completed run, market snapshot row, publication status | `A` for existing fields; parent remains `TEMPORARY`/`UNAVAILABLE` when not formal |
| TWSE primary index | Not rendered by current Today; legacy snapshot/mock surfaces contain placeholder index views | No formal index read model or route; TWSE adapter returns instrument bars | No `marketIndices` in Home; no client method; no formal Today adapter | Official index identity, mapping, persistence, date/as-of/freshness | `C+B+E`; display label is not identity |
| TPEx / OTC index | Same as TWSE index | No formal index read model or route | No typed field or client method | Same as TWSE | `C+B+E` |
| Index value / previous close / change / changePct | No formal value or calculation owner | No provider-neutral aggregate contract | Absent from OpenAPI and generated declarations | Official raw fields or approved backend derivation | `C+D+E` |
| Market turnover by market | Not rendered by canonical Today; legacy/mock compatibility data may contain placeholders | Generic canonical turnover is instrument-level; no market aggregate read model | Absent from Home/OpenAPI/client | Official per-market semantics, unit/currency/scale, grain, lineage | `C+B+E` |
| Combined TWSE + TPEx turnover | No formal source or approved sum | No backend aggregate contract | Absent | Same date, currency, unit, session, and approved aggregation policy | `C+D+E` |
| Daily Focus / Story | Shared Home; backend marks `RULE_BASED` and temporary | `HomeResponse.dailyFocus` | Typed Home field and adapter exist | Formal story authority | `A+E`, out of scope |
| Main Topics | Shared Home; backend order preserved | `HomeResponse.mainTopics` | Typed Home field and adapter exist | Topic snapshot publication/data quality | `A+E`, out of scope |
| Heating / Cooling | Shared Home; backend rotation projection | Home heating/cooling fields | Typed Home fields and adapter exist | Topic rotation read-model readiness | `A+E`, out of scope |
| Market Events | Shared Home `marketPulse`; topic-snapshot-derived | `HomeResponse.marketPulse` | Typed Home field and adapter exist | Formal event authority | `A+E`, out of scope |
| Opportunity teaser | Current page still has static array; formal path remains SHADOW | `/api/v1/opportunities/shadow` is explicit SHADOW | SHADOW types exist; static array is not formal | SHADOW publication and canonical provider | `D+E`, out of scope |

## 4. EXISTING_FASTAPI_ROUTES

| Method / route | Current response | 005A assessment |
|---|---|---|
| `GET /api/v2/home` | `HomeResponse`; PostgreSQL-backed Home composition | Existing primary route; extend typed `marketOverview` only after aggregate contract approval |
| `GET /api/v1/meta/data-status` | Bundle/source/freshness metadata | Operational metadata, not index/turnover authority |
| `GET /api/v1/snapshot/latest` | Flexible compatibility snapshot | Legacy surface; cannot be formal aggregate authority |
| `GET /api/v1/stocks/{code}/price-history` | Instrument historical prices | Instrument-level only |
| `GET /api/v1/operations/live/*` | Operational status/configuration/tracking | Not a customer Today metric contract |
| `GET /api/v1/opportunities/shadow` | Explicit SHADOW Opportunity data | Must remain SHADOW; outside 005A |

No FastAPI route exposes formal TWSE/TPEx index or market turnover facts. The
official exchange clients are provider adapters, not public API routes, and
their current result type is instrument-oriented `HistoricalFetchResult`.

## 5. MISSING_ROUTES

Prefer extending `GET /api/v2/home` with typed `HomeMarketOverview` fields.
Do not add `/api/v2/market-indices` or `/api/v2/turnover` speculatively; that
would create parallel contracts before source and persistence authority exist.

Only if independent history/pagination or a separate freshness boundary is
later proven necessary should a thin route such as
`GET /api/v2/market-overview?dataDate=YYYY-MM-DD` be considered. This is not
authorized by 005A.

## 6. EXISTING_READ_MODELS

### `public.market_snapshots`

The current `MarketSnapshot` model is keyed by ingestion run, data date, and
market. It stores breadth/status fields:

```text
market, status, total_stocks, advance_count, decline_count,
unchanged_count, unavailable_count, generated_at, metadata_json
```

It has no index identity/value/change/changePct or turnover columns.

### `topicpilot.canonical_volume_observations`

The canonical typed volume detail has nullable `volume_quantity`,
`volume_unit_code`, `volume_scale`, `turnover_amount`,
`turnover_currency_code`, `turnover_scale`, `aggregation_code`, and
`volume_context`. Its base canonical observation has a required
`instrument_id`. This is valid instrument storage, not a market aggregate
identity or Home projection.

### Home and post-close

`home_read_model.py` reads the latest completed run and existing market
snapshot, then emits `HomeMarketOverview`; it explicitly adds `marketIndices`
and `turnover` to `dataQuality.missingSections`. No index/turnover query exists.

`TwseOfficialDailyProvider` and `TpexOfficialDailyProvider` support one-date
market-batch requests but return only instrument-code to `HistoricalBar`. The
post-close runner uses `market_batch=True` and ingests each instrument through
the canonical observation pipeline. It does not capture index or market
aggregate turnover records.

The TWSE test payload includes a transaction-amount field (`成交金額` in the
exchange payload shape), but the current adapter maps only instrument code,
volume, and OHLC fields; that amount is discarded. The TPEx fixture proves the
current instrument row mapping but does not define a market turnover contract.
This is evidence for a future adapter extension, not an approved aggregate
authority.

## 7. FRONTEND_MOCKS/LOCAL_COMPUTATION

| File / symbol | Finding | Required boundary |
|---|---|---|
| `apps/web/app/data.ts:marketIndices` | Demo index object | Preview/demo only; never formal fallback |
| `apps/web/app/lib/data-source.ts:mockMarketIndexViews` | Converts demo data to index views | Compatibility/demo only; no Today formal use |
| `apps/web/app/lib/snapshot-adapter.ts:toMarketIndexViews` / `indexStance` | Legacy slots and stance derivation | Must not infer formal identity, change, or market stance |
| `apps/web/app/components/v2/TodayMarketPage.tsx:opportunities` | Static teaser remains in current page | Out of scope; never relabel as formal |
| Any React component | Index changePct, TWSE+TPEx sum, freshness, score, bullish/bearish, or ranking calculation | Forbidden; format backend-owned values only |

The canonical Today Market Overview path no longer uses the old snapshot/mock
metric assembly for its existing Home fields. Residual legacy surfaces remain
for compatibility and other pages; 005A does not clean them up.

## 8. MARKET_INDEX_CONTRACT

This is a proposed contract shape for the next implementation slice. It is not
activated because exact official aggregate source authority and field mapping
are unresolved.

```text
MARKETS=
  TPE / TWSE
  TWO / TPEx

CANONICAL_INDEX_IDENTITIES=
  TPE: primary TWSE broad-market index (TAIEX / 發行量加權股價指數)
  TWO: primary TPEx / OTC market index
  Exact provider identity/code: PENDING_SOURCE_AUTHORITY

OFFICIAL_SOURCE=
  Proposed exchange-official daily index/market-summary feeds.
  Existing TWSE_OFFICIAL_DAILY and TPEX_OFFICIAL_DAILY are currently
  approved only for instrument daily OHLCV, not this aggregate contract.

RAW_FIELDS=
  provider response date; provider index identity/code and display name;
  index close/value; previous close; change; change percentage when supplied;
  source endpoint/request parameters; raw field paths; retrieval timestamp;
  response status.

CANONICAL_FIELDS=
  market; indexCode; displayName; tradingDate; value/close; previousClose;
  change; changePct; dataStatus; sourceProvider; sourceIdentity;
  sourceFieldPath; asOf; updatedAt; lineage.

TRADING_DATE_SEMANTICS=
  Exchange-local Asia/Taipei trading date in the official response. It is not
  retrieval date and is not inferred from browser time.

DATA_DATE_SEMANTICS=
  Home publication/evaluation date. It normally equals tradingDate post-close,
  but remains distinct from tradingDate.

AS_OF_SEMANTICS=
  Latest timezone-aware observation/publication boundary asserted by backend,
  with source evidence.

FRESHNESS_SEMANTICS=
  Backend-owned source quality. A stale number cannot be labelled FORMAL merely
  because it exists. FRESH/STALE is quality evidence; product state is
  FORMAL/PREVIEW/UNAVAILABLE.

CHANGE_OWNER=
  Validated official provider field when present; otherwise backend canonical
  derivation from approved value and previous close with a versioned formula.
  Never frontend-derived.

CHANGE_PCT_OWNER=
  Same provider-first/backend-derived policy. Missing denominator or source
  evidence remains null; null is never converted to zero.

NULL_SEMANTICS=
  Missing value, missing previous close, closed/no-data, provider error,
  stale-beyond-policy, or unresolved identity is explicit unavailable/quality
  evidence. No zero fill and no placeholder index.

LINEAGE=
  Provider authority/version; source identity/code; endpoint/request or raw
  artifact identity; raw field path; tradingDate; retrievedAt; asOf;
  normalization/mapping/reference versions; canonical identity; content hash;
  quality/publication status.

PERSISTENCE_DECISION=
  No current table is accepted as canonical market-index fact. The safe next
  decision is a market-level aggregate fact family with a non-instrument
  identity. Existing market_snapshots may be a Home projection only after
  source/grain review and must not be silently extended in 005A.

HOME_API_MAPPING=
  Extend HomeMarketOverview with a typed marketIndices collection/section,
  preserving per-market records and backend metadata. Avoid a parallel endpoint
  unless independent history/pagination is proven necessary.
```

The labels `TAIEX`, `OTC`, `加權指數`, and similar UI text are not sufficient
canonical identity. The source owner must confirm exact code/namespace,
primary-series choice, timezone/calendar, and whether change/changePct are
source facts or backend-derived values.

## 9. TURNOVER_CONTRACT

The current product intent shows one turnover summary, but the formal contract
must preserve market-level provenance before exposing a combined number.

```text
TURNOVER_SCOPE=
  Daily post-close market turnover for TPE/TWSE and TWO/TPEx, with optional
  backend-owned combined value only after aggregation semantics are approved.

TWSE_SEMANTICS=
  PENDING exact official field mapping. Current MI_INDEX-shaped fixture contains
  a transaction-amount field, but the adapter does not retain it and no market
  aggregate mapping is approved.

TPEX_SEMANTICS=
  PENDING exact official field mapping. Current dailyQuotes maps instrument
  volume but has no approved market turnover field or aggregate.

COMBINED_SEMANTICS=
  Do not sum in React. Backend may compute TWSE + TPEx only when both records
  share tradingDate, session, currency, canonical unit/scale, source-quality
  status, and compatible grain. Retain both source records and a governed
  aggregation code. Otherwise combined is null/unavailable, not zero.

OFFICIAL_SOURCE=
  Proposed exchange-official market-summary/turnover fields. Exact endpoint,
  payload field path, authority code, retention permission, and correction
  policy are PENDING_SOURCE_AUTHORITY.

RAW_UNIT=
  Preserve provider-declared unit and semantics; do not infer a market total
  from instrument rows unless the source contract explicitly declares the rows
  complete for that aggregate.

CANONICAL_UNIT=
  Exact decimal amount with currency code and scale. Expected currency is TWD
  only after official source confirmation; no implicit conversion.

API_UNIT=
  Exact canonical amount plus currency, scale, source, tradingDate, asOf,
  freshness/publication status, and lineage.

DISPLAY_UNIT=
  Frontend may format an approved backend amount as TWD, 億元, or another
  presentation label. Display compaction/rounding never replaces raw amount.

ROUNDING_OWNER=
  Provider/canonical values are not display-rounded. Frontend owns presentation
  formatting only; aggregation/conversion is backend-owned and versioned.

TRADING_DATE_SEMANTICS=
  Asia/Taipei exchange-local trading date of official post-close record.

DATA_DATE_SEMANTICS=
  Home publication/evaluation date, distinct from retrieval/display time.

AS_OF_SEMANTICS=
  Timezone-aware provider observation or backend publication boundary.

FRESHNESS_SEMANTICS=
  Backend-owned quality/publication status. A delayed/stale amount is not
  formal merely because it exists.

NULL_SEMANTICS=
  Missing amount, incomplete payload, closed/no-data, incompatible markets, or
  unresolved semantics is null and explicitly unavailable. Never null-coalesce
  to zero.

LINEAGE=
  Provider, raw request/field path, retrieval time, trading/data date,
  normalization/mapping versions, source artifact/content hash, canonical fact
  identity, aggregation code, quality status, publication status.

PERSISTENCE_DECISION=
  Do not put market turnover into the instrument-bound canonical volume row.
  Persist it as market-level aggregate fact/governed snapshot family, then
  project to Home. Reusing public.market_snapshots is conditional on approved
  source/grain semantics, not ad hoc JSON fields.

HOME_API_MAPPING=
  Extend HomeMarketOverview with typed per-market turnover records and an
  optional backend-owned combined record. Preserve source/status/date/asOf and
  lineage at section/record boundaries.
```

## 10. FORMAL_UNAVAILABLE_PREVIEW_STATE_PLAN

| State | Backend condition | UI behavior |
|---|---|---|
| `FORMAL` | Approved source, exact identity, matching trading date, accepted quality/freshness, required fields, complete lineage/publication evidence | Render backend-owned values and source/date/as-of metadata |
| `UNAVAILABLE` | Source/route/model missing, G1/downstream not ready, closed/no-data, required field missing, provider error, stale beyond policy, or incompatible aggregate inputs | Clear unavailable reason; no numeric placeholder |
| `PREVIEW` | Explicit preview/fixture/synthetic mode selected | Persistent Preview label and source classification; never entered on a formal request error |

`STALE` is a quality reason, not permission to become formal. Under current
evidence, index and turnover subsections are `UNAVAILABLE` (or explicit
Preview fixture in preview mode). The parent Market Overview may remain
`TEMPORARY` while it contains existing partial Home fields, but it must not
claim formal index/turnover data.

## 11. API_CONTRACT_GAPS

1. `HomeMarketOverview` has no `marketIndices` or `turnover` field.
2. Exact TWSE/TPEx index identities and aggregate turnover source codes are not
   registered in the current provider-neutral contract.
3. Existing adapters discard the candidate TWSE transaction-amount field and
   expose no market aggregate result type.
4. `market_snapshots` has breadth/status only.
5. Generic canonical turnover is instrument-bound and cannot represent market
   totals without a market identity/grain.
6. No canonical market-level persistence, correction, idempotency, or lineage
   contract exists for these facts.
7. No section-level index/turnover publication/freshness contract exists.
8. OpenAPI/generated TypeScript declarations have no requested fields; client
   changes must follow approved backend schema.
9. Today renders no formal index/turnover values; legacy mock/snapshot helpers
   must remain outside the formal path.

## 12. IMPLEMENTATION_PHASES

This is a plan, not authorization to implement it in 005A.

1. **Source authority closure.** Confirm official datasets, exact endpoints and
   field paths, index identifiers, turnover semantics, licensing/retention,
   correction behavior, and authority/version codes.
2. **Canonical persistence.** Add the smallest governed market-level fact
   family with exact decimals, identity, session/calendar, trading/data date,
   as-of/retrieval, field path, quality, correction, and lineage. Do not overload
   instrument-bound canonical observations.
3. **Provider/post-close capture.** Extend only the approved official adapters
   and authorized post-close boundary; preserve closed/no-data/stale/duplicate
   and correction semantics.
4. **Home projection.** Project canonical facts into typed
   `HomeMarketOverview`; fail closed on missing source/quality/date evidence.
5. **FastAPI/OpenAPI/client.** Update schemas, regenerate OpenAPI/client, and
   test null/empty/error/loading/publication behavior.
6. **Today rendering.** Add a render-only adapter for
   `FORMAL`/`UNAVAILABLE`/explicit `PREVIEW`; no browser calculation, source
   fallback, freshness inference, or `null ?? 0`.

## 13. Implementation impact

| Required change | 005A result | Next-slice implication |
|---|---|---|
| `PROVIDER_CHANGE_REQUIRED` | `YES` | Extend official adapter contract; do not switch authority |
| `MIGRATION_REQUIRED` | `YES` | New/approved market aggregate persistence needs migration; not run |
| `PERSISTENCE_CHANGE_REQUIRED` | `YES` | Market-level identity/grain/lineage is absent |
| `POST_CLOSE_CHANGE_REQUIRED` | `YES` | Capture approved aggregates in authorized daily boundary |
| `READ_MODEL_CHANGE_REQUIRED` | `YES` | Project into Home after canonical persistence |
| `FASTAPI_SCHEMA_CHANGE_REQUIRED` | `YES` | Add typed fields only after authority closure |
| `OPENAPI_CHANGE_REQUIRED` | `YES` | Regenerate from approved schema |
| `GENERATED_CLIENT_CHANGE_REQUIRED` | `YES` | Regenerate client types/methods |
| `FRONTEND_CHANGE_REQUIRED` | `YES` | Render-only adapter/card changes after backend contract |

## 14. VERTICAL_SLICE_RECOMMENDATION

The next safe implementation slice is one backend vertical proving both
canonical markets through the full contract:

```text
official aggregate payload fixture
  -> provider-neutral index/turnover result
  -> market-level canonical persistence
  -> Home read-model projection
  -> GET /api/v2/home typed fields
  -> generated client
  -> Today render-only adapter
```

Minimum acceptance:

1. TPE and TWO index identities are source-confirmed, not display-label
   inferred.
2. Each market has a dated value/previousClose/change/changePct record or an
   explicit null/unavailable result.
3. Turnover preserves per-market records; combined is backend-owned and may be
   null until aggregation semantics are approved.
4. Every non-null value carries source, as-of, retrieval/lineage, and quality.
5. Provider error, closed date, stale result, incomplete payload, G1/not-ready,
   or missing value renders `UNAVAILABLE`; explicit fixtures render `PREVIEW`.
6. React never ranks, derives change, sums turnover, infers freshness, or
   substitutes mock values.

Planning labels for the next slices are `TODAY-005B` (provider/market
persistence/Home read model) and `TODAY-005C` (Home API/generated client/
frontend rendering). No `NEXT_TASK` file or pointer was changed.

## 15. Safety, gates, and parallelism

| Boundary | 005A result |
|---|---|
| `PARALLEL_SAFE_WITH_DATA_REF_001` | `YES` for this audit/report-only write set |
| G1 | `PRESERVED PASS` baseline; not rerun |
| G2 | `PRESERVED PASS` baseline; not rerun |
| G3 | `PRESERVED PASS` baseline; not rerun |
| Post-Close Canary | `PRESERVED PASS` baseline; not rerun |
| Production DB mutation | `NO` |
| Reference bootstrap | `NO` |
| Provider authority change | `NO` |
| Lifecycle / Opportunity / scoring change | `NO` |
| Scheduler activation | `NO` |
| Deploy / remote push | `NO` |
| Browser market-data inference | `NO` |
| Mock-as-formal or null-to-zero | `NO` |

No code, schema, migration, provider, post-close, API, OpenAPI, or frontend
file changed. Full backend/frontend suites and protected gates were not rerun;
docs-only validation is content review, cross-document consistency,
`git diff --check`, and secret-safe review.

## 16. Required handoff fields

```text
TASK_ID=TASK-FE-BE-TODAY-005A
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_START_SHA=bd0cabfde20a1e950737cc6ba17ee442036d0121
CANONICAL_FINAL_SHA=REPORTED_IN_FINAL_HANDOFF
LOCAL_COMMIT=REPORTED_IN_FINAL_HANDOFF

MARKET_INDEX_AUTHORITY=BLOCKED_PENDING_EXACT_OFFICIAL_AGGREGATE_SOURCE_IDENTITY_AND_FIELD_MAPPING
TURNOVER_AUTHORITY=BLOCKED_PENDING_EXACT_OFFICIAL_MARKET_AGGREGATE_SOURCE_IDENTITY_FIELD_MAPPING_AND_GRAIN
NEXT_TODAY_SLICE=TODAY-005B_BACKEND_MARKET_INDEX_TURNOVER_PROVIDER_PERSISTENCE_HOME_READ_MODEL

PROJECT_CONTEXT_UPDATED=N/A (current document already records the formal gap)
ROADMAP_UPDATED=N/A (current roadmap already routes this to formal-data follow-up)
PRODUCT_ROADMAP_UPDATED=N/A
DOCUMENTATION_INDEX_UPDATED=N/A
DAILY_PROGRESS_UPDATED=N/A

FILES_MODIFIED=NONE (only this report added)
NEW_REPORT=YES
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
FINAL_STATUS=BLOCKED_PENDING_MARKET_DATA_SOURCE_AUTHORITY
```
