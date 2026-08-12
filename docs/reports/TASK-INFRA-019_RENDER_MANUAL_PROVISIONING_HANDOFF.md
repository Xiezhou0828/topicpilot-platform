# TASK-INFRA-019｜Manual Render Provisioning Handoff

**Date:** 2026-08-12  
**Scope:** repository-side audit and exact first Render Web Service settings  
**External UI operation:** not performed by this task  
**Production claim:** no Render service has been deployed by this task

This handoff converted the remaining manual Render work into a safe, repeatable
UI procedure. The user has since completed that UI step. The original handoff
output below is retained as historical evidence; the post-provisioning status
and current next action are recorded in the continuation section at the end.

## Repository audit

| Area | Audited source | Finding |
|---|---|---|
| Render blueprint | `render.yaml` | Web service `topicpilot-api`, Docker, Oregon, Free, `/readyz`; startup runs Alembic then Uvicorn. |
| Docker image | `infra/docker/api.Dockerfile` | Python 3.12 slim; installs `services/api`; defaults to `topicpilot_api.main:app`, `0.0.0.0`, and `${PORT}`. |
| FastAPI entrypoint | `services/api/src/topicpilot_api/main.py` | `app = create_app()`; formal V2 routes are registered; `/healthz` and `/readyz` are defined. |
| API package | `services/api/pyproject.toml` | FastAPI, Uvicorn, SQLAlchemy, Psycopg, Alembic; one linear migration head. |
| Environment loading | `services/api/src/topicpilot_api/config.py` | Pydantic Settings reads `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `TOPICPILOT_CORS_ORIGINS`, freshness, and log level. |
| Runtime database | `services/api/src/topicpilot_api/database.py` | API SQLAlchemy engine uses `DATABASE_URL`; pooled Neon URL is the intended runtime value. |
| Alembic | `services/api/alembic/env.py`, `alembic.ini` | URL is injected at runtime; Alembic uses `MIGRATION_DATABASE_URL` when supplied, otherwise falls back to `DATABASE_URL`; head is `0024_task_be_007_topic_snapshots`. |
| CORS | `main.py`, `config.py` | Explicit allowlist; `allow_credentials=False`; GET and `Accept`/`Content-Type` only. |
| Readiness | `main.py` | `/healthz` is liveness; `/readyz` executes `SELECT 1` and returns 503 when PostgreSQL is unavailable. |
| Startup/bootstrap | `render.yaml` | `alembic upgrade head && exec uvicorn ...`; no importer or data seed. |
| Demo fixture path | `infra/docker/api.Dockerfile`, `fixtures/` | Fixtures are copied into the image but are inert; production startup does not call `topicpilot-import`. |
| Deployment documentation | `docs/operations/deployment.md`, architecture/report docs | Formal Neon → Render FastAPI → Sites boundary and no-production-demo rule are documented. |

## A. Exact Render UI settings

Use these settings when creating the **Web Service** from the authorized
`Xiezhou0828/topicpilot-platform` repository:

```text
SERVICE_NAME       = topicpilot-api
LANGUAGE           = NOT_REQUIRED
BRANCH             = main
REGION             = Oregon
ROOT_DIRECTORY     = NOT_REQUIRED (leave blank)
DOCKERFILE_PATH    = infra/docker/api.Dockerfile
DOCKER_BUILD_CONTEXT = . (repository root)
HEALTH_CHECK_PATH  = /readyz
INSTANCE_PLAN      = Free
```

`LANGUAGE` is not required because Docker selects the runtime from the
Dockerfile. `ROOT_DIRECTORY` is not required because the Dockerfile path and
build context are repository-root relative. Do not enter `services/api` as the
root directory: that would make `infra/docker/api.Dockerfile` and the root
`fixtures/` copy unavailable.

The repository's `render.yaml` is now aligned to the user-confirmed Oregon
region. If the Render UI shows a different label for the same Oregon region,
use the UI's exact Oregon option; do not substitute a guessed region.

### Render Start Command

If the manual form exposes a Docker **Start Command** override, enter exactly:

```text
/bin/sh -c 'alembic upgrade head && exec uvicorn topicpilot_api.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers'
```

This preserves the checked-in `render.yaml` command. If Render automatically
uses the repository Dockerfile command instead, do not add a second competing
command; the Dockerfile's default Uvicorn command is still formal-data-safe,
but the migration step must be run separately before the service is declared
ready.

## B. Environment variables

Set only the following on the **Web Service**. Secrets must be entered into
Render's secret environment UI; never paste them into chat, GitHub issues,
source files, `.env`, `render.yaml`, or a frontend build artifact.

| Variable | Classification | First-deploy value / rule |
|---|---|---|
| `DATABASE_URL` | `REQUIRED_SECRET` | Neon **pooled** `postgresql+psycopg://...` URL for the FastAPI runtime. Preserve Neon TLS/query parameters. |
| `MIGRATION_DATABASE_URL` | `REQUIRED_SECRET` | Neon **direct** `postgresql+psycopg://...` URL for Alembic DDL. This is separate from the pooled runtime URL. |
| `TOPICPILOT_CORS_ORIGINS` | `REQUIRED_PUBLIC_CONFIG` | Exactly `https://topicpilot-platform.game0962046460.chatgpt.site`; no `*`. |
| `TOPICPILOT_FRESHNESS_DAYS` | `OPTIONAL` | `3` is the repository value; the application default is also 3. |
| `TOPICPILOT_LOG_LEVEL` | `OPTIONAL` | `INFO` is the repository value and safe default. |
| `UVICORN_APP` | `OPTIONAL` | `topicpilot_api.main:app` is already the Dockerfile default and is explicit in the Start Command. |
| `PORT` | `NOT_REQUIRED` | Render injects this value. Never create a fixed production port variable. |
| `TOPICPILOT_DEMO_MODE` | `NOT_REQUIRED` | Do not set it on the formal Web Service. |
| `TOPICPILOT_BUNDLE_PATH` | `NOT_REQUIRED` | Do not set it on the formal Web Service. |
| `TOPICPILOT_TA_API_USER` / `TOPICPILOT_TA_API_PASSWORD` | `NOT_REQUIRED` for this Web Service | Worker-only private provider credentials; do not add them to the public API unless the separate worker is being provisioned. |

