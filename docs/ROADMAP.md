# TopicPilot execution roadmap

**Owner:** execution sequence, phase priority, status, and dependency routing
**Last reviewed:** `2026-08-22`

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

The protected data, historical, Today, Stock, and Topic foundations below
remain the current baseline; the parallel execution routes are stated first so
that active work does not get mistaken for a serialized release path.

## Current Parallel Plan

The 2026-08-22 execution route is four isolated workstreams. Completion or
readiness in one workstream does not establish overall release readiness, and
each workstream must preserve the authority boundaries below.

- **WS1 — Topic Derived Intelligence / Structural Role & Score Projection:**
  D001 is owner-decided and canonicalized; additive authority/read-model
  infrastructure and fail-closed as-of resolvers are in the canonical path.
  The next bounded step is Owner-reviewed, effective-dated authority ingestion
  for Structural Role and approved Score Projection V1 data. Role/projection
  records remain unpopulated, and Score/Grade publication is not authorized.
  Topic Lifecycle API/frontend integration and fail-closed disclosure are now
  committed; current live acceptance remains pending stage-bearing canonical
  rows, so Forward Shadow is not formal publication.
- **WS2 — Stock Technical V0:** policy, publication, and formal evidence
  surfaces are canonicalized for exactly 14 PIT-safe indicators. The next
  bounded step is Formal Evidence Provider & Consumer Contract integration of
  the normalized read-only surface; no new indicator, strategy, MA60 policy,
  migration, or Production activation is implied.
- **WS3 — Core V0 research:** A1 is frozen awaiting forward evidence; A2
  confirmed-breakout research and confirmatory validation remain bounded and
  descriptive. A2 Origin Attribution is evidence-only and not promoted. The
  expanded-universe/history route is for future runtime, coverage, and
  qualification evidence; it does not change A1/A2 semantics or algorithms.
  The latest Lifecycle-conditioned expectancy study is descriptive evidence
  only, with bounded join coverage and no strategy filter, score, threshold,
  OOS claim, or policy promotion.
- **WS4 — Release-chain Closure / RC Qualification:** remains an independent
  Owner-authorized lane. `READY_FOR_RELEASE_CHAIN_CLOSURE=YES` and
  `READY_FOR_PRODUCTION_RELEASE=NO`; WS4 does not globally block WS1-WS3.

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

Historical persistence authority is canonically promoted to the V2 canonical
observation chain. The local evidence reconciles 507 symbols and 63,826
canonical OHLCV rows through 2026-08-13. Stock-006A historical bar read and
raw historical price frontend publication are also canonically reconciled;
the detailed current matrix is in the [current-state reconciliation report](reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md).
The next historical slice is adjustment/corporate-action provenance plus the
expanded-universe/history evidence needed for bounded technical and research
qualification. This does not authorize strategy or recommendation semantics.

Historical OHLCV readiness is not historical Topic/System State readiness.
Six months of prices do not by themselves reproduce historical topic scores,
grades, lifecycle transitions, primary/secondary relations, membership, or
other system state. Those require point-in-time topic/reference inputs,
effective-dated relations, policy versions, and provenance.

### Mainline C — Today

Daily Focus, Main Topics, Heating/Cooling, Market Events, and Market Overview
wiring are reconciled on the shared Today Home resource path. The remaining
formal data/read-model gaps are follow-up work. The Today surface must preserve backend-owned order,
metadata, and explicit `FORMAL` / `TEMPORARY` / `PREVIEW` / `UNAVAILABLE`
semantics; missing indices, turnover, narrative, or derived market score must
remain unavailable until a backend-owned contract exists.

`TASK-FE-BE-TODAY-005B-INDEX-CONTRACT` is complete for the contract-only
boundary: official TWSE/TPEx index mappings, raw-date normalization,
provider-neutral typed results, reduced fixtures, and fail-closed tests are in
the canonical repository. It does not authorize persistence, post-close
capture, Home/API/client/frontend wiring, or turnover. Index activation remains
pending source-use approval and protected upstream gates; TPEx turnover remains
blocked pending exact semantics and usage approval.

The 005B index series is archived at the contract boundary with execution state
`WAITING_SOURCE_USE_APPROVAL`; no next Today index implementation is authorized
until source-use approval and the protected upstream gate are closed.

