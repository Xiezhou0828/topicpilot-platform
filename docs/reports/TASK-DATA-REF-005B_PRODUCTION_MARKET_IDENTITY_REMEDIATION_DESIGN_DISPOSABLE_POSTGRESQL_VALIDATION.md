# TASK-DATA-REF-005B Production Market Identity Remediation Design and Disposable PostgreSQL Validation

## Final status

`READY_FOR_ONE_SHOT_PRODUCTION_MARKET_IDENTITY_REMEDIATION_AUTHORIZATION`

This status means that the remediation design, implementation, rollback
boundary, and disposable PostgreSQL validation are complete. It is not a
Production authorization and does not authorize TASK-DATA-REF-005C until that
task is separately approved.

## Fixed authority and safety boundary

```text
TASK_DATA_REF_005B = YES
RELEASE_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
RUNTIME_SHA_VERIFIED = YES (prior operator evidence)
G0 = PASS (prior operator evidence)
REFERENCE_VERSION = tw-reference-v1
BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
BUNDLE_HASH_MATCH = PASS
PRODUCTION_BUNDLE_DRIFT = NO
STARTING_WORKTREE_COMMIT = af45356a0d55b789426865d63831188ba0267de1
BRANCH = codex/task-data-ref-005b-20260813
```

No Production connection, SELECT, mutation, bootstrap retry, remediation,
migration, seed, deploy, G2/G3, Canary, or Scheduler action was performed by
TASK-DATA-REF-005B. The prior Production blocked activation remains the only
Production activation attempt:

```json
{"status":"BLOCKED","error":"bundle/database conflict in market TPE name"}
```

The supplied Production post-failure evidence remains `MARKET_COUNT=2`,
`INSTRUMENT_COUNT=0`, `REFERENCE_ACTIVE=NO`,
`REFERENCE_LOAD_STATUS=NOT_READY`, `BOOTSTRAP_MUTATION_OCCURRED=NO`,
`ROLLBACK_REQUIRED=NO`, and `PARTIAL_STATE_LEFT=NO`.

## Canonical dataset and authority

The canonical bundle is committed under:

`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/`

It is `GENERATED_WITH_CURATED_GOVERNANCE_INPUTS`. The approved instrument
source is the V1 TSV export (`539` logical rows, `507` accepted identities),
while calendar, adjustment, status, market, currency, timezone, and session
inputs are governed by the bundle manifest and evidence artifacts. The bundle
manifest derives:

| Field | Value |
| --- | --- |
| Markets | `TPE`, `TWO` |
| Instruments | `507` (`TPE=314`, `TWO=193`) |
| Currency | `TWD` |
| Timezone | `Asia/Taipei` |
| Session | `REGULAR` |
| Calendar | `TW_MARKET`, 23 holidays + 1 suspended date |
| Trading statuses | 7 |
| Adjustments | 3 |

Canonical market metadata is:

| Internal code | Canonical name | Canonical exchange code |
| --- | --- | --- |
| `TPE` | `TWSE Listed` | `TWSE` |
| `TWO` | `TPEx OTC` | `TPEx` |

The Production rows audited by TASK-DATA-REF-005A are legacy conflict
evidence, not an authority override:

| Internal code | Observed name | Observed exchange code |
| --- | --- | --- |
| `TPE` | `Taiwan Stock Exchange` | `TPE` |
| `TWO` | `Taipei Exchange` | `TWO` |

Historical seed provenance is not conclusively persisted in the market rows;
the classification remains `LEGACY_CONVENTION_MATCH / EXACT_SEED_PATH_NOT_PROVEN`
and `ROOT_CAUSE_CLASS=PRODUCTION_LEGACY_NAME_DRIFT`.

## Market field semantic matrix

| Field | Semantic role | Can change? | FK/provider/API impact | Decision |
| --- | --- | --- | --- | --- |
| `market.code` | Stable TopicPilot internal market identity | No | Used by identity joins, provider routing, reference checks, API filters, importers, and projections | Preserve exactly; never re-key |
| `market.name` | Canonical/display metadata | Yes, governed in place | API and human-facing projections; name changes are presentation-contract risk | Reconcile only from the approved bundle |
| `market.exchange_code` | Exchange identity metadata | Yes, governed in place | Provider/exchange semantics and API/domain responses; change is high-risk | Reconcile only from the approved bundle |

The remediation preserves both primary keys and internal codes. It does not
delete/reinsert rows and does not alter foreign-key targets.

## Dependency and blast-radius audit

The repository audit covered the ORM/model/schema, reference bundle and
loader, live identity defaults, provider routing, API market responses,
frontend generated contract, legacy importer, migrations, CLI paths, tests,
and operations documentation. The meaningful dependency groups are:

```text
market.code       -> stable identity, instrument composite identity, provider
                     routing, reference-check, API filters, importer paths,
                     frontend/domain projections, tests
market.name       -> API/display metadata and documentation-facing projections
market.exchange_code -> exchange/provider metadata and API/domain semantics
markets.id        -> instrument.market_id and downstream foreign keys
```

The selected change is therefore limited to existing market metadata columns;
it does not modify instruments, observations, timeline, canonical daily data,
topics, relations, Lifecycle, Opportunity, audit rows, or provider config.

## Strategy comparison and decision

| Option | Result | Decision |
| --- | --- | --- |
| A. Update existing rows in place | Preserves PKs/codes/FKs; narrow write set; requires exact governance | Mechanism used by the selected design |
| B. Add aliases/reconciliation to generic bootstrap | Broadens bootstrap semantics and weakens the current fail-closed contract | Rejected for this incident |
| C. Dedicated one-shot remediation command | Exact precondition, dry-run, atomic update, postcondition, and auditable output | Recommended and implemented |
| D. Delete/reinsert or re-key | Risks FK breakage, identity replacement, audit gaps, and non-idempotency | Rejected |

