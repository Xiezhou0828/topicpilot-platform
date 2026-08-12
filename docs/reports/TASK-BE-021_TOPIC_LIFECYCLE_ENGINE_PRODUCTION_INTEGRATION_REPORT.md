# TASK-BE-021 ??Topic Lifecycle Engine Production Integration Report

**Date:** 2026-08-12
**Scope:** V2 production DB ??FastAPI ??Sites lifecycle integration
**Mode:** Shadow evaluation only; production activation is not enabled

## Executive Summary

The V2 lifecycle engine is implemented as a configurable, explainable shadow
read model. It reuses the existing canonical accepted daily-bar evidence and
`topic_snapshots`, persists immutable-as-of-date lifecycle results, exposes them
through the existing `/api/v2/topics` contract, and lets the frontend render
backend-owned lifecycle values only. Grade/Score and News/Radar are not used to
select a stage.

The production identity chain is present and reconciled at the identity level:
2 markets, 507 instruments, 130 topics, 107 hierarchy edges, and 848
instrument-topic relations. The observed production API has no formal accepted
price observations or topic snapshot rows yet; therefore replay and activation
remain data-gated.

## Required status markers

```text
LIFECYCLE_ARCHITECTURE_RECONCILIATION = PASS
LIFECYCLE_ENGINE = PASS
LIFECYCLE_STATE_MACHINE = PASS
LIFECYCLE_EXPLAINABILITY = PASS
LIFECYCLE_SNAPSHOT_PERSISTENCE = PASS
LIFECYCLE_API_INTEGRATION = PASS
LIFECYCLE_FRONTEND_INTEGRATION = PASS
HISTORICAL_REPLAY = BLOCKED_BY_DATA
LIFECYCLE_PRODUCTION_ACTIVATION = WAITING_FOR_FORMAL_OBSERVATIONS
```

## Existing design/code audit

The audit covered the V2 ORM identity and canonical-observation models, the
`0024_task_be_007_topic_snapshots` migration and `TopicSnapshotEngine`, the
production read model/API, frontend topic API and lifecycle components, and the
V2 architecture/frontend specifications. The existing snapshot engine already
preserved null prices, effective-dated membership, source ranking, accepted
DAILY_BAR evidence, and `score_status=DEFERRED`. Lifecycle now consumes that
same authority rather than creating a parallel market-data source.

The public production API readback on 2026-08-12 returned `200` for health and
readiness, 130 formal topic identities, and 507 formal stock identities. Topic
score/grade/direction coverage and lifecycle were unavailable; topic snapshots
were empty and stock prices were missing. No formal role/leader semantic was
present in the observed relation payloads.

## Formal input contract

For each topic/trading date the engine accepts expected effective membership,
member close-to-close changes from accepted canonical DAILY_BAR observations,
optional role metadata, the previous persisted state, and policy version. It
outputs candidate/final stage, stage entry and Day N, evaluation/data status,
five evidence groups, confidence/coverage, confirmation state, and a stable
transition decision/reason.

## Lifecycle architecture

```text
canonical accepted DAILY_BAR
        ??existing topic_snapshots + effective topic membership
        ??TopicLifecycleEngine (LifecyclePolicy, shadow mode)
        ??topicpilot.topic_lifecycle_results
        ??FastAPI /api/v2/topics ??Sites (backend-owned rendering)
```

The new table is separate from `topic_snapshots` so the provisional lifecycle
does not overwrite formal topic facts. `evaluation_mode=SHADOW` and an explicit
policy/calculation version make the boundary auditable.

## Stage semantics and state machine

The five frozen stages are `SPROUTING`, `FERMENTING`, `MAIN_RISE`, `MATURE`,
and `DECLINING`, mapping respectively to ???????????????????????????????
????????? Ordinary candidate changes require confirmation and hold the
previous stage. Strong high-confidence structure may jump to MAIN_RISE or
DECLINING. MAIN_RISE ??MATURE ??MAIN_RISE re-entry is legal and resets Day N.
MATURE requires prior MAIN_RISE/MATURE context plus divergence/consolidation;
DECLINING requires structural weakening, not a single lower return.

Transition guardrails:

