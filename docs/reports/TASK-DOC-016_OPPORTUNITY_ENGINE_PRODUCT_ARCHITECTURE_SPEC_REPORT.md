# TASK-DOC-016 Opportunity Engine Product & Architecture Specification Report

**Status:** `PASS / DOCUMENTATION COMPLETE`
**Date:** 2026-08-12
**Owner:** TopicPilot PM
**Generation:** `SHARED product direction / NEXT V2 specification context`
**Boundary:** documentation only

## Executive Summary

TASK-DOC-016 consolidates TopicPilot's downstream candidate capability as an **Opportunity Engine / 機會篩選與研究整合層**, not a black-box AI stock-picking or buy/sell recommendation system.

The frozen direction is topic-first, gate-before-rank, technical-led in V1, entry-quality-aware, evidence-first, backend-authoritative, and lifecycle/history-capable. The five customer-facing states are `升溫候選`、`轉強觀察`、`精選機會`、`等待回測`、`失效`.

This task did not implement or activate any engine. It changed no API, database, frontend, scheduler, deployment, runtime, or `AI/NEXT_TASK.md`. All thresholds, weights, formulas, transition mechanics, and validity/reordering rules remain open.

## Files Modified

| File | Change |
|---|---|
| `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md` | New canonical task specification for Opportunity product/architecture direction. |
| `docs/product/TOPICPILOT_PRODUCT_IDEAS.md` | Added a Current PM Decision section and legacy-continuity note. |
| `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` | Expanded the Opportunity surface presentation and frontend-authority rules. |
| `AI/AI_WORKLOG.md` | Added TASK-DOC-016 handoff, validation, boundaries, and remaining PM decisions. |
| `docs/reports/TASK-DOC-016_OPPORTUNITY_ENGINE_PRODUCT_ARCHITECTURE_SPEC_REPORT.md` | Added this completion report. |

No other file is part of the intended task diff.

## Existing Recommendation Concepts Found

| Existing concept | Evidence/location | Current handling |
|---|---|---|
| V1 strategy candidates and `落後補漲_觀察 / 落後補漲_確認` | `AI/DATA_SCHEMA.md`, runtime/read-model reports | Retained as legacy production/migration history; not the new state model. |
| Topic × technical composite/ranking ideas | historical product conversations/reports and strategy-candidate behavior | Retained as historical/provisional; no legacy formula or number is promoted. |
| Candidate Recommendation, 0–100 Recommendation Score, Rank | `DOMAIN_MODEL.md`, `ATTRIBUTION_SPEC.md`, Workshop 6, Architecture Overview | Retained as early architecture/read-model terminology. Numeric ranking may remain internal; it is not the default customer presentation. |
| Recommendation read-model boundary | `PHASE_3_7_003C_RECOMMENDATION_READ_MODEL_BOUNDARY.md` | Existing deterministic/explainable/fail-closed infrastructure boundary; ranking, technical analysis, entry timing, and activation were explicitly deferred. |
| Recommendation MVP API | `PHASE_3_7_003D_RECOMMENDATION_MVP.md` | Existing read-only unavailable-by-default API boundary; not Opportunity Engine implementation. |
| Earlier frontend Opportunity groups | Frontend Design Spec: `主線精選`, `龍頭先行`, `題材擴散`, `落後補漲`, etc. | Preserved as provisional grouping history; cannot replace the five current states. |
| Existing illustrative lifecycle states | Product Surfaces Contract: `watch`, `awaiting_confirmation`, `trial_entry_candidate`, `invalidated` | Preserved as older illustrative/internal terminology; current user-facing direction is the five-state set. Mapping requires a future explicit contract. |
| Future Recommendation persistence/evaluation skeletons | V2 architecture audit/domain model | Recorded as draft/future skeletons, not implemented Opportunity domains. |

## Decisions Consolidated

- TopicPilot is a Theme Intelligence platform; Opportunity is downstream decision support.
- Opportunity Engine is not an AI tip, buy/sell instruction, broker signal, or automatic trading engine.
- Research allocation starts at topic qualification before stock evaluation.
- Hard Gates and Ranking Factors are different policy mechanisms.
- V1 is technical-led; News/Radar supplies catalyst/context and never direct heat-score uplift.
- Chip/institution information confirms; it does not independently admit or recommend a stock.
- Entry Quality is a core decision layer and can route a strong stock to `等待回測`.
- Exception/warming discovery is retained but cannot bypass eligibility, risk, or entry checks.
- Formal output centers on state + structured evidence; backend numeric ranking is optional/internal.
- Backend owns formal semantics; the browser consumes them.
- Opportunity history and state transitions must eventually be evaluable.

