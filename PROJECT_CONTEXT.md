# TopicPilot current project context

**Status:** `CURRENT STARTUP / HANDOFF NAVIGATION`
**Last reviewed:** `2026-08-22`

This file is deliberately short. It tells a contributor where the current
authority lives and what is true at handoff; it is not a duplicate product,
architecture, schema, or work-order authority.

## Read first

1. [Collaboration and safety rules](AGENTS.md)
2. [Execution roadmap](docs/ROADMAP.md)
3. [High-level product roadmap](docs/product/TOPICPILOT_PRODUCT_ROADMAP.md)
4. [Architecture authority map](docs/architecture/README.md)
5. [Accepted product surfaces contract](docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md) — owner-retained semantic source; repository canonicalization status is tracked separately
6. [Documentation index](docs/DOCUMENTATION_INDEX.md)

## Canonical boundary

- Canonical repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
- All permanent changes belong in this repository. Task/worktree folders are
  isolated execution areas and are not formal authority.
- Do not modify application code, schema, migration, runtime/deploy config,
  Production data, or `NEXT_TASK` during a documentation handoff.
- `PRODUCT_SURFACES_AND_UX_CONTRACT.md` declares accepted/frozen product
  semantics when read, but it is currently owner-untracked in this canonical
  checkout. Semantic authority and repository canonicalization are separate;
  this reconciliation does not promote or edit that file.
- V1 is `LEGACY BRIDGE / PARTIAL RETIREMENT`; V2 is the active platform path.
  Legacy retirement requires V2 replacement plus dual-run/parity and an
  explicit cutover decision.

## Current Parallel Plan handoff

- **Mainline A — DATA / Reference / Post-Close:** complete through
  `TASK-DATA-REF-009A`. G0, G1, G2, G3, and Canary are current `PASS` evidence;
  the 2026-08-13 TPE 313 + TWO 193 date-effective universe reconciled to
  `506/506`, with `DOWNSTREAM_READY=true`. A is no longer the general product
  development critical path. Re-run its protected gates only when the impact
  reaches a protected boundary.
- **Mainline B — Historical:** historical persistence authority is canonicalized
  in the V2 canonical observation chain. The reconciled local evidence contains
  507 symbols and 63,826 canonical OHLCV rows from 2026-02-02 through
  2026-08-13; the 63,826-row authority promotion and the bounded Stock-006A
  read/publication closures are linked from the [current-state reconciliation
  report](docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md).
  Raw observed adjustment state and corporate-action continuity remain deferred.
  Historical OHLCV readiness is not historical Topic/System State readiness:
  prices cannot fully replay historical topic scores, grades, lifecycle, or
  relation state without point-in-time inputs and lineage.
- **Mainline C — Today:** Daily Focus, Main Topics, Heating/Cooling, Market
  Events, and Market Overview wiring are reconciled to the shared Home resource
  path. Remaining follow-up is formal-data/read-model authority for indices,
  turnover, narrative, volume trend, and derived market score; temporary or
  partial Home data must stay visibly temporary, preview, or unavailable.
  `TASK-FE-BE-TODAY-005B-INDEX-CONTRACT` now provides the typed, fail-closed
  TWSE/TPEx index contract and source-shaped fixtures. Index persistence,
  post-close capture, Home/API projection, and frontend rendering remain
  blocked by source-use approval and upstream activation gates; turnover remains
  blocked by the TPEx semantic/usage authority gap.
  The Today Market Index series is complete at the contract boundary and
  `WAITING_SOURCE_USE_APPROVAL`; Product capability is not complete. No
  persistence, post-close, Home/API, frontend, or turnover implementation is
  authorized from this closure.
- **Mainline E — Stock:** formal code/name search and formal topic-filter wiring
  are canonicalized through `TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001`.
  EOD list/detail and Explorer/Drawer wiring are also canonicalized through
  `TASK-FE-BE-STOCK-005B` and `TASK-FE-BE-STOCK-005C`. Historical bar backend
  and raw historical price frontend publication are canonicalized through
  Stock-006A. Technical V0 is now a separate policy/publication/evidence
  mainline; event/corporate-action markers, institution flow, narrative,
  Opportunity, and recommendation remain separate contracts.

