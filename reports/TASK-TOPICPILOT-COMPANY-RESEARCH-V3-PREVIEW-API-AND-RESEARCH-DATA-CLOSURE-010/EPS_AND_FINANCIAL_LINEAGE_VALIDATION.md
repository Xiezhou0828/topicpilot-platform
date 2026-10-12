# EPS 與財務資料血緣驗證

## 來源鏈

```text
官方財報／EPS Note evidence
  → real_preview.py normalized facts
  → financial_research.api response model
  → financial-research-api.ts
  → FinancialSection / EpsBridgeReadout
  → Browser Preview
```

## 結果

| 公司 | 期間 | 公告 EPS | 重算 EPS | 狀態 |
|---|---|---:|---:|---|
| 1303 | 2026 Q1 累計 | 1.80 | 1.80 | `RECOMPUTED_MATCH` |
| 1314 | 2026 Q1 累計 | -0.07 | -0.07 | `RECOMPUTED_MATCH` |
| 1314 | 2026 H1 累計 | -0.52 | -0.52 | `RECOMPUTED_MATCH` + `MANUAL_REVIEW_REQUIRED` |
| 1319 | FY2025 | 6.43 | 6.43 | `RECOMPUTED_MATCH` |

1314 的 NT$8,426,000 差異仍在 financial limitations 顯示，沒有因 EPS bridge 相符而宣稱整份財報已完成驗證。缺少股數的期間維持 `BRIDGE_INPUT_INCOMPLETE`，沒有用期末股數或公告 EPS 反推。

期間顯示驗收：1314 的 2026 Q2 YTD 在 EPS Bridge、財務摘要、可用期間、限制提示與比較表均顯示為「2026 上半年」；Q1 仍顯示「2026 年第1季累計」，FY2025 仍顯示「2025 全年」。H1 的 `MANUAL_REVIEW_REQUIRED` 狀態與官方數值相符不互相覆蓋。

