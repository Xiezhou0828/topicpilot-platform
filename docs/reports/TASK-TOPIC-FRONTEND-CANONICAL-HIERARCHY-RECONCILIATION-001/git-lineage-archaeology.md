# Git lineage archaeology

## Scope

This reconciliation was performed in the dedicated E: worktree:

- Worktree: `E:\topicpilot-worktrees\TASK-TOPIC-FRONTEND-CANONICAL-HIERARCHY-RECONCILIATION-001`
- Branch: `codex/topic-frontend-canonical-hierarchy-reconciliation-001`
- Canonical base: `origin/main`
- `origin/main` at inspection: `46e1096d6d63c6d6356103f9183f31c62ef3c43a`
- C: drive new workspace created: **NO**

The repository was first fetched and inspected before implementation. The unrelated dirty C: drive checkout was not modified.

## Relevant commits

| Area | Commit | Date | Finding |
| --- | --- | --- | --- |
| Topic Catalog backend | `163723a807a7008e2ea3e37d864fc7b5a94dde1a` | 2026-09-09 | Introduced the read-only `/api/v2/topic-catalog` root/detail/snapshot/history contract and Parent/Leaf schemas. |
| Contract convergence | `74226c387ff36bf328936da0bd12114c2773d9e3` | 2026-09-10 | Converged the release contract around the Topic Catalog. |
| Existing frontend topic source | `6eb554594040c9a9451d6b4a8922465ddcf2b5d6` | 2026-08-12 | Integrated the frontend with the flat `/api/v2/topics` production read model. |
| Reconciliation base | `46e1096d6d63c6d6356103f9183f31c62ef3c43a` | 2026-09-22 | Current `origin/main` base used for this isolated task. |

## Prior frontend integration result

Repository-wide history search for `/api/v2/topic-catalog` under `apps/web` found no prior frontend integration. The frontend remained on `/api/v2/topics` and used `groupName` plus `topicType` for browse filtering. No reusable prior frontend Catalog commit or branch was found.

Therefore the likely issue was not a Catalog data-loss regression. It was a contract adoption gap: the backend canonical Catalog had landed while the frontend still treated the legacy flat read model as the identity and hierarchy source.

## GitHub access boundary

The requested GitHub connector was attempted. The target repository was not exposed to that connector in this session, so local Git remote/history was used for read-only archaeology. No pull request, push, merge, deployment, or production write was performed.
