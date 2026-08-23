# Stock Technical V0 Formal Publication Policy

**Status:** `PHASE_2B_IMPLEMENTED / PUBLICATION_SURFACE_RECONCILED_WITH_BOUNDED_LIMITATIONS`
**Contract version:** `stock-technical-v0-policy.v4`
**Task:** `TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818`
**Predecessor:** `TASK-FE-BE-STOCK-006B-PHASE-2A-CONTINUITY-AUTHORITY-GAP-CLOSURE`
**Implementation task:** `TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION`
**Scope:** D1 continuity eligibility, D2 Technical V0 candidate policy, D3 product boundary, and D4 PIT/as-of evidence requirements

This is the current additive publication-surface increment for the [Stock
Technical Publication Foundation](STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md).
It preserves the Phase 2A2 D1-D4 algorithms, MA60 gate, known-event overlay,
and evidence-only boundary while separating technical validity, event
authority, and publication status for the existing read surface.

## Phase 2A3 — Technical result, event authority, and publication surface (normative)

The stock-level publication object MUST expose three independent dimensions:

| Dimension | States | Meaning |
|---|---|---|
| `technical_result_status` | `VALID`, `INELIGIBLE`, `UNAVAILABLE`, `ERROR` | Whether the raw Technical V0 result and the Owner MA60 eligibility rule can be evaluated at the requested as-of session |
| `event_authority_status` | `KNOWN_EVENT`, `NO_KNOWN_EVENT_EVIDENCE`, `LOOKUP_UNAVAILABLE`, `NOT_APPLICABLE`, `ERROR` | What the known-event-aware overlay actually established; it never treats absent evidence as no event |
| `publication_status` | `AVAILABLE`, `AVAILABLE_WITH_LIMITATION`, `BLOCKED`, `UNAVAILABLE`, `ERROR` | What a downstream consumer may use from the bounded read surface |

The existing `status`, `publication_state`, and per-indicator evidence remain
backward-compatible carriers. A visible raw value with unresolved event
authority is marked `FORMAL_WITH_LIMITATION`, not silently upgraded to an
ordinary `FORMAL` value.

### Bounded lookup limitation

The known-event-aware evaluator retains `publication_allowed=false` for a
missing or timed-out event lookup. When identity, raw observations, algorithm
inputs, and MA60 eligibility are otherwise valid, the evaluator may also set
`bounded_limitation_allowed=true`. Technical values then remain visible as
`FORMAL_WITH_LIMITATION`, the stock surface is
`publication_status=AVAILABLE_WITH_LIMITATION`, and the deterministic reason
code is `EVENT_LOOKUP_UNAVAILABLE`. This is a disclosure of incomplete event
authority, not an assertion of `NO_EVENT`, `PASS_BOUNDED`, or adjusted-price
truth.

Malformed lookup envelopes, invalid identity/lineage, corrupt input, a known
unresolved continuity-breaking event, insufficient required history, and
calculation/contract errors do not receive the bounded limitation allowance.
They remain `UNAVAILABLE`, `BLOCKED`, or `ERROR` according to the decision
matrix. A verified event that intersects an indicator window remains
unavailable for that indicator; a verified event outside the MA60 window may
leave the stock technically eligible but causes an explicit
`AVAILABLE_WITH_LIMITATION` / `KNOWN_EVENT_HANDLED` surface when other
indicator windows are constrained.

### Mainline stock surface

The existing `/api/v2/stocks/{symbol}/technical` read object carries, at
minimum, instrument identity, request/as-of binding, `technical_result_status`,
`technical_eligibility`, `event_authority_status`, `publication_status`, MA60
evidence, reason codes, limitation reasons, policy/contract versions, input
authority, source lineage, and per-indicator continuity/event evidence. The
surface is analytical evidence only; it never emits recommendation or strategy
acceptance semantics.

Full-universe qualification MUST classify every formal instrument into one
deterministic surface row. `PUBLICATION_AVAILABLE` is not the only successful
outcome: `PUBLICATION_AVAILABLE_WITH_LIMITATION` is a distinct bounded
outcome, and raw coverage rates MUST be reported separately from eligible
availability rates.

## Phase 2A2 Owner-approved canonical addendum (normative)

