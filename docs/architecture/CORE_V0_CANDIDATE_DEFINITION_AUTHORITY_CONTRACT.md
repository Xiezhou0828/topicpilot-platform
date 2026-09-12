# Core V0 Candidate Definition Authority Contract

**Status:** `AUTHORITY_CLOSURE / OWNER_DECISION_FORMALIZED`
**Task:** `TASK-REC-A1-CORE-V0-CANDIDATE-DEFINITION-AUTHORITY-CLOSURE-20260816`
**Scope:** WS3 research-only candidate-definition, eligibility, evidence, and
owner-policy closure for Core V0.

This contract is subordinate to the frozen `core-v0-walk-forward.v1` protocol
and does not authorize a walk-forward, performance conclusion, Strategy Review,
recommendation publication, runtime activation, or Production change.

## 1. Authority chain and reconciliation

The cold-start authority order for this task is:

1. the committed canonical repository at the audited source HEAD;
2. the canonical WS3 Phase 1 and Phase 2 contracts, reports, and machine-readable
   artifacts;
3. committed technical, PIT, OHLCV, Opportunity shadow, and test evidence;
4. committed Owner-approved policy evidence; and
5. the explicit `NEW OWNER DECISION` supplied in this task.

The new Owner decision in this task is authoritative for the Core V0 research
L1 policy, but it is not evidence that the repository previously had a MA60
hard-gate authority. The committed Opportunity shadow qualification policy
previously described 60MA as a structure/ranking/explainability factor and left
any 60MA gate open. This task records the reconciliation explicitly:

- `Close(T) >= MA60(T)` is formalized as the current Core V0 research-universe
  eligibility policy only.
- It does not rewrite the WS2 technical publication contract.
- It does not rewrite the Opportunity shadow/production policy.
- It does not authorize technical publication, candidate materialization, or
  any downstream recommendation meaning.

The predecessor Phase 2 REC-A1 provenance disposition is carried forward without
reopening the Freeze or the 154 reviewed `UNKNOWN` records:
`BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP`.

## 2. Scope lock

This task is limited to:

```text
WS3 Research
  -> Core V0
  -> Candidate Definition Authority
```

It does not implement WS1 Topic Derived Intelligence, WS2 Technical V0,
corporate-action continuity, technical API/UI publication, WS4 release/deploy,
Production, scheduler, recommendation publication, Opportunity productionization,
Strategy Review, performance optimization, tuning, or parameter optimization.
WS1/WS2 findings are recorded as bounded reverse dependencies only.

## 3. Frozen protocol boundary

`core-v0-walk-forward.v1` is unchanged:

| Field | Frozen value |
|---|---|
| Development | `2026-02-02..2026-06-30` |
| Validation | `2026-07-01..2026-07-31` |
| Holdout | `2026-08-01..2026-08-13` |
| Warm-up | At least 60 prior canonical trading sessions |
| Outcomes | `T+1`, `T+3`, `T+5`, `T+10`, evaluation only |
| Tuning/optimization | Forbidden |

If a candidate is structurally incompatible with V1, the result is a bounded
blocker. This task does not create Protocol V2 or alter a candidate definition
to make V1 executable.

## 4. L1-L5 separation

### L1 ? Common eligibility

L1 answers whether a symbol/date may enter the Core V0 research universe. It
contains session/tradability validity, identity validity, sufficient history,
continuity/lineage status, required data availability, and the current Owner
MA60 policy:

```text
L1_MA60_ELIGIBLE(T) = Close(T) >= MA60(T)
```

The expression is evaluable only when both values are formal, PIT-safe, and
bound to `T`. The canonical MA60 algorithm candidate is
`stock.sma.close.v1`, `period=60`: arithmetic mean of the last 60 accepted
daily close observations, with the inclusive observation window ending at `T`.

The exact L1 evidence gate is:

```text
L1_PASS(T) iff
  session/identity/history prerequisites pass
  AND canonical Close(T) is available
  AND stock.sma.close.v1(MA60, T) is available
  AND the MA60 window has accepted as-of-safe lineage
  AND continuity(T, MA60 window) = CONTINUITY_PASS
  AND Close(T) >= MA60(T)
```

Missing history, continuity `FAIL`/`UNKNOWN`, missing lineage, or unavailable
MA60 is not converted into a pass, zero, or a fabricated below-gate value. It
is a bounded `UNAVAILABLE`/dependency state. The current WS2 technical policy
still says general continuity PASS and formal publication are not established;
therefore the research authority is `READY_AFTER_WS2_MA60_EVIDENCE`, not a
claim that every symbol/date is currently eligible.

### L2 ? Candidate formation

L2 determines whether A1, A2, A3, or intra-topic Catch-up forms at `T`. It may
use only information effective/observable at or before `T`; once formed, the
candidate is frozen. A technical or topic field is not candidate identity unless
the frozen definition explicitly assigns it that role.

### L3 ? Technical/topic evidence

