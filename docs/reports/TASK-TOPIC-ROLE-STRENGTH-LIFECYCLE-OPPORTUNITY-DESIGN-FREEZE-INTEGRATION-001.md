# TASK-TOPIC-ROLE-STRENGTH-LIFECYCLE-OPPORTUNITY-DESIGN-FREEZE-INTEGRATION-001

Status: `COMPLETE_WITH_CALIBRATION_REQUIRED`

This report records the governed reconciliation of the Topic Role, Daily
Strength, Lifecycle, and Opportunity boundaries. It does not approve numeric
calibration, production activation, deployment, or a push.

## Governance and repository state

| Field | Recorded value |
|---|---|
| Repository | `Xiezhou0828/topicpilot-platform` |
| Canonical branch | `main` |
| Canonical base SHA | `c3542a900d6c46e07bc4243804e9705475023316` |
| Fetch result | `origin/main` did not advance beyond the observed SHA |
| Governed worktree | `E:\TopicPilot\w\trf-001` |
| Candidate branch | `codex/topic-role-strength-lifecycle-opportunity-freeze-001` |
| Candidate implementation SHA | `0a93217e589635e92dcd394402ea7e9edb7c8daf` |
| Push/deployment/Production migration | Not performed |

The owner checkout and unrelated worktrees were not modified. `AI/NEXT_TASK.md`
and Production data were not touched.

## Current-vs-target reconciliation matrix

| Area | CURRENT | TARGET | GAP | ACTION | STATUS |
|---|---|---|---|---|---|
| Daily Strength | Production V1 computes legacy `0.60 * Breadth + 0.40 * Leadership`. | Role-based bounded contributions: REP≈30, CORE≈60, RELATED≈10; member curve → bounded contribution → role aggregation. | Legacy evaluator remains attributable historical/compatibility behavior. | Added `topic_strength_contract.py` with explicit role caps, role curves, coverage, evidence, and bounded `CALIBRATION_REQUIRED` results. | Mechanics reconciled; formal activation pending calibration. |
| Score Projection | Persisted field is `selected_core_members`; current resolver was CORE-only with legacy importance assumptions. | Approved REP+CORE score members; REP `{1.25,1.50,1.75}`, CORE `{0.50,0.75,1.00}`, RELATED none. | Persisted names and old `GovernedLeaderSet` shape are compatibility surfaces. | Resolver validates role-specific domains and authority lineage; `selected_score_members` is the new semantic property; legacy field and adapter remain explicit compatibility. | Reconciled without historical rewrite. |
| Grade | Legacy `grade_for_score(score)` maps numeric bands, including low score→D. | Both Absolute and Relative expose S/A/B/D; D requires confirmed weakness, B is neutral, A clear strength, S exceptional. | Exact grade bands are not Owner-frozen. | Added `GradePolicy`, directional negative-evidence basis, explicit grade fields, and no-curve `CALIBRATION_REQUIRED` behavior. | Semantic boundary reconciled; thresholds open. |
| Relative Strength | No first-class role-based Relative contract in the legacy Daily Strength evaluator. | Same REP/CORE/RELATED structure using member excess return; TWSE→TAIEX and TPEx→TPEx Index; separate curves and grades. | Relative curves and neutral band require historical calibration. | Added member-level benchmark validation, explicit Relative view, separate policy dependency, and API/read-model fields. | Contract present; non-activating until calibrated. |
| Lifecycle | Legacy compatibility surface contained max-gainer/leader naming and a 70/30 authority blend. | Role diffusion across REP→CORE→RELATED; no dynamic leader; Absolute primary, Relative confirmation/early warning; stages remain BASE/SPROUTING/FERMENTING/MAIN_RISE/MATURE/DECLINING. | Existing field names and provisional thresholds remain for historical/read compatibility. | Added role-diffusion evidence boundary; removed max-gainer authority from the v2-shadow/v1 evaluation path; removed blend authority; kept state memory and hysteresis. | Provisional shadow semantics reconciled; lifecycle calibration open. |
| Opportunity | Existing qualification, technical, risk, ranking, and presentation sequence. | Consume upstream Absolute Grade, Relative context, and Lifecycle; do not recalculate them or double count price evidence. | Existing legacy `grade` aliases must remain readable. | Added explicit Absolute/Relative fields to ThemeContext, shadow context, qualification decision, TopicScore, and API schema; Absolute remains primary, Relative D is not a hard exclusion. | Adapter reconciled; existing 20MA/60MA/risk/strategy semantics preserved. |

