# TASK-REPO-002 — Frontend 13-Failure Classification & Release Gate Report

Date: 2026-08-12
Repository: `topicpilot-platform`
Branch: `main`
HEAD: `e333ed3`

## Executive summary

TASK-REPO-001 left the frontend at `59 passed / 13 failed`. The failures were
not fixed by reverting the V2 product surface or by skipping assertions. The
current V2 route/component architecture and the approved frontend specification
were used as the authority; the stale source-shape expectations were migrated
to test the current behavior. No frontend production source, backend contract,
Opportunity policy, Lifecycle algorithm, daily-market logic, or deployment
configuration was changed.

Final frontend result: **72 passed / 0 failed**. Production build, TypeScript,
lint, focused backend contract tests, and `git diff --check` also pass.

## Authority used

Classification followed this priority:

1. PM-frozen V2 frontend specification and current product decisions.
2. Approved frontend work-order/report evidence.
3. Current V2 route/component implementation.
4. Historical test expectations.

Key evidence:

- `apps/web/app/page.tsx` delegates `/` to `components/v2/V2Page.tsx`.
- `V2Page` owns the V2 Home and shared foundation routing.
- `TodayMarketPage` owns the frozen Home summary, mainline, event, rotation,
  and research-entry teaser surfaces.
- `TopicListPage` owns the formal/Preview Topic Overview and Lifecycle display.
- `StockExplorerPage` owns the formal stock-universe explorer and drawer path.
- `TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` Sections 22, 23, 26.9, and 26.10
  define the frozen Home/Topic/Stock boundaries and the shadow Opportunity
  presentation boundary.
- `TASK-FE-002C_HOME_FINAL_FREEZE_REPORT.md` records Home as frozen.
- `TASK-FE-005_TOPIC_OVERVIEW_UI_REFINEMENT_V3_REPORT.md` records the accepted
  Topic Overview/Lifecycle implementation.
- `TASK-FE-BE-015_STOCK_UNIVERSE_FULL_IMPORT_AND_STOCKS_FORMAL_INTEGRATION.md`
  records the formal Stock Explorer path.

## FRONTEND_FAILURE_MATRIX

| ID | Original failing test | Actual cause | Affected surface | Classification | Evidence-based action |
|---|---|---|---|---|---|
| F01 | one SnapshotProvider owns all live data refreshes | Test read legacy `page.tsx` and expected `useHomeData`; V2 Home is owned by `V2Page`/`TodayMarketPage` and uses `useSnapshot` | V2 route/data ownership | TEST_MIGRATION_DEBT | Rewrote test to verify shared provider and explicit V2 surface owners |
| F02 | strategy drilldown stays on home while the stock universe remains scan-only | Expected a legacy Home strategy drilldown that is not part of the frozen V2 Home | Home / Stock | OBSOLETE_EXPECTATION | Replaced with V2 research-entry and scan-only boundary assertions |
| F03 | new backend quote contract is adapted without parsing rule text | Expected Topic page to consume the old snapshot bundle; V2 Topic uses formal `fetchTopics`, while Stock uses `fetchFormalStocks` | Topic / Stock adapters | TEST_MIGRATION_DEBT | Rewrote around formal V2 adapters and unavailable/Preview states |
| F04 | home consumes backend market decision in one focused market judgement | Expected a later legacy `marketDecision` UI; frozen V2 Home uses market indices/breadth candidates and fixed presentation | Home | OBSOLETE_EXPECTATION | Rewrote around `TodayMarketPage` hierarchy and explicit backend candidate usage |
| F05 | home displays four canonical health metrics without recomputing values | Health-metric contract belongs to the superseded Home implementation; frozen V2 Home uses the approved two-row market summary | Home | OBSOLETE_EXPECTATION | Rewrote around `mockMarketMetrics`, live index/breadth replacement, and no browser arithmetic |
| F06 | home shows backend-limited strongest, warming, and cooling topics | Frozen Home explicitly keeps rotation/mock/deferred surfaces until an authoritative API exists; current component uses bounded presentation fixtures | Home rotation | OBSOLETE_EXPECTATION | Rewrote around bounded rotation arrays and existing Topic/Opportunity links |
| F07 | home copy has plain-language missing and freshness states | Test read the legacy entrypoint and old copy; V2 Home uses `isSyntheticPreview`, `canUseBackendData`, and `freshnessLabel` | Home freshness | TEST_MIGRATION_DEBT | Rewrote around current Preview/live/snapshot/unavailable semantics |
| F08 | strategy candidate drilldown uses only canonical registry, candidates, and performance | Strategy candidate drilldown is not a V2 Home surface; Stock Explorer owns scan/filter behavior | Home / Stock | OBSOLETE_EXPECTATION | Replaced with explicit absence of candidate inference and formal Stock Explorer ownership |
| F09 | strategy logic copy is fixed by strategyId and never inferred from candidates | Same superseded strategy-copy contract; frozen V2 Home presents topic mainlines and research teaser, not strategy prose | Home | OBSOLETE_EXPECTATION | Replaced with fixed mainline/Opportunity boundary assertions |
| F10 | renders all primary workspace routes | Render assertions expected stale mojibake copy rather than stable route/component markers | Route smoke | TEST_MIGRATION_DEBT | Rewrote route test to assert rendered route status and stable classes/markers |
| F11 | home source contains focused market workflow and safety language | Test inspected legacy `app/page.tsx`; V2 safety boundary lives in `TodayMarketPage` and the shared data state | Home | TEST_MIGRATION_DEBT | Rewrote to inspect current V2 source and prohibited recommendation language |
| F12 | home has focused guidance and guided unavailable states | Expected old `<b>` guidance copy and legacy source shape; V2 Home uses explicit freshness/data-state semantics in the frozen summary card | Home UX states | OBSOLETE_EXPECTATION | Rewrote around current V2 freshness and no-recommendation contract |
| F13 | topic empty state explains purpose and provides recovery routes | Expected legacy manual snapshot refresh; V2 Topic Overview uses formal API resource states, Preview disclosure, and explicit unavailable EmptyState | Topic Overview | TEST_MIGRATION_DEBT | Rewrote around `fetchTopics`, unavailable state, Preview disclosure, and API origin |

