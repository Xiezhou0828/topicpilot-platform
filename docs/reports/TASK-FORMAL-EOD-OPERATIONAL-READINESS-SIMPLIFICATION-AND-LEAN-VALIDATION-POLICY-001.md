# TASK-FORMAL-EOD-OPERATIONAL-READINESS-SIMPLIFICATION-AND-LEAN-VALIDATION-POLICY-001

## 1. Executive Summary

本任務已完成 `TOPICPILOT_LEAN_VALIDATION_POLICY_V1` 的受控實作與驗證。
正式 EOD readiness 不再要求交易所提供不可修訂或永久 finality 的明示保證，
改以 `READY / WAIT / BLOCKED` 三態判斷最低充分的 operational evidence。

保留 fail-closed 的正確性邊界：錯誤或無法解釋的日期、future/nonsensical
date、malformed required data、必要 coverage 不足、material authority
conflict、Corporate Action comparator authority 缺失、look-ahead、
survivorship、synthetic zero-fill 與未授權 forward-fill 仍會阻擋或使受影響
維度 unavailable。`EXCHANGE_NOT_READY`、暫時 provider unavailable，以及官方
仍服務前一個有效 session 的 publication lag 現在是 `WAIT`。

本次 application code 已變更，產生新的 implementation SHA；Production
deployment、database/migration、scheduler mutation、historical recovery、
2026-10-05/2026-10-06 replay 或 publication 均未執行。下一步是 Owner review
並重新授權這個 exact SHA 的 canonical promotion/release。

## 2. Owner Policy Decision

本任務將 validation 深度改為與 failure consequence 成比例：Tier 1 做 changed
scope 檢查，Tier 2 做 focused logic/provider/publication regression，Tier 3
仍對 formal state、Corporate Action、migration、destructive correction 與
duplicate-publication risk 做較強但仍有限的驗證。不因「理論上可以再收集更多
證據」而阻擋 ordinary product work，也不把低成本研究產品變成 institutional
assurance system。

`TOPICPILOT_LEAN_VALIDATION_POLICY_V1` 已寫入既有 canonical governance
document：`docs/policies/development-process.md`。沒有另建重疊治理文件。

## 3. Current Canonical State

| Item | Evidence |
|---|---|
| Repository | `Xiezhou0828/topicpilot-platform` |
| Canonical remote head | `e97f590cad497c0a23fb027fce39ec5891ea4bc1` |
| Implementation base | `9a5c35ae0398d55b9232d88dc727aa2111cfa92a` |
| Implementation SHA | `debf81f` (full SHA recorded in final handoff/evidence closure) |
| Worktree | `E:\TopicPilot\w\pcf001` |
| Branch | `codex/post-close-float-canonicalization-reconciliation-001` |
| Provider authority | TPE `TWSE_OFFICIAL_DAILY / twse-official-daily.v2 / MI_INDEX`; TWO `TPEX_OFFICIAL_DAILY / tpex-official-openapi-daily.v1 / tpex_mainboard_daily_close_quotes` |
| Prior candidate | `edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91` |

The remote main SHA was independently read through the GitHub read-only connector
and local tracking state. No push was performed. The local implementation commit is
not asserted to be canonical mainline until Owner-authorized promotion.

Preserved prior forensic evidence records 2026-10-06 TWSE target-date success,
TPEx dailyQuotes target-date success, TPEx OpenAPI `1151006` target-date success,
12,194 same-session reconciled rows, and zero OHLC/volume mismatches. Those facts
remain regression evidence; they are not hard-coded into the new policy.

## 4. Current Readiness Model

The old operational decision effectively treated missing explicit exchange finality
or no-revision metadata as a permanent blocker. The new model is:

- `READY`: minimum official same-session EOD evidence is coherent and complete.
- `WAIT`: evidence is expected to become available later in the same publication
  lifecycle; no downstream formal publication is attempted.
- `BLOCKED`: evidence is materially invalid, contradictory, or outside the
  authority contract; downstream formal publication stops fail-closed.

The provider CLI keeps its compatible top-level `status=PASS|WAIT|FAIL` output and
adds canonical `readinessState=READY|WAIT|BLOCKED`. This avoids breaking existing
operators while making the new state explicit.

## 5. Why Previous Finality Requirement Was Excessive

Official exchanges commonly publish valid daily data without an explicit immutable
or `FINAL=true` flag. Requiring a proof that no later correction can ever occur is
not a useful operational test for this product and cannot be established from the
available official response. It conflated publication readiness with an impossible
future guarantee.

