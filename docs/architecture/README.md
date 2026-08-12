# TopicPilot Software Architecture Book

> Version: v0.2  
> Documentation governance: Accepted 2026-08-08  
> Scope: the documented migration from `LEGACY / V1` to `NEXT / V2`.

This directory is the architecture book for TopicPilot. It describes system
boundaries, business concepts, runtime containers, data movement, persistence,
API exposure, deployment and architectural decisions. It is intentionally
separate from implementation details and from the private formal-data source.

## Documentation governance and single source of truth

This index governs the ownership of permanent V2 knowledge. Each topic has one canonical authority; other documents link to that authority instead of copying its rules.

### Four documentation layers

| Layer | Change rate | Content | Rule |
|---|---|---|---|
| 1 — Foundation | Rarely; normally annual or by explicit PM decision | Product Vision, Mission, Core Principles, Architecture Philosophy, accepted ADRs | Changes require explicit approval; current truth lives in a canonical contract and decision history lives in ADRs. |
| 2 — Design | Occasionally; normally per quarter or approved phase | Roadmap, architecture, ERD, engine design, data contracts | Update the owning specification; do not copy Layer 1 content. |
| 3 — Execution | Frequently; daily or per task | Work orders, daily progress, next task, handoff status | Record scope, evidence, and status only; link to permanent decisions. |
| 4 — Generated | Automatically | OpenAPI, database schema metadata, generated API client, Admin metadata | Generated output is never a hand-maintained source of truth. |

### Canonical authority map

| Topic | Canonical authority | Other documents may contain |
|---|---|---|
| Product Vision, Mission, Product Philosophy, Product Surfaces, Core Principles | [Product Direction and Surfaces Contract](PRODUCT_SURFACES_AND_UX_CONTRACT.md) | Link plus task-specific impact only |
| Accepted architecture decisions and rationale | [ADR index](decisions/README.md) and individual ADRs | Decision link and implementation consequence only |
| Architecture philosophy and V1/V2 system boundary | [Architecture Overview](ARCHITECTURE_OVERVIEW.md) | Boundary link; no copied product mission |
| Detailed system design, ERD, engines, data flow, API, deployment | The numbered architecture chapter or named specification that owns the subject | Cross-reference and local context only |
| V2 production data authority and infrastructure topology | [V2 Production Data Architecture](TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md) | Link plus implementation/audit status; do not copy runtime evidence into product documents |
| Theme Discovery, Theme Knowledge, Theme Governance, and their domain boundaries | [Theme Governance & Knowledge System](THEME_GOVERNANCE_KNOWLEDGE_SYSTEM.md) | Link plus task-specific impact only; no duplicated rules |
| Current milestones and sequence | [Roadmap](../ROADMAP.md) | A task status plus roadmap link |
| Repository startup and current handoff | [Project Context](../../PROJECT_CONTEXT.md) | Navigation, verified paths, and current status; no permanent product rules |
| Work scope, whitelist, and acceptance evidence | [Work Order Register](../WORK_ORDERS.md) and individual work-order files | Why and what to execute; no product philosophy |
| Historical engineering activity | [Daily Progress](../DAILY_PROGRESS.md) | Factual event and links; never normative rules |
| API, schema, generated client, and Admin metadata | OpenAPI, Alembic/SQLAlchemy metadata, and generated artifacts | Descriptive links only; regenerate instead of hand editing |

### Governance rules

1. Search this authority map before creating a document. Update the canonical file when an authority already exists.
2. Specifications describe the current formal contract; ADRs describe why an accepted architectural decision was made.
3. Work orders and progress logs must not become permanent repositories for product philosophy or architecture decisions.
4. If two documents conflict, the mapped canonical authority wins until an explicit ADR and owner-approved update changes it.
5. Deprecated duplicate files are deleted after all inbound links are redirected; aliases with copied content are not retained.
6. Status words such as `Draft`, `Accepted`, `Frozen`, and `Generated` must be explicit and must not be inferred from directory location.

## Reading order

1. [System Context](01_SYSTEM_CONTEXT.md) — C4 Level 1 and external boundaries
2. [Container Architecture](02_CONTAINER_ARCHITECTURE.md) — C4 Level 2
3. [Domain Model](03_DOMAIN_MODEL.md) — business concepts and relationships
4. [Engine Flow](04_ENGINE_FLOW.md) — engine responsibilities and Level 3 boundaries
5. [Data Flow](05_DATA_FLOW.md) — lineage from source to consumer
6. [Sequence Diagram](06_SEQUENCE_DIAGRAM.md) — pre-market, intraday and post-market behavior
7. [Database Design](07_DATABASE_DESIGN.md) — persistence responsibilities and rules
8. [ER Diagram](08_ER_DIAGRAM.md) — review-oriented logical relationships
9. [API Architecture](09_API_ARCHITECTURE.md) — read API and client boundary
10. [Deployment](10_DEPLOYMENT.md) — local, public and operational topology

## Architecture contract references

This index does not restate architecture rules. Use the owning contract:

- System boundary and architecture philosophy: [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
- Product and frontend responsibilities: [Product Direction and Surfaces Contract](PRODUCT_SURFACES_AND_UX_CONTRACT.md)
- Theme Knowledge and Governance: [Theme Governance & Knowledge System](THEME_GOVERNANCE_KNOWLEDGE_SYSTEM.md)
- Persistence, import, and null semantics: [Database Design](07_DATABASE_DESIGN.md)
- Read API boundary: [API Architecture](09_API_ARCHITECTURE.md)
- Public-safe data and licensing: [Public Data and Licensing Policy](../policies/public-data-and-licensing.md)
- Accepted decision rationale: [ADR index](decisions/README.md)

## C4 coverage

| Level | This book covers |
|---|---|
| Level 1 — System Context | Users, TopicPilot, legacy workflow, source/export boundaries and optional BI |
| Level 2 — Containers | React, FastAPI, PostgreSQL, importer/validator, fixtures and private exporter |
| Level 3 — Components | Engine responsibilities and boundaries; exact implementation components remain Draft |
| Level 4 — Code | Not yet required; implementation code and migrations are authoritative |

## Status vocabulary

- **Accepted:** explicitly approved as the current governing decision or contract.
- **Frozen:** accepted and change-controlled; modification requires the named owner or decision process.
- **Implemented:** supported by current repository code, migrations or contract.
- **Documented:** supported by architecture/data documents but not necessarily implemented here.
- **Draft:** a useful boundary or placeholder whose detailed rule is not settled.
- **Open Question:** requires a product, data-owner or architecture decision.
- **Generated:** produced from code or metadata and not maintained manually.

## Decisions

See [decisions/README.md](decisions/README.md). Existing ADRs remain in the
repository's current architecture directory until they are renamed or
re-indexed deliberately.

## Workshop status

Workshop 4 is `Completed`: 4.1 Detector Interface, 4.2 Detector Registry,
4.3 Evidence & Aggregation, and 4.4 Detector Catalog are recorded.

Workshop 5 is `Completed`: runtime orchestration and the Pipeline execution
model are recorded in [Workshop 5](../workshops/WORKSHOP_5_RUNTIME_ORCHESTRATION.md).

| Workshop | Status |
|---|---|
| Workshop 1 | Frozen |
| Workshop 2 | Frozen |
| Workshop 3 | Completed — Business Rules finalized; detector design moves to Workshop 4 |
| Workshop 4 | Completed — Detector catalog template and first detector specification recorded |
