# F9｜Truthful Read-only Commercial Beta Integration Closure — BLOCKED

```text
TASK=F9
EXACT_SHA_BEFORE=909c7600001e43e17f216cd8fed51ebda94805b3
EXACT_SHA_AFTER=recorded in final handoff after the single commit
COMMIT_SHA=recorded in final handoff after the single commit
COMMIT_MESSAGE=fix(ui): close commercial beta integration

TODAY_COMMERCIAL_READ_VIEW=PASS
TOPIC_COMMERCIAL_READ_VIEW=FAIL_COMMITTED_PROVIDER_ROUTE_MISSING
STOCK_COMMERCIAL_READ_VIEW=PASS
TECHNICAL_EVIDENCE_VIEW=PASS
CORE_USER_JOURNEY=FAIL_TODAY_TO_TOPIC_CATALOG_RETURNS_404
CROSS_PAGE_IDENTITY=PASS_FRONTEND_CONTRACT
CROSS_PAGE_ASOF_SEMANTICS=PASS_FRONTEND_CONTRACT
CROSS_PAGE_STATE_SEMANTICS=PASS
MARKET_AWARE_NAVIGATION=PASS
NO_LEGACY_FORMAL_FALLBACK=PASS
NO_FRONTEND_RECOMPUTATION=PASS
NO_FAKE_FORMAL_DATA=PASS
UNPUBLISHED_CAPABILITIES_TRUTHFUL=PASS
RESPONSIVE_SMOKE=PRESERVED_F8_PASS_NOT_RERUN
ACCESSIBILITY_SMOKE=PASS_STATIC_AND_TESTED
FRONTEND_REGRESSION=PASS
TSC=PASS_CLEAN_EXACT_SHA_CANDIDATE_WITH_F9_WRITE_SET
PRODUCTION_BUILD=PASS_CLEAN_EXACT_SHA_CANDIDATE_WITH_F9_WRITE_SET

FRONTEND_TRUTHFUL_READONLY_BETA=BLOCKED
FRONTEND_COMMERCIAL_BETA_SERIES=NOT_CLOSED
LATEST_PRODUCTION_FRESHNESS=PENDING_A10
NO_FURTHER_F_SERIES_TASK_OPENED=YES
```

## Decision and exact blocker

F9 cannot close the supported product journey. The committed frontend calls
`/api/v2/topic-catalog`, its detail route, and its snapshot-history route, but
the exact committed baseline contains none of those FastAPI routes. A clean
archive of HEAD loaded the real application and returned an empty Topic Catalog
OpenAPI path list and HTTP 404 for `GET /api/v2/topic-catalog`.

The apparent provider in the shared checkout is parallel, uncommitted work:
`topic_catalog.py`, `topic_catalog_api.py`, `topic_catalog_schemas.py`, its test,
and the `main.py` router registration are outside HEAD. F9 does not adopt,
stage, modify, or use that work to manufacture integration acceptance. Closing
this blocker requires backend/provider authority and canonical reconciliation,
which is outside this frontend-only integration closure.

## Bounded F9 fix

Topic formal history previously showed a retry button when the formal authority
was unconfigured. The F9 change limits retry to transport/contract `ERROR` and
adds a regression test proving `UNAVAILABLE` renders no retry and no inherited
formal facts. This preserves the F5 state contract and does not alter data,
schema, provider, calculations, or publication authority.

Write-set:

- `apps/web/app/components/v2/TopicSnapshotHistory.tsx`
- `apps/web/tests/topic-history.test.mjs`
- this report

## Acceptance evidence

The clean candidate was created from exact HEAD by `git archive`, installed from
the committed lockfile, and overlaid only with the two F9 frontend files.

- Focused Today/Topic/Stock/state/navigation journeys: 76 passed, 0 failed,
  skipped, cancelled, or todo.
- Clean frontend suite: 202 passed, 0 failed/skipped; F8 clean baseline was 201,
  delta +1 from the F9 authority-unavailable retry test.
- Shared working-tree frontend suite: 205 passed; diagnostic only because it
  includes three owner/parallel tests absent from committed HEAD.
- API client: 4 passed.
- Backend Home/Stock EOD/Technical focused contracts: 45 passed.
- Clean `tsc --noEmit`: PASS.
- Clean production Web build: PASS.
- `git diff --check`: PASS.
- Source review confirms the formal consumers preserve backend order, identity,
  market, as-of/session, publication and provenance; they do not calculate Topic,
  market, EOD, history, or technical values. Legacy/demo values remain visibly
  Preview and cannot populate formal detail/history/technical states.
- Accessibility review covers semantic primary links, `aria-current`, status and
  alert roles, named Drawer dialog/close action, table headings, transport-only
  retry, reduced motion, and keyboard-native links/buttons.
- F8's browser smoke at 1280×800 and 390×844 remains applicable to the unchanged
  layout. F9 browser smoke was not rerun because local preview startup was
  rejected by the execution approval layer; this preserved evidence is not
  upgraded into a new F9 execution claim.

The shared checkout `tsc` diagnostic still reports the pre-existing owner Today
overlay missing `sectionStatus`; the clean exact-SHA candidate plus F9 write-set
passes. This owner overlay is excluded from the F9 commit.

## Journey and state disposition

Today, Stock Drawer/standalone detail, raw history, formal Technical evidence,
market-aware duplicate-code identity, direct Stock links, `LOADING`, `ERROR`,
`EMPTY`, `UNAVAILABLE`, `PARTIAL`, `STALE`, and non-trading-day EOD semantics
pass their committed frontend contracts. Parent Topic remains
`NOT_APPLICABLE`; Leaf current/history identity and bounded as-of behavior pass
frontend tests. The live clean product journey stops at Topic Catalog because
the committed backend route returns 404.

Opportunity, Market Events without publication authority, Lifecycle/Selector,
AI Research Lab, institutional/news/revenue providers, advanced filters, and
legacy Watchlist/Studio remain explicitly unavailable, coming soon, shadow,
Preview, or demo. They do not cause this failure; their truthful boundaries pass.

The newest A10 repository report still records blocked activation and no fresh
Production readback, so `LATEST_PRODUCTION_FRESHNESS=PENDING_A10`. This is
separate from the committed Topic provider blocker.

All pre-existing owner/parallel tracked and untracked changes were preserved.
No reset, clean, checkout, stash manipulation, blanket staging, push, merge,
deployment, Production mutation, scheduler activation, or `NEXT_TASK` change
occurred. F9 stops here and does not start A10, B2/B3/B4, F9.1, F10, or another
frontend task.
