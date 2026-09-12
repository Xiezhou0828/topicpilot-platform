# TopicPilot V2 Mainline C｜Today Canonical Reconciliation

## Canonical state

```text
CANONICAL_REPO = C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_BRANCH = codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_START_SHA = 7be817ec8e40b7a6cdce2fed9ff542ff2f4f7864
CANONICAL_RECONCILIATION_COMMIT = 4d11abe4c86d09c9019a334ad8a2feb836443611
ORIGIN_MAIN_AT_RECONCILIATION = 26f635b95d8d88fd7ed7e43949583347f3ab5feb
SOURCE_TODAY_SHA = 4bb3a954760117a6e4aa424868101da5f1f20c2a
```

The canonical worktree already contained unrelated user changes in
documentation, fixtures, and runtime-adjacent files. Those changes were left
untouched. Content-level comparison showed that canonical still had the
pre-004C Today implementation: no `today-home.ts`, the old single-purpose
mainlines adapter, hardcoded story/events/rotation content, and legacy
`useSnapshot`/`mockMarketMetrics` Market Overview assembly.

The source branch also contained unrelated Stock and DATA-REF patches. They
were explicitly excluded from this reconciliation.

## Reconciled accepted Today implementation

Only the following Today write set was reconciled:

- shared `TodayHomeResource` and one runtime `getHome()` request;
- Daily Focus projection and state handling;
- Main Topics projection and backend order/slug preservation;
- Heating/Cooling projections;
- Market Events projection;
- Market Overview projection from `HomeResponse.marketOverview`;
- affected frontend regression/focused tests;
- 004D/004E evidence reports;
- append-only `docs/AI_WORKLOG.md` entry;
- owner-document status updates in `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`,
  and `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`.

No backend file, migration, schema, OpenAPI document, DATA-REF file, provider,
Production data, scheduler, lifecycle, scoring, Opportunity, Recommendation,
or historical file was changed.

## Today surface status

| Surface | Current state | Backend authority |
| --- | --- | --- |
| Daily Focus | `TEMPORARY` | `GET /api/v2/home` → `HomeResponse.dailyFocus`; current read model marks it temporary/rule-based |
| Main Topics | `UNAVAILABLE` by default (`PARTIAL`/`TEMPORARY` backend; explicit Preview only when enabled) | `HomeResponse.mainTopics` / `HomeTopicCard[]` |
| Heating / Cooling | `UNAVAILABLE` by default (`PARTIAL`/`TEMPORARY` backend; explicit Preview only when enabled) | `HomeResponse.heatingTopics` and `coolingTopics` |
| Market Events | `TEMPORARY` | `HomeResponse.marketPulse` / `HomeMarketPulseEvent[]` |
| Market Overview | `TEMPORARY` | `HomeResponse.marketOverview` / `HomeMarketOverview` |

No surface was relabeled `FORMAL`. `PARTIAL` remains backend publication truth;
null values remain null/unavailable, and API errors do not fall back to mock or
Preview data.

## Market Overview current-code audit

The canonical FastAPI authority remains the existing `GET /api/v2/home` route.
`HomeMarketOverview` contains:

```text
dataDate
updatedAt
dataStatus
trackedStockCount
trackedTopicCount
latestSnapshotTime
marketHealth.{market,status,totalStocks,advance,decline,flat,unavailable}
source
```

The current Home read model still emits `source=POSTGRESQL_READ_MODEL` and
`dataStatus=PARTIAL`, with nullable `marketHealth`. Its current missing-section
list still includes `marketIndices` and `turnover`.

The current `market_snapshots` model stores market breadth/status counts but no
index values or turnover columns. The canonical `canonical_volume_observations`
table has a generic nullable `turnover_amount` field, but the current code has
no approved market aggregate projection, TWSE/TPEx representation, source
authority, date/as-of/freshness contract, or Home read-model mapping for it.
It is therefore not sufficient authority for a Today Market Overview field.

## Remaining formal gaps

```text
MARKET_INDICES = BLOCKED_PENDING_FORMAL_DATA_AUTHORITY
TURNOVER = BLOCKED_PENDING_FORMAL_DATA_AUTHORITY
MARKET_SCORE = BLOCKED_PENDING_FORMAL_CONTRACT_AND_DERIVED_POLICY
BULLISH_BEARISH = BLOCKED_PENDING_FORMAL_CONTRACT_AND_DERIVED_POLICY
NARRATIVE = BLOCKED_PENDING_FORMAL_CONTRACT_AND_DERIVED_POLICY
VOLUME_TREND = BLOCKED_PENDING_FORMAL_CONTRACT_AND_DERIVED_POLICY
```

The proposed next Today slice is:

```text
PROPOSED_NEXT_TODAY_SLICE = FORMAL_MARKET_INDICES_TURNOVER
NEXT_TODAY_SLICE = BLOCKED_PENDING_FORMAL_DATA_AUTHORITY
```

Before implementation, the source owner must define index/turnover facts,
TWSE/TPEx identity, market aggregation semantics, data date, as-of/freshness,
lineage, null/missing behavior, and whether the existing Home contract can be
expanded without creating a parallel endpoint. The frontend must remain a
render-only consumer.

## Impact-based validation

```text
TODAY_FOCUSED_VALIDATION = 48/48 PASS
FRONTEND_FULL_TESTS_AND_BUILD = 96/96 PASS
TYPESCRIPT = PASS
FULL_FRONTEND_LINT = PASS (one pre-existing unrelated warning at TopicDetailPage.tsx:114)
GENERATED_API_CONTRACT_IDEMPOTENCE = PASS
API_CLIENT_TESTS = 3/3 PASS
DEMO_SNAPSHOT_CHECK = PASS
DIFF_CHECK = PASS
EXPLICIT_TODAY_SECRET_SCAN = PASS
BACKEND_TESTS = NOT RUN (backend unchanged)
G1 = PRESERVED PASS
G2 = PRESERVED PASS
G3 = PRESERVED PASS
POST_CLOSE_CANARY = PRESERVED PASS
```

The protected DATA/runtime gates were preserved from the current
`TASK-DATA-REF-009A` baseline because this reconciliation changed only
frontend/read-only wiring and documentation status.

## Safety and cleanup

```text
PRODUCTION_MUTATION = NO
PUSH_REMOTE = NO
DEPLOY = NO
SCHEDULER = NO
NEXT_TASK_CHANGED = NO
TODAY_RECONCILIATION = YES
UNIQUE_PATCHES_REMAINING = NO
```

The 004D continuation worktree was clean and its accepted Today content
matched the canonical reconciled files semantically. It has now been removed,
along with its disposable local branch, because the implementation and reports
are preserved in the canonical repository.

## Fixed status

```text
TODAY_004C_CANONICAL = YES
TODAY_004D_CANONICAL = YES
TODAY_004E_CANONICAL = YES
TODAY_WORKTREE_CLEANUP = COMPLETE
FINAL_STATUS = TODAY_EXISTING_WIRING_RECONCILED=YES
```
