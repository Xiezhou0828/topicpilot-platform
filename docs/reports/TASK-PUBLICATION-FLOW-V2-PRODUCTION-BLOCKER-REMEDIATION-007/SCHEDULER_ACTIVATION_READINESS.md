# Scheduler activation readiness

The Worker process is visibly running its scheduler poll, but the task did not activate it. Existing runtime events are fail-closed:

- schedulerDate=2026-10-08
- executionMode=SCHEDULED
- first observed reason WAIT_PROVIDER_NOT_READY
- later reason REFERENCE_PREFLIGHT_PendingRollbackError
- status BLOCKED

The current scheduler must not be treated as publication-ready merely because it polls. The API root cause is now known, but the repair is not deployed and the dependency is still HTTP 500; the provider wait cannot be attributed to a provider/product, database recovery is not operationally proven, and the Worker revision does not match current canonical main.

Required before Owner activation approval:

1. deploy and read back the Owner-approved Topics API serialization repair, or formally prove a contract-compliant unavailable response;
2. provide backup/PITR/restore evidence;
3. resolve or explain the reference preflight PendingRollbackError;
4. verify provider-level readiness and freshness predicates;
5. verify the formal writer and receipt path on the exact approved runtime;
6. perform one bounded non-Production market-staged E2E.

SCHEDULER_ACTIVATION_READINESS=BLOCKED
V2_SCHEDULER_ACTIVATED=NO
PRODUCTION_MANUAL_PUBLICATION=NO
PRODUCTION_REPLAY=NO
