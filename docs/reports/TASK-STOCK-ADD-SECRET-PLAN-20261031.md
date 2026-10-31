# Stock-add protected plan handoff

```text
TASK_ID=TASK-STOCK-ADD-SECRET-PLAN-20261031
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
AUTHORITY_BOUNDARY=Change the protected Production stock-add workflow to accept a plan digest and load the approved plan from production-db-maintenance; continue 2468 only after fresh production readback, dry-run review, and exact Owner confirmation. No Production write is authorized by this workflow change alone.
CANONICAL_SHA=37131e55d4bcd863fe33b353bf1736d8aebe55b2 (verified from origin/main at task start)
SOURCE_SHA=37131e55d4bcd863fe33b353bf1736d8aebe55b2
MIGRATION_HEAD=UNKNOWN at task start; must be read from live Production before the 2468 plan is refreshed.
FILES_CHANGED=.github/workflows/stock-add-master-write.yml; services/api/tests/test_stock_add_master_write_workflow.py; docs/operations/stock-add-master-write.md; docs/WORK_ORDERS.md; this report; local topicpilot-stock-add Skill.
SEMANTICS_CHANGED=No stock, research, topic, weight, or reference-universe semantics. The plan transport changes from public workflow_dispatch JSON to a protected Environment secret validated against its declared and recomputed canonical SHA-256.
PRODUCTION_DEPENDENCY=production-db-maintenance Environment secret and writer credential; a fresh production-catalog-readonly run; dry-run before any write; exact plan-bound final confirmation before apply.
FOLLOW_UP_REQUIRED=YES — merge and validate the workflow change, set the approved plan secret, obtain fresh authority readback, run dry-run, then continue only under the exact final confirmation. Reference-universe and post-close gates remain separate.
WORKTREE_STATUS=Isolated clean task worktree C:\tpw\stock-add-secret-2468 at start; canonical dirty checkout left untouched.
```

## Evidence and closure

Implementation, validation, canonical SHA, final authority readback, and remaining
Production gates will be recorded here as they are completed. Secret values and
the research package are intentionally not copied into this public repository.
