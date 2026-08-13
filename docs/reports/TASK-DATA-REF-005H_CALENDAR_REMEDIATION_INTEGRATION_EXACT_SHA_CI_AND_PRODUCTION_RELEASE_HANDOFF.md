# TASK-DATA-REF-005H Calendar Remediation Integration, Exact-SHA CI, and Production Release Handoff

## Outcome

The authoritative TASK-DATA-REF-005G implementation commit
`a009953c2c9270b6c9ffbaef11ab4fe435cd0242` was reconciled onto the then-current
`origin/main=71ba1ac27f2f72378df3df9266271de4f05f27d1` in a fresh worktree. It was
non-force pushed as application release SHA
`00b40762a9484d951d4cfe776b40557c64fb08fb`.

Exact-SHA CI run `31678008530` passed Secret scan, Frontend, Backend/PostgreSQL,
reference integration, migration rollback/upgrade, OpenAPI/generated contract,
and Docker Compose smoke. Protected deploy workflow run `31678267907` validated
that exact revision and successfully triggered only the Render API deploy hook;
Sites packaging was skipped.

Production operator evidence subsequently reported runtime SHA
`32f15f3c57240151bc5d35761e88c764448fa1cc`, not the authorized application
release SHA. Provider-lineage `buildSha` matched the observed runtime SHA and
reported READY, but exact release/runtime equality failed. The final status is
therefore `BLOCKED_RUNTIME_SHA_DRIFT`. No Production apply, bootstrap,
activation, G1/G2/G3, Canary, or Scheduler action is authorized or executed.

## Reconciliation and local validation

The 005G commit contained only the dedicated market-calendar remediation,
bootstrap dry-run/activation parity fix, shared market-context validator,
tests, runbooks, formal report, and append-only worklog. It did not modify
`NEXT_TASK` or Data Governance HOLD.

The integrated contract remains:

```text
REMEDIATION_ENTRYPOINT = topicpilot-market-calendar-remediation
REMEDIATION_WRITE_SET = markets.calendar_code
NON_CALENDAR_CONTEXT_WRITE_SET = NONE
CALENDAR_EXPECTATION_BUNDLE_DERIVED = YES
TRANSACTIONAL = YES
IDEMPOTENT = YES
SECOND_APPLY = NOOP
ROLLBACK_ON_FAILURE = PASS
MARKET_PK/CODE/IDENTITY_FIELDS_PRESERVED = YES
INSTRUMENT_FINGERPRINT_PRESERVED = YES
DRY_RUN_ACTIVATION_PARITY_FIELDS = code, name, exchange_code, timezone, calendar_code
```

Disposable PostgreSQL validation reproduced the 005F fixture: canonical TPE/TWO
identity, `Asia/Taipei`, NULL calendar, 507 compatible instruments, and empty
registry state. Bootstrap dry-run blocked on the calendar conflict before
mutation; calendar remediation dry-run/apply/NOOP succeeded; subsequent
bootstrap activation and reference check reached READY at 2/507, TPE 314 and
TWO 193.

Local gates passed: scoped reference/remediation PostgreSQL tests `27/27`,
frontend `104/104`, API client `3/3`, Ruff, migrations, OpenAPI drift,
generated-contract idempotence, AST compile, pip check, diff check, and targeted
secret scan. The full Windows backend run reached 340 passed, 20 skipped, and
59 deselected, with only the known unrelated schema-qualified PostgreSQL
`regclass` assertion failure. GitHub's Linux exact-SHA backend job passed.

## Production read-only evidence

The operator ran all commands in one authenticated Render Production shell.
The precheck and postcheck were identical:

```text
MARKET_COUNT = 2
INSTRUMENT_COUNT = 0
DUPLICATE_IDENTITIES = []
MISSING_MARKETS = []
MISSING_INSTRUMENTS = PRESENT
REFERENCE_ACTIVE = NO
REFERENCE_LOAD_STATUS = NOT_READY
REGISTRY_SET_COUNT = 0
REQUIRED_CONTEXT_COUNT = 0
TRADING_STATUS_CATALOGUE_COUNT = 0
REFERENCE_CALENDAR_DATE_COUNT = 0
```

