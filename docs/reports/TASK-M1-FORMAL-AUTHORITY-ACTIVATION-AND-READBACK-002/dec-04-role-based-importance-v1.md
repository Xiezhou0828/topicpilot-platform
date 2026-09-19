# DEC-04 Role-Based Importance V1

`DEC-04=APPROVED_ROLE_BASED_IMPORTANCE_V1`

The current D001 authority is now Model A: importance is a deterministic
projection of the already approved Structural Role.

```text
CORE           = 1.00
REPRESENTATIVE = 0.75
RELATED        = 0.25
```

The historical TSV remains `PROPOSAL_ONLY_NON_AUTHORITY`. It is retained for
provenance and reconciliation only; it is not used to overwrite the current
formal Structural Role authority. The current artifact consumes all 1,160
approved role rows across 107 Topics and does not create a second CORE
hierarchy, manual subset, Top-N, or analytical ordering rule.

Required semantic result:

```text
STRUCTURAL_ROLE_VALUES=CORE,REPRESENTATIVE,RELATED
HISTORICAL_ROLE_WEIGHT_EVIDENCE=TSV_HISTORICAL_PROVENANCE_ONLY; CURRENT_DEC-04_MAPPING_FORMALIZED
LEAD_WEIGHT=UNPROVEN_NOT_CANONICAL_ROLE
CORE_WEIGHT=1.00
RELATE_WEIGHT=0.25
REPRESENTATIVE_WEIGHT=0.75
IMPORTANCE_IS_ROLE_PROJECTION=YES
D001_SCORE_MEMBER_UNIVERSE=ALL_FORMAL_TOPIC_MEMBERS_WITH_APPROVED_EFFECTIVE_ROLE
D001_REQUIRES_SEPARATE_CORE_SUBSET=NO
D001_REQUIRES_PER_CORE_IMPORTANCE=NO
ORDER_AFFECTS_SCORE=NO
FIXED_MIN_REQUIRED_BY_FORMULA=NO
FIXED_MAX_REQUIRED_BY_FORMULA=NO
MODEL_CLASSIFICATION=MODEL_A
```

The formal artifact is [d001-role-importance-authority-20260920.v1.json](../../../config/topic_d001_role_importance_authority/d001-role-importance-authority-20260920.v1.json).
The runtime path now validates role-to-importance equality, accepts all three
roles, preserves the independent CORE coverage eligibility rule, and provides
transactional production materialization/readback with exact confirmation.
The `topicpilot-d001-role-importance` operator entrypoint supports artifact
validation, dry-run, materialization, and persisted readback. Readback reuses
the formal Score projection resolver and rejects future as-of dates and legacy
`0.50` state.

Migration `0043_task_m1_role_based_d001_importance` changes the persisted
importance check forward-only. It refuses to proceed if existing persisted
rows still contain `0.50`; no automatic historical rewrite is performed.

Formal Opportunity now has a persisted publication envelope (`0044_task_m1_formal_opportunity_publication`), an idempotent writer, and a PostgreSQL provider/readback adapter. The Render API service enables that provider through `TOPICPILOT_FORMAL_OPPORTUNITY_PROVIDER=POSTGRES`; when the envelope has not yet been published, the provider remains fail-closed. The package builder can publish `EMPTY` or `DEFERRED` formal states without inventing frozen downstream Opportunity rules.

Focused validation passed: 27 tests for the current D001/Opportunity slice,
plus the previously recorded DEC-04 focused suite. Migration offline SQL,
Ruff, and compile checks passed. Production materialization, Score/Grade/
Lifecycle/Topic/Today/Opportunity readback, and next-trading-day automation
were not run because no Production database access was available.
The repository-wide backend run completed with `770 passed, 59 skipped,
36 failed`; the failures are pre-existing missing research artifacts and the
older Lifecycle contract expectations, not this M1 write-set. No new failure
was introduced by the formal Opportunity migration after its architecture
freeze allowlist was updated.
`M2_STARTED=NO`.
