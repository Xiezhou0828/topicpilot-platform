# TASK-FE-BE-TODAY-004E｜Market Overview Formal Wiring

## Scope and authority

This isolated continuation uses the existing TASK-FE-BE-TODAY-004D branch and
its implementation base SHA `59cb1b1f50911d464eaa756a844ac2efe0ba18c0`.

The requested handoff path
`docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md` is not present in this checkout,
so the audit used the available repository authority: `PROJECT_CONTEXT.md`,
the 004D formal report, the frontend/product design contracts, the generated
OpenAPI client, the FastAPI schemas/read model, and the current Today Home
implementation and tests. `origin/main` was unchanged during this task:

```text
STARTING_ORIGIN_MAIN_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
CURRENT_ORIGIN_MAIN_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
MAIN_DRIFT = NO
```

The current operational truth remains G0 PASS, G1 FAIL with incomplete market
identity/instrument coverage, frontend formal real data NOT READY, Opportunity
SHADOW, and Scheduler unauthorized. This task does not change any of those
states.

## TODAY_MARKET_MODULES

| Today Market module | Current UI | Backend authority | 004E treatment |
| --- | --- | --- | --- |
| Market Overview | Previously hardcoded metrics plus legacy snapshot reads | `HomeResponse.marketOverview` / `HomeMarketOverview` | Implemented through the shared Home resource |
| Market breadth | Previously read from `bundle.marketRadar.breadth` when available | `HomeMarketOverview.marketHealth` | Uses nullable backend field; null renders unavailable |
| Today Market Story | Existing Today Home card | `HomeResponse.dailyFocus` / `HomeDailyFocus` | Existing 004C wiring retained; no reimplementation |
| Today Mainlines | Existing Today Home cards | `HomeResponse.mainTopics` / `HomeTopicCard[]` | Existing 004D continuation path retained |
| Market Events | Existing Today Home card | `HomeResponse.marketPulse` / `HomeMarketPulseEvent[]` | Existing 004D wiring retained |
| Heating / Cooling | Existing rotation cards | `HomeResponse.heatingTopics` and `coolingTopics` | Existing 004D wiring retained |
| Opportunity teaser | Current bounded presentation array | Opportunity is still SHADOW and outside 004E | Not processed; not treated as formal data |

The 004E implementation scope is only Market Overview. Opportunity,
Recommendation, historical views, Stock Explorer, Topic Detail, lifecycle
activation, G0/G1/G2/G3, Reference, Canary, Scheduler, provider changes, and
browser analytics remain outside this task.

## CURRENT_DATA_SOURCE_MATRIX

| UI data / field | Before 004E | Correct authority | Route / schema / client | Frontend adapter | Readiness and state |
| --- | --- | --- | --- | --- | --- |
| `dataStatus` | Not rendered from Home | `HomeMarketOverview.dataStatus` | Existing `GET /api/v2/home`; generated `HomeMarketOverview` | `mapMarketOverview` | Current backend value is `PARTIAL`; visible only as TEMPORARY, never relabeled FORMAL |
| `trackedStockCount` | Not rendered from Home | `HomeMarketOverview.trackedStockCount` | Existing Home route and generated schema | `mapMarketOverview` | Backend-owned count; no browser aggregation |
| `trackedTopicCount` | Not rendered from Home | `HomeMarketOverview.trackedTopicCount` | Existing Home route and generated schema | `mapMarketOverview` | Backend-owned count; no browser ranking or inference |
| `marketHealth.market/status` | Partially represented by legacy snapshot surface | `HomeMarketOverview.marketHealth` | Existing nullable generated field | `mapMarketOverview` | Preserved when present; missing health is unavailable |
| `marketHealth.totalStocks` | Browser/legacy breadth path | `HomeMarketHealth.totalStocks` | Existing nullable generated field | `mapMarketOverview` | Nullable value rendered as `—`; never fabricated |
| `marketHealth.advance/decline/flat/unavailable` | `bundle.marketRadar.breadth` fallback path | `HomeMarketHealth` fields | Existing nullable generated fields | `mapMarketOverview` | Backend values rendered directly; no recomputation from stock rows |
| `dataDate` | Legacy freshness path | `HomeMarketOverview.dataDate` | Existing generated field | Preserved in resource and UI metadata | Preserved; null remains null/unavailable metadata |
| `updatedAt` / `asOf` | Legacy snapshot freshness path | `HomeMarketOverview.updatedAt`, shared Home `asOf` fallback | Existing generated fields | Preserved as `asOf` | Preserved without browser freshness inference |
| `latestSnapshotTime` | Not an approved browser source | `HomeMarketOverview.latestSnapshotTime` | Existing generated field | Preserved inside backend data object; not reinterpreted | No client-side freshness rule added |
| `source` | Legacy source/fallback labels | `HomeMarketOverview.source` | Existing generated field | Preserved in resource and rendered metadata | Source remains backend-owned |
| Market indices | Hardcoded `加權指數` / `櫃買指數` and legacy `marketIndices` lookup | No current Home authority | No Today Market endpoint/schema field | None | Category C/E: unavailable; no new endpoint invented |
| Turnover | Hardcoded estimated value | No current Home authority; Home read model marks `turnover` missing | No route/schema/client field | None | Category C/E: unavailable; no estimate shown |
| Market score / bullish-bearish classification | Not an approved Home field | No current backend authority | No route/schema/client field | None | Category C/D: forbidden to calculate in browser |
| Volume trend / narrative / signal sorting | Not an approved Home field | No current backend authority | No route/schema/client field | None | Category C/D: no frontend derivation or sort added |

