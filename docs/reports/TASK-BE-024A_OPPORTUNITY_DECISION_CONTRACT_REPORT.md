# TASK-BE-024A — Opportunity Decision Contract & Explainable Ranking

**Status:** `PASS / SHADOW CONTRACT ONLY`
**Date:** 2026-08-12
**Scope:** deterministic strategy-local ranking profiles, Opportunity decision/state contract, structured explanation, provider-neutral read projection, fixtures, and calibration placeholders.

## Executive Summary

TASK-BE-024A extends the existing TASK-BE-024 V1 shadow layer without
activating a production Recommendation/Opportunity engine. Trend Continuation
and Catch-up now have independent, immutable, versioned provisional ranking
profiles. A deterministic decision contract maps strategy results to
`SELECTED`, `WAITING_RETEST`, `WAITING_CONFIRMATION`, `DEFERRED`, or `EXCLUDED`.

The new `OpportunityExplanation` is a structured evidence projection, not an
LLM decision. The provider-neutral `OpportunityReadModel` is ready for a
future API/frontend adapter but remains `SHADOW_ONLY`. Deterministic fixtures
cover every state and a calibration contract reserves future outcome fields
without evaluating them. Existing A/B replay, no-look-ahead semantics, Topic
Engine authority, and production boundaries remain unchanged.

## Files Modified

- `services/api/src/topicpilot_api/topic_engine/opportunity_contract.py` — new
  ranking profile, decision, explanation, read, fixture, and calibration
  contracts.
- `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py` —
  strategy-local profile selection, soft confirmation handling, and stable
  decision states while preserving the existing shadow engine.
- `services/api/src/topicpilot_api/topic_engine/__init__.py` — public exports
  for the shadow contracts.
- `services/api/tests/test_opportunity_contract.py` — focused contract tests.
- `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md` — TASK-BE-024A
  architecture amendment and contract boundary.
- `docs/product/TOPICPILOT_PRODUCT_DECISIONS.md` — PD-014.
- `docs/product/TOPICPILOT_PRODUCT_IDEAS.md` — current PM decision handoff.
- `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md` — shadow-contract roadmap row.
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` — evidence-first
  Opportunity presentation rules; no UI implementation.
- `docs/DAILY_PROGRESS.md` and `docs/AI_WORKLOG.md` — handoff and boundary
  records.
- `docs/reports/TASK-BE-024A_OPPORTUNITY_DECISION_CONTRACT_REPORT.md` — this
  report.

`AI/NEXT_TASK.md` was inspected for boundary verification and was not modified.

## Existing Recommendation Concepts Found

The audit found and preserved the following earlier concepts:

- legacy `Recommendation` remains a downstream projection of Topic
  Intelligence and is not a discovery/ranking authority;
- `StrategyCandidate`, `StrategyRun`, support/trigger/invalidation fields, and
  legacy MAS/MAV/TMC/BB/PB/KD strategy keys remain existing read-model and
  migration context;
- Product Ideas and earlier reports contain `題材 × 技術面綜合分數`,
  `推薦分數`, `補漲候選`, candidate rank, and numeric-score examples;
- the existing Opportunity Engine spec already froze the market → topic →
  stock → opportunity flow, Hard Gate vs Ranking Factor separation, technical
  scope, evidence-first presentation, and production non-goals.

These concepts were not deleted. They are labelled historical/provisional or
compatibility-only. The current PM Opportunity direction and this decision
contract take priority where terminology conflicts.

## Decisions Consolidated

1. Trend Continuation and Catch-up rank independently; no global winner exists.
2. Ranking parameters are centralized, immutable, profile-versioned, and
   `PROVISIONAL_TUNABLE_VERSIONED`; no optimization or PM freeze is implied.
3. Engine statuses (`CANDIDATE`, `DEFERRED`, `EXCLUDED`) remain compatible
   eligibility statuses; the decision contract adds stable uppercase
   Opportunity states.
4. Hard exclusions remain fail-closed. A missing required context is
   `DEFERRED`; incomplete optional confirmation can be
   `WAITING_CONFIRMATION`.
5. Explanation is structured backend evidence. An LLM, if used later, may
   verbalize evidence only and cannot decide state, rank, eligibility, or risk.
6. The read projection is provider-neutral/persistence-neutral and frontend
   ready, but publication remains `SHADOW_ONLY`.
7. Future `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain explicit
   `FUTURE_NOT_IMPLEMENTED` slots.

