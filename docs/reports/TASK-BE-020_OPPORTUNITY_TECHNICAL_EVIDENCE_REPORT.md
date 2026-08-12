# TASK-BE-020｜Opportunity Technical Evidence & Entry Quality V1

Date: 2026-08-12
Scope: shadow-only evidence calculation and historical replay; no production activation.

## Executive Summary

TASK-BE-020 establishes a deterministic, provider-neutral upstream evidence layer for the existing Opportunity Shadow Composer. Accepted canonical `DAILY_BAR` OHLCV is transformed into sufficiency, MA20/MA60, MA direction, price-volume, breakout/retest, support, Entry Quality, weak-candle, bearish-break, and Risk Gate facts. `OpportunityShadowInputBuilder` composes those facts into the existing `opportunity_shadow.py` input contract; the Composer remains responsible only for composition and structured shadow output.

The implementation is intentionally versioned and provisional. Numeric policy parameters are centralized in `OpportunityEvidencePolicy` and labelled `PROVISIONAL / TUNABLE`; no PM threshold, weight, candidate cap, validity period, or state-transition rule was frozen.

## Files Modified

- `services/api/src/topicpilot_api/topic_engine/opportunity_evidence.py` — new pure evidence builders, canonical OHLCV contract, input builder, and in-memory replay.
- `services/api/src/topicpilot_api/topic_engine/opportunity_shadow.py` — minimal compatibility extension: optional calculated evidence on `TechnicalStructureFacts`; existing Composer flow preserved.
- `services/api/src/topicpilot_api/topic_engine/__init__.py` — exports the evidence-layer contracts/functions.
- `services/api/tests/test_opportunity_evidence.py` — 9 focused tests.
- `services/api/tests/test_opportunity_shadow.py` — existing 10 shadow Composer tests remain passing.
- `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md` — Technical Evidence Layer, Composer/calculator separation, canonical/as-of/no-look-ahead rules.
- `docs/product/TOPICPILOT_PRODUCT_DECISIONS.md` — PM-frozen architecture decisions for canonical OHLCV, no-look-ahead/missing semantics, builder separation, and non-primary chip confirmation.
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` — evidence-first/status-first Opportunity presentation boundary; no black-box score UI or browser inference.
- `AI/AI_WORKLOG.md` — TASK-BE-020 handoff, verification, no-runtime-change statement, and open PM decisions.
- `docs/reports/TASK-BE-020_OPPORTUNITY_TECHNICAL_EVIDENCE_REPORT.md` — this report.

No `AI/NEXT_TASK.md` change was made.

## Existing Recommendation Concepts Found

The repository contains earlier V1 and V2 concepts including `RecommendationCandidateFact`, recommendation read models, `strategy candidate`, `補漲候選`, `題材 × 技術面綜合分數`, and legacy technical helpers in `tools/entry_setup_engine.py`, `tools/daily_observation_engine.py`, and related V1 reports. Those materials include historical numeric examples and/or V1 production boundaries. They were audited for terminology and explicitly not reused as the V2 Opportunity evidence authority. Existing Recommendation read APIs remain infrastructure/read-model history, not proof that this shadow policy is production-approved.

## Decisions Consolidated

1. The canonical upstream is accepted `PRICE` + `VOLUME` daily-bar data represented as canonical OHLCV; frontend/mock/synthetic/future full-history data is not an evidence source.
2. All calculations are as-of bounded and use trading observations; a missing value is unavailable/unknown, never zero or a pass.
3. Technical, Risk, Entry Quality, and input builders calculate structured facts; `opportunity_shadow.py` is the Composer and remains side-effect free.
4. Chip/institution evidence is optional confirmation, not a primary gate. Without a formal fresh input it is `UNKNOWN`.
5. Shadow replay is in-memory/report/test only and does not persist lifecycle, P&L, positions, orders, notifications, or production evaluation.

## New Opportunity Engine Architecture

```text
Canonical accepted DAILY_BAR OHLCV
  → OHLCV Sufficiency Evidence
  → MA20 / MA60 / MA Direction Evidence
  → Price/Volume Structure Evidence
  → Breakout + Retest Evidence
  → Support Candidate[] + deterministic Primary Support
  → Entry Quality (PASS / WAIT / UNKNOWN)
  → Bearish Break + Weak Candle Evidence
  → Risk Gate (PASS / FAIL / UNKNOWN)
  → OpportunityShadowInputBuilder
  → existing Composer
  → Structured Opportunity Shadow result
