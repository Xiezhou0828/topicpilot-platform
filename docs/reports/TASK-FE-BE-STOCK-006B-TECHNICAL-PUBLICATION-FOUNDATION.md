# TASK-FE-BE-STOCK-006B Technical Publication Foundation

**Date:** `2026-08-16`
**Scope:** Stock technical input/provenance and fail-closed publication foundation only

## Closure fields

```text
TASK_ID=TASK-FE-BE-STOCK-006B-TECHNICAL-PUBLICATION-FOUNDATION
FINAL_STATUS=FOUNDATION_IMPLEMENTED_AND_VALIDATED
CANONICAL_BASE_SHA=c40a1d4e0337d9c56cf805cbd708eba216b41ab0
SOURCE_IMPLEMENTATION_COMMIT_SHA=6f27c5f
SOURCE_BRANCH=codex/task-stock-technical-publication-20260816
SOURCE_WORKTREE=C:\\ws2-stock-tech-20260816
SOURCE_WORKTREE_CLEAN_AT_IMPLEMENTATION_COMMIT=YES
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_POST_SHA=193a9c5
CANONICAL_RUNTIME_VALIDATION_SHA=f8c26ca
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
PROMOTION_MODE=COMMIT_PRESERVING_CHERRY_PICK
SOURCE_TO_CANONICAL_COMMIT_MAP=6f27c5f->2ef975d;823e736->193a9c5
OWNER_DIRTY_UNTRACKED_STATE_PRESERVED=YES
TASK_OWNED_RESIDUAL_DIFF=NO
DATABASE_MUTATION=NO
HISTORICAL_DATA_MUTATION=NO
PROVIDER_CALLS=NO
SCHEDULER=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
```

The source commit is the exact implementation provenance for the accepted
WS2 code and generated contract artifacts. This report is a follow-on evidence
commit and does not change the implementation boundary.

## Decision

The canonical V2 historical read model is now exposed through an additive
read-only technical publication status route:

```text
GET /api/v2/stocks/{symbol}/technical?from=YYYY-MM-DD&to=YYYY-MM-DD&market=TPE&limit=200
```

The route consumes `read_historical_bars` and publishes only:

- the immutable foundation contract version;
- raw observed input state and backend-only calculation ownership;
- source, adapter, normalization, mapping, reference, quality, adjustment,
  as-of, and returned-window provenance; and
- explicit deferred/unavailable reasons.

No technical indicator values are published. The current canonical history
remains `RAW_OBSERVED_DAILY_BAR` with `adjustmentState=UNKNOWN`; it is not
treated as adjusted truth or as a continuity-safe series. MA, momentum,
returns, breakout/resistance, ATR/volatility, volume continuity indicators,
advanced technicals, event markers, and corporate-action markers remain
deferred or unavailable.

## Exact implementation write set

| File | Change | Owning boundary |
|---|---|---|
| `services/api/src/topicpilot_api/technical_publication.py` | New fail-closed technical input/provenance builder; no indicator calculation | Backend technical publication foundation |
| `services/api/src/topicpilot_api/schemas.py` | New `StockTechnicalInputProvenance` and `StockTechnicalPublicationRead` response models | FastAPI/OpenAPI contract |
| `services/api/src/topicpilot_api/production_read_model_api.py` | Add read-only bounded `/technical` route over shared historical authority | V2 production read model API |
| `services/api/tests/test_technical_publication.py` | Five focused policy/API/OpenAPI tests | Technical foundation validation |
| `packages/api-client/openapi.json` | Regenerated OpenAPI contract | Generated API authority |
| `packages/api-client/src/schema.d.ts` | Regenerated TypeScript schema | Generated API authority |
| `apps/web/app/lib/generated-api.d.ts` | Synchronized generated web declaration | Frontend wire contract; no UI behavior change |
| `docs/architecture/STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md` | Foundation contract and explicit non-scope | Stock technical architecture contract |
| `docs/reports/TASK-FE-BE-STOCK-006B-TECHNICAL-PUBLICATION-FOUNDATION.md` | This evidence report | Task evidence only |

