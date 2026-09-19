# SUPERSEDED BY DEC-04 ROLE-BASED IMPORTANCE V1

This historical closeout is preserved as audit evidence for the prior Model B
review boundary. It is not the current D001 policy or runtime status. The
current reconciliation and implementation state are recorded in
`docs/reports/TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002/dec-04-role-based-importance-v1.md`.

# TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002

## Executive Summary

`TASK_STATUS=BLOCKED` and `M1_COMPLETE=NO`. The task applied DEC-01 through
DEC-04 at the evidence/reconciliation boundary and stopped before any runtime,
schema, database, deployment, or Production business-state mutation.

DEC-04's required historical reconciliation is complete. The repository's
formal D001/Score evidence supports `MODEL_B`: approved/effective Structural
Role `CORE` rows are the candidate universe, while the Score consumer requires
a separately Owner-reviewed selected CORE subset with per-selected-member
importance. The formal role namespace is `REPRESENTATIVE/CORE/RELATED`, not
`LEAD/CORE/RELATE`; no formal `LEAD -> 1.00`, `CORE -> 0.75`, or
`RELATE -> 0.25` mapping was recovered. The current legal Score-consumer
values remain `1.00/0.75/0.50`, but they are not applied automatically from
Structural Role.

The current Owner position also resolves two prior over-assumptions: member
order has no product-policy meaning because the recovered Score formula does
not depend on order, and no additional fixed projection minimum or maximum is
required by the formula. A canonical stable identifier may be used only for
deterministic persistence/readback. The generated artifact is therefore an
Owner Review Draft, not formal runtime authority. All rows remain pending, so
execution stops at `D001_OWNER_ROW_REVIEW_REQUIRED`.

## Owner Decisions Applied

| Decision | Applied state | Evidence |
|---|---|---|
| DEC-01 | `APPROVED_A`; deterministic materialization permitted only from proven authority | Owner clarification says pre-materialized rows are not required when the approved contract and derivation are deterministic. |
| DEC-02 | `APPROVED_A`, implementation not reached | Existing Lifecycle V1.3 parameters remain unchanged; no activation was attempted without the blocked Score/Topic input chain. |
| DEC-03 | `APPROVED_FORMAL_OPPORTUNITY_REMAINS_IN_M1`, implementation not reached | Formal Opportunity remains in M1, but its frozen upstream Topic/Score/Grade/Lifecycle inputs cannot be proven complete. |
| DEC-04 | `APPROVED_A`; `MODEL_B` reconciliation and draft generation complete | Formal D001 evidence proves a separate selected CORE subset and per-selected-member importance; role-to-weight mapping is not formalized. Review is required before activation. |

No existing decision was reopened. The clarification was reconciled against
the existing D001 contract, Score code, migration/schema, tests, research-only
Leader Set evidence, and Lifecycle shadow path. The remaining gate is row-level
Owner review, not a new policy-design decision.

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

