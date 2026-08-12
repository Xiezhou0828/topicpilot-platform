# TASK-BE-024｜Opportunity Engine V1 Trend Continuation & Catch-up Strategies

Date: 2026-08-12
Generation: `NEXT / V2`
Execution mode: `SHADOW / CALIBRATION`; production activation is not authorized.

## Executive Summary

TASK-BE-024 adds the first multi-strategy layer above the existing canonical
OHLCV evidence builders and Opportunity Shadow Composer. `TREND_CONTINUATION`
and `CATCH_UP` are deterministic, independently ranked, provider-neutral shadow
strategies. `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` are explicit future
strategy identifiers and return `FUTURE_NOT_IMPLEMENTED`.

The implementation consumes explicit Theme Context, stock identity/effective
membership, data-quality/no-trade facts, canonical daily OHLCV, and topic return
evidence. It preserves the PM product boundary: no Buy/Sell instruction, no
black-box AI confidence, no Topic Score feedback, no global cross-strategy
winner, and no production API/database/frontend/scheduler activation.

## Existing Opportunity / Recommendation Audit

| Existing area | Finding | Reconciliation |
|---|---|---|
| `opportunity_shadow.py` | Pure shadow Composer over explicit facts | `KEEP / REUSE`; strategy layer supplies facts |
| `opportunity_evidence.py` | Canonical daily OHLCV builders | `KEEP / REUSE` |
| `recommendation.py` and Recommendation API | Downstream read-only Topic Intelligence projection | `KEEP`; no API change |
| Legacy `StrategyRun/Candidate/Performance` models | Tables constrained to `MAS/MAV/TMC/BB/PB/KD` | `HISTORICAL_ONLY / ADAPT LATER` |
| `snapshot.py`, `repository.py`, `home_read_model.py` | Legacy/public strategy candidate projections | `ADAPT LATER`; untouched here |
| `schemas.py` Home opportunity/candidate shapes | Existing compatibility read model | `ADAPT LATER`; no contract change |
| `detectors/range_detector.py` | Generic support/resistance primitive | `REUSE/ADAPT`; evidence builder remains authority |
| V1 tools and old reports | Legacy formulas and magic-number examples | `HISTORICAL_ONLY`; no values promoted |
| Topic Engine scoring modules | Topic Strength/Grade/Confidence boundary | `KEEP`; consumed, never recalculated |

No approved existing V2 Trend/Catch-up strategy contract was found. The new
module is additive and remains shadow-only.

## Architecture Reconciliation

```text
Theme Context → Eligibility → Exclusion / Risk → Evidence
             → Strategy-specific Ranking → Opportunity Strategy Result
```

`ThemeContext` consumes topic Grade, Lifecycle, Topic Strength, snapshot/as-of,
strength evidence, topic returns, and no-trade context. `StrategyStockContext`
consumes identity, effective membership, canonical bars, liquidity/no-trade
facts, role, and relative-gap history. `OpportunityPolicy` centralizes policy
version, allowed Grade/Lifecycle values, windows, thresholds, and ranking
weights, all labelled `PROVISIONAL / TUNABLE`.

The existing technical module remains the calculation authority for daily OHLCV
facts. Each strategy builds stages for Theme Context, data quality,
eligibility, exclusion, and strategy evidence. Missing required context returns
`DEFERRED / UNKNOWN`; hard exclusions return `EXCLUDED / FAIL`. Positive
evidence never overrides a confirmed breakdown, below-20MA condition, formal
no-trade, or invalid/insufficient data.

## Trend Continuation

`TREND_CONTINUATION` requires a policy-eligible topic and a stock with accepted
and sufficient daily history, price at or above the required 20MA structure,
rising MA direction, relative stock-vs-topic performance meeting the configured
window/minimum, price/volume evidence, and no structural breakdown.

Recent return, extension distance, support/entry context, volume behavior, and
volatility remain evidence/ranking context. They do not bypass hard gates.

## Catch-up Opportunity

`CATCH_UP` requires an eligible Theme Context, relative lag within a configured
window, healthy trend structure, no structural weakness, relative-strength
stabilization/improvement over the inflection lookback, and volume activation.

`LAGGING` is not equivalent to `WEAK`. Lag outside the window, persistent RS
deterioration, price below 20MA, breakdown, abnormal drawdown,
volume-supported selloff, no-trade, or formal data failure excludes or defers
the candidate. Volume activation alone cannot create a Catch-up result.

## Theme Context and Lifecycle Integration

Grade, Lifecycle, Topic Strength, snapshot identity, and effective membership
are upstream facts. The strategy layer does not calculate Grade, Lifecycle, or
Strength and does not alter Topic Score. Starting allowed Grade/Lifecycle sets
are policy defaults only, not PM-frozen thresholds. Missing context defers
evaluation rather than inventing a grade, zero score, or pass.

## Ranking, Confidence, and Explainability

Trend and Catch-up are ranked independently. `rank_strategy_results()` rejects
mixed strategy lists, and the engine serializes
`globalCrossStrategyRanking = null`. An internal rank score is an explainable
calibration artifact built from policy-provided component weights; it is not a
customer recommendation score. Confidence is a separate `HIGH / MEDIUM / LOW`
evidence-coverage label and is not a probability.

Each result retains strategy id, policy version, as-of date, stage assessments,
positive/negative evidence, exclusion codes, rank availability, confidence
basis, and deterministic reasons such as `TREND_STRUCTURE_HEALTHY`,
`RELATIVE_STRENGTH_POSITIVE`, `CATCHUP_LAG_IN_WINDOW`,
`CATCHUP_RS_IMPROVING`, `PRICE_NOT_ABOVE_20MA`, and `STRUCTURAL_BREAKDOWN`.

