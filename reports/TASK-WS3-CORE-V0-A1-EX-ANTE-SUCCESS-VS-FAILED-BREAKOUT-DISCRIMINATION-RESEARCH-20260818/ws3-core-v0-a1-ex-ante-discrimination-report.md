# WS3 Core V0 A1 Ex-Ante Success vs Failed-Breakout Discrimination Research

## Final readiness contract

```text
TASK_FINAL_STATUS=COMPLETE_A1_EX_ANTE_DISCRIMINATION_RESEARCH
FROZEN_SPEC_CHANGED=NO
A1_TOTAL_COUNT=700
SUCCESSFUL_A1_COUNT=386
FAILED_BREAKOUT_A1_COUNT=214
CONTINUED_CONSOLIDATION_COUNT=30
STRUCTURE_LOSS_COUNT=37
UNCLASSIFIED_COUNT=33
FEATURE_MANIFEST_FROZEN=YES
TOTAL_FEATURE_COUNT=40
POINT_IN_TIME_VALID_FEATURE_COUNT=40
UNAVAILABLE_FEATURE_COUNT=0
LOOK_AHEAD_LEAKAGE_DETECTED=NO
OUTCOME_DERIVED_FEATURE_DETECTED=NO
THRESHOLD_OPTIMIZATION_EXECUTED=NO
PARAMETER_SEARCH_EXECUTED=NO
ROBUST_CANDIDATE_FEATURE_COUNT=20
PROMISING_FEATURE_COUNT=12
REGIME_CONFOUNDED_FEATURE_COUNT=2
UNSTABLE_FEATURE_COUNT=6
NO_CLEAR_EVIDENCE_FEATURE_COUNT=0
TOP_FEATURE_FAMILIES=BREAKOUT_PROXIMITY;CANDLE_REJECTION;CONSOLIDATION_STRUCTURE;MARKET_REGIME;MA_STRUCTURE;MOMENTUM;RELATIVE_CONTEXT;TECHNICAL_INDICATORS;VOLATILITY;VOLUME_CONFIRMATION
VOLUME_CONFIRMATION_EVIDENCE=STRONG_CANDIDATE
BREAKOUT_PROXIMITY_EVIDENCE=STRONG_CANDIDATE
MA_STRUCTURE_EVIDENCE=STRONG_CANDIDATE
CANDLE_REJECTION_EVIDENCE=PROMISING_BUT_INSUFFICIENT
CONSOLIDATION_STRUCTURE_EVIDENCE=STRONG_CANDIDATE
MARKET_REGIME_EVIDENCE=PROMISING_BUT_INSUFFICIENT
STOCK_LEVEL_DISCRIMINATION_EXISTS=YES
MARKET_REGIME_CONFOUNDING_MATERIAL=YES
MULTIVARIATE_DIAGNOSTIC_EXECUTED=YES
MULTIVARIATE_VALIDATION_RESULT=DIAGNOSTIC_ONLY_NO_PRODUCTION_CLAIM
A1_EX_ANTE_DISCRIMINATION_SUPPORTED=YES
A1_QUALITY_FILTER_RESEARCH_CANDIDATE=YES_RESEARCH_CANDIDATE
READY_FOR_A1_THRESHOLD_SENSITIVITY_RESEARCH=YES
READY_FOR_A1_PRODUCTION_FILTER=NO
CORE_V0_CLASSIFICATION=BASELINE_SUPPORTED
CORE_V0_CHANGED=NO
A1_CHANGED=NO
A2_CHANGED=NO
MA60_POLICY_CHANGED=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
ANALYTICAL_ARTIFACTS_SHA256=788e5f05769dabde10da461b694fbfaa189e13408c39229eb29783144cc67df6
SOURCE_CANONICAL_HEAD=3ab70b612cbb30335b43a5650d145488f9e8b2c1
SOURCE_BASELINE_HEAD=9ca9ba4f15359aa5ea96ba4c3d6bed9439d0346e
FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
DATASET_AUTHORITY=canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved
TASK_COMMIT_SHA=4d6d8b06d3e6f9baed017f9f6fe572b985640c65
TESTS=ruff check PASS; py_compile PASS; test_core_v0_candidate_panel 11 passed; normalized analytical hash replay PASS
```

## Authority and temporal boundary

This is a research-only diagnostic over the frozen Core V0 A1 cohort. A1 and A2 definitions, MA60 eligibility, transition definition, failure taxonomy, validation segments, and the REC-A1 event-aware policy are unchanged.

