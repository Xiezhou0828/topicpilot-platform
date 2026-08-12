# TopicPilot V2 Roadmap

## Roadmap governance

This document owns milestone sequence and execution focus. Permanent product direction is governed by the [Product Direction and Surfaces Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md), accepted decision rationale by [ADR-003](architecture/ADR-003_TOPICPILOT_PRODUCT_POSITIONING.md), and document ownership by the [Architecture Book](architecture/README.md#documentation-governance-and-single-source-of-truth). Work-order scope and evidence remain in [WORK_ORDERS.md](WORK_ORDERS.md) and the individual work-order records.

### Implementation principle

- Every milestone must deliver a user-visible product capability.
- A PM decision is complete only when it unblocks implementation (or explicitly records why implementation remains deferred).
- Research may continue after implementation begins when the architecture supports pluggable policies.

## Long-term product vision

TopicPilot is a production-ready Topic Intelligence platform for understanding Taiwan-market topic strength, lifecycle, rotation, history, and explainable evidence. Recommendation is downstream: it consumes Topic Intelligence and does not define the product's identity or Topic Score. Theme Governance, Theme Discovery, and the Knowledge Graph are future planning capabilities that must not block the first Topic Intelligence product.

## Current execution roadmap

### Primary milestone: Topic Intelligence MVP

**Current objective:** Build the first production-ready Topic Intelligence platform. The MVP path is intentionally capability-led and proceeds in this order:

1. **Topic Engine Foundation** — completed foundation work grouped below; 3.7-001F is `PASS / VERIFIED`.
2. **Topic Formula Research & Plug-in** — research and implement pluggable Breadth, Leadership, and Aggregation policies within the PM-001–PM-007 boundaries. Exact formulas, weights, thresholds, normalization, and aggregation remain Formula Pending until justified by research and validation.
3. **Topic Intelligence API** — expose deterministic Topic Intelligence as a customer-consumable read surface.
4. **Customer Topic Dashboard** — make topic strength, components, confidence, evidence, and history visible to customers.
5. **Recommendation MVP** — consume Topic Intelligence to provide explainable downstream candidates; Recommendation does not feed back into Topic Strength.
6. **Historical Validation / Calibration** — evaluate topic scores against subsequent topic behavior and calibrate policies, thresholds, and aggregation with replayable evidence.

The Formula Research & Plug-in foundation is complete through `PHASE-3.7-002F`; `PHASE-3.7-003A`, `PHASE-3.7-003B`, `PHASE-3.7-003C`, `PHASE-3.7-003D`, and `PHASE-3.7-003E` are `PASS / VERIFIED`. 003B is the existing customer Topic Dashboard, 003C is the deterministic Recommendation read-model boundary, 003D is the Recommendation MVP API, and 003E is the research-only Historical Validation / Calibration Review. The Topic Intelligence and Recommendation default providers still deliberately fail closed until separately approved runtime/data sources exist. 003D does not activate ranking, prediction, trading behavior, persistence, or Theme Governance. 003E reports evidence and requires PM review; it does not choose or promote a formula.

## Topic Engine Foundation — completed work grouped by capability

The following completed work orders remain historically numbered and are grouped here to show that they form one capability rather than isolated roadmap targets:

- **3.7-001 Topic Engine Foundation** — `IN_PROGRESS`; deterministic, provider-neutral Topic Engine boundary.
- **3.7-001A Topic Feature Contract** — `PASS / VERIFIED`.
- **3.7-001B Topic Feature Runtime / Aggregator Boundary** — `PASS / VERIFIED`.
- **3.7-001C Topic Scorer Contract** — `PASS / VERIFIED`.
- **3.7-001E Topic Scorer Runtime** — `PASS / VERIFIED`.
- **3.7-001F Topic Intelligence Runtime Integration** — `PASS / VERIFIED`; deterministic ephemeral per-topic outputs.

The PM-001 Breadth semantic boundary, PM-002 Leadership semantic boundary,
PM-003–PM-006 freeze, and PM-007 approved Production V1 mechanics remain
authoritative. Executable mechanics are implemented only through the bounded
non-activating `PHASE-3.7-003I` order; persistence, API exposure, Recommendation,
and provider activation remain separately governed. See the [canonical scoring
inventory](reports/PHASE_3_7_001D_SCORING_POLICY_INVENTORY.md) and [Topic Engine
contract](architecture/PHASE_3_7_001_TOPIC_ENGINE_CONTRACT.md).

The scoring governance sequence is frozen as: **PM Semantic Freeze → Research Candidate → Historical Validation → PM Formula Approval → Production Policy**. V1 remains a research baseline only; its weighted return and strong/weak diffusion are Breadth evidence candidates, while `ln(N)` and coverage belong to Evidence Quality / Eligibility rather than Topic Score.

### Current handoff after Phase 4–6

The Phase 4–6 product capabilities are complete and verified through
`PHASE-3.7-003B` (Customer Topic Dashboard), `PHASE-3.7-003D` (Recommendation
MVP API), and `PHASE-3.7-003E` (Historical Validation / Calibration). The next
roadmap gate is `PHASE-3.7-003F` PM Formula Approval. Its mechanics are now
approved in the canonical brief; the active implementation gate is
`PHASE-3.7-003I`.

The PM Formula Approval Brief remains the single review entry point. Production
activation is blocked pending governed Leader Set population/approval, approved
live/as-of freshness binding, 003G/003H approval artifact metadata, and required
Eligibility Audit evidence. A bounded non-activating implementation may proceed
for frozen mechanics and must not activate providers or promote a policy.

`PHASE-3.7-003G` is now `PASS / VERIFIED`
as a formula-agnostic safety capability. It validates approval-record
provenance and scope only; it does not choose, calculate, persist, expose, or
activate a Topic Score policy. Production policy mechanics remain separately
tracked from provider activation.

`PHASE-3.7-003H` is now `PASS / VERIFIED`. It adds a strict JSON-compatible
transport boundary for the PM approval artifact and composes with the verified
003G Guard. It remains unable to create approval decisions or activate a
production provider.

`PHASE-3.7-003I` is now `PASS / VERIFIED`. It implements the approved
non-activating Production V1 classifier, Breadth/Leadership components,
normalization, consensus, aggregation, Eligibility Audit, Grade, and immutable
policy lineage. Provider activation remains a separate future gate.

### Backend runtime finalization audit — `PHASE-3.7-004`

`PHASE-3.7-004` is `PASS / AUDITED — ACTIVATION BLOCKED`. It adds the explicit
runtime readiness gate, canonical PRICE as-of query boundary, and deterministic
Eligibility Audit report builder. It does not activate a provider, create a
Leader Set, invent an approval artifact, read V1, or redesign the frontend.

The provider remains blocked until a real governed Leader Set, 003G/003H
approval artifact, approved canonical source/session/as-of/freshness binding,
and complete current-V2 Eligibility Audit evidence are supplied. The detailed
gap classification and future handoff are in the [Backend Runtime Finalization
Audit](reports/PHASE_3_7_004_BACKEND_RUNTIME_FINALIZATION_AUDIT.md).

## Existing completed and historical records

The following records are retained as completed/history and are not renumbered:

- **3.4-001 Database Foundation** — `VERIFIED`.
- **3.4-002 Identity Domain** — `VERIFIED`.
- **3.4-003 Topic Domain** — `VERIFIED`.
- **3.4-004 Instrument-Topic Relationship Domain** — `VERIFIED`.
- **3.4-005 Market Data Source & Raw Observation Foundation** — `PASS / VERIFIED`.
- **3.4-005A Validation Framework** — `PASS / VERIFIED`.
- **3.4-006 Observation Timeline Domain** — `PASS / PM Approved`.
- **3.4-006A Observation Timeline Physical Design & Implementation Planning** — `PASS / PM Approved`.
- **3.4-006B Observation Timeline Implementation** — `PASS / VERIFIED`.
- **3.5-001 Observation Normalization Contract** — `PASS / PM Approved`.
- **3.5-001A Observation Normalization Physical Design** — `PASS / PM Approved`.
- **3.5-001B Canonical Observation Schema Implementation** — `PASS / VERIFIED`.
- **3.5-002 Observation Normalizer Planning** — `PASS / PM Approved`.
- **3.5-002A Synthetic Reference Normalizer** — `PASS / VERIFIED`.
- **3.6-001A V1 Export Contract & Dry-Run Validation** — `PASS / PM Approved`.
- **3.6-001B Legacy Import Foundation** — `COMPLETED / POSTGRESQL IMPORT VERIFIED`.
- **3.6-002 Admin/Data Explorer Foundation** — `IMPLEMENTED / MVP READ-ONLY SLICE`.
- **3.6-002A Admin/Data Explorer Detail and ERD** — `PASS / VERIFIED`.
- **V2-FOUNDATION-CONSISTENCY-001 / Fix-001, Fix-002, Fix-003** — `PASS / COMPLETE`.
- **V2-VALIDATION-DEBT-001** — `PASS / VERIFIED`.

These entries preserve roadmap history; their detailed scope and evidence remain in their existing work orders and reports.

## Future planning milestones — not current implementation targets

- **Theme Governance** — `FUTURE PLANNING`; governance state machine and policy decisions must be completed before implementation is authorized.
- **Theme Discovery** — `FUTURE PLANNING`; proposal/discovery capability, not a current Topic Intelligence MVP dependency.
- **Theme Knowledge Graph** — `FUTURE PLANNING`; graph, lineage, and reasoning capabilities follow the MVP and validation path.

The registered `THEME-GOVERNANCE-KNOWLEDGE-001` remains `PLANNING / NEEDS PM DECISION`. No implementation, schema, migration, API, frontend, crawler, clustering runtime, scoring formula, or automatic knowledge promotion is authorized by that planning record. Theme Governance must not block current Topic Formula, API, Dashboard, Recommendation MVP, or Historical Validation work.

## Other deferred work

- Full Normalized Market Data warehouse, detector persistence/execution, performance, analytics implementation, and V1 parity/cutover remain deferred according to their existing specifications and work orders.
- Phase 3.5-002B Normalization Runtime is `PASS / VERIFIED` under its existing execution work order and does not change the Topic Intelligence MVP sequence.

`PLATFORM-PRIVATE-SYNC-001` is `PASS / VERIFIED` for the deterministic parity
evidence validator and a small read-only historical-price availability probe.
It does not unblock Topic Score policy approval and does not authorize V1/V2
source-of-truth cutover. Ten actual trading-day evidence and the separate
activation gates remain required.

`PLATFORM-V2-BACKEND-MIGRATION-001` is `PASS / VERIFIED` for its bounded
Provider -> normalized observations -> PostgreSQL -> V2 read model -> FastAPI
acceptance path. The current V1 frontend remains a legacy consumer and is not
used as the V2 contract authority; frontend redesign is separate. The Taishin
historical persistence slice is verified under
`PLATFORM-V2-HISTORICAL-INGESTION-001`; production provider approval,
scheduling, and full source-of-truth cutover remain separate gates.

## Navigation

- Architecture and implementation sequence: this Roadmap.
- Work-order scope, status, and validation evidence: [WORK_ORDERS.md](WORK_ORDERS.md).
- Product direction and surfaces: [Product Direction and Surfaces Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).
- V1/V2 generation and coexistence: [generation-model.md](architecture/generation-model.md).
> **003F status:** Formula/policy mechanics are frozen in the [canonical PM
> Formula Approval Brief](reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md).
> Activation remains blocked by governed Leader Set population/approval,
> approved live/as-of freshness binding, 003G/003H approval artifact metadata,
> and Eligibility Audit evidence.

## Opportunity Engine policy handoff (2026-08-12)

`TASK-BE-024` and `TASK-BE-024A` remain implemented as independent,
deterministic shadow strategies and decision/read contracts. `TASK-BE-024B`
adds the current PM semantic Qualification Policy V1: S/A formal universe, B
warming exception with provenance, D/Declining hard exclusion, Close >= 20MA
hard gate, missing-20MA deferral, non-hard-gate 60MA structure factor,
risk-before-ranking, independent A/B ranking, five stable states, Trend Top 3 /
Catch-up Top 2 presentation caps, and post-close/status-only cadence.

TASK-BE-024C now provides the separate Opportunity shadow API/UI adapter as a
read-only, fixture-backed integration. The next roadmap gates are canonical
production data, formal history accumulation, no-look-ahead replay, and
calibration review. Numeric thresholds and weights remain versioned provisional parameters;
no production Opportunity write, scheduler activation, or fake calibration is
authorized by this entry. `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain
future strategies.

The 024C contract exposes topic/stock/detail projections, structured evidence,
qualification provenance, policy/parameter/ranking-profile versions, explicit
UI data states, and Trend Top 3 / Catch-up Top 2 presentation caps while
retaining full strategy-local ranking metadata. It is not production
Recommendation publication; persistence, scheduler activation, daily-market
changes, replay, calibration, and NEXT_TASK changes remain out of scope.
