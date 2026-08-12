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
