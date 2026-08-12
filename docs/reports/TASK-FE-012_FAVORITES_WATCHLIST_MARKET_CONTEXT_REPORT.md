# TASK-FE-012 — Favorites Watchlist + Market Context Implementation Report

**Status:** Implemented; build and scoped tests passed; hydrated browser interaction recheck pending
**Generation:** NEXT / V2
**Route:** `/favorites`
**Scope:** First-version Favorites surface only

## 1. Product positioning

`我的收藏` is a personal market-monitoring surface: **Watchlist + Market Context**. It answers what has changed among items the user deliberately saved. It is not a holdings page, portfolio-performance page, recommendation surface, or second research center.

The page keeps two first-class saved entity types: topics and stocks. Topic rows route to the existing Topic Detail. Stock rows reuse the shared `StockEncyclopediaDrawer`.

## 2. Implemented changes

- Replaced the `/favorites` shared-foundation placeholder with a dedicated `FavoritesWorkspacePage`.
- Added a compact `今日有變化` section for factual topic direction and stock daily-price changes only.
- Added `題材 | 股票` segmented tabs with persisted saved-item counts.
- Added dense topic rows containing topic identity, formal Grade/Score, formal lifecycle stage and `Day N` only when returned, and today's factual direction.
- Added familiar watchlist rows containing stock name/code, price, daily change, main topic, topic role, and `LIVE / EOD / 資料待更新`.
- Topic-row navigation uses the existing `/topics/:slug` route.
- Stock-row interaction uses the existing shared `StockEncyclopediaDrawer`; no Favorites-specific stock detail was created.
- Added empty, loading, missing-item, partial-field, and page-level Preview disclosure states.
- Preserved the existing `topic-pilot-favorites` stock localStorage format.
- Added persisted topic favorites under `topic-pilot-topic-favorites`, and connected Topic Overview stars to that shared state so refresh and cross-route navigation preserve the selection.
- Added responsive overflow behavior for dense rows and a single-column Market Context layout at narrower widths.

## 3. Formal API versus Preview Data

| Surface | Formal source | Preview / unavailable behavior |
|---|---|---|
| Topic identity, Grade, Score, direction | `GET /api/v2/topics` through `fetchTopics` | Existing synthetic public topic snapshot only when no API origin is configured; page-level `Preview` disclosure |
| Topic lifecycle and Day N | `GET /api/v2/topics/{slug}` through `fetchTopic` | Remains `尚未提供`; Preview lifecycle is not invented or rendered as formal data |
| Stock identity, price, change, topic relations, update mode | `GET /api/v2/stocks` through `fetchFormalStocks` | Existing public snapshot only when formal API is not configured; missing saved codes remain visible with null fields |
| Saved-item membership | No formal API exists | Existing local saved state; stock key retained and topic key added |
| Today's changes | Formal topic `direction` and formal stock `changePct` | Preview-origin values are allowed only under the page-level Preview disclosure; null produces no event |

Formal non-null values always win. A configured formal Stock API returning an item set does not fall back item-by-item to Preview. Missing numeric values remain null and render as `—`; the browser does not infer lifecycle, role, freshness, recommendation, or business state.

## 4. Backend read models still needed

- User-scoped saved-item persistence for topics and stocks, including stable ordering and removal.
- A Favorites aggregate read model returning saved topic and stock identities in one bounded request.
- Canonical saved-item factual-change events with event type, occurred-at time, previous value, current value, and source lineage.
- Topic list fields for canonical direction/change semantics if the existing direction contract is not the final production event model.
- Topic lifecycle stage, stage-entry date, trading-day `Day N`, and lifecycle history on the formal detail read model.
- Stock main-topic selection semantics when several formal topic relations exist.
- Canonical stock topic role, update mode, freshness/as-of time, and missing-data reason per saved item.
- Authentication/user identity required to scope saved lists across devices.

## 5. Direct-switch path

The UI consumes topic and stock adapters rather than browser-derived business rules. When a formal Favorites API is available:

1. replace the two localStorage hooks with the user-scoped saved-item endpoint;
2. retain the existing topic and stock row view models;
3. replace the current factual-change composition with canonical event rows;
4. remove the page-level Preview disclosure when all displayed fields are formal;
5. keep the existing Topic Detail links and shared Stock Drawer interaction unchanged.

No page-layout rewrite is required for this switch.

## 6. Boundary confirmation

- No backend schema, API route, scoring rule, lifecycle rule, recommendation logic, or market-data derivation was added.
- No cost, share count, P/L, performance chart, buy/sell advice, recommendation, or large KPI card was added.
- Home, Topic Detail, Stock Explorer, Opportunity, AI Research, shared header, and global design language were not redesigned.
- Topic Detail and `StockEncyclopediaDrawer` remain the only downstream detail surfaces.
- `NEXT_TASK` was not modified.

## 7. Verification

- Scoped ESLint for Favorites, topic favorite integration, and route files: **passed**.
- Favorites unit tests: **6/6 passed**.
- Production `npm run build`: **passed**; `/favorites`, `/topics/:slug`, and `/stocks` are present in the route manifest.
- Standalone `npx tsc --noEmit`: **blocked by pre-existing unrelated errors** in `data-source.ts`, `snapshot-store.tsx`, legacy `/watchlist`, `vite.config.ts`, and worker platform globals. No error referenced the files added or modified by this task.
- Browser SSR verification: **passed** for the new heading, Market Context region, factual-change empty state, and counted topic/stock tabs.
- Hydrated browser interaction verification: **pending environment repair**. The local Vinext production server returned the rendered page but returned 404 for its generated `/assets/index-*.js`, preventing hydration. Therefore tab switching, seeded local saved state, Topic navigation by click, shared Stock Drawer opening/closing, Escape close, and viewport override checks are not claimed as runtime-passed in this report.
- Static interaction evidence: scoped tests confirm tab markup, Topic Detail route construction, shared Drawer import/use, shared favorite change event, and exclusion vocabulary.
- Responsive implementation evidence: explicit `820px` and `560px` rules collapse Market Context and preserve dense-row access through horizontal overflow; hydrated visual recheck remains pending with the asset-serving issue above.

## 8. Remaining issues

- Repair or bypass the local Vinext asset-serving mismatch, then rerun hydrated browser checks for both empty and seeded partial states.
- The shared Stock Drawer currently owns an internal favorite star state rather than reading the same persisted stock-favorite hook; this pre-existing Drawer behavior should be unified in a separate bounded refinement.
- Local topic and stock saved state is device/browser scoped until a formal authenticated Favorites API exists.
- `今日有變化` currently composes factual values available on list read models; a canonical backend change-event stream is still required for exact transitions such as first upgrade to S, lifecycle entry, or role change.