`MIGRATION_REQUIRED=NO`: no schema change is needed. This is a governed data
remediation over existing columns, not a migration or generic repair tool.

## Remediation contract

The dedicated entrypoint is:

```console
topicpilot-market-identity-remediation \
  --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --dry-run
```

Exactly one of `--dry-run` or `--apply` is required. The command validates the
approved bundle and fails closed unless the database has exactly two active
markets with codes `TPE` and `TWO`. The legacy-to-canonical apply path also
requires:

```text
TPE = Taiwan Stock Exchange / TPE
TWO = Taipei Exchange / TWO
instrument count = 0
reference registry-set count = 0
```

Any third market, inactive expected market, duplicate/unexpected code, mixed
state, unexpected name/exchange code, instrument state, or reference registry
state returns `BLOCKED` before a market update. A completely canonical state
returns `NOOP`.

```text
WRITE_SET = markets.name, markets.exchange_code
NON_MARKET_IDENTITY_WRITE_SET = NONE
PRIMARY_KEYS = PRESERVED
MARKET_CODES = PRESERVED
```

`--dry-run` is a read-only plan. `--apply` requires a fresh SQLAlchemy
session, owns one transaction, updates only the two existing rows in place,
flushes, verifies canonical values and unchanged instrument/registry counts,
and commits only after postconditions pass. Any exception rolls back both
market metadata updates. The source contains no delete/insert/re-key or
non-reference write path.

## Disposable PostgreSQL validation

Validation used an explicitly named disposable PostgreSQL 16 container and
port `55433`, with migrations applied to `0028_task_data_ref_001_reference_bootstrap`.
The test fixture seeds only the two exact legacy market rows and cleans its
own rows after each test.

```text
DATABASE_CLASS = DISPOSABLE / ISOLATED
POSTGRES_VERSION = 16-alpine
LEGACY_CONFLICT_REPRODUCED = YES (Production evidence and repository conflict coverage)
LEGACY_CONFLICT_RESULT = BLOCKED at TPE name
LEGACY_PARTIAL_STATE_LEFT = NO
```

The dedicated remediation plus existing reference PostgreSQL integration
suite completed:

```text
7 passed (fresh disposable PostgreSQL run)
```

The coverage includes:

- dry-run plan with zero mutation;
- in-place apply with both PKs and codes preserved;
- canonical dry-run and apply rerun as `NOOP`;
- mixed name/exchange state blocked without mutation;
- unexpected market shape blocked without mutation;
- unexpected instrument state blocked without mutation;
- non-empty reference registry state blocked without mutation;
- injected postcondition failure rolling both metadata changes back;
- reference bootstrap integration and conflict rollback coverage.

Post-remediation isolated reference validation passed:

```text
POST_REMEDIATION_REFERENCE_DRY_RUN = PASS
POST_REMEDIATION_REFERENCE_ACTIVATION_ISOLATED = PASS
REFERENCE_ACTIVE_ISOLATED = YES
REFERENCE_LOAD_STATUS_ISOLATED = READY
MARKET_COUNT_ISOLATED = 2
INSTRUMENT_COUNT_ISOLATED = 507
TPE_COUNT_ISOLATED = 314
TWO_COUNT_ISOLATED = 193
MISSING_MARKETS = 0
MISSING_INSTRUMENTS = 0
DUPLICATE_IDENTITIES = 0
MISSING_REFERENCE_CONTEXTS = 0
```

Migration downgrade from `0028` to `0027` and re-upgrade to head passed on
the same disposable PostgreSQL instance.

## Regression and contract gates

```text
RUFF = PASS (repository API/infra scope and modified files)
REMEDIATION_POSTGRES_TESTS = PASS (7)
REFERENCE_POSTGRES_INTEGRATION = PASS
MIGRATION_UPGRADE = PASS
MIGRATION_ROLLBACK = PASS
OPENAPI_GATE = PASS
GENERATED_CONTRACT = PASS / idempotent / no diff
API_CLIENT_TESTS = PASS (2)
AST_PARSE = PASS
PIP_CHECK = PASS
DIFF_CHECK = PASS
SECRET_SCAN = PASS (targeted pattern scan; gitleaks not installed locally)
FRONTEND_CONTRACT_CHANGED = NO
```

The correct root-level backend run completed `336 passed`, `8 skipped`, and
reported two unrelated pre-existing/environmental failures: the canonical
append-only trigger assertion compares qualified PostgreSQL `regclass` names
to unqualified names, and the observation migration test's migration command
does not use the test database URL. Neither failure imports or touches the
remediation path. The task-scoped gates above and the fresh dedicated
PostgreSQL suite passed.

Validation hygiene note: an early local harness invocation incorrectly set
`TEST_DATABASE_URL` for Alembic even though this repository's migration
configuration reads `MIGRATION_DATABASE_URL`; it advanced the existing local
non-Production database from migrations `0024` through `0028`. No Production
database or credential was accessed, and all subsequent migration and test
validation used the explicit disposable port `55433`. This report does not
silently omit that harness incident.

## Documentation and delivery boundary

```text
AI_WORKLOG_UPDATED = YES (append-only)
FORMAL_REPORT_CREATED_OR_UPDATED = YES
RUNBOOK_UPDATED = YES
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
PRODUCTION_REMEDIATION_EXECUTED = NO
PRODUCTION_BOOTSTRAP_RETRY = NO
G1 = NOT_REACHED
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
```

The isolated branch contains only the dedicated remediation implementation,
tests, runbook, worklog, and this report. The next authorized operational step
is a separately reviewed TASK-DATA-REF-005C one-shot Production remediation;
this task stops here.
