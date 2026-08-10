# TASK-FE-HEADER-002 — Global Header Information Architecture

**Status:** `IMPLEMENTED / READY FOR PM VISUAL REVIEW`
**Generation:** `NEXT / V2`
**Scope:** Desktop V2 Header layout only

## 1. Header before / after

### Before — TASK-001C

- Logo and navigation were rendered as siblings while navigation occupied the flexible center area.
- The navigation used `flex: 1` with `justify-content: center`, creating a SaaS-style centered composition.
- Search was 292px wide, which pushed the right controls farther toward the viewport edge.

Reference: [TASK-001C desktop screenshot](TASK-001C_GLOBAL_HEADER_DESKTOP.png)

### After — TASK-FE-HEADER-002

- Header is explicitly split into `.tp-header-left` and `.tp-header-right` groups.
- Left Group contains the TopicPilot logo and all primary navigation, kept naturally close to the logo.
- Right Group contains Global Search, Notification, and Account, aligned with `margin-left: auto`.
- Navigation no longer uses centered flex layout.
- Search is shortened to 276px, within the PM-approved 260–300px range.

## 2. Desktop screenshot

[Open the updated TASK-FE-HEADER-002 desktop screenshot](TASK-FE-HEADER-002_DESKTOP.png)

The updated screenshot shows the financial-information-platform composition: logo plus navigation on the left, tools on the right, and no added feature or page content.

## 3. Spacing adjustments

- Replaced centered navigation flex behavior with `flex: 0 1 auto` and `justify-content: flex-start`.
- Added a 28px logo-to-navigation group gap.
- Preserved 22px navigation item spacing.
- Kept the Right Group pinned to the right with `margin-left: auto`.
- Reduced Global Search from 292px to 276px.
- Preserved the existing 72px header height, colors, tokens, borders, and icon sizes.
- No Home/content vertical rhythm or page layout was changed.

## 4. Implementation files

- `apps/web/app/components/v2/V2Foundation.tsx`
  - Added explicit Left Group and Right Group wrappers in `PrimaryNav`.
  - No route, behavior, or business logic changes.
- `apps/web/app/globals.css`
  - Adjusted only V2 `tp-` header layout rules, group spacing, nav weights, and search width.
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`
  - Added/updated **Global Header Information Architecture — FROZEN / PM-APPROVED / TASK-FE-HEADER-002**.

## 5. Boundary confirmation

- No backend changes.
- No API or route changes.
- No schema, database, scoring, recommendation, or data-flow changes.
- No V1 changes.
- No business logic or 今日市場 content development started.
- Design tokens, brand color, and existing Modern Financial Workspace styling were preserved.

## 6. Validation

- `npm run lint` — passed with zero errors and zero warnings.
- `npm run build` — passed through the vinext production pipeline.
- Local desktop DOM smoke — all six V2 routes rendered exactly one Left Group, one Right Group, one active navigation item, and zero duplicate utility rows.
- Local geometry smoke — Left Group starts at 32px and ends before the Right Group; Right Group ends at 1233px; search width is 276px.
- Local interaction smoke — Search, Notification, and Account controls opened successfully; Account menu contained all five PM-frozen items.
- Retained route smoke — `/market`, `/watchlist`, `/guide`, `/studio`, `/topics/intelligence`, and `/stocks/2330` returned without 404/not-found content.
