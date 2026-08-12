# TASK-FE-002E Home Final Fix Report

## Scope

Only the Home first-screen presentation was adjusted. Market values, Today Focus copy, section order, Header, Topic Detail, and all downstream Home sections remain unchanged.

## Changes

- Removed the `盤中快照` helper text below `更新時間`; `10:48` remains the sole value in that field.
- Removed the `01／02／03` ordinal labels from the three `今日主線` cards.
- Preserved each card's topic name, state, grade chip, detail, and `進入題材頁` action.
- Tightened only the approved Home first-screen spacing and compact card geometry so the three full mainline cards are visible without scrolling at the approved desktop viewport.

## Visual evidence

- Before: [TASK-FE-002E before first screen](TASK-FE-002E_HOME_BEFORE_FIRST_SCREEN.png)
- After: [TASK-FE-002E after first screen](TASK-FE-002E_HOME_AFTER_FIRST_SCREEN.png)
- Public after deployment: [TASK-FE-002E public first screen](TASK-FE-002E_HOME_PUBLIC_AFTER.png)
- Full capture: [TASK-FE-002E desktop full screenshot](TASK-FE-002E_HOME_DESKTOP_FULL.png)

## Verification

- `npm run web:lint` — passed.
- `npm run web:build` — passed.
- `盤中快照` helper text — absent.
- `tp-home-card-index` elements — 0.
- Mainline cards — 3.
- At the measured desktop viewport `1280 × 720`, all three mainline card bottoms are `709px`, inside the first screen.
- Market overview, Today Focus, and mainline sections remain present.
- Public URL audit — helper text 0, card indices 0, mainline cards 3, and all card bottoms at 709px within the 1280×720 first screen.
