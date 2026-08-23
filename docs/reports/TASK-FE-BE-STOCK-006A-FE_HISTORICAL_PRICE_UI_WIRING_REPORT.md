# TASK-FE-BE-STOCK-006A-FE Historical Price UI Wiring

## Executive Decision

```text
TASK_ID=TASK-FE-BE-STOCK-006A-FE-HISTORICAL-PRICE-UI-WIRING
FINAL_STATUS=COMPLETE
TASK_MODE=ADDITIVE_FRONTEND_FORMAL_HISTORY_WIRING
BASELINE_TASK=TASK-FE-BE-STOCK-006A-HISTORICAL-BAR-READ-PUBLICATION
BASELINE_STATUS=COMPLETE_AND_ARCHIVED

CANONICAL_PRE_SHA=aa2bc8e206c62e35b76c3385afa53a7a8aca97a8
CANONICAL_POST_SHA=c85fa7ec90792b8b56a5dd71ea61f98ed6a30e9c
IMPLEMENTATION_COMMIT=NONE_WORKTREE_ONLY
HEAD_ADVANCED_DURING_TASK=YES_EXTERNAL_CONCURRENT_CORPORATE_ACTION_COMMIT
WORKTREE_CREATED=NO

FRONTEND_HISTORY_STATE=FORMAL_BOUNDED_RAW_HISTORY_WIRED
API_CLIENT_USAGE=V2_PRICE_HISTORY_GENERATED_SCHEMA_TYPED_EXISTING_FETCH_PATTERN
RAW_BAR_ADJUSTMENT_DISCLOSURE=RAW_OBSERVED_ADJUSTMENT_UNKNOWN
BROWSER_TECHNICAL_CALCULATION_ALLOWED=NO
HISTORY_TABLE_PRESENTATION=YES
HISTORY_CHART_PRESENTATION=NO

DATABASE_MUTATION=NO
BACKEND_CONTRACT_EXPANSION=NO
HISTORICAL_DATA_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
ENVIRONMENT_BLOCKED=NO
```

The archived backend publication contract is now wired into the Stock
Explorer Drawer through a collision-safe child component. The UI reads only
the formal bounded V2 price-history subresource and renders backend-owned
bars, source/lineage facts, period, as-of/freshness metadata, and the required
raw-price disclosure. It does not calculate or publish technical/business
semantics.

## Canonical HEAD and Collision Audit

The audit started at `aa2bc8e206c62e35b76c3385afa53a7a8aca97a8`. During the task,
another workstream advanced HEAD twice: first to `9afd0a31aa86294bc271af79716b1610b38b494f`
(`research: add corporate action coverage semantics`) and then to
`c85fa7ec90792b8b56a5dd71ea61f98ed6a30e9c`
(`docs(rec-a1): reassess coverage and freeze`). Those concurrent commits
changed only Corporate Action research/API/report files and did not touch the
frontend files used here. They were preserved and not included in this
implementation. No reset, stash, clean, blanket stage, or merge was
performed.

At the audit point, `StockEncyclopediaDrawer.tsx` and `TopicDetailPage.tsx`
had no active dirty collision. Existing dirty changes in `globals.css` and
other frontend/worktree files were retained. The implementation therefore
uses an isolated `StockPriceHistoryPanel` and one additive mount in the
shared Drawer; `TopicDetailPage.tsx` was not modified.

## Implementation Boundary

### API/client

`apps/web/app/lib/stock-api.ts` now exposes generated-schema aliases for
`HistoricalPriceHistoryResponse` and `HistoricalPricePoint`, plus
`fetchFormalStockHistory` using:

```text
GET /api/v2/stocks/{symbol}/price-history
from=2000-01-01
to=2100-01-01
limit=200
market=<formal market when available>
```

The existing frontend fetch pattern is retained while the response is typed
from `generated-api.d.ts`. The request carries an `AbortSignal`; HTTP/network
failure is returned as `ERROR`, missing formal API configuration is
`UNAVAILABLE`, and no V1, legacy, Preview, mock, or synthetic history fallback
exists.

### UI

`apps/web/app/components/v2/StockPriceHistoryPanel.tsx` is a dedicated child
component mounted from the Drawer. It renders a bounded table of backend rows
in backend order with nullable OHLCV values preserved as `—`; null is never
converted to zero. It also renders:

- returned period and bounded point count;
- source code and lineage versions;
- `asOf`, freshness, latest observed, and latest retrieved facts;
- `原始交易價格／未套用除權息調整。adjustmentState=UNKNOWN` disclosure;
- explicit state text and `data-history-status` for every required state.

No chart was added. A table is sufficient for the bounded history
publication and avoids adding browser-side geometry or derived series logic.

### State contract

| State | Entry condition | UI behavior |
|---|---|---|
| `LOADING` | Formal history request is pending | Loading copy; no stale prior symbol data is shown |
| `AVAILABLE` | Formal response contains accepted history items | Period, facts, disclosure, and raw OHLCV table |
| `EMPTY` | Response has no items or `coverageState=EMPTY` | Explicit no-bars message and backend availability reason when present |
| `UNAVAILABLE` | Preview surface or formal API origin is not configured | Explicit unavailable copy; no fallback source |
| `ERROR` | Configured formal API returns HTTP/network failure | Explicit error copy; no fallback source |

The component uses a request key, an active-request guard, and
`AbortController` cleanup so stock switching cannot publish a stale response.

## Preserved Behavior and Prohibited Scope

The Drawer animation modes (`overlay`, `inline`, `push`), header offset,
sticky/full-height behavior, internal scroll, Escape handling, existing formal
detail stale guard, advanced topic filtering, formal EOD wiring, and Favorites
were preserved. Topic Detail continues to use the same Drawer without any
changes to its data flow.

The task did not add STOCK-006B, MA/RSI/MACD/ATR/momentum/return/volume-ratio/
resistance fields, corporate-action adjustment or markers, event timeline,
institution/chip, narrative, opportunity, recommendation, backend contract
fields, DB writes, scheduler work, or roadmap/NEXT_TASK changes.

Browser work is render-only: number/date formatting and table presentation
only. There is no sorting, date arithmetic, chart geometry, indicator
calculation, return calculation, or business classification in the browser.

## Validation

```text
FOCUSED_HISTORY_DRAWER_EOD_FAVORITES_TESTS=21 passed
FULL_FRONTEND_BUILD_AND_SOURCE_CONTRACT_TESTS=127 passed
TYPESCRIPT_NO_EMIT=PASS
CHANGED_FILE_ESLINT=PASS
PRODUCTION_BUILD=PASS
DIFF_CHECK=PASS
SECRET_SCAN=NO_MATCH
```

The full frontend suite was rerun after the concurrent HEAD advance and still
passed 127/127. Browser smoke verification on the local Stock Explorer
confirmed that a Preview stock opens the Drawer with the new Historical Price
region in `UNAVAILABLE`, displays the raw-price/unknown-adjustment disclosure,
does not fall back to Preview/mock/legacy history, closes with Escape, and
produces no browser error logs. A live formal API response was not fabricated
when the local UI had no configured formal API origin; the fail-closed state
was verified instead.

## Delivery Flags and Recommendation

The implementation remains in the existing dirty worktree and was not
committed, pushed, merged, deployed, or staged as a blanket operation. The
canonical HEAD advanced externally during execution, so the report records
both the audit-start SHA and handoff SHA rather than misrepresenting a local
implementation commit.

Recommended next step only: keep this UI slice archived and wait for the
Corporate Action continuity/event policy closure before considering
`STOCK-006B Basic Technical Projection`. Do not auto-start 006B from this
task.