```

The builder exposes both functional entry points and a small `TechnicalEvidenceBuilder` wrapper for dependency injection. `HistoricalShadowReplayResult` contains date-bounded observations and a no-look-ahead flag; it deliberately does not calculate outcome/P&L.

## FROZEN vs OPEN Decision Matrix

| Area | Current decision | Status |
|---|---|---|
| Canonical accepted daily OHLCV input | Required upstream authority | FROZEN architecture |
| Trading-date/as-of and no look-ahead | Only `trading_date <= as_of` | FROZEN architecture |
| Missing data | unavailable/unknown, never zero/pass | FROZEN architecture |
| Builder/Composer separation | builders calculate, Composer composes | FROZEN architecture |
| Chip confirmation role | non-primary, optional confirmation | FROZEN role |
| OHLCV minimum and MA windows | policy defaults only | OPEN / NOT PM-FROZEN |
| Breakout/retest/price-volume definitions | policy defaults only | OPEN / NOT PM-FROZEN |
| Support distance and invalidation | policy defaults only | OPEN / NOT PM-FROZEN |
| Risk cooldown days | not defined | OPEN / NOT PM-FROZEN |
| Topic/Technical/Entry/Chip weights | not defined | OPEN / NOT PM-FROZEN |
| Candidate cap, validity, intraday reorder | not defined | OPEN / NOT PM-FROZEN |
| Exception upgrade and state transitions | not defined | OPEN / NOT PM-FROZEN |

`OpportunityEvidencePolicy` is versioned, but its numeric parameters are explicitly `PROVISIONAL_TUNABLE` and cannot be read as a product freeze.

## Conflict / Legacy Terminology Handling

Historical `推薦分數`, `Recommendation Score (0–100)`, `補漲候選`, `strategy candidate`, and V1 technical formulas remain in their source documents for traceability. They are not deleted, but the Opportunity Engine specification and Product Decisions record the newer PM direction as current. The frontend may retain historical score availability as a backend dependency, but must not expose a false-precision score or convert legacy “candidate” wording into a current Opportunity state.

## Frontend Implications

The frontend consumes formal backend fields only. Future Opportunity cards/lists are status-first and evidence-first: topic identity, stock identity, current state, primary evidence, primary risk/limiter, freshness/as-of, and `查看機會`. The visual system remains Modern Financial Workspace / warm neutral / dense editorial. No stars, AI confidence, `87.4`, `強烈買入`, `賣出`, or browser-side derivation of state, risk, support, technical classification, leader, ranking, or transition is authorized. The existing `市場 → 題材 → 題材內股票 → Stock Encyclopedia → Opportunity / 查看機會` flow is preserved.

## Backend Implications

Canonical PostgreSQL/FastAPI remains the formal data authority, but this task adds no route, response, repository write, migration, scheduler, or production activation. The evidence module is pure and provider-neutral. Any future production integration must separately specify source/as-of lineage, freshness, policy approval, persistence, API schema, and lifecycle activation.

## Data Dependencies

- accepted canonical PRICE and VOLUME rows with `DAILY_BAR` semantics;
- market calendar/trading-day semantics and explicit as-of date;
- stock/topic identity and upstream topic qualification;
- future formal chip/institution adapter if confirmation is approved;
- versioned policy and evidence lineage;
- later persistence/history/outcome data for performance evaluation.

The local test suite did not have `TEST_DATABASE_URL`/`DATABASE_URL`, so PostgreSQL integration tests were skipped. No production canonical history was queried; real-data shadow examples are therefore not claimed.

## No-implementation Boundary

This task does not implement or activate Recommendation/Opportunity production behavior. It does not change API routes, API payloads, DB/schema/migrations, frontend components, scheduler, deployment, notifications, favorites, broker/trading, ranking weights, Top N, lifecycle persistence, or `AI/NEXT_TASK.md`. The presence of pure shadow builders and tests must not be interpreted as production activation.

## Verification

- Targeted Composer + evidence tests: **19 passed**.
- Full V2 API suite: **270 passed, 31 skipped, 1 existing Starlette/httpx deprecation warning**.
- Ruff check for evidence module, Composer, and topic-engine exports: **passed**.
- Replay test verifies every visible bar satisfies `trading_date <= evaluation_date` and future bars are excluded.
- Canonical bar contract rejects non-`DAILY_BAR`, non-`ACCEPTED`, invalid OHLC relationships, and non-finite values; missing OHLCV is preserved as missing.
- `AI/NEXT_TASK.md` timestamp/content was not changed.

## Remaining PM Decisions

The following remain `OPEN / NOT PM-FROZEN`: Topic Grade threshold; Lifecycle rule; whether 20MA is the sole mandatory gate; 60MA gate/bonus/evidence role; support-distance bands; Risk cooldown days; formal price-volume/pattern definitions; Topic Quality/Technical/Entry/Chip weights; same-topic maximum; recommendation validity; intraday reorder; Exception upgrade; institution/chip confirmation; and Opportunity transition thresholds/graph.

## Recommended Next Step

Run a separately authorized canonical PostgreSQL read-only shadow sample for a small, explicitly selected set of instruments and dates, then review evidence quality and provisional policy behavior with PM. Do not activate production state or freeze thresholds until that review and the required policy/data governance decisions are complete.

## Fixed Outputs

```text
OPPORTUNITY_SHADOW_COMPOSER = PRESERVED
TECHNICAL_EVIDENCE_BUILDER = IMPLEMENTED
OHLCV_SUFFICIENCY = IMPLEMENTED
MA20_EVIDENCE = IMPLEMENTED
MA60_EVIDENCE = IMPLEMENTED
MA_DIRECTION = IMPLEMENTED
PRICE_VOLUME_STRUCTURE = IMPLEMENTED
BREAKOUT_EVIDENCE = IMPLEMENTED
RETEST_EVIDENCE = IMPLEMENTED
SUPPORT_EVIDENCE = IMPLEMENTED
ENTRY_QUALITY = IMPLEMENTED
WEAK_CANDLE_EVIDENCE = IMPLEMENTED
BEARISH_BREAK_EVIDENCE = IMPLEMENTED
RISK_GATE_BUILDER = IMPLEMENTED
OPPORTUNITY_INPUT_BUILDER = IMPLEMENTED
HISTORICAL_SHADOW_REPLAY = IMPLEMENTED
NO_LOOKAHEAD_VERIFICATION = PASS
POLICY_VERSIONED = YES
POLICY_STATUS = PROVISIONAL
REAL_DATA_SHADOW_EXAMPLES = NO
PRODUCTION_API_CHANGE = NO
PRODUCTION_DB_CHANGE = NO
FRONTEND_CHANGE = NO
PRODUCTION_ACTIVATION = NO
LIFECYCLE_PRODUCTION_ACTIVATION = NO
RANKING_WEIGHTS_FROZEN = NO
ENTRY_DISTANCE_THRESHOLD_FROZEN = NO
NEXT_TASK_MODIFIED = NO
```
