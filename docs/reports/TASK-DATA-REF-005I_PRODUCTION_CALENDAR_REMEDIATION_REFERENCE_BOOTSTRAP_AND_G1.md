# TASK-DATA-REF-005I Production Calendar Remediation, Reference Bootstrap Activation, and G1

## Closure decision

TASK-DATA-REF-005I is closed from the supplied Production operator evidence.
The authorized calendar remediation and reference bootstrap completed
transactionally, the canonical postchecks passed, and the runtime SHA did not
change during execution.

The application/runtime authority for this execution is:

```text
APPLICATION_RUNTIME_AUTHORITY_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
RUNTIME_CHANGED_DURING_EXECUTION = NO
PRODUCTION_EXECUTION_FREEZE = ACTIVE
```

Any documentation commit created after this execution is a separate
`DOCUMENTATION_SHA`. It is not an application/runtime authority and is not
being pushed during this closure. No documentation push or deploy is part of
this report.

## Runtime and baseline

The previously audited authority rebind was explicit and the observed
Production runtime remained the verified descendant SHA above. The supplied
execution evidence reports the following baseline and provider state:

```text
RUNTIME_SHA_VERIFIED = YES
G0 = PASS
PRECHECK_MARKET_COUNT = 2
PRECHECK_DATABASE_TOTAL_INSTRUMENT_ROWS = 507
PRECHECK_REFERENCE_ACTIVE = NO
PRECHECK_REFERENCE_LOAD_STATUS = NOT_READY
PRECHECK_DUPLICATE_IDENTITIES = []
PRECHECK_MISSING_MARKETS = []
```

The expected market contexts before remediation were:

```text
TPE = TWSE Listed / TWSE / Asia/Taipei / calendar_code NULL
TWO = TPEx OTC / TPEx / Asia/Taipei / calendar_code NULL
```

## Calendar remediation

The authorized calendar remediation applied only the missing calendar context
for the two existing markets:

```text
CALENDAR_REMEDIATION_APPLY_RESULT = APPLIED / CANONICAL
CALENDAR_APPLY_OPERATION = APPLIED
CALENDAR_APPLY_STATUS = CANONICAL
CALENDAR_APPLY_DRY_RUN = false
CALENDAR_APPLY_TRANSACTIONAL = true
CALENDAR_APPLY_IDEMPOTENT = true
CALENDAR_INSTRUMENT_COUNT = 507
CALENDAR_INSTRUMENT_WRITES = []
CALENDAR_MARKET_PRIMARY_KEYS_PRESERVED = true
CALENDAR_MARKET_CODES_PRESERVED = true
CALENDAR_MARKET_IDENTITY_FIELDS_PRESERVED = true
CALENDAR_NON_CONTEXT_WRITE_SET = []
CALENDAR_WRITE_SET = ["markets.calendar_code"]
```

Applied changes:

```text
TPE: NULL -> TW_MARKET
TWO: NULL -> TW_MARKET
```

The calendar postcheck passed. The database still contained 507 instrument
rows, and the canonical market contexts were:

```text
TPE = TWSE Listed / TWSE / Asia/Taipei / TW_MARKET
TWO = TPEx OTC / TPEx / Asia/Taipei / TW_MARKET
```

A second calendar dry-run returned no changes:

```text
CALENDAR_IDEMPOTENCE = NOOP / CANONICAL
CALENDAR_IDEMPOTENCE_CHANGES = []
CALENDAR_IDEMPOTENCE_DRY_RUN = true
CALENDAR_IDEMPOTENCE_OPERATION = NOOP
CALENDAR_IDEMPOTENCE_STATUS = CANONICAL
CALENDAR_IDEMPOTENCE_TRANSACTIONAL = true
CALENDAR_IDEMPOTENCE_INSTRUMENT_WRITES = []
CALENDAR_IDEMPOTENCE_NON_CONTEXT_WRITE_SET = []
CALENDAR_IDEMPOTENCE_WRITE_SET = ["markets.calendar_code"]
```

## Reference bundle and bootstrap

The canonical bundle and its committed manifest matched the Production
operator evidence:

```text
REFERENCE_VERSION = tw-reference-v1
BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
```

The bootstrap dry-run validated the planned reference write set without
mutating Production:

