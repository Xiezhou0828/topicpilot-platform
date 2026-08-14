# TASK-GOV-CANONICAL-RECONCILIATION-001 — 009/009A Runtime and Evidence Consolidation

## Scope and authority

This report records the minimal reconciliation of the completed TASK-DATA-REF-009 and
TASK-DATA-REF-009A implementation/evidence into the canonical repository.

```text
CANONICAL_REPO = C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_BRANCH_AT_START = codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_HEAD_AT_START = 0ffbdb991c603e2d23f41f317a22fbfe0c550d7b
SOURCE_WORKTREE = C:\Users\acer\Desktop\題材領航\topicpilot-platform-task-data-ref-009-post-close-canary-20260814
SOURCE_BRANCH = codex/task-data-ref-009-post-close-canary-20260814
SOURCE_HEAD = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
ORIGIN_MAIN_AFTER_FETCH = 8402f141979e9924c9cfa8a1fc1b8e5b36f176ab
ORIGIN_MAIN_FETCH = COMPLETE
```

The remote `origin/main` value was fetched and re-read before reconciliation. It
remained `8402f141…` at audit time; it was not treated as an assumed historical
baseline. The canonical branch and `origin/main` are divergent from the shared
merge base, so unrelated mainline/Today/Stock work was not merged into this
consolidation.

## Provenance audit

The source branch is clean for application code and has only the following local
evidence edits:

```text
M  docs/AI_WORKLOG.md
M  docs/reports/TASK-DATA-REF-009_POST_CLOSE_CANARY_PERSISTENCE_AND_END_TO_END_DATA_PUBLICATION_VALIDATION.md
?? docs/reports/TASK-DATA-REF-009A_RUNTIME_ACTIVE_REFERENCE_BINDING_FIX_AND_SINGLE_POST_CLOSE_CANARY_RETRY.md
```

The relevant committed lineage is:

- `0ec5bcfe` — date-effective lifecycle eligibility and the reference lifecycle
  dependency required by the post-close/G2 context.
- `b9c881af` — read-only G3 market-semantics gate, CLI, tests, and report.
- `edfeb0e5` — date-effective post-close canary universe propagation, bounded
  persistence/reconciliation/snapshot filtering, tests, and TASK-DATA-REF-009 report.

The canonical worktree already contained unrelated dirty documentation and fixture
changes before this task. They were preserved and are not part of this report or
the reconciliation commit.

## Minimal reconciliation set

### Included runtime and schema dependency

- date-effective instrument lifecycle model, migration 0029, bundle lifecycle
  payload, bootstrap validation, and `instrument_universe.py`;
- read-only `provider_preflight.py` and its operator CLI;
- G3 `market_semantics.py` and CLI;
- official provider market-day fetch boundary used by read-only G2/G3 checks;
- TASK-DATA-REF-009 post-close changes in CLI, persistence, reconciliation,
  lifecycle, snapshot, and post-close runner;
- affected backend contract/PostgreSQL tests and reference-bundle regression
  updates;
- only the two required package entrypoints:
  `topicpilot-provider-preflight` and `topicpilot-market-semantics-check`.

### Included formal evidence

- TASK-DATA-REF-008 G3 report;
- TASK-DATA-REF-009 report, including its fail-closed precondition evidence;
- TASK-DATA-REF-009A report, including the single authorized Canary result and
  SELECT-only persistence/non-corruption postcheck;
- this canonical reconciliation report;
- an append-only canonical `docs/AI_WORKLOG.md` entry.

### Explicitly excluded

- Today/Stock worktrees and UI changes;
- unrelated 005/006 remediation tools and reports;
- Scheduler, NEXT_TASK, deploy configuration, Production mutation, and any
  second Canary;
- direct whole-worktree merge;
- G1/G2/G3/Canary re-execution. Existing Production gate evidence remains the
  named baseline `TASK-DATA-REF-009A`.

## Conflict classification

| Area | Canonical at start | Source/current evidence | Classification | Action |
|---|---|---|---|---|
| G3 market semantics | Missing | `market_semantics.py`, CLI, tests, 008 report | Missing current implementation | Included |
| Post-close date-effective universe | Older physical-universe path | 009 runtime diff and tests | Current implementation delta | Included |
| Persistence/reconciliation/snapshot filtering | Older unbounded active-universe path | 009 runtime diff and tests | Current implementation delta | Included |
| Reference lifecycle eligibility | Missing model/migration/universe helper | 006E dependency used by 009/G2 | Required runtime dependency | Included |
| 009 report | Missing | Source report plus local closure evidence | Formal evidence missing | Included |
| 009A report | Missing/untracked in source | Source local formal report | Formal evidence missing | Included |
| AI worklog | Canonical history stops before 008/009 | Source append-only entries | Evidence provenance missing | Append-only entry |
| Today/Stock/UI | Existing or separately dirty | Not part of source 009 runtime | Out of scope | Preserved/excluded |
| Production data / Scheduler | Unchanged | Existing evidence only | No requested mutation | No action |

