# TASK-DATA-REF-005E Remediation Semantic Precondition Release and Production Dry-Run Reverification

## Outcome

The DATA-REF-005D existing-instrument semantic safety correction is integrated,
validated by exact-SHA CI, deployed, and verified in the authenticated
Production runtime. Production dry-run passed without mutation. This task does
not authorize or execute remediation apply or reference bootstrap.

```text
TASK_DATA_REF_005E = YES
005D_PROVENANCE_COMMIT = 47c0c2d09bc0c5796a97fa1f81b4b6c1df28a7ad
INITIAL_INTEGRATION_SHA = 564c9d8e739e7485c4f76b8e058034e5742b8974
FINAL_RELEASE_SHA = e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77
ZERO_INSTRUMENT_PRECONDITION_CORRECTED = YES
ROW_COUNT_ONLY_GATE = NO
MAGIC_507_GATE = NO
SEMANTIC_COMPATIBILITY_GATE = YES
SEMANTIC_CHECKS_PRESERVED = YES
```

## Reconciliation and release

The initial integration began from `origin/main` at
`8a818935fe63eb3c3db9592c5068363c7ec941e9` and replayed the single 005D
commit without conflict. The semantic contract validates expected TPE/TWO
topology, bundle-derived exact identities, no missing/extra/duplicate/orphan
identity, no unexpected market assignment, and canonical name/type/currency
metadata. It does not use zero or 507 as a row-count authorization gate.

Concurrent Today and Stock commits advanced main after the initial push. The
first Render runtime therefore reported descendant SHA `82419a27...` instead
of initial release SHA `564c9d8...`. Audit of the intervening commits found
only frontend and documentation changes and no DATA-REF drift. The operation
stopped before apply, selected the stable latest main descendant, reran exact
CI authority, and deployed final release SHA
`e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77`.

```text
RECONCILIATION_STRATEGY = latest-main descendant / scoped no-drift audit
CONFLICTS = NONE
005D_FIX_ANCESTOR_OF_FINAL_RELEASE = YES
DATA_REF_DRIFT = NO
INITIAL_EXACT_SHA_CI_RUN = 31668931779 / PASS
FINAL_EXACT_SHA_CI_RUN = 31672214158 / PASS
FINAL_DEPLOY_WORKFLOW_RUN = 31673036818 / PASS
SITES_PACKAGE = SKIPPED
```

The final official Linux/PostgreSQL CI passed Frontend install/lint/test/build,
Gitleaks, Ruff, empty-database migration, migration rollback/upgrade,
reference PostgreSQL integration, full release-scoped backend tests, OpenAPI,
generated contract idempotence, API client tests, and Docker Compose smoke.
This provides release authority over the unrelated Windows-only qualified
`regclass` assertion observed during local validation; that test was not
modified, disabled, or skipped in CI.

## Runtime and G0

Authenticated Render Shell evidence confirmed:

```text
RUNTIME_GIT_COMMIT = e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77
PROVIDER_LINEAGE_BUILD_SHA = e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77
RUNTIME_SHA_VERIFIED = YES
PROVIDER_LINEAGE_STATUS = READY
TWSE_ADAPTER = twse-official-daily.v2
TPEX_ADAPTER = tpex-official-daily.v2
MARKET_BATCH = true
TPE_AUTHORITY = TWSE_OFFICIAL_DAILY
TWO_AUTHORITY = TPEX_OFFICIAL_DAILY
YAHOO_CHART_ROLE = VERIFICATION_ONLY
YAHOO_QUOTE_ROLE = INTRADAY_VERIFICATION_ONLY
TAISHIN_ROLE = INTRADAY_ONLY
G0 = PASS
```

Public `/healthz` and `/readyz` remained `ok` and `ready` across rollout. These
public probes were availability evidence only; Shell SHA and lineage are the
runtime authority.

## Production baseline and semantic dry-run

The SELECT-only reference check immediately before dry-run reported:

```text
PRECHECK_MARKET_COUNT = 2
REFERENCE_VALID_INSTRUMENT_COUNT = 0
DATABASE_TOTAL_INSTRUMENT_ROWS = 507
DUPLICATE_IDENTITIES = []
MISSING_MARKETS = []
MISSING_INSTRUMENTS = PRESENT
PRECHECK_REFERENCE_ACTIVE = NO
PRECHECK_REFERENCE_LOAD_STATUS = NOT_READY
REGISTRY_SET_COUNT = 0
REQUIRED_CONTEXT_COUNT = 0
TRADING_STATUS_CATALOGUE_COUNT = 0
```

The 0 and 507 values intentionally describe different metrics: reference-check
counts active canonical identities with required reference state, while the
remediation inspects all existing instrument rows and validates them against
the committed bundle.

The exact Production command was dry-run only. Its result was:

```text
REMEDIATION_DRY_RUN = PASS
DRY_RUN_STATUS = VALIDATED
DRY_RUN_OPERATION = PLAN
DRY_RUN = true
TRANSACTIONAL = true
IDEMPOTENT = true
EXISTING_INSTRUMENT_COUNT = 507
SEMANTIC_COMPATIBILITY = CANONICAL_BUNDLE_COMPATIBLE
MARKET_COUNT = 2
REFERENCE_REGISTRY_COUNT = 0
MARKET_PRIMARY_KEYS_PRESERVED = true
MARKET_CODES_PRESERVED = true
```

Planned metadata changes were exact:

```text
PLANNED_TPE_CHANGE = Taiwan Stock Exchange / TPE -> TWSE Listed / TWSE
PLANNED_TWO_CHANGE = Taipei Exchange / TWO -> TPEx OTC / TPEx
PLANNED_WRITE_SET = markets.exchange_code, markets.name
PLANNED_INSTRUMENT_WRITES = NONE
PLANNED_NON_MARKET_IDENTITY_WRITE_SET = NONE
MARKET_PK_CHANGE_PLANNED = NO
MARKET_CODE_CHANGE_PLANNED = NO
```

The immediate post-dry-run reference check remained 2 markets, 0 valid
reference instruments, no duplicates/missing markets, reference inactive, and
`NOT_READY`. The database state therefore retained the approved pre-bootstrap
baseline. Earlier same-database diagnostics also recorded 507 total instrument
rows and an unchanged instrument fingerprint across dry-run; the final
exact-SHA run independently returned the same 507 bundle-compatible rows.

```text
DRY_RUN_MUTATION = NO
DRY_RUN_DB_STATE_CHANGED = NO
PRODUCTION_DB_CONNECTED = YES (operator SELECT/dry-run only)
PRODUCTION_MUTATION = NO
PRODUCTION_REMEDIATION_EXECUTED = NO
PRODUCTION_REFERENCE_BOOTSTRAP_RETRIED = NO
```

## Stop boundary

```text
G1 = NOT_REACHED_AFTER_BOOTSTRAP
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
FINAL_STATUS = READY_FOR_ONE_SHOT_PRODUCTION_MARKET_IDENTITY_REMEDIATION_AUTHORIZATION
BLOCKER = NONE
```

STOP. A separate TASK-DATA-REF-005F authorization is required before any
Production `--apply`. Reference bootstrap remains a separately ordered action
after successful market remediation and its postcheck.
