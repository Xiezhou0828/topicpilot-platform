# Validation evidence

Run from the isolated E worktree on 2026-09-16.

| Check | Result |
| --- | --- |
| FUND-A parser/trend/API tests | PASS: 10 focused tests; 21 tests when combined with existing Home publication/status coverage |
| Existing Home publication/status compatibility | PASS in the combined 22-test run |
| API client tests | PASS: 5 |
| Web build and full web test suite | PASS: build complete, 165 tests |
| OpenAPI required-route/schema validation and generation | PASS; generated OpenAPI, API schema, and web declarations synchronized |
| Ruff on changed Python and migration | PASS |
| Python compileall for API source and migration versions | PASS |
| `git diff --check` | PASS |
| Migration structural provenance | PASS: 0041 points to 0040; Alembic CLI itself exited with Windows native code `-1073740022` in the bundled runtime, so no database command is claimed as passed |
| PostgreSQL persistence round trip | NOT RUN: `TEST_DATABASE_URL` and `DATABASE_URL` were unset; no Production database was contacted |
| Official provider discovery | PASS, read-only endpoint/field/unit verification documented separately |

The Web build may emit a normal vinext route-classification notice for dynamic
API usage; it completed successfully. Package installation was limited to the
isolated worktree and no dependency lockfile was changed.
