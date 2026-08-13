# Deployment handoff

> Generation: `NEXT / V2` — formal production data chain. `LEGACY / V1`
> remains a separate retired/cutover boundary.

## Topology

| Surface | Target | Responsibility |
|---|---|---|
| PostgreSQL | Neon | Formal V2 identity, canonical/read-model persistence |
| FastAPI | Render Free web service | Read API and OpenAPI |
| React/vinext | ChatGPT Sites | Public V2 frontend |
| CI/release | GitHub Actions | Validation, gated API trigger, web artifact |

The public production authority is Neon PostgreSQL through Render FastAPI. The
frontend never connects directly to Neon and must not silently replace formal
API failures with a synthetic identity authority. Provider free-tier behavior
and quotas can change; review the official service documentation before each
release.

## Neon setup

1. Create or identify the approved Neon project/branch for V2 production.
2. Create a least-privilege application role where plan capabilities allow.
3. Copy a TLS-enabled pooled connection string for the API runtime and a
   direct connection string for migration DDL.
4. Store the pooled URL as `DATABASE_URL` and the direct URL as
   `MIGRATION_DATABASE_URL` in Render; never put either secret in
   `.env.example`, `render.yaml`, an issue, or a build artifact.
5. Run the repository Alembic migrations from the approved release image.
6. Bootstrap or reconcile the formal V2 identity/read models through the
   approved data-import process; do not use `fixtures/demo` as production data.

Use a SQLAlchemy/psycopg URL. If the copied URL starts with `postgresql://`,
change only that scheme to `postgresql+psycopg://`; the current application
does not rewrite the driver automatically. Preserve provider-required query
parameters such as `sslmode=require`.

## Render API blueprint

`render.yaml` defines the FastAPI web service and a separate live worker. It
intentionally does not create a Render database because persistence is provided
by Neon. The web service runs migrations and then starts Uvicorn; it does not
import a bundled demo fixture at startup.

Required Render variables:

| Variable | Secret | Purpose |
|---|---:|---|
| `DATABASE_URL` | Yes | Neon pooled PostgreSQL connection for the API runtime |
| `MIGRATION_DATABASE_URL` | Yes for first production migration | Neon direct PostgreSQL connection for Alembic DDL; falls back to `DATABASE_URL` only when omitted |
| `TOPICPILOT_CORS_ORIGINS` | No, environment-specific | Exact Sites/public web origin(s) |
| `TOPICPILOT_LOG_LEVEL` | No | Usually `INFO` |
The Free plan does not provide Render's paid pre-deploy command. Therefore the
container startup command performs idempotent `alembic upgrade head` against
`MIGRATION_DATABASE_URL` and only then starts Uvicorn. Alembic applies pending
revisions; it does not recreate or reset the database. A paid deployment should
move migrations into the provider's pre-deploy phase and keep application
startup free of migration ownership.

`autoDeployTrigger` is disabled. Either deploy manually in Render after CI or
use `.github/workflows/deploy.yml`, which requires approval for the
`production-api` GitHub environment.

Required protected GitHub API secret:

- `production-api / RENDER_DEPLOY_HOOK_URL`

Do not store a Render API key when a service-scoped deploy hook is sufficient.

## Free-tier cold start

Render documents that free web services spin down after 15 minutes without
inbound traffic and take roughly one minute to spin back up. The frontend must:

1. Keep the original TopicPilot layout visible while the API is waking.
2. Retry only network/5xx failures with bounded backoff.
3. Stop after the documented UI timeout and show the formal unavailable/error
   state; do not switch to a synthetic identity bundle in production.

## Formal daily close operation

The repository-side one-shot command is:

```console
topicpilot-live --mode post-close --once
```

For an authorized recovery or backfill, supply exactly one ISO trading date:

```console
topicpilot-live --mode post-close --once --run-date YYYY-MM-DD
```

The job uses official TWSE daily data for TPE and official TPEx daily data for
TWO, writes through the existing canonical observation pipeline, then records
separate priced/covered coverage and `downstreamReady` in the `POST_CLOSE`
collector-run metadata. Exit zero is not sufficient acceptance evidence:
operators must confirm the run is `SUCCESS`,
`dailyMarketReconciliation.status=READY`, `coveredCount=expectedCount`,
`unexplainedMissingCount=0`, and `downstreamReady=true`. An approved
`SUSPENDED`, `NO_TRADE`, or `EXCHANGE_CONFIRMED_NO_DATA` row may make the run
covered while its close remains null; it must never be zero-filled or
forward-filled. `PARTIAL`, `FAILED`, and `MARKET_CLOSED` must not trigger
Lifecycle processing. Re-running the same date is safe and reuses canonical
idempotency keys.

