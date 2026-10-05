# TopicPilot Daily Formal Publication Orchestration

## Implementation handoff

| Field | Value |
|---|---|
| Task | `TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-IMPLEMENTATION-001` |
| Repository | `Xiezhou0828/topicpilot-platform` |
| Canonical source base for implementation | `8894138fc930b4512541cacd5214162cd66b4c8f` |
| Forensic baseline ancestor | `a687c748e1b7d512449b69884626c58ac7d86d12` |
| Candidate implementation commit | `9a97feb98ff6405874747030412b93bc5df519e9` |
| Canonical branch | `main` source baseline; local candidate branch retained, not pushed |
| Migration head | `0049_task_daily_formal_publication_receipt` |
| Timezone | `Asia/Taipei` |
| Date | `2026-10-05` |

## Terminal decision

The implementation is activation-ready in code and repository state. Production activation is deliberately not performed.

```text
TASK_STATUS=COMPLETE_ACTIVATION_READY
TASK_TYPE=IMPLEMENTATION
REQUIRED_TERMINAL_STATE=ACTIVATION_READY
ACHIEVED_TERMINAL_STATE=ACTIVATION_READY
TASK_COMPLETE=true
FOLLOW_UP_REQUIRED=true
FOLLOW_UP_REASON=Separate owner-authorized Production migration, scheduler provisioning, release, runtime readback, and Sites promotion remain outside this task.
```

## Frozen daily contract

- Earliest post-close eligibility: `13:45` Asia/Taipei.
- Soft target: `14:30` Asia/Taipei.
- Hard deadline: `15:00` Asia/Taipei.
- Trigger: `DATA_READY`; the scheduler supplies wake-up timing only.
- Canonical calendar: database reference bundle `TW_MARKET` / `G2`; scheduler clock is not business authority.
- A successful `MARKET_CLOSED` decision is a silent no-op and creates no formal publication.
- Successful daily publication is silent. Soft-target misses are warnings; hard-deadline, integrity, provenance, conflict, and correction failures are actionable critical events.

## Implemented authorities and persistence

`DailyFormalPublicationReceipt` is an additive table at migration `0049`. It stores the market-local date, calendar/reference identity, execution key and generation, immutable revision/hash, source run, phase states, reconciliation state, formal Topic/Strength/Lifecycle/Home readback, correction lineage, operational events, runtime provenance, and formal identifiers.

Receipt writes are idempotent by `(execution_key, receipt_hash)`, corrections are appended rather than overwritten, and the PostgreSQL trigger rejects `UPDATE` and `DELETE`. The operator readback surface is read-only:

- `GET /api/v1/operations/live/publication-receipt`
- `GET /api/v1/operations/live/publication-receipts`

The existing `GET /api/v1/meta/data-status` contract was not changed; it remains the legacy imported-bundle status plane.

## Publication semantics

- Absolute Strength, Relative Strength, and Grade are represented through the formal Strength publication/readback state.
- Lifecycle is represented through the formal Lifecycle publication/readback state and retains fail-closed history behavior.
- Home is permitted only for current-day normal publication; correction/history replay records `homeReplayed=false` and `home_state=FORBIDDEN`.
- `DailyFormalCorrectionReplayer` performs bounded, explicit, path-dependent Lifecycle replay from `earliest_affected_date` through the requested end date and appends a `CORRECTION_COMPLETE` or `CORRECTION_FAILED` receipt that points to the superseded authority.
- Normal scheduler retries stop for terminal `DEADLINE_EXCEEDED` and `FAILED_CLOSED` receipts; an incomplete data state remains distinguishable from a completed publication.

## Runtime provenance

The receipt records independent API, Worker, migration, and Web provenance. API and Web values are read from explicit runtime environment markers; Worker uses the existing Render/GIT SHA readback; migration is read from `public.alembic_version`. Unknown values are `UNKNOWN`/`UNVERIFIED`; `unknownIsVerified=false`, and no unknown value is promoted to `VERIFIED`.

## Software-release separation

