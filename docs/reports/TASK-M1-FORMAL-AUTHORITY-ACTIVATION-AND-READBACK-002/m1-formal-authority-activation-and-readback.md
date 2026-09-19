# TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002

## Executive Summary

`TASK_STATUS=BLOCKED` and `M1_COMPLETE=NO`. The task was authorized to apply
DEC-01, DEC-02, and DEC-03, but execution stopped at the first genuine safety
boundary before any runtime, schema, database, deployment, or Production
business-state mutation.

The Owner clarification changes the classification of the absent runtime rows:
the rows do not need to pre-exist. Engineering may materialize them if the
approved D001 contract deterministically defines the derivation. The recovered
contract does not define the required member-selection and importance
derivation semantics. It says `BOUNDED_CORE_SUBSET` and
`AI_ASSISTED_PROPOSAL_PLUS_OWNER_REVIEW`, prohibits runtime AI and fixed Top-N,
and permits `1.00/0.75/0.50`, but does not specify which approved CORE members
enter each Topic's subset or which permitted importance each member receives.
It also defines no tie-break, minimum/maximum subset size, or deterministic
ordering rule. Those are formal analytical semantics, not implementation
convenience.

Therefore `D001_MATERIALIZATION_CLASS=OWNER_POLICY_GAP` and
`NEW_OWNER_POLICY_DECISION_REQUIRED=YES`. No materializer, Score writer,
Lifecycle activation, Opportunity provider, deployment, or Production state was
attempted. Selecting all CORE, alphabetical order, market data, or arbitrary
weights would violate the clarification's hard boundary.

## Owner Decisions Applied

| Decision | Applied state | Evidence |
|---|---|---|
| DEC-01 | `APPROVED_A`; contract exists, materialization semantics incomplete | Owner clarification says pre-materialized rows are not required. D001 still lacks the exact member-selection and importance derivation needed to generate them deterministically. |
| DEC-02 | `APPROVED_A`, implementation not reached | Existing Lifecycle V1.3 parameters remain unchanged; no activation was attempted without the blocked Score/Topic input chain. |
| DEC-03 | `APPROVED_FORMAL_OPPORTUNITY_REMAINS_IN_M1`, implementation not reached | Formal Opportunity remains in M1, but its frozen upstream Topic/Score/Grade/Lifecycle inputs cannot be proven complete. |

No existing decision was reopened. The clarification exposes a new precise
policy gap inside the already approved D001 contract; no safe engineering
choice can fill it.

## Canonical Base / Lineage

