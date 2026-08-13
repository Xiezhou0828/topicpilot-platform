# TASK-DATA-REF-006 Post-G1 G2 Authority Re-entry and Provider/Data Preflight

## Scope and stop decision

This report records a repository-authoritative, read-only audit after the
completed TASK-DATA-REF-005I G1 closure. It does not execute a Production
command, request a Production mutation, deploy, change Scheduler state, or
start G2/G3/Canary work.

The repository does not currently expose one exact, named, non-mutating G2
provider/data preflight authority. The documented G2 requirement is only that
official TWSE/TPEx endpoints be reachable and have data for the target date.
The only checked-in CLI that invokes the official daily provider path is the
mutating topicpilot-live --mode post-close --once path. Its --dry-run option
is a scheduler-decision dry-run and explicitly does not call a provider.
Therefore the task stops fail-closed:

    G2_AUTHORITY_FOUND = NO
    G2_AUTHORITY_AMBIGUOUS = YES
    G2_EXECUTED = NO
    PRODUCTION_MUTATION = NO
    FINAL_STATUS = BLOCKED_G2_AUTHORITY_AMBIGUOUS
    BLOCKER = No exact non-mutating G2 provider/data preflight entrypoint and
              complete authoritative G2 contract exists in the repository.

## Authority read order and repository result

The requested authority order was applied as far as the repository contains
the named artifacts:

| Authority | Result |
|---|---|
| docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md | Not present in this worktree |
| docs/DOCUMENTATION_AUTHORITY_INDEX.md | Not present; nearest canonical index is docs/DOCUMENTATION_INDEX.md |
| PROJECT_CONTEXT.md | Read; navigation/status layer, not operational G2 authority |
| Architecture Book | Read; docs/architecture/README.md maps deployment/data authority |
| Current operations/deployment runbook | docs/operations/deployment.md read |
| Reference bootstrap runbook | docs/operations/reference-bootstrap.md read; it governs G1/reference bootstrap, not G2 provider preflight |
| Provider lineage authority | market_data/lineage.py and provider_lineage_cli.py read |
| P3A/G0-G3 evidence | TASK-OPS-023A-P3A_ADAPTER_V2_DEPLOYMENT_PREFLIGHT_REPORT.md read |
| Current worklog and 005I closure | Read; 005I G1 evidence is the starting state, not a current 006 runtime recheck |

The current local branch contains only documentation commits after the
application runtime authority. The application/runtime authority remains:

    APPLICATION_RUNTIME_AUTHORITY_SHA = c75956336df03a1fd661a054b33b0c4845d4f159

The 005I local documentation closure commit remains local and is not an
application authority:

    005I_LOCAL_DOCS_COMMIT = 18116dbf96ee1de64ac954416b2e82cc1957d740
    PUSH = NO
    DEPLOY = NO

## Existing G2 statements and why they are insufficient

docs/operations/deployment.md defines the post-close command and says that it
uses official TWSE daily data for TPE and official TPEx daily data for TWO,
then writes through the canonical observation pipeline. Its acceptance output
is a completed SUCCESS run with dailyMarketReconciliation.status=READY,
full covered count, zero unexplained missing data, and downstreamReady=true
(lines 81-101). This is a post-close execution/acceptance contract, not a
read-only G2 preflight.

The same document's Canary gate says only:

    G2 = TWSE/TPEx official endpoints are reachable for the target date.

It labels the later topicpilot-live --mode post-close --once --run-date
YYYY-MM-DD command as a command to prepare only after the complete gate order
(lines 171-184). It does not define a separate G2 command, result schema,
freshness rule, coverage request, or write-free boundary.

The P3A report has the same gap: its gate matrix labels G2 Provider preflight
as operator-required and describes official endpoint reachability and
target-date availability, but does not identify an exact preflight entrypoint
(lines 210-215). Its listed Canary command is explicitly prepare-but-do-not-
execute and is the mutating post-close command (lines 243-252).

## Exact entrypoints found

### Provider lineage

    topicpilot-provider-lineage

This is a valid secret-free, read-only provenance command. The code constructs
the historical provider registry locally and does not make an exchange request
or access the database. It proves adapter composition and market authority,
not endpoint reachability, target-date payload availability, freshness, or
507-instrument coverage.

### Reference/G1 preservation

    topicpilot-reference-check --reference-version tw-reference-v1

This is the valid SELECT-only G1 preservation command. Its CLI creates an
engine from get_settings().database_url, opens a SQLAlchemy Session, calls
inspect_reference_preflight, prints the result, and disposes the engine
(reference_cli.py lines 25-44). The evaluator is documented as reading
formal tables and never committing (reference_check.py lines 149-157).

### Existing official daily provider path

    topicpilot-live --mode post-close --once --run-date YYYY-MM-DD

This is the only checked-in CLI path that invokes the official daily adapters
for the full post-close universe. services/api/pyproject.toml lines 30-41
list topicpilot-live but no topicpilot-g2-preflight,
topicpilot-provider-preflight, or equivalent G2 command.

The CLI accepts --dry-run, but its help text is print scheduler decision
without provider call; it returns before creating the provider router or
database engine (live/cli.py lines 25-38 and 69-74). It cannot establish G2
provider/data readiness.

