# TASK-DATA-REF-009A Runtime Active Reference Binding Fix & Single Post-Close Canary Retry

## Scope and preserved gates

TASK-DATA-REF-009A follows TASK-DATA-REF-009 after the authorized post-close
attempt was stopped before any write by `REFERENCE_CONTEXT_NOT_READY`.
The task does not redesign the reference registry, lifecycle, provider, G2/G3,
Scheduler, or historical backfill paths.

```text
APPLICATION_RELEASE_SHA = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
G0_CHECKPOINT = PASS / PRESERVED
G1_CHECKPOINT = PASS / PRESERVED
G2_CHECKPOINT = PASS / PRESERVED
G3_CHECKPOINT = PASS / PRESERVED
```

## Root-cause confirmation

The deployed live runtime reported:

```text
CURRENT_RUNTIME_REFERENCE_VERSION = tw-reference-v1
CURRENT_ACTIVE_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
ACTIVE_REGISTRY = ACTIVE / READY
ACTIVE_REGISTRY_COUNT = 1
ROOT_CAUSE_CONFIRMED = YES
```

Repository inspection confirms that the existing binding mechanism is the
environment-driven `TOPICPILOT_LIVE_REFERENCE_DATA_VERSION`. Its current
default is `tw-reference-v1` in
`services/api/src/topicpilot_api/live/config.py`; post-close passes that
configured value into the existing SELECT-only
`load_g2_preflight_context()` path. The active registry target was created by
the already completed TASK-DATA-REF-006I transition.

This is a runtime configuration binding mismatch. It is not a reference
dataset conflict, lifecycle corruption, provider-authority change, G2/G3
semantic issue, or persistence-writer defect.

## Minimal binding fix

Reuse the existing environment binding mechanism for the single authorized
run:

```text
ACTIVE_REFERENCE_TARGET = tw-reference-v1-rollover-daf19e9eb051255c
REFERENCE_BINDING_MECHANISM = TOPICPILOT_LIVE_REFERENCE_DATA_VERSION
REFERENCE_SEMANTICS_CHANGED = NO
PROVIDER_SEMANTICS_CHANGED = NO
G2_G3_SEMANTICS_CHANGED = NO
REGISTRY_MUTATION = NO
LIFECYCLE_MUTATION = NO
IDENTITY_MUTATION = NO
```

The temporary operator binding must be verified by the live CLI dry-run before
the one-shot retry. A durable Render service configuration update, if desired,
is a separate operator/configuration action and must not be silently inferred
from this report.

## Production stop evidence inherited from TASK-DATA-REF-009

```text
CANARY_RUN_DATE = 2026-08-13
CANARY_ATTEMPTS_BEFORE_BINDING_FIX = 1
CANARY = BLOCKED_REFERENCE_CONTEXT_NOT_READY
CANARY_PRECONDITION_FAILED_BEFORE_WRITES = YES
PRODUCTION_MARKET_DATA_MUTATION = NO
PRODUCTION_WRITE_SET = []
PROVIDER_REQUESTS = NOT_REACHED
SCHEDULER_CHANGED = NO
```

## Resume gate

After binding, verify the same runtime SHA and provider lineage, and confirm
the dry-run reports the active target version. Only then is one additional
post-close attempt authorized for `2026-08-13`; no second retry is permitted.
The acceptance target remains TPE=313, TWO=193, official TWSE/TPEx v2,
fallback=false, no TPE:6806 observation, and bounded post-close persistence.

```text
REFERENCE_BINDING_FIXED = PENDING OPERATOR RUNTIME VERIFICATION
CANARY_MAX_NEW_ATTEMPTS = 1
FINAL_STATUS = BLOCKED_RUNTIME_REFERENCE_BINDING_PENDING
BLOCKER = Runtime must be bound to the ACTIVE registry target before the
           single post-close Canary retry.
```

## Runtime binding and single Canary result

The operator applied the existing environment binding in the same Render
Shell and verified the deployed runtime before the single retry:

```text
RUNTIME_GIT_COMMIT = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
PROVIDER_LINEAGE_BUILD_SHA = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
RUNTIME_SHA_VERIFIED = YES
RUNTIME_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
REFERENCE_BINDING_FIXED = YES
G0_CHECKPOINT = PASS
G1_CHECKPOINT = PRESERVED PASS
G2_CHECKPOINT = PRESERVED PASS
G3_CHECKPOINT = PRESERVED PASS
```

The one authorized post-close Canary was then executed exactly once for the
approved historical run date:

```text
CANARY_RUN_DATE = 2026-08-13
CANARY_ATTEMPTS = 1 (new attempt after binding fix)
CANARY = PASS / SUCCESS
RUN_ID = c697da38-c093-4362-b4f3-6caea4077119
REQUESTED_COUNT = 506
SUCCESS_COUNT = 506
FAILURE_COUNT = 0
SKIPPED_COUNT = 0
RETRY_COUNT = 0
PROVIDER_POINT_COUNT = 506
TRACKING_COUNT = 506
SNAPSHOT_COUNT = 130
SNAPSHOT_STATUS = SUCCESS
SNAPSHOT_DATE = 2026-08-13
```