| Field | Value |
|---|---|
| Development worktree | `C:\Users\acer\Desktop\題材領航\topicpilot-platform-m1-final-closure` |
| Current branch | `codex/task-m1-formal-pipeline-final-closure-001` |
| Development canonical base | `0050d6d25a34938fa35225dade8541be9051d20c` |
| Previous Today fail-closed change | `c4405351f921ddd70089ec00a7c299ea97d9a768` |
| Recovery report | `docs/reports/TASK-M1-FORMAL-AUTHORITY-POLICY-DESIGN-RECOVERY-001/` |
| `origin/main` observed | `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| Protected Owner checkout | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Owner checkout HEAD before/after | `02d3086183d1c582bb6c66c4c316340ccce3fa97` / unchanged |
| Owner checkout dirty count before/after | `153` / unchanged |
| Production API SHA | `b14d5708d4cda0cad2341154bc4495b64cf472ec` (previous governed evidence) |
| Production Worker SHA | `45b1fa198db34471ce03f29a9184d8236299d525` (previous governed evidence) |
| Production Web version | `UNPROVEN` (previous governed evidence) |
| Current Alembic revision | `0042_task_fund_b_stock_institutional_flow_forward` |
| Canonical single head | `YES` by repository lineage; no migration was added |

## Formal Authority Artifacts

The following artifacts are present and were treated as authoritative only for
the scopes they actually prove:

- Score/Grade policy approval: `topic-b2-layer2-policy-v1`, Owner
  `topicpilot-owner`, effective `2026-09-15`, strict approval record under
  `docs/reports/TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001-20260915/`.
- Structural Role authority:
  `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json`,
  1,160 approved rows, effective `2026-08-24`.
- D001 policy: approved and canonicalized bounded CORE subset policy, with no
  fixed Top-N, no runtime AI selection, and importance only `1.00/0.75/0.50`.
- Runtime resolver/schema: migration 0031 and the existing fail-closed
  Structural Role / Score Projection resolvers.

The decisive missing authority is not a pre-generated artifact; it is the
derivation rule that would make materialization deterministic. The current
evidence explicitly records:

```text
score_projection_readiness.formal_artifact_present=false
projection_records_populated=0_NOT_YET_POPULATED
governed_leader_set_adapter_state=IMPLEMENTED_AND_VALIDATED_DETERMINISTIC_COMPATIBILITY_ONLY
```

The Owner clarification requires the following immediate classification:

```text
D001_CONTRACT_EXISTS=YES
D001_CONTRACT_FORMALLY_APPROVED=YES
D001_SCHEMA_EXISTS=YES
D001_ALLOWED_FORMAL_INPUTS_DEFINED=YES
D001_MEMBER_SELECTION_RULE_DEFINED=NO
D001_IMPORTANCE_RULE_DEFINED=NO_FOR_PER_MEMBER_ASSIGNMENT
D001_TIE_BREAK_RULE_DEFINED=NO
D001_AS_OF_RULE_DEFINED=YES
D001_MISSING_INPUT_BEHAVIOR_DEFINED=YES_FAIL_CLOSED
D001_RUNTIME_ARTIFACT_PREEXISTED=NO
D001_RUNTIME_ARTIFACT_REQUIRED=YES
D001_MATERIALIZATION_CLASS=OWNER_POLICY_GAP
NEW_OWNER_POLICY_DECISION_REQUIRED=YES
```

## D001 Runtime Projection

`D001_POLICY_APPROVED=YES`.

`D001_RUNTIME_ARTIFACT_READY=NO`.

`D001_AS_OF_READY=NO`.

`D001_READBACK_READY=NO`.

The existing `TopicScoreProjection` schema and resolver are suitable for the
future materialized artifact. They intentionally do not select members. A
materializer can be implemented only after the Owner defines the missing
selection/importance semantics or supplies an approved deterministic rule
artifact; no runtime selector may be introduced.

## Leader Set Runtime Projection

`LEADER_SET_POLICY_APPROVED=YES`.

`LEADER_SET_RUNTIME_PROJECTION_READY=NO`.

`LEADER_SET_AS_OF_READY=NO`.

`LEADER_SET_READBACK_READY=NO`.

The compatibility adapter exists and is deterministic, but it can only adapt a
validated D001 projection. Leader Set was not introduced as a Lifecycle
prerequisite or a global Opportunity gate.

## Score Activation

Not reached. The Score evaluator, policy approval record, formal bridge,
fail-closed as-of binding, and missing/partial semantics exist in the tree, but
Score cannot be persisted or published without the exact D001 projection and
Leader Set input.

```text
SCORE_POLICY_FORMALLY_APPROVED=YES
SCORE_RUNTIME_AUTHORITY_READY=NO
SCORE_WRITER_READY=NOT_REACHED
SCORE_PERSISTENCE_READY=NOT_REACHED
SCORE_PUBLICATION_READY=NO
SCORE_READBACK_READY=NO
SCORE_FORMAL_READY=NO
```

## Grade Activation

Not reached. Grade remains downstream of the approved formal Score and its
existing thresholds; no threshold or unrelated historical grade system was
changed.

```text
GRADE_POLICY_FORMALLY_APPROVED=YES
GRADE_RUNTIME_READY=NO
GRADE_WRITER_READY=NOT_REACHED
GRADE_PERSISTENCE_READY=NOT_REACHED
GRADE_PUBLICATION_READY=NO
GRADE_READBACK_READY=NO
GRADE_FORMAL_READY=NO
```

## Lifecycle V1.3 Activation

Not reached. The recovered five-stage V1.3 contract and existing formal
publisher were preserved. DEC-02 was not used to infer missing Score inputs or
to promote the shadow engine.

```text
LIFECYCLE_POLICY_APPROVED=YES
LIFECYCLE_TRANSITION_AUTHORITY_READY=YES_ARTIFACT_POLICY_APPROVED_NOT_ACTIVATED
LIFECYCLE_RUNTIME_READY=NO
LIFECYCLE_WRITER_READY=NOT_REACHED
LIFECYCLE_PERSISTENCE_READY=EXISTING_FORMAL_SCHEMA_NOT_READ_BACK
LIFECYCLE_PUBLICATION_READY=NO
LIFECYCLE_READBACK_READY=NO
LIFECYCLE_FORMAL_READY=NO
```

## Derived Historical Baseline

No historical recomputation was run. The predecessor evidence records the
canonical market sequence current through `2026-09-18`; derived Score/Grade
cannot be safely materialized until the D001 authority input exists.

```text
DERIVED_BASELINE_START_DATE=NOT_DETERMINED
DERIVED_BASELINE_END_DATE=2026-09-18
DERIVED_RECOMPUTE_REQUIRED=YES_AFTER_D001_ARTIFACT
MARKET_DATA_REFETCH_REQUIRED=NO
```

## Topic Reconciliation

No Topic snapshots were changed or republished. Existing formal Topic
publication evidence remains through `2026-09-18`, but Score/Grade/Lifecycle
readiness was not extended by inference.

```text
FORMAL_TOPIC_DATE=2026-09-18
FORMAL_TOPIC_COUNT=EXISTING_EVIDENCE_NOT_RERUN
FORMAL_TOPIC_SCORE_READY=NO
FORMAL_TOPIC_GRADE_READY=NO
FORMAL_TOPIC_LIFECYCLE_READY=NO
FORMAL_TOPIC_DAILY_STATE_READY=NO_FOR_DERIVED_LAYERS
FORMAL_TOPIC_READBACK_READY=EXISTING_TOPIC_CONTRACT_ONLY
```

## Today Reconciliation

No Today state was mutated. The previous `c4405351` fail-closed behavior was
preserved: incomplete formal dependencies remain `PARTIAL` or `UNAVAILABLE`,
and are never reported as `FORMAL_ZERO`.

```text
TODAY_MARKET_CURRENT=PARTIAL_PER_PREVIOUS_PRODUCTION_EVIDENCE
TODAY_FORMAL_READY=PARTIAL
TODAY_SIGNALS_STATE=PARTIAL_WHEN_FORMAL_DEPENDENCIES_INCOMPLETE
```

## Formal Opportunity Authority Package

DEC-03 keeps Formal Opportunity in M1, but no package was activated because the
package must reference complete formal Topic/Score/Grade/Lifecycle inputs. The
existing frozen universe boundary, C1-C5, S1-S2, MLCC, FUND-C V1, Structural
Role, dedupe, multi-Topic provenance, D-1, and no-D+1 rules were not changed.

```text
OPPORTUNITY_AUTHORITY_READY=NO
OPPORTUNITY_AUTHORITY_VERSION=EXISTING_CONTRACTS_NOT_ACTIVATED
FULL_TOPIC_UNIVERSE_READY=NO_FOR_FORMAL_DERIVED_CONSUMPTION
```

## Formal Opportunity Provider

Not activated. The existing provider boundary correctly rejects shadow,
fixture, research, or an inactive canonical provider. It remains unsafe to
return `FORMAL_ZERO` before the full formal input chain is proven.

```text
OPPORTUNITY_PROVIDER_READY=NO
OPPORTUNITY_FORMAL_STATE=UNAVAILABLE_PROVIDER_INACTIVE
OPPORTUNITY_CANDIDATE_COUNT=NOT_READ
OPPORTUNITY_PROVENANCE_READY=NO
```

## Formal Opportunity Writer / Persistence

Not reached. No formal Opportunity row, candidate, or business-state record
was written.

```text
OPPORTUNITY_WRITER_READY=NOT_REACHED
OPPORTUNITY_PERSISTENCE_READY=NO
OPPORTUNITY_PUBLICATION_READY=NO
```

## Formal Opportunity API

The existing API remained fail-closed at the inactive-provider boundary. No
permanent design decision was made to retain HTTP 503; activation must happen
after the D001-dependent formal chain is supplied and validated.

```text
FORMAL_OPPORTUNITY_API_READY=NO
```

## Migration

No migration was required for this stopped execution. The existing canonical
Alembic chain remains unchanged at revision 0042, and no data was touched.

```text
MIGRATION_REQUIRED=NO_FOR_STOPPED_EXECUTION
MIGRATION_REASON=NO_SAFE_RUNTIME_INPUT_ARTIFACT_TO_ACTIVATE
PRE_MIGRATION_HEAD=0042_task_fund_b_stock_institutional_flow_forward
POST_MIGRATION_HEAD=UNCHANGED
CANONICAL_SINGLE_HEAD=YES
```

## Automation / Orchestration

No post-close orchestration was changed. The readiness-aware `POST_CLOSE`
boundary at or after `13:35 Asia/Taipei` and existing retry/resume/session
guards were preserved.

```text
POST_CLOSE_AUTOMATION_READY=EXISTING_MARKET_PATH_ONLY
AUTHORITY_PROJECTION_AUTOMATED=NO
SCORE_AUTOMATED=NO
GRADE_AUTOMATED=NO
LIFECYCLE_AUTOMATED=NO
TOPIC_AUTOMATED=NO_FOR_NEW_DERIVED_LAYERS
TODAY_AUTOMATED=EXISTING_FAIL_CLOSED_READ_MODEL
OPPORTUNITY_AUTOMATED=NO
NEXT_TRADING_DAY_AUTOMATION_READY=NO
```

## Focused Validation

The current task performed read-only verification of the predecessor evidence,
current lineage, migration list, and the complete workspace search for a
concrete D001 projection artifact. Existing predecessor validation remains the
applicable code evidence: structural-role/projection focused tests, formal
Score tests, Lifecycle tests, Ruff, compile, and migration offline checks had
passed in their respective governed tasks. No new code was changed here.

```text
FOCUSED_TESTS=NOT_RUN_CODE_UNCHANGED_FORMAL_AUTHORITY_BOUNDARY
FULL_BACKEND_TESTS=NOT_RUN
WEB_TESTS=NOT_RUN
RUFF=NOT_RUN_CODE_UNCHANGED
COMPILE=NOT_RUN_CODE_UNCHANGED
TYPESCRIPT=NOT_RUN
BUILD=NOT_RUN
OPENAPI_DRIFT=NOT_RUN
GIT_DIFF_CHECK=PASS_FOR_REPORT_WRITESET
```

## Regression Validation

No regression was introduced: there was no application, schema, API, Web,
scheduler, or database write set. Production and the protected Owner checkout
were not mutated.

## Governed Commits

This report is the only new work product for the stopped execution. The
governed report commit is recorded in the final machine-readable closeout after
commit. No implementation SHA is claimed.

```text
IMPLEMENTATION_SHA=NOT_CREATED
GOVERNANCE_SHA=RECORDED_AFTER_COMMIT
PUSHED_BRANCH=codex/task-m1-formal-pipeline-final-closure-001
REMOTE_SHA=RECORDED_AFTER_PUSH_IF_AVAILABLE
```

## Production Promotion

Not performed. Authorization existed, but safe promotion requires the missing
D001 derivation semantics first. No Production API, Worker, Web, database, or
business state was changed.

## Production Materialization

Not performed. No formal projection, Score, Grade, Lifecycle, Topic, Today, or
Opportunity materialization was attempted.

## Production Persisted Readback

Not performed for this task. Previous governed evidence remains the last known
Production identity and reports Opportunity provider inactivity. No writer log
or local artifact was presented as Production readback.

## Next Trading Day Automation Proof

Not proven. The existing market post-close path is preserved, but the complete
authority-to-Opportunity dependency chain cannot run without deterministic D001
projection derivation semantics.

## M1 Definition of Done

```text
HISTORICAL_MARKET_SEQUENCE_CURRENT=YES_THROUGH_2026-09-18
DAILY_CLOSE_FORMAL_READY=YES_EXISTING_PATH
POST_CLOSE_AUTOMATION_READY=NO_FOR_COMPLETE_FORMAL_CHAIN
D001_RUNTIME_AUTHORITY_READY=NO
LEADER_SET_RUNTIME_PROJECTION_READY=NO
SCORE_FORMAL_READY=NO
GRADE_FORMAL_READY=NO
LIFECYCLE_FORMAL_READY=NO
FORMAL_TOPIC_DAILY_STATE_READY=NO_FOR_DERIVED_LAYERS
TODAY_MARKET_CURRENT=PARTIAL
TODAY_FORMAL_READY=PARTIAL
FULL_TOPIC_UNIVERSE_READY=NO_FOR_FORMAL_DERIVED_CONSUMPTION
OPPORTUNITY_AUTHORITY_READY=NO
OPPORTUNITY_PROVIDER_READY=NO
FORMAL_OPPORTUNITY_API_READY=NO
FORMAL_OPPORTUNITY_PUBLICATION_READY=NO
FORMAL_PRODUCTION_READBACK_READY=NO
NEXT_TRADING_DAY_AUTOMATION_READY=NO
PRODUCTION_FORMAL_PIPELINE_READY=NO
OWNER_CHECKOUT_PRESERVED=YES
```

## Remaining Blocker

Only one earliest blocker is returned. It is a precise Owner policy boundary,
not a request to manually generate runtime rows:

```text
EARLIEST_REMAINING_BLOCKER=DEC-01_D001_MEMBER_SELECTION_AND_IMPORTANCE_DERIVATION_UNDEFINED
BLOCKER_LAYER=FORMAL_AUTHORITY_POLICY_SEMANTICS
BLOCKER_CAUSE=D001 contract/schema/allowed inputs/as-of/fail-closed behavior exist, but the approved contract does not define per-Topic bounded-subset membership selection, per-member importance assignment, tie-break/order, or minimum/maximum subset size. The existing rule explicitly prohibits runtime AI, fixed Top-N, all-CORE substitution, market-data ranking, and arbitrary weights.
NEW_OWNER_POLICY_DECISION_REQUIRED=YES
TECHNICAL_ACCESS=AVAILABLE_FOR_REPOSITORY_WORK; PRODUCTION_DATABASE_AND_DEPLOYMENT_SECRETS_NOT_PRESENT_IN_THIS_ENVIRONMENT
OWNER_ACTION_REQUIRED=YES_DEFINE_THE_MISSING_D001_DERIVATION_SEMANTICS_OR_SUPPLY_A_FORMALLY_APPROVED_RULE_ARTIFACT
NEXT_SAFE_ACTION=After the missing D001 semantics are approved, implement the deterministic materializer through existing migration-0031 models, validate Structural Role and as-of lineage, read back projection and Leader Set, then continue Score/Grade/Lifecycle/Topic/Today/Opportunity activation.
```

### Exact Owner decision required

1. **Unresolved policy fields:** per-Topic member-selection rule for the
   bounded CORE subset; per-member importance assignment; deterministic order
   and tie-break; minimum/maximum subset size. The existing contract already
   defines the candidate universe, legal importance values, effective dating,
   versioning, Owner review, no runtime AI, no fixed Top-N, and fail-closed
   behavior.
2. **Existing evidence:** D001 is formally approved and canonicalized, but its
   own text says the bounded subset is not all CORE, has no fixed count, and
   that the approved artifact contains selected members. The schema/resolver
   require explicit selected members and importance, while tests only validate
   the permitted values and lineage; no derivation algorithm exists.
3. **Option A (recommended):** approve a versioned, Owner-reviewed explicit
   D001 projection rule/artifact that supplies the selected CORE member IDs and
   `1.00/0.75/0.50` importance for each Topic and effective interval. This lets
   engineering materialize rows deterministically without inventing a runtime
   selector.
4. **Option B:** approve a new deterministic selection/importance algorithm
   with explicit subset bounds, ordering, tie-break, and effective-date rules.
   This requires a new D001 policy version and formal review because the current
   contract does not contain those semantics.
5. **Option C:** retain fail-closed behavior and defer D001 runtime activation;
   M1 remains blocked.
6. **Engineering recommendation:** Option A, because it preserves the
   approved bounded-subset meaning and avoids turning runtime engineering into
   an unapproved selector. If the Owner explicitly wants automated derivation,
   Option B must be versioned and approved before implementation.
7. **Consequences:** A unlocks deterministic materialization with no Score
   formula change; B adds a new governed policy and requires replay/lineage
   treatment; C changes no semantics but leaves Score, Grade, Lifecycle,
   Opportunity, Production readback, and automation proof blocked.
8. **Downstream work unlocked:** D001 projection writer/readback, Leader Set
   adapter/readback, formal Score/Grade writer and persistence, Lifecycle V1.3
   activation, targeted Topic/Today reconciliation, Formal Opportunity
   authority/provider/writer/API, deployment/canary, Production readback, and
   next-trading-day automation proof.
