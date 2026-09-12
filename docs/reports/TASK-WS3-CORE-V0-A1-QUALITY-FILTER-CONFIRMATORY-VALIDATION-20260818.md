# WS3 Core V0 A1 Quality-Filter Confirmatory Validation

## Final contract

```text
TASK_FINAL_STATUS=COMPLETE_A1_QUALITY_FILTER_CONFIRMATORY_VALIDATION
SOURCE_CANONICAL_HEAD=8bc9c8ec403e03aa104c6feac481e2d5e561e134
CURRENT_CANONICAL_HEAD=8bc9c8ec403e03aa104c6feac481e2d5e561e134
TASK_COMMIT_SHA=bfbc8e99fec61af538dbb8df49025cfe221a1013
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
CONFIRMATORY_FREEZE_CREATED=YES
CONFIRMATORY_PROTOCOL_FROZEN_BEFORE_OUTCOME_REVIEW=YES
CONFIRMATORY_INDEPENDENCE_LEVEL=BOUNDED
RAW_A1_COUNT=700
SUCCESSFUL_A1_COUNT=386
FAILED_BREAKOUT_A1_COUNT=214
FROZEN_CANDIDATE_COUNT=7
CONFIRMED_CANDIDATE_COUNT=0
BOUNDED_SUPPORTED_CANDIDATE_COUNT=0
INCONCLUSIVE_CANDIDATE_COUNT=7
FAILED_CANDIDATE_COUNT=0
BEST_CONFIRMED_CANDIDATE=None
BEST_CONFIRMED_RETENTION_RATE=None
BEST_CONFIRMED_SUCCESS_RATE=None
BEST_CONFIRMED_FAILED_BREAKOUT_RATE=None
BASELINE_SUCCESS_RATE=0.5945945945945946
BASELINE_FAILED_BREAKOUT_RATE=0.40540540540540543
SUCCESS_RATE_UPLIFT=None
FAILED_BREAKOUT_RATE_REDUCTION=None
JULY_VALIDATION_IMPROVEMENT=YES
TPE_TWO_DIRECTIONAL_CONSISTENCY=YES
TEMPORAL_STABILITY=MIXED
DATE_CONCENTRATION_RISK=LOW_OR_MEDIUM
INSTRUMENT_CONCENTRATION_RISK=LOW_OR_MEDIUM
OUTLIER_DRIVEN=YES
FORWARD_RETURN_SUPPORT=SUPPORTIVE_OR_NON_DESTRUCTIVE
A1_QUALITY_FILTER_CONFIRMATORY_SUPPORT=NO
READY_FOR_A1_QUALITY_FILTER_PROVISIONAL_SPEC=NO
READY_FOR_A1_PRODUCTION_FILTER=NO
LOOK_AHEAD_LEAKAGE_DETECTED=NO
OUTCOME_DERIVED_FEATURE_DETECTED=NO
THRESHOLD_RETUNING_PERFORMED=NO
NEW_FEATURE_SEARCH_PERFORMED=NO
A1_FORMATION_CHANGED=NO
A2_FORMATION_CHANGED=NO
CORE_V0_FROZEN_SPEC_CHANGED=NO
MA60_POLICY_CHANGED=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
MIGRATION_EXECUTED=NO
PRODUCTION_MUTATION=NO
DEPLOY_EXECUTED=NO
PUSH_EXECUTED=NO
REPRODUCIBILITY_PASS=PASS
NORMALIZED_AGGREGATE_SHA256=6bc87a6b5ab182dae972bd198f4ee06dea90fea2050c3708b2da9cf10cd3075d
READY_FOR_WS3_NEXT_MAINLINE_STEP=YES
NEXT_WS3_MAINLINE_STEP=OWNER_DECISION_REQUIRED_AFTER_BOUNDED_CONFIRMATION
REMAINING_LIMITATIONS=No untouched temporal data remains; bounded retrospective independence; small HOLDOUT; no provisional production-like specification; July weakness remains a stress limitation.
FILES_CHANGED=confirmatory research module; focused tests; freeze; 10 confirmatory artifacts; closure report
TESTS=FOCUSED_CONFIRMATORY_8_PASS;EXISTING_WS3_47_PASS;REPLAY_AGGREGATE_SHA256_EQUAL_6bc87a6b5ab182dae972bd198f4ee06dea90fea2050c3708b2da9cf10cd3075d
SOURCE_CANONICAL_HEAD=8bc9c8ec403e03aa104c6feac481e2d5e561e134
CURRENT_CANONICAL_HEAD=8bc9c8ec403e03aa104c6feac481e2d5e561e134
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
NORMALIZED_AGGREGATE_SHA256=6bc87a6b5ab182dae972bd198f4ee06dea90fea2050c3708b2da9cf10cd3075d
TASK_COMMIT_SHA=bfbc8e99fec61af538dbb8df49025cfe221a1013
TESTS=FOCUSED_CONFIRMATORY_8_PASS;EXISTING_WS3_47_PASS;REPLAY_AGGREGATE_SHA256_EQUAL_6bc87a6b5ab182dae972bd198f4ee06dea90fea2050c3708b2da9cf10cd3075d
```

