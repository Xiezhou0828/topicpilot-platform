# PHASE-FE-001B Frontend Foundation Implementation Report

**Status:** B-stage complete; stopped before PHASE-FE-001C
**Repository:** `C:\Users\acer\Desktop\題材領航\topicpilot-platform`

## Delivered

- Added an isolated, scoped V2 light-mode app shell under `apps/web/app/components/v2`.
- Added frozen primary IA: 今日市場 / 題材 / 股票 / 收藏 / 機會 / AI研究室.
- Added `/ai-studio` as the AI research entry route.
- Added utility bar with global search shell, notification, settings, and help placeholders.
- Added desktop-first page container with a 1600px content maximum.
- Added semantic V2 tokens in `apps/web/app/styles/v2-tokens.css`:
  brand `#8A7462`, warm off-white page, white surfaces, warm gray text/borders, restrained warning/error colors, 10/12px radii, 8px rhythm, subtle shadow, 200ms ease, 560px drawer token, and typography baseline.
- Added shared primitives: Surface, Card, Table, Button, IconButton, Tabs, SegmentedControl, GradeChip, RoleChip, FavoriteStar, Freshness, Tooltip, SearchInput, Skeleton, EmptyState, and DataState.
- Added semantic data states: AVAILABLE, STALE, UNAVAILABLE, PROVIDER_ERROR, 盤中更新, 盤後更新, 資料待更新.
- Added placeholder routes for `/`, `/topics`, `/stocks`, `/favorites`, `/opportunities`, and `/ai-studio` with no business data or browser-side scoring.

## Boundary decisions

The existing root, topics, favorites, and stock-index route files were replaced with shell-only V2 placeholders because those exact paths are the PM-approved V2 entry paths and Next App Router cannot have two owners for the same URL. Existing V1 detail, market, watchlist, guide, studio, intelligence, and admin routes remain in place. No API, provider, schema, scoring, or data workflow was changed.

V1 styles remain in `globals.css` for operational routes; V2 styles are scoped with the `tp-` prefix and use the new token layer. No neon, AI gradient, glow, glassmorphism, or heavy V2 shadow was added.

## Verification

- `npm run lint` — passed with 0 errors and 0 warnings after cleanup.
- `npm run build` — passed; vinext generated all requested V2 routes and existing retained routes.
- No visual screenshot was generated in this pass because the request did not provide a running browser/session; the build is ready for the PM visual review.

## Explicitly deferred

Home, Topic, Stock, Favorites, Opportunity, and AI research business logic; search integration; API wiring; real tables; scoring; lifecycle/heatmap derivation; recommendation content; and V1 visual migration are deferred to later phases.
