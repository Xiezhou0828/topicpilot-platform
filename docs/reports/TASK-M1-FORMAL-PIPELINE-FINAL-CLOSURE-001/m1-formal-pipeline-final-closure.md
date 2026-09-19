# TASK-M1-FORMAL-PIPELINE-FINAL-CLOSURE-001

## 1. 結論

`TASK_STATUS=BLOCKED`。M1 未完成，且本次沒有啟動 M2。

本次已完成一個安全、局部、可回滾的 Today 修正候選：當正式訊號所需的指數、量價前值、法人流向或市場廣度依賴未齊時，Daily Focus 不再將空訊號誤報為「今日無異常訊號」，而是回傳 `PARTIAL`、`今日市場訊號尚未完成` 及機器可讀的依賴狀態。候選 commit 為 `c4405351f921ddd70089ec00a7c299ea97d9a768`，已推送至隔離治理分支，尚未進入 canonical Owner checkout，也尚未部署。

## 2. 唯一最早剩餘 blocker

`EARLIEST_REMAINING_BLOCKER=FORMAL_SCORE_GRADE_AUTHORITY_MISSING`

`BLOCKER_LAYER=FORMAL_AUTHORITY`

正式 Score/Grade 仍要求可驗證的 PM-approved policy approval、approved Leader Set、CORE authority、精確 observation-as-of binding 及對應 lineage。現有 `topic_score_formal.py` 明確是 non-persistent、non-activating bridge；快照仍寫入 `market_grade=NULL`、`topic_score=NULL`、`score_status=DEFERRED`。不可用研究候選或資料夾名稱推導正式權威，也不可把 Leader Set 當成 Structural Role。

因此不能安全地把 Score/Grade、正式 Lifecycle baseline 或正式 Opportunity provider/API/publication 宣告為 ready。這不是一般部署權限問題，而是缺少正式產品治理輸入；Owner/PM 需提供該 authority artifact 後才能繼續。

## 3. 範圍與禁止事項

- 僅處理 M1；沒有開始 M2。
- 沒有改變 Topic taxonomy、C1-C5、S1-S2、FUND-C evidence-only、Structural Role 或評分公式。
- 沒有創造新的 Leader Set、CORE、Lifecycle stage 或 Opportunity provider。
- 沒有在受保護 Owner checkout 執行 reset、clean、stash、checkout、merge 或檔案寫入。
- 沒有部署 `17ce8896…` 或本次候選 commit；Production 仍是既有 runtime truth。

## 4. 四個真相面

| Truth | 結果 | 證據 |
|---|---|---|
| Development | 候選修正已驗證並 commit/push | governed branch `codex/task-m1-formal-pipeline-final-closure-001`, `c4405351…` |
| Backend Production | 可達、但不是本候選 SHA | `/healthz`、`/readyz` 皆 200；API SHA `b14d5708d4cda0cad2341154bc4495b64cf472ec` |
| Web Production | 可達；exact Web SHA 未暴露 | `https://topicpilot-platform.game0962046460.chatgpt.site` HTTP 200；HTML 指向 Production API |
| Formal data | Topic formal publication 至 2026-09-18；Score/Grade/Lifecycle/Opportunity 仍 gated | task-provided governed evidence、Production `/api/v2/home`、Opportunity 503 |

## 5. 受保護 checkout 與隔離 worktree

受保護 Owner checkout：

`C:\Users\acer\Desktop\題材領航\topicpilot-platform`

- before HEAD: `02d3086183d1c582bb6c66c4c316340ccce3fa97`
- before dirty count: `153`，為既有狀態
- after HEAD: `02d3086183d1c582bb6c66c4c316340ccce3fa97`
- after dirty count: `153`
- `OWNER_CHECKOUT_PRESERVED=YES`

隔離 worktree：

`C:\Users\acer\Desktop\題材領航\topicpilot-platform-m1-final-closure`

- branch: `codex/task-m1-formal-pipeline-final-closure-001`
- base: `17ce8896d3b2e4d0c842edd9d847b91d2673a6a3`
- candidate commit: `c4405351f921ddd70089ec00a7c299ea97d9a768`
- remote branch: pushed successfully

## 6. 本次實作變更

`services/api/src/topicpilot_api/home_v2_publication.py` 新增正式訊號依賴 gate，逐項檢查：

1. TPE 與 TWO 指數均有正式 `change`。
2. TWO 成交金額及前一交易日 `changePct` 均有正式值。
3. TPE 法人流向與外資正式數值均有資料。
4. TPE/TWO breadth coverage、advance、decline 均為正式可用。

依賴不完整時，Daily Focus 現在回傳：

- `status=PARTIAL`
- `headline=今日市場訊號尚未完成`
- `reasonCode=TODAY_SIGNALS_FORMAL_DEPENDENCIES_INCOMPLETE`
- `formalDependenciesComplete=false`
- `formalDependencyStatus` 包含每一條 catalog rule 的 ready/missing 狀態

只有四條 rule 的必要輸入都完整時，才允許 `AVAILABLE` 且可顯示「今日無異常訊號」。API schema、OpenAPI snapshot、api-client type 與 Web generated type 已同步更新。