| Transition | Rule |
|---|---|
| Any ordinary candidate change | Legal only after the configured confirmation streak and minimum confidence. |
| Any stage ??`MAIN_RISE` | Legal after confirmation, or an explicit strong jump with high breadth/average change. |
| `MAIN_RISE`/`MATURE` ??`MATURE` | Legal only with prior main-rise context and consolidation/divergence evidence. |
| Any stage ??`DECLINING` | Legal after decline confirmation, or strong persistent weak ratio/negative average. |
| `MAIN_RISE` ??`SPROUTING` without broad weakness | Not promoted; evidence is held until the candidate is confirmed. |
| Missing/insufficient data ??new stage | Illegal; previous stage is held with an internal insufficient-data status. |

## Evidence and limitations

Leadership reports whether an approved role semantic exists. With current V2
data it is false and the strongest observed member is labelled as a proxy.
Diffusion records positive breadth and coverage. Group Strength records average
change and strong breadth. Divergence/Decay records weak ratio and divergence
signal. Persistence records prior stage/candidate/streak/date. Coverage and
sample confidence are separate so small populations do not look fully reliable.
Score/Grade, News/Radar, and unapproved leader sets remain supporting or absent
and never force a stage.

## Provisional/Tunable policy values

All values live in `LifecyclePolicy` and are not PM-frozen commercial rules:

| Parameter family | Initial value |
|---|---:|
| Minimum observed members / minimum coverage | 3 / 60% |
| Sample confidence full count | 10 members |
| Strong/weak member classification | ??.0% / ???4.0% |
| Sprouting leader proxy / max positive breadth | 4.0% / 45% |
| Fermenting positive breadth / average change | 45??8% / ??.5% |
| Main rise positive / strong breadth / average | ??0% / ??5% / ??.5% |
| Mature positive / strong breadth / average | 40??5% / ??5% / ??.25% |
| Declining positive / weak ratio / average | ??5% / ??5% / ???0.5% |
| Ordinary / decline confirmation | 2 / 2 trading days |
| Strong jump confidence / positive / strong / average | 70% / 82% / 45% / 3.0% |
| Strong decline confidence / weak / average | 70% / 60% / ??.0% |
| Minimum transition confidence | 30% |

These are calibration seeds only. A new policy version is required to change
them; no threshold is scattered through the decision logic.

## Shadow persistence and replay

`0027_task_be_021_topic_lifecycle_results.py` adds the result table with a
unique `(topic_id, evaluation_date, policy_version, evaluation_mode)` identity,
topic/date indexes, JSON evidence groups, and policy/calculation lineage. A
retry with the same identity leaves the immutable evidence unchanged; a
conflicting result fails and requires a new policy version. The CLI supports one
date or ascending replay of available topic snapshot dates.

The current production database has no snapshot dates/accepted observations, so
replay returns `BLOCKED_BY_DATA`/`WAITING_FOR_FORMAL_OBSERVATIONS` and does not
manufacture stages.

## FastAPI and frontend integration

`TopicLifecycleRead` now includes nullable current/history fields plus evaluation
date, candidate/previous stage, transition decision/reason, policy version,
evidence, and confidence. `/api/v2/topics` and topic detail read the latest
shadow results; absent or migration-not-yet-applied lifecycle storage safely
returns `NOT_AVAILABLE`. The frontend's formal API source uses these values;
it no longer calls preview lifecycle derivation for formal topics. Preview data
remains explicitly preview-only.

## Tests and verification

- Lifecycle deterministic fixtures: 13 passed (sprouting, fermenting, main rise,
  mature, declining, small sample, low data, re-entry, trading-day Day N,
  illegal-jump rejection, and deterministic replay).
- Existing V2 snapshot/freeze tests: 5 passed.
- Lifecycle/snapshot/freeze/observation targeted suite: 22 passed.
- Frontend lifecycle integration tests: 2 passed; frontend production build passed.
- Full backend suite: 247 passed, 31 skipped, 36 failed. The failures are
  pre-existing environment/source-shape failures in research fixtures,
  governance paths, and unrelated phase bundles; no lifecycle-targeted test
  failed. PostgreSQL integration was skipped because no test database URL was
  available.
- The broad frontend source-shape suite is 55 passed / 15 failed (including the
  two new lifecycle checks); those
  failures are unrelated baseline expectations for older page copy/routes.
- Python 3.12 compile check passed for the V2 source and migration.
- Targeted Ruff checks for all lifecycle files and tests passed. A broad Ruff
  run still reports pre-existing line-length findings in the older read-model,
  schema, and canonical-observation test files; no new lifecycle file is among
  those findings.

## Runtime/API/frontend impact

