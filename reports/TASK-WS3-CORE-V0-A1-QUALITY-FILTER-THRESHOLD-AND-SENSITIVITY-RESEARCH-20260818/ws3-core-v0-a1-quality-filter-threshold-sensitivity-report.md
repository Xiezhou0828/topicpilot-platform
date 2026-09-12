# WS3 Core V0 A1 Quality-Filter Threshold and Sensitivity Research

## Final contract

```text
TASK_FINAL_STATUS=COMPLETE_A1_QUALITY_FILTER_THRESHOLD_SENSITIVITY_RESEARCH
SOURCE_CANONICAL_HEAD=035587e4f263447e778f9384971885e03a53ecc2
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
A1_TOTAL_COUNT=700
A1_SUCCESSFUL_COUNT=386
A1_FAILED_BREAKOUT_COUNT=214
PRIMARY_ROBUST_FEATURE_COUNT=20
PRIMARY_SELECTED_FEATURE_COUNT=7
PRIMARY_SELECTED_FEATURES=recent_20_high_proximity;recent_20_high_age_sessions;return_5d;close_ma20_distance;volume_ratio_5;true_range_pct;same_day_volume_ratio_20_percentile
HIGH_REDUNDANCY_PAIR_COUNT=0
SINGLE_FEATURE_THRESHOLD_REGION_COUNT=49
ROBUST_THRESHOLD_REGION_COUNT=6
PROMISING_THRESHOLD_REGION_COUNT=0
NO_DEFENSIBLE_THRESHOLD_REGION_COUNT=43
THRESHOLD_PLATEAU_CANDIDATE_COUNT=48
TOP_SINGLE_FEATURE_CANDIDATES=true_range_pct__LOWER_LE_Q70;recent_20_high_proximity__UPPER_GE_Q30;return_5d__LOWER_LE_Q60
TWO_FEATURE_COMBINATIONS_TESTED=3
TOP_TWO_FEATURE_COMBINATION_CANDIDATES=recent_20_high_proximity__AND__true_range_pct
UNFILTERED_A1_SUCCESS_RATE=0.6433333333333333
BEST_DEFENSIBLE_FILTERED_SUCCESS_RATE=0.6940639269406392
BEST_DEFENSIBLE_FAILED_BREAKOUT_RATE=0.3059360730593607
BEST_DEFENSIBLE_RETENTION_RATE=0.7357142857142858
FAILED_BREAKOUT_REDUCTION_SUPPORTED=YES
SUCCESSFUL_A1_RETENTION_SUPPORTED=YES
JULY_VALIDATION_IMPROVEMENT_SUPPORTED=YES
DATE_CONCENTRATION_ACCEPTABLE=YES
INSTRUMENT_CONCENTRATION_ACCEPTABLE=YES
TPE_TWO_DIRECTIONALLY_CONSISTENT=YES
LOOK_AHEAD_LEAKAGE_DETECTED=NO
OUTCOME_DERIVED_FEATURE_USED=NO
THRESHOLD_DENSE_OPTIMIZATION_USED=NO
RETURN_OPTIMIZATION_USED=NO
PARAMETER_SEARCH_USED=NO
CORE_V0_CHANGED=NO
A1_DEFINITION_CHANGED=NO
A2_DEFINITION_CHANGED=NO
MA60_POLICY_CHANGED=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
REPRODUCIBLE=PASS
A1_QUALITY_FILTER_THRESHOLD_RESEARCH_SUPPORTED=YES
READY_FOR_A1_FILTER_CONFIRMATORY_VALIDATION=YES
READY_FOR_A1_PRODUCTION_FILTER=NO
REMAINING_RESEARCH_RISKS=NO_PRODUCTION_AUTHORITY; CONFIRMATORY_OUT_OF_SAMPLE_VALIDATION_REQUIRED; JULY_ENVIRONMENT_REMAINS_WEAK
FILES_CHANGED=research module; focused tests; 10 research artifacts
TESTS=FOCUSED_PASS_EXISTING_CORE_V0_PASS_REPLAY_HASH_EQUAL
TASK_COMMIT_SHA=9f67396
ANALYTICAL_ARTIFACTS_SHA256=2c3fc13503856016c1ce0465763dd4adc91c33f3924a9cca778a0c1d684da724
SOURCE_CANONICAL_HEAD=035587e4f263447e778f9384971885e03a53ecc2
PRIOR_RESEARCH_SOURCE_HEAD=3ab70b612cbb30335b43a5650d145488f9e8b2c1
SOURCE_BASELINE_HEAD=9ca9ba4f15359aa5ea96ba4c3d6bed9439d0346e
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
ANALYTICAL_ARTIFACTS_SHA256=2c3fc13503856016c1ce0465763dd4adc91c33f3924a9cca778a0c1d684da724
TASK_COMMIT_SHA=9f67396
TESTS=FOCUSED_PASS_EXISTING_CORE_V0_PASS_REPLAY_HASH_EQUAL
```

