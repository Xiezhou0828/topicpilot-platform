# TASK-DEPLOY-017｜Public FastAPI Origin & V2 Sites Runtime Integration

**Generation:** NEXT / V2  
**Date:** 2026-08-12  
**Status:** `BLOCKED — required external deployment resources are not present`  
**Scope:** public FastAPI origin, CORS, Sites environment, deployment and production runtime verification only.

## 1. Executive Summary

The requested public data chain could not be completed in this run because no
deployed TopicPilot FastAPI origin or deployment credentials are available.
The repository contains a documented Render blueprint. Its production startup
boundary now runs migrations and Uvicorn without importing a synthetic bundle.
No Render service, deploy hook, `DATABASE_URL`, or GitHub deployment
environment is discoverable from the connected repository account. The
candidate `https://topicpilot-api.onrender.com` returns HTTP 404 for all three
TopicPilot health/OpenAPI routes.

The existing Sites project is real and reachable, but its environment contains
only `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=true`; `NEXT_PUBLIC_API_BASE_URL` is not
configured. Production browser evidence therefore remains exactly the expected
fail-closed boundary:

- `/topics`: formal API unavailable message, no synthetic catalog.
- `/stocks`: four-row Preview snapshot, not the 507-row formal universe.

No production environment, database, Sites version, application code, UI,
business rule, score/grade/lifecycle/recommendation logic, or `NEXT_TASK` was
changed by this task. The release workflow was hardened with a read-only
formal-API/CORS gate; it does not deploy or change runtime state. This report is
the handoff artifact. `AI_WORKLOG.md` does not exist in the
V2 repository and the repository governance explicitly says not to create it
without an identified owner and migration plan; therefore no ungoverned
worklog file was added.

## 2. Root Cause

The break is between the public Sites bundle and the FastAPI origin, not in the
catalog/read-model code:

```text
V2 PostgreSQL/read models (local evidence: 130 topics, 507 stocks)
                         ↓
                 FastAPI public origin  ← missing / unverified
                         ↓
                  Sites NEXT_PUBLIC_API_BASE_URL  ← absent
                         ↓
 /topics = formal unavailable       /stocks = labelled 4-row Preview
```

The frontend correctly fails closed when a production API origin is absent.
Adding a guessed URL or a temporary tunnel would violate the requested data
boundary and was not done.

## 3. Current Deployment Topology

| Layer | Repository/config evidence | Actual verified state |
|---|---|---|
| PostgreSQL | `compose.yaml`, `docs/operations/deployment.md` | Local Docker topology documented; no listener on 5432 in this run; formal 130/507 counts are prior local runtime evidence, not newly re-established here. |
| FastAPI | `services/api`, `infra/docker/api.Dockerfile` | No listener on port 8000 in this run. |
| Render | `render.yaml` service `topicpilot-api`, Singapore, free Docker web, `$PORT`, `/readyz` | No GitHub Render deploy hook, deployment environment, or service evidence available. Candidate public hostname returns 404/timeout. |
| Sites | `.openai/hosting.json` project `appgprj_6a6ce02bd75c81919ab3678ebf013c53` | Existing public site is reachable; environment has only demo fallback. |
| Database connection source | `DATABASE_URL` is `sync: false` in `render.yaml` | No value is available in repository, GitHub repo variables/secrets, or the current process environment. |

The current Render command is now a formal-only startup boundary:

```text
alembic upgrade head
uvicorn topicpilot_api.main:app ...
```

The command no longer imports `/fixtures/demo`. The external service still must
be verified against an approved formal database before it can be presented as
the requested public authority.

## 4. Public FastAPI Origin

**Verified origin:** none.

The documented hostname `https://topicpilot-api.onrender.com` was checked with
PowerShell on 2026-08-12:

| Route | Result |
|---|---:|
| `/healthz` | 404 |
| `/readyz` | 404 |
| `/openapi.json` | 404 |

This is not sufficient evidence of a TopicPilot service and was not wired into
Sites.

GitHub checks were also read-only:

- `gh auth status`: authenticated as `Xiezhou0828`.
- Repository environments: `total_count=0`.
- `production-web` variables: endpoint 404 because the environment does not exist.
- Repository-level variables and secrets: none listed.
- `deploy.yml` workflow runs: none.

