# TopicPilot Product Decisions

**Status:** `CANONICAL / CURRENT DECISIONS`
**Owner:** PM / Product design
**Last reviewed:** 2026-08-10

This file records decisions that are safe to use as current product direction. It is not a backlog, work order, implementation report, or replacement for the detailed frontend specification. Undecided items remain in `TOPICPILOT_PRODUCT_IDEAS.md` or are marked provisional in the source document.

## Decision register

### PD-001 — Home is market navigation

- **Decision:** Home / 今日市場 is a market-navigation workspace, not a stock leaderboard, trading terminal, or complete topic map. It does not contain K-lines, a full topic heatmap/map, or strong/weak stock rankings.
- **Rationale:** Give the user orientation and the day's market structure before asking them to research an individual stock.
- **Date:** 2026-08-10 (consolidated from current frontend freeze)
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), sections 2, 5, and Home freeze amendments; [Product Direction Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)

### PD-002 — Shared desktop header information architecture

- **Decision:** The header is one horizontal workspace bar. The left group is Logo + expanded Primary Nav; the right group is Search + Notification + Account. The desktop hamburger and duplicate utility rows are removed.
- **Rationale:** Keep navigation and workspace utilities legible and stable across V2 customer routes.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), section 3; `TASK-FE-HEADER-002` report

### PD-003 — Visual system and responsive priority

- **Decision:** Light mode is the default and dark mode is fully supported. The product is desktop-first. Brand accent is `#8A7462`; surfaces use warm off-white and white, low shadow, restrained borders, and Taiwan-market red-up/green-down semantics.
- **Rationale:** Create a calm modern financial workspace with clear market semantics.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), sections 23–24; Home and header freeze reports

### PD-004 — Customer information architecture

- **Decision:** The primary customer surfaces are 今日市場, 題材, 股票, 收藏, 機會, and AI研究室. Each page answers one primary research question. AI研究室 remains in the IA but does not block the initial V2 launch.
- **Rationale:** Separate orientation, topic intelligence, stock exploration, saved items, recommendations, and future deep research.
- **Date:** 2026-08-10
- **Status:** `COMMITTED` (AI研究室 launch scope is deferred)
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), sections 3–4

### PD-005 — Topic hierarchy and lifecycle

- **Decision:** Topic pages are theme-first and preserve topic hierarchy. Topic Detail exposes representative/core/related stock roles (`代表股` / `核心股` / `關聯股`) and a topic lifecycle. The browser must not infer lifecycle or business scores when the canonical API/data contract is unavailable.
- **Rationale:** TopicPilot explains market themes and their evolution rather than presenting an undifferentiated stock list.
- **Date:** 2026-08-10
- **Status:** `COMMITTED` for product semantics; lifecycle derivation remains an API/data dependency where not yet contracted
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), topic and lifecycle sections; [Product Direction Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)

### PD-006 — Stock Explorer and Stock Detail interaction

- **Decision:** Stock Explorer and Stock Detail use the shared right-side Stock Drawer with a calm “atlas/catalogue” feel. Stock selection preserves the underlying page; it is not a traditional forced full-page navigation model.
- **Rationale:** Support comparison and exploration without losing market/topic context.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), stock surface and drawer sections

### PD-007 — 收藏 is user-owned saved items

- **Decision:** 收藏 / 我的收藏 is for the user's saved topics and saved stocks, not recommendations. Both entity types coexist, visibly separated as 題材 and 股票. Saved views show factual state/change only and do not invent advice.
- **Rationale:** Keep personal tracking distinct from system-generated opportunity discovery.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), sections 22–23

### PD-008 — 機會 is downstream research support

- **Decision:** 機會 owns recommendation/candidate/technical-validation presentation downstream of Topic Intelligence. It is theme-first, explainable, and reuses the Stock Drawer; it is not a generic buy/sell list.
- **Rationale:** Recommendations must not redefine Topic Strength or imply unsupported trading advice.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md), section 24; [Product Direction Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)

### PD-009 — V1 is not V2 UI authority

- **Decision:** V1 is a legacy production workflow and research baseline during coexistence. V1 is not the authority for V2 UI, product semantics, or frontend redesign.
- **Rationale:** V2 is a parallel rebuildable platform with its own governed contracts.
- **Date:** 2026-08-10
- **Status:** `COMMITTED`
- **Source:** [Product Direction Contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md), source-of-truth transition; [Project Context](../../PROJECT_CONTEXT.md)

### PD-010 - Opportunity technical evidence uses canonical OHLCV

- **Decision:** Opportunity technical evidence builders consume accepted canonical `DAILY_BAR` OHLCV with explicit trading-date/as-of semantics. Missing values remain unavailable/unknown and are never filled with zero or treated as a pass.
- **Rationale:** Keep calculations reproducible and aligned with the V2 PostgreSQL/FastAPI data authority while preventing frontend, mock, or future-data inference.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow architecture; production activation is not authorized
- **Source:** `TASK-BE-020` and [Opportunity Engine Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)