## EXISTING_FASTAPI_ROUTES

- `GET /api/v2/home` is the single existing read route and returns the required
  `HomeResponse.marketOverview` contract.
- The Home response is consumed by the existing frontend `TodayHomeResource`
  and one `client.getHome()` request. 004E adds no request and no parallel
  market endpoint.
- Other V2 routes such as topic/stock/admin reads are not Market Overview
  authorities and were not repurposed for this section.

## EXISTING_READ_MODELS

- FastAPI `HomeResponse.marketOverview` is built by the existing PostgreSQL
  Home read model.
- The exact current fields are:

  ```text
  dataDate
  updatedAt
  dataStatus
  trackedStockCount
  trackedTopicCount
  latestSnapshotTime
  marketHealth.{market,status,totalStocks,advance,decline,flat,unavailable}
  source
  ```

- The current read model emits `source=POSTGRESQL_READ_MODEL` and, when the
  relevant read data exists, `dataStatus=PARTIAL`. `marketHealth` is nullable.
  The read model also explicitly identifies `marketIndices` and `turnover` as
  missing sections; 004E does not create a second read model for them.
- OpenAPI and generated TypeScript schemas already contain the exact contract;
  no backend schema, route, OpenAPI, or generated-client change was required.

## FRONTEND_MOCKS/LOCAL_COMPUTATION

Removed from the Market Overview path:

- hardcoded `mockMarketMetrics` values;
- legacy `useSnapshot` consumption from `bundle.homeData.marketIndices`;
- legacy `marketRadar.breadth` reads and fallback assembly;
- browser-side `liveMetric`, index lookup, freshness label, and metric slicing;
- any browser aggregation from instrument rows.

The new card only renders fields from `TodayMarketOverviewResource.data` and
shared metadata. It does not calculate advance/decline totals, instrument
aggregates, market score, bullish/bearish state, narrative, volume trend, or
signal ordering.

The existing hardcoded Opportunity teaser remains untouched because Opportunity
is explicitly out of scope and still SHADOW. It is not used to populate Market
Overview and is not claimed as formal data.

## FORMAL_UNAVAILABLE_PREVIEW_STATE_PLAN

`TodayHomeResource` remains the only transport/publication envelope. The new
`TodayMarketOverviewResource` projection preserves the existing four-state
contract:

| State | Mapping | UI behavior |
| --- | --- | --- |
| `FORMAL` | Complete Home contract plus formal publication metadata | Render backend values as formal data |
| `TEMPORARY` | Complete fields but Home publication is partial/temporary | Render values with an explicit TEMPORARY state; never promote to FORMAL |
| `PREVIEW` | Only when preview is explicitly enabled | Render with an explicit Preview state |
| `UNAVAILABLE` | Null/incomplete fields, gated publication, preview disabled, missing formal data, or transport/API error | Render a clear unavailable/loading state; no fallback mock |

`dataDate`, `asOf`, and `source` are preserved in every non-loading projection.
Nullable counts remain nullable and render as `—`; nullable `marketHealth`
renders the explicit “市場廣度資料目前不可用” state. API errors flow through
the existing `errorTodayHomeResource` path and cannot silently become Preview
or mock data.

## API_CONTRACT_GAPS

| Gap | Category | Decision |
| --- | --- | --- |
| Index values | C / E | No backend authority in the current Home contract; leave unavailable and raise a future backend-owned read-model task only if product scope approves it |
| Turnover | C / E | No backend field or authority; do not show the previous estimate |
| Market score, bullish/bearish, narrative, volume trend | C / D | No authority and no browser calculation; do not add a thin presentation route |
| Nullable `marketHealth` | Existing contract gap, not a route gap | Fail closed at the card boundary while preserving the rest of `marketOverview` |
| Formal G1 readiness | Operational gate | Not changed by 004E; current non-formal Home data remains labeled TEMPORARY/UNAVAILABLE as appropriate |