Calendar remediation dry-run returned `PLAN` / `VALIDATED`, `dryRun=true`,
`transactional=true`, 507 compatible existing instruments, and exact planned
changes TPE/TWO from NULL to bundle-derived `TW_MARKET`. Its write set was only
`markets.calendar_code`; `nonCalendarContextWriteSet=[]` and
`instrumentWrites=[]`; all preservation flags were true.

Reference bootstrap dry-run then returned `BLOCKED` with
`bundle/database conflict in market TPE calendar`. This proves the 005G
dry-run/activation parity behavior is present in the observed runtime. The
unchanged postcheck proves both dry-runs caused no database state change.

## Runtime drift audit

Repository audit proved observed runtime SHA
`32f15f3c57240151bc5d35761e88c764448fa1cc` is a descendant of application
release SHA `00b40762a9484d951d4cfe776b40557c64fb08fb`. The intervening commits
changed only Today frontend files/tests and append-only `docs/AI_WORKLOG.md`;
they did not change reference bootstrap, calendar remediation, bundle,
migrations, or CLI paths. Exact-SHA CI run `31680613603` for the observed
runtime SHA passed.

This evidence is sufficient to show no DATA-REF code drift, but TASK-DATA-REF-005H
requires runtime SHA equality with its integrated release SHA. It does not
authorize silently replacing release authority with a concurrent descendant.
The task therefore stops at runtime drift pending explicit authority to adopt
the observed descendant or a new exact-SHA redeploy.

## Fixed status

```text
TASK_DATA_REF_005H = BLOCKED_RUNTIME_SHA_DRIFT
AUTHORITATIVE_005G_COMMIT = a009953c2c9270b6c9ffbaef11ab4fe435cd0242
005G_COMMIT_VERIFIED = YES
STARTING_ORIGIN_MAIN_SHA = 71ba1ac27f2f72378df3df9266271de4f05f27d1
RECONCILIATION_BRANCH = codex/task-data-ref-005h-20260813
CONCURRENT_MAIN_COMMITS_PRESERVED = YES
AI_WORKLOG_APPEND_PRESERVED = YES

MAIN_INTEGRATION = PASS
INTEGRATED_MAIN_SHA = 00b40762a9484d951d4cfe776b40557c64fb08fb
NON_FORCE_PUSH = PASS
EXACT_SHA_CI_RUN = 31678008530
EXACT_SHA_CI = PASS
DEPLOY_WORKFLOW_RUN = 31678267907
DEPLOY = PASS (protected Render API hook triggered; Sites skipped)

RUNTIME_GIT_COMMIT = 32f15f3c57240151bc5d35761e88c764448fa1cc
PROVIDER_LINEAGE_BUILD_SHA = 32f15f3c57240151bc5d35761e88c764448fa1cc
RUNTIME_SHA_VERIFIED = NO

PRODUCTION_CALENDAR_DRY_RUN = PLAN / VALIDATED
PRODUCTION_CALENDAR_PLANNED_WRITE_SET = markets.calendar_code
PRODUCTION_BOOTSTRAP_DRY_RUN = BLOCKED / calendar conflict
PRODUCTION_BOOTSTRAP_DRY_RUN_CALENDAR_CONFLICT_DETECTED = YES
PRODUCTION_DB_CONNECTED = YES (operator dry-run and SELECT-only checks)
PRODUCTION_MUTATION = NO
PRODUCTION_CALENDAR_REMEDIATION_EXECUTED = NO
PRODUCTION_REFERENCE_BOOTSTRAP_RETRY = NO

G1/G2/G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
FINAL_STATUS = BLOCKED_RUNTIME_SHA_DRIFT
BLOCKER = runtime 32f15f3c... does not equal authorized release 00b40762...
```
