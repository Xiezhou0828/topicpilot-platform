# TASK-GOV-003-CANONICAL-PROMOTION-001

**Date:** 2026-09-14
**Target branch:** `codex/task-gov-003-canonical-promotion-001-20260914`
**Target worktree:** `E:\topicpilot-worktrees\gov-003-canonical-promotion-001-20260914`
**Scope:** GOV-003 governance runtime promotion and first governed-baseline qualification only

## 1. Recovered project state

The GOV-003 project-memory skill recovered the state from committed repository
documents, Git, manifests, registries, and worktree readback before mutation.
The authoritative values are:

| Item | Evidence-backed value |
|---|---|
| Canonical remote baseline | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| C: owner checkout | `02d3086183d1c582bb6c66c4c316340ccce3fa97` on `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Development integration base | `a8357d46194f9669709f184949270e20a7a2546c` |
| GOV-003 source base | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| GOV-003 source branch | `codex/gov-003-agentic-parallel-development-runtime-20260914` |
| Production API evidence | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`, diverged Today branch |
| Candidate migration | `0039_task_a9_b2_formal_correction_supersession` |
| Production protected DB migration | Exact revision not verified; `0040_task_a10_recovery_checkpoint_observability` is branch-only evidence |
| Production release gate | `BLOCKED_OPERATOR_READBACK` |
| Owner checkout state | 1 tracked modification, 151 untracked entries, 0 staged; preserved unchanged |

Active workstream status remains Today `PARTIAL/BRANCH_DIVERGED`, A10/A9
`PARTIAL/BRANCH_ONLY_AND_OPERATOR_GATED`, Topic/B2
`BLOCKED/STRUCTURAL_ROLE_AUTHORITY`, Opportunity
`BLOCKED/AUTHORITY_AND_PUBLICATION_GAP`, and REL-002
`BLOCKED/INDEPENDENT`. No product workstream was started.

## 2. Source GOV-003 commits

The source commit parentage is linear and was verified:

```text
4ecea21  parent 02d3086  governance: add task memory and ownership contracts
801a95b  parent 4ecea21  governance: add deterministic guards and CI
beb5b3d  parent 801a95b  docs(governance): record GOV-003 runtime and dry-run
```

Each source commit was inspected at commit scope. The source commits contain
governance skills, agents, hooks, scripts, tests, registries, manifests,
governance docs, central navigation, and the GOV-003 report. No source commit
was promoted as a broad branch diff.

## 3. Target development base selection

`a8357d46194f9669709f184949270e20a7a2546c` was selected because the recovered
`CURRENT_PROJECT_STATE.md`, `BRANCH_RECOVERY_MATRIX.md`, `ACTIVE_WORK.md`, and
GOV-002 report all designate it as the main-derived development integration
base. It is not Production truth and it does not silently absorb the diverged
Today, A10/A9, Topic, or Opportunity branches.

The source base `02d3086` and target `a8357d4` are not ancestor/descendant
relationships; their merge base is `7be817ec8e40b7a6cdce2fed9ff542ff2f4f7864`.
Therefore fast-forward promotion was not available.

```yaml
GOVERNED_DEVELOPMENT_BASE_SHA: 2a062d8de8ab637e02aa1021c715b248fdd1322c
TARGET_BASE_BEFORE_PROMOTION: a8357d46194f9669709f184949270e20a7a2546c
PRODUCTION_BASE_USED_AS_TARGET: NO
```

The exact governed baseline is the clean promotion commit shown above. The
preceding `0e021b0` qualification commit and this report-binding commit contain
no product changes; the latter only records the final clean baseline.

## 4. Promotion map

```yaml
GOV003_PROMOTION_MAP:
  SOURCE_BASE: 02d3086183d1c582bb6c66c4c316340ccce3fa97
  TARGET_DEVELOPMENT_BASE: a8357d46194f9669709f184949270e20a7a2546c
  COMMITS:
    - source: 4ecea21e69f76ee00c4e521dcdfd4dc2c51a3b46
      target: 96879fd
      disposition: SAFE_COMMIT
    - source: 801a95b1866cb46d8630d6c16b725544d6e0803e
      target: 9fbbb8d
      disposition: SAFE_COMMIT
    - source: beb5b3d850bb8def248239f829abe39bcd24979b
      target: f96b229
      disposition: SAFE_AFTER_CENTRAL_DOC_RECONCILIATION
  SAFE_COMMITS: [96879fd, 9fbbb8d, f96b229]
  REQUIRES_RECONCILIATION:
    - PROJECT_CONTEXT.md
    - docs/ROADMAP.md
    - docs/WORK_ORDERS.md
    - docs/DOCUMENTATION_INDEX.md
  CONFLICTS: CENTRAL_GOVERNANCE_NAVIGATION_ONLY
  FORBIDDEN_PRODUCT_DIFF: NONE
```

The large diff between the two divergent tips was not used as a promotion
unit. Only the three named source commits were ported.

## 5. Conflicts and reconciliation

