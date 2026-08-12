# TASK-FE-BE-015 — Stock Universe Full Import & `/stocks` Formal API Integration Audit

日期：2026-08-12  
範圍：V2 Stock Explorer、正式股票 read model、前端資料路徑、設計規範與公開 Sites runtime 設定  
限制：未修改 Home、Topic Overview、Topic Detail、backend business rules 或 production API schema；本次 backend 僅做唯讀驗證。

## 1. Executive Summary

本次稽核確認 V2 PostgreSQL 與 FastAPI 的正式 TPE/TWO 股票 universe 已完整建立：TPE 314 檔、TWO 193 檔，共 507 檔。正式 read model 不會因為缺少價格、60MA tracking、topic relation、technical 或 institutional evidence 而丟棄股票身份；本次 runtime response 為 506 檔有價格、1 檔保留缺價。

原本 `/stocks` 看起來只有少數股票的原因不是 PostgreSQL 只匯入少數資料，而是公開 Sites runtime 沒有設定 `NEXT_PUBLIC_API_BASE_URL`，頁面遂使用 checked-in `web_snapshot.json` 的 Preview 資料；該 snapshot 只有 4 筆股票與 5 筆 relation。

本次修正把 `/stocks` 的正式資料路徑明確化：有 FastAPI origin 時只使用 `/api/v2/stocks`，完整讀取分頁並保留 nullable fields；正式 API 讀取失敗時顯示 unavailable，不以 4 筆 snapshot 蓋掉正式錯誤。沒有設定正式 API 時才顯示明確的 Preview badge。盤中刷新只更新卡片內容，不改既有卡片順序；只有手動更換排序或按下 `重新排序` 才重建順序。

## 2. Canonical Stock Master

正式身份來源是 V2 `topicpilot.instruments` 與 `topicpilot.markets`，篩選條件為：

- `instrument_type = EQUITY`
- `instruments.is_active = true`
- `markets.is_active = true`
- market code 為 `TPE` 或 `TWO`

Identity query 只以 instrument 與 market 為必要關係；價格、tracking、canonical observations、topic relations 都是 optional evidence，不是顯示身份的 prerequisite。

Canonical count：

| Market | Active formal instruments |
|---|---:|
| TPE | 314 |
| TWO | 193 |
| **Total** | **507** |

資料庫另有測試 fixture `TEST.EQ`，不計入正式 TPE/TWO universe。

## 3. PostgreSQL Evidence

2026-08-12 local PostgreSQL read-only query 結果：

```text
market | instrument_count | active_count
TPE    | 314              | 314
TWO    | 193              | 193

total_active_equity = 507
```

這表示 full import／identity bootstrap 已完成。日線資料 coverage 不等於 identity coverage；目前 6806 的官方來源曾回覆 `EXCHANGE_NO_DATA`，因此它仍必須出現在股票頁，但價格可以是 `NULL`。

## 4. Market Data Coverage

本次 live FastAPI `/api/v2/stocks?limit=1000&sort=symbolAsc` response 的 universe metadata：

| Evidence | Count |
|---|---:|
| Formal total | 507 |
| Priced | 506 |
| Missing price | 1 |
| INTRADAY | 15 |
| POST_CLOSE | 24 |
| UNKNOWN / data pending | 468 |
| TPE | 314 |
| TWO | 193 |

`UNKNOWN` 不代表股票不存在，也不代表負值或零值；它表示目前 tracking／history evidence 不足。前端將非 INTRADAY row 顯示為 EOD / `盤後更新`，不在卡片上曝露內部 classification reason。

## 5. FastAPI Stock List Evidence

正式路由：`GET /api/v2/stocks`

支援欄位：`market`、formal `topic` slug、`updateMode`、`sort`、`limit`、`offset`。OpenAPI contract 的最大 page size 為 1000；前端現在會在 `total > items.length` 時繼續讀取後續 pages，不把第一頁誤當成完整 universe。

Runtime evidence：

- HTTP 200，`total = 507`、`items.length = 507`、`limit = 1000`。
- `universe` metadata 與 PostgreSQL count 對齊：507 / 506 priced / 1 missing price / TPE 314 / TWO 193。
- Identity row 具備 `instrumentId`、`symbol`、`code`、`name`、`market`、`active`、`enabled`。
- nullable quote、tracking、technical、institution、favorite、opportunity 與 summary fields 會原樣保留。

