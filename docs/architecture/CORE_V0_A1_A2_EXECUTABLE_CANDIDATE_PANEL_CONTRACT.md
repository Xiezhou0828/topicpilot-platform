# Core V0 A1/A2 Executable Candidate Panel Contract

**Status:** `IMPLEMENTED_RESEARCH_ONLY / EXECUTION_READINESS_BOUNDED`
**Task:** `TASK-REC-A1-CORE-V0-A1-A2-EXECUTABLE-CANDIDATE-PANEL-AND-READINESS-CLOSURE-20260816`
**Predecessor:** `TASK-REC-A1-CORE-V0-A1-A2-BREAKOUT-FORMATION-POLICY-CLOSURE-20260816`
**Scope:** WS3 Core V0 A1 Pre-Breakout and A2 Confirmed Breakout candidate/date
panel, forward-outcome availability, and candidate-level readiness.

This is an incremental implementation contract. The frozen A1/A2 formation
authority remains
[Core V0 A1/A2 Breakout Formation Policy V0](CORE_V0_A1_A2_BREAKOUT_FORMATION_POLICY_V0.md).
This contract adds a deterministic, persistence-free research builder and does
not rewrite that policy, the frozen V1 protocol, WS2, REC-A1, A3, or Catch-up.

## 1. Scope and authority boundary

The implementation consumes explicit evidence and returns a panel record. It
does not fetch providers, infer missing sessions, write a database, expose an
API/UI, publish Opportunity/Recommendation data, run a scheduler, or activate
Production behavior. It never calculates forward returns, MFE, MAE, win rate,
Sharpe, hit rate, alpha, or any performance metric.

The authority order is:

1. exact canonical committed authority and frozen `core-v0-walk-forward.v1`;
2. the frozen A1/A2 formation policy;
3. the formal WS2 technical contract when a value is consumed;
4. the frozen REC-A1 research-only policy for evaluation integrity; and
5. explicit candidate/date evidence supplied to the builder.

`NEXT_TASK.md` is not a task authority. Its current owner-checkout state is
recorded in the closure artifact as an external, non-blocking provenance
disposition.

## 2. Candidate and protocol identity

| Candidate | ID | Version |
|---|---|---|
| A1 Pre-Breakout | `CORE_V0_A1_PRE_BREAKOUT` | `core-v0-a1-pre-breakout.v1` |
| A2 Confirmed Breakout | `CORE_V0_A2_CONFIRMED_BREAKOUT` | `core-v0-a2-confirmed-breakout.v1` |

The frozen protocol remains `core-v0-walk-forward.v1`:

- Development: `2026-02-02..2026-06-30`
- Validation: `2026-07-01..2026-07-31`
- Holdout: `2026-08-01..2026-08-13`
- At least 60 prior canonical accepted trading sessions per signal
- Evaluation outcomes only at T+1/T+3/T+5/T+10
- Tuning, parameter search, optimization, and performance execution forbidden

All formation inputs are effective/observable no later than `T`; the panel
sets `frozenAtT=true` only for a formed candidate. No outcome field is accepted
as a formation input.

## 3. Executable panel identity

Each candidate/date panel binds:

```text
candidate_record_id                 deterministic SHA-256 identity
candidate_id / candidate_version
protocol / panel contract version
instrument_id / symbol / name / market / lifecycle state
evaluation_session / evaluation_date / as_of=T / calendar version
L1 state / WS2 MA60 evidence identity, value, continuity, and lineage
reference policy / value / prior-20 member dates and observation IDs
reference birth session / age / maturity / lineage
Close(T) / Open(T) evidence
A1 distance OR A2 Close comparison
PIT Topic membership/context and snapshot lineage
candidate input lineage and calculation identity
formation state / reason
frozenAtT
```

The builder rejects any bar whose session or `as_of` is after `T`, rejects
duplicate accepted sessions, and rejects outcome sessions at or before `T`.
Missing evidence is represented by an explicit bounded state; it is not
converted to zero, false evidence, or a global block.

## 4. Formation implementation

The implementation applies the existing frozen policy exactly.

### A1

```text
L1_PASS(T)
AND mature PRIOR_20_ACCEPTED_SESSION_HIGH reference
AND Close(T) < Reference(T)
AND 0 < (Reference(T) - Close(T)) / Reference(T) <= 0.03
```

