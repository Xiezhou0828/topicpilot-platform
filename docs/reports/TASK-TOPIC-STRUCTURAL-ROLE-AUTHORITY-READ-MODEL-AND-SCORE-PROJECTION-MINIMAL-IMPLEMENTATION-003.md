# TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003

## Closure identity and authority boundary

| Field | Result |
| --- | --- |
| `TASK_ID` | `TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003` |
| `PREDECESSOR` | `TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002` |
| `CANONICAL_PRE_SHA` | `1acac134cebc994fdab350aeeb64fe5e997008bf` |
| `CANONICAL_POST_SHA` | `1597068099139ea9df03d6f2b944fb9b7a7f4267` |
| `SOURCE_BRANCH` | `codex/task-topic-structural-role-authority-score-projection-implementation-20260816` |
| `SOURCE_WORKTREE` | `C:\Users\acer\Documents\Codex\ws1-structural-role-authority-score-projection-implementation-20260816` |
| `WS1_P2B_D001_REOPENED` | `NO` |
| `FINAL_STATUS` | `COMPLETE` |
| `RELEASE_STATUS` | `NOT_RELEASE_CANDIDATE` |
| `PRODUCTION_VERIFICATION` | `NOT_PERFORMED` |

This task implements only the infrastructure explicitly routed by the
canonical D001 closure. It does not select members, create role/projection
data, redesign Score/Grade, publish an API, or activate a downstream lane.

## Implemented write set

### Structural Role Authority

`InstrumentTopicRelation` remains the sole role carrier. The additive
authority extension adds:

`structural_role`, `approval_state`, `authority_version`,
`source_artifact_id`, `source_artifact_hash`, `approval_reference`,
`correction_sequence`, `supersedes_authority_id`,
`superseded_by_authority_id`, and `lineage_hash`.

Legacy relation rows remain nullable/non-formal. No existing relation was
classified or rewritten.

### Score Projection V1

Migration `0031_task_topic_structural_role_score_projection` adds:

- `topic_score_projections`: approved projection identity, effective interval,
  approval reference, source authority version, projection lineage, and
  correction/supersession identity;
- `topic_score_projection_members`: explicit selected instrument, exact role
  authority binding/version, member lineage, and legal importance.

The database constraints accept only `1.00`, `0.75`, and `0.50`. The model is
append-only by correction/supersession identity and contains no selector or
runtime calculation.

### Resolvers and adapter

- `resolve_structural_role(..., read_mode="CURRENT")` excludes superseded
  authorities; `read_mode="HISTORICAL"` preserves the authority effective at
  the requested as-of date.
- `resolve_score_projection` validates the approved effective projection and
  every selected member against the same Structural Role Authority as-of.
- `build_governed_leader_set` performs deterministic representation mapping
  only. It cannot select members, change importance, inspect price/volume,
  Dynamic Leadership, Lifecycle, Opportunity, Recommendation, or Score output.

Missing, unapproved, ineffective, conflicting, superseded-current,
lineage-incomplete, non-CORE, authority-mismatched, or illegal-importance
inputs fail closed. Missing projection for Topic B does not block Topic A.

## 003F provenance reconciliation

The committed work order and implementation contract record
`PHASE-3.7-003F` as PM Approved and describe the same frozen mechanics used by
the existing non-activating evaluator. The referenced
`docs/reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md` was not present in
the committed canonical tree. An owner-untracked copy was observed with:

```text
SHA256=C304032F41BCA466B70C5F1919F239B52030E6F1D5D284506C63623F649AADDF
BYTES=6931
```

The content is consistent with the committed work-order references and
`production_policy.py`, but the repository has no committed digest, Git
provenance, or canonical attestation binding this untracked copy to the
original approval artifact. It is therefore not canonicalized, not consumed
as formal approval, and remains:

`BLOCKED_BY_COMMITTED_PM_APPROVAL_ARTIFACT_RECONCILIATION`

No look-alike approval document was created.

## Capability re-disposition

```text
WS1_P2B_D001_REOPENED=NO
STRUCTURAL_ROLE_VALUES=REPRESENTATIVE,CORE,RELATED
STRUCTURAL_ROLE_EXISTING_CARRIER=InstrumentTopicRelation
SECOND_ROLE_AUTHORITY_CREATED=NO
SCORE_PROJECTION_SELECTION=BOUNDED_CORE_SUBSET
FIXED_TOP_N=NO
RUNTIME_AI_SELECTION=PROHIBITED
IMPORTANCE_VALUES=1.00,0.75,0.50
GOVERNED_LEADER_SET_DISPOSITION=COMPATIBILITY_ADAPTER_OVER_STRUCTURAL_ROLE_AUTHORITY

STRUCTURAL_ROLE_POLICY_READY=YES
STRUCTURAL_ROLE_AUTHORITY_INFRASTRUCTURE_READY=YES
STRUCTURAL_ROLE_AS_OF_RESOLVER_READY=YES
SCORE_PROJECTION_POLICY_READY=YES
SCORE_PROJECTION_INFRASTRUCTURE_READY=YES
SCORE_PROJECTION_AS_OF_RESOLVER_READY=YES
GOVERNED_LEADER_SET_ADAPTER_READY=YES
PM_APPROVAL_ARTIFACT_READY=NO
GOVERNED_ROLE_DATA_POPULATED=0_NOT_YET_POPULATED
SCORE_PROJECTION_DATA_POPULATED=0_NOT_YET_POPULATED
READY_FOR_GOVERNED_ROLE_DATA_INGESTION=YES_APPROVED_OWNER_REVIEWED_DATA_ONLY
READY_FOR_SCORE_PROJECTION_DATA_INGESTION=YES_APPROVED_PROJECTION_DATA_ONLY
READY_FOR_SCORE_GRADE_BACKEND_PUBLICATION_IMPLEMENTATION=YES_ROUTING_ONLY
SCORE_READY_FOR_IMPLEMENTATION=YES_INFRASTRUCTURE_ONLY
GRADE_READY_FOR_IMPLEMENTATION=YES_INFRASTRUCTURE_ONLY
SCORE_READY_FOR_PUBLICATION=NO
GRADE_READY_FOR_PUBLICATION=NO
```

