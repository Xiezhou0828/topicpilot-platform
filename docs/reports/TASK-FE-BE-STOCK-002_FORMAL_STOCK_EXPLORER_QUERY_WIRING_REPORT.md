# TASK-FE-BE-STOCK-002｜Formal Stock Explorer Query Wiring

Date: 2026-08-13
Branch: `codex/task-fe-be-stock-002-20260813`
Final status: `READY_FOR_STOCK_002_INTEGRATION_REVIEW`

## Authority and scope

`git fetch origin --prune` was run before implementation.

- `CURRENT_ORIGIN_MAIN_SHA`: `8a818935fe63eb3c3db9592c5068363c7ec941e9`
- `STARTING_BRANCH`: `codex/task-fe-be-stock-002-20260813`
- `STARTING_HEAD`: `8a818935fe63eb3c3db9592c5068363c7ec941e9`
- Stock-001 comparison base: `446e318a9b158958ff3c6972994f68b2f5ca898b`

Commits after the Stock-001 audit base were classified as Today Market (`19bab07`) and documentation reconciliation (`8a81893`). No Stock or API-contract change was found, so the task did not enter the STOP path. The implementation was performed in an isolated worktree; no shared dirty worktree was changed.

The requested `TOPICPILOT_CURRENT_HANDOFF.md` and `DOCUMENTATION_AUTHORITY_INDEX.md` are not present in the fetched repository. The available authority layers were checked instead: `PROJECT_CONTEXT.md`, `docs/AI_WORKLOG.md`, the V2 frontend design and production-data architecture documents, deployment authority, generated OpenAPI types, FastAPI route/schema/read-model code, frontend runtime code, and existing tests.

## Existing formal contract

Repository evidence confirms `GET /api/v2/stocks` at `services/api/src/topicpilot_api/production_read_model_api.py` accepts:

```text
market?: string
topic?: string       # formal topic slug
updateMode?: string  # INTRADAY | POST_CLOSE | UNKNOWN
sort?: string        # symbolAsc | changePctDesc | priceDesc | volumeDesc
limit?: number       # default 1000, max 1000
offset?: number      # default 0
```

There is no `page` or `cursor` parameter in the actual FastAPI route or generated OpenAPI operation. Backend-owned validation and filtering remain in `production_read_model.py`; no backend or OpenAPI change was required.

## Implemented wiring

`StockExplorerPage` now builds a generated-type-backed `StockListQuery` from local React state:

```text
market = all       → omitted
topic  = empty     → omitted; otherwise formal topicSlug
mode   = all       → omitted
mode   = live      → updateMode=INTRADAY
mode   = eod       → updateMode=POST_CLOSE
sort   = change    → changePctDesc
sort   = price     → priceDesc
sort   = volume    → volumeDesc
limit/offset       → 1000/0
```

`stock-api.ts` serializes that query to the existing `/api/v2/stocks` route and follows the existing `total`/`offset` pagination with the same backend filters and sort. Filter or sort changes reconstruct the query at offset zero. Refresh and the 60-second formal poll reuse the same query object. Formal rows render in the exact API response order; the prior `formalOrder` browser reorder and all formal `filteredRows` business predicates were removed.

No formal API origin produces explicit `synthetic-snapshot` Preview. A configured API failure produces `unavailable` and never switches to Preview. Nullable `price`, `changePct`, and `volume` continue to render as the existing unavailable marker and are not converted to zero or mock values.

The existing technical, chip, and strategy controls remain visible but disabled with an explicit “formal API not provided” boundary. Their former browser predicates were removed. Preview-only presentation ordering remains as the pre-existing Preview behavior; it is not used for formal results.

Topic relations continue to display `topicName`/role, and the first displayed topic remains presentation-only. No canonical main-topic authority was inferred or added.

The shared push Drawer was not redesigned. Its switch, reverse close animation, Escape path, sticky `top:72px`, full remaining viewport height, internal scroll, and responsive fallback were regression-checked.

## Required status fields

```text
TASK_FE_BE_STOCK_002 = COMPLETE
FORMAL_QUERY_PARAMS_CONFIRMED = YES
MARKET_FILTER_BACKEND_OWNED = YES
TOPIC_FILTER_BACKEND_OWNED = YES
UPDATE_MODE_FILTER_BACKEND_OWNED = YES
SORT_BACKEND_OWNED = YES
QUERY_STATE_LOCATION = LOCAL
FILTER_CHANGE_PAGINATION_SAFE = YES
REFRESH_PRESERVES_QUERY = YES
REFRESH_PRESERVES_BACKEND_ORDER = YES
FORMAL_MAPPING = configured origin + successful API response → FORMAL
PREVIEW_MAPPING = no formal origin → explicit synthetic-snapshot Preview
UNAVAILABLE_MAPPING = configured origin + API error → UNAVAILABLE
API_ERROR_FALLBACK_TO_PREVIEW = NO
NULLS_PRESERVED = YES
TOPIC_RELATION_DISPLAY = backend topicSlug/topicName/topicRole; first topic is presentation-only
MAIN_TOPIC_AUTHORITY_ADDED = NO
DRAWER_UX_REGRESSION = PASS
BUSINESS_FILTERING_IN_BROWSER = NO
BUSINESS_SORTING_IN_BROWSER = NO (formal path; Preview ordering is presentation-only)
TECHNICAL_SCORING_IN_BROWSER = NO
PROVIDER_RECONCILIATION_IN_BROWSER = NO
UNSUPPORTED_ADVANCED_CONTROLS = technical, chip, strategy; disabled/unavailable
BACKEND_CONTRACT_CHANGED = NO
BACKEND_CONTRACT_GAP = NONE
OPENAPI_SEMANTICS_CHANGED = NO
GENERATED_TYPES_USED = YES
```

## Validation

- Focused Stock Explorer query tests: `PASS` — 21/21
- Frontend full test/build command: `PASS` — 99/99 tests; production build passed
- API client tests: `PASS` — 3/3
- TypeScript: `PASS`
- Targeted ESLint: `PASS`
- Full ESLint: `PASS` with one pre-existing warning in `TopicDetailPage.tsx`; no errors
- OpenAPI gate: `PASS`
- OpenAPI idempotence/generated-client check: `PASS`
- `git diff --check`: `PASS`
- Secret-pattern scan: `PASS` — no matches

## Files and boundaries

Changed implementation/test files:

- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/app/lib/stock-api.ts`
- `apps/web/tests/stock-explorer-query.test.mjs`
- `docs/AI_WORKLOG.md` — append-only task record
- this report

```text
DATA_REF_FILES_TOUCHED = NO
TODAY_FILES_TOUCHED = NO
PROVIDER_AUTHORITY_CHANGED = NO
LIFECYCLE_RULES_CHANGED = NO
OPPORTUNITY_RULES_CHANGED = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
PRODUCTION_MUTATION = NO
G1 = NOT_RUN
G2 = NOT_RUN
G3 = NOT_RUN
CANARY = NOT_RUN
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
```

The resulting scoped commit is intentionally left isolated for integration review. STOCK-003 search, history, lineage, and further detail-contract work remain roadmap items and were not started.