This addendum is the current normative D1-D4 policy. It records the Owner
decisions in `TASK-FE-BE-STOCK-006B-PHASE-2A2-OWNER-TECHNICAL-V0-POLICY-CANONICAL-CLOSURE`
and supersedes the unresolved-policy wording in the historical Phase 2A and
Phase 2A.1 sections below. The predecessor sections remain retained evidence;
they must not be read as current `OWNER_POLICY_DECISION_REQUIRED` state.

### D1 — `FORMAL_RAW_OBSERVED` plus known-event-aware official overlay

Technical V0 uses:

```text
FORMAL_RAW_OBSERVED
+
KNOWN_EVENT_AWARE_OFFICIAL_OVERLAY
```

It does not claim adjusted-price truth, total-return truth, exchange-grade
continuity, or authoritative complete empty-set coverage. A successful,
identity-bound official event lookup may return
`NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND`; this is not `PROVEN_NO_EVENT` and
does not require `COVERED_NO_EVENT`. `price_basis` for every price-based V0
indicator is `RAW_OBSERVED`.

Continuity is evaluated independently at the minimum scope:

```text
canonical_symbol / identity
+
as_of_session
+
indicator_id
+
required_observation_window
```

The current bounded states are:

| State | Required meaning | Value/publication outcome |
|---|---|---|
| `CONTINUITY_PASS_BOUNDED` | Exact identity, as-of session, complete accepted-session window, canonical raw OHLCV, Owner-approved bounded evidence method, complete lineage/version, no known unresolved continuity-breaking event in the window, and no material evidence conflict | Continuity prerequisite may pass; residual uncertainty is disclosed and never described as exchange-grade proof |
| `CONTINUITY_FAIL` | A known continuity-breaking event intersects the required window at an exact effective date and no legal continuity resolution is available | `UNAVAILABLE`; no formal value |
| `CONTINUITY_UNKNOWN` + `EVENT_LOOKUP_UNAVAILABLE` | Event authority is missing or timed out while identity, raw input, algorithm, and MA60 eligibility remain independently valid | Ordinary formal clearance is unavailable; the valid raw result may be `FORMAL_WITH_LIMITATION` with `EVENT_LOOKUP_UNAVAILABLE` |
| `CONTINUITY_UNKNOWN` + successful lookup with `NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND` | The configured official event lookup completed, identity/normalization/lineage checks passed, and no known verified breaking event matched this exact window; universal event absence is not claimed | Technical V0 may publish if all other requirements pass; continuity remains `UNKNOWN` |

An absent event row, empty event table, or raw OHLCV that appears continuous is
not evidence of `PROVEN_NO_EVENT`. A publication-eligible no-match requires a
successful official event lookup and valid identity, normalization, and source
lineage. The result means only that no known verified breaking event was found
for the configured lookup; it does not assert exchange-grade event-family
completeness.

### D2 — fixed Technical V0 set and deterministic numeric policy

The complete V0 set is fixed to these fourteen outputs:

```text
MA5
MA10
MA20
MA60
DISTANCE_TO_MA20
RAW_CLOSE_RETURN_5D
RAW_CLOSE_RETURN_20D
VOLUME_MA5
VOLUME_MA20
VOLUME_RATIO_20
RSI14
MACD_12_26_9
MACD_SIGNAL_12_26_9
MACD_HISTOGRAM_12_26_9
```

No other indicator is added by this closure. Advanced Technical remains
`DEFERRED`, including Liquidity Sweep, Order Flow, Anchored VWAP, Volume
Profile, Fair Value Gap, Fibonacci, Supply & Demand, and Trading Patterns.

