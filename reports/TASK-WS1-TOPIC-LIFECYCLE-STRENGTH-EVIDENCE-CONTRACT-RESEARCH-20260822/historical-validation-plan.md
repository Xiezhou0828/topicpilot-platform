# Historical validation plan for Strength V0

## Gate and dataset

This plan is future work only. It must begin only after an explicitly labelled
`HISTORICAL_RECONSTRUCTED_SHADOW` dataset exists with PIT-safe or separately
declared research-only membership, daily observations, lineage, and quality
status. This task did not reconstruct, backfill, optimize, or query future
outcomes.

Every row should retain:

- topic identity and trading date;
- Lifecycle final/candidate/previous stage and transition context;
- the raw Strength evidence vector, not only a label;
- evaluation mode, policy/calculation version, membership mode, mapping/date
  boundary, source lineage, and quality fields;
- explicit null/unavailable state for missing dimensions;
- no synthetic or current-state values substituted for historical facts.

The pre-analysis protocol must separate `PIT_FORMAL` from
`CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY`. The latter can test wiring but
cannot be mixed into formal performance claims.

## Questions to test

1. **Within-stage separation:** conditional on the same Lifecycle stage, do
   higher/lower raw Participation or Intensity values separate future outcomes?
2. **Persistence information:** once a genuine rolling breadth window exists,
   does it add information beyond today's Participation/Intensity and
   Lifecycle context?
3. **Topic outcomes:** for H5 and H10 trading-day horizons, do topic-level
   future equal-weight returns, median member returns, positive-member share,
   and drawdown/continuation measures vary monotonically across pre-specified
   evidence strata?
4. **Constituent outcomes:** for eligible constituent rows, do future H5/H10
   returns and positive outcome rates differ by the same evidence strata? Keep
   constituent identity, missing future bars, delisting/status, and horizon
   eligibility explicit; do not turn missing outcomes into zero.

No benchmark, volume, news, institutional-flow, or intraday input is added to
Strength V0. Any future outcome definition must remain an outcome, not become
an input to the Strength contract.

## Analysis design

### Stage conditioning

Primary analysis is within each Lifecycle stage and, where sample allows,
within broad data-quality strata. Do not compare `MAIN_RISE` versus `DECLINING`
and call the difference Strength value; that would rediscover Lifecycle rather
than validate Strength independence.

Use topic-clustered or topic-blocked uncertainty because adjacent trading days
from one topic are not independent. Report the number of distinct topics and
dates, not only row count.

### Monotonicity

For each raw continuous evidence field and each pre-registered dimension
summary:

- use frozen quantile bins or rank-based bins selected without looking at
  future outcomes;
- report bin counts, median/mean H5/H10 outcomes, positive rates, and
  confidence intervals;
- test ordered direction with rank correlation or an ordered trend test;
- report violations of monotonicity rather than smoothing them away;
- compare raw vector results with any later labels to measure information loss.

Monotonicity is a validation question, not a reason to tune thresholds after
seeing outcomes. A non-monotone pattern should keep the field raw or mark the
hypothesis unsupported.

### Sample-size and power gates

Before outcome inspection, pre-register minimum cell size and topic diversity.
A practical starting proposal is at least 30 topic-day rows and 10 distinct
topics per reported cell, with a separate rule for constituent rows; the Owner
must approve or revise these gates before the study. Cells below the gate are
`INSUFFICIENT_SAMPLE`, not merged until a result appears favorable.

Report missing forward outcomes, censored/delisted constituents, duplicate
topic-days, and overlapping H5/H10 windows. Use block bootstrap or topic-level
resampling rather than treating every row as independent.

### Stability

Use a chronological split: an earlier development/research period, a later
holdout period, and, if enough dates exist, rolling time blocks. Do not tune
cutoffs on the holdout. Re-run the same frozen vector summaries across:

- early versus late date blocks;
- topic leave-one-out or topic-block holdouts;
- alternative valid-member minimums already declared by the input quality
  contract;
- formal versus explicitly research-only membership modes, reported
  separately.

Stability means direction, magnitude, and coverage of the finding remain
similar; it does not mean every cell must be identical.

## No outcome-driven threshold adjustment

The following rules are mandatory:

1. Freeze the raw evidence schema, classifier lineage, missingness rules, and
   any proposed label cut points before opening H5/H10 outcomes.
2. Do not choose a label boundary because it maximizes future return, hit rate,
   Sharpe-like statistics, or a preferred strategy outcome.
3. Do not search a grid of weights or create a total score. A future label
   change requires a new contract/policy version and a fresh validation split.
4. Keep exploratory correlations clearly marked exploratory; they do not
   authorize production labels or strategy changes.
5. If a threshold is changed after review, preserve the old version, document
   the Owner decision and reason, and validate the new version on untouched
   dates. Never overwrite historical evidence.
6. Apply multiple-comparison disclosure or correction when testing many fields,
   horizons, stages, and bins; do not report only the best result.

## WS3 consumption boundary

WS3 may attach the Strength vector to a research panel and ask whether it
conditions expectancy or interacts with an existing signal. It may use
within-stage stratification, continuous regressors, interaction terms, and
quality/missingness controls after pre-registration. It must not alter A2,
Legacy-5, or BOTH definitions, eligibility, entry/exit rules, position logic,
or production policy. A positive outcome finding is a research result, not a
Lifecycle rewrite and not an approval for a new score.

## Exit criteria

A future validation can recommend a new Strength contract only if it reports:

- stage-conditioned H5/H10 topic and constituent outcomes;
- sample size and distinct-topic coverage for every result;
- monotonicity and non-monotonicity;
- chronological and topic-block stability;
- missing/quality sensitivity;
- proxy versus formal-role sensitivity when formal roles later exist;
- no outcome-driven threshold search or post-hoc label tuning;
- explicit Owner decision and a new version for any changed semantics.

Until these criteria are met, retain the raw evidence vector and keep all
labels/overall levels unavailable or provisional.
