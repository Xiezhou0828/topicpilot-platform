# TASK-FE-016 Stock Explorer Push Panel Refinement Report

**Status:** Implemented; deployed and verified
**Route:** `/stocks`
**Product role:** Stock Explorer / Stock Encyclopedia workspace
**Scope:** `/stocks` presentation only. No Home, Topic Overview, Topic Detail, backend API, database, or API contract changes.

## 1. Root cause

The Stock Explorer already rendered the encyclopedia beside the stock list in the same React workspace, but the shared `inline` presentation was overridden by later CSS rules:

- `.tp-stock-encyclopedia-drawer--inline` was forced to `position: fixed` with `right: 0`.
- The workspace `:has()` rules collapsed the page back to a single-column layout when the drawer opened.
- `selected` was cleared immediately on close, so the drawer could not play a reverse exit animation.

The result looked like an overlay drawer even though the component appeared inside the workspace DOM. The stock list did not truly reflow.

## 2. Implemented design

### Desktop push workspace

- Added a `/stocks`-only `push` presentation for the shared Stock Encyclopedia drawer.
- The desktop workspace transitions from one column to `minmax(0, 1fr) minmax(340px, 38%)`.
- The stock list remains visible and compresses to make room for the encyclopedia panel.
- The desktop panel is an in-flow `position: sticky` panel anchored below the shared 72px navigation bar; it is not `fixed` or `absolute`.
- The panel is capped at 560px so the stock grid keeps useful reading width.

### Stable interaction and motion

- Opening a tile sets the selected stock and opens the panel.
- Selecting another tile replaces the panel content directly without close/reopen repetition.
- Closing keeps the panel mounted for 280ms, plays the reverse `translateX` motion, then returns to the full-width grid.
- Escape and the close button use the same close path.

### Responsive behavior

- Desktop uses the true push layout.
- At widths below 860px, the panel becomes a full-height right-side fallback so the stock grid is not forced into an unusable split.
- The encyclopedia header remains fixed within the panel while the body scrolls internally.
- The page was checked for horizontal overflow at both desktop and narrow viewport sizes.

## 3. Files changed

- `apps/web/app/components/v2/StockExplorerPage.tsx`
  - Added open/closing/closed panel state.
  - Added the `/stocks` push workspace marker and stable close timing.
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
  - Added `presentation="push"` without changing existing `overlay` or `inline` consumers.
  - Removed modal semantics from non-overlay presentations.
- `apps/web/app/globals.css`
  - Added scoped push-grid, sticky panel, motion, internal scroll, and responsive rules.

The frontend design specification already contains the Stock Encyclopedia direction and the requirement that selecting a stock compresses/pushes the grid. This implementation closes the remaining visual gap between that specification and the actual `/stocks` behavior.

## 4. Scope boundary

Only the Stock Explorer presentation and its shared drawer presentation contract were changed. No stock API fetch behavior, sorting semantics, live update cadence, data model, backend, Home page, Topic Overview page, Topic Detail page, Favorites page, or production API contract was modified.

## 5. Verification

- `npm run build`: passed.
- `npm run lint -- --no-cache`: passed.
- `npx tsc --noEmit`: passed.
- Targeted `git diff --check`: passed.
- Public route: `https://topicpilot-platform.game0962046460.chatgpt.site/stocks`.

## 6. Final 12-item acceptance result

1. **Route loads:** PASS — public `/stocks` loaded successfully.
2. **No-selection state:** PASS — the workspace starts as one full-width stock grid.
3. **Desktop click opens encyclopedia:** PASS — a tile opens the right-side panel without navigation.
4. **Desktop list reflows:** PASS — at 1280px viewport, the list measured about 729px and the panel about 456px.
5. **Desktop panel is not overlay-positioned:** PASS — computed desktop position is `sticky`; no fixed/absolute desktop rule is used.
6. **Panel stays below the global header:** PASS — after page scroll, panel top and navigation bottom both measured 72px.
7. **Panel body scrolls internally:** PASS — body measured 1,048px scroll height versus 468px client height and accepted internal scroll.
8. **Close returns to full grid:** PASS — close interaction returns to `closed`, removes the panel, and restores the single-column grid after the 280ms close path.
9. **Switching stocks is stable:** PASS — selecting a second tile replaced the encyclopedia identity in place while the panel remained open.
10. **Narrow responsive fallback:** PASS — at 760px, the panel used the narrow-screen fixed fallback at 560px wide and remained below the 72px header.
11. **Horizontal overflow:** PASS — desktop and 760px checks reported no horizontal overflow.
12. **Regression/scope boundary:** PASS — build, lint, typecheck, and targeted diff checks passed; only the three Stock Explorer UI files were included in the deployed release.

## 7. Deployment result

The validated frontend was published to the existing TopicPilot Site. The requested page is live at:

`https://topicpilot-platform.game0962046460.chatgpt.site/stocks`
