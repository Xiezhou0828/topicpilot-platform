# Test and Regression Report

- Frontend build: `PASS`.
- Frontend unit/contract suite: `218 passed, 0 failed`.
- TypeScript `npx tsc --noEmit`: `PASS`.
- Backend Company Research / Financial / EPS focused suite: `46 passed, 0 failed`.
- Ruff on integrated backend source/tests: `PASS`.
- OpenAPI drift/read-only route check: `PASS`.
- Secret policy scan: `PASS` (`4` approved source digests, `18` regression cases).
- Two-gate test: `PASS` (Development permits dirty; Delivery blocks dirty).
- Existing governance test: `PASS` (clean/dirty/delivery states).
- Local API HTTP readback: `PASS` with Research `NOT_CONNECTED` fail-closed state.
- Preview browser readback: `PASS_FAIL_CLOSED`.
- Generated client: `NO_CHANGE_REQUIRED`; no generated API files were overwritten.
- Production write verification: `PASS_NO_PRODUCTION_WRITE`.

`OVERALL_VALIDATION=PASS`
