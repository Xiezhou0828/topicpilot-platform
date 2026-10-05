# TopicPilot Daily Formal Publication Orchestration

## CURRENT MAIN forensic and orchestration contract reconciliation

| Field | Value |
|---|---|
| Task | `TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-FORENSIC-001` |
| Repository | `Xiezhou0828/topicpilot-platform` |
| Canonical branch | `main` |
| Canonical HEAD inspected | `a687c748e1b7d512449b69884626c58ac7d86d12` |
| HEAD commit | `feat(web): complete topic experience v1` |
| `origin/main` at inspection | `a687c748e1b7d512449b69884626c58ac7d86d12` |
| Migration head | `0048_task_checkpoint_provider_metric_applicability` |
| Inspection date | 2026-10-05, Asia/Taipei |
| Production mutation | None; no deploy, migration, scheduler activation, retry, or push executed |
| Report state | Local working-tree report; not pushed or merged |

## Executive finding

The repository contains a substantial post-close implementation, but it does not yet prove a complete operational publication contract.

The software path is:

```text
session clock
  -> post-close invocation
  -> reference/calendar preflight
  -> TPE/TWO official batch collection
  -> trading-status resolution
  -> daily reconciliation
  -> official market facts
  -> formal Topic Snapshot
  -> formal Strength and formal Lifecycle
  -> current-day Home V2
  -> formal publication readback
  -> run completion receipt
```

The strongest current gate is not the clock. It is the reference-backed `G2` preflight plus `DailyMarketReconciliation.downstream_ready`, followed by formal Topic/Strength/Lifecycle/Home readback. The code is conservative about unknown data, legitimate no-trade, formal history gaps, and recovery Home publication.

The operational contract remains `PARTIAL` for two reasons:

1. The scheduler has a 13:45 Asia/Taipei start threshold and bounded provider attempts, but no explicit soft target, hard deadline, completion window, or terminal missed-window state.
2. Production scheduling, current runtime SHA readback, daily publication receipt readback, and Sites promotion are not proven by the checked-in release automation. The checked-in Render blueprint has no approved Cron resource and `autoDeployTrigger: off`.

## 1. Evidence boundary and source of truth

Evidence was taken from the clean nested repository `C:/Users/acer/Desktop/題材領航/topicpilot-platform`, not from the dirty outer workspace. `main` matched `origin/main` at the inspected commit. GitHub was used read-only to confirm the repository and commit identity.

The following are source-of-truth layers, in descending authority:

1. Current `main` source and tests.
2. Alembic schema at migration head `0048`.
3. Checked-in deployment and operations workflows.
4. Historical reports, used only as context and not as current runtime proof.

Historical production notes may contain a prior 15:00 schedule and prior runtime evidence. They do not override the current code default of `13:45`, and they do not prove the current runtime SHA or current scheduled execution.

## 2. Actual daily publication state machines

### 2.1 Scheduler state machine

`services/api/src/topicpilot_api/live/scheduler.py` and `live/session.py` implement:

| Condition | Scheduler mode | Action |
|---|---|---|
| Local session is open | `INTRADAY` | Maintain/start the intraday worker and run collector work |
| Before post-close threshold outside the session | `WAIT` | Sleep for the poll interval |
| At or after `TOPICPILOT_LIVE_POST_CLOSE_START` | `POST_CLOSE` | Invoke the configured post-close runner |
| Weekend or configured closed date | `WAIT` | Do not run post-close |
| Post-close exception | retry pending | Leave the in-memory completed date unset and retry on the next poll |
| `PARTIAL` or `FAILED` result | retry pending | Retry on the next poll |
| `SUCCESS` or `MARKET_CLOSED` result | completed for local date | Stop retrying in that process instance |

The default configuration is:

```text
timezone = Asia/Taipei
session = 09:00–13:30
post_close_start = 13:45
poll_interval = 300 seconds
```

