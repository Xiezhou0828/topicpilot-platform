# GOV-003 — TopicPilot Agentic Parallel Development Runtime

**Date:** 2026-09-14
**Execution branch:** `codex/gov-003-agentic-parallel-development-runtime-20260914`
**Execution worktree:** `E:\topicpilot-worktrees\gov-003-agentic-parallel-development-runtime-20260914`
**Repository evidence checkout:** `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
**Scope:** governance runtime only; no product feature, deployment, migration, push, merge, Production, or `NEXT_TASK` mutation

## A. Executive Conclusion

```yaml
GOV_003_RESULT: COMPLETE_SCOPED_IMPLEMENTATION
AGENTIC_GOVERNANCE_RUNTIME: READY_REPO_SIDE_CANDIDATE
CANONICAL_PROMOTION: PENDING_OWNER_REVIEW
PRODUCTION: UNTOUCHED
C_DRIVE: UNTOUCHED
PRODUCT_FEATURE_DEVELOPMENT: NONE
```

The repository-side runtime is implemented in three bounded layers: portable
skills/manifests/contracts, deterministic guards/tests/CI, and governance
navigation/reporting. The task manifest is now `READY_FOR_INTEGRATION`; that
means the candidate is complete for GOV-003 and awaits canonical reconciliation,
not that it is already promoted to the canonical owner checkout.

The two remaining capability gaps are explicit rather than hidden: actual
Copilot hook execution was not available in this local task, and GitHub branch
protection/merge-queue settings were not accessible or mutated. The portable
scripts and governance CI are the deterministic enforcement path until those
operator-controlled surfaces are configured.

## B. Recovered Project State

Repository/Git evidence, not chat history, was used as the authority:

| Item | Recovered state |
|---|---|
| Canonical remote baseline | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| Canonical owner checkout HEAD | `02d3086183d1c582bb6c66c4c316340ccce3fa97` |
| Canonical owner branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Development integration base | `a8357d46194f9669709f184949270e20a7a2546c` |
| Production API readback | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`, diverged Today convergence branch |
| Exact Production source/Web/Worker/protected DB | Not verified by current committed evidence |
| Candidate migration head | `0039_task_a9_b2_formal_correction_supersession` |
| Migration `0040_task_a10_recovery_checkpoint_observability` | Branch-only evidence; retained for separate reconciliation, not ported |
| Owner checkout at recovery | 1 tracked modification, 151 untracked entries, 0 staged; preserved read-only |
| Release state | `BLOCKED_OPERATOR_READBACK`; no release mutation performed |

Active workstream recovery remains:

- Today Signals: `PARTIAL / BRANCH_DIVERGED`; deterministic Signals history and
  generated artifacts require the separate canonical promotion task.
- A10/A9: `PARTIAL / BLOCKED`; POST_CLOSE, provider resilience, migration
  reservation, and operator readback remain separate boundaries.
- Topic/B2: `BLOCKED / STRUCTURAL_ROLE_AUTHORITY`; derived publication and
  Lifecycle remain fail-closed or deferred.
- Opportunity: bounded formal composition exists with fail-closed provider
  semantics, but formal authority/provider and Production publication remain
  absent.
- Release: `REL-002-OPERATOR-READBACK-001` remains independent and blocked on
  exact API/Web/Worker/DB readback.

## C. Existing Governance Audit

The pre-GOV-003 repository had `AGENTS.md`, existing architecture ADRs and
reports, `.github/workflows/ci.yml`, and `.github/workflows/deploy.yml`. It did
not have repository-native `.github/skills/topicpilot-*`, `.github/agents`,
`.github/hooks`, `scripts/governance`, task manifests, an ownership registry,
or a baseline-failure registry. `.github/copilot-instructions.md`,
`.github/instructions/`, `.agents/skills/`, and `CLAUDE.md` were absent.

Existing ADR/architecture authority was retained. GOV-003 adds navigation and
runtime contracts; it does not create a competing `docs/decisions/` hierarchy
or rewrite historical decisions.

