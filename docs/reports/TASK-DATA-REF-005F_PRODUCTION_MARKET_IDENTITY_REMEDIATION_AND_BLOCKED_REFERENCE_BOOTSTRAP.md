# TASK-DATA-REF-005F Production Market Identity Remediation and Blocked Reference Bootstrap

## Outcome

The one-shot Production market identity remediation completed successfully.
The subsequent reference bootstrap activation failed closed because both
Production market rows have a null calendar code while the canonical bundle
requires `TW_MARKET`. The bootstrap transaction rolled back completely and no
reference set became active. Execution stopped before G1/G2/G3/Canary or
Scheduler.

```text
TASK_DATA_REF_005F = YES
FINAL_RELEASE_SHA = 6d611cb7d5db589c375e27cb3e2abfef91e512e2
RUNTIME_GIT_COMMIT = 6d611cb7d5db589c375e27cb3e2abfef91e512e2
PROVIDER_LINEAGE_BUILD_SHA = 6d611cb7d5db589c375e27cb3e2abfef91e512e2
RUNTIME_SHA_VERIFIED = YES
RUNTIME_CHANGED_DURING_EXECUTION = NO
G0 = PASS
```

The release SHA is the explicitly accepted docs-only descendant of the 005E
application release. Exact-SHA CI run `31673484828` passed. No product,
DATA-REF, migration, or configuration file differs from the previously
verified application runtime.

## Pre-mutation gates

```text
PRECHECK_MARKET_COUNT = 2
PRECHECK_DATABASE_TOTAL_INSTRUMENT_ROWS = 507
PRECHECK_REFERENCE_VALID_INSTRUMENT_COUNT = 0
PRECHECK_REFERENCE_ACTIVE = NO
PRECHECK_REFERENCE_LOAD_STATUS = NOT_READY
PRECHECK_DUPLICATE_IDENTITIES = []
PRECHECK_MISSING_MARKETS = []
PRECHECK_MISSING_INSTRUMENTS = PRESENT

BUNDLE_VERSION = tw-reference-v1
BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
BUNDLE_HASH_MATCH = PASS

REMEDIATION_DRY_RUN = PASS
DRY_RUN_STATUS = VALIDATED
DRY_RUN_OPERATION = PLAN
SEMANTIC_COMPATIBILITY = CANONICAL_BUNDLE_COMPATIBLE
DRY_RUN_MUTATION = NO
DRY_RUN_DB_STATE_CHANGED = NO
PLANNED_WRITE_SET = markets.exchange_code, markets.name
PLANNED_INSTRUMENT_WRITES = NONE
PLANNED_NON_MARKET_IDENTITY_WRITE_SET = NONE
```

## Production market remediation

The authorized command used the dedicated remediation entrypoint with
`--apply`. It returned `operation=APPLIED`, `status=CANONICAL`,
`transactional=true`, and an empty non-market identity write set.

```text
PRODUCTION_REMEDIATION_EXECUTED = YES
REMEDIATION_APPLY_RESULT = APPLIED / CANONICAL

TPE_BEFORE = Taiwan Stock Exchange / TPE
TPE_AFTER = TWSE Listed / TWSE
TWO_BEFORE = Taipei Exchange / TWO
TWO_AFTER = TPEx OTC / TPEx

TPE_ID = 72380af3-52e9-4967-b6dc-14173ef4c688
TWO_ID = 4794d00b-7485-4177-b2bb-57446325a9d4
MARKET_PK_PRESERVED = YES
MARKET_CODE_PRESERVED = YES
INSTRUMENT_ROWS_CHANGED = 0
INSTRUMENT_COUNT_BEFORE = 507
INSTRUMENT_COUNT_AFTER = 507
INSTRUMENT_FINGERPRINT_BEFORE = daddec45ba36b3571e5d07171a7a7bd8
INSTRUMENT_FINGERPRINT_AFTER = daddec45ba36b3571e5d07171a7a7bd8
NON_MARKET_IDENTITY_WRITE_SET = NONE
REMEDIATION_POSTCHECK = PASS
```

