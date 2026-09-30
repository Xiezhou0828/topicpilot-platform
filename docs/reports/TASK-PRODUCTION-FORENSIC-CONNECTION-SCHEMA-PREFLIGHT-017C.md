# TASK-PRODUCTION-FORENSIC-CONNECTION-SCHEMA-PREFLIGHT-017C

## Disposition

The authorized Production read-only schema preflight was executed exactly
once. It failed at the database connection layer with the sanitized
classification `DNS_FAILED`. No schema metadata query or incident data query
was reached. The existing incident `POST_CLOSE_RUN_READBACK` was not retried.

## Canonical and workflow evidence

```text
TASK_ID=TASK-PRODUCTION-FORENSIC-CONNECTION-SCHEMA-PREFLIGHT-017C
CURRENT_MAIN_SHA=62c5a2c6ee51f087a4729d47e74750b9581181dd
SOURCE_WORKFLOW_RUN_ID=36621398206
PREFLIGHT_WORKFLOW_RUN_ID=36623970755
PREFLIGHT_TOOL_SHA=62c5a2c6ee51f087a4729d47e74750b9581181dd
PREFLIGHT_COMMAND=PRODUCTION_READONLY_SCHEMA_PREFLIGHT
```

The source 017B acceptance run had already passed its Environment, reviewer,
exact-SHA, and CLI preflight before failing with `FORENSIC_QUERY_FAILED`.
This task added and canonicalized a separate metadata-only preflight workflow;
it did not modify the existing incident readback workflow.

## Protected Environment state

The following were verified without reading any secret value:

```text
PRODUCTION_READONLY_ENVIRONMENT=READY
REQUIRED_REVIEWER_RULE=READY
PRODUCTION_READONLY_ROLE=topicpilot_forensic_readonly
TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL=CONFIGURED_VALUE_NOT_READ
```

The Owner-provisioned database role was not altered. No database
administrative credential was used.

## Preflight result

The protected workflow passed Environment protection, exact canonical checkout,
and CLI installation. The fixed preflight command then returned only the
sanitized code `DNS_FAILED`.

```text
DATABASE_CONNECT_STATUS=FAILED
CONNECTION_FAILURE_CLASS=DNS_FAILED
DATABASE_NAME=UNAVAILABLE
DATABASE_CURRENT_USER=UNAVAILABLE
DATABASE_SESSION_USER=UNAVAILABLE
TRANSACTION_READONLY=UNAVAILABLE

RUNS_TABLE_EXISTS=NOT_RUN
ATTEMPTS_TABLE_EXISTS=NOT_RUN
CHECKPOINTS_TABLE_EXISTS=NOT_RUN

RUNS_SCHEMA_MATCH=NOT_RUN
ATTEMPTS_SCHEMA_MATCH=NOT_RUN
CHECKPOINTS_SCHEMA_MATCH=NOT_RUN
MISSING_COLUMNS=NOT_RUN
UNEXPECTED_RELEVANT_COLUMNS=NOT_RUN

RUNS_SELECT=NOT_RUN
ATTEMPTS_SELECT=NOT_RUN
CHECKPOINTS_SELECT=NOT_RUN
MUTATION_PRIVILEGES_PRESENT=NOT_RUN
```

No database name, role identity, connection string, driver detail, schema
row, table row, or secret value was emitted. Because the connection could not
resolve, the preflight did not execute the target metadata SELECTs.

## Failure classification

```text
PRIMARY_FAILURE_LAYER=CONNECTION_URL_INVALID
REPOSITORY_FIX_REQUIRED=NO
OWNER_SECRET_CORRECTION_REQUIRED=YES
```

`CONNECTION_URL_INVALID` is the bounded connection-layer classification for
the observed DNS failure. It does not assert that the secret value is wrong;
the Owner must verify, in a protected administrative context, that the
environment secret points to the intended Production host/project and that
the GitHub runner can resolve and reach that host over the required TLS path.
The secret must not be pasted into chat, logs, reports, or repository files.