## Authority and selection provenance

The prior task is TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818; its committed evidence remains the only feature-selection authority. The prior manifest has 40 PIT-valid features, with 20 prior ROBUST_CANDIDATE features. This task selected exactly 7 features before threshold evaluation.

Selected features and reasons:
- recent_20_high_proximity (BREAKOUT_PROXIMITY): Prior robust BREAKOUT_PROXIMITY evidence, directionally consistent in Development/Validation/Holdout, and prior date-centered stock-level signal.
- recent_20_high_age_sessions (CONSOLIDATION_STRUCTURE): Prior robust CONSOLIDATION_STRUCTURE evidence with a large stable effect and no prior date-regime flag.
- return_5d (MOMENTUM): Prior robust MOMENTUM evidence, stable lower-in-success direction, and no prior date-regime flag.
- close_ma20_distance (MA_STRUCTURE): Prior robust MA_STRUCTURE evidence, stable lower-in-success direction, and stock-level date-centered signal.
- volume_ratio_5 (VOLUME_CONFIRMATION): Prior robust VOLUME_CONFIRMATION evidence with stable direction and no prior date-regime flag.
- true_range_pct (VOLATILITY): Prior top robust VOLATILITY evidence, stable direction, and the strongest prior stock-level effect among the selected families.
- same_day_volume_ratio_20_percentile (RELATIVE_CONTEXT): Prior robust RELATIVE_CONTEXT evidence, stable direction, and a distinct cross-sectional participation interpretation.

## Reverse dependency for WS1/WS2 planning