The checked-in Render blueprint still has no approved Cron resource. Until an
operator provisions and verifies the scheduler, production scheduling remains
`WAITING/BLOCKED`; the CLI is the supported manual execution boundary.

## Adapter-v2 deployment and reference preflight (TASK-OPS-023A-P3A)

The official daily adapter lineage is verified locally with a secret-free
command. It performs no provider request and no database access:

```console
topicpilot-provider-lineage
```

The result must report `READY`, `twse-official-daily.v2` and
`tpex-official-daily.v2` with `marketBatch=true`, TPE→TWSE and TWO→TPEx
authority, Yahoo daily as verification-only, and Taishin as intraday-only.

Run the same command inside the deployed worker image or protected runtime;
it is secret-free and read-only. Its optional `buildSha` is populated from
`RENDER_GIT_COMMIT` or `GIT_SHA` when the hosting runtime supplies one; a
missing SHA is not evidence that a different provider is active.

In the protected Production runtime, run the reference check before any
Canary. It only issues SELECTs and exits non-zero unless the versioned context
and formal identities are complete:

```console
topicpilot-reference-check
```

The command derives expected daily markets from the provider registry and
counts active `EQUITY` identities from `topicpilot.instruments` joined to
active `topicpilot.markets`. It does not hard-code 507, bootstrap, seed,
repair, mutate the active version, or run a migration. The expected protected
runtime result is `tw-reference-v1`, active `YES`, 2 markets, 507 instruments,
empty missing/duplicate lists, and `referenceLoadStatus=READY`.

`tw-reference-v1` covers versioned currency, timezone, session/calendar,
trading-status, and adjustment catalogues. It does not own topics or
instrument-topic relations; those remain in the identity domain. A missing,
duplicate, inactive, or incomplete registry/context fails closed as
`NOT_READY` and must stop the Canary.

## G2 official provider read-only preflight (TASK-DATA-REF-006A)

The canonical G2 authority is [the official provider preflight runbook](provider-preflight.md).
After the runtime SHA, provider lineage, and G1 reference state are verified
in the same protected runtime, run:

```console
topicpilot-provider-preflight \
  --run-date YYYY-MM-DD \
  --reference-version tw-reference-v1
```

The target date is required and is validated against the active
`tw-reference-v1` `TW_MARKET` session/calendar context. The command performs
SELECT-only context reads and one market-level request through each canonical
official adapter with `marketBatch=true`. It never calls `topicpilot-live`,
`PostCloseUpdater`, historical ingestion, tracking, Snapshot, Lifecycle,
Opportunity, or Scheduler code. Its result must contain
`status=PASS`, `readOnly=true`, `productionWriteSet=[]`,
`nonReferenceWriteSet=[]`, `fallbackAllowed=false`, and passing per-market
TPE/TWO official evidence. A failure is a STOP condition; it does not
authorize the post-close command or Canary.

### Adapter-v2 deployment checklist

- [ ] Release revision is committed and includes FIX01A adapter-v2 files.
- [ ] TWSE/TPEx adapter-v2 versions and `PostClose market_batch` are present.
- [ ] Provider authority is unchanged; Yahoo/Taishin roles are unchanged.
- [ ] No migration is required for FIX01A/P3A.
- [ ] Backend tests, Ruff, formatting, compile, and release CI pass.
- [ ] Runtime provider-lineage command is available after deploy.
- [ ] Protected `topicpilot-reference-check` returns `READY`.
- [ ] Protected `topicpilot-provider-preflight --run-date YYYY-MM-DD` returns `PASS`.
- [ ] 6806 official no-data follows the existing DATA-022A contract.
- [ ] Canary command is reviewed; Scheduler remains disabled.

The deployment trace is `GitHub checkout release_ref` →
`infra/docker/api.Dockerfile` → `COPY services/api/` → package console script
`topicpilot-live` → Render worker command `alembic upgrade head && exec
topicpilot-live` → `PostCloseUpdater` → official adapter-v2. Render
`autoDeployTrigger` is off and the deploy hook is protected by the
`production-api` environment. Local uncommitted changes are not a deployable
release until an operator publishes a committed revision.

### Canary #2 gate order

