# Owner Decision Memo — TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822

## Decision

Final disposition: **RESEARCH_CANDIDATE**. This is an evidence-only WS3 robustness study; `JOINT_SIGNAL_ACCEPTED=NO` and `OUT_OF_SAMPLE_SUPPORTED=NO`.

The study tried to disprove the fixed A2 × LEGACY-5 hypothesis with endpoint medians, dispersion, fixed outlier treatment, instrument concentration, calendar/time stability, market split, signal timing, and the predeclared MA60 ablation. It did not change either signal or promote a strategy.

## Fixed cohorts and core counts

- A2_ONLY: 4485 events / 599 instruments.
- LEGACY5_ONLY: 1679 events / 504 instruments.
- BOTH_SAME_SESSION: 560 matched pairs / 1120 source observations.
- BOTH_WITHIN_1_SESSION: 232 matched pairs / 464 source observations.

## Direct answers

1. BOTH T+5 mean is 2.5834%, median 0.4695%; T+10 mean is 5.0841%, median 1.5094%.
2. The prior +5.0841% figure was the BOTH T+10 mean, not its median. The current median is reported explicitly and is not treated as +5.0841%.
3. After fixed 5% trimming, BOTH T+5/T+10 means are 1.8286%/3.7553%; outlier dependence is not decisive.
4. Both signals capture a substantial number of different events: A2_ONLY=4485, LEGACY5_ONLY=1679, same-session BOTH=560.
5. Timing pair counts are Legacy earlier=220, same session=560, A2 earlier=12.
6. The timing table compares A2, LEGACY5, and paired-combined path metrics without changing the fixed ±1 window.
7. Calendar years use 2024/2025/2026; EARLY/LATE uses the fixed dataset midpoint 2025-08-13, not a performance-selected split.
8. Market split is TPE/TWO and is descriptive; no market-specific production rule is proposed.
9. MA60 joint ablation: BOTH same-session H5 is unchanged (2.5834% to 2.5834%); A2_ONLY changes 1.7540% to 1.7426% with MAE -4.6100% to -4.6132%; LEGACY5_ONLY changes 0.7001% to 0.6215% with MAE -5.2578% to -5.7169%. It removes 375 of 2,471 anchors and also removes MFE≥5% opportunities in 173 cases versus 185 non-positive endpoints and 100 MAE≤−5% cases. MA60 remains research-only and is not accepted.
10. Benchmark-adjusted analysis: NOT_AVAILABLE; no PIT-safe accepted benchmark daily series was present.
11. Regime robustness: NOT_AVAILABLE; existing evidence explicitly lacks PIT-safe event-level index/breadth/peer regime data.
12. The MFE/|MAE| ratio is included only as a descriptive excursion ratio, not a risk-adjusted return.
13. Corporate actions remain UNKNOWN_RAW_ONLY; no synthetic adjustment was introduced.
14. No untouched later-period OOS exists in this task; OUT_OF_SAMPLE_SUPPORTED=NO.
15. Minimum next OOS design: freeze definitions and reporting now, accumulate only future sessions after 2026-08-13, and evaluate an untouched later period without threshold or overlap-window changes.

## Governance

`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `JOINT_SIGNAL_ACCEPTED=NO`; `CORE_V0_MUTATION=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`.

Source surface: 288881 accepted rows / 603 instruments / 2024-08-13–2026-08-13. One read-only accepted price surface scan was used only for exact session positions and LEGACY-5 barrier reconstruction; no data download or write occurred.
