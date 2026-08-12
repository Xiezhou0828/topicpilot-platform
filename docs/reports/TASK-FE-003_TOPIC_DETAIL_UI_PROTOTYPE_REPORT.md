# TASK-FE-003 Topic Detail UI Prototype Report

## Preview route

`/topics/ai-server`

The implementation is static Phase 1 UI only. It does not call formal Topic, Stock, News, lifecycle, scoring, or recommendation APIs.

## Information architecture

1. Breadcrumb and topic identity: `AI伺服器`, `S`, strength `92`, lifecycle `主升 · Day 4`, stock count `14 檔`, and local favorite action.
2. Short topic summary focused on why the topic is worth researching.
3. 題材生命圖 with five retail-readable stages, current marker, start date, and trading-day duration.
4. 題材歷程 with four meaningful mock transitions.
5. 題材內股票, separated into 代表股、核心股、關聯股 cards and compact list rows.
6. 題材新聞, collapsed by default and expandable with mock context items.
7. 題材關聯, using restrained heat cards linking to other `/topics/[slug]` mock routes.
8. Bottom rectangular market-topic heat map.

## Mock Data used

- Topic identity: AI伺服器, S, strength 92, state 全面走強, 主升 Day 4, 14 stocks.
- Lifecycle: 萌芽、發酵、主升、高檔整理、退潮 with dates and trading-day durations.
- History: 7/01 聚焦、7/03 升 A、7/06 升 S、今天維持主升.
- Stocks: 廣達、鴻海、緯穎、緯創、奇鋐、華通 with mock price, change, role, and readable status.
- News: three concise mock context items.
- Related topics: CPO、高速傳輸、BBU.
- Heat map: six restrained topic rectangles with relative mock strengths.

## Interaction boundaries

- Favorite state is local prototype state.
- Clicking any stock row opens the 560px Stock Detail Drawer mock.
- News is collapsed initially and expands on click.
- Related topic cards navigate to another mock Topic Detail route.
- No hover drawer, Topic Peek, animation system, API wiring, scoring, or recommendation logic was added.

## Validation

- `npm run web:lint` — passed.
- `npm run web:build` — passed.
- Desktop route smoke — `/topics/ai-server` renders the shared shell and active 題材 navigation.
- Section audit — identity 1, lifecycle 1, history 1, role cards 3, news 1, related cards 3, heat map 1, stock rows 6.
- News default — collapsed.
- Interaction audit — favorite toggles, stock drawer opens/closes, news expands.
- Mobile CSS confirmation — at `max-width: 760px`, identity stacks, lifecycle becomes vertical, role/related cards stack, and heat map becomes a two-column grid.

## Screenshots

- [Desktop first screen](TASK-FE-003_TOPIC_DETAIL_DESKTOP_FIRST_SCREEN.png)
- [Desktop full capture](TASK-FE-003_TOPIC_DETAIL_DESKTOP_FULL.png)
- [Public Preview first screen](TASK-FE-003_TOPIC_DETAIL_PUBLIC_FIRST_SCREEN.png)

## Spec sync

`TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` now records the `/topics/[slug]` Phase 1 prototype route, mock-data boundary, frozen section order, and limited interaction scope.
