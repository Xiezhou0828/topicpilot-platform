# Work orders

Allowed statuses: `PLANNED`, `IN_PROGRESS`, `PASS`, `FAIL`, `BLOCKED`, `NEEDS_PM_DECISION`.

| Task | Status | Single completion goal | Modification whitelist | Validation whitelist |
|---|---|---|---|---|
| PLATFORM-CONTRACT-001 | PASS | Freeze the public bundle, source classification, and architecture decisions. | `docs/`, `fixtures/schema/` | Contract examples and schema validation |
| PLATFORM-POSTGRES-001 | PASS | Create the PostgreSQL schema, migrations, synthetic bundle, and idempotent importer. | `services/api/`, `fixtures/` | PostgreSQL 16 migration, idempotency, conflict, rollback, null, and view tests pass in CI |
| PLATFORM-API-001 | PASS | Expose the approved read-only FastAPI and OpenAPI contract. | `services/api/`, `packages/api-client/` | PostgreSQL-backed API, problem JSON, pagination, OpenAPI drift, and generated-client tests pass in CI |
| PLATFORM-WEB-001 | PASS | Reuse the original TopicPilot React UI and replace only its shared data source with FastAPI plus a synthetic fallback. | `apps/web/`, `packages/api-client/` | Lint, 65 tests, production build, all original route checks, synthetic-contract check, and public deployment pass |
| PLATFORM-DEVOPS-001 | PASS | Make the platform reproducible through containers and CI. | `infra/`, `.github/`, root configs | GitHub Actions builds the full Compose stack, seeds demo data, probes API/Web health, and scans secrets |
| PLATFORM-DEMO-DOCS-001 | PASS | Publish complete architecture, ERD, API, data, runbook, and portfolio documentation. | `docs/`, `README.md` | README, Quick Start, diagrams, API/data/runbooks, public URL, CI badge, and an original-UI screenshot checklist are committed |
| PLATFORM-PRIVATE-SYNC-001 | PLANNED | Validate manual private imports, then define daily read-only synchronization. | Generic importer and private runbook only | Ten-trading-day parity report; no formal writes |
| PLATFORM-BI-001 | NEEDS_PM_DECISION | Provide a Power BI-ready analytics contract and synthetic report specification. | `docs/bi/`, SQL views, synthetic exports | SQL/report specification complete; native `.pbix` requires Power BI Desktop |

Each task stops as soon as its PASS evidence is complete. Adjacent improvements require a new work order.
