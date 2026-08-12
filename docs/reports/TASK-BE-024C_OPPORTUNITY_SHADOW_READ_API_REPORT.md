# TASK-BE-024C — Opportunity Shadow Read API & Frontend Adapter V1

**Status:** `COMPLETE / SHADOW ONLY`
**Date:** 2026-08-12
**Production activation:** `NO`

## Executive Summary

TASK-BE-024C adds the first integration seam for the BE-024/024A/024B
Opportunity contracts: a provider-neutral, persistence-free
`OpportunityShadowReadService`, four read-only shadow routes, deterministic
synthetic fixtures, and a frontend adapter. It does not activate a production
Recommendation API, write a database row, calculate historical performance,
or let the browser infer business semantics.

## Existing Architecture Audit

The existing architecture was read before changes: BE-024 strategy evaluators
produce independent Trend/Catch-up results; BE-024A supplies decision,
explainability, read, and calibration-placeholder contracts; BE-024B supplies
the S/A/B/D qualification matrix, B exception provenance, risk-before-ranking,
20MA gate, strategy-local caps, and versioned provisional parameters. The
legacy `/api/v1/recommendations/latest` route remains fail-closed and was not
repurposed. Existing Topic, Stock, Home, Stock Encyclopedia, and legacy
Recommendation surfaces remain compatible.

## Shadow Read Architecture

```text
Topic/Strategy Evidence -> Qualification -> Risk -> Strategy-local Ranking
  -> Decision -> Explainability -> OpportunityReadModel
  -> OpportunityShadowReadService -> Shadow API -> Frontend Adapter -> UI
```

`OpportunityReadProvider` is the seam. `FixtureOpportunityReadProvider` is
deterministic and synthetic; `CanonicalOpportunityReadProvider` is an explicit
unavailable placeholder for future canonical production data. Neither path
writes production persistence.

## API Contract

Contract version: `opportunity-shadow-read.v1`. Routes:

- `GET /api/v1/opportunities/shadow`
- `GET /api/v1/topics/{topic_id}/opportunities/shadow`
- `GET /api/v1/stocks/{instrument_id}/opportunities/shadow`
- `GET /api/v1/opportunities/shadow/{opportunity_id}`

Supported filters are strategy, state, topicId, instrumentId, grade, and
lifecycle. No minimum-score, buy, expected-return, target-price, or stop-loss
query is accepted. Responses expose `publicationStatus=SHADOW`, synthetic
data status, as-of, query, structured projections, and explicit status
semantics: `READY`, `EMPTY`, `DEFERRED`, or provider `UNAVAILABLE`.

## Topic Projection

Topic responses include both nested and flattened topic identity, Grade,
Lifecycle, strength, and strategy sections. Each section reports backend
candidate count, presented count, presentation cap, compact full backend
ranking metadata, backend-provided display order, and whether the full ranking
is retained. Known empty topics return `EMPTY` with Grade/Lifecycle context;
unknown topics remain a not-found boundary.

## Stock Projection

Stock responses group the same Opportunity contract by instrument identity and
retain strategy-local Trend/Catch-up sections. No stock-level business state is
re-derived in the route or adapter.

## Opportunity Detail Projection

Detail responses provide deterministic opportunity id/key, topic and instrument
identity, strategy, state, eligibility/status, qualification class and
provenance, display/label keys and reason codes, rank metadata, entry/support/
risk context, positive/waiting/risk/exclusion factors, invalidation and
data-quality/evidence coverage context, as-of, publication and data status,
and policy/parameter/ranking-profile versions.

## Explainability Mapping

The projection preserves `OpportunityExplanation` groups and display keys:
positive, waiting, risk, exclusion, entry, invalidation, data quality, and
confidence basis. Explanation is structured evidence authored by the backend;
an eventual LLM may verbalize it but cannot decide state, gate, risk, or rank.

## Fixture Provider

Fixtures are deterministic synthetic examples with `dataStatus=FIXTURE` and
`publicationStatus=SHADOW`. Both Trend and Catch-up cover SELECTED,
WAITING_RETEST, WAITING_CONFIRMATION, DEFERRED, and EXCLUDED, plus a Grade-B
`EXCEPTION_CANDIDATE` warming case, Mature context, Declining/D exclusion,
known empty topic/stock fixtures, and one stock appearing across multiple
topics/strategies.
Fixtures contain no win rate, expected return, target, stop-loss, or historical
performance and are not valid calibration input.

## Frontend Adapter

`apps/web/app/lib/opportunity-shadow-adapter.ts` maps the response to
`OpportunityPageModel` with topic sections plus Trend/Catch-up sections. It only groups sections, preserves backend fields,
sorts by backend `displayOrder`, and maps status to
`LOADING/READY/EMPTY/DEFERRED/UNAVAILABLE/ERROR`. It does not calculate
eligibility, state, risk, score, rank, technical classification, or exception
qualification. The UI remains on the Market -> Topic -> Stock Encyclopedia ->
Opportunity path and uses the existing Modern Financial Workspace,
warm-neutral, dense editorial style.

## UI State Semantics

`LOADING` is transport/request pending; `READY` has usable backend rows;
`EMPTY` is a valid filter result with no rows; `DEFERRED` means the backend
has rows but evidence is incomplete; `UNAVAILABLE` is a missing provider/data
source; `ERROR` is transport or contract failure. The adapter does not turn
one state into another from raw fields.

## A Top3/B Top2 Contract

Trend Continuation is capped at three presented cards and Catch-up at two.
`candidateCount` and `fullRankingRetained=true` preserve the complete
strategy-local backend ranking beyond the presentation cap. A/B are never
globally merged into one winner.