No thin backend route was necessary: the existing Home read model and generated
schema already contain the approved Market Overview fields. A future route, if
needed for missing index/turnover authority, must start from a backend-owned
read model and contract rather than frontend derivation.

## VERTICAL_SLICE_RECOMMENDATION

The smallest accepted vertical slice is complete:

1. Reuse the existing `GET /api/v2/home` request.
2. Project `HomeResponse.marketOverview` through
   `TodayMarketOverviewResource`.
3. Render `dataStatus`, tracked counts, nullable market health, and preserved
   `dataDate` / `asOf` / `source` metadata.
4. Show explicit loading, TEMPORARY, Preview, and unavailable states.
5. Prove that API errors and missing health do not fall back to mock data.

The slice adds zero Home requests and leaves the existing 004C/004D mainline,
heating/cooling, Daily Focus, and Market Events projections on the same shared
resource.

## IMPLEMENTATION_PHASES

| Phase | Status | Result |
| --- | --- | --- |
| Contract audit | COMPLETE | Confirmed existing `HomeMarketOverview` authority and exact fields |
| Adapter projection | COMPLETE | Added fail-closed Market Overview projection to `today-mainlines.ts` |
| UI wiring | COMPLETE | Replaced legacy/mock overview with backend-owned card |
| Focused tests | COMPLETE | Mapping, state, metadata, single-request, and no-browser-computation assertions pass |
| Full frontend validation | COMPLETE | Build, tests, TypeScript, lint, demo snapshot, diff, and secret sanity scan pass |
| Local handoff | COMPLETE | Report and append-only worklog prepared; local commit only |

## Validation

```text
FOCUSED_TESTS = 23/23 PASS
FRONTEND_TESTS = 116/116 PASS
FRONTEND_BUILD = PASS
TYPESCRIPT = PASS
FULL_LINT = PASS (one pre-existing unrelated warning at TopicDetailPage.tsx:114)
API_CLIENT_GENERATED_CONTRACT_IDEMPOTENCE = PASS
API_CLIENT_TESTS = 3/3 PASS
BACKEND_TESTS = NOT RUN (backend unchanged)
DEMO_SNAPSHOT_CHECK = PASS
DIFF_CHECK = PASS
CHANGED_FILE_SECRET_SANITY_SCAN = PASS
```

## Fixed handoff fields

```text
TASK_FE_BE_TODAY_004E = Market Overview Formal Wiring
TODAY_004D_BASE_SHA = 59cb1b1f50911d464eaa756a844ac2efe0ba18c0
BRANCH = codex/task-fe-be-today-004d-20260814
HOME_REQUEST_REUSED = YES
EXTRA_HOME_REQUESTS_ADDED = 0
MARKET_OVERVIEW_BACKEND_FIELDS = dataDate, updatedAt, dataStatus, trackedStockCount, trackedTopicCount, latestSnapshotTime, marketHealth.{market,status,totalStocks,advance,decline,flat,unavailable}, source
MARKET_OVERVIEW_SOURCE = POSTGRESQL_READ_MODEL
MARKET_OVERVIEW_CONTRACT_STATE = PARTIAL / TEMPORARY
HARDCODED_MARKET_OVERVIEW_REMOVED = YES
BROWSER_AGGREGATION = NO
BROWSER_MARKET_SCORE = NO
BROWSER_NARRATIVE = NO
BROWSER_SIGNAL_SORTING = NO
FORMAL_MAPPING = FORMAL only
TEMPORARY_MAPPING = TEMPORARY with explicit state
PREVIEW_MAPPING = explicit preview only
UNAVAILABLE_MAPPING = null/incomplete/gated/preview-disabled/error fail-closed
SOURCE_PRESERVED = YES
DATA_DATE_PRESERVED = YES
AS_OF_PRESERVED = YES
MODE_PRESERVED = N/A (no Market Overview mode field)
API_ERROR_FALLBACK_TO_MOCK = NO
BACKEND_CONTRACT_CHANGED = NO
OPENAPI_SEMANTICS_CHANGED = NO
TODAY_MAIN_TOPICS_REGRESSION = PASS
TODAY_HEATING_COOLING_REGRESSION = PASS
TODAY_DAILY_FOCUS_REGRESSION = PASS
TODAY_MARKET_EVENTS_REGRESSION = PASS
DATA_REF_FILES_TOUCHED = NO
PRODUCTION_MUTATION = NO
PUSH_MAIN = NO
MERGE_MAIN = NO
DEPLOY = NO
NEXT_TASK_MODIFIED = NO
AI_WORKLOG_UPDATED = YES
AI_WORKLOG_APPEND_ONLY = YES
FINAL_STATUS = READY_FOR_TODAY_004E_INTEGRATION_REVIEW
```

Implementation files are limited to the Today Market adapter/UI, affected
frontend contract/regression tests, this report, and the append-only worklog.
