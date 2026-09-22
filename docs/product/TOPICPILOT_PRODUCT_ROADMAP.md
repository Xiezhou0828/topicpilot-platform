# TopicPilot product roadmap

**Status:** `CANONICAL / ACTIVE`
**Last reviewed:** `2026-09-22`
**Evidence baseline before this documentation commit:** canonical `main` at `f88ff51`

This document owns product-level routing, sequencing, and deferrals. Detailed
execution order belongs in [the execution roadmap](../ROADMAP.md), and settled
product principles belong in [the decision register](TOPICPILOT_PRODUCT_DECISIONS.md).
Historical reports remain evidence and are not rewritten by this reconciliation.

## Product position

TopicPilot is a Taiwan-equity research workflow that moves from market context
to Topics, from Topics to stocks, and from stocks to evidence-backed
Opportunities. It is not a black-box recommendation product. Formal facts,
research findings, and user-facing explanations remain distinct layers.

## 2026-09-22 routing model

The roadmap now uses three product streams. A establishes formal authority, B
turns that authority into customer surfaces, and C tests evidence before it is
allowed to influence product decisions.

| Stream | Route | Current disposition | Product completion condition |
|---|---|---|---|
| **A — Formal Data / Topic Engine** | A1 Current Formal Pipeline → A2 Historical Data Foundation → A3 Formal Historical Continuity | Current-date formal Topic scope can be materialized at 107/107 in committed integration evidence; the complete result is not yet integrated into `main`. Production raw history starts on 2026-08-13 and is discontinuous. Formal derived history is incomplete. | Exact implementation and authority artifacts are integrated into `main`, validated there, released through the governed path, and independently read back. |
| **B — User-facing Product** | B1 Today → B2 Opportunity → B3 Topic → B4 Stock | Today, Topic, Stock, institutional-flow, and Opportunity capabilities exist at different canonicalization levels. The surfaces must continue to fail closed where formal inputs are missing. | Each surface consumes backend-owned formal contracts from `main`; no browser-side reconstruction of business semantics; Production visibility is separately proven. |
| **C — Decision Intelligence** | C1 Statistical Research → C2 Feature Validation → C3 Decision Layer | Research and validation evidence exist, but research history is not formal history and evidence is not automatically policy. | A reviewed result is accepted or rejected, then receives a versioned formal contract and canonical implementation before affecting a decision layer. |

### A — Formal Data / Topic Engine

#### A1 — Current Formal Pipeline

- Formal Topic identity, PIT membership, daily state, Structural Role authority,
  Score/Grade contract surfaces, Lifecycle publication paths, correction and
  supersession lineage exist in committed implementation lineage.
- The committed M1 integration line demonstrates a 107/107 current Topic
  materialization path. `107` is an observed scope, not a business constant;
  every run must resolve the effective Topic universe as of its date.
- Daily Grade and Lifecycle are independent formal outputs. Lifecycle may
  consume approved upstream facts, but neither field is a synonym or a browser
  derivation of the other.
- Structural Role and the Leader/importance projection are owner-curated,
  effective-dated formal inputs. Research Leader Set artifacts cannot be
  promoted by inference.
- Current blocker: the complete post-2026-09-12 implementation lineage and its
  authority/readback evidence are not all ancestors of canonical `main`.

#### A2 — Historical Data Foundation

- Production canonical OHLCV evidence begins on 2026-08-13. It is not a
  continuous two-year Production history.
- The earlier two-year bootstrap is non-Production evidence. It may support
  diagnostics and research, but it does not prove Production availability or
  formal replayability.
- Missing sessions, unknown adjustment state, corporate-action gaps, and
  unavailable provider rows remain explicit. They are never forward-filled or
  converted to zero.

#### A3 — Formal Historical Continuity

- Formal history requires historically effective Topic scope, PIT membership,
  Structural Role/Leader authority, Score, Grade, Lifecycle, and publication
  lineage for each as-of date. Price history alone is insufficient.
