# C1 Decision Intelligence Research Foundation

**Task:** `TASK-C1-DECISION-INTELLIGENCE-RESEARCH-FOUNDATION-001`
**Canonical base:** `Xiezhou0828/topicpilot-platform@4a35867a61d7a51051261f1706604fb42d3f5b24`
**Authority:** `EVIDENCE_ONLY`
**Mode:** deterministic, research-only, no production mutation

## Final status

`C1_RESEARCH_FOUNDATION_STATUS=PARTIAL_RESEARCH_FOUNDATION_WITH_EXPLICIT_DATA_GAPS`

The foundation is replayable for the committed L5 current-taxonomy
reconstruction and A2 technical/outcome panel. It is not formal historical
truth and cannot affect Score, Grade, Lifecycle, eligibility, ranking, or any
decision layer until owner review, C2 validation, formal contract creation,
and integration into canonical `main`.

## Existing research archaeology

`EXISTING_RESEARCH_REUSABLE=WS1/L5 lifecycle-strength reconstruction; WS3 technical x lifecycle conditional expectancy; WS3 A2 outcome/MFE/MAE panel; WS3 regime-not-available and benchmark-not-available disclosures`

`EXISTING_RESEARCH_GAPS=PIT Daily Grade history; PIT market regime series; historical institutional flow lineage; date-valid Structural Role/Leader history; market-relative benchmark`

`DUPLICATE_RESEARCH_AVOIDED=YES`

The implementation reuses committed evidence rather than recreating the WS1
or WS3 pipelines. The current taxonomy mapping is retained only as an
explicit research join and is marked `taxonomy_pit_safe=false`.

## Dataset design

- L5 source: 16,250 topic/date rows, 125 sessions, 130 topics, bounded to `2026-02-03`-`2026-08-13`.
- A2 source: 5,277 event rows; only signal dates inside the L5 window are joined.
- Joined C1 feature exposures: 2906; outcome labels: 11624.
- Every label uses trading-session horizon arithmetic from the committed A2 panel. A target date is never used to form the same-date feature group.
- Missing values remain unavailable; no value is inferred as zero.

## Feature coverage

| Feature family | Status | Interpretation |
|---|---|---|
| Lifecycle / breadth / structure | AVAILABLE_RESEARCH_ONLY | Reused L5 raw evidence; current taxonomy retrospective, not PIT |
| Technical MA60 state | AVAILABLE_RESEARCH_ONLY | Existing A2 research input; descriptive grouping only |
| Daily Grade | INSUFFICIENT | No canonical PIT Grade history; no proxy imputation |
| Market Regime | INSUFFICIENT | Canonical WS3 artifact explicitly records missing PIT-safe source |
| Institutional Flow | INSUFFICIENT | Historical lineage unavailable; no fabricated flow |
| Structural Role / Leader | UNKNOWN | Owner-curated authority unavailable for the historical window |

## Outcome coverage

| Horizon | Available forward labels | MFE/MAE source |
|---:|---:|---|
| T+1 | 2893 | A2 path-aware panel; status preserved |
| T+3 | 2845 | A2 path-aware panel; status preserved |
| T+5 | 2804 | A2 path-aware panel; status preserved |
| T+10 | 2677 | A2 path-aware panel; status preserved |

`market_relative_return` is unavailable because the canonical repository does
not contain a PIT-safe market benchmark for this study. `topic_relative_return`
is only populated when the current-taxonomy topic window and A2 target session
match exactly; it is not formal topic history.

## Conditional expectancy results

The generated `c1-lifecycle-technical-expectancy.csv` contains sample size,
coverage, missingness, mean/median, standard deviation, win rate, quantiles,
MFE, MAE, and sample warnings for each Lifecycle x MA60 state x horizon.
20 cells meet the descriptive minimum of 30 complete
labels without a flagged small-sample warning. Candidate cells are:
`DECLINING x ABOVE_MA60, FERMENTING x ABOVE_MA60, MAIN_RISE x ABOVE_MA60, MATURE x ABOVE_MA60, SPROUTING x ABOVE_MA60`.

The Grade x Lifecycle and Market Regime x Grade x Lifecycle tables are emitted
with explicit unavailable status, not fabricated combinations.

## Robustness analysis

The robustness surface includes earlier/later time splits, instrument/topic/date
concentration, trimmed means, missingness, and sample-size warnings. These are
descriptive diagnostics only. No group is called good or bad, and no threshold
is promoted into product policy.

Baseline status:

- unconditional, Lifecycle-only, and Technical-only descriptive baselines are available;
- Grade-only and Grade x Lifecycle are deferred for missing PIT Grade history;
- simple logistic and linear baselines are deferred until the feature contract is complete, so no proxy model is silently introduced.

## C2 disposition

`C2_PROMOTION_CANDIDATES=DECLINING x ABOVE_MA60; FERMENTING x ABOVE_MA60; MAIN_RISE x ABOVE_MA60; MATURE x ABOVE_MA60; SPROUTING x ABOVE_MA60`

`DEFERRED_FEATURES=Daily Grade; Market Regime; Institutional Flow; Structural Role/Leader; market-relative return; logistic/linear model baselines`

`REJECTED_FEATURES=none; no feature was rejected from evidence, but no unavailable feature was synthesized`

Lifecycle and MA60 state are candidates for C2 validation only. They remain
research evidence and are not production policy.

## Governance and replay checks

- `NO_LOOKAHEAD_VALIDATION=PASS`: only as-of L5/A2 feature columns form groups; future columns are consumed as labels only.
- `DUPLICATE_KEY_CHECK=PASS`: one `(event_id, topic_id, horizon)` label per joined exposure.
- `FUTURE_WINDOW_BOUNDARY_CHECK=PASS`: available targets are strictly later than signal dates; incomplete windows retain unavailable status.
- `RESEARCH_FORMAL_AUTHORITY_SEPARATION=PASS`: source class is `HISTORICAL_RECONSTRUCTED_RESEARCH` and output authority is `EVIDENCE_ONLY`.
- `JEV_INTEGRATION_READY=YES`; `JEV_INTEGRATION_IMPLEMENTED=NO`.
- `FORMAL_POLICY_CHANGED=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOYMENT=NO`; `MIGRATION=NO`.

## Canonical provenance and CI

This candidate was built from a clean isolated worktree based on
`Xiezhou0828/topicpilot-platform@4a35867a61d7a51051261f1706604fb42d3f5b24`. It is not canonical until the
accepted implementation and artifacts are integrated into `main` and re-run at
the exact integration SHA.

The GitHub Actions CI run `35684511356` for canonical `main` at
`4a35867a61d7a51051261f1706604fb42d3f5b24` was completed with `failure`: the backend Ruff no-new-debt
gate passed, but the changed-scope gate reported the pre-existing import-order
finding `I001` in
`services/api/alembic/versions/0037_task_b2_lifecycle_v1_3_formal_publication.py`;
the frontend job and secret scan passed. This task does not treat local focused
tests as a replacement for that remote CI evidence.

## Files and limitations

The artifact directory contains the feature inventory, outcome inventory,
coverage summary, conditional expectancy tables, robustness summary, joined
research dataset, manifest, and this report. Institutional flow is not emitted
as an expectancy table because its canonical status is
`INSUFFICIENT_FOR_RESEARCH`.

Remaining blockers are PIT historical Topic/Grade/Lifecycle authority, a
versioned market regime source, institutional history with lineage, date-valid
Structural Role/Leader authority, and a clean CI baseline. The next action is
to review this evidence and either provide those authorities for C2 or formally
defer the missing feature families.