## New Opportunity Engine Architecture

```text
Market Context
  → Topic Qualification
  → Stock Eligibility
  → Technical Structure
  → Risk Gate
  → Entry Quality
  → Chip Confirmation
  → Opportunity State
  → Evidence / Explanation
```

The pipeline is ordered but not reduced to one sum. Eligibility and risk can fail closed; Entry Quality can reduce priority or produce `等待回測`; chip and news cannot override invalidation. Explanation is constructed from structured evidence after the decision.

The connected product flow remains:

```text
市場 → 題材 → 題材內股票 → Stock Encyclopedia → Opportunity / 查看機會
```

## FROZEN vs OPEN Decision Matrix

| Decision | Status | Notes |
|---|---|---|
| Opportunity Engine product positioning | `FROZEN` | Opportunity screening/research integration; not buy/sell advice. |
| Topic-first product flow | `FROZEN` | No undifferentiated whole-market brute ranking as the primary model. |
| Canonical pipeline stage order | `FROZEN` | Stage mechanics remain open. |
| Hard Gate versus Ranking separation | `FROZEN` | Not all evidence is additive. |
| Technical-led V1, News as context | `FROZEN` | News heat cannot directly raise rank. |
| Chip as confirmation | `FROZEN` | Not a primary gate or standalone trigger. |
| Entry Quality as a core layer | `FROZEN` | Exact support-distance policy open. |
| Exception/warming pipeline | `FROZEN` | Exact detection/upgrade threshold open. |
| Five customer-facing Opportunity states | `FROZEN` | Transition thresholds and graph open. |
| Evidence-first/status-first presentation | `FROZEN` | Internal rank may exist without customer display. |
| Backend semantic authority | `FROZEN` | No browser-side classification/inference. |
| History and performance-evaluation requirement | `FROZEN` | Persistence schema/metrics mechanics not authorized here. |
| Topic Grade qualification threshold | `OPEN / NOT PM-FROZEN` | No S/A/B/D shortcut adopted. |
| Lifecycle qualification rule | `OPEN / NOT PM-FROZEN` | No lifecycle stage automatically qualifies/excludes. |
| 20MA as sole mandatory gate | `OPEN / NOT PM-FROZEN` | Historical preference is not a finalized rule. |
| 60MA gate/bonus/evidence role | `OPEN / NOT PM-FROZEN` | No rule frozen. |
| Support-distance threshold/bands | `OPEN / NOT PM-FROZEN` | Earlier 0–5/5–8/>8 examples are provisional only. |
| Risk cooldown days | `OPEN / NOT PM-FROZEN` | No duration chosen. |
| Price/volume pattern definitions | `OPEN / NOT PM-FROZEN` | Lookbacks/normalization/definitions pending. |
| Topic/Technical/Entry/Chip weights | `OPEN / NOT PM-FROZEN` | No formula or percentages chosen. |
| Maximum stocks per topic | `OPEN / NOT PM-FROZEN` | No cap chosen. |
| Opportunity validity period | `OPEN / NOT PM-FROZEN` | No expiry chosen. |
| Intraday automatic reranking | `OPEN / NOT PM-FROZEN` | Behavior and stability policy pending. |
| Exception upgrade threshold | `OPEN / NOT PM-FROZEN` | No warming/relative-strength threshold chosen. |
| Institution/chip confirmation threshold | `OPEN / NOT PM-FROZEN` | No net-buy/holding rule chosen. |
| State transition thresholds | `OPEN / NOT PM-FROZEN` | Names/meanings frozen; mechanics pending. |

## Conflict / Legacy Terminology Handling

No historical concept was deleted. The new specification explicitly labels legacy and provisional language so it cannot be mistaken for the current formal product decision.

- `Recommendation` may remain in old code, work orders, APIs, database skeletons, and evaluation history.
- `Opportunity Engine` is the current user/product positioning.
- `Strategy Candidate` is a V1/parity concept.
- `Candidate Recommendation + Score + Rank` is an earlier architecture/read-model concept.
- The five Chinese states are the current customer-facing state direction.
- Old numbers and group labels are not silently reused as formulas, thresholds, or state mappings.

