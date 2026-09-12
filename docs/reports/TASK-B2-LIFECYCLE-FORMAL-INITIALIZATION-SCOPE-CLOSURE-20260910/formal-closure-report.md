# TASK B2.1/B2.2 | Formal Initialization and Leaf Scope Closure

Date: 2026-09-10 (Asia/Taipei)

```text
EXACT_SHA_BEFORE=ca78738d76335043dae4917b11a9ea80cee4d08c
EXACT_SHA_AFTER=THIS_COMMIT
COMMIT_MESSAGE=fix(lifecycle): define formal initialization contract

B0_FROZEN_TRANSITION_SEMANTICS_UNCHANGED=PASS
FORMAL_BASE_BOOTSTRAP_V1=PASS
INITIALIZATION_CONTRACT_VERSIONED=PASS
NO_RESEARCH_SHADOW_DEMO_BOOTSTRAP=PASS
FIRST_ELIGIBLE_DATE_ONLY=PASS
LATE_ENTERING_LEAF_BOOTSTRAP=PASS
FORMAL_CATALOG_SCOPE_RECONCILED=BLOCKED_PRODUCTION_ONTOLOGY_MAPPING_NOT_ACTIVATED
EXPLICIT_VERSIONED_MAPPING=PASS_SOURCE_AUTHORITY;NOT_ACTIVE_IN_PRODUCTION
FORMAL_CATALOG_LEAF_IDENTITIES=107_SOURCE_AUTHORITY
LIFECYCLE_FORMAL_SCOPE_LEAVES=107_CONTRACT
FORMAL_SCOPE_ACCOUNTING=PASS_SOURCE;BLOCKED_PRODUCTION_PREFLIGHT
A9_FORMAL_TOPIC_SNAPSHOT_CONSUMED=YES_READ_ONLY
SECOND_TOPIC_AUTHORITY_CREATED=NO
PARENT_LIFECYCLE=NOT_APPLICABLE
FORMAL_LINEAGE=PASS
DETERMINISTIC_REPLAY=PASS_SOURCE_TEST
IDEMPOTENCY=PASS_SOURCE_TEST
NO_FAKE_DATA=PASS
NO_FALLBACK=PASS
B2_IMPLEMENTATION=PASS

EARLIEST_ELIGIBLE_FORMAL_DATE=2026-08-28_FOR_CURRENT_COMPLETE_A9_ROWS
PRODUCTION_CATALOG_LEAVES=106
PRODUCTION_COMPLETE_FORMAL_SNAPSHOT_LEAVES=92
PRODUCTION_UNAVAILABLE_CATALOG_LEAVES=14
FROZEN_SCOPE_UNAVAILABLE_LEAVES=15

LIFECYCLE_V1_3_FORMAL=NO
B2_STATUS=BLOCKED_FORMAL_SCOPE_AUTHORITY_ACTIVATION
SAFE_TO_PROCEED_WITH_B3=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
B3_STARTED=NO
B4_STARTED=NO
NEXT_TASK_MUTATION=NO
C_DRIVE_ARTIFACTS_CREATED=0
```

`THIS_COMMIT` denotes the commit containing this report. A commit cannot embed
its own object ID; the resolved SHA is recorded in the final handoff.

## Owner decision materialized

`FORMAL_BASE_BOOTSTRAP_V1` is now the explicit first-state contract. For a
Leaf with a complete, lineage-qualified A9 FORMAL observation and no earlier
published FORMAL Lifecycle state, the evaluator receives logical prior state
`BASE`, prior entry date equal to that Leaf's current eligible trading date,
prior trading-day count `0`, no prior candidate, candidate streak `0`, and an
empty state-memory mapping. The resulting row records the initialization mode,
version, first eligible date, logical prior values, and empty/default
confirmation-memory declaration in formal source lineage.

An incomplete or missing observation writes only an unavailable decision and
does not initialize state. Consequently, a Leaf absent on the global first
date initializes independently on its own later first complete date. Once an
earlier published FORMAL row exists, the bootstrap helper returns that row and
the normal V1.3 forward-persistent path is permanently used. No SHADOW,
research reconstruction, demo, manual, legacy, forward-filled, or retroactive
state is queried or inherited.

The formal contract version advances from
`topic-lifecycle-v1.3-formal.v1` to `topic-lifecycle-v1.3-formal.v2` so the new
initialization decision is explicit and cannot collide with the previous
fail-closed unavailable facts. The calculation version remains
`topic-lifecycle-v1.3-formal-evaluator.v1`.