```text
BOOTSTRAP_DRY_RUN = PLAN / VALIDATED
BOOTSTRAP_DRY_RUN = true
BOOTSTRAP_TRANSACTIONAL = true
BOOTSTRAP_IDEMPOTENT = true
CREATED_MARKETS = 0
CREATED_INSTRUMENTS = 0
CREATED_REFERENCE_ROWS = 37
NOOP_REFERENCE_ROWS = 0
RETIRED_REGISTRY_SETS = 0
BOOTSTRAP_NON_REFERENCE_WRITE_SET = []
```

The subsequent authorized activation completed canonically in one
transaction:

```text
REFERENCE_BOOTSTRAP_RESULT = ACTIVATED / ACTIVE
REFERENCE_BOOTSTRAP_OPERATION = ACTIVATED
REFERENCE_BOOTSTRAP_STATUS = ACTIVE
REFERENCE_BOOTSTRAP_DRY_RUN = false
REFERENCE_BOOTSTRAP_TRANSACTIONAL = YES
REFERENCE_BOOTSTRAP_IDEMPOTENT = true
REFERENCE_BOOTSTRAP_CREATED_MARKETS = 0
REFERENCE_BOOTSTRAP_CREATED_INSTRUMENTS = 0
REFERENCE_BOOTSTRAP_CREATED_REFERENCE_ROWS = 37
REFERENCE_BOOTSTRAP_NOOP_REFERENCE_ROWS = 0
REFERENCE_BOOTSTRAP_RETIRED_REGISTRY_SETS = 0
REFERENCE_BOOTSTRAP_NON_REFERENCE_WRITE_SET = []
```

The bootstrap write set contained only the approved reference and identity
tables. No topics, topic hierarchy, relations, raw/timeline/canonical daily
observations, Lifecycle, or Opportunity writes were reported. The supplied
activation completed without failure, so rollback was not triggered; the
transactional contract remained intact.

## Reference and G1 postchecks

The postcheck reported a complete active reference set:

```text
REFERENCE_ACTIVE = YES
REFERENCE_LOAD_STATUS = READY
MARKET_COUNT = 2
INSTRUMENT_COUNT = 507
DATABASE_TOTAL_INSTRUMENT_ROWS = 507
MISSING_MARKETS = []
MISSING_INSTRUMENTS = []
DUPLICATE_IDENTITIES = []
MISSING_REFERENCE_CONTEXTS = []
REGISTRY_SET_COUNT = 1
REQUIRED_CONTEXT_COUNT = 1
REFERENCE_CALENDAR_DATE_COUNT = 24
TRADING_STATUS_CATALOGUE_COUNT = 7
ADJUSTMENT_CATALOGUE_COUNT = 3
TPE_COUNT = 314
TWO_COUNT = 193
```

The canonical market contexts remained:

```text
TPE = TWSE Listed / TWSE / Asia/Taipei / TW_MARKET
TWO = TPEx OTC / TPEx / Asia/Taipei / TW_MARKET
```

The supplied `topicpilot-reference-check --reference-version tw-reference-v1`
postcheck therefore passed the 005I G1 criteria:

```text
G1 = PASS
```

## Production boundary and follow-up gate

Production mutation did occur in this task, but only through the explicitly
authorized calendar apply and reference activation recorded above. No further
Production action is requested or performed by this closure.

```text
PRODUCTION_DB_CONNECTED = YES (authenticated operator runtime)
PRODUCTION_MUTATION = YES (authorized calendar apply and reference activation)
CALENDAR_APPLY = APPLIED / CANONICAL
REFERENCE_BOOTSTRAP = PASS
REFERENCE_ACTIVATED = YES
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
```

Documentation and release controls:

```text
AI_WORKLOG_UPDATED = YES
FORMAL_REPORT_CREATED = YES
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
PUSH = NO
DEPLOY = NO
DOCUMENTATION_SHA = LOCAL_ONLY_CLOSURE_COMMIT_REPORTED_SEPARATELY
```

## Fixed final status

```text
FINAL_STATUS = READY_FOR_G2_AUTHORIZATION
BLOCKER = NONE
```

This report closes TASK-DATA-REF-005I only. It does not authorize or start
G2, G3, Canary #2, Scheduler changes, or DATA-REF-006.
