# API Route 與前端契約核對

## 五個唯讀端點

| Frontend fetch | 本機 Router | OpenAPI | 本機 HTTP | 4317 HTTP |
|---|---|---|---:|---:|
| `financial-summary` | `financial_research.api` | 已註冊 | 200 | 404 |
| `financial-coverage` | `financial_research.api` | 已註冊 | 200 | 404 |
| `financial-statements` | `financial_research.api` | 已註冊 | 200 | 404 |
| `financial-research-status` | `financial_research.api` | 已註冊 | 200 | 404 |
| `eps-bridge` | `financial_research.api` | 已註冊 | 200 | 404 |

對應程式：

- Frontend：`apps/web/app/lib/financial-research-api.ts`
- Frontend renderer：`apps/web/app/components/v2/StockResearchCards.tsx`
- Backend router：`services/api/src/topicpilot_api/financial_research/api.py`
- Backend registration：`services/api/src/topicpilot_api/main.py`
- Isolated store：`services/api/src/topicpilot_api/financial_research/real_preview.py`

## 010 最小修正

`infra/scripts/preview_review.mjs` 新增 `--financial-api-origin`，並將其只注入 `NEXT_PUBLIC_FINANCIAL_RESEARCH_API_BASE_URL`。原股票／題材 read API 不變；沒有把 404 轉成成功空資料，也沒有加入任何寫入能力。

本次另同步了期間契約：Financial Summary Metric、Financial Statement Line 與 EPS Bridge Record 均保留 `period_type`；前端以同一規則呈現年度、季度、上半年與前三季累計，避免 `2026Q2_YTD` 在不同區塊被顯示成不一致的期間。

