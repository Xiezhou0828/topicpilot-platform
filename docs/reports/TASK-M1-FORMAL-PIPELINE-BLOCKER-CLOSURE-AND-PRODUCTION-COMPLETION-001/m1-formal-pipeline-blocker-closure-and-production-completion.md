# M1 Formal Pipeline Blocker Closure and Production Completion

Task: `TASK-M1-FORMAL-PIPELINE-BLOCKER-CLOSURE-AND-PRODUCTION-COMPLETION-001`  
Roadmap: `TOPICPILOT_DEVELOPMENT_ROADMAP_V1.0_FROZEN`  
Milestone: `M1_FORMAL_POST_CLOSE_PIPELINE`  
Execution date: `2026-09-18` (Asia/Taipei)

## Executive result

Result: `BLOCKED`.

Authoritative continuation closeout: the M1 recovery entrypoint and scheduled Worker execution-mode defects were fixed and deployed. The owner-supplied `TWO:8277` lifecycle evidence was independently verified against the official TPEx bulletin, registered through the governed reference bundle, and activated in Production. M1 remains blocked by the unreplayed required historical sessions and the formal Opportunity provider/policy gate; `TWO:8277` is now handled as a date-effective lifecycle exclusion rather than an unresolved reference mismatch.

The governed release was reconstructed from `origin/main` without carrying the
historical 6.4 GiB LFS artifact set, pushed successfully, and deployed to the
Production API and Worker at exact SHA
`b14d5708d4cda0cad2341154bc4495b64cf472ec`. The Production API is healthy,
the Worker runtime SHA was read back from a new live run, and the database
read-only probe reports the single Alembic head
`0042_task_fund_b_stock_institutional_flow_forward`.

The earlier technical-access stop was cleared: the protected
`production-worker` environment secret was verified by name only, and the
exact-SHA Worker deployment and runtime readback completed. The formal
Opportunity provider also remains correctly unavailable: the repository
contains a consumer boundary, but the current PM specification leaves the
numeric Opportunity policy open and no approved canonical provider/Leader Set
publication artifact exists. Shadow output was not promoted.

The historical first unsafe boundary was the superseded Production provider
canary. The governed POST_CLOSE run for `2026-09-18` initially failed before
any formal recovery could be trusted: 553 requested, 0 succeeded, 553 failed.
The recovery-routing and scheduled execution-mode defects were then fixed, the
reference lifecycle evidence was activated, and the authorized continuation
completed the target session with an isolated legal no-trade outcome for
`TWO:8277`. Historical replay is now proceeding sequentially from
`2026-09-10`; no failed provider output was promoted.

## Protected Owner checkout

| Check | Before | After | Result |
|---|---|---|---|
| C Owner HEAD | `02d3086183d1c582bb6c66c4c316340ccce3fa97` | same | unchanged |
| C Owner dirty-file count | `153` | `153` | unchanged |
| C Owner mutation | none | none | protected checkout preserved |

All work was performed in `D:\topicpilot-m1-clean-release-20260918`.

## Blocker closure table

| Blocker | Starting status | Root cause | Action taken | Final status | Evidence | Still blocking M1? |
|---|---|---|---|---|---|---|
| A Runtime provenance | API known; Worker/Web/DB incomplete | Worker had no exact runtime readback; DB was last proven at 0040 | Added bounded Worker runtime provenance; deployed API and Worker at `b14d5708…`; read health, live-run SHA, and migration probe | Exact API/Worker deployment proven; the failed POST_CLOSE row itself lacks the field because its separate PostClose persistence path does not yet attach it; Web remains package-only | `/readyz` returns `b14d5708…`; new intraday run `cbd2a804…` returns `runtimeGitSha=b14d5708…`; migration returns `0042…` | No; canary failure is earlier |
| B Git delivery / 6.4 GiB history | Full recovery push rejected | Historical LFS pointer to a 6,726,285,286-byte generated CSV introduced by `79229bcc…`, plus other historical report blobs | Built a clean forward composition from `origin/main` `b2eaf33…`; applied required Daily Close lineage and consumer changes; excluded unrelated top-level report history; no deletion or history rewrite | Closed for release | Push of `codex/task-m1-formal-pipeline-clean-release-20260918` succeeded; clean release has no LFS files | No |
| C Production technical access | Partial/uncertain | GitHub API deploy path available; Worker hook was initially absent | Verified the protected Worker secret name without reading its value; deployed API and Worker at exact SHA; migration and health readback completed | Available for deployment; provider canary is the stop | Workflow `35307215356`: validation, API hook, and Worker hook pass | No |
| D Formal policy/provider authority | Reported unresolved | Layer2 Score/Grade authority is approved, but Daily Strength is partial-by-design, transition provenance is partial, and Opportunity numeric rules/Leader Set publication are not formally approved | Recovered and used existing authority records; kept formal provider fail-closed; did not promote shadow or invent thresholds | Partial; provider not ready | B2 authority records; `TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md`; formal API returns 503 | Downstream of C; remains fail-closed |
| E Historical recovery | Not executed | First governed POST_CLOSE provider canary failed on 2026-09-18 | Stopped before replay; did not fabricate formal dates 2026-09-10..17 | Blocked / not proven | POST_CLOSE run `4e745108…`; 0/29 batches completed; required-session table below | Yes, downstream |
| F Downstream publication/readback | Formal Opportunity API was 404 before release | Provider boundary was absent from deployed API and has no approved canonical implementation | Deployed release; formal route is now present and returns truthful 503 unavailable | Formal API boundary deployed; publication not ready | `/api/v2/opportunities` returns 503 with canonical-provider-unavailable problem; shadow remains separate | Yes, downstream |

