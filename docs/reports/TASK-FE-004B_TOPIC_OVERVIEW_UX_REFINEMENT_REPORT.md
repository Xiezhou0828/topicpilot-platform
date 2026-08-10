# TASK-FE-004B｜Topic Overview UX Refinement V2 Report

**Status:** Implemented; deployed and verified
**Route:** `/topics`
**Product role:** Market Scan first; Topic Detail remains the research surface.

## 1. Implemented UX refinement

- Removed the Topic Overview eyebrow and explanatory 10-second teaching copy from the page header.
- Removed the duplicate local search from the page header. Global Search remains in the shared App Shell.
- Moved `全部 / 轉強 / 轉弱` into the `今日題材地圖` header row and kept the Preview badge at the far right.
- Removed the Market Rotation section from Topic Overview because its event-summary role overlaps with Home's intraday events.
- Reworked the Kanban into a fixed-height Market Lane with compact scrollable lane bodies.
- Changed lane labels to `S｜市場主線`, `A｜重點觀察`, `B｜輪動題材`, and `D｜等待確認`.
- Reduced Kanban card padding, height, and type scale so more topics remain visible at once.
- Reduced direction presentation to one symbol only: `↑`, `↓`, or `→`, with a separate topic-direction rail that does not reuse stock price red/green semantics.
- Added a horizontal `Topic Lifecycle` stage timeline with `萌芽 / 發酵 / 主升 / 高檔整理 / 退潮 / 觀察` columns.
- Lifecycle items are compact chips containing only topic name, `Day X`, today's score, and a direct Topic Detail link.
- Preserved `依大族群瀏覽` and `全部題材`, including search, favorites, direction filtering, grade filtering, and Detail routing.

## 2. Scope boundary

The Overview no longer presents lifecycle descriptions, rotation event copy, news, constituents, representative stocks, related-topic research, market commentary, or extra KPI summaries. Topic Detail retains the existing deep-research sections.

## 3. Data contract

Topic identity, grade, score, group, state, data date, and constituent count continue to use the formal Topic API when configured. Lifecycle stage/day metadata is Preview Data because the current formal Topic contract does not expose lifecycle stages. The lifecycle section is explicitly marked `Preview（Mock Data）· 等待正式 Read Model`.

## 4. Verification plan

- Targeted ESLint for changed Overview files.
- `npm run build` with `/topics` and `/topics/:slug` route manifest checks.
- Public DOM audit for header simplification, four fixed lanes, single direction symbols, absence of Market Rotation, lifecycle stages, and preserved group/list controls.
- Public interaction audit for direction filtering, lifecycle Topic Detail links, group collapse/expand, list search, favorites, and grade filtering.

## 5. Final verification result

- Production build passed; targeted ESLint passed for the changed Overview files; `git diff --check` passed.
- Public release 22 passed structure audit: four lanes at `332px`, six lifecycle stages, no Market Rotation, and the Preview label `Preview（Mock Data）· 等待正式 Read Model`.
- Public interaction audit passed for `轉強 / 轉弱`, list search (`AI伺服器` → one row), favorite toggle, group expand/collapse, and lifecycle Detail routing.
- Deployed to `https://topicpilot-platform.game0962046460.chatgpt.site/topics`.

## 6. Unchanged surfaces

No Home, Stock, Favorites, Opportunity, V1 business page, backend schema, scoring logic, or Topic Detail research layout changes are included in this work order.