## 7. 官方 dataset readiness inventory

Production 2026-09-18 readback：

| Dataset | Observed state | Formal implication |
|---|---|---|
| TPE index | `UNAVAILABLE`, `change=null` | Index divergence、institution-price、breadth rules 不能完成判定 |
| TWO index | `AVAILABLE`, `change=14.51` | 單獨可用，但不能補齊 TPE 依賴 |
| TPE/TWO turnover | `AVAILABLE` values；兩者 `changePct=null` | OTC volume-price rule 不能完成前日比較 |
| Institutional flows | `null` | Institution-price rule 不可判定；目前不是零值 |
| TPE breadth | `AVAILABLE`, observed `1077`, advance `748`, decline `251` | breadth 子資料可用 |
| TWO breadth | `AVAILABLE`, observed `868`, advance `565`, decline `219` | breadth 子資料可用，但不能抵銷缺失指數 |
| Formal Topic | `AVAILABLE` through `2026-09-18` per governed task evidence | Topic publication boundary is current through that date |
| Opportunity | endpoint returns `503` | no canonical formal provider |

官方 source endpoint 的 2026-09-18 read-only probe 皆 HTTP 200：

- [TWSE official MI_INDEX](https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX)
- [TPEx official dailyQuotes](https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes)
- [TWSE OpenAPI market index](https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX)
- [TPEx OpenAPI daily trading index](https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index)

HTTP 200 僅證明 upstream endpoint 回應，不代表 Production persisted dataset 已具備所有訊號依賴或可正式發布。

## 8. Timing model

選擇 `MODEL_C_READINESS_AWARE_STAGED` 作為 M1 應採用的 timing model，而不是硬編一個固定的 17:00 deadline：

- session close: `13:30`
- post-close start: `13:35`
- scheduler poll: `300s`
- provider retries: bounded by existing runtime configuration，history max retries `4`，backoff `2s`
- official sources 可各自出現不同的 available/partial/unavailable 狀態

現有 post-close 對 OHLCV 已具備 idempotence、checkpoint、resume、duplicate-writer guard 與 bounded retry；但 official market facts 的 persisted readiness gate 及法人流向正式供應仍未達到 M1 的完整 closure。`MODEL_C` 因此是正確的產品/運營模型，但目前不是可宣稱完成的 Production formal pipeline。

## 9. Historical replay 與 D+1

- `HISTORICAL_REPLAY_STATUS=CURRENT_THROUGH_20260918`
- `NEXT_MISSING_TRADING_DAY=NONE`
- task-provided governed evidence states 2026-09-10..09-18 are current, with 2026-09-16/17 complete and 2026-09-18 readback complete.
- 本次沒有重跑已宣告 current 的 historical dates，也沒有以 D+1、fallback date、stale row 或 zero substitution 補資料。
- Missing/unknown/unavailable remain typed unavailable/partial rather than zero.

## 10. Today formal publication

Production readback from `/api/v2/home` for `2026-09-18`：

```text
marketOverview.dataStatus=AVAILABLE
marketOverview.indices=TPE:UNAVAILABLE(change=null), TWO:AVAILABLE(change=14.51)
marketOverview.institutionFlows=null
marketOverview.breadth=TPE/TWO AVAILABLE
sectionStatuses.dailyFocus.status=AVAILABLE       # current bug on deployed SHA
dailyFocus.headline=今日無異常訊號                  # current bug on deployed SHA
sectionStatuses.opportunities.status=UNAVAILABLE
sectionStatuses.opportunities.reasonCode=OPTIONAL_SECTION_NOT_FORMAL
```

本次候選 commit 對同等輸入會將 Daily Focus 改為 `PARTIAL`，並輸出 `formalDependenciesComplete=false`；因候選尚未 canonicalize/deploy，Production readback 尚未改變。

## 11. A9 / Daily Strength / Score / Grade

```text
A9_READY=DEFERRED_NOT_SEPARATELY_PERSISTED
DAILY_STRENGTH_READY=DEFERRED_NOT_SEPARATELY_PERSISTED
SCORE_READY=DEFERRED
GRADE_READY=DEFERRED
```

現有 snapshot materializer 明確保留 nullable `market_grade`、`topic_score` 與 `score_status=DEFERRED`；不能以現有 shadow/preview 值填入正式欄位。

## 12. Lifecycle

```text
LIFECYCLE_READY=NO;LIFECYCLE_UNAVAILABLE_BASELINE
```

Formal V1.3 publisher 與 migration 0037 存在，但 post-close 目前呼叫的是 shadow `TopicLifecycleEngine`，不是已達正式 authority gate 的完整 formal baseline。Formal publisher 本身會對缺失 formal snapshot、structural-role authority 或 observation evidence fail closed；不能把 shadow result 當成正式 lifecycle。

## 13. Formal Topic

```text
FORMAL_TOPIC_PUBLICATION_READY=YES_THROUGH_20260918
```

Topic identity、PIT formal snapshot、correction/supersession lineage 與 2026-09-18 readback 依 task-provided governed evidence 已 current。這不延伸成 Score/Grade/Lifecycle/Opportunity ready。

