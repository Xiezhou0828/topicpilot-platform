# TASK-FE-BE-STOCK-005B — Additive Stock EOD Read Implementation

Date: 2026-08-14
Task: TASK-FE-BE-STOCK-005B
Scope: additive backend/API read projection only; no Stock Explorer or Drawer UI wiring

## Executive result

The accepted TASK-FE-BE-STOCK-005A semantic contract is implemented as an
additive StockEodRead object on the existing Stock list and detail response
models. The implementation is read-only and set-based: it selects accepted,
non-superseded canonical DAILY_BAR observations, derives the market-local
trading date and nearest earlier priced trading-day close, and serializes the
approved EOD/null/status/lineage semantics through FastAPI, OpenAPI, and the
generated client.

No new EOD endpoint was created. Existing intraday top-level price behavior
is preserved. Existing top-level changePct is a nullable completed-session EOD
compatibility alias and is null for INTRADAY rows until a separate intraday
change contract exists. Frontend rendering remains the next slice,
TASK-FE-BE-STOCK-005C.

## CURRENT_CANONICAL_STATE

    TASK_ID=TASK-FE-BE-STOCK-005B
    TASK_NAME=Additive Stock EOD Read Implementation
    CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
    CURRENT_MAIN_SHA=26f635b95d8d88fd7ed7e43949583347f3ab5feb
    CANONICAL_START_SHA=017460da9d0a8fde2905e85f39e8670b5393b9c9
    CANONICAL_FINAL_SHA=14adf94 / canonical closure content before report metadata provenance commit
    CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
    ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
    DIRTY_STATE=YES / canonical worktree had pre-existing unrelated user changes
    WORKTREE_USED=C:\Users\acer\Documents\Codex\2026-08-14\stock-005-worktree
    WORKTREE_BRANCH=codex/task-fe-be-stock-005-20260814
    WORKTREE_REBASED=YES / final rebase onto canonical HEAD 017460d
    WORKTREE_RECONCILED=YES / exact 005B application write set and targeted owner docs
    WORKTREE_CLEANUP=Stock source worktree removed; task branch retained for predecessor 005A evidence

The fetched origin/main is recorded separately from the canonical checked-out
HEAD because the canonical branch contains local commits beyond its remote
tracking ref. The canonical repository was never staged, reset, overwritten,
merged, or otherwise modified.

## STOCK_PAGE_SECTIONS

The audited Stock surface includes:

1. Stock Explorer list/grid and pagination.
2. Formal code/name search with debounce and stale-request protection.
3. Market filtering (TPE/TWO), update-mode filtering, backend-owned sorting, and
   the advanced topic filter.
4. Latest price, change percentage, volume, freshness, and publication-state
   tile fields.
5. Topic relations and topic-role presentation.
6. Existing right-side full-height sticky/push detail Drawer with header offset,
   internal scrolling, tile switching, close/Escape, and reverse animation.
7. Drawer identity and basic stock data.
8. Technical/price detail placeholders and tracking evidence.
9. Topic/market narrative, institution-flow, Opportunity, and favorite
   sections where the current contract exposes explicit unavailable/temporary
   state.
10. Timeline/history and source/provider/as-of metadata paths that remain
    separate or only partially wired in the current UI.

The requested slide-in behavior, header-offset/full-height sticky Drawer, and
advanced topic filter were treated as preserved product requirements. They were
not reimplemented in this task.

## HARDCODED_OR_MOCK_SECTIONS

- The configured formal Stock path does not hardcode price, volume, change,
  topic membership, topic options, or backend ranking.
- The explicit no-API preview path uses the checked-in synthetic snapshot and
  labels itself Preview; it is not a formal EOD fallback.
- API errors become explicit unavailable state and do not silently fall back to
  Preview.
- Technical/chip/strategy controls and Drawer technical, flows, narrative, and
  Opportunity values remain disabled or null/unavailable where no formal
  contract is published. They are not promoted as factual mock data.
- The legacy V1 stock models remain repository evidence only; the formal Stock
  Explorer path uses V2 routes.

## EXISTING_ROUTES

| Route | Role after 005B |
| --- | --- |
| GET /api/v2/stocks | Existing formal list route; each item now has additive nullable eod. |
| GET /api/v2/stocks/{symbol} | Existing formal detail route; same additive EOD projection path and semantics. |
| GET /api/v2/topics | Existing topic option catalog used by advanced filtering; unchanged. |
| GET /api/v1/stocks/{code}/price-history | Existing historical contract; unchanged and not used as an EOD fallback. |

