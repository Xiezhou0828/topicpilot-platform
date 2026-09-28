# OWNER_SEEDED_V0 Policy Report

- Policy ID: `topic-strength-lifecycle.owner-seeded-v0`
- Policy version: `v0`
- Policy hash: `5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef`
- Calibration method: `OWNER_SEEDED_FROM_DESIGN_FREEZE`
- Historical calibration: `NOT_AVAILABLE`
- Provisional: `YES`
- Production active: `NO`

This is an explicit Owner-seeded policy, not a historical calibration or backtest result.
The existing active policy remains unchanged; this module is opt-in and non-activating.

## Policy components

| Design semantic | Owner-seed value | Implementation location | Scenario effect | Known limitation |
|---|---|---|---|---|
| Absolute REP | Exact piecewise knots in policy JSON | `owner_seeded_v0_policy.py:PiecewiseLinearCurve` | Early visible confirmation | No historical fit |
| Absolute CORE | Exact piecewise knots in policy JSON | `owner_seeded_v0_policy.py:PiecewiseLinearCurve` | Broad CORE outranks one outlier | No historical fit |
| Absolute RELATED | Breadth bucket x positive-median quality | `owner_seeded_v0_policy.py:_related_evidence` | Weak tiny breadth stays low | No per-member importance |
| Absolute Grade | S>=82, A>=62, D guard precedence | `owner_seeded_v0_policy.py:_grade` | D is directional, not low-score-only | Synthetic evidence only |
| Relative | Member return minus own-market official benchmark | `MemberObservation.value_for` | Absolute/Relative can diverge | No historical role overlap |
| Lifecycle | Exact role evidence and confirmation rules | `advance_lifecycle` | Diffusion and hysteresis | Forward observation required |
| Forward observation output | Deterministic review fields plus PM placeholders | `build_forward_observation_output` | Enables later forward review | No scheduler or publication activation |

## Lifecycle thresholds

```json
{
  "declining_confirmation_sessions": 2,
  "declining_core_median_deep_max": -2.5,
  "declining_core_median_max": -1.5,
  "declining_core_positive_breadth_max": 0.3,
  "declining_core_weak_ratio_min": 0.5,
  "declining_rep_raw_max": -1.0,
  "expansion_core_breadth_delta": 0.1,
  "expansion_core_median_min": 1.5,
  "expansion_lookback_sessions": 5,
  "expansion_related_breadth_delta": 0.15,
  "expansion_related_core_breadth_min": 0.55,
  "expansion_related_median_min": 0.75,
  "fermenting_core_median_min": 1.0,
  "fermenting_core_positive_breadth_min": 0.5,
  "fermenting_core_strong_breadth_min": 0.25,
  "fermenting_rep_raw_min": -1.5,
  "fermenting_required_sessions": 2,
  "fermenting_window_sessions": 3,
  "main_rise_core_median_min": 2.0,
  "main_rise_core_positive_breadth_min": 0.65,
  "main_rise_core_strong_breadth_min": 0.4,
  "main_rise_related_positive_breadth_min": 0.5,
  "main_rise_related_positive_median_min": 1.0,
  "main_rise_rep_raw_min": -1.0,
  "main_rise_required_sessions": 2,
  "main_rise_window_sessions": 3,
  "mature_confirmation_sessions": 2,
  "mature_core_breadth_drawdown": 0.2,
  "mature_core_median_drawdown": 1.5,
  "mature_late_core_breadth_max": 0.5,
  "mature_late_related_breadth_min": 0.5,
  "mature_no_expansion_sessions": 3,
  "mature_rep_nonpositive_required": 2,
  "mature_rep_nonpositive_window": 3,
  "relative_deterioration_strength_max": 45.0,
  "reset_confirmation_sessions": 3,
  "reset_core_median_max": 0.5,
  "reset_core_median_min": -0.5,
  "reset_core_positive_breadth_max": 0.6,
  "reset_core_positive_breadth_min": 0.3,
  "reset_core_weak_ratio_max": 0.3,
  "reset_grade": "B",
  "sprouting_confirmation_sessions": 1,
  "sprouting_core_median_max": 1.5,
  "sprouting_core_median_min": -1.0,
  "sprouting_core_positive_breadth_max": 0.5,
  "sprouting_rep_raw_min": 0.8
}
```

## Absolute and relative seed tables

