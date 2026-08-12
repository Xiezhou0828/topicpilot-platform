# TopicPilot V2 Production Data Architecture

**Status:** `PM-FROZEN BOUNDARY / IMPLEMENTATION AUDIT BLOCKED`  
**Generation:** `NEXT / V2`  
**Owner:** Architecture / Backend / Operations  
**Effective date:** 2026-08-12  
**Source:** TASK-INFRA-019 infrastructure handoff; implementation evidence is
recorded separately in [TASK-INFRA-019 V2 Production Infrastructure Report](../reports/TASK-INFRA-019_V2_PRODUCTION_INFRASTRUCTURE_REPORT.md).

This specification defines the intended V2 production data chain and the
authority boundaries required to activate it. It does not claim that the
external Neon, Render, Windows, GitHub, or Sites resources are currently
provisioned. Current implementation status is explicit in the linked report.

## 1. Production components

| Component | Intended owner | Responsibility | Current repository evidence |
|---|---|---|---|
| Neon PostgreSQL | Database/Operations | Formal V2 data authority and read-model persistence | `DATABASE_URL` is required but no production value is available. |
| Render FastAPI Web Service | Backend/Operations | Public read-only HTTPS API over formal PostgreSQL | `render.yaml` defines `topicpilot-api` in the user-confirmed Oregon region; startup runs migrations and Uvicorn without importing a bundled demo fixture. External service/database activation remains unverified. |
| Render post-close job | Operations | Official daily collection and read-model update | Target topology; no Render Cron resource is present in the checked-in blueprint. |
| Windows Taishin runtime | Data Engineering | Private intraday provider runtime and persistence into Neon | Capability and host-side evidence exist; deployment prerequisite remains open. |
| GitHub Actions | Release Engineering | Validation, deployment control, acceptance gates, and artifact handoff | `.github/workflows/deploy.yml` now contains the formal API/CORS gate. |
| ChatGPT Sites | Frontend/Release Engineering | Public V2 customer frontend | Existing project is reachable, but API base is not configured. |

## 2. Formal authority and prohibited substitutions

The formal V2 path is:

```text
External provider
  -> raw observations
  -> observation timeline
  -> canonical PRICE/VOLUME
  -> tracking and topic snapshots
  -> PostgreSQL read models
  -> FastAPI
  -> HTTPS
  -> Sites frontend
```

Formal production identity and read-model authority are PostgreSQL and FastAPI.
The frontend must not connect directly to Neon. Google Sheets, R2 snapshots,
`web_snapshot.json`, and `fixtures/demo` remain legacy or development/demo
surfaces and must not be promoted to V2 production authority.

Missing numeric evidence remains `NULL`; it is not converted to zero and does
not remove the underlying formal identity.

## 3. Runtime boundaries

### 3.1 Public API

Render FastAPI reads the formal PostgreSQL/read models and exposes read-only
health, OpenAPI, topic, stock, and operational routes. The public origin must
serve HTTPS and pass the acceptance contract in Section 8.

### 3.2 Post-close collection

The intended post-close path is an idempotent scheduled job on the approved
Render scheduler or an explicitly approved equivalent:

```text
Taiwan trading-day gate
  -> TWSE / TPEx official daily collection
  -> raw / timeline / canonical observations
  -> tracking
  -> topic snapshots
  -> downstream read models
```

The current repository contains a `topicpilot-live` worker definition, not a
Render `cron` service definition. The currently evidenced operational owner is
the Windows Task Scheduler task `TopicPilot_V2_Daily_Close_1440`; its report
marks the scheduler `PARTIALLY_READY` because the official holiday catalogue
and a successful scheduled run remain open.

### 3.3 Intraday Taishin boundary

The private Taishin runtime remains on the Windows boundary where its vendor
runtime and credentials are available. It writes normalized observations to the
approved PostgreSQL target. It must not silently substitute synthetic prices on
provider failure. Container/Linux deployment requires a separately approved
private-runtime and secret handoff.

### 3.4 Frontend boundary