No existing History panel, Stock Drawer, EOD projection, `StockTechnicalEvidence`
tracking shape, Topic Score/Grade/Lifecycle, Opportunity, Recommendation,
Today, migration, scheduler, Production, or `NEXT_TASK` file was modified.

## Collision and provenance boundary

The implementation starts from committed `c40a1d4`, which is the proven SHA
recorded by the current cold-start handoff. The canonical checkout itself had
owner modified/untracked state and was not used as a dirty source. Existing
Stock-002/002b/003/004 worktrees were retained and treated as read-only
collision evidence. The WS2 worktree was clean at the implementation commit.

The technical route shares the already canonicalized historical reader rather
than querying the retained legacy OHLCV relation, calling a provider, or
creating a second persistence family. The browser receives generated types
only; it does not request raw bars and derive technical semantics locally.

## Validation

### Backend and contract validation

```text
FOCUSED_TESTS=9 passed, 0 failed, 1 warning
BACKEND_TEST_COUNT_PRE=460 passed, 41 skipped
BACKEND_TEST_COUNT_POST=465 passed, 41 skipped
BACKEND_TEST_COUNT_DELTA=+5 passed
BACKEND_TEST_COUNT_DELTA_REASON=5 new tests in test_technical_publication.py; no existing test removal or discovery reduction
BACKEND_FAILED=0
BACKEND_XFAILED=0
BACKEND_DESELECTED=0
```

The pre-count was executed from a clean detached c40a1d4 baseline worktree;
the post-count was executed from WS2. The 41 skipped tests are explicit
PostgreSQL or ingestion-database gates and were not promoted to PASS.

After promotion, the canonical branch was rechecked at `f8c26ca`: focused
technical/history tests remained `9 passed`, Ruff and OpenAPI baseline checks
remained PASS, and the canonical backend suite reported `474 passed, 41
skipped, 1 warning`. The higher canonical total includes the committed
parallel WS1 state already present on the canonical branch; no task-owned test
was removed or deselected.

```text
RUFF=PASS
PYTHON_COMPILE=PASS
OPENAPI_VALIDATION=PASS
OPENAPI_BASELINE_SELF_CHECK=PASS
API_CLIENT_TESTS=3 passed, 0 failed
GENERATED_PACKAGE_WEB_SCHEMA_EQUALITY=PASS
GIT_DIFF_CHECK=PASS
SECRET_PATTERN_SCAN=PASS
```

### Frontend validation

```text
WEB_BUILD=PASS
WEB_TESTS=142 passed, 0 failed, 0 skipped
WEB_TEST_COUNT_DELTA=0
WEB_TEST_COUNT_DELTA_REASON=No frontend test files or runtime components changed; generated declaration synchronization only
WEB_LINT=0 errors, 1 pre-existing warning in FavoriteButton.tsx
```

### Dependency and source-state validation

```text
PYTHON_DEPENDENCY_STATE=PASS (fresh Python 3.12 venv; editable install from services/api[dev] declared constraints)
API_CLIENT_DEPENDENCY_STATE=PASS (npm ci from packages/api-client/package-lock.json)
WEB_DEPENDENCY_STATE=PASS (npm ci from apps/web/package-lock.json)
REPRODUCIBLE_DEPENDENCY_STATE=PASS_FOR_VALIDATION_SCOPE
CLEAN_SOURCE_STATE=PASS_AT_IMPLEMENTATION_COMMIT
```

The temporary validation environment was outside the repository and is not a
runtime or Production dependency. Production/database integration gates were
not rerun because this change does not reach provider, reference, market
semantics, post-close writer, persistence, migration, or live-runtime
boundaries. `G1`, `G2`, `G3`, and the Post-Close Canary remain preserved PASS
evidence, not new execution claims.

## Canonical promotion handoff

The source result was promoted into the current canonical branch with
commit-preserving cherry-pick after verifying that the accepted file mapping
had no collision with owner dirty/untracked state. Canonical promotion is
recorded as `2ef975d` plus this final report update commit; the canonical
working tree kept its existing owner changes intact. No push, deploy,
Production mutation, scheduler activation, or `NEXT_TASK` update occurred in
WS2.
