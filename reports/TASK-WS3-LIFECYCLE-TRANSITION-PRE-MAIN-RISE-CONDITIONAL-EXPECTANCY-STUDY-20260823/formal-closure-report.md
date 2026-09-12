# Formal Closure — TASK-WS3-LIFECYCLE-TRANSITION-PRE-MAIN-RISE-CONDITIONAL-EXPECTANCY-STUDY-20260823

## Disposition

`RESEARCH_CANDIDATE`. This is a WS3-only, research-only transition study and Strategy
Review input. It is not an accepted strategy, formal Recommendation
publication, Opportunity activation, production filter, or production-ready
result.

## Dataset and protocol identity

- L5 dataset: `WS1-L5-CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`, declared normalized identity `17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95`, 16,250 Topic×Date rows, `2026-02-03..2026-08-13`.
- Historical status: `CURRENT_TAXONOMY`, `RETROSPECTIVE_RESEARCH_ONLY`, `NON_PIT_HISTORICAL_RECONSTRUCTION`; adjustment/corporate-action continuity is `UNKNOWN_RAW_ONLY`.
- Candidate semantics: candidate onset and confirmed entry are separate. Confirmed entry includes `CONFIRMED_TRANSITION` and `JUMP_TRANSITION`; bootstrap prior-state cases are disclosed and are not silently treated as full pre-window evidence.
- Frozen signal contracts: A2 `5277` source events, Legacy-5 `2471` distinct episodes, BOTH same-session `560` pairs / two source observations per pair, and ALL technical source union with same-date duplicates retained.

## Walk-forward and anti-leakage result

The fixed D-3, D-2, D-1 and D0 slices were executed against the L5 topic-date
sequence. D-3 uses only its as-of row and earlier rows, D-2 excludes D-1/D0,
and D-1 excludes D0. D0 is labeled
`CONTEMPORANEOUS_TRANSITION_CONDITIONED`; it is never pooled with pre-transition
evidence as independent predictive lift. Outcome fields are future T+5/T+10
artifacts only and never define events or select signals.

Confirmed MAIN_RISE transition events: **65**. Candidate
onset events: **80**. Full D-3/D-2/D-1 pre-window confirmed
events: **54**.

## Required research answers

1. MAIN_RISE transition events: `65` confirmed entries; `80` candidate-onset events are separately inventoried.
2. Confirmed-entry signal counts by window (A2 / Legacy-5 / BOTH same-session): see `pre-main-rise-signal-join-coverage.csv` and `run-summary.json`; machine-readable values are `{"A2": {"D-1": 8, "D-2": 4, "D-3": 10, "D0": 27}, "BOTH_SAME_SESSION": {"D-1": 0, "D-2": 0, "D-3": 0, "D0": 10}, "LEGACY5": {"D-1": 5, "D-2": 2, "D-3": 1, "D0": 15}}`.
3. Best pre-transition window for ALL technical: T+5 `D-3 (mean 9.17%, median 9.96%)`; T+10 `D-1 (mean 17.63%, median 15.38%)`. This is descriptive and not an acceptance rule.
4. Mean vs median: the report preserves both. Any disagreement is an outlier/skew warning; no mean-only conclusion is used.
5. D-1 versus technical-alone baseline: T+5 mean delta `0.060546`, median delta `0.068581`; T+10 mean delta `0.118686`, median delta `0.130963`.
6. D-2/D-3 incremental evidence: see `transition-day-vs-pretransition-comparison.csv` and the delta columns in `pre-main-rise-conditional-expectancy.csv`; no window is promoted by this report.
7. D0 conditioning: MAIN_RISE uses same-day constituent price evidence thresholds, so D0 is contemporaneous conditioning and cannot establish independent predictive lift.
8. MAE/path risk: `pre-main-rise-path-risk-analysis.csv` reports MAE, MFE, barrier races, same-session-order-unknown counts/rates, and comparison to technical-alone. Mean-only improvement is insufficient.
9. Signal/opportunity cost: `sample-retention-and-opportunity-cost.csv` reports retained percentage and removed opportunities against each same-cohort technical-alone baseline.
10. Concentration: `robustness-concentration-audit.csv` reports top-1/top-5 topic, instrument, and date shares plus extreme/winner concentration.
11. Raw Strength trajectory: `strength-trajectory-analysis.csv` reports raw vector levels and as-of deltas for D-3→D-2→D-1; no score, label, 0–100 value, or production threshold was created.
12. Incremental research value: disposition is `RESEARCH_CANDIDATE` only; evidence is descriptive transition-context evidence with all PIT/lineage limitations preserved.
13. Production filter: **NO**. No owner-approved acceptance protocol, production filter, accepted strategy, or production-ready claim was created.
14. Next robustness/OOS window: use the strongest non-D0 pre-transition window only as a predeclared candidate for a later untouched post-`2026-08-13` OOS/robustness study; freeze semantics and do not select future windows on outcomes.

## Controls and limitations

- Negative control exact matching is `NOT_AVAILABLE_EXACT_MATCHING_NOT_PERFORMED`; the file provides descriptive stratification by signal type and early/middle/late period and discloses prior five-session return where available.
- Missing topic matches, ambiguous relations, missing lifecycle rows, missing prior windows, incomplete strength, fail-closed lineage, and unmatured outcomes remain explicit; no browser-side or ad-hoc replacement was used.
- Corporate-action and adjustment authority remains `UNKNOWN_RAW_ONLY`; results are not exact economic-return truth.
- Full-suite application test-count delta is not applicable because this task is research-only and changed no application/runtime/test surface.

## Governance

`WS3_ONLY=YES`, `RESEARCH_ONLY=YES`, `E_DRIVE_ONLY=YES`,
`C_DRIVE_NEW_ARTIFACTS_CREATED=NO`, `LIFECYCLE_POLICY_CHANGED=NO`,
`STRENGTH_SCORE_CREATED=NO`, `STRATEGY_DEFINITION_CHANGED=NO`,
`PRODUCTION_FILTER_CREATED=NO`, `DB_MUTATION=NO`, `DEPLOY=NO`, `PUSH=NO`,
`NEXT_TASK_CHANGED=NO`.

`CANONICAL_STATUS=ISOLATED_VALIDATED_PENDING_PROMOTION`;
`RELEASE_STATUS=NOT_RELEASED`;
`PRODUCTION_VERIFICATION=NOT_PERFORMED_BY_SCOPE`;
`CANONICAL_RECONCILIATION_DISPOSITION=COMMIT_PRESERVING_PROMOTION_ONLY`.
