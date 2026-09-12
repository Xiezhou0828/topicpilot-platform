# Owner Decision Memo — Legacy-5 Benchmark

Task: `TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822`  
Dataset: `sdf-603-ohlcv-2y.v1`; `288881` accepted rows / `603` instruments; `e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4`.

## Direct answers

- Original `LEGACY-5`: distinct-episode endpoint expectancy is **0.0172 at T+5** and **0.0316 at T+10**; this is descriptive gross forward evidence, not a trade rule.
- `+MA60`: distinct episodes change T+5 endpoint mean from **0.0172** to **0.0184** (**+0.0011**), while removing **375 / 2471 (15.2%)** anchors/episodes. This is a small descriptive improvement, not acceptance evidence.
- `+PRICE20`: distinct episodes change T+5 endpoint mean from **0.0184** to **0.0180** (**-0.0004**), while removing another **144 / 2096 (6.9%)**. It does not further improve the endpoint mean in this comparison.
- Opportunity cost is material: `+MA60` excludes **236 / 172 / 73** distinct episodes that still reached MFE >=3% / >=5% / >=10%; incremental `+PRICE20` excludes **99 / 81 / 40**. It also removes **185 / 100** and **74 / 37** endpoint<=0 / MAE<=-5% cases respectively.
- A2 comparison: **PASS**. When PASS, the anchor/endpoint/MFE/MAE definitions are aligned; comparison remains descriptive and does not rank or merge strategies.
- Research decision: **evidence is worth continued research as a benchmark**, subject to the KD fallback contract, UNKNOWN_RAW_ONLY corporate-action limitation, gross/no-cost results, and a predeclared out-of-sample protocol before any acceptance discussion.

## Boundary

This memo does not create BUY/SELL, stop, take-profit, cooldown, or production semantics. `LEGACY-5+MA60` and `LEGACY-5+MA60+PRICE20` are descriptive comparisons only; A2/Core V0 is unchanged.
