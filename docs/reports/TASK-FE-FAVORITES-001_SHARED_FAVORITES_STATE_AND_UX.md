# TASK-FE-FAVORITES-001 — Shared Favorites State and UX

## Executive Result

`FAVORITES_SHARED_LOCAL_STATE_UX_COMPLETE`

The frontend now uses one shared local-device favorites state for the currently supported `STOCK` and `TOPIC` entities. Stock Explorer, the shared Stock Drawer, Topic List, Topic Detail, the existing Favorites workspace, and the retained FavoriteButton surface use the same storage family, change notification, identity semantics, and accessibility contract. Favorite state remains a user preference and is kept separate from formal market data, Preview data, API availability, and server-side product state.

No server-side favorites API, account synchronization, database change, aggregate read model, Recommendation change, Today source-authority change, or Production mutation was introduced.

## Canonical State

- Task ID: `TASK-FE-FAVORITES-001`
- Current authority identity: no existing formal Favorites task identity was present in `docs/ROADMAP.md` or `docs/WORK_ORDERS.md`; the requested task ID is therefore adopted.
- Canonical repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
- Baseline SHA before this task's application/docs commit: `c0431be078766320996a48a392d79d42c2f3e996`
- Branch: `codex/task-ops-023a-p3c-runtime-sha-audit-20260813`
- Origin remote: `https://github.com/Xiezhou0828/topicpilot-platform.git`
- `origin/main`: no local remote-tracking ref was present during audit; no main SHA is asserted.
- Worktree: direct canonical work; no new worktree was created.
- Pre-existing unrelated dirty files were preserved. `apps/web/app/components/v2/TopicListPage.tsx` was treated as an active Topic Detail workstream collision and was not modified by this task.

## Current Favorites Surface Matrix

| Surface | FAVORITE_CONTROL_EXISTS | STATE_SOURCE | LOCAL_STORAGE/CLIENT_STATE | SHARED_STORE | INITIALIZATION_BEHAVIOR | PERSISTENCE_ACROSS_RELOAD | CROSS_SURFACE_SYNC | EMPTY_STATE | ERROR_BEHAVIOR | ACCESSIBILITY | CURRENT_GAP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Today Market | NO | N/A; no current favorite affordance | Shared contract is available if a control is added later; no Today-specific state | N/A | No favorite initialization | N/A | N/A | Existing Today empty/unavailable states unchanged | Today/API state does not touch favorites | N/A | Add a favorite control only through a future bounded product decision |
| Topic List | YES | Shared `useTopicFavoritesState` | Existing `topic-pilot-topic-favorites` key, normalized to versioned identities | Yes | Hydrates once from local storage and subscribes to shared change events | YES | Topic List ↔ Topic Detail | Existing topic empty/unavailable presentation remains | API refresh/error does not clear local topic identities | Clear label and `aria-pressed` retained | File was not edited because it was an active dirty workstream file |
| Topic Detail | YES | Shared `useTopicFavoritesState` | Same topic storage key and schema | Yes | Reads the stable topic slug through the shared hook | YES | Topic Detail ↔ Topic List | Detail remains usable when topic data is unavailable | Topic API state is independent from local toggle state | Button label, `aria-pressed`, keyboard/focus behavior | No server synchronization |
| Stock Explorer | YES | Shared `useFavoritesState` | Existing `topic-pilot-favorites` key, normalized to versioned identities | Yes | Hydrates shared stock snapshot; filters and controls use market-aware identity matching | YES | Explorer ↔ Stock Drawer | Existing list empty state remains; favorite filter reflects shared state | Stock data refresh/error does not clear identities | `FavoriteStar` has label and `aria-pressed`; control is keyboard reachable | Legacy code-only callers remain compatibility adapters |
| Stock Drawer | YES | Shared `useFavoritesState` | Same stock storage key and schema | Yes | Uses displayed stock code plus market stable identity | YES | Drawer ↔ Explorer | Drawer behavior remains bounded to selected identity | Formal data unavailable does not remove the favorite | Shared button semantics, clear add/remove label, `aria-pressed` | No remote watchlist |
| Favorites workspace/watchlist | YES | Shared stock/topic hooks | Same two existing storage keys; no market response is persisted | Yes | Local identities become visible as soon as local state hydrates; market data is independently resolved | YES | Reflects all supported surfaces | Retains identity rows even when data is unavailable; empty state directs users to browse and add items | API error/unavailable data is rendered as unavailable and never clears local favorites or silently converts to Preview | Tab/list controls use existing semantic buttons; favorite controls use shared semantics | A future richer unavailable-data affordance may improve identity rows |