## 14. Formal Opportunity

```text
OPPORTUNITY_FORMAL_DAILY_RECOMMENDATION_READY=NO;OPTIONAL_SECTION_NOT_FORMAL
```

Production `/api/v2/opportunities` read-only request returned HTTP 503，訊息為沒有 approved canonical formal Opportunity provider。現有 `formal_opportunity_universe.py` 是 formal Topic-universe consumer boundary；它明確不執行 Grade/Lifecycle policy、Leader membership、C1-C5、Strategy、Selector 或 FUND-C effects。這符合 frozen boundary，不能為了 closure 偽造 provider。

## 15. Full universe 與 semantic preservation

- Full formal Topic publication is current through 2026-09-18 per governed evidence.
- Opportunity full-universe read model remains unavailable until formal Score/Grade/Lifecycle and eligibility authorities exist.
- C1-C5/S1-S2 status remains not executed by the formal consumer.
- FUND-C remains evidence-only and not consumed as a recommendation authority.

## 16. Four truths / API / Web readback

- Production API health: `200`, SHA `b14d5708d4cda0cad2341154bc4495b64cf472ec`.
- Production API ready: `200`, same SHA.
- Production Home: `200`, data date `2026-09-18`, but deployed Daily Focus has the fail-open bug described above.
- Production Opportunity: `503`, expected fail-closed boundary.
- Production Web: HTTP `200`; HTML carries `data-api-base-url=https://topicpilot-api.onrender.com`; exact Web build SHA not exposed by the public page and is therefore `UNPROVEN`.
- Worker SHA: `45b1fa198db34471ce03f29a9184d8236299d525` per governed task evidence; not changed by this task.

## 17. Validation

Passed in isolated worktree using Python 3.12:

- `test_home_v2_publication.py`: `11 passed`
- `test_home_status_contract.py` plus `test_home_read_model.py`: `1 passed, 1 PostgreSQL integration skipped` because no test database URL was configured
- Opportunity/policy/score/formal-lifecycle focused suite: `65 passed`
- Ruff on changed Python files: PASS
- Python compileall on changed modules: PASS
- `git diff --check`: PASS

Not run or not proven:

- Full backend regression against PostgreSQL production schema: not run in this isolated environment.
- `packages/api-client npm run check`: not runnable because `node_modules` is not installed in the sparse worktree.
- Production deployment/canary after `c4405351…`: intentionally not executed.

## 18. M1 Definition of Done matrix

| DoD item | State |
|---|---|
| Production formal pipeline ready | NO |
| Historical dates current | YES through 2026-09-18 per governed evidence |
| Daily close idempotent/resumable | YES for existing OHLCV path; formal downstream closure NO |
| Readiness-aware official dataset publication | PARTIAL; Today gate fixed only in candidate |
| Today market current | PARTIAL; production has typed facts but missing formal signal dependencies |
| A9/Strength embedded or formal | NO; deferred/not separately persisted |
| Score and Grade | NO; deferred |
| Lifecycle | NO; unavailable baseline |
| Topic publication | YES through 2026-09-18 |
| Full formal Opportunity API/publication | NO; 503 fail-closed |
| Production readback | PARTIAL; API/Web reachable, exact Web SHA unavailable |
| Next trading-day automation | NOT PROVEN for complete formal pipeline |
| Owner checkout preserved | YES |

## 19. Machine status fields

```text
TASK_STATUS=BLOCKED
TODAY_FORMAL_READY=PARTIAL
TODAY_SIGNALS_FORMAL_DEPENDENCIES_COMPLETE=NO
A9_READY=DEFERRED_NOT_SEPARATELY_PERSISTED
DAILY_STRENGTH_READY=DEFERRED_NOT_SEPARATELY_PERSISTED
SCORE_READY=DEFERRED
GRADE_READY=DEFERRED
LIFECYCLE_READY=NO;LIFECYCLE_UNAVAILABLE_BASELINE
FORMAL_TOPIC_PUBLICATION_READY=YES_THROUGH_20260918
OPPORTUNITY_FORMAL_DAILY_RECOMMENDATION_READY=NO;OPTIONAL_SECTION_NOT_FORMAL
HISTORICAL_REPLAY_STATUS=CURRENT_THROUGH_20260918
NEXT_MISSING_TRADING_DAY=NONE
M1_COMPLETE=NO
PRODUCTION_FORMAL_PIPELINE_READY=NO_REMAINING_FORMAL_OPPORTUNITY_AUTHORITY_AND_LIFECYCLE_SCORE_BASELINE
OWNER_CHECKOUT_PRESERVED=YES
M2_STARTED=NO
```

## 20. Required next safe action

Supply and register the governed formal Score/Grade authority artifacts: approved policy record, approved Leader Set, explicit CORE authority, exact observation-as-of binding, and their lineage. Then run the bounded formal lifecycle replay and formal Opportunity provider/readback integration against those artifacts. Until that exists, keep formal Score/Grade/Lifecycle/Opportunity fail closed and do not promote the candidate to Production.

