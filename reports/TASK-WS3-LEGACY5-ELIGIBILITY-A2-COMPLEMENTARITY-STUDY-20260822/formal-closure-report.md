# TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822

## Formal closure

```text
TASK_ID=TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822
TASK_FINAL_STATUS=COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS
WS3_ONLY=YES
A_SETUP_ACCEPTED=NO
A_STRATEGY_ACCEPTED=NO
LEGACY_STRATEGY_ACCEPTED=NO
CORE_V0_SEMANTICS_CHANGED=NO
A2_SEMANTICS_CHANGED=NO
WS1_WS2_WS4_MUTATION=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
PUSH=NO
NEXT_TASK_CHANGED=NO
DATABASE_WRITES=NO
DATA_DOWNLOAD=NO
LARGE_OHLCV_PIPELINE_RERUN=NO
THRESHOLD_SEARCH=NO
PRICE20_RESEARCHED=NO
ADJUSTMENT_STATE=UNKNOWN_RAW_ONLY
SAME_SESSION_ORDER=SAME_SESSION_ORDER_UNKNOWN
OVERLAP_WINDOW=+/-1_TRADING_SESSION_FIXED
```

## Scope and frozen variants

Only four predeclared eligibility variants were compared: V0 Legacy-5, V1 +MA20, V2 +MA60, and V3 +MA20+MA60. No MA10/MA30/MA40/MA120 or price threshold was searched.

{
  "surface": {
    "rows": 288881,
    "instruments": 603,
    "date_min": "2024-08-13",
    "date_max": "2026-08-13",
    "normalized_surface_sha256": "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
  },
  "legacy_source": {
    "raw_anchors": 2471,
    "a2_events": 5277,
    "a2_path_rows": 52770
  },
  "variants": {
    "V0_LEGACY5": {
      "raw_anchors": 2471,
      "episodes": 2471,
      "instruments": 544,
      "active_dates": 415,
      "ma20_pass_count": 2471
    },
    "V1_LEGACY5_MA20": {
      "raw_anchors": 2471,
      "episodes": 2471,
      "instruments": 544,
      "active_dates": 415,
      "ma20_pass_count": 2471
    },
    "V2_LEGACY5_MA60": {
      "raw_anchors": 2096,
      "episodes": 2096,
      "instruments": 529,
      "active_dates": 373,
      "ma20_pass_count": 2096
    },
    "V3_LEGACY5_MA20_MA60": {
      "raw_anchors": 2096,
      "episodes": 2096,
      "instruments": 529,
      "active_dates": 373,
      "ma20_pass_count": 2096
    }
  },
  "overlap_primary_v0": {
    "A2_ONLY": {
      "event_count": 4485,
      "a2_event_count": 4485,
      "legacy_event_count": 0,
      "pair_count": 0,
      "instrument_count": 599
    },
    "LEGACY5_ONLY": {
      "event_count": 1679,
      "a2_event_count": 0,
      "legacy_event_count": 1679,
      "pair_count": 0,
      "instrument_count": 504
    },
    "BOTH_SAME_SESSION": {
      "event_count": 560,
      "a2_event_count": 560,
      "legacy_event_count": 560,
      "pair_count": 560,
      "instrument_count": 330
    },
    "BOTH_WITHIN_BOUNDED_WINDOW": {
      "event_count": 232,
      "a2_event_count": 232,
      "legacy_event_count": 232,
      "pair_count": 232,
      "instrument_count": 185
    }
  }
}

## Semantics reconciliation

Endpoint/MFE/MAE use the same signal-day close and future accepted-session definitions. Legacy path outcomes are reused from the committed event-outcomes artifact. A2 path outcomes are reused from the committed path-aware artifact. A2 event-level first-threshold time-to-opportunity is unavailable; those cells are marked NOT_AVAILABLE rather than inferred from future outcomes.

Source/semantics manifest: `ws3-legacy5-a2-semantics-reconciliation.v1`.

## Governance and limitations

- Corporate-action adjustment remains UNKNOWN_RAW_ONLY and no synthetic adjustment is applied.
- Same-session daily High/Low barrier races are SAME_SESSION_ORDER_UNKNOWN; intraday ordering is not guessed.
- Overlap matching uses only instrument/date/session position and never uses future outcome metrics.
- Results are descriptive, gross, and not a strategy ranking or acceptance.
- A2 and Legacy are directly comparable for endpoint/MFE/MAE and barrier metrics under the reconciled anchor contract; A2 group-level time-to-opportunity is NOT_DIRECTLY_COMPARABLE from existing artifacts.

## Artifacts

- `a2-legacy5-complementarity-path-metrics.csv`: `fa6c2af3ee9f5e0e793ca44cd7390650e1384cb8587bb669c5819c2d9f01b89f`
- `a2-legacy5-overlap-summary.csv`: `c7b6ab8c766d02f00d2d4e24d652f61a6dbcbfffa85137de7504caf0a33fa088`
- `eligibility-anchor-panel.csv`: `3bace0135b967d3aadc34a161b134a4951f3230a2566030303731e254e76d2d8`
- `eligibility-distinct-episodes.csv`: `6dff77ea092488b06f601712e4cd00788adfd0b65e3bab5f94632c992ddece3c`
- `eligibility-path-metrics.csv`: `671bdb83d39a6d5c788d93a1819bc97ec70ac6a9dfd1e78821c0f28a23863380`
- `legacy5-ma20-ma60-variant-comparison.csv`: `d76bd156aaf21f7e98ff7b3f3b278ff9ee173df38d528f4cc73988e168017bf7`
- `signal-lead-lag-summary.csv`: `d8b1a8df06e7dea98f4d3e7a534980eb4ac2bcdf850de1d6d8bdb35fcdacb3c5`
- `source-semantics-reconciliation-manifest.json`: `4f3499766a0fb6cd3e89e9f84fd33113ff166ccd7aea22a496bac66b76a45c88`

No application, API/UI, scheduler, Production, WS1/WS2/WS4, Core V0, A2 semantics, or NEXT_TASK mutation occurred.