## Supported Entity Types

`SUPPORTED_FAVORITE_ENTITY_TYPES=STOCK,TOPIC`.

No additional entity type was invented. Today currently has no favorite affordance, so it is not treated as a third supported type. The implementation can reject unknown entity types instead of silently conflating them.

## Identity and Persistence Contract

The minimal versioned identity contract is implemented in `apps/web/app/lib/favorites-view.mjs`:

```text
FavoriteIdentity {
  version: 1,
  entityType: STOCK | TOPIC,
  stableId: string,
  displayLabel?: string
}
```

- `STOCK` stable identity is market-aware: `MARKET:CODE` when market is known; code-only legacy values remain readable for compatibility.
- `TOPIC` stable identity is the canonical topic slug/id used by the current product surface.
- `displayLabel` is optional presentation metadata and is never the primary key.
- Entity type is part of matching, preventing a stock code and topic slug from colliding.
- Different stock markets do not match when both sides carry explicit market identity.
- Existing storage keys were retained: `topic-pilot-favorites` and `topic-pilot-topic-favorites`.
- Legacy string arrays are normalized into the versioned in-memory contract; new writes use `{version: 1, items: [...]}`.
- Malformed JSON, malformed items, unsupported versions/types, and storage access failures fail safe to an empty in-memory snapshot without crashing the UI.
- Only minimal local preference identity metadata is stored. Formal market data, API responses, secrets, and credentials are not persisted.

## Cross-Surface Sync

- Stock Explorer toggle → Stock Drawer: PASS.
- Stock Drawer toggle → Stock Explorer: PASS.
- Topic List toggle → Topic Detail: PASS through the existing shared topic hook.
- Topic Detail toggle → Topic List: PASS through the same store/event path.
- Favorites workspace reflects both supported entity types: PASS.
- Today sync: `NOT_APPLICABLE_NO_CURRENT_FAVORITE_AFFORDANCE`.
- Reload persistence: PASS through the existing local-storage family and versioned normalization.
- Entity switching: stable identity matching prevents stale state from carrying between selected stocks/topics.
- Remote/formal refresh: decoupled; refresh status cannot clear a local favorite.

## Failure, Reload, and Unavailable-Data Semantics

Favorite toggles do not depend on a currently available stock/topic response once a stable identity is known. API errors, unavailable formal data, and refresh transitions leave the local identity in place. The Favorites workspace no longer requires both market-data requests to resolve before showing locally stored identities, and it does not silently replace unavailable configured data with Preview data. An unavailable row may remain visible with an unavailable-data status.

Malformed or old local state is ignored safely, while valid identities remain usable. A storage write failure does not crash the surface; the shared in-memory snapshot remains coherent for the current session.

## UI and Accessibility

- Shared stock controls use `FavoriteButton`; V2 presentation controls use `FavoriteStar`.
- Active state is communicated with `aria-pressed`, not color alone.
- Labels distinguish adding from removing a favorite.
- Controls are real buttons with keyboard activation and visible focus behavior from existing tokens.
- Stock Explorer places the star beside the tile button rather than nesting interactive buttons.
- Responsive spacing reserves control room inside the stock tile so the star does not overflow or cover the main tile content.
- No global redesign or shared loading/error framework rewrite was introduced.

