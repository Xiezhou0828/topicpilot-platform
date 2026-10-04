# TopicPilot Formal Post-Close Strength + Lifecycle Chain

Date: 2026-10-05 (Asia/Taipei)

```text
TASK_TYPE=IMPLEMENTATION
REQUIRED_TERMINAL_STATE=CANONICALIZED_LOCAL
ACHIEVED_TERMINAL_STATE=CANONICALIZED_LOCAL
TASK_COMPLETE=YES
FOLLOW_UP_REQUIRED=NO
FOLLOW_UP_REASON=No in-scope implementation work remains; Production promotion is separately unauthorized.
CANONICAL_BASE=topicpilot-platform
EXACT_SHA_BEFORE=c79d823022f9ffa283a53a3ad5043de1b4393ebb
EXACT_SHA_AFTER=THIS_COMMIT
BRANCH=main
MIGRATION_HEAD=0048_task_checkpoint_provider_metric_applicability
PRODUCTION_DEPENDENCY=YES_RUNTIME_PATH_ONLY
PRODUCTION_STATUS=NOT_AUTHORIZED_NOT_EXECUTED
PUSH_STATUS=NOT_AUTHORIZED_NOT_EXECUTED
MERGE_STATUS=NOT_AUTHORIZED_NOT_EXECUTED
NEXT_TASK_STATUS=UNCHANGED
TEST_COUNT_PRE=NOT_RECORDED
TEST_COUNT_POST=1030
TEST_COUNT_DELTA=NOT_COMPUTED
TEST_COUNT_DELTA_REASON=Added formal Strength/Lifecycle contract coverage; no baseline full-suite run was recorded at task start.
```

## Implemented boundary

The canonical post-close runner now executes the formal chain after the
current-session formal Topic Snapshot and bounded formal daily-state gate:

```text
formal Topic Snapshot
  -> formal Absolute / Relative Strength + Daily Grade
  -> six structural derivatives + Market Context
  -> candidate / confirmed Lifecycle + Day N
  -> append-only formal receipts and readback
```

Strength is persisted in the existing `topic_score_formal_results` table from
migration `0045_task_m1_formal_score_grade_publication`; the ORM and writer
were added without introducing a parallel table. Absolute is the persisted
formal score/grade authority. Relative remains a separate analytical view and
uses the TAIEX/TWSE or TPEx/TPEX benchmark by member market. Missing or stale
benchmark facts remain unavailable rather than becoming zero.

Formal Lifecycle uses the existing formal publication table and now consumes
formal Strength/derivative evidence when available. Its structural evaluator
does not require mechanical stage adjacency, does not make one observation
into MAIN_RISE, supports direct MAIN_RISE-to-DECLINING evidence, treats
MATURE as healthy saturation, and preserves candidate versus confirmed state.
Small complete Topics are not penalized by member count; incomplete formal
authority coverage remains unavailable/partial.

Both publication writers are append-only and correction-aware. Same-date
changes create a superseding decision with input hashes, policy metadata,
implementation SHA, member-fact lineage, and correction reason. Strength has
an explicit replay entry point from a caller-supplied earliest affected date;
Lifecycle replay already re-evaluates the formal date range using the active
snapshot authority. Unavailable Lifecycle sessions preserve the last
successful state in auditable memory and do not publish a fake Day N; the next
successful same-state observation may continue Day N + 1.

The post-close checkpoint/readback path records formal Strength and Lifecycle
publication status independently. A valid Strength result is retained when
Lifecycle is unavailable, while overall final publication becomes partial or
blocked according to the existing run vocabulary. Recovery reuses committed
readback where available and never falls back to SHADOW output.

## Files and owning boundary

- `services/api/src/topicpilot_api/formal_strength_publication.py` — formal
  Strength writer, Market Context, structural derivatives, receipt lineage,
  replay, and active-result read API.
- `services/api/src/topicpilot_api/formal_lifecycle_evaluator.py` — formal
  structural candidate/confirmation evaluator.
- `services/api/src/topicpilot_api/lifecycle_formal_publication.py` — dynamic
  formal leaf scope, formal Strength binding, gap memory, supersession, and
  replay integration.
- `services/api/src/topicpilot_api/live/post_close.py` — post-close DAG,
  independent publication lanes, checkpoint metadata, recovery readback, and
  partial/fail-closed finalization.
- `services/api/src/topicpilot_api/orm/formal_lifecycle.py` and
  `services/api/src/topicpilot_api/orm/__init__.py` — ORM registration for the
  existing formal Strength result table.
- `services/api/src/topicpilot_api/production_read_model.py` — backend-owned
  formal Strength overlay; no frontend calculation was added.
- `services/api/src/topicpilot_api/topic_engine/owner_seeded_v0_policy.py`,
  `topic_lifecycle_v1.py` — optional formal member-count gate and compatible
  Lifecycle input extensions.
- `services/api/tests/test_formal_strength_lifecycle_chain.py` plus updated
  formal publication/post-close/architecture tests — contract and regression
  coverage.

## Validation

```text
RUFF=PASS
FOCUSED_TESTS=114 passed
FULL_API_TESTS=1030 passed, 60 skipped
ALEMBIC_HEAD=0048_task_checkpoint_provider_metric_applicability
ALEMBIC_FORMAL_SCORE_REVISION=0045_task_m1_formal_score_grade_publication
DIFF_CHECK=PASS
```

The 60 skipped tests require PostgreSQL or other explicitly configured
integration credentials and were not converted into false PASS results.
Production database mutation, migration execution against Production,
scheduler activation, deploy, remote push, merge, and `NEXT_TASK` changes were
not performed.
