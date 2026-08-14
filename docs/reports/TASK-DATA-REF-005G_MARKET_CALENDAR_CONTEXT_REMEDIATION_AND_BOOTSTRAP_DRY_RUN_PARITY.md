# TASK-DATA-REF-005G Market Calendar Context Remediation and Bootstrap Dry-Run Parity

## Outcome

A dedicated bundle-derived `topicpilot-market-calendar-remediation` command now
plans or atomically repairs only `markets.calendar_code`. The reference bootstrap
dry-run now applies the same shared market-context validator as activation, so
the TASK-DATA-REF-005F `calendar_code=NULL` conflict is visible before an
authorized mutation.

Work was performed on isolated branch `codex/task-data-ref-005g-20260813` from
`origin/main=71ba1ac27f2f72378df3df9266271de4f05f27d1`. No Production database was
connected, no Production remediation/bootstrap was retried, and nothing was
deployed, pushed, or merged.

## Authority and root cause

`markets.calendar_code` is a nullable `VARCHAR(64)` in ORM and migration 0014,
with no foreign key and no database default. The canonical bundle explicitly
sets both TPE and TWO to `TW_MARKET`; its calendar dataset and reference-session
catalogue use the same code. Reference preflight consumes each market calendar
to establish required context. The legacy importer creates market rows without
assigning `calendar_code`, while the later live bootstrap assigns `TW_MARKET`.

The evidence therefore classifies the Production NULL values as
`LEGACY_IMPORTER_CONTEXT_OMISSION / HISTORICAL_DATA_DRIFT`. This is row-state
remediation, not a schema defect, so no migration is required.

## Safety contract

The new command validates exactly two active bundle markets, canonical name,
exchange code and timezone, an empty reference registry, and the complete
bundle-derived instrument identity and metadata set. The observed 507 total is
derived from the bundle and fixture, not hardcoded. NULL calendar values may
move only to each bundle record's target. Any conflicting non-null value,
unexpected market, incompatible instrument, or context drift blocks before
mutation.

The declared write set is only `markets.calendar_code`; non-calendar context and
instrument write sets are empty. Apply owns one transaction and verifies the
full instrument snapshot plus immutable market fields before commit. Failure
rolls back both updates. A canonical rerun is `NOOP`.

Bootstrap plan and activation now call `validate_market_context` for market code,
name, exchange code, timezone, and calendar code. The disposable 005F fixture
therefore blocks at bootstrap dry-run before any reference row exists.

## Disposable PostgreSQL 16 evidence

A fresh database was migrated through revision 0028 and seeded with canonical
TPE/TWO identity, `Asia/Taipei`, NULL calendars, 507 bundle-compatible inactive
instruments, and empty reference tables. The sequence proved:

```text
PRE_REMEDIATION_BOOTSTRAP_DRY_RUN = BLOCKED (market TPE calendar)
REFERENCE_TABLE_COUNTS_AFTER_BLOCK = all zero
CALENDAR_REMEDIATION_DRY_RUN = PLAN / VALIDATED; zero mutation
CALENDAR_REMEDIATION_APPLY = APPLIED / CANONICAL
SECOND_APPLY = NOOP
POST_REMEDIATION_BOOTSTRAP_DRY_RUN = PLAN
POST_REMEDIATION_BOOTSTRAP = ACTIVATED / ACTIVE
POST_BOOTSTRAP_MARKET_COUNT = 2
POST_BOOTSTRAP_INSTRUMENT_COUNT = 507
POST_BOOTSTRAP_TPE_COUNT = 314
POST_BOOTSTRAP_TWO_COUNT = 193
POST_BOOTSTRAP_REFERENCE_ACTIVE = YES
POST_BOOTSTRAP_REFERENCE_LOAD_STATUS = READY
MISSING_MARKETS / MISSING_INSTRUMENTS / DUPLICATE_IDENTITIES = []
```

Negative PostgreSQL coverage rejects conflicting non-null calendar, timezone,
name, and unexpected market topology without mutation. An injected postcondition
failure proves transaction rollback. Existing market-identity and reference
bootstrap regression suites pass.

## Validation

```text
TARGETED_POSTGRESQL_AND_CONTRACT_TESTS = PASS (9 passed)
REFERENCE_AND_MARKET_IDENTITY_REGRESSION = PASS (27 passed total)
RUFF = PASS
MIGRATION_DOWNGRADE_0028_TO_0027 = PASS
MIGRATION_UPGRADE_TO_HEAD_0028 = PASS
OPENAPI_GATE = PASS
GENERATED_CONTRACT_IDEMPOTENCE = PASS
API_CLIENT_TESTS = PASS (3 passed)
AST_COMPILE = PASS
PIP_CHECK = PASS
DIFF_CHECK = PASS
SECRET_SCAN = PASS (targeted staged scan; gitleaks unavailable locally)
```

The CI-equivalent backend run reached 340 passed, 20 skipped, and 59 deselected.
Its sole failure is the existing Windows/PostgreSQL `regclass` qualification
assertion in `test_canonical_observation_postgres.py`: PostgreSQL returns
schema-qualified trigger table names while the test expects unqualified names.
This failure is outside the changed reference/remediation paths. The new isolated
PostgreSQL tests skip during the full suite once unrelated tests have populated
the intentionally empty database; they passed separately against the same fresh
migration head.

`npm audit` continues to report two pre-existing high-severity advisories. This
task changes no package or lockfile. OpenAPI and generated clients are unchanged.

## Delivery boundary

```text
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
PRODUCTION_CALENDAR_REMEDIATION_EXECUTED = NO
PRODUCTION_REFERENCE_BOOTSTRAP_RETRY = NO
G1/G2/G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
FINAL_STATUS = READY_FOR_MARKET_CALENDAR_REMEDIATION_INTEGRATION_REVIEW
```
