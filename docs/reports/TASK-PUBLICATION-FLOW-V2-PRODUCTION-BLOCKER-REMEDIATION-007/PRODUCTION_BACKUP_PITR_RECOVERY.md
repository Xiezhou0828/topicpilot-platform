# Production backup, PITR, and recovery

## Verified database facts

The current forensic artifact identifies:

- databaseName=neondb
- databaseRole=topicpilot_forensic_readonly
- transactionReadOnly=true
- no mutation operation was attempted

The same artifact records permission failures for SELECT on topicpilot.topics and public.alembic_version. migrationHead is therefore null in this current artifact. Task 006 historically read migration head 0050_task_purge_retired_topics; that historical value was not re-executed or re-proved by Task 007.

## Owner-assisted Neon readback

The authenticated Neon Console was verified as the Production project `topicpilot` (`fancy-tree-29602211`), branch `production` (`br-icy-brook-azcflty0`), database `neondb`, AWS Asia Pacific 1 (Singapore), PostgreSQL 18.

- History/PITR window: 6 hours.
- At readback, earliest restore time: 2026-10-09 13:37 GMT+8 (rolling window; exact boundary advances with time).
- Snapshots: none.
- Backup schedule: none.
- Restore controls were not activated; Preview data and Restore were not clicked.

The rolling window no longer contains a recoverable 2026-10-08 point. This is configuration/readback evidence only; it is not proof that a restore is available for that date.

BACKUP_CONFIGURATION=NO_SNAPSHOT_OR_SCHEDULE_OBSERVED
PITR_CONFIGURATION=6_HOUR_HISTORY_WINDOW
RECOVERY_POINT=2026-10-09_13:37_GMT+8_AT_READBACK; NO_2026-10-08_POINT
RECOVERY_PROCEDURE=NEON_CONSOLE_RESTORE_CONTROL_OBSERVED_NOT_EXECUTED
ISOLATED_RECOVERY_TEST=NOT_AUTHORIZED
DATABASE_RECOVERY_READINESS=BLOCKED

## Role/privilege readback

Only read-only SQL was executed. `topicpilot_forensic_readonly` can connect, has `topicpilot` schema usage, and has SELECT only on `live_collector_runs`, `live_collector_attempts`, and `live_collector_checkpoints`; it has no INSERT, UPDATE, or DELETE. Direct checks returned `can_select=false` for both `topicpilot.topics` and `public.alembic_version`. No role, password, GRANT, or database object was changed.

The exact minimal SQL for Owner review, not executed, is:

```sql
GRANT SELECT ON TABLE topicpilot.topics, public.alembic_version
TO topicpilot_forensic_readonly;
```

This is only the confirmed missing-object scope; it is not an authorization request and may not be sufficient for the complete bounded diagnostic. Separate Owner approval is required before any privilege change.

The architecture deployment document still does not define a restore operator, isolated restore target, or restore-drill objectives. An isolated Production restore was not attempted because the task forbids destructive or unauthorized recovery operations.

Owner action required: define an approved non-Production restore target/runbook and backup policy; do not treat a backup toggle alone as proof of recoverability.