SUCCESSFUL_A1 and FAILED_BREAKOUT_A1 are outcome labels. They are never present in the feature matrix. Every predictor is derived from canonical OHLCV and frozen candidate reference inputs through T; outcomesFlowBackward=false.

## Cohort reconciliation

The primary comparison is 386 SUCCESSFUL_A1 observations versus 214 FAILED_BREAKOUT_A1 observations. Secondary controls are consolidation=30, structure loss=37, and unclassified=33. Reconciliation pass=True.

## Frozen feature inventory

The manifest freezes 40 features before outcome comparison; 40 are timestamp-valid by construction and 0 are wholly unavailable in the observed A1 matrix. No feature hunting, threshold search, or future-derived feature was performed.

## Univariate, monotonicity, and stability findings

Top descriptive findings by absolute standardized effect are: [{'feature_name': 'true_range_pct', 'category': 'VOLATILITY', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.5322531897909484, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'recent_20_high_age_sessions', 'category': 'CONSOLIDATION_STRUCTURE', 'classification': 'ROBUST_CANDIDATE', 'direction': 'HIGHER_IN_SUCCESS', 'standardized_effect_size': 0.5020920293309611, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'realized_volatility_20', 'category': 'VOLATILITY', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.4460546997935751, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'atr14_pct', 'category': 'VOLATILITY', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.43967638164733197, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'recent_20_close_range_location', 'category': 'BREAKOUT_PROXIMITY', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.42526128532649604, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'recent_20_high_proximity', 'category': 'BREAKOUT_PROXIMITY', 'classification': 'ROBUST_CANDIDATE', 'direction': 'HIGHER_IN_SUCCESS', 'standardized_effect_size': 0.4176730398758115, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'reference_below_high_streak', 'category': 'CONSOLIDATION_STRUCTURE', 'classification': 'ROBUST_CANDIDATE', 'direction': 'HIGHER_IN_SUCCESS', 'standardized_effect_size': 0.4124057761549246, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'return_5d', 'category': 'MOMENTUM', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.40980491472298386, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'close_ma20_distance', 'category': 'MA_STRUCTURE', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.369109699342304, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}, {'feature_name': 'same_day_volume_ratio_20_percentile', 'category': 'RELATIVE_CONTEXT', 'classification': 'ROBUST_CANDIDATE', 'direction': 'LOWER_IN_SUCCESS', 'standardized_effect_size': -0.3398040338924812, 'validation_consistent': 'YES', 'date_regime_confounding': 'NO'}].
Time stability uses the frozen Development/Validation segments. Stable means direction agreement only; a validation effect that is weak or contradictory is not promoted to ROBUST_CANDIDATE. Feature families: [{'feature_family': 'BREAKOUT_PROXIMITY', 'feature_count': 4, 'classification_counts': {'PROMISING_BUT_INSUFFICIENT': 1, 'ROBUST_CANDIDATE': 3}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['recent_20_close_range_location', 'recent_20_high_proximity', 'reference_touch_count_20', 'reference_gap_pct'], 'not_a_strategy_rule': True}, {'feature_family': 'CANDLE_REJECTION', 'feature_count': 5, 'classification_counts': {'UNSTABLE': 1, 'PROMISING_BUT_INSUFFICIENT': 4}, 'assessment': 'PROMISING_BUT_INSUFFICIENT', 'top_features': ['close_location_value', 'upper_wick_range_fraction', 'lower_wick_range_fraction', 'gap_pct', 'candle_body_range_fraction'], 'not_a_strategy_rule': True}, {'feature_family': 'CONSOLIDATION_STRUCTURE', 'feature_count': 2, 'classification_counts': {'ROBUST_CANDIDATE': 2}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['recent_20_high_age_sessions', 'reference_below_high_streak'], 'not_a_strategy_rule': True}, {'feature_family': 'MARKET_REGIME', 'feature_count': 5, 'classification_counts': {'PROMISING_BUT_INSUFFICIENT': 3, 'UNSTABLE': 2}, 'assessment': 'PROMISING_BUT_INSUFFICIENT', 'top_features': ['same_day_universe_median_return_5d', 'same_day_universe_breadth_above_ma60', 'same_day_signal_density', 'trailing_20d_breadth_above_ma60', 'same_day_universe_median_return_1d'], 'not_a_strategy_rule': True}, {'feature_family': 'MA_STRUCTURE', 'feature_count': 6, 'classification_counts': {'ROBUST_CANDIDATE': 2, 'UNSTABLE': 2, 'PROMISING_BUT_INSUFFICIENT': 1, 'REGIME_CONFOUNDED': 1}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['close_ma20_distance', 'close_ma60_distance', 'ma20_ma60_spread', 'ma60_slope_5d', 'ma20_slope_5d'], 'not_a_strategy_rule': True}, {'feature_family': 'MOMENTUM', 'feature_count': 5, 'classification_counts': {'REGIME_CONFOUNDED': 1, 'ROBUST_CANDIDATE': 3, 'PROMISING_BUT_INSUFFICIENT': 1}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['return_5d', 'return_3d', 'return_10d', 'return_20d', 'return_1d'], 'not_a_strategy_rule': True}, {'feature_family': 'RELATIVE_CONTEXT', 'feature_count': 2, 'classification_counts': {'ROBUST_CANDIDATE': 2}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['same_day_volume_ratio_20_percentile', 'same_day_return_5d_percentile'], 'not_a_strategy_rule': True}, {'feature_family': 'TECHNICAL_INDICATORS', 'feature_count': 3, 'classification_counts': {'ROBUST_CANDIDATE': 1, 'UNSTABLE': 1, 'PROMISING_BUT_INSUFFICIENT': 1}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['rsi14', 'macd_line_12_26', 'macd_histogram_12_26_9'], 'not_a_strategy_rule': True}, {'feature_family': 'VOLATILITY', 'feature_count': 4, 'classification_counts': {'ROBUST_CANDIDATE': 4}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['true_range_pct', 'realized_volatility_20', 'atr14_pct', 'range_compression_5_vs20'], 'not_a_strategy_rule': True}, {'feature_family': 'VOLUME_CONFIRMATION', 'feature_count': 4, 'classification_counts': {'ROBUST_CANDIDATE': 3, 'PROMISING_BUT_INSUFFICIENT': 1}, 'assessment': 'STRONG_CANDIDATE', 'top_features': ['volume_ratio_5', 'volume_ratio_20', 'volume_ma5_ma20_spread', 'volume_expansion_5_vs_prior20'], 'not_a_strategy_rule': True}].

