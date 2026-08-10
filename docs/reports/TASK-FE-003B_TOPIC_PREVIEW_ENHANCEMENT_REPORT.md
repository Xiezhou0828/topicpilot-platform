# TASK-FE-003B — Topic Preview Enhancement Report

**Status:** Implemented; validation and preview deployment pending
**Scope:** V2 Topic List and Topic Detail only. Home, Stock, Watchlist, Opportunity, Backend schema/provider, and V1 remain unchanged.

## 1. 已改進項目

### Topic List

- 保留正式 Topic API 的名稱、強度、Grade、狀態、股票數與資料邊界。
- 從偏 Admin Table 的閱讀方式改為產品化題材列：題材 icon、強度、狀態 chip、Grade Badge、股票數、收藏與右箭頭入口。
- 加入 hover feedback、selected highlight、搜尋與升溫／退潮篩選。
- 題材與群組名稱、狀態、更新狀態改為 V2 中文 mapping。

### Topic Detail

- 正式 API 核心資料仍位於頁首與正式成分股清單：名稱、強度、Grade、狀態、股票數、資料日期、角色與成分股。
- 摘要、生命圖、研究摘要、歷程、新聞、相關題材與題材熱圖改為各自獨立的 Preview 區塊。
- 每個 Preview 區塊均顯示 `Preview · 等待正式 Read Model`，不再以大量「資料待更新」取代完整產品形狀。
- Stock Drawer 保留正式成分股入口；當價格／更新 read model 尚未提供時，以 Preview 標示，不推導正式行情。

### Heatmap / Treemap

- Topic List 與 Topic Detail 均改為真正的矩形 Treemap。
- 矩形大小以目前題材強度做近似預覽分配，Grade 套用 S/A/B/D 的中性 taupe 層次。
- 保留點擊矩形進入 Topic Detail、hover border 與可讀狀態。

### Preview Data / UI

- 新增集中式 `topic-preview.ts`，只承載 Backend 尚未提供的摘要、生命週期、歷程、新聞、相關題材與 Heatmap layout。
- Preview identity 只在沒有 API origin 的公開 synthetic fallback 中支援完整展示；API 已存在時不覆寫 API 核心欄位。
- 中文化 `Digital Infrastructure`、`Cloud Security`、`Edge AI`、`CURRENT`、`WARMING` 等呈現，避免 raw backend code 出現在客戶頁。

## 2. 正式 API 使用情況

| 區塊 | 正式 API | Preview Data | 備註 |
|---|---|---|---|
| Topic List identity/strength/grade/state/count/date | `GET /api/v1/topics` | 僅無 API origin 的公開 synthetic fallback | API 優先，不覆寫 |
| Topic Detail identity/strength/grade/state/count | `GET /api/v1/topics/{slug}` | 僅無 API origin 時的完整 Preview identity | API 優先，不覆寫 |
| Topic constituents / roles | `GET /api/v1/topics/{slug}` | 僅公開 synthetic fallback 供展示 | relationType 轉成代表股／核心股／關聯股 |
| Summary | 尚無欄位 | Preview | 每區有 Preview Badge |
| Lifecycle | 尚無正式 read model | Preview | 五階段與 current marker |
| Timeline / events | 尚無正式 read model | Preview | 重要節點示意 |
| News | 尚無正式 curated news read model | Preview 新聞 | 明確標示 Preview 新聞 |
| Related topics | 尚無正式 read model | Preview | 可點擊研究入口 |
| Heatmap / Treemap sizing | 尚無正式 read model | Preview | 強度近似尺寸、Grade 中性色 |

## 3. 尚待 Backend 完成

- Topic summary / readable summary copy。
- Lifecycle segments、stage transition、交易日持續天數與 re-entry history。
- Topic event / intraday evolution timeline。
- Curated topic news/context。
- Related topic graph and relationship strength。
- User-scoped topic favorite persistence and reminder state。
- Formal Heatmap/Treemap sizing input and topic map read model。
- Stock price、change、freshness in the Topic Detail constituent contract。
- Downstream Opportunity candidates/cross-link read model。

## 4. 未來可直接切換正式 API 的區塊

Preview data is isolated behind `getTopicPreview()` and the preview section components. Once the corresponding read models exist, each section can replace its `preview` prop with the API adapter field while preserving the current section layout, badge placement, reading order, and Treemap component contract. No second UI rewrite should be required.

## Verification

- `npm run lint` — passed.
- `npm run build` — passed; `/topics` and `/topics/:slug` remain in the production route manifest.
- Repository TypeScript check still reports only pre-existing errors outside the TASK-FE-003B files.

## Boundary

TASK-FE-003B does not modify Home, Stock, Watchlist, Opportunity, Backend schema/provider, or V1. It stops after Topic Preview Mode implementation and deployment verification.