## Release composition and lineage

| Field | Value |
|---|---|
| `SOURCE_BASE` | `origin/main` at `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| `DAILY_CLOSE_SOURCE` | logical required tree from `969bf12a3a12a9a5c9799c66b74995dd69974c29` |
| `OPPORTUNITY_CONSUMER_SOURCE` | `3b58908be864fff8bc4fa2fa4671c28fffda37f9` |
| `FORMAL_PROVIDER_SOURCE` | no approved canonical provider; fail-closed boundary retained |
| `FINAL_RELEASE_SHA` | `45b1fa198db34471ce03f29a9184d8236299d525` |
| `REMOTE_BRANCH` | `origin/codex/task-m1-formal-pipeline-clean-release-20260918` |
| `PUSH_STATUS` | `PASS` |
| `TREE_EQUIVALENCE` | `YES` for required application files; forward-composed from a clean reachable base |
| `GIANT_ARTIFACTS_REQUIRED` | `NO` |
| `HISTORY_REWRITE_PERFORMED` | `NO` |
| `PRODUCTION_WORKFLOW_RUN` | `35332835125` (Worker continuation; prior API/Worker release `35327998794`) |

The dominant rejected object is the Git LFS pointer for
`reports/TASK-WS2-E1-603-UNIVERSE-TECHNICAL-V0-EXPANDED-QUALIFICATION-RESUME-AFTER-SOURCE-CONTRACT-UNBLOCK-20260820/ws2-e1-resume-full-historical-formal-evidence-surface.csv`.
Its LFS object is 6,726,285,286 bytes and was introduced by
`79229bccf5ab7b3dad8921ef71e6113ff29360cf`. It is a generated historical
research artifact, not a runtime source dependency. The clean release contains
no LFS-tracked files and was accepted by GitHub.

Relevant lineage remains distinguishable:

- `969bf12…`: local Daily Close recovery final evidence; not the remote main tip.
- `3b58908…`: formal Opportunity topic-universe consumer implementation.
- `0e42965…`: pushed thin consumer handoff branch tip.
- `3a51922…`: prior recovery branch push-boundary report; full branch remained too large.
- `99a5a52…`: pushed clean deployable composition and exact Production API target.

## Production provenance

| Field | Before | After |
|---|---|---|
| API SHA | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` | `b14d5708d4cda0cad2341154bc4495b64cf472ec` |
| Worker SHA | `UNPROVABLE` | `b14d5708d4cda0cad2341154bc4495b64cf472ec` |
| Web SHA | `UNPROVABLE` | `UNPROVABLE_PACKAGE_ONLY` |
| DB revision | `0040_task_a10_recovery_checkpoint_observability` (last governed evidence) | `0042_task_fund_b_stock_institutional_flow_forward` |
| Deployment ID | prior Render deployment not exposed | GitHub workflow `35307215356`; Render deployment ID not exposed |
| Deployment time | not available | API hook accepted 2026-09-18; exact Render timestamp not exposed |
| Health | `/readyz` and `/healthz` ready/ok at old SHA | `/readyz` and `/healthz` ready/ok at `b14d5708…` |
| Scheduler | configured POST_CLOSE `13:35` Asia/Taipei; poll `300s`; runtime Worker unproven | same configuration; Worker runtime SHA proven from live run `cbd2a804…` |

The API Render command runs `alembic upgrade head` before Uvicorn. The
post-deployment read-only probe at `/api/v1/admin/migration` returned HTTP 200
with `{"alembicRevision":"0042_task_fund_b_stock_institutional_flow_forward","readOnly":true}`.
No direct migration credential or secret value was exposed.

### Provider canary stop

The first eligible POST_CLOSE run was:

| Field | Value |
|---|---|
| Run ID | `4e745108-1e0b-416f-9c49-dfc2a626ced5` |
| Run date | `2026-09-18` |
| Requested | `553` |
| Succeeded / failed | `0 / 553` |
| Failure code | `EMPTY_RESPONSE` |
| Failure message | `EMPTY_RESPONSE;EXCHANGE_NO_DATA;MARKET_PROVIDER_UNAVAILABLE` |
| TPE | `347` `EXCHANGE_NO_DATA` |
| TWO | `206` `EMPTY_RESPONSE` |
| Checkpoint | `FAILED`, `0/29` batches completed |
| Safe continuation | `STOPPED` |

This was an unsafe provider canary failure, not a valid zero-candidate result
and not a formal historical session. The original continuation stopped at this
historical boundary; the current exact-date recheck is recorded below.

### Historical read-only provider root-cause diagnosis (superseded)

The following diagnosis records the earlier bounded probe and is retained for
auditability. Its 2026-09-18 TWO row count of zero is superseded by the fresh
official-source recheck below; it must not be used as current production truth.

Before any code or deployment change, the same official market-level endpoints
used by the deployed adapters were probed independently for the known-good
2026-09-17 control and the failed 2026-09-18 date. The probes were bounded to
one request per market/date and retained only safe response metadata:

| Date | Market | Official request contract | HTTP / stat | Response date | Market rows | Adapter conclusion |
|---|---|---|---|---|---:|---|
| 2026-09-17 | TPE | TWSE `MI_INDEX`, `YYYYMMDD` | 200 / `OK` | `20260917` | 1,377 | available |
| 2026-09-17 | TWO | TPEx `dailyQuotes`, `YYYY/MM/DD` | 200 / `ok` | `20260917` | 11,479 | available |
| 2026-09-18 | TPE | TWSE `MI_INDEX`, `YYYYMMDD` | 200 / `OK` | `20260918` | 1,377 | available; parser-compatible |
| 2026-09-18 | TWO | TPEx `dailyQuotes`, `YYYY/MM/DD` | 200 / `ok` | `20260918` | 0 | unsafe unavailable market payload |

The historical 2026-09-18 TPE response contained the expected `證券代號`
table. The historical 2026-09-18 TWO response was valid JSON with the expected
`上櫃股票行情` table, but that earlier probe recorded zero rows. The requested
and returned dates matched, and 2026-09-18 is a Friday. This historical result
was conservatively treated as unavailable at the time and is retained only as
the reason the first Production canary stopped.

The original Production TPE `EXCHANGE_NO_DATA` response body and safe
provider metadata were not persisted by the failed run, so the historical
TPE failure cannot be distinguished after the fact between a transient
official-source no-data response and another first-failing provider condition.
The current TPE success did not justify replaying the full canary at that
time. The historical TWO result likewise remained a fail-closed stop. No
provider, parser, date, filter, or policy change was evidence-backed; none was
made.

The exact Web SHA remains unproven because the workflow successfully packaged
the exact release artifact but does not publish it to the Sites host. The
public Web root is healthy and points at the configured API, but exposes no
release SHA.

### Current truth recheck — 2026-09-18

At `2026-09-18T15:39:28+08:00`, a new read-only request was made directly to
the official TPE/TWO market-level endpoints for the exact target date
`2026-09-18`. No fallback date, D-1/D+1 substitution, database write, code
change, deployment, or replay was performed.

| Market | Official endpoint contract | HTTP / stat | Response date | Market rows | Current classification |
|---|---|---|---|---:|---|
| TPE | TWSE `MI_INDEX`, `YYYYMMDD` | 200 / `OK` | `20260918` | 1,377 | `AVAILABLE` |
| TWO | TPEx `dailyQuotes`, `YYYY/MM/DD` | 200 / `ok` | `20260918` | 11,481 | `AVAILABLE` |

The previous `TWO=0` diagnosis is therefore superseded. The response dates
match the requested date and both payloads are compatible with the canonical
adapters. The canonical provider classes were then exercised in a bounded,
read-only canary: TPE representative `2330` (1/1), TWO representative `6488`
(1/1), mixed TPE `2330,2317` (2/2), and mixed TWO `6488,5274` (2/2). All
requested bars succeeded, all source and normalized dates were
`2026-09-18`, and stale/look-ahead violations were zero.

| Bounded provider canary | Result |
|---|---|
| `TPE_PROVIDER_CANARY` | `PASS_READ_ONLY_BOUNDED` |
| `TWO_PROVIDER_CANARY` | `PASS_READ_ONLY_BOUNDED` |
| `PRODUCTION_POST_CLOSE_CANARY` | `FAIL` |
| Stale fallback violations | `0` |
| Look-ahead violations | `0` |

The current Production read-only reference readback reports 556 instruments,
555 active instruments, 348 active TPE instruments, 207 active TWO
instruments, and 555 formal stock items. The earlier failed POST_CLOSE
requested 553 (`347` TPE and `206` TWO); that is retained as a historical
date-effective run count and is not silently reinterpreted as the current
physical reference total.

### Historical pre-remediation Production stop boundary

This subsection records the original stop exactly as observed; it is
superseded by the authoritative continuation closeout immediately below.

The Production one-shot POST_CLOSE recovery was executed exactly once through
the authenticated Render Worker Shell with:

`topicpilot-live --mode post-close --once --run-date 2026-09-18 --recover`

The command completed with `FAILED`: `553` requested, `0` succeeded, `553`
failed, failure codes `EMPTY_RESPONSE`, `EXCHANGE_NO_DATA`, and
`MARKET_PROVIDER_UNAVAILABLE`; checkpoint `FAILED`, `0/29` batches completed,
and `snapshotStatus=BLOCKED_DAILY_MARKET_NOT_READY`. The persisted run ID is
`4e745108-1e0b-416f-9c49-dfc2a626ced5`; the recovery reused that terminal run
record rather than creating a second competing run. The Worker output proved
runtime SHA `b14d5708d4cda0cad2341154bc4495b64cf472ec` and the runtime
reference version was `tw-reference-v1-rollover-dd2c70fbfea8e400`.

This is now a Production provider/runtime failure, not an authentication
boundary. No second retry, historical replay, Daily Close, Topic publication,
or formal Opportunity evaluation was attempted.

Until the Production provider/runtime failure is separately remediated and
re-authorized, historical replay, Daily Close, Topic publication, and formal
Opportunity evaluation remain blocked. No code, deployment, migration, or
historical replay was performed in this continuation.

## Authoritative continuation closeout

The earlier stop-boundary narrative above is retained as historical evidence;
the following is authoritative for this continuation.

### Root-cause and path differential

- `ROOT_CAUSE_STATUS=PROVEN`.
- `ROOT_CAUSE_LAYER=CLI_ENTRYPOINT_RECOVERY_ROUTING`.
- Proven root cause: the CLI created the explicit `--recover` closure but
  passed the ordinary daily-forward closure to `LiveScheduler`; the authorized
  recovery therefore reused the old terminal failure instead of executing a
  fresh provider-backed recovery.
