# G2 分支與工作樹追溯盤點

**Task ID:** `TASK-DOC-WORKSTREAM-SYNC-20261112`
**TASK_TYPE:** `documentation`
**REQUIRED_TERMINAL_STATE:** `VALIDATED`
**盤點範圍:** GitHub 即時 main／遠端 refs／PR，以及 canonical repository 的本機 worktree audit。
**報告狀態:** G2 盤點驗收報告；最新狀態以本文最前方的 superseding checkpoint 為準，完整執行路由由 Roadmap 與 Work Orders 擁有。
**本次查核時間:** GitHub branches、main、open PR：2026-11-12 16:06:46Z（2026-11-13 00:06:46 Asia/Taipei）；全部 PR 歷史於 2026-11-12 16:16:03Z 前重查（2026-11-13 00:16:03 Asia/Taipei）；完整 Compare 核驗亦於該時間前完成。
**本機 worktree audit 時間:** 2026-11-12 15:57:21.786Z（2026-11-12 23:57:21.786 Asia/Taipei）。

> **最新狀態覆蓋（2026-11-13 06:32:08Z / 14:32:08 Asia/Taipei）：**本節是目前最新查核；下方 04:23 checkpoint 與清單保留為歷史證據。G2 仍 BLOCKED；Owner 已核准 G3 有界實作與 G2 並行，但 G3 尚未 canonicalize 或發布。

## 最新 G2 / G3 檢查點（2026-11-13 06:32 UTC）

### 即時來源

- GitHub branches 與 open PRs 於 2026-11-13 06:32:08 UTC 重查：main 與本機 origin/main 均為 f27a0c4fa189810c6caa01ad3f2944d7fd4919e2；另一遠端分支為 codex/integrate-worker-stock-add-branches-001，SHA 987adb61eb4c8422054b9c752724bc9932f208e8；open PR 數為 0。
- GitHub branches API 將 main 回報為 protected=false；可讀取的 repository rulesets 清單為空。直接查 classic branch-protection endpoint 回應 403 Resource not accessible by integration。因此 task-id-validation 是否為 required check **未能證實**，不得稱為具合併阻擋效果。

### 清理後本機狀態

- 2026-11-13 06:03 UTC 的唯讀盤點：16 個 worktree（14 DIRTY、2 CLEAN、3 detached、0 unreadable）。三個 detached worktree 均為 DIRTY。
- Canonical checkout codex/canonical-main-sync-20261112：HEAD 38eeeacc02a950d21d903d7c939d11c8492d6770，較 GitHub main ahead 6 / behind 0，33 個變更路徑。本機共有 39 個 branch refs，其中 26 個未附掛 worktree；未刪除任何 local 或 remote branch ref。
- 已移除 8 個乾淨的一般 worktree，並封存 1 個乾淨、由 Codex 管理的 worktree。另保留 2 個乾淨 worktree：目前對話的 primary checkout（0b8d01731b9685b117cb59f2259a897ae6b809e2）及含 ignored preview fixture apps/web/public/__preview.json 的預覽工作目錄。14 個髒 worktree 全部保留，沒有以名稱推斷可刪除性。

### Owner 授權的 worktree 清除範圍（以 2026-11-13 06:03 UTC 盤點為準）

| ID | Branch / HEAD SHA | 狀態 | Owner 指示的處置 |
|---|---|---|---|
| CWT-01 | codex/canonical-main-sync-20261112 / 38eeeacc02a950d21d903d7c939d11c8492d6770 | DIRTY (33) | 保留：固定 canonical repository，不可移除。 |
| CWT-02 | codex/governance-g0-g3-safe-integration / 0b8d01731b9685b117cb59f2259a897ae6b809e2 | CLEAN | 保留：目前對話的 primary checkout，Codex 保護不可移除。 |
| CWT-03 | detached / 9a0fa7ea541302cd64e2f60f17e3adf94854bad5 | DIRTY (1 untracked) | 移除工作樹；保留 branch refs（無 branch）。 |
| CWT-04 | codex/company-research-core-and-analysis-framework-20261019 / c22dae110572d3e0278f08cb21e42cc489d0d9ef | DIRTY (19; includes ignored .env.local) | 移除工作樹；分支保留。 |
| CWT-05 | detached / 8ab2a7f69d359cb6fbf42682f573c2e1b536cb03 | DIRTY (224; 137 untracked) | 移除工作樹；保留 branch refs（無 branch）。 |
| CWT-06 | codex/preview-production-release-candidate-001 / 0b32b7670c050dc793264859b2ab273d66a68d88 | CLEAN; ignored preview fixture present | 移除工作樹及該預覽副本；分支保留。 |
| CWT-07 | codex/publication-flow-v2-canonical-gate-unblock-003-validation / 76d34cb21742b23cdf966f459f928e539ffdf3bc | DIRTY (2 untracked reports) | 移除工作樹；分支保留。 |
| CWT-08 | codex/publication-flow-v2-end-to-end-production-recovery-008 / f9ee0bff1431fcbbdfa7127a6f396aa4fd4b7e95 | DIRTY (2) | 移除工作樹；分支保留。 |
| CWT-09 | codex/selection-vnext-attack-outcome-research-001 / e97f590cad497c0a23fb027fce39ec5891ea4bc1 | DIRTY (4) | 移除工作樹；分支保留。 |
| CWT-10 | codex/selection-vnext-benchmark-universe-executability-authority-001 / 4db4ec749ad1ab978573d1a326b4d28bdd9bbf6c | DIRTY (1) | 移除工作樹；分支保留。 |
| CWT-11 | codex/selection-vnext-pit-entry-access-authority-001 / 4d5190346f8177677d5e76d5a407c59db82e7aec | DIRTY (1) | 移除工作樹；分支保留。 |
| CWT-12 | codex/selection-vnext-pit-recovery-002 / 5ca32a2504cc8f54ea10cccda764090f77beb885 | DIRTY (2) | 移除工作樹；分支保留。 |
| CWT-13 | codex/selection-vnext-broad-pit-threshold-research-001 / 3fe3975cda724c30391ac8112c5190b71d5d749e | DIRTY (1) | 移除工作樹；分支保留。 |
| CWT-14 | codex/stock-research-bootstrap-v1 / 9852f03b4586572b13f744868b2aac4dbd33ff89 | DIRTY (22; includes untracked skill/research package) | 移除工作樹；分支保留。 |
| CWT-15 | codex/stock-topic-impact-direction-evidence-ui-001 / b17355eaba3573ed43e48e25d98ffa89506327c1 | DIRTY (16) | 移除工作樹；分支保留。 |
| CWT-16 | detached / 8383a5ee5d601e5da6a277a3ccf12f970c5342ec | DIRTY (2 untracked reports) | 移除工作樹；保留 branch refs（無 branch）。 |

此清單保留分支與提交溯源；Owner 明確要求移除非必要工作樹，因此上述 14 個非 protected 工作樹將被移除。分支 refs 不在本次清理範圍。
### G2 / G3 結論

- G2 出口仍 **BLOCKED**：14 個髒 worktree 與 26 個未附掛 refs 尚未完成逐項 owner、work order、來源 SHA、證據及處置對應。未解項目均維持保留；本檢查點不代表可清理。
- G3 有界實作可依 Owner 已核准方向與 G2 並行。乾淨本機候選 SHA 為 0b8d01731b9685b117cb59f2259a897ae6b809e2，較 origin/main ahead 3；既有工作單記錄其 focused validation。此候選仍未 canonicalize，required-check 設定也尚未證實。
- 本次未 push、merge、deploy、修改 Production、刪除 branch refs 或變更 NEXT_TASK。
> **前次狀態覆蓋（2026-11-13 04:23:43Z / 12:23:43 Asia/Taipei）：**以下較早的盤點與結論皆保留為其查核時點的歷史證據；若與本節不同，以本節為目前最近一次唯讀盤點。G2 仍為 BLOCKED。Owner 已指示在剩餘 G2 工作並行下開始 G3；G3 僅為本機未提交候選，未 canonicalize、未發布。

## 前次 G2 / G3 檢查點（2026-11-13 04:23 UTC）

### 即時來源與整合基線

- GitHub 即時查核於 2026-11-13 04:21 UTC：`main` 與本機 `origin/main` 均為 `f27a0c4fa189810c6caa01ad3f2944d7fd4919e2`；唯一遠端 feature ref 為 `codex/integrate-worker-stock-add-branches-001`，SHA `987adb61eb4c8422054b9c752724bc9932f208e8`；同時查得開啟中的 PR 數為 0。
- PR #107 head `987adb61eb4c8422054b9c752724bc9932f208e8` 是 canonical HEAD `38eeeacc02a950d21d903d7c939d11c8492d6770` 的祖先，故該 PR 的提交已在本機整合歷史中。
- G1/G2 來源分支提交 `4da1cbc1d88385984fcb6ebd14def384dd1df4fd` 不是 canonical HEAD 的祖先。其較舊、重疊的治理文字以目前較新的 canonical 工作副本為準；該來源的 `.github/workflows/deploy.yml` 變更不在本次授權範圍，未整合。
- canonical checkout：分支 `codex/canonical-main-sync-20261112`，HEAD `38eeeacc02a950d21d903d7c939d11c8492d6770`，相對 GitHub main ahead 6 / behind 0；audit 時工作樹有 32 個變更路徑。該 32 項含既有、與本任務無關差異；不得將全部差異歸因於本任務或整批提交。

### 本機 worktree 逐項清單（匿名化路徑）

