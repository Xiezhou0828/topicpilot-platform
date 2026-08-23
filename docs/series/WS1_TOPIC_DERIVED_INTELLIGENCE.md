# WS1 — Topic Derived Intelligence

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; the linked contracts own the formal rules.

## Scope

Topic-derived intelligence covers structural roles, Score Projection,
point-in-time topic state, ranking/breadth/leadership/concentration, Topic
Lifecycle, and the boundary between derived data and formal publication.

## Current state

- Owner decision D001 and the additive Structural Role / Score Projection read
  infrastructure are canonicalized.
- Fail-closed as-of resolvers and the `0..N` instrument-to-topic relation
  boundary are in place. A zero-topic instrument is valid and must not be
  dropped or assigned a placeholder topic.
- Role and projection rows are still unpopulated. Topic Score and Grade remain
  unpublished.
- The bounded formal Topic PIT state has 460 published, non-superseded daily
  snapshots and 4,235 member facts across five dates.
- Missing projection is scoped to the affected Topic/as-of request; it must not
  globally fail unrelated Topics or derived lanes.

### Lifecycle boundary

```text
Product meaning: SPROUTING / FERMENTING / MAIN_RISE / MATURE / DECLINING
Lifecycle != Topic Score != Grade
Policy: topic-lifecycle-policy.provisional.1
Execution: SHADOW only
Formal publication: NO
Leader/core meaning: strongest observed member is a labelled leadership proxy only
Frontend: renders backend fields; never derives Lifecycle in the browser
```

Lifecycle code or shadow rows do not establish formal production publication.
Missing formal point-in-time role authority keeps the formal lane unavailable.

## Canonical authority

- [Topic Derived Intelligence Publication and Lifecycle Dependency Contract](../architecture/TOPIC_DERIVED_INTELLIGENCE_PUBLICATION_AND_LIFECYCLE_DEPENDENCY_CONTRACT.md)
- [Topic Derived Intelligence Definition and Publication Authority Closure](../architecture/TOPIC_DERIVED_INTELLIGENCE_DEFINITION_AND_PUBLICATION_AUTHORITY_CLOSURE.md)
- [Topic Lifecycle Specification](../product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md)
- [Topic Engine Contract](../architecture/PHASE_3_7_001_TOPIC_ENGINE_CONTRACT.md)

## Completed

- Structural-role and Score Projection authority/read boundaries.
- Fail-closed as-of resolution and nullable derived-field behavior.
- Bounded Topic PIT membership and daily-state materialization.
- Product semantic separation of Lifecycle, Score, and Grade.

## Unfinished / unpublished

- Owner-reviewed, effective-dated role data ingestion.
- Approved Score Projection V1 data population.
- Formal Score, Grade, ranking, breadth, leadership, concentration, and
  Lifecycle history publication.
- Complete Topic Detail fields and any derived values that depend on missing
  formal authority.

## Dependencies and blockers

- Formal role/core semantics and effective-dated PIT provenance.
- Approved Score Projection V1 source and publication contract.
- Separate authority for ranking, breadth, leadership, concentration, and
  Lifecycle history.

## Do not do

- Do not turn a leader proxy into an approved formal leader/core role.
- Do not infer Lifecycle, Score, Grade, ranking, or breadth in the frontend.
- Do not treat a non-null shadow value as Production publication.
- Do not use a report or fixture to override the canonical contract.

## Historical evidence

- [WS1 policy closure](../reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002.md)
- [WS1 implementation closure](../reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003.md)
- [Topic PIT membership and daily-state closure](../reports/TASK-TOPIC-PIT-MEMBERSHIP-AND-DAILY-STATE-CONTRACT-CLOSURE.md)
- [Topic daily-state schema and materialization](../reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md)
- [Lifecycle readiness audit](../reports/TASK-TOPIC-HISTORICAL-STATE-LIFECYCLE-READINESS-AUDIT.md)

## Next bounded route

Ingest only approved, Owner-reviewed, effective-dated role data and approved
Score Projection V1 data. Validate as-of and fail-closed behavior before any
formal publication decision. This route does not authorize Score/Grade release,
Lifecycle activation, ranking implementation, or a `NEXT_TASK` change.
