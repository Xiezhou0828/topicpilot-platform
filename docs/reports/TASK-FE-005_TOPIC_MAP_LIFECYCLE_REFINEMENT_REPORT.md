# Topic Page UI Refinement｜Topic Map + Topic Lifecycle

**Status:** Implemented; validation and deployment pending
**Route:** `/topics`
**Scope:** Existing Topic Map and Topic Lifecycle presentation only

## 1. Files changed

- `apps/web/app/components/v2/TopicListPage.tsx`
- `apps/web/app/globals.css` — only `.tp-topic-*` rules were added or overridden
- This report

No shared navigation, backend, API contract, data model, scoring, lifecycle derivation, or other page implementation was changed.

## 2. Topic Map

- Kept the existing four lanes: `S｜市場主線`, `A｜重點觀察`, `B｜輪動題材`, `D｜等待確認`.
- Topic Tiles are now fixed-height single-row market-scan links: topic name on the left, score immediately before the direction arrow on the right.
- Topic names use restrained 14px semibold typography with ellipsis; scores use a restrained 14px tabular scale.
- Direction icons are plain `↑ / ↓ / →` glyphs with no circle, badge, button, or extra arrow. Existing Topic direction semantics remain separate from stock price colors.
- Desktop Lane height is `276px`; tablet and mobile use `260px` and `240px`. Lane bodies retain `overflow-y: auto` and keyboard focus, while `scrollbar-width: none` plus the WebKit zero-size scrollbar hides scrollbar chrome.
- The `全部 / 轉強 / 轉弱` filter computes `marketTopics` only. Lifecycle, group browse, and full topic list use the unfiltered `overviewTopics` set.

## 3. Lifecycle component structure

- Five equal Stage Panels remain visible side by side on desktop: `萌芽 / 發酵 / 主升 / 成熟 / 衰退`.
- Existing Lucide icons are used with equal size and stroke weight: `Sprout`, `Activity`, `TrendingUp`, `Crown`, and `TrendingDown`.
- Every Stage Header uses the same icon/title/hint structure and the same visual treatment.
- Topic content uses editorial list rows with subtle dividers, topic name, `Day N`, score, and direct Topic Detail links. No repeated lifecycle badges, descriptions, rounded cards, or heavy shadows are used.
- The default view shows up to four rows per stage. If a stage has more, it shows `查看另外 N 個 →`, where `N = total items - 4`. Clicking expands only that stage; the control changes to `收合 ↑`. Clicking again collapses it, and opening another stage closes the previous expansion.
- Lifecycle rows have no scrollbar. Expansion is local and keeps the five-column structure intact.

## 4. Lifecycle color implementation

- Stage icon and title use the existing `var(--tp-color-brand-primary)` token, which resolves to `#8A7462`.
- Stage panels use the existing `var(--tp-color-surface)` background and `var(--tp-color-border)` border. Headers use the shared `var(--tp-color-surface-muted)` treatment.
- All five stages use the same brand brown and the same neutral panel treatment. There is no stage-specific color mapping, gradient, opacity hierarchy, red/green lifecycle meaning, neon, glow, or new palette.
- The Help control uses the existing brand brown token as its circular background and white Lucide question mark stroke.

## 5. Help content

The Help dialog explains all five stages, `Day N` as consecutive days in the current lifecycle stage, and the disclaimer: `這只是市場狀態描述，不是買賣建議。`

`高檔整理` is displayed as `成熟`, `退潮` as `衰退`, and the non-lifecycle `觀察` presentation state is omitted rather than assigned to a new business stage. No backend lifecycle derivation is changed.

## 6. Existing Design System used

- Brand: `--tp-color-brand-primary` / `#8A7462`
- Page and surfaces: `--tp-color-page`, `--tp-color-surface`, `--tp-color-surface-muted`
- Text: `--tp-color-text-primary`, `--tp-color-text-secondary`
- Borders: `--tp-color-border`, `--tp-color-border-strong`
- Spacing rhythm: existing 8px token family, with 8px lane gaps and compact padding
- Typography: existing Noto Sans TC / Microsoft JhengHei stack; 14–15px editorial controls and 11px metadata
- Radius: `--tp-radius-sm` / `--tp-radius-md` (10px / 12px)
- Motion: existing `--tp-motion` (`200ms ease`)
- Shadow: no new shadow on Tile or Lifecycle rows; existing subtle surface shadow remains available to shared components only

## 7. Responsive behavior

- Desktop: four Topic Map lanes and five Lifecycle Panels are visible in one horizontal row.
- Tablet: Topic Map remains a two-column scan board; Lifecycle Panels use two columns with equal structure and no horizontal overflow.
- Mobile: Topic Map becomes one column; Lifecycle Panels stack vertically rather than forcing five narrow columns.

## 8. Verification

- `/topics` production build passed and route manifest includes `/topics` and `/topics/:slug`.
- Targeted ESLint for `TopicListPage.tsx` passed.
- `git diff --check` passed for the changed page and scoped stylesheet.
- Full `tsc --noEmit` remains blocked by pre-existing errors outside this scope (`data-source.ts`, `snapshot-store.tsx`, `watchlist`, `vite.config.ts`, and worker globals).
- Existing `npm test` build phase passed; the repository test suite currently reports 51 passing and 14 pre-existing failures tied to older route/source expectations outside this task.
- Public interaction verification remains to be recorded after the final deployment: filter isolation, hidden Lane scrollbar, Stage expansion, Help, and responsive checks.

## 9. Scope check

No Header / Navigation, group browse, full topic list, Topic Detail, Home, Stock, Favorites, Opportunity, AI Studio, backend, API contract, scoring, lifecycle derivation, or router files were changed for this refinement.
