# TASK-FE-BE-011｜Stock + Topic Detail Production Read Models & Runtime Integration

日期：2026-08-12  
範圍：`/stocks`、V2 stock encyclopedia Drawer、`/topics/:slug`；未改 Overview/Home、Opportunity 或 NEXT_TASK。

## Executive Summary

本階段完成 V2 正式 FastAPI read model 與前端 runtime wiring：

- 新增正式端點：`GET /api/v2/stocks`、`GET /api/v2/stocks/{symbol}`、`GET /api/v2/topics`、`GET /api/v2/topics/{slug}`。
- Stock Explorer 的市場、題材、LIVE/EOD 篩選與排序改由正式資料語意驅動；沒有 API 時才保留既有 Preview/Unavailable fallback。
- Topic detail 改讀正式 topic read model、正式成分股價格/漲跌/更新狀態與 participation status evidence。
- Drawer 改為 viewport-fixed，header 與 body 分離；body 獨立滾動，並加入 200ms 動畫與 reduced-motion 規則。
- OpenAPI 與 generated client types 已由 live API 重新產生。

目前尚未宣稱全部資料 ready：資料庫尚未提供正式 lifecycle、leader、diffusion、MA20/MA60 完整技術模型；這些欄位保持 `NULL` 或 `NOT_AVAILABLE`，不由前端推導。

## Existing implementation audit

原有 `/api/v1/stocks`、`/api/v1/topics` 是 legacy/demo contract，不能作為 V2 production read model。既有 V2 正式資料來源為 `topicpilot` schema 的 instruments、markets、topics、instrument_topic_relations、live_tracking_universe、canonical observations、topic_snapshots。

本階段新增的 composition code 位於：

- `services/api/src/topicpilot_api/production_read_model.py`
- `services/api/src/topicpilot_api/production_read_model_api.py`
- `services/api/src/topicpilot_api/schemas.py`

前端 wiring 位於：

- `apps/web/app/lib/stock-api.ts`
- `apps/web/app/lib/topic-api.ts`
- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/app/components/v2/TopicDetailPage.tsx`
- `apps/web/app/globals.css`

## API contracts

### Stock list/detail

`StockReadModel` 包含 identity、market、price/change、observed/retrieved、freshness/updateMode/marketStatus、topic relations、tracking、history coverage、technical evidence，以及 nullable favorite/opportunity/institutionFlows/summary placeholders。

`topicRole` 只接受正式明確角色 `代表股`、`核心股`、`關聯股`；目前 DB 的 `RELATED` relation_type 沒有被轉成 `關聯股`，所以沒有正式 role 時回傳 `NULL`。

`mainTopic` 目前回傳 `NULL`，因現有正式資料尚未提供 approved main-topic field；前端不以第一個 relation 推導主題。

### Topic detail

`TopicReadModel` 包含 topic identity、grade/score/direction/strength state、dataDate、status、lifecycle、constituents。

成分股包含 instrument identity、role、relationWeight、price/changePct、observedAt、updateMode、freshness。正式 topic relation 不含 role 時保持 `NULL`。

### Status semantics

目前只提供可由正式 snapshot/constituent data 支持的 `族群表現`；`領漲核心`、`動能擴散` 保留 `NULL` state 並附上「正式規則尚未核准」 evidence，不以 `max(changePct)` 或前端推論代替。

Participation detail 使用：`observedStockCount`、`totalStockCount`、`risingCount`、`fallingCount`、`flatCount`、`participationPct`。Leader/diffusion rule 待後續正式 policy approval。

### Lifecycle

API 已保留 `currentStage`、`currentStageEnteredAt`、`currentStageTradingDays`、history segments contract，但現有 DB 沒有可供 production 消費的 lifecycle table/snapshot，因此回傳 `NOT_AVAILABLE`，沒有用今日漲跌推導階段，也沒有移除 re-entry model 的位置。

## Universe evidence

以 V2 formal universe 的 active TPE/TWO instruments 為範圍：

| Metric | Runtime result |
|---|---:|
| Total formal universe | 507 |
| TPE | 314 |
| TWO | 193 |
| INTRADAY | 15 |
| POST_CLOSE | 24 |
| UNKNOWN / DATA_PENDING | 468 |
| Priced | 506 |
| Missing price | 1 |
| Topics | 130 |
| Topic relations | 848 |
| Instruments with formal topic relation | 507 |

這是 DB formal universe，不是 4 檔 curated sample。`TEST.EQ` 不列入 production TPE/TWO universe。

## FastAPI / DB / API evidence

已以 live Docker API 驗證：

- `GET /readyz`：HTTP 200。
- `GET /api/v2/stocks?limit=3`：HTTP 200，回傳 formal universe metadata 與 read-model fields。
- `GET /api/v2/stocks/2330`：HTTP 200；包含 TPE/TWSE identity、price、changePct、freshness、tracking 與 topicRelations。
- `GET /api/v2/topics/AI%20PCB`：HTTP 200；包含 formal topic identity、participation evidence 與 28 筆成分股。
- `GET /openapi.json`：HTTP 200；再同步至 `packages/api-client/openapi.json` 並執行 generated type generation。

Representative DB/API/UI traces:

1. Stock `2330`：DB formal instrument → `/api/v2/stocks/2330` → Stock Explorer formal row；price、changePct、observedAt、updateMode 與 relation roles 由 API 直接提供。
2. Stock `2317`：同一 stock read model contract；未有正式 role 時 role 保持 `NULL`。
3. Stock `6488`：同一 market/price/freshness contract；沒有 institution-flow/summary 欄位時維持 `NULL`。
4. Topic `AI PCB`：DB topic snapshot/relations → `/api/v2/topics/AI PCB` → Topic detail；28 constituents 與 participation counts 由正式資料計算/組合。
5. Topic `ADAS`：同一 `/api/v2/topics/{slug}` contract；4 constituents、COOLING direction 與 formal freshness 由 API 提供。
6. Topic `12 吋矽晶圓`：同一 topic detail contract；4 constituents 與 WARMING direction 由 API 提供，缺少 grade/score 時保持 `NULL`。
7. Topic list：`/api/v2/topics` 提供 list-level identity、date、direction 與 coverage evidence。

The shared Drawer now requests `/api/v2/stocks/{symbol}` on formal-stock open, so the detail surface does not rely only on the list payload.

## UI → API mapping

| UI | Formal source | Preview / missing behavior |
|---|---|---|
| Stock market TPE/TWO | `market` | 不再使用 relation type；無 API 時 unavailable/Preview |
| Stock topic filter | `topicRelations.topicSlug/topicName` | 不從前端自行建立題材關係 |
| LIVE/EOD | `updateMode` | UNKNOWN 不被塞入 LIVE 或 EOD |
| Stock sort | API semantic sort parameter | 沒有 frontend recommendation sort |
| Stock Drawer | formal row/detail contract | formal data 優先；nullable fields 顯示尚未提供 |
| Topic status | formal `status[]` | 只有 formal evidence 才顯示；其餘 Preview/Unavailable |
| Topic constituents | formal constituent read model | formal price/change 不以 legacy preview 覆蓋 |
| Technical / relative topic state | formal nullable fields | 尚無 formal evidence 時明確顯示尚未提供 |

## Drawer viewport lock

`apps/web/app/globals.css` 的 TASK-FE-BE-011 override 將 inline Drawer 設為：

- `position: fixed`
- `top: 72px`（primary nav bottom）
- `bottom: 0`
- `width: var(--tp-drawer-width)`，預設 560px
- `overflow: hidden` 外框
- header 不滾動、body `flex: 1; overflow-y: auto`
- close/switch actions 維持於 header
- 約 200ms ease-out；`prefers-reduced-motion` 時停用動畫

本機 browser smoke test 另外受到本次 production preview 的舊 `index-n6TMV3ou.js` 404 影響，未把失敗的 chunk load 誤算成 Drawer UI PASS。公開 Sites version 35 已重新驗證：viewport `1280x720` 下 Drawer computed `position=fixed`、`top=72`、`bottom=0`、`right=0`、寬度 `537.6px`；header 位於 body scroll container 之前，body `clientHeight=469`、`scrollHeight=962`，在 Drawer 內滾動後 `scrollTop=360` 且 Drawer 仍維持 `top=72`。Close action 返回 0 個 Drawer，重新點擊第二張 tile 後 header 切換為 `Boreal Energy`。

公開 Preview 的四筆資料頁本身 document height 為 720px，沒有足夠的頁面 overflow 可執行 `scrollY >= 500`；因此 page-scroll case 以 computed fixed anchor 與獨立 body scroll 交叉驗證，沒有把不可滾動的 Preview 頁誤報成已完成 page-scroll 測試。

## OpenAPI / generated types

`packages/api-client/openapi.json` 由 live `http://localhost:8000/openapi.json` 重新取得；`packages/api-client/src/schema.d.ts` 與 `apps/web/app/lib/generated-api.d.ts` 已重新生成。