There is no code-level `soft_target`, `hard_deadline`, `post_close_end`, `missed_window`, or `owner_escalation` state in the live configuration. Provider readiness and retry budgets are bounded, but the scheduler's outer retry loop is not bounded by a publication deadline. A process restart resets the in-memory completed-date marker; deterministic run identity and idempotent reuse are the protection against duplicate publication.

### 2.2 Daily data and formal publication state machine

The actual `PostCloseUpdater` phase model is:

```text
SESSION_VALIDATION
  -> INPUT_READINESS
  -> FORMAL_MARKET_FACTS
  -> A9_B2_FORMAL_PROCESSING
  -> FINAL_PUBLICATION
  -> COMPLETION
```

The phase is durable through append-only `live_collector_checkpoints`; the run also stores structured metadata and completion status.

| Phase | Current implementation | Blocking condition |
|---|---|---|
| Session validation | Resolve Asia/Taipei date, reference version, calendar code, session identity, and date-effective universe | Invalid reference bundle, wrong market scope, unavailable market context, or invalid run date |
| Input readiness | Verify exactly `TPE` and `TWO`, build official provider registry and tracking scope | Missing/duplicate/delisted/ineligible reference instruments |
| Market collection | Official TWSE and TPEx daily adapters, market-batched provider requests | Provider failure, timeout, wrong date, unknown missing data |
| Status resolution | Trading-status authority may convert legitimate no-trade to covered/unpriced | Unresolved instrument status remains uncovered |
| Reconciliation | Compute expected, observed, priced, covered, unavailable, and unexplained missing counts | `downstream_ready == false` |
| Formal market facts | Official indexes, aggregates, and institutional flows | Required market-fact readback not available |
| Formal Topic | Materialize bounded formal daily Topic Snapshot from the provisional engine output | Topic formal state is not `PUBLISHED`/`FINAL`/`COMPLETE` |
| Formal Strength | Persist and read back formal absolute/relative strength and structural derivatives | Strength lane fails or is incomplete |
| Formal Lifecycle | Evaluate formal lifecycle from formal Topic input and, when available, formal Strength | Formal history or input gate unavailable; no fake Day N is emitted |
| Home V2 | Current-day Home envelope and typed sections; forbidden in history recovery | No published market facts or current-day publication rule fails |
| Final readback | Verify Topic, Home or recovery exemption, institutional flow, Strength, and Lifecycle | Overall readback is `PARTIAL` or `FAIL` |

The final run status vocabulary is `SUCCESS`, `PARTIAL`, `FAILED`, or `MARKET_CLOSED`. A run is not a formal publication success merely because provider collection succeeded: the implementation downgrades a nominally successful collection when reconciliation is not downstream-ready or the formal readback is incomplete.

## 3. Session, calendar, and date authority

### 3.1 Canonical data authority

`provider_preflight.py` establishes the stronger data-plane authority:

```text
reference version = tw-reference-v1
calendar code = TW_MARKET
required session code = REGULAR
markets = TPE, TWO
```

The context is ready only when the reference registry is ready, the target date is a trading session, the prior session exists, the target date has valid lifecycle identity, and both market contexts are available. Closed dates are read from the database reference calendar, not inferred from observed price rows.

### 3.2 Scheduler authority split

The scheduler's `MarketSessionClock` knows the timezone, weekday/weekend, open/close time, and `TOPICPILOT_LIVE_CLOSED_DATES`. It does not directly query the canonical database reference calendar. Therefore a database holiday or exchange closure is only visible to the scheduler if the environment closed-date list is also maintained.

This creates a current authority split:

```text
scheduler gate: local clock + weekend + environment closed dates
publication gate: G2 reference bundle + TW_MARKET reference calendar + lifecycle identity
```

The publication gate is safer, but the scheduler may still invoke a post-close attempt on a date the canonical calendar later rejects. The outcome is then determined downstream. This must be reconciled before treating the scheduler as the sole daily orchestration authority.

### 3.3 Date selection

`DailyForwardRunner` selects the latest closed session when no explicit date is supplied, walking back up to fourteen days. Explicit dates are treated as replay/history paths. `PostCloseUpdater` binds a normal run to the market-local date and binds recovery to an explicit date. A recovery run is namespaced as `HISTORY_RECOVERY` and is forbidden from publishing Home.

