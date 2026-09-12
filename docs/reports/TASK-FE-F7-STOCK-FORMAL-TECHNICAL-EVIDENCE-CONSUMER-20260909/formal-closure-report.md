# Frontend F7｜Stock Formal Technical Evidence Consumer

```text
TASK=F7
EXACT_SHA_BEFORE=1e8baf6d99c2c960eda7490de345a6b34d1393fc
EXACT_SHA_AFTER=reported in final handoff after commit (self-referential commit field)
COMMIT_SHA=reported in final handoff after commit (self-referential commit field)
COMMIT_MESSAGE=feat(stocks): connect formal technical evidence

STOCK_TECHNICAL_EVIDENCE_CONSUMER=PASS
FORMAL_SOURCE_ONLY=PASS
NO_FRONTEND_TECHNICAL_RECOMPUTATION=PASS
PARTIAL_EVIDENCE_TRUTHFUL=PASS
UNAVAILABLE_TECHNICAL_STATE=PASS
TECHNICAL_SOURCE_ASOF_VISIBLE=PASS
STOCK_DRAWER_DETAIL_TECHNICAL_PARITY=PASS
MARKET_AWARE_TECHNICAL_IDENTITY=PASS
LEGACY_TECHNICAL_NOT_FORMAL=PASS
F5_STATE_SEMANTICS_PRESERVED=PASS

FOCUSED_STOCK_FRONTEND_TESTS=PASS (52 passed)
SHARED_DIRTY_WORKTREE_FRONTEND_TESTS=PASS (198 passed)
CLEAN_CANDIDATE_FRONTEND_TESTS=PASS (195 passed)
TEST_COUNT_PRE=190 passed (F5 clean-candidate closure baseline)
TEST_COUNT_POST=195 passed
TEST_COUNT_DELTA=+5
TEST_COUNT_DELTA_REASON=F7 adds five formal technical consumer, authority, state, parity, and legacy-isolation tests
API_CLIENT_TESTS=PASS (4 passed)
BACKEND_TECHNICAL_CONTRACT_TESTS=PASS (33 passed)
TSC_NO_EMIT=PASS (clean candidate)
WEB_PRODUCTION_BUILD=PASS (shared dirty worktree and clean candidate)
GIT_DIFF_CHECK=PASS

SAFE_TO_PROCEED_WITH_F8=YES
FRONTEND_ONLY_BLOCKER_FOR_F9=NO
PUSH=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

## Result

The shared Stock Drawer and `/stocks/[code]` now use the existing
`/api/v2/stocks/{symbol}/technical` read-only publication contract through the
same React view. The request is bound to the formal EOD trading date and exact
`(market, code)` identity. A response with a different code, market, request
date, calculation owner, browser-calculation permission, evidence identity, or
available-source authority fails closed.

The UI exposes technical result, MA60 eligibility, event-authority status, and
publication status as separate backend-owned fields. It shows the formal source,
raw-observed series semantics, evidence session, `asOf`, adjustment state,
contract version, policy version, reason codes, and limitation reasons. The
technical contract does not publish a freshness enum, so the UI states that the
freshness status is not published rather than inferring `FRESH` or `STALE` from
the current date.

`AVAILABLE_WITH_LIMITATION`, any `FORMAL_WITH_LIMITATION` evidence, a missing
member of the fixed 14-indicator set, or a mixture of available and unavailable
evidence remains `PARTIAL`. `BLOCKED`, authority `UNAVAILABLE`, and contract
`ERROR` outcomes remain `UNAVAILABLE` and do not offer a transport retry. Only
an actual HTTP/transport or response-contract failure renders `ERROR` with a
retry action. An available authority with zero publishable records is `EMPTY`.

Raw historical prices remain a separate raw table. The frontend performs only
identity validation, session selection, status mapping, and string display. It
does not calculate, aggregate, reconstruct, round, rank, screen, or interpret a
technical value.

The old Stock list `technicalEvidence` shape (`above20MA`, `above60MA`, `ma20`,
`ma60`, `breakoutState`, and `technicalState`) is no longer copied into the
formal Drawer model or used by disabled browser filters. It cannot masquerade
as the formal Technical V0 consumer.

## Exact formal technical fields exposed

The current backend contract publishes these 14 Technical V0 indicator IDs,
and F7 supports exactly this fixed set:

1. `MA5`
2. `MA10`
3. `MA20`
4. `MA60`
5. `DISTANCE_TO_MA20`
6. `RAW_CLOSE_RETURN_5D`
7. `RAW_CLOSE_RETURN_20D`
8. `VOLUME_MA5`
9. `VOLUME_MA20`
10. `VOLUME_RATIO_20`
11. `RSI14`
12. `MACD_12_26_9`
13. `MACD_SIGNAL_12_26_9`
14. `MACD_HISTOGRAM_12_26_9`

Each displayed record is passed through with its `indicatorId`, `value`,
`sessionDate`, `publicationState`, and `availabilityReason`. The consumer also
uses the top-level `technicalResultStatus`, `technicalEligibility`,
`eventAuthorityStatus`, `publicationStatus`, `limitationReasons`,
`reasonCodes`, `calculationOwner`, `browserCalculationAllowed`,
`technicalContractVersion`, `technicalPolicyVersion`, `priceBasis`, `asOf`, and
the provenance `authority`, `seriesSemantics`, `adjustmentState`, and
`latestTradingDate` fields.

## Intentionally unavailable or deferred

No formal boolean price-versus-MA state, breakout trigger, technical score,
screen result, Selector result, or recommendation is created. Legacy KD,
MA-slope, days-above-MA, high-distance, up-volume, pullback-volume, structure,
and breakout fields remain outside the formal consumer. Advanced Liquidity
Sweep, Order Flow, Anchored VWAP, Volume Profile, Fair Value Gap, Fibonacci,
Supply/Demand, and Trading Pattern families remain deferred by the backend
policy. Corporate-action completeness, adjusted-price truth, institutional
flow, fundamentals, news, Opportunity, Lifecycle, and Selector semantics are
unchanged.

## F7 write-set

- `apps/web/app/lib/stock-api.ts`
- `apps/web/app/components/v2/StockEncyclopediaDrawer.tsx`
- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/tests/stock-formal-view.test.mjs`
- `apps/web/tests/stock-explorer-query.test.mjs`
- `docs/reports/TASK-FE-F7-STOCK-FORMAL-TECHNICAL-EVIDENCE-CONSUMER-20260909/formal-closure-report.md`