## Frozen V1.3 compatibility proof

The frozen B0 decisions define BASE as a Lifecycle state, explicitly allow
direct `BASE -> FERMENTING`, make SPROUTING optional, and retain all confirmed
states through the existing forward-persistence rules. The bootstrap supplies
only the otherwise-missing logical prior context before the existing evaluator
call. It changes no thresholds, evidence calculations, candidate rules,
confirmation length, transition rule, failure reset, or persistence guard.
Focused tests preserve FERMENTING failure to BASE, MATURE renewed-strength
persistence, DECLINING rebound persistence, optional SPROUTING, and direct
BASE-to-FERMENTING confirmation.

## 107-identity reconciliation

| Authority surface | Parent | Leaf | Disposition |
| --- | ---: | ---: | --- |
| Frozen/Owner-approved ontology materialization | 25 | 107 | Lifecycle scope authority |
| Owner-approved `config/topic_master_v1/topics.csv` active rows | 25 | 107 | Source authority confirmed |
| Production Topic Catalog readback, 2026-09-10 | 24 | 106 | Older ontology remains active |
| Production A9 complete formal snapshots, latest audited session | n/a | 92 | Complete observations |
| Production catalog Leaves without a formal snapshot | n/a | 14 | Explicitly unavailable |
| Frozen-scope Leaves without complete coverage | n/a | 15 | Must remain accounted for |

The Owner-approved identity map explicitly preserves rename/replacement
lineage for `CCL -> 銅箔基板CCL`, retires old `PCB` while adding
`傳統硬板與軟板`, and maps `其他高頻材料 -> 製程耗材與特料`,
`其他連接器 -> 特用與精密線束`, and `半導體原料 -> 利基型光電磊晶`.
The source authority contains 13 active Leaf identities absent from the live
catalog, while the live catalog contains 12 obsolete/older Leaf identities
absent from the active source authority. This is the exact net `107 - 106 = 1`
identity discrepancy. Those identities cannot be silently paired beyond the
approved map, resurrected, or double-counted.

The `92` discrepancy is observation availability: Production readback has 92
complete current A9 snapshots and 14 catalog Leaves with
`FORMAL_SNAPSHOT_NOT_PUBLISHED`. Against the 107 frozen denominator, this is
`92 complete + 15 unavailable = 107`. Availability therefore does not define
scope membership.

The publisher now derives formal scope from all effective hierarchy child
identities, including disabled or temporarily unavailable topics, and enforces
the versioned exact count `lifecycle-formal-leaf-scope.v1 = 107`. A count other
than 107 raises `FORMAL_LEAF_SCOPE_RECONCILIATION_REQUIRED` before any result
write. Parent identities cannot enter this child-only scope.

## Replay and activation disposition

No Production database credential is present in this authorized source
checkout, and the deployed ontology preflight is 106 rather than 107. Running
the new publisher against that state would correctly fail before publication.
Migration 0037 is already the source single-head migration, but it has not been
deployed or applied by this task. No Production mutation or deployment was
performed because all preflight gates do not pass.

The exact activation sequence after the existing Owner-approved ontology map
is promoted is: verify effective hierarchy child count is 107; deploy/apply the
existing B2 schema and this v2 publisher through the protected release path;
run `topicpilot-lifecycle-formal --replay` with the protected Production
database binding; run the same replay a second time; compare normalized result
and lineage hashes; and read back formal Lifecycle rows through the production
API. The current blocker is independent of the former initialization deadlock.

## Validation

- Direct initialization/publication suite: 17 passed; repeated direct run
  before the final formatting-only edit also passed.
- Broader Lifecycle, Topic Snapshot, Topic Catalog, and production read-model
  scope: 51 passed, 0 failed, with two dependency deprecation warnings.
- Initialization coverage includes first bootstrap, Leaf-local late entry,
  prior-FORMAL bypass, empty confirmation memory/default streak, entry date and
  day count, incomplete first observation, Parent exclusion, deterministic
  evaluator equality, and persistence retry idempotency.
- Python compilation passed. Ruff and `git diff --check` are final gates run
  immediately before commit.
- Production checks were read-only. No second Topic authority or fallback was
  created.

## Preservation

All pre-existing frontend, A10, deployment, API-client, report, and tooling
dirty/untracked work was preserved. This task stages only the two Lifecycle
source files, the focused test file, and this report. It performs no reset,
clean, checkout, overwrite, stash manipulation, push, merge, deployment,
Production write, `NEXT_TASK` change, B3, or B4 work.
