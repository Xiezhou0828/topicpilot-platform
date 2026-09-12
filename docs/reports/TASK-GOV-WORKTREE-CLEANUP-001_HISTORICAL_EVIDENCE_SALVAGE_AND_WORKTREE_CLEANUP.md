# TASK-GOV-WORKTREE-CLEANUP-001 | Historical Evidence Salvage and Worktree Cleanup

## Purpose and safety boundary

This report records the final historical-evidence audit, the minimum evidence
salvage plan, and the worktree cleanup boundary. The canonical baseline was
re-read after `git fetch origin`; no prior SHA was reused.

```text
ORIGIN_MAIN_AT_START = 3682962b530aa6cd5b23286a8469b6c5d9acee74
SALVAGE_BRANCH_BASE = 3682962b530aa6cd5b23286a8469b6c5d9acee74
CANONICAL_REPO = C:\Users\acer\Desktop\題材領航\topicpilot-platform
TOTAL_WORKTREES_BEFORE = 39
TEMPORARY_SALVAGE_WORKTREE = topicpilot-platform-task-gov-worktree-cleanup-20260814
CANONICAL_PREEXISTING_DIRTY_PRESERVED = YES
CANONICAL_PREEXISTING_DIRTY_AT_START = 4 tracked + 148 untracked
PRODUCTION_MUTATION = NO
DEPLOY = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
```

The canonical repository was not reset, cleaned, stashed, switched, or
otherwise modified during the audit. All salvage edits are isolated on the
cleanup branch based directly on the latest `origin/main`.

## Salvage decision counts

```text
SALVAGE_REQUIRED = 11 files
NOOP = 1 file
SUPERSEDED = 3 files
KEEP_FOR_FUTURE_004E = grouped branch-only implementation/report/test content
AI_WORKLOG_APPEND = NO
```

The 11 required files are formal historical reports only. The 008 closure was
added to the existing historical report as historical evidence; it does not
change current authority. Opportunity work salvages only the strategy
authority report. The branch-only Opportunity spec is superseded by the
canonical spec and was not copied over it. No full `AI_WORKLOG.md`,
screenshots, duplicate authority, or current-handoff file was moved.

## Evidence matrix

