# TASK-DATA-REF-004 — Exact-SHA Production Deploy, Runtime Re-Verification & Reference Bootstrap Dry-Run

## Final status

`READY_FOR_ONE_SHOT_PRODUCTION_REFERENCE_BOOTSTRAP_AUTHORIZATION`

The earlier screenshot transcription of the Production dry-run bundle hash
was corrected with a machine-readable extraction from the same Render
Production runtime. The corrected hash exactly matches the committed
canonical bundle manifest at the exact release SHA. This report records
readiness for a separately authorized one-shot Production reference
bootstrap; it does not execute or authorize that mutation itself.

## Scope and safety boundary

This closing review does not execute a new Production command. It does not
activate a reference registry, run G1 after bootstrap, run G2/G3, run Canary
#2, change Scheduler state, modify `NEXT_TASK`, or touch the Data Governance
HOLD.

## Repository and release reconciliation

| Field | Result |
| --- | --- |
| `EXPECTED_SHA` | `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c` |
| `REMOTE_MAIN_SHA` | `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c` |
| Local isolated worktree HEAD | `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c` |
| Protected API deploy workflow | PASS; run `31646749478` |
| API deploy hook | PASS; `deploy_api=true` in `production-api` |
| Same-SHA web validation | PASS; run `31646945930` |
| `PRODUCTION_DB_CONNECTED` | YES, operator evidence only; no local credential use |
| `PRODUCTION_MUTATION` | NO |

The API deploy workflow used the protected `production-api` environment and
the release ref was the exact SHA. The web validation used the same release
SHA without triggering an API deploy. No worker deploy was requested.

## Runtime and G0 operator evidence

The supplied Render Shell evidence reports:

- `RUNTIME_GIT_COMMIT` = `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`.
- `RUNTIME_SHA_VERIFIED` = `YES`.
- `PROVIDER_LINEAGE_BUILD_SHA` = `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`.
- `G0` = `PASS`.
- status = `READY`.
- TWSE = `twse-official-daily.v2`.
- TPEx = `tpex-official-daily.v2`.
- TPE authority = `TWSE_OFFICIAL_DAILY`.
- TWO authority = `TPEX_OFFICIAL_DAILY`.
- canonical daily `marketBatch` = `true`.
- Yahoo chart = `VERIFICATION_ONLY`.
- Yahoo quote = `INTRADAY_VERIFICATION_ONLY`.
- Taishin = `INTRADAY_ONLY`.

## Production precheck and dry-run evidence

The supplied SELECT-only precheck before and after dry-run reports:

| Field | Result |
| --- | --- |
| `PRECHECK_REFERENCE_VERSION` | `tw-reference-v1` |
| `PRECHECK_REFERENCE_ACTIVE` | `NO` |
| `PRECHECK_MARKET_COUNT` | `2` |
| `PRECHECK_INSTRUMENT_COUNT` | `0` |
| `PRECHECK_MISSING_MARKETS` | `[]` |
| `PRECHECK_MISSING_INSTRUMENTS` | `PRESENT` |
| `PRECHECK_DUPLICATE_IDENTITIES` | `[]` |
| `PRECHECK_MISSING_REFERENCE_CONTEXTS` | `[]` |
| `PRECHECK_REFERENCE_LOAD_STATUS` | `NOT_READY` |
| Registry set count after dry-run | `0` |
| Required context count after dry-run | `0` |
| Trading status catalogue count after dry-run | `0` |

The supplied dry-run output reports:

| Field | Result |
| --- | --- |
| Runtime bundle path | `/app/src/topicpilot_api/reference_data/bundles/tw-reference-v1` |
| `DRY_RUN` | `true` |
| `DRY_RUN_RESULT` | `VALIDATED / PLAN` |
| `referenceVersion` | `tw-reference-v1` |
| `transactional` | `true` |
| `createdMarkets` | `0` |
| `createdInstruments` | `0` |
| `createdReferenceRows` | `37` planned rows; not a mutation |
| `retiredRegistrySets` | `0` |
| `idempotent` | `true` |
| `noopReferenceWriteSet` | `[]` |
| `DRY_RUN_MUTATION` | `NO` |
| `DRY_RUN_DB_STATE_CHANGED` | `NO` |

## Canonical bundle reconciliation

The exact release SHA contains and locally validates the canonical bundle at:

`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/`

The repository manifest validates the expected derived dataset:

- `BUNDLE_VERSION` = `tw-reference-v1`.
- `BUNDLE_VALIDATION` = `PASS`.
- `BUNDLE_MARKETS` = `2`.
- `BUNDLE_INSTRUMENTS` = `507`.
- `BUNDLE_TPE` = `314`.
- `BUNDLE_TWO` = `193`.
- `BUNDLE_CONTEXTS` = TWD, Asia/Taipei, REGULAR, TW_MARKET.
- `BUNDLE_CALENDAR` = 23 holidays + 1 suspended date, 24 dates total.
- `BUNDLE_6806_EVIDENCE` = `TWSE-DELISTED-6806-20260623`.

The exact committed manifest records:

`5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`

The corrected machine-readable Production dry-run evidence records the same
value:

`5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`

