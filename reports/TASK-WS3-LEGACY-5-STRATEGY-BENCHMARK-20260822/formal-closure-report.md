# TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822

## Formal closure

```text
TASK_ID=TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822
TASK_FINAL_STATUS=COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS
WS3_ONLY=YES
A_SETUP_ACCEPTED=NO
A_STRATEGY_ACCEPTED=NO
CORE_V0_SEMANTICS_CHANGED=NO
A2_SEMANTICS_CHANGED=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
PUSH=NO
NEXT_TASK_CHANGED=NO
DATABASE_WRITES=NO
SOURCE_AUTHORITY=sdf-603-ohlcv-2y.v1
SOURCE_ROWS=288881
SOURCE_INSTRUMENTS=603
SOURCE_NORMALIZED_SURFACE_SHA256=e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4
RAW_ANCHORS_LEGACY5=2471
DISTINCT_EPISODES_LEGACY5=2471
DISTINCT_EPISODE_RULE=CONTIGUOUS_QUALIFYING_ACCEPTED_SESSION_STATE_FIRST_ANCHOR
ADJUSTMENT_STATE=UNKNOWN_RAW_ONLY
SYNTHETIC_ADJUSTMENT=NO
THRESHOLD_SEARCH=NO
MODEL_FITTING=NO
BUY_SELL_STOP_RULE=NO
```

## Frozen semantics

1. Close condition uses the prior-session slice exactly as specified: `Close_t >= max(Close[t-19:t])`; intraday High is not used for this formation condition.
2. KD(9) canonical repository lookup: no canonical implementation found. The fixed research fallback is RSV over inclusive 9-session High/Low, K/D recursive smoothing alpha=1/3, K0=D0=50, and zero-range RSV=50. The limitation is explicit in `run-summary.json`.
3. Volume condition is `mean(last five canonical daily volume lots) > 500`. The query joins accepted canonical VOLUME observations and fail-closes unknown unit codes; SHARES are converted by 1,000 shares per lot.
4. `+MA60` means `Close_t > MA60_t`; `+PRICE20` means `Close_t >= 20`; neither is part of LEGACY-5.
5. Outcomes use future accepted sessions strictly after the anchor. Endpoint is future Close / anchor Close - 1; MFE uses future High; MAE uses future Low. Daily simultaneous barriers are `SAME_SESSION_ORDER_UNKNOWN`.

## Raw anchors and distinct episodes

{
  "LEGACY-5": {
    "raw_qualifying_anchors": 2471,
    "raw_unique_instruments": 544,
    "raw_active_dates": 415,
    "distinct_episodes": 2471,
    "episode_unique_instruments": 544,
    "episode_active_dates": 415
  },
  "LEGACY-5+MA60": {
    "raw_qualifying_anchors": 2096,
    "raw_unique_instruments": 529,
    "raw_active_dates": 373,
    "distinct_episodes": 2096,
    "episode_unique_instruments": 529,
    "episode_active_dates": 373
  },
  "LEGACY-5+MA60+PRICE20": {
    "raw_qualifying_anchors": 1952,
    "raw_unique_instruments": 504,
    "raw_active_dates": 368,
    "distinct_episodes": 1952,
    "episode_unique_instruments": 504,
    "episode_active_dates": 368
  }
}

Raw and episode views are both delivered. The episode view is not a position simulation; it is a deterministic deduplication view to avoid reporting persistence observations as independent events.

## Findings

Endpoint rows: `24`; MFE/MAE rows: `24`; barrier rows: `120`; time-to-opportunity rows: `72`; variant comparison rows: `60`.

Variant comparisons report candidate retention, endpoint distribution, MFE/MAE, barrier-race rates, opportunity sacrificed, and adverse cases removed. The adverse-case fields are descriptive flags only; no stop rule is inferred.

A2 benchmark posture: `PASS`. If PASS, it uses aligned signal-close endpoint/MFE/MAE semantics and is retained as a descriptive benchmark only. If not, do not rank.

## Governance and limitations

- Adjustment state remains UNKNOWN_RAW_ONLY; no synthetic adjustment or corporate-action correction was introduced.
- Results are gross and exclude transaction costs, slippage, liquidity constraints, and execution timing; no BUY/SELL rule is established.
- KD(9) uses an explicit fallback because no repository canonical definition was found; alternative initialization/zero-range conventions were not searched or optimized.
- The input query is accepted canonical daily data with supersession/lifecycle predicates; quarantine, NO_DATA, and lifecycle skip work items remain fail-closed upstream.
- The 20-session Close formula is preserved literally as requested; its slice notation is recorded to prevent silent semantic drift.

## Reproducibility and promotion

The isolated branch should be promoted only through the existing safe review process after a second replay and artifact hash match. No application, API/UI, scheduler, Production, WS1/WS2/WS4, or NEXT_TASK mutation occurred.

Artifacts are listed in `reproducibility-manifest.json`; source files are written under this task directory.