## 4. Data readiness and reconciliation contract

`DailyMarketReconciliation` is the operative data gate. It distinguishes:

- `expectedCount` from `observedCount`;
- `pricedCount` from `coveredCount`;
- legitimate no-trade/unpriced instruments from unknown missing data;
- provider/pipeline failure from an empty but valid market;
- wrong-date and duplicate stable-key observations.

`downstream_ready` is true only when no blocking reason remains. A legitimate exchange-confirmed no-trade can count as covered without a price. Null close is not silently converted to zero. Unknown or unexplained missing data fails closed.

Current acceptance evidence is therefore:

```text
status = READY
coveredCount = expectedCount
unexplainedMissingCount = 0
downstreamReady = true
```

The field names are present in reconciliation metadata and operations documentation, but they are not yet represented as one dedicated daily publication receipt with a stable external contract.

## 5. Formal Topic, Strength, Lifecycle, and Home behavior

### 5.1 Formal Topic prerequisite

The Topic Snapshot engine first produces provisional output. `materialize_bounded_formal_dates` produces the formal daily state. Formal consumers require a non-superseded snapshot with:

```text
publication_mode = FORMAL
membership_mode = PIT_FORMAL
finality_state = FINAL
publication_state = PUBLISHED
data_status = COMPLETE
```

### 5.2 Independent Strength and Lifecycle lanes

The post-close path invokes `FormalStrengthPublisher` and `FormalLifecyclePublisher` independently after the formal Topic snapshot. A Strength exception is converted to a fail-closed Strength result while Lifecycle still gets its own execution opportunity. Lifecycle uses formal Strength evidence when the Strength row is published; otherwise its own formal evaluation path applies.

Lifecycle unavailable rows preserve the last successful confirmed state in memory and record the observation gap. They do not fabricate a new lifecycle day or advance Day N through missing formal input.

Both formal tables are append-only and correction-aware. They use topic/date/contract/revision identity with supersession and lineage fields. This is stronger than a mutable overwrite contract.

### 5.3 Home V2

Home is materialized by the same post-close run for the current day. Its envelope is publishable when published market facts meet the market minimum; Main Topics and Daily Focus are typed sections and can be independently available or unavailable. A history-recovery run explicitly forbids Home publication.

The overall post-close readback still requires the configured formal chain: Topic, institutional flow, current-day Home where applicable, formal Strength, and formal Lifecycle. Home is not a substitute for formal Topic or Lifecycle evidence.

## 6. Checkpoint, retry, recovery, and single-flight behavior

### 6.1 Durable checkpointing

`live_collector_checkpoints` is an append-only event stream. The uniqueness contract is:

```text
(run_id, batch_key, attempt_number)
```

Each event stores status, counts, stable checkpoint hash, execution scope/key, semantic type, failure classification, and provider metric applicability. Non-provider checkpoints deliberately store provider counters as not applicable rather than zero.

### 6.2 Recovery behavior

- A normal run is keyed by reference version, calendar, date, scope, and full/targeted mode.
- A history recovery uses a separate `history-recovery:` namespace.
- Completed checkpoints may be reused on resume.
- A non-completed provider batch may be reissued after a stale-run resume; duplicate provider points remain possible until downstream idempotency/readback rejects or absorbs them.
- Terminal recovery requires explicit date, reentry contract, idempotency-key continuity, and owner reauthorization for orchestration failures.
- History recovery does not materialize Home.

This is a strong restart contract for the existing run namespace. It is not yet a complete correction/replay taxonomy: there is no first-class `CORRECTION_REPLAY` execution mode with an explicit correction reason, source receipt, and public supersession receipt.

### 6.3 Concurrency matrix

