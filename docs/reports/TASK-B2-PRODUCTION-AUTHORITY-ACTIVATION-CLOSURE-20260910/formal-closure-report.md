# TASK B2 Production Authority Activation Closure

Date: 2026-09-10 (Asia/Taipei)

```text
EXACT_SHA_BEFORE=4666942c098a507f299b9a7210ddecd7d217e7a9
EXACT_SHA_AFTER=THIS_COMMIT
PRODUCTION_REVISION_BEFORE=74226c387ff36bf328936da0bd12114c2773d9e3
PRODUCTION_REVISION_AFTER=74226c387ff36bf328936da0bd12114c2773d9e3

ONTOLOGY_MAPPING_VERSION=NOT_ACTIVATABLE_FROM_EXISTING_PROTECTED_PROCEDURE
ONTOLOGY_MAPPING_ACTIVE=NO
FORMAL_ONTOLOGY_MAPPING_ACTIVE=NO
FORMAL_CATALOG_SCOPE_RESOLUTION=106_ACTIVE_LEAVES
LIFECYCLE_FORMAL_SCOPE_LEAVES=106_RESOLVED;107_REQUIRED
FORMAL_SCOPE_ACCOUNTING=FAIL_CLOSED

FORMAL_BASE_BOOTSTRAP_V1=PASS
LATE_ENTERING_LEAF_BOOTSTRAP=PASS
DETERMINISTIC_REPLAY=PASS_SOURCE
IDEMPOTENCY=PASS_SOURCE
PRODUCTION_B2_REPLAY=NOT_RUN_PREFLIGHT_FAILED

A10_SCHEDULER_REGRESSION=PASS_SOURCE_TESTS
PRODUCTION_FINAL_SCHEDULE=15:00_ASIA_TAIPEI
PRODUCTION_WORKER_HEALTH=PASS_PRESERVED_LATEST_AUTHORITY;NOT_MUTATED

LIFECYCLE_V1_3_FORMAL=NO
B2_STATUS=BLOCKED_MISSING_PROTECTED_ONTOLOGY_ACTIVATION_AUTHORITY
SAFE_TO_PROCEED_WITH_B3=NO
B3_STARTED=NO
NEXT_TASK_MUTATION=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
C_DRIVE_ARTIFACTS_CREATED=0
```

`THIS_COMMIT` denotes the commit containing this report; its resolved object ID
is recorded in the final handoff.

## Disposition

The requested Production activation cannot be executed under the task's hard
rules. The repository has no protected procedure that promotes
`config/topic_master_v1` into the V2 Production Topic, hierarchy, and relation
tables. The existing `topicpilot-topic-master` command explicitly performs
validation and dry-run planning only, writes at most a local derived JSON
snapshot, and deliberately does not connect to PostgreSQL. The protected
`Manual release handoff` workflow deploys a committed API revision and runs
migrations at service startup; it contains no ontology authority activation or
data-publication step. The admin Topic endpoints are read-only.

The generic `topicpilot-import` command is not a valid substitute. It imports
an enterprise bundle into a different legacy read-model schema and replaces
current relations; it does not consume the Owner Topic Master V1 sync plan or
write the formal V2 authority tables used by A9 and B2. Using it would bypass
the required authority boundary. A9.3 is evidence from a non-Production
database and explicitly records `PRODUCTION_MUTATION=NO`; it is not a reusable
protected Production activation workflow.

No ad-hoc SQL, manual row edit, registry bypass, deployment, or Production B2
replay was attempted after this preflight failure.

## Production authority readback

Read-only Production results at revision
`74226c387ff36bf328936da0bd12114c2773d9e3`:

| Surface | Actual |
| --- | ---: |
| Topic rows | 130 |
| Hierarchy edges | 107 |
| Public current Parent identities | 24 |
| Public current active Leaf identities | 106 |
| Current COMPLETE formal snapshots | 92 |
| Current catalog Leaves with `FORMAL_SNAPSHOT_NOT_PUBLISHED` | 14 |
| Alembic revision | `0036_task_ws4_active_reference_daily_projection` |

`/healthz` and `/readyz` both reported the exact Production revision and healthy
state. The B2 migration and formal v2 publisher are not deployed.