The first two commits applied without conflict. The third commit conflicted in
the four central navigation documents because the target development base had
its own historical work-order/roadmap state. Resolution preserved the target
GOV-001/current work-order content and added the GOV-002, GOV-003, REL, and
documentation-navigation entries required by the source governance checkpoint.

No application, schema, migration, provider, scheduler, frontend, generated
client, or Production file was resolved or modified. Conflict-marker scanning
passed after reconciliation.

## 6. Final governed development baseline

The target branch contains the ordered GOV-003 port on top of the selected
development base, plus the promotion manifest and qualification report. The
final clean governed runtime commit SHA is `2a062d8de8ab637e02aa1021c715b248fdd1322c`; its only difference from
the preceding qualification state is whitespace normalization in promoted
governance files. The later report-binding commit is documentation-only.

```yaml
GOVERNED_DEVELOPMENT_BASE_KIND: MAIN_DERIVED_GOV003_GOVERNANCE_CANDIDATE
GOVERNED_DEVELOPMENT_BASE_PRODUCTION_STATUS: NOT_PRODUCTION
SOURCE_GOV003_RUNTIME: PROMOTED_BY_EXACT_COMMIT_PORT
REMOTE_PUSH: NO
C_OWNER_CHECKOUT_PROMOTION: NO
```

## 7. Governance runtime validation

Re-run results on the new target worktree:

```text
governance self-test: PASS
governance unit tests: 8 passed, 0 failed
manifest validation: PASS
ownership validation: PASS
lifecycle validation: PASS
worktree guard: PASS
JSON-compatible governance YAML: PASS
workflow YAML: PASS
Ruff: PASS
compile: PASS
git diff --check: PASS
conflict-marker scan: PASS
```

The release dry-run correctly returned `BLOCKED_MIGRATION` for candidate 0039
versus the branch-evidenced 0040 scenario. No migration command was executed.
The integration gate for the validated Today reconciliation returned `READY`
with safe commit `e4d675453aa03c51bd1c4e198ee3b7cb6742657f`.

## 8. Task-hardcoding audit

Reusable skills, agents, ownership logic, and integration/release guards are
manifest/registry-driven. The validator no longer requires a hardcoded set of
workstream names; it validates the registry shape and checks manifest
workstream references against the loaded registry. The status parser preserves
leading porcelain columns, preventing a first-path character loss during
ownership checks. Single-manifest validation resolves dependencies against the
repository manifest graph.

References to Today/A10/Topic/B2/Opportunity/REL remain only in task
manifests, ownership registry, collision matrix, and governance tests/dry-run
fixtures. The migration `0039`/`0040` pair remains only in release-gate
self-test evidence and the baseline/release governance boundary; it is not
product behavior.

```yaml
NEW_TASK_REQUIRES_SKILL_CHANGE: NO
NEW_WORKSTREAM_REQUIRES_SKILL_CHANGE: NO
TASK_BEHAVIOR_DRIVEN_BY: MANIFEST
OWNERSHIP_DRIVEN_BY: REGISTRY
```

## 9. A/B/C dry-run

All three manifests were re-resolved on the new governed base without starting
implementation:

| Task | Manifest | Dependencies | Base/worktree policy | Ownership/forbidden paths | Result |
|---|---|---|---|---|---|
| `TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003` | PASS | PASS | PASS | PASS | `PLANNED / DRY-RUN PASS` |
| `TASK-A10-POST-CLOSE-CHECKPOINT-RECONCILIATION-002` | PASS | PASS | PASS | PASS | `PLANNED / DRY-RUN PASS` |
| `TOPIC-B2-CANONICAL-ARTIFACT-PROVENANCE-AND-PUBLICATION-GATE-001` | PASS | PASS | PASS | PASS | `PLANNED / DRY-RUN PASS` |

No task changed from `PLANNED`, and no implementation commit was created for
any of them.

## 10. Parallel collision gate

| Surface | Today | A10/A9 | Topic/B2 | Authority / resolution |
|---|---|---|---|---|
| Bounded implementation paths | OWNED | OWNED | OWNED | Parallel isolated worktrees |
| Migrations | FORBIDDEN | FORBIDDEN/RESERVED | FORBIDDEN | Separate migration lineage task |
| OpenAPI | SHARED | SHARED | SHARED | Integration owner, serial |
| Generated clients | SHARED | SHARED | SHARED | Source contract plus drift check, serial |
| Shared schemas | SHARED | SHARED | SHARED | Integration owner, serial |
| Formal publication | SHARED/authority-gated | SHARED/authority-gated | SHARED/authority-gated | Authority and integration gate |
| Governance manifests | Registry-owned | Registry-owned | Registry-owned | Per-task manifest; no cross-task rewrite |
| Central governance docs | SHARED | SHARED | SHARED | Per-task report first; serial navigation reconciliation |
| Production/scheduler | FORBIDDEN | FORBIDDEN | FORBIDDEN | Operator/release gate only |

