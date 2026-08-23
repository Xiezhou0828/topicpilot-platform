# TopicPilot Software Architecture Book

> Version: v0.2
> Documentation governance: Accepted 2026-08-08
> Scope: the documented migration from `LEGACY / V1` to `NEXT / V2`.

This directory is the architecture book for TopicPilot. It describes system
boundaries, business concepts, runtime containers, data movement, persistence,
API exposure, deployment, and architectural decisions. It is intentionally
separate from implementation details and from private formal-data sources.

## Documentation governance and single source of truth

Each topic has one canonical authority. Other documents link to that authority
instead of copying its rules.

| Topic | Canonical authority | Other documents may contain |
|---|---|---|
| Product vision, mission, surfaces, and core principles | Owner-retained Product Direction and Surfaces Contract; explicit promotion pending | Link plus task-specific impact only |
| Accepted architecture decisions and rationale | Tracked [ADR-001](ADR-001-parallel-read-model.md) and [ADR-002](ADR-002-openapi-generated-client.md); ADR-003 remains owner-retained | Decision link and implementation consequence only |
| Architecture philosophy and V1/V2 system boundary | [System Overview](system-overview.md) and this book | Boundary link; no copied product mission |
| Detailed system design and data architecture | [V2 Production Data Architecture](TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md), [ERD](erd.md), and named tracked specifications | Cross-reference and local context only |
| Frontend responsibility boundary | [V2 Frontend Design Specification](TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md) | Link plus implementation status only |
| Theme Governance and Knowledge | Owner-retained planning authority; PM decision/promotion pending | Link plus task-specific impact only |
| Current milestones and sequence | [Roadmap](../ROADMAP.md) | A task status plus roadmap link |
| Repository startup and current handoff | [Project Context](../../PROJECT_CONTEXT.md) | Navigation and verified paths only |
| Work scope and acceptance evidence | [Work Order Register](../WORK_ORDERS.md) | Why and what to execute; no product philosophy |
| Historical engineering activity | [Daily Progress](../DAILY_PROGRESS.md) | Factual event and links; never normative rules |
| API and generated artifacts | OpenAPI, Alembic/SQLAlchemy metadata, and generated artifacts | Descriptive links only |

### Governance rules

1. Search this authority map before creating a document.
2. Specifications describe the current formal contract; ADRs describe why an
   accepted architectural decision exists.
3. Work orders and progress logs must not become permanent repositories for
   product philosophy or architecture decisions.
4. If two documents conflict, the mapped canonical authority wins until an
   explicit owner-approved decision changes it.
5. Deprecated duplicate files are removed only after inbound links are
   redirected and the owner approves the disposition.
6. Status words such as `Draft`, `Accepted`, `Frozen`, and `Generated` must be
   explicit and must not be inferred from directory location.

## Reading order

1. [System Overview](system-overview.md) — current system boundary and containers
2. [Production Data Architecture](TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md) — governed data and infrastructure boundary
3. [ERD](erd.md) — tracked review-oriented logical relationships
4. [Frontend Design Specification](TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md) — tracked UI boundary
5. [Deployment](10_DEPLOYMENT.md) — local, public, and operational topology

The numbered architecture chapter set, Phase 3 planning documents, research,
and workshops remain owner-retained historical evidence until their complete
source graphs are explicitly promoted. This prevents a clean checkout from
depending on untracked providers.

## Architecture contract references

This book does not restate implementation rules. Use the owning tracked
contract or the owner-retained disposition recorded in the task report:

- System boundary: [System Overview](system-overview.md)
- Frontend boundary: [V2 Frontend Design Specification](TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md)
- Persistence and data boundary: [V2 Production Data Architecture](TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md)
- Topic derived-intelligence publication and Lifecycle dependency boundary: [Topic Derived Intelligence Publication and Lifecycle Dependency Contract](TOPIC_DERIVED_INTELLIGENCE_PUBLICATION_AND_LIFECYCLE_DEPENDENCY_CONTRACT.md)
- Topic derived-intelligence definition and publication authority closure: [Topic Derived Intelligence Definition and Publication Authority Closure](TOPIC_DERIVED_INTELLIGENCE_DEFINITION_AND_PUBLICATION_AUTHORITY_CLOSURE.md)
- API boundary: [API guide](../api/api-guide.md)
- Stock technical V0 policy: [Stock Technical V0 Formal Publication Policy](STOCK_TECHNICAL_V0_POLICY_CONTRACT.md)
- Stock technical V0 formal evidence provider/consumer contract: [Technical V0 Formal Evidence Provider & Consumer Contract](STOCK_TECHNICAL_V0_FORMAL_EVIDENCE_PROVIDER_CONSUMER_CONTRACT.md)
- Stock technical V0 Phase 2B implementation: [Technical V0 Implementation Closure](../reports/TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION.md)
- Stock technical V0 Phase 2B1 runtime continuity attachment: [Runtime Continuity Evidence Attachment Closure](../reports/TASK-FE-BE-STOCK-006B-PHASE-2B1-RUNTIME-CONTINUITY-EVIDENCE-ATTACHMENT-20260816.md)
- Stock technical V0 Owner policy closure: [Phase 2A2 Owner Technical V0 Policy Canonical Closure](../reports/TASK-FE-BE-STOCK-006B-PHASE-2A2-OWNER-TECHNICAL-V0-POLICY-CANONICAL-CLOSURE.md)
- Stock technical V0 continuity authority closure: [Stock Technical V0 Continuity Authority Closure](STOCK_TECHNICAL_V0_CONTINUITY_AUTHORITY_CLOSURE.md)
- Core V0 candidate-definition authority: [Core V0 Candidate Definition Authority Contract](CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md)
- Core V0 A1/A2 breakout formation authority: [Core V0 A1/A2 Breakout Formation Policy V0](CORE_V0_A1_A2_BREAKOUT_FORMATION_POLICY_V0.md)
- Core V0 A1/A2 executable candidate panel: [Core V0 A1/A2 Executable Candidate Panel Contract](CORE_V0_A1_A2_EXECUTABLE_CANDIDATE_PANEL_CONTRACT.md)
- Core V0 real coverage and walk-forward preflight: [Core V0 Real Coverage and Walk-forward Preflight Contract](CORE_V0_REAL_COVERAGE_AND_WALK_FORWARD_PREFLIGHT_CONTRACT.md)
- Public-safe data and licensing: [Public Data and Licensing Policy](../policies/public-data-and-licensing.md)
- Accepted decision rationale: [ADR-001](ADR-001-parallel-read-model.md) and [ADR-002](ADR-002-openapi-generated-client.md)

## Status vocabulary

- **Accepted:** explicitly approved as the current governing decision or contract.
- **Frozen:** accepted and change-controlled; modification requires the named owner.
- **Implemented:** supported by current repository code, migrations, or contract.
- **Documented:** supported by architecture/data documents but not necessarily implemented.
- **Draft:** a useful boundary whose detailed rule is not settled.
- **Open Question:** requires a product, data-owner, or architecture decision.
- **Generated:** produced from code or metadata and not maintained manually.

## Workshop status

Workshop 4 is `Completed` in the owner-retained historical evidence. Workshop
5 is also recorded as completed there, but its source is not a canonical link
target in this clean checkout.
