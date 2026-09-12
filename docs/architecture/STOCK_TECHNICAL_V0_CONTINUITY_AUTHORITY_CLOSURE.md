# Stock Technical V0 Continuity Authority Closure

**Status:** `PHASE_2A1_CLOSURE / BOUNDED_CONTINUITY_AUTHORITY_GAP_REMAINS`
**Contract version:** `stock-technical-v0-continuity-authority.v1`
**Task:** `TASK-FE-BE-STOCK-006B-PHASE-2A-CONTINUITY-AUTHORITY-GAP-CLOSURE`
**Scope:** bounded continuity authority, remaining V0 algorithm-policy decisions, and family-level Phase 2B routing

This is the Phase 2A.1 policy increment over the [Stock Technical V0 Formal
Publication Policy](STOCK_TECHNICAL_V0_POLICY_CONTRACT.md). It audits the
currently committed event and price-lineage evidence. It does not calculate,
persist, expose, migrate, adjust, or render any technical value.

## Closure result

The current canonical evidence is sufficient to define the three-state
continuity evaluator and to fail closed, but it is not sufficient to approve a
general `CONTINUITY_PASS` for the V0 windows. A bounded exact known event can
support `CONTINUITY_FAIL` when its accepted effective date intersects the
requested window and no legal continuity resolution exists. A missing event
row, partial event-family method, missing as-of lineage, identity gap, or
unproven empty set is `CONTINUITY_UNKNOWN`.

```text
CONTINUITY_AUTHORITY_RESULT=BOUNDED_FAIL_AND_UNKNOWN_ONLY
GENERAL_CONTINUITY_PASS_AUTHORITY=NOT_ESTABLISHED
EMPTY_EVENT_RESULT_IS_NO_EVENT=NO
RAW_OHLCV_REWRITE=NO
ROUTING_OUTCOME=BLOCKED_BY_BOUNDED_CONTINUITY_AUTHORITY_GAP
```

This is a bounded gap. It does not require a full adjusted-price engine,
adjusted OHLCV persistence, full-history migration, or a global 507-symbol
continuity reconstruction before any future family can be considered.

## 1. Bounded indicator-level continuity evaluator

For indicator `I` at anchor session `t`, the evaluator must first resolve the
exact required observation window from the accepted algorithm contract. It
then evaluates the following gates without changing raw observations:

```text
continuity(I, t) =
  UNKNOWN if identity/market/session/as-of/event-family authority is incomplete
  FAIL if an authoritative continuity-breaking event intersects the window
       and no accepted legal continuity resolution is available
  PASS only if every relevant event family has authoritative empty-set proof
       or an accepted continuity resolution for every intersecting event
```

The result is independent for each indicator window. A symbol-level
`adjustmentState=UNKNOWN` does not permanently block every future window, but
it does not permit a window to be called clear by default.

### Three-state publication semantics

| Status | Evidence requirement | Future value outcome |
|---|---|---|
| `CONTINUITY_PASS` | Exact identity, market, session range, event-family coverage, effective-date/as-of lineage, and authoritative empty-set or legal-resolution evidence all pass | May satisfy the continuity prerequisite; it is not by itself a complete publication gate |
| `CONTINUITY_FAIL` | An accepted event/continuity authority proves a continuity-breaking event intersects the exact window and no accepted resolution applies | `UNAVAILABLE`; reason `CONTINUITY_FAIL` |
| `CONTINUITY_UNKNOWN` | Any required authority is missing, partial, conflicting, method-dependent, not PIT-bound, or cannot prove the empty set | `UNAVAILABLE`; reason `CONTINUITY_UNKNOWN` |

The following are invariant and must be tested by any future evaluator:

```text
event_table_has_no_matching_row != NO_EVENT
event_table_has_no_data       != CONTINUITY_PASS
reviewed_not_found            != AUTHORITATIVE_EMPTY_SET
```

### Required authority fields

For every exact window, the authority closure must bind:

- canonical instrument identity and market (`tw-reference-v1` or a later
  accepted version);
- market-local session calendar and the inclusive required session range;
- event-family coverage, source/method, retrieval or source-as-of lineage, and
  effective date semantics;
- authoritative empty-set/no-event proof when `PASS` is claimed;
- event identity, old/new identity or ratio fields, and legal continuity
  resolution for split, reduction, merger, conversion, or similar cases when
  `PASS` is claimed; and
- a stable evidence reference or a specific `UNKNOWN` reason.

Known event evidence is window-scoped. It can prove a failure for an exact
intersecting window, but it cannot prove that other windows or other event
families are clear.

## 2. Current canonical authority audit

The audit uses only committed repository evidence:

