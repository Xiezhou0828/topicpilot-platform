# Selector V1 research contract

Status: `FROZEN_RESEARCH_CONTRACT`  
Version: `1.0`  
Owner decision: `FREEZE_SELECTOR_V1_RESEARCH_CONTRACT`  
Production status: `NOT_PRODUCTION`

## Purpose

This document is the canonical, research-only specification for TopicPilot
Core V0 Selector V1. It materializes the already-reviewed research result; it
does not run new research, create a production selector, or authorize a buy
list.

## Frozen architecture

`Lifecycle V1.3 topic context → C5 candidate screen → S2 within-topic ranking → Top2 research output`

Lifecycle is context, not a buy signal. Its information value remains
`PARTIALLY_SUPPORTED`.

## Candidate screen: C5

The frozen working screen is:

`C5_PASS = BREAKOUT_20D_T == TRUE AND CLOSE_T >= MA60_T`

`BREAKOUT_20D` and the accepted session/MA60 definitions are inherited from
the previous canonical implementation; they are not redefined here. C5 is
`WORKING_BASELINE_PARTIALLY_SUPPORTED`: frozen for Selector V1, but not
universal screen authority. The previous evidence reported same-event spread
of `+0.15% / +1.78% / +4.08%` at 5D / 10D / 20D, with downside
`MIXED_OR_WORSE`. These are same-event selection spreads, not absolute,
strategy, portfolio, alpha, or net returns.

## Ranking: S2

Within the same Leaf Topic, Lifecycle event/date, and C5 candidate pool:

1. Primary: `distance_to_ma60 = (Close_T - MA60_T) / MA60_T`, descending;
   higher is better as a structural distance measure.
2. Secondary: `volatility_20d`, descending, only when the raw primary value is
   exactly equal. Volatility remains a return-and-risk amplifier and does not
   become an equal decision authority.
3. Final deterministic fallback: canonical identity ascending in the order
   `instrument_id`, `market_code`, `instrument_code`.

S2 is lexicographic ordering. It is not a continuous weighted score and has
no 50/50, 70/30, optimized weight, or invented equivalence threshold.

## Top-N and small pools

`TOP2` is frozen for Selector V1. It is a research shortlist, not a portfolio,
buy list, equal-weight construction, or production recommendation.

- Empty pool: `NO_CANDIDATE_AFTER_SCREEN`; no fallback.
- One candidate: output that unique candidate; do not fill with a C5 failure.
- Two or more: output S2 Top2.

Top1 is retained as a secondary product option. Top3 is not preferred because
the evidence shows greater dilution and no better overall product trade-off.

## Missing data and boundaries

Missing price, MA60, breakout authority, distance, or required volatility
evidence fails closed. There is no synthetic fill or fallback. The price basis
is `PRICE_OPTION_A_RAW_CLOSE_BASELINE`; it is not adjusted-price or executable
performance authority. Historical research uses current canonical membership
as a frozen mapping because point-in-time historical membership authority is
unavailable.

Entry timing, position sizing, risk regime, benchmark, execution, and
transaction-cost contracts are not defined by Selector V1.

## Frozen evidence summary

The evidence table is maintained in
`selector-v1-frozen-evidence-summary.csv` in the closure package. The S2 Top2
same-event spreads are `+0.568%`, `+1.124%`, and `+1.761%` at 5D, 10D, and
20D. These figures describe within-event selection discrimination only.

The historical research universe contains 8,815 event-member rows, 8,198
price-valid rows, 617 fail-closed rows, 618 Lifecycle events, and 229 cycles.
The formal downside values and all other evidence remain traceable to the
source artifacts listed below.

## Non-goals

Selector V1 does not claim alpha, net executable return, Sharpe, production
activation, entry timing, position sizing, risk-regime control, or portfolio
construction. No future result may silently change this frozen V0 research
contract.

## Source reports

See the closure package at
`reports/TASK-WS3-CORE-V0-SELECTOR-V1-OWNER-FREEZE-CANONICAL-CONTRACT-MATERIALIZATION-AND-RESEARCH-SERIES-CLOSURE-20260830/`
for the Owner decision, evidence summary, lineage, limitations, tests, and
closure checklist. The machine-readable equivalent is
`selector-v1-contract.json` in this directory.
