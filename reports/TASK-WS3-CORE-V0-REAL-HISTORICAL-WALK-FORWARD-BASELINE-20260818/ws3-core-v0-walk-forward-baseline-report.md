# WS3 Core V0 Real Historical Walk-forward Baseline

## Required headline fields

```text
TASK_FINAL_STATUS=COMPLETE_FROZEN_CORE_V0_BASELINE_WALK_FORWARD
CORE_V0_FROZEN_SPEC_IDENTIFIED=YES
CORE_V0_FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
REAL_HISTORICAL_ROW_COUNT=63826
REAL_HISTORICAL_DISTINCT_INSTRUMENTS=507
RESEARCH_DATE_RANGE=2026-05-12..2026-08-13
RESEARCH_TRADING_DAY_COUNT=66
METHOD_A_HARD_ELIGIBILITY_PRESERVED=YES
MA60_POLICY_CHANGED=NO
CORE_V0_STRATEGY_CHANGED=NO
PARAMETER_OPTIMIZATION_EXECUTED=NO
LOOKAHEAD_LEAKAGE_DETECTED=NO
SYNTHETIC_DATA_USED=NO
KNOWN_EVENT_OVERLAY_PRESERVED=YES
DATA_GAP_FAIL_CLOSED_PRESERVED=YES
RAW_SIGNAL_OBSERVATION_COUNT=1212
UNIQUE_SIGNAL_INSTRUMENT_COUNT=406
ACTIVE_SIGNAL_DATE_COUNT=66
FORMAL_PRE_BREAKOUT_STATE_AVAILABLE=YES
T1_EVALUABLE_COUNT=1186
T1_MEAN_RETURN=0.00926006
T1_MEDIAN_RETURN=0.00146428
T1_WIN_RATE=0.51096121
T3_EVALUABLE_COUNT=1137
T3_MEAN_RETURN=0.01480325
T3_MEDIAN_RETURN=0.00288184
T3_WIN_RATE=0.51539138
T5_EVALUABLE_COUNT=1080
T5_MEAN_RETURN=0.02301029
T5_MEDIAN_RETURN=0.00589537
T5_WIN_RATE=0.53611111
T10_EVALUABLE_COUNT=964
T10_MEAN_RETURN=0.04437282
T10_MEDIAN_RETURN=0.01003269
T10_WIN_RATE=0.54253112
METHOD_A_FORWARD_EDGE=NEGATIVE
DOES_CORE_V0_ADD_VALUE_BEYOND_MA60_ELIGIBILITY=POSITIVE
SCORE_MONOTONICITY=INCONCLUSIVE_NO_FROZEN_CORE_V0_SCORE
PERFORMANCE_STABLE_ACROSS_WINDOWS=YES
OUTLIER_CONCENTRATION_RISK=NOT_DOMINATED_BY_TOP_5_PERCENT
WALK_FORWARD_REPRODUCIBLE=YES
CORE_V0_BASELINE_CLASSIFICATION=BASELINE_SUPPORTED
READY_FOR_CORE_V0_BASELINE_REVIEW=YES
READY_FOR_WS3_NEXT_MAINLINE_STEP=READY_FOR_BOUNDED_CONFIRMATION_VALIDATION
REMAINING_WS3_BLOCKERS=BOUNDED_CENSORING_AND_NO_FORMAL_SCORE_OR_DAILY_SELECTION_CONTRACT
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
G2R_C_EXECUTED=NO
SHARED_G3_EXECUTED=NO
PRODUCTION_CHANGED=NO
DEPLOY_EXECUTED=NO
FILES_CHANGED=14 task-owned files (runner, focused tests, and 12 evidence artifacts)
TESTS=26 passed; focused WS3/Core V0 baseline, candidate-panel, coverage, and research-policy tests
TASK_COMMIT_SHA=fc49acb
CANONICAL_PROMOTION_COMMIT=1f01757
```

## Scope and frozen authority