| Family | Algorithm identity/version | Parameters and minimum history | Required-window/warm-up semantics |
|---|---|---|---|
| MA | `SMA_CLOSE_V1` | `period ∈ {5,10,20,60}`; arithmetic mean of accepted closes; minimum `N` closes | Last `N` accepted sessions ending at `as_of_session`; incomplete window is `UNAVAILABLE_INSUFFICIENT_HISTORY` |
| Distance-to-MA20 | `DISTANCE_TO_MA20_V1` | `(close_t - MA20_t) / MA20_t`; ratio authority value; zero denominator unavailable | Same 20 accepted-close window as MA20; no automatic `EXTENDED`, `BUYABLE`, or entry interpretation |
| Returns | `RAW_OBSERVED_CLOSE_RETURN_V1` | `close_t / close_(t-N) - 1`; `N ∈ {5,20}`; raw observed close only | 5D requires 6 accepted closes; 20D requires 21; endpoint-to-anchor window is continuity-gated |
| Volume MA | `SMA_VOLUME_QUANTITY_V1` | Arithmetic mean of canonical `volume_quantity`; `period ∈ {5,20}` | Last `N` accepted volume sessions; unit/scale/aggregation remain bound to source lineage |
| Volume Ratio | `VOLUME_RATIO_20_V1` | `current_session_volume / volume_ma20`; no Volume Ratio 5 | 20 accepted volume sessions including the anchor; missing/zero denominator unavailable |
| RSI | `RSI_WILDER_14_V1` | Wilder RSI; 14 changes; minimum 15 closes | Initial seed is arithmetic mean of first 14 gains/losses, then Wilder recursion; flat series is 50, all-gain is 100, all-loss is 0; never NaN for these cases |
| MACD | `MACD_12_26_9_SMA_SEEDED_EMA_V1` | EMA alpha `2/(N+1)`; EMA12/EMA26 seeded by SMA; Signal is EMA9 of MACD line seeded by first 9 valid MACD values; Histogram is line minus Signal | MACD line first valid at 26 closes; Signal/Histogram first valid at 34 closes; accepted-session ordering is canonical and deterministic |

Calculation and serialization rules:

- No intermediate or dependent-calculation rounding is permitted.
- Authority values use the canonical Decimal numeric boundary already used by
  the V2 observation chain (`NUMERIC(38,18)` evidence); UI precision is not
  computation precision and may not alter the authority value.
- Accepted observations are canonical market-local sessions. The current TPE/TWO
  session context is `Asia/Taipei`; deterministic order is `trading_date ASC`,
  `observed_at ASC`, `ordering_key ASC`, `observation_id ASC`. Missing sessions
  are not filled, carried forward, or inferred from a browser or display layer.
- Price basis is `RAW_OBSERVED`; returns are not adjusted or total-return
  values.
- Missing, invalid, insufficient, continuity-failed, or continuity-unknown
  inputs remain unavailable; no partial window, zero-fill, carry-forward, or
  browser fallback is permitted.

### D3 — evidence-only product boundary

Technical V0 answers only what formal technical evidence exists for a stock at
an exact as-of session. It does not emit or imply `BUY`, `SELL`, `HOLD`, win
rate, entry/entry zone, stop-loss, take-profit, recommendation, position
 sizing, or strategy acceptance. Opportunity, Recommendation, WS3 research
candidate behavior, and Core V0 research protocol remain outside this task.

### D4 — PIT, lineage, and publication binding

Every future formal or unavailable V0 record must bind:

```text
canonical_symbol / identity
as_of_session
indicator_id
algorithm_id / version / parameters
minimum_history / required_observation_window
actual_observation_window
price_basis
continuity_state / continuity_evidence
source_authority / source_lineage
publication_state
value OR unavailable_reason
```

No later bar, event correction, reference snapshot, or adjustment result may
flow backward into an earlier walk-forward decision. A bare value such as
`RSI = 63` is not a reproducible formal publication.

### Current Phase 2B routing

All seven capability families have `OWNER_POLICY_STATUS=CLOSED` and
`IMPLEMENTATION_READINESS=READY_FOR_IMPLEMENTATION` at the policy/input
contract boundary. The known-event-aware official overlay remains a mandatory
runtime gate. A failed lookup remains unavailable for ordinary formal
clearance, but a valid raw result may use the bounded limitation surface
defined above. Invalid identity/lineage, ambiguous event, or a known
unresolved breaking event remains blocked/unavailable. The former affirmative
no-event, `COVERED_NO_EVENT`, and complete-event-family prerequisites are not
mandatory for WS2 publication after this Owner closure.

```text
OWNER_POLICY_DECISION_REQUIRED_REMAINING=0
INDICATOR_FAMILIES_READY_FOR_IMPLEMENTATION=7
INDICATOR_FAMILIES_BLOCKED=0
PHASE_2B_ROUTING=READY_FOR_PHASE_2B_TECHNICAL_V0_IMPLEMENTATION
IMPLEMENTATION_STARTED_BY_PHASE_2A2=NO
```

