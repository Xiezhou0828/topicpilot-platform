# TASK-A10-TODAY-POST-CLOSE-SEMANTIC-RECONCILIATION-003R

Date: 2026-09-29 (Asia/Taipei)

## Reconciliation scope

This report reconciles the latest canonical mainline Today official-source
publication behavior with the A10 post-close checkpoint/retry implementation.
It updates the existing PR #12 candidate; it does not merge, release, deploy,
activate a scheduler, or mutate a Production database.

```text
TASK_ID=TASK-A10-TODAY-POST-CLOSE-SEMANTIC-RECONCILIATION-003R
LATEST_CANONICAL_MAIN_SHA=ec46db023c8e701044e162dcf723f362002b88d7
PR_NUMBER=12
PR_BRANCH=codex/task-a10-post-close-checkpoint-canonical-promotion-003
PR_HEAD_BEFORE_RECONCILIATION=137cb46a283d5292a8cf8a4d536d033b2cdc321b
RECONCILED_CANDIDATE_SHA=8d831bb1ec7cdf3031350b2326b4b6a4ddca5e47
```

## Explicit semantic reconciliation

### Institutional-flow persistence

MAIN_BEHAVIOR: Today obtains official TWSE and TPEx exchange-level flow facts,
keeps same-date market composition, persists typed facts through the existing
upsert authority, and fails closed for unavailable provider rows.

A10_BEHAVIOR: A durable `FORMAL_MARKET_FACTS:OFFICIAL` checkpoint records the
flow publication attempt and its authoritative readback. A committed complete
readback is reused on retry; it is not written again for the same recovery
path.

CONFLICT: Main's official flow persistence was inside the shared finalization
path, while A10 needed a durable boundary before terminal completion and crash
recovery.

RECONCILED_BEHAVIOR: Official flow facts are persisted and committed before
A9/B2 processing. The checkpoint is completed only after readback confirms
both `TPE` and `TWO`, the target date, `AVAILABLE`, and the expected official
source identities. Partial or missing flow remains non-terminal.

WHY_BOTH_ARE_PRESERVED: The mainline source and whole-market rules remain the
input authority; A10 adds durable progress and recovery authority without a
second dedupe table or a second source.

### Home publication and formal Topic publication

MAIN_BEHAVIOR: Home V2 can publish independently sourced market facts when
stock-dependent downstream work is blocked; it uses its existing deterministic
publication identity and idempotent behavior.

A10_BEHAVIOR: Topic Snapshot and Home publication are read back before
terminal completion, and a prior checkpoint cannot by itself imply success.

CONFLICT: A market-facts-only Home publication must be retained for Today but
must not satisfy A9/B2 or the full post-close terminal gate.

RECONCILED_BEHAVIOR: The `downstream_ready` false path retains Home market
facts publication and returns a partial/blocked run. Formal Topic, Home
`PUBLISHED`, and complete institutional-flow readback are jointly required for
terminal SUCCESS.

### Execution ordering

The reconciled ordering is:

```text
SESSION_VALIDATION
  -> INPUT_READINESS
  -> official market-fact fetch
  -> official institutional-flow persistence/readback authority
  -> A9_B2_FORMAL_PROCESSING (when downstream_ready)
  -> Home V2 publication
  -> formal Topic/Home/flow readback
  -> FINAL_PUBLICATION checkpoint
  -> COMPLETION checkpoint
```

The market-facts-only branch omits A9/B2 by design, still publishes eligible
Today market facts, and remains non-terminal. A9/B2 business semantics and
formal PIT readback remain unchanged.

## Conflict matrix

| Concern | Reconciled authority and behavior |
|---|---|
| Institutional persistence | Existing official TWSE/TPEx fact table and upsert; committed before A9/B2; same-date whole-market only. |
| Home publication | Existing Home V2 materialization and deterministic identity; market-facts-only is preserved but non-terminal. |
| Formal Topic publication | Existing formal Topic snapshot/PIT authority; no market-facts-only promotion into Topic. |
| Terminal SUCCESS | Requires Topic PASS, Home `PUBLISHED`, and both official flow rows PASS; checkpoint alone is insufficient. |
| Checkpoint completion | Append-only A10 events; official flow checkpoint records IN_PROGRESS then COMPLETE/FAILED after readback. |
| Formal readback | Authoritative Topic, Home, and institutional-flow readback are combined; any mismatch fails closed. |
| Failure handling | Typed partial/failed status and failure code; no zero-fill, stale carry-forward, unofficial fallback, or single-market whole-market claim. |
| Rollback | Persistence errors roll back only the active uncommitted transaction; already committed outputs are reconciled by readback and are not erased. |
| Retry | Stale RUNNING and interrupted phases resume by deterministic run identity; completed outputs are reused/idempotent. |

## Recovery cases

```text
A flow committed, checkpoint missing       -> readback converges checkpoint; no duplicate flow write
B checkpoint ahead, flow missing            -> terminal gate fails closed; flow must be republished/read back
C flow committed, Home missing              -> flow is reused; Home is materialized; no terminal success until readback
D Home committed, final checkpoint stale    -> readback reuses Home and converges FINAL_PUBLICATION/COMPLETION
E duplicate after all publications          -> deterministic run/readback path; no second formal publication
F TWSE available, TPEx unavailable          -> partial institutional-flow readback; no whole-market success
```

## Verification

```text
FOCUSED_POST_CLOSE_HOME_FLOW=PASS; 43 passed
POST_CLOSE_CONTRACT=PASS; 27 passed
LIVE_A9_B2_DAILY_FLOW_SUITE=PASS; 88 passed
BROADER_BACKEND=805 passed / 4 skipped / 10 pre-existing failures
BROADER_FAILURE_CLASS=corporate-action reference-bundle version/effective-date mismatch; unchanged and out of scope
RUFF=PASS
COMPILEALL=PASS
ALEMBIC_GRAPH=PASS; 47 revisions / 1 head / 0046_task_stock_maint_relation_weight_authority_001d
NEW_MIGRATION=NO
PRODUCTION_DB_MUTATION=NO
DEPLOYED=NO
MERGED=NO
```

## Final status block

```text
TASK_STATUS=COMPLETE_SEMANTIC_RECONCILIATION_PR_READY
CANONICAL_BASE_USED=ec46db023c8e701044e162dcf723f362002b88d7
TODAY_OFFICIAL_SOURCE_BEHAVIOR_PRESERVED=YES
A10_CHECKPOINT_RETRY_IDEMPOTENCY_PRESERVED=YES
FORMAL_READBACK_TERMINAL_GATE=PASS_IN_CODE_AND_TESTS
WHOLE_MARKET_FLOW_REQUIRES_TWSE_AND_TPEX_SAME_DATE=YES
HOME_MARKET_FACTS_ONLY_PATH_PRESERVED=YES
BEFORE_1335_WAIT_PRESERVED=YES
CLOSED_SESSION_WAIT_OR_MARKET_CLOSED_PRESERVED=YES
A9_B2_SEMANTICS_CHANGED=NO
SCHEMA_OR_MIGRATION_REQUIRED=NO
PR_UPDATED=YES_PENDING_PUSH
CI_ELIGIBLE=YES_PENDING_PUSH
PR_MERGED=NO
RELEASED=NO
PRODUCTION_MUTATED=NO
BLOCKERS=NONE_FOR_PR_READINESS
```