An immature reference returns `REFERENCE_MATURITY_LT_5`; it never falls back
to an older lower reference. Structure-improving, RSI, MACD, volume, MA slope,
return acceleration, and pattern score are not accepted as hidden gates.

### A2

```text
L1_PASS(T)
AND mature PRIOR_20_ACCEPTED_SESSION_HIGH reference
AND Close(T) > Reference(T)
```

Confirmation is one session and Close-only. Intraday High alone cannot form A2;
gap-up is allowed and gap magnitude is evidence only. No extra margin is added.

### Reference and temporal semantics

`Reference(T)` is the maximum canonical High from 20 accepted sessions strictly
before `T`. A strictly higher High starts a new reference; equal High does not
reset birth. Reference age is the count of accepted sessions `s` where
`birth < s <= T`; maturity requires 5. The reference lineage/birth is an
explicit panel input, and unknown birth/age is `UNAVAILABLE_REFERENCE_MATURITY`.

The hard 60-session warm-up is checked independently from the 20-session
reference window. A symbol having some OHLCV does not certify a candidate/date.

## 5. WS2 MA60 dependency

The panel consumes, but does not recalculate, the formal WS2 identity
`stock.sma.close.v1`, `SMA_CLOSE_V1`, period 60, raw observed close, as-of `T`.
Formal consumption requires:

```text
value present
60 accepted observations and complete observation window
last observation = T
CONTINUITY_PASS_BOUNDED
complete source lineage
publication_state = FORMAL_AVAILABLE
```

The current canonical WS2 contract is policy-ready but still reports
`PHASE_2B_IMPLEMENTATION_PENDING_OWNER_AUTHORIZATION`; no formal MA60
publication evidence is claimed by this task. Such a candidate/date returns
`WAITING_FOR_FORMAL_WS2_MA60_EVIDENCE`, and readiness returns
`READY_AFTER_WS2_MA60_PUBLICATION`.

`CONTINUITY_FAIL`, `CONTINUITY_UNKNOWN`, missing lineage, missing value, or
missing formal publication never becomes an L1 pass.

## 6. PIT Topic and REC-A1 boundaries

Topic context is candidate-specific. The panel binds effective-dated membership
or context, role, validity interval, snapshot/as-of, publication mode, and
lineage when the candidate universe requires it. Missing context returns
`UNAVAILABLE_PIT_TOPIC_CONTEXT`; it does not require a global historical Topic
System State replay.

REC-A1 is not a formation dependency. Its current disposition remains
`BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP` for evaluation-integrity
consumption. A frozen corporate-action post-hoc exclusion can mark an outcome
invalid/excluded, but cannot rewrite candidate eligibility at `T`.

## 7. Forward outcome panel

The outcome builder is separate from the candidate builder. It accepts only
subsequent canonical outcome records for T+1/T+3/T+5/T+10, with session date,
close/value availability, lineage, and integrity state. It returns one of:

```text
AVAILABLE
UNAVAILABLE_INSUFFICIENT_FORWARD_WINDOW
UNAVAILABLE_LINEAGE
EXCLUDED_BY_FROZEN_REC_A1_INTEGRITY_POLICY
```

The panel carries `outcomesFlowBackward=false`. Outcome availability never
changes the frozen candidate record.

## 8. Candidate-level readiness

Readiness is evaluated independently for A1 and A2:

```text
BLOCKED_BY_CANDIDATE_DATE_PANEL
READY_AFTER_WS2_MA60_PUBLICATION
READY_AFTER_REC_A1_PROVENANCE_RECONCILIATION
READY_AFTER_FORWARD_OUTCOME_PANEL
READY_FOR_CORE_V0_WALK_FORWARD_EXECUTION
```

The last state is emitted only when that candidate/date has a formed panel,
formal WS2 MA60 evidence, REC-A1 evaluation-integrity consumption, and all four
forward outcome records. This task has no canonical real candidate/date rows,
so it does not emit a walk-forward execution-ready claim.

## 9. Artifacts and lifecycle

The implementation lives under `topicpilot_api.research` and is covered by
research-only focused tests. Coverage output contains availability/formation
counts only. Synthetic fixtures are explicitly labelled and cannot enter a
production snapshot or performance ledger.

Application behavior, schema, migration, persistence, API/UI, provider,
scheduler, deploy, Production, Strategy Review, Recommendation, and
`NEXT_TASK` are unchanged. A3 and Catch-up are unchanged. G1/G2/G3/Canary and
the Core V0 walk-forward are not run or rerun by this task.