No /api/v2/stocks/{symbol}/eod route was created.

## IMPLEMENTATION

    STOCK_EOD_READ_IMPLEMENTED=YES
    STOCK_READ_MODEL_EOD_FIELD=eod: StockEodRead | null
    LIST_ROUTE_EOD=YES / GET /api/v2/stocks
    DETAIL_ROUTE_EOD=YES / GET /api/v2/stocks/{symbol}

    TRADING_DATE_IMPLEMENTED=YES / market timezone from markets.timezone; TPE/TWO Asia/Taipei/TW_MARKET authority preserved
    PREVIOUS_CLOSE_IMPLEMENTED=YES / nearest earlier priced accepted DAILY_BAR trading date
    CHANGE_IMPLEMENTED=YES / backend Decimal close - previousClose
    CHANGE_PCT_IMPLEMENTED=YES / backend Decimal percentage; null unless comparable and previousClose > 0
    ADJUSTMENT_POLICY_IMPLEMENTED=YES / ADJUSTED+ADJUSTED or UNADJUSTED+UNADJUSTED only; UNKNOWN fails closed
    NO_TRADE_IMPLEMENTED=YES / explicit NO_TRADE or EXCHANGE_CONFIRMED_NO_DATA
    SUSPENSION_IMPLEMENTED=YES / explicit SUSPENDED status
    MISSING_DATA_IMPLEMENTED=YES / missing row is not promoted to NO_TRADE; absent EOD remains null
    VOLUME_IMPLEMENTED=YES / same trading date, accepted DAILY_BAR, DAILY_TOTAL VOLUME
    TURNOVER_IMPLEMENTED=YES / canonical turnover_amount only; null when unavailable
    TURNOVER_DERIVED_FROM_PRICE_VOLUME=NO
    PRICE_LINEAGE_IMPLEMENTED=YES
    VOLUME_LINEAGE_IMPLEMENTED=YES
    DATA_STATUS_IMPLEMENTED=YES / AVAILABLE, PARTIAL, UNAVAILABLE, NO_TRADE, SUSPENDED, ADJUSTMENT_UNKNOWN, SOURCE_CONFLICT
    INTRADAY_BOUNDARY_IMPLEMENTED=YES / EOD is completed-session data; top-level intraday price remains separate
    TOP_LEVEL_CHANGE_PCT_COMPATIBILITY=YES / EOD alias for non-INTRADAY; null for INTRADAY
    SOURCE_FACT_ROUNDING=NO / direct source values are not rounded
    DERIVED_ROUNDING=ROUND_HALF_UP to four fractional places at API serialization boundary

The read path excludes rejected/quarantined observations by requiring accepted
canonical rows and excludes accepted superseded rows. Unresolved daily quality
or value conflicts fail closed as SOURCE_CONFLICT with derived values
suppressed. No provider arbitration, corporate-action inference, browser
calculation, zero fill, carry-forward, or price-times-volume turnover
derivation was added.

## DATA_REF_OR_GATE_DEPENDENCIES

- No DATA-REF, provider, reference bundle, migration, persistence writer,
  post-close writer, scheduler, or Production boundary changed.
- Existing G1/G2/G3 and Post-Close Canary evidence from the current DATA-REF
  handoff remains preserved and was not rerun because this slice only reads
  existing canonical observations.
- A future change to provider authority, reference/calendar semantics,
  canonical persistence, post-close publication, or adjustment governance must
  repeat impact assessment and the applicable protected gates.
- Technical Drawer fields remain dependent on Historical publication authority;
  this read projection does not make technical data formal.

## BROWSER_BUSINESS_LOGIC_RISKS

No browser business rule was added. The protected boundary is explicit:

- Browser code must not calculate change or change percentage.
- Browser code must not rank topics or stocks, reconcile providers, classify
  business states, infer no-trade, infer adjustment state, or derive turnover.
- Existing formatting remains presentation-only over backend fields.
- The intraday latest price and completed-session EOD object remain distinct;
  no frontend alias was introduced.

## MISSING_OR_PARTIAL_CONTRACTS

- Explorer/Drawer rendering of the new EOD object is not implemented; it is
  TASK-FE-BE-STOCK-005C.
- Canonical turnover remains unavailable for current upstream observations that
  do not publish turnover_amount; no substitute formula is authorized.
- Timeline/history integration, market/topic narrative, institution flows,
  Opportunity, and complete technical detail remain separate or unavailable
  contracts. Technical publication remains Historical-dependent.
