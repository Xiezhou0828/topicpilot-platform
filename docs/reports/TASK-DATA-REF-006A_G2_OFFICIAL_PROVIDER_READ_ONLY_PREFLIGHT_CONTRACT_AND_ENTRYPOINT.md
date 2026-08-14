# TASK-DATA-REF-006A G2 Official Provider Read-Only Preflight Contract and Entrypoint

## Fixed handoff

```text
TASK_DATA_REF_006A = IMPLEMENTED
APPLICATION_RUNTIME_AUTHORITY_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
ORIGIN_MAIN_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
WORKTREE_BASE_SHA = 1c9938733d3befc2e3d6e7fffd5763197986d19f
BRANCH = codex/task-data-ref-006a-20260814
DOCUMENTATION_SHA = DISTINCT_LOCAL_COMMIT_REPORTED_AT_HANDOFF

G2_AUTHORITY_CREATED = YES
G2_AUTHORITY_FILE = docs/operations/provider-preflight.md
G2_ENTRYPOINT_CREATED = YES
G2_ENTRYPOINT = topicpilot-provider-preflight --run-date YYYY-MM-DD --reference-version tw-reference-v1
G2_EXECUTION_CLASS = READ_ONLY
G2_PRODUCTION_EXECUTED = NO

TARGET_DATE_AUTHORITY = EXPLICIT_RUN_DATE_VALIDATED_AGAINST_REFERENCE_SESSION_CALENDAR
TARGET_DATE_SYSTEM_OR_BROWSER_DERIVED = NO
TARGET_DATE_HARDCODED = NO

TPE_PROVIDER_AUTHORITY = TWSE_OFFICIAL_DAILY
TPE_ADAPTER_VERSION = twse-official-daily.v2
TWO_PROVIDER_AUTHORITY = TPEX_OFFICIAL_DAILY
TWO_ADAPTER_VERSION = tpex-official-daily.v2
MARKET_BATCH = true
FALLBACK_ALLOWED = NO
VERIFICATION_ONLY_PROVIDERS = Yahoo daily / Taishin intraday

DATABASE_REQUIRED = YES
DATABASE_ACCESS_CLASS = SELECT_ONLY
PRODUCTION_WRITE_SET = []
NON_REFERENCE_WRITE_SET = []
REFERENCE_TABLE_WRITES = NONE
MARKET_INSTRUMENT_WRITES = NONE
OBSERVATION_WRITES = NONE
LIVE_RUN_ATTEMPT_WRITES = NONE
TRACKING_SNAPSHOT_LIFECYCLE_OPPORTUNITY_WRITES = NONE
SCHEDULER_WRITES = NONE
TRANSACTIONAL_MUTATION = NOT_APPLICABLE_READ_ONLY

G1 = PRESERVED_NOT_REEXECUTED
G2 = NOT_RUN_IN_PRODUCTION
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
PUSH = NO
DEPLOY = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_MODIFIED = NO

FINAL_STATUS = READY_FOR_G2_PREFLIGHT_INTEGRATION_REVIEW
BLOCKER = NONE
```

## Implemented contract

The new preflight is a dedicated operator path. It loads the approved
`tw-reference-v1` registry/context and active EQUITY identities with the
existing reference evaluator and SELECT-only ORM queries. It validates the
explicit `--run-date` against `REGULAR` / `TW_MARKET`, including persisted
HOLIDAY and SUSPENDED dates, before making provider requests.

For each canonical market it builds the existing historical provider registry
for a one-day window with `market_batch=true`, requires the exact official
registration and adapter version, and invokes the adapter's validated
market-level endpoint once. It requires a parsed response, the requested date,
non-empty data, and complete coverage of the active identity codes derived at
runtime. The count is never a permanent `507` rule.

No Yahoo or Taishin fallback can satisfy the gate. Provider, parse, date,
empty-payload, authority, context, and partial-coverage failures return a
machine-readable `FAIL` result and a non-zero exit code. Database/context
exceptions are sanitized to `PREFLIGHT_READ_FAILED`; connection strings,
credentials, headers, cookies, tokens, and exception text are not printed.

The emitted contract contains `gate`, `status`, `referenceVersion`,
`targetDate`, `targetDateIsSession`, `targetDateReason`, `readOnly`, empty
write-set fields, `fallbackAllowed=false`, reference evidence, and per-market
provider/reachability/parse/date/data/coverage evidence. A PASS requires both
official markets to pass all conditions.

The path does not import or call the live collector, `PostCloseUpdater`,
historical ingestion, tracking refresh, Topic Snapshot, Lifecycle,
Opportunity, or Scheduler code. It does not call `add`, `flush`, `commit`,
update, delete, or migration operations. Existing `topicpilot-live`, live
dry-run, provider lineage, and reference-check behavior is unchanged.

## Verification record

The focused local suite passed:

```text
24 passed, 1 skipped
```

The skipped test is the PostgreSQL SELECT-only boundary test because this
worktree environment did not provide `TEST_DATABASE_URL` or `DATABASE_URL`.
The same boundary test was then run against an isolated disposable PostgreSQL
database after loading the completed `tw-reference-v1` state and passed `1/1`.
It snapshots markets, instruments, reference tables, observation tables, live
tables, snapshots, and Lifecycle results before and after the preflight and
requires exact equality plus an empty write set.

The CI-equivalent backend run passed `322 passed / 49 skipped / 59 deselected`
with one existing Starlette/httpx deprecation warning. Full repository API
Ruff passed; targeted Ruff/format, Python compile, pip check, OpenAPI drift,
and `git diff --check` passed. Alembic upgrade, downgrade-one, and upgrade
head passed on the disposable PostgreSQL database. The reference bootstrap
PostgreSQL test passed `1/1`. A changed-file secret-value scan found no
connection strings, bearer values, or credential assignments; policy mentions
of DATABASE_URL/credentials remain intentionally documented. No Production
validation was attempted.

## Operator stop boundary

After deployment of an explicitly authorized application revision, the
operator must first verify the runtime SHA and provider lineage in the same
protected runtime, then run the command from the runbook. Preserve the JSON
evidence. A PASS stops for a separate G2 integration review; it does not
authorize `topicpilot-live`, `--apply`, `--activate`, G3, Canary, or Scheduler.
