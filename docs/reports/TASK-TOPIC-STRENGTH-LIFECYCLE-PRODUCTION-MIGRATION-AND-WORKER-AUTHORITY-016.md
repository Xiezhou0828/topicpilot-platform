# TASK-TOPIC-STRENGTH-LIFECYCLE-PRODUCTION-MIGRATION-AND-WORKER-AUTHORITY-016

## Terminal disposition

This task was limited to resolving the migration and Worker authority blockers
from TASK-015. It did not activate the Today/Topic Production stack.

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-PRODUCTION-MIGRATION-AND-WORKER-AUTHORITY-016
TASK_STATUS=BLOCKED_OWNER_MIGRATION_APPROVAL_REQUIRED
CURRENT_MAIN_SHA=cb67f9c599caf3ceabeb290a7b433e1d4a5210fa
PRODUCTION_MIGRATION_HEAD_BEFORE=0046_task_stock_maint_relation_weight_authority_001d
EXPECTED_MIGRATION=0047_task_topic_role_strength_design_freeze
MIGRATION_SCOPE_AUDIT=PASS
MIGRATION_GRAPH_STATUS=PASS_SINGLE_HEAD_0047
OWNER_MIGRATION_APPROVAL_STATUS=BLOCKED_NOT_EVIDENCED
```

The task prompt authorizes the bounded workstream, but the repository's
governance explicitly requires separate Owner authority for Production data
mutation. Existing Owner acceptance authorizes forward observation and
diagnostic flags; it does not authorize applying migration 0047. TASK-015 also
records that a separate migration activation approval is required.

## Migration 0047 audit

The canonical migration is
`services/api/alembic/versions/0047_task_topic_role_strength_design_freeze.py`.

```text
REVISION=0047_task_topic_role_strength_design_freeze
DOWN_REVISION=0046_task_stock_maint_relation_weight_authority_001d
CLASSIFICATION=SCHEMA_ONLY
TABLE=topicpilot.topic_score_projection_members
CHANGE=Replace check constraint score_importance with the additive set 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75
DATA_MIGRATION=NO
BUSINESS_ROW_REWRITE=NO
UPGRADE_DESTRUCTIVE_DATA_EFFECT=NO
DOWNGRADE_BEHAVIOR=Refuses downgrade when 1.25/1.50/1.75 rows exist; otherwise restores the legacy check constraint
RUNTIME_DEPENDENCY=Canonical runtime accepts the expanded REP/CORE design-freeze importance values
```

The migration directly follows the Production-reported 0046 head. The
repository contains one Alembic head, 0047. The canonical CI migration and
Docker smoke gates passed on the current main lineage, including upgrade and
rollback coverage against disposable databases. No Production migration was
run from this task.

## Production safety and execution status

The public read-only migration endpoint reported 0046 before this task. The
available repository procedure uses the protected Render release image and its
direct `MIGRATION_DATABASE_URL`; the API and Worker startup commands run
`alembic upgrade head`. No protected database backup/concurrency/recovery
control-plane evidence was available to this task, and no Owner approval for
the Production mutation was present in canonical governance records.

```text
MIGRATION_RUN_ID=NONE
MIGRATION_EXECUTION_STATUS=NOT_RUN_OWNER_APPROVAL_MISSING
PRODUCTION_MIGRATION_HEAD_AFTER=NOT_RUN
MIGRATION_HEAD_STATUS=NOT_VERIFIED_AFTER_NO_EXECUTION
SCHEMA_MUTATION_OCCURRED=NO
BUSINESS_DATA_MUTATED=NO
```

No manual `ALTER TABLE`, `INSERT`, `UPDATE`, stamp, backfill, score, lifecycle,
or observation write was performed.

## Worker authority audit

The canonical topology defines a separate Render worker named `topicpilot-live`
with `autoDeployTrigger: off` and the command:

```text
alembic upgrade head && exec topicpilot-live
```

The existing GitHub Actions release workflow only has a protected API deploy
hook and a Web packaging job. It has no Worker deploy job or Worker-specific
protected environment trigger. Repository operations documentation provides a
read-only `topicpilot-provider-lineage` command whose optional `buildSha` can
come from `RENDER_GIT_COMMIT` or `GIT_SHA`, but no protected Worker runtime
readback was available to this task.

```text
WORKER_RELEASE_AUTHORITY_STATUS=BLOCKED_WORKER_RELEASE_AUTHORITY_MISSING
WORKER_RELEASE_WORKFLOW=NONE_IN_CANONICAL_GITHUB_ACTIONS
WORKER_RELEASE_SOURCE=Render topicpilot-live blueprint; autoDeployTrigger=off
WORKER_READBACK_METHOD=NOT_ESTABLISHED; protected runtime metadata unavailable
WORKER_READBACK_STATUS=BLOCKED_WORKER_READBACK_UNAVAILABLE
REQUESTED_WORKER_SHA=NOT_REQUESTED
BUILT_WORKER_SHA=NOT_BUILT_FOR_PRODUCTION
RUNTIME_WORKER_SHA=NOT_VERIFIED
WORKER_SHA_STATUS=NOT_APPLICABLE_NO_RELEASE
WORKER_PRODUCTION_RELEASED=NO
```

No manual Render deployment, image-tag inference, API-to-Worker inference, or
Worker release was performed. Establishing a real Worker authority path would
require a separately governed platform/operator capability or a minimal
canonical observability change; neither was silently invented here.

## Independent conditions

The prior post-close failure remains a separate runtime/data-source condition:

```text
EXCHANGE_NO_DATA_STATUS=REMAINS_RELEVANT; prior governed run failed with EXCHANGE_NO_DATA
OBSERVATION_SESSION_COUNT_CHANGED=NO
API_DEPLOYED=NO
WEB_DEPLOYED=NO
```

TASK-015 was not resumed. No Today/Topic formal readback, observation capture,
frontend publication, scheduler activation, or Production-ready claim was
made.

## Final status

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-PRODUCTION-MIGRATION-AND-WORKER-AUTHORITY-016
TASK_STATUS=BLOCKED_OWNER_MIGRATION_APPROVAL_REQUIRED
CURRENT_MAIN_SHA=cb67f9c599caf3ceabeb290a7b433e1d4a5210fa

PRODUCTION_MIGRATION_HEAD_BEFORE=0046_task_stock_maint_relation_weight_authority_001d
EXPECTED_MIGRATION=0047_task_topic_role_strength_design_freeze
MIGRATION_SCOPE_AUDIT=PASS
MIGRATION_GRAPH_STATUS=PASS_SINGLE_HEAD_0047
OWNER_MIGRATION_APPROVAL_STATUS=BLOCKED_NOT_EVIDENCED
MIGRATION_RUN_ID=NONE
MIGRATION_EXECUTION_STATUS=NOT_RUN_OWNER_APPROVAL_MISSING
PRODUCTION_MIGRATION_HEAD_AFTER=NOT_RUN
MIGRATION_HEAD_STATUS=NOT_VERIFIED_AFTER_NO_EXECUTION
SCHEMA_MUTATION_OCCURRED=NO
BUSINESS_DATA_MUTATED=NO

WORKER_RELEASE_AUTHORITY_STATUS=BLOCKED_WORKER_RELEASE_AUTHORITY_MISSING
WORKER_RELEASE_WORKFLOW=NONE_IN_CANONICAL_GITHUB_ACTIONS
WORKER_RELEASE_SOURCE=Render topicpilot-live blueprint; autoDeployTrigger=off
WORKER_READBACK_METHOD=NOT_ESTABLISHED
WORKER_READBACK_STATUS=BLOCKED_WORKER_READBACK_UNAVAILABLE
REQUESTED_WORKER_SHA=NOT_REQUESTED
BUILT_WORKER_SHA=NOT_BUILT_FOR_PRODUCTION
RUNTIME_WORKER_SHA=NOT_VERIFIED
WORKER_SHA_STATUS=NOT_APPLICABLE_NO_RELEASE
WORKER_PRODUCTION_RELEASED=NO

EXCHANGE_NO_DATA_STATUS=REMAINS_RELEVANT
OBSERVATION_SESSION_COUNT_CHANGED=NO
API_DEPLOYED=NO
WEB_DEPLOYED=NO
PRODUCTION_READY=NO
TASK_015_RESUMABLE=NO

KNOWN_LIMITATIONS=Owner migration approval, protected DB safety evidence, governed Worker release trigger, and authoritative Worker readback are unavailable.
OWNER_DECISIONS_REQUIRED=Explicitly approve Production migration 0047 with the protected DB safety procedure; provide or authorize a governed Worker release/readback path.
TASK_COMPLETE=NO
NEXT_RECOMMENDED_TASK=After the two authority gates are supplied, execute 0047 only, verify head 0047, establish Worker exact-SHA readback, then resume TASK-TODAY-TOPIC-LOWER-HALF-PRODUCTION-ACTIVATION-015.
```

## Evidence

- Current canonical main: `cb67f9c599caf3ceabeb290a7b433e1d4a5210fa`
- Migration: `services/api/alembic/versions/0047_task_topic_role_strength_design_freeze.py`
- Prior activation blocker: `docs/reports/TASK-TODAY-TOPIC-LOWER-HALF-PRODUCTION-ACTIVATION-015.md`
- Owner acceptance: `docs/reports/TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003/owner-acceptance.md`
- Governed release configuration: `.github/workflows/deploy.yml`, `render.yaml`
- Production migration readback before this task: `0046_task_stock_maint_relation_weight_authority_001d`

No Production release, schema mutation, business-data mutation, Worker release,
or TASK-015 activation occurred.
