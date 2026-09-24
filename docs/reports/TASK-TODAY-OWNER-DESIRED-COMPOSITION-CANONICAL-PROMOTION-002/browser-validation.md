# Browser validation

## Candidate local smoke

Candidate server: `http://localhost:3000` from the E: promotion worktree,
without a configured FastAPI origin.

```text
BROWSER_TODAY_STATUS=PASS (required sections render; unavailable state is explicit)
BROWSER_TOPIC_LIST_STATUS=PASS (formal API unavailable state is explicit)
BROWSER_TOPIC_DETAIL_STATUS=PASS (unavailable state is explicit for the synthetic test slug)
BROWSER_FAVORITES_STATUS=PASS
BROWSER_STOCK_EXPLORER_STATUS=PASS (synthetic Preview boundary remains explicit)
```

Today DOM readback confirmed `市場概況`, `今日市場重點`, and `今日主線` in the
required order. It contained no numeric `01`/`02`/`03` labels and no redundant
`盤中快照` label. No console error or warning was captured on the required
routes in this local smoke.

## Hydration classification

```text
TOPICS_HYDRATION_418_PRESENT=NO (not reproduced in this no-origin smoke)
TOPICS_HYDRATION_418_BASELINE_REPRODUCIBLE=NO (baseline no-origin smoke also clean)
TODAY_CANDIDATE_INTRODUCED_NEW_HYDRATION_ERROR=NO
BROWSER_REGRESSION_GATE=PASS
```

Historical reports classify minified React hydration warning `#418` as an
existing public/formal-runtime issue. This local environment intentionally had
no formal API origin, so it did not exercise the runtime condition that
historically emitted that warning. The same no-origin route was checked on
baseline `c177b949` and candidate; neither emitted it, and the candidate added
no new hydration error.

No browser action deployed, uploaded, submitted, or changed external state.
