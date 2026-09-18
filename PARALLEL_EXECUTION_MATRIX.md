# Parallel Execution Matrix
6. Release promotion remains separate and requires exact API/Web/Worker/DB,
   migration/data, rollback, and post-deploy evidence.
**Matrix state:** `OWNER CLOSURE CANONICAL / 2026-09-16`

`YES` below means the named audit/readiness packet may start in its isolated
worktree. It does not authorize product implementation, migration execution,
deployment, Production writes, or a blind source-branch merge.

## 2026-09-16 owner closure checkpoint

Historical recovery and canonical lineage convergence are CLOSED and VERIFIED.
The owner-controlled forward baseline is
277a49382240503fcd0767e9cfb17e2fd974e8a3, a documentation-only descendant of
the verified unified implementation baseline
d6371af5994f0c2d5e0612969f100f6cef26b772. Integration is complete. Release
remains an external gate because exact Web/Worker provenance and operator
canary authorization are unavailable. POST_CLOSE freshness and formal
Opportunity readiness are forward runtime dependencies; they are not reasons
to reopen the recovered historical implementation scope.

| Packet | Start now | Allowed scope | Dependencies / blockers | Conflict class |
|---|---:|---|---|---|
| `TODAY-MAINLINE-RECOVERY-001` | YES | Read-only branch archaeology, source-to-candidate mapping, file ownership and bounded port plan | Must review Home contract, generated artifacts, and broad Today commit boundaries | Shared Home/API/generated/release surfaces; serial integration |
| `A10-A9-RECOVERY-RECONCILIATION-001` | YES | Read-only writer/quote/post-close/migration audit and operator packet | POST_CLOSE/operator readback and migration reservation absent | Shared operations/release/migration surfaces; serial integration |
| `OPP-FORMAL-AUTHORITY-READINESS-001` | NO | Packet is ready; implementation remains authority-gated | Formal provider/source, effective date, and owner approval absent | Opportunity API/schema/frontend release surface; serial integration |
| `TOPIC-AUTHORITY-RECOVERY-001` | NO | Packet is ready; authority readback and fail-closed acceptance only | Structural-role authority and approved projection data absent | Topic/Lifecycle/schema surface; serial integration |
| `B3-INITIATION-REVIEW-001` | NO | Scope/evidence review only | No authoritative scope or implementation evidence | Locked |
| `B4-INITIATION-REVIEW-001` | NO | Scope/evidence review only | No authoritative scope or implementation evidence | Locked |
| `F-POST-CLOSURE-RECONCILIATION-001` | NO | Owner-requested F-series status reconciliation only | F1-F3 unknown; F4-F9 branch-only closure; no owner activation | Today/UI overlap; serial if activated |
| `FUND-001` | NO | Owner decision packet only | Formal institution-flow authority and acceptance decision absent | New provider/schema/API/frontend surface; serial |
| `REL-002-OPERATOR-READBACK-001` | INDEPENDENT | External exact runtime/release readback | Operator access; not a source-code workstream | Independent release gate |

## Safe parallel groups

### Group A — isolated recovery audits

Today and A10/A9 may perform read-only audits concurrently because each has its
own branch/worktree and neither may write shared canonical files during the
audit. Their findings must be integrated serially after file-level ownership
and source-to-candidate mapping are reviewed.

### Group B — authority packet preparation

Opportunity and Topic may prepare evidence packets in isolated worktrees, but
their implementation gates remain closed. Neither may populate a provider,
publish derived data, alter a migration, or change the shared frontend/API
contract without the missing authority decision.

### Serial-only surfaces

The following are always integrated one governed task at a time from a current
committed base: Alembic migrations; schema/model changes; OpenAPI and generated
client changes; shared Home/Topic contracts; release/deployment configuration;
provider registry and scheduler activation; Production data or deployment.

## Sync and integration protocol

1. Begin from the recorded base SHA and verify the worktree is clean.
2. Fetch/read new evidence without rewriting history. If the base advances,
   stop and record the new base; do not force-rebase a shared branch.
3. Keep source contract, generated artifact, consumer, and drift tests in one
   bounded change set. Generated output alone is not an implementation.
4. Before integration, run conflict and ownership review, targeted validation,
   `git diff --check`, and the applicable API/schema/migration checks.
5. Integration creates a new exact-SHA candidate or merge commit under Owner
   authorization. It does not make the branch Production or change `NEXT_TASK`.
6. Release promotion remains separate and requires exact API/Web/Worker/DB,
   migration, data, rollback, and post-deploy evidence.
