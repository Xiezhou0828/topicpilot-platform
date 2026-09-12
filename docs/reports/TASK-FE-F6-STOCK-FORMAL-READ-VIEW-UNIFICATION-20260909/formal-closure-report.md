# Frontend F6｜Stock Formal Read View Unification

```text
TASK=F6
ROADMAP=N7
EXACT_SHA_BEFORE=09bc660e6a660afff2ac86076a0e42c6ea8e01c1
EXACT_SHA_AFTER=reported in final handoff after commit (self-referential commit field)
COMMIT_SHA=reported in final handoff after commit (self-referential commit field)
COMMIT_MESSAGE=feat(stocks): unify formal read view

STOCK_FORMAL_READ_VIEW_UNIFIED=PASS
STOCK_DRAWER_STANDALONE_PARITY=PASS
MARKET_AWARE_IDENTITY=PASS
EOD_ASOF_PARITY=PASS
RAW_HISTORY_PARITY=PASS
LEGACY_FIRST_PAINT_NOT_FORMAL=PASS
NO_TRIGGER_RECOMPUTATION=PASS
TOPIC_RELATION_TRUTHFUL=PASS
MISSING_MAIN_TOPIC_NOT_GUESSED=PASS
ADJUSTMENT_STATUS_TRUTHFUL=PASS
DEEP_LINK_NAVIGATION=PASS

FOCUSED_STOCK_FRONTEND_TESTS=PASS (47 passed)
FRONTEND_TESTS=PASS (190 passed)
TEST_COUNT_PRE=182 passed (F4 closure baseline)
TEST_COUNT_POST=190 passed
TEST_COUNT_DELTA=+8
TEST_COUNT_DELTA_REASON=F6 added eight Stock formal-view contract/component integration tests
API_CLIENT_TESTS=PASS (4 passed)
BACKEND_STOCK_EOD_HISTORY_CONTRACT_TESTS=PASS (13 passed, 5 skipped PostgreSQL integration without TEST_DATABASE_URL/DATABASE_URL)
TSC_NO_EMIT=PASS
WEB_PRODUCTION_BUILD=PASS
GIT_DIFF_CHECK=PASS

SAFE_TO_PROCEED_WITH_F7=YES (within the separately accepted Technical provider/consumer contract)
SAFE_TO_PROCEED_WITH_F5_OR_F8=YES
PRODUCTION_MUTATION=NO
PUSH=NO
MERGE=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
CANONICAL_STATUS=CANONICALIZED_IN_REQUESTED_CHECKOUT
RELEASE_STATUS=NOT_RELEASED
PRODUCTION_VERIFICATION=NOT_RUN
```

## Result

`/stocks`, the shared Stock Drawer, and `/stocks/[code]` now converge on the
existing V2 Stock read model for identity, EOD, raw history, source, as-of,
freshness, topic relations, and publication/availability display. The standalone
route reuses the shared Drawer view and no longer reads the bundled snapshot,
evaluates triggers, or renders legacy chip, fundamental, and recommendation-like
fields.

The detail consumer resolves an exact `(market, instrument_code)` through the
formal Stock list contract. A code that exists in more than one market remains
unavailable until a market is supplied; the frontend does not choose the first
match. Historical responses are also checked against the requested market and
code before rendering.

Formal Drawer and standalone first paint starts in `LOADING` with an empty
formal shell. Values supplied by an Explorer tile, bundled snapshot, legacy
route, or earlier instrument are not displayed as formal while detail is loading
or after a failure. The bounded Stock surface distinguishes `LOADING`, `ERROR`,
`EMPTY`, `UNAVAILABLE`, `PUBLISHED`, `PARTIAL`, and explicit `PREVIEW` states.

The history table remains raw observed OHLCV. It displays adjustment state per
bar and keeps the series-level disclosure `UNKNOWN` when authority is absent or
mixed. It does not publish adjusted-history or total-return meaning. The
frontend performs no trigger, screening, EOD, historical, topic-role, technical,
Selector, Lifecycle, Opportunity, institutional, news, or fundamental
calculation.

Topic relations are rendered only from `topicRelations`. A missing relation
role is shown as unpublished, and `mainTopic` remains unavailable unless the
backend publishes that distinct field. The first relation is never promoted to
the main topic.

The Drawer deep link includes the market and opens in a new tab so the Explorer
filter and selection context remain intact. The standalone route uses browser
back navigation with `/stocks` as the direct-entry fallback.

## F6 write-set

- `apps/web/app/lib/stock-api.ts`
- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
- `apps/web/app/components/v2/StockPriceHistoryPanel.tsx`
- `apps/web/app/stocks/[code]/page.tsx`
- `apps/web/tests/stock-formal-view.test.mjs`
- `apps/web/tests/stock-eod-wiring.test.mjs`
- `apps/web/tests/stock-explorer-query.test.mjs`
- `apps/web/tests/rendered-html.test.mjs`
- `apps/web/tests/ux-guidance-empty-state.test.mjs`
- `docs/reports/TASK-FE-F6-STOCK-FORMAL-READ-VIEW-UNIFICATION-20260909/formal-closure-report.md`

## Validation boundary

The focused frontend suite executes the real typed Stock consumer and shared
React views with synthetic contract-shaped API responses. It covers TPE/TWO
identity, ambiguous codes, detail/history response mismatch, EOD and history
parity, loading/error/empty/unavailable/published rendering, legacy first-paint
suppression, missing main-topic authority, raw adjustment disclosure, and deep
link/back navigation.

The five skipped backend checks require an explicitly configured PostgreSQL test
database. Non-database Stock EOD/history/search contracts passed. No database,
runtime, provider, scheduler, or Production state was changed.

## Preserved pre-existing dirty work

All owner/parallel tracked and untracked changes present before F6 remain outside
the F6 commit. They include the existing Today/Topic changes, API client owner
hunks, deployment/runtime/A10/B2 changes, lifecycle files/tests, bounded EOD
tools, and the source-workspace hygiene report. F6 did not reset, clean, stash,
checkout, overwrite, stage, or commit those paths. The exact remaining paths are
reported in the final handoff from the post-commit `git status`.

F7, F5, and F8 were not started.