唯讀 audit：2026-11-13 04:23:43.707Z；以 `origin/main` SHA `f27a0c4fa189810c6caa01ad3f2944d7fd4919e2` 比較。`ahead/behind` 為本地 HEAD 相對基準的提交數。分支名稱僅供定位，不作為工作單或負責人證據。除明確列出的治理來源外，歸屬未能由本次可讀證據確認。

| ID | Branch / HEAD SHA | 工作樹 | ahead/behind | Task-ID 證據／處置 |
|---|---|---:|---:|---|
| CWT-01 | `codex/canonical-main-sync-20261112` / `38eeeacc02a950d21d903d7c939d11c8492d6770` | DIRTY (32) | 6/0 | `TASK-DOC-WORKSTREAM-SYNC-20261112` 為本次明確工作單；32 路徑並非全屬本任務，逐項歸屬仍需保留。 |
| CWT-02 | `codex/docs-workstream-sync-001` / `4da1cbc1d88385984fcb6ebd14def384dd1df4fd` | CLEAN | 1/0 | G1/G2 文件來源候選；與目前較新 canonical 文件有版本差異；保留，不清理。 |
| CWT-03 | `codex/stock-add-workflow-integration-001` / `f2f038deef6dd837175f438f381305642b3b0824` | CLEAN | 18/23 | 未匹配明確工作單／負責人；保留，待 owner disposition。 |
| CWT-04 | DETACHED / `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | DIRTY (1) | 10/72 | 未匹配；保留。 |
| CWT-05 | `codex/topic-semiconductor-facilities-flow-20261101` / `5d646a58a46eb0064b5b5bc85969caa6fe14801c` | CLEAN | 1/41 | 未匹配明確工作單／負責人；保留。 |
| CWT-06 | `codex/company-research-mainline-integration` / `faf4e3cbedb22c2cf8c399c0b31c18b5166012d1` | CLEAN | 1/56 | 未匹配明確工作單／負責人；保留。 |
| CWT-07 | `codex/company-research-core-and-analysis-framework-20261019` / `c22dae110572d3e0278f08cb21e42cc489d0d9ef` | DIRTY (19) | 49/86 | 未匹配明確工作單／負責人；保留。 |
| CWT-08 | DETACHED / `8ab2a7f69d359cb6fbf42682f573c2e1b536cb03` | DIRTY (224) | 42/433 | 未匹配；大幅髒差異，保留且不可清理。 |
| CWT-09 | `codex/preview-production-release-candidate-001` / `0b32b7670c050dc793264859b2ab273d66a68d88` | CLEAN | 7/86 | 未匹配明確工作單／負責人；保留。 |
| CWT-10 | `codex/publication-flow-v2-canonical-gate-unblock-003-validation` / `76d34cb21742b23cdf966f459f928e539ffdf3bc` | DIRTY (2) | 5/79 | 未匹配明確工作單／負責人；保留。 |
| CWT-11 | `codex/publication-flow-v2-canonical-reconciliation-002` / `40be6f0cecedd83b3f70271acd05ba2aa297cc24` | CLEAN | 3/79 | 未匹配明確工作單／負責人；保留。 |
| CWT-12 | `codex/publication-flow-v2-end-to-end-production-recovery-008` / `f9ee0bff1431fcbbdfa7127a6f396aa4fd4b7e95` | DIRTY (2) | 2/58 | 未匹配明確工作單／負責人；保留。 |
| CWT-13 | `codex/publication-flow-v2-recovery-continuation-009` / `92ebd4e78acb588aaadeed65c406011fd2d3306c` | CLEAN | 9/56 | 未匹配明確工作單／負責人；保留。 |
| CWT-14 | `codex/selection-vnext-attack-outcome-research-001` / `e97f590cad497c0a23fb027fce39ec5891ea4bc1` | DIRTY (4) | 0/85 | 提交已在 `origin/main` 祖先，但髒差異／owner 未知；保留，不據此判定完成。 |
| CWT-15 | `codex/selection-vnext-benchmark-universe-executability-authority-001` / `4db4ec749ad1ab978573d1a326b4d28bdd9bbf6c` | DIRTY (1) | 1/85 | 未匹配明確工作單／負責人；保留。 |
| CWT-16 | `codex/selection-vnext-broad-pit-threshold-stability-001` / `a01a3a23238f15fcb9c71c54abab7aeb45fc00f9` | CLEAN | 8/72 | 未匹配明確工作單／負責人；保留。 |
| CWT-17 | `codex/selection-vnext-pit-entry-access-authority-001` / `4d5190346f8177677d5e76d5a407c59db82e7aec` | DIRTY (1) | 5/85 | 未匹配明確工作單／負責人；保留。 |
| CWT-18 | `codex/selection-vnext-pit-recovery-002` / `5ca32a2504cc8f54ea10cccda764090f77beb885` | DIRTY (2) | 8/85 | 未匹配明確工作單／負責人；保留。 |
| CWT-19 | `codex/selection-vnext-v0-event-transition-closure-002` / `38aae3834485645f29d590edae0d12ca7651d0bd` | CLEAN | 28/72 | 未匹配明確工作單／負責人；保留。 |
| CWT-20 | `codex/selection-vnext-broad-pit-threshold-research-001` / `3fe3975cda724c30391ac8112c5190b71d5d749e` | DIRTY (1) | 10/85 | 未匹配明確工作單／負責人；保留。 |
| CWT-21 | `codex/stock-research-bootstrap-v1` / `9852f03b4586572b13f744868b2aac4dbd33ff89` | DIRTY (22) | 18/58 | 未匹配明確工作單／負責人；保留。 |
| CWT-22 | `codex/stock-topic-impact-direction-evidence-ui-001` / `b17355eaba3573ed43e48e25d98ffa89506327c1` | DIRTY (16) | 2/79 | 未匹配明確工作單／負責人；保留。 |
| CWT-23 | DETACHED / `8383a5ee5d601e5da6a277a3ccf12f970c5342ec` | DIRTY (2) | 4/79 | 未匹配；保留。 |
| CWT-24 | `codex/worker-formal-bounded-20261013` / `2d1998e1ce8ce6b43516e4acccb59579002be36e` | CLEAN | 9/49 | 未匹配明確工作單／負責人；保留。 |

總計 24 個 worktree：14 DIRTY、10 CLEAN、3 DETACHED、0 unreadable。上述 32 個 canonical dirty paths 已計入 CWT-01 的 DIRTY (32)，不是另加一個 worktree。

### 未附掛於 worktree 的本機分支 refs

2026-11-13 04:21 UTC 清點到 38 個本機 branch refs，其中 21 個附掛於具名 worktree；以下 17 個未附掛。僅記錄 refs 與 SHA，不代表可以刪除。特別是本機 `main` 仍指向舊 SHA `61f9cf8fc1a4a71aad9fb4e38c0061171be1fd6e`，它不等於即時 `origin/main`。

| 本機 ref | SHA | 處置 |
|---|---|---|
| `codex/company-research-core-and-analysis-framework-20261019-before-sites-reconcile` | `e3fc858eb6840a90a85b76f2f8047673e2eb6b5b` | OWNER_DECISION_REQUIRED |
| `codex/company-research-core-and-analysis-framework-20261019-publish-clean` | `c0aa9739d474f716c54656ff2349423653992081` | OWNER_DECISION_REQUIRED |
| `codex/integrate-worker-stock-add-branches-001` | `987adb61eb4c8422054b9c752724bc9932f208e8` | 已是 canonical HEAD 祖先；ref 保留 |
| `codex/one-shot-delivery-governance-closure-001` | `deea8325bb63c58e6e6c1f3625df155ca6dde218` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-broad-pit-threshold-stability-final-001` | `ac7157ccf15315b7a3374082bed3c5be0a84db7b` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-entry-quality-contract-002` | `17f3cb597593c21a8bd38edb858d786d607d3245` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-external-literature-001` | `ef6d535e4118df2f283904ce4e9b35bd8ead2863` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-independent-setup-validation-001` | `94adb752cf01f58123686ea9c7d507e7983565ec` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-pit-membership-interval-closure-003` | `3fe3975cda724c30391ac8112c5190b71d5d749e` | OWNER_DECISION_REQUIRED |
| `codex/selection-vnext-v0-policy-design-001` | `919048aa790a82e746657c6e27fbc2d08fe3a6a0` | OWNER_DECISION_REQUIRED |
| `codex/stock-research-integration-001` | `3acf02a953e49477e3bff9f1a71f80ad7b3456fb` | OWNER_DECISION_REQUIRED |
| `codex/task-021-bounded-follow-up` | `6e5ac99d157c908a7237072a67099d781782cfb4` | OWNER_DECISION_REQUIRED |
| `codex/task-021-canonical-reconciliation` | `6e5ac99d157c908a7237072a67099d781782cfb4` | OWNER_DECISION_REQUIRED |
| `codex/task-021-canonical-reconciliation-v2` | `57a3fcb166a8b80c59fbb90144f16d390e455093` | OWNER_DECISION_REQUIRED |
| `codex/task-025-taiex-covered-distribution` | `6c211de0f27bb1d88ad62f84f94a850fdff13c9e` | OWNER_DECISION_REQUIRED |
| `codex/task-preview-staging-release-lane-001` | `e86bc65a9700c2a917fa569994dbc5f74cdc6797` | OWNER_DECISION_REQUIRED |
| `main` | `61f9cf8fc1a4a71aad9fb4e38c0061171be1fd6e` | STALE_LOCAL_REF; preserve until separately reconciled |

### G2 / G3 disposition at this checkpoint