- The bounded canonical path and the Production recovery path used the same
  official TPE/TPEx adapter registry, exact target date, market-batch mode,
  headers/base URLs, and `RateLimitedTransport` after the fix. Production
  alone used the rollover reference version and persisted DB universe.
- A separate scheduled-path defect was proven after recovery: the CLI passed
  `execution_mode` to `DailyForwardRunner.run_once`, whose signature omitted
  it. Commit `45b1fa1…` fixed the interface and forwarded the value to the
  post-close updater. The new Worker logged scheduled completion without the
  former `TypeError`.

### Remediation and runtime evidence

| Item | Evidence | Result |
|---|---|---|
| Recovery routing fix | `b87781a6c928a3a8749d76374d369da4f0017b7f`; workflow `35327998794` | deployed |
| Scheduled execution-mode fix | `45b1fa198db34471ce03f29a9184d8236299d525`; workflow `35332835125`; Render `dep-damgpi2jnfac738m5jl0` | deployed |
| Exact runtime Worker | instance `5nxl6`, runtime SHA `45b1fa198db34471ce03f29a9184d8236299d525` | proven |
| Post-fix TPE runtime canary | exact `2026-09-18`, 1,377 rows, stale/look-ahead 0 | PASS |
| Post-fix TWO runtime canary | exact `2026-09-18`, 11,481 rows, stale/look-ahead 0 | PASS |
| Scheduled Worker readback | `post_close_scheduled_complete`, `executionMode=SCHEDULED`, `status=SUCCESS` | PASS |

### One authorized Production recovery

Command, executed once after both runtime canaries passed:

`topicpilot-live --mode post-close --once --run-date 2026-09-18 --recover`

| Field | Readback |
|---|---|
| Run ID | `2b5f8547-70a7-4783-a2dd-5729cb4799ac` |
| Runtime SHA | `b87781a6c928a3a8749d76374d369da4f0017b7f` for the full recovery; scheduled Worker subsequently verified at `45b1fa1…` |
| Requested / succeeded / failed / skipped | `553 / 552 / 0 / 1` |
| Retries | `0` |
| Checkpoint | `COMPLETED`, `29/29` |
| Provider / freshness | `AVAILABLE / FRESH` |
| Failure code | `UNAVAILABLE_DAILY_CLOSE` / `ISOLATED_UNAVAILABLE_COVERAGE` |
| Isolated provider outcome | `TWO:8277`, `MISSING_MARKET_DATA`, `OFFICIAL_NO_ROW` |
| Historical replay | `NOT_EXECUTED` |

The official exact-date TWO response had 11,481 rows but did not contain the
active reference identity `8277`; the TPEx management table did not contain it
either. The reference row was not deleted, filtered, or fabricated. The one
missing identity is therefore the earliest remaining technical blocker:
`TWO_REFERENCE_COVERAGE_MISMATCH_8277` at the production reference/provider
coverage layer. No second full recovery was run.

### Current publication readback

`/api/v2/home` is `PUBLISHED` for `2026-09-18`, with `sourceRunId` equal to
`2b5f8547-70a7-4783-a2dd-5729cb4799ac`; `marketOverview` and `mainTopics` are
available. Optional `opportunities` remains `UNAVAILABLE` with
`OPTIONAL_SECTION_NOT_FORMAL`, and the required historical session table below
remains `NOT_PROVEN`.

## Required historical recovery table

These are the actual trading dates between 2026-09-10 and 2026-09-17. No date
was marked formal merely because source rows were retrievable. The previous
read-only 2026-09-17 source check (TPE 1,377 rows; TWO 11,479 rows) proves
retrievability only, not original-runtime provider health or formal publication.

| Date | Daily Close | Today Market | A9 | Strength | Score | Grade | Lifecycle | Topic publication | Opportunity | Readback |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-10 | PASS | READY | NOT_PROVEN | NOT_PROVEN | DEFERRED | NOT_PROVEN | UNAVAILABLE (registered Lifecycle `TypeError`) | PASS | UNAVAILABLE | recovery `2e05c3fe-8174-47df-a371-1143bf32140c`; 553/553 attempts; EOD/topic readback and publication PASS |
| 2026-09-11 | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | STOP REQUESTED | UNAVAILABLE | recovery `c73eeeb7-9e2f-49ad-9701-fd237a6c7ee2`; canonical supersession conflict on TPE 2049 and 2308 (`PRICE`,`VOLUME`); DB row retained RUNNING with heartbeat unchanged; no cross-date continuation |
| 2026-09-14 | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no recovered formal snapshot |
| 2026-09-15 | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no recovered formal snapshot |
| 2026-09-16 | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no recovered formal snapshot |
| 2026-09-17 | SOURCE_RETRIEVABLE_ONLY | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no original-runtime or persisted formal readback |

The latest successfully read formal Topic catalog is dated `2026-09-09` and
returns 87 items. Production Home also reports `asOf=2026-09-09`. This is not
a substitute for the required 2026-09-10..17 recovery.

## Opportunity funnel

