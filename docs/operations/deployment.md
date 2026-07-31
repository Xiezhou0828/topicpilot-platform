# Deployment handoff

## Topology

| Surface | Target | Responsibility |
|---|---|---|
| PostgreSQL | Neon | Persistent synthetic read model |
| FastAPI | Render Free web service | Read API and OpenAPI |
| React/vinext | Sites/Cloudflare | Public frontend |
| CI/release | GitHub Actions | Validation, gated API trigger, web artifact |

This configuration is a portfolio/demo deployment, not production-grade
infrastructure. Provider free-tier behavior and quotas can change; review the
official service documentation before each public release.

## Neon setup

1. Create a dedicated Neon project/branch for the public synthetic demo.
2. Create a least-privilege application role where plan capabilities allow.
3. Copy a TLS-enabled pooled connection string from the Neon dashboard.
4. Store it as `DATABASE_URL` in Render and the protected GitHub environment;
   never put it in `.env.example`, `render.yaml`, an issue, or a build artifact.
5. Run migrations and seed only from the approved release image.

Use a SQLAlchemy/psycopg URL. If the copied URL starts with `postgresql://`,
change only that scheme to `postgresql+psycopg://`; the current application
does not rewrite the driver automatically. Preserve provider-required query
parameters such as `sslmode=require`.

## Render API blueprint

`render.yaml` defines only the FastAPI web service. It intentionally does not
create a Render database because persistence is provided by Neon.

Required Render variables:

| Variable | Secret | Purpose |
|---|---:|---|
| `DATABASE_URL` | Yes | Neon pooled PostgreSQL connection |
| `TOPICPILOT_CORS_ORIGINS` | No, environment-specific | Exact Sites/public web origin(s) |
| `TOPICPILOT_LOG_LEVEL` | No | Usually `INFO` |
| `TOPICPILOT_DEMO_MODE` | No | Must be `true` for public deployment |
| `TOPICPILOT_BUNDLE_PATH` | No | Synthetic fixture path in the image |

The Free plan does not provide Render's paid pre-deploy command. Therefore the
container startup command performs idempotent `alembic upgrade head`, imports
the committed synthetic bundle as a no-op-safe seed, and only then starts
Uvicorn. A paid deployment should move migrations into the provider's
pre-deploy phase and keep application startup free of migration ownership.

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
3. Stop after the documented UI timeout and switch to the clearly labelled
   public synthetic bundle instead of replacing the page design.
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
   approval after the synthetic-data and security checklist passes.
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
- synthetic-data warning and data date are visible;
- warming, unavailable, and stale states are distinguishable;
- no private URL or local filesystem path is present in page source/network
  responses.

## Release checklist

- [ ] CI passed on the release revision.
- [ ] Empty Neon test branch migrated successfully.
- [ ] Synthetic bundle imported and replayed as a no-op.
- [ ] Gitleaks and public-data review passed.
- [ ] Render variables and GitHub protected environments are configured.
- [ ] Render health/readiness/data-status pass after a cold start.
- [ ] Sites build uses the verified API origin.
- [ ] CORS allows only intended production and local development origins.
- [ ] Screenshots contain no credentials, holdings, private data, or URLs.
- [ ] Rollback revision and operator are recorded privately.
