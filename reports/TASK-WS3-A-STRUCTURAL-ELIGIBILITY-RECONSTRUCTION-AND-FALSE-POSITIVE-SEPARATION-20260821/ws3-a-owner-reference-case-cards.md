# WS3 A Structural Eligibility Owner Review — TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821

These are research classifications only. They do not accept A, create a strategy, or explain causality.

## A. Strongest retained A examples

- `2303` on `2026-01-02`: global `GLOBAL_ELIGIBLE`, environment `CONSTRUCTIVE_UPTREND`, base `TIGHT_CONSOLIDATION`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_SUCCESS`; T+5 `13.14%`, T+10 `20.12%`.
  - Structural subtype: `TIGHT_CONSOLIDATION`; decision layer: `L3_BREAKOUT_EVENT`; owner-reference conflict: `YES`.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `2303` on `2026-07-07`: global `GLOBAL_ELIGIBLE`, environment `TREND_TRANSITION`, base `VOLATILITY_CONTRACTION_BASE`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_SUCCESS`; T+5 `7.10%`, T+10 `-10.32%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L3_BREAKOUT_EVENT`; owner-reference conflict: `YES`.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `2615` on `2026-07-28`: global `GLOBAL_ELIGIBLE`, environment `TREND_TRANSITION`, base `FLAT_BASE`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_SUCCESS`; T+5 `2.99%`, T+10 `4.19%`.
  - Structural subtype: `FLAT_BASE`; decision layer: `L3_BREAKOUT_EVENT`; owner-reference conflict: `YES`.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `5351` on `2026-05-18`: global `GLOBAL_ELIGIBLE`, environment `TREND_TRANSITION`, base `VOLATILITY_CONTRACTION_BASE`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_SUCCESS`; T+5 `-3.75%`, T+10 `5.16%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L3_BREAKOUT_EVENT`; owner-reference conflict: `YES`.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.

## B. Structural false positives removed

- `1597` on `2025-06-23`: global `GLOBAL_ELIGIBLE`, environment `CONSTRUCTIVE_UPTREND`, base `FLAT_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `1.21%`, T+10 `-3.03%`.
  - Structural subtype: `FLAT_BASE`; decision layer: `L3_BREAKOUT_EVENT`; owner-reference conflict: `YES`.
  - Owner review label: `STRUCTURAL_FALSE_POSITIVE`; frozen structural classification remains `STRUCTURAL_FALSE_POSITIVE` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.
- `1477` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `FLAT_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `-4.32%`, T+10 `-1.64%`.
  - Structural subtype: `FLAT_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.
- `1514` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `FLAT_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `-2.22%`, T+10 `1.33%`.
  - Structural subtype: `FLAT_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.
- `1584` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `VOLATILITY_CONTRACTION_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `-0.63%`, T+10 `0.78%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.
- `1597` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `VOLATILITY_CONTRACTION_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `-1.72%`, T+10 `-2.04%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.

## C. Borderline / ambiguous examples

- `6122` on `2025-03-21`: global `GLOBAL_UNKNOWN`, environment `UNKNOWN`, base `UNKNOWN`, breakout `AMBIGUOUS_BREAKOUT`, classification `AMBIGUOUS`; T+5 `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`, T+10 `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
  - Structural subtype: `UNKNOWN`; decision layer: `SOURCE_ARTIFACT_GAP`; owner-reference conflict: `YES`.
  - Owner review label: `STRUCTURAL_FALSE_POSITIVE`; frozen structural classification remains `AMBIGUOUS` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `No matching frozen source anchor found.`; no causal explanation is asserted.
