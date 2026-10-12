# Local Preview Runtime and API Readback

## Runtime

- User-visible Frontend Preview: `http://localhost:4317`
- Acceptance surface: the existing implemented frontend Preview, not the temporary isolated 4318 process.
- 4318 status: stopped and browser tab closed; excluded from acceptance.
- Backend readback harness: `http://127.0.0.1:8001` was used only for isolated read-only API verification and is not the user-facing Preview URL.
- No Production origin, write route, migration, or database write was used.

## HTTP readback

| Endpoint | Result |
|---|---|
| `/healthz` | HTTP 200 |
| `/api/v2/stocks/1303/research` | HTTP 200, `publication_status=NOT_CONNECTED`, empty sections |
| `/api/v2/stocks/1303/financial-summary` | HTTP 200, `status=AVAILABLE` |
| `/api/v2/stocks/1303/financial-coverage` | HTTP 200, rights/status envelope retained |
| `/api/v2/stocks/1303/financial-statements` | HTTP 200 |
| `/api/v2/stocks/1303/financial-research-status` | HTTP 200, `publication_status=NOT_PUBLISHED` |
| `/api/v2/stocks/1303/eps-bridge` | HTTP 200 |

## Browser readback

The existing implemented Preview was read at `http://localhost:4317/stocks/1303?tab=fundamental`. It rendered the actual Chinese Company Research surface for 南亞 1303, including 公司研究概況、產品與營收結構、重要轉投資、產業鏈與競爭位置、成長驅動與主要風險、財報與法說會補充，以及研究來源與資料限制。 The page retained the implemented stock header, navigation, tabs, cards, source links, and fail-closed wording for unavailable fields.

`4317_PREVIEW_ACCEPTANCE=PASS`
`4317_PREVIEW_IS_CANONICAL_USER_VISIBLE_SURFACE=YES`
`4318_PREVIEW_ACCEPTANCE=EXCLUDED`
Exact viewport automation was not used; `RESPONSIVE_ACCEPTANCE=PARTIAL_VIEWPORT_NOT_CONFIGURABLE`.

`LOCAL_PREVIEW_STATUS=PASS_FAIL_CLOSED`