The replacement is not blind acceptance. It accepts only coherent official
same-session evidence and relies on the existing immutable receipt plus correction/
supersession path if an official source later corrects a fact. The correction path
is the safety mechanism; it is not a reason to relax date, payload, coverage,
authority, comparator, or research-integrity checks.

## 6. Lean Validation Policy v1

The canonical policy now requires:

1. Validate changed behavior and its immediate contract first.
2. Run the smallest meaningful focused and relevant regression suites.
3. Use realistic fixtures and deterministic decisions where business/data logic is
   touched.
4. Run the full backend only when the blast radius materially justifies it.
5. Keep exact-SHA runtime readback and release authority for actual deployment.
6. Keep strict research protections against look-ahead, survivorship, fabricated
   fills, and outcome-based membership.

The policy explicitly forbids provider switching, new paid dependencies, complex
queue/consensus infrastructure, and uncontrolled retry loops for this problem.

## 7. READY / WAIT / BLOCKED Contract

| State | Required evidence | Action |
|---|---|---|
| `READY` | Official source, retrieval success, target-session match, valid response status/payload, required rows and parseable OHLCV, minimum coverage, no material conflict | Continue normal downstream calculation/publication |
| `WAIT` | `EXCHANGE_NOT_READY`, empty publication payload, bounded temporary retrieval failure, or clearly stale previous valid session during publication lag | Persist retryable state/receipt, do not formal-publish, retry on existing cadence |
| `BLOCKED` | Unexplained/future/nonsensical date, malformed required data, required coverage failure, authority conflict, or unresolved comparator authority | Stop fail-closed and require investigation/correction |

`WAIT` is not a fallback authority and never rewrites the served date. `BLOCKED`
does not become `READY` by ignoring the evidence.

## 8. Operational EOD Readiness

`OPERATIONAL_EOD_READINESS=YES` requires all of the following:

- official source authority;
- successful retrieval and any available provider success status;
- `SERVED_SESSION == TARGET_SESSION`;
- existing required payload/table;
- non-empty required rows;
- parseable required OHLCV for expected instruments;
- minimum expected coverage/completeness;
- no explicit NOT_READY/ERROR/INCOMPLETE marker;
- no material authority conflict.

No explicit finality or no-revision field is required. Missing numeric values remain
null/unavailable and do not become zero. The TPEx formal market-batch registration
remains the official OpenAPI v1 path; the date-addressable dailyQuotes path is a
supporting official authority where its comparator/history contract is needed, not
an implicit provider replacement.

## 9. Provider Date-Mismatch Semantics

`PROVIDER_DATE_MISMATCH` is classified with the served date:

- `WAIT_PROVIDER_PUBLICATION_LAG` when the requested date is the current completed
  trading session, the official provider serves the immediately previous valid
  session, and the evidence is clearly stale rather than falsely labeled as the
  target date.
- `BLOCKED_PROVIDER_DATE_AUTHORITY` when the served date is future, nonsensical,
  internally conflicting, unexplained, or cannot be established as ordinary
  publication lag.

The response date is never silently rewritten to the requested date.

## 10. Scheduler / Retry Behavior

The existing short provider readiness window remains bounded at the verified
approximately `MAX_ATTEMPTS=3` and total wait of approximately 90 seconds. A
provider `WAIT` exits the run cleanly as `WAITING_LIVE_VALIDATION`, records no
formal publication, and reuses the existing date-keyed/idempotent run and scheduler
cadence on a later invocation. A later `READY` result can continue the same normal
publication lifecycle.

No new queue, worker sleep-until-ready loop, provider fallback, or infinite in-run
retry was added. Existing immutable receipt hashing and run idempotency remain in
place. The 15:00 event is still recorded as critical even while receipt state is
retryable `WAITING_FOR_DATA`.

## 11. 13:45 / 14:30 / 15:00 Semantics

- `13:45`: earliest eligibility is unchanged.
- `14:30`: soft operational late-data warning is unchanged.
- `15:00`: hard operational SLA alert threshold; it is not a permanent same-session
  publication boundary.
- After `15:00`: a `WAIT` remains retryable and records the critical late-data event.
  If official data later becomes `READY`, the same session may publish through the
  normal path without historical replay solely due to lateness.

## 12. Receipt / Correction Safety

Daily Formal Publication Receipt remains immutable and hash-idempotent. The new WAIT
state maps to `RECEIPT_WAITING_FOR_DATA`, while the 15:00 hard-SLA event is retained
as an operational event. Existing successful receipts, correction receipts,
supersession lineage, and chronological correction/replay semantics are unchanged.

