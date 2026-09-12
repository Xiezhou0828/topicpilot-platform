# WS1 Lifecycle V1 Identity-Aware State Machine — Formal Closure

Task: `TASK-WS1-LIFECYCLE-V1-IDENTITY-AWARE-STATE-MACHINE-IMPLEMENTATION-20260823`

Status: `IMPLEMENTATION_COMPLETE / HISTORICAL_RECONSTRUCTION_BLOCKED_BY_LOCAL_DB_UNAVAILABLE / PRODUCTION_NOT_PROVEN`

## Closure result

The five Owner-approved stages remain unchanged:

`SPROUTING → FERMENTING → MAIN_RISE → MATURE → DECLINING`

The implementation now evaluates identity-aware Lead/Core/Related evidence, persists deterministic state memory for Main Rise segments and price progression, and keeps the existing raw Strength evidence vector separate from Lifecycle. The prior `topic-lifecycle-policy.provisional.1` definition was not edited; V1 is an additive, separately versioned contract with the same numeric boundaries plus the approved state-machine semantics.

The implementation is in the isolated E: worktree branch. No push, deploy, merge, production database mutation, backfill, replay against production, or NEXT_TASK change was performed.

## Production/runtime conclusion

The previously supplied production read-only probe remains the only production evidence available in this task:

- `/api/v2/topics`: 130 topics; 130/130 `INSUFFICIENT_DATA`; `currentStage=null`.
- API health/readiness returned 200.
- Production runtime did not expose Git SHA or image digest.
- Production formal PIT materializer lineage, scheduler execution, migration 0032/0033 state, and persisted stage-bearing shadow rows were not directly proven.

Therefore the primary production root cause is classified as **FAIL-CLOSED INPUT/PROVENANCE CHAIN NOT PROVEN**. The symptom is compatible with missing formal inputs, an unexecuted runner, fail-closed price/identity evidence, or a stale/read-model selection, but the first broken layer cannot be named safely from the available evidence. This is not evidence that thresholds should be lowered. Deployment/release provenance remains the separate WS4 blocker.

The isolated 2026-08-12 evidence (`92 snapshots / 848 facts / 847 exact price matches`) demonstrates that a bounded shadow input set existed in isolation; it is not production evidence and is not promoted by this task.

## Required answers

| Question | Answer |
|---|---|
| Main root cause of production 130/130 insufficient | Formal Lifecycle input/runtime provenance chain is not proven; production read model is fail-closed at insufficient data. |
| Data missing, runner missing, fail-closed, API issue, or deployment lag? | Exact first layer `UNKNOWN`; observed API symptom is `INSUFFICIENT_DATA`. Deployment lag is a separate WS4 blocker, not a proven explanation for the input failure. |
| Latest legally stage-bearing production trading date | `UNKNOWN / NOT_PROVEN`; 2026-08-12 is isolated non-production evidence only. |
| Any production stage-bearing shadow row? | `NOT_PROVEN`; API exposed none, but direct DB row evidence was not available. |
| Modify Lifecycle policy? | `NO`. No threshold was lowered and no Strength contract was changed. |
| DB/schema/runtime repair? | Additive schema support is required: migration 0033 for role-bearing facts and V1 state memory. Production application of it is `NOT_PROVEN`; no mutation was executed. Runtime/scheduler provenance still needs a read-only verification. |
| Next smallest safe WS1 action | Read-only production verification of migration 0033, runtime SHA/image, scheduler last-run, formal snapshot/fact counts, canonical price-date coverage, lifecycle persistence rows, and API selection; then a non-production deterministic canary. |

## Governance

`WS1_ONLY=YES`; `E_DRIVE_ONLY=YES`; `C_DRIVE_NEW_ARTIFACTS_CREATED=NO`; `LIFECYCLE_V1_IMPLEMENTED=YES`; `LIFECYCLE_POLICY_CHANGED=NO`; `STRENGTH_CHANGED=NO`; `STRENGTH_SCORE_CREATED=NO`; `HISTORICAL_RECONSTRUCTION=REQUIRED_BUT_NOT_RUN`; `LOOKAHEAD=NO`; `DETERMINISTIC_REPLAY=UNIT_PASS`; `OWNER_VALIDATION_READY=YES`; `WS3_FULL_BACKTEST=NO`; `PRODUCTION_DB_MUTATION=NO`; `BACKFILL=NO`; `RETROSPECTIVE_REPLAY=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`.
