# TASK-DATA-REF-006B G2 Preflight Integration, Exact-SHA CI, and Production Release Handoff

## Fixed handoff fields

```text
TASK_DATA_REF_006B = INTEGRATED_RELEASE_HANDOFF

006A_COMMIT_SHA = 2c8e88b3c1de3e324a6a1f7b3d1e9d00e3eff868
006A_BASE_SHA = 1c9938733d3befc2e3d6e7fffd5763197986d19f
CURRENT_ORIGIN_MAIN_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
MERGE_BASE = c75956336df03a1fd661a054b33b0c4845d4f159

CONCURRENT_MAIN_AUDIT = PASS
CONCURRENT_MAIN_COMMITS_AFTER_006A_BASE = 0
LOCAL_DOCUMENTATION_COMMITS_RECONCILED = 3
CONFLICTS = NONE
RECONCILIATION = CLEAN_REPLAY_PRESERVING_APPEND_ONLY_HISTORY

G2_AUTHORITY_PRESERVED = YES
G2_ENTRYPOINT_PRESERVED = YES
G2_ENTRYPOINT = topicpilot-provider-preflight --run-date YYYY-MM-DD --reference-version tw-reference-v1
G2_EXECUTION_CLASS = READ_ONLY
DATABASE_ACCESS_CLASS = SELECT_ONLY

TPE_PROVIDER_AUTHORITY = TWSE_OFFICIAL_DAILY
TPE_ADAPTER_VERSION = twse-official-daily.v2
TWO_PROVIDER_AUTHORITY = TPEX_OFFICIAL_DAILY
TWO_ADAPTER_VERSION = tpex-official-daily.v2
MARKET_BATCH = true
FALLBACK_CAN_PASS_G2 = NO
PRODUCTION_WRITE_SET = []
NON_REFERENCE_WRITE_SET = []

TOPICPILOT_LIVE_BEHAVIOR_CHANGED = NO
TOPICPILOT_LIVE_DRY_RUN_BEHAVIOR_CHANGED = NO
TOPICPILOT_PROVIDER_LINEAGE_CHANGED = NO
TOPICPILOT_REFERENCE_CHECK_BEHAVIOR_CHANGED = NO
MIGRATION_CHANGED = NO
OPENAPI_CHANGED = NO

CLI_PACKAGING = PASS
G2_PRODUCTION_EXECUTED = NO
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
G1_REFERENCE_ACTIVE = YES
G1_REFERENCE_LOAD_STATUS = READY
G1_MARKET_COUNT = 2
G1_INSTRUMENT_COUNT = 507
G1_PRESERVED = YES
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO

INTEGRATED_MAIN_SHA = PENDING_RELEASE_COMMIT
NON_FORCE_PUSH = PENDING_RELEASE
LOCAL_MAIN_SHA = PENDING_RELEASE_COMMIT
ORIGIN_MAIN_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
EXACT_SHA_CI_RUN = PENDING_RELEASE_COMMIT
EXACT_SHA_CI = PENDING
DEPLOY_WORKFLOW_RUN = PENDING_OPERATOR_RELEASE_HANDOFF
DEPLOY_TRIGGER = PENDING_OPERATOR_RELEASE_HANDOFF
RUNTIME_GIT_COMMIT = OPERATOR_EVIDENCE_REQUIRED_AFTER_DEPLOY
PROVIDER_LINEAGE_BUILD_SHA = OPERATOR_EVIDENCE_REQUIRED_AFTER_DEPLOY
RUNTIME_SHA_VERIFIED = OPERATOR_EVIDENCE_REQUIRED_AFTER_DEPLOY

AI_WORKLOG_UPDATED = YES
REPORT_CREATED = YES
PUSH = PENDING_RELEASE
DEPLOY = PENDING_RELEASE_HANDOFF

FINAL_STATUS = READY_FOR_G2_PRODUCTION_PREFLIGHT_AUTHORIZATION
BLOCKER = NONE
```

## Reconciliation authority

The current fetched `origin/main` was `c75956336df03a1fd661a054b33b0c4845d4f159`.
It is an ancestor of the 006A base, so there were no concurrent main commits
after the 006A base to audit. The three local append-only documentation commits
between that runtime authority and 006A were replayed in order, followed by
006A. No application-path conflict occurred, and no historical report was
rewritten. The resulting worktree is a dedicated 006B reconciliation branch.

The integrated application change is limited to the 006A G2 capability:
the provider preflight core and CLI, the public market-level adapter methods,
the CLI registration, focused/PostgreSQL boundary tests, and the runbook/report
documentation. The official provider mapping, market-batch requirement,
runtime-derived identity coverage, explicit target-date validation, empty write
sets, and no-live-persistence boundary are unchanged from 006A.

The existing live collector, live dry-run, provider lineage, reference-check,
provider registry composition, post-close path, migrations, OpenAPI contract,
and generated API client are not refactored by 006B.

## Release validation

The integrated worktree passed the repository-equivalent validation before the
non-force release push:

- G2 focused/provider tests and PostgreSQL read-only boundary test;
- reference bootstrap PostgreSQL test;
- backend suite excluding only the repository's research/governance markers;
- Ruff, Python compile, pip check, migration upgrade/downgrade/upgrade;
- OpenAPI gate and generated-contract idempotence;
- API client tests;
- frontend lint/test/build;
- Docker Compose smoke;
- diff check and changed-file secret scan.

Recorded local results on the integrated worktree:

```text
FOCUSED_TESTS = 24 passed / 1 skipped
PROVIDER_TESTS = included in focused suite; pass
POSTGRESQL_READ_ONLY_BOUNDARY = 1 passed
REFERENCE_TESTS = 1 passed
BACKEND_TESTS = 322 passed / 49 skipped / 59 deselected
RUFF = PASS
PYTHON_COMPILE = PASS
PIP_CHECK = PASS
MIGRATION_UPGRADE_ROLLBACK = PASS
OPENAPI_GATE = PASS
GENERATED_CONTRACT_IDEMPOTENCE = PASS
API_CLIENT_TESTS = 3 passed
FRONTEND = lint PASS (one existing warning) / 110 tests passed / build PASS
DOCKER_COMPOSE_SMOKE = PASS (isolated PostgreSQL/API/Web)
DIFF_CHECK = PASS
SECRET_SCAN = PASS (no secret values)
CLI_PACKAGING = PASS (--help; mutation flags rejected)
```

The release commit SHA, exact-SHA CI run, and protected deploy workflow run are
recorded in the final local reconciliation update after the release workflow
completes. Documentation added after the release handoff is not pushed, so it
cannot silently change the application/runtime SHA under review.

## Production boundary

006B prepares the release only. It does not run
`topicpilot-provider-preflight`, `topicpilot-live`, reference bootstrap,
activation, market/calendar remediation, G3, Canary, or Scheduler. After the
protected deploy handoff, the operator must verify `RENDER_GIT_COMMIT` and
`topicpilot-provider-lineage.buildSha` in the same authenticated runtime before
running the dedicated read-only G2 preflight under a separate authorization.