- **WS1 — Topic Derived Intelligence / Structural Role & Score Projection:**
  Owner decision D001 is canonicalized, and the additive Structural Role/
  Score Projection read infrastructure and fail-closed as-of resolvers are
  canonicalized in the [WS1 policy closure](docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002.md)
  and [WS1 implementation closure](docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003.md).
  The next route is initial authority ingestion, restricted to approved,
  Owner-reviewed, effective-dated role data and approved Score Projection V1
  data. Role and projection records remain unpopulated; Score/Grade remain
  unpublished. Instrument-to-topic relation cardinality is accepted as `0..N`:
  a zero-topic instrument is valid, must not be dropped, and must not create a
  placeholder topic. Missing projection is Topic/as-of-scoped and does not
  globally fail unrelated Topics or derived lanes.
  The Topic Lifecycle API/frontend contract and fail-closed disclosure path are
  now committed in `c5b2239`. Current live acceptance remains pending: the
  canonical API has not produced stage-bearing rows, so the UI must continue to
  show `INSUFFICIENT_DATA`/unavailable states and must not infer a Lifecycle
  stage. Forward Shadow evidence accumulation is ready only in the isolated
  runtime; formal promotion remains blocked.

- **WS2 — Stock Technical V0:** policy and publication contracts are
  canonicalized with separate technical-result, event-authority, and
  publication dimensions. The latest inventory confirms exactly 14 formal,
  PIT-safe indicators over the 507-instrument, 63,826-row evidence surface;
  formal evidence publication is currently available for 0 instruments, with
  85 `AVAILABLE_WITH_LIMITATION` and 422 blocked at the current surface, with
  no calculation errors.
  The next bounded route is the Owner-authorized Formal Evidence Provider &
  Consumer Contract integration of the existing normalized read-only surface;
  it is not a new indicator, strategy, recommendation, migration, or
  Production activation. See the [publication closure](docs/reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818.md)
  and [indicator/evidence-surface inventory](docs/reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819.md).

- **WS3 — Core V0 research:** A1 quality-filter confirmatory evidence is
  `FROZEN_AWAITING_FORWARD_EVIDENCE`; the seven frozen candidates were not
  promoted. A2 confirmed-breakout formation remains frozen; entry and
  invalidation research/confirmatory evidence is bounded and descriptive, with
  no provisional entry/stop or Production rule. The [A1 confirmation](docs/reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818.md),
  [A2 research](docs/reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819.md),
  and [A2 confirmatory validation](docs/reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-INVALIDATION-CANDIDATE-CONFIRMATORY-VALIDATION-20260819.md)
  remain research evidence, not strategy authority. The parallel
  `TASK-WS3-R-A2-ORIGIN-ATTRIBUTION-20260819` result is
  `EVIDENCE_ONLY_NOT_PROMOTED`: direct-entry A2 remains valid, A1-origin
  context is not supported as a formation requirement, and no strategy
  semantic is changed. The 96-stock [expanded-universe reference pack](docs/reports/TASK-INSTRUMENT-UNIVERSE-96-STOCK-EXPANSION-REFERENCE-PACK-AND-RUNTIME-HANDOFF-20260819.md)
  is staging-only toward a 603 candidate universe; runtime identity/security
  validation, historical OHLCV bootstrap, coverage/quality checks, and
  expanded-universe/history evidence qualification remain future bounded
  routes. No threshold retuning or A1/A2 algorithm change is authorized.
  The latest committed WS3 conditional-expectancy study is
  `COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS`: Lifecycle conditioning is
  descriptive evidence with bounded join coverage, not a strategy filter,
  score, threshold, OOS claim, or production policy.

- **WS4 — Release-chain Closure / RC Qualification:** remains independent.
  The [WS4 canonicalization closure](docs/reports/TASK-OPS-WS4-RELEASE-CANDIDATE-QUALIFICATION-CANONICALIZATION-20260816.md)
  records `READY_FOR_RELEASE_CHAIN_CLOSURE=YES` and
  `READY_FOR_PRODUCTION_RELEASE=NO`; it does not globally block WS1-WS3 and
  does not authorize a new RC qualification, Production promotion, deployment,
  scheduler activation, or `NEXT_TASK` change.

- **Topic formal publication boundary:** formal PIT daily state remains
  bounded-materialized by migration 0030: 460 published, non-superseded formal
  snapshots for five dates and 4,235 member facts. WS1 now has canonicalized
  authority infrastructure, but no role/projection data population or Score/
  Grade publication has occurred. Ranking, breadth, leadership, concentration,
  and formal Lifecycle publication remain separately governed; the Topic
  Overview/Market Map UI must fail closed when those fields are null. The
  Lifecycle read surface is integrated, but current live data remains
  `INSUFFICIENT_DATA`/unavailable rather than a published stage.

## Product surface gaps and deferrals

- Topic page still needs formal publication for Score/Grade, Today Topic Map
  `S/A/B/D` lanes, ranking/breadth/leadership/concentration, formal Topic
  Lifecycle history, and missing detail fields. The formal PIT snapshot
  foundation is present, but it does not imply those derived capabilities.
- The Topic Overview/Market Map UI and field-level disclosure boundary are
  implemented; formal API mode does not synthesize missing score, grade,
  ranking, or lifecycle values. Do not treat `TopicSource=api` as proof that
  every Topic field is formally published.
