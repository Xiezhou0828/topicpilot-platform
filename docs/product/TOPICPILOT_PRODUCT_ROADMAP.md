# TopicPilot product roadmap

**Status:** `CANONICAL / HIGH-LEVEL PRODUCT ROUTING`
**Last reviewed:** `2026-08-22`

This document owns product-level routing, sequencing, and deferrals. It is not
a work-order list, implementation permission, or date promise. Current
execution status belongs in [docs/ROADMAP.md](../ROADMAP.md); startup/handoff
navigation belongs in [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md); product
vision and frozen semantics belong in the [Product Direction and Surfaces
Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).

## Product position

TopicPilot is a Taiwan Theme Intelligence platform. Topic strength, lifecycle,
rotation, history, and explainable evidence are the product center. Stock
selection, Today summaries, watchlists, technical evidence, and Opportunity
are downstream decision-support surfaces; Recommendation does not define Topic
Score or the product identity.

## Current product routing

| Product area | Current state | Product routing |
|---|---|---|
| DATA / Reference / Post-Close | `COMPLETE / PROTECTED BASELINE` | Mainline A is complete through TASK-DATA-REF-009A with G0/G1/G2/G3/Canary PASS; 2026-08-13 TPE 313 + TWO 193 = 506/506 and `DOWNSTREAM_READY=true`. It is a protected dependency, not the general product critical path. |
| Historical | `OHLCV AUTHORITY + STOCK-006A COMPLETE / RESEARCH FOLLOW-UP` | V2 canonical observation authority owns 63,826 OHLCV rows; bounded historical bar read and raw price frontend publication are canonicalized. Adjustment/corporate-action continuity and historical Topic/System State remain separate research/data contracts. |
| Today | `WIRING COMPLETE / FORMAL DATA FOLLOW-UP` | Daily Focus, Main Topics, Heating/Cooling, Market Events, and Market Overview wiring are complete on the shared Home resource; formal indices, turnover, narrative, and derived market score remain unavailable or contract-only. |
| Stock | `SEARCH/FILTER + EOD + RAW HISTORY + TECHNICAL V0 EVIDENCE SURFACE` | Formal search/filter, EOD Explorer/Drawer wiring, historical bar backend, raw historical price frontend, and the Technical V0 policy/publication/evidence surface are canonicalized; the Formal Evidence Provider & Consumer Contract is the next bounded integration. Event markers, institution flow, narrative, Opportunity, and recommendation remain separate contracts. |
| Topic | `PIT DAILY STATE + WS1 DERIVED AUTHORITY INFRASTRUCTURE / LIFECYCLE READ SURFACE / P0 PUBLICATION FOLLOW-UP` | Migration 0030 materializes bounded formal PIT snapshots/member facts; WS1 adds additive Structural Role/Score Projection authority infrastructure and a fail-closed Lifecycle read surface. Owner-reviewed ingestion and live stage-bearing data remain bounded, and Score, Grade, ranking/breadth/leadership/concentration, Lifecycle history, formal Map lanes, and detail fields remain separately gated. |

Stock EOD status: `TASK-FE-BE-STOCK-005B` provides the additive
`StockEodRead` projection and `TASK-FE-BE-STOCK-005C` wires it into the formal
Explorer/Drawer path. Technical fields remain Historical-dependent.

| Favorites | `P3 UI POLISH` | Keep watchlist/market-context semantics; polish shared state and Drawer behavior. |
| Opportunity | `SHADOW / RESEARCH EVIDENCE ONLY` | Bounded shadow wiring exists; A1 is frozen pending forward evidence and A2 remains bounded research. No accepted strategy, production entry/stop, or recommendation publication is implied. |
| Intraday | `P4 DEFERRED` | Wait for formal source, freshness, scheduling, and update semantics. |
| AI Studio | `P5 DEFERRED` | Follow the core product, data governance, and research contracts first. |

## Release-hygiene closure boundary

The 2026-08-16 release-hygiene A/B closure workstreams are closed. The four
tracked blockers (`BLK-HYGIENE-01/02/03/04`) are closed, and the linked closure
reports ([A](../reports/TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001.md),
[B](../reports/TASK-OPS-DOCUMENTATION-PROVIDERS-OWNER-DISPOSITION-AND-DB-INTEGRATION-FIXTURE-CLOSURE-001.md)) remain the detailed evidence owners.
`READY_FOR_RELEASE_CHAIN_CLOSURE=YES`
and `READY_FOR_PRODUCTION_RELEASE=NO`. Owner dirty/untracked state remains
preserved and classified. Release-chain closure remains an independent WS4
Owner-authorized lane; WS1-WS3 continue under their separate bounded
contracts. This product roadmap does not set or alter `NEXT_TASK`.

## Product priorities

| Priority | Product intent |
|---|---|
| **P0 Product Completion** | Complete Stock, Today, and Topic formal data and UI. |
| **P1 Historical + Recommendation research** | Establish replayable historical evidence and review candidate strategies. |
| **P2 Data Management + News + Discovery** | Build canonical master-data/admin and News/Event foundations, then advisory discovery. |
| **P3 Opportunity + Favorites polish** | Improve bounded Opportunity presentation and Favorites usability. |
| **P4 Intraday** | Add quote updates only after ownership and freshness are formalized. |
| **P5 AI Studio** | Add the multi-agent research experience after its prerequisites. |

These priorities describe product dependency and investment order, not a global
serialization lock. Independent workstreams may proceed in parallel when their
contracts, schemas, and write sets do not conflict.

