# TASK-A10-POST-CLOSE-CHECKPOINT-RECONCILIATION-002

Date: 2026-09-29 (Asia/Taipei)

## Governance result

```yaml
TASK_ID: TASK-A10-POST-CLOSE-CHECKPOINT-RECONCILIATION-002
TASK_STATUS: COMPLETE_POST_CLOSE_CHECKPOINT_RECONCILED
CANONICAL_BASE_SHA: c3542a900d6c46e07bc4243804e9705475023316
CANDIDATE_SHA: 6433078c2da5e495fb5ab691b153b53025e159ca
WORKTREE: E:/TopicPilot/worktrees/a10-post-close-checkpoint-reconciliation-002
PRODUCTION_DB_MUTATED: NO
PRODUCTION_TRIGGER_EXECUTED: NO
DEPLOYED: NO
PUSHED: NO
MIGRATION_CREATED: NO
MIGRATION_APPLIED: NO
```

The implementation uses the existing migration-0040 checkpoint table. No
second checkpoint store, new business semantics, provider, score, grade,
lifecycle, structural-role, or B2 authority was introduced.

## A. Current POST_CLOSE execution map

```text
normal scheduler/CLI AUTO
  -> LiveScheduler.decide / decide_runtime_mode
  -> inclusive >= 13:35 Asia/Taipei and open reference calendar date
  -> DailyForwardRunner.run_once
  -> PostCloseUpdater.run_once
  -> date-effective reference preflight and exact TPE/TWO universe
  -> deterministic session/scope run claim
  -> SESSION_VALIDATION checkpoint
  -> INPUT_READINESS checkpoint
  -> FORMAL_MARKET_FACTS:<market>:<batch> checkpoints
  -> existing official historical ingestion + canonical daily projection
  -> A9_B2_FORMAL_PROCESSING checkpoint
  -> existing formal Topic Snapshot / lifecycle / Home writers
  -> authoritative formal readback
  -> FINAL_PUBLICATION checkpoint
  -> COMPLETION checkpoint
```

The explicit recovery CLI remains date-bound (`--recover --run-date`) and
uses the same `PostCloseUpdater` chain. Targeted symbol capture remains
non-promoting and does not run the full formal publication path.

## B. Checkpoint authority audit

| Concern | Current authority | Reconciled behavior |
|---|---|---|
| Run identity | `live_collector_runs` plus `metadata.executionKey` | UUID5 identity derived from reference version, calendar, session date, and scope; one run is reused on recovery |
| Phase state | `topicpilot.live_collector_checkpoints` | Existing migration-0040 append-only events; latest event per `run_id`/`batch_key` is authoritative |
| Process liveness | `LiveCollectorRun.heartbeat_at` | Existing heartbeat retained; stale bound derives from poll interval and provider timeout/retry budget |
| Durable instrument work | `live_collector_attempts` plus canonical observation writers | Completed market batches are skipped on resume; incomplete batches retry through existing ingestion idempotency |
| Formal publication | `topicpilot.topic_snapshots` and existing Home publication authority | Readback is required before terminal success; writers are not re-entered when the committed formal output already reads back valid |
| Transient scheduler state | in-process scheduler fields | Never treated as durable completion authority |

Existing run statuses are preserved. They map conceptually as:

| Existing status | Checkpoint meaning |
|---|---|
| `RUNNING` | active or resumable execution |
| `SUCCESS` | terminal only after formal readback and checkpoint agreement |
| `PARTIAL` | retryable/incomplete terminal result |
| `FAILED` | failed result; explicit recovery remains required for terminal rerun |
| `MARKET_CLOSED` | terminal non-session outcome; no fake publication is created |

## C. Failure, retry, and recovery matrix

| Scenario | Durable evidence | Result |
|---|---|---|
| Crash before first durable market batch | no completed market checkpoint | same deterministic run resumes from `FORMAL_MARKET_FACTS` |
| Crash after a completed batch | latest batch event is `COMPLETED` | batch is skipped; later batches resume |
| Crash after canonical write before batch checkpoint | latest batch event is `IN_PROGRESS` | batch is retried; existing canonical ingestion/idempotency handles replay |
| Provider/readiness failure | attempt error and batch `PARTIAL`/`FAILED` | existing provider retry policy applies; terminal rerun uses explicit recovery |
| Formal output committed, checkpoint not completed | phase is `IN_PROGRESS`, formal readback is `PASS` | readback wins; writers are not re-entered; phase converges to `COMPLETED` |
| Checkpoint says complete, formal output missing/invalid | phase is `COMPLETED`, readback is `FAIL` | fail closed with `CHECKPOINT_PUBLICATION_MISMATCH`; repair is attempted only through the existing recovery path |
| Worker restarts with fresh `RUNNING` heartbeat | active lease evidence | duplicate invocation is blocked |
| Worker restarts with stale `RUNNING` heartbeat | existing heartbeat plus derived bounded timeout | same run is claimed and resumed in place |
| Duplicate full/targeted first invocation | deterministic run IDs plus PostgreSQL transaction advisory lock | one session claim wins; competing claim blocks/fails closed |
| Invocation after terminal success | terminal run and formal readback | existing result is reused; no second formal publication |
| Weekend/configured closed date | `MarketSessionClock` and reference preflight | `WAIT`/`MARKET_CLOSED`; no provider or formal publication |
| Before 13:35 | shared scheduler/CLI boundary | `WAIT`; normal POST_CLOSE path is not entered |

The implementation uses “effectively once” for formal publication. It does
not claim distributed exactly-once execution.

## D. Formal publication/readback reconciliation

The completion gate now requires:

1. date-effective session and input preconditions are valid;
2. required market facts reconcile as downstream-ready;
3. formal Topic Snapshot rows are `FORMAL`, `PIT_FORMAL`, `TRADING`,
   `GENERATED`, `FINAL`, `PUBLISHED`, and not superseded;