| Authority surface | Current committed evidence | Phase 2A.1 conclusion |
|---|---|---|
| Raw price/volume observations | HIST-002B: 507 approved identities, 63,826 accepted OHLCV rows, 2026-02-02 through 2026-08-13; `RAW_OBSERVED` / `ADJUSTMENT_STATE=UNKNOWN` | `PASS_RAW_OBSERVATION_ONLY`; not continuity proof |
| Identity and market context | `tw-reference-v1`, 314 TPE and 193 TWO identities, market-local historical lineage | Bounded identity/session context passes; not event completeness |
| Event-family coverage | REC-A1 coverage matrix: 4,056 identity×family cells, 368 `COVERED_EVENT`, 3,688 `UNKNOWN`; reviewed `METHOD_GAP` remains | Partial; default for uncovered cells is `CONTINUITY_UNKNOWN` |
| Empty-set/no-event proof | REC-A1 freeze: 353 event identities, 154 reviewed UNKNOWN identities, 0 authoritative no-event identities, complete empty-set proof `NO` | No general `CONTINUITY_PASS` |
| Exact known lifecycle event | TPE:6806 effective termination 2026-06-23; last accepted bar 2026-06-22; no rows on/after effective date | Bounded known intersection may be `CONTINUITY_FAIL`; not a global pass |
| Corporate-action source use | REC-A1 is owner-approved internal research-only, partial/method-dependent, and explicitly not exchange-grade completeness | Research evidence only; do not upgrade to Stock technical authority |
| Raw-series adjustment/lineage | No accepted adjustment factor, event hash, event version, or adjusted OHLCV field in HIST-002B | `CONTINUITY_UNKNOWN` where continuity depends on it |

The REC-A1 Dataset/Protocol Freeze remains accepted for its bounded
research-only outcome-integrity use case. Its 154 reviewed UNKNOWN identities
retain family-level method gaps; “not found” is not a complete empty-set proof.
This Phase 2A.1 does not change that governance decision or convert REC-A1
research artifacts into exchange-grade corporate-action authority.

## 3. Remaining Technical V0 algorithm decisions

The candidate set remains exactly the Phase 2A set: MA5, MA10, MA20, MA60,
price-vs/distance-to-MA20, 5D/20D raw observed-close return, Volume MA5/MA20,
volume ratio, RSI14, and MACD 12/26/9. No values are calculated in this
closure.

| Family | Candidate shape that may be retained | Decision still required before formal implementation/publication |
|---|---|---|
| SMA close MA5/10/20/60 | Arithmetic mean of the last `N` accepted daily closes; minimum `N`; inclusive `N`-observation window | Numeric scale/rounding or unrounded Decimal serialization; continuity evaluator |
| Price-vs/distance-to-MA20 | Exact comparison to SMA20; candidate distance `(close - SMA20) / SMA20`; zero denominator unavailable | Numeric scale/rounding; whether distance is ratio or percentage serialization; continuity evaluator |
| 5D/20D return | Candidate raw observed-close endpoint formula `close_t / close_(t-N) - 1`; minimum `N+1` closes | Exact endpoint/session semantics; explicit raw vs adjusted/total-return boundary; rounding; continuity evaluator |
| Volume MA5/MA20 | Arithmetic mean of accepted daily `volume_quantity` retaining unit/aggregation | Event-window volume comparability and numeric serialization; continuity evaluator |
| Volume ratio | Candidate `volume_t / VolumeMA20_t`; zero/missing denominator unavailable | Owner acceptance of denominator; event-window comparability; rounding; continuity evaluator |
| RSI14 | Candidate Wilder smoothing; first seed requires 14 changes / 15 closes | Seed, zero gain/loss behavior, restarted-series pre-roll, historical seed requirement, rounding, continuity evaluator |
| MACD 12/26/9 | Candidate EMA alpha `2/(N+1)`; provisional 26-close line and 34-close signal/histogram warm-up | EMA seed, pre-roll, signal/histogram warm-up, line-only publication policy, rounding, continuity evaluator |

Industry convention is not treated as canonical authority. Until each open
item is accepted by the Owner policy authority, the candidate ID is
`PROPOSED_CANDIDATE`, not a permission to calculate or publish.

### Shared deterministic policy that is already bounded

- Price input is canonical accepted daily `close`; volume input is canonical
  `volume_quantity` with unit, scale, and aggregation retained.
- Missing observations are not zero-filled, carried forward, or shortened.
- Session identity is market-local and uses the canonical calendar/version.
- Browser calculation and legacy V1 fields are not input authority.
- Values are formal only with exact indicator ID/version/parameters, required
  and actual windows, PIT/as-of, source lineage, continuity evidence, and a
  stable availability/publication state.
- `CONTINUITY_FAIL` and `CONTINUITY_UNKNOWN` are unavailable, never zero,
  neutral, or an assertion of no event.

## 4. Indicator-level Phase 2B readiness

The matrix is intentionally family-level. There is no global technical
READY/BLOCKED flag that erases differences between windows or algorithms.