### Historical probe

    topicpilot-history-probe

This is not the G2 authority. Its implementation is a bounded Taishin
historical-window probe, requires Taishin credentials, accepts a small
explicit symbol list, and does not exercise the official TWSE/TPEx
market-batch path (live/history_probe.py lines 1-2, 57-64, and 125-167).
It is therefore not evidence for the required TPE/TWO official daily
provider/data preflight.

## Code-path and write-boundary audit

The official daily post-close path is behaviorally mutating before it can
produce the data needed for downstream acceptance:

1. topicpilot-live creates a database engine from application settings, opens
   a SQLAlchemy session, refreshes the tracking universe, constructs
   PostCloseUpdater, and calls the scheduler (live/cli.py lines 72-90).
2. PostCloseUpdater._create_run adds a LiveCollectorRun, flushes, and commits
   before provider collection (live/post_close.py lines 115-147).
3. Each instrument calls ingest_historical, commits successful provider
   results, adds LiveCollectorAttempt, and commits again
   (live/post_close.py lines 229-302).
4. ingest_historical is explicitly a persistence path into the raw,
   observation-timeline, and canonical observation chain; its contract says
   that the caller owns the transaction and rolls back that write set on
   failure (market_data/ingestion.py lines 250-260).
5. The post-close flow refreshes tracking and, when reconciliation is ready,
   invokes Topic Snapshot and Lifecycle shadow processing
   (live/post_close.py lines 304-365).

Accordingly, the existing post-close candidate is not safe to use as an
unapproved G2 preflight.

    G2_EXISTING_PROVIDER_CALLING_ENTRYPOINT = topicpilot-live --mode post-close --once --run-date YYYY-MM-DD
    G2_EXISTING_ENTRYPOINT_CLASS = MUTATING
    G2_EXISTING_ENTRYPOINT_PRODUCTION_WRITE_RISK = YES

For a proper G2 preflight under this task, the required write set is empty:

    G2_REQUIRED_ALLOWED_WRITE_SET = []
    G2_REQUIRED_NON_REFERENCE_WRITE_SET = []

The following must remain prohibited during a G2 preflight:

    raw_market_observations
    observation_timeline_batches
    observation_timeline_entries
    observation_timeline_quality_events
    canonical_observations
    canonical_price_observations
    canonical_volume_observations
    canonical_trading_status_observations
    live_collector_runs
    live_collector_attempts
    tracking state
    topic snapshots
    Lifecycle results
    Scheduler state/configuration

## G2 contract resolution

    G2_AUTHORITY_FILE = NONE (no single authoritative G2 preflight file)
    G2_AUTHORITY_CODE_PATH = NONE (no dedicated G2 preflight implementation)
    G2_ENTRYPOINT = NONE (safe official-daily G2 preflight is not implemented)
    G2_EXECUTION_CLASS = UNRESOLVED; existing provider path is MUTATING
    G2_PASS_CRITERIA = PARTIAL ONLY:
      official TWSE/TPEx reachable for target date;
      repository post-close acceptance additionally requires SUCCESS,
      READY reconciliation, full covered count, zero unexplained/date/duplicate
      errors, and downstreamReady=true.
    G2_ALLOWED_WRITE_SET = NONE for the required preflight
    G2_PROHIBITED_WRITE_SET = all observation, run/attempt, tracking, snapshot,
      Lifecycle, and Scheduler writes listed above
    G2_REQUIRES_PRODUCTION_MUTATION = YES for the only existing provider-calling
      entrypoint; this was not authorized and was not executed

The repository therefore cannot truthfully produce the status
READY_FOR_G2_MUTATION_AUTHORIZATION_REVIEW yet: that status would require a
unique exact G2 authority and a complete contract first. This task does not
invent flags or promote the post-close mutating command into a preflight.

## Runtime and G1 re-entry boundary

The 005I closure supplies the starting application authority and a passing G1
state. TASK-DATA-REF-006 requires a fresh protected-runtime recheck before a
future G2 review. No current 006 operator evidence was supplied or executed by
this audit.

The exact secret-safe operator commands defined by existing repository
contracts are:

    printenv RENDER_GIT_COMMIT
    topicpilot-provider-lineage
    topicpilot-reference-check --reference-version tw-reference-v1

Expected preservation values from 005I are:

    RUNTIME_GIT_COMMIT = c75956336df03a1fd661a054b33b0c4845d4f159
    PROVIDER_LINEAGE_BUILD_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
    PROVIDER_LINEAGE_STATUS = READY
    G1_REFERENCE_ACTIVE = YES
    G1_REFERENCE_LOAD_STATUS = READY
    G1_MARKET_COUNT = 2
    G1_INSTRUMENT_COUNT = 507
    G1_MISSING_MARKETS = []
    G1_MISSING_INSTRUMENTS = []
    G1_DUPLICATE_IDENTITIES = []
    G1_PRESERVED = PASS in 005I; CURRENT_006_RECHECK = NOT_SUPPLIED