### Mainline E — Stock

Formal stock code/name search and formal topic-filter wiring are complete in
canonical through `TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001`. EOD list,
detail, Explorer, and Drawer wiring are also closed through Stock-005B/005C;
raw historical bar backend and price frontend publication are closed through
Stock-006A. Technical V0 policy/publication and its formal evidence surface
are now a separate mainline; the next execution slice is the Formal Evidence
Provider & Consumer Contract integration. Event markers, institution flow,
narrative, and downstream Opportunity/recommendation contracts remain
separate. Existing search/filter behavior remains backend-owned: the browser
must not infer membership, ranking, sorting, or topic semantics.

## Current Topic execution note

Formal PIT daily state is canonically implemented and bounded-materialized by
migration 0030. The authority is effective-dated membership plus valid
identity/reference/session/calendar bindings; the materialization contains
460 formal, published, non-superseded snapshots for five dates and 4,235
member facts. Formal-only reads exclude research/shadow rows and pass the
bounded replay/immutability checks.

WS1 has now canonicalized additive Structural Role and Score Projection
authority/read infrastructure with fail-closed as-of resolution. It is ready
only for approved Owner-reviewed authority ingestion; no role/projection data
has been populated and Score/Grade remain unpublished. Instrument-to-topic
relations accept `0..N`, so a valid zero-topic instrument is retained without
a placeholder topic. Missing derived data is Topic/as-of scoped and does not
globally fail unrelated Topics or workstreams.

This foundation still does not complete Topic Score, Grade, ranking, breadth,
leadership, concentration, or Lifecycle publication. Those states remain
separately governed as `DEFERRED`, `UNAVAILABLE`, or `SHADOW_ONLY / UNPUBLISHED`
as recorded in the [current-state reconciliation report](reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md).
Lifecycle UI/API integration is committed, but live stage-bearing data remains
unavailable and must stay fail-closed rather than becoming formal publication.
The Topic Overview/Market Map UI is implemented, but formal lanes must remain
empty or explicitly unavailable when the formal derived fields are null.

## Release-hygiene closure checkpoint

The two release-hygiene closure workstreams are closed: A closed the Stock-004
canonical reconciliation and B closed the documentation provider, DB fixture,
and owner/branch disposition blockers. The [A closure report](reports/TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001.md)
and [B closure report](reports/TASK-OPS-DOCUMENTATION-PROVIDERS-OWNER-DISPOSITION-AND-DB-INTEGRATION-FIXTURE-CLOSURE-001.md)
remain the evidence owners.

The `BLK-HYGIENE-01/02/03/04` blockers are closed:
`BLK_HYGIENE_01_CLOSED=YES`, `BLK_HYGIENE_02_CLOSED=YES`,
`BLK_HYGIENE_03_CLOSED=YES`, and `BLK_HYGIENE_04_CLOSED=YES`.
`READY_FOR_RELEASE_CHAIN_CLOSURE=YES`; `READY_FOR_PRODUCTION_RELEASE=NO`.
Owner dirty/untracked state remains preserved and classified. Release-chain
closure remains an independent Owner-authorized WS4 lane; WS1-WS3 may continue
within their bounded contracts. This checkpoint does not change `NEXT_TASK`,
authorize Production mutation, or replace the product phase routing below.

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

- Stock-004 formal search and topic-filter wiring are canonicalized; the
  affected API/frontend boundary is closed under the [reconciliation
  report](reports/TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001.md).
- Stock-005B/005C EOD presentation and Explorer/Drawer wiring are also closed;
  Stock-006A raw historical bar and price frontend publication are closed.
- Finish technical publication, event/corporate-action markers, institution
  flow, narrative, and downstream Opportunity/recommendation contracts without
  inventing browser-side values.
- Preserve backend ordering and formal/preview/unavailable disclosure.

### Today

- Define the next formal-data contract for the remaining Market Overview gaps
  on the shared Home resource; existing Market Overview wiring is complete.
- Keep Daily Focus and Market Events as backend-owned projections. Temporary
  topic-snapshot-derived content must remain labelled `TEMPORARY`; it is not
  promoted to formal data by frontend wiring.
