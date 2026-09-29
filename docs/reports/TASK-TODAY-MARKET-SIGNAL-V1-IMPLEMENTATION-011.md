# TASK-TODAY-MARKET-SIGNAL-V1-IMPLEMENTATION-011

## Scope and terminal state

This candidate implements the frozen Today Market Signal V1 Product Grill.
It does not merge `main`, deploy, publish Web, activate Production, mutate
Production data, or apply a migration.

The canonical base was fetched and recorded as
`ec46db023c8e701044e162dcf723f362002b88d7` at the beginning of this task.
`origin/main` subsequently advanced to `6cb88c0d7fceb45b244d295883636706f50ea0be`
while concurrent repository work continued; this candidate remains anchored to
the captured base and was not rebased or merged into that later remote state.

The implementation candidate commit is
`65eb36553849ccaa4d9fc5ae85ab04b7a25f5d08`; this report finalization is an
additive governance follow-up commit on the same candidate branch.

## Existing signal audit

The four signals present at the captured base were reconciled as follows:

| Existing signal | V1 disposition |
| --- | --- |
| `INDEX_DIVERGENCE` | `KEEP_WITH_SEMANTIC_UPDATE` → `INDEX_MARKET_DIVERGENCE` (`雙盤分家`) with opposite-sign or 1.0pp spread semantics |
| `OTC_VOLUME_PRICE_DIVERGENCE` | `REMOVE_FROM_V1`; it is not present in the executable catalog or active payload |
| `INSTITUTION_PRICE_DIVERGENCE` | `SUPERSEDED` by the frozen institutional structure signals; no price-only institutional signal remains |
| `BREADTH_DIVERGENCE` | `KEEP_WITH_SEMANTIC_UPDATE` → `BREADTH_RED_INDEX_DISCONNECT` (`紅盤失隊`) with TPE +0.3% and positive breadth ≤40% |

The historical Design-010 recommendation count was 12. The Product Grill
explicitly expanded and froze V1 at 16 by adding formal Topic breadth
structure and reconciling institutional structure.

## Implemented contract

- `services/api/src/topicpilot_api/market_signals.py` is the single executable
  evaluator and stable catalog authority.
- The frozen catalog contains 16 signals in family/catalog order:
  `INDEX_STRUCTURE` (3), `MARKET_BREADTH` (5),
  `TOPIC_BREADTH_STRUCTURE` (3), `MARKET_PARTICIPATION` (2), and
  `INSTITUTIONAL_STRUCTURE` (3).
- Every record is explicitly `ACTIVE`, `INACTIVE`, or `NOT_EVALUABLE`.
  Missing formal facts never become a silent false result.
- Index precedence is divergence → both strong → both weak.
- Breadth uses the existing formal whole-market TWSE + TPEx denominator and
  allows the specified overlap cases.
- Topic signals use dynamically selected formal Topic snapshots and formal CORE
  member facts. Topics with fewer than three formal members are excluded, and
  fewer than five evaluable Topics yields `NOT_EVALUABLE`. Daily Grade,
  Lifecycle, and Topic Score are not signal inputs.
- Participation uses formal whole-market turnover, requiring formal TPE and
  TPEx legs plus TOTAL, with the previous 20 governed-session median excluding
  the current session.
- Institutional signals use same-date official TWSE + TPEx rows and whole-market
  turnover ratios. Dealer data is not a required trigger.

Temporal state and frequency are backend-owned. `NEW`, `PERSISTING`, streaks,
20 governed-session occurrence, insufficient-history handling, and all 16
signal-specific deterministic frequency templates are included in the payload.

## API and UI

`HomeMarketSignal` was extended additively and the OpenAPI/generated client
artifacts were regenerated. The Today page renders all backend-active signals,
shows at most five cards per group, exposes labelled Previous/Next controls and
visible/total pagination state, and has no automatic carousel. Market Overview
remains the first Today section. The browser does not recalculate thresholds,
temporal state, frequency bands, Topic structure, turnover, or institutional
ratios.

## Validation evidence

| Check | Result |
| --- | --- |
| Focused backend signal/Home tests | PASS; 21 passed |
| Temporal, Topic, institutional, turnover, and frequency boundary tests | PASS; included in focused suite |
| Broader backend suite | PASS; 723 passed, 4 skipped, 146 deselected |
| Frontend full test suite | PASS; 181 passed |
| Generated API client tests | PASS; 4 passed |
| Ruff | PASS |
| Frontend lint | PASS; one pre-existing `FavoriteButton.tsx` hook warning, no errors |
| Frontend production build | PASS |
| OpenAPI drift | PASS; schema valid and required read-only routes present |
| Alembic migration graph | PASS; 47 revisions, 1 head (`0046_task_stock_maint_relation_weight_authority_001d`) |
| Diff/whitespace check | PASS; only the repository's existing OpenAPI line-ending warning was reported |

The four skipped backend tests are environment-gated PostgreSQL integrations
requiring `TOPICPILOT_INGEST_TEST_DATABASE_URL`, `TEST_DATABASE_URL`, or
`DATABASE_URL`; no failure was hidden by the task-specific tests.

## Migration and Production boundary

No new persistent schema is required. Existing Home publication history, formal
Topic snapshot/member facts, formal turnover, and institutional-flow tables are
used. No migration was created or applied. No Production database, API, Worker,
Web deployment, scheduler, or post-close process was touched.

