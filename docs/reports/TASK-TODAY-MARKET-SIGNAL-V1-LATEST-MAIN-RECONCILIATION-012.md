# TASK-TODAY-MARKET-SIGNAL-V1-LATEST-MAIN-RECONCILIATION-012

## Reconciliation scope

This report records the semantic reconciliation of the Today Market Signal V1
candidate with the latest fetched `origin/main` before PR creation.

```text
LATEST_MAIN_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be
PRE_RECONCILIATION_HEAD=89e3aa7e54dbd292127e222988531e5d09cf2912
ORIGINAL_IMPLEMENTATION_BASE=ec46db023c8e701044e162dcf723f362002b88d7
IMPLEMENTATION_COMMIT=65eb36553849ccaa4d9fc5ae85ab04b7a25f5d08
REPORT_FINALIZATION_COMMIT=89e3aa7e54dbd292127e222988531e5d09cf2912
```

The latest mainline A10 post-close/live reconciliation is retained, including
official TWSE/TPEx flow persistence, Home market-facts-only publication
semantics, durable checkpoint/readback behavior, terminal success criteria,
the CI workflow, and the secret-scan policy. No second source or replacement
table was introduced.

The frozen 16-signal Market Signal V1 evaluator, catalog, contract, additive
Home schema/OpenAPI fields, backend tests, frontend rendering/pagination, and
implementation report are retained on top of that mainline. The apparent
signal-file deletions in the latest mainline diff were absence from the
pre-candidate base rather than a semantic change to the shared A10 Today/Home
authority; the shared files had no conflicting latest-main edits.

## Local validation after reconciliation

| Check | Result |
| --- | --- |
| Focused backend reconciliation suite | PASS; 51 passed |
| Broader backend suite | PASS; 734 passed, 4 skipped, 146 deselected |
| Changed-scope Ruff | PASS; 5 changed Python files |
| Frontend full test suite | PASS; 181 passed |
| Frontend signal/commercial static tests | PASS; 5 passed |
| Generated API client tests | PASS; 4 passed |
| Frontend production build | PASS |
| Frontend lint | PASS; one pre-existing `FavoriteButton.tsx` hook warning, no errors |
| OpenAPI drift | PASS |
| Alembic migration graph | PASS; 47 revisions, 1 head |
| Secret-scan policy | PASS |
| Diff/whitespace check | PASS |

The repository-wide Ruff command still reports unrelated pre-existing debt in
research modules; the required changed-scope Ruff gate passes and no unrelated
files were modified to mask that debt.

## Boundary and promotion status

```text
SEMANTIC_RECONCILIATION=PASS
A10_POST_CLOSE_LIVE_SEMANTICS_PRESERVED=YES
MARKET_SIGNAL_V1_RETAINED=YES
MIGRATION_REQUIRED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
PRODUCTION_MUTATED=NO
DEPLOYED=NO
PR_STATUS=PENDING
CI_STATUS=PENDING
MERGE_STATUS=PENDING
```

The unrelated pre-existing untracked report
`docs/reports/TASK-GOV-COMPLETED-CANDIDATE-REMOTE-PRESERVATION-001.md` was
preserved and is intentionally excluded from the reconciliation commit.
