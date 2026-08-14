# TopicPilot execution roadmap

**Owner:** execution sequence, phase priority, status, and dependency routing
**Last reviewed:** `2026-08-14`

This document owns execution routing. It does not replace the accepted product
contract, architecture specifications, work orders, or validation reports.
Permanent product direction belongs to the [Product Direction and Surfaces
Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md). Work-order scope
and evidence remain in [WORK_ORDERS.md](WORK_ORDERS.md) and the linked reports.
Startup and handoff navigation belongs to [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md).

## Execution principles

- Roadmap status describes the current product path, not a promise of dates.
- A completed isolated implementation is not automatically a reconciled
  canonical release; reconciliation and affected validation remain explicit.
- Use impact-based validation. Preserve a named PASS baseline when the changed
  dependency is outside its protected boundary; do not rerun G1/G2/G3/Canary for
  an ordinary read-only or UI change unless the impact analysis reaches that
  boundary. See [AGENTS.md](../AGENTS.md) and the repository
  [documentation governance](DOCUMENTATION_GOVERNANCE.md).
- Phase priority is product priority and dependency order, not a global
  serialization lock. Independent workstreams may proceed in parallel when
  contracts and write sets do not conflict.
- This roadmap never authorizes Production mutation, scheduler activation,
  deployment, source-of-truth cutover, or a `NEXT_TASK` change.

## Current operational baseline

### Mainline A — DATA / Reference / Post-Close

`TASK-DATA-REF-009A` is complete for the current handoff. G0, G1, G2, G3, and
the Post-Close Canary are `PASS`; the preserved 2026-08-13 date-effective
universe is TPE 313 + TWO 193, and the one-shot result is `506/506` with
`DOWNSTREAM_READY=true`. The physical 507-row identity universe remains
distinct from the 506 date-effective run because TPE:6806 is retained
physically but not eligible for that date.

Mainline A is no longer the general product-development critical path. Future
work that changes reference identity/lifecycle/calendar, official provider
authority, G2/G3 semantics, post-close persistence/reconciliation/snapshots,
or the relevant runtime must explicitly re-enter the protected gates. An
ordinary FastAPI read path, frontend change, read-only reconciliation, or UI
bug fix does not do so merely by association; record `PRESERVED PASS` with the
baseline and targeted validation.

### Mainline B — Historical

`HIST-001` is complete. The next historical slice is six-month local/full seed
coverage with durable historical provenance, followed by technical and
recommendation inputs suitable for replay and review.

Historical OHLCV readiness is not historical Topic/System State readiness.
Six months of prices do not by themselves reproduce historical topic scores,
grades, lifecycle transitions, primary/secondary relations, membership, or
other system state. Those require point-in-time topic/reference inputs,
effective-dated relations, policy versions, and provenance.

### Mainline C — Today

Daily Focus and Market Events isolated wiring is complete on the shared Today
resource path. Market Overview wiring and the remaining formal data/read-model
gaps are follow-up work. The Today surface must preserve backend-owned order,
metadata, and explicit `FORMAL` / `TEMPORARY` / `PREVIEW` / `UNAVAILABLE`
semantics; missing indices, turnover, narrative, or derived market score must
remain unavailable until a backend-owned contract exists.

### Mainline E — Stock

Formal stock code/name search and formal topic-filter wiring are complete in
isolation. The next execution slice is reconciliation, EOD presentation,
漲跌幅 semantics, Stock Drawer regression/detail data, and remaining formal
detail fields. Existing search/filter behavior remains backend-owned: the
browser must not infer membership, ranking, sorting, or topic semantics.

## Phase priorities

| Priority | Product focus | Current routing |
|---|---|---|
| **P0** | Product Completion | Complete Stock, Today, and Topic formal data plus UI; close the remaining read-model, publication, detail-field, and layout gaps. |
| **P1** | Historical + Recommendation research | Complete historical seed/provenance and research-only recommendation validation; no direct HIST-to-production jump. |
| **P2** | Data Management + News + Discovery | Build governed master-data/admin and News/Event foundations before AI discovery or correction suggestions. |
| **P3** | Opportunity + Favorites polish | Keep Opportunity shadow/production wiring bounded and finish Favorites UI polish. |
| **P4** | Intraday | Deferred until formal quote freshness/update ownership is ready. |
| **P5** | AI Studio | Deferred; not a prerequisite for P0–P4. |

## P0 — Product Completion

### Stock

- Reconcile the isolated formal search and topic-filter implementation into the
  canonical repository and validate the affected API/frontend boundary.