## Change impact matrix

| Changed dependency | Runtime impact | Protected boundary | Validation decision |
|---|---|---|---|
| date-effective lifecycle/G2 context | Yes; selects eligible identities before post-close writes | G1/G2 reference/lifecycle boundary | Run focused unit/contract tests and CI checks; preserve 009A G1/G2 evidence |
| G3 market semantics read-only gate | Yes, read-only evaluator/CLI | G3 semantics boundary | Run focused G3 tests; do not run Production G3 |
| post-close eligibility propagation | Yes; filters writer, tracking, reconciliation, snapshots, lifecycle | Canary writer/persistence boundary | Run affected tests; preserve 009A Canary PASS because this is canonical consolidation of the already deployed SHA |
| reports/worklog only | No application runtime impact | None | Path/link/diff/secret-safe review only |
| Scheduler/deploy/Production data | No change | Canary/Scheduler boundary | Not run / not changed |

## Preserved Production baseline

```text
PRESERVED_GATE_BASELINE = TASK-DATA-REF-009A
APPLICATION_RELEASE_SHA = edfeb0e59c53ccf957d2b100a4f4ec619f67b519
G0 = PASS
G1 = PRESERVED PASS
G2 = PRESERVED PASS
G3 = PRESERVED PASS
CANARY = PASS
CANARY_REQUESTED = 506
CANARY_SUCCESS = 506
CANARY_FAILURE = 0
CANARY_RUN_ID = c697da38-c093-4362-b4f3-6caea4077119
DOWNSTREAM_READY = true
TPE = 313/313
TWO = 193/193
DUPLICATE_STABLE_KEY_GROUPS = 0
DAILY_TPE_6806_ROWS = 0
PRODUCTION_MUTATION_DURING_RECONCILIATION = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_CHANGED = NO
```

No protected gate was re-run. The reconciliation preserves the existing
Production evidence because the application behavior is being restored to the
canonical repository at the same already-verified runtime lineage; the new work
does not claim a new Production execution.

## Reconciliation execution

At this checkpoint the selected files have been applied to the canonical working
tree. Affected tests, diff review, exact-SHA commit/push, and CI verification are
recorded in the append-only closure section below after execution completes.

```text
FINAL_STATUS = PENDING_AFFECTED_VALIDATION_AND_CANONICAL_PUSH
BLOCKER = NONE
```

## Affected validation and push checkpoint

The canonical working tree passed the affected local validation boundary:

```text
FOCUSED_UNIT_AND_CONTRACT_TESTS = 44 passed
POSTGRES_TESTS = 5 skipped (no TEST_DATABASE_URL/DATABASE_URL in local shell)
RUFF = PASS
PYTHON_COMPILEALL = PASS
GIT_DIFF_CHECK = PASS
NON_FORCE_PUSH = YES
PUSHED_IMPLEMENTATION_COMMIT = 0457de8e199e57d0a01cc3634169079b1fb44456
PULL_REQUEST = https://github.com/Xiezhou0828/topicpilot-platform/pull/4
EXACT_SHA_CI = PENDING_GITHUB_RUN
```

This checkpoint is documentation-only after the implementation commit; it does
not change application runtime behavior or the preserved Production baseline.

## Canonical closure

The canonical branch was refreshed against the fetched latest `origin/main` by
an ordinary merge commit. Conflict resolution retained the current 009/009A
runtime/evidence and the latest base-branch Today/mainline and migration
contract files. No force update was used.

```text
RECONCILED_MAIN_SHA = ee3d5d1557addd71a79e6d8d39a7d5ed9c2dc9ec
ORIGIN_MAIN_USED = 8402f141979e9924c9cfa8a1fc1b8e5b36f176ab (freshly fetched)
NON_FORCE_PUSH = YES
PULL_REQUEST = https://github.com/Xiezhou0828/topicpilot-platform/pull/4
EXACT_SHA_CI_RUN = 31787341655
EXACT_SHA_CI_URL = https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/31787341655
EXACT_SHA_CI = PASS
BACKEND_MIGRATION_OPENAPI = PASS
FRONTEND_INSTALL_TEST_BUILD = PASS
SECRET_SCAN = PASS
DOCKER_COMPOSE_SMOKE = PASS
DEPLOY = NO
PRODUCTION_MUTATION = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_CHANGED = NO
PRESERVED_GATE_BASELINE = TASK-DATA-REF-009A
G0 = PRESERVED PASS
G1 = PRESERVED PASS
G2 = PRESERVED PASS
G3 = PRESERVED PASS
CANARY = PRESERVED PASS (506/506, failure=0)
FINAL_STATUS = 009_009A_CANONICAL_CONSOLIDATION_COMPLETE
BLOCKER = NONE
```

The exact-SHA CI result covers the reconciled application commit. The final
append-only documentation closure does not change application runtime code or
protected inputs.