- Favorites is mainly UI polish and shared Drawer/favorite-state cleanup.
- REC-A1 Dataset/Protocol Freeze is canonicalized as a research-only,
  owner-accepted residual-risk dataset. Core V0 research has progressed through
  A1/A2 attribution, entry/invalidation research, and bounded confirmatory
  validation; those results remain evidence-only and do not accept a strategy.
- Opportunity keeps its shadow/production wiring boundary. A1 remains frozen
  pending forward evidence and A2 remains bounded research; no entry/stop,
  strategy, or recommendation publication is complete.
- Intraday quote update is deferred. AI Studio is deferred.
- Master Data/Admin, News/Event foundation, AI Topic Discovery, and correction
  suggestions follow the sequence in the execution and product roadmaps. AI may
  suggest; it may not directly change canonical taxonomy or relations.

## Priority and parallelism

The product priority order is P0 Product Completion, P1 Historical +
Recommendation research, P2 Data Management + News + Discovery, P3 Opportunity
+ Favorites polish, P4 Intraday, and P5 AI Studio. This is a product priority
and dependency order, not a global serialization lock. Independent workstreams
may run in parallel when their contracts and write sets do not conflict.

Recommendation candidates A1 Pre-Breakout, A2 Confirmed Breakout, A3 Strong
Pullback/Retest, and Catch-up/rotation are `RESEARCH CANDIDATE` only. The
required path is Historical/Proxy Backtest → Point-in-time/Walk-forward →
Strategy Review → Accepted/Rejected → Formal Contract → Production
Implementation. `HIST-001` completion does not authorize production
recommendation implementation.

## Stale-document rule

Old `TASK-LIVE-002 = WAITING_LIVE_VALIDATION`, provider-activation blockers,
old migration-head summaries, repository-status snapshots, and old Opportunity
“next gate” wording are historical evidence unless the current authority above
links them as active. Do not use them to override this 2026-08-22 handoff.
The repository does not currently contain a separate
`docs/DOCUMENTATION_AUTHORITY_INDEX.md` or
`docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md`; do not create a parallel copy.

## Stock-005B canonical reconciliation checkpoint

`TASK-FE-BE-STOCK-005B` is now canonically reconciled. The existing Stock list
and detail routes expose the additive nullable `StockEodRead` projection;
Explorer/Drawer presentation is also canonically reconciled by
`TASK-FE-BE-STOCK-005C`. Technical detail remains Historical-dependent, and
canonical turnover remains nullable when no accepted canonical turnover
observation exists.

## Stock-005C frontend EOD wiring checkpoint

`TASK-FE-BE-STOCK-005C` is complete: the V2 Stock Explorer and shared Drawer
consume the canonical `StockEodRead` fields for completed-session presentation,
including null-safe status, trading date, OHLC, previous close, change,
volume, turnover, and source/as-of metadata. Intraday latest quote behavior
remains separate; Preview is explicit and never a formal API fallback. The
Drawer shell and advanced topic filter remain preserved. Technical detail,
timeline/history, institution flow, narrative, Opportunity, and
recommendation remain separate follow-up contracts.

## Current canonical handoff summary

**Current canonical baseline:** this handoff is based on canonical HEAD at the
2026-08-22 boundary plus the committed capability closures listed in the
[current-state reconciliation report](docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md).
The report and its machine-readable
[evidence ledger](docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001/current-state-evidence-ledger.json)
are the detailed current-state evidence owners. No owner-untracked report is
required to reconstruct this summary.

**Active workstreams:** WS1 Structural Role/Score Projection authority
ingestion and Lifecycle forward-shadow accumulation, WS2 Technical V0 formal
evidence consumer integration, WS3 bounded Lifecycle-conditioned expectancy
research plus forward and expanded evidence routing, and independent WS4
release-chain/RC qualification. Stock-004/005B/005C/006A, Historical
persistence authority promotion, Topic PIT daily-state materialization, and
REC-A1 Dataset/Protocol Freeze remain closed at their documented boundaries.
No workstream completion implies overall release readiness, and no unapproved
next task is opened.

**Capability matrix:**

| Area | Current canonical state | Remaining boundary |
|---|---|---|
| Stock | Search/filter, EOD, historical bar backend, raw historical price frontend, and the Technical V0 formal evidence surface are canonicalized at their documented boundaries | Formal Evidence Provider & Consumer Contract integration, event/corporate-action markers, institution flow, narrative, Opportunity, and recommendation remain separate |
| Today | Home/Today wiring is canonicalized with explicit partial/temporary semantics | Formal indices, turnover, narrative, derived market score, and complete formal market data are not published |
| Topic | PIT membership and daily formal state are implemented and bounded-materialized: 460 snapshots and 4,235 member facts; WS1 authority infrastructure and Lifecycle read surface are canonicalized, with live stage data still unavailable | Score, Grade, ranking, breadth, leadership, concentration, formal Lifecycle history, and complete Topic Detail remain separately gated/unpublished |
| Historical | V2 canonical observation chain owns 63,826 OHLCV rows | OHLCV price history is not historical Topic/System State; adjustments and corporate-action continuity remain deferred |
| REC-A1 / Opportunity | REC-A1 freeze is canonicalized research-only; Opportunity is bounded shadow wiring; A1/A2 evidence remains research-only | A1 forward evidence, A2 bounded review/strategy acceptance, and recommendation publication are incomplete |