4. the formal readback is readable and has distinct topic identities;
5. checkpoint and publication state agree.

Home publication readback is captured as diagnostic evidence using the
existing `home_publications` authority. A9/B2 processing remains behind its
existing formal gates; lifecycle remains the current authorized behavior.

## E. A10/A9 lineage report

```yaml
A10_TRIGGER: shared LiveScheduler/CLI boundary, inclusive >= 13:35 Asia/Taipei
A10_ENTRYPOINT: services/api/src/topicpilot_api/live/post_close.py:PostCloseUpdater.run_once
A10_CHECKPOINT: topicpilot.live_collector_checkpoints, migration 0040
A9_FORMAL_BOUNDARY: existing materialize_bounded_formal_dates and formal TopicSnapshot readback
B2_AUTHORITY: unchanged; no inferred role/leader authority
SCORE_GRADE_POLICY: unchanged
LIFECYCLE_POLICY: unchanged; existing current engine remains downstream behavior
```

The current mainline had reverted runtime defaults and CLI AUTO comparison to
13:30, so the frozen completed trigger contract was ported back to 13:35 as a
compatibility prerequisite. This does not introduce a new trigger rule.

## F. Test report

Executed with the repository-compatible Python 3.12 runtime:

```text
Focused live/checkpoint/trigger/architecture tests: 50 passed
Ruff on changed Python files: passed
Python 3.12 compile check for live/ORM packages: passed
git diff --check: passed
```

The broader backend suite completed with `802 passed, 59 skipped, 10
pre-existing failures`. The failures are confined to the existing corporate
action/reference-bundle mismatch. PostgreSQL tests were skipped because no
test database URL was configured. The architecture-freeze failure caused by
registering the existing checkpoint table was corrected by adding that table
to the explicit implemented-table allowlist; the corrected full-suite count
is therefore `803 passed, 59 skipped, 10 pre-existing failures`.

## G. Governance and final status

```yaml
POST_CLOSE_CANONICAL_ENTRY_IDENTIFIED: YES
CHECKPOINT_AUTHORITY_IDENTIFIED: YES
SESSION_IDENTITY_DETERMINISTIC: YES
DUPLICATE_INVOCATION_SAFE: YES
CRASH_RESUME_SAFE: YES
PUBLICATION_CHECKPOINT_RECONCILIATION: YES
FORMAL_READBACK_REQUIRED_BEFORE_COMPLETE: YES
BEFORE_1335_BLOCKED: YES
CLOSED_SESSION_BLOCKED: YES
A9_B2_BOUNDARY_PRESERVED: YES
NO_NEW_BUSINESS_SEMANTICS: YES
FOCUSED_TESTS: PASS
RUFF: PASS

POST_CLOSE_ENTRYPOINT: LiveScheduler/CLI -> DailyForwardRunner -> PostCloseUpdater.run_once
CHECKPOINT_AUTHORITY: topicpilot.live_collector_checkpoints (migration 0040)
SESSION_IDENTITY_AUTHORITY: ACTIVE_REFERENCE_PREFLIGHT + Asia/Taipei date-effective session
POST_CLOSE_PHASE_MODEL: SESSION_VALIDATION -> INPUT_READINESS -> FORMAL_MARKET_FACTS -> A9_B2_FORMAL_PROCESSING -> FINAL_PUBLICATION -> COMPLETION
RETRY_MODEL: existing RateLimitedTransport retries; explicit recovery for terminal PARTIAL/FAILED
STALE_RUNNING_MODEL: heartbeat plus existing derived provider/poll timeout bound; resume in place
CONCURRENCY_MODEL: deterministic run UUID, PostgreSQL session advisory transaction lock, row lock
DUPLICATE_INVOCATION_SAFE: YES
CRASH_RESUME_SAFE: YES
FORMAL_PUBLICATION_IDEMPOTENT: YES
CHECKPOINT_PUBLICATION_RECONCILIATION: YES
FORMAL_READBACK_GATE: YES
BEFORE_1335_BEHAVIOR: WAIT
CLOSED_SESSION_BEHAVIOR: WAIT / MARKET_CLOSED without publication
ALREADY_COMPLETED_BEHAVIOR: return existing result after readback-backed terminal state
A9_B2_INTEGRATION_STATUS: existing boundary preserved and readback-gated
A9_B2_SEMANTICS_CHANGED: NO
CHECKPOINT_SCHEMA_CHANGE_REQUIRED: NO
MIGRATION_CREATED: NO
MIGRATION_APPLIED: NO
FOCUSED_TEST_STATUS: PASS (50)
A10_TEST_STATUS: PASS
A9_B2_TEST_STATUS: PASS (boundary/readback injection coverage)
BROADER_TEST_STATUS: 803 passed / 59 skipped / 10 pre-existing failures
RUFF_STATUS: PASS
MIGRATION_HEAD_STATUS: repository head 0046; database head not queried/mutated
PRODUCTION_DB_MUTATED: NO
PRODUCTION_TRIGGER_EXECUTED: NO
DEPLOYED: NO
PUSHED: NO
PREEXISTING_FAILURES: corporate-action/reference-bundle version and lifecycle-date mismatch
OWNER_DECISIONS_REQUIRED: none for this bounded implementation; PostgreSQL integration remains required before release
KNOWN_LIMITATIONS: no live PostgreSQL failure-injection run was authorized/configured; effectively-once, not distributed exactly-once
ARTIFACTS: this report; ORM checkpoint mapping; runtime reconciliation; focused tests
NEXT_RECOMMENDED_TASK: PostgreSQL disposable integration validation and release review of A10/A9 formal readback
```
