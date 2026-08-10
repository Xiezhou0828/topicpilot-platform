# TASK-FE-002D Home Market Summary Density Report

## Result

Only the `今日市場重點` Card was adjusted. No other Home section, Header, data content, or business logic was changed.

## Changes

- Changed the three market-focus messages from four separate rows to one responsive inline reading row.
- Added semi-bold emphasis to `AI伺服器`, `BBU`, and `機器人`.
- Removed the duplicated `今日觀察：AI是否開始向其他族群擴散。` sentence.
- Kept `今日一句話：今天研究重心：觀察 AI 是否開始擴散。` as the PM research direction.
- Reduced the rendered Card height from `207.6px` to `137.6px`, a `70px` / `33.7%` reduction.

## Visual evidence

- Before: [TASK-FE-002D before first screen](TASK-FE-002D_HOME_BEFORE_FIRST_SCREEN.png)
- After: [TASK-FE-002D updated first screen](TASK-FE-002D_HOME_AFTER_FIRST_SCREEN.png)
- Full desktop capture: [TASK-FE-002D desktop full screenshot](TASK-FE-002D_HOME_DESKTOP_FULL.png)

The before/after comparison shows the three scan-friendly inline bullets, bold topic names, removal of the repeated observation sentence, and the shorter Card.

## Verification

- `npm run web:lint` — passed.
- `npm run web:build` — passed.
- `今日市場重點` items — 3.
- Bold topics — `AI伺服器`, `BBU`, `機器人`.
- `今日觀察` — absent.
- `今日一句話` — present.
- Unchanged section counts — 市場概況 1, 今日主線 3 cards, 盤中重要事件 1, rotation 2 cards, 今日機會 1.