## Implementation Files

- `apps/web/app/lib/favorites-view.mjs` — versioned identity, normalization, matching, and serialization helpers.
- `apps/web/app/components/FavoriteButton.tsx` — shared local-device store, hydration, persistence, same-tab/cross-tab notification, and stock/topic hooks.
- `apps/web/app/components/v2/StockExplorerPage.tsx` — stock tile favorite affordance and market-aware filtering.
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx` — shared drawer control wiring.
- `apps/web/app/components/v2/TopicDetailPage.tsx` — Topic Detail shared favorite wiring.
- `apps/web/app/components/v2/V2Foundation.tsx` — shared favorite star accessibility semantics.
- `apps/web/app/components/v2/FavoritesWorkspacePage.tsx` — identity-first rendering and independent unavailable-data behavior.
- `apps/web/app/globals.css` — bounded responsive stock-tile control layout.
- `apps/web/tests/favorites.test.mjs` — identity, storage, malformed-state, and source-wiring coverage.

## Collision Handling with D/E

The exact-file audit found the Topic Detail workstream's existing dirty `TopicListPage.tsx`; it was not edited or staged. The Favorites implementation was kept in the shared store/helper and non-colliding Stock, Drawer, Topic Detail, Favorites workspace, and shared presentation files. The Stock readiness audit and Today reassessment were report/audit workstreams without an exact Favorites implementation collision. No isolation worktree was needed. All unrelated dirty and untracked files remain outside this task's write set.

## Tests and Validation

- Focused Favorites tests: PASS — 8/8 (`node --test tests/favorites.test.mjs`).
- Related Stock/Topic regression tests: PASS — 17/17.
- Full frontend source-contract tests: PASS — 115/115 (`node --test tests/*.test.mjs`).
- TypeScript: NOT PASS — direct compiler execution is blocked by the incomplete local dependency tree (`react`, `lucide-react`, and type packages are unavailable); one unrelated existing `TopicDetailPage` status-section type diagnostic also remains.
- Changed-file ESLint: NOT RUN — local ESLint executable/dependency is unavailable.
- Production build: NOT RUN — `npm run build` stops because `cross-env` is unavailable in the local dependency tree.
- Route smoke: `NOT_RUN_ENVIRONMENT_RESTRICTION`.
- `git diff --check`: PASS for the exact Favorites write set.
- Changed-file secret scan: PASS; no secret material was introduced.
- G1/G2/G3/Post-Close Canary: `PRESERVED PASS`; this frontend/local-device task did not rerun them.

## Documentation Reconciliation

- `docs/DAILY_PROGRESS.md`: updated with this completed shared Favorites local-state UX milestone.
- `PROJECT_CONTEXT.md`: not updated; its existing Favorites positioning and local-device boundary already match this task.
- `docs/ROADMAP.md`: not updated; existing roadmap already places Favorites in UI polish/shared state and no new priority decision is required.
- `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`: not updated; no product-scope change was introduced.
- `docs/WORK_ORDERS.md`: not updated; no duplicate task identity or new backend work order was created.
- `docs/DOCUMENTATION_INDEX.md`: not updated; this report is task closure, not a new architecture authority.
- No `NEXT_TASK` change.

## Remaining Favorites Gaps

- Today has no current favorite control, so there is no Today toggle to sync.
- There is no server/account sync or remote watchlist by design.
- Legacy code-only callers remain compatible but could be migrated to explicit market identity in a future bounded cleanup.
- Favorites list unavailable-data presentation can receive further copy/layout polish without changing the local-state contract.

## Final Status

`FAVORITES_SHARED_LOCAL_STATE_UX_COMPLETE`

The task stops here. No server sync, backend task, Recommendation work, technical/historical work, Today source-authority work, scheduler, deployment, merge, or push was started.
