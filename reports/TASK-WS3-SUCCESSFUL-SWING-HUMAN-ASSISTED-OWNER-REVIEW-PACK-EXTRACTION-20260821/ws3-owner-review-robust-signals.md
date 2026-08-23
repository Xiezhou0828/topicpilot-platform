# WS3 robust discovery signals

All values below are direct extracts or deterministic joins of the completed discovery artifacts. They are not accepted strategy rules.

> Explicit rank was not persisted in the source artifact. This stable ordering reconstructs a review order from existing classification, absolute standardized mean difference, sample count, overlap, relative day, and source-key tie-breakers; no new search, fit, threshold, or feature was executed.

| Rank | Family | Feature | Day | Stratum | nS/nC | Success median | Control median | SMD | Overlap | Market | Temporal | Classification |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | TREND_STRUCTURE | ma_alignment_bearish | D0 | T5_GE_3 | 6785/6785 | 0 | 0 | 0.3452 | 0.8352 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 2 | TREND_STRUCTURE | ma_alignment_bearish | D0 | T5_GE_5 | 6569/6569 | 0 | 0 | 0.2834 | 0.8677 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 3 | TREND_STRUCTURE | ma_alignment_bearish | D-1 | T5_GE_3 | 6785/6785 | 0 | 0 | 0.2792 | 0.871 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 4 | TREND_STRUCTURE | ma_alignment_bearish | D0 | T10_GE_3 | 6306/6306 | 0 | 0 | 0.2738 | 0.87 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 5 | VOLUME_PARTICIPATION | volume_contraction_state | D-3 | T5_GE_3 | 6785/6785 | 1 | 1 | 0.2481 | 0.8884 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 6 | TREND_STRUCTURE | ma_alignment_bearish | D-1 | T5_GE_5 | 6569/6569 | 0 | 0 | 0.2232 | 0.9004 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 7 | VOLUME_PARTICIPATION | volume_contraction_state | D-1 | T5_GE_3 | 6785/6785 | 1 | 1 | 0.2207 | 0.9023 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 8 | VOLUME_PARTICIPATION | volume_contraction_state | D-1 | T5_GE_5 | 6569/6569 | 1 | 1 | 0.2177 | 0.903 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 9 | TREND_STRUCTURE | ma_alignment_bearish | D0 | T10_GE_5 | 6083/6083 | 0 | 0 | 0.2168 | 0.8982 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 10 | VOLUME_PARTICIPATION | volume_contraction_state | D-3 | T5_GE_5 | 6569/6569 | 1 | 1 | 0.2076 | 0.9068 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |
| 11 | VOLATILITY_COMPRESSION | rolling_range_pct_20 | D0 | T5_GE_3 | 6785/6785 | 0.1837 | 0.168 | 0.204 | 0.9313 | 1 | 1 | ROBUST_DISCOVERY_SIGNAL |

## Definitions and interpretation

### 1. `TREND_STRUCTURE/ma_alignment_bearish` at D0 — `T5_GE_3`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.1648`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D0; this is descriptive and is not a trading rule.

### 2. `TREND_STRUCTURE/ma_alignment_bearish` at D0 — `T5_GE_5`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.1323`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D0; this is descriptive and is not a trading rule.

### 3. `TREND_STRUCTURE/ma_alignment_bearish` at D-1 — `T5_GE_3`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.129`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-1; this is descriptive and is not a trading rule.

### 4. `TREND_STRUCTURE/ma_alignment_bearish` at D0 — `T10_GE_3`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.13`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D0; this is descriptive and is not a trading rule.

### 5. `VOLUME_PARTICIPATION/volume_contraction_state` at D-3 — `T5_GE_3`

- Definition: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline.
- Median difference (success - control): `0`; mean difference: `0.1116`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=1,T5=1,T10=1,mono=NONDECREASING; h10:T3=1,T5=1,T10=1,mono=NONDECREASING`.
- Earliest useful family lead time: `D-5`.
- Interpretation: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-3; this is descriptive and is not a trading rule.

### 6. `TREND_STRUCTURE/ma_alignment_bearish` at D-1 — `T5_GE_5`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.09956`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-1; this is descriptive and is not a trading rule.

### 7. `VOLUME_PARTICIPATION/volume_contraction_state` at D-1 — `T5_GE_3`

- Definition: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline.
- Median difference (success - control): `0`; mean difference: `0.09772`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=1,T5=1,T10=1,mono=NONDECREASING; h10:T3=1,T5=1,T10=1,mono=NONDECREASING`.
- Earliest useful family lead time: `D-5`.
- Interpretation: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-1; this is descriptive and is not a trading rule.

### 8. `VOLUME_PARTICIPATION/volume_contraction_state` at D-1 — `T5_GE_5`

- Definition: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline.
- Median difference (success - control): `0`; mean difference: `0.09697`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=1,T5=1,T10=1,mono=NONDECREASING; h10:T3=1,T5=1,T10=1,mono=NONDECREASING`.
- Earliest useful family lead time: `D-5`.
- Interpretation: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-1; this is descriptive and is not a trading rule.

### 9. `TREND_STRUCTURE/ma_alignment_bearish` at D0 — `T10_GE_5`

- Definition: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.
- Median difference (success - control): `0`; mean difference: `0.1018`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0,T5=0,T10=0,mono=NONDECREASING; h10:T3=0,T5=0,T10=0,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering. Existing discovery evidence shows the successful group had a higher mean than matched controls at D0; this is descriptive and is not a trading rule.

### 10. `VOLUME_PARTICIPATION/volume_contraction_state` at D-3 — `T5_GE_5`

- Definition: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline.
- Median difference (success - control): `0`; mean difference: `0.09316`; outlier dependence: `1.25`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=1,T5=1,T10=1,mono=NONDECREASING; h10:T3=1,T5=1,T10=1,mono=NONDECREASING`.
- Earliest useful family lead time: `D-5`.
- Interpretation: Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline. Existing discovery evidence shows the successful group had a higher mean than matched controls at D-3; this is descriptive and is not a trading rule.

### 11. `VOLATILITY_COMPRESSION/rolling_range_pct_20` at D0 — `T5_GE_3`

- Definition: (rolling 20-session high - rolling 20-session low) / current close.
- Median difference (success - control): `0.01574`; mean difference: `0.02941`; outlier dependence: `0.7807`.
- Stability: market `1` (TPE/TWO pooled); temporal `1`; detailed per-segment breakdown: `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- Outcome-strength gradient: `h5:T3=0.1837,T5=0.1923,T10=0.2287,mono=NONDECREASING; h10:T3=0.1874,T5=0.1949,T10=0.2235,mono=NONDECREASING`.
- Earliest useful family lead time: `D-20`.
- Interpretation: (rolling 20-session high - rolling 20-session low) / current close. Existing discovery evidence shows the successful group had a higher mean than matched controls at D0; this is descriptive and is not a trading rule.

This pack preserves discovery classifications only. It does not promote any observation into a rule, score, recommendation, or production feature.