### PD-011 - Evidence builders remain separate from the Shadow Composer

- **Decision:** Technical, Risk, Entry Quality, and Opportunity input builders calculate structured facts; `opportunity_shadow.py` remains the composition boundary and does not calculate technical patterns. Historical replay is in-memory shadow/test/report scope only.
- **Rationale:** Preserve evidence provenance, make no-look-ahead checks testable, and avoid silently turning a shadow experiment into production Recommendation semantics.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow architecture; numeric policy remains provisional
- **Source:** `TASK-BE-020` and [Opportunity Engine Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)

### PD-012 - Chip confirmation is non-primary

- **Decision:** Institution/chip signals are an optional confirmation layer. If no formal, fresh canonical chip input exists, the result is `UNKNOWN`; chip data alone cannot pass a primary gate or produce an Opportunity.
- **Rationale:** Avoid the invalid inference that institution net buying equals a recommendation.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow architecture; confirmation thresholds are open
- **Source:** `TASK-BE-020` and [Opportunity Engine Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)

### PD-013 - V1 Opportunity strategies are independent shadow paths

- **Decision:** V1 adds `TREND_CONTINUATION` and `CATCH_UP` as independently evaluated and ranked shadow strategies above canonical OHLCV evidence. `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain future, not implemented. No global cross-strategy winner feeds Topic Score.
- **Rationale:** Preserve strategy-specific explainability and the downstream Opportunity boundary without converting legacy Recommendation rows or scores into a new production policy.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow architecture; production API/persistence/activation remain separately gated
- **Source:** `TASK-BE-024` and [Opportunity Engine Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)

### PD-014 - Opportunity decision and read contracts are deterministic shadow contracts

- **Decision:** Trend Continuation and Catch-up retain independent provisional ranking profiles. A deterministic decision contract maps each strategy result to `SELECTED`, `WAITING_RETEST`, `WAITING_CONFIRMATION`, `DEFERRED`, or `EXCLUDED`. A structured `OpportunityExplanation` and provider-neutral `OpportunityReadModel` are the future adapter boundary; the frontend consumes them and does not infer business semantics.
- **Rationale:** Keep state, evidence, and strategy rationale reproducible while preserving the distinction between internal ranking metadata and user-facing explanation.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow contract; numeric weights/thresholds and production publication remain open/gated
- **Source:** `TASK-BE-024A` and [Opportunity Engine Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)

### PD-015 - Opportunity Qualification Policy V1 is a semantic shadow freeze

- **Decision:** The existing A/B Opportunity shadow engine now consumes a
  deterministic Qualification Policy V1. `S/A` form the formal universe; `B`
  requires warming/improving exception provenance; `D` hard-excludes new
  Opportunities. Lifecycle is strategy-specific, `Close >= 20MA` is a hard
  gate, missing 20MA defers, 60MA is never a hard gate, risk precedes ranking,
  A/B ranking remains independent, and V1 ranks post-close with intraday
  status-only behavior. Trend presentation is capped at Top 3 and Catch-up at
  Top 2 while the backend retains complete rankings.
- **Rationale:** Freeze product semantics and fail-closed ordering without
  pretending provisional numeric parameters are calibrated or activating a
  production Opportunity surface.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for the deterministic shadow policy; numeric
  parameters remain `PROVISIONAL / TUNABLE / VERSIONED`; production API,
  persistence, scheduler, and publication remain gated.
- **Source:** [TASK-BE-024B report](../reports/TASK-BE-024B_OPPORTUNITY_QUALIFICATION_POLICY_REPORT.md),
  [Opportunity Qualification Policy ADR](../architecture/decisions/OPPORTUNITY_QUALIFICATION_POLICY_V1.md)

### PD-016 - Opportunity Shadow Read API is the first integration surface

- **Decision:** The first BE-024C integration surface is a provider-neutral,
  read-only Shadow API plus frontend adapter. It exposes topic/stock/detail
  projections, structured evidence, qualification provenance, explicit data
  states, and version metadata. It does not publish a Recommendation, write
  production persistence, or let the browser infer business semantics.
- **Rationale:** Preserve the frozen BE-024B policy while giving Topic, Stock
  Encyclopedia, and Opportunity surfaces a deterministic contract that can
  later be backed by canonical production data.
- **Date:** 2026-08-12
- **Status:** `COMMITTED` for shadow integration; canonical provider,
  persistence, replay/calibration, and production activation remain gated.
- **Source:** TASK-BE-024C report and [V2 Frontend Design Specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md)

## Explicitly not decisions

Exact notification taxonomy/thresholds, exact navigation label variants, exact Home watch-summary placement, and lifecycle API derivation remain provisional or dependency-gated where the source specification says so. Do not promote chat discussion or a work-order prompt into this register without PM approval.