## 6. FastAPI Stock Detail Evidence

正式路由：`GET /api/v2/stocks/{symbol}`，由同一個 formal read model composition 產出，不讀 legacy `public.stocks` demo table。

Detail contract 保留：

- identity／market／listing
- price／changePct／observedAt／retrievedAt
- `updateMode`、`dataFreshness`、`trackingMode`、`trackingReason`
- `historyCoverage` 與 20MA／60MA evidence
- `topicRelations`、main topic placeholder
- institution、favorite、opportunity、summary 的 nullable state

對於 6806 這類缺少官方當日價格的股票，detail 仍應回傳 identity 與 `price = null`，而不是 404 或用 0 代替。對於沒有 canonical role 的 relation，`topicRole` 保留 `NULL`，前端顯示待資料狀態，不自行猜測代表股／核心股／關聯股。

## 7. Frontend Data Path Audit

修正前的資料鏈如下：

```text
/stocks
  → StockExplorerPage
  → fetchFormalStocks()
  → 若沒有 API origin，回傳 synthetic-snapshot
  → useSnapshot().bundle.stockUniverse
  → checked-in web_snapshot.json
  → 4 筆 Preview 股票
```

修正後：

```text
有 NEXT_PUBLIC_API_BASE_URL
  → GET /api/v2/stocks（含分頁）
  → formal StockApiItem
  → 507 identities / nullable evidence
  → Stock Explorer cards + Encyclopedia Drawer

沒有 API origin
  → 明確 Preview
  → checked-in snapshot only

有 API origin 但 API 失敗
  → unavailable state
  → 不回退到 snapshot
```

正式 API origin 可由 layout 的 runtime `data-api-base-url` 或 `NEXT_PUBLIC_API_BASE_URL` 取得。Home、Topic、Watchlist 等既有 snapshot compatibility path 未被本次頁面改寫。

## 8. Snapshot / Preview Audit

checked-in `apps/web/app/lib/web_snapshot.json` 的實際內容是 prototype snapshot，不是正式 stock master：

| Snapshot field | Count |
|---|---:|
| stock records | 4 |
| topic relation records | 5 |
| priced records | 4 |

這 4 筆不是 PostgreSQL universe 的完整結果，因此只能在沒有正式 API origin 時標示 Preview。公開 Sites 目前只有 `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=true`，沒有 `NEXT_PUBLIC_API_BASE_URL`；這是公開頁仍會看到 Preview subset 的直接原因。

## 9. DB → API → UI Reconciliation

| Layer | Expected / actual | Status | Evidence |
|---|---:|---|---|
| PostgreSQL formal identities | 507 | PASS | `topicpilot.instruments` + `markets` |
| PostgreSQL TPE / TWO | 314 / 193 | PASS | read-only count query |
| FastAPI list `total` | 507 | PASS | `/api/v2/stocks?limit=1000` |
| FastAPI list `items` | 507 | PASS | runtime response |
| FastAPI identity fields | present for all rows | PASS | formal read model query |
| Price coverage | 506 priced / 1 null | PASS | `universe` metadata |
| Frontend formal API client | formal when configured | PASS | `stock-api.ts` |
| Frontend full pagination | `total`-aware | PASS | TASK-FE-BE-015 implementation |
| Frontend card identity | API row → card | PASS | `fromFormal()` |
| Frontend missing-price semantics | null preserved | PASS | `formatPrice(null) = —` |
| Public Sites API origin | not configured | PARTIAL | Sites env audit |
| Public `/stocks` 507 visibility | not yet possible | FAIL | no public HTTPS FastAPI origin |

## 10. Missing Stock List

Formal local API missing identity list：無。507 檔均存在於 formal list response。

Formal market-data gap：TPE `6806`（森崴能源）為已知官方 `EXCHANGE_NO_DATA` boundary；它不是 missing identity，應以缺價／待資料狀態顯示。

Public page missing list：目前公開站點因未配置 formal API origin 仍只會看到 checked-in Preview snapshot 的 4 筆；這不是正式 API missing list，而是 deployment configuration gap。