This is an as-is baseline of the existing WS3 Core V0 A1/A2 candidate
authority. It uses the committed `core-v0-walk-forward.v1` protocol and the
real canonical historical reader. It does not use the provisional Opportunity
shadow strategy ranking, A3, Catch-up, future pullback acceptance, or any
post-hoc parameter selection.

The frozen spec is stored in `ws3-core-v0-frozen-spec.json`; all result files
reference `CORE_V0_FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d`. Source authority was frozen
from commit `7d49ce7e8c4ed855479a763102048aba2938e1b0` before forward outcomes were calculated.

The exact Method A source rule is `Close(T) >= MA60(T)`, as frozen in the
Core V0 candidate-definition authority and implemented by the candidate panel.
The old global 20MA rule was not used.

## Anti-leakage and outcome handling

For every signal date `T`, candidate formation used only accepted bars with
session date and as-of at or before `T`. The prior-20 reference excludes `T`
from its high window. T+1/T+3/T+5/T+10 are evaluated only after the candidate
is frozen. No future highs, lows, volume, topic state, market state, or
forward return entered candidate formation.

Forward horizons are instrument-session based and are never filled with zero.
End-of-data dates after 2026-08-13 are explicitly censored. Known verified
REC-A1 events exclude formation windows when they intersect the trailing MA60
dependency and exclude an outcome only on the evaluation side; they never
rewrite the candidate at `T`. PARTIAL event authority remains UNKNOWN.

There is no frozen cost, benchmark, MFE, MAE, formal Core V0 continuous score,
or daily Top-N selection contract. Those fields are reported as unavailable,
not fabricated. Episode-level trade performance is
`NOT_FORMALLY_DEFINED`; observation-level and persistence surfaces are both
provided.

## Baseline performance

| Group | T+1 evaluable | T+3 evaluable | T+5 evaluable | T+10 evaluable |
| --- | ---: | ---: | ---: | ---: |
| All MA60-calculable | 22861 | 21853 | 20846 | 18335 |
| Method A eligible | 15595 | 15026 | 14455 | 13073 |
| Core V0 candidates | 1186 | 1137 | 1080 | 964 |

Full mean, median, win rate, quartiles, dispersion, best/worst, censoring,
and event-exclusion metrics are in `ws3-core-v0-forward-performance-by-horizon.csv`.
Candidate-state metrics are in `ws3-core-v0-performance-by-signal-state.csv`.

## Diagnostics and interpretation

- `DOES_CORE_V0_ADD_VALUE_BEYOND_MA60_ELIGIBILITY` is derived by comparing
  frozen Core V0 candidate outcomes against Method A at all four horizons; it
  is not a tuned threshold or acceptance rule.
- `METHOD_A_FORWARD_EDGE` compares Method A against the all-MA60-calculable
  baseline.
- No frozen score or ranking exists in Core V0, so score monotonicity and
  daily-selection performance are inconclusive/not applicable rather than
  reverse-engineered from the provisional Opportunity shadow engine.
- Chronological development-available, validation, and holdout surfaces are
  provided in `ws3-core-v0-performance-by-walk-forward-window.csv`.
- Outlier concentration and date concentration are provided in the summary,
  signal-date distribution, and horizon CSVs. Repeated signals are not
  silently converted into independent trades.

## Quality and lifecycle state

The quality audit reports source reconciliation, frozen-spec hash, no-lookahead
checks, horizon censoring, Method A rule checks, event overlay handling,
duplicate/data-gap fail-closed handling, and reproducibility. The run is
research evidence only:

```text
WALK_FORWARD=EXECUTED_BASELINE_ONLY
PERFORMANCE_METRICS=PRODUCED_RESEARCH_ONLY
STRATEGY_REVIEW=NOT_RUN
PARAMETER_OPTIMIZATION=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
G2R_C=NOT_RUN
SHARED_G3=NOT_RUN
MIGRATION=NOT_RUN
PRODUCTION=NOT_RUN
DEPLOY=NOT_RUN
NEXT_TASK=UNCHANGED
```

The baseline classification is `BASELINE_SUPPORTED`.
That classification routes to Owner review and does not authorize tuning,
strategy redesign, production publication, or WS1/WS2/WS4 work.