The routing recorded at Phase 2A2 closure was not implementation
authorization. Phase 2B required its own Owner-authorized task, implementation
contract/schema work, tests, and window-level `PASS_BOUNDED`/`FAIL`/`UNKNOWN`
evaluation. Bare `CONTINUITY_UNKNOWN` remains unavailable. With an unavailable
lookup, only a technically valid raw/MA60 result may publish through the
explicit bounded limitation surface; it must not be represented as a
successful no-match or as affirmative no-event evidence.

The Phase 2B implementation task has now been Owner-authorized and adds the
backend-owned deterministic calculator/read boundary described in the [Phase
2B closure report](../reports/TASK-FE-BE-STOCK-006B-PHASE-2B-TECHNICAL-V0-IMPLEMENTATION.md).
The D1-D4 decisions above retain the fixed algorithms, output set, product
boundary, and PIT requirements. The implementation does not make continuity
authority stronger than the exact event lookup envelope supplied at runtime.

## Historical Phase 2A baseline (superseded by the Phase 2A2 addendum)

| Decision | Phase 2A result |
|---|---|
| D1 continuity | Adopt event-bounded, indicator-level eligibility with `CONTINUITY_PASS`, `CONTINUITY_FAIL`, and `CONTINUITY_UNKNOWN`. The current canonical evidence can fail closed to `UNKNOWN`, but cannot generally prove `PASS`; no event row is not evidence of no event. |
| D2 Technical V0 | Candidate set is fixed to MA5/10/20/60, price-vs/distance-to-MA20, 5D/20D raw observed close return, Volume MA5/20, volume ratio, RSI14, and MACD 12/26/9. Candidate algorithm identities and required windows are documented below; seed/rounding/return-policy items that lack canonical authority remain unresolved. |
| D3 boundary | WS2 owns Observation -> Continuity/Eligibility -> Technical Evidence only. It never owns trade recommendations, strategy acceptance, or Opportunity/Recommendation scoring. |
| D4 PIT/as-of | Every future formal value must carry its indicator identity/value or explicit unavailable reason, session/as-of binding, required and actual observation window, algorithm/version/parameters, input authority/lineage, continuity status/evidence, and publication state. |
| Routing | `BLOCKED_BY_BOUNDED_CONTINUITY_AUTHORITY_GAP` |

The routing outcome is intentionally bounded. It does not require a complete
historical adjusted-price engine, exchange-grade event completeness for every
past symbol, or a global symbol-level technical block. It means that the next
implementation cannot publish a value until the exact indicator window has a
continuity decision and the remaining algorithm-policy items are accepted.

## 1. D1 — event-bounded, indicator-level continuity

### 1.1 Eligibility rule

For an indicator `I` at anchor session `t`, formal eligibility is:

```text
FORMAL_ELIGIBLE(I, t) =
  required observations exist
  AND actual observations satisfy quality and lineage requirements
  AND market session/calendar semantics pass
  AND the input is available as of t
  AND the indicator algorithm/parameter contract is accepted
  AND continuity(I, t) = CONTINUITY_PASS
```

Continuity is evaluated against the indicator's own required observation and
continuity window. A symbol-level `adjustmentState=UNKNOWN` does not by itself
invalidate every future window forever; it does mean that each affected window
must be evaluated fail-closed until an authoritative event/continuity result is
available.

### 1.2 Three-state semantics

| Status | Meaning | Formal value outcome |
|---|---|---|
| `CONTINUITY_PASS` | The authoritative event/adjustment evidence proves that no unresolved continuity-breaking event intersects the required window, or proves an applicable legal continuity resolution for every such event. | May satisfy the continuity prerequisite; it is not sufficient by itself for publication. |
| `CONTINUITY_FAIL` | The authoritative evidence proves that a continuity-breaking event intersects the required window and no accepted adjustment/continuity resolution is available for the requested series. | `UNAVAILABLE`; reason `CONTINUITY_FAIL`. No value is emitted. |
| `CONTINUITY_UNKNOWN` | Authority, coverage, event method, adjustment state, identity mapping, or source lineage is insufficient or conflicting for the required window. | `UNAVAILABLE`; reason `CONTINUITY_UNKNOWN`. No value is emitted. |

The following rule is absolute:

```text
event_table_has_no_matching_row != NO_EVENT
event_table_has_no_data       != CONTINUITY_PASS
```