## 11. Implementation Changes

本次實際修改：

- `apps/web/app/lib/stock-api.ts`
  - 使用 generated OpenAPI schema types。
  - 支援 `/api/v2/stocks` 1000-row page 與後續分頁。
  - formal API origin 未配置時明確回報 Preview；已配置但失敗時回報 unavailable。
  - normalize optional topic relations、main topic、history coverage，保留 nullable evidence。
- `apps/web/app/components/v2/StockExplorerPage.tsx`
  - formal API 優先資料路徑。
  - 市場、題材、技術、籌碼／法人、個人策略、更新模式分組篩選。
  - 60 秒正式資料刷新；既有卡片順序由 order state 固定。
  - 更換排序或 `重新排序` 才更新順序並記錄 `last sorted` timestamp。
  - LIVE / EOD card semantics；EOD card 只顯示 `盤後更新`。
  - click 開啟 shared Stock Encyclopedia Drawer。
- `apps/web/app/globals.css`
  - 統一 `市場`、`排序`、`進階篩選`、`重新排序` control height、border、background 與 hover state。
  - EOD card muted styling。
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`
  - 新增 TASK-FE-BE-015 的 formal/Preview boundary、pagination、stable sorting、filter group 與 drawer semantics。

未修改：Home、Topic Overview、Topic Detail、FastAPI business logic、database schema、migration、production API source。

## 12. Formal vs Preview

### Formal

- source：V2 PostgreSQL-backed FastAPI read model
- route：`/api/v2/stocks`、`/api/v2/stocks/{symbol}`
- identity：507 formal instruments
- missing values：保留 `NULL`，不補 0、不刪除 identity
- LIVE/EOD：由 API `updateMode` 與 freshness evidence 決定
- topic options：由 formal `topicRelations` 動態產生

### Preview

- source：checked-in `web_snapshot.json`
- size：4 stock rows / 5 relations
- label：Preview
- purpose：未配置正式 API 時讓 UI prototype 可檢查
- restriction：不得覆蓋已配置但失敗的 formal API，也不得宣稱完整 507 universe

## 13. Browser Verification

Local source/build verification confirms `/stocks` remains in the route manifest and the page compiles with the new formal path. The intended browser checks are:

1. configured FastAPI origin：頁首不顯示 Preview，顯示 formal Read Model，507 identities 可由 cards/filter 讀到。
2. changing quotes：price/change 更新，card position 不變。
3. changing sort or pressing `重新排序`：order changes and timestamp updates。
4. EOD selection：card muted and shows `盤後更新` only；reason remains in drawer。
5. card click：right-side Encyclopedia Drawer opens while Explorer remains visible。

Public browser verification remains partial because the current Sites environment does not expose a verified HTTPS FastAPI origin. The site can be deployed with the new UI, but it will intentionally remain labelled Preview until that origin is configured.

## 14. Production Deployment Verification

Sites project：`appgprj_6a6ce02bd75c81919ab3678ebf013c53`  
Public URL：`https://topicpilot-platform.game0962046460.chatgpt.site/stocks`

Current production environment audit：

| Variable | Current state |
|---|---|
| `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK` | `true` |
| `NEXT_PUBLIC_API_BASE_URL` | not configured |

Therefore the public page can receive the UI implementation, but cannot truthfully show all 507 formal identities. A verified HTTPS FastAPI endpoint must be configured before the public production verdict can become READY.

## 15. OpenAPI / Generated Types

The formal stock contract is present in:

- `packages/api-client/openapi.json`
- `packages/api-client/src/schema.d.ts`
- `apps/web/app/lib/generated-api.d.ts`

The contract includes `/api/v2/stocks`, `/api/v2/stocks/{symbol}`, `StockReadModel`, `StockReadModelPage`, `StockTopicRelationRead`, `StockTechnicalEvidence`, pagination fields and `universe` metadata. The frontend client now consumes these generated types instead of narrowing formal nullable values into a synthetic card type.

## 16. Tests and Validation

Passed after the implementation:

- `npm run build` — PASS; `/stocks` present in route manifest.
- `npm run lint -- --no-cache` — PASS.
- `npx tsc --noEmit` — PASS.
- `git diff --check` — PASS for task files.
- Live API evidence captured before the local Docker runtime became unavailable: `/api/v2/stocks` returned 507 rows and the universe metadata matched PostgreSQL.

