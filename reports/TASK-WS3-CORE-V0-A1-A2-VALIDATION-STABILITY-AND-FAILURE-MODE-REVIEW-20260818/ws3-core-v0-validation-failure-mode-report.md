# WS3 Core V0 Validation Stability and Failure-Mode Review

## Required final fields

```text
TASK_FINAL_STATUS=COMPLETE_CORE_V0_VALIDATION_FAILURE_MODE_REVIEW
FROZEN_SPEC_UNCHANGED=YES
LOOKAHEAD_LEAKAGE_DETECTED=NO
VALIDATION_FAILURE_EXPLAINED=YES
VALIDATION_FAILURE_PRIMARY_DRIVER=BROAD_A1_A2_VALIDATION_DATE_AND_WEEK_WEAKNESS
A1_VALIDATION_STABILITY=INCONCLUSIVE
A2_VALIDATION_STABILITY=INCONCLUSIVE
A1_NON_TRANSITION_TAXONOMY_READY=YES_BOUNDED
A1_NON_TRANSITION_FALSE_BREAKOUT_HYPOTHESIS=YES_BOUNDED
A1_TO_A2_FORWARD_SEPARATION_REPRODUCED=YES
A1_TO_A2_EX_ANTE_RULE_CREATED=NO
CORE_V0_BASELINE_CLASSIFICATION_CHANGED=NO
CORE_V0_BASELINE_CLASSIFICATION=BASELINE_SUPPORTED
FUTURE_EX_ANTE_DISCRIMINATION_RESEARCH=YES_RESEARCH_CANDIDATE
READY_FOR_WS3_NEXT_MAINLINE_STEP=YES_WITH_BOUNDED_LIMITATIONS
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
SOURCE_BASELINE_HEAD=9ca9ba4f15359aa5ea96ba4c3d6bed9439d0346e
DATASET_AUTHORITY=canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved
FILES_CHANGED=task-owned validation runner, tests, and 9 evidence artifacts
TESTS=32 passed; focused rerun 3 passed; py_compile pass; ruff F/E731/I pass
TASK_COMMIT_SHA=0282530e8360ee77735d6a4677a4e07996610b53
```

## Scope and authority

This review consumes the frozen Core V0 A1/A2 definitions, the existing MA60 eligibility, the existing REC-A1 event-aware policy, the canonical real historical OHLCV reader, and the already-established 2026-05-12..2026-08-13 transition framework. No threshold, formation rule, score, ranking, or strategy state was changed.

A1-to-A2 linkage and all failure labels are post-formation diagnostics. Later A2 occurrence is never used as an ex-ante input; outcomesFlowBackward=false.

## Validation decomposition

The negative stability conclusion is produced by the frozen VALIDATION segment (2026-07-01..2026-07-31). Development and holdout are reported without redefining boundaries. A1 validation T+5 mean=-0.027821703230706145; A2 validation T+5 mean=-0.06798936006962135; Core validation T+5 mean=-0.04030905768839999.

The validation weakness is broad across A1 and A2 in this segment, with date/week and instrument concentration diagnostics below. Topic/sector/regime attribution is NOT_AVAILABLE because no such authority is present in the frozen candidate record.

### Validation concentration

Core V0 worst signal dates by T+5 mean: ['2026-07-13', '2026-07-08', '2026-07-06', '2026-07-09', '2026-07-23', '2026-07-17', '2026-07-03', '2026-07-22', '2026-07-07', '2026-07-15']; best signal dates: ['2026-07-29', '2026-07-31', '2026-07-20', '2026-07-28', '2026-07-14', '2026-07-27', '2026-07-16', '2026-07-30', '2026-07-02', '2026-07-01'].
Worst five dates contributed T+5 return sum=-4.8846529552409335 and 0.512639416986048 of negative-return magnitude; worst ten contributed T+5 return sum=-6.990810839235052 and 0.7861390944642911.
Weekly Core V0 T+5 means were [{'week': '2026-06-29', 'mean': -0.028049926072823292, 'n': 74}, {'week': '2026-07-06', 'mean': -0.0809615034730626, 'n': 55}, {'week': '2026-07-13', 'mean': -0.03929481552568128, 'n': 38}, {'week': '2026-07-20', 'mean': -0.02924622728024219, 'n': 39}, {'week': '2026-07-27', 'mean': 0.0015595934397882164, 'n': 18}].
Leave-one-instrument validation sensitivity: 115 instruments tested; qualitative conclusion changed by any single removal=False; sign-changing instruments=[].

## Non-transition interpretation

Among 314 A1 observations without a later A2 inside the established window, the taxonomy is intentionally bounded: breakout rejection=0.68152866, never broke out / continued consolidation=0.09554140, structural loss before breakout=0.11783439, unclassified=0.10509554.

The structurally intact but unresolved share (Q3) is the continued-consolidation subset at 0.09554140. Delayed or outside-window transition is not measurable here because no transition horizon beyond the established frozen research window was introduced.

Therefore A1_NOT_TO_A2 versus FALSE_BREAKOUT is classified YES_BOUNDED; it is not a one-to-one equivalence. The observed A1-to-A2 T+5 separation is associated with post-formation structural outcomes, but no future-informed discriminator is implemented.

Q6=YES_BOUNDED: the transition/non-transition separation is associated with observable post-formation structural failure. Q7=YES: this explains part of the negative validation segment. Q8=YES_RESEARCH_CANDIDATE: the distinction may support future ex-ante research, but no discriminator is designed or implemented here.

## Formal versus economic interpretation

Formally, A1 remains the frozen pre-breakout candidate state and A2 remains the frozen confirmed-breakout state. Economically, the path evidence is consistent with A1 representing an earlier setup and A2 representing greater structural confirmation, but this interpretation is not a new rule or acceptance decision.

## Lifecycle and integrity

Frozen spec unchanged=True; source reconciliation=True; accepted baseline reconciliation={'A1': True, 'A2': True, 'TOTAL': True}; look-ahead violations=0; state mutation based on outcome=False; optimization=False; reproducibility=YES.

```text
VALIDATION_FAILURE_MODE_REVIEW=RESEARCH_ONLY
A1_TO_A2_EX_ANTE_RULE=NOT_CREATED
STRATEGY_REVIEW=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
PRODUCTION=NOT_RUN
DEPLOY=NOT_RUN
NEXT_TASK=UNCHANGED
CANONICAL_STATUS=CANONICALIZED
CANONICAL_HEAD_AT_PROMOTION=723b2019261552269e2ddc7e913f092a995db5e2
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF
CANONICAL_RECONCILIATION_DISPOSITION=CANONICALIZED
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
PUSH_REMOTE=NO
```
