# Owner-approved development process

**Status:** Process v2; effective immediately upon merge to canonical `main`.
The canonical merge timestamp is the effective point.
**Owner approval:** Decisions A–O and `PROCESS_V2_EFFECTIVE_SCOPE`, recorded in the
TopicPilot development-process interview, 2026-09-25
**Scope:** Task definition, execution, interruption, validation, canonicalization, release
boundaries, documentation ownership, parallel work, and worktree lifecycle.

This file is the detailed source of truth for the approved process decisions. `AGENTS.md`
contains only the operational entry points and non-negotiable reminders; `PROJECT_CONTEXT.md` and
`docs/DOCUMENTATION_INDEX.md` route readers here. Do not create competing copies of these rules.

## 0. Process v2 effective scope and transition

The effective point for Process v2 is the timestamp when this policy is merged into
canonical `main`:

- Tasks created after that point must follow Process v2.
- A task already `ACTIVE` or `WAITING` at that point may continue under its original
  governance contract. It switches to Process v2 only at a natural boundary: resumption
  after a blocker, canonical promotion, release, or the start of a new implementation
  phase.
- A transition applies prospectively from that boundary. Do not reopen or rewrite a
  historical task solely to satisfy Process v2.
- The transition itself does not invalidate previously accepted evidence. Preserve and
  reuse it unless repository evidence shows that it is incorrect; independently apply
  the existing impact-based revalidation rule when a relevant SHA, environment,
  configuration, dependency, fixture, or authority boundary has changed. Such
  revalidation assesses evidence for the changed scope; it does not erase or invalidate
  the previously accepted evidence for its original scope.

At transition, keep the existing task identity and record that its remaining work now
uses Process v2. Do not retroactively change the task's earlier status or evidence.

## 1. Declare the task outcome before work starts

Every new task in Process v2, and every existing task that transitions to Process v2,
declares its type and required terminal state at the beginning of its applicable work
phase, before implementation or research begins:

```text
TASK_TYPE=<research | analysis | documentation | implementation | release>
REQUIRED_TERMINAL_STATE=<VALIDATED | CANONICALIZED | POST_DEPLOY_VERIFIED>
```

The task record also captures its scope and authority boundary. Use the start manifest
below; use `N/A` or `UNKNOWN` where a field does not apply or cannot yet be verified.
Volatile facts must include their verification time and system of record.

```text
TASK_ID=
TASK_TYPE=
REQUIRED_TERMINAL_STATE=
AUTHORITY_BOUNDARY=
CANONICAL_SHA=
SOURCE_SHA=
MIGRATION_HEAD=
FILES_CHANGED=
SEMANTICS_CHANGED=
PRODUCTION_DEPENDENCY=
FOLLOW_UP_REQUIRED=
WORKTREE_STATUS=
```

The required terminal state is task-specific. The task is complete only when its
achieved terminal state equals the state it declared at the start.

## 2. Preserve the lifecycle; select the terminal state by task type

The shared lifecycle remains:

`IMPLEMENTED` → `VALIDATED` → `CANONICALIZED` → `RELEASE_CANDIDATE` → `PRODUCTION_RELEASED` → `POST_DEPLOY_VERIFIED`

A task need not pass through all six stages. Choose its required terminal state as
follows:

| Task type | Required terminal state |
|---|---|
| Research, archaeology, analysis, or documentation with no canonical repository artifact | `VALIDATED` |
| Research/analysis that produces documentation intended for the canonical repository | `CANONICALIZED` |
| Deliverable application capability, backend, frontend, contract, or migration implementation | `CANONICALIZED` |
| Release candidate or feature whose requested outcome includes Production | `POST_DEPLOY_VERIFIED` |

A candidate intentionally waiting for Owner approval may end at `VALIDATED` or `CANONICALIZED`,
provided it reports `FOLLOW_UP_REQUIRED=YES`, names the next authority boundary, and does not claim the
higher state.

`COMMITTED` is an implementation/evidence checkpoint, not a terminal state. `PASS`,
`COMPLETE`, and passing tests are evidence only; none substitutes for the declared terminal
state. `BLOCKED` is not terminal success. A blocked task remains incomplete and normally
resumes as the same task when its blocker clears. Start a new task only when scope,
authority boundary, or implementation lineage has materially changed.

Abandon a task only on explicit Owner cancellation or objective evidence that its goal
is obsolete or superseded. A blocker, age, repeated pause, or status label alone is not
grounds for abandonment. Abandonment is not success: report `TASK_COMPLETE=NO`.

## 3. Keep one bounded outcome per persistent task

A task owns one bounded outcome/workstream. Phases that contribute to that outcome stay
in the same task. Split work only for an independent deliverable, a separate authority
boundary, or a material change in scope or implementation lineage. Record dependencies
and write sets so parallel work cannot silently claim shared ownership.

## 4. Bind validation and promotion to exact evidence

Validation evidence is bound to the code SHA and the environment, dependencies,
configuration, and fixtures used. Evidence may be reused only when those conditions and
the relevant authority boundary are unchanged. A change in SHA, environment,
configuration, dependency set, fixture, or boundary requires impact-based revalidation.
Every deployment requires runtime readback of the deployed revision.

When a validated task has a canonical repository target, proceed to canonical promotion
in the same task by default. Stop short only for a specific blocker, unresolved
authority, collision, or dependency; record the reason and next authority boundary. A
local commit alone does not satisfy `CANONICALIZED`.

Migration integration uses a serial lane: first reconcile against canonical `main` and
the latest verified Production migration revision; then finalize the migration on the
latest canonical head. CI rejects duplicate revision identifiers, unresolved or
abbreviated revision references, and graphs with anything other than one head; the
database smoke gate also exercises upgrade and rollback/downgrade. Do not create a
parallel registry as a substitute. Production migration or data mutation still needs its
separate explicit authorization.

