# Work orders

Allowed statuses: `PLANNED`, `IN_PROGRESS`, `PASS`, `FAIL`, `BLOCKED`, `NEEDS_PM_DECISION`.

| Task | Status | Single completion goal | Modification whitelist | Validation whitelist |
|---|---|---|---|---|
| PLATFORM-CONTRACT-001 | PASS | Freeze the public bundle, source classification, and architecture decisions. | `docs/`, `fixtures/schema/` | Contract examples and schema validation |
| PLATFORM-POSTGRES-001 | IN_PROGRESS | Create the PostgreSQL schema, migrations, synthetic bundle, and idempotent importer. | `services/api/`, `fixtures/` | Awaiting hosted PostgreSQL CI evidence; local contract/null tests pass |
| PLATFORM-API-001 | IN_PROGRESS | Expose the approved read-only FastAPI and OpenAPI contract. | `services/api/`, `packages/api-client/` | Awaiting PostgreSQL-backed API CI; OpenAPI and client tests pass locally |
| PLATFORM-WEB-001 | IN_PROGRESS | Deliver the synthetic public React demo over the API. | `apps/web/`, `packages/api-client/` | Lint, 14 tests, production build, and runtime dependency audit pass; browser/deploy pending |
| PLATFORM-DEVOPS-001 | IN_PROGRESS | Make the platform reproducible through containers and CI. | `infra/`, `.github/`, root configs | Docker unavailable locally; GitHub Compose/secret-scan evidence pending |
| PLATFORM-DEMO-DOCS-001 | IN_PROGRESS | Publish complete architecture, ERD, API, data, runbook, and portfolio documentation. | `docs/`, `README.md` | Core documents complete; verified public URLs/screenshots pending |
| PLATFORM-PRIVATE-SYNC-001 | PLANNED | Validate manual private imports, then define daily read-only synchronization. | Generic importer and private runbook only | Ten-trading-day parity report; no formal writes |
| PLATFORM-BI-001 | NEEDS_PM_DECISION | Provide a Power BI-ready analytics contract and synthetic report specification. | `docs/bi/`, SQL views, synthetic exports | SQL/report specification complete; native `.pbix` requires Power BI Desktop |

Each task stops as soon as its PASS evidence is complete. Adjacent improvements require a new work order.