1. G0 — deployed runtime reports both adapter-v2 lineages.
2. G1 — protected reference check reports `READY`.
3. G2 — TWSE/TPEx official endpoints are reachable for the target date.
4. G3 — 6806 is priced or approved official no-data, never a fake bar.
5. G4 — operator separately authorizes one-shot Production Canary; this does
   not authorize Scheduler.

Only after G0–G4 pass may the operator prepare:

```console
topicpilot-live --mode post-close --once --run-date 2026-08-12
```

Do not execute that command as part of P3A. After an authorized run, verify
POST_CLOSE → daily reconciliation `READY` → matching 130-topic snapshot →
Lifecycle `evaluation_mode=SHADOW`; stop before any Scheduler action.

## TASK-OPS-023 activation status

The public read-only preflight currently passes `/healthz` and `/readyz` and
confirms the formal identity totals (2 markets, 507 instruments, 130 topics,
848 relations). It does not prove daily readiness: live status is `NO_RUN` and
`/api/v2/topic-snapshots?latest=true` is empty. The production Alembic revision
and combined 0027 migration status cannot be verified without protected Neon access.

Do not run the canary, write a snapshot, or activate a scheduler until an
operator has confirmed the migration lineage and supplied the protected
runtime. The required acceptance remains `READY`, 100% covered, zero
unexplained/date/duplicate errors, and `downstreamReady=true`. The complete
blocked handoff is in
`docs/reports/TASK-OPS-023_V2_DAILY_CLOSE_PRODUCTION_ACTIVATION_REPORT.md`.

The parallel TASK-BE-021 Lifecycle implementation is shadow-only and remains
data-gated. Its engine tests pass, but no production shadow result may be
claimed until a READY daily market run and topic snapshot exist.

Release note: repository reconciliation resolved the historical `0025` collision
by preserving DATA-022/022A as 0025/0026 and renumbering the additive Lifecycle
results migration to `0027_task_be_021_topic_lifecycle_results`.
The combined line is repository-ready, but production migration/canary/scheduler
activation remains operator-gated; migration 0026 alone is not a combined
Lifecycle release.
4. Never treat a 4xx contract error as a cold start.
5. Keep live, stale, unavailable, and synthetic states visibly distinct.

See [Render Free documentation](https://render.com/docs/free) and the
[Blueprint reference](https://render.com/docs/blueprint-spec).

## Sites/Cloudflare frontend handoff

The frontend is a vinext Sites project and keeps its existing npm lockfile.
`.openai/hosting.json` contains only the Sites `project_id` and optional logical
`d1`/`r2` bindings. It must never contain access tokens or runtime secrets.

Before handoff:

1. Set the `production-web` GitHub environment variable
   `PUBLIC_API_BASE_URL` to the verified HTTPS Render API origin. The release
   workflow exposes it to the existing frontend as `NEXT_PUBLIC_API_BASE_URL`.
2. Run the manual release workflow with `package_web=true`.
3. Verify the uploaded artifact came from the approved revision and includes
   `apps/web/dist` plus `.openai/hosting.json`.
4. In the Sites publishing flow, package and publish that exact validated
   source/build. Manage runtime values through Sites.
5. Start with private deployment. Make public access a separate deliberate
   approval after the formal-data, CORS, and security checklist passes.
6. Record the final verified URL in portfolio material; do not commit an
   invented placeholder URL.

No D1 or R2 binding is required for v1 because PostgreSQL/FastAPI own the public
read path. This changes the data-access layer only; the original TopicPilot
routes, navigation, styling, favorites, guide, and AI Studio remain the public
frontend.

## CORS and browser verification

After both surfaces are deployed:

```text
GET <API_ORIGIN>/healthz
GET <API_ORIGIN>/readyz
GET <API_ORIGIN>/api/v1/meta/data-status
```

Then open the deployed Sites URL and verify:

- API calls use HTTPS and the configured public origin;
- no mixed-content or CORS errors appear;
- formal data status and data date are visible;
- warming, unavailable, and stale states are distinguishable;
- no private URL or local filesystem path is present in page source/network
  responses.

## Release checklist

- [ ] CI passed on the release revision.
- [ ] Empty Neon test branch migrated successfully.
- [ ] Formal identity/read-model bootstrap reconciled against the approved
      PostgreSQL source.
- [ ] Gitleaks and public-data review passed.
- [ ] Render variables and GitHub protected environments are configured.
- [ ] Render health/readiness/data-status pass after a cold start.
- [ ] Sites build uses the verified API origin.
- [ ] CORS allows only intended production and local development origins.
- [ ] Screenshots contain no credentials, holdings, private data, or URLs.
- [ ] Rollback revision and operator are recorded privately.
