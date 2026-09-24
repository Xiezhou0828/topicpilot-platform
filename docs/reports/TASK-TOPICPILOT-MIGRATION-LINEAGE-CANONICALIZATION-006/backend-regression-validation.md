# Backend regression validation

## Migration-focused tests

The same Python 3.12 focused command was run on the d272 baseline and the candidate:

pytest -q tests/test_database_foundation.py tests/test_identity_migration.py tests/test_instrument_topic_relationship_migration.py tests/test_market_data_migration.py

Both results were 7 passed, 1 skipped; the skipped test required PostgreSQL.

MIGRATION_FOCUSED_TEST_STATUS=PASS

## Canonical suite differential

The full suite was run with the repository's src and repository root on PYTHONPATH. The comparison suite excluded only tests/test_canonical_observation_implementation.py, whose test test_canonical_revision_is_linear_after_0018 hard-codes the pre-restoration 0039 head and therefore is intentionally obsolete for this candidate.

| Run | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| d272 baseline | 694 | 15 | 59 |
| candidate | 694 | 15 | 59 |

The same 15 baseline failures were unrelated fixture/governance-artifact failures in corporate-action and WS3 research tests. No candidate-only failure remained after excluding the intentional pre-restoration-head assertion.

- BACKEND_REGRESSION_STATUS=PASS_NO_DIFFERENTIAL_REGRESSION
- BASELINE_FAILURE_COUNT=15
- CANDIDATE_FAILURE_COUNT=15
- NEW_FAILURE_COUNT=0

The unexcluded head assertion fails only on the candidate because the required head correctly changed from 0039 to 0045; it is evidence of the intended migration restoration, not an application-code regression.

## Ruff and import/compile

- Full ruff check src alembic: 751 errors on both baseline and candidate; no new lint debt.
- Ruff on restored 0040–0045 files: All checks passed!
- RUFF_STATUS=PASS_NO_NEW_DEBT
- COMPILE_IMPORT_STATUS=PASS — Python 3.12 compileall and imports of topicpilot_api, topicpilot_api.main, and topicpilot_api.models succeeded.