| Scenario | Current behavior | Residual concern |
|---|---|---|
| Two PostgreSQL workers, same date | Transaction advisory lock on reference/calendar/date; second worker sees active run or deterministic existing run | Depends on PostgreSQL; no DB unique key on date alone |
| Scheduler plus manual `--once`, same date | Deterministic execution key and active-run checks prevent duplicate active orchestration | Operator-facing receipt should state which invocation won |
| Normal run plus history recovery, same date | Different namespaces, but active same-date run blocks the other scope | No explicit correction mode; recovery is not a correction contract |
| Worker restart during active run | Recent `RUNNING` run conflicts; stale run can resume in place | Incomplete provider batch can be reissued |
| Completed run rerun | Idempotent result/readback reuse for qualifying normal runs | Reuse evidence is in run metadata, not a standalone publication receipt |
| Non-PostgreSQL local execution | Advisory lock path is not available | Local fallback is not equivalent single-flight protection |

## 7. Receipt and readback forensics

The current receipt is distributed across:

1. `live_collector_runs`: status, counters, provider state, timestamps, config hash, adapter version, metadata.
2. `live_collector_checkpoints`: append-only phase and batch evidence.
3. `live_collector_attempts`: instrument-level attempt and error evidence.
4. `home_publications`: Home envelope, section states, lineage, source run, and publication state.
5. `topic_score_formal_results` and `topic_lifecycle_formal_results`: formal output, contract versions, lineage, and supersession.

This is enough to diagnose many failures, but not enough to claim a single durable daily formal publication receipt. The current run metadata does not normalize all of the following as a first-class receipt contract:

```text
canonical source SHA
deployed API SHA
deployed Worker SHA
Sites parent/source SHA
artifact digest
migration head readback
calendar authority version
publication target/deadline outcome
final readback timestamp and verifier identity
```

The checked-in `production-forensic-readback` workflow is read-only and intentionally limited to selected live collector tables. It is useful forensic evidence, but it is not a complete daily formal publication receipt and does not prove the current runtime.

## 8. `data-status` contract reconciliation

`GET /api/v1/meta/data-status` and `/api/v1/snapshot/latest` call `latest_completed_run`, which selects the latest `IngestionRun` with `status == COMPLETED`. The returned freshness is calculated from the imported enterprise bundle's `data_date` and configured freshness days.

That is a legacy bundle/import-plane contract. It does not read:

- `LiveCollectorRun` post-close status;
- `DailyMarketReconciliation.downstream_ready`;
- formal Topic publication state;
- formal Strength or Lifecycle readback;
- Home V2 publication state.

Therefore a stale or absent legacy bundle can coexist with a successful formal daily post-close run, and a fresh legacy bundle can coexist with an incomplete formal publication. The two planes must not be conflated in the daily publication gate. A future compatibility contract should either expose both planes explicitly or rename the legacy endpoint so its scope is unambiguous.

## 9. Software release state machine

### 9.1 Checked-in release path

`.github/workflows/ci.yml` validates backend, frontend, OpenAPI, compose, and tests on pull requests and pushes to `main`. It is not a production deploy workflow.

`.github/workflows/deploy.yml` is manually dispatched and requires an exact 40-character `release_ref`. It can independently request:

- migration 0048 through protected `production-db-maintenance`;
- Worker deploy through protected `production-worker`;
- API deploy through protected `production-api`;
- Web artifact packaging through protected `production-web`.

Render services have `autoDeployTrigger: off`. The Worker command runs migrations and `topicpilot-live`; the API command runs migrations and Uvicorn. The checked-in blueprint has no approved Cron resource.

### 9.2 Release proof boundary

The workflow proves exact source-ref validation and can build/package artifacts. It does not, in the same workflow, prove:

```text
requested SHA == API runtime SHA
requested SHA == Worker runtime SHA
requested SHA == public Sites deployed source/artifact
migration head == expected head after deploy
public daily readback == formal publication receipt
```

The repository contains capability for API `/healthz` and `/readyz` SHA exposure and `topicpilot-worker-revision --json`. The Worker CLI fails closed when the Render SHA environment is unknown. These are useful readback primitives, but current release automation does not invoke and archive their exact post-deploy comparison.