The late re-run of the local API was blocked by the existing Docker daemon/container state (`read-only file system` and a stale compose container-name conflict). No database write, migration, reset, or destructive cleanup was performed.

## 17. Remaining Gaps

1. Public Sites still lacks a verified HTTPS `NEXT_PUBLIC_API_BASE_URL`; this is the blocker for public 507-card verification.
2. Formal read model currently has partial evidence coverage by design: 468 rows are `UNKNOWN`, one row lacks a price, and optional institution/favorite/opportunity/summary fields may be null.
3. Topic role, main topic, institutional-flow detail and deeper technical fields remain backend-authoritative and are not inferred in the browser.
4. The existing `/stocks/[code]` legacy detail route is outside this task; the Explorer uses the shared Encyclopedia Drawer instead.

## 18. Recommended Next Step

Provision or verify the public HTTPS FastAPI origin, set it as the Sites environment variable `NEXT_PUBLIC_API_BASE_URL`, redeploy the same validated frontend version, then repeat the production browser check for `total = 507`, TPE 314, TWO 193, one explicit null-price row, stable live refresh ordering, and the detail drawer.

## Final Verdict

```text
STOCK_UNIVERSE_DB = READY
STOCK_IDENTITY_COUNT = 507
STOCK_LIST_API = READY
STOCK_DETAIL_API = READY
STOCKS_FRONTEND_FORMAL_DATA = READY
ALL_FORMAL_STOCK_IDENTITIES_VISIBLE = PASS
ALL_507_STOCK_IDENTITIES_VISIBLE = FAIL
LEGACY_STOCK_FALLBACK_IN_PRODUCTION = PARTIAL
PRODUCTION_STOCK_PAGE = PARTIAL
```

### Questions answered

1. DB 是否完整匯入？是；正式 TPE/TWO identity 共 507 檔。
2. API 是否回傳完整 universe？是；local formal `/api/v2/stocks` 回傳 507/507，nullable evidence 另行標示。
3. 為什麼之前只有 4 檔？公開 runtime 沒有 API origin，頁面使用 4 筆 checked-in snapshot Preview。
4. 是否已修正 frontend formal integration？是；配置正式 API 時不再用 snapshot 覆蓋 formal data，並支援完整分頁。
5. 修正後是否所有 identity 可見？在 configured local formal runtime 是；目前公開 Sites 因未配置 HTTPS API 仍是 Preview，故 public verdict 仍為 FAIL。
6. 剩餘問題是什麼？公開 API origin／Sites env 尚未完成；另外 market-data 與 optional evidence coverage 仍照實保留，不影響 identity visibility。

## Post-bootstrap production reconciliation (2026-08-12)

The previously recorded public-origin gap is resolved. The user confirmed the
Neon `topicpilot` production bootstrap, including 507 instruments and 848
instrument-topic relations. Read-only verification against the existing Render
origin now returns:

- `/api/v2/stocks?limit=1000&offset=0`: `total=507`, 507 items;
- TPE/TWO membership: 314/193;
- `/api/v2/stocks/2330`: 200 with formal ASIC/topic relations;
- `/api/v2/stocks/6806`: 200 with identity retained and `price=null`;
- no DEMO/PREVIEW identity rows.

The production browser `/stocks` shows `507/507 檔`, TPE/TWO filters, 2330,
and the formal Stock Encyclopedia Drawer. Sites uses the Render API base and
`NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false`. The API, UI, and formal DB counts
therefore reconcile.

## Current fixed output

```text
STOCK_UNIVERSE_DB = READY
STOCK_IDENTITY_COUNT = 507
STOCK_LIST_API = READY
STOCK_DETAIL_API = READY
STOCKS_FRONTEND_FORMAL_DATA = READY
ALL_FORMAL_STOCK_IDENTITIES_VISIBLE = PASS
ALL_507_STOCK_IDENTITIES_VISIBLE = PASS
LEGACY_STOCK_FALLBACK_IN_PRODUCTION = REMOVED
PRODUCTION_STOCK_PAGE = READY
```
