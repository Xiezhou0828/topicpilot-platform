# TASK-INT-CANONICAL-LINEAGE-CONVERGENCE-AND-RELEASE-BASELINE-001

## Final summary

```text
TASK: TASK-INT-CANONICAL-LINEAGE-CONVERGENCE-AND-RELEASE-BASELINE-001
ROLE: INTEGRATION_OWNER_AND_CANONICAL_BASELINE_OWNER
MODE: ONE_SHOT_GLOBAL_CANONICAL_LINEAGE_CONVERGENCE_AND_RELEASE_BASELINE
RESULT: COMPLETE_WITH_EXTERNAL_GATE
STOP_REASON: PRODUCTION_OPERATOR_AUTHORITY_REQUIRED

PREVIOUS_CANONICAL_SHA: 02d3086183d1c582bb6c66c4c316340ccce3fa97
PREVIOUS_GOVERNED_BASELINE_SHA: a8357d46194f9669709f184949270e20a7a2546c

UNIFIED_CANONICAL_DEVELOPMENT_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772
UNIFIED_GOVERNED_BASELINE_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772

GOV003: VERIFIED / CANONICAL_INTEGRATED
TODAY: INTEGRATED / CLOSED
MIGRATION_0040: CANONICAL_PROVENANCE_VERIFIED
A10_1335: COMPLETE / ALREADY_PRESENT
A10_POST_CLOSE: COMPLETE / CANONICAL_INTEGRATED
B2_003F: VERIFIED / CANONICAL_INTEGRATED
B2_LAYER2_FORMAL_AUTHORITY: READY / PUBLICATION_BLOCKED / NOT_ACTIVE
B2_DB_107_25_107_1160: VERIFIED / EVIDENCE_ONLY
F1_F9_HISTORICAL_RECOVERY: VERIFIED / PROVENANCE_ONLY
F6_F7_CANONICAL: INTEGRATED
OPS_REMEDIATION_CANONICAL: INTEGRATED

UNKNOWN_HISTORICAL_IMPLEMENTATIONS: 0
UNKNOWN_PROVENANCE_BLOCKERS: 0
UNKNOWN_MIGRATION_COLLISIONS: 0
ORPHAN_GOVERNANCE_RECORDS: 0 TASK-SCOPED

BACKEND_TESTS: 807 collected; 739 passed; 59 skipped; 9 registered TOPIC_B2 baseline failures; 0 task-caused; 0 unknown
WEB_TESTS: 164 passed; 0 failed
OPENAPI_DRIFT: PASS
GENERATED_CLIENT_DRIFT: PASS

TASK_CAUSED_FAILURES: 0
REGISTERED_BASELINE_FAILURES: 9 active; migration-head baseline resolved
UNKNOWN_FAILURES: 0

INTEGRATION_GATE: PASS
RELEASE_GATE: BLOCKED_PROVENANCE

RELEASE_CANDIDATE_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772
PRODUCTION_EXACT_SHA: UNAVAILABLE_OPERATOR_READBACK_REQUIRED
PRODUCTION_DB_REVISION: 0040_task_a10_recovery_checkpoint_observability
OPS_PRODUCTION_CANARY: NOT_EXECUTED_OPERATOR_AUTHORITY_REQUIRED

HISTORICAL_RECOVERY_STATUS: CANONICAL_CONVERGENCE_COMPLETE
HISTORICAL_GOVERNANCE_DEBT: NONE_TASK_SCOPED; inherited TOPIC_B2 lifecycle baseline remains registered and non-blocking to this Integration workstream

NORMAL_FORWARD_DEVELOPMENT_BACKLOG: Leader Set authority/publication; Lifecycle publication; A9 formal writer; B2 formal publication activation; Daily Close E2E/freshness; Opportunity daily recommendation; remaining Stock capabilities; FUND-001 Institutional Flow; later F1-F9 implementation

READY_TO_START_DAILY_CLOSE_E2E: NO
OPPORTUNITY_DAILY_RECOMMENDATION_READY: NO_NOT_YET_VERIFIED

PROJECT_MEMORY_RECOVERY_TEST: PASS

C_DRIVE: UNTOUCHED
PRODUCTION: UNTOUCHED
MIGRATION_EXECUTION: NOT_PERFORMED
PUSH: NO

IMPLEMENTATION_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772
GOVERNANCE_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772
FINAL_CLOSEOUT_SHA: d6371af5994f0c2d5e0612969f100f6cef26b772

OWNER_DECISION_REQUIRED: NO
INTEGRATION_OWNER_ACTION_REQUIRED: NO
RELEASE_OWNER_ACTION_REQUIRED: YES

NEXT_GOVERNED_ACTION: Owner review and promotion of the exact E candidate into C; release owner readback of exact Production API/Web/Worker SHAs and separate canary authorization.
```

