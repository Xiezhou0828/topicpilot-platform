# TASK-FE-005｜Topic Overview UI Refinement V3 Report

**Status:** Implemented; validation and deployment pending
**Route:** `/topics`
**Product role:** Market Scan first; Topic Lifecycle is a separate lifecycle-reading surface.

## 1. Product and information architecture changes

- Removed the duplicate `題材` page title from the content header. The shared navbar remains the location indicator.
- Kept only `今日題材地圖` as the first content heading and removed page-introduction copy.
- Direction filters `全部 / 轉強 / 轉弱` now control only the Market Lane.
- Topic Lifecycle and the complete topic index read from the unfiltered overview topic set, so the Market Lane filter cannot hide lifecycle or index content.

## 2. Market Lane redesign

- Preserved the four semantic lanes: `S｜市場主線`, `A｜重點觀察`, `B｜輪動題材`, and `D｜等待確認`.
- Reduced the lane height and card height to increase first-screen information density.
- Kept internal lane scrolling but hides the browser scrollbar chrome while preserving wheel, touch, and keyboard scrolling.
- Kanban cards now contain only the topic name, one neutral topic-direction symbol, and today's score. The card itself remains the direct Topic Detail link.
- Direction symbols use a stronger circular treatment and remain separate from Taiwan stock price colors.

## 3. Topic Lifecycle redesign

- Renamed the section to `題材生命週期` and added a clickable Help icon.
- Help content explains the five lifecycle meanings: `萌芽`, `發酵`, `主升`, `成熟`, and `衰退`.
- Removed `觀察` from the displayed lifecycle taxonomy. Existing Preview `觀察` records are normalized into the earliest displayed stage so no topic disappears from the lifecycle view.
- Renamed `高檔整理` to `成熟` and `退潮` to `衰退` at the Overview presentation layer.
- Replaced the second Kanban-like card grid with a horizontal process timeline: connected stage markers, stage columns, and minimal topic rows.
- Lifecycle rows contain only topic name, `Day X`, today's score, and a direct Topic Detail link. No stage name or research description is repeated inside a row.
- Lifecycle rows are not affected by the Market Lane direction filter.

## 4. Scope boundary

Only `/topics` Overview presentation and its local Preview presentation mapping were changed. No Topic Detail layout, Home, Stock, Favorites, Opportunity, Router, API schema, backend, database model, or scoring logic changes are included.

## 5. Verification plan

- Targeted ESLint and `git diff --check` for changed Overview files.
- `npm run build` with `/topics` and `/topics/:slug` route manifest checks.
- Public structure audit for header removal, filter scope, four lanes, hidden lane scrollbars, compact cards, five lifecycle stages, Help dialog, and absence of `觀察` / `市場輪動`.
- Public interaction audit for Market Lane filtering, unchanged lifecycle contents under filter, Help open/close, lifecycle Detail links, group navigation, list search, and favorites.

## 6. Unchanged surfaces

Topic Detail remains the deep-research surface. Group browsing, full topic list search, favorites, grade filtering, and Detail routing remain available on Overview.
