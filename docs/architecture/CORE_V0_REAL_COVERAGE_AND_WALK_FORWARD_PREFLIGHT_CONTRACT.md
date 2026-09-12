# Core V0 Real Coverage and Walk-forward Preflight Contract

**Status:** `READ_ONLY_PREFLIGHT / BLOCKED_BY_REAL_CANDIDATE_PANEL_AUTHORITY_GAP`
**Task:** `TASK-REC-A1-CORE-V0-A1-A2-REAL-COVERAGE-AND-WALK-FORWARD-PREFLIGHT-CLOSURE-20260816`
**Predecessor:** `TASK-REC-A1-CORE-V0-A1-A2-EXECUTABLE-CANDIDATE-PANEL-AND-READINESS-CLOSURE-20260816`
**Scope:** WS3 Core V0 real candidate-date coverage, WS2 MA60 join preflight, candidate freeze preflight, and forward-outcome mapping.

This is a read-only preflight contract. It does not execute Core V0
walk-forward, calculate returns or performance metrics, perform Strategy
Review, publish Recommendation/Opportunity data, or activate Production.

## 1. Authority and clean-source boundary

The authority order is:

1. exact committed canonical HEAD;
2. the frozen `core-v0-walk-forward.v1` protocol;
3. the frozen A1/A2 formation policy and executable candidate-panel contract;
4. the canonical WS2 Technical V0 policy/runtime publication contract;
5. the frozen research-only REC-A1 dataset/freeze evidence; and
6. explicit read-only real evidence available from the approved canonical
   observation chain.

The owner-dirty canonical checkout is not a data source. In particular, the
owner artifact hash `1091f972...` is not used as the REC-A1 dataset identity;
the clean committed dataset hash is `78f684d5...`. Synthetic fixtures,
browser-derived values, provider calls, and ad-hoc files are excluded.

## 2. Frozen protocol and candidate rules

The protocol remains unchanged:

- Development: `2026-02-02..2026-06-30`
- Validation: `2026-07-01..2026-07-31`
- Holdout: `2026-08-01..2026-08-13`
- At least 60 prior canonical accepted trading sessions per candidate/date
- Evaluation-only `T+1`, `T+3`, `T+5`, and `T+10`
- Tuning, optimization, and parameter sweeps prohibited

A1 and A2 remain the frozen definitions from
`CORE_V0_A1_A2_BREAKOUT_FORMATION_POLICY_V0.md`:

```text
Reference(T) = max prior 20 accepted-session High values strictly before T
maturity >= 5 accepted sessions
A1: Close(T) < Reference(T) and 0 < distance <= 3%
A2: Close(T) > Reference(T), single-session Close confirmation
```

RSI, MACD, volume, MA slope, return acceleration, pattern score, gap size,
and any newly invented threshold are not formation hard gates.

## 3. Read-only real coverage audit

The audit may inspect only:

- canonical identity/session/calendar evidence;
- canonical OHLCV through `T` with source lineage and accepted-session order;
- PIT Topic membership/context when required by the candidate universe;
- the prior-20 reference and five-session maturity evidence;
- pre-MA60 formation state;
- formal WS2 MA60 evidence joined by instrument identity, evaluation session,
  as-of, indicator identity, and algorithm/version; and
- subsequent canonical sessions for outcome mapping.

If no approved database endpoint or committed row-level panel/export is
available, the audit must return `NOT_AVAILABLE` / an exact bounded blocker.
`0` is never interpreted as zero eligible dates unless rows were actually
loaded and counted.

## 4. WS2 MA60 join contract

WS3 consumes, and never recalculates, the WS2 formal evidence:

```text
indicator_id       = stock.sma.close.v1
algorithm_id       = SMA_CLOSE_V1
period             = 60
price_basis        = RAW_OBSERVED
window             = 60 accepted closes ending at T
as_of              = T
continuity         = CONTINUITY_PASS_BOUNDED
publication_state  = FORMAL
```

The join requires instrument identity, evaluation session/as-of, indicator
identity/version, required/actual observation window, continuity state, and
lineage. Symbol-only, latest-value, cross-session reuse, fallback rolling
means, and duplicate MA60 calculations are forbidden. The current canonical
WS2 implementation is consumable at a bounded contract boundary, but a real
formal value is unavailable when the historical reader has no continuity
evidence envelope or no reachable canonical database.

## 5. REC-A1 boundary

REC-A1 remains research-only and owner-accepted with reviewed residual
uncertainty. This preflight reconciles identity and provenance binding only;
it does not reopen the Freeze, re-research the 154 reviewed UNKNOWN identities,
or assert exchange-grade completeness. A missing review-ledger archive remains
the exact bounded blocker:

```text
BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP
```

REC-A1 post-hoc corporate-action evidence may invalidate an evaluation outcome,
but it cannot alter candidate eligibility at `T`.

## 6. Preflight lifecycle and routing

The preflight produces candidate-level evidence in this order:

```text
authority and provenance
  -> real candidate/date availability
  -> 60-session temporal eligibility
  -> prior-20 reference and maturity
  -> pre-MA60 A1/A2 formation
  -> WS2 formal MA60 join
  -> candidate freeze identity
  -> T+1/T+3/T+5/T+10 outcome mapping
```

The current result is Route D:

```text
BLOCKED_BY_REAL_CANDIDATE_PANEL_AUTHORITY_GAP
```

This is independent of A3 and Catch-up, which remain
`BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` and
`BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY`. No aggregate global READY/NO
decision is emitted.

## 7. Forbidden side effects

This task does not modify schema, migration, database data, API/UI/provider,
scheduler, deployment, Production, WS1, WS2, WS4, or `NEXT_TASK`. It does not
run the walk-forward harness after preflight, generate performance metrics,
accept/reject a strategy, tune parameters, or publish Recommendation or
Opportunity output.