The Web provenance script can build and verify canonical-main and artifact provenance, including `client/__release.json`, but the checked-in workflow packages the Web artifact and does not itself complete or prove the external Sites promotion.

No rollback job or automatically archived last-known-good runtime receipt was found in the checked-in release workflow.

## 10. Failure and retry matrix

| Failure | Current handling | Terminal/publication meaning |
|---|---|---|
| Weekend/configured closed date | `MARKET_CLOSED`; market reconciliation marked not run | Valid non-publication outcome |
| Reference preflight not ready | Precondition error before run creation or blocked context | No formal publication |
| Provider batch empty/not ready/no data | Whole market batch failure; no per-symbol refetch for market-level failure codes | Collection incomplete; downstream blocked |
| Single-symbol provider error | Savepoint isolation and attempt error | Other symbols may proceed; reconciliation decides |
| Legitimate no-trade | Trading-status authority can mark covered but unpriced | Does not by itself block downstream |
| Unknown missing/status unresolved | Remains unexplained/uncovered | Fails closed |
| Formal Topic unavailable | Strength/Lifecycle wait for formal input | Formal publication incomplete |
| Strength failure | Strength lane fail-closed; Lifecycle gets independent attempt | Overall formal readback may be partial/fail |
| Lifecycle formal-history gap | Publish unavailable row, preserve prior state, no fake Day N | Overall formal readback may be partial |
| Home market facts unavailable | Home unavailable with `NO_PUBLISHED_MARKET_FACTS` | Current-day full chain not complete |
| Checkpoint interruption after durable output | Readback can reuse committed output | Avoids unnecessary writer rerun when all evidence passes |
| Orchestration exception | Run marked failed; reentry requires owner authorization | No automatic terminal recovery authorization |
| Scheduler post-close `PARTIAL`/`FAILED` | Retry on next poll without outer deadline | Indefinite retry risk until process stop or external intervention |
| Runtime SHA unknown | Worker revision CLI fails closed; API reports `UNKNOWN` | Runtime provenance unverified |
| Sites promotion not completed | Artifact may exist without public deployment proof | Web publication unverified |

## 11. Gap classification

The following sixteen findings use the contract's A–P vocabulary. They are forensic findings and implementation requirements for a later governed task; none was implemented here.

