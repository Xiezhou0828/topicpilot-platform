# TASK-DATA-REF-005I Runtime Authority Provenance Audit and Rebind Decision

## Decision

TASK-DATA-REF-005I Gate 1 failed because the operator observed runtime SHA
`c75956336df03a1fd661a054b33b0c4845d4f159`, while the previously authorized
runtime authority was `32f15f3c57240151bc5d35761e88c764448fa1cc`.

The read-only provenance audit passes. `c75956336df03a1fd661a054b33b0c4845d4f159`
is a descendant of `32f15f3c57240151bc5d35761e88c764448fa1cc`.

The authority rebind decision is prepared as:

```text
RUNTIME_AUTHORITY_REBIND_DECISION = READY_FOR_EXPLICIT_APPROVAL
ORIGINAL_RUNTIME_AUTHORITY_SHA = 32f15f3c57240151bc5d35761e88c764448fa1cc
OBSERVED_RUNTIME_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
PROVENANCE_CLEAN = YES
005I_BEHAVIORAL_EQUIVALENCE = YES
PRODUCTION_MUTATION = NO
```

This document prepares the rebind decision; it does not silently change the
005I authority, authorize calendar apply, authorize reference bootstrap or
activation, or waive the runtime freeze. Explicit approval is still required
before treating c759 as the 005I runtime authority.

## Provenance evidence

```text
MERGE_BASE = 32f15f3c57240151bc5d35761e88c764448fa1cc
DESCENDANT_RELATIONSHIP = PASS
ANCESTOR_CHECK = PASS
CURRENT_ORIGIN_MAIN = c75956336df03a1fd661a054b33b0c4845d4f159
```

Intervening commits:

```text
768ff5ccf46fe7b5465a769a0d1c62d27f309717 docs(reference): record 005H runtime drift stop
c75956336df03a1fd661a054b33b0c4845d4f159 docs(reference): rebind verified runtime authority
```

Intervening changed files:

```text
docs/AI_WORKLOG.md
docs/reports/TASK-DATA-REF-005H_CALENDAR_REMEDIATION_INTEGRATION_EXACT_SHA_CI_AND_PRODUCTION_RELEASE_HANDOFF.md
```

The complete range contains only 290 lines of documentation additions. No
application, migration, bundle, generated contract, test, or runtime source
file changed.

## DATA-REF/runtime path audit

```text
DATA_REF_PATH_CHANGED = NO
REFERENCE_DATA_BUNDLE_CHANGED = NO
REFERENCE_RUNTIME_PATH_CHANGED = NO
REFERENCE_CHECK_PATH_CHANGED = NO
REFERENCE_BOOTSTRAP_PATH_CHANGED = NO
MARKET_IDENTITY_REMEDIATION_PATH_CHANGED = NO
MARKET_CALENDAR_REMEDIATION_PATH_CHANGED = NO
PROVIDER_AUTHORITY_PATH_CHANGED = NO
DATA_REF_TEST_CONTRACT_PATH_CHANGED = NO
MIGRATION_PATH_CHANGED = NO
```

Therefore c759 is documentation-only relative to 005I and is behaviorally
equivalent for the calendar remediation, bootstrap parity, provider lineage,
reference-check, and G1 precondition paths. This equivalence is based on exact
zero diff in those paths, not on a count or an assumption.

## Exact-SHA CI

```text
EXACT_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
CI_RUN = 31694695626
CI_RESULT = PASS
```

All required jobs passed:

```text
Backend, migration, and OpenAPI = PASS
Frontend install, test, and build = PASS
Secret scan = PASS
Docker Compose smoke = PASS
```

## Production boundary

The operator stopped immediately at Gate 1. No subsequent command was run.

```text
RUNTIME_SHA_VERIFIED = NO (against the old authority; rebind decision pending)
CALENDAR_APPLY = NOT_RUN
REFERENCE_BOOTSTRAP = NOT_RUN
REFERENCE_ACTIVATION = NOT_RUN
G1 = NOT_RUN
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PRODUCTION_MUTATION = NO
```

No credentials were requested or exposed. No manual SQL, retry, deploy,
bootstrap, activation, or Production mutation was performed by this audit.

## Fixed status

```text
FINAL_STATUS = READY_FOR_EXPLICIT_RUNTIME_AUTHORITY_REBIND_APPROVAL
BLOCKER = explicit approval to rebind 005I authority from 32f15f3c... to c7595633...
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
PUSH = NO
DEPLOY = NO
```
