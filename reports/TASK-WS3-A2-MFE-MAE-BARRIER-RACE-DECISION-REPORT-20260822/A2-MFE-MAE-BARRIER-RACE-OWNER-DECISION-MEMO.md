# A2 MFE/MAE Barrier-Race Owner Decision Memo

Task: `TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822`
Scope: existing WS3 Core V0 A2 walk-forward research only.
Disposition: **STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED**.

## Decision questions

1. **Q1 — Does endpoint-only evaluation understate path opportunity?** **INCONCLUSIVE**. T10 endpoint-non-positive events with MFE10 ≥5%: 967/2559 (0.37788198515); with MFE10 ≥10%: 328/2559 (0.128175068386). This is path/endpoint disagreement evidence, not a declared strategy success.
2. **Q2 — Among T10 non-positive endpoint events, how many reached MFE10 ≥3/5/10?** 1413/2559 (0.552168815944); 967/2559 (0.37788198515); 328/2559 (0.128175068386).
3. **Q3 — How often did positive endpoint coexist with adverse path?** H10 endpoint-positive events with MAE10 ≤−3%: 1134/2587; ≤−5%: 634/2587; ≤−10%: 136/2587. No exit rule is inferred.
4. **Q4 — Typical favorable-excursion speed?** The H10 first-reach distribution is in `time-to-opportunity.csv`; median first reach is +3% day 1, +5% day 1, +10% day 3. `NOT_REACHED` remains a valid outcome.
5. **Q5 — Barrier race?** +5% before −5%: H5 2476/5160 (0.47984496124); H10 2709/5146 (0.52642829382). +10% before −5%: H5 1394/5160 (0.27015503876); H10 1736/5146 (0.33734939759). Same first day is order-unknown; no intraday guess was made.
6. **Q6 — Do candidate filters improve the path profile?** **MIXED**. The four rows in `path-aware-filter-ablation.csv` are descriptive ablations only; no price/volume floor is accepted as a production rule.
7. **Q7 — Is the claim “A2 is not as bad as endpoint proxy suggests” supported?** **PARTIALLY_SUPPORTED**. The path disagreement evidence is present, but Owner labels are 0/30, adjustment state is UNKNOWN_RAW_ONLY, and no executable exit semantics were supplied.
8. **Q8 — Next reasonable research focus?** **Owner label formalization**, followed by explicit outcome/exit semantics review. This is a recommendation only and does not change `NEXT_TASK`.

## Guardrails and blockers

- MFE/MAE anchor and endpoint semantics were inherited from the committed path-aware artifact: anchor is signal-day `a2_close`; endpoint is future close divided by anchor minus one; MFE/MAE use future high/low path extrema.
- Corporate-action uncertainty remains fail closed. `2327/2025-08-05` remains non-interpretable in `corporate-action-data-quality-audit.csv`.
- `3675/2026-07-06` remains `UNKNOWN_NO_PIT_SAFE_INDEX_BREADTH_PEER_DATA`; performance stays included when not suppressed, and it is not deleted as a supposed market shock.
- Owner fields in `owner-30-case-label-input-template.csv` are intentionally blank. The 30 reviewed cases are reference scope, not a training set or threshold-fitting set.
- `A_SETUP_ACCEPTED=NO`, `A_STRATEGY_ACCEPTED=NO`, `PRODUCTION_MUTATION=NO`, `DEPLOY=NO`, `PUSH=NO`, `NEXT_TASK_CHANGED=NO`.
