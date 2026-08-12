# OPS-023A-P1B | Combined Release → Primary Working Tree Integration

**Date:** 2026-08-12
**Scope:** primary working-tree reconciliation and repository validation only
**Production operations:** prohibited and not performed

## Result

The verified P1 Combined Release is now integrated into the formal primary
working tree at `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
The primary Alembic command was executed in `services/api` using the operator's
PythonCore 3.12 command and returns exactly one head:

```text
0027_task_be_021_topic_lifecycle_results (head)
```

The primary migration history is linear through DATA-022, DATA-022A, and
BE-021. No primary user changes were reset, discarded, overwritten, or deleted.

## Fixed status report

```text
P1_RELEASE_LOCATION = C:\Users\acer\Documents\Codex\2026-08-12\referenced-chatgpt-conversation-this-is-an-7\work\TopicPilot-task-data-022
                        branch=task-data-022
                        commit=49ac18591b67cb67902feab23bf86eb05bc014a2
PRIMARY_WORKING_TREE_AUDITED = YES
PRIMARY_UNCOMMITTED_WORK_PRESERVED = YES
COMBINED_RELEASE_INTEGRATED_TO_PRIMARY = PASS
PRIMARY_ALEMBIC_HEADS = 1
PRIMARY_ALEMBIC_HEAD = 0027_task_be_021_topic_lifecycle_results
PRIMARY_MIGRATION_LINEAGE = PASS
DUPLICATE_REVISION_IDS = 0
DATA_022_PRIMARY = PASS
DATA_022A_PRIMARY = PASS
BE_021_PRIMARY = PASS
BE_021A_PRIMARY = PASS
PRIMARY_TESTS = PASS
PRODUCTION_NEON_WRITE = NO
PRODUCTION_MIGRATION = NOT_RUN
PRODUCTION_REVISION = 0024_task_be_007_topic_snapshots
READY_FOR_PHASE_2_PRODUCTION_MIGRATION = YES
NEXT_TASK_MODIFIED = NO
```

`PRODUCTION_REVISION=0024_task_be_007_topic_snapshots` is only the operator's
provided readback. The earlier operator `alembic upgrade head` no-op is not
treated as a migration result, and no production verification/write was
repeated by this task.

## Audit evidence

### Primary working tree

- Path: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
- Branch: `main`
- HEAD before integration: `547cc89` (`Document Stock Explorer push panel refinement`)
- Existing state: extensive modified and untracked user work, including frontend,
  architecture, reports, `.venv-live`, and work artifacts.
- Divergence from common base `57dcd49`: primary `main` has two local commits
  (`ac02d16`, `547cc89`); the separate P1 worktree has its transfer commit
  `49ac185`. The P1 commit was reconciled file-by-file rather than merged over
  the dirty primary branch.
- Preservation: no force reset, destructive checkout, deletion, or history
  rewrite was used. P1 files were added/reconciled as additional local changes.

### P1 source working tree

- Path: `C:\Users\acer\Documents\Codex\2026-08-12\referenced-chatgpt-conversation-this-is-an-7\work\TopicPilot-task-data-022`
- Branch: `task-data-022`
- Source commit created for safe transfer: `49ac18591b67cb67902feab23bf86eb05bc014a2`
- Source commit contains the previously validated DATA-022/022A + BE-021/BE-021A
  implementation, migrations, tests, frontend contract, and documentation.

## Integrated release inventory

The primary now contains all of the following P1 release components:

- DATA-022 Daily Market implementation and official TPE/TWO canonical source
  contract;
- DATA-022A no-trade/trading-status coverage, null semantics, and status-aware
  projection;
- additive migrations `0025`, `0026`, and `0027`;
- post-close audit, retry, coverage, reconciliation, and topic snapshot gate;
- BE-021 Lifecycle engine/state machine, explainability, shadow persistence, and
  backend-owned API contract;
- BE-021A calibration/replay CLI and deterministic tests;
- frontend Topic List/Detail Lifecycle contract integration and generated API
  types;
- migration, daily-market, no-trade, snapshot, Lifecycle, calibration, API, and
  architecture tests;
- DATA, Lifecycle, OPS-023, and combined release reports plus architecture,
  deployment, and work-order updates.

## Migration verification in primary

Executed from the primary `services/api` directory:

```text
pymanager exec -V:PythonCore/3.12 -m alembic heads
0027_task_be_021_topic_lifecycle_results (head)
```

History confirms:

```text
0024_task_be_007_topic_snapshots
  -> 0025_task_data_022_daily_market_contract
  -> 0026_task_data_022a_no_trade_coverage
  -> 0027_task_be_021_topic_lifecycle_results (head)
```

Revision ID audit reports `DUPLICATE_REVISION_IDS=0`. Offline SQL generation to
0027 passed and included the additive Lifecycle-results table without destructive
table drops or identity/bootstrap operations.

## Validation in primary

| Validation | Result |
|---|---|
| Combined daily/no-trade/snapshot/Lifecycle targeted backend suite | **53 passed, 1 skipped** |
| API-focused suite | **17 passed, 5 skipped** (PostgreSQL URL absent) |
| Schema boundary/API integration tests | **PASS** |
| Targeted Ruff for all changed DATA/Lifecycle implementation and tests | **PASS** |
| Python compile validation | **PASS** |
| Frontend Lifecycle integration tests | **2 passed** |
| Frontend production build | **PASS** |
| `git diff --check` | **PASS** |

The one combined-suite skip and five API-suite skips are database-backed tests
that require an explicit `TEST_DATABASE_URL` or `DATABASE_URL`; no production
URL was used or requested.

## Production boundary

Not performed:

- Production Neon `alembic upgrade` or any database write;
- production canary or 507-instrument run;
- production topic snapshot or Lifecycle shadow evaluation;
- Render deployment, scheduler activation, or secret changes;
- identity/bootstrap/destructive operation.

The primary repository is ready for the operator's Phase 2 protected migration,
but this report does not authorize or execute that operation.

## Final acceptance

| Acceptance | Result |
|---|---|
| Primary audit completed | PASS |
| P1 location and source commit identified | PASS |
| Existing primary uncommitted work preserved | PASS |
| Combined release integrated into primary | PASS |
| Exactly one Alembic head | PASS |
| Head equals 0027 Lifecycle | PASS |
| 0024→0025→0026→0027 lineage | PASS |
| Duplicate revision IDs | 0 |
| Repository-side tests/build/compile | PASS |
| Production migration/write | NOT RUN |
| Ready for Phase 2 operator migration | YES |
| NEXT_TASK modified | NO |

## Suggested NEXT_TASK

`TASK-OPS-023A-P2 | Protected Production Migration, 507-Instrument Canary,
Scheduler and Lifecycle Shadow Handoff`

This suggestion is report-only. The authoritative `NEXT_TASK` was not modified.