## What was frozen before confirmatory outcomes

The freeze artifact contains 7 candidates: 6 robust single-feature regions and 1 previously declared two-feature diagnostics. No confirmatory outcome is used in candidate selection.

Confirmatory independence is BOUNDED: the available history was already inspected during exploration, so this is a frozen chronological retrospective replay rather than untouched new-data confirmation.

## R1-R4 authority and executability lanes

R1 — REC-A1 provenance reconciliation: the clean canonical research artifact was consumed with normalized file SHA-256 `78f684d5b014f43f3b34393be1bc644805e67f05e18b21e7ab98d075a1cd60b2` and logical content hash `4d9b4912bd1c4613510e60c5cf4b5a629c367e1c94dd733d3b1dc3f935e0eb5d`. The Phase 1 owner-export SHA `1091f972...` was not silently substituted and the dataset was not changed by this task. The owner-versus-clean mismatch is therefore an authority/provenance binding issue, not evidence of a new dataset identity conflict. The research-only Freeze remains closed; the 154 reviewed UNKNOWN population and best-effort residual uncertainty were not reopened. The previously recorded review-ledger archive gap remains a bounded provenance limitation and is not promoted to an exchange-grade completeness blocker.

R2 — candidate-specific minimum research panel: every frozen filter candidate uses the preserved raw A1 cohort, candidate-specific PIT feature inputs, evaluation date/as-of, OHLCV lineage, and REC-A1 integrity context. The observed canonical panel reconciles to 63,826 real rows, 507 instruments, 2026-02-02..2026-08-13, zero duplicates, zero invalid lineage rows, and the preserved 700/386/214 A1/success/failed counts. No global Historical Topic/System State prerequisite was introduced. T+1/T+3/T+5/T+10 are evaluation-only outcomes and do not flow backward into candidate formation.

R3 — candidate definition authority: the seven quality-filter candidates are immutable carry-forward definitions from the prior threshold research: six previously robust single regions and one previously declared two-feature diagnostic. The freeze records exact feature, operator, quantile, threshold, PIT timestamp rule, and combination logic. This task did not invent A1/A2/A3/Catch-up strategy definitions, breakout/support/RSI/volume thresholds, or any new formula. The separate upstream formation-authority gaps remain outside this confirmatory filter decision.

R4 — temporal eligibility and warm-up: replay is chronological over the frozen TRAIN/VALIDATION/HOLDOUT segments, with the Core V0 minimum 60 prior canonical trading-session requirement preserved. Feature warm-up and as-of checks are candidate-specific; a symbol having OHLCV alone is not treated as eligibility. The confirmatory HOLDOUT is 2026-08-01..2026-08-13 and the July VALIDATION segment is stress evidence only. Because no untouched temporal data remains, the independence level is BOUNDED rather than HIGH.

## Candidate-level disposition matrix

The minimum-panel and temporal columns describe evidence availability and eligibility checks; they do not override the predeclared primary cohort minimum. All seven candidates have complete feature/outcome artifact coverage, but each primary HOLDOUT cohort is below at least one predeclared per-cohort minimum of 20, so none is promoted to confirmation.