- Preview remains an explicit non-formal mode and is not part of the EOD
  authority.

## PARALLEL_SAFE_SLICES

Safe to continue in an isolated worktree while A DATA-REF-005C and C/D Today
work proceed, provided the write sets remain disjoint:

1. TASK-FE-BE-STOCK-005C — map eod to the existing Explorer/Drawer while
   preserving null/unavailable and publication-state semantics.
2. A read-only Stock technical-detail audit or contract planning task;
   implementation remains blocked on Historical publication authority.
3. Additional backend semantic tests that exercise canonical observations in a
   disposable database, without changing provider/persistence behavior.

Do not parallelize a provider, reference, post-close, migration, scheduler,
Today, Topic, taxonomy, relation, recommendation, or Production change under
this slice.

## RECOMMENDED_VERTICAL_SLICE_ORDER

    STOCK-005B  Additive StockEodRead backend/API projection       COMPLETE LOCALLY
    STOCK-005C  Explorer/Drawer EOD formal wiring                  NEXT
    STOCK-006   Technical detail contract/publication audit        AFTER Historical authority
    STOCK-007   Timeline/history and remaining detail fields      AFTER their contracts

## UI_REQUIREMENTS_PRESERVED

- Slide-in Drawer behavior remains preserved.
- Drawer starts below the shared header, fills the remaining viewport height,
  remains sticky while the page scrolls, and scrolls internally.
- Advanced filtering includes topic filtering through the formal backend path.
- Existing search, debounce, stale-request protection, pagination reset,
  backend order, market/update-mode filters, and unsupported-control disclosure
  remain unchanged.

## API

    FASTAPI_SCHEMA_UPDATED=YES
    NEW_ENDPOINT_CREATED=NO
    BREAKING_CHANGE=NO
    OPENAPI_UPDATED=YES
    OPENAPI_DRIFT=PASS
    GENERATED_CLIENT_UPDATED=YES

StockEodRead and StockEodSource were added to the FastAPI schema and generated
artifacts. The existing StockReadModel.eod property is required at the
response-model boundary but nullable in value, preserving an explicit null
result rather than silently omitting the field.

## QUERY

    LIST_EOD_QUERY_STRATEGY=single set-based STOCK_ROWS_SQL projection with CTEs
    PREVIOUS_CLOSE_QUERY_STRATEGY=nearest earlier priced trading_date in eod_previous_price; no calendar-date subtraction
    N_PLUS_ONE_RISK=NO

The same read model feeds list and detail, so the two routes do not have
separate EOD selection logic.

## VALIDATION

| Check | Result |
| --- | --- |
| Focused Stock EOD tests | PASS — 6 passed |
| Stock list/detail contract path | PASS — shared read_stocks path; empty and seeded disposable PostgreSQL readback passed |
| Relevant backend regression | PASS — 8 passed |
| Full non-PostgreSQL backend suite | PASS — 349 passed, 4 skipped, 92 deselected |
| FastAPI schema tests | PASS — included in focused suite |
| OpenAPI regeneration | PASS — schema valid and written from app authority |
| OpenAPI drift check | PASS — baseline matches regenerated artifact |
| Generated client validation | PASS — regeneration and 3 generated-client tests; package check only fails its intentional clean-diff guard |
| Frontend TypeScript | PASS — web production build compiled generated client graph |
| Frontend related tests | PASS — 96 passed |
| Production build | PASS — apps/web production build |
| Ruff / compile | PASS — targeted modified Python files |
| git diff --check | PASS |
| Changed-file secret scan | PASS — no credential/private-key pattern |
| Disposable PostgreSQL migrations | PASS — all migrations applied in ephemeral containers |
| Disposable PostgreSQL EOD query | PASS — empty universe and seeded DAILY_BAR readback |

PostgreSQL integration tests that require an externally supplied database URL
were skipped; no external or Production database was used. Protected G1/G2/G3
and Canary gates were preserved, not rerun.

## DOCUMENTATION

    ROADMAP_UPDATED=YES
    PROJECT_CONTEXT_UPDATED=YES
    WORK_ORDERS_UPDATED=N/A / current register has no Stock task row; no duplicate register entry added
    PRODUCT_ROADMAP_UPDATED=YES
    DOCUMENTATION_INDEX_UPDATED=N/A / existing accepted 005A authority is already indexed; 005B adds no new authority document
    DAILY_PROGRESS_UPDATED=N/A / repository practice records this capability in AI_WORKLOG and the formal report
    AI_WORKLOG_UPDATED=YES / append-only
    FORMAL_REPORT_CREATED=YES