`BUNDLE_HASH_MATCH = PASS` and `PRODUCTION_BUNDLE_DRIFT = NO`. The earlier
`...aa5f17c...` value was a screenshot transcription error and is superseded;
it is not the accepted Production evidence.

## Planned write boundary

The supplied dry-run write set matches the repository runbook:

- `markets`
- `instruments`
- `reference_registry_sets`
- `reference_currencies`
- `reference_timezones`
- `reference_sessions`
- `reference_trading_statuses`
- `reference_adjustments`
- `reference_calendar_dates`

`PLANNED_NON_REFERENCE_WRITE_SET = NONE`.

Topics, topic hierarchy, instrument-topic relations, raw/timeline/canonical
observations, Lifecycle, Opportunity, and legacy audit tables are outside the
planned write set. The dry-run reported no non-reference table.

## Activation and rollback boundary

No activation occurred. The reviewed repository contract remains:

`DRAFT -> VALIDATED -> ACTIVE`,

with at most one ACTIVE registry set; a previous ACTIVE set is retired only
inside the same transaction after final validation. A failed transaction
rolls back the registry, identity, context, calendar, and activation changes
together. These properties were not exercised against Production in this
task because only dry-run was authorized.

## Fixed final fields

```text
TASK_DATA_REF_004 = YES
REMOTE_MAIN_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
WORKFLOW_RELEASE_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
WORKFLOW_RUN = 31646749478
DEPLOY_HOOK_POST = PASS
WEB_DEPLOY = SAME_SHA_VALIDATION_PASS (31646945930); actual Sites deploy NOT RUN
WORKER_DEPLOY = NOT RUN
EXPECTED_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
RUNTIME_GIT_COMMIT = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c (operator evidence)
PROVIDER_LINEAGE_BUILD_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c (operator evidence)
RUNTIME_SHA_VERIFIED = YES
READYZ_HTTP = 200
READYZ = PASS
TWSE_ADAPTER = twse-official-daily.v2
TPEX_ADAPTER = tpex-official-daily.v2
MARKET_BATCH = true
TPE_AUTHORITY = TWSE_OFFICIAL_DAILY
TWO_AUTHORITY = TPEX_OFFICIAL_DAILY
G0 = PASS
PRECHECK_REFERENCE_VERSION = tw-reference-v1
PRECHECK_REFERENCE_ACTIVE = NO
PRECHECK_MARKET_COUNT = 2
PRECHECK_INSTRUMENT_COUNT = 0
PRECHECK_MISSING_MARKETS = []
PRECHECK_MISSING_INSTRUMENTS = PRESENT
PRECHECK_DUPLICATE_IDENTITIES = []
PRECHECK_MISSING_REFERENCE_CONTEXTS = []
PRECHECK_REFERENCE_LOAD_STATUS = NOT_READY
BUNDLE_VERSION = tw-reference-v1
BUNDLE_VALIDATION = PASS (local exact-SHA manifest validation)
BUNDLE_SHA256_REPO = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
BUNDLE_SHA256_OPERATOR = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
BUNDLE_SHA256_MATCH = PASS
PRODUCTION_BUNDLE_DRIFT = NO
BUNDLE_MARKETS = 2
BUNDLE_INSTRUMENTS = 507
BUNDLE_TPE = 314
BUNDLE_TWO = 193
BUNDLE_CONTEXTS = TWD, Asia/Taipei, REGULAR, TW_MARKET
BUNDLE_CALENDAR = 23 holidays + 1 suspended date
BUNDLE_6806_EVIDENCE = TWSE-DELISTED-6806-20260623
DRY_RUN = true
DRY_RUN_RESULT = VALIDATED / PLAN
DRY_RUN_MUTATION = NO
DRY_RUN_DB_STATE_CHANGED = NO
PLANNED_REFERENCE_WRITE_SET = markets, instruments, reference_registry_sets, reference_currencies, reference_timezones, reference_sessions, reference_trading_statuses, reference_adjustments, reference_calendar_dates
PLANNED_NON_REFERENCE_WRITE_SET = NONE
CURRENT_ACTIVE_REFERENCE = NONE
PLANNED_TRANSITION = DRAFT -> VALIDATED -> ACTIVE (NOT EXECUTED)
AI_WORKLOG_UPDATED = YES (append-only)
AI_WORKLOG_UPDATE_REQUIRED_AFTER_OPERATOR_RUN = YES (satisfied)
REPORT_UPDATED_OR_CREATED = UPDATED (formal report created and corrected in this closeout)
NEXT_TASK_MODIFIED = NO
PRODUCTION_DB_CONNECTED = YES (operator read-only/dry-run session)
PRODUCTION_MUTATION = NO
REFERENCE_BOOTSTRAP_EXECUTED = NO
G1_PRODUCTION = NOT_RECHECKED_AFTER_BOOTSTRAP
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
FINAL_STATUS = READY_FOR_ONE_SHOT_PRODUCTION_REFERENCE_BOOTSTRAP_AUTHORIZATION
BLOCKER = NONE
```

## Final boundary

No additional Production command is part of this closeout. Do not run
activation, bootstrap, G1-after-bootstrap, G2/G3, Canary #2, or Scheduler
from this task. The next action requires separate explicit
TASK-DATA-REF-005 authorization; no DATA-REF-005 work is started here.
