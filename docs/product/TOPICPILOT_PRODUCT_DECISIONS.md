# TopicPilot product decisions

**Status:** `CANONICAL / ACTIVE`
**Last reviewed:** `2026-09-22`

This register records settled product principles. It is not a backlog,
implementation report, or permission to mutate Production. Provisional ideas
remain in [Product Ideas](TOPICPILOT_PRODUCT_IDEAS.md).

## Current decision register

### PD-001 — Home/Today is market navigation

- **Decision:** Today answers “what is happening in the market?” through
  backend-owned market facts, events, distribution, flows, and signals.
- **Boundary:** It is not an Opportunity selector or recommendation surface.
- **Status:** `COMMITTED`

### PD-002 — Topic is the primary thematic intelligence object

- **Decision:** Topic owns identity, effective membership, Structural Role,
  Score, Daily Grade, Lifecycle, ranking, and evidence-backed explanation.
- **Boundary:** Every field retains explicit provenance and availability.
- **Status:** `COMMITTED`

### PD-003 — Stock is an evidence and drill-down surface

- **Decision:** Stock search, price history, technical evidence, institutional
  flow, Topic relations, and Opportunity context are consumed from formal
  backend contracts.
- **Status:** `COMMITTED`

### PD-004 — Favorites is user-owned state

- **Decision:** Favorites is a saved-item/watch surface, not an implicit
  recommendation or model label.
- **Status:** `COMMITTED`

### PD-005 — Opportunity is downstream research support

- **Decision:** Opportunity consumes formal upstream Topic and stock evidence,
  applies independently governed qualification/strategy contracts, and returns
  evidence-first states. It does not feed back into Topic Score.
- **Status:** `COMMITTED`; formal provider/publication remains gated

### PD-006 — V1 is not V2 product authority

- **Decision:** V1 remains a protected legacy bridge until V2 replacement and
  parity/cutover approval. It is not authority for V2 UI or semantics.
- **Status:** `COMMITTED`

### PD-007 — Daily Grade and Lifecycle are independent

- **Decision:** Daily Grade is a daily classification and Lifecycle is a
  state/transition model. They may share governed inputs, but one is not
  derived from the display value of the other and neither substitutes for the
  other when unavailable.
- **Rationale:** Preserve temporal meaning, replayability, and honest partial
  states.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-008 — Structural Role and Leader/importance are owner-curated inputs

- **Decision:** Structural Role (`REPRESENTATIVE`, `CORE`, `RELATED`) and the
  selected Leader/importance projection are separate, effective-dated formal
  inputs. Research Leader Set results, member order, or role names cannot be
  converted into formal importance without owner review.
- **Rationale:** Formal selection and weighting are business authority, not an
  inference task.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-009 — 107 is not a business constant

- **Decision:** `107` is the observed current formal Topic count for the
  2026-09-22 reconciliation. Runtime, tests, UI, and reports must resolve the
  effective Topic universe by as-of date and must not hard-code 107.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-010 — Research history is not formal history

- **Decision:** Local bootstrap, research replay, shadow rows, and historical
  studies may diagnose or validate ideas but cannot backfill formal history
  without historically effective authority, lineage, and governed publication.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-011 — Frontend never recomputes formal business logic

- **Decision:** The frontend may group, format, filter presentation, and follow
  backend display order. It must not derive Score, Grade, Lifecycle,
  eligibility, risk, ranking, signals, leaders, or formal availability from raw
  fields.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-012 — Today and Opportunity have different product roles

- **Decision:** Today summarizes market state and attention. Opportunity
  evaluates downstream Topic/stock candidates under separate qualification and
  evidence contracts. Today signals are context, not an automatic Opportunity.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

### PD-013 — Product completion requires canonical main integration

- **Decision:** A completed implementation counts as product-complete only when
  the accepted implementation and required authority artifacts are committed
  into canonical `main` and validated there. Release and Production readback
  remain later, separately proven lifecycle stages.
- **Date:** 2026-09-22
- **Status:** `FROZEN GOVERNANCE PRINCIPLE`

### PD-014 — Opportunity evidence uses canonical OHLCV

- **Decision:** Opportunity technical evidence consumes accepted canonical
  daily OHLCV with explicit trading-date/as-of semantics. Missing values remain
  unavailable and never pass a gate by default.
- **Status:** `COMMITTED`

### PD-015 — Opportunity composition is backend-owned and deterministic

- **Decision:** Technical, risk, entry-quality, and optional institutional
  builders produce structured facts. The formal Opportunity composition
  boundary maps them into versioned states and explanations; the frontend does
  not infer those semantics.
- **Status:** `COMMITTED`; formal activation remains gated

### PD-016 — Institutional evidence is non-primary

- **Decision:** Institutional flow is optional confirmation/evidence. Missing
  data is `UNKNOWN`; it cannot independently bypass a hard gate or create an
  Opportunity. FUND-C does not create a composite institutional score.
- **Status:** `COMMITTED`

### PD-017 — Opportunity strategies remain independent

- **Decision:** Trend Continuation and Catch-up retain independent evidence,
  ordering, and presentation. There is no global cross-strategy winner and no
  feedback into Topic Score.
- **Status:** `COMMITTED`; thresholds remain versioned and governed

### PD-018 — Missing data fails closed

- **Decision:** Missing or stale formal inputs produce explicit `PARTIAL`,
  `UNAVAILABLE`, `DEFERRED`, or `UNKNOWN` states. An empty result may be called
  “none” only when all required formal dependencies are complete.
- **Date:** 2026-09-22
- **Status:** `FROZEN PRINCIPLE`

## Explicitly not decided

This reconciliation does not approve a new Score formula, hard-coded Leader
count, Opportunity threshold/weight, institutional SUPPORT/CONFLICT policy,
notification taxonomy, formal backfill, Production activation, or release.
Those require their own owner decision and governed contract.