- G2 exit remains **BLOCKED**: 14 worktrees are dirty, 3 are detached, 17 local refs are unattached, and most worktree/ref rows still lack exact task/owner/disposition evidence. This report does not authorize removal.
- G3 subphase declaration: `TASK_TYPE=implementation`, `REQUIRED_TERMINAL_STATE=VALIDATED`. The local candidate validates explicit PR work-order metadata; `transition=YES` requires all declared rows to change; same-repository PRs merged into `main` create a draft evidence PR with merge SHA/date. It does not modify task terminal state or roadmap priority.
- G3 focused checks passed locally: 7 metadata/parser tests plus syntax checks for the shared parser, PR validator, merge-evidence recorder, and workstream snapshot. The candidate is not committed or in GitHub `main`. `task-id-validation` has not been verified as a required branch-protection check, so it is not yet a merge blocker.
- This checkpoint did not commit, push, merge, deploy, query or mutate Production, clean branches/worktrees, or change `NEXT_TASK`.

## 較早查核結論摘要（2026-11-12；歷史證據）

- GitHub 即時 `main` 與本機 `origin/main` 相同：`f27a0c4fa189810c6caa01ad3f2944d7fd4919e2`。
- GitHub 有 46 個分支 refs（含 `main`，另 45 個功能 refs）、107 筆 PR 歷史；重查時有 5 筆開啟 PR。
- 45 個功能 refs 對同一 `main` SHA 執行 GitHub Compare：26 個 `behind`、19 個 `diverged`。這是提交圖的 ancestry 資訊，不等同 patch 等價或可刪除證明。
- 45 個本機 worktree：18 個 dirty、27 個 clean、6 個 detached/unbranched、0 個讀取失敗。按分支名與即時 refs 對照：6 個 HEAD 與遠端 tip 相同、3 個不同、30 個沒有目前同名遠端 ref、6 個 detached。
- 45 個功能 refs 中，41 個可按 PR head branch 找到 PR 歷史、4 個沒有同名 PR；41 個當中 40 個現行 ref SHA 等於至少一筆相關 PR head SHA，另 1 個不同。分支表列出每筆 PR 的 head SHA 和是否等於目前 tip。
- 5 筆開啟 PR 都沒有 assignee 或 requested reviewer；PR author 是可查的提交者欄位，但不能據此認定 accountable owner。#86 文字宣告的 Task ID 不存在於目前工作訂單登錄。
- 目前唯一由本機工作樹明確對應本治理工作的是 WT-08（本次候選工作樹）；其 23 項 dirty 變更並非都能歸屬本任務。其餘工作樹的 owner／Task ID 以未記錄或未匹配呈現，不以分支命名推測。

本盤點是現況證據，不代表任何分支、PR、提交或 worktree 已過時、可合併、可刪除或可清理。

## 查核方法與限制

- GitHub 以 repository branches、`commits/main`、`pulls?state=open`、`pulls?state=all` 與 Compare API 為來源。Branches/main/open PR 在 16:06:46Z 即時重查；全部 PR 歷史在 16:16:03Z 前完成重查。兩次 branches/main 讀取間 46 個 refs 的 SHA 及 main SHA 未變。
- 本機執行 `node infra/scripts/governance/audit_worktrees.mjs` 的唯讀盤點；基準為本機 `origin/main` SHA。未執行 fetch、checkout、reset、stash、clean 或任何工作樹／分支變更。
- 本機 `origin/main` ref 與即時 GitHub main 一致。GitHub Compare 的 ahead/behind 數字依精確記錄的遠端 tip SHA 計算。
- PR 歷史關聯依 PR 的 `head.ref`；Task ID 只在 PR 文字或現有工作訂單明確交叉引用時才連結。PR author 不視為 owner。
- 報告用 WT-01…WT-45 匿名代碼取代本機路徑。代碼僅在本次 audit 內識別工作樹；完整路徑未寫入此公開報告。
- 無法從現有證據確定的責任、變更歸屬、worktree 年齡與 patch 等價均標為未記錄／未知；沒有據此推定清理資格。

## GitHub 遠端分支逐項清單

Compare 欄為 `status (ahead/behind)`，以遠端 tip 相對於 GitHub main 計。PR 標記：`O` open、`M` merged、`C` closed but not merged；`=tip` 表示 PR head SHA 等於目前遠端 ref，`≠tip` 表示不同。所有 SHA 均為完整值。Task ID 僅採明確文字證據；「未能精確匹配」不代表沒有負責人或任務，只表示目前登錄無證據可連結。

