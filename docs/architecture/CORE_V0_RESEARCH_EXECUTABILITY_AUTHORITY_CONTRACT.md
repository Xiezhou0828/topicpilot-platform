# Core V0 Research Executability / Authority Closure Contract

**Task ID:** `TASK-REC-A1-CORE-V0-PHASE-2-EXECUTABILITY-AUTHORITY-CLOSURE-20260816`
**Workstream:** `WS3 / Recommendation research`
**Contract status:** `CLOSED_FOR_AUDIT / EXECUTION_NOT_AUTHORIZED`
**Protocol:** `core-v0-walk-forward.v1` (unchanged)
**Authority baseline:** canonical HEAD `7e28284161d172cc5aa4c967e0306050c748cebf`

## Purpose and boundary

This contract closes the Phase 2 executability and authority audit for Core V0.
It defines what must be present before a candidate can be formed and evaluated
from a clean canonical research checkout. It does not define or approve a
strategy, run walk-forward, calculate performance, publish a Recommendation, or
activate Opportunity production behavior.

The contract is deliberately candidate-specific. Missing evidence for one
candidate does not become a global readiness decision for the other candidates.
Conversely, a symbol-level or workstream-level PASS is never evidence that an
individual candidate/date is eligible.

Out of scope: migrations, Production persistence, API/UI/provider/scheduler or
deployment work, parameter tuning, threshold invention, strategy acceptance or
rejection, and any change to `NEXT_TASK`.

## Authority chain

The Phase 2 audit consumes these committed authorities and implementation
surfaces from the canonical baseline:

- Phase 1 report and machine-readable preflight:
  `docs/reports/TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-2026-08-16.md` and
  `reports/TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-20260816/core-v0-protocol-and-preflight.json`.
- REC-A1 research-only Dataset/Protocol Freeze closure and its frozen metadata:
  `docs/reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE_CANONICAL_CLOSURE.md` and
  `reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE-RISK-ACCEPTANCE-REASSESSMENT/freeze-risk-acceptance-metadata.json`.
- Canonical raw research dataset:
  `reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json`.
- Canonical OHLCV authority and PIT membership foundation:
  `docs/reports/TASK-DATA-HIST-002B_CANONICAL_RECONCILIATION_CLOSURE.md` and
  `docs/reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md`.
- Technical dependency contract:
  `docs/architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md` and
  `docs/reports/TASK-FE-BE-STOCK-006B-PHASE-2A-TECHNICAL-V0-POLICY-CLOSURE.md`.
- Opportunity shadow contract, implementation, and read boundary:
  `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md`,
  `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py`,
  `services/api/src/topicpilot_api/topic_engine/opportunity_evidence.py`,
  `services/api/src/topicpilot_api/topic_engine/opportunity_contract.py`, and
  `services/api/src/topicpilot_api/topic_engine/opportunity_shadow.py`.
- Cold-start state reconciliation:
  `docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001.md`.

Reports remain evidence owners for the facts they record. This contract adds
the Phase 2 formation/evaluation boundary and does not rewrite those reports.

## Frozen V1 protocol

The following values are carried forward without modification:

| Item | Frozen value |
|---|---|
| Protocol | `core-v0-walk-forward.v1` |
| Development | `2026-02-02..2026-06-30` |
| Validation | `2026-07-01..2026-07-31` |
| Holdout | `2026-08-01..2026-08-13` |
| Minimum history | At least 60 prior canonical trading sessions per signal |
| Outcome horizons | T+1, T+3, T+5, T+10 subsequent canonical trading sessions |
| As-of rule | Every formation input is effective/observable no later than evaluation date T |
| Tuning | Parameter search, threshold tuning, and optimization are forbidden |

If these rules are insufficient for a future executable run, the required
result is `OWNER_DECISION_REQUIRED_FOR_V2`; this contract does not edit V1.

## Formation/evaluation separation

```text
Canonical information effective/observable <= T
                |
                v
Candidate-specific formation at T
                |
                v
Candidate is frozen; no later input may rewrite eligibility
                |
       +--------+--------+--------+--------+
       v        v        v        v
      T+1      T+3      T+5      T+10
                |
                v
        Evaluation outcomes only
```

`T+1/T+3/T+5/T+10` are never candidate inputs. A frozen REC-A1 corporate-action
post-hoc integrity exclusion may invalidate or exclude an evaluation outcome
under its already-authorized policy; it may not change the candidate formed at
T. An unknown event authority remains fail-closed for the affected evaluation
denominator and is never coerced to `NO_EVENT` or zero.

## Candidate-specific minimum research panel

Every candidate/date panel must be a bounded, source-linked record. The common
minimum formation envelope is:

| Field group | Required evidence at or before T |
|---|---|
| Evaluation anchor | Evaluation date T, market-local session identity, calendar/session authority, and as-of boundary |
| Instrument identity | Immutable instrument ID, symbol, name, market, lifecycle/eligibility state, and identity lineage |
| Topic membership/context | Effective-dated topic membership, topic ID/name, membership role, validity interval, publication mode, snapshot date/as-of, and source lineage |
| Canonical bars | Required canonical OHLCV observations through T, trading dates, accepted observation identity, no-trade/trading-status semantics where applicable, and source/normalizer/reference lineage |
| Candidate inputs | The exact input fields authorized by the candidate's frozen machine-executable definition; absent authority means no candidate can be formed |
| Policy identity | Protocol, candidate-definition version, parameter/policy version, and any technical contract version used at formation |

