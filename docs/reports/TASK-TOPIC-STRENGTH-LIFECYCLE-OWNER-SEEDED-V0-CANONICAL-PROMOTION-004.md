# Topic Strength/Lifecycle Owner-seeded V0 — Canonical Promotion

## Scope and reconciliation

This report records the exact candidate audit and canonical-promotion gates
for Owner-seeded V0. It does not redesign policy, recalibrate thresholds,
backfill observation sessions, apply migration 0047, deploy API/Worker/Web, or
mutate Production.

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-CANONICAL-PROMOTION-004
TASK_TYPE=CANONICAL_PROMOTION
REQUIRED_TERMINAL_STATE=COMPLETE_OWNER_SEEDED_V0_CANONICAL_PROMOTION
CURRENT_MAIN_SHA=7dee5f99e8127326b51c9672f3a01cab208a0f96
ORIGINAL_CANDIDATE_SHA=eb358c10968a78772376020a605edd62253e6dc4
ORIGINAL_MERGE_BASE_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be
ORIGINAL_AHEAD_BY=16
ORIGINAL_BEHIND_BY=4
RECONCILED_SOURCE_SHA=1d37107_PENDING_REPORT_COMMIT
RECONCILED_AHEAD_BY=0
RECONCILED_BEHIND_BY=0
LINEAGE_COMMIT_COUNT=17
LINEAGE_AUDIT_STATUS=PASS
UNEXPECTED_COMMIT_COUNT=0
POLICY_ID=topic-strength-lifecycle.owner-seeded-v0
POLICY_VERSION=v0
POLICY_HASH=5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef
POLICY_HASH_STATUS=PASS
IMPLEMENTATION_IDENTITY=0e083d41bcce1aa89e5339025f4d1f9d3586dfbf
IMPLEMENTATION_IDENTITY_MEANING=RUNTIME_SOURCE_IMPLEMENTATION_COMMIT
IMPLEMENTATION_IDENTITY_STATUS=PASS_PRESERVED_FROM_TASK_003
OWNER_REVIEW_STATUS=OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS
POLICY_CHANGED=NO
POLICY_RECALIBRATED=NO
OWNER_DECISIONS_REQUIRED=NONE_FOR_CANONICAL_PROMOTION;PR_BRANCH_PROTECTION_AND_CI_MUST_PASS
```

The original candidate was 16 commits ahead and 4 commits behind current
`main`. The reconciliation commit preserved all current main changes. The
complete ordered audit is in
`docs/reports/canonical-promotion-lineage-audit.md`.

## Policy and runtime boundary

The policy hash was recomputed by the Owner-seeded policy runner and matched
the policy JSON, runtime loader, tests, forward-observation manifests/schema,
backend read model, and governance artifacts. The implementation identity
continues to mean the runtime source implementation commit recorded by TASK-
003; it is not silently redefined as the later promotion merge SHA.

The accepted bounded defect correction remains present: deep broad CORE
weakness can satisfy the D guard and DECLINING predicate through `REP <= -1`
or `CORE median <= -2.5`, without requiring REP evidence when the deep CORE
condition is met. The exact regression passed.

Absolute and relative grades remain independent, Grade and Lifecycle remain
independent, structural roles remain Owner-governed, Topic authority remains
dynamic, and Relation Weight remains outside Topic Strength/Lifecycle scoring.
The frontend consumes backend read-model fields and does not rederive policy
thresholds or lifecycle transitions.

## Observation and migration status

```text
RUNTIME_REQUIRED_ARTIFACT_STATUS=PASS
GOVERNANCE_ARTIFACT_STATUS=PASS
RESEARCH_ARTIFACT_STATUS=PASS_EVIDENCE_ONLY
CALIBRATION_ARTIFACT_STATUS=PASS_NOT_RUNTIME_AUTHORITY
MIGRATION_HEAD=0047_task_topic_role_strength_design_freeze
MIGRATION_REQUIRED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
PRODUCTION_DB_MUTATED=NO
MANUAL_DATA_WRITE=NO
OBSERVATION_START_DATE=PENDING_RUNTIME_ACTIVATION
OBSERVATION_SESSION_COUNT=0
OBSERVATION_20D_STATUS=NOT_STARTED
OBSERVATION_40D_STATUS=NOT_STARTED
OBSERVATION_60D_STATUS=NOT_STARTED
DEPLOYED=NO
PRODUCTION_ACTIVE=NO
```

The read model remains fail-closed and diagnostic-only before activation. No
historical session or observation date was fabricated.

## Validation on the reconciled candidate

The baseline is the latest `origin/main` at
`7dee5f99e8127326b51c9672f3a01cab208a0f96`. The full API baseline had
`815 passed, 59 skipped, 10 failed`; the reconciled candidate had
`892 passed, 59 skipped, 10 failed`. The delta is `+77 passed`, with the same
10 failures. The failures are the existing corporate-action/reference-bundle
fixtures and are classified `PRE_EXISTING_CANONICAL` / `UNRELATED`; none
touches this candidate's Topic Strength/Lifecycle or Today reconciliation.

```text
FOCUSED_TEST_STATUS=PASS_109
SCENARIO_REPLAY_STATUS=PASS_25
FORWARD_OBSERVATION_TEST_STATUS=PASS
BACKEND_READ_MODEL_TEST_STATUS=PASS
FRONTEND_TEST_STATUS=PASS_183
BROADER_API_TEST_STATUS=892_PASS_59_SKIPPED_10_PRE_EXISTING_UNRELATED_FAILURES
TEST_COUNT_PRE=815_PASS_59_SKIPPED_10_FAILURES
TEST_COUNT_POST=892_PASS_59_SKIPPED_10_FAILURES
TEST_COUNT_DELTA=+77_PASS;FAILURES_UNCHANGED
TEST_COUNT_DELTA_REASON=TASK_004_TOPIC_READ_MODEL_FORWARD_OBSERVATION_AND_RECONCILIATION_COVERAGE
RUFF_STATUS=CHANGED_SCOPE_PASS;REPOSITORY_EXISTING_DEBT_RECORDED
LINT_STATUS=PASS_WITH_ONE_PREEXISTING_WARNING
BUILD_STATUS=PASS
OPENAPI_STATUS=PASS
GENERATED_CLIENT_STATUS=PASS
MIGRATION_GRAPH_STATUS=PASS_HEAD_0047_NO_APPLY
DIFF_CHECK_STATUS=PASS
CLIENT_TEST_STATUS=PASS_4
```

The frontend lint warning is the existing `FavoriteButton.tsx` missing hook
dependency warning. Repository-wide Ruff reports pre-existing research-file
debt; the changed Python scope passed.

## PR / merge record

```text
PR_NUMBER=PENDING_PR_CREATION
PR_HEAD_SHA=PENDING_PR_CREATION
PR_BASE_SHA=7dee5f99e8127326b51c9672f3a01cab208a0f96
PR_STATUS=PENDING
PR_MERGEABLE=PENDING
REQUIRED_CHECKS=Secret scan;Backend, migration, and OpenAPI;Frontend install, test, and build;Docker Compose smoke
PRE_MERGE_CI_RUN=PENDING
PRE_MERGE_CI_STATUS=PENDING
MERGE_STATUS=PENDING
PROMOTED_CANONICAL_SHA=PENDING
POST_MERGE_CI_RUN=PENDING
POST_MERGE_CI_STATUS=PENDING
```

No force push, bypass, squash, deployment, or Production activation is
authorized by this report. The normal repository merge policy must preserve
the audited lineage.

## Known limitations

- Historical calibration is unavailable as formal authority; calibration and
  replay files remain evidence-only.
- Full API suite retains 10 pre-existing reference-bundle failures and 59
  skipped integration tests without a configured PostgreSQL test database.
- The frontend lint warning is pre-existing.
- Forward observation requires a separate Production activation gate and does
  not start at canonical merge.
- The 0047 migration is present but not applied.

```text
ACHIEVED_TERMINAL_STATE=READY_FOR_PR
TASK_COMPLETE=NO
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=PR_CREATION_CI_MERGE_AND_POST_MERGE_CANONICAL_SHA_REMAIN
CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION
RELEASE_STATUS=NOT_PRODUCTION_RELEASED
PRODUCTION_VERIFICATION=NOT_RUN_BY_SCOPE
CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION
PUSH_REMOTE=NO
DEPLOY=NO
NEXT_RECOMMENDED_TASK=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-PRODUCTION-ACTIVATION-005
```
