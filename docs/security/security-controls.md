# Security controls

## Threat model

The v1 service is a public, anonymous, read-only demo. Primary risks are secret
exposure, publishing private/licensed data, injection through imported content,
overly broad CORS, dependency/image compromise, denial of service against free
resources, and diagnostic leakage.

Authentication, user-generated content, admin writes, order execution, and
trading integrations are out of scope. Adding any of them requires a new threat
model and work order.

## Controls by layer

### Repository and CI

- `.env` and common generated artifacts are ignored; `.env.example` contains
  local-only non-secret defaults.
- Gitleaks scans full reachable history in CI.
- GitHub Actions default to read-only contents permission.
- Deployment is manual and protected by GitHub environments.
- Provider credentials are environment secrets, never workflow literals.
- Lockfiles and bounded Python dependency ranges support reproducible review.

### Containers

- API and web runtime containers run as non-root users.
- Only required ports are exposed.
- Fixture mounts are read-only.
- Healthchecks have bounded timeout/retry behavior.
- The public image includes synthetic fixtures only; private bundles are mounted
  at runtime in private environments.
- `.env`, Git metadata, tests containing secrets, and private data must be
  excluded from production build contexts/artifacts.

### Importer and database

- Contract/schema/hash/reference validation precedes publication.
- One transaction prevents partial snapshots.
- Unique constraints implement replay and duplicate-key protection.
- Bound parameters/ORM APIs are required; no string-built SQL from bundle data.
- Public database roles should have only required schema/table privileges.
- Error messages and lineage records must not contain credentials or full paths.

### API

- Only GET/HEAD/OPTIONS are expected in v1 application routes.
- CORS uses an explicit comma-separated allowlist; wildcard origins are not
  permitted for public deployment.
- Problem responses omit stack traces, SQL, and internal paths.
- Pagination maxima prevent unbounded reads.
- OpenAPI drift and endpoint tests make accidental write routes visible.
- Hosting/provider request limits are the initial abuse control; add explicit
  rate limiting before traffic or risk increases.

### Frontend and BI

- Browser bundles receive only the public API base URL, never `DATABASE_URL`.
- Rendered evidence/reason text is treated as untrusted content and escaped.
- No secret belongs in a `NEXT_PUBLIC_*` variable.
- Power BI uses synthetic extracts for public artifacts and a read-only database
  role for private development.

## Required production configuration

- Neon pooled TLS connection URL stored in Render.
- Exact production web origin in `TOPICPILOT_CORS_ORIGINS`.
- GitHub environments `production-api` and `production-web` with required
  reviewers and deployment branch limited to `main`.
- `RENDER_DEPLOY_HOOK_URL` only in `production-api`.
- `PUBLIC_API_BASE_URL` as a non-secret environment variable in
  `production-web`.

## Verification

- CI: Ruff, pytest, empty PostgreSQL migration, frontend test/build, OpenAPI
  contract, Compose smoke, and gitleaks.
- Release: synthetic-data review, CORS test, image/history scan, health/readiness,
  and public error-response inspection.
- Quarterly or before interviews: update dependencies/images, re-run all checks,
  and verify provider permissions/secrets are still minimal.

## Known v1 limitations

- Anonymous APIs can be scraped; only synthetic data is exposed.
- Free hosting is not resilient and can be exhausted or cold-started.
- Dependency ranges do not replace vulnerability monitoring.
- Gitleaks reduces but cannot eliminate the need for human data review.
- No `.pbix` can be considered safe until opened and inspected in Power BI
  Desktop for embedded connection details and cached data.