| Class | Severity | Evidence and current authority | Required change and dependency | Production impact | Migration? | Owner decision? |
|---|---|---|---|---|---|---|
| `SCHEDULER_GAP` | High | `live/scheduler.py` has a 13:45 threshold and poll retry, but no soft target, hard deadline, missed-window, or deadline-aware terminal state. Authority is the in-process scheduler. | Add explicit timing state and bounded retry/deadline policy. Depends on timing decision and scheduler owner. | Indefinite retry can hide a missed publication SLA. | No, unless receipt fields are added together. | Yes |
| `TRADING_CALENDAR_GAP` | High | Scheduler uses weekend plus `TOPICPILOT_LIVE_CLOSED_DATES`; G2 preflight uses database `TW_MARKET` reference calendar. Authority is split. | Share one canonical calendar decision at scheduler entry. Depends on reference-calendar read access and operator policy. | Holiday/closure may trigger an unnecessary run or wrong date attempt. | Usually no; a new calendar cache/table would require one. | Yes |
| `DATA_READINESS_GAP` | High | Provider readiness is bounded, and `downstream_ready` is a hard gate, but no distinct scheduler-level data-ready wait/deadline state exists. Authority is post-close reconciliation. | Add explicit readiness state, deadline outcome, and operator-visible reason. Depends on provider and timing contracts. | Incomplete data can consume the full window without a clear terminal outcome. | Only if persisted in a receipt. | Yes |
| `CHECKPOINT_RECOVERY_GAP` | Medium | Checkpoints are append-only and resumable, but an unfinished provider batch may be reissued; correction replay is not first-class. Authority is `PostCloseUpdater` reentry. | Add provider idempotency/readback and a correction/replay namespace with reason and supersession. Depends on data lineage contract. | Restart/recovery can create duplicate attempts or ambiguous corrections. | Likely, for correction/receipt lineage. | Yes |
| `SINGLE_FLIGHT_GAP` | Medium | PostgreSQL advisory lock and active-run checks exist; `live_collector_runs` has no date-only unique constraint and non-PostgreSQL fallback is weaker. Authority is PostgreSQL transaction locking. | Decide supported runtime and add DB lease/unique protection if non-PG or stronger guarantees are required. Depends on schema and deployment topology. | Concurrent workers outside the assumed PostgreSQL path may race. | Yes if DB uniqueness/lease is added. | Yes |
| `FORMAL_PUBLICATION_GAP` | High | Formal Topic, Strength, and Lifecycle writers/readbacks exist, but the overall formal outcome is distributed in run metadata and multiple result tables. Authority is `_formal_publication_readback`. | Define one formal publication receipt and public/private readback contract. Depends on receipt schema. | A partial formal chain can be difficult to consume consistently. | Yes |
| `HOME_PUBLICATION_GAP` | Medium | Home V2 has a market-facts gate and typed sections; history recovery forbids Home, but the external daily Home proof is not a separate receipt. Authority is `HomePublication` plus post-close readback. | Expose Home publication/readback as a typed daily component of the receipt. Depends on formal receipt and API policy. | Consumers may not distinguish Home unavailable from the overall run state. | Likely |
| `DATA_STATUS_CONTRACT_GAP` | High | `/api/v1/meta/data-status` reads completed `IngestionRun` bundles, not formal daily Topic/Home results. Authority is the legacy repository read model. | Keep legacy semantics explicit and add a separate formal-publication status contract or versioned response. Depends on client migration. | A fresh bundle can look current while formal publication is incomplete, or vice versa. | No, unless a view/receipt is introduced. | Yes |
| `DAILY_READBACK_GAP` | High | The read-only forensic workflow selects live collector runs/checkpoints/attempts, but does not prove the whole formal chain or current API/Worker/Web runtime. Authority is the checked-in forensic workflow. | Add a non-mutating end-to-end daily readback that consumes the formal receipt. Depends on receipt and runtime access. | Current Production daily status remains unverified. | No, unless receipt storage is added. | Yes |
| `SOFTWARE_RELEASE_GAP` | High | Manual release workflow validates exact ref and can call protected Render hooks, but does not close the loop with API/Worker post-deploy verification or rollback. Authority is `.github/workflows/deploy.yml`. | Add post-deploy verification, failure terminal state, and last-known-good/rollback evidence. Depends on Render/GitHub permissions. | Release success may be reported before runtime correctness is proven. | No |
| `WORKER_RUNTIME_READBACK_GAP` | High | `topicpilot-worker-revision --json` exists and fails closed on unknown SHA, but current deploy automation does not invoke/archive its comparison. Authority is Worker CLI capability. | Run it after deploy, compare with requested SHA, and attach evidence to the release/daily receipt. Depends on Worker endpoint/command access. | Worker may run an unverified revision. | No |
| `WEB_PROVENANCE_GAP` | Medium | Web provenance script verifies canonical source/artifact inputs and embeds `client/__release.json`; current workflow packages but does not prove the public runtime. Authority is build artifact provenance. | Integrate public byte/provenance readback into the promotion workflow. Depends on Sites access and artifact retention. | Public Web may differ from the verified artifact. | No |
| `SITES_AUTOMATION_GAP` | High | The workflow uploads a Web artifact; no checked-in Sites production promotion and current public readback are present. Authority is external Sites handoff. | Define and authorize the Sites promotion boundary and verify the public successor. Depends on Sites owner and credentials. | No checked-in proof that the public site was promoted. | No |
| `RECEIPT_GAP` | High | Evidence is split across run, checkpoint, attempts, Home, Strength, and Lifecycle tables; runtime SHA, migration head, deadline outcome, and verifier identity are not normalized. Authority is distributed persistence. | Add one immutable daily/release receipt with stable identity and lineage. Depends on schema and readback API design. | Audit/recovery requires joining multiple planes and can miss a close-loop fact. | Yes |
| `NOTIFICATION_GAP` | Medium | No checked-in formal notification/outbox/escalation contract was found for deadline miss, partial formal output, or required owner reentry. Authority is currently logs and operator inspection. | Define quiet-success and actionable-failure notification policy, preferably through an outbox/readback-safe path. Depends on channel owner and receipt states. | Operators may not know that publication needs intervention. | Yes |
| `DOCUMENTATION_ONLY_GAP` | Low | Current code defaults to 13:45; historical closure material contains a prior 15:00 schedule. Authority is current code, but documentation is inconsistent. | Reconcile docs after the timing decision; do not use docs to silently activate a schedule. Depends on G01 owner decision. | Conflicting operator expectations can cause timing mistakes. | Yes |

