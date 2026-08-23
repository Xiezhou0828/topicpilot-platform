# TopicPilot Series Summaries

**Status:** `NAVIGATION LAYER / PHASE 1`

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

This directory is a second-layer navigation surface for TopicPilot. It does
not create a new product, architecture, API, or data authority. Each summary
points to the document that owns the rule and to the reports that preserve the
implementation or research evidence.

## Cold-start reading order

For a normal new conversation, read only the smallest relevant set:

1. [`AGENTS.md`](../../AGENTS.md)
2. [`PROJECT_CONTEXT.md`](../../PROJECT_CONTEXT.md)
3. [`DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md)
4. [`ROADMAP.md`](../ROADMAP.md)
5. One relevant series summary below
6. The linked canonical contract when the task changes or evaluates that rule

Reports, work orders, research, and raw artifacts are opened only when the
task requires provenance or validation detail.

## Series map

| Series | Summary | Primary route |
|---|---|---|
| WS1 | [Topic Derived Intelligence](WS1_TOPIC_DERIVED_INTELLIGENCE.md) | Topic roles, projections, PIT state, Lifecycle, and publication gates |
| WS2 | [Stock Technical V0](WS2_STOCK_TECHNICAL_V0.md) | Fixed indicators, continuity, event authority, and formal evidence publication |
| WS3 | [Core V0 Research](WS3_CORE_V0_RESEARCH.md) | A1/A2 research, candidate definitions, evidence, and forward validation |
| Data | [Data / Reference / Historical](DATA_REFERENCE_HISTORICAL.md) | Reference universe, OHLCV authority, historical persistence, and PIT limits |
| Surfaces | [Today & Stock Surfaces](TODAY_AND_STOCK_SURFACES.md) | Home/Today and Stock Explorer/detail/read-surface boundaries |
| Opportunity | [Opportunity / Recommendation](OPPORTUNITY_RECOMMENDATION.md) | Shadow-only Opportunity semantics and recommendation deferrals |
| Release | [Release / Deployment](RELEASE_DEPLOYMENT.md) | CI, release-candidate, deployment, and post-deploy gates |
| Product | [Product Surfaces & AI Studio](PRODUCT_SURFACES_AND_AI_STUDIO.md) | Product direction, accepted surfaces, and AI boundaries |

## Summary contract

Every summary keeps the same compact sections:

`scope` → `current state` → `canonical authority` → `completed` →
`unfinished` → `blockers/dependencies` → `do not do` → `evidence` →
`next bounded route`.

The `Canonical baseline` records the repository SHA that was read when the
summary was reconciled. It is a source snapshot, not a replacement for the
linked authority. When a canonical contract changes, the affected summary must
be reconciled against the new SHA rather than silently relying on its date.

The next bounded route is informational. It does not set or advance
`NEXT_TASK`, authorize Production work, or override an Owner decision.

## Phase 1 boundary

Phase 1 adds this navigation layer only. Existing documents remain in place:

- no deletion;
- no move of `reports/` or `work-orders/`;
- no rename;
- no duplicate merge;
- no archive;
- no rewrite of existing authority documents.

The later audit sequence remains: inbound links → duplicate comparison →
source SHA/hash/provenance → committed consumer check → `UNKNOWN` owner
disposition → archive proposal.
