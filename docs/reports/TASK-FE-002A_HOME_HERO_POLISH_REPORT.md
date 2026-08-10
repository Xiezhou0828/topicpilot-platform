# TASK-FE-002A — Home Hero Polish + Live Data Integration Report

日期：2026-08-10  
狀態：完成，停止於 TASK-FE-002A，等待 PM 第二輪 Home Review

## 1. 這次調整

這次沒有重新設計 Home，也沒有新增功能。調整集中在第一屏：

- 移除 Page Header 上方重複的 `今日市場` 小標。
- 保留單一 `今日市場` H1 與既有副標。
- 移除市場概況的 `MARKET PULSE` 英文 overline 與解釋句。
- 壓縮 Page Header、freshness、Summary Card 之間的垂直節奏。
- 壓縮 Summary Card 高度，保留第一列三個主要市場數字與第二列六個密度欄位。
- 移除正式畫面中的 `開發用固定快照` 開發字樣。
- 無資料時改用正式產品語氣 `資料待更新`；不把 bundled synthetic timestamp 當成即時更新時間。
- 第一屏在桌面視窗內同時看到市場概況與 `今日市場重點` 開頭。

## 2. 修改前／修改後截圖

- 修改前：[TASK-FE-002 Home desktop](TASK-FE-002_HOME_DESKTOP.png)
- 修改後：[TASK-FE-002A Home desktop](TASK-FE-002A_HOME_AFTER_DESKTOP.png)

修改後第一屏即為本次驗收截圖：Header → H1 → 副標 → Data State → 市場概況 → 今日市場重點開頭。

## 3. Live Backend 資料盤點

首頁已接入既有 `SnapshotProvider`，其 runtime endpoint 為 `GET /api/v1/snapshot/latest`。只有後端回傳欄位存在、非 pending，且不是公開 synthetic preview 時才會取代 mock 顯示。

| 首頁欄位 | API / read model | 目前狀態 | 目前畫面來源 |
| --- | --- | --- | --- |
| 加權指數 | `GET /api/v1/snapshot/latest` → `market.indices[]` → `homeData.marketIndices` | 已接入；目前 public response 未提供可用 index | Mock fallback |
| OTC 指數 | 同上 | 已接入；目前 public response 未提供可用 index | Mock fallback |
| 成交金額 | 目前 snapshot contract 沒有成交金額欄位 | 無可安全串接欄位 | Mock |
| 上漲／下跌／平盤 | `marketRadar.breadth`（同一 snapshot read model） | 已接入；目前 public response 未提供 market radar | Mock fallback |
| 漲停／跌停 | 目前 snapshot contract 沒有漲停／跌停欄位 | 無可安全串接欄位 | Mock |
| 更新時間 | `freshness.quoteUpdatedAt` / `generatedAt` | 已接入；公開 synthetic preview 不當成正式即時時間 | 資料待更新 |
| 今日市場重點 | 尚無 authoritative Home focus API | 等待 API | Mock |
| 主線 Top 3 | 尚無 authoritative topic ranking API；既有 topics read model 不等於排序契約 | 等待 API | Mock |
| Timeline | 尚無 Home event API | 等待 API | Mock |
| 升溫／退潮 | 尚無 Home rotation API | 等待 API | Mock |
| 我的收藏 | 尚無登入／收藏 API | 等待登入 | Mock / hidden signed out |
| 今日機會 | 尚無 opportunity preview API | 等待 API | Mock |

因此本次不是把所有內容強行標成 Live：能安全接入的欄位已建立 Live path，當前 public read model 沒有提供的欄位維持既有 mock，且未推測或新增 Backend contract。

## 4. 尚未串接 API

- 市場概況完整 aggregate：成交金額、漲停、跌停。
- 可供 Home 使用的 authoritative market indices 與 breadth read model。
- Today Focus API。
- Topic ranking / Top 3 API。
- Intraday event timeline API。
- Topic rotation API。
- Authentication 與 favorites summary API。
- Opportunity preview API。

## 5. 修改元件與文件

修改：

- `apps/web/app/components/v2/TodayMarketPage.tsx`
  - Hero polish、freshness formal state、snapshot live-data adapters。
- `apps/web/app/components/v2/V2Foundation.tsx`
  - `PageContainer` 增加 scoped `className`，只供 Home Hero spacing 使用。
- `apps/web/app/globals.css`
  - 新增 TASK-FE-002A scoped Hero density overrides；未修改 Design Tokens 或 Header styles。
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`
  - 新增 Section 22.7，記錄 Hero hierarchy、第一屏密度與 data boundary。

新增：

- `docs/reports/TASK-FE-002A_HOME_HERO_POLISH_REPORT.md`
- `docs/reports/TASK-FE-002A_HOME_AFTER_DESKTOP.png`

## 6. 驗證

- `npm run lint`：通過。
- `npm run build`：通過。
- `npx tsc --noEmit`：仍有既有錯誤，集中在 `app/lib/data-source.ts`、`app/lib/snapshot-store.tsx`、`app/watchlist/page.tsx`、`vite.config.ts` 與 `worker/index.ts`；沒有新增 TASK-FE-002A 檔案錯誤。
- Browser desktop smoke：H1 為 `今日市場`、Hero eyebrow count 為 0、Market Pulse count 為 0、首頁區塊數為 6，`今日市場重點` 在第一屏可見。
- Header、Topic、Stock、Favorites、Opportunity、Backend business logic、Schema、API contract、Design Tokens 均未修改。

本階段完成後停止，未開始下一個頁面或下一個 Phase。