## 12. Reconciled target contract

The following target contract is a mapping proposal, not current implementation. It preserves current canonical statuses where they exist and adds only the missing orchestration semantics.

### 12.1 Target state machine A — daily formal publication

```text
NOT_REQUIRED
  -> WAITING_FOR_ELIGIBILITY
  -> WAITING_FOR_MARKET_DATA
  -> COLLECTING
  -> RECONCILING
  -> READY_FOR_FORMAL_PUBLICATION
  -> PUBLISHING
  -> VERIFYING
  -> SUCCESS

Any active state may terminate as:
  PARTIAL
  FAILED
  MANUAL_INTERVENTION_REQUIRED
```

Mapping to current main:

| Target state | Current authority/status |
|---|---|
| `NOT_REQUIRED` | `MARKET_CLOSED` or non-session preflight outcome |
| `WAITING_FOR_ELIGIBILITY` | G2 reference/preflight not ready |
| `WAITING_FOR_MARKET_DATA` | Provider readiness, missing data, or `downstream_ready == false` |
| `COLLECTING` | Provider checkpoint `IN_PROGRESS` |
| `RECONCILING` | `DailyMarketReconciliation` |
| `READY_FOR_FORMAL_PUBLICATION` | Reconciliation ready and formal inputs available |
| `PUBLISHING` | Formal Topic, Strength, Lifecycle, and Home writers |
| `VERIFYING` | `_formal_publication_readback` and future receipt readback |
| `SUCCESS` | Current run `SUCCESS` plus downstream-ready and formal chain ready |
| `PARTIAL` | Current run `PARTIAL` or overall readback `PARTIAL` |
| `FAILED` | Current run `FAILED` or failed formal readback |
| `MANUAL_INTERVENTION_REQUIRED` | Owner reentry required, deadline miss, or unrecoverable receipt/provenance mismatch |

Required target fields are: market-local trading date, reference/calendar identity, execution scope, run and receipt IDs, expected/observed/priced/covered/unexplained counts, provider and formal phase outcomes, Topic/Strength/Lifecycle/Home readback, deadline outcome, runtime provenance, migration head, last-known-good pointer, and verifier timestamp.

### 12.2 Target state machine B — software release

```text
RELEASE_REQUESTED
  -> PREFLIGHT
  -> DEPLOYING_API and/or DEPLOYING_WORKER
  -> VERIFYING_RUNTIME
  -> BUILDING_WEB
  -> VERIFYING_ARTIFACT
  -> PROMOTING_SITES
  -> POST_DEPLOY_VERIFY
  -> SUCCESS

Any release state may terminate as FAILED,
with a last-known-good release retained for rollback.
```

Current mapping: exact-ref validation is `PREFLIGHT`; Render hooks are deployment capability; Web artifact packaging is `BUILDING_WEB`/partial `VERIFYING_ARTIFACT`; API/Worker SHA endpoints are readback primitives; Sites promotion and complete `POST_DEPLOY_VERIFY` are outside the checked-in workflow. Daily data publication must remain a separate state machine from software release.

## 13. Current readiness verdict

