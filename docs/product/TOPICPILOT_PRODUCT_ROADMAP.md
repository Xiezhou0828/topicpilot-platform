# TopicPilot product roadmap

**Status:** `CANONICAL / HIGH-LEVEL PRODUCT ROUTING`
**Last reviewed:** `2026-08-14`

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
| Historical | `HIST-001 COMPLETE / RESEARCH FOLLOW-UP` | Build six-month local/full seed, provenance, and technical/recommendation inputs. Price history alone does not recreate historical Topic/System State. |
| Today | `WIRING COMPLETE / FORMAL DATA FOLLOW-UP` | Daily Focus and Market Events isolated wiring is complete; Market Overview and formal-data gaps continue through the execution roadmap. |
| Stock | `ISOLATED IMPLEMENTATION COMPLETE / RECONCILIATION FOLLOW-UP` | Formal search and formal topic filter are complete in isolation; reconcile and finish EOD, change %, Drawer, and detail data. |
| Topic | `P0 PRODUCT COMPLETION` | Formal Today Topic Map S/A/B/D publication, Topic Lifecycle data, detail fields, and accordion layout coupling remain. |
| Favorites | `P3 UI POLISH` | Keep watchlist/market-context semantics; polish shared state and Drawer behavior. |
| Opportunity | `SHADOW / BOUNDED WIRING` | Continue shadow/production wiring without claiming production recommendation publication. |
| Intraday | `P4 DEFERRED` | Wait for formal source, freshness, scheduling, and update semantics. |
| AI Studio | `P5 DEFERRED` | Follow the core product, data governance, and research contracts first. |

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
- Product semantics: [Product Direction and Surfaces
  Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).
- Detailed evidence: [documentation index](../DOCUMENTATION_INDEX.md), work
  orders, and reports.