- Add missing indices, turnover, narrative, or score only through an approved
  backend-owned contract and read model.

### Topic page

- PIT membership and daily formal snapshots are already materialized under
  migration 0030; this closes the bounded state foundation, not the derived
  publication surface.
- Provide formal Topic Score/Grade, ranking/breadth/leadership/concentration,
  Lifecycle history, Today Topic Map `S/A/B/D`, and missing detail fields
  through separately authorized backend work.
- The large-group accordion same-row height coupling bug is complete via the
  frontend-only layout fix; topic semantics and lifecycle derivation remain
  unchanged.

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

REC-A1 Dataset/Protocol Freeze is canonically closed as research-only with
owner-accepted residual uncertainty. A1 is frozen awaiting forward evidence.
A2 confirmed-breakout formation remains frozen while entry/path and
invalidation research/confirmatory validation stay bounded and descriptive.
A2 Origin Attribution is evidence-only and not promoted. Opportunity remains
shadow wiring; no candidate has an accepted strategy, production entry/stop,
or recommendation publication. Expanded-universe/history work is evidence
expansion and qualification routing only; it does not change strategy
semantics or algorithms.

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
override the 2026-08-22 Parallel Plan or its phase priorities. Do not edit or infer `NEXT_TASK` from
this document.

## Stock-005B canonical reconciliation checkpoint

`TASK-FE-BE-STOCK-005B` is canonically reconciled: the additive StockEodRead
backend/API projection is present on the existing list/detail routes, with
OpenAPI and generated client artifacts aligned. The next Stock slice is
`TASK-FE-BE-STOCK-005C` for Explorer/Drawer EOD wiring; technical detail remains
Historical-dependent and canonical turnover remains nullable when upstream
turnover_amount is unavailable.

## Stock-005C canonical frontend checkpoint

`TASK-FE-BE-STOCK-005C` is complete for the formal EOD frontend vertical:
Explorer and the shared Drawer consume `StockEodRead` render-only, preserve
intraday/EOD separation, fail closed for missing formal EOD, and keep Preview
explicit. The existing Drawer interaction shell and advanced topic filter are
regression-protected. Technical detail/publication, timeline/history,
institution flow, narrative, Opportunity, and recommendation remain separate
follow-up work.

## Canonical-to-production delivery flow

Every delivery follows the shared lifecycle:

`IMPLEMENTED` -> `VALIDATED` -> `CANONICALIZED` -> `RELEASE_CANDIDATE` -> `PRODUCTION_RELEASED` -> `POST_DEPLOY_VERIFIED`.

Roadmap status must distinguish `Implemented`, `Canonicalized`, `Release
Candidate`, and `Production Released`; capability `COMPLETE` and test `PASS`
do not advance a milestone by themselves. Canonicalization requires the
approved files at a committed canonical SHA and a source-to-canonical SHA
mapping. An isolated PASS is source evidence only, and a dirty-worktree PASS is
diagnostic only. A clean candidate must be checked out from that exact SHA.

Promotion routing is: canonical reconciliation -> clean exact-SHA candidate
validation -> owner-authorized Production promotion -> post-deploy public and
revision verification. Release readiness must cover exact-SHA API/Web
provenance, fail-closed behavior, migration/data state, rollback readiness, and
deployed revision verification. Local migration/data/materialization evidence
does not establish Production readiness or visibility. `PUSH_REMOTE=NO` and
`DEPLOY=NO` are safety boundaries, not terminal success states.

`NEXT_TASK` is changed only by the Owner. Agents may record a recommendation,
but may not promote a recommendation into an authorized next task.

## Governance hardening checkpoint

The execution flow may advance to a release candidate only when clean source
state and reproducible lockfile-derived dependency state both pass. Commit-
preserving canonical promotion is preferred; shared dirty-file hunk exceptions
require explicit attribution and HEAD/index/worktree audit evidence. Before
promotion, the repository/worktree/remote hygiene gate must classify divergence,
stale or orphaned worktrees, uncommitted dependencies, and provenance gaps.
Validation count deltas must carry explicit pre/post attribution with
PASS/FAIL/SKIP/XFAIL/DESELECTED kept separate. This is an execution checkpoint,
not a release runbook or authorization to clean owner state.