| Stage | Entity type | Input count | Output count | Status | Reason |
|---|---|---:|---:|---|---|
| Formal Topic catalog | Topics | — | 87 | READBACK | `/api/v2/topics` total and items both 87; data date 2026-09-09 |
| Formally published Topic snapshots for required recovery dates | Topics | 6 dates | NOT_PROVEN | BLOCKED | historical recovery not run |
| Opportunity-eligible Topics | Topics | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no approved canonical Opportunity eligibility policy/provider |
| Approved Topic-stock relations | relations | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no recovered eligible universe |
| Role-eligible relations | relations | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no formal Leader Set publication |
| Unique stocks | stocks | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no complete formal universe |
| Price-available stocks | stocks | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no complete formal evaluation |
| Strategy input | stocks | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | provider unavailable |
| Selector input | stocks | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | provider unavailable |
| C1, C2, C3, C4, C5 | candidates | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no complete formal evaluation; filters unchanged |
| S1, S2 | candidates | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | no complete formal evaluation; filters unchanged |
| Final candidates | candidates | NOT_PROVEN | NOT_PROVEN | UNAVAILABLE | do not report ZERO without a complete evaluation |

`MLCC_IS_ONE_TOPIC=YES`; `MLCC_GLOBAL_GATE=NO`; non-MLCC Topics were not
automatically excluded. `ZERO` was not used; the honest state is
`UNAVAILABLE/NOT_PROVEN`.

## Policy authority matrix

| Policy | Formal authority source | Shadow source, if any | Consumer behavior | Status |
|---|---|---|---|---|
| Topic eligibility | Layer2 formal authority records and Topic daily contracts | research/topic-universe mapping | consumer may read only formal enabled/effective Topics | FORMAL READ MODEL; historical dates not recovered |
| Daily Strength | B2 approval record; explicitly `PARTIAL_BY_DESIGN`, fail-closed | Topic engine shadow/derived evidence | must not supply a formal Opportunity decision when incomplete | PARTIAL |
| Score | approved Score/Grade policy record and Topic Score formal module | prior shadow/research diagnostics | may be consumed only with formal daily lineage | APPROVED_CALCULATION; publication/readback incomplete |
| Grade | approved Score/Grade policy record | prior shadow/research diagnostics | may be consumed only as backend-owned formal state | APPROVED_CALCULATION; publication/readback incomplete |
| Lifecycle | frozen five-stage Lifecycle contract; independent from Score/Grade and Daily Strength | lifecycle engine tests/legacy diagnostics | no stage may be inferred by Opportunity | APPROVED_SEMANTICS; transition provenance/publication incomplete |
| Structural Role | structural-role authority module/contract | research leader-set material | only formal role rows may be consumed | PARTIAL / no full production readback |
| Leader Set | no approved formal production artifact | `docs/research/leader-set-research.v*.md` | no formal Leader Set consumption | MISSING_FORMAL_ARTIFACT |
| Strategy | Opportunity product specification only; numeric parameters provisional | `opportunity_strategies.py` | not promoted to formal provider | SHADOW_ONLY / PROVISIONAL |
| Selector | no approved numeric production policy | shadow Opportunity read model | not promoted | SHADOW_ONLY / PROVISIONAL |
| C1-C5 | existing frozen technical/read contracts | research diagnostics | unchanged; no tuning | FROZEN, NOT EXECUTED |
| S1-S2 | existing frozen strategy/selection contracts | research diagnostics | unchanged; no tuning | FROZEN, NOT EXECUTED |
| FUND-C | canonical evidence-enrichment contract | current-snapshot evidence adapters | eligibility, ranking, and final selection effects all none | FORMAL EVIDENCE-ONLY |

The current Opportunity specification explicitly leaves grade/lifecycle
qualification, technical thresholds, weights, transition mechanics, and
publication authorization open. The implementation constants identify their
numeric status as `PROVISIONAL_TUNABLE_VERSIONED`. The formal API therefore
rejects a shadow provider and returns truthful 503 rather than manufacturing a
formal Opportunity result.

## Validation summary

| Area | Result |
|---|---|
| Focused Daily Close / post-close / exchange recovery | 64 passed in the combined focused command |
| Focused Topic / formal universe | included in the 64-pass focused command |
| Focused Lifecycle | registered baseline failures remain; no new task-caused failure |
| Focused Opportunity / formal API | included in the 64-pass focused command |
| FUND-C non-interference | verified by existing focused contract coverage; no Opportunity effect |
| Backend full | 784 passed, 59 skipped, 9 registered Lifecycle baseline failures |
| API client / generated contract | Web/API contract suites pass |
| Web tests | 165 passed, 0 failed |
| OpenAPI | local validation passed; production OpenAPI has shadow paths before formal provider and formal path after API deployment |
| Build | Web build passed locally and in workflow |
| Lint | ESLint passed with 2 existing warnings, 0 errors |
| Ruff | repository-wide run reports 750 pre-existing research-file findings; no unrelated cleanup was performed |
| Compile | Python compileall passed before final report composition |
| Alembic | one head `0042…`; two known branchpoints are historical migration graph structure, not multiple heads |
| Workflow | validation pass; API deploy pass; Web package pass; Worker deploy fails at missing environment hook |
| Production API | `/readyz` and `/healthz` HTTP 200 at exact target SHA; migration probe HTTP 200 at 0042 |
| Formal Opportunity API | HTTP 503 unavailable with canonical-provider-unavailable problem; fail-closed behavior verified |

The nine backend failures are the same registered Lifecycle baseline class
already accepted in the prior recovery evidence (frozen-stage expectation,
candidate stage expectations, re-entry reset, trading-day arithmetic, and
adjacent-stage enforcement). Environment skips are PostgreSQL/integration
tests without `TEST_DATABASE_URL`/`DATABASE_URL`. No task-caused or unknown
failure was observed.