The additive migration and nullable API fields preserve the formal catalog when
lifecycle data is missing. No frontend page is allowed to infer lifecycle from
Grade, Score, direction, news, or constituent percentages. No Opportunity or
Recommendation Engine integration was added.

## Production activation safety

Production activation remains explicitly off. The remote service must first run
the new Alembic migration, ingest accepted formal observations, produce topic
snapshots, and pass PM evidence review. Until then, API lifecycle is unavailable
or pending and the formal frontend remains fail-closed.

## PM calibration checklist

1. Confirm official effective-dated role/leader metadata or approve the proxy.
2. Supply multiple formal trading dates with complete lineage and holidays.
3. Review representative shadow cases for all five stages and mark expected
   transitions, jumps, and re-entry.
4. Tune policy values by creating a new policy version; do not rewrite old rows.
5. Approve a separate production activation task only after replay evidence and
   API/Sites reconciliation pass.

## Files modified

- `services/api/src/topicpilot_api/topic_lifecycle_engine.py`
- `services/api/src/topicpilot_api/topic_lifecycle_cli.py`
- `services/api/src/topicpilot_api/topic_snapshot_engine.py`
- `services/api/src/topicpilot_api/live/post_close.py`
- `services/api/src/topicpilot_api/orm/lifecycle.py` and ORM registry
- `services/api/src/topicpilot_api/production_read_model.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/alembic/versions/0027_task_be_021_topic_lifecycle_results.py`
- `services/api/tests/test_topic_lifecycle_engine.py`
- `services/api/tests/test_topic_lifecycle_contract.py`
- frontend `topic-api.ts`, `TopicListPage.tsx`, `TopicDetailPage.tsx`
- `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md`

## Final markers

```text
LIFECYCLE_PRODUCT_DEFINITION = FROZEN
LIFECYCLE_STAGE_SEMANTICS = FROZEN
LIFECYCLE_ARCHITECTURE = FROZEN
LIFECYCLE_TRANSITION_PHILOSOPHY = FROZEN
LIFECYCLE_THRESHOLDS = PROVISIONAL_TUNABLE
LIFECYCLE_SHADOW_ENGINE = IMPLEMENTED
LIFECYCLE_PRODUCTION_ACTIVATION = NO
NEXT_TASK_MODIFIED = NO
```

## Completion audit addendum

### Existing Design Audit

The prior design already separated TopicSnapshot aggregation from the formal
read model and treated Grade/Score as deferred. No existing production lifecycle
authority was found; the new result table is therefore additive and shadow-only.

### Existing Code Audit

The implementation audit covered ORM models, migrations through `0024`, canonical
observation selection, effective-dated membership, live tracking universe,
snapshot engine, FastAPI serializers/read model, post-close orchestration,
frontend Topic API, Topic List/Detail pages, tests, product specs, architecture
reports, and work-log entries. The engine reuses these authorities and does not
invent topic roles, scores, news signals, or a parallel price source.

### Architecture Reconciliation

`canonical_observations (accepted DAILY_BAR)` -> `topic_snapshots` and effective
tracked membership -> `TopicLifecycleEngine` -> append-only
`topic_lifecycle_results` -> FastAPI V2 Topic read model -> Sites. The lifecycle
table is not a replacement for TopicSnapshot and is never read by the frontend
as a client-derived fallback.

### Lifecycle State Machine

Stages are ordered `SPROUTING` -> `FERMENTING` -> `MAIN_RISE` -> `MATURE` ->
`DECLINING`. The persisted previous stage, candidate stage, candidate streak,
stage entry date, and trading-day count are carried into each evaluation.
Ordinary transitions move at most one adjacent stage after confirmation;
non-adjacent transitions are held unless the strong-jump/strong-decline guard
is satisfied. `MATURE` -> `MAIN_RISE` is legal re-entry and resets Day N.

### Transition Rules

`INSUFFICIENT_DATA`, low confidence, no candidate, and illegal jumps hold the
previous final stage. A normal candidate requires the configurable confirmation
streak; a strong structure signal may transition immediately. Declining has its
own confirmation requirement and stronger structural weakening thresholds.
There is no automatic stage promotion from Score/Grade, news, or a single-day
return.

### Explainability / Evidence Model