**Release and next dependency:** `BLK-HYGIENE-01/02/03/04` are closed and
`READY_FOR_RELEASE_CHAIN_CLOSURE=YES`; `READY_FOR_PRODUCTION_RELEASE=NO`.
There is no committed release candidate, production release, post-deploy
verification, runtime revision, push, or merge in this handoff. Release-chain
closure remains an independent Owner-authorized lane and does not globally
block WS1-WS3; `NEXT_TASK` is unchanged.

## Release-hygiene closure checkpoint

The two release-hygiene closure workstreams are closed. Workstream A closed
the Stock-004 canonical reconciliation; workstream B closed the documentation
provider, DB integration fixture, and owner/branch disposition blockers. See
the [A closure report](docs/reports/TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001.md)
and [B closure report](docs/reports/TASK-OPS-DOCUMENTATION-PROVIDERS-OWNER-DISPOSITION-AND-DB-INTEGRATION-FIXTURE-CLOSURE-001.md)
for the evidence.

The `BLK-HYGIENE-01/02/03/04` blockers are closed:
`BLK_HYGIENE_01_CLOSED=YES`, `BLK_HYGIENE_02_CLOSED=YES`,
`BLK_HYGIENE_03_CLOSED=YES`, and `BLK_HYGIENE_04_CLOSED=YES`.
`READY_FOR_RELEASE_CHAIN_CLOSURE=YES`; `READY_FOR_PRODUCTION_RELEASE=NO`.
Owner dirty/untracked state remains preserved and classified. Release-chain
closure remains an independent Owner-authorized lane; WS1-WS3 may continue
within bounded contracts, and this handoff does not change `NEXT_TASK`.

## SDLC promotion architecture

The shared lifecycle is:

`IMPLEMENTED` -> `VALIDATED` -> `CANONICALIZED` -> `RELEASE_CANDIDATE` -> `PRODUCTION_RELEASED` -> `POST_DEPLOY_VERIFIED`.

Capability completion is not canonicalization, and canonicalization is not
release or public visibility. `FINAL_STATUS=COMPLETE`,
`CAPABILITY_STATUS=COMPLETE`, and passing tests describe only the claimed task
or validation boundary. The canonical repository is the single authority;
isolated PASS results remain source evidence until an explicit source-to-
canonical SHA mapping is recorded. A clean release candidate must be produced
from that committed exact SHA in a clean checkout.

Promotion requires the applicable API/Web exact-SHA provenance, fail-closed
behavior, migration/data evidence, rollback boundary, and deployed-revision
verification. Local migration, data, or materialization results do not make a
capability Production-ready or Production-visible. The release path is an
owner-authorized promotion stage, not an automatic consequence of capability
completion.

## New work startup read set

For a new conversation or work item, read in this order: `AGENTS.md`, this
`PROJECT_CONTEXT.md`, the related roadmap and work order, and the latest
capability-closure report. A release task additionally reads the applicable
release-readiness and canonical-closure reports before touching its write set.
For a cold-start reconstruction, also read the [current-state cold-start
reconciliation report](docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md)
and its linked evidence ledger; those committed files are sufficient without
chat memory or owner-untracked reports.
`NEXT_TASK` remains Owner-controlled; an agent may recommend a task but may not
change the roadmap's authorized next task.

## Hardened promotion evidence

Final candidate evidence requires separate `CLEAN_SOURCE_STATE=PASS` and
`REPRODUCIBLE_DEPENDENCY_STATE=PASS` from a lockfile-derived or approved
container/CI environment; a borrowed dependency directory is diagnostic only.
Canonical promotion prefers validated commit-preserving reconciliation. Any
shared-dirty-file hunk exception must preserve HEAD/index/worktree agreement,
report its reason and audit fields, and leave no task-owned residual diff.

Repository/worktree/remote hygiene is a checkpoint before promotion, covering
divergence, local/remote-only commits, stale or orphaned worktrees,
unattributed dirty/untracked state, and source-to-canonical provenance. An
unhealthy checkpoint requires owner disposition and does not authorize cleanup.
Validation count changes must report pre/post counts, delta, explicit reason,
and separate PASS/FAIL/SKIP/XFAIL/DESELECTED outcomes; unexplained reductions
block the claim.