## 5. Keep release authority explicit and narrow

An Owner authorization for one exact SHA may cover canonical promotion plus deployment
to the specifically named services and environment, followed by runtime readback, only
when the release has no database/data migration, scheduler or writer activation, or
additional configuration/secrets change.

If the SHA, requested scope, or canonical mainline changes, stop and obtain renewed
authorization. Database/data mutation, migration execution, scheduler/writer activation,
and unlisted services or environments remain separate authority boundaries. A release
authorization does not imply authorization for these excluded actions.

## 6. Maintain a truthful user-visible delivery lane

Keep at least one safe, truthful user-visible delivery lane represented in the roadmap.
It may pause for an explicit release-critical, data, or authority blocker only when the
blocker and recovery trigger are recorded. Do not invent product semantics, weaken
evidence, or bypass a gate to preserve apparent momentum.

## 7. Use one roadmap and documentation hierarchy

The product hierarchy is `A/B/C` with `A1–C3` subareas; execution priorities are
`P0–P5`. Do not introduce `R1–R5` as a parallel priority system. Lifecycle states are
cross-cutting and are not a replacement for this hierarchy.

- `docs/ROADMAP.md` is the sole source for execution status, dependencies, and priority.
- `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md` owns durable product outcomes and product-level deferrals.
- `PROJECT_CONTEXT.md` is the startup/navigation entry point.
- `docs/WORK_ORDERS.md` owns task-level scope and work-order detail.
- Track and M1/M2 labels may be used as references, not as competing status or priority
  authorities.

Link to the owner instead of duplicating status or rules.

## 8. Classify parallel work before dispatch

Every concurrent work item uses one of these classes:

- `SAFE_PARALLEL` — disjoint write sets, contracts, and resources; no shared mutable dependency.
- `SHARED_CANONICAL_DEPENDENCY` — tasks touch a shared canonical provider, contract, authority document, or
  integration point; assign ownership and sequence integration.
- `SHARED_MIGRATION_DEPENDENCY` — tasks affect the same migration lineage or head; serialize migration
  authoring and integration.
- `SHARED_FRONTEND_DEPENDENCY` — tasks share UI components, routes, client contracts, or interaction state;
  assign an owner and coordinate changes.
- `PRODUCTION_SERIAL_ONLY` — any work that changes Production state or performs an authorized deployment;
  execute serially within the named authorization envelope.

Apply the most restrictive class among the task's dependencies. Shared canonical,
migration, or frontend dependencies require explicit sequencing/ownership around the
shared surface. Production-only work is serial. Parallel status never grants authority
to change another task's semantics, write set, or release boundary.

## 9. Preflight Owner interruptions with evidence

When an Owner interruption requires a decision, first check current facts in the
canonical repository and the relevant system of record. Present:

```text
DECISION_TYPE=
FACTS_CHECKED=
WHY_NOT_INFERABLE=
```

Ask only about unresolved product semantics, authority, or Production authorization. Do
not ask the Owner to restate facts already established by current authoritative
evidence.

## 10. Track task and worktree state separately

Use these worktree classifications:

| State | Meaning and default handling |
|---|---|
| `ACTIVE` | Task is executing; retain its worktree. |
| `WAITING` | Same task is waiting on a named dependency or authority; retain it and record the recovery trigger. |
| `COMPLETE` | The task reached its declared terminal state and its closure/evidence is durable. This does not itself delete the worktree. |
| `ARCHIVE` | Organizes task history; it neither means success nor determines worktree retention/deletion. |
| `EVIDENCE_ONLY` | Temporary retention while unique evidence is not yet durably preserved elsewhere; name the evidence and its durable destination. |
| `CLEANUP_ELIGIBLE` | Exact-target checks passed and no preservation reason remains; remove through an explicit cleanup step or bounded cleanup pass. |

At creation and resumption, record the exact worktree path, branch, HEAD, base, and
dirty state. This is task-local hygiene; it does not require a globally clean workspace.
Before removal, recheck and record those same facts plus task ownership of changes,
unique patches, canonical presence of code/evidence, and active dependencies. Preserve
unrelated or unattributed Owner state. Do not automatically delete a worktree on commit,
promotion, task completion, or archive. Do not retain completed worktrees indefinitely
by default: once eligible, route them through cleanup. Never use blanket cleanup, reset,
or stash operations.

## 11. Required closure and compact manifest

Every task closure reports:

```text
TASK_TYPE=
REQUIRED_TERMINAL_STATE=
ACHIEVED_TERMINAL_STATE=
TASK_COMPLETE=YES/NO
FOLLOW_UP_REQUIRED=YES/NO
FOLLOW_UP_REASON=
```

It also carries the compact provenance manifest:

```text
TASK_ID=
CANONICAL_SHA=
SOURCE_SHA=
MIGRATION_HEAD=
FILES_CHANGED=
SEMANTICS_CHANGED=
PRODUCTION_DEPENDENCY=
FOLLOW_UP_REQUIRED=
WORKTREE_STATUS=
```

Use `N/A` or `UNKNOWN` rather than guessing. Volatile values include the verification
time and source of truth. Set `TASK_COMPLETE=YES` only when `ACHIEVED_TERMINAL_STATE` equals `REQUIRED_TERMINAL_STATE`. If incomplete or
waiting at an approved authority boundary, say why, name the next boundary, and set
`FOLLOW_UP_REQUIRED=YES`. Never report `BLOCKED` as an achieved terminal state.
