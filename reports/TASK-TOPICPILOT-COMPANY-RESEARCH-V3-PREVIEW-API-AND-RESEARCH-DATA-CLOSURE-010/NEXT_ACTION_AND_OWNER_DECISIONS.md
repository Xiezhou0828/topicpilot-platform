# 下一步與 Owner 決策

## 建議順序

1. 授權 Preview target 將五個 financial GET routes 與目前本機 API 契約同步，先做非 Production read-only 部署。
2. 將 Company Research JSON 移入版本化 Research Read Model；同時建立 Owner review、publication version、timestamp、unpublish／rollback。
3. 先把研究內容與正式財務事實分開投影，再進行來源 rights review。
4. 建立可指定 viewport 的 Browser lane，完成 1440×900、768×1024、390×844、360×800 三家公司截圖驗收。
5. 另開工單處理 1314 8,426,000 元差異與未完成 EPS periods。

## 不應在下一步自動執行

- 不直接推送或合併目前 detached dirty worktree。
- 不執行 Migration 或 Production DB write。
- 不發布研究包。
- 不接受題材建議或修改 132 題材唯一權威。
- 不把 Fixture 複製進正式資料庫冒充 Writer 已核准內容。

