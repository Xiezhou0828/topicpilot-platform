# TASK-FE-010｜Stock Encyclopedia Real-Data Preview + Drawer Refinement

**Status:** Implemented; build and lint verified. Typecheck/test suite retain pre-existing repository failures documented below.
**Route:** `/stocks`

## 1. Product Positioning

Stock remains the TopicPilot Market Encyclopedia: a dense, formal-data-first stock surface for scanning the complete universe and opening a shared Stock Drawer without leaving context. This task does not change the stock-page information architecture.

## 2. Implemented Changes

- Reused `SnapshotBundle.stockUniverse`, formal `StockView`, formal `TopicView`, and `TopicRelationView` data.
- Added a single-topic Advanced Filter sourced from `bundle.topics`; no topic vocabulary is hard-coded in the UI.
- Preserved compact fixed-size tiles, LIVE/EOD presentation, explicit null display, stable manual sorting, direct tile switching, Close, and Escape behavior.
- Added page-level Preview disclosure only when the bundle source is not the formal snapshot.
- Refined the shared inline Stock Drawer to fill the viewport below the 72px shared header and scroll internally while its header remains visible.
- Kept the existing shared Drawer component reusable by Topic Detail.

## 3. Formal API versus Preview Data

| Surface | Formal source | Preview fallback | Missing behavior |
|---|---|---|---|
| Stock identity / symbol | `StockView.code`, `StockView.name` from snapshot adapter | None | `未提供名稱` / code remains visible |
| Market | No market field in current `StockView` contract | None | Listed/OTC options remain disabled pending formal field |
| Price | `StockView.price` | None | `—` |
| Change | `StockView.change` | None | `—` |
| LIVE/EOD | `StockView.dataFreshness` | None | `資料待更新`; no false EOD conversion |
| Topic | `StockView.topicNames`, `TopicRelationView.topic` | None | `尚未提供題材身分` |
| Topic role | `TopicRelationView.role`, normalized only to approved labels | None | `—` |
| Technical state | Not consumed by this surface | None | Not displayed |
| Favorite | Existing local `FavoriteStar` state | Device-local component state | Neutral inactive star |
| Stock summary | Existing topic identity/read-model fields | None | `狀態尚未提供` |
| Opportunity CTA | Existing `/opportunities` route | None | CTA remains a navigation shell |

## 4. Real Data Evidence

The current checked-in web snapshot contains 4 stock records, 5 topic-relation records, and 4 priced records. The frontend reads the full `stockUniverse` bundle and does not restrict the grid to a hand-picked demo subset. Formal runtime data availability remains dependent on the snapshot source selected by `useSnapshot`; the page shows an unavailable state instead of substituting mock rows.

The checked-in snapshot is synthetic development evidence, not a claim of production market-data completeness. Live/EOD counts, TPE/TWO counts, and relation coverage are surfaced from the formal bundle when the backend snapshot provides the corresponding semantic fields.

## 5. Topic Filter

- **Topic source:** `bundle.topics` formal Topic read model.
- **Relation source:** `StockView.topicNames` and `StockView.relations` produced by the snapshot adapter.
- **Behavior:** one selected topic filters stocks with an exact formal topic relation; clearing returns the full universe.
- **Status:** Formal when the bundle source is `snapshot`; page-level Preview disclosure appears for non-formal bundle sources.

## 6. Stock Drawer

- **Positioning:** existing shared inline push drawer; the grid remains visible and clickable.
- **Header offset:** uses the shared 72px header token/contract rather than a page-specific arbitrary offset.
- **Viewport height:** `height: calc(100vh - 72px)` on desktop; width strategy is unchanged.
- **Internal scroll:** drawer body scrolls independently while identity/header actions remain visible.
- **Page scroll:** drawer remains sticky/anchored in the workspace while the grid can continue to scroll.
- **Close:** existing `×` clears the selected stock and restores the full-width grid.
- **Switching:** selecting another tile replaces the shared Drawer content directly.

## 7. Animation

**Deferred.** No new mount/unmount animation was added in this task. The shared Drawer remains a stable inline component with a persistent selected-state boundary, so restrained enter/exit transforms can be added later without redesigning the data mapping or layout. Reduced-motion handling remains available for that future transition.

## 8. Backend Read Models Still Needed

- Formal market/exchange field for reliable Listed/OTC filtering.
- Formal update mode or freshness semantics that distinguish LIVE, EOD, and data-pending without inference.
- Formal stock summary/identity fields beyond topic relation and topic status.
- Formal favorite persistence if favorites move beyond local UI state.

## 9. Direct-switch Path

The UI consumes `StockView`, `TopicView`, and `TopicRelationView` through the existing snapshot adapter. When backend fields become formal, the Preview disclosure and null/pending presentation can be removed at the adapter boundary; tile and Drawer structure do not need to change. Topic filtering already reads formal topic identity and relation names rather than a second frontend vocabulary.

## 10. Boundary Confirmation

- No backend business rules changed.
- No Topic Overview, Topic Detail, Market, Favorites, Opportunity, or AI Research page was changed.
- Shared Header/navigation was not redesigned.
- No new topic-role enum was created; only existing approved role values are normalized for display.

## 11. Verification

- `npm run build`: **PASS**; `/stocks` present in route manifest.
- `npm run lint -- --no-cache`: **PASS**.
- `git diff --check`: **PASS** for the task diff.
- `npx tsc --noEmit`: **BLOCKED by pre-existing errors** in `app/lib/data-source.ts`, `app/lib/snapshot-store.tsx`, `app/watchlist/page.tsx`, `vite.config.ts`, and `worker/index.ts`.
- `npm test`: **BLOCKED by pre-existing repository test failures** across legacy home/rendered-html and data-source expectations; build portion passes.
- Route/data mapping: build verifies the route and formal bundle wiring; browser interaction still needs a live authenticated/served runtime check after deployment.

## 12. Remaining Issues

- Market filter remains disabled for Listed/OTC until a formal market field exists in `StockView`.
- Drawer slide-in/slide-out animation is deferred.
- Full live production data coverage depends on the backend snapshot/read model and is not claimed by the checked-in synthetic snapshot.
- Repository-wide typecheck and test debt remains outside this task's whitelist.

## 13. Recommended Next Step

Add the formal market/exchange and explicit update-mode fields to the approved Stock read model, then enable the already-present UI controls without changing the Stock Tile or Drawer structure.
