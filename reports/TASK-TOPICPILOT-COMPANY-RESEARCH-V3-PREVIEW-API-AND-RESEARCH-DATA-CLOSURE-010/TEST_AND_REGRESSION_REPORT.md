# 測試與回歸報告

| 測試 | 結果 |
|---|---|
| `npx tsc --noEmit` | PASS |
| `npm run build` | PASS |
| `npm test` | 227 passed / 0 failed |
| Company Research／Financial／EPS／Source Discovery pytest | 38 passed / 0 failed |
| Ruff（financial research modules + related tests） | PASS |
| Local OpenAPI route check | 五個 financial routes 全部存在 |
| Local HTTP contract | 1303／1314／1319 五路由均 HTTP 200 |
| Remote 4317 comparison | 五路由均 HTTP 404，記為既有 target gap |
| `git diff --check` | PASS |

追加回歸：1314 `2026Q2_YTD` 的 `period_type=ytd` 由共用前端期間格式化規則呈現為「2026 上半年」；EPS Bridge 的官方附註仍可提供更精確的 `half_year` 型別。研究 Fixture 的 Preview 審閱提示已加入，未改變 `UNPUBLISHED` 狀態。

沒有發現本次 Preview 設定修正造成的前端回歸。既有 dirty worktree 中未屬於本次的修改沒有被重排或清理。