## Verification

- Frontend build：PASS。
- Frontend lint：PASS。
- Frontend `npx tsc --noEmit`：PASS。
- `git diff --check`：PASS。
- Backend pytest：PASS，251 passed / 31 skipped（skips require an explicitly configured PostgreSQL test database）。
- Backend Python compile/import/read-model schema validation：PASS。
- Live Docker API readiness and endpoint smoke tests：PASS。
- Ruff：changed production read-model files PASS with existing repository E501 line-length baseline excluded；full repository Ruff remains blocked by 183 pre-existing style findings。
- API integration assertions：PASS；507 stocks、TPE 314、TWO 193、2330/2317/6488 detail、3 topic detail samples 與 OpenAPI paths 均驗證。
- Browser visual smoke：公開 Sites version 35 `/stocks` 與 `/topics/AI%20PCB` 可開啟；Drawer viewport/body metrics、close、switch PASS。

公開部署資訊：Sites version `35`，deployment `appgdep_6a7b60e1843081918b5c9fec6e96fb93`，URL `https://topicpilot-platform.game0962046460.chatgpt.site`。

## Known gaps / follow-up

1. Public Sites environment 目前只有 `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=true`，沒有公開 FastAPI `NEXT_PUBLIC_API_BASE_URL`；因此公開站點目前仍會走 Preview/Unavailable，而不是直接連本機 API。不能把 localhost API 暴露給公開站點。
2. Formal lifecycle data 尚未建立。
3. Formal leader/diffusion status policy 尚未核准。
4. Formal MA20/MA60、breakout、institution flows、summary、favorite/opportunity read models 尚未完整具備。
5. 舊 `/stocks/[code]` legacy detail route 尚未搬遷；本階段的 V2 Stock Detail contract 由正式 API 與 V2 encyclopedia Drawer 消費。

## Final verdict

STOCK_LIST_API = READY  
STOCK_DETAIL_API = READY  
TOPIC_DETAIL_API = READY  
TOPIC_STATUS_DATA = PARTIAL  
LIFECYCLE_DATA = NOT_READY  
TOPIC_CONSTITUENT_DATA = READY  
FRONTEND_FORMAL_DATA = PARTIAL  
DRAWER_VIEWPORT_LOCK = PASS  
PRODUCTION_SYNTHETIC_DEPENDENCY = PARTIAL

停止於 TASK-FE-BE-011；未自動開始下一階段。