The remaining bounded gaps are:

- `BLOCKED_BY_COMMITTED_PM_APPROVAL_ARTIFACT_RECONCILIATION`;
- `GOVERNED_ROLE_DATA_NOT_YET_POPULATED`;
- `SCORE_PROJECTION_DATA_NOT_YET_POPULATED`.

These do not authorize bulk ingestion or publication. They do not form a
global blocker for unrelated Topics or derived lanes.

## Prohibited-scope confirmation

```text
507_STOCK_PROPOSAL_LANE_TOUCHED=NO
RANKING_CHANGED=NO
BREADTH_CHANGED=NO
DYNAMIC_LEADERSHIP_CHANGED=NO
CONCENTRATION_CHANGED=NO
LIFECYCLE_CHANGED=NO
HISTORICAL_BACKFILL=NO
TOPIC_MAP_IMPLEMENTED=NO
FRONTEND_CHANGED=NO
OPPORTUNITY_CHANGED=NO
RECOMMENDATION_CHANGED=NO
SCORE_API_PUBLICATION=NO
GRADE_API_PUBLICATION=NO
PRODUCTION_MUTATION=NO
WS2_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER_ACTIVATION=NO
NEXT_TASK_CHANGED=NO
```

## Validation evidence

| Check | Result |
| --- | --- |
| Focused Structural Role / Projection tests | `14 PASS` |
| Existing relation/Score/Runtime readiness regression tests | `16 PASS` |
| Backend full suite | `506 PASS`, `41 SKIPPED`; skips require unavailable PostgreSQL environment |
| Test count | `533 -> 547`, delta `+14`, explained by new focused coverage |
| Ruff | `PASS` |
| Python compile | `PASS` |
| Alembic offline upgrade through 0031 | `PASS` |
| Alembic offline downgrade 0031 -> 0030 | `PASS` |
| JSON parse / lineage / correction assertions | `PASS` |
| `git diff --check` | `PASS` |
| Secret scan | `PASS_NO_MATCHES` |
| Database fixture/integration | `NOT_RUN_ENVIRONMENT_NOT_PROVIDED` |
| G1/G2/G3 | `PRESERVED_NOT_RERUN` |
| Post-Close Canary | `PRESERVED_NOT_RERUN` |
| Production/deploy/scheduler | `NOT_RUN_PROHIBITED` |

The first full-suite collection attempt used only `services/api/src` and
failed to import the existing repository-root `infra` package. It was an
environment-only collection error, not a test result. The final suite used
`PYTHONPATH=repository-root + services/api/src` and produced the result above.

## Owner and parallel-state preservation

At cold-start, owner state was `18` tracked modifications and `167`
untracked paths. `NEXT_TASK` SHA-256 remained
`FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70`.

The task used only the isolated WS1 worktree named above. WS2/WS3/WS4 and the
507-stock proposal boundary were not edited, staged, cleaned, reset, stashed,
merged, or reconciled by this task.

## Closure markers

```text
TASK_ID=TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003
PREDECESSOR=TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002
FINAL_STATUS=COMPLETE
CANONICAL_STATUS=CANONICALIZED
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
CANONICAL_PRE_SHA=1acac134cebc994fdab350aeeb64fe5e997008bf
CANONICAL_POST_SHA=1597068099139ea9df03d6f2b944fb9b7a7f4267
CANONICAL_PROMOTION_COMMIT=1597068099139ea9df03d6f2b944fb9b7a7f4267
WS1_P2B_D001_REOPENED=NO
STRUCTURAL_ROLE_AUTHORITY_INFRASTRUCTURE_READY=YES
STRUCTURAL_ROLE_AS_OF_RESOLVER_READY=YES
SCORE_PROJECTION_INFRASTRUCTURE_READY=YES
SCORE_PROJECTION_AS_OF_RESOLVER_READY=YES
GOVERNED_LEADER_SET_ADAPTER_READY=YES
PM_APPROVAL_ARTIFACT_READY=NO
GOVERNED_ROLE_DATA_POPULATED=0_NOT_YET_POPULATED
SCORE_PROJECTION_DATA_POPULATED=0_NOT_YET_POPULATED
SCORE_READY_FOR_IMPLEMENTATION=YES_INFRASTRUCTURE_ONLY
GRADE_READY_FOR_IMPLEMENTATION=YES_INFRASTRUCTURE_ONLY
SCORE_READY_FOR_PUBLICATION=NO
GRADE_READY_FOR_PUBLICATION=NO
REMAINING_BLOCKERS=BLOCKED_BY_COMMITTED_PM_APPROVAL_ARTIFACT_RECONCILIATION;GOVERNED_ROLE_DATA_NOT_YET_POPULATED;SCORE_PROJECTION_DATA_NOT_YET_POPULATED
MIGRATION_CHANGED=YES
PERSISTENCE_CHANGED=YES_SCHEMA_READ_MODEL_ONLY
APPLICATION_TESTS=506_PASS_41_SKIPPED
DATABASE_VALIDATION=NOT_RUN_ENVIRONMENT_NOT_PROVIDED
G1_G2_G3=PRESERVED_NOT_RERUN
CANARY=PRESERVED_NOT_RERUN
OWNER_STATE_PRESERVED=YES
NEXT_TASK_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
```

Machine-readable evidence is stored at:

`docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003/implementation-evidence.json`
