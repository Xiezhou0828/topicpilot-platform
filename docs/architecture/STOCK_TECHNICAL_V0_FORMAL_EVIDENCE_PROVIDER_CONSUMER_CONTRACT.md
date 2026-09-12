# Stock Technical V0 Formal Evidence Provider & Consumer Contract

**Task:** `TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820`
**Scope:** WS2-E2 contractification, bounded consumer validation, and 603-universe mainline closure
**Status:** `CANONICALIZED` only after the task commit is promoted; this document does not authorize release or Production

## 1. Authority and scope

This contract consumes, without redefining, the canonical Technical V0 policy
and the WS2-E1 expanded qualification. The owning algorithm source is
`services/api/src/topicpilot_api/technical_publication.py`; the frozen
indicator manifest is the E1 expanded formal indicator manifest.

The upstream Shared Data Foundation is `sdf-603-ohlcv-2y.v1`, with 603 active
instruments (TPE 370, TWO 233), 288,881 accepted OHLCV rows, and the
2024-08-13 through 2026-08-13 accepted-session window. Its normalized source
surface SHA-256 is
`e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4`; its
authority-content SHA-256 is
`fe1a51015d48d64b28007d36e291bed59085e7beacf5599ee5d5a35569747fcf`.

WS2 owns only:

```text
canonical observation
  -> indicator-specific required window
  -> continuity / eligibility
  -> Technical V0 evidence or explicit unavailable state
```

This contract does not create a route, persistence table, scheduler, UI, or
Production behavior. Advanced Technical remains deferred. Daily OHLCV is not
an Order Flow authority.

## 2. D1 continuity and eligibility

Continuity is event-bounded and indicator-level. Each indicator request is
evaluated against its own required observation window. The canonical state
vocabulary is:

| Contract meaning | Canonical state | Consumer behavior |
| --- | --- | --- |
| bounded authority proves the window is covered | `CONTINUITY_PASS_BOUNDED` | eligible for formal publication prerequisites |
| a known unresolved continuity-breaking event intersects the window | `CONTINUITY_FAIL` | no value; `UNAVAILABLE` / `BLOCKED` |
| authority, coverage, identity, lineage, or event scope is insufficient | `CONTINUITY_UNKNOWN` | fail closed; no ordinary formal value |

`event_table_has_no_matching_row` is never interpreted as `NO_EVENT`.
`event_table_has_no_data` is never interpreted as `CONTINUITY_PASS`. An empty
event result is evidence of no event only when a complete, authoritative,
identity-bound, market/session-bound query contract says so. Raw OHLCV remains
`adjustment_state=UNKNOWN`; this task does not infer adjusted truth.

The existing publication addendum may expose
`FORMAL_WITH_LIMITATION` / `AVAILABLE_WITH_LIMITATION` only when an explicit
bounded lookup limitation or known-event handling is present. The reference
provider additionally fails closed when no continuity envelope exists at all,
so missing authority cannot become a limited value by omission.

## 3. D2 frozen Technical V0 indicator identity

The following 14 IDs and policies are reused exactly from the canonical
`stock-technical-v0-policy.v4` contract. No new indicator, parameter, MA60
policy, rounding rule, or algorithm is introduced here.