| SOURCE_WORKTREE | SOURCE_FILE | CANONICAL_EXISTS | EQUIVALENT / SUPERSEDED | ACTION | TARGET |
|---|---|---:|---|---|---|
| task-data-ref-001 | `docs/reports/TASK-DATA-REF-004_EXACT_SHA_PRODUCTION_DEPLOY_RUNTIME_REVERIFICATION_REFERENCE_BOOTSTRAP_DRY_RUN.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-001 | `docs/reports/TASK-DATA-REF-005A_PRODUCTION_MARKET_IDENTITY_CONFLICT_READ_ONLY_AUDIT.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-006b | `docs/reports/TASK-DATA-REF-006C-A_EXPLICIT_G2_RUN_DATE_AUTHORIZATION_AND_PREFLIGHT_RESUME.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-006b | `docs/reports/TASK-DATA-REF-006C_PRODUCTION_G2_OFFICIAL_PROVIDER_READ_ONLY_PREFLIGHT_EXECUTION.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-006b | `docs/reports/TASK-DATA-REF-006D_G2_MISSING_IDENTITY_AND_INSTRUMENT_LIFECYCLE_ROOT_CAUSE_AUDIT.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-006f | `docs/reports/TASK-DATA-REF-006F_DATE_EFFECTIVE_G2_INTEGRATION_RELEASE_AND_PRODUCTION_REPREFLIGHT.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-006h | `docs/reports/TASK-DATA-REF-007_CONTINUOUS_PRODUCTION_DATA_GATE_EXECUTION_WINDOW_G2_STOP.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-007 | `docs/reports/TASK-DATA-REF-007B_G2_PRODUCTION_REPREFLIGHT_STOP.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-007 | `docs/reports/TASK-DATA-REF-007C_G2_PRODUCTION_PASS_G3_AUTHORITY_STOP.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-008 | `docs/reports/TASK-DATA-REF-008_G3_MARKET_SEMANTICS_VALIDATION_CONTRACT_AND_EXECUTABLE_GATE.md` | YES | NO; current worktree has unique production closure append | SALVAGE_REQUIRED | existing canonical report path, historical append only |
| task-doc-opportunity-001 | `docs/reports/TASK-DOC-OPPORTUNITY-001_OPPORTUNITY_ENGINE_STRATEGY_AUTHORITY_REPORT.md` | NO | NO | SALVAGE_REQUIRED | same canonical report path |
| task-data-ref-009 | `docs/reports/TASK-DATA-REF-009_POST_CLOSE_CANARY_PERSISTENCE_AND_END_TO_END_DATA_PUBLICATION_VALIDATION.md` | YES | YES after normalized comparison | SUPERSEDED / NOOP | none |
| task-data-ref-009 | `docs/reports/TASK-DATA-REF-009A_RUNTIME_ACTIVE_REFERENCE_BINDING_FIX_AND_SINGLE_POST_CLOSE_CANARY_RETRY.md` | YES | YES after normalized comparison; only terminal blank-line difference | SUPERSEDED / NOOP | none |
| task-doc-opportunity-001 | `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md` | YES | YES; canonical already contains the consolidation | SUPERSEDED | none; canonical not overwritten |
| task-today-004d | `docs/reports/TASK-FE-BE-TODAY-004D_MARKET_EVENTS_FORMAL_WIRING.md` | YES | YES exact content/hash | NOOP | none |
| task-today-004d | 004E report, Today market-overview implementation, and overview test | NO | Unique branch-only future content | KEEP_FOR_FUTURE_004E | source worktree retained |
| 006h / 007 / 008 / 009 | dirty `docs/AI_WORKLOG.md` additions | YES | Evidence is represented in the corresponding reports; no unique unrepresented evidence found | NOOP | none; no full log moved |

## Implementation and special-worktree findings

### 009

The latest canonical main contains the 009/009A implementation surfaces
including date-effective universe, market-semantics, post-close, and related
tests. The 009 and 009A report content is canonical-equivalent. After the
salvage commit and required checks, the 009 worktree is eligible for
`READY_FOR_DELETE`.

### Today-004D

The 004D report and event-wiring implementation/test are canonical-complete.
The same source worktree also contains branch-only 004E market-overview
implementation, report, and test content. It is explicitly retained as
`KEEP_FOR_FUTURE_004E`; it is not deleted and no 004E content is merged by
this cleanup task.

### VENV_003B

`C:\Users\acer\Desktop\題材領航\topicpilot-api-venv-003b-20260813` is
not a registered Git worktree. Its top-level Git root resolves to
`C:\Users\acer\Desktop\題材領航`, and it contains only virtual-environment
shape (`Include`, `Lib`, `Scripts`, `pyvenv.cfg`) but its files are part
of the parent repository's broad dirty/untracked state. The parent status
enumerated 3,767 entries when inspected, including paths outside the venv.
Because the venv boundary cannot be independently removed without affecting
the dirty parent workspace, this item remains
`NEEDS_MANUAL_REVIEW`. No file was removed.

## Phase 2 boundary

The cleanup branch contains only the 11 listed historical reports, including
the historical 008 closure append, and this audit report. It does not change
`AGENTS.md`, `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`,
`docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`, or current authority indexes.
It does not append `AI_WORKLOG.md`.

Required pre-push checks:

```text
DOCUMENTATION_LINK_CHECK = required
DIFF_CHECK = required
SECRET_CHECK = required
PRODUCTION_GATES = not rerun
```

Phase 3 may begin only after the salvage commit is present in latest
canonical main through the protected non-force PR path and the required CI
checks pass.
