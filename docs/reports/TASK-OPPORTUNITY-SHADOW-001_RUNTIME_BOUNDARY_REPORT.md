# TASK-OPPORTUNITY-SHADOW-001 — Shadow State and Structured Evidence Runtime Boundary

**Status:** `PASS / SHADOW-ONLY`
**Date:** 2026-08-12
**Generation:** `NEXT / V2`
**Scope:** pure in-process contract; no API, DB, migration, frontend, scheduler, deployment, or production activation

## Result

Added a deterministic, side-effect-free evaluator for the current Opportunity objective:

```text
Topic Context / Qualification
  → Stock Eligibility
  → Technical Structure
  → Risk Gate
  → Entry Quality
  → Opportunity Shadow State
  → Structured Evidence
```

The evaluator requires explicit topic, stock, technical, risk, entry, and chip facts. It does not discover candidates, calculate technical patterns, rank securities, or persist state.

## Implemented Boundary

- Formal stock identity is required.
- `sufficient_ohlcv` is an explicit fact and fails closed when false or unavailable.
- `20MA` is required for the shadow eligibility check.
- `price >= 20MA` is the only arithmetic hard-gate comparison in this slice.
- Technical structure preserves explicit facts for 20MA/60MA, MA direction, price/volume structure, breakout/retest, support, bearish break, and weak-candle structure.
- Risk Gate is caller-supplied and can block or defer evaluation.
- Entry Quality preserves support price and derives support distance when both prices are available; no distance threshold is invented.
- Chip confirmation is evidence-only and cannot block a selected shadow state.
- Shadow states are `升溫候選`、`轉強觀察`、`精選機會`、`等待回測`、`失效`.
- Evidence is grouped into why selected, confirmations, risks, and priority limiters, with observed/derived/unavailable kinds and JSON-safe serialization.

## Files

- `services/api/src/topicpilot_api/topic_engine/opportunity_shadow.py`
- `services/api/src/topicpilot_api/topic_engine/__init__.py`
- `services/api/tests/test_opportunity_shadow.py`
- `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md`
- `docs/reports/TASK-OPPORTUNITY-SHADOW-001_RUNTIME_BOUNDARY_REPORT.md`
- `AI/AI_WORKLOG.md`

## Verification

- Shadow tests: `10 passed`.
- Full V2 API test suite: `261 passed, 31 skipped, 1 warning`.
- Targeted Ruff check: passed.
- Targeted Ruff format check: passed.
- No runtime/API/DB integration was run because this slice deliberately has no external side effects or API wiring.

## Boundary and Open Decisions

This is not a production Recommendation/Opportunity engine. It does not freeze or implement Topic Grade/Lifecycle qualification, technical pattern definitions, 60MA gate/bonus semantics, support-distance thresholds, risk cooldown, weights, candidate caps, validity periods, intraday reorder behavior, chip thresholds, or state transition thresholds. Those remain `OPEN / NOT PM-FROZEN`.

```text
OPPORTUNITY_SHADOW_STATE = IMPLEMENTED
STRUCTURED_EVIDENCE = IMPLEMENTED
PRODUCTION_ACTIVATION = NO
API_OR_DB_CHANGE = NO
```