Every persisted result records leadership (role-aware or explicit proxy),
diffusion (positive breadth and coverage), group strength (average and strong
breadth), divergence/decay (weak ratio and divergence signal), persistence
(previous state/streak/date), sample confidence, transition decision/reason,
policy version, calculation version, and evaluation mode. Missing fields remain
null; `INSUFFICIENT_DATA` is an internal status, not a sixth user-facing stage.

### Historical Replay / Calibration

`topicpilot-lifecycle --replay` walks distinct formal TopicSnapshot trading dates
in ascending order and is deterministic for a fixed policy. Current live replay
is `BLOCKED_BY_DATA` because no accepted observations or snapshot dates exist.
Each successful run includes a `topicResults` array with stage, evidence,
confidence, and transition reason for every topic, not only an aggregate count.
Deterministic fixtures cover all five stage shapes, low coverage, confirmation,
jump, re-entry, trading-day Day N, illegal jump rejection, and repeatability.

### Snapshot Persistence

Migration `0027` is additive and has no destructive operation. The identity key
is `(topic_id, evaluation_date, policy_version, evaluation_mode)`; retries leave
the original as-of evidence unchanged, while conflicting same-key output raises
an error and requires a new policy version. The engine writes only `SHADOW`
rows and does not overwrite TopicSnapshot or formal topic semantics.

### FastAPI Integration

`TopicLifecycleRead` fields are nullable and backend-owned. The read model filters
to the active provisional policy version and catches a not-yet-applied migration
as `NOT_AVAILABLE`, preserving the 130-topic formal catalog. Post-close runs the
snapshot first and treats lifecycle failure as a diagnostic shadow failure rather
than failing the market snapshot.

### Frontend Integration

Production API responses render lifecycle only when `dataStatus` is
`SHADOW_AVAILABLE`; otherwise the Topic List/Detail surfaces an explicit pending
state. Preview lifecycle remains available only for preview resources and is
never substituted into a formal API response. No frontend lifecycle derivation
from Grade, Score, direction, news, or constituent percentages was added.

### Production Activation Status

Activation is `WAITING_FOR_FORMAL_OBSERVATIONS`. The code path is integrated but
the deployed Render service has not received the migration or a lifecycle
shadow run, and no formal stage is claimed from the current empty snapshot state.

The public Render service was read-only audited on 2026-08-12: health/readiness
were `200`, the formal catalog returned 130 topics and 507 instruments, and the
live topic-snapshot endpoint returned zero rows. No deploy, write, or activation
was attempted during this task.

### Production Safety Verification

The combined migration head is `0027_task_be_021_topic_lifecycle_results`; compile,
targeted lint, deterministic tests, frontend lifecycle tests, and frontend build
passed. Live verification was read-only. No production database write, deploy,
frontend activation flag, or semantic overwrite was performed.

### Documents Updated

The lifecycle product spec, architecture documentation, AI worklog, work-order
record, and this production-integration report were updated incrementally. The
actual `NEXT_TASK` file was not modified.

### Known Issues

The live environment has no accepted price observations/topic snapshots yet;
therefore no historical representative topics can be reported. Formal role/leader
metadata is absent in the observed relation payload and the engine records a
max-change proxy. PostgreSQL integration requires a configured test database.

### Risks / Technical Debt

All thresholds are provisional and must be calibrated against PM-labelled replay
cases. Broad legacy test failures remain outside this task. A future deployment
must apply the additive migration and perform observation ingestion before any
production semantic activation is considered.

### Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Architecture reconciliation | PASS | Shared canonical snapshot/evidence path and separate shadow table |
| Engine/state machine | PASS | 13 deterministic lifecycle tests, including legal jump guard |
| Explainability | PASS | Five evidence groups, confidence, persistence, reason, versions |
| Snapshot persistence | PASS | Additive `0027`, unique identity, immutable retry behavior |
| FastAPI contract | PASS | Nullable backend-owned fields and migration-safe read model |
| Frontend contract | PASS | Formal-only shadow rendering and explicit pending state |
| Historical replay | BLOCKED_BY_DATA | Live formal snapshot dates = 0 |
| Production activation | WAITING_FOR_FORMAL_OBSERVATIONS | No deploy/write/activation performed |

### Suggested NEXT_TASK (report-only; actual NEXT_TASK unchanged)

Ingest a bounded set of accepted formal trading-day observations, run the
shadow replay, and collect PM labels for all five stages plus jump/re-entry and
insufficient-data cases. Keep this as a separate calibration/observation task;
Recommendation or Opportunity Engine integration remains out of scope.
