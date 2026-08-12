# TopicPilot Topic Lifecycle Specification

**Status:** PM-frozen product meaning; backend policy values remain provisional
**Implementation:** TASK-BE-021 V2 shadow integration
**Authority:** V2 backend read model; the frontend does not derive lifecycle

## Product meaning

Lifecycle describes the diffusion of a topic through its constituent stocks:
?????? ???????? ???????? ??????????????????? It is a market-structure
dimension, separate from Grade and Score. News/Radar may explain a catalyst but
cannot select a lifecycle stage.

## Stage semantics

| Backend stage | Product meaning | Historical market language |
|---|---|---|
| `SPROUTING` | A reaction is concentrated in one or a few leading/representative stocks. | ?????? |
| `FERMENTING` | Strength diffuses to part of the core/related group, but participation is not broad. | ?????? |
| `MAIN_RISE` | Representative, core, and many related stocks participate together. | ?????? |
| `MATURE` | After a main rise, strength remains but the group is consolidating, rotating, or diverging. | ??????????????|
| `DECLINING` | Leadership and group participation weaken persistently and structurally. | ????|

`MATURE` is not weakness and `DECLINING` is not a one-day pullback. A missing
or insufficient observation is an internal `INSUFFICIENT_DATA`/`PENDING` state,
not a sixth user-facing stage.

## Evidence model

The backend result records Leadership, Diffusion, Group Strength,
Divergence/Decay, Persistence, coverage/sample confidence, confirmation state,
candidate/final stage, transition decision/reason, as-of trading date, and policy
version. The V2 engine reuses accepted canonical daily bars and effective-dated
instrument-topic relations through the existing `topic_snapshots` authority.

The current formal relation data does not contain an approved leader/core role
semantic. The engine therefore uses the strongest observed member as a clearly
labelled leadership proxy and reports `leaderSemanticAvailable=false`.

## State machine and transitions

Normal candidate changes require adaptive confirmation over trading days and hold
the previous stage while confirmation is pending. High-confidence, high-breadth
structure may jump directly to `MAIN_RISE`; high-confidence structural weakness
may jump to `DECLINING`. `MAIN_RISE ??MATURE ??MAIN_RISE` re-entry is legal and
resets Day N. No intermediate history is fabricated.

Day N is counted from persisted trading-date observations, not calendar days.
The engine is hysteretic: a stage does not change merely because one daily
return moved below a single threshold.

## Sample confidence and insufficient data

Coverage is observed valid member changes divided by expected topic membership.
Sample confidence is separately capped by observed count, so `2/2` is not
equivalent to `16/20`. Required minimum observed members and coverage are policy
values. Missing prices remain missing; they are never converted to zero.

## Config policy and shadow mode

All numeric values are centralized in `LifecyclePolicy`, versioned as
`topic-lifecycle-policy.provisional.1`, and labelled `PROVISIONAL/TUNABLE`.
`TopicLifecycleEngine` writes `topicpilot.topic_lifecycle_results` with
`evaluation_mode=SHADOW`; rows are idempotent and immutable for a policy/as-of
identity. `topicpilot-lifecycle --date ...` evaluates one snapshot date and
`--replay` evaluates all available snapshot dates. No activation flag exists in
this task and no production topic semantic is overwritten.

## Backend and frontend contract boundary

FastAPI exposes nullable lifecycle fields plus evidence, confidence, transition
reason, and policy version from the backend row. The frontend only renders those
fields for the API source. Preview lifecycle remains explicitly preview-only;
formal API responses with no lifecycle row remain unavailable/pending.

## Known limitations and future calibration

- The production database currently has formal identity (2 markets, 507
  instruments, 130 topics, 107 hierarchy edges, 848 relations) but no accepted
  formal price observations or topic snapshot rows, so historical replay and
  activation are waiting on data.
- Topic score/grade remain nullable/DEFERRED and are not used to force lifecycle.
- Approved role/leader metadata, relative-market performance, and multi-day
  historical observations are not yet available in production.
- PM calibration must compare shadow evidence with labelled trading-day reviews
  before any future activation decision. A new policy version, not an overwrite,
  is required for recalibration.

## Shadow calibration review contract

The repository provides a review-only contract over persisted `SHADOW` rows. It
contains topic identity and evaluation date; previous, candidate, and final
stage; transition decision/reason; stage entry and Day N; participation and
coverage; positive breadth and sample confidence; average change, strong breadth,
and weak ratio; leadership/proxy evidence; persistence and confirmation state;
data status; policy/calculation versions; and blank PM fields:
`PM_EXPECTED_STAGE`, `PM_RESULT`, and `PM_NOTE` (also emitted with stable
lowercase aliases). PM result values are constrained
to `MATCH`, `TOO_EARLY`, `TOO_LATE`, `TOO_STRONG`, `TOO_WEAK`, `WRONG_STAGE`, or
`INSUFFICIENT_EVIDENCE` when a reviewer supplies them; the engine never writes
these judgements.

`topicpilot-lifecycle --replay --export --format json|csv|markdown` emits a
deterministic export. `--representatives` adds one best-evidence case (or an
explicit missing case) for each frozen stage, transition candidate, confirmed
transition, strong jump, strong decline, MATURE-to-MAIN_RISE re-entry,
insufficient-data, and small-sample category. The export is additive review
tooling and does not create fixture market truth or activate frontend semantics.