These expected values are not claimed as new runtime evidence in this report.
If a later protected-runtime recheck differs, the task must stop for runtime
provenance or G1 regression review before any G2 decision.

## Provider and reference authority preservation

The repository contract remains consistent with 005I:

    TWSE = twse-official-daily.v2
    TPEx = tpex-official-daily.v2
    TPE authority = TWSE_OFFICIAL_DAILY
    TWO authority = TPEX_OFFICIAL_DAILY
    marketBatch = true for the official daily adapters
    Yahoo daily = VERIFICATION_ONLY
    Taishin = INTRADAY_ONLY
    REFERENCE_VERSION = tw-reference-v1

The local application diff from the verified runtime authority to the current
documentation branch contains documentation files only; no provider,
reference, migration, bootstrap, or remediation code changed. This is a
repository provenance result, not a substitute for the protected runtime
recheck.

The reference check and live CLI both obtain DATABASE_URL through
get_settings().database_url in their code paths. The provider-lineage command
does not use a database at all. Thus the code gives the following result:

    REFERENCE_CHECK_DATABASE_BINDING = application settings DATABASE_URL
    LIVE_DATABASE_BINDING = application settings DATABASE_URL
    REFERENCE_CHECK_AND_LIVE_BINDING = SAME_BY_CODE_PATH
    PROVIDER_LINEAGE_DATABASE_BINDING = NONE
    CURRENT_PRODUCTION_BINDING_VERIFIED = NO (no 006 operator evidence)

## Fixed report fields

    TASK_DATA_REF_006 = POST-G1 G2 AUTHORITY RE-ENTRY AUDIT
    STARTING_APPLICATION_RUNTIME_SHA = c75956336df03a1fd661a054b33b0c4845d4f159
    RUNTIME_GIT_COMMIT = OPERATOR_REQUIRED
    PROVIDER_LINEAGE_BUILD_SHA = OPERATOR_REQUIRED
    RUNTIME_SHA_VERIFIED = NOT_RECHECKED_IN_006
    PROVIDER_LINEAGE_STATUS = OPERATOR_REQUIRED

    G1_REFERENCE_ACTIVE = YES (005I closure evidence)
    G1_REFERENCE_LOAD_STATUS = READY (005I closure evidence)
    G1_MARKET_COUNT = 2 (005I closure evidence)
    G1_INSTRUMENT_COUNT = 507 (005I closure evidence)
    G1_MISSING_MARKETS = [] (005I closure evidence)
    G1_MISSING_INSTRUMENTS = [] (005I closure evidence)
    G1_DUPLICATE_IDENTITIES = [] (005I closure evidence)
    G1_PRESERVED = CURRENT_006_RECHECK_NOT_SUPPLIED

    G2_AUTHORITY_FILE = NONE
    G2_AUTHORITY_CODE_PATH = NONE
    G2_ENTRYPOINT = NONE
    G2_EXECUTION_CLASS = UNRESOLVED; existing official path is MUTATING
    G2_PASS_CRITERIA = INCOMPLETE REPOSITORY CONTRACT
    G2_ALLOWED_WRITE_SET = [] for required preflight
    G2_PROHIBITED_WRITE_SET = observation/run/attempt/tracking/snapshot/
      Lifecycle/Scheduler writes
    G2_REQUIRES_PRODUCTION_MUTATION = YES for existing provider-calling path

    PROVIDER_AUTHORITY_PRESERVED = REPOSITORY_CONTRACT_PASS_RUNTIME_RECHECK_REQUIRED
    REFERENCE_AUTHORITY_PRESERVED = REPOSITORY_CONTRACT_PASS_RUNTIME_RECHECK_REQUIRED

    G2_EXECUTED = NO
    G2_RESULT = NOT_RUN
    G2 = NOT_RUN
    G2_BLOCKER_CLASS = CONTRACT / AUTHORITY
    G2_BLOCKER = No unique exact non-mutating G2 provider/data preflight authority;
      current official-daily CLI is a mutating post-close path.

    PRODUCTION_DB_CONNECTED = NO (no Production connection made by this audit)
    PRODUCTION_MUTATION = NO
    G3 = NOT_RUN
    CANARY_2 = NOT_RUN
    SCHEDULER_CHANGED = NO

    G2_EXECUTION_FREEZE = ACTIVE
    RUNTIME_CHANGED_DURING_EXECUTION = NOT_APPLICABLE; no execution occurred
    AI_WORKLOG_UPDATED = YES
    FORMAL_REPORT_CREATED = YES
    005I_LOCAL_DOCS_COMMIT_PUSHED = NO
    PUSH = NO
    DEPLOY = NO
    NEXT_TASK_MODIFIED = NO
    DATA_GOVERNANCE_HOLD_TOUCHED = NO

    FINAL_STATUS = BLOCKED_G2_AUTHORITY_AMBIGUOUS
    BLOCKER = No exact non-mutating G2 provider/data preflight entrypoint and
              complete authoritative G2 contract exists in the repository.

The next safe step is to define and review a dedicated read-only or explicitly
shadow-safe G2 provider/data preflight contract and entrypoint. This report
does not implement that new capability, run the mutating post-close path, or
start G2/G3/Canary/Scheduler.