The following machine-readable blocks are reproduced here so every Owner knot, bucket, grade boundary, benchmark mapping, and lifecycle threshold is visible in the human review artifact.

### Absolute

```json
{
  "coreCurve": {
    "cap": 60.0,
    "knots": [
      {
        "inputPct": -6.0,
        "points": 0.0
      },
      {
        "inputPct": -4.0,
        "points": 3.0
      },
      {
        "inputPct": -3.0,
        "points": 7.0
      },
      {
        "inputPct": -2.0,
        "points": 12.0
      },
      {
        "inputPct": -1.0,
        "points": 20.0
      },
      {
        "inputPct": 0.0,
        "points": 27.0
      },
      {
        "inputPct": 1.0,
        "points": 34.0
      },
      {
        "inputPct": 2.0,
        "points": 42.0
      },
      {
        "inputPct": 3.0,
        "points": 49.0
      },
      {
        "inputPct": 4.0,
        "points": 54.0
      },
      {
        "inputPct": 5.0,
        "points": 57.0
      },
      {
        "inputPct": 7.0,
        "points": 60.0
      }
    ],
    "name": "absolute-core-v0"
  },
  "grade": {
    "clear_min": 62.0,
    "d_core_median_deep_max": -2.5,
    "d_core_median_max": -1.5,
    "d_core_positive_breadth_max": 0.25,
    "d_core_weak_ratio_min": 0.6,
    "d_rep_weighted_raw_max": -1.0,
    "exceptional_min": 82.0
  },
  "relatedBreadth": [
    {
      "lowerInclusive": 0.0,
      "upperExclusive": 0.2,
      "value": 0.0
    },
    {
      "lowerInclusive": 0.2,
      "upperExclusive": 0.3,
      "value": 1.0
    },
    {
      "lowerInclusive": 0.3,
      "upperExclusive": 0.4,
      "value": 2.0
    },
    {
      "lowerInclusive": 0.4,
      "upperExclusive": 0.5,
      "value": 3.5
    },
    {
      "lowerInclusive": 0.5,
      "upperExclusive": 0.6,
      "value": 5.0
    },
    {
      "lowerInclusive": 0.6,
      "upperExclusive": 0.7,
      "value": 6.5
    },
    {
      "lowerInclusive": 0.7,
      "upperExclusive": 0.8,
      "value": 8.0
    },
    {
      "lowerInclusive": 0.8,
      "upperExclusive": 0.9,
      "value": 9.0
    },
    {
      "lowerInclusive": 0.9,
      "upperExclusive": null,
      "value": 10.0
    }
  ],
  "relatedMagnitudeQuality": [
    {
      "lowerInclusive": 0.0,
      "upperExclusive": 0.25,
      "value": 0.25
    },
    {
      "lowerInclusive": 0.25,
      "upperExclusive": 0.5,
      "value": 0.5
    },
    {
      "lowerInclusive": 0.5,
      "upperExclusive": 1.0,
      "value": 0.75
    },
    {
      "lowerInclusive": 1.0,
      "upperExclusive": 2.0,
      "value": 0.9
    },
    {
      "lowerInclusive": 2.0,
      "upperExclusive": null,
      "value": 1.0
    }
  ],
  "representativeCurve": {
    "cap": 30.0,
    "knots": [
      {
        "inputPct": -5.0,
        "points": 0.0
      },
      {
        "inputPct": -3.0,
        "points": 3.0
      },
      {
        "inputPct": -2.0,
        "points": 6.0
      },
      {
        "inputPct": -1.0,
        "points": 10.0
      },
      {
        "inputPct": 0.0,
        "points": 14.0
      },
      {
        "inputPct": 0.5,
        "points": 18.0
      },
      {
        "inputPct": 1.0,
        "points": 21.0
      },
      {
        "inputPct": 1.5,
        "points": 24.0
      },
      {
        "inputPct": 2.0,
        "points": 26.0
      },
      {
        "inputPct": 3.0,
        "points": 28.5
      },
      {
        "inputPct": 5.0,
        "points": 30.0
      }
    ],
    "name": "absolute-representative-v0"
  }
}
```

### Relative

