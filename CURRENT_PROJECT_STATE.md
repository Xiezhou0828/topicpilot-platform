# TopicPilot Current Project State

**State:** `OWNER CLOSURE COMPLETE / HISTORICAL RECOVERY CLOSED / RELEASE GATE OPEN`
**As of:** `2026-09-16` (Asia/Taipei)
**Authority:** Repository, Git, committed evidence reports, and obtainable
runtime readback. Chat memory and task prompts are discovery inputs only.

## Current truth

```yaml
PROJECT_MEMORY_RECOVERABLE: YES
HISTORICAL_RECOVERY: CLOSED
CANONICAL_LINEAGE: VERIFIED
OWNER_CLOSURE_TASK: TASK-OWNER-TOPICPILOT-CANONICAL-PROMOTION-RELEASE-AND-RUNTIME-CLOSURE-001
OWNER_CANONICAL_PROMOTION_SHA: 277a49382240503fcd0767e9cfb17e2fd974e8a3
FORWARD_DEVELOPMENT_BASE_SHA: 277a49382240503fcd0767e9cfb17e2fd974e8a3
READY_FOR_CLEAN_FORWARD_DEVELOPMENT: YES
GOV_002_STATUS: COMPLETE_DEVELOPMENT_TOPOLOGY_RECOVERED
CANONICAL_REPOSITORY: C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_OWNER_CHECKOUT_DEVELOPMENT_USE: NO
CANONICAL_OWNER_CHECKOUT_STATE: DIRTY_OWNER_CONTROLLED_STATE_PRESERVED
CANONICAL_DOCUMENTATION_PARENT: 6f03372b38efbfe5634cc2d1703fef28d373ce80
REPOSITORY_BASELINE: origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
DEVELOPMENT_INTEGRATION_BASE: 277a49382240503fcd0767e9cfb17e2fd974e8a3
DEVELOPMENT_INTEGRATION_BASE_KIND: OWNER_CONTROLLED_CANONICAL_CLOSURE_BASELINE
DEVELOPMENT_INTEGRATION_BASE_PRODUCTION_STATUS: NOT_PRODUCTION / NOT_RELEASED
PRODUCTION_API_SHA: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
PRODUCTION_API_SHA_RELATION: DIVERGED_TODAY_PRODUCTION_CONVERGENCE_BRANCH
PRODUCTION_EXACT_SOURCE_SHA_VERIFIED: API_ONLY
PRODUCTION_WEB_SHA_VERIFIED: NO
PRODUCTION_WORKER_SHA_VERIFIED: NO
PRODUCTION_PROTECTED_DB_REVISION_VERIFIED: YES_OPERATOR_READBACK_2026-09-15
PRODUCTION_PROTECTED_DB_REVISION: 0040_task_a10_recovery_checkpoint_observability
PRODUCTION_POST_DEPLOY_VERIFIED: PARTIAL_API_ONLY
PRODUCTION_RELEASE_GATE: BLOCKED_PROVENANCE
MIGRATION_CANDIDATE_HEAD: 0040_task_a10_recovery_checkpoint_observability
MIGRATION_EXECUTION: NONE
FORMAL_OPPORTUNITY_PUBLICATION: NOT_PUBLISHED / SHADOW_ONLY_IN_RUNTIME
TOPIC_DERIVED_PUBLICATION: DEFERRED / FAIL_CLOSED
POST_CLOSE_RUNTIME: FAILED_RUN_PARTIAL_FRESHNESS
POST_CLOSE_LATEST_STATUS: FAILED
POST_CLOSE_LATEST_SESSION: 2026-09-15 POST_CLOSE
POST_CLOSE_FAILURE_CODE: EXCHANGE_NO_DATA
PRODUCTION_WEB_EXACT_SOURCE_SHA_VERIFIED: NO_OPAQUE_DEPLOYMENT_ONLY
PRODUCTION_WORKER_EXACT_SOURCE_SHA_VERIFIED: UNKNOWN_NOT_READABLE
CANARY_AUTHORIZATION: NOT_AUTHORIZED
FORMAL_OPPORTUNITY_INPUT_READINESS: BLOCKED
NEXT_TASK_MUTATED_BY_GOV_002: NO
PRODUCT_FEATURE_IMPLEMENTATION_STARTED_BY_GOV_002: NO
```