| Indicator ID | Algorithm ID | Input / parameters | Minimum observations | Required window / warm-up |
| --- | --- | --- | ---: | --- |
| `MA5` | `SMA_CLOSE_V1` | accepted raw close; period 5 | 5 | last 5 accepted closes |
| `MA10` | `SMA_CLOSE_V1` | accepted raw close; period 10 | 10 | last 10 accepted closes |
| `MA20` | `SMA_CLOSE_V1` | accepted raw close; period 20 | 20 | last 20 accepted closes |
| `MA60` | `SMA_CLOSE_V1` | accepted raw close; period 60 | 60 | last 60 accepted closes |
| `DISTANCE_TO_MA20` | `DISTANCE_TO_MA20_V1` | `(close_t - MA20_t) / MA20_t` | 20 | same 20-close window; zero denominator unavailable |
| `RAW_CLOSE_RETURN_5D` | `RAW_OBSERVED_CLOSE_RETURN_V1` | `close_t / close_(t-5) - 1` | 6 | anchor-to-anchor 6-close window |
| `RAW_CLOSE_RETURN_20D` | `RAW_OBSERVED_CLOSE_RETURN_V1` | `close_t / close_(t-20) - 1` | 21 | anchor-to-anchor 21-close window |
| `VOLUME_MA5` | `SMA_VOLUME_QUANTITY_V1` | canonical volume quantity; period 5 | 5 | last 5 accepted volume observations |
| `VOLUME_MA20` | `SMA_VOLUME_QUANTITY_V1` | canonical volume quantity; period 20 | 20 | last 20 accepted volume observations |
| `VOLUME_RATIO_20` | `VOLUME_RATIO_20_V1` | current volume / `VOLUME_MA20` | 20 | same 20-volume window; zero denominator unavailable |
| `RSI14` | `RSI_WILDER_14_V1` | Wilder period 14; arithmetic mean seed of 14 changes | 15 | 15 closes for first seeded value; recursive state is retained |
| `MACD_12_26_9` | `MACD_12_26_9_SMA_SEEDED_EMA_V1` | fast 12, slow 26, signal 9; alpha `2/(N+1)` | 26 | 26 closes for MACD line |
| `MACD_SIGNAL_12_26_9` | `MACD_12_26_9_SMA_SEEDED_EMA_V1` | same; signal seed is first 9 valid MACD values | 34 | 34 closes for signal |
| `MACD_HISTOGRAM_12_26_9` | `MACD_12_26_9_SMA_SEEDED_EMA_V1` | MACD line minus signal | 34 | 34 closes for histogram |

Input sessions are canonical accepted market-local daily sessions ordered by
`trading_date`, `observed_at`, `ordering_key`, and `observation_id`. Missing,
invalid, or non-accepted observations are not zero-filled, carried forward, or
replaced by a browser calculation. No intermediate rounding is permitted;
the existing backend Decimal authority boundary remains the calculation
boundary.

## 4. Evidence identity and version contract

The logical identity is deliberately smaller than the metadata envelope:

```text
EVIDENCE_LOGICAL_IDENTITY =
  (instrument_identity, market, session_date, indicator_id)
```

The stable `evidence_key` is the canonical serialization of that tuple. The
version identity is metadata and is not silently folded into the logical key:

```text
EVIDENCE_VERSION_IDENTITY =
  technical_contract_version
  technical_policy_version
  indicator_id / indicator_version
  algorithm_id / algorithm_version
  parameter_set
```

The source identity binds:

```text
SOURCE_IDENTITY =
  source_foundation_version
  source_foundation_sha256
  source_authority_content_sha256
  price_authority
  series_semantics
  adjustment_state
  source_lineage
```

Every provider record carries `evidence_schema_version`, the three identity
envelopes, and a stable `lineage_reference`. A consumer can therefore ask
which source and formula produced a value without loading a historical
reconstruction artifact.

## 5. Provider contract

The bounded reference implementation is
`topicpilot_api.technical_v0_evidence_contract.TechnicalV0EvidenceProvider`.
It wraps the existing `build_technical_publication` implementation over an
in-memory bounded canonical-history envelope. A future provider may use the
canonical read model, but it must preserve this output contract.

Required operations are conceptually:

```text
get_evidence(indicator_id, session_date, as_of?)
get_batch(indicator_ids, session_date, as_of?)
get_historical(indicator_ids, from_session, to_session, as_of?, limit)
```

Each record preserves indicator/version/parameters, value or null reason,
session/as-of, required and actual observation windows, source foundation and
lineage, continuity/event evidence, PIT state, publication state, and the
instrument-level technical surface status. A failed lookup is an explicit
record; it is not an exception that a consumer is expected to reinterpret as
zero or false. Unknown indicator IDs are rejected because the formal set is
closed at 14.

The 6.7 GB E1 CSV is not a provider input. It remains a validation and
reproducibility artifact only.

## 6. Consumer contract and availability

