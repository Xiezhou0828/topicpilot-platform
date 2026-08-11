# TASK-FE-013｜Favorites Deployment + Hydrated Runtime Verification

## 1. Root Cause

FE-012 was already present in the production source lineage: production version 35 pointed to commit `c00960c6854c39d589ca169d81b1b6ee474e4b38`, and that commit is an ancestor of the current `main` branch. A production HTML check already contained `我的收藏`, `今日有變化`, the Favorites module preload, and the Preview disclosure.

The apparent “old build” / `/assets/index-*.js` 404 was reproduced locally after rebuilding while an older `vinext start` process was still running. The process retained its old SSR asset manifest while `dist/client/assets` had been replaced with new hashes, so HTML referenced files that no longer existed. This was a stale runtime/process issue, not a missing `base` setting or a separate frontend site. Production version 35 itself returned matching assets with HTTP 200.

Runtime testing also found that the shared stock drawer used an internal favorite boolean. Clicking `加入收藏` changed the star but did not update the Favorites watchlist count. The drawer now reuses the existing local favorite state and change event.

## 2. Production Deployment Source

- Existing Sites project: `appgprj_6a6ce02bd75c81919ab3678ebf013c53`
- Existing source branch: `main`
- Deployed source commit: `6247786e50eb83c83840afde99884ced4d8500f6`
- Saved Sites version: `36` (`appgprj_6a6ce02bd75c81919ab3678ebf013c53~appgver_a1571da813748191af4e36ab7befa66e`)
- Deployment: `appgdep_6a7b67f1523c8191868bc31cdbfcf62b`
- Deployment status: `succeeded`
- Access mode: existing public site; no second site was created

## 3. Asset 404 Root Cause

The validated build was packaged from `apps/web/dist` using the Sites package helper. The stale local process was the only observed source of mismatched HTML/hash assets. The production response after version 36 referenced 14 current assets; every sampled CSS/JS asset returned HTTP 200. The safe operational fix is to restart the local production process after each build and deploy the archive generated from that same build.

## 4. Fix

- `useFavoritesState()` now exposes a `toggle(code)` operation that writes the existing `topic-pilot-favorites` localStorage key and dispatches the existing shared change event.
- `StockEncyclopediaDrawer` now reads `favoriteCodes` from that hook and toggles the shared state; it does not create a second favorite store or a second stock detail surface.
- No IA, Topic Detail, Stock Explorer, Shared Header, scoring, lifecycle, recommendation, or `NEXT_TASK` changes were made for this deployment.

## 5. Deployed URL