## D. External Skill Audit

No third-party repository or executable code was imported. The audit recorded
the official GitHub patterns used for compatibility:

| Pattern | Source | Imported code | Decision |
|---|---|---:|---|
| Portable `SKILL.md` with frontmatter and progressive disclosure | [GitHub agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | No | Adapted into concise `topicpilot-*` skills |
| Repository custom-agent markdown/frontmatter | [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) | No | Adapted into bounded agents |
| Versioned repository hooks and pre-tool decisions | [Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference) | No | Added minimal config; portable guards remain authoritative |
| Merge-group CI trigger | [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | No | Added CI compatibility trigger; settings remain unconfigured |

Shell, network, package-install, credential, push, and destructive-git code
from external sources was not executed or vendored.

## E. Adopted External Patterns

The adapted patterns are: short skill entrypoints with repo-specific
authority routing; custom agents with explicit bounded responsibilities;
pre-tool safety as an additional guard rather than the only enforcement;
merge-group-compatible CI; and progressive disclosure from project memory to
task manifest to validation/handoff. TopicPilot-specific ownership, C-drive
protection, migration fail-closed rules, baseline attribution, and authority
boundaries were implemented locally.

## F. Project Memory Skill

`.github/skills/topicpilot-project-memory/SKILL.md` requires recovery of
canonical state, active work, incomplete work, branch/worktree matrices,
roadmap/work orders/reports, Git history, and task manifests before mutation.
Its recovery fields include task ID, canonical/development bases, Production
baseline, migration head, active workstreams, previous tasks, last known good
implementation, partial/blocked/superseded work, baseline failures, owned and
shared surfaces, dependencies, owner decisions, and recommended base.

## G. Task Lifecycle Skill

`.github/skills/topicpilot-task-lifecycle/SKILL.md` and
`docs/governance/task_lifecycle.json` define machine-readable statuses and
legal transitions. Source existence is not completion; tests passing is not
deployment; deployment acceptance is not post-deploy verification. The
`ABANDONED` state requires explicit disposition or supersession evidence.

The lifecycle deliberately uses `READY_FOR_INTEGRATION`, `INTEGRATED`,
`DEPLOYED`, `VERIFIED`, and `CLOSED` as distinct states. GOV-003 is
`READY_FOR_INTEGRATION`, while its scoped implementation result is complete.

## H. Parallel Worktree Skill

`.github/skills/topicpilot-parallel-worktree/SKILL.md` defines one governed
mutation task as one named branch in one isolated E: worktree. It checks drive,
expected path, branch, base ancestry, and dirty/staged policy. The canonical C:
owner checkout is evidence-only while dirty.

GOV-003 executed only in the named E: worktree and left the C: checkout
unchanged.

## I. Incomplete Work Audit Skill

`.github/skills/topicpilot-incomplete-work-audit/SKILL.md` and
`scripts/governance/audit_incomplete_work.py` detect and classify TODO, FIXME,
HACK, placeholder, fixture/synthetic/mock, legacy/deprecated, orphan, unwired,
and dead-code candidates. It reports but never deletes or automatically marks
an artifact abandoned. A scoped audit of `scripts/governance` found 18
candidates, including 5 fixture/synthetic, 6 incomplete, 2 legacy/deprecated,
3 orphan, and 2 placeholder candidates; these are runtime-audit findings, not
dispositions.

## J. Integration Gate Skill

`.github/skills/topicpilot-integration-gate/SKILL.md` and
`scripts/governance/check_integration_gate.py` require source implementation
commit, target base, ownership, shared-surface diff, migration lineage,
dependencies, baseline attribution, and owner decision state. The gate
returns `READY`, `BLOCKED`, or reconciliation requirements. It does not rewrite
a feature or silently resolve product/authority decisions.

The Today Signals reconciliation manifest dry-ran `READY` with safe commit
`e4d675453aa03c51bd1c4e198ee3b7cb6742657f`; injecting an unknown failure
returned `BLOCKED`.

## K. Release Gate Skill

`.github/skills/topicpilot-release-gate/SKILL.md` and
`scripts/governance/check_release_gate.py` compare candidate and Production
migrations and exact API/Web/Worker provenance. A newer Production migration
or divergent lineage fails closed; no downgrade or rollback is attempted.
Research, shadow, fixture, and synthetic data are not formal readiness.

The simulated `0039` candidate versus branch-evidenced `0040` Production
scenario returned `BLOCKED_MIGRATION`. This is a gate test, not a claim that
the protected Production DB has been read back as `0040`.

## L. Custom Agents

Five bounded agents were added under `.github/agents/`:

- `recovery.agent.md`: read-only branch/task archaeology and supersession
  recovery, with governance-document mutation only when authorized.
- `bounded-developer.agent.md`: manifest, memory, worktree, ownership, focused
  validation, and handoff before mutation.
- `integration.agent.md`: cross-workstream reconciliation, shared contracts,
  generated artifacts, migration lineage, and candidate validation; no new
  product semantics or deployment.
- `release-operator.agent.md`: exact SHA, migration, deployment, data, and
  post-deploy readback; no product development.
- `governance-auditor.agent.md`: manifest/registry consistency, stale work,
  missing handoff, and invalid lifecycle evidence.

## M. Hooks / Deterministic Guards

`.github/hooks/topicpilot-governance.json` is a minimal version-1 hook
configuration with session-start validation and pre-tool C-drive protection.
The configuration shape and local guard behavior were validated, but this task
environment did not provide the actual host Copilot hook runtime. Therefore:

```yaml
HOOK_RUNTIME: UNVERIFIED
HOOKS: PARTIAL
DETERMINISTIC_REPLACEMENT: scripts/governance + governance CI + unit tests
```

The guard rejected a mutation target under the C: owner path and allowed a
safe E: target during local readback.

## N. Task Manifest Schema

`docs/governance/TASK_MANIFEST_SCHEMA.yaml` defines required task identity,
status, role, workstream, base, branch/worktree, owned/shared/forbidden paths,
dependencies, implementation/governance commits, migration/Production scope,
owner decision, and next-state fields. The portable JSON-compatible YAML form
is validated with the standard library so the core contract does not depend on
an unpinned parser.

Current manifests cover GOV-003, Today Signals reconciliation and promotion,
A10/A9 recovery and post-close reconciliation, Topic recovery and B2
provenance/publication, Opportunity authority readiness, and REL-002 operator
readback. Historical tasks are not bulk-transcribed.

## O. Ownership Registry

`docs/governance/WORKSTREAM_OWNERSHIP.yaml` classifies bounded owned paths,
shared surfaces, and forbidden paths for GOVERNANCE, TODAY, A10_A9, TOPIC_B2,
OPPORTUNITY, RELEASE, and INTEGRATION. Shared schemas, migrations, OpenAPI,
generated clients, central governance documents, and formal publication are
`SHARED_REQUIRES_RECONCILIATION` or integration-owner-only.

The ownership guard supports glob semantics without broadening a workstream to
an entire application tree. An owned Today Home path passed; Today-on-A10,
Today-on-shared-schema, A10-on-Topic, and Topic-on-A10 cases failed.

## P. Baseline Failure Registry

`docs/governance/BASELINE_FAILURE_REGISTRY.yaml` records the known full-suite
failures with test identity, first observation, owner workstream, class,
evidence, blocked workstreams, recheck/expiry, and resolution. It uses
10 known baseline entries from the recovered governance state, with recheck
dates rather than a permanent waiver. A known failure attributed to another
workstream does not block an unrelated task; an unknown failure blocks
qualification.

## Q. Governance Authority Matrix

`docs/governance/GOVERNANCE_AUTHORITY_MATRIX.md` routes each question to one
canonical source: repository/Git evidence for history and identity, current
state and active-work registries for aggregate navigation, task manifests for
task status/branch/worktree/ownership/dependencies/commits, the baseline
registry for failure attribution, architecture/product decisions for semantic
authority, and operator readback for Production provenance. Chat history is
recovery context only.

## R. Central-document Conflict Reduction

The runtime makes per-task manifests and reports the normal write surface.
Central `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`, `docs/WORK_ORDERS.md`, and
`docs/DOCUMENTATION_INDEX.md` are aggregate/navigation surfaces and require
serial reconciliation. GOV-003 added only one bounded checkpoint/navigation
entry to each; future task execution should not rewrite them independently.

An aggregate-view generator was not introduced because changing existing
canonical documents into generated output would expand this bounded task. The
migration path is documented: current active tasks use manifests, new tasks
become mandatory-manifest tasks, and historical tasks migrate on demand.

## S. CI Integration

`.github/workflows/governance.yml` runs on pull requests, `merge_group`, and
pushes to `main`. It validates manifests/registries, runs governance self-test
and unit tests, produces an incomplete-work summary, and checks whitespace.
Existing backend/frontend CI remains in place; GOV-003 does not replace it.
`.github/workflows/ci.yml` received only the merge-group trigger needed for
future queue qualification.

## T. GitHub Capability / Plan Findings

Official documentation supports the repository paths and formats audited in
section D. The repository-side files are therefore compatible with the stated
GitHub patterns, but this task did not mutate account/repository settings.
Branch protection, required checks, rulesets, and merge queue state remain
operator-controlled and were not observable here.

```yaml
MERGE_QUEUE: NOT_CONFIGURED
BRANCH_PROTECTION: NOT_VERIFIED
REPOSITORY_SETTINGS_MUTATION: NO
REPLACEMENT: integration-candidate-branch + required governance/CI checks
```

## U. Three-Task Parallel Dry Run

The following manifests were validated without starting their product work:

| Task | Manifest status | Isolated start | Collision result |
|---|---|---:|---|
| `TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003` | `PLANNED` | YES | Owns bounded Today Home paths; shared schemas/OpenAPI/generated clients require reconciliation |
| `TASK-A10-POST-CLOSE-CHECKPOINT-RECONCILIATION-002` | `PLANNED` | YES | Owns Live/Post-Close paths; Topic, Today, migration, and shared publication surfaces are forbidden/shared |
| `TOPIC-B2-CANONICAL-ARTIFACT-PROVENANCE-AND-PUBLICATION-GATE-001` | `PLANNED` | YES | Owns bounded Topic/B2 authority paths; A10/Today paths and shared publication remain blocked/serial |

Collision matrix:

| Surface | Today | A10/A9 | Topic/B2 | Resolution |
|---|---|---|---|---|
| Bounded implementation paths | OWNED | OWNED | OWNED | Parallel allowed when path check passes |
| Shared schemas/models | SHARED | SHARED | SHARED | Integration owner only |
| OpenAPI/generated client | SHARED | SHARED | SHARED | One serial contract update plus drift check |
| Migration chain | FORBIDDEN | FORBIDDEN/RESERVED | FORBIDDEN | Separate migration task and lineage gate |
| Formal publication | SHARED/forbidden by manifest | SHARED/forbidden by manifest | SHARED | Authority and integration reconciliation |
| Governance central docs | SHARED | SHARED | SHARED | Per-task report/manifest first; serial navigation reconciliation |
| Production/scheduler | FORBIDDEN | FORBIDDEN | FORBIDDEN | Operator/release gate only |

Therefore the answer is **YES for safe isolated execution/readback**, and
**NO for independent canonical integration or Production qualification**. The
three tasks were not started by GOV-003.

## V. Validation

```text
GOVERNANCE_SELF_TEST: PASS
GOVERNANCE_UNIT_TESTS: 8 passed, 0 failed
COMPILEALL: PASS
OWNERSHIP_CORRECT_TODAY_PATH: PASS
OWNERSHIP_TODAY_ON_A10_PATH: FAIL as expected
OWNERSHIP_TODAY_ON_SHARED_SCHEMA: FAIL as expected
OWNERSHIP_A10_ON_TOPIC_PATH: FAIL as expected
OWNERSHIP_TOPIC_ON_A10_PATH: FAIL as expected
WORKTREE_GOV003: PASS
INTEGRATION_TODAY_RECONCILIATION: READY
INTEGRATION_UNKNOWN_FAILURE: BLOCKED as expected
RELEASE_NEWER_MIGRATION: BLOCKED_MIGRATION as expected
INCOMPLETE_WORK_SCOPED_AUDIT: PASS (18 candidates classified; no mutation)
```

Governance count record:

```yaml
TEST_COUNT_PRE: 0
TEST_COUNT_POST: 8
TEST_COUNT_DELTA: 8
TEST_COUNT_DELTA_REASON: new GOV-003 governance unit suite; no prior suite existed
PASSED: 8
FAILED: 0
SKIPPED: 0
XFAILED: 0
DESELECTED: 0
NEW_FAILURES: 0
NEW_RUFF_VIOLATIONS: 0
PRODUCT_TESTS: NOT_RUN_BY_SCOPE
```

The required product/backend/frontend validation suite was not run because
GOV-003 forbids product implementation and the changed surfaces are governance
only. Final checks also require `git diff --check` and conflict-marker scans;
no migration, Production, owner-checkout, or cross-workstream product diff is
part of this candidate.

## W. Files Changed

Commit 1 adds 25 files: seven `topicpilot-*` skills, routing instructions,
governance guide/audits/contracts, manifests, registries, and lifecycle data.
Commit 2 adds 21 files or bounded workflow changes: five agents, one hook,
governance CI, merge-group compatibility, deterministic governance scripts,
and eight unit tests. The final governance-doc commit contains the GOV-003
manifest state, four central navigation updates, and this report. No product,
schema, migration, generated-client, application, or Production file was
implemented.

## X. Commits

```text
4ecea21  governance: add task memory and ownership contracts
801a95b  governance: add deterministic guards and CI
<final governance-doc/report commit recorded in the task handoff>
```

The first two commits are implementation commits for the runtime. The final
commit is intentionally kept separate for governance navigation, task status,
and evidence report review.

## Y. Remaining Gaps

1. Owner review and canonical promotion from this E: candidate have not been
   performed; no merge or push was authorized.
2. Actual host Copilot hook execution is unverified; portable scripts and CI
   are the current enforcement path.
3. GitHub branch protection, required checks, rulesets, and merge queue are
   not configured or verified by this task.
4. `ACTIVE_WORK.md` and other aggregate state remain the pre-GOV-003 canonical
   recovery snapshot; they were not rewritten wholesale. The GOV-003 manifest
   and report are the detailed runtime evidence until reconciliation.
5. Production exact source/Web/Worker/protected DB provenance remains blocked;
   migration `0040` remains branch-only and was not integrated.
6. The 10 baseline failures remain open with registry recheck dates; they were
   classified, not waived or fixed.
7. The three future workstreams still require their own owner-approved task
   start and later serial canonical promotion.

## Z. Recommended Adoption Sequence

1. Owner reviews the E: candidate, its three commits, manifest, report, and
   dry-run evidence.
2. Run the canonical reconciliation/promotion of GOV-003 itself; do not copy
   the E: branch into C: by hand.
3. Adopt manifests for the currently active tasks and keep per-task reports as
   the primary handoff artifact.
4. Require manifests for new tasks; add central-document updates only through
   the integration/reconciliation owner.
5. Configure GitHub required checks/merge queue in a separate operator task if
   desired, then verify actual hook execution in the supported host.
6. Start at most one of the named A/B/C tasks at a time unless their owner
   explicitly approves the isolated parallel starts shown in section U.

## Fifteen Required Answers

1. **Yes, with a bounded caveat.** A new agent can recover project state,
   active tasks, dependencies, branch, worktree, and ownership from committed
   state plus manifests/registries; exact Production provenance remains an
   explicit unknown until operator readback.
2. **Yes.** `docs/governance/tasks/*.yaml` plus the schema and validator.
3. **Yes.** `docs/governance/WORKSTREAM_OWNERSHIP.yaml`.
4. **Yes.** The ownership guard rejects Today changes to A10-owned paths.
5. **Yes in the portable guard; host hook execution is partial.** The worktree
   guard rejects a mutation task under the protected C: path.
6. **Yes.** Lifecycle statuses distinguish implementation, ready for
   integration, integrated, deployed, verified, and closed.
7. **Yes.** The baseline registry attributes known failures by test, workstream,
   evidence, blocked lines, and expiry; unknown failures block qualification.
8. **Yes.** `integration.agent.md` plus the integration gate script.
9. **Yes.** `release-operator.agent.md` plus the release gate skill/script.
10. **Yes.** A candidate older than the compared Production migration returns
    `BLOCKED_MIGRATION` and never downgrades.
11. **Adopted patterns:** official portable skills, agent frontmatter, hooks,
    and merge-group CI. **Imported code:** none.
12. **Not fully available here.** Hook JSON is validated, but actual host hook
    execution is unverified; scripts, unit tests, and governance CI provide
    deterministic replacement enforcement.
13. **Not configured/verified.** Use an integration-candidate branch with
    required governance and existing CI checks as the replacement.
14. **YES for isolated, bounded starts; NO for independent integration.** The
    collision matrix is in section U; schemas, migrations, OpenAPI/generated
    clients, formal publication, central docs, and Production remain serial or
    forbidden.
15. **Yes for a named governed task, conditionally.** A short prompt can name
    the task and instruct the agent to obey its manifest. Human context is still
    required for Owner decisions, formal authority, ambiguous supersession,
    GitHub permissions/settings, and operator Production readback. The three
    tasks are not authorized to start merely because the runtime is ready.

## Final Status

```yaml
TASK: GOV-003
RESULT: COMPLETE
AGENTIC_GOVERNANCE_RUNTIME: READY
PROJECT_MEMORY_SKILL: READY
TASK_LIFECYCLE_SKILL: READY
PARALLEL_WORKTREE_SKILL: READY
INCOMPLETE_WORK_AUDIT_SKILL: READY
INTEGRATION_GATE_SKILL: READY
RELEASE_GATE_SKILL: READY
TASK_MANIFEST: READY
OWNERSHIP_GUARD: READY
WORKTREE_GUARD: READY
BASELINE_FAILURE_REGISTRY: READY
RECOVERY_AGENT: READY
BOUNDED_DEVELOPER_AGENT: READY
INTEGRATION_AGENT: READY
RELEASE_OPERATOR_AGENT: READY
GOVERNANCE_AUDITOR: READY
HOOKS: PARTIAL
CI_GOVERNANCE: READY
MERGE_QUEUE: NOT_CONFIGURED
THREE_PARALLEL_TASKS_SAFE: YES
OWNER_DECISION_REQUIRED: NO
IMPLEMENTATION_COMMITS:
  - 4ecea21
  - 801a95b
GOVERNANCE_COMMIT: FINAL_GOVERNANCE_DOC_REPORT_COMMIT
PRODUCTION: UNTOUCHED
C_DRIVE: UNTOUCHED
READY_TO_START_A_B_C: NO
RECOMMENDED_NEXT_STEP: Owner review and canonical promotion of the GOV-003 runtime; then separately start one named A/B/C task.
```

GOV-003 stops here. It does not start Today Signals promotion, A10/A9
post-close reconciliation, Topic/B2 provenance/publication, INT-001, or any
product workstream.