| Candidate | REC-A1 | Minimum panel | Definition authority | Temporal eligibility | Outcome coverage | Final disposition |
|---|---|---|---|---|---|---|
| `recent_20_high_proximity__UPPER_GE_Q30` | BOUNDED identity binding; ledger archive gap preserved | PIT high/close, 20-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 19 success / 13 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — below primary cohort minimum |
| `recent_20_high_proximity__UPPER_GE_Q40` | BOUNDED identity binding; ledger archive gap preserved | PIT high/close, 20-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 16 success / 11 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — below primary cohort minimum |
| `recent_20_high_proximity__UPPER_GE_Q50` | BOUNDED identity binding; ledger archive gap preserved | PIT high/close, 20-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 15 success / 10 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — below primary cohort minimum |
| `return_5d__LOWER_LE_Q60` | BOUNDED identity binding; ledger archive gap preserved | PIT close, six-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 15 success / 9 failed | T+1/T+3/T+5/T+10; outlier flag YES | `INCONCLUSIVE` — below primary cohort minimum |
| `true_range_pct__LOWER_LE_Q60` | BOUNDED identity binding; ledger archive gap preserved | PIT high/low/close, one-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 20 success / 9 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — failed cohort below minimum |
| `true_range_pct__LOWER_LE_Q70` | BOUNDED identity binding; ledger archive gap preserved | PIT high/low/close, one-session feature, date/as-of, lineage available | FROZEN carry-forward quality-filter rule | Chronological HOLDOUT; 21 success / 11 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — failed cohort below minimum |
| `recent_20_high_proximity__AND__true_range_pct` | BOUNDED identity binding; ledger archive gap preserved | PIT high/close + high/low/close, both lineages available | FROZEN previously declared pair; no new search | Chronological HOLDOUT; 19 success / 10 failed | T+1/T+3/T+5/T+10 plus Wilson intervals | `INCONCLUSIVE` — below primary cohort minimum |

Reverse dependencies are therefore bounded to the fields actually consumed: raw A1 outcome labels for evaluation partitioning, `high`/`low`/`close` OHLCV, the frozen feature lookbacks, evaluation session/date/as-of, PIT lineage, and T+1/T+3/T+5/T+10 outcome fields. No full Historical Topic/System State build is required for this task, and no candidate is blocked by a global readiness gate.

## Candidate outcomes

- recent_20_high_proximity__UPPER_GE_Q30: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- recent_20_high_proximity__UPPER_GE_Q40: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- recent_20_high_proximity__UPPER_GE_Q50: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- return_5d__LOWER_LE_Q60: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- true_range_pct__LOWER_LE_Q60: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- true_range_pct__LOWER_LE_Q70: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.
- recent_20_high_proximity__AND__true_range_pct: INCONCLUSIVE — Primary confirmatory holdout cohort is below the predeclared per-cohort minimum.

## Required questions

Q1/Q2: Successful-A1 uplift and failed-breakout reduction are evaluated on the frozen HOLDOUT segment; best bounded candidate is none.
Q3: Retention is reported per candidate; no candidate is accepted on success rate alone.
Q4/Q5/Q6: Temporal, TPE/TWO, and July results are separated in the temporal, market, and July artifacts.
Q7/Q10: Forward means, medians, trimmed means, win rates, and outlier flags are reported by horizon.
Q8/Q9: Date and instrument concentration are reported with top-1/3/5 dates and top-1/5/10 instruments.
Q11/Q12: The evidence remains NO; a provisional production-like specification is not authorized, and the next step is OWNER_DECISION_REQUIRED_AFTER_BOUNDED_CONFIRMATION.
Q13: No candidate is ready for production.

## Safety and lifecycle

A1 formation, A2 formation, Core V0, MA60 policy, WS1, WS2, WS4, NEXT_TASK, migrations, database writes, Production, deployment, and push were not changed or executed.

```text
CANONICAL_STATUS=CANONICALIZED
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF
FINAL_CANONICAL_HEAD_AT_PROMOTION=d7ad7f3f5d274f5ff444bd29c25cf70239522bb0
CANONICAL_PROMOTION_COMMITS=2319796;82ad1b6;d7ad7f3
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
PUSH_REMOTE=NO
DEPLOY=NOT_RUN
MIGRATION=NOT_RUN
```