## Parallel Plan guardrail

WS1 Topic Derived Intelligence, WS2 Technical V0, and WS3 Core V0 research may
advance under their own evidence and authority contracts. WS4 Release-chain
Closure / RC Qualification remains an independent owner-authorized lane. A
workstream's completion or readiness does not establish overall release
readiness, and research evidence does not become strategy authority without the
documented review and promotion gates.

## SDLC milestone vocabulary

Roadmap milestones must keep these states distinct:

| State | Meaning |
|---|---|
| `IMPLEMENTED` | The scoped capability exists in source; it is not yet canonical or released. |
| `CANONICALIZED` | The approved capability is committed in the canonical repository with provenance. |
| `RELEASE_CANDIDATE` | One exact committed SHA passed clean-candidate release checks. |
| `PRODUCTION_RELEASED` | Owner-authorized promotion is complete with API/Web, migration/data, and revision evidence. |

`POST_DEPLOY_VERIFIED` is the subsequent public/runtime verification state.
`COMPLETE` or `PASS` wording in a capability report must not be used as a
shortcut for any of these roadmap states. Product routing remains separate from
release promotion, and this roadmap does not authorize `NEXT_TASK`, deployment,
Production data, or a source-of-truth cutover.

## Historical and Recommendation route

Recommendation candidates are deliberately `RESEARCH CANDIDATE` rather than
committed strategies:

- A1 — Pre-Breakout;
- A2 — Confirmed Breakout;
- A3 — Strong Pullback / Retest;
- Catch-up / rotation.

The product gate is:

`Historical/Proxy Backtest` → `Point-in-time/Walk-forward` → `Strategy Review`
→ `Accepted/Rejected` → `Formal Contract` → `Production Implementation`.

`HIST-001 COMPLETE` is not a production implementation gate. Historical OHLCV
readiness is distinct from historical topic/system-state readiness: a full
price window cannot by itself replay historical topic score, grade, lifecycle,
membership, or relation state. Candidate results must retain point-in-time
inputs, no-look-ahead evidence, policy/parameter versions, and explainability.

REC-A1 Dataset/Protocol Freeze is canonically closed as research-only with
owner-accepted residual uncertainty. Core V0 research is active within bounded
evidence routes: A1 is frozen awaiting forward evidence; A2 confirmed-breakout
formation remains frozen while entry/path and invalidation research and
confirmatory validation continue. A2 Origin Attribution is evidence-only and
not promoted. The latest Lifecycle-conditioned expectancy study is descriptive
evidence with bounded join coverage; it creates no strategy filter, score,
threshold, OOS claim, or policy promotion. No candidate has an accepted
strategy, production entry/stop, or recommendation publication.

## Data Management / Admin roadmap

The governed master-data product should support:

- adding stocks;
- adding, updating, and removing stock–topic relations;
- primary and secondary topic classification;
- relation weights;
- immutable audit history, actor, source, and effective time.

This is a canonical-data management capability, separate from read-only Admin
and Data Explorer surfaces. It requires its own authorization, API/schema
contract, validation, and audit evidence.

## News, Events, and AI discovery

Build a source-grounded News/Event foundation before AI discovery. The
foundation must preserve source identity, publication time, event type,
affected topic/stock references, provenance, deduplication, and review state.

AI Topic Discovery and topic-correction suggestions are advisory layers. AI may
propose a topic, rename, merge, relation, weight, or correction, but AI must not
directly change canonical taxonomy, hierarchy, stock–topic relations, primary/
secondary state, weights, or audit history.

## V1 bridge / partial retirement

V1 is `LEGACY BRIDGE / PARTIAL RETIREMENT`. New product investment routes to V2;
V1 remains protected because it still supplies operational capabilities not yet
fully replaced. Preserve:

- `price_engine.py`: TWSE MIS + Yahoo fallback, Sheet/TSV input, and Google
  Sheets `H:I:J:K` quote write-back;
- `ta_engine.py`: Yahoo approximately six-month OHLCV and MA/Market Structure/
  Volume/RS/Pullback technical factors connected to Sheets/CSV;
- `radar.py`: Google Sheets groups/stocks/relations/synonyms, RSS/news, topic
  heat/warming/cooling, related stocks, sentiment, interpretation, AI題材雷達,
  and historical V2 output;
- legacy master-data and scheduling bridges.

Retire a bridge only after the V2/PostgreSQL/FastAPI replacement for that
capability has passed dual-run/parity and an explicit cutover decision. V1 is
not the formal authority for new V2 documentation, and its old source-of-truth
wording must not be copied into current roadmap status.

## Product boundary rules

1. `CURRENT` means the product route is active or already evidenced; it does
   not authorize a runtime change in this document.
2. `RESEARCH CANDIDATE` requires the full research-to-contract gate above.
3. `SHADOW` means explicitly non-production publication and must remain visible
   in API/UI state.
4. `DEFERRED` means intentionally delayed, not silently started by another
   workstream.
5. Product roadmap text never changes `NEXT_TASK`, taxonomy, relations, scoring,
   scheduler state, or Production data.

## Navigation

- Execution sequence and detailed status: [docs/ROADMAP.md](../ROADMAP.md).
- Startup and current handoff: [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md).
- Current-state cold-start reconciliation: [handoff report](../reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md).
- Product semantics: [Product Direction and Surfaces
  Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).
- Detailed evidence: [documentation index](../DOCUMENTATION_INDEX.md), work
  orders, and reports.