- `3346` on `2026-04-22`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `FLAT_BASE`, breakout `AMBIGUOUS_BREAKOUT`, classification `AMBIGUOUS`; T+5 `-5.45%`, T+10 `-6.27%`.
  - Structural subtype: `FLAT_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `YES`.
  - Owner review label: `GLOBAL_INELIGIBLE_REFERENCE`; frozen structural classification remains `AMBIGUOUS` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `Participation alone cannot establish a structural boundary break.`; no causal explanation is asserted.
- `4807` on `2024-11-12`: global `GLOBAL_ELIGIBLE`, environment `UNKNOWN`, base `VOLATILITY_CONTRACTION_BASE`, breakout `AMBIGUOUS_BREAKOUT`, classification `AMBIGUOUS`; T+5 `-28.99%`, T+10 `-36.16%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L1_ENVIRONMENT`; owner-reference conflict: `YES`.
  - Owner review label: `LATE_OR_EXTENDED_SETUP`; frozen structural classification remains `AMBIGUOUS` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `Participation alone cannot establish a structural boundary break.`; no causal explanation is asserted.
- `1303` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `TIGHT_CONSOLIDATION`, breakout `AMBIGUOUS_BREAKOUT`, classification `AMBIGUOUS`; T+5 `1.22%`, T+10 `-2.08%`.
  - Structural subtype: `TIGHT_CONSOLIDATION`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `Participation alone cannot establish a structural boundary break.`; no causal explanation is asserted.
- `1515` on `2024-11-12`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `TIGHT_CONSOLIDATION`, breakout `AMBIGUOUS_BREAKOUT`, classification `AMBIGUOUS`; T+5 `-3.54%`, T+10 `-1.69%`.
  - Structural subtype: `TIGHT_CONSOLIDATION`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `Participation alone cannot establish a structural boundary break.`; no causal explanation is asserted.

## D. Legitimate setups that subsequently failed

- `4566` on `2025-11-24`: global `GLOBAL_INELIGIBLE`, environment `NOT_EVALUATED_GLOBAL_INELIGIBLE`, base `VOLATILITY_CONTRACTION_BASE`, breakout `NO_BREAKOUT`, classification `STRUCTURAL_FALSE_POSITIVE`; T+5 `-0.38%`, T+10 `1.53%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L0_GLOBAL_ELIGIBILITY`; owner-reference conflict: `YES`.
  - Owner review label: `LEGITIMATE_OR_PLAUSIBLE_FAILURE`; frozen structural classification remains `STRUCTURAL_FALSE_POSITIVE` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `No existing structural event evidence; no future outcome was used.`; no causal explanation is asserted.
- `3533` on `2024-12-11`: global `GLOBAL_ELIGIBLE`, environment `CONSTRUCTIVE_UPTREND`, base `VOLATILITY_CONTRACTION_BASE`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_FAILURE`; T+5 `0.26%`, T+10 `-0.77%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L4_QUALITY_AFTER_STRUCTURE`; owner-reference conflict: `NO`.
  - Owner review label: `LEGITIMATE_OR_PLAUSIBLE_FAILURE`; frozen structural classification remains `LEGITIMATE_SETUP_FAILURE` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `3533` on `2024-12-13`: global `GLOBAL_ELIGIBLE`, environment `TREND_TRANSITION`, base `VOLATILITY_CONTRACTION_BASE`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_FAILURE`; T+5 `-3.11%`, T+10 `0.00%`.
  - Structural subtype: `VOLATILITY_CONTRACTION_BASE`; decision layer: `L4_QUALITY_AFTER_STRUCTURE`; owner-reference conflict: `NO`.
  - Owner review label: `LEGITIMATE_OR_PLAUSIBLE_FAILURE`; frozen structural classification remains `LEGITIMATE_SETUP_FAILURE` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `9904` on `2025-12-09`: global `GLOBAL_ELIGIBLE`, environment `TREND_TRANSITION`, base `TIGHT_CONSOLIDATION`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_FAILURE`; T+5 `1.46%`, T+10 `-0.97%`.
  - Structural subtype: `TIGHT_CONSOLIDATION`; decision layer: `L4_QUALITY_AFTER_STRUCTURE`; owner-reference conflict: `NO`.
  - Owner review label: `LEGITIMATE_OR_PLAUSIBLE_FAILURE`; frozen structural classification remains `LEGITIMATE_SETUP_FAILURE` and is not overridden by the owner label.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.
- `1504` on `2024-11-18`: global `GLOBAL_ELIGIBLE`, environment `SIDEWAYS_CONSTRUCTIVE`, base `TIGHT_CONSOLIDATION`, breakout `BREAKOUT_ATTEMPT`, classification `LEGITIMATE_SETUP_FAILURE`; T+5 `-1.91%`, T+10 `1.91%`.
  - Structural subtype: `TIGHT_CONSOLIDATION`; decision layer: `L4_QUALITY_AFTER_STRUCTURE`; owner-reference conflict: `NO`.
  - Inclusion/exclusion evidence: `Existing A-state context suggests an attempt, but no frozen exact event row was available.`; no causal explanation is asserted.

## Interpretation boundary

- Rising-base floor, repeated upper-boundary tests, and precise breakout distance were unavailable in the frozen panel and remain open evidence gaps.
- A2 event evidence is consumed as an existing frozen event reference only; A2 semantics were not changed.
- Future returns appear only after structural classification for descriptive evaluation.
