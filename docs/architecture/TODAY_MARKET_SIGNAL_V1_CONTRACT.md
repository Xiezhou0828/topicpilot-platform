# Today Market Signal V1 Contract

Status: `FROZEN_OWNER_PRODUCT_CONTRACT`

This document is the durable semantic authority for Today Market Signal V1.
The executable evaluator is `services/api/src/topicpilot_api/market_signals.py`;
the machine-readable catalog is
[`TODAY_MARKET_SIGNAL_V1_CATALOG.json`](TODAY_MARKET_SIGNAL_V1_CATALOG.json).

## Purpose and boundary

Today answers 「今天市場正在交易什麼」 with deterministic, explainable,
formal-data-bound market conditions. Backend evaluation owns all thresholds,
temporal state, history, and frequency wording. The frontend formats the
backend payload only; it does not rederive signal logic.

V1 contains 16 signals in this fixed order:

1. `INDEX_STRUCTURE`: 雙盤分家、雙盤齊揚、雙盤走弱
2. `MARKET_BREADTH`: 紅盤失隊、全面開花、跌多漲少、上漲擴散、下跌擴散
3. `TOPIC_BREADTH_STRUCTURE`: 題材集中、題材擴散、題材分化
4. `MARKET_PARTICIPATION`: 量價齊揚、量增價跌
5. `INSTITUTIONAL_STRUCTURE`: 法人助攻、法人逆風、法人分歧

`OTC_VOLUME_PRICE_DIVERGENCE` is excluded from V1. The old four-signal
implementation is superseded by this catalog; no legacy signal is evaluated in
parallel.

## Formal authorities

- Index and whole-market breadth/price distribution: the existing formal Home
  market overview, using the TWSE + TPEx whole-market denominator.
- Topic breadth: current effective `FORMAL`/`PUBLISHED` Topic snapshots and
  their formal snapshot member facts. Topics with only one or two formal
  members are excluded from the evaluable denominator. The denominator is
  dynamic and never assumes a fixed Topic count.
- Turnover: formal TWSE and TPEx close turnover, combined as whole-market
  turnover. The baseline is the median of the previous 20 governed sessions;
  the current session is excluded.
- Institutional structure: same-date official TWSE + TPEx institutional-flow
  facts already persisted by the Today 009 path. A single exchange, stale
  carry-forward, unofficial fallback, or missing date is not sufficient.
- Temporal history: prior published Home publication payloads plus the existing
  formal Topic and institutional-flow history. No second signal-history table
  is created.

## Evaluation and fail-closed rules

Each record includes `signalStatus` (`ACTIVE`, `INACTIVE`, or
`NOT_EVALUABLE`), `evaluationStatus`, `authorityStatus`, and family-specific
`evidenceDetail`. Missing formal input is never converted to `INACTIVE`.

Index structure is mutually exclusive with precedence:

`INDEX_MARKET_DIVERGENCE → INDEX_BOTH_STRONG → INDEX_BOTH_WEAK → none`.

Breadth and Topic signals are intentionally allowed to overlap when their
separate dimensions support it. Turnover signals require both exchanges,
complete current facts, and 20 prior governed sessions. Institutional ratios
are net flow divided by whole-market turnover, with meaningful flow at ±0.20%.

Topic structure uses the median daily return of formal CORE members as a
signal-specific observation. It never uses Daily Grade, Lifecycle, or Topic
Score as an input.

## Temporal and frequency contract

An active signal is `NEW` only when the previous governed/evaluable session is
known false. It is `PERSISTING` when the previous governed/evaluable session is
also active. When prior state is unavailable, temporal status is
`INSUFFICIENT_HISTORY`; the backend must not make a false `NEW` claim.

`streakDays` counts consecutive governed sessions with the same signal active.
`occurrenceDays20d` counts true evaluations in the latest 20 governed sessions,
including the current session. A complete 20-session evaluable window is
required; otherwise `frequencyStatus=INSUFFICIENT_HISTORY` and the frequency
message is omitted.

Frequency text is static, signal-specific, and selected by the evaluator from
the catalog's template key. The product displays 「近20日發生 X 日」, never
event-episode wording and never the internal bands (`LOW`, `NORMAL`, `HIGH`,
`VERY_HIGH`) as the primary label.

## API and UI contract

`HomeMarketSignal` is extended additively with the signal identity, family,
active/status fields, temporal fields, 20-session fields, summary, trading date,
authority state, and structured evidence. Existing `key`, `name`, `severity`,
`direction`, `evidence`, and `interpretation` fields remain for compatibility.

The Today page displays all backend-active signals. It shows no more than five
cards in one active group and provides labelled, keyboard-accessible previous /
next controls when more groups exist. There is no automatic carousel. Market
Overview remains the first Today section.

## Governance

All thresholds are `OWNER_SEEDED_V1_PRODUCT_THRESHOLDS`; they are not
historically calibrated or statistically optimized. This implementation does
not run grid search, backtest optimization, threshold selection by returns, or
ML fitting.

`MIGRATION_REQUIRED=NO`: existing publication, Topic snapshot/member-fact, and
institutional-flow authorities support the contract. This candidate does not
create or apply a migration, deploy, activate Production, or mutate Production
data.