MA slope, RSI, MACD, volume ratio, return, Topic context, Topic strength, and
role remain evidence unless a future frozen candidate definition promotes one.
WS2 owns `Observation -> Continuity/Eligibility -> Technical Evidence`, not
BUY/SELL, entry, recommendation, strategy acceptance, or outcome meaning.

### L4 ? Entry/risk

Distance from a reference, support distance, stop-loss, long-black or limit-down
exclusion, structural failure, and other risk rules remain separate from L2
unless a future frozen definition explicitly requires them for candidate
formation. `Entry Eligible = NO` must not retroactively delete a valid L2
candidate.

### L5 ? Evaluation outcome

`T+1/T+3/T+5/T+10` are evaluation-only outcomes. They never flow backward into
L1-L4. A frozen REC-A1 corporate-action post-hoc integrity exclusion may
invalidate an outcome; it may not rewrite candidate eligibility at `T`.

## 5. Breakout/reference authority audit

The following committed evidence was found, but none is a frozen Core V0
reference authority:

| Reference source | Current status | Core V0 authority result |
|---|---|---|
| `detectors/range_detector.py` repeated support/resistance primitive | Committed generic detector; policy parameters are implementation evidence | Not approved as A1/A2 reference identity; owner decision required |
| Opportunity technical evidence breakout/retest/support builders | Committed deterministic shadow evidence; report labels definitions and support distance `OPEN / NOT PM-FROZEN` | Evidence only; not Core V0 formation authority |
| Business rules and range-detector documents | Conceptual/research semantics; no frozen Core V0 versioned reference contract | Not sufficient for formation authority |
| Legacy V1 formulas, fixtures, and historical reports | Historical or synthetic traceability evidence | Not eligible for Core V0 authority |

No committed authority selects prior-high, rolling-high, swing-high, resistance,
consolidation range, or another reference type for A1/A2. No committed authority
settles PIT legality, near-reference semantics, breakout margin, gap handling,
one-session versus multi-session confirmation, or volume confirmation role.
Selecting the easiest implementation would be an unauthorized policy choice.

## 6. Candidate authority boundary

| Candidate | Canonical evidence | Owner intent only | Unresolved authority | Disposition |
|---|---|---|---|---|
| A1 Pre-Breakout | Research label, common PIT/OHLCV envelope, technical evidence primitives | `NOT_YET_BREAKOUT + STRUCTURE_IMPROVING + NEAR_VALID_REFERENCE` | Reference identity, proximity, structure-improving semantics, exact formation fields and thresholds | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` |
| A2 Confirmed Breakout | Research label, common PIT/OHLCV envelope, shadow breakout evidence | `VALID_PREEXISTING_REFERENCE + BREAKOUT_AT_T + CONFIRMATION_REQUIREMENT` | Reference identity, high/close semantics, confirmation, margin, gap, session count, volume role | `BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` |
| A3 Pullback/Retest | Research label, shadow support/retest evidence, future `PULLBACK_ACCEPTANCE` slot | Prior strength/breakout, valid support retest, no structural failure | Support authority, acceptance sessions, failure semantics, risk-versus-formation role | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` |
| Catch-up | Provisional `CATCH_UP` shadow input shape and intra-topic relative-gap evidence | Strong-topic relative laggard becoming stronger | Frozen strong-topic, laggard, improving definitions and historical PIT Topic context | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` |

Cross-topic Rotation is a separate deferred research concept and is not part of
the current Catch-up candidate.

## 7. Owner decision and freeze boundary

The machine-readable Owner Decision Table and reverse dependency matrix are
delivered with the closure report. Unresolved decisions default to
`BLOCK`/`DEFER`; this task does not invent thresholds. A candidate that becomes
deterministic after explicit Owner decisions may be reported as
`READY_FOR_OWNER_APPROVAL_TO_FREEZE`, not silently promoted to frozen authority.

`FROZEN_RESEARCH_CANDIDATE` is distinct from `ACCEPTED_STRATEGY`,
`PRODUCTION_STRATEGY`, and `RECOMMENDATION`.

## 8. Deferred research

The following are recorded only:

- MA60 ABOVE/BELOW/CROSSING feature/B-path and any A/B performance comparison:
  `DEFERRED_FUTURE_RESEARCH`.
- Cross-topic Rotation: `DEFERRED / SEPARATE_RESEARCH_CONCEPT`.
- Advanced Technical such as AVWAP, Volume Profile, Liquidity Sweep, FVG,
  Supply/Demand, Fibonacci, and Order Flow: deferred; OHLCV proxies are not
  true Order Flow authority.

## 9. Implementation and lifecycle boundary

This is an authority/policy/documentation closure. No candidate runtime,
candidate panel generation, materialization, database table, migration, API,
frontend, forward-outcome generation, walk-forward, performance metric,
Strategy Review, recommendation, release, deploy, scheduler, or Production
mutation is authorized.

The closure report records `CANONICAL_STATUS`,
`CANONICAL_RECONCILIATION_DISPOSITION`, `RELEASE_STATUS`,
`PRODUCTION_VERIFICATION`, `NEXT_TASK` state, owner-state preservation, and
source-to-canonical provenance.