| Family | Observation authority | Window/warm-up authority | Continuity authority | Algorithm/numeric authority | Disposition | Phase 2B routing |
|---|---|---|---|---|---|---|
| MA5/10/20/60 | Raw observations `PASS` | Candidate shape closed: `N` observations | Bounded evaluator required; general `PASS` unavailable | Formula shape bounded; rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner numeric policy + bounded evaluator |
| Price-vs/distance MA20 | Raw observations `PASS` | Candidate 20-observation window | Bounded evaluator required; general `PASS` unavailable | Distance serialization/rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner numeric policy + bounded evaluator |
| 5D/20D return | Raw observations `PASS` only | `N+1` endpoint candidate; endpoint policy open | Bounded evaluator required | Return semantics and rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner return policy + bounded evaluator |
| Volume MA5/20 | Raw volume observations `PASS` only | Candidate `N`-observation window | Volume comparability across events unresolved | Numeric serialization open | `OWNER_POLICY_DECISION_REQUIRED` | Owner volume policy + bounded evaluator |
| Volume ratio | Raw volume observations `PASS` only | Candidate 20-observation denominator window | Volume comparability unresolved | Denominator and rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner volume-ratio policy + bounded evaluator |
| RSI14 | Raw observations `PASS` only | 15-close seed candidate; recursive pre-roll open | Seed/recursive window needs evaluator | Seed/zero/pre-roll/rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner RSI policy + bounded evaluator |
| MACD 12/26/9 | Raw observations `PASS` only | 26/34 candidate; recursive pre-roll open | Seed/recursive window needs evaluator | EMA seed/signal/warm-up/rounding open | `OWNER_POLICY_DECISION_REQUIRED` | Owner MACD policy + bounded evaluator |

`OWNER_POLICY_DECISION_REQUIRED` is a family-level disposition, not a global
block. The bounded evaluator can be designed once and then applied per exact
window; a family can route to implementation only after its own algorithm and
numeric policy is accepted. No family is `READY_FOR_PHASE_2B_IMPLEMENTATION`
under the current committed authority.

## 5. PIT, product, and advanced-technical boundaries

Every future formal or unavailable technical record must bind at least:

```text
indicator_id
value OR availability_reason
session_date / as_of
required_observation_window
actual_observation_window
algorithm_id / version / parameter_set
price_authority / source_lineage
continuity_status / continuity_evidence
publication_state
```

No later bar, corporate-action correction, reference snapshot, or current
adjustment result may flow backward into an earlier walk-forward decision.
Raw OHLCV remains unchanged.

WS2 remains limited to:

```text
Observation -> Continuity/Eligibility -> Technical Evidence
```

`BUY`, `SELL`, entry/target/stop-loss, win rate, strategy acceptance,
Opportunity Grade, Recommendation score/gate, and other recommendation
semantics remain outside WS2 and belong to later WS3 research/recommendation
contracts.

Liquidity Sweep, Anchored VWAP, Volume Profile, FVG, Supply & Demand,
Fibonacci, Patterns, and Order Flow remain `DEFERRED`. Daily OHLCV is not true
order-flow authority and must not be labelled as such.

## 6. Bounded next closure and explicit non-goals

The minimum bounded authority closure for a future implementation task is:

1. an accepted source/method and versioned event-family evidence envelope by
   identity, market, effective date, and as-of boundary;
2. an authoritative complete empty-set result whenever `CONTINUITY_PASS` is
   claimed;
3. exact known-event mapping to `FAIL` and unresolved coverage to `UNKNOWN`;
4. legal continuity-resolution fields for split, reduction, merger, and
   conversion cases where `PASS` is claimed; and
5. an Owner-approved decision for each open algorithm/numeric item in the
   family matrix.

This task does not authorize runtime calculation, technical persistence,
migration, API publication, generated clients, frontend/UI, provider,
scheduler, PostgreSQL, Production, release, deployment, or `NEXT_TASK`
changes. It does not expand into a full adjusted-price engine, full-history
corporate-action migration, or global 507-symbol continuity reconstruction.

## Owning evidence

- [Phase 2A Technical V0 policy](STOCK_TECHNICAL_V0_POLICY_CONTRACT.md)
- [WS2 Phase 1 foundation](STOCK_TECHNICAL_PUBLICATION_FOUNDATION.md)
- [Phase 2A closure report](../reports/TASK-FE-BE-STOCK-006B-PHASE-2A-TECHNICAL-V0-POLICY-CLOSURE.md)
- [Phase 2A.1 closure report](../reports/TASK-FE-BE-STOCK-006B-PHASE-2A-CONTINUITY-AUTHORITY-GAP-CLOSURE.md)
- [Phase 2A.1 machine-readable readiness audit](../../reports/TASK-FE-BE-STOCK-006B-PHASE-2A-CONTINUITY-AUTHORITY-GAP-CLOSURE/indicator-readiness-audit.json)
- [HIST-002B canonical historical authority closure](../reports/TASK-DATA-HIST-002B_CANONICAL_RECONCILIATION_CLOSURE.md)
- [REC-A1 source and semantics closure](../reports/TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE.md)
- [REC-A1 dataset/protocol freeze closure](../reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE_CANONICAL_CLOSURE.md)
