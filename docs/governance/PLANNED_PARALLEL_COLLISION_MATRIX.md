# Planned Parallel Collision Matrix

This matrix qualifies isolated execution, not simultaneous integration.
Shared surfaces remain serial and belong to the integration owner.

| Surface | Today Signals Promotion | A10/A9 Post-Close Reconciliation | Topic/B2 Artifact Provenance | Resolution |
|---|---|---|---|---|
| Today Home/Signals | Owned | Read-only dependency only | No write | Today task owns bounded Home/Signals paths |
| A10 post-close writer/scheduler | No write | Owned | No write | A10/A9 task owns live post-close paths |
| Topic/B2 lifecycle/artifact | No write | No write | Owned | Topic/B2 task owns topic paths |
| Shared schemas/models | Shared | Shared | Shared | SHARED_REQUIRES_RECONCILIATION; integration owner only |
| OpenAPI/generated client | Shared | Shared | Shared | SHARED_REQUIRES_RECONCILIATION; one candidate at a time |
| Alembic migrations | Forbidden | Shared/audit only | Shared/audit only | INTEGRATION_OWNER_ONLY; no parallel mutation |
| Formal publication contracts | Shared | Shared | Shared | Reconcile source/provider/data authority before integration |
| Governance registries | Per-task manifest/report only | Per-task manifest/report only | Per-task manifest/report only | Aggregate centrally by governed reconciliation |
| Production/release configuration | Forbidden | Forbidden | Forbidden | Release/operator task only |
| Today UI/CSS | Not in promotion unit | Forbidden | Forbidden | Separate frontend task; no implicit redesign |

**Dry-run result:** YES for isolated start and read/audit activity; NO for
independent integration of shared paths. A combined candidate must be created
serially from the latest governed base.
