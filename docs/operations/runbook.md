# Operations runbook

## Service objectives

This is a portfolio deployment with no production SLA. Operational goals are:

- a fresh clone starts with synthetic data through Docker Compose;
- a failed or conflicting bundle never becomes partially visible;
- operators can identify the deployed revision, bundle, data date, and health;
- public logs and errors do not disclose secrets or private data;
- a cold start is distinguishable from corrupt or stale data.

## Routine local operations

### Start

```bash
cp .env.example .env
docker compose up --build
```

Expected dependency order is `postgres -> migrate -> seed -> api -> web`.
`migrate` and `seed` are one-shot services and should exit with status 0.

### Inspect status

```bash
docker compose ps
docker compose logs --tail=200 migrate seed api web
curl --fail http://localhost:8000/healthz
curl --fail http://localhost:8000/readyz
curl --fail http://localhost:8000/api/v1/meta/data-status
```

### Stop or reset

```bash
docker compose down
docker compose down --volumes --remove-orphans  # destructive local reset
```

The second command deletes only the Compose-managed local PostgreSQL volume.
Never point it at a shared or cloud database.

## Manual bundle import

Before importing, confirm the bundle contains only the approved filenames and
its classification matches the target environment. Mount private bundles from
outside the repository and do not copy them into `fixtures/`.

The supported importer is the API package's `topicpilot-import` command. Run it
from the same immutable image/revision as the API. A repeated version/hash must
report a no-op. A repeated version with changed content must fail.

After import:

1. Query `data-status` and verify bundle version, date, hash/count summary.
2. Review all warning/error quality events.
3. Compare expected counts and key samples.
4. For private synchronization, append evidence to the parity template.

## Health interpretation

| `/healthz` | `/readyz` | Meaning | Action |
|---:|---:|---|---|
| 200 | 200 | Serving approved data | None |
| 200 | non-200 | Process alive; DB/migration/dataset unavailable | Inspect DB, migration, and latest import |
| Timeout/5xx | — | Cold start, crash, or platform outage | Retry briefly, then inspect provider logs |
| 200 | 200 but stale | Readable old data | Show stale label; investigate source/export schedule |

## Incident playbooks

### API cold start

Render Free may sleep after 15 minutes without inbound traffic and can take
about a minute to wake. Confirm the first request reaches Render, wait through
the UI's bounded retry window, then check `/healthz`. Do not run an external
keep-alive solely to defeat free-tier sleeping.

### Database connection failure

1. Confirm `DATABASE_URL` exists in the target protected environment.
2. Confirm it uses the intended Neon project/branch and required TLS settings.
3. Check Neon compute status and connection limits.
4. Run readiness, then a migration status command from a trusted environment.
5. Rotate the credential if it appeared in logs, artifacts, or shell history.

### Migration failure

1. Stop deployment; do not seed against an unknown schema.
2. Preserve migration and provider logs without credentials.
3. Reproduce against a new empty PostgreSQL database.
4. Fix with a forward migration; do not edit an applied migration.
5. Re-run empty-database migration and importer tests before release.

### Seed/import failure

1. Verify manifest and artifact hashes before examining SQL.
2. Confirm source classification is allowed.
3. Check natural-key and cross-file references.
4. Verify no partial facts are visible; the transaction should have rolled back.
5. Correct the producer and publish a new bundle version.

### OpenAPI drift

If CI reports drift, decide whether the API change is intentional. For an
intentional change, update API tests, normalized OpenAPI baseline, generated
TypeScript client, web usage, and documentation together. Otherwise restore the
previous contract. Never simply overwrite the baseline to make CI green.

### Suspected secret or private-data leak

1. Remove public access if the leak is active.
2. Rotate affected credentials immediately.
3. Preserve evidence privately; do not copy leaked values into issues.
4. Purge the material from the current tree and deployment artifacts.
5. Follow repository-history remediation appropriate to the host.
6. Re-run gitleaks and public-data review before restoring access.

## Backup and recovery

Public synthetic data is reproducible from migrations and the committed bundle,
so the default recovery is rebuild rather than database restore. Cloud-provider
backups are still useful for deployment continuity but are not the source of
truth. Private bundles and parity evidence follow the private system's retention
policy and are not stored here.

## Release and rollback

- CI must pass on the exact release revision.
- Render auto-deploy is disabled; the manual workflow uses a protected deploy
  hook and environment approval.
- Sites publication is a separate explicit handoff of the validated frontend.
- Roll back application code to a known compatible revision. Database rollback
  should normally be a forward corrective migration, not a destructive down
  migration.
- After rollback, verify health, readiness, data status, and one representative
  stock/topic/strategy query.