No backend, schema, generated client, database, runtime, deployment, roadmap,
or `NEXT_TASK` artifact changed.

## Validation boundary

Focused Stock validation covers formal endpoint query construction, exact
market/code/date/authority validation, the full 14-ID inventory, latest-session
selection, available/empty/partial/unavailable/loading/error behavior, source
and as-of disclosure, transport-only retry, Drawer/detail shared rendering, and
legacy technical isolation. Backend validation uses Python 3.12 and passes the
existing provider/consumer and publication route suites.

The shared dirty working tree passes all 198 frontend tests and the production
build. Its direct `tsc --noEmit` remains affected by a pre-existing owner Today
overlay: `today-mainlines.ts` constructs one `TodayRotationResource` without
the owner-added required `sectionStatus`. A clean candidate containing committed
F5 plus only the F7 files passes `tsc --noEmit`, the production build, and all
195 discovered clean-candidate frontend tests after `npm ci` from the committed
lockfile. The clean test count differs from the shared dirty count because the
preserved owner Today/Topic overlay adds three uncommitted tests, matching the
F5 closure's recorded dirty-versus-clean split.

## Preserved parallel work

All tracked and untracked owner/parallel changes present at F7 start remain
outside the commit. F7 uses no reset, clean, checkout, stash manipulation,
blanket staging, push, merge, deployment, Production mutation, or `NEXT_TASK`
change. The exact post-commit remaining paths are:

```text
M apps/web/app/components/v2/TodayMarketPage.tsx
M apps/web/app/components/v2/TopicDetailPage.tsx
M apps/web/app/lib/today-mainlines.ts
M apps/web/app/lib/topic-api.ts
M compose.yaml
M docs/operations/deployment.md
M packages/api-client/src/client.d.mts
M packages/api-client/src/client.mjs
M render.yaml
M services/api/.env.example
M services/api/pyproject.toml
M services/api/src/topicpilot_api/live/cli.py
M services/api/src/topicpilot_api/live/config.py
M services/api/src/topicpilot_api/live/post_close.py
M services/api/src/topicpilot_api/live/scheduler.py
M services/api/src/topicpilot_api/main.py
M services/api/src/topicpilot_api/orm/__init__.py
M services/api/src/topicpilot_api/production_read_model.py
M services/api/src/topicpilot_api/schemas.py
M services/api/tests/test_v2_architecture_freeze.py
?? apps/web/app/lib/formal-topic-snapshot.ts
?? apps/web/tests/formal-topic-snapshot.test.mjs
?? reports/TASK-SOURCE-WORKSPACE-HYGIENE-DIRTY-STATE-CLASSIFICATION-CLOSURE-20260831/
?? services/api/alembic/versions/0037_task_b2_lifecycle_v1_3_formal_publication.py
?? services/api/src/topicpilot_api/lifecycle_formal_publication.py
?? services/api/src/topicpilot_api/live/daily_forward.py
?? services/api/src/topicpilot_api/orm/formal_lifecycle.py
?? services/api/src/topicpilot_api/topic_catalog.py
?? services/api/src/topicpilot_api/topic_catalog_api.py
?? services/api/src/topicpilot_api/topic_catalog_schemas.py
?? services/api/src/topicpilot_api/topic_lifecycle_formal_cli.py
?? services/api/src/topicpilot_api/topic_lifecycle_v1_3_formal.py
?? services/api/tests/test_daily_forward.py
?? services/api/tests/test_lifecycle_v1_3_formal_publication.py
?? services/api/tests/test_topic_catalog.py
?? tools/ws4_bounded_eod_catchup.py
?? tools/ws4_formal_eod_publication.py
```
