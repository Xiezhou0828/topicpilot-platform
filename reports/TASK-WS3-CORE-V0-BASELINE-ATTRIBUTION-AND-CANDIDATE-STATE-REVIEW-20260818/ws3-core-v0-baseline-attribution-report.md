# WS3 Core V0 Baseline Attribution and Candidate-State Review

## Required headline fields

```text
TASK_FINAL_STATUS=COMPLETE_CORE_V0_BASELINE_ATTRIBUTION
SOURCE_BASELINE_TASK=TASK-WS3-CORE-V0-REAL-HISTORICAL-WALK-FORWARD-BASELINE-20260818
SOURCE_BASELINE_HEAD=9ca9ba4f15359aa5ea96ba4c3d6bed9439d0346e
CORE_V0_FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d
FROZEN_SPEC_CHANGED=NO
PARAMETER_OPTIMIZATION_EXECUTED=NO
LOOKAHEAD_LEAKAGE_DETECTED=NO
ATTRIBUTION_REPRODUCIBLE=YES
TOTAL_SIGNAL_OBSERVATIONS=1212
A1_SIGNAL_OBSERVATIONS=700
A1_UNIQUE_INSTRUMENTS=297
A1_ACTIVE_SIGNAL_DATES=66
A2_SIGNAL_OBSERVATIONS=512
A2_UNIQUE_INSTRUMENTS=320
A2_ACTIVE_SIGNAL_DATES=62
A1_T1_MEAN=0.006237143832012744
A1_T1_MEDIAN=0.0
A1_T1_WIN_RATE=0.4933920704845815
A1_T3_MEAN=0.013089157524164601
A1_T3_MEDIAN=0.002881844380403458
A1_T3_WIN_RATE=0.5238828967642527
A1_T5_MEAN=0.020637173727993056
A1_T5_MEDIAN=0.003976158856636944
A1_T5_WIN_RATE=0.5294117647058824
A1_T10_MEAN=0.04758732410234259
A1_T10_MEDIAN=0.011928476569910832
A1_T10_WIN_RATE=0.5764925373134329
A2_T1_MEAN=0.013336499095067261
A2_T1_MEDIAN=0.004884004884004884
A2_T1_WIN_RATE=0.5346534653465347
A2_T3_MEAN=0.017082845659529257
A2_T3_MEDIAN=0.002680160875585152
A2_T3_WIN_RATE=0.5040983606557377
A2_T5_MEAN=0.026113584459963746
A2_T5_MEDIAN=0.0112451958928469
A2_T5_WIN_RATE=0.5448717948717948
A2_T10_MEAN=0.04034718260556977
A2_T10_MEDIAN=0.0006775067750677507
A2_T10_WIN_RATE=0.5
A1_VALUE_BEYOND_MA60=POSITIVE
A2_VALUE_BEYOND_MA60=POSITIVE
A1_VS_A2_FORWARD_EDGE=INCONCLUSIVE
A1_BASELINE_CLASSIFICATION=PROMISING_BUT_INSUFFICIENT
A2_BASELINE_CLASSIFICATION=PROMISING_BUT_INSUFFICIENT
A1_STABLE_ACROSS_WINDOWS=INCONCLUSIVE
A2_STABLE_ACROSS_WINDOWS=INCONCLUSIVE
A1_OUTLIER_CONCENTRATION_RISK=MEDIUM
A2_OUTLIER_CONCENTRATION_RISK=LOW
A1_TO_A2_TRANSITION_COUNT=386
A1_TO_A2_TRANSITION_RATE=0.5514285714285714
MEDIAN_SESSIONS_A1_TO_A2=4.0
FORMAL_PRE_BREAKOUT_STATE_AVAILABLE=YES
CORE_V0_PERFORMANCE_ATTRIBUTION=BROAD_BASED_ACROSS_A1_A2
TAIHONG_STYLE_QUALITATIVE_INTUITION_INDEPENDENTLY_SUPPORTED=YES
CORE_V0_STRATEGY_CHANGED=NO
MA60_POLICY_CHANGED=NO
WS1_CHANGED=NO
WS2_CHANGED=NO
WS4_CHANGED=NO
PRODUCTION_CHANGED=NO
READY_FOR_WS3_BASELINE_REVIEW=YES
READY_FOR_WS3_NEXT_MAINLINE_STEP=READY_FOR_BOUNDED_CONFIRMATION_VALIDATION
REMAINING_WS3_BLOCKERS=NO_FORMAL_EPISODE_SCORE_OR_SELECTION_CONTRACT; ATTRIBUTION_IS_RESEARCH_ONLY
FILES_CHANGED=15 task-owned files (runner, focused tests, and 13 evidence artifacts)
TESTS=29 passed; focused attribution, baseline, candidate-panel, coverage, and research-policy tests
TASK_COMMIT_SHA=4f1e55eb86b8f622dafa9b86b0789940d54ddf13
```

