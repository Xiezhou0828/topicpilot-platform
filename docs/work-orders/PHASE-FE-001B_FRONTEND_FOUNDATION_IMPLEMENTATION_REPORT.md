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
- Deployed to the existing Sites project at [topicpilot-platform.game0962046460.chatgpt.site](https://topicpilot-platform.game0962046460.chatgpt.site/).
- Saved Sites version: `4`; deployment completed successfully from commit `021bdcd44d3513bc6a629c39d7db003f6bb3dfe3`.
- Browser smoke passed for `/`, `/topics`, `/stocks`, `/favorites`, `/opportunities`, and `/ai-studio`: each returned its expected URL, one matching page heading, and the full primary navigation.
- Browser smoke passed for retained operational routes `/market`, `/watchlist`, `/guide`, `/studio`, `/topics/intelligence`, and `/stocks/2330`; no 404/not-found body was observed.
- Global search shell interaction passed: trigger opened the disabled-search popover with the expected pending copy and close control.
- Desktop visual review completed at the deployed URL; V2 rendered with warm off-white background, white surfaces, restrained borders, `#8A7462` brand, and no neon/glass/gradient treatment.

## Explicitly deferred

Home, Topic, Stock, Favorites, Opportunity, and AI research business logic; search integration; API wiring; real tables; scoring; lifecycle/heatmap derivation; recommendation content; and V1 visual migration are deferred to later phases.

## Deployment and rollback

- Customer-facing V2 routes are live at the existing PM-accessible URL above.
- The published site is versioned in Sites; rollback can be performed by redeploying the prior saved version (`3`) from the same Sites project.
- Backend services, PostgreSQL, collector, scheduler, credentials, and V1 data workflows were not changed by this cutover.
- PHASE-FE-002 business implementation was not started.
