# Production forensic readback

## Purpose

This is the governed, reusable Production evidence channel for operational
readback. It is intended for incident evidence such as a bounded
`POST_CLOSE` run, its attempt distributions, and its checkpoint timeline. It
does not repair an incident, retry a run, deploy an application, activate a
Worker, or write Production data.

The initial approved command is:

```text
POST_CLOSE_RUN_READBACK
```

The command accepts exactly one UUID. It does not accept SQL, table names,
where clauses, shell fragments, wildcards, or multiple run IDs.

## Security model

The workflow is `.github/workflows/production-forensic-readback.yml` and must
run in the protected GitHub Environment `production-readonly`. The Environment
must require an Owner-approved reviewer before a job can receive its secret.
The workflow also requires an exact 40-character commit SHA and rejects branch
names at dispatch time. The checked-out SHA must be an ancestor of the current
canonical `origin/main`.

The only Production secret consumed by the workflow is:

```text
TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL
```

It must be a dedicated database login, never the application writer URL,
migration URL, or an administrator URL. The expected login name is supplied as
the protected Environment variable:

```text
TOPICPILOT_PRODUCTION_READONLY_ROLE
```

The workflow never prints either value. The repository CLI does not fall back
to `DATABASE_URL`, `MIGRATION_DATABASE_URL`, or
`TOPICPILOT_PRODUCTION_DATABASE_URL`.

Before any forensic `SELECT`, the CLI:

1. opens a database transaction;
2. executes `SET TRANSACTION READ ONLY`;
3. verifies `SHOW transaction_read_only` is `on`;
4. reads and verifies `current_user` and `session_user`; and
5. reads the target-table privilege probe.

Any failed assertion stops the command before operational evidence is read.
The artifact records the connected role, session role, read-only assertion,
and whether mutation privileges were observed. Production mutation is never
used as a privilege probe.

## Approved database scope

Only these tables are queried:

```text
topicpilot.live_collector_runs
topicpilot.live_collector_attempts
topicpilot.live_collector_checkpoints
```

The database role requires `CONNECT`, `USAGE` on schema `topicpilot`, and
`SELECT` on those three tables only. It must not own objects, inherit an
administrator role, hold migration authority, or have mutation privileges.
No broad `SELECT ON ALL TABLES` grant is part of this channel.

## Owner provisioning path

Role and Environment provisioning are administrative actions and are not
performed by the application, the forensic CLI, or ordinary CI. An authorized
database owner should use the platform's administrative console or protected
admin session to create a dedicated login and apply the narrow matrix below.
The password is generated and stored only in the protected GitHub Environment
secret; it is never pasted into a workflow command, report, or chat.

```sql
-- Run only in the governed Production database-admin path.
CREATE ROLE topicpilot_forensic_readonly LOGIN PASSWORD '<operator-generated-secret>';
ALTER ROLE topicpilot_forensic_readonly NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT CONNECT ON DATABASE <production-database> TO topicpilot_forensic_readonly;
GRANT USAGE ON SCHEMA topicpilot TO topicpilot_forensic_readonly;
GRANT SELECT ON TABLE
  topicpilot.live_collector_runs,
  topicpilot.live_collector_attempts,
  topicpilot.live_collector_checkpoints
  TO topicpilot_forensic_readonly;
```

The owner must additionally verify that the login has no inherited role with
`INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, DDL, or mutation-capable function
authority, and that it is not an object owner. That verification belongs in
platform/database administration evidence, not in the application process.

In GitHub, create `production-readonly`, configure required reviewers and the
appropriate deployment branch policy, then add the secret and variable named
above. Do not use the existing `production-api`, `production-worker`, or
`production-db-maintenance` Environment secrets for this channel.

## Workflow usage

After the Environment and role are attested, dispatch the workflow with an
exact canonical SHA:

```text
forensic_command = POST_CLOSE_RUN_READBACK
run_id           = <one UUID>
forensic_ref     = <40-character commit SHA>
```

The workflow installs only the API package, invokes the repository-owned CLI,
and uploads one sanitized artifact named:

```text
production-forensic-readback-<run_id>.json
```

It also writes a compact job summary containing no credential or raw database
output. A missing secret, missing expected role, non-canonical SHA, invalid
UUID, writable transaction, role mismatch, or query failure is a blocked run;
it is not converted into an empty or partial success artifact.

## Artifact contract

The JSON artifact contains:

```json
{
  "forensicToolSha": "<exact SHA>",
  "databaseRole": "<current_user>",
  "sessionUser": "<session_user>",
  "transactionReadOnly": true,
  "targetPrivileges": [],
  "mutationPrivilegesPresent": "NO",
  "run": {},
  "attemptSummary": [],
  "attemptRepresentatives": [],
  "checkpointTimeline": [],
  "firstFailedCheckpoint": null,
  "marketSummary": [],
  "errorSummary": [],
  "providerStatusSummary": [],
  "generatedAt": "<UTC timestamp>"
}
```

Run rows preserve status, timestamps, counts, provider/adapter identity, and
failure code/message after bounded text sanitization. Attempt results are
grouped by market, status, provider status, and error code, with at most 50
sanitized representative rows. Checkpoints preserve their ordered timeline,
counts, request/failure counts, status, hash, and a whitelist of operational
metadata fields. No raw JSON metadata, connection string, authorization data,
headers, cookies, PII, or unrelated business data is emitted.

## Incident use case

The first intended acceptance case is the 2026-09-29 run:

```text
30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
```

Reading it is a separate, SELECT-only acceptance action. The command must not
retry the run. Any root-cause remediation, provider change, Worker release,
post-close retry, or TASK-015 activation must be a separate owner-authorized
task.

## Forbidden actions

This channel does not:

- execute arbitrary SQL;
- use application, migration, or admin credentials;
- issue database mutation, DDL, migration, or function calls;
- expose a public API route;
- deploy API, Web, or Worker services;
- activate a scheduler or post-close run;
- retry or replay the incident;
- alter Production data, schema, or configuration.

The repository implementation is `topicpilot-production-readback` and the
focused unit and disposable-PostgreSQL tests are under
`services/api/tests/`.