The 107 hierarchy edges do not establish 107 current canonical Leaves. One
edge resolves to a disabled/retired predecessor identity. Counting every
hierarchy child, as the first B2.2 implementation did, could therefore make the
number reach 107 by counting an obsolete identity. This task fixes that bounded
defect: formal scope now requires an active effective child and fails with
`expected=107:actual=106`. Missing observation data still cannot remove an
active Leaf; it produces an unavailable formal result after scope authority is
valid.

## Identity reconciliation and missing authority

The frozen and Owner-approved source ontology contains 107 active Leaf rows.
Production contains 106 current Leaf rows. Comparing stable names shows 13
Owner-source active identities absent from Production and 12 older Production
identities absent from the active source, for the exact net difference of one.

Owner-source only:

```text
銅箔基板CCL
特用與精密線束
利基型光電磊晶
貨代與物流
貨櫃海運
散裝航運
航空客貨運
邊緣運算與智慧影像 (Edge AI & Vision)
高階測試介面與探針 (Advanced Testing Interfaces)
利基型特用化學 (Specialty Chemical Materials)
生技醫藥與CDMO (Biotech & CDMO)
製程耗材與特料
傳統硬板與軟板
```

Production only relative to the active Owner source:

```text
CCL
PCB
其他高頻材料
其他連接器
半導體原料
其他建設
其他晶圓材料
其他自動化
其他資安
其他高速互連
大型金融權值
特殊金屬材料
```

The existing Owner-approved rename artifact authorizes these Leaf resolutions:

| Research/source identity | Canonical decision |
| --- | --- |
| `CCL` | rename to `銅箔基板CCL` |
| `PCB` | deactivate; add distinct `傳統硬板與軟板` |
| `其他高頻材料` | rename to `製程耗材與特料` |
| `其他連接器` | rename to `特用與精密線束` |
| `半導體原料` | rename to `利基型光電磊晶` |

It does not provide a complete stable-ID/UUID mapping for all 107 frozen
identities to the current Production UUID set, and its own identity field says
`NO_STABLE_ID_NAME_KEY_UPDATED`. The remaining source-only/Production-only
identities cannot be paired by inference. Therefore the exact 107th resolution
cannot be proven without inventing mappings or double-counting obsolete nodes.

Safe activation requires both missing pieces:

1. an Owner-approved, versioned, complete mapping artifact with all 107 frozen
   identity keys, target Production UUID/current canonical identity, effective
   date, action (`PRESERVE`, `RENAME`, `REPLACE`, or `DEACTIVATE`), and an
   explicit no-double-count canonical resolution; and
2. a repository-governed protected writer/workflow that validates that artifact
   and transactionally activates the V2 Topic/hierarchy authority with dry-run,
   duplicate, Parent/Leaf, lineage, revision, rollback, and readback guards.

Creating either authority or activation mechanism in this task would violate
the explicit instruction to use the existing protected procedure and not
design a new ontology/activation path.

## Preflight and tests

The current Owner Master validates successfully with source hash
`8f5646f4b9e5f00c9263bf7511911f4520ec2b940af1fc50c778b0d9e83ce2c4`,
136 total Topic rows, zero errors, and 382 warnings. Validation proves internal
CSV shape; it does not create the absent stable identity mapping or Production
writer.

- B2 direct suite: 18 passed.
- Lifecycle, initialization, Topic Snapshot, Topic Catalog, production
  read-model, and A10 daily-forward regression scope: 59 passed, 0 failed.
- Ruff: PASS.
- The new regression proves that 106 active children plus one retired child
  fail scope resolution instead of counting the obsolete child as number 107.
- Production replay, second replay, Lifecycle API publication readback, and
  migration 0037 readback were correctly withheld because activation preflight
  failed.

## A10 and preservation

No scheduler setting, worker deployment, environment, frontend, Selector,
`NEXT_TASK`, B3, or B4 state changed. The latest Production authority remains
15:00 Asia/Taipei and the source daily-forward regression passed. All existing
owner/frontend/A10/deployment/tooling tracked and untracked work was preserved.
Only the bounded formal-scope guard, its test, and this report are committed.

The blocker is a concrete authority/runtime gap and is independent of the
resolved `PREVIOUS_FORMAL_STATE_REQUIRED` initialization deadlock.
