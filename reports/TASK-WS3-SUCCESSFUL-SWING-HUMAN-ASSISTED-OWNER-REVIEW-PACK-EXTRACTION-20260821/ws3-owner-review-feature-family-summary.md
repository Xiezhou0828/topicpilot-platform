# WS3 feature-family interpretation

This is a compact reading of existing discovery artifacts. Family-level descriptions are hypotheses for owner review only; none is a strategy rule or accepted feature.

## TREND_STRUCTURE

- Signal available: `YES`
- Robust observations: `6`; Promising observations: `11`
- Earliest useful lead time: `D-20`
- Strongest existing observations: `ma_alignment_bearish` at D0 (T5_GE_3), `ma_alignment_bearish` at D0 (T5_GE_5), `ma_alignment_bearish` at D-1 (T5_GE_3)
- Existing outcome-strength gradient labels: `MIXED=9, NONDECREASING=111`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `0.0` and temporal value `0.0`; promising pooled market `0.0` and temporal `0.0`. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: Price location, moving-average ordering, and moving-average slopes describe directional structure and distance from recent reference levels.
- Unresolved: discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.

## VOLATILITY_COMPRESSION

- Signal available: `YES`
- Robust observations: `1`; Promising observations: `65`
- Earliest useful lead time: `D-20`
- Strongest existing observations: `rolling_range_pct_20` at D0 (T5_GE_3), `rolling_range_pct_20` at D0 (T5_GE_5), `rolling_range_pct_20` at D0 (T5_GE_10)
- Existing outcome-strength gradient labels: `MIXED=4, NONDECREASING=79, NONINCREASING=1`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `1.0` and temporal value `0.5`; promising pooled market `1.0` and temporal `0.5`. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: Range width and realized-volatility ratios describe whether recent movement is tighter or broader than its own recent baseline.
- Unresolved: discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.

## VOLUME_PARTICIPATION

- Signal available: `YES`
- Robust observations: `4`; Promising observations: `12`
- Earliest useful lead time: `D-5`
- Strongest existing observations: `volume_contraction_state` at D-3 (T5_GE_3), `volume_contraction_state` at D-1 (T5_GE_3), `volume_contraction_state` at D-1 (T5_GE_5)
- Existing outcome-strength gradient labels: `MIXED=8, NONDECREASING=63, NONINCREASING=1`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `0.5` and temporal value `0.5`; promising pooled market `0.5` and temporal `0.5`. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: Volume ratios describe participation relative to recent baselines; contraction and expansion are frozen descriptive states.
- Unresolved: discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.

## MOMENTUM

- Signal available: `YES`
- Robust observations: `0`; Promising observations: `0`
- Earliest useful lead time: `NONE`
- Strongest existing observations: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Existing outcome-strength gradient labels: `MIXED=18, NONDECREASING=70, NONINCREASING=8`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `0.0` and temporal value `0.0`; promising pooled market `0.0` and temporal `0.0`. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: Raw returns, RSI, and MACD fields describe recent price impulse and oscillator state under Technical V0 semantics.
- Unresolved: discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.

## A_STATE

- Signal available: `YES`
- Robust observations: `0`; Promising observations: `0`
- Earliest useful lead time: `NONE`
- Strongest existing observations: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Existing outcome-strength gradient labels: `INSUFFICIENT=12, NONDECREASING=48`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `0.0` and temporal value `0.0`; promising pooled market `0.0` and temporal `0.0`. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: A1/A2 fields provide frozen event-context labels from the prior P1E work; they are not retuned here.
- Unresolved: discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.

## RELATIVE_STRENGTH

- Signal available: `UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK`
- Robust observations: `0`; Promising observations: `0`
- Earliest useful lead time: `NONE`
- Strongest existing observations: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Existing outcome-strength gradient labels: `INSUFFICIENT=24`. This records the source labels; it does not claim monotonic strategy strength.
- Stability: robust pooled market value `` and temporal value ``; promising pooled market `` and temporal ``. Detailed split evidence: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Technical interpretation: Relative performance versus a canonical benchmark would compare stock movement with a shared market reference.
- Unresolved: UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK; this is not a no-signal conclusion; discovery-only; no confirmatory validation or strategy acceptance; per-market and per-temporal-split detail is NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS.
