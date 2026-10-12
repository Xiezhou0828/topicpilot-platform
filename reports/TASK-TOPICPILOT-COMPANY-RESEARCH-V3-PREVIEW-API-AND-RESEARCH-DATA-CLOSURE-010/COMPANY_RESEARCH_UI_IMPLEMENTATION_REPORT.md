# Company Research V3 UI 實作報告

## 共用架構

```text
/stocks/[code]
  → StockDetailPage
    → StockResearchCards
      → OverviewSection
      → BusinessSection
      → IndustrySection
      → GrowthRiskSection
      → FinancialSection
      → SourcesSection
```

1303、1314、1319 均透過同一個 renderer；公司差異由研究資料物件提供，不是在 React 元件內建立三份頁面。

## 已驗證互動

- 產業鏈可切換。
- 成長／風險可展開。
- 轉投資可開啟詳情。
- 財務表格保留缺值為 `—`，不補零。
- EPS 期間標籤區分季度累計、上半年累計與全年。
- 研究 Fixture 在 `UNPUBLISHED` 狀態下顯示中文 Preview 審閱提示；正式發布後才隱藏提示。
- 官方來源僅顯示官方入口。

## 尚未完成

- 正式研究 Read Model 與公開發布 Gate。
- Forecast／估值公開頁。
- 遠端 Preview financial target 更新。
- 精確指定 viewport 的平板／手機截圖驗收。

