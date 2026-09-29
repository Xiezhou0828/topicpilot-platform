# Owner-seeded V0 forward-observation contract

## Authority boundary

This is a diagnostic evidence layer for the exact policy
`topic-strength-lifecycle.owner-seeded-v0`, version `v0`, hash
`5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef`.

It is not a new policy, score publisher, lifecycle authority, calibration
sample, or Production path. It must not override formal Grade/Lifecycle output,
rewrite historical output, infer historical role authority, or mutate a
Production database.

The initial manifest remains `OBSERVATION_START_DATE=PENDING_OWNER_ACTIVATION`.
The capture command requires a later explicitly authorized start date in its
input, so an activation task must precede real capture.

## Storage decision

The existing repository already has deterministic report and audit artifacts;
no persistent database schema is required for this evidence-only layer. Daily
artifacts are optional JSON files under an explicitly supplied observation
directory. No migration is created or applied.

## Daily input contract

The command consumes one JSON object containing:

- `as_of_date`, `observation_start_date`, and a governed-session marker;
- the exact policy id, version, and hash;
- `topic_id` and `topic_name`;
- formal-member, structural-role, benchmark, and trading-calendar authority versions;
- complete formal member rows with absolute return, market benchmark return, role,
  and role-legal Score Importance;
- the prior observation-chain lifecycle state, including only strictly earlier
  governed sessions.

Missing price or benchmark inputs, an unauthorized/non-trading date, a policy
identity mismatch, unordered/future history, or invalid role data fails closed
and produces no artifact.

## Deterministic capture interface

From `services/api`:

```text
PYTHONPATH=src python tools/capture_owner_seeded_v0_forward_observation.py \
  --input <authorized-snapshot.json> \
  --output-dir <observation-directory>
```

Use `--input -` and omit `--output-dir` for a no-write dry run. With an output
directory, the path is deterministic:
`<as_of_date>__<sanitized-topic-id>.json`. An identical rerun returns
`NOOP_IDENTICAL_ARTIFACT`; a conflicting rerun fails closed with
`EXISTING_ARTIFACT_CONFLICT`.

The helper only evaluates the supplied snapshot through the existing V0 module
and emits the required role evidence, absolute/relative score inputs and
contributions, grades, lifecycle candidate/after state, transition reason,
quality flags, and next observation-chain state. It does not connect to the
database or scheduler.

## Required daily fields

The machine-readable shape is
`forward-observation-schema.json`. It records:

- role counts and absolute/relative member score inputs;
- REP weighted raw, CORE median/breadth/strong/weak metrics, and RELATED breadth/
  median metrics;
- absolute and relative role contributions, totals, Grades, and D guards;
- lifecycle before/candidate/after, confirmation, transition reason, meaningful
  expansion, and renewed expansion flags;
- `FORMAL_MEMBER_COVERAGE_OK`, `STRUCTURAL_ROLE_AUTHORITY_OK`,
  `BENCHMARK_READY`, `PRICE_DATA_COMPLETE`, `RELATIVE_SCORE_AVAILABLE`,
  `SMALL_SAMPLE_X`, and `FAIL_CLOSED_REASON`;
- an explicit boundary marker proving the artifact is diagnostic-only.

One or two formal members remain an explicit `X` small-sample result. They are
not penalized and do not receive a Topic-size multiplier.

## Checkpoints

The manifest counts governed trading sessions only:

- `OBSERVATION_20D`: coverage/missing-data summary, Grade and Lifecycle
  distributions, transition matrix, boundary-near cases, unexpected outcomes,
  and Owner notes;
- `OBSERVATION_40D`: the 20D package plus persistence, repeated false starts,
  MATURE renewal, DECLINING recovery, relative/absolute disagreement, and
  topic-specific anomalies;
- `OBSERVATION_60D`: the provisional evidence package, boundary sensitivity
  questions, and one of `KEEP_V0`, `REVIEW_SELECTED_BOUNDARIES`, or
  `REQUIRES_POLICY_V1_RESEARCH`.

No checkpoint retunes thresholds automatically. No grid-search winner is
selected, no P&L definition of success is introduced, and any parameter change
requires a separate governed task.