The application now supports a separate direct migration URL. Alembic falls
back to `DATABASE_URL` only when `MIGRATION_DATABASE_URL` is omitted; for the
first production deployment, do not rely on that fallback.

## C. Demo bootstrap safety

The production startup is **demo-free**:

- `render.yaml` no longer calls `topicpilot-import`.
- `render.yaml` no longer sets `TOPICPILOT_DEMO_MODE` or
  `TOPICPILOT_BUNDLE_PATH`.
- Startup runs only `alembic upgrade head` followed by Uvicorn.
- Alembic migrations do not call `Base.metadata.create_all`, reset the
  database, or recreate existing tables.
- `fixtures/demo` is copied by the image for development/test compatibility,
  but it is not imported and cannot seed the production database through the
  checked-in startup command.
- Formal database unavailable therefore fails readiness; it does not trigger
  a four-stock Preview seed or synthetic fallback.

Do not add `topicpilot-import /fixtures/demo` to the Render command. Do not
run any bootstrap command against Neon until the formal 130-topic/507-stock
artifact and its lineage have been approved separately.

## D. FastAPI entrypoint

The verified production process is:

```text
module  = topicpilot_api.main
ASGI app = app
host    = 0.0.0.0
port    = $PORT (Render-injected)
flags   = --proxy-headers
```

The equivalent command is:

```text
uvicorn topicpilot_api.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers
```

No production command binds to `localhost:8000`. The Dockerfile's `PORT=8000`
is only a local default; Render's injected `PORT` wins at runtime.

## E. Migration strategy

### First deploy

1. Set both Neon secrets: pooled `DATABASE_URL` and direct
   `MIGRATION_DATABASE_URL`.
2. Use the Start Command above.
3. Press **Deploy Web Service**. Render runs `alembic upgrade head` once at
   startup against the direct migration endpoint, then starts Uvicorn.
4. Verify `/healthz`, `/readyz`, and `/openapi.json` before any formal data
   bootstrap.
5. Treat an empty read model as a migration/bootstrap sequencing state, not as
   permission to import the demo fixture.

The first migration creates or advances only the repository's versioned schema.
It does not import the four-row Preview dataset and does not establish the
formal 130/507 data counts.

### Normal deploy

Every subsequent Render restart may execute the same idempotent command:

```text
alembic upgrade head
```

This applies only pending Alembic revisions and does not drop, reset, or
recreate the database. After migrations complete, Uvicorn starts. A later
formal data refresh/bootstrap must be an explicitly approved operator job,
with reconciliation evidence, and must not be embedded in Web Service startup.

### Exact repository migration command

From the repository's API directory, with the two environment variables already
set in the approved operator shell:

```text
cd services/api
python -m alembic upgrade head
```

This handoff does not execute that command against Neon and does not request
that any credential be shared here.

## F. First deploy checklist

### STEP 1 — Create the Web Service

Select the authorized repository and fill the A-section settings. Set the
Start Command exactly as shown above if the UI exposes it.

### STEP 2 — Add Neon variables

Set pooled Neon URL in `DATABASE_URL` and direct Neon URL in
`MIGRATION_DATABASE_URL`. Keep both secret in Render.

### STEP 3 — Add CORS

Set `TOPICPILOT_CORS_ORIGINS` to the exact public Sites origin. Do not add a
wildcard and do not enable credentials.

### STEP 4 — Press Deploy Web Service

Yes: it is safe to press Deploy after the settings and both Neon URLs are
entered. This creates the API infrastructure and applies versioned migrations;
it does not seed demo data. It does not yet prove formal 130/507 data.

### STEP 5 — Record the origin

Render should provide an HTTPS service URL similar to
`https://<service-name>.onrender.com`. Record the exact URL Render displays;
do not invent or infer it from the service name.

