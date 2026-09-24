# Today owner-desired composition validation

## Browser validation A-K

| Check | Result | Evidence |
|---|---|---|
| A. `/` route | PASS | Local Vite/Vinext browser DOM rendered the Today route. |
| B. Reading order | PASS | DOM order is `市場概況` → `今日市場重點` → `今日主線`. |
| C. Market Overview | PASS / fail-closed | Section renders the official market summary surface; local run without API origin showed explicit `讀取中`/`尚未提供`, not invented values. |
| D. Official index and turnover fields | PASS by contract | `OfficialMarketFields` reads `marketIndices(overview)` and `marketTurnover(overview)`; production API readback confirmed both fields exist. |
| E. Breadth/distribution | PASS by contract | `BreadthAndDistribution` reads backend market health/distribution and explicitly excludes unavailable observations. |
| F. Today Focus | PASS | `今日市場重點` is backend-owned and disclosure metadata is secondary. |
| G. Mainline count | PASS | Production API readback returned 3 `mainTopics`; UI maps the backend array without browser ranking. |
| H. Grade and navigation | PASS | Conditional `GradeChip` plus `/topics/{slug}` links are present in the mainline card source. |
| I. Compact composition | PASS | Three core sections use compact section/card styles; no ordinal labels or redundant `盤中快照` render. |
| J. Fail-closed behavior | PASS | Local browser showed explicit loading/unavailable state with no fallback/mock values. |
| K. Topic/Stock/Favorites non-regression | PASS | Clean local browser tabs rendered `/topics`, `/topics/solar`, `/favorites`, and `/stocks` with no console errors. |

The local browser run intentionally used the no-origin mode to verify the safety boundary. A direct read-only request to the current API returned `mainTopics=3`, `hasIndices=true`, `hasTurnover=true`, `hasBreadth=true`, and `dataDate=2026-09-24`. The formal API payload therefore supports the live-data branch; the browser no-origin branch proves that missing runtime configuration remains explicit rather than synthetic.

## Automated validation

```text
WEB_TESTS=167 passed / 0 failed / 0 skipped
NEW_FAILURE_COUNT=0
TYPESCRIPT=PASS (tsc --noEmit)
WEB_BUILD=PASS
WEB_LINT=PASS (0 errors; 1 pre-existing FavoriteButton Hook warning)
```

The full web test command includes a production build before the 167-test run. The independent build was also run separately. Dependency installation was local to the E: task worktree; npm reported existing dependency advisories and no audit remediation was performed.

## Gate

```text
TODAY_OWNER_PRODUCT_MATCH_GATE=PASS
```

The candidate is safe for review and handoff. Production deployment remains out of scope for this task.