The decisive missing authority is now the Owner-reviewed projection row
artifact. The repository contract is deterministic enough to enumerate
formal CORE candidates, but it does not contain explicit approved D001 rows
or recovered human decisions for inclusion and importance. The current
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
D001_MEMBER_SELECTION_RULE_DEFINED=YES_OWNER_EXPLICIT_MODEL_B
D001_IMPORTANCE_RULE_DEFINED=YES_SELECTED_MEMBER_OWNER_REVIEW_ALLOWED_VALUES
D001_TIE_BREAK_RULE_DEFINED=NO_PRODUCT_POLICY_ORDER_CANONICAL_TECHNICAL_ONLY
D001_AS_OF_RULE_DEFINED=YES
D001_MISSING_INPUT_BEHAVIOR_DEFINED=YES_FAIL_CLOSED
D001_RUNTIME_ARTIFACT_PREEXISTED=NO
D001_RUNTIME_ARTIFACT_REQUIRED=YES
D001_MATERIALIZATION_CLASS=OWNER_REVIEW_DRAFT_GENERATION
D001_OWNER_ROW_REVIEW_REQUIRED=YES
NEW_OWNER_POLICY_DECISION_REQUIRED=NO
```

## D001 Runtime Projection

`D001_POLICY_APPROVED=YES`.

`D001_RUNTIME_ARTIFACT_READY=NO`.

`D001_AS_OF_READY=NO`.

`D001_READBACK_READY=NO`.

The existing `TopicScoreProjection` schema and resolver are suitable for the
future materialized artifact. They intentionally do not select members or
calculate importance. The generated draft only enumerates approved CORE
candidates and carries no formal inclusion or importance decisions. No runtime
selector or Structural Role-to-importance inference was introduced.

## DEC-04 Semantic Reconciliation

The required reconciliation searched the current canonical repository and
relevant history across Structural Role artifacts/schemas, D001 and Score
contracts, migrations, tests, research/governance reports, and the Lifecycle
shadow path.

```text
STRUCTURAL_ROLE_VALUES=REPRESENTATIVE,CORE,RELATED
HISTORICAL_ROLE_WEIGHT_EVIDENCE=NO_FORMAL_LEAD_CORE_RELATE_ROLE_WEIGHT_MAPPING_RECOVERED
LEAD_WEIGHT=UNPROVEN
CORE_WEIGHT=UNPROVEN
RELATE_WEIGHT=UNPROVEN
IMPORTANCE_IS_ROLE_PROJECTION=NO
D001_SCORE_MEMBER_UNIVERSE=APPROVED_EFFECTIVE_NON_SUPERSEDED_STRUCTURAL_ROLE_CORE_ROWS
D001_REQUIRES_SEPARATE_CORE_SUBSET=YES
D001_REQUIRES_PER_CORE_IMPORTANCE=YES_FOR_SELECTED_PROJECTION_MEMBERS
ORDER_AFFECTS_SCORE=NO
FIXED_MIN_REQUIRED_BY_FORMULA=NO
FIXED_MAX_REQUIRED_BY_FORMULA=NO
MODEL_CLASSIFICATION=MODEL_B
```

Evidence reconciliation:

| Evidence | Recovered meaning |
|---|---|
| `docs/architecture/TOPIC_DERIVED_INTELLIGENCE_DEFINITION_AND_PUBLICATION_AUTHORITY_CLOSURE.md` Addendum G and `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002.md` | D001 is canonicalized as approved effective CORE candidates -> an explicit bounded CORE subset -> Score consumer metadata; importance values are `1.00/0.75/0.50` and are explicitly not a Structural Role taxonomy. |
| `services/api/src/topicpilot_api/topic_engine/production_policy.py`, `score_projection.py`, ORM, migration 0031, and focused tests | Score receives explicit `LeaderDefinition(member_id, importance)` / selected projection members; the validator accepts only `0.50/0.75/1.00`, requires selected members to resolve as CORE, and provides no member selector or role-weight mapping. |
| `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json` | The formal role values are `REPRESENTATIVE`, `CORE`, and `RELATED`; 650 approved CORE rows are candidates, not D001 INCLUDE decisions. |
| `C:\Users\acer\.codex\worktrees\c3a0\題材領航\reports\WS1-AUX-507-STOCK-STRUCTURAL-ROLE\final_owner_approved_structural_role_authority_candidate_post_c2_20260819.tsv` | Useful historical candidate evidence, but every row has `proposal_state=PROPOSAL_ONLY_NON_AUTHORITY`; 822 rows include 720 `owner_reviewed=NO`, and its populated final importance contradicts a fixed role mapping (`CORE` has `1.00` and `0.75`; `REPRESENTATIVE` has `1.00`; `RELATED` has `0.50`; no `0.25`). |
| `docs/research/leader-set-research.v2.md` and `fixtures/research/leader_set_pm_review_shortlist.v1.csv` | `1.00/0.75/0.50` appear as candidate/research proposals, explicitly `CANDIDATE/NEEDS_REVIEW/NOT APPROVED`; no formal `0.25` role-weight mapping is present. |
| `services/api/src/topicpilot_api/topic_lifecycle_v1.py` and `topic_lifecycle_engine.py` | `LEAD/CORE/RELATED` normalization and `0.70/0.30` breadth authority weights belong to the shadow Lifecycle path; they are not D001 Score authority and do not establish `LEAD -> 1.00`, `CORE -> 0.75`, `RELATE -> 0.25`. |
| `docs/DAILY_PROGRESS.md` PM-001/PM-002 | CORE population and a semi-static Leader Set are conceptually separated; exact Leader Set weights and mechanics were recorded as `NEEDS PM`, not as a role-to-importance projection. |

Therefore the Owner recollection does not override or contradict the current
D001 evidence: it is an unproven historical hypothesis for this consumer.
The adjacent Lifecycle role path is a separate shadow consumer, not a reason
to create a second CORE hierarchy or map all Structural Roles into Score.

## D001 Owner Review Draft

The draft was generated only after the reconciliation above. It is explicitly
`DRAFT_NOT_FORMAL_AUTHORITY`; no Score runtime may consume it. Each formal CORE
candidate remains `PENDING_OWNER_REVIEW` for inclusion and importance, and the
no-CORE Topic remains fail-closed.

```text
D001_REVIEW_TOPICS=107
D001_REVIEW_CANDIDATES=650
D001_TOPICS_FULLY_RECOVERED_FROM_EXISTING_HUMAN_AUTHORITY=0
D001_TOPICS_REQUIRING_OWNER_REVIEW=107
D001_TOPICS_WITH_NO_CORE_CANDIDATES=1
```

Artifacts:

- `docs/reports/TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002/d001-owner-review-draft/d001-owner-review-draft.json`
- `docs/reports/TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002/d001-owner-review-draft/d001-owner-review-draft.csv`
- `docs/reports/TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002/d001-owner-review-draft/d001-owner-review-draft.md`

The draft records no additional Owner-imposed minimum or maximum projection
size. Canonical identifier ordering is technical persistence/readback only;
it does not affect importance, Score, Grade, Lifecycle, ranking, or
Opportunity. Review must set final INCLUDE/EXCLUDE and importance before a
versioned formal projection can be materialized.

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
authority-to-Opportunity dependency chain cannot run until the D001 Owner
Review Draft is approved and materialized as formal projection authority.

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

Only one earliest blocker is returned. It is a precise Owner row-review
boundary, not a request to infer or manually edit runtime database rows:

```text
EARLIEST_REMAINING_BLOCKER=D001_OWNER_ROW_REVIEW_REQUIRED
BLOCKER_LAYER=FORMAL_AUTHORITY_OWNER_REVIEW
BLOCKER_CAUSE=DEC-04 proves the current D001 model is a separate Owner-reviewed CORE subset with per-selected-member importance; no explicit approved rows or recovered human decisions exist. All 107 Topics remain pending, and one Topic has no formal CORE candidate. The draft is not runtime authority.
NEW_OWNER_POLICY_DECISION_REQUIRED=NO
TECHNICAL_ACCESS=AVAILABLE_FOR_REPOSITORY_WORK; PRODUCTION_DATABASE_AND_DEPLOYMENT_SECRETS_NOT_PRESENT_IN_THIS_ENVIRONMENT
OWNER_ACTION_REQUIRED=YES_REVIEW_AND_APPROVE_OR_EDIT_THE_D001_OWNER_REVIEW_DRAFT
NEXT_SAFE_ACTION=After Owner row review approval, materialize a versioned formal D001 projection with exact lineage and read back the projection and Leader Set; then continue Score/Grade/Lifecycle/Topic/Today/Opportunity activation.
```

### Owner action

Review the machine-readable and human-readable draft. For each formal CORE
candidate, set final `INCLUDE` or `EXCLUDE`; for included members, set one
approved importance value from the current D001 contract. Do not map
importance from Structural Role unless a future Owner decision changes the
formal model. The reviewed artifact must then receive its own version,
effective date, approval reference, source authority binding, correction/
supersession identity, and lineage hash before runtime activation.
