# TASK-DATA-REF-005D Market Identity Remediation Existing-Instrument Safety Contract Fix

## Outcome

`topicpilot-market-identity-remediation` no longer requires the raw
`topicpilot.instruments` row count to be zero. It now allows an empty table or
an existing instrument set that is semantically compatible with the validated
`tw-reference-v1` bundle. The expected set is derived from the bundle; 507 is
test evidence, not a hardcoded business rule.

This task used an isolated branch/worktree and did not connect to or mutate
Production. No Production remediation retry, reference bootstrap, deployment,
push, merge, G1/G2/G3, Canary, or Scheduler action was performed.

## Root cause and corrected contract

The Production evidence was internally consistent but measured two different
states:

- `topicpilot-reference-check` counts active canonical EQUITY identities that
  satisfy its reference/context joins. It therefore reported 0 while the
  reference registry was absent/inactive.
- the old remediation precondition used an unfiltered `COUNT(*)` over
  `topicpilot.instruments`. It therefore observed all 507 existing rows and
  blocked with `expected=0 actual=507`.

The corrected remediation inspects every existing instrument joined through
`instruments.market_id` to `markets.id`, then compares its
`(market.code, instrument_code)` identity and canonical `name`,
`instrument_type`, and `currency` against the validated bundle. It rejects
orphan, missing, extra, duplicate, reassigned, and metadata-conflicting rows.
It accepts an empty set or an exact bundle-compatible set. Row count alone
cannot authorize remediation.

## Identity and write safety

```text
MARKET_PK_COLUMN = markets.id
MARKET_CODE_COLUMN = markets.code
INSTRUMENT_MARKET_FK_COLUMN = instruments.market_id
WRITE_SET = markets.name, markets.exchange_code
NON_MARKET_IDENTITY_WRITE_SET = NONE
MARKET_PK_PRESERVED = YES
MARKET_CODE_PRESERVED = YES
INSTRUMENT_ROWS_PRESERVED = YES (full before/after snapshot)
TRANSACTIONAL = YES
ROLLBACK_ON_FAILURE = YES
IDEMPOTENT = YES (second apply is NOOP)
```

The apply path still owns one SQLAlchemy transaction. It changes only the two
market metadata fields, verifies canonical postconditions, compares the full
instrument snapshot, verifies the registry count, and commits only after all
checks pass. Exceptions roll back both market changes.

## Disposable PostgreSQL 16 evidence

A fresh isolated PostgreSQL 16 database was migrated to head and populated
with two legacy market rows and all 507 bundle-derived instruments as
inactive. This reproduces the Production metric split without copying or
accessing Production data:

```text
REFERENCE_CHECK_BASELINE_MARKET_COUNT = 2
REFERENCE_CHECK_BASELINE_INSTRUMENT_COUNT = 0
REFERENCE_CHECK_BASELINE_LOAD_STATUS = NOT_READY
REMEDIATION_EXISTING_INSTRUMENT_COUNT = 507
REMEDIATION_INSTRUMENT_COMPATIBILITY = CANONICAL_BUNDLE_COMPATIBLE
REMEDIATION_DRY_RUN = PLAN / VALIDATED
DRY_RUN_MUTATION = NO
REMEDIATION_APPLY_DISPOSABLE = PASS
INSTRUMENT_ROWS_CHANGED_BY_REMEDIATION = 0
SECOND_APPLY = NOOP
REFERENCE_BOOTSTRAP_AFTER_REMEDIATION = ACTIVATED
REFERENCE_LOAD_STATUS_AFTER_BOOTSTRAP = READY
MARKET_COUNT_AFTER_BOOTSTRAP = 2
INSTRUMENT_COUNT_AFTER_BOOTSTRAP = 507
TPE_COUNT_AFTER_BOOTSTRAP = 314
TWO_COUNT_AFTER_BOOTSTRAP = 193
```

Negative coverage proves that a missing row, wrong market assignment, or
canonical metadata conflict blocks before any market mutation. Existing
coverage also rejects a third market, mixed market state, unexpected identity
shape, and non-empty registry state, and proves rollback under an injected
postcondition failure. Database uniqueness and foreign-key constraints remain
the first line of defense against duplicate identities and orphan market
references; the remediation performs explicit duplicate/orphan checks as a
fail-closed defense.

## Validation

```text
RUFF = PASS
REMEDIATION_AND_REFERENCE_POSTGRES_TESTS = PASS (11 passed)
CONTRACT_UNIT_TESTS = PASS (7 passed)
MIGRATION_DOWNGRADE_0028_TO_0027 = PASS
MIGRATION_UPGRADE_TO_HEAD_0028 = PASS
OPENAPI_GATE = PASS
GENERATED_CONTRACT_IDEMPOTENCE = PASS
API_CLIENT_TESTS = PASS (3 passed)
AST_COMPILE = PASS
PIP_CHECK = PASS
DIFF_CHECK = PASS
```

The CI-equivalent backend run completed `337 passed`, `14 skipped`, and
`59 deselected`, with one unrelated pre-existing Windows/PostgreSQL assertion
failure in the canonical-observation trigger test: PostgreSQL returned
schema-qualified `regclass` names while the assertion expects unqualified
names. The remediation and reference suites passed on the same disposable
database.

`npm audit` reported two existing high-severity advisories; this task made no
package or lockfile changes. The generated API contract remained unchanged.

## Delivery boundary

```text
STARTING_ORIGIN_MAIN_SHA = 8a818935fe63eb3c3db9592c5068363c7ec941e9
ISOLATED_BRANCH = codex/task-data-ref-005d-20260813
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
PRODUCTION_REMEDIATION_RETRY = NO
REFERENCE_BOOTSTRAP_EXECUTED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
G1_PRODUCTION = NOT_RECHECKED
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
FINAL_STATUS = READY_FOR_REMEDIATION_PRECONDITION_INTEGRATION_REVIEW
```

Actual Production semantic compatibility is intentionally not inferred from
the count 507. It must be proven by a future exact-SHA Production dry-run only
after separate integration, deployment, and operator authorization.