## Scope and protected boundaries

This was a repository-side canonical lineage convergence, not feature development. A fresh isolated worktree was created at:

`E:\topicpilot-worktrees\int-canonical-lineage-convergence-and-release-baseline-001-20260916`

The protected owner checkout remained unchanged:

| Item | Evidence |
|---|---|
| C path | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| C HEAD before/after | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| C branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| C pre-existing status entries | 152 |
| C mutation | None |
| Production mutation | None |
| Migration execution | None |
| Push | None |

## Canonical lineage matrix

| Workstream | Source evidence | Implementation | Governance | Canonical development | Production state |
|---|---|---|---|---|---|
| GOV-003 | Verified | Verified | Verified | Integrated | Not released |
| Today Signals | Verified (`e4d6754`, `4bd1850`) | Verified | Verified (`4fc7983`) | Integrated (`9ec77e0`) | Not released |
| Migration 0040 / A10 | Verified exact source blob and SHA256 | Verified | Verified | Canonical | Evidence-only |
| A10 13:35 | Verified (`68600af`) | Complete; already present | Verified | Integrated | Not released |
| A10 post-close | Verified (`35a4e53`) | Complete | Verified | Integrated | Not released |
| B2 003F | Verified (`05c4866`, `34fb730`) | Verified | Verified | Integrated | Evidence-only |
| B2 Layer 2 | Verified actual reachable source objects | Verified | Verified | Ready; publication blocked | Not active |
| B2 DB readback | Operator evidence verified | N/A | Verified | Provenance registered | Evidence-only |
| F1-F9 recovery | Historical map verified | Provenance-only | Verified | Provenance-only | Evidence-only |
| Stock F6/F7 | Verified (`a47a693`, `f5153cf`) | Verified | Verified | Integrated (`b8f1689`) | Not released |
| OPS remediation | Newer canonical source verified | Verified (`9d327ea`) | Verified (`25a8d3d`) | Integrated | Canary not executed |

The unavailable original rematerialized OPS IDs are not unknown blockers. They are superseded by the newer canonical OPS integration and closeout, which preserve the transaction containment surface. Likewise, the malformed historical A10/B2 IDs were resolved by reachable exact source objects and the verified 0040 source hash; no implementation was invented.

## Migration reconciliation

The candidate has one migration source for the canonical head:

```text
0039_task_a9_b2_formal_correction_supersession
  -> 0040_task_a10_recovery_checkpoint_observability
```

Source: `services/api/alembic/versions/0040_task_a10_recovery_checkpoint_observability.py`

Source commit: `51dbe48db203adb56e5fbc47da2f44b0e33997d2`

SHA256: `FA435D2DC1E632A0B11E454484ADB6F59FA49B0D273845E315500A45EC2D063E`

The Today historical 0040 candidate was not reintroduced. No 0041 migration was created, and no migration was executed. The stale baseline assertion that expected the former 0036 head was updated to the actual converged 0040 head and marked resolved in the baseline registry.

## B2 authority and readback

The recovered B2 Layer 2 contract remains fail-closed and unchanged in meaning:

- schema: `topic-layer2-formal-authority.v1`
- policy: `POLICY_APPROVED`
- publication: `BLOCKED`
- activation: `NOT_ACTIVE`
- Daily Strength: `PARTIAL_BY_DESIGN`, fail closed
- Score/Grade: `APPROVED_VERIFIED`
- lifecycle: `SPROUTING`, `FERMENTING`, `MAIN_RISE`, `MATURE`, `DECLINING`
- 003G: PASS; 003H: PASS

