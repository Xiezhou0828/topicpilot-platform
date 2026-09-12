# Core V0 A1/A2 Breakout Formation Policy V0

**Status:** `FROZEN_RESEARCH_DEFINITION / EXECUTION_DEPENDENCIES_REMAIN`
**Task:** `TASK-REC-A1-CORE-V0-A1-A2-BREAKOUT-FORMATION-POLICY-CLOSURE-20260816`
**Scope:** WS3 research-only A1 Pre-Breakout and A2 Confirmed Breakout
candidate formation authority.

This contract is the incremental authority closure for the A1/A2 breakout
reference and formation gap identified by the predecessor
[Core V0 Candidate Definition Authority Contract](CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md).
It supersedes only the predecessor A1/A2
`BLOCKED_BY_BREAKOUT_REFERENCE_AUTHORITY` and related A1/A2 confirmation
decisions. It does not alter A3, Catch-up, REC-A1 Freeze, WS2 implementation,
the frozen walk-forward protocol, or any production policy.

## 1. Authority and non-goals

The authority chain is:

1. the audited canonical repository and its exact committed source SHA;
2. the frozen `core-v0-walk-forward.v1` protocol and canonical research-only
   data contracts;
3. the predecessor candidate-definition closure;
4. the explicit Owner decisions D1-D10 recorded by this task; and
5. the machine-readable policy and scenario ledger committed with this
   contract.

This is a definition, dependency, and documentation closure. It does not
authorize candidate runtime implementation, DB or schema work, migration,
API/UI/provider/scheduler/deploy work, materialization, walk-forward,
performance metrics, tuning, Strategy Review, recommendation publication, or
Production activation.

The policy is a Core V0 research parameterization, not an assertion of
optimality and not a production or recommendation strategy.

## 2. Frozen protocol boundary

`core-v0-walk-forward.v1` remains unchanged:

| Field | Frozen value |
|---|---|
| Development | `2026-02-02..2026-06-30` |
| Validation | `2026-07-01..2026-07-31` |
| Holdout | `2026-08-01..2026-08-13` |
| Warm-up | At least 60 prior canonical trading sessions |
| Outcomes | `T+1`, `T+3`, `T+5`, `T+10`, evaluation only |
| Tuning/optimization | Forbidden |

All formation inputs must be effective or observable at or before `T`. The
candidate is frozen at `T`. Forward outcomes never flow backward into
formation, eligibility, reference maturity, or candidate identity
(`outcomesFlowBackward=false`). A V2 protocol is not created by this task;
any protocol incompatibility is an Owner decision surface.

## 3. Candidate IDs and layer separation

The frozen research definition IDs are:

| Candidate | Definition ID | Version | Layer |
|---|---|---|---|
| A1 Pre-Breakout | `CORE_V0_A1_PRE_BREAKOUT` | `core-v0-a1-pre-breakout.v1` | L2 candidate formation |
| A2 Confirmed Breakout | `CORE_V0_A2_CONFIRMED_BREAKOUT` | `core-v0-a2-confirmed-breakout.v1` | L2 candidate formation |

L1 common eligibility remains the predecessor Owner policy and its bounded WS2
dependency: `Close(T) >= MA60(T)` using the formal WS2 candidate
`stock.sma.close.v1`, without duplicating or changing WS2 computation. L3
volume, RSI, MACD, MA slope, return acceleration, pattern score, and gap
magnitude are evidence fields only unless a future Owner-approved contract
promotes one. They are not hidden formation gates in V0.

## 4. Breakout reference authority

### 4.1 Reference value

For evaluation session `T`, the only V0 breakout reference is:

```text
Reference(T) = max(High(s) for the prior 20 accepted daily trading sessions s
                   strictly before T)
```

The policy identifier is `PRIOR_20_ACCEPTED_SESSION_HIGH`, with
`referenceWindowAcceptedSessions=20` and `evaluationSessionIncluded=false`.
The window is session-based, not calendar-day based; it contains no synthetic
backfill, swing-high inference, subjective resistance, rolling close high,
volume-weighted resistance, Fibonacci, or support/resistance-engine output.

The reference is available only when all 20 accepted sessions, their canonical
High values, accepted-session identity, and source lineage are present. A
missing or non-canonical observation is unavailable; it is never silently
filled or treated as zero.

### 4.2 Reference birth and maturity

Each reference lineage records `referenceBirthSession`. A strictly higher
accepted daily High starts a new reference level. A later equal High does not
reset the birth session. For the current reference level, the birth is the
accepted session that first established that level in the canonical High
lineage; if the lineage cannot prove the birth or age, maturity is unavailable.

For an evaluation session `T`:

```text
referenceAgeSessions(T) = count of accepted sessions s where
                          referenceBirthSession < s <= T
referenceMature(T) = referenceAgeSessions(T) >= 5
```

This is an accepted-session count, not a calendar-day count. The evaluation
session may be counted for maturity because its close is known when the
candidate is evaluated, while its High is still excluded from
`Reference(T)`. A reference formed on the immediately preceding session has
age 1 on `T` and is not mature. A current maximum that is immature or whose
lineage is unknown makes the reference invalid for A1/A2; an older lower
reference is not substituted. A newer higher High starts a new immature
reference and cannot be used to reclassify the immediate post-breakout
pullback as A1.

