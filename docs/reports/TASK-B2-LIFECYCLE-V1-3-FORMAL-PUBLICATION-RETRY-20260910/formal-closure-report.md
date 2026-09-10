# B2 | Lifecycle V1.3 Formal Publication Retry — Fail-Closed Closure

Date: 2026-09-10 (Asia/Taipei)

```text
TASK=B2 Lifecycle V1.3 Formal Publication Retry
EXACT_SHA_BEFORE=11f89614626b4690ff5da6f97d0de36356841f32
EXACT_SHA_AFTER=THIS_COMMIT
COMMIT_MESSAGE=feat(lifecycle): publish formal v1.3 states

B0_FROZEN_CONTRACT_UNCHANGED=PASS
A9_FORMAL_TOPIC_SNAPSHOT_CONSUMED=YES
SECOND_TOPIC_AUTHORITY_CREATED=NO
LEAF_TOPIC_SCOPE=107_FROZEN;106_CURRENT_CATALOG;92_FORMAL_ROWS_PER_DATE
PARENT_LIFECYCLE=NOT_APPLICABLE
FORMAL_HISTORY_AUDIT=PASS_WITH_AUTHORITY_GAPS
FORMAL_HISTORY_DATES=2026-08-28,2026-08-31,2026-09-04,2026-09-07,2026-09-08,2026-09-09
FORMAL_HISTORY_SESSION_COUNT=6
FORMAL_HISTORY_ROWS=552
FORMAL_ROWS_PER_SESSION=92
EXPECTED_FROZEN_LEAF_ROWS_PER_SESSION=107
MISSING_FROZEN_LEAF_ROWS_PER_SESSION=15
EARLIEST_FORMAL_LIFECYCLE_DATE=UNAVAILABLE
FIRST_FORMAL_STATE_INITIALIZATION=FAIL_CLOSED_FROZEN_CONTRACT_UNDEFINED
LIFECYCLE_V1_3_EVALUATOR_FROZEN=PASS
FORMAL_PERSISTENCE_BOUNDARY=PASS
SHADOW_NOT_PROMOTED=PASS
FORMAL_LINEAGE=PASS_FOR_552_AVAILABLE_A9_ROWS
FORMAL_PUBLICATION_READBACK=NOT_APPLICABLE_NO_LEGITIMATE_PUBLICATION
DETERMINISTIC_REPLAY=PASS
IDEMPOTENCY=PASS
NO_RESEARCH_FIXTURE_PROMOTION=PASS
NO_FALLBACK=PASS
B2_IMPLEMENTATION=PASS

LIFECYCLE_V1_3_FORMAL=NO
B2_STATUS=BLOCKED_INITIALIZATION_CONTRACT
SAFE_TO_PROCEED_WITH_B3=NO
PRODUCTION_MUTATION=NO
B2_DEPLOY=NO
B3_STARTED=NO
B4_STARTED=NO
C_DRIVE_ARTIFACTS_CREATED=0
```

`THIS_COMMIT` denotes the commit containing the B2 source, tests, and this
report because a commit cannot embed its own object ID. The resolved SHA is
reported in the final handoff.

## Closure decision

B2's implementation is complete and fail-closed, but Lifecycle V1.3 cannot be
formally published under the frozen contract. More A9 sessions do not resolve
the blocker: the publisher may consume a prior state only from an earlier
`PUBLISHED` B2 formal row, while the first formal row has no prior B2 state.
Every otherwise-qualified first row therefore returns
`INSUFFICIENT_FORMAL_HISTORY:PREVIOUS_FORMAL_STATE_REQUIRED`; unavailable rows
cannot bootstrap a later published state.

The frozen B0 decision artifact states that FERMENTING is the first formally
confirmed Lifecycle state, SPROUTING is optional, BASE→FERMENTING is legal,
and confirmed states are forward-persistent. It does not define an initial
prior state, an initial state-entry date, or permission to treat the first A9
observation as BASE. It also provides no authority to seed from the 52,002-row
research reconstruction or from SHADOW rows. Assigning any of those would
redesign the frozen contract, so this retry fails closed.