### STEP 6 — Verify the API process

Open the exact origin at:

```text
GET /healthz
GET /readyz
GET /openapi.json
```

Expected first-deploy results are `/healthz` 200, `/readyz` 200 only when the
Neon connection and migrations are usable, and `/openapi.json` 200. Formal
topic/stock count checks happen only after the approved formal bootstrap.

### STEP 7 — Formal migration/bootstrap timing

Alembic migration happens at first deploy. Formal identity/read-model
bootstrap happens later, only after the API is healthy and the approved
130-topic/507-stock source artifact, lineage, and reconciliation procedure are
available. Never use `fixtures/demo` for this step.

### STEP 8 — GitHub environments

Only after the Render origin and service-scoped deploy hook are known, create:

```text
production-api:
  secret RENDER_DEPLOY_HOOK_URL
production-web:
  variable PUBLIC_API_BASE_URL=<verified Render HTTPS origin>
```

Keep Neon credentials out of these frontend/release variables unless a
separate protected backend migration job explicitly requires them.

### STEP 9 — Sites API base

Only after public `/readyz`, OpenAPI, formal counts, details, and CORS pass,
set Sites `NEXT_PUBLIC_API_BASE_URL` to the exact verified Render HTTPS origin,
save a new version, redeploy, and then verify `/topics` and `/stocks` in the
real production browser.

## G. Initial fixed final output (historical; superseded below)

```text
RENDER_REPOSITORY_CONNECTED = USER_CONFIRMED
NEON_PROJECT_CREATED = USER_CONFIRMED
RENDER_SERVICE_CREATED = NO
RENDER_PUBLIC_ORIGIN = NOT_YET_AVAILABLE
RENDER_SETTINGS_AUDITED = YES
PRODUCTION_STARTUP_DEMO_FREE = YES
DATABASE_URL_RUNTIME_MODE = POOLED
MIGRATION_CONNECTION_MODE = DIRECT
FASTAPI_ENTRYPOINT_VERIFIED = YES
READY_ENDPOINT_VERIFIED_IN_CODE = YES
SAFE_TO_PRESS_DEPLOY = YES
EXACT_NEXT_USER_ACTION = In Render, create topicpilot-api with the audited settings, add pooled DATABASE_URL and direct MIGRATION_DATABASE_URL as secrets, add the exact Sites origin to TOPICPILOT_CORS_ORIGINS, then press Deploy Web Service.
```

## H. Post-provisioning continuation

The user confirmed that `topicpilot-api` was created and deployed at
`https://topicpilot-api.onrender.com`, with Neon pooled runtime and direct
migration URLs plus the exact Sites CORS origin. The service initially served
the old image; after the V2 backend revision was pushed to `main`, the public
OpenAPI exposed the V2 routes. A formal-only Docker startup guard now runs the
additive Alembic upgrade before Uvicorn even when the manually created service
does not copy the Blueprint command.

Current public results:

```text
/healthz = 200
/readyz = 200
/openapi.json = 200 (V2 routes present)
/api/v2/topics = 200, total=0
/api/v2/stocks = 200, total=0
OPTIONS /api/v2/topics = 200, exact Sites origin allowed
```

The Neon schema is therefore reachable and migrated, but the formal
130-topic/507-stock artifact has not been imported. No demo fixture was used.
Sites production now has `NEXT_PUBLIC_API_BASE_URL` set to the Render origin
and `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false`, and the public frontend was
redeployed. The pages correctly show empty formal states rather than Preview
rows. The remaining action is an approved operator import from the private
formal source, followed by count/detail reconciliation; this handoff does not
execute that production write.

## Current fixed final output

```text
RENDER_REPOSITORY_CONNECTED = USER_CONFIRMED
NEON_PROJECT_CREATED = USER_CONFIRMED
RENDER_SERVICE_CREATED = USER_CONFIRMED
RENDER_PUBLIC_ORIGIN = https://topicpilot-api.onrender.com
RENDER_SETTINGS_AUDITED = YES
PRODUCTION_STARTUP_DEMO_FREE = YES
DATABASE_URL_RUNTIME_MODE = POOLED
MIGRATION_CONNECTION_MODE = DIRECT
FASTAPI_ENTRYPOINT_VERIFIED = YES
READY_ENDPOINT_VERIFIED_IN_CODE = YES
SAFE_TO_PRESS_DEPLOY = YES (already deployed)
EXACT_NEXT_USER_ACTION = Supply the approved formal 130-topic/507-stock artifact to the protected import operator, run the non-demo import, then recheck the public V2 counts and detail identities.
```

## Scope and non-changes

- No Render or Neon UI was operated by this task.
- No production migration or formal bootstrap was executed.
- No secret was requested in chat or written to the repository.
- No Topic Score, Grade, Lifecycle, Opportunity/Recommendation, Favorites,
  UI design, or `NEXT_TASK` was modified.
- The repository changes are limited to formal startup safety, the explicit
  migration connection boundary, the user-confirmed Render region, and this
  handoff documentation.