| 遠端分支 | 遠端 tip SHA | 對 main 的提交關係 | 同名 PR（狀態、tip 關係、PR head SHA） | 精確 Task ID 證據 | 負責人 |
|---|---|---|---|---|---|
| `main` | `f27a0c4fa189810c6caa01ad3f2944d7fd4919e2` | 基準 | — | 非任務分支 | — |
| `codex/approved-formal-topic-membership-20261029` | `48327a98a17ef2c2dcc99d0083ca9548dd37f024` | behind (0/48) | [#96](https://github.com/Xiezhou0828/topicpilot-platform/pull/96) M=tip `48327a98a17ef2c2dcc99d0083ca9548dd37f024` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/current-day-health-018` | `b251904a5620ce816f3fa36801e761b7e1189777` | diverged (1/176) | [#37](https://github.com/Xiezhou0828/topicpilot-platform/pull/37) M=tip `b251904a5620ce816f3fa36801e761b7e1189777`<br>[#35](https://github.com/Xiezhou0828/topicpilot-platform/pull/35) M≠tip `0cd163106c2365369ac405afcbfc668df5dc4262`<br>[#34](https://github.com/Xiezhou0828/topicpilot-platform/pull/34) M≠tip `cc8034ba95b97ba517d275f51059f9acc7a7f938`<br>[#32](https://github.com/Xiezhou0828/topicpilot-platform/pull/32) M≠tip `3d2817f15ec3c5792c96c13359c93ba09ae29e12` | 宣告未登錄：TASK-POST-CLOSE-20260930-CURRENT-DAY-HEALTH-018 | 未記錄 |
| `codex/daily-formal-publication-activation-closure-001` | `27c13431eca64e5c0ec9372ef4ea7e0de2e482da` | behind (0/86) | [#75](https://github.com/Xiezhou0828/topicpilot-platform/pull/75) M=tip `27c13431eca64e5c0ec9372ef4ea7e0de2e482da` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/daily-formal-publication-activation-evidence-001` | `3f90d5a7687336986c28b43ccef7c1fa4e6ab989` | behind (0/90) | [#74](https://github.com/Xiezhou0828/topicpilot-platform/pull/74) M=tip `3f90d5a7687336986c28b43ccef7c1fa4e6ab989` | 宣告未登錄：TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-PRODUCTION-ACTIVATION-001 | 未記錄 |
| `codex/daily-formal-publication-production-activation-001` | `1e992e3dc26900777cbbc9b654728dfa385ff168` | behind (0/103) | [#72](https://github.com/Xiezhou0828/topicpilot-platform/pull/72) M=tip `1e992e3dc26900777cbbc9b654728dfa385ff168` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/expire-stale-cross-scope-post-close-20261104` | `a06a0313de4d101e765ae14a4e33087ee0f15458` | behind (0/35) | [#103](https://github.com/Xiezhou0828/topicpilot-platform/pull/103) M=tip `a06a0313de4d101e765ae14a4e33087ee0f15458` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/fix-worker-release-precondition-021` | `c918a3523339da1db1b8f4842d2164fa84c9fc4f` | diverged (1/171) | [#41](https://github.com/Xiezhou0828/topicpilot-platform/pull/41) M=tip `c918a3523339da1db1b8f4842d2164fa84c9fc4f` | 宣告未登錄：TASK-POST-CLOSE-20260930-EXACT-SHA-RECOVERY-AND-VALIDATION-021 | 未記錄 |
| `codex/formal-dimension-release-blocker-reconciliation-002` | `b17355eaba3573ed43e48e25d98ffa89506327c1` | diverged (2/79) | [#77](https://github.com/Xiezhou0828/topicpilot-platform/pull/77) O=tip `b17355eaba3573ed43e48e25d98ffa89506327c1` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/formal-strength-history-shape-20261029` | `06423bd9058920b0591f182b69eb4f6977f04cc3` | diverged (1/50) | [#95](https://github.com/Xiezhou0828/topicpilot-platform/pull/95) M=tip `06423bd9058920b0591f182b69eb4f6977f04cc3` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/integrate-worker-stock-add-branches-001` | `987adb61eb4c8422054b9c752724bc9932f208e8` | behind (0/1) | [#107](https://github.com/Xiezhou0828/topicpilot-platform/pull/107) M=tip `987adb61eb4c8422054b9c752724bc9932f208e8` | TASK-LIVE-PARTIAL-COVERAGE-20261028（工作訂單明列此 PR） | 未記錄 |
| `codex/legacy-extract-reconciliation-20261005` | `a36fb75fb7d508dc78983696981483ffd1cd7068` | diverged (1/120) | [#68](https://github.com/Xiezhou0828/topicpilot-platform/pull/68) O=tip `a36fb75fb7d508dc78983696981483ffd1cd7068` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/live-tpex-limited-gap-20261029` | `4ccca87a833eea2a04f786253adcc2c7d6a79557` | behind (0/51) | [#94](https://github.com/Xiezhou0828/topicpilot-platform/pull/94) M=tip `4ccca87a833eea2a04f786253adcc2c7d6a79557` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/post-close-fetch-outside-transaction-20261103` | `cc9bf59a3a47b64489835a9d53485b10dfd7e353` | behind (0/37) | [#102](https://github.com/Xiezhou0828/topicpilot-platform/pull/102) M=tip `cc9bf59a3a47b64489835a9d53485b10dfd7e353` | TASK-LIVE-PARTIAL-COVERAGE-20261028（工作訂單明列此 PR） | 未記錄 |
| `codex/post-close-float-canonicalization-reconciliation-001` | `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | diverged (10/72) | [#76](https://github.com/Xiezhou0828/topicpilot-platform/pull/76) O=tip `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/post-close-schedule-freeze-021` | `d0f39c8ade4e39da3f1f2e2c5bca60a4a5305299` | diverged (1/172) | [#40](https://github.com/Xiezhou0828/topicpilot-platform/pull/40) M=tip `d0f39c8ade4e39da3f1f2e2c5bca60a4a5305299` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/publication-flow-v2-production-blocker-remediation-007-diag2` | `a6b7077c8e1a07d11d11d960bbf9b1872d2d2b39` | diverged (1/58) | [#84](https://github.com/Xiezhou0828/topicpilot-platform/pull/84) O=tip `a6b7077c8e1a07d11d11d960bbf9b1872d2d2b39`<br>[#83](https://github.com/Xiezhou0828/topicpilot-platform/pull/83) M≠tip `2513829c40b411d008ad5ca21ba0703b9df2d189` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/publication-flow-v2-production-cutover-005-integration` | `d8f36d7b84d96c2d2645be89971859479292f2cc` | behind (0/64) | [#78](https://github.com/Xiezhou0828/topicpilot-platform/pull/78) M=tip `d8f36d7b84d96c2d2645be89971859479292f2cc` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/publication-flow-v2-runtime-closure-006` | `764fb3ccec140ed013f6005c5f3f4b95e26eb925` | behind (0/62) | [#79](https://github.com/Xiezhou0828/topicpilot-platform/pull/79) M=tip `764fb3ccec140ed013f6005c5f3f4b95e26eb925` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/release/api-only-f6d4700` | `f6d4700d82bf4c3b8d4577e2394c4a3cd4ccee2e` | diverged (1/56) | —（無同名 PR） | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/stock-add-authority-readback-guard-fix` | `7eaf60f02ea614aaa331cd38be963309dc234080` | behind (0/53) | [#91](https://github.com/Xiezhou0828/topicpilot-platform/pull/91) M=tip `7eaf60f02ea614aaa331cd38be963309dc234080` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/stock-add-optional-market-metrics-20261106` | `1f76bbc36554d320cb4a492f9c2182ef18024667` | behind (0/26) | [#105](https://github.com/Xiezhou0828/topicpilot-platform/pull/105) M=tip `1f76bbc36554d320cb4a492f9c2182ef18024667` | TASK-LIVE-PARTIAL-COVERAGE-20261028（工作訂單明列此 PR） | 未記錄 |
| `codex/stock-add-topic-candidate-readback` | `7b42301290f8ddde60539c0400420eb69a8dc5b5` | diverged (1/45) | —（無同名 PR） | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/structural-role-production-read-boundary` | `51a74279c742e8ffaf769aba73031e62876a0e2d` | diverged (16/250) | —（無同名 PR） | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-021-authority-checkpoint-followup` | `f528bbe54782963ba71ffeb21864d43c2580f5a0` | behind (0/155) | [#52](https://github.com/Xiezhou0828/topicpilot-platform/pull/52) M=tip `f528bbe54782963ba71ffeb21864d43c2580f5a0` | 宣告未登錄：TASK-021 | 未記錄 |
| `codex/task-021-report` | `93d2673d74b084f00fa97876d504563357157f4c` | diverged (1/170) | [#42](https://github.com/Xiezhou0828/topicpilot-platform/pull/42) M=tip `93d2673d74b084f00fa97876d504563357157f4c` | 宣告未登錄：TASK-021 | 未記錄 |
| `codex/task-022-incident-report` | `7dc61c1e82d44e32c1c54424b69817c72b48837f` | diverged (2/168) | [#44](https://github.com/Xiezhou0828/topicpilot-platform/pull/44) C=tip `7dc61c1e82d44e32c1c54424b69817c72b48837f` | 宣告未登錄：TASK-022 | 未記錄 |
| `codex/task-022-incident-report-final` | `f977fad1fbb52cd9bfec71a9765e6627a3af1422` | diverged (1/168) | [#45](https://github.com/Xiezhou0828/topicpilot-platform/pull/45) M=tip `f977fad1fbb52cd9bfec71a9765e6627a3af1422` | 宣告未登錄：TASK-022 | 未記錄 |
| `codex/task-022-public-today-fetch` | `4d52aa1475493e80d6e7146b3ac6283046866bea` | diverged (2/169) | [#43](https://github.com/Xiezhou0828/topicpilot-platform/pull/43) M=tip `4d52aa1475493e80d6e7146b3ac6283046866bea` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-024-canonical-closure` | `cc723d659fc65b6950da44e448445d8fb4f9a861` | behind (0/160) | [#51](https://github.com/Xiezhou0828/topicpilot-platform/pull/51) M=tip `cc723d659fc65b6950da44e448445d8fb4f9a861` | 宣告未登錄：TASK-024 | 未記錄 |
| `codex/task-024-trading-status-authority` | `263c0b2a44a04c78762b665ac3f6320e44aae08b` | behind (0/162) | [#50](https://github.com/Xiezhou0828/topicpilot-platform/pull/50) M=tip `263c0b2a44a04c78762b665ac3f6320e44aae08b` | 宣告未登錄：TASK-024, TASK-023, TASK-021 | 未記錄 |
| `codex/task-history-recovery-scope-separation-20261002` | `7bd9867932b7cef9a988949b2e522bbea0f26b50` | behind (0/150) | [#55](https://github.com/Xiezhou0828/topicpilot-platform/pull/55) M=tip `7bd9867932b7cef9a988949b2e522bbea0f26b50` | 宣告未登錄：TASK-HISTORY-RECOVERY-SCOPE-SEPARATION-AND-CURRENT-DAY-PUBLICATION-BOUNDARY-20261002 | 未記錄 |
| `codex/task-post-close-readiness-020` | `a1e21b8fb5db71f85a87465a9ec7279229baa82c` | diverged (2/174) | [#39](https://github.com/Xiezhou0828/topicpilot-platform/pull/39) M=tip `a1e21b8fb5db71f85a87465a9ec7279229baa82c` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-preview-review-environment-001` | `47d870870a1a4f12404da8a12e8bb3efbcefa409` | behind (0/106) | [#71](https://github.com/Xiezhou0828/topicpilot-platform/pull/71) M=tip `47d870870a1a4f12404da8a12e8bb3efbcefa409` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-preview-review-environment-001-canonical-report` | `72fa5b541c4884458e2eb38f309d1173c376e3b4` | behind (0/94) | [#73](https://github.com/Xiezhou0828/topicpilot-platform/pull/73) M=tip `72fa5b541c4884458e2eb38f309d1173c376e3b4` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-preview-staging-release-lane-001-canonical` | `79b7179bdfc4891c4370f1db1005ee7ba4293bf9` | behind (0/115) | [#69](https://github.com/Xiezhou0828/topicpilot-platform/pull/69) M=tip `79b7179bdfc4891c4370f1db1005ee7ba4293bf9` | 宣告未登錄：TASK-PREVIEW-STAGING-RELEASE-LANE-001 | 未記錄 |
| `codex/task-preview-staging-release-lane-001-closure` | `e79d04a7c66d81e2d814c860b237e51f67e58eaf` | behind (0/113) | [#70](https://github.com/Xiezhou0828/topicpilot-platform/pull/70) M=tip `e79d04a7c66d81e2d814c860b237e51f67e58eaf` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/task-today-20261002-final-production-publication` | `3bb0f8c6123784c4f35a31c1521cfdd5206b3bf9` | behind (0/121) | [#67](https://github.com/Xiezhou0828/topicpilot-platform/pull/67) M=tip `3bb0f8c6123784c4f35a31c1521cfdd5206b3bf9`<br>[#66](https://github.com/Xiezhou0828/topicpilot-platform/pull/66) M≠tip `a23ef4679a7c4f0c237fc750cd87691cea15a749`<br>[#65](https://github.com/Xiezhou0828/topicpilot-platform/pull/65) M≠tip `9dcea1cf163f40b4e95725e4d8afb35700627d0b`<br>[#64](https://github.com/Xiezhou0828/topicpilot-platform/pull/64) M≠tip `2e887dc7e22365c1a43a11d7937c85b1fae3bfd1`<br>[#63](https://github.com/Xiezhou0828/topicpilot-platform/pull/63) M≠tip `6a9ffab5886e732ad47a9fcaddc098760d11a85b`<br>[#62](https://github.com/Xiezhou0828/topicpilot-platform/pull/62) M≠tip `b40bf927da4b1f718512811205c1610ed7871e72`<br>[#61](https://github.com/Xiezhou0828/topicpilot-platform/pull/61) M≠tip `b3bd53c973d08786d50775b8662d0da29a811e1c`<br>[#60](https://github.com/Xiezhou0828/topicpilot-platform/pull/60) M≠tip `872c66f95d09f9ef0415c1d015f4c91389a1b86e`<br>[#59](https://github.com/Xiezhou0828/topicpilot-platform/pull/59) M≠tip `e50ac6225106a97cb0ce7fa947a746b05a191da4`<br>[#58](https://github.com/Xiezhou0828/topicpilot-platform/pull/58) M≠tip `6688fa14f1b24b4c0515c970f1955cb7b3f83866` | 宣告未登錄：TASK-TODAY-20261002-FINAL-PRODUCTION-PUBLICATION | 未記錄 |
| `codex/task-today-closure-task021-production-20261002` | `7b12d9522eee83c1c154d42da4fdc0efd1aed4b6` | behind (0/152) | [#54](https://github.com/Xiezhou0828/topicpilot-platform/pull/54) M=tip `7b12d9522eee83c1c154d42da4fdc0efd1aed4b6` | 宣告未登錄：TASK-021, TASK-TODAY-CLOSURE-TASK021-PRODUCTION-END-TO-END-20261002 | 未記錄 |
| `codex/task-today-final-closure-reconstruct-task025-20261003` | `17a5b8e59552e9afc63620ac753895cb682c6e68` | behind (0/144) | [#56](https://github.com/Xiezhou0828/topicpilot-platform/pull/56) M=tip `17a5b8e59552e9afc63620ac753895cb682c6e68` | 宣告未登錄：TASK-025, TASK-TODAY-FINAL-CLOSURE-RECONSTRUCT-TASK025-SCOPE-20261003 | 未記錄 |
| `codex/task-today-final-closure-worker-sites-20261003` | `82412efd7f33cdc80a706c92af325f6fe609c539` | behind (0/142) | [#57](https://github.com/Xiezhou0828/topicpilot-platform/pull/57) M=tip `82412efd7f33cdc80a706c92af325f6fe609c539` | 宣告未登錄：TASK-WORKER-COLD-IMPORT-SUCCESSOR-VALIDATION-20261003 | 未記錄 |
| `codex/topic-partial-quote-20261110` | `0508374c2dadd28ffc8019c7dc8ead9eb3f20105` | behind (0/24) | [#106](https://github.com/Xiezhou0828/topicpilot-platform/pull/106) M=tip `0508374c2dadd28ffc8019c7dc8ead9eb3f20105` | TASK-LIVE-PARTIAL-COVERAGE-20261028（工作訂單明列此 PR） | 未記錄 |
| `codex/topic-stock-design-restoration` | `6cdf9ffd4134574e877b594c70c5189b237f1e6f` | behind (0/29) | [#104](https://github.com/Xiezhou0828/topicpilot-platform/pull/104) M=tip `6cdf9ffd4134574e877b594c70c5189b237f1e6f` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/topicpilot-local-preview-canonical-delivery-002` | `e8a570c4fc9b2242ce0c37dd2198ff065f5997c6` | diverged (5/56) | [#86](https://github.com/Xiezhou0828/topicpilot-platform/pull/86) O=tip `e8a570c4fc9b2242ce0c37dd2198ff065f5997c6` | 宣告未登錄：TASK-TOPICPILOT-GITHUB-DELIVERY-AND-LOCAL-WORKTREE-RETIREMENT-003 | 未記錄 |
| `codex/worker-db-session-recovery-20261103` | `b933494802fdf8e389bf36c09f27697365398307` | diverged (1/39) | [#101](https://github.com/Xiezhou0828/topicpilot-platform/pull/101) M≠tip `f7d06ff446d6dc8dabcd267b2cc0f9175df8d24a` | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |
| `codex/worker-tpex-recovery-20261013` | `6a85d569f1fc7731df9121402b5274e19712fe9a` | diverged (2/49) | —（無同名 PR） | 未能由目前工作訂單／PR 文字精確匹配 | 未記錄 |

## 開啟中的 PR 逐項清單

PR 與 head branch/SHA 於查核時間即時讀取。requested reviewer 與 assignee 欄位均為空；author 不代表已指派負責人。PR #86 的 Task ID 被宣告但未登錄；其餘 open PR 未宣告 Task ID。

| PR | 標題 | head branch | 精確 head SHA | 最後更新 | Author | Assignee | Requested reviewer | Task ID 狀態 |
|---|---|---|---|---|---|---|---|---|
| [#86](https://github.com/Xiezhou0828/topicpilot-platform/pull/86) | [Draft] TopicPilot local preview and Company Research V3 delivery | `codex/topicpilot-local-preview-canonical-delivery-002` | `e8a570c4fc9b2242ce0c37dd2198ff065f5997c6` | 2026-10-12T07:54:46Z | `Xiezhou0828` | 無 | 無 | 未登錄：TASK-TOPICPILOT-GITHUB-DELIVERY-AND-LOCAL-WORKTREE-RETIREMENT-003 |
| [#84](https://github.com/Xiezhou0828/topicpilot-platform/pull/84) | fix(api): serialize persisted Topic strength dates | `codex/publication-flow-v2-production-blocker-remediation-007-diag2` | `a6b7077c8e1a07d11d11d960bbf9b1872d2d2b39` | 2026-10-09T12:03:12Z | `Xiezhou0828` | 無 | 無 | 未宣告 |
| [#77](https://github.com/Xiezhou0828/topicpilot-platform/pull/77) | ops: purge retired topic identities and preserve migration chain | `codex/formal-dimension-release-blocker-reconciliation-002` | `b17355eaba3573ed43e48e25d98ffa89506327c1` | 2026-10-08T08:51:46Z | `Xiezhou0828` | 無 | 無 | 未宣告 |
| [#76](https://github.com/Xiezhou0828/topicpilot-platform/pull/76) | fix: recover TPEx natural post-close publication | `codex/post-close-float-canonicalization-reconciliation-001` | `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | 2026-10-08T03:33:00Z | `Xiezhou0828` | 無 | 無 | 未宣告 |
| [#68](https://github.com/Xiezhou0828/topicpilot-platform/pull/68) | feat: fail-closed formal Topic Snapshot consumer | `codex/legacy-extract-reconciliation-20261005` | `a36fb75fb7d508dc78983696981483ffd1cd7068` | 2026-10-04T19:50:25Z | `Xiezhou0828` | 無 | 無 | 未宣告 |

## 本機 worktree 逐項清單

Ahead/behind 以各 worktree HEAD 相對於 audit 時本機 `origin/main` 計；dirty 數為 audit script 偵測的變更路徑數。遠端關係只表示當下同名 ref 是否存在及 tip SHA 是否相同。PR 欄列出同名分支的 PR；detached 或不同名分支也會列出 head SHA 與 worktree HEAD 完全相同的 PR。owner 未由 Git worktree 資訊提供，故不從帳戶或分支名稱推定。WT 代碼排序只供本報告定位，不包含本機路徑。

| ID | 分支／狀態 | HEAD SHA | 工作樹 | Ahead/behind | 即時遠端 ref 關係 | PR 關聯（狀態及本機 HEAD 關係） | Task ID／owner 證據 |
|---|---|---|---|---|---|---|---|
| WT-01 | `codex/docs-workstream-sync-001` | `4da1cbc1d88385984fcb6ebd14def384dd1df4fd` | CLEAN | 1/0 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-02 | `codex/topic-partial-quote-20261110` | `12d4e2b5ea840514a801d8e0395c550df52ec4f7` | CLEAN | 1/24 | 遠端 ref SHA 不同 | [#106](https://github.com/Xiezhou0828/topicpilot-platform/pull/106)M≠HEAD | TASK-LIVE-PARTIAL-COVERAGE-20261028（工作訂單明列此 PR）; owner 未記錄 |
| WT-03 | `codex/stock-add-workflow-integration-001` | `f2f038deef6dd837175f438f381305642b3b0824` | CLEAN | 18/23 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-04 | `codex/topic-stock-design-restoration` | `6cdf9ffd4134574e877b594c70c5189b237f1e6f` | CLEAN | 0/29 | 遠端 ref SHA 相同 | [#104](https://github.com/Xiezhou0828/topicpilot-platform/pull/104)M=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-05 | `codex/task-preview-staging-release-lane-001` | `e86bc65a9700c2a917fa569994dbc5f74cdc6797` | CLEAN | 2/117 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-06 | `main` | `61f9cf8fc1a4a71aad9fb4e38c0061171be1fd6e` | CLEAN | 3/89 | 遠端 ref SHA 不同 | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-07 | `codex/approved-formal-topic-membership-20261029` | `48327a98a17ef2c2dcc99d0083ca9548dd37f024` | CLEAN | 0/48 | 遠端 ref SHA 相同 | [#96](https://github.com/Xiezhou0828/topicpilot-platform/pull/96)M=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-08 | `codex/canonical-main-sync-20261112` | `38eeeacc02a950d21d903d7c939d11c8492d6770` | DIRTY (23) | 6/0 | 沒有目前同名遠端 ref | — | TASK-DOC-WORKSTREAM-SYNC-20261112（目前 G2 候選；此髒工作樹含其他既有變更，無法把全部差異歸給本任務）; owner 未記錄 |
| WT-09 | `DETACHED` | `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | DIRTY (1) | 10/72 | 無分支名稱 | [#76](https://github.com/Xiezhou0828/topicpilot-platform/pull/76) O=HEAD（head branch `codex/post-close-float-canonicalization-reconciliation-001`） | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-10 | `codex/topic-semiconductor-facilities-flow-20261101` | `5d646a58a46eb0064b5b5bc85969caa6fe14801c` | CLEAN | 1/41 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-11 | `codex/company-research-mainline-integration` | `faf4e3cbedb22c2cf8c399c0b31c18b5166012d1` | CLEAN | 1/56 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-12 | `codex/company-research-core-and-analysis-framework-20261019` | `c22dae110572d3e0278f08cb21e42cc489d0d9ef` | DIRTY (19) | 49/86 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-13 | `DETACHED` | `8ab2a7f69d359cb6fbf42682f573c2e1b536cb03` | CLEAN | 42/433 | 無分支名稱 | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-14 | `DETACHED` | `8ab2a7f69d359cb6fbf42682f573c2e1b536cb03` | DIRTY (224) | 42/433 | 無分支名稱 | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-15 | `codex/post-close-float-canonicalization-reconciliation-001` | `9a0fa7ea541302cd64e2f60f17e3adf94854bad5` | DIRTY (1) | 10/72 | 遠端 ref SHA 相同 | [#76](https://github.com/Xiezhou0828/topicpilot-platform/pull/76)O=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-16 | `codex/preview-production-release-candidate-001` | `0b32b7670c050dc793264859b2ab273d66a68d88` | CLEAN | 7/86 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-17 | `codex/publication-flow-v2-api-release-candidate-010` | `f6d4700d82bf4c3b8d4577e2394c4a3cd4ccee2e` | CLEAN | 1/56 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-18 | `DETACHED` | `b17355eaba3573ed43e48e25d98ffa89506327c1` | CLEAN | 2/79 | 無分支名稱 | [#77](https://github.com/Xiezhou0828/topicpilot-platform/pull/77) O=HEAD（head branch `codex/formal-dimension-release-blocker-reconciliation-002`） | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-19 | `codex/publication-flow-v2-canonical-gate-unblock-003-validation` | `76d34cb21742b23cdf966f459f928e539ffdf3bc` | DIRTY (2) | 5/79 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-20 | `codex/publication-flow-v2-canonical-reconciliation-002` | `40be6f0cecedd83b3f70271acd05ba2aa297cc24` | CLEAN | 3/79 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-21 | `codex/publication-flow-v2-end-to-end-production-recovery-008` | `f9ee0bff1431fcbbdfa7127a6f396aa4fd4b7e95` | DIRTY (2) | 2/58 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-22 | `codex/publication-flow-v2-market-staged` | `bf5b8cf45ee9daf84b19b5eddc86d429c2780254` | CLEAN | 0/71 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-23 | `codex/publication-flow-v2-production-blocker-remediation-007-diag2` | `b45d7b13d7ac58f007fd002718da9fbced8a39a2` | DIRTY (2) | 4/59 | 遠端 ref SHA 不同 | [#84](https://github.com/Xiezhou0828/topicpilot-platform/pull/84)O≠HEAD<br>[#83](https://github.com/Xiezhou0828/topicpilot-platform/pull/83)M≠HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-24 | `DETACHED` | `af3c26543ce1da9b4b2988a19b01026cfd1b7c97` | CLEAN | 0/72 | 無分支名稱 | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-25 | `codex/publication-flow-v2-production-cutover-005-integration` | `d8f36d7b84d96c2d2645be89971859479292f2cc` | DIRTY (1) | 0/64 | 遠端 ref SHA 相同 | [#78](https://github.com/Xiezhou0828/topicpilot-platform/pull/78)M=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-26 | `codex/publication-flow-v2-recovery-continuation-009` | `92ebd4e78acb588aaadeed65c406011fd2d3306c` | CLEAN | 9/56 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-27 | `codex/publication-flow-v2-runtime-closure-006` | `764fb3ccec140ed013f6005c5f3f4b95e26eb925` | DIRTY (5) | 0/62 | 遠端 ref SHA 相同 | [#79](https://github.com/Xiezhou0828/topicpilot-platform/pull/79)M=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-28 | `codex/selection-vnext-attack-outcome-research-001` | `e97f590cad497c0a23fb027fce39ec5891ea4bc1` | DIRTY (4) | 0/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-29 | `codex/selection-vnext-benchmark-universe-executability-authority-001` | `4db4ec749ad1ab978573d1a326b4d28bdd9bbf6c` | DIRTY (1) | 1/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-30 | `codex/selection-vnext-broad-pit-threshold-stability-final-001` | `ac7157ccf15315b7a3374082bed3c5be0a84db7b` | CLEAN | 11/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-31 | `codex/selection-vnext-broad-pit-threshold-stability-001` | `a01a3a23238f15fcb9c71c54abab7aeb45fc00f9` | CLEAN | 8/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-32 | `codex/selection-vnext-entry-quality-contract-002` | `17f3cb597593c21a8bd38edb858d786d607d3245` | CLEAN | 16/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-33 | `codex/selection-vnext-external-literature-001` | `ef6d535e4118df2f283904ce4e9b35bd8ead2863` | CLEAN | 23/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-34 | `codex/selection-vnext-independent-setup-validation-001` | `94adb752cf01f58123686ea9c7d507e7983565ec` | CLEAN | 21/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-35 | `codex/selection-vnext-pit-entry-access-authority-001` | `4d5190346f8177677d5e76d5a407c59db82e7aec` | DIRTY (1) | 5/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-36 | `codex/selection-vnext-pit-membership-interval-closure-003` | `3fe3975cda724c30391ac8112c5190b71d5d749e` | CLEAN | 10/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-37 | `codex/selection-vnext-pit-recovery-002` | `5ca32a2504cc8f54ea10cccda764090f77beb885` | DIRTY (2) | 8/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-38 | `codex/selection-vnext-v0-event-transition-closure-002` | `38aae3834485645f29d590edae0d12ca7651d0bd` | CLEAN | 28/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-39 | `codex/selection-vnext-v0-policy-design-001` | `919048aa790a82e746657c6e27fbc2d08fe3a6a0` | CLEAN | 26/72 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-40 | `codex/selection-vnext-broad-pit-threshold-research-001` | `3fe3975cda724c30391ac8112c5190b71d5d749e` | DIRTY (1) | 10/85 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-41 | `codex/stock-research-bootstrap-v1` | `9852f03b4586572b13f744868b2aac4dbd33ff89` | DIRTY (22) | 18/58 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-42 | `codex/stock-topic-impact-direction-evidence-ui-001` | `b17355eaba3573ed43e48e25d98ffa89506327c1` | DIRTY (16) | 2/79 | 沒有目前同名遠端 ref | [#77](https://github.com/Xiezhou0828/topicpilot-platform/pull/77) O=HEAD（不同名 PR head branch `codex/formal-dimension-release-blocker-reconciliation-002`） | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-43 | `DETACHED` | `8383a5ee5d601e5da6a277a3ccf12f970c5342ec` | DIRTY (2) | 4/79 | 無分支名稱 | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-44 | `codex/expire-stale-cross-scope-post-close-20261104` | `a06a0313de4d101e765ae14a4e33087ee0f15458` | CLEAN | 0/35 | 遠端 ref SHA 相同 | [#103](https://github.com/Xiezhou0828/topicpilot-platform/pull/103)M=HEAD | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |
| WT-45 | `codex/worker-formal-bounded-20261013` | `2d1998e1ce8ce6b43516e4acccb59579002be36e` | CLEAN | 9/49 | 沒有目前同名遠端 ref | — | 未能由目前工作訂單／PR 文字精確匹配; owner 未記錄 |

## 已核對的 PR／工作訂單交叉證據

- 現有 `docs/WORK_ORDERS.md` 的 `TASK-LIVE-PARTIAL-COVERAGE-20261028` 記錄明列 PR #102、#105、#106、#107 為後續合併證據；因此上述四筆 PR／同名分支與該 work order 有明確交叉引用。這只證明 work order 引用這些 PR 作為該任務的相關證據，不表示 PR 只服務於這一任務，也不等於 2026-10-28 Production 驗收已完成。
- GitHub PR #4 與 #5 的文字明確引用已登錄的 `TASK-DATA-REF-009A`；這是歷史 PR 的精確 ID 關聯，不代表它們目前仍有遠端分支或待執行工作。
- PR #86 宣告 `TASK-TOPICPILOT-GITHUB-DELIVERY-AND-LOCAL-WORKTREE-RETIREMENT-003`，但目前 `docs/WORK_ORDERS.md` 沒有此 ID；標記為未登錄，不擅自建立或重命名任務。
- 下列 8 個分支 tip 對應已合併 PR head，且該 PR 的 merge commit 可在 main ancestry 中找到：[#37](https://github.com/Xiezhou0828/topicpilot-platform/pull/37) `codex/current-day-health-018`；[#41](https://github.com/Xiezhou0828/topicpilot-platform/pull/41) `codex/fix-worker-release-precondition-021`；[#95](https://github.com/Xiezhou0828/topicpilot-platform/pull/95) `codex/formal-strength-history-shape-20261029`；[#40](https://github.com/Xiezhou0828/topicpilot-platform/pull/40) `codex/post-close-schedule-freeze-021`；[#42](https://github.com/Xiezhou0828/topicpilot-platform/pull/42) `codex/task-021-report`；[#45](https://github.com/Xiezhou0828/topicpilot-platform/pull/45) `codex/task-022-incident-report-final`；[#43](https://github.com/Xiezhou0828/topicpilot-platform/pull/43) `codex/task-022-public-today-fetch`；[#39](https://github.com/Xiezhou0828/topicpilot-platform/pull/39) `codex/task-post-close-readiness-020`。這只核對 merge ancestry；不作為清理授權，也不代替未提交差異或後續 tip 內容檢查。
- 遠端分支 `codex/worker-db-session-recovery-20261103` 的目前 tip `b933494802fdf8e389bf36c09f27697365398307` 與已合併 PR #101 head `f7d06ff446d6dc8dabcd267b2cc0f9175df8d24a` 不同；GitHub Compare 顯示目前 tip 相對於該 PR head ahead 1、behind 0，且本機沒有同名 worktree。該多出的提交仍需 Owner 檢視，不判定可清理或已完成。
- 另外 11 個 diverged refs 未被上述 merge-ancestry證據解決；需逐案檢查 PR、差異內容與後續替代提交，不能僅依 `diverged` 或舊分支名稱判定。

## Hygiene 與未解歸屬

```text
REPOSITORY_HYGIENE_STATUS=ACTION_REQUIRED
LOCAL_ONLY_COMMIT_COUNT=UNKNOWN
STALE_WORKTREE_COUNT=UNKNOWN
ORPHANED_WORKSTREAM_COUNT=UNKNOWN
UNATTRIBUTED_DIRTY_COUNT=UNKNOWN
```

證據與限制：

- `LOCAL_ONLY_COMMIT_COUNT` 保持 UNKNOWN：本機曾得到「41 個唯一 worktree HEAD 可達、但不在 origin/main 的提交共 196 個」的診斷數；這不是嚴格 local-only，因本機沒有所有即時遠端 tip 的 Git objects。依本任務邊界不能 fetch，故不能排除那些提交也存在於遠端 refs。
- `STALE_WORKTREE_COUNT` 保持 UNKNOWN：雖然已列出每個 HEAD 與 ahead/behind，現有 audit 未提供可驗證的最近活動時間、owner 或 stale 門檻。
- `ORPHANED_WORKSTREAM_COUNT` 保持 UNKNOWN：30 個 worktree 沒有目前同名遠端 ref、4 個遠端分支沒有同名 PR，這些事實本身不能證明任務已遺失、完成或無主。
- `UNATTRIBUTED_DIRTY_COUNT` 保持 UNKNOWN：18 個 worktree dirty；目前只有 WT-08 可連到本任務，但其中 23 項變更也包含其他既有工作。其餘 dirty worktree 尚無經核實的逐檔 owner／task 歸屬。
- 6 個 detached worktree（含 2 個 HEAD 相同但 dirty 狀態不同的獨立 worktree）全部分開保留。無 worktree 被標成可清理。

## 驗收結果

| 項目 | 結果 | 證據 |
|---|---|---|
| GitHub main、分支數與 SHA | PASS | main `f27a0c4fa189810c6caa01ad3f2944d7fd4919e2`；46 refs；branches/open PR 在 2026-11-12 16:06:46Z 即時重查。 |
| 遠端分支逐筆列示 | PASS | 46/46；45 個 feature ref 均有精確 tip SHA、比較狀態及 PR/任務匹配結果或明確未匹配。 |
| 開啟 PR 逐筆列示 | PASS | 5/5；每筆含 head branch、head SHA、URL、author、assignee/reviewer 與 Task ID 狀態。 |
| 本機 worktree 逐筆列示 | PASS | 45/45；含匿名 ID、HEAD、dirty 狀態、ahead/behind、遠端 tip 關係與匹配結果；0 個讀取失敗。 |
| 髒檔及未歸屬保護 | PASS | 18 個 dirty worktree 原樣保留；沒有 merge/delete/push/cleanup。 |
| 絕對本機路徑 | PASS | 報告未輸出 worktree 完整路徑。 |
| 秘密資訊 | PASS | 報告只含公開 GitHub refs/PR 與程式碼 SHA；不含 credentials/secrets。 |
| 文件連結、Task ID 與差異檢查 | PASS | G2 報告、Roadmap、Index 路徑存在；工作訂單首欄 ID 16 筆、無重複；4 份目標文件無尾端空白；tracked 文件 `git diff --check` 通過。 |

## 交付界線

截至本報告驗收時，G2 盤點產物仍是未提交、未 canonicalize 的已驗證候選。後續如在本機整合分支提交，不代表已合併至 GitHub `main`。本任務沒有執行應用程式測試、Production 查詢／寫入、資料庫遷移、推送、合併、部署、分支刪除、worktree 清理或 `NEXT_TASK` 修改。G3 的 Task-ID 自動檢查、owner 正式歸屬與上述 UNKNOWN 指標仍待後續治理階段處理。


## Post-review revalidation and Owner dispositions

**Revalidated:** 2026-11-13 Asia/Taipei. The original tables above remain the
complete historical snapshot captured on 2026-11-12; this section records the
subsequent Owner-reviewed disposition and the refreshed current counts.

### Live GitHub state

- Read-only git ls-remote --heads origin returned 36 refs: main plus 35
  feature refs. Main remains
  f27a0c4fa189810c6caa01ad3f2944d7fd4919e2. All 35 surviving feature refs
  match the SHA recorded in the original G2 table; no new or changed feature
  ref was found.
- GitHub branch search returned 35 feature refs with no next page. Two open-PR
  searches returned no open PRs.
- Ten refs present in the original snapshot are now absent:
  codex/formal-dimension-release-blocker-reconciliation-002,
  codex/legacy-extract-reconciliation-20261005,
  codex/post-close-float-canonicalization-reconciliation-001,
  codex/publication-flow-v2-production-blocker-remediation-007-diag2,
  codex/release/api-only-f6d4700,
  codex/stock-add-topic-candidate-readback,
  codex/structural-role-production-read-boundary,
  codex/topicpilot-local-preview-canonical-delivery-002,
  codex/worker-db-session-recovery-20261103, and
  codex/worker-tpex-recovery-20261013. These absences correspond to the
  individually Owner-authorized PR/branch cleanup decisions in this review.
  Historical PR and commit records remain available on GitHub.

### Refreshed local worktree state

The read-only audit script infra/scripts/governance/audit_worktrees.mjs
completed at 2026-11-12 18:08:59Z against origin/main
f27a0c4fa189810c6caa01ad3f2944d7fd4919e2.

- Worktrees: 38
- Dirty: 16
- Clean: 22
- Detached: 3
- Unreadable: 0

The 16 dirty worktrees, shown without local paths, are:

| Local branch / detached label | HEAD | Changed paths |
|---|---|---:|
| codex/canonical-main-sync-20261112 | 38eeeacc02a950d21d903d7c939d11c8492d6770 | 24 |
| DETACHED (formal shadow) | 9a0fa7ea541302cd64e2f60f17e3adf94854bad5 | 1 |
| codex/company-research-core-and-analysis-framework-20261019 | c22dae110572d3e0278f08cb21e42cc489d0d9ef | 19 |
| DETACHED (frontend publish squashed) | 8ab2a7f69d359cb6fbf42682f573c2e1b536cb03 | 224 |
| codex/publication-flow-v2-canonical-gate-unblock-003-validation | 76d34cb21742b23cdf966f459f928e539ffdf3bc | 2 |
| codex/publication-flow-v2-end-to-end-production-recovery-008 | f9ee0bff1431fcbbdfa7127a6f396aa4fd4b7e95 | 2 |
| codex/publication-flow-v2-production-cutover-005-integration | d8f36d7b84d96c2d2645be89971859479292f2cc | 1 |
| codex/publication-flow-v2-runtime-closure-006 | 764fb3ccec140ed013f6005c5f3f4b95e26eb925 | 5 |
| codex/selection-vnext-attack-outcome-research-001 | e97f590cad497c0a23fb027fce39ec5891ea4bc1 | 4 |
| codex/selection-vnext-benchmark-universe-executability-authority-001 | 4db4ec749ad1ab978573d1a326b4d28bdd9bbf6c | 1 |
| codex/selection-vnext-pit-entry-access-authority-001 | 4d5190346f8177677d5e76d5a407c59db82e7aec | 1 |
| codex/selection-vnext-pit-recovery-002 | 5ca32a2504cc8f54ea10cccda764090f77beb885 | 2 |
| codex/selection-vnext-broad-pit-threshold-research-001 | 3fe3975cda724c30391ac8112c5190b71d5d749e | 1 |
| codex/stock-research-bootstrap-v1 | 9852f03b4586572b13f744868b2aac4dbd33ff89 | 22 |
| codex/stock-topic-impact-direction-evidence-ui-001 | b17355eaba3573ed43e48e25d98ffa89506327c1 | 16 |
| DETACHED (runtime parity) | 8383a5ee5d601e5da6a277a3ccf12f970c5342ec | 2 |

The governance source worktree is clean at
4da1cbc1d88385984fcb6ebd14def384dd1df4fd (1 ahead / 0 behind origin/main).
The canonical checkout remains at
38eeeacc02a950d21d903d7c939d11c8492d6770 (6 ahead / 0 behind) with 24 dirty
paths. A separate clean local branch named main remains at
61f9cf8fc1a4a71aad9fb4e38c0061171be1fd6e (3 ahead / 89 behind origin/main);
it is not the current GitHub main. All these worktrees remain intact.

### Final disposition

The Owner-approved cleanup items were executed only for the exact PR refs,
orphan refs, and clean duplicate worktrees reviewed in this conversation.
Remaining unattributed worktrees and local state are PRESERVED / OWNER
DISPOSITION REQUIRED. No cleanup eligibility is inferred from cleanliness,
ancestry, branch naming, or absent remote refs.

REPOSITORY_HYGIENE_STATUS=ACTION_REQUIRED
LOCAL_ONLY_COMMIT_COUNT=UNKNOWN
STALE_WORKTREE_COUNT=UNKNOWN
ORPHANED_WORKSTREAM_COUNT=UNKNOWN
UNATTRIBUTED_DIRTY_COUNT=UNKNOWN

G0-G2 remain a validated documentation candidate, not a clean committed
canonical result. This review performed no fetch, application test, Production
query/write, migration, push, merge, deploy, NEXT_TASK change, or unreviewed
branch/worktree cleanup. G3 should not start until the preserved workstreams
receive explicit ownership/disposition and the candidate is reconciled into a
clean canonical commit with provenance.

## 2026-11-13 G2 exit recheck（00:34Z；已由 04:23Z 檢查點取代）

**Local audit:** 2026-11-13 00:34:29Z (08:34:29 Asia/Taipei), read-only
audit_worktrees.mjs, based on origin/main f27a0c4fa189810c6caa01ad3f2944d7fd4919e2.
**GitHub:** REST read-only branch and open-PR queries checked approximately
2026-11-13 00:40Z (08:40 Asia/Taipei).

- GitHub main: f27a0c4fa189810c6caa01ad3f2944d7fd4919e2.
- Remote branches: 36 refs including main; 35 feature refs. The exact names and
  tips of all 35 feature refs match the existing remote-branch table above.
- Open PRs: 0. The previous open-PR list is historical evidence, not a current
  open-PR inventory.
- Local worktrees: 27 total, 16 dirty, 11 clean, 3 detached, 0 unreadable.
  The canonical checkout is 38eeeacc02a950d21d903d7c939d11c8492d6770,
  6 ahead / 0 behind origin/main, with 24 dirty paths.
- The following table refreshes every worktree retained from the earlier
  WT-indexed inventory. Branch names, full HEAD SHAs, and ahead/behind values
  are cross-referenced by the historical WT ID in the table above; current
  changed-path counts and attribution are recorded here. No full local path is
  included.

| Historical WT ID | Current state | Exact work-order match | Accountable owner | Disposition |
|---|---|---|---|---|
| WT-01 | CLEAN | No exact match | Not recorded | PRESERVED; provenance/owner decision required |
| WT-02 | CLEAN | TASK-LIVE-PARTIAL-COVERAGE-20261028 (PR #106 work-order reference; PR head differs from worktree) | Not recorded | PRESERVED; reconcile source/head before closure |
| WT-03 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-08 | DIRTY (24 paths) | TASK-DOC-WORKSTREAM-SYNC-20261112 is the current governance work order, but all 24 paths are not attributed to it | Not recorded | PRESERVED; mixed canonical changes, OWNER_DECISION_REQUIRED |
| WT-09 | DETACHED, DIRTY (1 path) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-10 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-11 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-12 | DIRTY (19 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-14 | DETACHED, DIRTY (224 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-16 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-19 | DIRTY (2 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-20 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-21 | DIRTY (2 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-25 | DIRTY (1 path) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-26 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-27 | DIRTY (5 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-28 | DIRTY (4 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-29 | DIRTY (1 path) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-31 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-35 | DIRTY (1 path) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-37 | DIRTY (2 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-38 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-40 | DIRTY (1 path) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-41 | DIRTY (22 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-42 | DIRTY (16 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-43 | DETACHED, DIRTY (2 paths) | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |
| WT-45 | CLEAN | No exact match | Not recorded | PRESERVED; OWNER_DECISION_REQUIRED |

### Six approved worktree removals

The following worktrees were removed after explicit Owner approval. Their local
branch refs still exist at the listed SHAs in the canonical repository. The
exact same-named remote refs are absent from the 2026-11-13 GitHub branch
inventory. The removal applied only to the worktree; it did not delete the
local branch ref.

| Historical WT ID | Removed worktree branch | Original HEAD SHA | Recorded removal basis | Branch state |
|---|---|---|---|---|
| WT-05 | codex/task-preview-staging-release-lane-001 | e86bc65a9700c2a917fa569994dbc5f74cdc6797 | Clean worktree; its changes were verified patch-equivalent to main before the approved worktree removal | Local branch retained at the original SHA; no exact-named remote ref |
| WT-30 | codex/selection-vnext-broad-pit-threshold-stability-final-001 | ac7157ccf15315b7a3374082bed3c5be0a84db7b | Clean worktree; its commit was an ancestor of the V0 event-transition closure work | Local branch retained at the original SHA; no exact-named remote ref |
| WT-32 | codex/selection-vnext-entry-quality-contract-002 | 17f3cb597593c21a8bd38edb858d786d607d3245 | Clean worktree; its commit was an ancestor of the V0 event-transition closure work | Local branch retained at the original SHA; no exact-named remote ref |
| WT-33 | codex/selection-vnext-external-literature-001 | ef6d535e4118df2f283904ce4e9b35bd8ead2863 | Clean worktree; its commit was an ancestor of the V0 event-transition closure work | Local branch retained at the original SHA; no exact-named remote ref |
| WT-34 | codex/selection-vnext-independent-setup-validation-001 | 94adb752cf01f58123686ea9c7d507e7983565ec | Clean worktree; its commit was an ancestor of the V0 event-transition closure work | Local branch retained at the original SHA; no exact-named remote ref |
| WT-39 | codex/selection-vnext-v0-policy-design-001 | 919048aa790a82e746657c6e27fbc2d08fe3a6a0 | Clean worktree; its commit was an ancestor of the V0 event-transition closure work | Local branch retained at the original SHA; no exact-named remote ref |

The original 45-row snapshot has 27 matching worktrees in the latest audit.
Six absent rows have the explicit cleanup evidence listed above. The following
12 historical rows are also absent from the current worktree list, but their
removal time and disposition could not be confirmed from a complete
intermediate inventory. “Absent” does not imply their refs or commits were
deleted.

| Historical WT ID | Historical branch / detached label | Historical HEAD SHA | Current evidence and disposition |
|---|---|---|---|
| WT-04 | codex/topic-stock-design-restoration | 6cdf9ffd4134574e877b594c70c5189b237f1e6f | No worktree; local and remote branch refs still exist at this SHA. Removal reason/time not recorded. OWNER_DECISION_REQUIRED |
| WT-06 | main | 61f9cf8fc1a4a71aad9fb4e38c0061171be1fd6e | No worktree; local main remains at this SHA while GitHub main is f27a0c4fa189810c6caa01ad3f2944d7fd4919e2. Removal reason/time not recorded. OWNER_DECISION_REQUIRED |
| WT-07 | codex/approved-formal-topic-membership-20261029 | 48327a98a17ef2c2dcc99d0083ca9548dd37f024 | No worktree; local and remote branch refs still exist at this SHA. Removal reason/time not recorded. OWNER_DECISION_REQUIRED |
| WT-13 | DETACHED | 8ab2a7f69d359cb6fbf42682f573c2e1b536cb03 | No separate worktree; the same HEAD is present in current WT-14, which is dirty. The earlier clean worktree disposition is not recorded. OWNER_DECISION_REQUIRED |
| WT-15 | codex/post-close-float-canonicalization-reconciliation-001 | 9a0fa7ea541302cd64e2f60f17e3adf94854bad5 | No separate worktree or exact-name local/remote branch; the same HEAD remains in current detached WT-09. Removal/ref disposition is not recorded. OWNER_DECISION_REQUIRED |
| WT-17 | codex/publication-flow-v2-api-release-candidate-010 | f6d4700d82bf4c3b8d4577e2394c4a3cd4ccee2e | No current worktree or exact-name local/remote branch found. Commit reachability and disposition were not revalidated. OWNER_DECISION_REQUIRED |
| WT-18 | DETACHED | b17355eaba3573ed43e48e25d98ffa89506327c1 | No separate worktree; the same HEAD is present in current WT-42, which is dirty. The earlier clean worktree disposition is not recorded. OWNER_DECISION_REQUIRED |
| WT-22 | codex/publication-flow-v2-market-staged | bf5b8cf45ee9daf84b19b5eddc86d429c2780254 | No current worktree or exact-name local/remote branch found. Commit reachability and disposition were not revalidated. OWNER_DECISION_REQUIRED |
| WT-23 | codex/publication-flow-v2-production-blocker-remediation-007-diag2 | b45d7b13d7ac58f007fd002718da9fbced8a39a2 | No current worktree or exact-name local/remote branch found. Commit reachability and disposition were not revalidated. OWNER_DECISION_REQUIRED |
| WT-24 | DETACHED | af3c26543ce1da9b4b2988a19b01026cfd1b7c97 | No current worktree or matching current HEAD found. Commit reachability and disposition were not revalidated. OWNER_DECISION_REQUIRED |
| WT-36 | codex/selection-vnext-pit-membership-interval-closure-003 | 3fe3975cda724c30391ac8112c5190b71d5d749e | No separate worktree; the same HEAD is present in current WT-40, which is dirty. The earlier clean worktree disposition is not recorded. OWNER_DECISION_REQUIRED |
| WT-44 | codex/expire-stale-cross-scope-post-close-20261104 | a06a0313de4d101e765ae14a4e33087ee0f15458 | No worktree; local and remote branch refs still exist at this SHA. Removal reason/time not recorded. OWNER_DECISION_REQUIRED |

The 2026-11-12 18:08Z checkpoint reported 38 worktrees and did not retain a
complete row-by-row list. Its net difference from the current count is 11, but
it cannot be mapped to exact worktree additions/removals. Across the older
45-row inventory, six removals are evidenced and 12 additional historical rows
remain untraced. No branch deletion, commit deletion, or cleanup action is
inferred from absence.
WORKTREE_DELTA_RECONCILIATION=BLOCKED.

### G2 exit disposition

- Branch and PR inventory: PASS for the current 35 feature refs and zero open
  PRs; exact tips were checked against the prior report.
- Worktree enumeration: PASS for 27 current worktrees; 16 remain dirty and 3
  are detached. Each is cross-referenced above without exposing local paths.
- Ownership and Task-ID traceability: BLOCKED. Most retained worktrees have no
  exact Task ID or accountable owner in the current work-order/PR evidence.
  OWNER_DECISION_REQUIRED remains for unresolved rows; cleanliness and branch
  names do not resolve ownership.
- Removed-worktree evidence: PARTIAL. Six exact removals and local branch-ref
  retention are recorded; the broader 38-to-27 inventory delta remains
  unresolved.
- G1/G2 candidate canonicalization: BLOCKED. Source worktree SHA
  4da1cbc1d88385984fcb6ebd14def384dd1df4fd is clean, while canonical HEAD
  38eeeacc02a950d21d903d7c939d11c8492d6770 has 24 dirty paths, including
  overlapping governance files. The exact approved hunks cannot be committed
  without first separating their provenance from the pre-existing canonical
  changes. No commit was made.

G2_EXIT=BLOCKED
G3_STARTED=NO
CANONICAL_RECONCILIATION_DISPOSITION=OWNER_DECISION_REQUIRED
