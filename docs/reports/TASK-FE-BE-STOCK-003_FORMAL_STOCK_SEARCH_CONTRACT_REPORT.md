# TASK-FE-BE-STOCK-003｜Stock Search Formal Contract & FastAPI Integration

Date: 2026-08-13
Task status: `READY_FOR_STOCK_003_INTEGRATION_REVIEW`

## Authority and repository reality

```text
STARTING_ORIGIN_MAIN_SHA = 71ba1ac27f2f72378df3df9266271de4f05f27d1
BRANCH = codex/task-fe-be-stock-003-20260813
APPLICATION_COMMIT = 3c8d10024f8172168f822cacf6b924b393bcfe1a
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
```

The task started from a fresh `git fetch origin --prune` and an isolated
worktree based on `origin/main`. While the worktree was being prepared,
`origin/main` advanced from the earlier Stock-002B tip through DATA-REF-005F
documentation commits to `71ba1ac`. The latest concurrent commit was
`docs: record blocked reference bootstrap`; it touched DATA-REF documentation
and `docs/AI_WORKLOG.md` only. No Stock or Today application change was
reconciled into this task. The Stock-003 branch was rebased onto `71ba1ac`
before the final validation run.

The attachment requested `docs/TOPICPILOT_CURRENT_HANDOFF.md`,
`docs/DOCUMENTATION_AUTHORITY_INDEX.md`, and `docs/PROJECT_CONTEXT.md`, but
those exact paths do not exist in this checkout. Per repository evidence, the
available authority files read for this task were root `PROJECT_CONTEXT.md`,
`docs/architecture/README.md`, `docs/architecture/system-overview.md`,
`docs/architecture/ADR-002-openapi-generated-client.md`,
`docs/architecture/10_DEPLOYMENT.md`, and `docs/operations/deployment.md`,
plus the existing Stock-002/002B and Stock UI reports.

## Current formal search contract

The pre-task `/api/v2/stocks` contract had `market`, `topic`, `updateMode`,
`sort`, `limit`, and `offset`, but no search parameter. This was therefore
Case B: a narrowly scoped backend/OpenAPI contract addition was required.

```text
SEARCH_PARAMETER = search
SEARCH_FIELDS = code, name
CODE_SEARCH_MODE = case-insensitive substring (exact and prefix included)
NAME_SEARCH_MODE = case-insensitive substring
CASE_SEMANTICS = case-insensitive
WHITESPACE_NORMALIZATION = trim at frontend debounce and adapter/backend boundary
BACKEND_SEARCH_OWNED = YES
DATABASE_SEARCH_FILTERING = YES
BUSINESS_SEARCH_IN_BROWSER = NO
```

The backend applies the search predicate in the formal stock SQL universe using
database-side `POSITION(LOWER(...))` over instrument code and nullable name.
No topic, industry, technical, institution, narrative, synonym, phonetic, AI
semantic, or relevance-ranking search was added.

## Query composition and state semantics

```text
SEARCH_REQUEST_MODE = DEBOUNCED_250MS
STALE_SEARCH_RESULT_PROTECTED = YES (AbortController + request identity guard)
SEARCH_CHANGE_PAGINATION_SAFE = YES (formal offset remains 0)
REFRESH_PRESERVES_SEARCH = YES
BACKEND_ORDER_PRESERVED = YES
SEARCH_MARKET_COMPOSITION = YES
SEARCH_TOPIC_COMPOSITION = YES
SEARCH_UPDATE_MODE_COMPOSITION = YES
SEARCH_SORT_COMPOSITION = YES
```

The Stock Explorer owns only input state and transport normalization. It sends
the trimmed `search` value through the generated OpenAPI-backed adapter. Every
search/filter change rebuilds the formal query with `offset=0`; refresh reuses
the same query object. Formal rows are rendered in backend order and are not
browser-filtered or browser-sorted.

## Result, error, and boundary semantics

```text
VALID_EMPTY_RESULT = formal API response with source=api, data=[], total=0
API_ERROR_STATE = source=unavailable, data=null, diagnostic error
API_ERROR_FALLBACK_TO_PREVIEW = NO
FORMAL_PREVIEW_BOUNDARY_PRESERVED = YES
NULLS_PRESERVED = YES
MAIN_TOPIC_AUTHORITY_ADDED = NO
UNSUPPORTED_ADVANCED_CONTROLS_DISABLED = YES
DRAWER_UX_REGRESSION = PASS
```

Preview remains explicit only when no formal FastAPI origin is configured.
Configured formal API failure does not silently display Preview rows. Existing
sticky/full-height push Drawer behavior and close animation were not changed.

## Backend, OpenAPI, and generated client changes

```text
BACKEND_CONTRACT_CHANGED = YES (search query parameter only)
OPENAPI_SEMANTICS_CHANGED = YES (documented code/name search parameter)
GENERATED_TYPES_USED = YES
```

Changed backend files add the `search` FastAPI query parameter, normalization,
SQL predicate, and response query echo. `packages/api-client/openapi.json`,
`packages/api-client/src/schema.d.ts`, and
`apps/web/app/lib/generated-api.d.ts` were regenerated from the live FastAPI
application; no generated file was edited manually.

## Validation

```text
FOCUSED_STOCK_TESTS = PASS 24/24
FOCUSED_BACKEND_SEARCH_TESTS = PASS 3/3
FRONTEND_FULL_TESTS_AND_BUILD = PASS 107/107
API_CLIENT_TESTS = PASS 3/3
BACKEND_RELEASE_TESTS = PASS 313 passed, 42 skipped, 59 deselected
POSTGRESQL_TESTS = LOCAL_SKIPPED where TEST_DATABASE_URL/DATABASE_URL was absent
TYPESCRIPT = PASS
TARGETED_LINT = PASS
FULL_LINT = PASS (one pre-existing TopicDetailPage.tsx unused-variable warning)
BUILD = PASS
RUFF = PASS
OPENAPI_GATE = PASS
OPENAPI_IDEMPOTENCE = PASS after generated files were committed
DIFF_CHECK = PASS
SECRET_SCAN = PASS
```

The skipped PostgreSQL cases were environment-gated integration tests; no
database was connected or mutated by this task. The full backend release suite
passed all runnable non-research/non-governance tests.

## Files changed

```text
apps/web/app/components/v2/StockExplorerPage.tsx
apps/web/app/globals.css
apps/web/app/lib/generated-api.d.ts
apps/web/app/lib/stock-api.ts
apps/web/tests/stock-explorer-query.test.mjs
packages/api-client/openapi.json
packages/api-client/src/schema.d.ts
services/api/src/topicpilot_api/production_read_model.py
services/api/src/topicpilot_api/production_read_model_api.py
services/api/tests/test_production_read_model_search.py
docs/reports/TASK-FE-BE-STOCK-003_FORMAL_STOCK_SEARCH_CONTRACT_REPORT.md
docs/AI_WORKLOG.md (append-only)
```

## Boundaries and handoff

```text
DATA_REF_FILES_TOUCHED = NO
PROVIDER_AUTHORITY_CHANGED = NO
REFERENCE_SEMANTICS_CHANGED = NO
PRODUCTION_MUTATION = NO
DEPLOY = NO
G1 = NOT_RUN
G2 = NOT_RUN
G3 = NOT_RUN
CANARY = NOT_RUN
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
STOCK_004_STARTED = NO
FINAL_STATUS = READY_FOR_STOCK_003_INTEGRATION_REVIEW
```

The scoped implementation commit is local only. Stop here for separately
authorized Stock-003 integration review; do not treat this worktree commit as
an official `main` integration or production release.