No role mismatch, transaction-read-only failure, missing table, missing
column, missing SELECT privilege, or forensic query defect can be concluded
because none of those layers were reached.

## Safety boundary

```text
PRODUCTION_DB_MUTATED=NO
INCIDENT_DATA_READ=NO
POST_CLOSE_RUN_READBACK=NOT_EXECUTED
POST_CLOSE_RETRIED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
TASK_015_CHANGED=NO
OBSERVATION_CHANGED=NO
SANITIZED_DIAGNOSTIC_ARTIFACT=NOT_GENERATED; CONNECTION_FAILED
```

## Final status

```text
TASK_STATUS=BLOCKED_DATABASE_READONLY_ATTESTATION
TASK_COMPLETE=NO
NEXT_RECOMMENDED_TASK=Owner verify the production-readonly secret host/DNS/TLS reachability without exposing the secret, then issue a new explicit preflight authorization before any further execution
```

## Renewed preflight attempt

The Owner explicitly authorized one renewed 017C test after correcting the
secret. The latest canonical main was fetched first:

```text
RENEWED_CURRENT_MAIN_SHA=3b09a5ae5e74d48c724e27fdc3a0eeac0862320f
RENEWED_PREFLIGHT_WORKFLOW_RUN_ID=36667554536
RENEWED_PREFLIGHT_TOOL_SHA=3b09a5ae5e74d48c724e27fdc3a0eeac0862320f
RENEWED_PREFLIGHT_COMMAND=PRODUCTION_READONLY_SCHEMA_PREFLIGHT
```

The protected Environment approval, exact-SHA checkout, and CLI installation
passed. The fixed preflight then failed at authentication with the sanitized
classification `AUTHENTICATION_FAILED`. This is a new connection-layer
result; it replaces the prior DNS failure as the current blocker. The
preflight stopped before schema, privilege, or table-row inspection.

```text
RENEWED_DATABASE_CONNECT_STATUS=FAILED
RENEWED_CONNECTION_FAILURE_CLASS=AUTHENTICATION_FAILED
DATABASE_NAME=UNAVAILABLE
DATABASE_CURRENT_USER=UNAVAILABLE
DATABASE_SESSION_USER=UNAVAILABLE
TRANSACTION_READONLY=UNAVAILABLE

RUNS_TABLE_EXISTS=NOT_RUN
ATTEMPTS_TABLE_EXISTS=NOT_RUN
CHECKPOINTS_TABLE_EXISTS=NOT_RUN
RUNS_SCHEMA_MATCH=NOT_RUN
ATTEMPTS_SCHEMA_MATCH=NOT_RUN
CHECKPOINTS_SCHEMA_MATCH=NOT_RUN
MISSING_COLUMNS=NOT_RUN
UNEXPECTED_RELEVANT_COLUMNS=NOT_RUN
RUNS_SELECT=NOT_RUN
ATTEMPTS_SELECT=NOT_RUN
CHECKPOINTS_SELECT=NOT_RUN
MUTATION_PRIVILEGES_PRESENT=NOT_RUN
SANITIZED_DIAGNOSTIC_ARTIFACT=NOT_GENERATED; AUTHENTICATION_FAILED
```

No secret value, connection string, driver detail, database row, schema row,
or incident UUID row was exposed. No additional preflight or incident
readback was attempted after this result.

```text
PRIMARY_FAILURE_LAYER=AUTHENTICATION_FAILURE
REPOSITORY_FIX_REQUIRED=NO
OWNER_SECRET_CORRECTION_REQUIRED=YES
PRODUCTION_DB_MUTATED=NO
INCIDENT_DATA_READ=NO
POST_CLOSE_RETRIED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
TASK_STATUS=BLOCKED_DATABASE_READONLY_ATTESTATION
TASK_COMPLETE=NO
NEXT_RECOMMENDED_TASK=Owner verify that the protected secret credential matches the dedicated topicpilot_forensic_readonly login and Production database endpoint, without exposing the secret; obtain new authorization before another preflight
```