## New Opportunity Engine Architecture

```text
Theme Context
  → Eligibility
  → Risk / Exclusion
  → Strategy Evidence
  → Strategy-specific Ranking
  → Opportunity Decision
  → Explainability Projection
  → Shadow Read Contract
```

Topic Engine remains upstream authority for Topic Score, Grade, Lifecycle,
and Topic Strength. The strategy layer consumes those fields and does not
recalculate them. Canonical daily OHLCV and existing evidence builders remain
the technical source. The new projection is in-memory and deterministic.

## FROZEN vs OPEN Decision Matrix

| Area | Current decision | Status |
|---|---|---|
| Opportunity positioning | Opportunity Engine, not black-box buy/sell advice | FROZEN |
| Pipeline | Theme → eligibility → risk → evidence → ranking → decision → explanation → read | FROZEN |
| Decision states | SELECTED / WAITING_RETEST / WAITING_CONFIRMATION / DEFERRED / EXCLUDED | FROZEN for shadow contract |
| Hard Gate concept | Gates remain separate from ranking factors | FROZEN |
| Evidence presentation | Structured, status-first/evidence-first | FROZEN |
| Trend/Catch-up profiles | Separate profiles, no global cross-strategy ranking | FROZEN for shadow contract |
| Topic Grade qualification threshold | Not defined here | OPEN / NOT PM-FROZEN |
| Lifecycle qualification rule | Not defined here | OPEN / NOT PM-FROZEN |
| 20MA mandatory status; 60MA gate/bonus | Not defined here | OPEN / NOT PM-FROZEN |
| Support-distance threshold | Not defined here | OPEN / NOT PM-FROZEN |
| Risk cooldown days | Not defined here | OPEN / NOT PM-FROZEN |
| Price/volume formal definitions | Not defined here | OPEN / NOT PM-FROZEN |
| Topic/Technical/Entry/Chip weights | Provisional profile placeholders only | OPEN / NOT PM-FROZEN |
| Max stocks per topic | Not defined here | OPEN / NOT PM-FROZEN |
| Opportunity validity period | Not defined here | OPEN / NOT PM-FROZEN |
| Intraday automatic reorder | Not defined here | OPEN / NOT PM-FROZEN |
| Exception upgrade threshold | Not defined here | OPEN / NOT PM-FROZEN |
| Institution/chip confirmation threshold | Not defined here | OPEN / NOT PM-FROZEN |
| State transition thresholds | Not defined here | OPEN / NOT PM-FROZEN |
| Calibration/outcome evaluation | Schema placeholder only | OPEN / NOT IMPLEMENTED |

## Conflict / Legacy Terminology Handling

`Recommendation`, `推薦分數`, `補漲候選`, `Candidate Recommendation Score/Rank`,
and old strategy keys remain searchable historical terms. They are not
silently renamed or deleted. Current documentation marks them
`HISTORICAL_ONLY`, `ADAPT`, or `DEPRECATE_LATER` according to the existing
architecture reconciliation. New user-facing copy uses Opportunity state and
evidence rather than Buy/Sell, stars, AI confidence, or false-precision score
labels.

## Frontend Implications

The future surface follows the existing Modern Financial Workspace and warm
neutral/dense editorial style. Cards/lists may show topic, instrument identity,
state, major evidence, major risk/waiting context, as-of/data status, and an
inspect-opportunity CTA. The browser consumes the read contract and must not
derive state, gates, leaders, technical classes, rank, or risk. No UI code was
changed in this task.