The common envelope is not a substitute for a candidate definition. A complete
Historical Topic/System State replay is not a global prerequisite; only the
PIT fields actually required by the candidate definition are required.

### Candidate-specific additions

| Candidate | Minimum candidate-specific addition | Authority state in this audit |
|---|---|---|
| A1 Pre-Breakout | Definition-owned pre-breakout inputs and their exact PIT/as-of lineage, in addition to the common envelope | Not enumerable: no frozen canonical runtime definition |
| A2 Confirmed Breakout | Definition-owned confirmation inputs and their exact PIT/as-of lineage, in addition to the common envelope | Not enumerable: no frozen canonical runtime definition |
| A3 Pullback/Retest | Definition-owned pullback/retest acceptance inputs and their exact PIT/as-of lineage, in addition to the common envelope | Blocked by the future `PULLBACK_ACCEPTANCE` slot; no acceptance authority is implemented |
| Catch-up/rotation | The current shadow input shape is evidence only: topic grade/lifecycle/strength and snapshot context; topic/stock return context; instrument identity; canonical bars; active membership/role; liquidity/no-trade state; relative-gap history with dates; as-of; policy/parameter version; and lineage | `CATCH_UP` is provisional shadow-only, not a frozen Core V0 candidate definition |

The table records dependency shape, not a new strategy formula. It does not
authorize any threshold, lookback, support rule, RSI/volume rule, breakout rule,
or ranking parameter.

## Technical evidence dependency

When a candidate definition consumes WS2 Technical Evidence, it must consume the
formal `stock-technical-v0-policy.v1` semantics, not a new WS3 warm-up rule.
Each indicator record must bind:

- indicator ID and accepted algorithm/version/parameter set;
- value or explicit unavailable reason;
- market-local session date and `as_of`;
- required and actual observation windows, including counts and first/last dates;
- canonical observation authority and complete source lineage; and
- `CONTINUITY_PASS`, `CONTINUITY_FAIL`, or `CONTINUITY_UNKNOWN` with evidence.

The WS2 contract's candidate families are dependency identities only: MA5/10/20/60,
price-vs/distance-to-MA20, raw 5D/20D close return, Volume MA5/20 and ratio,
RSI14, and MACD 12/26/9. This Phase 2 contract does not select which family an
undefined A1/A2/A3 strategy must use. An empty event result or absent event row
is not `CONTINUITY_PASS` without the WS2 source/coverage proof.

## Outcome contract

For every formed candidate, the evaluation panel must separately contain the
subsequent canonical sessions and lineage for T+1, T+3, T+5, and T+10. Outcome
records must retain the candidate ID, formation date T, horizon/session date,
source/as-of evidence, and the frozen REC-A1 integrity-exclusion state. No
outcome record may be joined back into candidate formation or eligibility.

The Phase 2 audit found no canonical candidate/outcome panel. Therefore outcome
coverage is `BLOCKED_BY_FORWARD_OUTCOME_PANEL` for every candidate, and no
outcome or performance metric was produced.

## Temporal eligibility and warm-up

The hard Core V0 history requirement is 60 prior canonical trading sessions.
The date-level audit must prove this for each candidate/date, not infer it from
the aggregate fact that a symbol has OHLCV. The audit must additionally prove:

1. candidate-specific warm-up required by the frozen definition;
2. accepted canonical observations exist for every required window;
3. WS2 indicator-specific observation and continuity semantics pass where used;
4. every input is safe at the formation as-of boundary; and
5. identity, session, and source lineage are complete.

No candidate/date was certified in this Phase 2 audit because no canonical
candidate panel exists and A1/A2/A3 definition authority is incomplete. The
absence of a panel is a bounded dependency result, not a claim that every
symbol/date is globally unavailable.

## Authority and status rules

- A1 and A2 remain blocked by `BLOCKED_BY_CANDIDATE_DEFINITION_AUTHORITY`.
- A3 remains blocked by `BLOCKED_BY_PULLBACK_ACCEPTANCE_AUTHORITY`.
- Catch-up remains blocked by `BLOCKED_BY_CATCH_UP_DEFINITION_AUTHORITY`; the
  existing `CATCH_UP` implementation is shadow evidence, not formal authority.
- REC-A1 Freeze remains `OWNER_ACCEPTED_FROZEN_RESEARCH_ONLY_PRESERVED`. The
  Phase 1 owner-artifact/canonical-artifact hash mismatch and missing review
  ledger are recorded as a provenance/archive reconciliation gap. They do not
  reopen the 154 reviewed UNKNOWN decisions, and no unauthorized identity
  conflict was established by this audit.
- `READY_FOR_CORE_V0_EXECUTION` can only be emitted for an individual candidate
  after its own definition, panel, temporal, REC-A1, and outcome evidence all
  pass. No aggregate WS3 READY/NO state is emitted.

The full candidate disposition matrix and reverse-dependency record are in the
Phase 2 machine-readable artifact linked from the closure report.

## Governance states

| State | Phase 2 result |
|---|---|
| Application/schema/migration/runtime changes | `NO` |
| Walk-forward/backtest/performance metrics | `NOT_RUN / NONE` |
| Strategy Review accepted/rejected | `NOT_MADE` |
| Recommendation publication/Opportunity production activation | `NOT_AUTHORIZED` |
| Database/G1/G2/G3/Canary | `NOT_RUN / NOT_RERUN / PRESERVED EVIDENCE` |
| `NEXT_TASK` | `NOT_MODIFIED` |
| Release status | `NOT_A_RELEASE_CANDIDATE` |