Relation Weight remains separate from Structural Role, Score Importance,
Strength, Grade, Lifecycle, and Opportunity. No automatic Relation Weight effect
was introduced.

## Canonical contracts and implementation changes

The canonical design-freeze document is
[`TOPIC_ROLE_STRENGTH_LIFECYCLE_OPPORTUNITY_DESIGN_FREEZE.md`](../architecture/TOPIC_ROLE_STRENGTH_LIFECYCLE_OPPORTUNITY_DESIGN_FREEZE.md).
It records the frozen topology, grade meanings, lifecycle vocabulary,
Opportunity boundary, explicit `DO NOT INFER` rules, and readiness boundary.

Added or versioned contracts:

- `topic-strength-role-based.v2`
- `topic-strength-role-based.v2.boundary`
- `topic-strength-calibration-register.v1`
- `topic-lifecycle-role-diffusion.v2`
- `topic-lifecycle-role-diffusion.v2.shadow`
- `topic-lifecycle-role-diffusion.v2.provisional`
- Alembic revision `0047_task_topic_role_strength_design_freeze`

The migration is additive: it permits the new REP importance domain while
retaining legacy `0.25` rows for compatibility. It does not rewrite rows or
apply a Production database migration.

## Required calibration register

All of the following remain `CALIBRATION_REQUIRED`; none is presented as an
Owner-approved production number:

1. Absolute REPRESENTATIVE response knots.
2. Absolute CORE response knots.
3. RELATED breadth/magnitude mapping.
4. Absolute Grade bands.
5. Relative neutral band.
6. Relative REPRESENTATIVE response knots.
7. Relative CORE response knots.
8. Relative RELATED diffusion mapping.
9. Relative Grade bands.
10. Lifecycle role breadth thresholds.
11. Lifecycle role magnitude thresholds.
12. Lifecycle confirmation days.
13. MATURE persistence parameters.
14. DECLINING deterioration/drawdown parameters.

The machine-readable register is
[`topic-strength-calibration-register.v1.json`](../calibration/topic-strength-calibration-register.v1.json).
The read-only descriptive helper reports canonical historical distributions
and refuses non-canonical calibration sources; it does not choose knots or
optimize thresholds.

## Repository audit classification

The repository-wide audit classified the relevant legacy occurrences as
follows:

| Occurrence | Classification | Reconciliation |
|---|---|---|
| `production_policy.py` `0.60/0.40`, `LeaderDefinition`, `grade_for_score` | `HISTORICAL_ONLY` / `COMPATIBILITY_ONLY` | Retained for attributable Production V1 behavior; not treated as the new role-strength contract. |
| `score_projection.py` `selected_core_members`, `GovernedLeaderSet` | `ADAPT` / `COMPATIBILITY_ONLY` | New REP+CORE validation and `selected_score_members`; deterministic adapter preserves downstream shape. |
| ORM projection member constraint | `ADAPT` | Additive migration permits both legal current domains and historical `0.25`; current resolver rejects legacy `0.25`. |
| `topic_lifecycle_v1.py` leader fields, `leader_change`, authority-weighted breadth | `ADAPT` / `COMPATIBILITY_ONLY` | Formal role set is REP/CORE/RELATED; leader outputs are null/compatibility-only and no max-gainer or 70/30 authority remains. |
| `topic_lifecycle_engine.py` persistence adapter | `KEEP` with v2 shadow binding | Public evaluator aliases the role-diffusion v2-shadow policy; persistence, state memory, and fail-closed lineage remain. |
| `topic_lifecycle_v1_3_formal.py` | `KEEP` as historical/formal publication wrapper | Existing stage vocabulary and publication guardrails remain version-attributable. |
| Legacy architecture/research documentation mentioning Breadth/Leadership | `HISTORICAL_ONLY` | Not silently rewritten; the canonical freeze document is the current semantic authority. |
| Opportunity qualification/shadow/strategy layers | `ADAPT` | Explicit Absolute/Relative fields added; technical and risk gates are unchanged. |
| Relation Weight authorities and consumers | `KEEP` | No automatic effect injected into Strength, Lifecycle, or Opportunity. |

## Files changed in the candidate implementation