The governed operator readback remains trusted provenance rather than being downgraded because this isolated worktree has no Production credentials:

| Readback | Verified value |
|---|---:|
| Production DB revision | `0040_task_a10_recovery_checkpoint_observability` |
| B2 leaves | 107 |
| B2 parents | 25 |
| hierarchy edges | 107 |
| structural-role rows | 1,160 |
| formal snapshot rows | 92 |
| structural roles | all APPROVED |

Source manifest SHA256: `992B8F676C19519B443B3BCDD870AFF577D54E72B302D174B5B1CA73588FFA2F`

## Validation and failure classification

The practical validation was run after semantic overlap repairs.

| Area | Result |
|---|---|
| Backend full suite | 807 collected; 739 passed; 59 PostgreSQL/environment skips; 9 registered lifecycle baselines |
| A10/OPS/convergence focused checks | 39 passed; 1 registered lifecycle baseline |
| Governance runtime | 8 passed |
| Web build and tests | 164 passed; build completed |
| TypeScript | PASS |
| Web lint | PASS; 0 errors; 2 pre-existing warnings |
| OpenAPI/generated-client drift | PASS / PASS |
| Targeted Ruff | PASS |
| Python compileall | PASS |
| Conflict-marker scan | PASS |
| Project Memory recovery | PASS |

The nine backend failures are the already-registered `TOPIC_B2` lifecycle contract/engine baselines. They are not owned by this Integration task, were not introduced by the convergence, and remain visible in `docs/governance/BASELINE_FAILURE_REGISTRY.yaml`. The former migration-head assertion was task-reconciled and is now recorded with `resolved_by: dc8534adee9696c1a52097e8d9698631203e1cf0`. No unknown or task-caused failure remains.

Repository-wide Ruff/format still expose inherited hygiene debt in the large recovered historical merge surface. Targeted runtime Ruff passed. The reported EOF/trailing-space findings were normalized in E, and the final `git diff --check` is PASS; no formatting finding was silently treated as a semantic regression or used to weaken tests.

## Gate decisions

The Integration Gate is `PASS` with a registered unrelated baseline. The candidate has no unknown lineage, provenance, collision, ownership, or task-caused regression blocker.

The release gate is `BLOCKED_PROVENANCE`, not because canonical convergence failed, but because exact Production API/Web/Worker SHAs and operator authority for a canary were not available. Migration compatibility is `MIGRATION_COMPATIBLE` at 0040. Engineering readiness of the candidate surfaces is distinct from Production release readiness.

No Daily Close E2E task was started. Its exact blockers are owner-controlled promotion of the candidate, exact Production SHA readback, and separate governed freshness/readback authorization. Opportunity daily recommendation readiness is therefore not claimed.

## Historical debt versus forward backlog

### Historical / governance debt

Task-scoped historical debt is zero:

- unknown historical implementations: 0
- unknown provenance blockers: 0
- unknown migration collisions: 0
- orphan governance records: 0 task-scoped
- unclassified failures: 0

The inherited TOPIC_B2 lifecycle baseline remains a registered, non-blocking baseline for this Integration workstream. It is not normalised away and is not reclassified as convergence debt.

### Normal forward development

The following remain product backlog and were intentionally not developed here: Leader Set authority/publication, Lifecycle publication support, A9 formal writer, B2 formal publication activation, Daily Close E2E/freshness, Opportunity daily recommendation, remaining Stock capabilities, FUND-001 Institutional Flow, and later F1-F9 implementation work.

## Governed handoff

The manifest and complete provenance record are:

- `docs/governance/tasks/TASK-INT-CANONICAL-LINEAGE-CONVERGENCE-AND-RELEASE-BASELINE-001.yaml`
- `docs/governance/provenance/TASK-INT-CANONICAL-LINEAGE-CONVERGENCE-AND-RELEASE-BASELINE-001.json`

The candidate is ready for owner review and promotion from E into C. Release owner action remains required before any deployment or canary; this task performed neither.