The immediate reference check remained inactive/`NOT_READY`, as required
before bootstrap. A second remediation dry-run returned `NOOP` / `CANONICAL`
with no changes, proving idempotent canonical market state.

## Reference bootstrap attempt

The reference bootstrap dry-run returned the reviewed hash and:

```text
REFERENCE_BOOTSTRAP_ENTRYPOINT = topicpilot-reference-bootstrap --activate
REFERENCE_BOOTSTRAP_DRY_RUN = PLAN / VALIDATED
DRY_RUN_CREATED_MARKETS = 0
DRY_RUN_CREATED_INSTRUMENTS = 0
DRY_RUN_CREATED_REFERENCE_ROWS = 37
DRY_RUN_NON_REFERENCE_WRITE_SET = []
DRY_RUN_TRANSACTIONAL = true
DRY_RUN_IDEMPOTENT = true
```

The one-shot activation was then attempted and returned:

```text
REFERENCE_BOOTSTRAP_EXECUTED = ATTEMPTED
REFERENCE_BOOTSTRAP_RESULT = BLOCKED
REFERENCE_BOOTSTRAP_ERROR = bundle/database conflict in market TPE calendar
REFERENCE_ACTIVATED = NO
ACTIVATION_AFTER_VALIDATION = NO
```

Code evidence locates the fail-closed comparison in
`reference_data/bootstrap.py::_ensure_market`: bundle `calendar_code` is
compared exactly with the existing `markets.calendar_code`. The canonical
bundle requires `TW_MARKET` for both TPE and TWO. Production diagnostics found:

```text
TPE_TIMEZONE = Asia/Taipei
TPE_CALENDAR_CODE = NULL
TWO_TIMEZONE = Asia/Taipei
TWO_CALENDAR_CODE = NULL
EXPECTED_TPE_CALENDAR_CODE = TW_MARKET
EXPECTED_TWO_CALENDAR_CODE = TW_MARKET
```

The planner gap is also explicit: dry-run `_plan` counts existing market codes
and identity keys but does not invoke `_ensure_market`, so it did not surface
the calendar mismatch before activation. No code correction is authorized in
this execution task.

## Transaction rollback evidence

After the blocked activation, SELECT-only evidence showed:

```text
POST_REMEDIATION_MARKET_COUNT = 2
POST_REMEDIATION_DATABASE_TOTAL_INSTRUMENT_ROWS = 507
POST_REMEDIATION_REFERENCE_ACTIVE = NO
POST_REMEDIATION_REFERENCE_LOAD_STATUS = NOT_READY

reference_registry_sets = 0
reference_currencies = 0
reference_timezones = 0
reference_sessions = 0
reference_trading_statuses = 0
reference_adjustments = 0
reference_calendar_dates = 0

PARTIAL_REFERENCE_SET_ACTIVE = NO
REFERENCE_BOOTSTRAP_TRANSACTION_ROLLED_BACK = YES
POST_BOOTSTRAP_MARKET_COUNT = NOT_REACHED
POST_BOOTSTRAP_INSTRUMENT_COUNT = NOT_REACHED
G1 = NOT_REACHED
```

The successful market remediation remains committed and canonical. No reverse
update, second apply, bootstrap retry, manual SQL, migration rollback, or
automatic recovery was attempted.

## Scope and final status

```text
REFERENCE_BOOTSTRAP_WRITE_SET_COMMITTED = NONE
PRODUCT_CODE_CHANGED = NO
MIGRATION_CHANGED = NO
CONFIG_CHANGED = NO

PRODUCTION_DB_CONNECTED = YES
PRODUCTION_MUTATION = YES (market name/exchange remediation only)

G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO

FINAL_STATUS = MARKET_REMEDIATION_COMPLETE_REFERENCE_BOOTSTRAP_BLOCKED
BLOCKER = TPE and TWO markets.calendar_code are NULL; bundle requires TW_MARKET
```

STOP. A separately scoped review is required to design and validate the
Production market-calendar context remediation and to make bootstrap dry-run
exercise the same fail-closed context preconditions as activation. This report
does not authorize that fix, redeployment, or another Production bootstrap.
