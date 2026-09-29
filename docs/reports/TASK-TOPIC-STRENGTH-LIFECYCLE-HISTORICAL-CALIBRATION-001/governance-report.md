# TASK-TOPIC-STRENGTH-LIFECYCLE-HISTORICAL-CALIBRATION-001 Governance Report

The calibration work was performed in `E:\TopicPilot\w\cal-001` from the
prior governed Design Freeze lineage. `origin/main` remained at the canonical
base SHA. The owner checkout contained unrelated uncommitted Today/production
edits and was not touched.

## Artifacts

- `source-readiness.json`: committed evidence and strict eligibility boundary.
- `historical-coverage-audit.json`: deterministic row audit; zero input rows
  were accepted because no PIT export was available.
- `absolute-member-return-distribution.json` and
  `relative-member-return-distribution.json`: required percentile schema,
  empty strict distributions, and explicit insufficient-data status.
- `absolute-topic-role-day-distribution.json` and
  `relative-topic-role-day-distribution.json`: role-day aggregate schema with
  no guessed strong-breadth threshold.
- `candidate-absolute-curve.json`, `candidate-relative-curve.json`,
  `candidate-grade-calibration.json`, and
  `candidate-lifecycle-parameters.json`: candidate slots only; all values are
  unresolved and inactive.
- `replay-pm-review.csv`: deterministic review columns with blank PM fields.
- `replay-scenario-status.json` and `calibration-diagnostics.json`: every
  required scenario/diagnostic is marked `NOT_RUN_INSUFFICIENT_DATA`.
- `updated-calibration-register.v2.json`: versioned 15-parameter register.

## Safety and lineage

```text
PRODUCTION_POLICY_ACTIVATED=NO
PRODUCTION_DB_MUTATED=NO
MIGRATION_0047_APPLIED=NO
NEW_MIGRATION_ADDED=NO
DEPLOYED=NO
PUSHED=NO
LOOKAHEAD_USED=NO
P_AND_L_OPTIMIZATION_USED=NO
RELATION_WEIGHT_USED=NO
```

The prior migration `0047_task_topic_role_strength_design_freeze` remains
`ADDED_NOT_APPLIED`. No schema dependency was added for calibration.

## Test scope

The new calibration tests cover strict PIT eligibility, market aliases,
benchmark identity, current-taxonomy rejection, deterministic descriptive
statistics, role-day aggregation, and unresolved empty-input candidates.
The existing Design Freeze focused suites remain the compatibility baseline.

## Required status

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-HISTORICAL-CALIBRATION-001
TASK_STATUS=COMPLETE_WITH_BOUNDED_DATA_LIMITATION
CANONICAL_BASE_SHA=c3542a900d6c46e07bc4243804e9705475023316
CANDIDATE_SHA=0ce1879f3f7780b650f69bde8d634cb816cd2f7
DESIGN_FREEZE_PRESERVED=YES
HISTORICAL_DATE_RANGE=2026-02-02..2026-08-13 observed price evidence; strict calibration range unavailable
HISTORICAL_INSTRUMENT_COUNT=507 canonical price-only evidence; 0 strict calibration instruments
ELIGIBLE_TOPIC_DAY_COUNT=0
ROLE_AUTHORITY_COVERAGE=0% strict PIT calibration rows; formal boundary evidence fail-closed
BENCHMARK_COVERAGE=0 strict same-date benchmark rows in committed export
ABSOLUTE_REP_CALIBRATION=INSUFFICIENT_DATA candidate null
ABSOLUTE_CORE_CALIBRATION=INSUFFICIENT_DATA candidate null
ABSOLUTE_RELATED_CALIBRATION=INSUFFICIENT_DATA candidate null
ABSOLUTE_GRADE_CALIBRATION=INSUFFICIENT_DATA candidate null
ABSOLUTE_D_GUARD=INSUFFICIENT_DATA candidate null
RELATIVE_NEUTRAL_BAND=INSUFFICIENT_DATA candidate null
RELATIVE_REP_CALIBRATION=INSUFFICIENT_DATA candidate null
RELATIVE_CORE_CALIBRATION=INSUFFICIENT_DATA candidate null
RELATIVE_RELATED_CALIBRATION=INSUFFICIENT_DATA candidate null
RELATIVE_GRADE_CALIBRATION=INSUFFICIENT_DATA candidate null
RELATIVE_D_GUARD=INSUFFICIENT_DATA candidate null
SPROUTING_CALIBRATION=INSUFFICIENT_DATA candidate null
FERMENTING_CALIBRATION=INSUFFICIENT_DATA candidate null
MAIN_RISE_CALIBRATION=INSUFFICIENT_DATA candidate null
MATURE_CALIBRATION=INSUFFICIENT_DATA candidate null
DECLINING_CALIBRATION=INSUFFICIENT_DATA candidate null
CONFIRMATION_CALIBRATION=INSUFFICIENT_DATA candidate null
POINT_IN_TIME_AUTHORITY_STATUS=BOUNDED_FORMAL_INPUT_FAIL_CLOSED
NO_LOOK_AHEAD_STATUS=PASS_BY_CONTRACT_NO_ROWS_REPLAYED
TOPIC_SIZE_BIAS_STATUS=NOT_RUN_INSUFFICIENT_DATA
OUTLIER_ROBUSTNESS_STATUS=NOT_RUN_INSUFFICIENT_DATA
TPE_TWSE_ROBUSTNESS_STATUS=NOT_RUN_INSUFFICIENT_DATA
FOCUSED_TEST_STATUS=57_PASSED
BROADER_TEST_STATUS=809_PASSED_59_SKIPPED_10_UNRELATED_REFERENCE_BUNDLE_FAILURES
RUFF_STATUS=PASS
MIGRATION_STATUS=0047_ADDED_NOT_APPLIED
OWNER_DECISIONS_REQUIRED=Approve non-Production PIT export/reconciliation boundary; later approve candidate policy separately
CALIBRATION_LIMITATIONS=No strict PIT role rows, no same-date benchmark export, no fully reconstructable topic-day cells
PRODUCTION_POLICY_ACTIVATED=NO
PRODUCTION_DB_MUTATED=NO
MIGRATION_APPLIED=NO
DEPLOYED=NO
PUSHED=NO
ARTIFACTS=docs/reports/TASK-TOPIC-STRENGTH-LIFECYCLE-HISTORICAL-CALIBRATION-001 and docs/calibration/topic-strength-calibration-register.v2.json
NEXT_RECOMMENDED_TASK=Owner-approved read-only PIT historical export and lineage reconciliation, then rerun this calibration pipeline
```
