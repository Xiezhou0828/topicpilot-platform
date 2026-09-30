# TASK-FORMAL-MARKET-UNAVAILABLE-INSTRUMENT-READINESS-AND-DISCLOSURE-023

## Closure status

```text
TASK_ID=TASK-FORMAL-MARKET-UNAVAILABLE-INSTRUMENT-READINESS-AND-DISCLOSURE-023
TASK_FINAL_STATUS=COMPLETE_WITH_BOUNDED_READBACK_LIMITATION
CANONICAL_MAIN_SHA=e7bbd7c9d7c2ceb1a19805c37736323cbeba3229
MERGED_PR_46=https://github.com/Xiezhou0828/topicpilot-platform/pull/46
MERGED_PR_47=https://github.com/Xiezhou0828/topicpilot-platform/pull/47
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
PRODUCTION_DEPLOYED=NO
HISTORICAL_BACKFILL=NO
RECOVERY_PERFORMED_BY_THIS_TASK=NO
MIGRATION_ADDED=NO
ZERO_FILL_OR_FORWARD_FILL_ADDED=NO
```

TASK-023 is implemented and canonicalized on `main`. The implementation keeps
the existing fail-closed boundary: a legitimate unavailable instrument is
covered only when a current canonical trading-status observation proves that
state; an absent row, provider error, date mismatch, or unknown state remains a
publication blocker.

## Implemented contract

- Added the typed availability taxonomy: `AVAILABLE`, `NO_TRADE`, `SUSPENDED`,
  `EXCHANGE_CONFIRMED_NO_DATA`, `HALTED`, `DELISTED`, `TERMINATED`,
  `MISSING_MARKET_DATA`, `PROVIDER_ERROR`, `DATE_MISMATCH`, and `UNKNOWN`.
- Added a canonical daily market read model that joins the date-effective
  universe, current price evidence, current canonical status evidence, last
  valid close, and effective Topic membership. It never writes a price for an
  unavailable instrument.
- Added reconciliation metadata for `eligibleUniverse`, `pricedCount`,
  `coveredCount`, `unavailableCount`, `pipelineFailureCount`, `unknownCount`,
  `coveragePct`, and typed `unavailableInstruments`.
- Legitimate unavailable rows remain in the universe, are excluded from price
  calculations, and do not block unrelated formal Topic publication. Pipeline
  failure and unknown rows remain fail-closed for formal publication.
- Today/Home now exposes `今日無有效行情：N 檔` with an expandable detail list
  containing symbol, name, market, status, reason, and last-valid-price
  fields. Missing last-valid values remain null/unavailable.
- The protected forensic readback now returns a fixed, bounded list of all
  skipped collector attempts up to 1000 rows. The bound is above the current
  553-instrument TPE+TWO universe and remains limited to the existing three
  collector tables.

## Protected evidence for the exposed recovery blocker

The existing recovery run was read through the protected
`production-readonly` Environment using transaction-level `READ ONLY`:

```text
READBACK_WORKFLOW_RUN=36755060467
READBACK_ARTIFACT_ID=11116177737
READBACK_TOOL_SHA=e7bbd7c9d7c2ceb1a19805c37736323cbeba3229
READBACK_TRANSACTION_READ_ONLY=true
POST_CLOSE_RUN_ID=2284ae32-fb83-45bf-bad5-4dd506c3d9a8
POST_CLOSE_RUN_STATUS=PARTIAL
REQUESTED_INSTRUMENTS=553
FINAL_SUCCESS_COUNT=552
FINAL_FAILURE_COUNT=0
FINAL_SKIPPED_COUNT=1
FINAL_RETRY_COUNT=0
FAILURE_CODE=FORMAL_TOPIC_SNAPSHOT_NOT_READY
```

The protected `unavailableAttempts` evidence contains 207 skipped attempts:
206 TWO attempts that later have successful attempts, plus one final TPE skip.
The one final TPE unavailable instrument is:

```text
SYMBOL=2601
NAME=益航
MARKET=TPE
STATUS=SKIPPED
ERROR_CODE=MISSING_MARKET_DATA
PROVIDER_STATUS=UNKNOWN
OBSERVED_AT=NULL
RETRIEVED_AT=NULL
ATTEMPT_STARTED_AT=2026-09-30T18:16:40.100188+08:00
```

The symbol/name mapping is from the committed expansion reference bundle;
collector readback scope intentionally contains no identity or price-history
tables. Therefore `lastValidPriceDate` and `lastValidClose` remain null when
that protected scope cannot prove them. The application read model follows the
same rule and does not fabricate either value.

The attempt evidence is consistent with the market summary: TPE had 347
initial provider failures, 346 successful final attempts, and one final skip;
TWO had 206 successful final attempts after 206 initial skips. The provider was
available, and the remaining final skip is correctly classified as genuine
missing market data rather than an exchange-confirmed no-trade state.

## Validation

- Backend CI passed, including migration/OpenAPI and the full repository test
  job; the final local backend run passed 961 tests with 60 PostgreSQL tests
  skipped because no local test database was configured.
- Frontend CI passed install, test, and build; the local workspace lacked
  `cross-env`, so the local build command could not start, while the GitHub
  Frontend install/test/build job passed.
- Added availability-policy matrix tests covering all legitimate unavailable
  states, pipeline failures, unknown states, no zero-fill behavior, and
  unrelated formal publication readiness.
- No Production deployment, recovery, historical backfill, or database write
  was performed by TASK-023.