No new correction machinery was introduced. A later official correction continues
to use the existing new-receipt/correction/supersession path and affected lifecycle
replay rules. Historical Home is not republished by this change.

## 13. Corporate Action Protections Preserved

Corporate Action Price Authority v1 remains strict:

- `previous_traded_close` and `daily_comparison_reference` remain conceptually
  distinct;
- neither value is synthesized or inferred from price movement;
- no special case was added for TPE 2601;
- missing comparator authority leaves the affected return/dimension unavailable;
- the current close remains a separate current-session fact;
- Corporate Action authority is not extended by the lean readiness policy.

Dimension-aware completeness continues to distinguish legitimate unavailable,
source/data failure, and authority conflict.

## 14. Implementation

Changed application behavior:

- added the pure `market_data.readiness` contract and date parsing/classification;
- added `readinessState` and reason codes to read-only provider preflight;
- classified exchange-not-ready, temporary provider failure, and previous-session
  publication lag as WAIT;
- preserved top-level `PASS|WAIT|FAIL` compatibility for provider preflight;
- prevented institutional-flow and formal downstream work while provider preflight
  is WAIT/FAIL;
- made PostClose persist `WAITING_LIVE_VALIDATION` without entering formal
  publication;
- removed the 15:00 early permanent-deadline return from the normal forward path;
- kept hard-deadline operational receipt events;
- updated CLI exit handling for retryable WAIT;
- documented the policy in canonical governance and provider-preflight documents.

No provider switch, migration, schema change, new dependency, scheduler
configuration change, or Production configuration change was made.

## 15. Focused Validation

Validation executed in the implementation worktree with the repository API virtual
environment and `PYTHONPATH=services/api/src`:

- focused readiness/preflight/forward/receipt/post-close/live suite: **93 passed**;
- expanded relevant backend/worker regression suite: **143 passed**;
- Ruff lint on all changed Python scope: **passed**;
- `git diff --check`: **passed**;
- full backend suite: **NOT RUN**; this is allowed by the Owner's lean policy and
  is not a completion blocker for this bounded change.

The required focused cases cover official target data without finality metadata,
explicit not-ready, previous-session publication lag, future-date blocking,
malformed/incomplete/authority-conflict blocking, WAIT-to-READY transition,
post-15:00 same-session retryability, market-closed behavior, receipt contracts,
and existing comparator/float-canonicalization regressions in the relevant suites.

## 16. Release Impact

`APPLICATION_CODE_CHANGED=YES`. Therefore `debf81f` is a new release candidate
(full SHA is in the evidence closure and final handoff), and the previously known
`edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91` is not silently reusable as the final
candidate for this behavior. The old candidate may remain historical evidence, but
it does not contain this implementation.

`PRODUCTION_RELEASE_READY=NO` until Owner reviews and reauthorizes the new exact
SHA. No deployment is authorized or executed in this task. Production runtime
readback remains required after any separately authorized deployment.

## 17. Mutation Ledger

| Boundary | Result |
|---|---|
| Production deployment | NO |
| Production DB write | NONE |
| Migration execution | NO |
| Scheduler mutation | NO |
| Provider registry mutation | NO |
| 2026-10-05 touched | NO |
| 2026-10-06 replayed | NO |
| Historical recovery/backfill | NO |
| Formal publication | NO |
| Historical Home republish | NO |
| Preview worktree / localhost:4317 | NOT TOUCHED |
| Remote push | NO |
| NEXT_TASK mutation | NO |

Original failed executions for 2026-10-05 and 2026-10-06 remain preserved in the
existing lineage. `FORMAL_HISTORICAL_GENESIS_DATE` remains
`PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION`.

## 18. Next Action

Owner review the report and the exact implementation SHA, then explicitly
reauthorize canonical promotion and the separately governed Production release if
desired. The next release review can use the lean readiness evidence; it does not
need to continue finality-forensic work. This task itself performs no deployment,
Production mutation, historical replay, or scheduler change.

## Owner Summary — Traditional Chinese

1. 原本是哪一個驗證條件把系統卡得過嚴？
   原本要求官方來源提供 `EXPLICIT_FINALITY_AUTHORITY_REQUIRED`，也就是明示
   不可修訂或 `FINAL=true` 的保證。
2. 為什麼 explicit no-revision/finality guarantee 不再是必要條件？
   官方有效日資料通常不提供不可修訂保證；要求證明未來永不更正既不切實際，
   也不是研究產品判斷當下可用性的必要條件。既有 correction/supersession 是
   安全網。