## Final machine-readable summary

```text
TASK: TASK-M1-FORMAL-PIPELINE-BLOCKER-CLOSURE-AND-PRODUCTION-COMPLETION-001
ROADMAP: TOPICPILOT_DEVELOPMENT_ROADMAP_V1.0_FROZEN
MILESTONE: M1_FORMAL_POST_CLOSE_PIPELINE
RESULT: BLOCKED
FURTHEST_SAFE_AUTHORIZED_STATE: exact-SHA API and Worker deployed with runtime SHA readback, DB at Alembic 0042, official 2026-09-18 TPE/TWO sources available, bounded read-only provider canaries PASS, one Production POST_CLOSE recovery executed and stopped on runtime provider failure
OWNER_AUTHORIZATION: GRANTED
TECHNICAL_ACCESS: PARTIAL
CURRENT_CANONICAL_SHA: 45b1fa198db34471ce03f29a9184d8236299d525
FINAL_RELEASE_SHA: 45b1fa198db34471ce03f29a9184d8236299d525
RELEASE_BRANCH: codex/task-m1-formal-pipeline-clean-release-20260918
RELEASE_PUSH: PASS
GIT_6_4_GIB_ROOT_CAUSE: reachable historical Git LFS/generated research artifact introduced by 79229bccf5ab7b3dad8921ef71e6113ff29360cf; not runtime source
GIANT_ARTIFACTS_REQUIRED_FOR_RELEASE: NO
SHARED_HISTORY_REWRITTEN: NO
OPPORTUNITY_CONSUMER_INTEGRATED: YES
CANONICAL_OPPORTUNITY_PROVIDER: NOT_READY
FORMAL_PROVIDER_AUTHORITY: PARTIAL
PRODUCTION_API_SHA_BEFORE: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
PRODUCTION_WORKER_SHA_BEFORE: UNPROVABLE
PRODUCTION_WEB_SHA_BEFORE: UNPROVABLE
PRODUCTION_DB_REVISION_BEFORE: 0040_task_a10_recovery_checkpoint_observability
PRODUCTION_API_SHA_AFTER: b14d5708d4cda0cad2341154bc4495b64cf472ec
PRODUCTION_WORKER_SHA_AFTER: 45b1fa198db34471ce03f29a9184d8236299d525
PRODUCTION_WEB_SHA_AFTER: UNPROVABLE_PACKAGE_ONLY
PRODUCTION_DB_REVISION_AFTER: 0042_task_fund_b_stock_institutional_flow_forward
EXACT_SHA_API_PROVEN: YES
EXACT_SHA_WORKER_PROVEN: YES
DB_REVISION_PROVEN: YES
MIGRATION_REQUIRED: YES
MIGRATION_EXECUTED: YES
MIGRATION_STATUS: PASS
TPE_PROVIDER_CANARY: PASS_READ_ONLY_BOUNDED
TWO_PROVIDER_CANARY: PASS_READ_ONLY_BOUNDED
PRODUCTION_POST_CLOSE_CANARY: FAIL
DAILY_CLOSE_CANARY: NOT_EXECUTED
EARLIEST_REQUIRED_RECOVERY_DATE: 2026-09-10
LATEST_REQUIRED_RECOVERY_DATE: 2026-09-17
RECOVERED_TRADING_SESSIONS: []
DAILY_CLOSE_RECOVERY: BLOCKED
TODAY_MARKET_RECOVERY: BLOCKED
A9_RECOVERY: BLOCKED
DAILY_STRENGTH_RECOVERY: BLOCKED
SCORE_RECOVERY: PARTIAL
GRADE_RECOVERY: PARTIAL
LIFECYCLE_RECOVERY: PARTIAL
FORMAL_TOPIC_PUBLICATION: BLOCKED
TOTAL_FORMAL_TOPICS: 87
FORMALLY_PUBLISHED_TOPICS: 87
OPPORTUNITY_ELIGIBLE_TOPICS: NOT_PROVEN
FULL_TOPIC_UNIVERSE_READY: NO
MLCC_IS_ONE_TOPIC: YES
MLCC_GLOBAL_GATE: NO
PRIOR_613_TO_5_FULL_FUNNEL: INVALID
FORMAL_OPPORTUNITY_API: UNAVAILABLE
FULL_2026_09_17_FORMAL_RESULT: NOT_PROVEN
FULL_2026_09_17_FINAL_CANDIDATES: NOT_PROVEN
ZERO_VS_UNAVAILABLE: PASS
LOOK_AHEAD_PROTECTION: PASS
SHADOW_FORMAL_SEPARATION: PASS
C1_C5_CHANGED: NO
S1_S2_CHANGED: NO
FUND_C_ELIGIBILITY_EFFECT: NONE
FUND_C_RANKING_EFFECT: NONE
FUND_C_FINAL_SELECTION_EFFECT: NONE
TODAY_MARKET_LATEST_FORMAL_DATE: 2026-09-09
A9_LATEST_FORMAL_DATE: NOT_PROVEN
LIFECYCLE_LATEST_FORMAL_DATE: NOT_PROVEN
OPPORTUNITY_LATEST_FORMAL_DATE: NOT_PROVEN
POST_CLOSE_BOUNDARY: 13:35 Asia/Taipei
POST_CLOSE_POLL_INTERVAL: 300 seconds
NEXT_TRADING_SESSION_AUTOMATIC_PIPELINE_READY: NO
FOCUSED_TESTS: 64 passed
BACKEND_FULL: 784 passed, 59 skipped, 9 registered baseline failures
WEB_TESTS: 165 passed
OPENAPI: PASS
BUILD: PASS
RUFF: BASELINE_FINDINGS
COMPILE: PASS
ALEMBIC_SINGLE_HEAD: YES
TASK_CAUSED_FAILURES: 0
REGISTERED_BASELINE_FAILURES: 9 Lifecycle
ENVIRONMENT_FAILURES: 59 PostgreSQL/integration skips; 2 ESLint warnings; missing production-worker hook
UNKNOWN_FAILURES: 0
PRODUCTION_DEPLOYMENT_PERFORMED: YES (API and Worker)
PRODUCTION_MIGRATION_PERFORMED: YES
PRODUCTION_REPLAY_PERFORMED: NO
PRODUCTION_POST_CLOSE_RETRY: EXECUTED_ONCE_COMPLETED_WITH_ISOLATED_NO_ROW
C_OWNER_HEAD_CHANGED: NO
C_OWNER_DIRTY_STATE_CHANGED: NO
OWNER_POLICY_DECISION_REQUIRED: NO for this closeout; the remaining mismatch is technical and no second recovery is authorized
OWNER_INTERACTION_REQUIRED: NO for this closeout
EARLIEST_REMAINING_BLOCKER: TWO_REFERENCE_COVERAGE_MISMATCH_8277
REMAINING_BLOCKERS: ["Production POST_CLOSE 2026-09-18 recovery failed with EMPTY_RESPONSE/EXCHANGE_NO_DATA/MARKET_PROVIDER_UNAVAILABLE", "formal Opportunity numeric policy/Leader Set publication authority", "historical formal replay and downstream publication"]
M1_PRODUCTION_FORMAL_PIPELINE_READY: NO
M1_TODAY_MARKET_READY: PARTIAL
M1_FORMAL_TOPIC_DAILY_STATE_READY: PARTIAL
M1_LIFECYCLE_FORMAL_READY: PARTIAL
M1_FULL_TOPIC_UNIVERSE_READY: NO
M1_FORMAL_OPPORTUNITY_API_READY: NO
M1_COMPLETE: NO
NEXT_ROADMAP_MILESTONE: NOT_AUTHORIZED_BEFORE_M1_COMPLETE
```

