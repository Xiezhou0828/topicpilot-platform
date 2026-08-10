# TASK-001C — TopicPilot V2 Global Header / App Shell Freeze

**Status:** `COMPLETE / PM FREEZE IMPLEMENTED`
**Generation:** `NEXT / V2`
**Scope:** Desktop customer frontend only

## A. Header before / after

### Before

- Primary navigation was rendered as one row with a desktop hamburger.
- Search, notification, settings, and help were rendered in a second utility row.
- Search was visually separated from the primary navigation.
- Settings and help were separate header controls.
- The two-row structure created excessive vertical distance before 今日市場 content.

### After

- One shared 72px sticky V2 header is used by every V2 customer route.
- Left: TopicPilot wordmark.
- Center: 今日市場 / 題材 / 股票 / 收藏 / 機會 / AI研究室.
- Right: 292px Global Search, Bell notification control, Account control.
- Desktop hamburger, duplicate utility row, settings icon, and help icon were removed.
- Page content now starts with a compact 28px top rhythm; freshness remains inside 今日市場 content.

## B. Updated desktop screenshot

[Open the updated desktop header screenshot](TASK-001C_GLOBAL_HEADER_DESKTOP.png)

The screenshot was captured from the locally verified desktop V2 shell at 1280px viewport width. The published site HTML was separately checked over HTTPS and contains the same new header labels.

## C. React components changed

Modified `apps/web/app/components/v2/V2Foundation.tsx`:

- `GlobalSearchShell`: moved into the single header; placeholder is `搜尋股票、題材...`; preserves `Ctrl K` and dummy search behavior.
- `NotificationPlaceholder`: Bell toggle with a future-facing notification panel placeholder.
- `AccountMenu`: account dropdown with the PM-frozen menu items.
- `PrimaryNav`: now owns the complete shared header layout.
- `AppShell`: renders one header and the page main content; removed the second `UtilityBar` render.
- Removed the desktop hamburger and the Settings/Help controls from V2 header composition.

## D. CSS / styling changed

Modified `apps/web/app/globals.css` within the `tp-` V2 scope:

- Sticky single-header layout and 72px height.
- 292px search field width.
- Compact page top rhythm.
- Account outline control and dropdown.
- Notification placeholder panel.
- Restrained hover/focus states using existing warm-neutral tokens.
- No new gradient, glass, neon, glow, or heavy-shadow treatment.

No Tailwind configuration or backend-facing styling contract was changed.

## E. Design spec changed

Updated `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` with a new **Global Header Freeze — FROZEN / PM-APPROVED / TASK-001C** section covering:

- Header layout and desktop navigation.
- Global Search location, width, placeholder, and dummy/API boundary.
- Notification placeholder and future semantics.
- Account dropdown contents and deferred authentication.
- Desktop hamburger removal.
- Removal of the duplicate utility row.
- Freshness remaining in 今日市場 content.
- Compact financial-workspace vertical rhythm and style constraints.

## F. Intentionally not implemented

- Search API, result ranking, search navigation, and backend search contract.
- Notification API or real notification records.
- Login, account creation, membership state, or authentication.
- Real Settings, Help, or Feedback workflows; menu entries are placeholders.
- Home/Topic/Stock/Favorites/Opportunity business content.
- Any recommendation, scoring, lifecycle, ranking, or data inference.

## G. Boundary confirmation

- V1 customer and operational routes were not changed by this task.
- Backend source was not modified by this task.
- API contracts and generated API behavior were not modified by this task.
- Database schema, migrations, scoring, recommendation, and data workflows were not modified by this task.
- Only the V2 header component, V2-scoped CSS, canonical V2 frontend spec, and this report/screenshot were added or changed for TASK-001C.

## Validation evidence

- `npm run lint` — passed with zero errors and zero warnings.
- `npm run build` — passed through the vinext production pipeline.
- Local desktop smoke — all six V2 routes rendered one `.tp-primary-nav`, zero `.tp-utility` rows, and one active nav item.
- Local interaction smoke — Search opened with one `搜尋股票、題材...` input; Notification opened `通知中心`; Account opened all five PM-frozen menu items; hamburger/settings/help controls were absent.
- Retained route smoke — `/market`, `/watchlist`, `/guide`, `/studio`, `/topics/intelligence`, and `/stocks/2330` returned without 404/not-found content.
- Published HTTPS smoke — all six V2 routes returned HTTP 200 with the new header text and without the removed hamburger/old search labels.
- Published Sites version: `6`, deployed successfully to `https://topicpilot-platform.game0962046460.chatgpt.site`.