- `docs/architecture/TOPIC_ROLE_STRENGTH_LIFECYCLE_OPPORTUNITY_DESIGN_FREEZE.md`
- `docs/calibration/topic-strength-calibration-register.v1.json`
- `services/api/alembic/versions/0047_task_topic_role_strength_design_freeze.py`
- `services/api/src/topicpilot_api/orm/score_projections.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/src/topicpilot_api/topic_engine/__init__.py`
- `services/api/src/topicpilot_api/topic_engine/opportunity_qualification.py`
- `services/api/src/topicpilot_api/topic_engine/opportunity_shadow.py`
- `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py`
- `services/api/src/topicpilot_api/topic_engine/score_projection.py`
- `services/api/src/topicpilot_api/topic_engine/scoring_contracts.py`
- `services/api/src/topicpilot_api/topic_engine/topic_strength_calibration.py`
- `services/api/src/topicpilot_api/topic_engine/topic_strength_contract.py`
- `services/api/src/topicpilot_api/topic_intelligence_api.py`
- `services/api/src/topicpilot_api/topic_lifecycle_contract.py`
- `services/api/src/topicpilot_api/topic_lifecycle_role_evidence.py`
- `services/api/src/topicpilot_api/topic_lifecycle_v1.py`
- `services/api/tests/test_canonical_observation_implementation.py`
- `services/api/tests/test_lifecycle_v1_3_formal_publication.py`
- `services/api/tests/test_structural_role_score_projection.py`
- `services/api/tests/test_topic_lifecycle_engine.py`
- `services/api/tests/test_topic_role_strength_design_freeze.py`

## Test report

Focused validation:

- Design-freeze semantic tests, structural score projection, lifecycle engine,
  and formal lifecycle publication: **53 passed**.
- Opportunity/API compatibility suites: **18 passed**.
- Ruff checks for all changed Python files: **passed**.
- Alembic head inspection: **0047_task_topic_role_strength_design_freeze**.
- No task-focused test failed in the broader run.

Broader backend run from the governed worktree:

`804 passed, 59 skipped, 10 failed`.

All 10 failures are in the unrelated corporate-action dataset/reference-bundle
surface: nine fail because the checked-in `tw-reference-v1` manifest version
does not match the expected version, and one control fixture has the existing
effective-date mismatch (`2026-08-27` versus `2026-06-23`). These failures do
not involve the changed files or the Topic role/strength/lifecycle/Opportunity
contracts.

## Final governance status

```text
TASK_STATUS=COMPLETE_WITH_CALIBRATION_REQUIRED
DESIGN_FREEZE_RECONCILIATION=COMPLETE
DAILY_STRENGTH_TARGET=ROLE_BASED_REP30_CORE60_RELATED10_NONACTIVATING
ABSOLUTE_STRENGTH_CONTRACT=EXPLICIT_ROLE_BASED_0_TO_100_CALIBRATION_REQUIRED
RELATIVE_STRENGTH_CONTRACT=MEMBER_LEVEL_TWSE_TO_TAIEX_TPEX_TO_TPEX_INDEX_SEPARATE_CURVES
GRADE_SEMANTICS=S_A_B_D_DIRECTIONAL_D_CONFIRMED_WEAKNESS
SCORE_PROJECTION_RECONCILIATION=REPRESENTATIVE_PLUS_CORE_DOMAINS_RECONCILED
LIFECYCLE_RECONCILIATION=ROLE_DIFFUSION_NO_DYNAMIC_LEADER_NO_70_30_AUTHORITY
OPPORTUNITY_RECONCILIATION=ABSOLUTE_PRIMARY_RELATIVE_CONTEXT_NO_RECALCULATION
RELATION_WEIGHT_SEPARATION=MAINTAINED
HISTORICAL_COMPATIBILITY=YES_VERSIONED_AND_ADAPTED
CALIBRATION_REQUIRED=YES
OWNER_DECISIONS_REQUIRED=NONE_FOR_THIS_RECONCILIATION
TEST_STATUS=FOCUSED_PASS_BROAD_PASS_WITH_10_UNRELATED_REFERENCE_DATA_FAILURES
MIGRATION_STATUS=0047_ADDED_NOT_APPLIED
PRODUCTION_READY=NO
CANONICAL_BASE_SHA=c3542a900d6c46e07bc4243804e9705475023316
CANDIDATE_SHA=0a93217e589635e92dcd394402ea7e9edb7c8daf
NEXT_RECOMMENDED_TASK=Run no-lookahead canonical historical role-day calibration, then approve versioned curves/grades/lifecycle thresholds before formal activation.
```