3. 新 READY 最低條件是什麼？
   官方來源、retrieval 成功、served session 等於 target session、成功狀態、
   payload/required rows 存在、OHLCV 可解析、最低 coverage 通過、沒有 NOT_READY
   或 material authority conflict。
4. WAIT 是什麼？
   暫時不可用、exchange 尚未 ready、空的 publication payload，或仍服務前一個
   有效 session 的 publication lag；不永久失敗，記錄後稍後重試。
5. BLOCKED 是什麼？
   證據無效或矛盾，例如 malformed required data、coverage 不足、future/無法解釋
   的日期、authority/comparator conflict；必須 fail-closed。
6. `EXCHANGE_NOT_READY` 現在如何處理？
   分類為 `WAIT_PROVIDER_NOT_READY` / `WAIT`，不走 fallback、不做 formal write。
7. previous-session date mismatch 何時是 WAIT？
   target 是目前已完成交易 session、官方來源明確只服務立即前一個 valid session，
   且沒有把舊資料誤標成 target。
8. 哪種 date mismatch 仍是 BLOCKED？
   future、nonsensical、內部衝突、無法解釋為正常 publication lag，或無法證明 served
   date 的 authority mismatch。
9. 13:45 的意義有沒有改？
   沒有，仍是 earliest eligibility。
10. 14:30 的意義有沒有改？
    沒有，仍是 soft late-data warning。
11. 15:00 的意義改成什麼？
    hard operational SLA alert threshold，不再是永久同日 publication boundary。
12. 15:00 後資料才 ready 是否仍可正常發布？
    可以；後續同日 `READY` 可走原本 normal publication path。
13. 是否需要 replay 才能發布？
    不需要；單純因同日 15:00 後才 ready 不需 historical replay。
14. 是否建立無限 retry？
    沒有；保留每次約 3 attempts/約 90 秒的 bounded window，之後使用既有 scheduler
    cadence，不做 busy loop 或無限 worker sleep。
15. 是否新增付費服務？
    沒有。
16. TPEx 是否換 provider？
    沒有；仍是 `TPEX_OFFICIAL_DAILY`，正式 market-batch adapter 是
    `tpex-official-openapi-daily.v1`。
17. cross-check 是否變成強制雙來源？
    沒有；自然存在的官方 cross-check 是 supporting evidence，不是全球強制雙來源。
18. correction/replay safety 是否保留？
    保留，包含 immutable original receipt、correction receipt、supersession 與受影響
    Lifecycle replay。
19. immutable receipt 是否保留？
    保留，並維持 hash-idempotent duplicate prevention。
20. Corporate Action authority 是否被放寬？
    沒有；`previous_traded_close` 與 `daily_comparison_reference` 仍分離，不能猜測
    或合成，也沒有 2601 特例。
21. missing data 是否仍禁止當 0？
    是，仍是 null/unavailable，不得 zero-fill 或未授權 forward-fill。
22. look-ahead / survivorship protection 是否仍保留？
    保留，仍是直接 correctness gate。
23. 一般 UI change 未來最低需要什麼 validation？
    Tier 1：changed behavior 可用，必要時 focused test，以及 changed scope 的 lint/typecheck。
24. business logic change 最低需要什麼 validation？
    Tier 2：focused logic tests、relevant regression、realistic fixture/known example，
    並在重要處維持 deterministic behavior。
25. Production/migration change 最低需要什麼 validation？
    Tier 3：只做 materially relevant 的較強驗證、exact SHA/runtime readback 與明確授權；
    migration/data mutation 仍是獨立 authority boundary。
26. full backend 是否仍每次必跑？
    不必。
27. 什麼情況才需要 full backend？
    changed blast radius 足夠廣、或 release/owner gate 明確要求時；本任務不是必要條件。
28. focused tests 是否通過？
    是，focused readiness/preflight/forward/receipt/post-close/live suite `93 passed`；
    擴大相關 regression `143 passed`。
29. application code 是否有改？
    有，新增 readiness contract 並調整 provider preflight、forward、post-close、receipt 與 CLI。
30. 是否產生新的 release candidate？
    是，implementation commit 為新的 candidate。
31. 舊 `edcd73ce...` 是否仍可作 release candidate？
    對這個已變更的 application behavior，不可視為最終 candidate；只能保留為歷史 evidence。
32. 是否需要 Owner 重新授權 release？
    需要，因為 application code changed 且 exact SHA 已改變。
