# TASK-DATA-REF-006C-A Explicit G2 Run-Date Authorization and Preflight Resume

## Fixed fields

```text
TASK_DATA_REF_006C_A = DATE_AUTHORIZED_PHASE_1_COMPLETE

AUTHORIZED_G2_RUN_DATE = 2026-08-13
AUTHORIZED_DATE_SOURCE = explicit operator authorization
TRADING_DAY_VALIDATION = PASS
DATE_SUBSTITUTED = NO

RUNTIME_GIT_COMMIT = PENDING_OPERATOR_RECHECK
PROVIDER_LINEAGE_BUILD_SHA = PENDING_OPERATOR_RECHECK
RUNTIME_SHA_VERIFIED = PENDING_OPERATOR_RECHECK
G0 = PENDING_OPERATOR_RECHECK

G1_REFERENCE_ACTIVE = PENDING_OPERATOR_RECHECK
G1_REFERENCE_LOAD_STATUS = PENDING_OPERATOR_RECHECK
G1_MARKET_COUNT = PENDING_OPERATOR_RECHECK
G1_INSTRUMENT_COUNT = PENDING_OPERATOR_RECHECK

TPE_PROVIDER = TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION = twse-official-daily.v2
TPE_RESULT = PENDING_OPERATOR_PREFLIGHT
TPE_DATA_DATE = PENDING_OPERATOR_PREFLIGHT
TPE_COVERAGE = PENDING_OPERATOR_PREFLIGHT
TPE_MISSING_IDENTITIES = PENDING_OPERATOR_PREFLIGHT

TWO_PROVIDER = TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION = tpex-official-daily.v2
TWO_RESULT = PENDING_OPERATOR_PREFLIGHT
TWO_DATA_DATE = PENDING_OPERATOR_PREFLIGHT
TWO_COVERAGE = PENDING_OPERATOR_PREFLIGHT
TWO_MISSING_IDENTITIES = PENDING_OPERATOR_PREFLIGHT

FALLBACK_USED = PENDING_OPERATOR_PREFLIGHT
FALLBACK_CAN_PASS_G2 = NO

G2 = NOT_RUN
G3 = NOT_RUN

PRODUCTION_DB_ACCESS = NOT_CONNECTED (planned access class: SELECT_ONLY)
PRODUCTION_MUTATION = NO
PRODUCTION_WRITE_SET = []

CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO

AI_WORKLOG_UPDATED = YES
REPORT_CREATED = YES

FINAL_STATUS = BLOCKED_OPERATOR_EVIDENCE_REQUIRED
BLOCKER = Phase 2 G0 recheck, Phase 3 minimum G1 recheck, and the authorized
  read-only Production preflight still require execution in the authenticated
  Render runtime.
```

## Phase 1 repository validation

The explicit operator authorization is `2026-08-13`; this task did not
substitute another date. The committed bundle calendar
`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/calendar_dates.json`
contains no `TW_MARKET` row for `2026-08-13`, and the date is a Thursday. It is
therefore not a persisted `HOLIDAY` or `SUSPENDED` date and passes the
repository-level trading-day precheck.

This validates the date authority only. It does not prove that the Production
runtime has the same active reference state or that either provider endpoint is
available for the date.

## Required operator sequence

Run the following in the same authenticated Render Production Shell and stop
immediately on any SHA, lineage, G1, or state drift:

```console
printenv RENDER_GIT_COMMIT
topicpilot-provider-lineage

topicpilot-reference-check \
  --reference-version tw-reference-v1

topicpilot-provider-preflight \
  --run-date 2026-08-13 \
  --reference-version tw-reference-v1
```

The last command is the dedicated read-only G2 path. It uses the application
database only for SELECT-only reference/calendar/market/active-EQUITY context,
calls the official TPE/TWO market-batch providers once, disallows fallback as
a PASS condition, and reports an empty Production/non-reference write set.

The command must not be replaced by `topicpilot-live`, a dry-run of the live
collector, manual SQL, persistence, reconciliation, G3, Canary, or Scheduler.
The operator should return the JSON result and the SHA/lineage/G1 evidence;
credentials and `DATABASE_URL` must not be included.