## 5. HTTPS / Health / OpenAPI Evidence

No public origin passed any acceptance route. Consequently the required
`/readyz`, `/openapi.json`, `/api/v2/topics`, `/api/v2/stocks`, topic-detail,
2330-detail, and 6806-detail checks are **not run against a verified public
FastAPI service**. A 404 candidate hostname cannot be used as API evidence.

## 6. PostgreSQL Authority Evidence

The prior task reports record local V2 evidence of 130 enabled topics and 507
formal TPE/TWO instruments (506 priced, one null-price). Those reports are
consistent with the repository's read-model contracts, but this run could not
reconnect to PostgreSQL because there was no local 5432 listener and no external
`DATABASE_URL` was available. No synthetic fixture was promoted to formal
authority.

## 7. CORS Configuration & Browser Evidence

The FastAPI application uses `CORSMiddleware` with:

- explicit `settings.cors_origins` values;
- `allow_credentials=False`;
- `GET` methods and `Accept`/`Content-Type` headers.

This is structurally compatible with a public read-only browser client, but the
required production origin is not present in the deployed environment, so
`Access-Control-Allow-Origin`, preflight, and browser fetch behavior cannot be
marked PASS. No wildcard-plus-credentials configuration or browser-security
workaround was introduced.

## 8. Sites Environment Before / After

Sites project: `appgprj_6a6ce02bd75c81919ab3678ebf013c53`.

The Sites connector returned revision 1 with exactly:

| Variable | Before | After |
|---|---|---|
| `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK` | `true` | unchanged |
| `NEXT_PUBLIC_API_BASE_URL` | absent | absent |

The current saved Sites version is version 37 (commit
`fce3d1ba8f809446cdb7c7e4c458c077f5ca4282`). No version or environment
mutation was performed because there is no verified API origin to set.

## 9. Build / Deploy Workflow

The repository's approved workflow is `.github/workflows/deploy.yml`:

1. validate Compose and Render configuration;
2. optionally trigger the protected Render deploy hook;
3. build/package the Sites frontend with `vars.PUBLIC_API_BASE_URL`;
4. require a non-empty API origin before packaging.

The workflow is currently non-operational for production because the required
GitHub environments and variables do not exist. The package job now performs a
read-only gate before `npm ci`: it verifies `/readyz`, `/openapi.json`, the
130-topic page, the 507-stock page, a topic detail, 2330 and 6806 stock details,
and an OPTIONS request whose `Access-Control-Allow-Origin` must exactly match
the public Sites origin. It then runs the three deployment-relevant frontend
test files, lint, typecheck, and production build. It will reject a non-formal
or incorrectly configured API before building a production bundle. No duplicate
hosting stack, temporary tunnel, or unapproved deployment was created.

## 10. `/topics` Production Evidence

Browser-tested URL: `https://topicpilot-platform.game0962046460.chatgpt.site/topics`.

Observed text includes `資料暫不可用`, `正式題材清單目前無法取得`, and
`尚未設定正式 FastAPI API origin；production 不使用 Preview 題材清單替代。`
The document has no `data-api-base-url` value. This proves the fail-closed
production path is active, but does not prove any public formal identity is
visible.

## 11. `/stocks` Production Evidence

Browser-tested URL: `https://topicpilot-platform.game0962046460.chatgpt.site/stocks`.

Observed state is `Preview · 僅供預覽，未連接正式 API`, `4/4 檔`, and the four
synthetic DEMO symbols (`DEMO-A1`, `DEMO-C3`, `DEMO-B2`, `DEMO-D4`). No 2330,
2317, TWO listing, or 6806 identity is visible. Console capture also recorded
an existing minified React hydration warning on the page; it is outside this
deployment task and was not modified.

## 12. DB → API → Public UI Reconciliation

| Layer | Required | Evidence in this run | Verdict |
|---|---:|---|---|
| Formal PostgreSQL topics | 130 | Prior task report only; no current DB connection | PARTIAL |
| Formal PostgreSQL stocks | 507 | Prior task report only; no current DB connection | PARTIAL |
| Public FastAPI | HTTPS + routes | Candidate hostname 404 | FAIL |
| Sites API base | configured | absent | FAIL |
| Public `/topics` | 130 formal identities | unavailable state | FAIL |
| Public `/stocks` | 507 formal identities | four Preview rows | FAIL |