| Capability | Verdict | Reason |
|---|---|---|
| Code-level daily post-close chain | `READY_WITH_GAPS` | End-to-end phases, gates, checkpoints, recovery, and readback are implemented and tested |
| Formal Topic/Strength/Lifecycle semantics | `READY_WITH_GAPS` | Independent lanes, fail-closed behavior, append-only lineage, and no-fake-Day-N policy exist |
| Home V2 integration | `READY_WITH_GAPS` | Current-day typed envelope exists; history recovery is correctly Home-forbidden |
| Scheduler as Production authority | `NOT_PROVEN` | No approved Cron in Render blueprint; activation/provisioning not evidenced |
| Current daily Production publication | `UNVERIFIED` | No current runtime/readback receipt was executed or supplied |
| Software release automation | `PARTIAL` | Exact-ref validation and protected hooks exist; runtime/Web/rollback close loop is incomplete |
| `data-status` as formal daily gate | `NOT_EQUIVALENT` | It remains an imported-bundle read model |

## 14. Owner decisions required before implementation

1. Confirm the formal timing contract: retain 13:45 start, or define 14:30/15:00 target/deadline behavior and the missed-window state.
2. Choose the Production scheduler authority and provision it only in a separately authorized activation task.
3. Make the database reference calendar the scheduler's date authority, or explicitly accept and operate the environment closed-date mirror.
4. Approve the single daily publication receipt schema and its public/private readback boundary.
5. Decide whether `data-status` should remain legacy-only or expose a separate formal-publication status contract.
6. Define correction/replay semantics, supersession visibility, and owner authorization.
7. Require API, Worker, migration, and Sites provenance readback in the release close loop.
8. Approve rollback and last-known-good receipt retention.

## 15. Minimal implementation sequence after approval

This is a future plan only; no item below was implemented in this task.

1. Freeze the timing, calendar, receipt, and correction contracts.
2. Add one scheduler-facing canonical session decision using the reference calendar and explicit deadline outcomes.
3. Add a dedicated daily publication receipt, with unique execution identity, phase outcomes, reconciliation counts, formal readback, runtime provenance, migration head, and verifier timestamp.
4. Add read-only daily receipt API/readback and extend the forensic workflow to collect it without mutation.
5. Add post-deploy API/Worker/migration exact-SHA verification and archive the evidence.
6. Complete Web/Sites promotion provenance and rollback/last-known-good handling.
7. Add correction/replay tests, multi-worker tests, deadline tests, calendar mismatch tests, and receipt continuity tests.
8. Run a separately authorized staging/Production activation task. Do not combine activation with forensic reconciliation.

## Validation performed

Focused local validation used Python 3.12, the repository-required runtime:

```text
151 passed in 8.28s
```

Covered suites included scheduler runtime, post-close contract, final-publication contract, checkpoint canonicalization, Home V2 publication/status/receipt, formal Strength/Lifecycle chain, Worker revision readback, release provenance, and market-calendar remediation. PostgreSQL integration tests requiring an explicit isolated database were not used as Production evidence.

`py -3.12 -m alembic heads` returned:

```text
0048_task_checkpoint_provider_metric_applicability (head)
```

No migration, deployment, Production endpoint, scheduler activation, retry, or GitHub write operation was executed.

## Task closure manifest

```text
TASK_TYPE=FORENSIC
REQUIRED_TERMINAL_STATE=REPORT_CREATED_NO_ACTIVATION
ACHIEVED_TERMINAL_STATE=REPORT_CREATED_NO_ACTIVATION
TASK_COMPLETE=true
FOLLOW_UP_REQUIRED=true
FOLLOW_UP_REASON=Owner decisions and a separately authorized implementation/activation task are required for the sixteen classified gap findings.
GAP_COUNT=16
CURRENT_MAIN=a687c748e1b7d512449b69884626c58ac7d86d12
REPORT_PATH=docs/reports/TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-FORENSIC-001.md
PRODUCTION_MUTATION=NOT_EXECUTED
PUSH_OR_MERGE=NOT_EXECUTED
NEXT_TASK_RECOMMENDATION=TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-IMPLEMENTATION-001
```