## B Exception Contract

Grade B is not silently promoted to the formal universe. The fixture and
projection carry `EXCEPTION_CANDIDATE`, `exceptionCandidate=true`, explicit
reason codes (including warming provenance), qualification policy version, and
parameter version. Exception status does not bypass eligibility, risk, or
entry checks.

## Compatibility

The old Recommendation route remains fail-closed and unchanged. Existing
BE-024/024A/024B contracts, topic/stock/home read models, and legacy
Recommendation terminology remain available as historical/provisional
context. The new surface is additive and shadow-only.

## Tests

- Backend focused shadow/API tests: `11 passed`; combined with the existing
  Opportunity contract tests, the focused run is `19 passed`.
- Full backend regression: `362 passed, 31 skipped, 1 pre-existing warning`.
- Targeted Ruff: `PASS`.
- Frontend adapter tests: `2 passed`.
- Frontend lint: `PASS` with one pre-existing unused-variable warning in
  `TopicDetailPage.tsx`.
- Frontend TypeScript: `PASS` (`npx tsc --noEmit`). Two small pre-existing
  `TopicListPage.tsx` compatibility defects were corrected so the gate could
  run; no adapter error remains.
- Frontend build: `PASS` (`npm run build`). The focused adapter test is green;
  the broader legacy source-contract suite remains `59 passed / 13 failed`
  on pre-existing Home/Topic wrapper assertions outside this task.

## Files Changed

- `services/api/src/topicpilot_api/opportunity_shadow_read.py`
- `services/api/src/topicpilot_api/opportunity_shadow_api.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/src/topicpilot_api/main.py`
- `services/api/tests/test_opportunity_shadow_read_api.py`
- `apps/web/app/lib/opportunity-shadow-adapter.ts`
- `apps/web/tests/opportunity-shadow-adapter.test.mjs`
- `apps/web/app/components/v2/TopicListPage.tsx` (pre-existing lifecycle
  type/preview compatibility correction needed for the TypeScript gate; no
  Opportunity UI was added)
- `docs/api/opportunity-shadow-read-v1.md`
- `docs/architecture/decisions/OPPORTUNITY_SHADOW_READ_API_V1.md`
- Product, architecture, roadmap, worklog, daily-progress documents listed in
  the handoff below.

## Documentation Updated

Updated `TOPICPILOT_PRODUCT_IDEAS.md`,
`TOPICPILOT_PRODUCT_DECISIONS.md` (PD-016),
`TOPICPILOT_PRODUCT_ROADMAP.md`,
`TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`, `docs/ROADMAP.md`,
`docs/DAILY_PROGRESS.md`, and `docs/AI_WORKLOG.md`.

## Production Actions NOT Performed

No production API activation, DB write, migration, scheduler change, daily
market pipeline change, production data publication, historical replay,
calibration, ranking-weight optimization, or frontend UI implementation was
performed. `AI/NEXT_TASK.md` was not modified.

## Remaining Production Data Dependencies

Completion of a production-backed read surface still requires an approved
canonical provider, point-in-time Topic Grade/Lifecycle, canonical daily
OHLCV/technical evidence, instrument/topic identity binding, data freshness
and availability semantics, and a publication/activation decision. None is
substituted by synthetic fixtures.

## Historical Replay Handoff

Future replay requires canonical production daily OHLCV, point-in-time topic
snapshot and selection timestamp, opportunity state at selection, lifecycle and
Grade at selection, ranking-profile version, policy version, and parameter
version. Fixtures and synthetic data must remain excluded from calibration;
no-look-ahead and forward 1/3/5/10-day outcome evaluation remain future work.

## Suggested Next Step

PM should approve a canonical production `OpportunityReadProvider` contract
and its freshness/publication gates. Only after that approval should a separate
work order wire a production adapter and evaluate point-in-time replay; this
task's shadow surface should remain unchanged.

## Fixed Outputs

```text
TASK_BE_024C_STATUS = COMPLETE
SHADOW_READ_SERVICE = PASS
SHADOW_API = PASS
TOPIC_PROJECTION = PASS
STOCK_PROJECTION = PASS
OPPORTUNITY_DETAIL = PASS
EXPLAINABILITY = PASS
FIXTURE_PROVIDER = PASS
FRONTEND_ADAPTER = PASS
UI_STATE_CONTRACT = PASS
TREND_PRESENTATION_CAP = TOP_3
CATCHUP_PRESENTATION_CAP = TOP_2
FULL_BACKEND_RANKING_RETAINED = YES
A_B_GLOBAL_RANKING = DISABLED
B_EXCEPTION_PROVENANCE = PASS
POLICY_VERSION_EXPOSED = YES
PARAMETER_VERSION_EXPOSED = YES
RANKING_PROFILE_VERSION_EXPOSED = YES
PUBLICATION_STATUS = SHADOW
PRODUCTION_DATA_REQUIRED_TO_COMPLETE = NO
HISTORICAL_REPLAY_PERFORMED = NO
CALIBRATION_PERFORMED = NO
PRODUCTION_DB_WRITE = NO
MIGRATION = NO
SCHEDULER_CHANGED = NO
DAILY_MARKET_CHANGED = NO
NEXT_TASK_MODIFIED = NO
BACKEND_TESTS = PASS (11 new focused tests; 19 combined focused tests; 362 full-suite passed, 31 skipped)
FRONTEND_TESTS = PASS (2 focused adapter tests; legacy suite 59 passed / 13 pre-existing failures)
RUFF = PASS (targeted)
TYPECHECK = PASS
BUILD = PASS
```
