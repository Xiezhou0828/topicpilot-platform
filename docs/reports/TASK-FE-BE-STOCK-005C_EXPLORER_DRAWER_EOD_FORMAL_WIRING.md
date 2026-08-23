# TASK-FE-BE-STOCK-005C — Stock Explorer / Drawer EOD Formal Wiring

## Executive Result

The V2 Stock Explorer and shared Stock Encyclopedia Drawer now consume the
canonical nullable `StockEodRead` projection from the existing formal Stock
list/detail routes. The browser only selects and formats serialized backend
values; it does not reconstruct EOD semantics, silently substitute Preview
data, or derive turnover.

## Canonical State

    TASK_ID=TASK-FE-BE-STOCK-005C
    TASK_NAME=Stock Explorer / Drawer EOD Formal Wiring
    CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
    CANONICAL_PRE_SHA=ca881f88363dcb5c0b5354ac4ed2cbc31252b2af
    CANONICAL_POST_SHA=070a072c0e0a0e943fdeb6d4fa3462a7534658fc
    CANONICAL_RECONCILIATION_COMMIT=070a072c0e0a0e943fdeb6d4fa3462a7534658fc
    CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
    ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
    WORKTREE_USED=C:\Users\acer\Documents\Codex\2026-08-14\stock-005c-worktree
    WORKTREE_BRANCH=codex/task-fe-be-stock-005c-20260814
    REBASED_ON_CANONICAL_SHA=ca881f88363dcb5c0b5354ac4ed2cbc31252b2af

The canonical checkout contained pre-existing user-owned dirty Topic,
architecture, research, and owner-document changes. They were preserved. The
application commit was replayed cleanly as `f364655`; owner-doc changes below
were applied at hunk level after the final rebase.

## Existing UI Audit

- `/stocks` uses the V2 formal Stock Explorer list/grid and the formal adapter.
- Existing market, sorting, update-mode, advanced topic, technical, chip, and
  strategy controls remain intact; the advanced topic filter remains client
  render/filter behavior over formal topic relations.
- The shared Drawer loads `GET /api/v2/stocks/{symbol}` and protects against a
  prior symbol's async detail response replacing the selected stock.
- The Drawer remains a right-side push surface with slide-in/reverse-close,
  header offset, full remaining viewport height, sticky shell, internal scroll,
  close/Escape controls, and stock switching.
- Technical detail, timeline/history, institution/chip data, narrative,
  Opportunity, and recommendation remain separate or unavailable contracts.

## EOD Field Mapping

| UI need | Formal source | Browser behavior |
| --- | --- | --- |
| Close / OHLC | `eod.close`, `eod.open`, `eod.high`, `eod.low` | Format only |
| Previous close | `eod.previousClose` | Format only |
| Change / change percentage | `eod.change`, `eod.changePct` | Format only |
| Volume / turnover | `eod.volume`, `eod.turnover` | Null remains unavailable |
| Trading date | `eod.tradingDate` | Format only |
| Status | `eod.dataStatus` | Explicit status label |
| Lineage | `eod.priceSource`, `eod.volumeSource` | Source code disclosure |
| Freshness/as-of | `eod.observedAt`, `eod.retrievedAt` | Metadata disclosure |
| Adjustment compatibility | `eod.adjustmentState` | Metadata disclosure |

The generated `StockEodRead` type remains the field/nullability authority. No
new route, schema, OpenAPI field, or generated client field was created.

## Explorer and Drawer Wiring

Formal rows retain both top-level latest quote fields and nullable `eod`. The
presenter applies the accepted boundary:

- `INTRADAY` rows use top-level latest price/change percentage/volume.
- Non-intraday formal rows use `eod.close`, `eod.changePct`, and `eod.volume`.
- Non-intraday formal `eod=null` renders unavailable and does not fall back to
  top-level values, historical data, or Preview.
- Explicit Preview remains labelled Preview and is never formal EOD.

The Drawer adds an EOD section for close, previous close, change, percentage,
OHLC, volume, turnover, trading date, data status, source codes, adjustment
state, observed-at, and retrieved-at. Numeric nulls remain `—`/unavailable;
they are never zero-filled.