## FILES_MODIFIED

    PROJECT_CONTEXT.md
    docs/ROADMAP.md
    docs/product/TOPICPILOT_PRODUCT_ROADMAP.md
    docs/AI_WORKLOG.md
    docs/reports/TASK-FE-BE-STOCK-005B_ADDITIVE_STOCK_EOD_READ_IMPLEMENTATION.md
    services/api/src/topicpilot_api/production_read_model.py
    services/api/src/topicpilot_api/schemas.py
    services/api/tests/test_stock_eod_read.py
    packages/api-client/openapi.json
    packages/api-client/src/schema.d.ts
    apps/web/app/lib/generated-api.d.ts

No frontend component/UI file, provider, reference, migration, persistence,
post-close, historical, Today, Topic, taxonomy, relation, recommendation,
Production, Scheduler, or NEXT_TASK file was modified.

## SAFETY

    PROVIDER_CHANGED=NO
    REFERENCE_CHANGED=NO
    MIGRATION_CREATED=NO
    PERSISTENCE_CHANGED=NO
    POST_CLOSE_CHANGED=NO
    HISTORICAL_CHANGED=NO
    TODAY_CHANGED=NO
    TOPIC_CHANGED=NO
    TAXONOMY_CHANGED=NO
    RELATIONS_CHANGED=NO
    RECOMMENDATION_CHANGED=NO
    FRONTEND_UI_CHANGED=NO

    PRODUCTION_MUTATION=NO
    PRODUCTION_DB=NO
    PUSH_REMOTE=NO
    MERGE_MAIN=NO
    DEPLOY=NO
    SCHEDULER=NO
    NEXT_TASK_CHANGED=NO

    G1=PRESERVED PASS / NOT RERUN
    G2=PRESERVED PASS / NOT RERUN
    G3=PRESERVED PASS / NOT RERUN
    POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN

## Canonical reconciliation closure

The implementation was reconciled with current canonical HEAD
017460da9d0a8fde2905e85f39e8670b5393b9c9 using a clean temporary reconciliation
worktree. The exact application/schema/test/OpenAPI/generated-client/report
write set was committed as b78d4db and cherry-picked into canonical. The
canonical worktree's unrelated dirty files were preserved; only targeted Stock
owner-document additions were merged.

    RECONCILIATION_PHASE=COMPLETE
    PRE_RECONCILIATION_CANONICAL_SHA=017460da9d0a8fde2905e85f39e8670b5393b9c9
    POST_RECONCILIATION_CANONICAL_SHA=7aec60c
    APPLICATION_RECONCILIATION=PASS / canonical commit b78d4db
    SCHEMA_RECONCILIATION=PASS
    DOC_RECONCILIATION=PASS / targeted semantic additions; unrelated dirty hunks preserved
    OPENAPI_REGENERATED=YES
    OPENAPI_DRIFT=PASS
    GENERATED_CLIENT_REGENERATED=YES
    IMPACT_VALIDATION=PASS
    WORKTREE_CLEANUP=TEMPORARY_RECONCILIATION_WORKTREE_REMOVED; Stock source worktree removed; task branch retained for predecessor 005A evidence

    STOCK_EOD_READ_CANONICAL=YES
    LIST_ROUTE_EOD_CANONICAL=YES
    DETAIL_ROUTE_EOD_CANONICAL=YES
    NEW_ENDPOINT_CREATED=NO
    BREAKING_CHANGE=NO
    N_PLUS_ONE_RISK=NO

    CANONICAL_CONTENT_RECONCILED=YES
    CANONICAL_COMMIT_CREATED=YES
    CANONICAL_RECONCILIATION_COMMIT=b78d4db
    PRODUCTION_MUTATION=NO
    PRODUCTION_DB=NO
    PUSH_REMOTE=NO
    MERGE_MAIN=NO
    DEPLOY=NO
    SCHEDULER=NO
    NEXT_TASK_CHANGED=NO

    G1=PRESERVED PASS / NOT RERUN
    G2=PRESERVED PASS / NOT RERUN
    G3=PRESERVED PASS / NOT RERUN
    POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
    FINAL_STATUS=STOCK_EOD_READ_CANONICAL_COMPLETE
    NEXT_STOCK_SLICE=TASK-FE-BE-STOCK-005C