- Committed continuity evidence records incomplete historical Topic snapshots,
  no complete historical Score/Grade/Lifecycle/Opportunity session, and 14 of
  15 formal sessions for the rotation contract as of 2026-09-21.
- Research history is not eligible for formal backfill. Formal gaps remain
  visible until governed, date-effective inputs exist.

### B — User-facing Product

#### B1 — Today

Today is the market-orientation surface: market pulse, indices, turnover,
institutional flow, breadth/distribution, events, and deterministic signals.
It summarizes what is happening in the market; it does not select investable
Opportunities.

Committed development lineages exist for index/turnover, market and stock
institutional flow, distribution/breadth, and Today Signals. Because those
lineages are not all integrated into current `main`, they remain reconciliation
candidates rather than completed canonical product capabilities. Missing
dependencies must produce `PARTIAL` or `UNAVAILABLE`, never a false “no signal”.

#### B2 — Opportunity

Opportunity is downstream decision support. It consumes formal market, Topic,
stock, technical, risk, and optional institutional evidence through the formal
composition boundary. It does not redefine Topic Grade/Lifecycle and does not
turn Today signals into recommendations.

The formal full-universe consumer and FUND-C enrichment have committed
evidence, but a complete formal provider/publication chain is not yet canonical
on `main`. The user-facing product remains fail-closed; shadow and research
results are not formal daily recommendations.

#### B3 — Topic

Topic is the thematic intelligence surface. Identity, membership, Structural
Role, daily Score, Daily Grade, Lifecycle, ranking and explanation must retain
their own provenance. Current formal scope is dynamic; UI lists and counts must
not assume 107.

#### B4 — Stock

Stock is the evidence and drill-down surface. Search/filter, EOD and historical
price foundations are canonical. Technical evidence and institutional-flow
capabilities must be integrated and published through formal backend contracts
before the UI may present them as current product facts.

### C — Decision Intelligence

#### C1 — Statistical Research

Run PIT-safe, no-look-ahead studies against explicitly classified research
datasets. Research outputs remain evidence-only.

#### C2 — Feature Validation

Validate stability, coverage, missingness, concentration, temporal robustness,
and failure modes. A passing study does not itself create a formal feature.

#### C3 — Decision Layer

Only owner-reviewed, versioned, effective-dated inputs may affect formal
eligibility, ranking, states, or explanations. The route is:

`Research → Validation → Owner review → Formal contract → main integration → Release → Production readback`.

## Execution priorities

| Priority | Outcome |
|---|---|
| **P0** | Reconcile A1 and the shared daily pipeline into canonical `main`; prove current-date Topic/Today readback without relaxing fail-closed rules. |
| **P1** | Establish A2/A3 continuity: authoritative Production history, historically effective formal inputs, and the missing 15th rotation session. |
| **P2** | Complete B1 Today and B3 Topic formal consumption, then B4 Stock evidence publication. |
| **P3** | Activate B2 Opportunity only after its complete upstream authority and provider chain is canonical; continue C1/C2 research in parallel without policy promotion. |
| **Deferred** | Intraday full reranking, AI Studio, advanced notifications, and interaction polish remain in [Product Ideas](TOPICPILOT_PRODUCT_IDEAS.md). |

## Product boundary rules

1. `IMPLEMENTED` or `VALIDATED` outside `main` is not product completion.
2. Canonical `main` integration is necessary but does not imply Production
   release or public visibility.
3. Research history and formal history are separate authorities.
4. Frontend code formats and presents backend-owned semantics; it does not
   recompute Score, Grade, Lifecycle, eligibility, ranking, or signal policy.
5. Today explains market state. Opportunity evaluates downstream candidates.
   Neither surface silently takes over the other's role.
6. Missing numeric values remain `null`/unavailable, never zero by convenience.
7. Historical reports are preserved as evidence; current routing is owned here.

## Canonicalization note

This reconciliation records committed branch evidence without silently
promoting application changes. The next governed engineering action is a
separate canonical reconciliation of the accepted post-`f88ff51` lineages.
This document does not authorize a merge, deployment, migration, Production
mutation, scheduler change, or `NEXT_TASK` change.
