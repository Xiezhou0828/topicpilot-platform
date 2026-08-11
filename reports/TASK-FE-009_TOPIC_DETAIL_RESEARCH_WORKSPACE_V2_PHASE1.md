# TASK-FE-009 — Topic Detail Research Workspace V2 / Phase 1

## Executive summary

已完成 `/topics/:slug` Topic Detail 上半部 Phase 1，將頁面固定為「題材研究工作區」的閱讀順序：

1. 題材階層與 identity：名稱、強度等級、題材強度、目前狀態、收藏與一段摘要。
2. 題材狀態：固定三個研究視角「族群表現／領漲核心／動能擴散」。
3. 題材生命週期：固定五階段「萌芽 → 發酵 → 主升 → 成熟 → 衰退」。
4. 題材內股票：保留後端成分股順序的統一研究表格。
5. 既有歷程、新聞、相關題材與熱圖仍留在下層研究內容。

未修改 `/topics` Overview、Home、Stocks 的 IA、Opportunity、Favorites、backend、API schema、scoring、lifecycle derivation 或其他 V1 business logic。

## Modified files

- `apps/web/app/components/v2/TopicDetailPage.tsx`
  - 重排 Topic Detail 上半部。
  - 新增三視角 Topic Status presentation。
  - 將生命週期改為五階段單一路徑。
  - 股票表格增加題材表現、技術狀態、Action 欄位，缺資料顯示 `尚未提供`。
  - 移除前端 role/code 排序，保留 read model 回傳順序。
  - 每列可點擊、Enter/Space 可開啟、Escape 可關閉 Drawer。
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
  - 將既有 Stock Explorer Drawer 抽成共用元件。
  - 支援 inline push layout 與 overlay presentation。
  - 提供唯一 Favorite Star、Close/X、更新狀態、題材身分、主要題材摘要與 `查看機會 →`。
- `apps/web/app/components/v2/StockExplorerPage.tsx`
  - 僅改為使用共用 Stock Encyclopedia Drawer，保留原有 Stocks toolbar、tile、sort/filter IA 與 inline responsive push 行為。
- `apps/web/app/components/v2/V2Foundation.tsx`
  - FavoriteStar 支援受控 active state 與 button event props，未改變既有視覺 primitive。
- `apps/web/app/lib/topic-api.ts`
  - 未映射或缺失的 relation type 不再被錯誤歸為 `關聯股`，改為 `null`，由 UI 顯示 `—`。
- `apps/web/app/globals.css`
  - 新增僅以 `tp-topic-detail-*`、`tp-stock-encyclopedia-*` 為主的 Phase 1 layout/style rules。

## Topic Detail structure

- Identity header：breadcrumb、題材名稱、收藏題材、Grade、題材強度、目前狀態、股票數、資料日期、單一 Preview summary。
- Topic Status：三欄固定視角，不新增第四或第五個 KPI tile。
- Lifecycle：五階段水平 timeline，current stage 使用 brand taupe marker；在窄寬度改為垂直連續線。
- Topic Stocks：單一 unified table；每列提供股票名稱/股號、題材角色、今日漲跌、題材表現、技術狀態、更新狀態與 Action。
- Lower research sections：題材歷程、限定新聞、相關題材、熱圖維持在上半部之後，未改成首頁式 dashboard。

## Data authority and missing-field handling

正式 Topic read model 目前提供：題材 identity、group、score、grade、strength state、coverage、constituent count、constituent code/name/relation/weight。

目前正式 Topic contract 尚未提供：

- 族群表現／領漲核心／動能擴散三項語意欄位；
- lifecycle history、正式 current stage、日期與交易日 duration；
- constituent price/change/freshness 的 Topic Detail 欄位；
- 題材相對表現 `領漲／同步／轉強／落後`；
- 技術狀態。

處理方式：

- identity 與正式存在的欄位仍以 API 為準。
- 三項 Topic Status 與 lifecycle 目前使用明確標示的 Preview presentation；不由 browser 從 score、role、price 或 constituent count 推導。
- Lifecycle 的 Preview current stage/entry display 保留，但 Preview 的交易日數不呈現；Day N／交易日 duration 僅在正式 read model 欄位存在時顯示。
- 股票表中的缺失題材表現、技術狀態顯示 `尚未提供`；缺失 role 顯示 `—`。
- Preview 價格與漲跌資料只在 synthetic snapshot 明確存在時呈現，並在 Drawer 顯示 `Preview` 與 `資料待更新` 語意。

## Shared Stock Drawer reuse and interaction

- Topic Detail 與 Stocks 共用 `StockEncyclopediaDrawer`。
- Topic stock table 任一列可用滑鼠、Enter 或 Space 開啟。
- 選取另一檔股票時直接替換 Drawer 內容，不需要 close/reopen。
- Drawer 有唯一 Favorite Star、X close、`查看機會 →` CTA。
- Topic Detail 與 Stocks 都支援 Escape 關閉；Stocks 原有的 inline push layout 與窄寬 responsive behavior 保留。
- Topic Detail 使用同一個 inline Drawer，保持股票表格與研究上下文可見；窄寬度改為單欄堆疊。

## Design tokens and visual boundary

沿用 V2 tokens：`#8A7462` brand、warm off-white page、white surfaces、warm gray borders/text、Taiwan red/green 僅用於實際價格漲跌、restrained amber Preview、10–12px radius、8px rhythm、subtle shadow、`--tp-drawer-width: 560px`、`200ms ease`。

沒有新增 neon、AI gradient、glassmorphism、heavy shadow 或以紅綠表達 role/grade/lifecycle 的視覺語意。

## Responsive behavior

- Desktop：Topic stock table 與 560px shared Drawer 以雙欄呈現。
- ≤760px：Topic stock workspace 改單欄，Drawer 置於表格後方；lifecycle 改垂直路徑；status 三欄改單欄。
- 既有 Stocks page 的 tile grid、toolbar、sorting/filter interaction 未搬移到其他頁面。

## Verification

- Targeted ESLint：pass，無 warning/error。
- `npm run build`：pass；包含 `/topics/:slug` 與 `/stocks` routes。
- TypeScript：未出現本次變更檔案的新錯誤；workspace 仍有既有非本任務錯誤，主要集中於 `data-source.ts`、`snapshot-store.tsx`、`watchlist/page.tsx`、`vite.config.ts` 與 `worker/index.ts`。
- `git diff --check`：pass。
- Scope audit：未修改 `/topics` Overview component、Home、Opportunity、Favorites、backend 或 API schema。

## Remaining / recommended next step

下一步應由 PM／backend read-model 一起確認三項 Topic Status 的正式欄位定義、lifecycle history contract、題材相對表現與技術狀態 payload；本 Phase 已先完成不推導、可替換的 presentation boundary。Phase 1 完成後停止，不自動開始下一個 Phase。