An absent row can become `CONTINUITY_PASS` only when the source method and
coverage contract provide a complete, authoritative empty-set result for the
identity, event family, effective-date range, market, and as-of boundary.
Otherwise it is `CONTINUITY_UNKNOWN`.

### 1.3 Authority inputs required by a future evaluator

The evaluator must be able to bind, without rewriting raw OHLCV:

- canonical instrument identity and market;
- the exact market-local session range and session calendar version;
- event-family coverage and query/export method;
- event effective date, announcement/reference dates when relevant, and source
  as-of or retrieval lineage;
- old/new identity or ratio fields for split, reduction, merger, or conversion
  cases when continuity resolution is claimed;
- adjustment/continuity resolution policy and version; and
- a stable evidence reference or explicit `UNKNOWN` reason.

The event authority is window-scoped. A known lifecycle or event row may prove
a failure for an intersecting window, but it does not prove that all other
windows are event-free.

## 2. D2 — Technical V0 candidate contract

The following identities are the only Technical V0 candidates in this phase.
The IDs are immutable candidate names for Phase 2B implementation; naming an ID
does not authorize calculation or publication.

### 2.1 Candidate definitions and windows

| Indicator ID | Input and parameters | Minimum observations | Candidate warm-up / required window | Policy state |
|---|---|---:|---|---|
| `stock.sma.close.v1` (`MA5`, `MA10`, `MA20`, `MA60`) | Accepted daily `close`; `period=N`; arithmetic mean of the last `N` accepted close observations | `N` | First value only after `N` accepted observations; continuity covers the inclusive `N`-observation window ending at `t` | Deterministic candidate; publication still blocked by continuity and rounding authority |
| `stock.price_vs_sma20.v1` | Accepted daily `close`; `period=20`; `position` is `ABOVE`/`EQUAL`/`BELOW` by exact comparison with SMA20 | `20` | Same 20-observation window as SMA20, including the anchor close | Deterministic candidate; publication still blocked by continuity and rounding authority |
| `stock.distance_to_sma20.v1` | Accepted daily `close`; `period=20`; candidate distance is `(close_t - SMA20_t) / SMA20_t` | `20` | Same 20-observation window as SMA20; zero denominator is unavailable | Candidate formula documented; percentage/display scale and rounding remain unresolved |
| `stock.raw_close_return.v1` (`5D`, `20D`) | Accepted raw observed `close`; `horizon=N`; candidate formula is `close_t / close_{t-N} - 1` and is explicitly not adjusted or total return | `N+1` close observations, subject to endpoint/session decision | Inclusive anchor-to-anchor window `[t-N, t]`; no value before both endpoints and all required continuity checks are available | Unresolved until raw-return endpoint, adjustment, and rounding policy are explicitly accepted |
| `stock.sma.volume.v1` (`Volume MA5`, `Volume MA20`) | Accepted daily `volume_quantity`; `period=N`; arithmetic mean of the last `N` accepted volume observations with unit/aggregation retained | `N` | First value after `N` accepted volume observations; continuity covers the same window and volume-comparability policy | Deterministic raw-volume candidate; cross-event comparability remains unresolved |
| `stock.volume_ratio_to_sma20.v1` | Accepted daily `volume_quantity`; denominator is candidate `Volume MA20`; formula is `volume_t / VolumeMA20_t` | `20` | Same 20-observation volume window; zero/missing denominator is unavailable | Denominator is documented as a candidate, not yet an accepted publication policy |
| `stock.rsi.wilder.v1` | Accepted daily `close`; `period=14`; `delta`, positive/negative moves, Wilder averages, and `RSI = 100 - 100/(1+RS)` | `15` closes for the first seeded value (`14` changes) | Candidate seed is the arithmetic mean of the first 14 gains/losses; recursive values require the prior Wilder state. No value before the seed window; required pre-roll for a restarted series is not silently shortened | Seed, restart/pre-roll, zero-loss handling, and rounding require explicit acceptance |
| `stock.macd.ema.v1` | Accepted daily `close`; fast `12`, slow `26`, signal `9`; EMA alpha is candidate `2/(period+1)` | `26` closes for MACD line; `34` closes for MACD plus signal/histogram | Candidate SMA seeds slow/fast EMA; signal is seeded from the first 9 MACD lines. First signal/histogram candidate is close observation 34. Any longer pre-roll requirement is unresolved | EMA seed, pre-roll, line/signal publication, and rounding require explicit acceptance |