### Continuation machine-readable closeout (authoritative)

The preceding 2026-09-18-only machine summary is retained as the pre-reference-transition snapshot. The latest owner-evidence, reference-transition, and historical-replay state is recorded in the addendum at the end of this report and supersedes any earlier `TWO_REFERENCE_COVERAGE_MISMATCH_8277` or `HISTORICAL_REPLAY_STATUS=NOT_EXECUTED` wording.

```text
M1_COMPLETE=NO
PRODUCTION_FORMAL_PIPELINE_READY=NO
OFFICIAL_TPE_SOURCE_READY=YES
OFFICIAL_TWO_SOURCE_READY=YES
BOUNDED_TPE_PROVIDER_READY=YES
BOUNDED_TWO_PROVIDER_READY=YES
PRODUCTION_TPE_RUNTIME_PROVIDER_READY=YES
PRODUCTION_TWO_RUNTIME_PROVIDER_READY=YES
ROOT_CAUSE_STATUS=PROVEN
ROOT_CAUSE_LAYER=CLI_ENTRYPOINT_RECOVERY_ROUTING
ROOT_CAUSE=--recover recovery closure was created but not passed to LiveScheduler; the old failed run was reused without a fresh provider fetch
SCHEDULED_PATH_REMEDIATION=45b1fa198db34471ce03f29a9184d8236299d525
CANONICAL_SHA=45b1fa198db34471ce03f29a9184d8236299d525
PRODUCTION_API_SHA=b14d5708d4cda0cad2341154bc4495b64cf472ec
PRODUCTION_WORKER_SHA=45b1fa198db34471ce03f29a9184d8236299d525
WORKER_RUNTIME_SHA=45b1fa198db34471ce03f29a9184d8236299d525
POST_CLOSE_20260918=SUCCESS_WITH_ISOLATED_NO_ROW
POST_CLOSE_RUN_ID=2b5f8547-70a7-4783-a2dd-5729cb4799ac
POST_CLOSE_REQUESTED=553
POST_CLOSE_SUCCEEDED=552
POST_CLOSE_FAILED=0
POST_CLOSE_SKIPPED=1
POST_CLOSE_RETRIES=0
POST_CLOSE_CHECKPOINT=COMPLETED_29_OF_29
POST_CLOSE_PROVIDER_STATUS=AVAILABLE
POST_CLOSE_FRESHNESS=FRESH
POST_CLOSE_ISOLATED_FAILURE=TWO:8277:OFFICIAL_NO_ROW
HISTORICAL_REPLAY_STATUS=NOT_EXECUTED
HOME_V2_20260918=PUBLISHED
HOME_V2_SOURCE_RUN_ID=2b5f8547-70a7-4783-a2dd-5729cb4799ac
FORMAL_OPPORTUNITY_STATUS=UNAVAILABLE_OPTIONAL_SECTION_NOT_FORMAL
OWNER_CHECKOUT_PRESERVED=YES
OWNER_AUTHORIZATION=GRANTED
REFERENCE_TRANSITION_STATUS=ACTIVATED
ACTIVE_REFERENCE_VERSION=tw-reference-v1-rollover-0578862f98914eb7
RETIRED_REFERENCE_VERSION=tw-reference-v1-rollover-dd2c70fbfea8e400
REFERENCE_BUNDLE_SHA256=0578862f98914eb7b52fa2de8c253b6da6c4f882429c4c65dff2bdf7317b3662
REFERENCE_TRANSITION_CREATED_REFERENCE_ROWS=45
REFERENCE_TRANSITION_NON_REFERENCE_WRITE_SET=[]
REFERENCE_8277_LIFECYCLE=OFFICIAL_TPEX_BULLETIN_11500055041
REFERENCE_8277_SUSPENDED=2026-09-10..2026-09-18
REFERENCE_8277_NEW_SHARES_TRADE=2026-09-21
REFERENCE_8277_ELIGIBILITY=EXCLUDED_DURING_SUSPENSION;ELIGIBLE_2026-09-09_AND_2026-09-21
RENDER_RUNTIME_REFERENCE_VERSION=tw-reference-v1-rollover-0578862f98914eb7
TARGET_REFERENCE_PREFLIGHT_20260918=PASS
EARLIEST_REMAINING_BLOCKER=HISTORICAL_FORMAL_REPLAY_AND_OPPORTUNITY_AUTHORITY
BLOCKER_LAYER=HISTORICAL_REPLAY_AND_FORMAL_OPPORTUNITY_POLICY
OWNER_ACTION_REQUIRED=NO
TECHNICAL_ACCESS_REQUIRED=NO
HISTORICAL_REPLAY_20260910=SUCCESS_553_OF_553;APPROVED_NO_TRADE_8277
HISTORICAL_REPLAY_20260911=STOP_REQUESTED_ORPHANED_RUNNING_UNSAFE_CANONICAL_CONFLICT;TPE:2049,2308;PRICE_VOLUME
NEXT_SAFE_ACTION=Resolve canonical supersession conflicts for TPE:2049 and TPE:2308, then separately authorize continuation; do not cross to 2026-09-12
```