## Intraday / Null / Preview Semantics

    INTRADAY_EOD_BOUNDARY_PRESERVED=YES
    NULL_FAIL_CLOSED=YES
    API_ERROR_PREVIEW_FALLBACK=NO
    PREVIEW_BOUNDARY_PRESERVED=YES
    AVAILABLE_RENDERING=YES
    PARTIAL_RENDERING=YES
    UNAVAILABLE_RENDERING=YES
    NO_TRADE_RENDERING=YES
    SUSPENDED_RENDERING=YES
    ADJUSTMENT_UNKNOWN_RENDERING=YES
    SOURCE_CONFLICT_RENDERING=YES

`INTRADAY_SOURCE` and `EOD_SOURCE` are explicit presenter modes. The browser
does not infer status, no-trade, suspension, adjustment state, provider
reconciliation, or a previous calendar day.

## Browser Business Logic Guard

    BROWSER_CHANGE_CALCULATION=NO
    BROWSER_CHANGE_PCT_CALCULATION=NO
    BROWSER_PREVIOUS_CLOSE_CALCULATION=NO
    BROWSER_TURNOVER_DERIVATION=NO
    BROWSER_PROVIDER_RECONCILIATION=NO
    BROWSER_TOPIC_RANKING=NO
    BROWSER_BUSINESS_CLASSIFICATION=NO

The focused source guard rejects close/previous-close arithmetic, price-times-
volume turnover derivation, and browser calendar-date reconstruction. No
technical score, topic ranking, recommendation, narrative, timeline, or
institution business rule was added.

## Interaction Regression

    DRAWER_SLIDE_IN_PRESERVED=YES
    DRAWER_REVERSE_ANIMATION_PRESERVED=YES
    DRAWER_HEADER_OFFSET_PRESERVED=YES
    DRAWER_FULL_HEIGHT_PRESERVED=YES
    DRAWER_STICKY_PRESERVED=YES
    DRAWER_INTERNAL_SCROLL_PRESERVED=YES
    STOCK_SWITCH_STALE_DATA_PROTECTION=PASS
    ADVANCED_TOPIC_FILTER_REGRESSION=PASS

## Tests and Gates

- Focused EOD wiring tests: `8 passed`.
- Full frontend suite: `104 passed`.
- TypeScript `npx tsc --noEmit`: passed.
- Changed-file ESLint: passed.
- Production frontend build: passed; `/stocks` and `/stocks/:code` remain in
  the generated route tree.
- `git diff --check`: passed.
- Changed-file secret scan: passed during canonical reconciliation.
- Route smoke: `NOT_RUN_ENVIRONMENT_RESTRICTION`; no local background runtime
  was started.
- G1/G2/G3/Post-Close Canary: `PRESERVED PASS`, not rerun. This frontend read
  slice does not cross provider, reference, persistence, post-close, or
  Production boundaries.

## Safety and Scope

    BACKEND_CHANGED=NO
    OPENAPI_CHANGED=NO
    GENERATED_CLIENT_CHANGED=NO
    HISTORICAL_CHANGED=NO
    REFERENCE_CHANGED=NO
    TODAY_CHANGED=NO
    TOPIC_CHANGED=NO
    RECOMMENDATION_CHANGED=NO
    PRODUCTION_MUTATION=NO
    PRODUCTION_DB=NO
    PUSH_REMOTE=NO
    MERGE_MAIN=NO
    DEPLOY=NO
    SCHEDULER=NO
    NEXT_TASK_CHANGED=NO

## Documentation Reconciliation

Updated the concise 005C checkpoints in `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`,
`docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`, `docs/DAILY_PROGRESS.md`, and
`docs/WORK_ORDERS.md`. `docs/DOCUMENTATION_INDEX.md` was not changed because
this report is execution evidence, not a new architecture authority.

## Files Modified

- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
- `apps/web/app/globals.css`
- `apps/web/app/lib/stock-api.ts`
- `apps/web/app/lib/stock-eod-presenter.mjs`
- `apps/web/app/lib/stock-eod-presenter.d.ts`
- `apps/web/tests/stock-eod-wiring.test.mjs`
- `docs/reports/TASK-FE-BE-STOCK-005C_EXPLORER_DRAWER_EOD_FORMAL_WIRING.md`
- owner-doc checkpoints listed above

## Remaining Stock Gaps

Technical detail/publication, timeline/history, institution flow, narrative,
Opportunity, and recommendation remain separate follow-up work. The next
candidate is `TASK-FE-BE-STOCK-006` for technical-detail contract/publication
reassessment, subject to Historical publication authority.

## Final Status

    TASK_ID=TASK-FE-BE-STOCK-005C
    FINAL_STATUS=STOCK_EOD_FRONTEND_VERTICAL_COMPLETE
