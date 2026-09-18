# FUND-A contract, lifecycle, and freshness

## Availability contract

Each market/session row carries exactly one availability state:

`AVAILABLE`, `NOT_YET_PUBLISHED`, `SOURCE_UNAVAILABLE`,
`INGESTION_FAILED`, or `NON_TRADING_DAY`.

Missing fields, invalid numbers/dates, provider date mismatch, transport error,
and total reconciliation failure remain explicit. They are not neutral values.

## Read contract

`GET /api/v2/market/institutional-flow` accepts optional `market`, `asOf`,
`from`, `to`, and bounded `limit`. It returns a versioned envelope containing
TPE and TWO trends, with current and previous rows, complete-only rolling
5-session and 20-session sums, directional buy/sell streaks, numeric 5-vs-prior
5 acceleration deltas when ten complete sessions exist, and an evidence-only
price/flow relation.

Incomplete windows have `complete=false` and null numeric sums. A zero net is a
real flat observation; an unavailable or missing observation is not flat.

## Lifecycle

```text
market session close
  -> official provider publishes after-close summary
  -> separately activated FUND-A capture
  -> parse/reconcile with source hash
  -> idempotent formal persistence
  -> read API / Home materialization
  -> Today Market render and existing Today Signals evidence adapter
```

The existing daily post-close path begins earlier than the provider's confirmed
institutional summary availability. FUND-A is therefore modeled as
`PROVIDER_AFTER_CLOSE_ASYNC`: scheduler/job activation and operational timing
remain an owner/integration decision. This task does not alter A10 or any
scheduler.

## Freshness

Freshness is resolved by exact session identity: `CURRENT` when the fact's
trading date is the requested as-of date (or later under the explicit contract),
`STALE` when it is older, and `UNKNOWN` when session or source-as-of metadata is
missing. No age bucket or trading-day approximation is invented here.
