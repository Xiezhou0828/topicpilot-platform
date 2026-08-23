# Formal Closure Report — TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822

## Scope and disposition

This report closes an isolated WS3-only descriptive robustness study of the already-frozen A2 × LEGACY-5 overlap. It does not create A3, alter A2/Core V0 semantics, alter LEGACY-5 semantics, or mutate WS1/WS2/WS4, Production, API/UI, scheduler, or NEXT_TASK.

Final disposition: **RESEARCH_CANDIDATE**. `OUT_OF_SAMPLE_SUPPORTED=NO`; the result is not an accepted strategy.

## Input reconciliation

- Accepted source surface: 288881 rows, 603 instruments, 2024-08-13 to 2026-08-13; normalized source SHA-256 `e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4`.
- A2 cohort: 5,277 committed events with path-aware H1-H10 reconstruction.
- LEGACY-5 cohort: 2,471 raw anchors; V2 MA60 ablation: 2,096 anchors.
- Matching: one-to-one by instrument and accepted canonical session position within the predeclared ±1 window.
- Corporate-action state: UNKNOWN_RAW_ONLY; same-session barrier races: SAME_SESSION_ORDER_UNKNOWN.
- Benchmark/regime: NOT_AVAILABLE dispositions; no external or synthetic series.

## Robustness controls

Endpoint statistics include count, mean, median, sample standard deviation, positive rate, P25 and P75 at T+1/T+3/T+5/T+10. Path statistics include MFE/MAE distributions, threshold rates, fixed barrier races, and MFE/|MAE| as a descriptive excursion ratio. Extreme-winner policies were fixed at 1%/5% quantiles before outcome review. Calendar years and the 2025-08-13 midpoint were fixed before comparison. No threshold search or multiple-testing selection was performed.

The BOTH rows intentionally report two source observations per matched pair, with pair_count reported separately. This preserves the prior artifact's PAIR_COMBINED descriptive convention while avoiding a claim that the two source observations are independent.

MA60 ablation is not a joint-quality acceptance: the same-session BOTH H5 mean is unchanged at 0.025834; V2 removes 375 raw anchors, including 173 MFE>=5% opportunities and 185 non-positive endpoints. The path/downside trade-off is therefore descriptive and unresolved, not a production recommendation.

## OOS and acceptance boundary

The current 2024-08-13 to 2026-08-13 panel is reused in-sample for this robustness exercise. No untouched later period exists, so OUT_OF_SAMPLE_SUPPORTED=NO. A future OOS must freeze the signal definitions, ±1 matching, horizons, barriers, and reporting rules before accumulating later sessions.

## Governance flags

`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `JOINT_SIGNAL_ACCEPTED=NO`; `CORE_V0_MUTATION=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`.

## Artifact hashes

- `OWNER-DECISION-MEMO.md`: `239fcee59763c8f52ff4d118827cd81d15b233d3b63b135f37949d8f57cd428e`
- `benchmark-adjusted-analysis.csv`: `80c45ad4087cf4f33acd5153a0339facfcbea434901829a493029c9ff9771afa`
- `benchmark-not-available.csv`: `80c45ad4087cf4f33acd5153a0339facfcbea434901829a493029c9ff9771afa`
- `extreme-winner-dependence.csv`: `a8f74ebd898a00068031419cf6763392feeb7009166b3edffdbfc1de6c8d25ca`
- `instrument-concentration-analysis.csv`: `8c6ade99d1910c29cda6be9dde8b75ef09a76e310b1b07113a6027eb61c91147`
- `joint-signal-endpoint-robustness.csv`: `462230ddd30befe675f5b912b9eafaa8e152b69edb8d9afc7399244758f53b4f`
- `joint-signal-path-robustness.csv`: `1cb7e7e9b0cdc1104836265158eb0d8b5e60941e01917543f443618c6983c443`
- `ma60-joint-signal-ablation.csv`: `15ceceb9e9fa4917c5633f15c38cc967586e5f909ca0f9deca65e47b628ab1dd`
- `market-split-analysis.csv`: `0faaf007db14deb6a63424f6d42f9a95c870e980a39055be4b30d5a026631de5`
- `regime-not-available.csv`: `0a1b318edfc853ec66a1e258d9cdc77993fef4ad492b98490655e987442954b7`
- `regime-robustness.csv`: `0a1b318edfc853ec66a1e258d9cdc77993fef4ad492b98490655e987442954b7`
- `signal-timing-path-analysis.csv`: `4fe3b34aa4f2615fecf2fdb96334b12bc0344753991cb9fbb1eef476a17df17b`
- `source-semantics-reconciliation-manifest.json`: `9fa5e54da5ab293abbd9bcc0e7a37f11344a62c6e71ecf80ca219d99651c93bd`
- `statistical-robustness-summary.json`: `11710758e80a1f86d92e337425207037bb0a379b1d13fbf60bb6d65abe928e46`
- `time-stability-analysis.csv`: `591751e81bc6b15759bedc212ec3bbfc9c3b5ff644317a5a08f45796ded2e0e7`