```json
{
  "benchmarkByMarket": {
    "TPEX": "TPEX_INDEX",
    "TWSE": "TAIEX"
  },
  "coreCurve": {
    "cap": 60.0,
    "knots": [
      {
        "inputPct": -5.0,
        "points": 5.0
      },
      {
        "inputPct": -4.0,
        "points": 10.0
      },
      {
        "inputPct": -3.0,
        "points": 16.0
      },
      {
        "inputPct": -2.0,
        "points": 22.0
      },
      {
        "inputPct": -1.0,
        "points": 29.0
      },
      {
        "inputPct": -0.5,
        "points": 32.0
      },
      {
        "inputPct": 0.0,
        "points": 35.0
      },
      {
        "inputPct": 0.5,
        "points": 39.0
      },
      {
        "inputPct": 1.0,
        "points": 43.0
      },
      {
        "inputPct": 2.0,
        "points": 50.0
      },
      {
        "inputPct": 3.0,
        "points": 55.0
      },
      {
        "inputPct": 4.0,
        "points": 58.0
      },
      {
        "inputPct": 6.0,
        "points": 60.0
      }
    ],
    "name": "relative-core-v0"
  },
  "grade": {
    "clear_min": 63.0,
    "d_core_median_deep_max": -2.5,
    "d_core_median_max": -1.5,
    "d_core_positive_breadth_max": 0.25,
    "d_core_weak_ratio_min": 0.6,
    "d_rep_weighted_raw_max": -1.0,
    "d_total_max": 42.0,
    "exceptional_min": 80.0
  },
  "relatedBreadth": [
    {
      "lowerInclusive": 0.0,
      "upperExclusive": 0.2,
      "value": 0.0
    },
    {
      "lowerInclusive": 0.2,
      "upperExclusive": 0.3,
      "value": 1.0
    },
    {
      "lowerInclusive": 0.3,
      "upperExclusive": 0.4,
      "value": 2.0
    },
    {
      "lowerInclusive": 0.4,
      "upperExclusive": 0.5,
      "value": 3.5
    },
    {
      "lowerInclusive": 0.5,
      "upperExclusive": 0.6,
      "value": 5.0
    },
    {
      "lowerInclusive": 0.6,
      "upperExclusive": 0.7,
      "value": 6.5
    },
    {
      "lowerInclusive": 0.7,
      "upperExclusive": 0.8,
      "value": 8.0
    },
    {
      "lowerInclusive": 0.8,
      "upperExclusive": 0.9,
      "value": 9.0
    },
    {
      "lowerInclusive": 0.9,
      "upperExclusive": null,
      "value": 10.0
    }
  ],
  "relatedMagnitudeQuality": [
    {
      "lowerInclusive": 0.0,
      "upperExclusive": 0.2,
      "value": 0.25
    },
    {
      "lowerInclusive": 0.2,
      "upperExclusive": 0.5,
      "value": 0.5
    },
    {
      "lowerInclusive": 0.5,
      "upperExclusive": 1.0,
      "value": 0.75
    },
    {
      "lowerInclusive": 1.0,
      "upperExclusive": 1.75,
      "value": 0.9
    },
    {
      "lowerInclusive": 1.75,
      "upperExclusive": null,
      "value": 1.0
    }
  ],
  "representativeCurve": {
    "cap": 30.0,
    "knots": [
      {
        "inputPct": -4.0,
        "points": 2.0
      },
      {
        "inputPct": -3.0,
        "points": 5.0
      },
      {
        "inputPct": -2.0,
        "points": 8.0
      },
      {
        "inputPct": -1.0,
        "points": 12.0
      },
      {
        "inputPct": -0.5,
        "points": 14.0
      },
      {
        "inputPct": 0.0,
        "points": 15.0
      },
      {
        "inputPct": 0.5,
        "points": 19.0
      },
      {
        "inputPct": 1.0,
        "points": 23.0
      },
      {
        "inputPct": 2.0,
        "points": 27.0
      },
      {
        "inputPct": 3.0,
        "points": 29.0
      },
      {
        "inputPct": 4.0,
        "points": 30.0
      }
    ],
    "name": "relative-representative-v0"
  }
}
```

## Validation

- Synthetic scenario replay: `25 cases`, `PASS`
- Monotonicity audit: `PASS`
- Sensitivity audit: `DIAGNOSTIC_ONLY`; supplied values were not changed.
- No historical replay claim is made.

## Design-freeze traceability

See `design-freeze-traceability.json` for the D01-D51 implementation map.
