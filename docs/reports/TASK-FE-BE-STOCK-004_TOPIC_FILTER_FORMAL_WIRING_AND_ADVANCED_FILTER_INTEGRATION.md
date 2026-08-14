# TASK-FE-BE-STOCK-004｜Topic Filter Formal Wiring & Advanced Filter Integration

Date: 2026-08-14
Task status: `READY_FOR_STOCK_004_INTEGRATION_REVIEW`

## Authority and continuation boundary

```text
TASK_FE_BE_STOCK_004 = TASK-FE-BE-STOCK-004
STOCK_003_BASE_SHA = 3c8d10024f8172168f822cacf6b924b393bcfe1a
STOCK_003_CONTINUATION_BASE = 2069ccc43bccaf079009fd30eef0049f72430c4d
STARTING_ORIGIN_MAIN_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
CURRENT_ORIGIN_MAIN_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
BRANCH = codex/task-fe-be-stock-004-20260814
MAIN_DRIFT = YES; origin/main advanced 15 commits beyond Stock-003's 71ba1ac authority
MAIN_RECONCILIATION = NO
```

Stock-004 was created as a continuation worktree from the verified Stock-003
implementation/report state. The newer `origin/main` commits were not merged
or rebased into this branch. The drift is reference/Today/mainline activity;
no Stock-003 implementation was re-created from current main.

## Contract audit result

The repository already has the required formal contracts:

```text
STOCK_TOPIC_QUERY_PARAMETER = topic
STOCK_TOPIC_QUERY_IDENTITY = canonical topic slug
TOPIC_OPTIONS_SOURCE = GET /api/v2/topics?limit=200&offset=0 via fetchTopics()
TOPIC_OPTIONS_BACKEND_OWNED = YES
TOPIC_FILTER_DATABASE_OWNED = NO; existing formal read_stocks applies the
  topic-slug relation predicate in the backend service layer after the SQL
  stock universe read; no browser membership filtering is used
BACKEND_CONTRACT_CHANGED = NO
OPENAPI_SEMANTICS_CHANGED = NO
GENERATED_TYPES_USED = YES; existing Stock query remains generated OpenAPI typed
```

The formal stock route documents `topic` as a topic slug. The formal topic
catalog returns the canonical `slug` and display `name`. Before this task,
Stock Explorer rebuilt its topic options from the currently loaded stock
relations. That made the options dependent on the current result set and did
not make the formal topic catalog the authority. The task therefore required
frontend wiring, not a new backend contract.

## Implementation

```text
TOPIC_FILTER_UI_ADDED = NO; existing advanced single-select preserved and formally wired
HARDCODED_TOPIC_OPTIONS_ADDED = NO
SEARCH_TOPIC_COMPOSITION = PASS
MARKET_TOPIC_COMPOSITION = PASS
UPDATE_MODE_TOPIC_COMPOSITION = PASS
SORT_TOPIC_COMPOSITION = PASS
FILTER_CHANGE_PAGINATION_SAFE = YES; formalQuery always resets offset to 0
```

Stock Explorer now loads topic options through the existing `fetchTopics()`
resource. In formal mode this is the formal `/api/v2/topics` route. In the
existing explicit Preview authority it may use the existing synthetic topic
resource. When the topic resource is loading or unavailable, the topic select
is disabled and does not fabricate options.

The selected option value is the backend canonical slug. Clearing the select
sends `topic=undefined`, restoring the unfiltered formal stock query. The
existing Stock-003 search, market, update-mode, and sort values remain in the
same generated query composition, so topic changes reload from offset zero and
preserve backend ordering.

## Browser and presentation boundaries

```text
BROWSER_TOPIC_FILTERING = NO
BROWSER_TOPIC_MEMBERSHIP = NO
BROWSER_SEARCH_FILTERING = NO
BROWSER_SORTING = NO
BACKEND_ORDER_PRESERVED = YES
FORMAL_PREVIEW_BOUNDARY_PRESERVED = YES
API_ERROR_FALLBACK_TO_PREVIEW = NO
DRAWER_UX_REGRESSION = PASS
STOCK_003_SEARCH_REGRESSION = PASS
```

The browser no longer derives the topic option list from stock relation rows.
It still renders backend-provided topic relations for presentation and does
not infer membership, scoring, ranking, recommendation, or main-topic
authority. The disabled technical, chip, and strategy controls remain
unchanged. The right-side sticky/full-height push Drawer, header offset,
scroll behavior, and close animation were not redesigned.

If the formal Stock API fails, stock rows remain unavailable and do not fall
back to Preview. If the formal topic catalog fails, only the topic control is
disabled with unavailable semantics; no mock formal options are inserted.

## Validation

```text
FOCUSED_STOCK_TESTS = PASS 26/26
FRONTEND_FULL_TESTS = PASS 109/109, including build
API_CLIENT_TESTS = PASS 3/3
BACKEND_TESTS = NOT_REQUIRED; Case A, no backend/OpenAPI change
TYPESCRIPT = PASS
LINT = PASS; one pre-existing TopicDetailPage.tsx unused-variable warning
BUILD = PASS
OPENAPI_GATE = NOT_REQUIRED; existing generated contract unchanged
GENERATED_CLIENT_IDEMPOTENCE = PASS via packages/api-client npm run check
DIFF_CHECK = PASS
SECRET_SCAN = PASS
```

The full frontend suite includes the Stock-003 search regression, topic query
composition, formal topic catalog sourcing, unavailable/disabled behavior,
backend-order preservation, and Drawer regression assertions. No PostgreSQL or
Production gate was required because this is a frontend-only Case-A change.

## Files modified

```text
apps/web/app/components/v2/StockExplorerPage.tsx
apps/web/tests/stock-explorer-query.test.mjs
docs/reports/TASK-FE-BE-STOCK-004_TOPIC_FILTER_FORMAL_WIRING_AND_ADVANCED_FILTER_INTEGRATION.md
docs/AI_WORKLOG.md (append-only)
```

## Protected boundaries and handoff

```text
DATA_REF_FILES_TOUCHED = NO
PROVIDER_AUTHORITY_CHANGED = NO
REFERENCE_SEMANTICS_CHANGED = NO
PRODUCTION_MUTATION = NO
G0 = NOT_RUN
G1 = NOT_RUN
G2 = NOT_RUN
G3 = NOT_RUN
CANARY = NOT_RUN
SCHEDULER_CHANGED = NO
TODAY_PAGE_TOUCHED = NO
TOPIC_DETAIL_PAGE_TOUCHED = NO
NEXT_TASK_MODIFIED = NO
STOCK_005_STARTED = NO

NEW_IMPLEMENTATION_COMMIT = b1d436b7a5e022d34f63d33be3b69882e3d9a081
DOCUMENTATION_COMMIT = 8974bf4df0545b031191538fd8489d13babd57bd
PUSH_MAIN = NO
MERGE_MAIN = NO
DEPLOY = NO
AI_WORKLOG_UPDATED = YES
AI_WORKLOG_APPEND_ONLY = YES
FINAL_STATUS = READY_FOR_STOCK_004_INTEGRATION_REVIEW
BLOCKER = NONE
```

Stop at this isolated continuation. After the mainline Production Post-Close
Canary is complete, reconcile Stock-003 and Stock-004 together against the
then-current main. Do not treat this branch as an official main integration or
production release, and do not start Stock-005.
