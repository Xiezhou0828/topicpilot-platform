# TopicPilot Product Roadmap

**Status:** `CANONICAL / HIGH-LEVEL PRODUCT VIEW`
**Last reviewed:** 2026-08-12

This is a product-level map, not a work-order list and not a date promise. Execution detail remains in [docs/ROADMAP.md](../ROADMAP.md), [WORK_ORDERS.md](../WORK_ORDERS.md), and the linked evidence reports.

## V2 launch / current work

| Scope | State | Notes |
|---|---|---|
| Topic Intelligence foundation, deterministic boundaries, read API/dashboard, Recommendation boundary/MVP, research validation | `COMMITTED / CURRENT` | Repository context records these as implemented or verified, with providers and activation still fail-closed where gated. |
| V2 customer shell and frozen Home, header, Topic, Stock, 收藏, 機會 interaction direction | `COMMITTED / CURRENT` | Authority is the Product Direction Contract plus V2 Frontend Design Specification. |
| Backend production activation gates | `PLANNED / BLOCKED BY EXPLICIT GATES` | Governed Leader Set, approved artifact metadata, live/as-of freshness binding, and Eligibility Audit evidence remain required. |
| `TASK-LIVE-002` live validation | `PLANNED / WAITING_LIVE_VALIDATION` | Do not change its status here; see its readiness report. |
| Opportunity Engine V1 strategy shadow layer | `IMPLEMENTED / SHADOW CALIBRATION` | `TREND_CONTINUATION` and `CATCH_UP` are independent, deterministic, policy-versioned shadow strategies; production API/persistence/activation remain separately gated. |
| `TASK-BE-024A` decision/read contract and explainability layer | `IMPLEMENTED / SHADOW CONTRACT` | Strategy-local provisional ranking profiles, deterministic states, structured evidence projection, frontend fixtures, and calibration placeholders; no production publication or global ranking. |
| `TASK-BE-024B` Opportunity Qualification Policy V1 | `IMPLEMENTED / SHADOW POLICY` | PM-frozen qualification order, S/A formal universe, B warming exception, D/Declining exclusion, 20MA hard gate, risk-before-ranking, independent strategy caps, and versioned provisional parameters; no production activation. |
| `TASK-BE-024C` Opportunity Shadow Read API & Frontend Adapter V1 | `IMPLEMENTED / SHADOW READ` | Provider-neutral read service, topic/stock/detail projections, deterministic synthetic fixtures, and frontend adapter. `publicationStatus=SHADOW`; no persistence, activation, replay, or calibration. |

## V2.x enhancement candidates

- `PLANNED / CANDIDATE`: polish and validate the committed customer surfaces through prototype review.
- `PLANNED / CANDIDATE`: strengthen current operational/readiness evidence and activation gates.
- `IDEA`: Topic Peek signature interaction, likely V2.2/V3 candidate.
- `IDEA`: factual 收藏 reminders and topic notifications.

No item in this section creates a work order or date commitment.

## V3 / later candidates

- `IDEA`: richer topic lifecycle animation and interaction.
- `IDEA`: full AI研究室 multi-agent research experience.
- `PLANNED / FUTURE`: Theme Governance, Theme Discovery, and Knowledge Graph planning; these must not block the Topic Intelligence MVP path.
- `PLANNED / FUTURE`: broader normalized market-data warehouse, detector persistence/execution, performance and analytics work where existing specifications defer them.
- `PLANNED / FUTURE`: Opportunity Engine `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE`; both remain explicit future strategies and are not V1 implementation commitments.

## Boundary rules

1. `COMMITTED` means an approved product direction or an already recorded current milestone, not permission to modify runtime in this document task.
2. `PLANNED` means an explicitly registered future/current gate; dates are intentionally absent.
3. `IDEA` means consideration only. It is not a roadmap commitment.
4. NEXT_TASK and work-order status remain owned by existing PM/current-status documents; this file does not overwrite them.

## Newly consolidated UX direction

- `APPROVED_LATER`: 今日市場 Market Pulse carousel with consistent section
  headings, hover pause, topic filtering, and topic-page navigation.
- `APPROVED_LATER`: topic-page formal-data-first rendering with a complete,
  clearly labelled Mock Data fallback when a source is unavailable.
- `FUTURE UX`: the V2 topic-card right-side peel-open interaction remains a
  later enhancement and is documented in [Product ideas](TOPICPILOT_PRODUCT_IDEAS.md).

Completed work-order details and implementation transcripts remain historical
evidence. Durable product direction and roadmap states belong in the canonical
product documents; execution detail should be linked from reports or archived
work orders.

## Opportunity policy next gates

`TASK-BE-024C` is the current shadow-read integration milestone. The next
separate gates are canonical production data provider wiring, formal history
accumulation, point-in-time replay, and calibration review. Intraday reranking,
advanced technical evidence, chip/institution calibration, and the future
`EARLY_STRENGTH` / `PULLBACK_ACCEPTANCE` strategies remain outside V1.
