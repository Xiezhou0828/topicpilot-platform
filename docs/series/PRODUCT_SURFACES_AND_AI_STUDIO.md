# Product Surfaces & AI Studio

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; product direction and accepted surface
semantics remain with their named owner documents.

## Scope

This series covers product direction, accepted/frozen product surfaces, V1/V2
positioning, AI Topic Discovery, AI Studio, Master Data/Admin, News/Event
foundation, and the rule that AI may assist without becoming taxonomy or
relation authority.

## Current state

- V2 is the active product direction; V1 is a legacy bridge under partial
  retirement protection.
- The accepted product surfaces and UX contract defines the intended surface
  boundaries. Its semantic authority and repository canonicalization status
  are tracked separately; this summary does not promote or rewrite it.
- Current product priority is P0 Product Completion, P1 Historical and
  Recommendation research, P2 Data Management/News/Discovery, P3 Opportunity
  and Favorites polish, P4 Intraday, and P5 AI Studio.
- AI Studio is deferred. AI Topic Discovery and correction suggestions remain
  future governed capabilities.
- AI may suggest or explain; it may not directly mutate canonical taxonomy,
  relations, product rules, or publication state.

## Canonical authority

- [Product roadmap](../product/TOPICPILOT_PRODUCT_ROADMAP.md)
- [Accepted product surfaces and UX contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)
- [V2 frontend design specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md)
- [Product decisions](../product/TOPICPILOT_PRODUCT_DECISIONS.md)
- [Product ideas](../product/TOPICPILOT_PRODUCT_IDEAS.md)
- [Architecture authority map](../architecture/README.md)

## Completed

- V1/V2 product positioning and protected migration boundary.
- Accepted surface vocabulary and frontend responsibility boundary at the
  documented semantic level.
- AI non-authority principle: suggestions and explanations are separate from
  canonical mutation and formal publication.

## Unfinished / deferred

- AI Studio product surface and governed execution contract.
- AI Topic Discovery, correction suggestions, and Master Data/Admin flows.
- News/Event foundation and other product-roadmap capabilities that depend on
  their own data and owner approvals.

## Dependencies and blockers

- PM/Owner promotion of product direction where repository canonicalization is
  still separate.
- Formal data, taxonomy, relation, and publication contracts for each surface.
- Security, auditability, explainability, and human approval for any future AI
  action path.

## Do not do

- Do not create a standalone AI recommendation page or let AI issue trades.
- Do not let AI directly change canonical taxonomy, relations, Score, Grade,
  Lifecycle, or publication state.
- Do not treat an idea, mockup, fixture, or old surface as an accepted product
  contract.
- Do not use this summary to replace the product or frontend authority.

## Historical evidence

- [Product architecture and surface reconciliation](../reports/TASK-DOC-016_OPPORTUNITY_ENGINE_PRODUCT_ARCHITECTURE_SPEC_REPORT.md)
- [Topic detail research workspace](../reports/TASK-FE-TOPIC-DETAIL-001_TOPIC_DETAIL_RESEARCH_WORKSPACE.md)
- [Product roadmap and decision history](../product/TOPICPILOT_PRODUCT_ROADMAP.md)
- [Architecture surface governance](../architecture/README.md)

## Next bounded route

Continue P0/P1 product completion and governed data contracts first. Keep AI
Studio and AI Discovery deferred until their owner-approved surface, security,
human-review, and canonical-write boundaries exist.