- Finish EOD presentation, percentage-change semantics, Drawer regression/detail
  data, and any missing formal fields without inventing browser-side values.
- Preserve backend ordering and formal/preview/unavailable disclosure.

### Today

- Complete the Market Overview/formal-data follow-up on the shared Home resource.
- Keep Daily Focus and Market Events as backend-owned projections. Temporary
  topic-snapshot-derived content must remain labelled `TEMPORARY`; it is not
  promoted to formal data by frontend wiring.
- Add missing indices, turnover, narrative, or score only through an approved
  backend-owned contract and read model.

### Topic page

- Close the formal publication gap for Today Topic Map `S/A/B/D` groups.
- Provide formal Topic Lifecycle data and missing detail fields.
- Fix the large-group accordion same-row height coupling bug without changing
  topic semantics or lifecycle derivation.

### Favorites

Favorites is mainly UI polish: unify shared Drawer/favorite state and keep
formal values, nulls, and local-device state explicit until a formal aggregate
read model and change-event contract exist.

## P1 — Historical and Recommendation research

The following are research candidates, not accepted production strategies:

- A1 — Pre-Breakout;
- A2 — Confirmed Breakout;
- A3 — Strong Pullback / Retest;
- Catch-up / rotation.

Every candidate must pass this gate sequence:

`Historical/Proxy Backtest` → `Point-in-time/Walk-forward` → `Strategy Review`
→ `Accepted/Rejected` → `Formal Contract` → `Production Implementation`.

No candidate may move directly from `HIST-001 complete` to production
implementation. Recommendation remains downstream of Topic Intelligence and
must retain explainability, no-look-ahead evidence, versioned parameters, and
explicit publication state.

## P2 — Data Management, News, and Discovery

### Master Data / Admin

Provide a governed data-management surface for:

- adding stocks;
- adding, updating, and removing stock–topic relations;
- primary versus secondary topic assignment;
- relation weights;
- immutable audit history and actor/source provenance.

These are canonical-data writes and require their own contract, authorization,
validation, and audit boundary. They are not implied by a read-only Admin/Data
Explorer or a frontend form.

### News / Event foundation

Establish a source-grounded News/Event foundation first: source identity,
publication time, event type, affected topic/stock references, provenance,
deduplication, and review state. Then add AI Topic Discovery and topic
correction suggestions as advisory outputs.

AI may propose a new topic, relation, merge, rename, or correction. AI may not
directly mutate canonical taxonomy, topic hierarchy, stock–topic relations,
weights, primary/secondary state, or audit history.

## P3 — Opportunity and Favorites

Opportunity continues to use the existing shadow/production wiring boundary.
The shadow read contract, evidence projection, and presentation caps do not
constitute production recommendation publication. Production activation still
requires the P1 research gate, formal contract, data/provenance readiness, and
an explicit approval.

Favorites remains a watchlist and market-context surface. Formal aggregate
storage and canonical factual-change events are future bounded contracts; UI
polish may proceed independently when its write set does not conflict.

## P4 / P5 — Deferred surfaces

- **P4 Intraday:** delay quote-update work until source ownership, freshness,
  scheduling, and user-facing update semantics are formally bound.
- **P5 AI Studio:** delay the multi-agent research experience until the core
  product surfaces, governed data foundations, and research contracts are ready.

## V1 bridge and retirement boundary

V1 is `LEGACY BRIDGE / PARTIAL RETIREMENT`, not a new-feature target. Preserve
`price_engine.py` (TWSE MIS + Yahoo fallback, Sheet/TSV input, H:I:J:K quote
write-back), `ta_engine.py` (Yahoo six-month OHLCV and technical factors),
`radar.py` (Sheets master/relations/synonyms, RSS/news, topic heat and history),
and legacy master-data/scheduling bridges. Retire each bridge only after its
V2/PostgreSQL/FastAPI replacement has passed dual-run/parity and an explicit
cutover decision.

## Navigation and stale-status handling

- Product direction and semantics: [Product Direction and Surfaces
  Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).
- Startup/current handoff: [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md).
- Collaboration, worktrees, and validation: [AGENTS.md](../AGENTS.md).
- Detailed task evidence: [WORK_ORDERS.md](WORK_ORDERS.md) and `docs/reports/`.

Old `TASK-LIVE-002 = WAITING_LIVE_VALIDATION`, provider-activation blockers,
old migration-head/repository snapshots, and old Opportunity “next gate” text
are historical unless explicitly linked as current by this roadmap. They do not
override the 2026-08-14 phase priorities. Do not edit or infer `NEXT_TASK` from
this document.