`PARALLEL_COLLISION_GATE=PASS` for isolated development. It does not authorize
independent shared-surface integration or Production qualification.

## 11. Central-doc conflict status

```yaml
CENTRAL_DOC_CONFLICT_RISK: PARTIAL
CENTRAL_DOC_POLICY: per-task manifests/reports first; serial reconciler for aggregate views
```

The four central documents still require serial updates when an aggregate
checkpoint is needed. GOV-003's runtime reduces future conflict by making task
manifests and reports the task-local source; this promotion did not redesign
the document hierarchy.

## 12. GitHub runtime/settings gaps

Repository-side Skills, custom agents, hooks, and merge-group-compatible CI
are present. Actual Copilot hook execution, GitHub branch protection/rulesets,
required checks, and Merge Queue settings were not accessible or mutated.
The deterministic replacement is repository scripts, unit tests, governance CI,
and a future integration-candidate branch qualification.

```yaml
HOOK_RUNTIME: UNVERIFIED
MERGE_QUEUE: NOT_CONFIGURED
BRANCH_PROTECTION: NOT_VERIFIED
SETTINGS_MUTATION: NO
```

These gaps do not block the governance-only development baseline.

## 13. C: safety evidence

The C: checkout was read-only throughout. Final readback remained:

```text
HEAD=02d3086183d1c582bb6c66c4c316340ccce3fa97
BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
STATUS_ENTRIES=152
TRACKED_ENTRIES=1
UNTRACKED_ENTRIES=151
STAGED_ENTRIES=0
```

No C: add, commit, merge, cherry-pick, stash, reset, restore, clean, build,
or temporary-file operation was performed.

## 14. Production safety evidence

Production was untouched. No deployment, database connection, migration
execution, scheduler activation, provider activation, release cutover,
rollback, or Production readback mutation occurred. The candidate/Production
migration comparison is a fail-closed read-only gate test only.

```yaml
PRODUCTION: UNTOUCHED
MIGRATION_EXECUTION: NO
MIGRATION_DOWNGRADE: NO
DATABASE_MUTATION: NO
DEPLOY: NO
```

## 15. Commits

Ported promotion commits:

```text
96879fd  governance: add task memory and ownership contracts
9fbbb8d  governance: add deterministic guards and CI
f96b229  docs(governance): record GOV-003 runtime and dry-run
0e021b0  governance: qualify GOV-003 canonical promotion
2a062d8  chore(governance): normalize promoted file endings
```

The final promotion manifest and this qualification report were committed in
qualification commit `0e021b0`; the clean whitespace normalization was recorded
in `2a062d8`. A subsequent documentation-only binding records that exact
baseline in this report.

## 16. Recommended next action

Owner review the exact target branch and final SHA, then use the short governed
task prompt to separately start one named A/B/C task. Do not start all three
automatically, do not begin INT-001, and do not port 0040 or any Product branch
content as part of this promotion.

```yaml
TASK: TASK-GOV-003-CANONICAL-PROMOTION-001
RESULT: COMPLETE
GOVERNANCE_RUNTIME_RECOVERY: PASS
CANONICAL_PROMOTION: COMPLETE
CANONICAL_PROMOTION_SCOPE: CLEAN_E_DRIVE_GOVERNED_DEVELOPMENT_BASE; NOT_PUSHED_OR_MERGED_TO_C_OWNER_CHECKOUT
GOVERNED_DEVELOPMENT_BASE_SHA: 2a062d8de8ab637e02aa1021c715b248fdd1322c
TASK_MANIFEST_RUNTIME: READY
OWNERSHIP_RUNTIME: READY
WORKTREE_RUNTIME: READY
INTEGRATION_GATE: READY
RELEASE_GATE: READY
RELEASE_GATE_MODE: FAIL_CLOSED
NEW_TASK_REQUIRES_SKILL_CHANGE: NO
NEW_WORKSTREAM_REQUIRES_SKILL_CHANGE: NO
TASK_BEHAVIOR_DRIVEN_BY: MANIFEST
OWNERSHIP_DRIVEN_BY: REGISTRY
TODAY_DRY_RUN: PASS
A10_A9_DRY_RUN: PASS
TOPIC_B2_DRY_RUN: PASS
PARALLEL_COLLISION_GATE: PASS
PARALLEL_COLLISION_SCOPE: ISOLATED_ONLY; SHARED_INTEGRATION_REMAINS_SERIAL
SHORT_PROMPT_RUNTIME_READY: YES
CENTRAL_DOC_CONFLICT_RISK: PARTIAL
READY_TO_START_A_B_C: YES
START_AUTHORIZATION: OWNER_REQUIRED
OWNER_DECISION_REQUIRED: NO
PRODUCTION: UNTOUCHED
C_DRIVE: UNTOUCHED
PUSH: NO
NEXT_RECOMMENDED_ACTION: Owner review final governed development SHA, then separately start one named A/B/C task.
```

Stop condition is satisfied: the governed development baseline is qualified,
and no A/B/C implementation was started.
