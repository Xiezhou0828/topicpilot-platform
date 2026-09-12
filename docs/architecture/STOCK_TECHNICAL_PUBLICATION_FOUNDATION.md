# Stock Technical Publication Foundation

**Status:** `FOUNDATION + TECHNICAL V0 IMPLEMENTED / WINDOW-GATED`
**Contract version:** `stock-technical-publication-foundation.v2`
**Scope:** formal Stock technical input, deterministic V0 evidence, provenance, and fail-closed publication

This contract is additive to the canonical bounded historical-bar read model.
It does not change the historical observation authority, adjustment data, EOD
semantics, Stock detail payload, Topic Intelligence, Opportunity, or
Recommendation behavior. Technical V0 calculation is backend-owned and is
governed by the frozen [Technical V0 policy contract](STOCK_TECHNICAL_V0_POLICY_CONTRACT.md).

## Authority and semantic boundary

The only technical input authority is the shared backend reader:

```text
topicpilot.canonical_observations
  -> topicpilot_api.historical_read_model.read_historical_bars
  -> topicpilot_api.technical_publication.build_technical_publication
  -> Stock technical publication/read model
```

The input is `RAW_OBSERVED_DAILY_BAR`. Raw observed OHLCV is not adjusted
truth, a total-return series, or proof of cross-event continuity. The reader
keeps canonical source, quality, market-local date, lifecycle, as-of, ordering,
and lineage-version fields; it does not call a provider, read the retained
legacy OHLCV table, fill nulls, or infer missing sessions.

The current canonical historical bar chain has `adjustmentState=UNKNOWN` at
this publication boundary. Technical V0 therefore evaluates each exact
indicator window through bounded continuity evidence. Missing evidence is
`CONTINUITY_UNKNOWN` and the indicator is `UNAVAILABLE`; it is never treated as
`NO_EVENT`. Only a bounded `CONTINUITY_PASS_BOUNDED` window may publish a
`FORMAL` value.

## Read contract

```text
GET /api/v2/stocks/{symbol}/technical
required query: from, to
optional query: market, limit
limit: 1..200, default 200
date range: inclusive market-local date; reversed range is 422
```

The response is `StockTechnicalPublicationRead` and contains:

- `technicalContractVersion`: immutable contract identity;
- `status`: `FORMAL` when at least one exact window passes, otherwise
  `UNAVAILABLE` for a non-empty raw input;
- `publicationState`: `FORMAL`, `UNAVAILABLE`, `DEFERRED`, or
  `NOT_PUBLISHED` for an empty range;
- `inputState`: `RAW_OBSERVED` or `UNAVAILABLE`;
- `calculationOwner=BACKEND_ONLY` and `browserCalculationAllowed=NO`;
- `publishedIndicators`: the canonical fourteen output IDs that have formal
  evidence in the requested range;
- `technicalEvidence`: backend-owned formal or unavailable records with
  identity, as-of, exact required/actual windows, algorithm/version/parameters,
  price basis, continuity evidence, lineage, publication state, and reason;
- explicit `availabilityReasons` and deferred Advanced Technical families; and
- `provenance`, including authority, raw-series semantics, adjustment state,
  accepted quality states, source/adapter/normalization/mapping/reference
  versions, lineage state, row count, and returned/as-of timestamps.

An empty accepted range is `UNAVAILABLE` with
`NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS`. It is not zero-filled, carried
forward, or replaced by Preview data.

## Fail-closed rules

Technical values remain unavailable when any required authority is missing:

| Condition | Foundation result |
|---|---|
| Exact continuity evidence is `CONTINUITY_PASS_BOUNDED` | The window may publish `FORMAL` evidence |
| Exact continuity evidence is `CONTINUITY_FAIL` | `UNAVAILABLE`; reason `CONTINUITY_FAIL` |
| Exact continuity evidence is `CONTINUITY_UNKNOWN` | `UNAVAILABLE`; reason `CONTINUITY_UNKNOWN`; fail closed |
| Required algorithm/warm-up observations are missing | `UNAVAILABLE_INSUFFICIENT_HISTORY`; no partial value |
| Source lineage versions are incomplete or mixed | `UNAVAILABLE`; disclose the lineage reason |
| No accepted canonical price observations | `UNAVAILABLE`; publish no values |

The absence of a corporate-action record does not prove `NO_ACTION`. The
bounded continuity evaluator requires explicit identity/as-of/indicator/window
scope, evidence lineage, and completed bounded coverage. It never creates an
adjusted-price or total-return series.

## Frontend boundary

The browser may request and render this backend-owned evidence contract only.
It must not calculate, adjust, rank, reconcile, or infer technical semantics
from raw OHLCV. No new frontend product surface is introduced by Phase 2B;
generated API declarations may consume the backend contract later.

## Explicit non-scope

This foundation does not implement or publish:

- Advanced Technical: Liquidity Sweep, Order Flow, Anchored VWAP, Volume
  Profile, FVG, Fibonacci, Supply & Demand, Trading Patterns, support/retest,
  breakout strategy logic, or technical events;
- corporate-action markers or event timeline items;
- database tables, migrations, historical data writes, provider calls,
  scheduler changes, Production changes, deploy, or `NEXT_TASK` changes.

## Owning references

- [Historical bar publication](../reports/TASK-FE-BE-STOCK-006A_HISTORICAL_BAR_READ_PUBLICATION.md)
- [Technical V0 policy](STOCK_TECHNICAL_V0_POLICY_CONTRACT.md)
- [Technical V0 Phase 2B implementation closure](../reports/TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION.md)
- [Technical historical publication readiness audit](../reports/TASK-FE-BE-STOCK-006_TECHNICAL_HISTORICAL_PUBLICATION_READINESS_AUDIT.md)
- [Current project state handoff](../reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md)
- [V2 frontend design specification](TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md)
