# TASK-FE-002 — 今日市場正式實作報告

日期：2026-08-10  
狀態：完成，停止於 TASK-FE-002

## 1. 完成內容

`/` 已由 Foundation preview 替換為正式的「今日市場」市場導航頁，並保留既有 V2 App Shell 與 Global Header。頁面閱讀順序固定為：

1. Page Header + 頁面 freshness/data state
2. 市場概況 Summary Card
3. 今日市場重點
4. 今日主線 TOP3
5. 盤中重要事件
6. 快速升溫／快速退潮
7. 我的收藏登入邊界
8. 今日機會 Preview

首頁沒有加入股票排行、完整股票列表、K 線、技術分析圖、新聞流、完整題材地圖或 AI 對話。

## 2. Home Component Tree

```text
AppShell
└─ TodayMarketPage
   └─ PageContainer
      ├─ Page Status
      │  ├─ Freshness: 盤中更新
      │  └─ DataState: 資料待更新
      └─ Home Content
         ├─ 市場概況 / Card
         │  ├─ Primary metrics: 加權指數、OTC 指數、成交金額
         │  ├─ Secondary metrics: 漲跌家數、漲跌停、更新時間
         │  └─ Development snapshot note
         ├─ 今日市場重點 / Card
         ├─ 今日主線 TOP3 / clickable topic cards → /topics
         ├─ 盤中重要事件 / timeline
         ├─ 快速升溫／快速退潮 / two compact topic lists → /topics
         ├─ 我的收藏 / authenticated-only boundary, hidden signed out
         └─ 今日機會 / teaser list → /opportunities
```

## 3. Layout 說明

- Desktop-first，沿用 V2 frozen `1600px` content max width、24px card padding 與 8px spacing rhythm。
- 市場概況使用一張橫向白色 Summary Card；前三個核心市場數字獨立提高權重，其餘指標以較密集的第二列呈現。
- 今日主線固定三張卡，卡片可點擊進入題材頁；不在首頁暴露股票清單或 Leader Table。
- 盤中事件採四欄時間線，僅保留四個具意義的狀態轉換。
- 升溫／退潮採左右雙欄，各三個題材，回答資金輪動方向。
- 整體維持暖灰頁面背景、白色 surfaces、細暖灰 border、低強度 shadow；紅綠只用於市場價格方向與漲跌家數。

## 4. Design Spec 更新

已更新 `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`：

- Section 5 改為 TASK-FE-002 的固定 Home hierarchy 與頁面目的。
- 明確定義市場概況、單段市場重點、Top 3、事件、升溫／退潮、登入後收藏、機會 preview 的順序。
- Section 22 從未實作的 Home V1 freeze 更新為已核准的 V2 implementation freeze。
- 移除今日強勢股／今日弱勢股與首頁股票排行的相關描述。
- 補上固定開發快照與 market aggregate、freshness、timeline、favorites、opportunity API 的整合邊界。

## 5. Mock 資料與 API 等待項目

目前首頁全部內容使用 `TodayMarketPage.tsx` 內的固定 development snapshot：市場指標、今日市場重點、Top 3 題材、事件時間線、升溫／退潮清單與機會 preview。

仍等待 Backend/API 的項目：

- 市場概況 aggregate 與正式更新時間。
- 盤中／盤後／待更新 freshness 狀態。
- 有門檻的題材事件 timeline。
- 確定性的今日市場重點來源。
- 題材卡片的等級與可讀狀態。
- 登入後收藏摘要與會員身份狀態。
- 今日機會 teaser 與符合條件數量。

本階段未修改 API、backend、schema 或 V1 business pages。

## 6. 驗證與預覽

- `npm run lint`：通過。
- `npm run build`：通過。
- `npx tsc --noEmit`：未通過，但錯誤集中於既有 `data-source.ts`、`snapshot-store.tsx`、`watchlist/page.tsx`、`vite.config.ts` 與 `worker/index.ts`，不涉及本次新增 Home component。
- `git diff --check`：通過。
- Desktop route smoke：`/`、`/topics`、`/stocks`、`/favorites`、`/opportunities`、`/ai-studio` 均保留單一 Header、單一 active nav，且無 `.tp-utility` 重複 utility row。
- Home smoke：6 個正式區塊、3 張主線卡、4 個事件、12 個可導覽內容連結均正常展示；禁止內容關鍵字檢查為空。

Desktop 預覽：

- [Home desktop top](TASK-FE-002_HOME_DESKTOP.png)
- [Home desktop mainline and timeline](TASK-FE-002_HOME_DESKTOP_LOWER.png)
- [Home desktop additional capture](TASK-FE-002_HOME_DESKTOP_BOTTOM.png)

本階段完成後停止，未開始題材頁或其他下一階段工作。
