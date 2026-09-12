# Frontend F8｜Commercial UX & Navigation Closure

```text
TASK=F8
EXACT_SHA_BEFORE=e814e78780fce303ab9d823ecc51dcf2bac9de0c
EXACT_SHA_AFTER=reported in final handoff after commit (self-referential commit field)
COMMIT_SHA=reported in final handoff after commit (self-referential commit field)
COMMIT_MESSAGE=refactor(ui): close commercial navigation ux

COMMERCIAL_NAVIGATION=PASS
CORE_USER_JOURNEY=PASS
DEEP_LINKS=PASS
MARKET_AWARE_STOCK_NAVIGATION=PASS
ERROR_RECOVERY_UX=PASS
UNAVAILABLE_COMING_SOON_UX=PASS
LEGACY_ROUTE_BOUNDARY=PASS
OPERATOR_UI_BOUNDARY=PASS
RESPONSIVE_BASELINE=PASS
ACCESSIBILITY_BASELINE=PASS
SOURCE_ASOF_VISUAL_CONSISTENCY=PASS
F5_STATE_SEMANTICS_PRESERVED=PASS
NO_NEW_DATA_AUTHORITY=PASS
NO_FAKE_PRODUCT_CAPABILITY=PASS

SHARED_DIRTY_WORKTREE_FRONTEND_TESTS=PASS (204 passed)
CLEAN_CANDIDATE_FRONTEND_TESTS=PASS (201 passed)
TEST_COUNT_PRE=195 passed (F7 clean-candidate baseline)
TEST_COUNT_POST=201 passed
TEST_COUNT_DELTA=+6
TEST_COUNT_DELTA_REASON=F8 adds bounded commercial navigation, deep-link, state, legacy-boundary, accessibility and responsive contract coverage
TSC_NO_EMIT=PASS (clean candidate); shared owner overlay retains its pre-existing sectionStatus error
WEB_PRODUCTION_BUILD=PASS
GIT_DIFF_CHECK=PASS

SAFE_TO_PROCEED_WITH_F9=YES
FRONTEND_ONLY_BLOCKER_FOR_F9=NO
PUSH=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

## Result

The commercial header exposes only Today, Topic, Stock, and Favorites. The
unfinished Opportunity and AI Research routes remain addressable for old links,
but render an explicit unpublished boundary with a route back to Today. Search,
notification, account, and unfinished-product controls are not rendered in the
commercial header because no working commercial capability backs them.

The formal Topic catalog preserves its `asOf` context through list, hierarchy,
detail, and back links. Leaf members now link to `/stocks/[code]?market=...`, so
the Stock consumer resolves the exact market/code identity and attaches the
same formal Technical evidence consumer used by the Drawer. Authority
unavailability has no retry control; transport failures retain retry. Empty and
NOT_APPLICABLE remain distinct.

Internal topic UUIDs, enabled flags, and relation-version diagnostics are no
longer presented as primary customer table content. Source, `asOf`, publication,
availability, effective-date, and lineage disclosures remain visible. Retained
legacy Watchlist and Studio routes display an explicit Legacy Preview/DEMO
boundary, their old navigation no longer promotes those routes, and the Guide
routes users to the formal Stock surface.

## Routes and journeys validated

- Today `/` → formal Topic `/topics/[slug]` with backend-owned slug.
- Topic list/detail/hierarchy links retain `asOf`.
- Leaf Topic member → `/stocks/[code]?market=TPE|TWO`.
- Stock direct link preserves market/code identity and exposes formal EOD,
  history, Topic relations, and Technical evidence through the shared consumer.
- Stock detail provides a semantic link and direct-entry fallback to `/stocks`.
- `/opportunities` and `/ai-studio` truthfully disclose that the commercial
  capability is not published.
- `/market` retains its unambiguous redirect to the Today market anchor.
- `/watchlist` and `/studio` remain retained legacy/demo routes with visible
  boundaries and no commercial navigation exposure.

## Responsive and accessibility evidence

The commercial header scrolls safely at narrow width; page padding contracts,
wide table containment, single-column Technical evidence, and full-viewport
Stock Drawer behavior cover common mobile widths. Browser checks at 1280×800
and 390×844 found no page-level horizontal overflow on representative
unfinished, Topic, and market-aware Stock routes. Primary navigation uses
semantic links and `aria-current`; Stock back navigation is a link; retry is a
button only for transport errors; core actions remain keyboard reachable; the
Drawer close action has an accessible label; reduced-motion rules remain in
place.

## Intentionally unavailable

Opportunity, AI Research Lab, unpublished Lifecycle/Selector outputs, Market
Events without field-level publication authority, advanced Stock filters, and
other deferred providers remain unavailable, preview, shadow, or not applicable
according to their existing contracts. F8 adds no provider, schema, field,
calculation, fallback, recommendation, or publication authority.

## F8 write-set

- `apps/web/app/components/v2/V2Foundation.tsx`
- `apps/web/app/components/v2/V2Page.tsx`
- `apps/web/app/components/v2/TopicCatalogPage.tsx`
- `apps/web/app/stocks/[code]/page.tsx`
- `apps/web/app/components/AppNav.tsx`
- `apps/web/app/watchlist/page.tsx`
- `apps/web/app/studio/page.tsx`
- `apps/web/app/guide/page.tsx`
- `apps/web/app/globals.css`
- `apps/web/tests/commercial-navigation.test.mjs`
- `apps/web/tests/topic-catalog.test.mjs`
- `apps/web/tests/rendered-html.test.mjs`
- `docs/reports/TASK-FE-F8-COMMERCIAL-UX-NAVIGATION-CLOSURE-20260909/formal-closure-report.md`

## Preserved parallel work

All Today/Topic owner overlay, API-client, deployment/runtime, A10/B2/Lifecycle,
formal database, EOD tooling, and hygiene-report changes present at task start
remain outside the F8 commit. F8 used no reset, clean, checkout, stash
manipulation, blanket staging, push, merge, deployment, Production mutation, or
`NEXT_TASK` change. The exact remaining dirty paths are reported from the
post-commit working tree in the final handoff.
