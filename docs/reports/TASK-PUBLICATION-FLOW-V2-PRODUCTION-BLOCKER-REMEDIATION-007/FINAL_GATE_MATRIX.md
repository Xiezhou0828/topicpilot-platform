# Final gate matrix

| Gate | Status | Evidence |
|---|---|---|
| CANONICAL_IDENTITY | PASS | origin/main fc11856... |
| API_RUNTIME_IDENTITY | PASS | Render live API 9703c956... |
| WORKER_RUNTIME_IDENTITY | PASS | Render live Worker 9703c956... |
| WORKER_CANONICAL_MATCH | FAIL | live revision differs from fc11856... |
| DATABASE_SCHEMA_INVARIANTS | BLOCKED | current forensic role cannot read alembic_version/core tables |
| DATABASE_RECOVERY_READINESS | BLOCKED | backup/PITR/restore proof unavailable |
| TOPICS_API_ROOT_CAUSE | PASS | Render traceback confirms date-to-string response contract defect |
| TOPICS_API_DEPENDENCY_STATUS | BLOCKED | live API remains HTTP 500 until Owner-approved candidate release |
| TOPICS_API_REMEDIATION_CANDIDATE | PASS_NOT_DEPLOYED | isolated isoformat boundary fix and contract test validated |
| PROVIDER_WAIT_CLASSIFICATION | BLOCKED | provider/product/freshness cause not exposed |
| PUBLICATION_RESULT_SEMANTICS | PASS | PR #79 and Task 006 contract |
| DURABLE_RECEIPT_READINESS | PASS | Task 006 receipt/checkpoint evidence |
| SINGLE_FORMAL_PUBLISHER | PARTIAL | no conflict found, but live writer path remains blocked |
| MARKET_CALENDAR | PASS | official TWSE and TPEx 2026 calendars |
| MARKET_STAGE_SCHEDULE | PASS | source schedule and observed scheduled events |
| CHECKPOINT_AND_RETRY_SAFETY | PASS | existing V2 contract/tests |
| EMERGENCY_DISABLEMENT_READY | PARTIAL | provider rollback visible; scheduler disable/readback not fully evidenced |

CANONICAL_GATES=BLOCKED
POSTGRESQL_GATES=BLOCKED
REGRESSION_STATUS=PASS
PRODUCTION_ROOT_CAUSE=CONFIRMED_TOPICS_RESPONSE_VALIDATION
PRODUCTION_FIX_DEPLOYED=NO
SCHEDULER_ACTIVATION_READINESS=BLOCKED
FINAL_STATUS=PRODUCTION_RUNTIME_BLOCKED

The matrix deliberately does not downgrade a required gate to obtain READY status. Root-cause confirmation and local candidate validation do not close the Production release, Worker transaction, PostgreSQL compatibility, or recovery gates.