## Current A9 formal-history audit

Read-only Production API pagination with `latest=false` returned 552 formal
Topic Snapshot rows across six dates:

| Formal date | Rows | COMPLETE | Partial/unavailable |
| --- | ---: | ---: | ---: |
| 2026-08-28 | 92 | 92 | 0 |
| 2026-08-31 | 92 | 92 | 0 |
| 2026-09-04 | 92 | 92 | 0 |
| 2026-09-07 | 92 | 92 | 0 |
| 2026-09-08 | 92 | 92 | 0 |
| 2026-09-09 | 92 | 92 | 0 |

All 552 rows are `FORMAL`, `PIT_FORMAL`, `FINAL`, `PUBLISHED` and have the
required snapshot identity, membership ID/hash, relation version, source
artifact ID/hash, registry/mapping versions, session/calendar, and lineage
hash. No malformed or superseded current row was accepted.

The current catalog independently reports 130 active nodes: 24 Parent and 106
Leaf. This differs from the frozen B2 ontology of 25 Parent and 107 Leaf. Only
92 formal snapshots exist per audited date, leaving 15 rows short of the
frozen 107-Leaf denominator. The history is therefore both initialization-
blocked and scope-incomplete. Research history was not used to fill either
gap.

## Implemented boundary

- The formal evaluator adapter binds the accepted V1.3 transition and
  persistence rules without changing thresholds or B0/B1 research semantics.
- The publisher consumes only A9 formal Topic Snapshots and member facts,
  qualifies exact lineage and canonical price evidence, and excludes Parent
  topics.
- Migration 0037 creates a separate constrained formal result table with
  publication, version, input lineage, correction, and supersession fields.
- Persistence is deterministic and idempotent for identical inputs; conflicting
  input/lineage fails reconciliation instead of overwriting history.
- Formal readback prefers the formal table. Missing or explicitly unavailable
  formal authority returns unavailable and never exposes SHADOW as formal.
- The operator command supports one date or deterministic replay and has a
  dry-run boundary. No scheduler or second Topic authority was created.

## Validation

- Direct B2 suite: 15/15 passed twice with identical results.
- Broader Lifecycle, Topic formal-state, production read-model, and architecture
  scope: 47 passed, 1 pre-existing failure. The failure is the existing
  architecture-freeze table inventory omitting the already-present Home tables
  (`home_publications`, `home_publication_sections`, `home_market_facts`); it is
  reported as failure and is not attributed to B2.
- Alembic graph: migration 0037 is the single head and follows 0036.
- Python compile and Ruff B2 scope: PASS.
- `git diff --check`: PASS.
- API/OpenAPI/generated-client files were not changed by B2. Phase 1 already
  verified the deployed combined contract at 45/45.

## Exact activation boundary and required decision

No B2 migration, materialization, deployment, scheduler action, or Production
data write was performed because preflight cannot produce a legitimate first
formal state. Before B2 can close, the Owner must add one explicit frozen
initialization rule defining all of the following together:

1. the prior state used for a Leaf's first eligible formal A9 observation;
2. the authoritative state-entry date and trading-day count for that state;
3. whether the first observation may directly confirm FERMENTING or another
   state, and how confirmation streak/memory starts; and
4. how a Leaf missing on the initialization date first enters later, without
   borrowing research or SHADOW history.

The smallest likely decision to review is an explicit formal BASE
initialization contract, but this report does not adopt it. The 107-Leaf frozen
scope must also be reconciled against the current 106-Leaf catalog and 92-row
A9 publication surface before any migration/materialization activation.

## Preservation

All unrelated owner/frontend/A10/deployment/tooling dirty hunks and untracked
files were preserved. The B2 commit stages only the previously prepared B2
model, migration, evaluator, publisher, CLI, formal read boundary, focused
test, exact shared registration/read-model hunks, and this report. No reset,
clean, checkout, overwrite, stash manipulation, broad staging, push, deploy,
Production mutation, `NEXT_TASK` change, B3, or B4 work occurred.