The read-only consumer facade is
`TechnicalV0EvidenceConsumer`. Consumers may rely on explicit version,
session/as-of, PIT, source identity, lineage, continuity, and availability.
Consumers must not:

- treat unavailable as zero, false, or a missing signal;
- treat lookup limitation as no event;
- treat raw OHLCV as adjusted OHLCV;
- recalculate the frozen indicators in a browser or downstream consumer; or
- turn Technical V0 evidence into a strategy, ranking, recommendation, or
  opportunity meaning.

The canonical state mapping is:

| `publication_state` | `availability.state` | Meaning |
| --- | --- | --- |
| `FORMAL` | `AVAILABLE` | value and all mandatory prerequisites pass |
| `FORMAL_WITH_LIMITATION` | `AVAILABLE_WITH_LIMITATION` | value is bounded but carries explicit limitation reasons |
| `UNAVAILABLE` | `UNAVAILABLE` or `BLOCKED` | no consumer-usable value; reason is mandatory |
| `DEFERRED` | `BLOCKED` | outside the frozen contract |

`TechnicalV0EvidenceConsumer.value()` is the only reference unwrapping helper
and raises `EvidenceUnavailable` for non-available states. It never coerces a
null value.

## 7. PIT / as-of contract

Every record binds:

| Field | Rule |
| --- | --- |
| `session_date` | market-local anchor session for the evidence observation |
| `as_of` | retrieval/as-of boundary used for the request; it may be a date or timestamp |
| `required_observation_window` | indicator-defined window and minimum observation semantics |
| `actual_observation_window` | observations actually accepted into the value or warm-up decision |
| `source_max_session` | latest source session visible to this bounded request |
| `pit_status` | `PIT_SAFE` only when the request is prefix-bounded and no future observation/revision is consumed |

For a request at session `T`, the reference provider removes observations and
event knowledge after `T`, and additionally respects a supplied earlier as-of
boundary. A request with `as_of < session_date` is returned as
`AS_OF_VIOLATION`. A walk-forward consumer may use only records whose as-of
boundary is no later than its simulated decision point.

The E1 audit's `future_observation_invariance_pass=true` and
`future_event_invariance_pass=false` are both preserved in interpretation:
future bars/revisions did not leak, while event-aware publication is allowed
to change when a future event lookup is intentionally introduced. The latter
is not a future-price look-ahead claim.

## 8. Lineage contract

The source lineage is a compact, versioned reference rather than an arbitrary
large payload. It retains source code, adapter, normalization, mapping,
reference, observation semantics, quality, adjustment, and lineage state from
the canonical observation chain. The `lineage_reference` hash is stable for
the emitted source identity. A future adapter must preserve the same source
identity and version fields even if physical storage changes.

## 9. E1 artifact and future storage boundary

The E1 full surface is 4,044,334 rows, 6,726,285,286 bytes, and SHA-256
`48bdc38b9da4e2ba7e298f5341d04ad5dd11475c6019df1ac80593c9858ec254`. It is
retained in Git LFS as `REPRODUCIBILITY_VALIDATION_ARTIFACT` and has no runtime
provider, API, UI, or mandatory consumer dependency. Checkout/CI burden and
repository maintenance risk are recorded, but this task does not delete,
migrate, rewrite, or make a new persistence system. Future physical storage
is `OPTIONAL_OPTIMIZATION`: it may improve scale or checkout ergonomics, but
it is not required for this contract or WS2 mainline closure.

## 10. Boundaries and routing

The following remain outside this contract and deferred: Liquidity Sweep,
Order Flow, Anchored VWAP, Volume Profile, FVG, Supply & Demand, Fibonacci,
Patterns, and Technical V1. No daily OHLCV-derived proxy may be called true
Order Flow.

The contract is compatible with a future WS3 read-only research consumer,
future API adapter, and future UI adapter without requiring the E1 CSV or
redefining indicator semantics. This compatibility does not authorize WS3
strategy semantics, a route, a UI change, persistence, Production, deployment,
release, push, or any change to `NEXT_TASK`.