## 13. Preview / Fallback Boundary

The boundary is behaving as intended for topics: missing production API does
not silently fabricate a formal catalog. Stocks still displays its explicitly
labelled local Preview path when no API origin is configured, as specified by
the existing Stock Explorer contract. This cannot be promoted to production
formal data until the API origin is configured and a new build is deployed.

## 14. Other Route Smoke Tests

No production API base exists, so cross-route API smoke tests cannot establish
formal data. The frontend production build still emitted the expected routes,
including `/`, `/topics`, `/topics/:slug`, `/stocks`, `/stocks/:code`,
`/favorites`, `/watchlist`, `/opportunities`, and `/ai-studio`.

## 15. Tests / Build

Passed:

- targeted frontend formal topic/stock/contract tests: **11 passed**;
- frontend ESLint: **PASS**;
- frontend TypeScript check: **PASS**;
- frontend production build: **PASS**;
- backend readiness/API/identity targeted tests: **9 passed, 5 skipped** because PostgreSQL integration variables were absent;
- `git diff --check`: **PASS** for the existing worktree diff.

The full frontend `npm test` command currently reports **55 passed / 13
failed**. The failures are pre-existing source-contract/rendered-HTML assertions
for the broader V2 frontend migration (for example, tests expecting the older
Home implementation); the targeted TASK-FE-BE-014 formal-boundary tests pass.

## 16. Remaining Issues / Required External Handoff

An authorized operator must provide all of the following before this task can
continue:

1. A real public Render service (or the existing service's exact URL) running
   the current FastAPI image.
2. A TLS-enabled PostgreSQL connection containing the formal V2 read models,
   with evidence for 130 topics and 507 stocks; no demo bundle as authority.
3. Render `DATABASE_URL`, an exact CORS origin list including the Sites host,
   and a service-scoped deploy hook or equivalent approved deployment access.
4. GitHub `production-api` and `production-web` environments, including
   `RENDER_DEPLOY_HOOK_URL` and `PUBLIC_API_BASE_URL`.
5. A redeploy through the existing workflow, followed by public API and browser
   acceptance checks, including OPTIONS/preflight and the 2330/6806 details.

`AI_WORKLOG.md` remains absent by repository governance. The full handoff is
recorded in this report until an owner authorizes introducing that historical
worklog file.

### Local runtime recovery attempt

As a non-destructive follow-up, the existing Docker Desktop Linux engine was
checked again. The Docker named pipe was unavailable and no Docker Desktop
executable was present at the standard installation path. No container,
volume, database, migration, or bootstrap command was run; this does not alter
the public deployment blocker.

## 17. Recommended Next Step

Provision or identify the approved Render/Neon resources and supply their
deployment credentials through the existing protected workflow. Then resume
TASK-DEPLOY-017 at public API health checks; do not change the frontend data
boundary or use a tunnel.

## Initial Audit Fixed Output (superseded by the continuation below)

```text
PUBLIC_FASTAPI_ORIGIN = BLOCKED
PUBLIC_FASTAPI_HTTPS = FAIL
PUBLIC_FASTAPI_CORS = FAIL
SITES_API_BASE_CONFIGURED = NO
TOPICS_PRODUCTION_FORMAL_DATA = NOT_READY
ALL_130_TOPIC_IDENTITIES_PUBLICLY_VISIBLE = FAIL
STOCKS_PRODUCTION_FORMAL_DATA = NOT_READY
ALL_507_STOCK_IDENTITIES_PUBLICLY_VISIBLE = FAIL
LEGACY_PREVIEW_FALLBACK_IN_PRODUCTION = ACTIVE
V2_PUBLIC_DATA_CHAIN = NOT_READY
NEXT_TASK_MODIFIED = NO
```

## 18. Continuation after user-provisioned Render/Neon resources

The user later confirmed the existing Render service and Neon project and
provided the public origin `https://topicpilot-api.onrender.com`. The source
revision containing the V2 backend and formal-only startup was pushed to
`main`; the service subsequently exposed the V2 OpenAPI routes. No duplicate
service or tunnel was created.

### Public API evidence

| Request | Result |
|---|---|
| `/healthz` | 200, `{"status":"ok"}` |
| `/readyz` | 200, `{"status":"ready"}` |
| `/openapi.json` | 200; `/api/v2/stocks`, `/api/v2/stocks/{symbol}`, `/api/v2/topics`, `/api/v2/topics/{slug}`, `/api/v2/topic-snapshots`, and `/api/v2/home` present |
| `/api/v2/topics?limit=200&offset=0` | 200; `total=0`, `items.length=0` |
| `/api/v2/stocks?limit=1000&offset=0` | 200; `total=0`, `items.length=0` |
| `/api/v2/stocks/2330`, `/api/v2/stocks/6806` | 404 because the Neon read model has no formal identities yet |
| `/api/v2/topics/ai-server` | 404 because the Neon read model has no formal topic identity yet |

An OPTIONS request from the exact Sites origin returned 200 with
`Access-Control-Allow-Origin: https://topicpilot-platform.game0962046460.chatgpt.site`,
`Access-Control-Allow-Methods: GET`, and no wildcard or credentials. The
production browser loaded `/topics` and `/stocks` from the configured origin
without a CORS console error. The pages intentionally rendered formal empty
states (`0 個題材`, `0/0 檔`) rather than Preview rows.

### Sites runtime evidence

The Sites production environment is now:

```text
NEXT_PUBLIC_API_BASE_URL=https://topicpilot-api.onrender.com
NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false
```

The existing public frontend version was redeployed after the environment
revision. Home and Favorites smoke tests load without a route crash. Existing
presentation-only content on those routes was not redesigned.

### Formal data boundary

The V2 schema is migrated and the API is connected to Neon, but the production
read model is empty. No approved formal 130-topic/507-stock artifact is present
in this repository, and `fixtures/demo` was not imported. Therefore no detail
identity can yet be claimed for 2330, 6806, or any of the 130 topics. The next
data action is an explicitly approved operator import from the private formal
source, followed by count, lineage, and detail reconciliation; it must not be
implemented as Web Service startup or replaced by the demo importer.

The repository's approved private input directory is available locally at
`C:\Users\acer\Desktop\題材領航\input`. A no-write dry-run completed during
this continuation with `records_read=1594`, `valid=1594`, zero rejected,
duplicate, conflict, or warning records, and counts of 507 instruments, 130
topics, 107 hierarchy edges, and 848 relations. It did not contact Neon.
After the operator has reviewed the dry-run, the protected import command is:

```text
$env:PYTHONPATH='services/api/src'
python infra/scripts/phase3_6_001b_legacy_import.py `
  --input 'C:\Users\acer\Desktop\題材領航\input' `
  --database-url "$env:MIGRATION_DATABASE_URL" `
  --apply
```

This session intentionally did not execute that production write because the
Neon secret is not available here. The command must be run once from the
approved revision, then `/api/v2/topics`, `/api/v2/stocks`, the 2330/6806
details, and the public browser must be rechecked.

## Current Fixed Final Output

```text
PUBLIC_FASTAPI_ORIGIN = READY
PUBLIC_FASTAPI_HTTPS = PASS
PUBLIC_FASTAPI_CORS = PASS
SITES_API_BASE_CONFIGURED = YES
TOPICS_PRODUCTION_FORMAL_DATA = NOT_READY
ALL_130_TOPIC_IDENTITIES_PUBLICLY_VISIBLE = FAIL
STOCKS_PRODUCTION_FORMAL_DATA = NOT_READY
ALL_507_STOCK_IDENTITIES_PUBLICLY_VISIBLE = FAIL
LEGACY_PREVIEW_FALLBACK_IN_PRODUCTION = REMOVED
V2_PUBLIC_DATA_CHAIN = PARTIAL
NEXT_TASK_MODIFIED = NO
```

## Modified / Created / Validation

- **Created:** this report only.
- **Modified:** `.github/workflows/deploy.yml` (read-only formal API/CORS
  deployment gate). No application, UI, business-rule, schema, database, or
  `NEXT_TASK` files were modified.
- **Validation:** public Sites environment read, public browser checks,
  candidate Render route checks, GitHub environment/workflow checks, targeted
  frontend tests/lint/typecheck/build, targeted backend tests, and diff check.
- **Open:** the public API/database wiring is live, but the private formal
  identity/read-model artifact and approved import operator are still absent;
  130/507 acceptance therefore remains intentionally open.
