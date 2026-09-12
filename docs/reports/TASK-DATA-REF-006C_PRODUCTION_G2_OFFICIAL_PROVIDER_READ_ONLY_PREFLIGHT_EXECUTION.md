# TASK-DATA-REF-006C Production G2 Official Provider Read-Only Preflight Execution

## Fixed execution fields

```text
TASK_DATA_REF_006C = BLOCKED_G2_RUN_DATE_AUTHORITY_AMBIGUOUS

APPLICATION_RUNTIME_AUTHORITY_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
RUNTIME_GIT_COMMIT = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
PROVIDER_LINEAGE_BUILD_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
RUNTIME_SHA_VERIFIED = YES
G0 = PASS

G1_REFERENCE_ACTIVE = YES (last verified 006B baseline; no new 006C recheck)
G1_REFERENCE_LOAD_STATUS = READY (last verified 006B baseline; no new 006C recheck)
G1_MARKET_COUNT = 2 (last verified 006B baseline; no new 006C recheck)
G1_INSTRUMENT_COUNT = 507 (last verified 006B baseline; no new 006C recheck)
G1_RECHECK = NOT_RUN

G2_RUN_DATE = NOT_SUPPLIED
G2_RUN_DATE_REASON = The required explicit ISO target date was not supplied or
  authorized. The repository contract forbids deriving it from the local
  system date, browser date, or a hardcoded trading date.

TPE_PROVIDER = TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION = twse-official-daily.v2
TPE_RESULT = NOT_RUN
TPE_DATA_DATE = NOT_RUN
TPE_COVERAGE = NOT_RUN
TPE_MISSING_IDENTITIES = NOT_RUN

TWO_PROVIDER = TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION = tpex-official-daily.v2
TWO_RESULT = NOT_RUN
TWO_DATA_DATE = NOT_RUN
TWO_COVERAGE = NOT_RUN
TWO_MISSING_IDENTITIES = NOT_RUN

FALLBACK_USED = NOT_RUN
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

FINAL_STATUS = BLOCKED_G2_RUN_DATE_AUTHORITY_AMBIGUOUS
BLOCKER = An explicitly authorized G2 run date is required before the
  SELECT-only provider preflight can be executed.
```

## Repository authority and safety verification

The canonical runbook is `docs/operations/provider-preflight.md`. It defines
the exact command as:

```console
topicpilot-provider-preflight \
  --run-date YYYY-MM-DD \
  --reference-version tw-reference-v1
```

The CLI requires `--run-date`; it parses an explicit ISO date and does not
derive a date from the browser, local system clock, or a hardcoded trading
date. The preflight validates that date against the active `TW_MARKET`
reference calendar before any official provider request.

The implementation creates an engine from the application settings and opens
one SQLAlchemy session for SELECT-only reference, calendar, market, and active
EQUITY identity context. It does not call the live collector or any persistence
path, and its declared `productionWriteSet` and `nonReferenceWriteSet` are
empty. No Production command was run by this task because the required date
authority was absent.

The supplied runtime evidence confirms the application SHA and provider
lineage for G0. The 2-market/507-instrument READY reference state is retained
as the last verified 006B Production baseline; 006C has not claimed a fresh G1
observation. No TPE/TWO request, database connection, mutation, G3, Canary, or
Scheduler action occurred.

## Required operator continuation

After an explicit target date is authorized, the operator must recheck G0 and
the minimum G1 baseline in the same authenticated Production runtime, then run
the command above with that exact date. A PASS requires the target date to be
a session date, both official market-batch providers to reach and parse the
requested date, complete active-identity coverage for TPE and TWO, no fallback,
and empty Production/non-reference write sets. Any failure is fail-closed and
stops before G3 or downstream execution.

No credentials, DATABASE_URL, tokens, or secret values were requested or
printed. Documentation is local-only and has not been pushed.