No Production command was run by this task. No Production database connection,
provider request, mutation, deploy, push, G3, Canary, or Scheduler action
occurred. Documentation remains local-only.

## Production operator evidence and final decision

The operator executed the authorized sequence in the same authenticated
Production runtime. The runtime SHA and provider-lineage build SHA both equal
`3366ee61ba71a4f98ad886b53284e3faedbf44e0`, and lineage status is `READY`.
G0 therefore passed.

The fresh `topicpilot-reference-check` returned active and READY
`tw-reference-v1`, two markets, 507 instruments, 24 calendar dates, one
registry set, one required context, seven trading statuses, three adjustments,
and empty missing/duplicate identity and market sets. G1 therefore passed.

The authorized preflight returned the following raw provider evidence:

```text
targetDate = 2026-08-13
targetDateIsSession = true
status = FAIL
readOnly = true
fallbackAllowed = false
productionWriteSet = []
nonReferenceWriteSet = []

TPE:
  provider = TWSE_OFFICIAL_DAILY
  providerVersion = twse-official-daily.v2
  reachable = true
  payloadParsed = true
  targetDateMatched = true
  dataAvailable = true
  recordCount = 1378
  expectedInstrumentCount = 314
  coveredInstrumentCount = 313
  missingInstrumentCount = 1
  coverageComplete = false
  status = FAIL
  errorCode = PARTIAL_PROVIDER_COVERAGE

TWO:
  provider = TPEX_OFFICIAL_DAILY
  providerVersion = tpex-official-daily.v2
  reachable = true
  payloadParsed = true
  targetDateMatched = true
  dataAvailable = true
  recordCount = 10474
  expectedInstrumentCount = 193
  coveredInstrumentCount = 193
  missingInstrumentCount = 0
  coverageComplete = true
  status = PASS
```

The CLI did not emit the missing TPE identity code, only
`missingInstrumentCount=1`; no identity code is inferred here. The result is
therefore not promoted to G2 PASS. No fallback was used, and fallback cannot
turn this official-provider coverage failure into PASS.

```text
TASK_DATA_REF_006C_A = COMPLETED_FAIL_CLOSED
AUTHORIZED_G2_RUN_DATE = 2026-08-13
TRADING_DAY_VALIDATION = PASS
DATE_SUBSTITUTED = NO

RUNTIME_GIT_COMMIT = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
PROVIDER_LINEAGE_BUILD_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
RUNTIME_SHA_VERIFIED = YES
G0 = PASS

G1_REFERENCE_ACTIVE = YES
G1_REFERENCE_LOAD_STATUS = READY
G1_MARKET_COUNT = 2
G1_INSTRUMENT_COUNT = 507

TPE_PROVIDER = TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION = twse-official-daily.v2
TPE_RESULT = FAIL
TPE_DATA_DATE = 2026-08-13
TPE_COVERAGE = 313/314, coverageComplete=false
TPE_MISSING_IDENTITIES = 1 (identity code not emitted)

TWO_PROVIDER = TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION = tpex-official-daily.v2
TWO_RESULT = PASS
TWO_DATA_DATE = 2026-08-13
TWO_COVERAGE = 193/193, coverageComplete=true
TWO_MISSING_IDENTITIES = 0

FALLBACK_USED = NO
FALLBACK_CAN_PASS_G2 = NO

G2 = FAIL
G3 = NOT_RUN

PRODUCTION_DB_ACCESS = SELECT_ONLY
PRODUCTION_MUTATION = NO
PRODUCTION_WRITE_SET = []

CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO

AI_WORKLOG_UPDATED = YES
REPORT_CREATED/UPDATED = YES

FINAL_STATUS = BLOCKED_G2_PROVIDER_COVERAGE_FAILURE
BLOCKER = TPE official daily payload covered 313 of 314 required active
  identities; errorCode=PARTIAL_PROVIDER_COVERAGE. Exact missing identity code
  was not emitted by the CLI. No remediation or retry is authorized here.
```

The preflight was read-only and reported empty write sets. No live collector,
daily persistence, reconciliation, reference mutation, G3, Canary, or
Scheduler action was run. Documentation remains local-only and no Production
runtime authority was changed.