Thresholds are `OWNER_SEEDED_V1_PRODUCT_THRESHOLDS`. Historical calibration and
statistical optimization were not performed.

## Required final status

```text
TASK_ID=TASK-TODAY-MARKET-SIGNAL-V1-IMPLEMENTATION-011
TASK_STATUS=COMPLETE_TODAY_MARKET_SIGNAL_V1_IMPLEMENTATION_CANDIDATE_READY

CANONICAL_BASE_SHA=ec46db023c8e701044e162dcf723f362002b88d7
CANDIDATE_SHA=65eb36553849ccaa4d9fc5ae85ab04b7a25f5d08
REMOTE_BRANCH=codex/today-market-signal-v1-implementation-011
PUSH_STATUS=PASS

OLD_V1_RECOMMENDED_SIGNAL_COUNT=12
FROZEN_V1_SIGNAL_COUNT=16

INDEX_STRUCTURE_STATUS=YES
MARKET_BREADTH_STATUS=YES
TOPIC_BREADTH_STRUCTURE_STATUS=YES
MARKET_PARTICIPATION_STATUS=YES
INSTITUTIONAL_STRUCTURE_STATUS=YES

TEMPORAL_STATE_STATUS=YES
STREAK_STATUS=YES
OCCURRENCE_20D_STATUS=YES
FREQUENCY_MESSAGE_STATUS=YES

SIGNAL_HISTORY_AUTHORITY=EXISTING_PUBLISHED_HOME_PUBLICATIONS_PLUS_FORMAL_TOPIC_AND_INSTITUTIONAL_HISTORY
TOPIC_AUTHORITY_STATUS=FORMAL_DYNAMIC_TOPIC_SNAPSHOTS_AND_CORE_MEMBER_FACTS
TURNOVER_AUTHORITY_STATUS=FORMAL_TWSE_PLUS_TPEX_WHOLE_MARKET_TURNOVER
INSTITUTIONAL_AUTHORITY_STATUS=OFFICIAL_SAME_DATE_TWSE_PLUS_TPEX_FLOW_TABLE

LEGACY_SIGNAL_DISPOSITION=OTC_VOLUME_PRICE_DIVERGENCE_REMOVE_FROM_V1; OTHER_THREE_RECONCILED_INTO_FROZEN_CATALOG

BACKEND_FORMAL_AUTHORITY=YES
FRONTEND_REDERIVES_BUSINESS_LOGIC=NO

OVER_5_SIGNAL_NAVIGATION_STATUS=YES
FIRST_VIEWPORT_CONTRACT_PRESERVED=YES

FOCUSED_BACKEND_TEST_STATUS=PASS
TEMPORAL_TEST_STATUS=PASS
TOPIC_SIGNAL_TEST_STATUS=PASS
INSTITUTIONAL_TEST_STATUS=PASS
FRONTEND_TEST_STATUS=PASS
BROADER_BACKEND_TEST_STATUS=PASS
RUFF_STATUS=PASS
LINT_STATUS=PASS_WITH_PREEXISTING_WARNING_ONLY
BUILD_STATUS=PASS
OPENAPI_STATUS=PASS
MIGRATION_GRAPH_STATUS=PASS
DIFF_CHECK_STATUS=PASS

MIGRATION_REQUIRED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO

PRODUCT_THRESHOLDS=OWNER_SEEDED_V1_PRODUCT_THRESHOLDS
HISTORICAL_CALIBRATION=NOT_PERFORMED
STATISTICAL_OPTIMIZATION=NOT_PERFORMED

PR_CREATED=NO
MERGED=NO
DEPLOYED=NO
PRODUCTION_DB_MUTATED=NO
PRODUCTION_ACTIVE=NO

OWNER_DECISIONS_REQUIRED=NONE_FOR_IMPLEMENTATION; CANONICAL_PROMOTION_IS_SEPARATE
KNOWN_LIMITATIONS=PRODUCTION_OR_FORMAL_FIXTURE_DATA_MAY_RETURN_NOT_EVALUABLE_UNTIL_COMPLETE_20_SESSION_HISTORY_AND_REQUIRED_TOPIC_TURNOVER_INSTITUTIONAL_FACTS_EXIST; PRODUCTION_VERIFICATION_NOT_RUN

ARTIFACTS=services/api/src/topicpilot_api/market_signals.py; services/api/src/topicpilot_api/home_v2_publication.py; services/api/src/topicpilot_api/schemas.py; services/api/tests/test_market_signals_v1.py; apps/web/app/components/v2/TodayMarketPage.tsx; apps/web/tests/today-market-signals.test.mjs; docs/architecture/TODAY_MARKET_SIGNAL_V1_CONTRACT.md; docs/architecture/TODAY_MARKET_SIGNAL_V1_CATALOG.json; packages/api-client/openapi.json; packages/api-client/src/schema.d.ts

TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=TASK-TODAY-MARKET-SIGNAL-V1-CANONICAL-PROMOTION-012
```

The unrelated pre-existing untracked report
`docs/reports/TASK-GOV-COMPLETED-CANDIDATE-REMOTE-PRESERVATION-001.md` was
preserved and is intentionally not part of this candidate commit.