The owner-controlled canonical closure baseline is the shared starting point
for clean forward development. It contains the verified unified candidate and
the closure records for the recovered historical scope. It is not a claim
that the current Production runtime is serving this SHA.

## Runtime and publication boundary

- API readback is live at bf68cc8bf0a4432d7623db43f42e9219c94d7b6b.
  /healthz and /readyz are available. The protected database readback is
  revision 0040_task_a10_recovery_checkpoint_observability. Exact Web/Worker
  source SHAs remain unavailable, so release provenance is partial.
- Home is formally readable but partial: the runtime readback was as-of
  `2026-09-09`, with optional market-events/opportunity sections unavailable
  and heating/cooling unavailable for insufficient formal rotation history.
- Topic identity/snapshot reads are published, while Lifecycle and derived
  Score/Grade/ranking/leadership outputs remain deferred by the structural-role
  authority gate.
- The runtime Opportunity route is the shadow synthetic contract; the formal
  `/api/v2/opportunities` route was not published in the readback.
- POST_CLOSE is operationally failed/partial: the latest obtainable run on
  2026-09-15 requested 553, succeeded for 0, failed for 347, skipped 206,
  recorded 0 retries, and reported EXCHANGE_NO_DATA. This is evidence for
  forward operational remediation, not a claim of healthy automation.

## Workstream routing

| Line | Current state | Canonical routing |
|---|---|---|
| Opportunity | `BLOCKED / AUTHORITY_AND_PUBLICATION_GAP` | `TASK-OPP-REC-002` owns evidence and formal-authority readiness only; shadow algorithm is not reopened |
| Today Market Signals | `PARTIAL / BRANCH_DIVERGED` | `TASK-TODAY-REC-002` audits and maps the branch-only chain before any bounded port |
| A10 / A9 | `PARTIAL / BRANCH_ONLY_AND_OPERATOR_GATED` | `TASK-A10-A9-REC-002` reconciles writer, quote, post-close, and migration evidence; no scheduler or migration activation |
| Topic / B2 | `BLOCKED / STRUCTURAL_ROLE_AUTHORITY` | `TASK-TOPIC-REC-002` prepares authority readback; no Topic redesign or score publication |
| B3 / B4 | `UNKNOWN / LOCKED_NOT_STARTED` | No branch or worktree by design; initiation review only |
| F1-F9 | `MIXED / MAINLINE_STATUS_NOT_UNIFORMLY_VERIFIED` | F4-F9 are branch-only historical closures; F1-F3 are `UNKNOWN`; no automatic reopen |
| FUND-001 | `PROPOSED / OWNER_DECISION_REQUIRED` | Institution-flow initiation packet only; no implementation branch |

Exact ownership, file sets, dependencies, next named tasks, and worktree
locations are maintained in [ACTIVE_WORK.md](ACTIVE_WORK.md). Unfinished,
partial, blocked, unknown, and superseded evidence is maintained in
[INCOMPLETE_WORK_REGISTRY.md](INCOMPLETE_WORK_REGISTRY.md).

## Canonical evidence navigation

- [Active work and ownership](ACTIVE_WORK.md)
- [Incomplete work registry](INCOMPLETE_WORK_REGISTRY.md)
- [Branch recovery matrix](BRANCH_RECOVERY_MATRIX.md)
- [Parallel execution matrix](PARALLEL_EXECUTION_MATRIX.md)
- [GOV-002 recovery report](docs/reports/TASK-GOV-002-PARALLEL-WORKSTREAM-RECOVERY-AND-BRANCH-HYGIENE-20260913.md)
- [GOV-001 canonical reconciliation](docs/reports/TASK-GOV-001-CANONICAL-RECONCILIATION-20260913.md)
- [REL-002 release composition and operator readback](docs/reports/TASK-REL-002-RELEASE-COMPOSITION-AND-OPERATOR-READBACK-20260913.md)

## Status vocabulary and decision rule

`VERIFIED` means the claimed boundary has direct evidence at the stated
repository/runtime layer. `IN_PROGRESS` means active work exists but the
acceptance boundary is open. `PARTIAL` means only a bounded slice is proven.
`BLOCKED` means a named prerequisite prevents the next governed action.
`SUPERSEDED` means a later evidence-backed baseline replaces the prior route.
`ABANDONED` is used only when an explicit owner or repository disposition says
so. `UNKNOWN` means the repository evidence is insufficient. Code existence,
passing isolated tests, or a chat statement does not promote a row to
`VERIFIED`.