## Backend Implications

The backend shadow layer owns state mapping, ranking-profile selection,
reason/display keys, structured values, policy version, confidence basis, and
read-model projection. Global cross-strategy ranking is explicitly null or
unavailable. The contract is provider-neutral and persistence-neutral; no
database model, API response, scheduler, or daily pipeline was changed.

## Data Dependencies

The contract depends on the existing formal Theme Context, effective topic
membership, canonical daily OHLCV, as-of date, evidence builders, data-quality
and no-trade flags, and optional future chip confirmation inputs. Missing data
remains unknown/deferred; news/Radar remains catalyst/context and cannot
increase rank by heat alone. Future calibration additionally needs point-in-
time forward bars and support/invalidation observations, but those are not
collected or evaluated here.

## No-implementation Boundary

This task did not activate production Recommendation/Opportunity semantics,
write a database row, add/migrate a schema, expose an API, modify frontend
runtime, modify scheduler/daily market pipeline, change Topic Score/Grade/
Lifecycle, modify legacy V1, or modify `AI/NEXT_TASK.md`. The only code scope
is the in-memory/test/report shadow contract above the existing TASK-BE-024
engine.

## Verification

- Focused strategy regression: `20 passed`.
- Focused decision/read-contract suite: `7 passed`.
- Full backend suite: `332 passed, 31 skipped, 1 warning` (the warning is the
  existing Starlette/httpx deprecation notice; skips are PostgreSQL-dependent).
- Targeted Ruff checks for all 024A Python files pass. A repository-wide Ruff
  run still reports pre-existing unrelated violations in other modules; those
  files were not changed by this task.
- Fixture validation confirms all five decision states are represented and no
  prohibited recommendation language is emitted.
- Deterministic replay remains as-of bounded and no-look-ahead.
- `NEXT_TASK` timestamp/content was checked and remained unchanged.

## Remaining PM Decisions

The OPEN matrix above still requires explicit PM decisions before any
production adapter: exact thresholds/formulas, Topic Grade/Lifecycle
qualification, 20MA/60MA gate semantics, support distance, cooldown/validity,
candidate limits, intraday reorder, exception upgrades, chip confirmation,
state transition rules, and outcome/calibration methodology.

## Recommended Next Step

Run a separate PM review of the decision/read contract and a point-in-time
calibration dataset design. Only after those decisions are approved should a
new work order consider an API adapter or persistence; production activation
must remain separately gated.

## Fixed Outputs

```text
OPPORTUNITY_DECISION_CONTRACT = PASS
TREND_RANKING_PROFILE = PASS
CATCHUP_RANKING_PROFILE = PASS
RANKING_PROFILES_INDEPENDENT = PASS
OPPORTUNITY_STATE_MACHINE = PASS
SELECTED = PASS
WAITING_RETEST = PASS
WAITING_CONFIRMATION = PASS
DEFERRED = PASS
EXCLUDED = PASS
EXPLAINABILITY_CONTRACT = PASS
READ_CONTRACT = PASS
FRONTEND_FIXTURES = PASS
POLICY_VERSIONING = PASS
PARAMETERS_PROVISIONAL = YES
GLOBAL_CROSS_STRATEGY_RANKING = DISABLED
EARLY_STRENGTH = FUTURE_NOT_IMPLEMENTED
PULLBACK_ACCEPTANCE = FUTURE_NOT_IMPLEMENTED
REPLAY_NO_LOOKAHEAD = PASS
PRODUCTION_DB_WRITE = NO
PRODUCTION_API_ACTIVATION = NO
PRODUCTION_SCHEDULER_CHANGE = NO
DAILY_MARKET_PIPELINE_CHANGE = NO
TOPIC_LIFECYCLE_CHANGE = NO
TOPIC_SCORE_CHANGE = NO
NEXT_TASK_MODIFIED = NO
IMPLEMENTATION_STARTED = NO
```