33. 10/05 是否完全沒碰？
    是，沒有 replay、recovery、publication 或寫入。
34. 10/06 是否完全沒 replay？
    是，只使用既有 forensic evidence 作 regression context，沒有 replay。
35. D0 是否仍 pending？
    是，`PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION`。
36. 下一步是不是可以回到 Production release，而不是繼續做 finality forensic？
    可以回到 Owner-governed release review；但要先由 Owner 重新授權新 exact SHA，
    本任務本身仍不部署、不寫 Production。

## Terminal Summary

```text
TASK_STATUS=COMPLETE_LEAN_READINESS_IMPLEMENTED_RELEASE_REAUTH_REQUIRED
CANONICAL_REMOTE_HEAD=e97f590cad497c0a23fb027fce39ec5891ea4bc1
IMPLEMENTATION_BASE_SHA=9a5c35ae0398d55b9232d88dc727aa2111cfa92a
WORKTREE=E:\TopicPilot\w\pcf001
BRANCH=codex/post-close-float-canonicalization-reconciliation-001
LEAN_VALIDATION_POLICY_VERSION=TOPICPILOT_LEAN_VALIDATION_POLICY_V1
LEAN_VALIDATION_POLICY_IMPLEMENTED=YES
READINESS_MODEL=READY_WAIT_BLOCKED
EXPLICIT_FINALITY_FLAG_REQUIRED=NO
EXPLICIT_NO_REVISION_GUARANTEE_REQUIRED=NO
OFFICIAL_SOURCE_REQUIRED=YES
TARGET_SESSION_MATCH_REQUIRED=YES
VALID_REQUIRED_PAYLOAD_REQUIRED=YES
MINIMUM_COVERAGE_REQUIRED=YES
KNOWN_MATERIAL_CONFLICT_ALLOWED=NO
EXCHANGE_NOT_READY_STATE=WAIT
PREVIOUS_SESSION_PUBLICATION_LAG_STATE=WAIT
MALFORMED_REQUIRED_DATA_STATE=BLOCKED
AUTHORITY_CONFLICT_STATE=BLOCKED
EARLIEST_ELIGIBILITY=13:45
SOFT_WARNING=14:30
HARD_SLA_ALERT=15:00
POST_1500_LATE_PUBLICATION_ALLOWED=YES
INFINITE_RETRY_CREATED=NO
NEW_PAID_DEPENDENCY=NO
PROVIDER_SWITCH_EXECUTED=NO
DUAL_SOURCE_REQUIRED_GLOBALLY=NO
IMMUTABLE_RECEIPT_PRESERVED=YES
CORRECTION_PATH_PRESERVED=YES
CORPORATE_ACTION_AUTHORITY_PRESERVED=YES
MISSING_DATA_ZERO_FILL_ALLOWED=NO
LOOKAHEAD_PROTECTION_PRESERVED=YES
SURVIVORSHIP_PROTECTION_PRESERVED=YES
FOCUSED_TESTS=93 passed
RELEVANT_REGRESSION_TESTS=143 passed
FULL_BACKEND=NOT_RUN
FULL_BACKEND_REQUIRED_FOR_COMPLETION=NO
APPLICATION_CODE_CHANGED=YES
IMPLEMENTATION_SHA=debf81f
EVIDENCE_CLOSURE_SHA=debf81f68185c1a12c1294840838e32d956eda1f
PREVIOUS_AUTHORIZED_CANDIDATE=edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91
NEW_RELEASE_CANDIDATE_REQUIRED=YES
CURRENT_TASK004_CANDIDATE_SUPERSEDED=YES
OWNER_RELEASE_AUTHORIZATION_REQUIRED=YES
PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_WRITE_SET=NONE
DATABASE_MIGRATION_EXECUTED=NO
SCHEDULER_MUTATED=NO
PROVIDER_REGISTRY_MUTATED=NO
TARGET_DATE_2026_10_05_TOUCHED=NO
TARGET_DATE_2026_10_06_REPLAYED=NO
HISTORICAL_RECOVERY_EXECUTED=NO
FORMAL_PUBLICATION_EXECUTED=NO
PREVIEW_TOUCHED=NO
PUSH_EXECUTED=NO
NEXT_TASK_MODIFIED=NO
ORIGINAL_2026_10_05_FAILED_EXECUTION_PRESERVED=YES
ORIGINAL_2026_10_06_FAILED_EXECUTION_PRESERVED=YES
FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
NEXT_ACTION=Owner review and explicit reauthorization of the new exact SHA for canonical promotion and Production release; no deployment in this task
```
