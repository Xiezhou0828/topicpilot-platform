# 財務與 EPS UI 資料 lineage

## 來源鏈

```text
畫面欄位
  -> StockResearchCards / FinancialSection
  -> fetchFinancialResearchReadout(symbol)
  -> financial-summary / coverage / statements / status / eps-bridge
  -> financial_research.api
  -> REAL_FINANCIAL_PREVIEW store
  -> normalized official financial facts + EPS note evidence
```

## 1303／1314／1319

| 公司 | 可確認的 API 結果 | 前端呈現 |
|---|---|---|
| 1303 | Q1 parent earnings、weighted shares、EPS 重算為 1.80；狀態 `RECOMPUTED_MATCH` | EPS 核對顯示公告 1.80／重算 1.80；Q2／FY 未驗證期間保留橋接不足 |
| 1314 | Q1 -0.07、H1 -0.52 均 `RECOMPUTED_MATCH`；H1 source note `MANUAL_REVIEW_REQUIRED`；8,426,000 差異獨立保留 | 顯示可用期間、來源權利待確認、EPS 核對及待釐清限制；未宣稱整份財報完全驗證 |
| 1319 | FY2025 6.43 `RECOMPUTED_MATCH`；2026 Q1／Q2 source unavailable | 顯示 FY2025 相符，其他期間顯示橋接資料不足 |

## 4317 與 4319 的差異

4317 的 `TOPICPILOT_PREVIEW_READ_API_ORIGIN` 指向 `https://topicpilot-api.onrender.com`；本次對五個財務端點讀回均為 HTTP 404，因此 `financialReadout.source=unavailable`。4319 使用同一套前端、同一個本機非 Production API，讀回 HTTP 200，完整顯示 `RealFinancialReadiness` 與 `EpsBridgeReadout`。

這證明前端接線存在且可工作，但正式 Preview API 合約尚未在遠端 target 完成暴露。這不是前端把 API 當 fixture 的問題，而是 target readiness gap。

## 邊界

- 研究 fixture 與 official financial facts 沒有互相覆蓋；API 可用時只替換財務 metrics 與狀態區。
- `source_rights_status=UNVERIFIED`，不得因此發布到公開 Production。
- 沒有把 EPS 公告值反推成股數，也沒有以期末股數代替加權平均股數。