## Date/regime confounding

Date-centered diagnostics subtract the same-day median from each A1 feature using only same-day T observations. This separates stock-level variation from broad date conditions without using later performance.
Stock-level discrimination exists=YES; market-regime confounding material=YES.

## Minimal multivariate diagnostic

Fixed predeclared logistic diagnostic: train ROC-AUC=0.6655584956012394, validation ROC-AUC=0.7217391304347827, train PR-AUC=0.7912233917904046, validation PR-AUC=0.8017344169984844; diagnostic only, not a production model.

## Owner questions

Q1/Q11: YES and threshold sensitivity readiness=YES; no threshold research was executed.
Q2: top feature families=BREAKOUT_PROXIMITY;CANDLE_REJECTION;CONSOLIDATION_STRUCTURE;MARKET_REGIME;MA_STRUCTURE;MOMENTUM;RELATIVE_CONTEXT;TECHNICAL_INDICATORS;VOLATILITY;VOLUME_CONFIRMATION.
Q3: time-stable features are reported in the time-stability artifact; no feature is called robust unless Development and Validation directions agree.
Q4/Q5: market-regime evidence=PROMISING_BUT_INSUFFICIENT; stock-level discrimination=YES.
Q6 volume=STRONG_CANDIDATE; Q7 breakout proximity=STRONG_CANDIDATE; Q8 MA structure=STRONG_CANDIDATE; Q9 candle rejection=PROMISING_BUT_INSUFFICIENT; Q10 consolidation=STRONG_CANDIDATE.
Q12: A1 quality filter=YES_RESEARCH_CANDIDATE; no filter was created.

## Lifecycle and safety

frozen_spec_unchanged=True; cohort_definitions_unchanged=True; lookahead_violations=0; outcome_derived_features=False; threshold_optimization=False; parameter_search=False; reproducibility=PASS.

```text
RESEARCH_ONLY=YES
A1_QUALITY_FILTER_IMPLEMENTED=NO
A1_QUALITY_FILTER_PRODUCTION=NO
STRATEGY_REVIEW=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
MIGRATION=NOT_RUN
PRODUCTION_MUTATION=NOT_RUN
DEPLOY=NOT_RUN
PUSH_REMOTE=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
```