The production bundle receives only a public HTTPS API origin through
`NEXT_PUBLIC_API_BASE_URL` (or the repository's equivalent release variable).
It never receives `DATABASE_URL` or provider credentials. With a configured API
failure, formal pages show an unavailable state; they do not silently overlay a
synthetic catalog.

## 4. Environments

| Environment | Data source | Preview behavior | Authority |
|---|---|---|---|
| Local development | Local PostgreSQL/Compose or explicit test database | Explicit preview may be enabled | Development only |
| CI/test | Isolated test database and synthetic fixtures | Synthetic fixtures are allowed and labelled | Test only |
| Public production | Neon formal V2 database through Render FastAPI | Preview fallback is forbidden as an identity authority | Formal PostgreSQL/FastAPI |

## 5. Secrets and variables

| Location | Variable class | Examples | Rule |
|---|---|---|---|
| Render secret environment | Backend secrets | `DATABASE_URL` (pooled runtime), `MIGRATION_DATABASE_URL` (direct Alembic endpoint), Taishin credentials, provider keys | Never commit, log, or send to the browser. |
| Render non-secret environment | Backend configuration | exact CORS origins, log level, timezone | Keep environment-specific and explicit. |
| GitHub `production-api` | Release secret | service-scoped Render deploy hook | Protected environment; no broad API token required. |
| GitHub `production-web` | Public build variable | `PUBLIC_API_BASE_URL` | Must be a verified HTTPS origin. |
| Sites environment | Public runtime/build variable | `NEXT_PUBLIC_API_BASE_URL` | Must match the validated production API origin. |

`NEXT_PUBLIC_*` values are browser-visible configuration, never database
secrets. CORS must use an exact allowlist; `*` with credentials is forbidden.

## 6. Migration and formal bootstrap

Production Neon must be migrated with the repository's Alembic history before
the API is marked ready. The API runtime uses the pooled `DATABASE_URL`; when
supplied, Alembic uses the separate direct `MIGRATION_DATABASE_URL`. If the
latter is omitted, the repository falls back to `DATABASE_URL`. The repository
migration head is
`0024_task_be_007_topic_snapshots` (verified through `alembic heads`). A live
`alembic current` readback requires a reachable database and therefore remains
blocked in the current environment.

Formal bootstrap must establish, with auditable counts and lineage:

- 130 enabled topic identities;
- 507 active TPE/TWO formal stock identities;
- current hierarchy, instrument-topic relations, observations, tracking, and
  topic snapshot/read-model coverage;
- explicit 6806 identity retention with nullable price where the provider has
  no current quote.

The bootstrap path must not use the checked-in synthetic `fixtures/demo` bundle
as formal authority. Any migration drift or unknown database lineage is a stop
condition, not a reason to run a destructive reset.

## 7. Public API contract

The production API must provide:

- `GET /healthz` → 200;
- `GET /readyz` → 200 and database readiness;
- `GET /openapi.json` → 200;
- `GET /api/v2/topics?limit=200&offset=0` → `total=130`, 130 items;
- `GET /api/v2/stocks?limit=1000&offset=0` → `total=507`, 507 items;
- one formal topic detail route → 200;
- `/api/v2/stocks/2330` → 200;
- `/api/v2/stocks/2317` → 200;
- `/api/v2/stocks/6806` → 200 with identity retained even when price is null.

The API response must be reconciled to formal PostgreSQL evidence, not a
synthetic fixture or an inferred browser-side universe.

## 8. CORS and production acceptance

The production Sites origin is:

```text
https://topicpilot-platform.game0962046460.chatgpt.site
```

FastAPI must allow that origin explicitly, with `allow_credentials=False` for
the current read-only public client. The release gate performs an OPTIONS
preflight with `Origin` and `Access-Control-Request-Method: GET` and requires
an exact `Access-Control-Allow-Origin` match. Browser verification must confirm
the same result in the real production page with no mixed-content or console
CORS errors.

## 9. Release control plane

The approved release sequence is:

```text
GitHub checkout
  -> backend and migration checks
  -> formal API readiness / count / detail / CORS acceptance
  -> frontend targeted tests, lint, typecheck, build
  -> Render API deployment or protected deploy hook
  -> Sites artifact/version deployment
  -> production API and browser smoke tests
```

The workflow must fail closed if `PUBLIC_API_BASE_URL` is missing, if the API
returns a non-formal count, if detail identity is missing, or if CORS does not
match the production origin.

## 10. Observability and recovery

At minimum, operations must be able to establish:

- API liveness and database readiness;
- latest successful collection run and canonical trading date;
- latest topic snapshot date and coverage;
- provider failure/timeout classification without zero-filling;
- migration revision and database backup/restore readiness.

Neon backup retention, point-in-time recovery, restore drill, migration rollback
and alerting objectives remain open operational decisions. No production
database reset, volume deletion, or destructive prune is authorized by this
specification.

## 11. Lifecycle, Opportunity, and V1 boundaries

This infrastructure document does not activate Lifecycle Engine thresholds,
Topic Score/Grade, Opportunity/Recommendation, Favorites persistence, or any
frontend redesign. Lifecycle and Opportunity remain downstream API/data
contracts; unavailable formal read models remain unavailable. V1 Google Sheets,
legacy snapshots, and V1 runtime remain separate until an explicit cutover task.

## 12. Current status

The topology is accepted as the intended V2 production boundary, but the
implementation audit is blocked by missing external resources:

- no verified public Render FastAPI origin;
- no accessible production Neon `DATABASE_URL` or current database readback;
- no Render deploy hook/service control evidence;
- no GitHub production environments or variables;
- Sites API base absent;
- Render Cron and private Taishin deployment not provisioned in the checked-in
  runtime configuration.

See [TASK-INFRA-019 V2 Production Infrastructure Report](../reports/TASK-INFRA-019_V2_PRODUCTION_INFRASTRUCTURE_REPORT.md)
for evidence, fixed outputs, and the external handoff.