```text
DAILY_DATA_PUBLICATION_SEPARATE_FROM_SOFTWARE_RELEASE=TRUE
```

No release workflow, Web artifact promotion, or Sites publish was triggered by this implementation. Daily publication readiness and software release readiness remain separate state machines.

## Validation evidence

- Focused receipt/scheduler/post-close/forward tests: `27 passed in 4.34s`.
- Focused plus architecture-freeze tests after schema allowlist updates: `32 passed in 8.69s`.
- Ruff targeted check: `All checks passed`.
- Python 3.12 compile check: passed.
- `py -3.12 -m alembic heads`: `0049_task_daily_formal_publication_receipt (head)`.
- Offline Alembic SQL generation emitted the receipt table, indexes, constraints, and append-only trigger; no database was contacted.
- Full repository backend run from the correct repository-root import context: `1342 passed, 79 skipped, 7 failed in 501.06s`. Two failures were stale freeze assertions for the newly required migration/table and are covered after the explicit test updates by the 32-test validation above. Five failures were 30-second cold-interpreter worker-boundary timeouts, including an unrelated market-data import case; no receipt/orchestration assertion failed.
- Baseline evidence from the forensic task: `151 passed in 8.28s` on canonical source `a687c748e1b7d512449b69884626c58ac7d86d12`. Candidate implementation validation is bounded by the focused/architecture result above; no Production database was used.
- Task-scope regression status: focused and architecture checks are regression-free; the five bounded cold-import timeout cases remain an environment/test-boundary limitation and are not treated as Production evidence.

## Production boundary

```text
PRODUCTION_ACTIVATION_READINESS=OWNER_AUTHORIZATION_REQUIRED
PRODUCTION_SCHEDULER_ACTIVE=NO
SCHEDULER_ACTIVATED=NO
PRODUCTION_MUTATION=NOT_AUTHORIZED_NOT_EXECUTED
PRODUCTION_MIGRATION=NOT_AUTHORIZED_NOT_EXECUTED
DEPLOY=NOT_AUTHORIZED_NOT_EXECUTED
SITES_PUBLISH=NOT_AUTHORIZED_NOT_EXECUTED
SOFTWARE_RELEASE_TRIGGERED=NO
```

Remaining activation gaps are external-state gaps: apply migration `0049` in the authorized environment, provision/authorize the scheduler, deploy the exact candidate, perform API/Worker/migration/Web runtime readback, and verify the public Sites artifact. Those actions require separate owner authorization and are not implied by this code handoff.

## Process v2 closure manifest

```text
TASK_ID=TASK-DAILY-FORMAL-PUBLICATION-ORCHESTRATION-IMPLEMENTATION-001
CANONICAL_BASE=8894138fc930b4512541cacd5214162cd66b4c8f
FORENSIC_BASE=a687c748e1b7d512449b69884626c58ac7d86d12
IMPLEMENTATION_HEAD=9a97feb98ff6405874747030412b93bc5df519e9
MIGRATION_HEAD=0049_task_daily_formal_publication_receipt
FILES_CHANGED=14 implementation paths plus 1 handoff report; prior forensic report preserved as a separate commit
SEMANTICS_CHANGED=daily timing phases, terminal receipts, formal readback, correction supersession, bounded Lifecycle replay, operator receipt API
PRODUCTION_DEPENDENCY=authorized migration, scheduler provisioning, deploy, runtime provenance, Sites promotion
WORKTREE_STATUS=task-owned paths clean; preserved unrelated untracked apps/web/public/__preview.json
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RELEASED
PRODUCTION_VERIFICATION=NOT_EXECUTED
PUSH_REMOTE=NO
DEPLOY=NO
NEXT_TASK=UNCHANGED
COMMITS=695d479,9a97feb,dc4b90d,acb1f1f,d521e99
```

```text
OWNER_AUTHORIZATION_REQUIRED_NEXT=YES
DAILY_FORMAL_PUBLICATION_IMPLEMENTATION_READY=YES
PRODUCTION_ACTIVATION_REQUIRES_SEPARATE_OWNER_AUTHORIZATION=YES
```
