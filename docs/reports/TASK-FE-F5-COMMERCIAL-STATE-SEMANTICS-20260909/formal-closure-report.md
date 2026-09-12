# Frontend F5｜Commercial State Semantics & Truthful UI Consistency

```text
TASK=F5
EXACT_SHA_BEFORE=1fec0260c2e0fa2b3e4b9592294dc5e34281d5f5
EXACT_SHA_AFTER=reported in final handoff after commit (self-referential commit field)
COMMIT_SHA=reported in final handoff after commit (self-referential commit field)
COMMIT_MESSAGE=refactor(ui): unify commercial data states

COMMERCIAL_STATE_SEMANTICS=PASS
SHARED_STATE_MAPPING=PASS
EMPTY_NOT_UNAVAILABLE=PASS
PARTIAL_NOT_COMPLETE=PASS
STALE_NOT_FRESH=PASS
NOT_APPLICABLE_NOT_ERROR=PASS
AUTHORITY_UNAVAILABLE_NOT_TRANSPORT_ERROR=PASS
TODAY_STATE_CONSISTENCY=PASS
TOPIC_STATE_CONSISTENCY=PASS
STOCK_STATE_CONSISTENCY=PASS
SOURCE_ASOF_FRESHNESS_CONSISTENCY=PASS
NO_FAKE_FORMAL_FALLBACK=PASS

FOCUSED_SHARED_TODAY_TOPIC_STOCK_TESTS=PASS (47 passed)
FRONTEND_TESTS=PASS (193 passed)
TEST_COUNT_PRE=190 passed (F6 closure baseline)
TEST_COUNT_POST=193 passed
TEST_COUNT_DELTA=+3
TEST_COUNT_DELTA_REASON=F5 adds two shared-state mapping tests and one Today empty-section contract test
API_CLIENT_TESTS=PASS (4 passed)
TSC_NO_EMIT=PASS
WEB_PRODUCTION_BUILD=PASS
GIT_DIFF_CHECK=PASS

SAFE_TO_PROCEED_WITH_F7=YES
SAFE_TO_PROCEED_WITH_F8=YES
FRONTEND_ONLY_STATE_BLOCKER_FOR_F9=NO
PUSH=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

## Result

The shared presentation mapper owns the canonical `LOADING`, `ERROR`,
`AVAILABLE`/`PUBLISHED`, `EMPTY`, `PARTIAL`, `STALE`, `UNAVAILABLE`, and
`NOT_APPLICABLE` vocabulary. It uses explicit transport, authority status,
publication, row count, and freshness inputs. Backend reason text and reason
codes remain visible metadata and never promote an unknown state.

Today maps an explicitly `AVAILABLE` Heating/Cooling section with zero rows to
`EMPTY`, preserves section `PARTIAL`, and exposes Market Overview `PARTIAL` or
`STALE` without calling it complete. Topic Leaf empty history remains distinct
from authority failure, Parent history remains `NOT_APPLICABLE`, and retry is
limited to transport errors. Stock maps formal EOD `PARTIAL` and explicit stale
freshness into the same presentation states; loading and unavailable shells do
not inherit formal facts, and only transport errors offer retry.

No backend authority, provider, formal database, calculation, lifecycle,
selector, navigation, deployment, or later frontend task was changed.

## F5 write-set

- `apps/web/app/lib/commercial-state.mjs`
- `apps/web/app/lib/commercial-state.d.mts`
- `apps/web/app/lib/today-mainlines.ts` (F5 hunks only; owner section-status disclosure hunks remain uncommitted)
- `apps/web/app/components/v2/TodayMarketPage.tsx` (F5 hunks only; owner disclosure hunks remain uncommitted)
- `apps/web/app/components/v2/TopicSnapshotHistory.tsx`
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
- `apps/web/tests/commercial-state.test.mjs`
- `apps/web/tests/today-section-state-disclosure.test.mjs`
- `apps/web/tests/topic-history.test.mjs`
- `apps/web/tests/stock-formal-view.test.mjs`
- `docs/reports/TASK-FE-F5-COMMERCIAL-STATE-SEMANTICS-20260909/formal-closure-report.md`

## Preserved dirty work

All tracked and untracked owner/parallel changes present at task start remain
outside the F5 commit. The post-commit handoff lists their exact paths. Because
Today files overlap, staging uses hunk-level reconciliation and audits HEAD,
index, and working tree separately.
