# GOV-002 — Parallel Workstream Recovery and Branch Hygiene

**Date:** 2026-09-13 (Asia/Taipei)
**Status:** `COMPLETE — DEVELOPMENT TOPOLOGY RECOVERED; PRODUCT WORK NOT STARTED`
**Authority:** repository/Git/committed evidence/runtime readback only

## Executive result

GOV-002 established a recoverable development topology for the four requested
parallel lines and reconciled their branch, worktree, dependency, and
integration boundaries. The development integration base is the clean
main-derived REL-002 candidate:

```text
SHA:    a8357d46194f9669709f184949270e20a7a2546c
Branch: codex/rel-002-release-candidate-20260913
Base:   origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
```

This SHA is suitable as a shared development/recovery starting point. It is
not a Production SHA, not a released revision, and not a substitute for the
independent `REL-002-OPERATOR-READBACK-001` gate.

The four isolated recovery branches/worktrees are registered in
[BRANCH_RECOVERY_MATRIX.md](../../BRANCH_RECOVERY_MATRIX.md). Their initial
tip is the same `a8357d...`; each is clean and task-scoped sparse. GOV-002 made
no product implementation commit, did not run a migration, did not activate a
scheduler/provider, did not deploy or mutate Production, and did not change
`NEXT_TASK`.

## Gate result

```yaml
PROJECT_MEMORY.RECOVERABLE: YES
DEVELOPMENT_INTEGRATION_BASE.KNOWN: YES
ACTIVE_WORKSTREAMS.ALL_REGISTERED: YES
EACH_ACTIVE_WORKSTREAM.BASE_SHA_BRANCH_WORKTREE_OWNER_DEPENDENCIES_NEXT_TASK_FILE_OWNERSHIP_KNOWN: YES
OLD_DIVERGED_BRANCHES.DISPOSITIONED: YES
DIRTY_OWNER_CHECKOUT.USED_FOR_DEVELOPMENT: NO
PARALLEL_EXECUTION_MATRIX.COMPLETE: YES
NEXT_TASKS.NAMED_AND_GOVERNED: YES
PRODUCT_FEATURE_IMPLEMENTATION_STARTED: NO
MEMORY_RECOVERY_COMPLETE: YES
ALLOW_NEW_DEVELOPMENT: YES_ONLY_THROUGH_NAMED_GOVERNED_TASK
```

“Allow new development” means a later task may start after reading this
registry and its applicable contract. It does not grant a blanket permission
to implement all four product lines.

## A. Development baseline and repository hygiene