## Versioned Policy

The policy identifier is `topic-opportunity-policy.provisional.1`. It contains
strategy-specific allowed Grade/Lifecycle sets, relative-strength windows and
minimums, Catch-up lag/inflection windows, recent-return and extension context,
volume activation, ranking weights, and the nested canonical technical policy.
Every numeric and vocabulary default is `PROVISIONAL / TUNABLE`; legacy
`MAS/MAV/TMC/BB/PB/KD` values and old score examples are not copied into it.

## Persistence Boundary

No persistence implementation was added. Existing StrategyRun,
StrategyCandidate, and StrategyPerformance tables remain historical/read-model
compatibility structures and are not reused as an implicit Opportunity schema.
Future persistence requires a separate schema/API work order with strategy,
topic/instrument, as-of, eligibility/exclusion/evidence, rank, confidence,
policy, and calculation lineage.

## Deterministic Replay and PM Calibration

`replay_opportunity_strategies()` evaluates explicit `StrategyReplayCase` values
at sorted evaluation dates and filters every bar to `trading_date <= as_of`.
`StrategyReplayResult` exposes the no-look-ahead assertion and remains
`SHADOW_ONLY`. `build_pm_calibration_report()` emits date, topic, instrument,
strategy, Grade, Lifecycle, eligibility, exclusions, relative performance, rank
score, confidence, and reason codes for PM review. It does not calculate P&L,
outcome metrics, notifications, or production performance.

## Architecture Labels

- **KEEP:** canonical Topic/Stock identity, effective membership, daily OHLCV,
  Topic Snapshot/Grade/Lifecycle upstream context, structured evidence, and
  read-only API boundaries.
- **REUSE:** technical evidence builders, `Evidence`/`StageAssessment`,
  no-look-ahead replay, and status-first/evidence-first presentation.
- **ADAPT:** legacy candidate/support/trigger/invalidation fields and internal
  ranking metadata through a future explicit shadow/read adapter.
- **DEPRECATE_LATER:** legacy Recommendation terminology when a governed
  Opportunity read contract exists.
- **HISTORICAL_ONLY:** V1 `MAS/MAV/TMC/BB/PB/KD`, old Recommendation Score/rank
  examples, `補漲候選` formulas, private/demo snapshots, and legacy magic numbers.

## Tests and Validation

Added `services/api/tests/test_opportunity_strategies.py` with 20 tests for the
versioned policy, Trend positive/exclusion paths, missing Theme deferral,
Catch-up lag and RS inflection, independent ranking, future strategies,
no-look-ahead replay including future Theme snapshot deferral, and PM calibration output. Existing Composer/evidence
tests remain unchanged and passing.

Validation performed:

- focused strategy tests: **10 passed**;
- full V2 API suite after implementation: **291 passed, 31 skipped, 1 existing warning**;
- Ruff check/format for new strategy module, exports, and focused tests: **passed**;
- replay assertions verify all visible bars satisfy `trading_date <= as_of`;
- no API, DB/schema/migration, frontend, scheduler, deployment, V1 source, or
  NEXT_TASK change.

Formal PostgreSQL history was not available in the local runtime, so tests use
explicit canonical-shaped deterministic fixtures. No production-data result is
claimed.

## Files Modified / Created

- Created `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py`.
- Created `services/api/tests/test_opportunity_strategies.py`.
- Modified `services/api/src/topicpilot_api/topic_engine/__init__.py` exports.
- Modified `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md`.
- Modified `docs/product/TOPICPILOT_PRODUCT_DECISIONS.md` with the shadow-only V1 strategy decision.
- Modified `docs/product/TOPICPILOT_PRODUCT_IDEAS.md`.
- Modified `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`.
- Modified `docs/DAILY_PROGRESS.md`.
- Created this report.

## Production Actions Not Performed

No API route/response, PostgreSQL schema or data, migration, frontend,
scheduler, deployment, notification, favorite, broker/order, trading,
Topic Score, Grade, Lifecycle, Leader Set, global ranking, or production
Opportunity activation was changed. No destructive migration, Neon reset,
V1 read, or V1/V2 cutover was performed.

## Final Acceptance Matrix

```text
OPPORTUNITY_PRODUCT_DIRECTION = FROZEN
MULTI_STRATEGY_ARCHITECTURE = PASS
TREND_CONTINUATION = PASS
CATCH_UP = PASS
EARLY_STRENGTH = FUTURE_NOT_IMPLEMENTED
PULLBACK_ACCEPTANCE = FUTURE_NOT_IMPLEMENTED
THEME_CONTEXT_INTEGRATION = PASS
LIFECYCLE_INTEGRATION = PASS / UPSTREAM CONSUMED, NOT RECALCULATED
DAILY_OHLCV_FEATURES = PASS
RISK_EXCLUSION = PASS
RELATIVE_STRENGTH = PASS
CATCH_UP_INFLECTION = PASS
VERSIONED_POLICY = PASS
EXPLAINABILITY = PASS
DETERMINISTIC_REPLAY = PASS
PM_CALIBRATION_OUTPUT = PASS
PRODUCT_IDEAS_UPDATED = YES
ROADMAP_UPDATED = YES
C_D_IMPLEMENTED = NO
OPPORTUNITY_PRODUCTION_ACTIVATION = NO
NEXT_TASK_MODIFIED = NO
```

## Suggested Next Step

When separately authorized canonical history and Theme Context are available,
run a bounded A/B shadow replay and PM calibration review. Do not freeze
thresholds, persist Opportunity lifecycle, expose an API, or activate
production behavior until PM/data-owner approvals and freshness/no-trade gates
are complete.
