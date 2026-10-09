# Code changes and regression

## Integrated changes

The current canonical main contains three forensic-only PRs:

- PR #80, CI run 37842457222: initial fixed Topics read-model diagnostic.
- PR #82, CI run 37844835907: resilience when migration metadata privilege is missing.
- PR #83, CI run 37845935578: final nested-savepoint isolation; CI run 37845935578 passed.

PR links:

- https://github.com/Xiezhou0828/topicpilot-platform/pull/80
- https://github.com/Xiezhou0828/topicpilot-platform/pull/82
- https://github.com/Xiezhou0828/topicpilot-platform/pull/83

Forensic readback run:

https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/37846564207

## Validation

- Focused forensic tests: 18 passed.
- Ruff: passed.
- compileall: passed.
- diff/allowlist checks: passed.
- Required CI for each merged PR: passed, including backend/migration/OpenAPI, frontend, secret scan, and Docker Compose.
- Production migration/read-model compatibility: not passed because the approved forensic role lacks SELECT; no migration was run.
- Non-Production market-staged E2E: not run in Production and not represented as a pass.

CI_RESULT=PASS
REGRESSION_STATUS=PASS for the diagnostic changes
## Owner-assisted root-cause candidate

After the Render traceback identified the concrete response-contract defect, the isolated Task 007 worktree added:

- `services/api/src/topicpilot_api/production_read_model.py`: serialize persisted `snapshot_date` to ISO text before assigning `ownerSeededV0.asOfDate`;
- `services/api/tests/test_topic_read_model_strength_contract.py`: validate the public `TopicOwnerSeededV0Read` contract for a PostgreSQL `date` input.

No migration, frontend, scheduler, publication writer, authority, or Production data was changed.

Validation evidence:

- focused candidate + Strength read-model tests: 10 passed;
- full API regression from repository root: 1,392 passed, 79 PostgreSQL/environment-gated tests skipped, 0 failed;
- Ruff: passed;
- compileall: passed;
- `git diff --check`: passed.

The first full run from `services/api` produced six path/environment failures; rerunning from repository root removed the five fixture-path failures and the final full run passed. The remaining PostgreSQL-gated tests were skipped because no authorized non-Production `TEST_DATABASE_URL` was available.

REGRESSION_STATUS=PASS for isolated candidate and full API regression; PostgreSQL gates remain blocked
PRODUCTION_BUSINESS_FIX=ISOLATED_CANDIDATE_NOT_DEPLOYED

The pass is intentionally scoped. It does not certify the live Topics API or scheduler readiness.