[https://topicpilot-platform.game0962046460.chatgpt.site/favorites](https://topicpilot-platform.game0962046460.chatgpt.site/favorites)

The route is the existing `/favorites` route and is live on the existing production hostname.

## 6. Browser Hydration Evidence

Using a fresh production browser page after version 36:

- `/favorites` rendered `我的收藏`, `今日有變化`, the `收藏類型` tablist, and the Preview disclosure.
- After the page settled, the DOM exposed selected tabs and interactive buttons, proving client hydration rather than SSR-only HTML.
- `tab.dev.logs({levels:["error","warn"]})` returned an empty list after the Favorites load.
- The final URL remained the production `/favorites` route (with only a cache-busting query during verification).

## 7. Favorites Interaction Evidence

- Initial partial state showed `題材 1` and `股票 0`, with the empty stock state rendered.
- Clicking the stock tab switched selection and content without navigation.
- From the stock database, opening Aster Systems in the shared drawer and clicking `加入收藏` changed the button to `取消收藏`.
- Returning to Favorites produced `題材 1` / `股票 1`; the factual change strip showed `Aster Systems · 今日 +1.35%`.
- The stock tab showed a compact row with name/code, `45.2`, `+1.35%`, `Edge AI`, `PRIMARY`, and `LIVE`.

## 8. Topic Navigation Evidence

Clicking the saved `AI伺服器` row navigated to `/topics/ai-server`. The Topic Detail page rendered its existing identity, lifecycle, status, and research stock sections. No duplicate topic detail was introduced.

## 9. Shared Stock Drawer Evidence

Clicking the Favorites stock row opened the existing `StockEncyclopediaDrawer` dialog titled `Aster Systems`, with the same Preview/formal-field boundaries used elsewhere. The dialog exposed `取消收藏` and `Close stock drawer`. Pressing Escape closed the dialog and removed it from the DOM. No second stock detail implementation was added.

## 10. Responsive Evidence

At a temporary 390×844 viewport, the Favorites title, change region, tabs, and topic row remained present and readable. The dense table intentionally keeps a horizontal scroll surface at narrow widths (the existing compact-table behavior); the pre-existing shared header also remains outside this task’s scope. The viewport override was reset after verification.

## 11. Formal / Preview Data Status

The Favorites page continues to prefer formal fields and leaves unavailable values as `尚未提供` / `—`. Current production data remains Preview where the formal API/read model is not configured; Preview does not overwrite formal values. The change strip only reports factual values available from the saved snapshot, such as a stock’s displayed daily percentage.

## 12. Backend read models still needed

No formal Favorites persistence/read API exists yet. Backend work still needed for a durable user-scoped Favorites read model and write contract, including:

- authenticated user/portfolio ownership and favorite entity type;
- saved topic/stock identifiers and ordering;
- topic `grade`, `score`, lifecycle stage, lifecycle trading day, and factual state-change events;
- stock price/change, primary topic, topic role, freshness/update mode, and as-of date;
- a formal “today changes” collection with event type, timestamp, and source lineage.

Until then, the current implementation intentionally uses the existing local saved state and the public snapshot/Preview adapter.

## 13. Direct-switch path

The formal switch path is: replace the local favorites source with the authenticated Favorites read/write API, map its explicit nullable fields into the current view model, retain the existing tabs/rows, and keep `Topic Detail` and `Shared Stock Encyclopedia Drawer` as the destinations. No IA change is required.

## Boundary confirmation

This remains a Watchlist + Market Context surface, not a portfolio or recommendation surface. It does not add cost basis, position size, P/L, performance charts, buy/sell advice, ranking, opportunity scores, or a second detail page. Empty and partial states remain explicit.

## Verification

- ESLint on changed Favorites/drawer files: PASS
- Favorites unit tests (`node --test tests/favorites.test.mjs`): PASS (6/6)
- Vinext production build: PASS; `/favorites`, `/topics/:slug`, and `/stocks` routes present
- Production HTML: HTTP 200; Favorites title and change region present
- Production assets: 14 referenced CSS/JS assets checked; 14/14 HTTP 200
- Hydration/runtime console: PASS; no warning/error entries captured
- Tabs/count updates: PASS
- Topic navigation: PASS (`/topics/ai-server`)
- Shared drawer open, shared favorite persistence, Close, and Escape: PASS
- Production deployment: PASS; Sites version 36 status `succeeded`

Final fixed statuses:

```text
FAVORITES_DEPLOYED = PASS
HYDRATION = PASS
STATIC_ASSETS = PASS
TAB_INTERACTION = PASS
TOPIC_NAVIGATION = PASS
STOCK_DRAWER = PASS
PRODUCTION_ROUTE = READY
```

## Remaining issues

1. A formal authenticated Favorites API/read model is still missing; localStorage and Preview remain the temporary source.
2. Narrow screens intentionally use a horizontally scrollable dense table, and the shared header has pre-existing narrow-viewport overflow. Both are outside the requested Favorites-only scope and should be handled in a separate responsive shell task if a no-horizontal-scroll mobile target is required.
3. The local production server must be restarted after a new build so its SSR manifest and `dist/client/assets` remain in sync.

`NEXT_TASK` was not modified.
