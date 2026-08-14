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

## Production execution closure

The implementation was released and verified by the operator in the same
authenticated Production runtime. The application runtime authority is kept
separate from any later local documentation change:

```text
TASK_DATA_REF_008 = CLOSED
STARTING_ORIGIN_MAIN_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
IMPLEMENTATION_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
INTEGRATED_MAIN_SHA = NOT_MERGED; exact-ref release deployed from task branch
APPLICATION_RUNTIME_AUTHORITY_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
DOCUMENTATION_SHA = NONE_CREATED_AFTER_DEPLOYMENT
RUNTIME_GIT_COMMIT = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
PROVIDER_LINEAGE_BUILD_SHA = b9c881af0fa34d29e9ac0ccdf123351741e7f62d
RUNTIME_SHA_VERIFIED = YES

G0 = PASS (preserved prior evidence; not rerun)
G1 = PASS (preserved prior evidence; not rerun)
G2 = PASS (preserved prior evidence; not rerun)
G3_ENTRYPOINT = topicpilot-market-semantics-check
G3_EXECUTION_CLASS = READ_ONLY
G3_RUN_DATE = 2026-08-13
G3_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
G3 = PASS

TPE_PROVIDER = TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION = twse-official-daily.v2
TPE_DATA_DATE = 2026-08-13
TPE_EXPECTED_ELIGIBLE_COUNT = 313
TPE_SEMANTIC_ELIGIBLE_COUNT = 313
TPE_MISSING_EXPECTED_IDENTITIES = 0
TPE_OUT_OF_SCOPE_PROVIDER_IDENTITIES = 1065 (diagnostic-only)

TWO_PROVIDER = TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION = tpex-official-daily.v2
TWO_DATA_DATE = 2026-08-13
TWO_EXPECTED_ELIGIBLE_COUNT = 193
TWO_SEMANTIC_ELIGIBLE_COUNT = 193
TWO_MISSING_EXPECTED_IDENTITIES = 0
TWO_OUT_OF_SCOPE_PROVIDER_IDENTITIES = 10281 (diagnostic-only)

FALLBACK_USED = false
TARGET_DATE_MATCHED = YES
PRODUCTION_DB_ACCESS = YES (read-only)
PRODUCTION_WRITE_SET = []
PRODUCTION_MUTATION = NO
PHYSICAL_6806_ROW_PRESERVED = YES
CANARY = NOT_RUN
SCHEDULER_CHANGED = NO

EXACT_SHA_CI_RUN = 31770418256
EXACT_SHA_CI = PASS
DEPLOY_RUN = 31770585896
DEPLOY = PASS
PUSH = NON_FORCE_TASK_BRANCH_ONLY
MAIN_PUSH = NO
AI_WORKLOG_UPDATED = YES (local append-only)
REPORT_UPDATED = YES (local closure append)
BLOCKER = NONE
FINAL_STATUS = READY_FOR_POST_CLOSE_CANARY
```

The Production G3 output had `readOnly=true`, `fallbackUsed=false`, an empty
`failureReasons` list, and `productionWriteSet=[]`. Both official market
payloads matched the authorized date and covered every date-effective expected
identity. The additional provider identities were retained only as diagnostic
counts and did not affect the PASS decision.

No Canary, Scheduler, post-close writer, `topicpilot-live`, or other
Production mutation was authorized or executed. The deployed application
runtime authority remains `b9c881af0fa34d29e9ac0ccdf123351741e7f62d`; this
closure update was kept local and did not create or push a new documentation
release.