The `5D` and `20D` labels are not permission to use a provider's adjusted
return or to infer a return from display data. The candidate above is a raw
observed-close return and remains unavailable until the endpoint/session and
adjustment semantics are accepted.

### 2.2 Shared algorithm, session, and numeric policy

These are contract requirements, with unresolved values explicitly recorded
where current canonical authority is insufficient:

| Dimension | Phase 2A policy |
|---|---|
| Input fields | Price indicators use canonical accepted daily `close`; volume indicators use canonical accepted daily `volume_quantity` plus unit/scale/aggregation. No browser or legacy V1 field is an input authority. |
| Observation identity | Use canonical instrument, market, market-local session date, source/lineage version, and observation identity. Missing rows are not zero-filled or carried forward. |
| Session/calendar | Use the canonical market/session calendar and market timezone already attached to the historical read model. A calendar gap is not automatically a no-trade or no-event fact; the actual accepted observation window must be recorded. |
| As-of/PIT | At anchor session `t`, only observations and event/continuity evidence available under the contract's as-of boundary may enter. Later corrections or event findings cannot flow backward into a historical value without a new versioned replay. |
| Rounding | `UNRESOLVED_POLICY`; no display rounding, EOD rounding, binary-float shortcut, or implicit provider rounding may be used for a formal value. Phase 2B requires an explicit scale and rounding mode or an explicit unrounded Decimal serialization decision. |
| Null/availability | A value is `FORMAL` only after every prerequisite passes. Otherwise the field is `UNAVAILABLE` with a stable reason; no zero, carry-forward, shortened window, or browser fallback is allowed. |
| Core null reasons | `INSUFFICIENT_HISTORY`, `MISSING_REQUIRED_FIELD`, `INVALID_NUMERIC`, `CONTINUITY_FAIL`, `CONTINUITY_UNKNOWN`, `LINEAGE_INCOMPLETE`, `AS_OF_VIOLATION`, `DENOMINATOR_ZERO`, `ALGORITHM_POLICY_UNRESOLVED`, and `SOURCE_CONFLICT`. |
| Calculation owner | Backend-only deterministic implementation. Browser calculation is permanently `NO`. |

### 2.3 Unresolved algorithm decisions

The current canonical repository contains no accepted Stock algorithm contract
for these V0 fields. Phase 2A therefore records, rather than invents, the
following decisions for Phase 2B acceptance:

- whether the candidate raw-return endpoint rule is accepted as the formal
  meaning of `5D`/`20D`;
- the exact rounding scale/mode or unrounded serialization policy;
- RSI14 seed, zero-loss/zero-gain semantics, restarted-series pre-roll, and
  whether a longer historical seed is mandatory;
- MACD EMA seed, restarted-series pre-roll, and whether the formal publication
  includes line-only values before signal/histogram availability; and
- whether the candidate volume ratio denominator is formally Volume MA20 and
  how volume comparability is treated across an event window.

Until those decisions are accepted, the named IDs remain `PROPOSED_CANDIDATE`
and their values remain unavailable even when observations exist.

## 3. D3 — product boundary

WS2 owns this chain only:

```text
canonical observation
  -> indicator-specific required window
  -> continuity / eligibility decision
  -> backend technical evidence or explicit unavailable reason
```

WS2 must not emit or derive:

- `BUY`, `SELL`, entry, target, stop-loss, win rate, or position sizing;
- strategy trigger, acceptance, ranking, grade, or expected outcome;
- Opportunity Grade, Recommendation score, recommendation gate, or strategy
  acceptance semantics; or
- any claim that a technical state is a recommendation.

Those meanings remain downstream WS3 research and the later formal
recommendation gate. Technical evidence may be an input to future research,
but it does not become a strategy result merely because it is deterministic.

## 4. D4 — PIT/as-of and evidence binding

Every future formal technical record, including an unavailable record when a
request is evaluated, must be able to bind at least:

| Required field | Meaning |
|---|---|
| `indicator_id` | Immutable candidate/accepted algorithm identity, such as `stock.sma.close.v1`. |
| `value` or `availability_reason` | A formal numeric/state value or explicit null/unavailable reason; never a silent omission. |
| `session_date` / `as_of` | Market-local anchor session and the as-of boundary used for the decision. |
| `required_observation_window` | Contract-defined start/end, count, and observation semantics. |
| `actual_observation_window` | Actual accepted observations, IDs/count, first/last session, and any missing/invalid state. |
| `algorithm_id` / `version` / `parameter_set` | Exact calculation identity and parameters used or the unresolved policy identity. |
| `price_authority` / `source_lineage` | Canonical observation authority, source/adapter/normalization/mapping/reference versions, and lineage references. |
| `continuity_status` / `continuity_evidence` | One of `PASS`, `FAIL`, `UNKNOWN` plus the bounded event/authority evidence or reason. |
| `event_lookup_state` / `event_lookup_evidence` | Successful official lookup with `NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND`, or explicit unavailable/known-event handling; never a universal no-event claim. |
| `publication_state` | `FORMAL`, `FORMAL_WITH_LIMITATION`, `UNAVAILABLE`, or `DEFERRED`; bounded event-authority uncertainty is explicit and never serialized as ordinary `FORMAL`. |

The minimum accepted publication state is therefore:

```text
FORMAL =
  value present
  + as-of and session bound
  + exact observation window bound
  + exact algorithm/parameters bound
  + canonical source lineage bound
  + successful official event lookup
    (or explicit event-aware handling)
  + all other quality/PIT prerequisites pass
```

`FORMAL_WITH_LIMITATION` carries the same value, window, algorithm, lineage,
and PIT bindings but records a bounded `EVENT_LOOKUP_UNAVAILABLE` or
`KNOWN_EVENT_HANDLED` limitation through the current publication-surface
addendum. It is available to the bounded analytical surface only; it is not an
affirmative no-event or ordinary event-cleared publication.

A walk-forward consumer may query only records whose as-of boundary is at or
before its simulated decision point. It must not use a later event correction,
later bar, later reference snapshot, or current-state adjustment result to
reconstruct an earlier technical value.

## 5. Advanced Technical remains deferred

The following are not Technical V0 and have no Phase 2A publication contract:

`Liquidity Sweep`, `Anchored VWAP`, `Volume Profile`, `FVG`, `Supply & Demand`,
`Fibonacci`, `Patterns`, and `Order Flow`.

Daily OHLCV can be a raw input to a future explicitly named bar-structure
detector, but it is not true order-flow data. No OHLCV-derived proxy may be
labelled or published as `Order Flow` without a separate authority and
contract.

## 6. Phase 2B gate

Phase 2B may begin implementation only after all of the following are present:

1. a bounded, source-approved continuity authority that can return
   `PASS`/`FAIL`/`UNKNOWN` for the exact required window without treating an
   empty result as `NO_EVENT`;
2. a legal adjustment/continuity resolution policy for known events, without
   requiring a full adjusted-price engine;
3. acceptance of the unresolved algorithm decisions in Section 2.3;
4. tests for minimum history, warm-up, missing/invalid inputs, all three
   continuity states, as-of isolation, null reasons, and deterministic
   serialization; and
5. no change to the WS2 product boundary or the WS3/WS4 frozen scopes.

The next bounded authority task should close only the continuity evidence gap
for the required indicator windows. It must not expand into a full historical
corporate-action migration or adjusted-price persistence project.

## Owning evidence

- [WS2 Phase 1 foundation contract](STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md)
- [WS2 Phase 1 closure report](../reports/TASK-FE-BE-STOCK-006B-TECHNICAL-PUBLICATION-FOUNDATION.md)
- [Stock technical readiness audit](../reports/TASK-FE-BE-STOCK-006_TECHNICAL_HISTORICAL_PUBLICATION_READINESS_AUDIT.md)
- [Stock-006A raw historical bar publication](../reports/TASK-FE-BE-STOCK-006A_HISTORICAL_BAR_READ_PUBLICATION.md)
- [Current-state cold-start reconciliation](../reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md)
- [HIST-002B canonical historical authority closure](../reports/TASK-DATA-HIST-002B_CANONICAL_RECONCILIATION_CLOSURE.md)
- [REC-A1 corporate-action source/semantics closure](../reports/TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE.md)
- [REC-A1 research-only protocol closure](../reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE_CANONICAL_CLOSURE.md)
- [Phase 2A machine-readable authority audit](../../reports/TASK-FE-BE-STOCK-006B-PHASE-2A-TECHNICAL-V0-POLICY-CLOSURE/technical-v0-policy-authority-audit.json)
