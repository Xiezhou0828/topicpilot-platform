# TASK-A10-POST-CLOSE-CHECKPOINT-CANONICAL-PROMOTION-003

Date: 2026-09-29 (Asia/Taipei)

## Promotion scope

This report records the governed promotion of the locally verified A10
post-close checkpoint reconciliation. The implementation is carried by
`6433078c2da5e495fb5ab691b153b53025e159ca`; the preceding implementation
report is `89e0f1e5864a404bbf5b54ec8ff6ecc032827c7b`.

No A10 checkpoint semantics, A9/B2 business semantics, migration, scheduler
activation, or manual Production database mutation is authorized by this
report.

## Pre-promotion evidence

```text
TASK_ID=TASK-A10-POST-CLOSE-CHECKPOINT-CANONICAL-PROMOTION-003
TASK_STATUS=BLOCKED_CANONICAL_RECONCILIATION
PRE_TASK_CANONICAL_SHA=c3542a900d6c46e07bc4243804e9705475023316
ORIGINAL_CANDIDATE_SHA=6433078c2da5e495fb5ab691b153b53025e159ca
IMPLEMENTATION_SHA=6433078c2da5e495fb5ab691b153b53025e159ca
REPORT_SHA=89e0f1e5864a404bbf5b54ec8ff6ecc032827c7b
CANDIDATE_HEAD_SHA=5ff2a3e9038c1c077b2a59d485fed410775894ec
LATEST_CANONICAL_MAIN_SHA=ec46db023c8e701044e162dcf723f362002b88d7
CANONICAL_RECONCILIATION_STATUS=BLOCKED_SEMANTIC_CONFLICT
FOCUSED_TEST_STATUS=PASS; A10 core 40 passed; extended A10/A9/B2 suite 97 passed
BROADER_TEST_STATUS=802 passed / 4 skipped / 10 pre-existing failures
RUFF_STATUS=PASS
MIGRATION_HEAD_STATUS=PASS; one repository head 0046_task_stock_maint_relation_weight_authority_001d
MIGRATION_REQUIRED=NO
MIGRATION_APPLIED=NO
PRODUCTION_DB_MANUAL_MUTATION=NO
DEPLOYED=NO
PUSHED=YES; candidate branch pushed and PR #12 opened; main not updated
```

End of pre-promotion record.
The broader failures remain the previously classified corporate-action and
reference-bundle mismatch. They do not touch A10, live scheduling,
checkpoint reconciliation, formal publication, or A9/B2 runtime behavior.

## Canonical reconciliation blocker

GitHub `main` advanced from `c3542a900d6c46e07bc4243804e9705475023316` to
`ec46db023c8e701044e162dcf723f362002b88d7` through the Today official-source
promotion. The overlap is
`services/api/src/topicpilot_api/live/post_close.py`.

The newer mainline adds exchange-level market-fact fetching and
`_publish_market_facts_only()` when the stock daily reconciliation is not
ready. The A10 candidate changes the same finalization path into a durable
checkpoint phase machine with formal publication/readback reconciliation and a
fail-closed completion gate. The merge has two content conflict regions in
that finalization path. Resolving them requires an explicit semantic decision
about phase ordering, market-facts-only publication authority, and whether
that output is eligible to satisfy or remain separate from the A10 completion
gate. No automatic merge or silent behavior rewrite was made.

```text
CONFLICT_CLASS=SEMANTIC_CONFLICT
CONFLICT_FILES=services/api/src/topicpilot_api/live/post_close.py
MERGE_ATTEMPT=ABORTED_WITHOUT_CHANGES
PROMOTION=NOT_PERFORMED
CI=NOT_STARTED_FOR_CONFLICTING_PR
RELEASE=NOT_PERFORMED
```

## Promotion and release ledger

The remaining fields are filled only from GitHub, release workflow, and
read-only Production evidence after the exact SHA is promoted. A missing
worker revision or missing checkpoint readback is a release blocker, not a
successful Production claim.

```text
RECONCILED_CANDIDATE_SHA=NOT_RECONCILED
PROMOTED_CANONICAL_SHA=NOT_PERFORMED
RELEASED_SHA=NOT_PERFORMED
PUSH_STATUS=BLOCKED_AFTER_CANDIDATE_BRANCH_PUSH
CI_RUN_ID=PENDING
CI_SHA=PENDING
CI_STATUS=NOT_STARTED; PR is conflicting with latest main
RELEASE_RUN_ID=PENDING
RELEASE_STATUS=NOT_PERFORMED
POST_CLOSE_RUNTIME_OWNER=topicpilot-live
CHECKPOINT_RUNTIME_OWNER=topicpilot-live
FORMAL_PUBLICATION_RUNTIME_OWNER=topicpilot-live
WORKER_REVISION=PENDING
API_REVISION=c3542a900d6c46e07bc4243804e9705475023316
SCHEDULER_REVISION=NOT_SEPARATE
VERIFIED_TRADING_SESSION_DATE=PENDING
```

## Production safety boundary

Production verification must remain read-only for checkpoint state. It must not
insert or repair checkpoint events, create formal publications, force a
post-close run, intentionally kill a worker, apply a migration, or activate a
scheduler. A valid Production completion claim requires the deployed worker to
run the promoted SHA and requires checkpoint/publication/readback evidence for
an eligible session.

```text
DUPLICATE_INVOCATION_SAFE_PRODUCTION=PENDING
CRASH_RESUME_MODEL_VERIFIED_PRODUCTION=PENDING
FORMAL_PUBLICATION_IDEMPOTENT_PRODUCTION=PENDING
CHECKPOINT_PUBLICATION_RECONCILIATION_PRODUCTION=PENDING
FORMAL_READBACK_GATE_PRODUCTION=PENDING
BEFORE_1335_BEHAVIOR_PRODUCTION=PENDING
CLOSED_SESSION_BEHAVIOR_PRODUCTION=PENDING
ALREADY_COMPLETED_BEHAVIOR_PRODUCTION=PENDING
A9_B2_PRODUCTION_COMPATIBILITY=PENDING
A9_B2_SEMANTICS_CHANGED=NO
PRODUCTION_READY=NO
BLOCKERS=SEMANTIC_CONFLICT_WITH_LATEST_MAIN_IN_LIVE_POST_CLOSE
TASK_COMPLETE=NO
```