The command completed with the active target reference and no provider or
retry failure. This is the authorized bounded Production market-data
mutation; no reference registry, market identity, instrument identity, or
Scheduler mutation was requested. The final acceptance remains pending the
SELECT-only persistence postcheck for market split, 6806 exclusion, duplicate
stable keys, and unchanged reference/identity state.

```text
REFERENCE_DATA_MUTATION = NO
MARKET_IDENTITY_MUTATION = NO
INSTRUMENT_IDENTITY_MUTATION = NO
PRODUCTION_MARKET_DATA_MUTATION = YES (authorized bounded Canary)
SCHEDULER_CHANGED = NO
FINAL_STATUS = READY_FOR_SELECT_ONLY_CANARY_POSTCHECK
BLOCKER = Persistence and non-corruption postcheck pending.
```

## SELECT-only persistence and non-corruption postcheck

The postcheck was executed after the single Canary and emitted only the
closure fields:

```text
RUN_STATUS = SUCCESS
REQUESTED_COUNT = 506
SUCCESS_COUNT = 506
FAILURE_COUNT = 0
RETRY_COUNT = 0

TRADE_DATE = 2026-08-13
RECONCILIATION_STATUS = READY
DOWNSTREAM_READY = true
EXPECTED_COUNT = 506
COVERED_COUNT = 506

TPE_EXPECTED = 313
TPE_OBSERVED = 313
TPE_PRICED = 313
TPE_COVERED = 313
TWO_EXPECTED = 193
TWO_OBSERVED = 193
TWO_PRICED = 193
TWO_COVERED = 193

SNAPSHOT_DATE = 2026-08-13
SNAPSHOT_STATUS = SUCCESS
SNAPSHOT_TOPIC_COUNT = 130

DUPLICATE_STABLE_KEY_GROUPS = 0
PHYSICAL_6806_ROWS = 1
DAILY_6806_ROWS = 0
ACTIVE_REGISTRY_COUNT = 1
```

The postcheck confirms complete date-effective persistence without deleting
the retained TPE:6806 physical identity. No 6806 daily observation was
published for the ineligible date, and no duplicate stable-key group was
detected.

## 009A closure

```text
TASK_DATA_REF_009A = COMPLETE
ROOT_CAUSE_CONFIRMED = YES
REFERENCE_BINDING_FIXED = YES
OLD_RUNTIME_REFERENCE_VERSION = tw-reference-v1
NEW_RUNTIME_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
ACTIVE_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c

APPLICATION_RELEASE_SHA = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
DOCUMENTATION_SHA = NONE; local append-only docs remain uncommitted
RUNTIME_GIT_COMMIT = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
PROVIDER_LINEAGE_BUILD_SHA = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
RUNTIME_SHA_VERIFIED = YES

G0_CHECKPOINT = PASS
G1_CHECKPOINT = PRESERVED PASS
G2_CHECKPOINT = PRESERVED PASS
G3_CHECKPOINT = PRESERVED PASS

CANARY_RUN_DATE = 2026-08-13
CANARY_ATTEMPTS = 1
CANARY = PASS
TPE_EXPECTED = 313
TPE_ACTUAL = 313
TWO_EXPECTED = 193
TWO_ACTUAL = 193
FALLBACK_USED = NO

PERSISTENCE_COMPLETE = YES
PERSISTED_TPE_COUNT = 313
PERSISTED_TWO_COUNT = 193
PERSISTED_TOTAL_COUNT = 506
CANARY_IDEMPOTENCE_VERIFIED = YES (contract, idempotent writer, and zero duplicates; no second Production invocation)
DUPLICATE_OBSERVATIONS = 0

REFERENCE_DATA_MUTATION = NO
MARKET_IDENTITY_MUTATION = NO
INSTRUMENT_IDENTITY_MUTATION = NO
PRODUCTION_MARKET_DATA_MUTATION = YES (authorized bounded Canary)
SCHEDULER_CHANGED = NO

EXACT_SHA_CI = PASS (31771593422)
DEPLOY = PASS (31771782436; API only)
AI_WORKLOG_UPDATED = YES
REPORT_CREATED = YES
NEXT_TASK_MODIFIED = NO

FINAL_STATUS = POST_CLOSE_CANARY_PERSISTENCE_COMPLETE
BLOCKER = NONE
```
The broader TASK-DATA-REF-009 continuation status is
`READY_FOR_FORMAL_DATA_PUBLICATION_AND_FRONTEND_WIRING`. Scheduler enablement,
frontend wiring, and later data tasks remain out of scope.