The exact age convention is intentionally minimal and deterministic. Any
alternative birth, equality, expiry, or maturity semantics requires a new
Owner decision and a new policy version; this task does not add one.

## 5. A1 Pre-Breakout formation

For an evaluation session `T`, A1 forms only when all of the following are
true:

```text
L1_PASS(T)
AND Reference(T) exists and referenceMature(T)
AND Close(T) < Reference(T)
AND 0 < (Reference(T) - Close(T)) / Reference(T) <= 0.03
```

The proximity parameter is `A1_MAX_REFERENCE_DISTANCE_PCT=0.03` (3%).
Equality with the reference is not A1 because the lower bound is strictly
positive. `structureImproving` has no V0 hard gate. RSI, MACD, volume, MA
slope, return acceleration, and pattern score can be retained as L3 evidence,
but cannot create, block, or reclassify A1.

If a recent breakout creates a newer reference that has not reached five
accepted sessions of maturity, a close below that newer reference is not A1;
the policy does not fall back to an older reference merely because the close
is within 3%. This prevents immediate post-breakout pullbacks from being
reclassified as A1 through a rolling-reference update.

## 6. A2 Confirmed Breakout formation

For an evaluation session `T`, A2 forms only when all of the following are
true:

```text
L1_PASS(T)
AND Reference(T) exists and referenceMature(T)
AND Close(T) > Reference(T)
```

The confirmation policy is `single-session-close`; the confirmation session
count is exactly `1`. The comparison uses the daily Close, not intraday High.
No extra breakout margin is required (`A2_EXTRA_BREAKOUT_MARGIN_PCT=0.0`),
so the strict `Close(T) > Reference(T)` comparison is sufficient. Equality is
not A2. A gap-up is not excluded: `Open(T) > Reference(T)` together with
`Close(T) > Reference(T)` may form A2 if the other eligibility conditions
pass. Gap magnitude is evidence only; there is no gap threshold or exclusion.

`High(T) > Reference(T)` while `Close(T) <= Reference(T)` is not A2. No
multi-day close confirmation, retest, volume, RSI, or MACD hard gate is
introduced.

## 7. Minimum panel and reverse dependencies

The candidate-specific minimum panel is not a global Historical Topic/System
State prerequisite. For each candidate/date it must prove only the fields
assigned by this definition:

| Panel component | A1/A2 minimum evidence |
|---|---|
| Evaluation identity | symbol, accepted evaluation session/date, as-of `T`, session/calendar lineage |
| L1 Stock evidence | canonical close through `T`, formal WS2 `stock.sma.close.v1` MA60 evidence and continuity/lineage, at least 60 prior accepted canonical sessions |
| Reference OHLCV | canonical High for the prior 20 accepted sessions, canonical Close(T), reference window membership, birth session, age, maturity, and source lineage; Open(T) is retained for gap evidence; Low/Volume are not hard gates |
| PIT Topic context | only PIT membership/context required by the candidate universe at `T`; no global historical Topic score/grade/lifecycle requirement |
| Candidate inputs | reference policy/version, reference value, `T` exclusion, maturity result, Close comparison, A1 distance or A2 breakout result, and all input lineage |
| Evaluation outcomes | subsequent canonical `T+1`, `T+3`, `T+5`, `T+10` session/outcome records, kept separate from candidate inputs and used only for evaluation |

The reverse dependency is therefore bounded: WS1 need not build a complete
Historical Topic/System State before A1/A2 definition closure or every A1/A2
execution; WS2 remains responsible for its formal MA60 observation,
continuity, and publication semantics; REC-A1 remains an evaluation-integrity
dependency under its frozen policy; and the panel must be assembled per
candidate/date. No dependency is converted into a global four-candidate gate.

## 8. Candidate-level disposition

Definition readiness and execution readiness are separate. A1 and A2 are no
longer blocked by breakout-reference or confirmation semantics, but a clean
Core V0 execution still depends on candidate-specific panel evidence, formal
WS2 MA60/continuity evidence, and the bounded REC-A1 outcome-provenance path.
A3 and Catch-up are preserved exactly as bounded by the predecessor closure.

| Candidate | Definition authority | Execution disposition |
|---|---|---|
| A1 | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `READY_AFTER_WS2_MA60_EVIDENCE_CANDIDATE_PANEL_AND_OUTCOME_PROVENANCE` |
| A2 | `FROZEN_CORE_V0_DEFINITION_AUTHORITY` | `READY_AFTER_WS2_MA60_EVIDENCE_CANDIDATE_PANEL_AND_OUTCOME_PROVENANCE` |
| A3 | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` (preserved) | `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY` |
| Catch-up | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` (preserved) | `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY` |

These are independent dispositions. A3/Catch-up do not block A1/A2, and A1/A2
closure does not imply A3/Catch-up readiness.

## 9. Lifecycle boundary

This contract changes policy/documentation authority only. Application behavior
has not changed. DB/G1-G3/Canary/Production are not run or rerun by scope;
existing evidence is preserved and is not relabeled as a fresh PASS. There is
no push, merge, deploy, Production mutation, recommendation publication, or
`NEXT_TASK` change.