### Latest continuation addendum — owner evidence, reference transition, and replay

The owner-supplied `TWO:8277` evidence was independently verified against the
[official TPEx bulletin](https://www.tpex.org.tw/www/zh-tw/bulletin/annDetail?content_file=MTE1MDAwNTUwNDEuaHRtbA%3D%3D&docId=MTE1MDAwNTUwNDE%3D), bulletin `11500055041`. It records temporary suspension from `2026-09-10` through `2026-09-18`, replacement-share base date `2026-09-18`, and new-share OTC trading date `2026-09-21`.

The governed reference transition was validated and activated atomically. The
new active version is `tw-reference-v1-rollover-0578862f98914eb7`, with bundle
SHA-256 `0578862f98914eb7b52fa2de8c253b6da6c4f882429c4c65dff2bdf7317b3662`;
the previous version `tw-reference-v1-rollover-dd2c70fbfea8e400` is retired and
preserved. The dry-run reported 45 reference-only rows, zero instrument or
market creations, an empty non-reference write set, and transactional atomicity.

Date-effective eligibility readback is now:

- `2026-09-09`: 8277 eligible and included in the TWO quote universe.
- `2026-09-10` through `2026-09-18`: 8277 suspended and excluded with reason `LIFECYCLE_SUSPENDED`.
- `2026-09-21`: 8277 eligible again and included in the TWO quote universe.

The Render Worker environment was updated to the active reference version and
the live runtime read back the same version at Worker SHA
`45b1fa198db34471ce03f29a9184d8236299d525`. The target-date reference
preflight passed with TWO official record count `11481` and no missing identity
codes.

Sequential historical replay then started at `2026-09-10`. Run
`2e05c3fe-8174-47df-a371-1143bf32140c` completed `553/553` attempts with zero
failures and zero retries. The 8277 attempt is explicitly `SUCCESS` with
provider status `SUSPENDED`, freshness `FRESH`, error code
`APPROVED_NO_TRADE`, and the message that the official TPEx market dataset had
no row for the requested instrument/date. This is the expected isolated
lifecycle outcome, not a provider outage. Its persisted downstream readback
reports `normalEodReadback=PASS`, `normalEodPublication=PASS`,
`normalTopicSnapshotReadback=PASS`, and `normalTopicSnapshotPublication=PASS`;
market reconciliation is `READY` at 100% coverage with 551 priced items and 2
legal no-trade items. The same metadata records the pre-existing Lifecycle
`TypeError` baseline as `LIFECYCLE_UNAVAILABLE` and `scoreStatus=DEFERRED`, so
those stages remain fail-closed and are not relabeled as successful.

The next sequential recovery, `2026-09-11`, reached 3 checkpoints with 58
successful and 2 failed attempts before the governed stop boundary. TPE
instruments `2049` and `2308` returned `RuntimeError` with
`canonical supersession branch conflict: ['PRICE', 'VOLUME']`. This is a
canonical-data conflict, not an isolated legal no-trade or provider-unavailable
classification. A stop signal was sent; the persisted run row remains
`RUNNING` with heartbeat unchanged after the stop request, so it is treated as
an orphaned/incomplete run and not as a formal result. The run was not advanced
to `2026-09-12` and no fallback, manual overwrite, or policy relaxation was
performed.
