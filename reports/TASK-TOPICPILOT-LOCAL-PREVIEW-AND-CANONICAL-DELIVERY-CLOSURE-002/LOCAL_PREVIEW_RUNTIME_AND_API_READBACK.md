# Local Preview Runtime and API Readback

## Runtime

- Frontend Preview: `http://localhost:4318`
- Local API: `http://127.0.0.1:8001`
- Preview mode: iterative, read-only proxy.
- Financial API origin: explicitly supplied as a separate Preview configuration value; no Production origin was used.
- Research Read Model: no formal file configured, so the public research route fails closed.

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

The new Preview opened at `http://localhost:4318/stocks/1303?tab=fundamental`. When the formal stock snapshot was unavailable, the UI showed the explicit data-unavailable state and did not invent a stock or published research package. This is the expected fail-closed behavior. Exact viewport automation was not used; `RESPONSIVE_ACCEPTANCE=PARTIAL_VIEWPORT_NOT_CONFIGURABLE`.

`LOCAL_PREVIEW_STATUS=PASS_FAIL_CLOSED`
