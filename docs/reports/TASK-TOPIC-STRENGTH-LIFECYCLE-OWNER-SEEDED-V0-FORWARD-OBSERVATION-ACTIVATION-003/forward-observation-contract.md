# Owner-seeded V0 activation and forward-observation contract

## Authorization and identity

This activation candidate is authorized only after:

```text
OWNER_REVIEW_STATUS=OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS
POLICY_REVISION_REQUIRED=NO
POLICY_CHANGED=NO
POLICY_RECALIBRATED=NO
FORWARD_OBSERVATION_AUTHORIZED=YES
```

Every daily artifact binds the four-part identity:

```text
policy_id
policy_version
policy_hash
implementation_sha
```

The policy hash is the frozen semantic payload identity. The implementation
SHA is the exact executable candidate identity and is preserved per observation.
They are never substituted for one another.

## Capture boundary

The capture helper consumes a completed, formal post-close Topic evaluation
readback. The caller must provide a governed session marker with:

- `status=POST_CLOSE`;
- `evaluable=true`;
- `timezone=Asia/Taipei`;
- a time-zoned `post_close_at` at or after `13:35` Asia/Taipei;
- complete formal member price and official benchmark inputs.

Weekend, market-closed, pre-boundary, missing-authority, incomplete-price,
incomplete-benchmark, and non-evaluable inputs fail closed and create no
artifact. The helper is read-only with respect to formal Topic authority.

The observation directory is an already-authorized JSON audit/artifact store;
no database table or migration is required. The deterministic artifact key is
`<as_of_date>__<sanitized-topic-id>.json`. An identical rerun returns
`NOOP_IDENTICAL_ARTIFACT`; a conflicting rerun fails with
`EXISTING_ARTIFACT_CONFLICT`.

## Formal versus diagnostic boundary

The backend continues to publish formal Daily Grade, Lifecycle, candidate and
transition state from their formal authority. Observation flags are derived
from the captured formal output and are diagnostic only. They cannot override
Grade, Lifecycle, Structural Role, Topic authority, Relation Weight, or
historical output. Capture failure does not roll back a committed formal
evaluation because the artifact write is a separate, post-readback diagnostic
boundary.

## Session denominator and checkpoints

The read model counts unique `as_of_date` values across valid artifacts bound to
this policy hash. A date is counted only when at least one Topic artifact has
passed the complete formal/evaluable capture boundary. Weekend, market-closed,
failed, and `evaluable=false` sessions do not count. Partially missing member
rows fail that Topic capture and do not add a global session date.

The read model exposes `OBSERVATION_20D`, `OBSERVATION_40D`, and
`OBSERVATION_60D` with these states:

```text
NOT_STARTED
IN_PROGRESS
READY_FOR_OWNER_REVIEW
REVIEWED
```

Reaching a checkpoint produces `READY_FOR_OWNER_REVIEW`; it never automatically
produces `REVIEWED` and never recalibrates the policy. Before the first valid
artifact, the start date is `PENDING_CANONICAL_ACTIVATION`, the session count is
zero, and all checkpoints are `NOT_STARTED`.

## Accepted diagnostic flags

The four Owner-accepted flags are emitted deterministically by the backend:

- `STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE`
- `GRADE_D_WHILE_DECLINING_PENDING`
- `ABS_REL_GRADE_DIVERGENCE`
- `MATURE_OR_MAIN_RISE_WITH_GRADE_B`

The frontend renders them as `觀察中`, not errors, and never re-derives them.

## Post-close integration status

The capture helper and backend read model are activation-ready. Wiring a
canonical scheduler/Production environment and selecting the first eligible
trading session remains the separate canonical promotion decision. No
Production database is mutated by this task.
