# TASK-DATA-REF-008 | G3 Market Semantics Validation Contract & Executable Gate

## Scope

This task adds the missing executable G3 gate after the already-preserved G0,
G1, and G2 checkpoints. It does not redo reference bootstrap, registry
transition, lifecycle remediation, provider-preflight contract work, or the
6806 root-cause investigation.

## Contract implemented

The new `topicpilot-market-semantics-check` command is deterministic,
machine-readable, fail-closed, and read-only. It validates:

1. authorized run date and canonical market session;
2. date-effective lifecycle-aware expected `EQUITY` identities;
3. official provider authority, adapter version, market identity, and data date;
4. missing expected identities, duplicate expected identities, and malformed
   lifecycle evidence; and
5. the policy that out-of-scope provider identities are diagnostic-only.

The command does not write database rows, observations, snapshots, lifecycle
results, Opportunity state, registry state, or scheduler state.

## 6806 regression

The existing reference lifecycle evidence is used without modification:

```text
TPE:6806 / 2026-06-22 = ELIGIBLE
TPE:6806 / 2026-06-23 = NOT_ELIGIBLE
TPE:6806 / 2026-08-13 = NOT_ELIGIBLE
PHYSICAL_6806_ROW_PRESERVED = YES
```

An ineligible physical identity is excluded from the date-effective expected
universe; its absence from the provider payload is therefore not a G3 failure.

## Implementation and validation

```text
G3_CONTRACT_CREATED = YES
G3_ENTRYPOINT = topicpilot-market-semantics-check
G3_EXECUTION_CLASS = READ_ONLY
MIGRATION_CHANGED = NO
OPENAPI_CHANGED = NO
PRODUCTION_WRITE_SET = []
```

Focused G3, lifecycle, and G2 regression tests passed. The CI-equivalent
backend relevant suite passed with PostgreSQL-dependent fixtures skipped when
no test database URL was configured. The dedicated PostgreSQL integration test
uses a disposable database, injects deterministic official-provider fixtures,
and asserts every schema table count is unchanged by the G3 run.

## Production boundary

Production execution is separately operator-gated. Before running the command,
the operator must verify the deployed runtime SHA and provider-lineage build
SHA are identical to the application release SHA and must preserve G0/G1/G2
evidence. A G3 PASS only establishes:

```text
READY_FOR_POST_CLOSE_CANARY
```

It does not authorize the post-close writer, Canary, or Scheduler. A missing
runtime match, reference/session inconsistency, provider/date mismatch,
fallback, lifecycle error, missing expected identity, or non-empty production
write set is a fail-closed stop.

## Fixed report fields

```text
TASK_DATA_REF_008 = IMPLEMENTED_PENDING_RELEASE
G0_CHECKPOINT = PRESERVED
G1_CHECKPOINT = PRESERVED
G2_CHECKPOINT = PRESERVED
AUTHORIZED_RUN_DATE = 2026-08-13
G3_CONTRACT_CREATED = YES
G3_ENTRYPOINT = topicpilot-market-semantics-check
G3_EXECUTION_CLASS = READ_ONLY
PHYSICAL_6806_ROW_PRESERVED = YES
OUT_OF_SCOPE_PROVIDER_IDENTITIES = DIAGNOSTIC_ONLY
PRODUCTION_WRITE_SET = []
PRODUCTION_MUTATION = NO
CANARY = NOT_RUN
SCHEDULER_CHANGED = NO
BLOCKER = Awaiting exact-SHA integration/deploy and operator G3 evidence.
FINAL_STATUS = READY_FOR_EXACT_SHA_CI_AND_PRODUCTION_G3_REVIEW
```