## Scope and frozen authority

This is attribution of the accepted real-data Core V0 baseline. The frozen A1 and A2 definitions, prior-20 reference, T exclusion, five-session maturity, A1 3% proximity, A2 close confirmation, MA60 rule, event-aware policy, and forward outcome methodology are unchanged.

No A3, Catch-up, shadow Opportunity, score, ranking, daily Top-N, technical filter, cost assumption, benchmark, stop-loss, entry rule, or strategy variant was introduced.

## Interpretation

A1 is PROMISING_BUT_INSUFFICIENT and A2 is PROMISING_BUT_INSUFFICIENT under the frozen comparison surface. The direct A1-versus-A2 result is INCONCLUSIVE; this is not a strategy-selection decision.

Core V0 attribution is BROAD_BASED_ACROSS_A1_A2. A1/A2 transition, persistence, first/repeated A2, and later-A2 splits are descriptive diagnostics only. outcomesFlowBackward=false.

The historical pre-breakout intuition is evaluated only through the frozen A1 state. No named instrument or qualitative example was used as a target or tuning criterion.

## Quality and lifecycle state

Source reconciliation: True; frozen hash unchanged: True; look-ahead violations: 0; state mutation based on outcome: False; event-aware policy preserved: True.

```text
ATTRIBUTION=EXECUTED_RESEARCH_ONLY
STRATEGY_REVIEW=NOT_RUN
PARAMETER_OPTIMIZATION=NOT_RUN
RECOMMENDATION_PUBLICATION=NOT_RUN
MIGRATION=NOT_RUN
PRODUCTION=NOT_RUN
DEPLOY=NOT_RUN
NEXT_TASK=UNCHANGED
```

## Candidate-state inventory

| State | Version | Raw observations | Instruments | Active dates | First | Last |
| --- | --- | ---: | ---: | ---: | --- | --- |
| A1_PRE_BREAKOUT | core-v0-a1-pre-breakout.v1 | 700 | 297 | 66 | 2026-05-12 | 2026-08-13 |
| A2_CONFIRMED_BREAKOUT | core-v0-a2-confirmed-breakout.v1 | 512 | 320 | 62 | 2026-05-12 | 2026-08-13 |

## State forward attribution

| State | Horizon | Evaluable | Censored | Event excluded | Mean | Median | Win rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | T+1 | 681 | 13 | 6 | 0.00623714 | 0.00000000 | 0.49339207 |
| A1 | T+3 | 649 | 34 | 17 | 0.01308916 | 0.00288184 | 0.52388290 |
| A1 | T+5 | 612 | 54 | 34 | 0.02063717 | 0.00397616 | 0.52941176 |
| A1 | T+10 | 536 | 90 | 74 | 0.04758732 | 0.01192848 | 0.57649254 |
| A2 | T+1 | 505 | 3 | 4 | 0.01333650 | 0.00488400 | 0.53465347 |
| A2 | T+3 | 488 | 9 | 15 | 0.01708285 | 0.00268016 | 0.50409836 |
| A2 | T+5 | 468 | 14 | 30 | 0.02611358 | 0.01124520 | 0.54487179 |
| A2 | T+10 | 428 | 29 | 55 | 0.04034718 | 0.00067751 | 0.50000000 |

## Persistence and concentration

Persistence is defined as same-state presence on the immediately prior canonical instrument session. It is descriptive only; no trade episode is inferred.

| State | Consecutive persistence rate | Median persistence days | Max persistence days | Top-5 date share | Top-10 instrument signal share | Top-10 instrument positive P&L share (T+5) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 0.28571429 | 1.0 | 15 | 0.19285714 | 0.21714286 | 0.22962521 |
| A2 | 0.04296875 | 1.0 | 3 | 0.27343750 | 0.06835938 | 0.19450648 |

## Transition and component diagnostics

A1-to-A2 transitions: 386 raw A1 observations (0.55142857); median 4.0 sessions, P25 1.0, P75 10.0. This is post-hoc attribution only and outcomesFlowBackward=false.

A1 observations that later reach A2 and those that do not are reported in `ws3-core-v0-a1-transition-outcome-diagnostic.csv` as POST_HOC_OUTCOME_DIAGNOSTIC_ONLY / NOT_A_FORMATION_RULE.
A2 first-versus-repeated observations use only the descriptive previous-session-same-state flag; formal episode semantics remain NOT_FORMALLY_DEFINED.

Frozen evidence-level availability: MA60 and prior-20 reference are formation inputs. Volume, RSI, MACD, MA slope, and short-return fields are not present in the frozen candidate record and were not reconstructed or filtered.