Classification totals:

```text
TEST_MIGRATION_DEBT = 6
OBSOLETE_EXPECTATION = 7
REAL_REGRESSION = 0
PM_DECISION_REQUIRED = 0
```

No evidence required a source fix. No failure was hidden with `skip`, `todo`,
commented assertions, or test deletion.

## Test/source changes

Updated only the four frontend test files below:

- `apps/web/tests/data-refresh.test.mjs`
- `apps/web/tests/home-market-summary.test.mjs`
- `apps/web/tests/rendered-html.test.mjs`
- `apps/web/tests/ux-guidance-empty-state.test.mjs`

The tests now cover current V2 route ownership, shared SnapshotProvider
behavior, frozen Home composition, formal Topic/Stock adapter boundaries,
unavailable/Preview semantics, retained route smoke, and the no-recommendation
Opportunity boundary.

No application source files were changed for TASK-REPO-002.

## Opportunity and Lifecycle boundary verification

- Opportunity frontend: PASS. The Home surface remains a research-entry teaser;
  no Buy/Sell/Strong Buy/target/stop-loss or client-side ranking inference was
  introduced. Existing shadow adapter tests remain green.
- Lifecycle frontend: PASS. `TopicListPage` consumes formal Lifecycle only when
  `SHADOW_AVAILABLE`, uses Preview only in the labelled Preview path, and does
  not derive lifecycle state in the browser. Existing lifecycle integration
  tests remain green.
- Backend contract regression: PASS — 34 focused tests passed across
  preflight, no-trade, Opportunity shadow read API, and Lifecycle contracts.

## Validation

| Check | Result |
|---|---|
| Initial frontend suite | 59 passed / 13 failed |
| Final frontend suite | **72 passed / 0 failed** |
| Production build (`npm test` build phase) | PASS |
| TypeScript (`npx tsc --noEmit`) | PASS |
| ESLint (`npm run lint`) | PASS; one existing unused-variable warning in `TopicDetailPage.tsx` |
| Focused backend contract suite | 34 passed |
| `git diff --check` | PASS |

The one ESLint warning is non-blocking and pre-existing in the application
source; this task did not change that source file.

## Gates and prohibited actions

```text
TASK_REPO_002 = COMPLETE
FAILURES_CLASSIFIED = 13 / 13
TEST_MIGRATION_DEBT = 6
OBSOLETE_EXPECTATION = 7
REAL_REGRESSION = 0
PM_DECISION_REQUIRED = 0
TESTS_UPDATED = YES
SOURCE_FIXES_REQUIRED = NO
SOURCE_FIXES_COMPLETED = N/A
V2PAGE_ARCHITECTURE = VERIFIED
OPPORTUNITY_FRONTEND = PASS
LIFECYCLE_FRONTEND = PASS
FINAL_FRONTEND_TESTS = 72 PASSED / 0 FAILED
FRONTEND_BUILD = PASS
TYPECHECK = PASS
LINT = PASS (one existing warning)
BACKEND_CONTRACT_REGRESSION = PASS
GIT_DIFF_CHECK = PASS
FRONTEND_RELEASE_GATE = READY
LIFECYCLE_RELEASE = READY
DAILY_MARKET_RELEASE = UNCHANGED_READY
OPS_P3A_RELEASE = UNCHANGED_READY
OPPORTUNITY_RELEASE = UNCHANGED_READY
DATA_GOVERNANCE_GATE = UNCHANGED_REVIEW_REQUIRED
GIT_ADD_PERFORMED = NO
GIT_COMMIT_PERFORMED = NO
GIT_PUSH_PERFORMED = NO
PRODUCTION_DEPLOYMENT = NO
PRODUCTION_CANARY = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
```

The frontend release gate is ready for selective staging of the reviewed test
migration and existing V2 implementation groups. The repository-wide data
governance review from TASK-REPO-001 remains unchanged and still governs the
research CSV/JSON hold group.