This task closes only the A1 candidate-specific minimum panel. It does not require complete Historical Topic/System State or WS2 technical publication; the exact bounded dependency is recorded in the summary JSON.
{"candidate_type": "A1_PRE_BREAKOUT", "minimum_panel": {"canonical_ohlcv_fields": ["close", "high", "low", "volume"], "evaluation_context": ["evaluation_session", "signal_date", "instrument_id", "market (TPE/TWO)", "as_of_timestamp <= signal_date"], "formation_boundary": "Candidate formation consumes only information effective/observable <= T; candidate state is frozen at T. Forward outcomes cannot alter eligibility.", "forward_outcomes_evaluation_only": ["T+1", "T+3", "T+5", "T+10", "REC-A1 event-aware outcome exclusion metadata"], "pit_membership_and_candidate_context": ["A1_PRE_BREAKOUT membership/context at T", "candidate_inputs.reference_value as observed at T", "canonical cohort/source lineage"], "selected_feature_dependencies": [{"category": "BREAKOUT_PROXIMITY", "feature_name": "recent_20_high_proximity", "lookback": "20 sessions including T", "point_in_time_available": true, "required_input_columns": ["high", "close"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "CONSOLIDATION_STRUCTURE", "feature_name": "recent_20_high_age_sessions", "lookback": "20 sessions including T", "point_in_time_available": true, "required_input_columns": ["high"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "MOMENTUM", "feature_name": "return_5d", "lookback": "6 sessions", "point_in_time_available": true, "required_input_columns": ["close"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "MA_STRUCTURE", "feature_name": "close_ma20_distance", "lookback": "20 sessions", "point_in_time_available": true, "required_input_columns": ["close"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "VOLUME_CONFIRMATION", "feature_name": "volume_ratio_5", "lookback": "5 sessions", "point_in_time_available": true, "required_input_columns": ["volume"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "VOLATILITY", "feature_name": "true_range_pct", "lookback": "1 session", "point_in_time_available": true, "required_input_columns": ["high", "low", "close"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}, {"category": "RELATIVE_CONTEXT", "feature_name": "same_day_volume_ratio_20_percentile", "lookback": "20 sessions per instrument and date cross-section", "point_in_time_available": true, "required_input_columns": ["volume"], "source_lineage": "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved", "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP"}], "technical_evidence_fields": []}, "scope": "A1 quality-filter threshold research only; no global WS3 readiness gate", "source_lineage": {"event_dataset_is_evaluation_integrity_only": true, "frozen_spec_hash": "6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d", "prior_research_source_head": "3ab70b612cbb30335b43a5650d145488f9e8b2c1", "research_read_model": "canonical Postgres historical read model via read_historical_bars; REC-A1 event-aware research dataset preserved"}, "ws1_ws2_implication": "No complete Historical Topic/System State or WS2 technical publication is required for this A1 panel; only the listed candidate-specific fields are a dependency for this research lane."}

## Method boundary

Thresholds are train-derived Q20/Q30/Q40/Q50/Q60/Q70/Q80 regions, applied unchanged to Validation, Holdout, and Full Sample. The expected direction comes from the prior success-versus-failed evidence. No dense numeric search, return optimization, or exact optimal cutoff was used.

The primary target is successful A1 versus failed-breakout A1. Retention includes all A1 observations, while success/failure rates use resolved primary cohorts. T+1/T+3/T+5/T+10 are post-selection diagnostic outcomes only.

Redundancy used pairwise Spearman rank correlation without labels; 0 high-redundancy pairs were identified. They were not silently removed or treated as independent confirmation.

## Results

Top single-feature research candidates: [{'candidate_type': 'SINGLE_FEATURE', 'candidate_id': 'true_range_pct__LOWER_LE_Q70', 'feature_or_combination': 'true_range_pct', 'market_interpretation': 'Prior top robust VOLATILITY evidence, stable direction, and the strongest prior stock-level effect among the selected families.', 'defensible_threshold_region': 'true_range_pct__LOWER_LE_Q70', 'threshold_value_not_a_production_cut': 0.06408819993349192, 'full_sample_success_rate_delta': 0.05073059360730592, 'validation_success_rate_delta': 0.0811962170912498, 'failed_breakout_reduction': 0.050730593607305974, 'retention_rate': 0.7357142857142858, 'july_behavior': 'YES', 'threshold_plateau': 'YES', 'date_concentration': 'LOW', 'instrument_concentration': 'MEDIUM', 'forward_return_diagnostics': {'T+1': {'N': 435, 'mean': 0.0077525281697734425, 'median': 0.001694915254237288, 'win_rate': 0.5241379310344828}, 'T+3': {'N': 425, 'mean': 0.01551082934298088, 'median': 0.00398406374501992, 'win_rate': 0.5576470588235294}, 'T+5': {'N': 410, 'mean': 0.02232264852419146, 'median': 0.00705872594558726, 'win_rate': 0.5707317073170731}, 'T+10': {'N': 367, 'mean': 0.04928950951866369, 'median': 0.014492753623188406, 'win_rate': 0.6021798365122616}}, 'major_caveat': 'Research candidate only; no production filter authority and no exact optimal cutoff claimed.', 'research_classification': 'STRONG_RESEARCH_CANDIDATE'}, {'candidate_type': 'SINGLE_FEATURE', 'candidate_id': 'recent_20_high_proximity__UPPER_GE_Q30', 'feature_or_combination': 'recent_20_high_proximity', 'market_interpretation': 'Prior robust BREAKOUT_PROXIMITY evidence, directionally consistent in Development/Validation/Holdout, and prior date-centered stock-level signal.', 'defensible_threshold_region': 'recent_20_high_proximity__UPPER_GE_Q30', 'threshold_value_not_a_production_cut': -0.02684279376635195, 'full_sample_success_rate_delta': 0.05111111111111111, 'validation_success_rate_delta': 0.07247298156389059, 'failed_breakout_reduction': 0.05111111111111111, 'retention_rate': 0.7185714285714285, 'july_behavior': 'YES', 'threshold_plateau': 'YES', 'date_concentration': 'LOW', 'instrument_concentration': 'MEDIUM', 'forward_return_diagnostics': {'T+1': {'N': 430, 'mean': 0.009913430790356993, 'median': 0.0017376312658892866, 'win_rate': 0.5279069767441861}, 'T+3': {'N': 420, 'mean': 0.01835955606368501, 'median': 0.005363189952040706, 'win_rate': 0.5714285714285714}, 'T+5': {'N': 407, 'mean': 0.02895989112443591, 'median': 0.008032128514056224, 'win_rate': 0.5847665847665847}, 'T+10': {'N': 362, 'mean': 0.054664284903288965, 'median': 0.018424439477071057, 'win_rate': 0.6270718232044199}}, 'major_caveat': 'Research candidate only; no production filter authority and no exact optimal cutoff claimed.', 'research_classification': 'STRONG_RESEARCH_CANDIDATE'}, {'candidate_type': 'SINGLE_FEATURE', 'candidate_id': 'return_5d__LOWER_LE_Q60', 'feature_or_combination': 'return_5d', 'market_interpretation': 'Prior robust MOMENTUM evidence, stable lower-in-success direction, and no prior date-regime flag.', 'defensible_threshold_region': 'return_5d__LOWER_LE_Q60', 'threshold_value_not_a_production_cut': 0.07389330024813896, 'full_sample_success_rate_delta': 0.05103663985701523, 'validation_success_rate_delta': 0.13920143383451156, 'failed_breakout_reduction': 0.05103663985701523, 'retention_rate': 0.6185714285714285, 'july_behavior': 'YES', 'threshold_plateau': 'YES', 'date_concentration': 'LOW', 'instrument_concentration': 'MEDIUM', 'forward_return_diagnostics': {'T+1': {'N': 370, 'mean': 0.005347736730367911, 'median': 0.001039024126949857, 'win_rate': 0.5027027027027027}, 'T+3': {'N': 360, 'mean': 0.016956119237363298, 'median': 0.004179463911768812, 'win_rate': 0.575}, 'T+5': {'N': 352, 'mean': 0.028247490880906802, 'median': 0.008021404710966698, 'win_rate': 0.5965909090909091}, 'T+10': {'N': 318, 'mean': 0.06241285334527426, 'median': 0.019687785821693768, 'win_rate': 0.6477987421383647}}, 'major_caveat': 'Research candidate only; no production filter authority and no exact optimal cutoff claimed.', 'research_classification': 'STRONG_RESEARCH_CANDIDATE'}].
Top two-feature research candidates: [{'candidate_type': 'TWO_FEATURE_COMBINATION', 'candidate_id': 'recent_20_high_proximity__AND__true_range_pct', 'feature_or_combination': 'recent_20_high_proximity AND true_range_pct', 'defensible_threshold_region': 'recent_20_high_proximity__UPPER_GE_Q30 AND true_range_pct__LOWER_LE_Q70', 'full_sample_success_rate_delta': 0.08687194525904207, 'validation_success_rate_delta': 0.11434250444607175, 'failed_breakout_reduction': 0.08687194525904207, 'retention_rate': 0.5757142857142857, 'july_behavior': 'YES', 'threshold_plateau': 'INHERITED_FROM_SINGLE_REGIONS', 'date_concentration': 'LOW', 'instrument_concentration': 'MEDIUM', 'forward_return_diagnostics': {'T+1': {'N': 340, 'mean': 0.008774656819116152, 'median': 0.0015305177364082615, 'win_rate': 0.5294117647058824}, 'T+3': {'N': 332, 'mean': 0.01706955102953291, 'median': 0.004179463911768812, 'win_rate': 0.572289156626506}, 'T+5': {'N': 320, 'mean': 0.021592760367210827, 'median': 0.007458881121474531, 'win_rate': 0.58125}, 'T+10': {'N': 285, 'mean': 0.04625299236327662, 'median': 0.013245033112582781, 'win_rate': 0.6210526315789474}}, 'major_caveat': 'Bounded two-feature diagnostic only; complexity must be confirmed out of sample.', 'research_classification': 'PROMISING_RESEARCH_CANDIDATE'}].

The trade-off artifact reports every tested region's quality delta against unfiltered A1 alongside A1 retention. Any low-sample region is explicitly marked INSUFFICIENT_SAMPLE; no production minimum was introduced.

## July validation and concentration

July is reported as the frozen Validation segment separately. A region is not promoted to robust merely because its full-sample aggregate is attractive; temporal direction, July behavior, date concentration, instrument concentration, and TPE/TWO split are all included in the classification.

## Safety and lifecycle

This is discrimination research only. Core V0, A1, A2, MA60, baseline formation, labels, WS1/WS2/WS4, NEXT_TASK, production persistence, API/UI/provider/scheduler/deploy surfaces were not changed. No production filter or trading rule was created.

reproducible=True; threshold_leakage=False; outcome_derived_feature_used=False; return_optimization_used=False; parameter_search_used=False; database_writes=False; production_filter_created=False.

```text
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
PUSH_REMOTE=NO
DEPLOY=NOT_RUN
MIGRATION=NOT_RUN
```