Where an older document describes implemented infrastructure, that factual implementation status remains valid. What changes is the current product direction and the interpretation required for future work.

## Frontend Implications

Future Opportunity cards/lists should expose topic, stock identity, formal state, primary evidence, primary risk/limiter, freshness, and a `查看機會` CTA. They remain visually consistent with Modern Financial Workspace: warm-neutral, calm, restrained, and dense-editorial.

The frontend must not calculate gates, technical classes, support validity, entry quality, relative leadership, ranks, or state transitions. It must avoid stars, AI confidence, imperative buy/sell terms, and decimal-score-first presentation. This task changed the design specification only; no UI was implemented.

## Backend Implications

Future backend work needs versioned, deterministic contracts for each pipeline stage, structured reason/evidence codes, fail-closed missing-data behavior, internal ranking, formal states/transitions, and policy/data lineage.

The existing Recommendation read model/API can be assessed as reusable infrastructure, but TASK-DOC-016 does not decide reuse, rename routes, change payloads, activate providers, or claim semantic parity with the Opportunity specification.

## Data Dependencies

- market/session and freshness context;
- Topic identity, role/membership, Grade, Lifecycle/history, rotation/warming evidence;
- stock identity and topic relations;
- adjusted daily OHLCV sufficient for 20MA/60MA and approved patterns;
- intraday/daily as-of semantics;
- governed support/resistance and price/volume evidence;
- corporate-action and missing-data handling;
- institution/chip data with unit/source/period/freshness lineage;
- attributed News/Radar catalyst/risk context;
- versioned policy/model identity;
- Opportunity snapshots, transitions, and later evaluation observations.

Data availability alone does not freeze policy.

## No-implementation Boundary

This task made no Recommendation/Opportunity Engine implementation and no runtime behavior change. Specifically:

- no API route or payload changed;
- no database/schema/migration changed;
- no frontend component, route, style, or deployment changed;
- no scheduler, provider, pipeline, or production data changed;
- no threshold, formula, weight, cooldown, expiry, or transition rule was activated;
- no `AI/NEXT_TASK.md` change was made.

## Verification

- Read required Product Ideas, Frontend Design Spec, and current AI Worklog.
- Read the canonical product contract/document-governance context and existing Recommendation 003C/003D boundaries.
- Searched relevant Markdown for Recommendation, Opportunity, strategy candidate, Recommendation Score, 補漲候選/落後補漲, 推薦分數, 綜合分數, and 技術選股 concepts.
- Reconciled current direction against Attribution, Domain Model, Workshop 6, V1 data/schema context, architecture audit, Home read-model reports, and institution-collector boundary.
- Verified that every PM-mandated open item is explicitly listed as `OPEN / NOT PM-FROZEN`.
- Verified fixed decision outputs, required report sections, valid relative links, UTF-8 readability/no `U+FFFD`, whitespace/diff integrity, intended file scope, and unchanged `AI/NEXT_TASK.md`.
- Runtime tests/build were not run because this is documentation-only and no runtime artifact changed.

## Remaining PM Decisions

1. Freeze topic Grade and Lifecycle qualification semantics.
2. Decide the mandatory technical eligibility set, especially 20MA and 60MA roles.
3. Define formal price/volume, support, invalidation, and cooldown rules.
4. Define Entry Quality/support-distance policy without fake precision.
5. Decide ranking factors/weights, per-topic cap, validity, and intraday stability.
6. Define Exception and chip confirmation thresholds.
7. Define the allowed state-transition graph and reason taxonomy.
8. Decide the compatibility/migration mapping from existing Recommendation contracts and legacy terminology.

## Recommended Next Step

Run a dedicated PM business-rule freeze sequence before implementation. Define and approve each open rule in dependency order: Topic Qualification → Stock Eligibility/Hard Gates → Technical/Risk definitions → Entry Quality → optional Chip Confirmation → internal Ranking → State Transition policy → evidence/reason taxonomy. Only then create a separately scoped implementation work order with explicit API/DB/frontend boundaries.

```text
OPPORTUNITY_PRODUCT_POSITIONING = FROZEN
OPPORTUNITY_PIPELINE = FROZEN
OPPORTUNITY_STATES = FROZEN
HARD_GATE_CONCEPT = FROZEN
EVIDENCE_FIRST_PRESENTATION = FROZEN
WEIGHTS_AND_THRESHOLDS = OPEN
IMPLEMENTATION_STARTED = NO
```