| Layer | Verified state |
|---|---|
| Canonical repository | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Canonical remote baseline | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| Development integration base | `a8357d46194f...` from clean main-derived REL-002 candidate |
| Canonical governance parent | `6f03372b38efbfe5634cc2d1703fef28d373ce80` |
| Owner checkout | 1 tracked modification + 151 untracked entries at the preserved pre-GOV-002 check; no staged entries |
| Development in owner checkout | Prohibited; owner changes and historical artifacts remain untouched |
| Production API | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`, diverged Today branch |
| Production Web/Worker/DB exact identity | Not obtainable in this readback |
| Candidate migration line | One head at `0039_task_a9_b2_formal_correction_supersession` |

The owner dirty/untracked state is evidence, not release proof. GOV-002 did not
stage, clean, reset, rewrite, or classify individual owner files beyond the
aggregate preservation rule.

## B. Workstream status

### Opportunity

`BLOCKED / AUTHORITY_AND_PUBLICATION_GAP`. The bounded formal Opportunity
contract is present on the candidate, but runtime evidence remains shadow and
synthetic: `/api/v1/opportunities/shadow` was ready while `/api/v2/opportunities`
was 404. There is no configured formal provider or approved publication data
authority. The recovery packet is `OPP-FORMAL-AUTHORITY-READINESS-001`, with
owner/formal-data authority as the dependency. The shadow algorithm, ranking,
recommendation semantics, and page redesign are explicitly out of scope.

### Today Market Signals

`PARTIAL / BRANCH_DIVERGED`. The public API reports `bf68cc8...` from the
Today production-convergence branch, not the canonical main baseline. The
Today line includes a broad commercial/UI chain, persisted-focus/breadth fixes,
deterministic signals publication, and generated artifacts. Some commits are
bounded sources for recovery; the broad convergence commit is split-required.
`TODAY-MAINLINE-RECOVERY-001` may audit and map this chain, but no blind port
or new Signals implementation is authorized by GOV-002.

### A10 / A9

`PARTIAL / BRANCH_ONLY_AND_OPERATOR_GATED`. The A10/A9 branches contain
13:35 POST_CLOSE trigger, formal writer/release wiring, isolated quote
publication, and migration `0040` evidence. These commits are not one safe
merge unit. POST_CLOSE runtime evidence is partial (552 requested, 347 success,
205 failure, 240 retries), and operator/release readback is missing.
`A10-A9-RECOVERY-RECONCILIATION-001` owns evidence mapping only. Migration
0040, scheduler activation, provider activation, and Production writes are
forbidden in this recovery task.

### Topic / B2

`BLOCKED / STRUCTURAL_ROLE_AUTHORITY`. Mainline includes the bounded Topic
Lifecycle and formal publication contracts through migration 0039. Runtime
identity and snapshots are readable, but Lifecycle, Score/Grade, ranking,
leadership, and related derived publication remain deferred or fail-closed
because structural-role authority is incomplete. B2 branch content is already
represented in mainline; later writer changes remain branch-only.
`TOPIC-AUTHORITY-RECOVERY-001` prepares authority readback only and must not
redesign Topic semantics or publish derived values.

### B3 / B4

`UNKNOWN / NOT_STARTED`. The scan found no authoritative implementation,
closure, active branch, or runtime evidence that establishes either line. They
remain locked with no worktree. `B3-INITIATION-REVIEW-001` and
`B4-INITIATION-REVIEW-001` are review packets, not implementation tasks.

## Evidence scan summary

The repository archaeology covered Git history/refs/worktrees, task and report
directories, handoffs and decisions, migration heads, schema/OpenAPI/generated
client paths, backend routes, frontend consumers, and marker candidates
(`TODO`, `FIXME`, `HACK`, `placeholder`, `mock`, `legacy`, `deprecated`). The
marker scan identified legacy/V1, mock/synthetic, generated, and partially
wired candidates, but no candidate was promoted or deleted by name alone.
File liveness remains an owner-and-consumer question recorded in the incomplete
registry.

| Surface | Repository/runtime finding | Classification |
|---|---|---|
| Schema and migrations | Candidate line has one head at `0039_task_a9_b2_formal_correction_supersession`; branch-only A10 `0040` is retained but excluded from recovery integration | `VERIFIED` baseline / `PARTIAL` branch recovery |
| API and OpenAPI | Home v2, Topic, Topic Snapshot, Stock, and the shadow Opportunity route were readable in the available runtime; formal `/api/v2/opportunities` was 404 | `PARTIAL`; fail-closed where formal data is absent |
| Frontend consumers | Topic disclosure/fail-closed consumers are canonicalized; Today commercial/UI consumers are branch-diverged; Opportunity page is fail-closed when formal data is absent; Header, AI Research, Search, and Account remain partial or unknown | `MIXED / PARTIAL / UNKNOWN` |
| Reference / Instrument / Relation authority | Committed authority evidence records 79 instruments, 49 approved, 30 excluded, 1,160 relations, and 107 leaf nodes; this does not by itself prove current derived Topic publication | `VERIFIED` for the bounded evidence / `BLOCKED` for downstream derived publication |
| TODO/FIXME/HACK and placeholder/mock/legacy/deprecated candidates | Candidates exist across historical, synthetic, generated, legacy, and partially wired paths; no owner disposition proves them live, dead, or abandoned | `UNKNOWN` until file-level consumer mapping |

This scan is intentionally conservative: an implementation file, fixture,
closure report, generated client, or UI route is not completion evidence without
the corresponding contract, consumer, runtime, and release-layer proof.

### F1-F9

`MIXED`. F4-F9 closure reports are present on the Today branch history but not
identified as current canonical-main closures; they are preserved as
`BRANCH_ONLY_CLOSED / SUPERSEDED_FOR_CURRENT_BASE`. F1-F3 closure evidence was
not found in the canonical evidence scan and remains `UNKNOWN`. Code or closure
report presence does not promote either group to current Production or
mainline completion. No F-series implementation is reopened by GOV-002.

### FUND-001

`PROPOSED / OWNER_DECISION_REQUIRED`. The existing initiation packet is the
only governed next step. Formal institution-flow authority, PIT contract,
provider, persistence, consumer, and release gates remain undecided. No branch
or implementation worktree is created.

## C. Branch recovery and divergence decisions

The detailed matrix is [BRANCH_RECOVERY_MATRIX.md](../../BRANCH_RECOVERY_MATRIX.md).
The essential decisions are:

- `origin/main@b2eaf33` remains the canonical repository baseline.
- `a8357d...` is the shared development integration base because it is a clean
  main-derived candidate with a single migration head and bounded approved
  Opportunity composition. It remains release/operator-gated.
- Today branches `bf68cc8...` and `569d2b4...` are source evidence, not direct
  development bases. Their broad release/UI commits require file-level split
  and source-to-candidate mapping.
- A10/A9 branches `51dbe48...`, `68600af...`, and `17523a8...` are source
  evidence with serial integration boundaries. `0040` is retained but not
  ported.
- A10 production/batch branches and B2 authority branch are already represented
  in mainline history and are retained as historical references.
- Old detached and task worktrees remain retained. GOV-002 does not delete or
  clean historical evidence.

## D. Parallel execution matrix

The complete matrix is [PARALLEL_EXECUTION_MATRIX.md](../../PARALLEL_EXECUTION_MATRIX.md).
The safe topology is:

| Group | Can run | Constraint |
|---|---|---|
| Group A | Today and A10/A9 read-only recovery audits | Separate worktrees; no shared writes; serial integration afterward |
| Group B | Opportunity and Topic authority packet preparation | Both implementation gates remain closed pending authority |
| Serial-only | schema/migration/OpenAPI/generated/release/provider/scheduler surfaces | One governed task at a time from a current committed base |
| Independent | REL-002 operator readback | External runtime/release evidence; never use its absence to force product work |
| Locked | B3/B4, F1-F3, FUND-001 | Scope/authority/owner decision required |

## E. Governance policies now canonicalized

### Branch policy

Every product change starts from a recorded exact SHA on a named task branch.
Existing divergent branches are evidence sources until explicitly mapped.
No force-rebase, force-push, branch deletion, or historical cleanup occurs in
recovery.

### Worktree policy

The canonical owner checkout is not a product development worktree while
dirty. Each active packet uses a dedicated worktree, verifies clean status, and
records its path and base SHA. Sparse worktrees are scope controls, not proof
that an absent file never existed.

### Sync policy

A task reads/fetches new evidence and records base movement. It does not
silently rebase shared work or overwrite another task's state. Base changes
require a new mapping/review before integration.

### Shared-file policy

Schemas/models, migrations, OpenAPI/generated clients, shared Home/Topic
contracts, release configuration, provider registries, and scheduler entry
points are serial integration surfaces. Frontend-only parallelism is allowed
only for disjoint routes/assets with explicit ownership.

### Generated-artifact policy

Generated clients/types are downstream outputs. A governed change must identify
the source contract, regenerate deterministically, and pass drift checks.
Generated files alone are not completion evidence.

### Migration policy

Migration heads are integrated serially and checked against the candidate line.
Branch-only `0040` is not ported by recovery. Local migration success is not
Production migration proof.

### Integration and release policy

Recovery findings become an exact-SHA candidate only after ownership, conflict,
targeted validation, and contract drift checks. Release requires separate exact
API/Web/Worker/DB, migration/data, rollback, and post-deploy evidence. Runtime
readback must not be inferred from source existence.

## F. Recovery commits, branches, and worktrees

GOV-002 governance changes are made only in the canonical repository and are
recorded in the post-change Git handoff. The four recovery branches listed in
the matrix were created from `a8357d...` with no product changes. Their initial
worktrees are clean and sparse. The REL-002 candidate worktree remains clean
and separate. The canonical owner checkout's dirty/untracked state remains
unchanged by design.

## G. Ready-to-launch task packets

| Packet | Base | Branch/worktree | Launch condition | Do not touch |
|---|---|---|---|---|
| `TODAY-MAINLINE-RECOVERY-001` | `a8357d...` | Today recovery branch/worktree | Start after reading Home/Signals contracts and recording the branch commit map | No new market semantics, no Production branch mutation, no broad cherry-pick |
| `A10-A9-RECOVERY-RECONCILIATION-001` | `a8357d...` | A10/A9 recovery branch/worktree | Start read-only; operator readback is required before implementation recommendation | No `0040`, scheduler activation, provider activation, Production write |
| `OPP-FORMAL-AUTHORITY-READINESS-001` | `a8357d...` | Opportunity recovery branch/worktree | Owner supplies formal provider/authority and effective-date decision | No algorithm redesign, recommendation semantics, formal publication activation |
| `TOPIC-AUTHORITY-RECOVERY-001` | `a8357d...` | Topic recovery branch/worktree | Owner-reviewed structural-role authority becomes available | No Topic redesign, Score/Grade publication, or relation rewrite |

The safe next action is `TODAY-MAINLINE-RECOVERY-001` as a read-only recovery
audit, because it can produce a bounded source-to-candidate map without
requiring a missing provider or protected runtime authority. This is a
recommendation only; the Owner-controlled `NEXT_TASK` was not modified.

## Consistency check and final classification

The registries cross-reference one another, use the same `a8357d...` recovery
base, identify the same Production/runtime gaps, and preserve the same branch
dispositions. The final state is:

```text
MEMORY RECOVERY COMPLETE
DEVELOPMENT TOPOLOGY GOVERNED
NEW DEVELOPMENT ALLOWED ONLY THROUGH NAMED TASK PACKETS
PRODUCT FEATURE IMPLEMENTATION: NOT STARTED
PRODUCTION RELEASE: NOT VERIFIED / OPERATOR BLOCKED
```
