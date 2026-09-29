# Topic Strength/Lifecycle Owner-seeded V0 — Forward Observation Activation

## Scope and disposition

This candidate implements the Owner-authorized forward-observation and Topic
frontend readback path. It does not retune or recalibrate the accepted V0
policy, does not promote Production, and does not mutate the Production
database.

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003
CANONICAL_BASE_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be
OWNER_REVIEW_SOURCE_SHA=04f208a6e3465207652938e1229f41be122f63f9
IMPLEMENTATION_SHA=PENDING_ACTIVATION_CODE_COMMIT
POLICY_ID=topic-strength-lifecycle.owner-seeded-v0
POLICY_VERSION=v0
POLICY_HASH=5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef
OWNER_REVIEW_STATUS=OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS
POLICY_REVISION_REQUIRED=NO
POLICY_CHANGED=NO
POLICY_RECALIBRATED=NO
```

## Owner acceptance

The durable acceptance record is in the activation directory's
`owner-acceptance.md`. The accepted flags are:

- `STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE`
- `GRADE_D_WHILE_DECLINING_PENDING`
- `ABS_REL_GRADE_DIVERGENCE`
- `MATURE_OR_MAIN_RISE_WITH_GRADE_B`

The bounded CORE-only deep-weakness correction remains preserved. No V0
threshold, lifecycle confirmation count, guard, cap, importance, or small-
sample semantics changed in this task.

## Observation activation and storage

The capture helper now requires the exact policy identity, the activation
acceptance status, and a 40-character implementation SHA. It accepts only a
formal post-close readback with `POST_CLOSE`, `evaluable=true`,
`Asia/Taipei`, and a time-zoned boundary at or after `13:35`. It fails closed
for weekend/closed, non-evaluable, incomplete, or unbound inputs. The artifact
key remains deterministic and identical reruns are no-ops; conflicts fail
closed.

The observation store is the existing JSON audit/artifact path. No new table is
required. The backend read model reads only valid activation-v2 artifacts
bound to the frozen policy hash and preserves each artifact's implementation
SHA. A failed observation write cannot change a previously committed formal
Grade/Lifecycle result because the capture boundary is post-readback and
diagnostic-only.

Observation begins only after canonical promotion. Since this task does not
deploy or activate Production:

```text
OBSERVATION_START_DATE=PENDING_CANONICAL_ACTIVATION
OBSERVATION_SESSION_COUNT=0
OBSERVATION_20D_STATUS=NOT_STARTED
OBSERVATION_40D_STATUS=NOT_STARTED
OBSERVATION_60D_STATUS=NOT_STARTED
```

The denominator is unique valid governed trading-session dates. Weekend,
market-closed, failed, and non-evaluable sessions do not count. Checkpoints
become `READY_FOR_OWNER_REVIEW` when reached and are never auto-marked
`REVIEWED`; no checkpoint triggers recalibration.

## Backend formal read model

`/api/v2/topics` and `/api/v2/topics/{slug}` retain their existing formal
Topic fields and add two additive fields:

- `ownerSeededV0`: current diagnostic readback with Daily Grade, separate
  Absolute/Relative score and Grade, lifecycle before/candidate/after,
  transition reason, exact identity, quality flags, and accepted observation
  flags;
- `forwardObservation`: start status, unique session count, next checkpoint,
  20D/40D/60D status, latest date, and implementation identities.

Before the first artifact, the read model returns a waiting state and
`PENDING_CANONICAL_ACTIVATION`; it does not publish a misleading `0/20`.
Malformed artifacts fail the diagnostic read model closed and do not affect
formal Topic authority.

## Frontend placement and boundary

The existing Topic detail page consumes the additive backend read model. It
shows Daily Grade, Lifecycle, candidate/confirmation state, distinct Absolute
and Relative values, neutral `觀察中` flag chips with backend-provided copy,
and forward-observation progress. A missing formal read model is shown as
unavailable. No local Grade/Lifecycle/flag/checkpoint calculation or policy
threshold is present in the frontend, and no new top-level product area was
created. The layout uses the existing Topic design language and responsive
grids for desktop and compact desktop widths.

## Status

```text
OWNER_ACCEPTANCE_RECORDED=YES
POLICY_HASH_VERIFIED=YES
POLICY_CHANGED=NO
POLICY_RECALIBRATED=NO
BOUNDED_DEFECT_FIX_PRESERVED=YES
FORWARD_OBSERVATION_CAPTURE_READY=YES
OBSERVATION_SCHEMA_READY=YES
OBSERVATION_MANIFEST_READY=YES
OBSERVATION_FLAGS_IMPLEMENTED=YES
POLICY_AND_IMPLEMENTATION_IDENTITY_BOUND=YES
BACKEND_TOPIC_READ_MODEL_READY=YES
FRONTEND_TOPIC_STRENGTH_DISPLAY_READY=YES
FRONTEND_LIFECYCLE_DISPLAY_READY=YES
FRONTEND_CANDIDATE_CONFIRMATION_READY=YES
FRONTEND_ABSOLUTE_RELATIVE_DISPLAY_READY=YES
FRONTEND_OBSERVATION_FLAGS_READY=YES
FRONTEND_OBSERVATION_PROGRESS_READY=YES
FRONTEND_REDERIVES_POLICY=NO
MIGRATION_REQUIRED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
DEPLOYED=NO
PRODUCTION_ACTIVE=NO
PRODUCTION_DB_MUTATED=NO
```

No real-world V0 validation, Lifecycle verification, or completed 20D/40D/60D
evidence is claimed. The next governed step is
`TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-CANONICAL-PROMOTION-004`.
