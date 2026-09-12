# WS1/L2 Owner-Decision Readiness Disposition

Date: 2026-08-22
Canonical HEAD observed: `b569430d2a358cab6a5915aeaacff2810df4913c`
Policy: `topic-lifecycle-policy.provisional.1`
Calculation contract: `topic-lifecycle-shadow.v1`

## Decision

`CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION_READY=PARTIAL`

The Owner Decision removes the requirement that historical topic relations be fully PIT-safe. A deterministic retrospective research reconstruction may freeze the current canonical topic taxonomy and instrument-topic relation set, then apply that frozen set consistently backward from 2026-01-01. This is expressly not historical PIT truth and is expressly not `FORWARD_SHADOW`.

The authority for this route is fixed as:

`CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`

Research mode is `RETROSPECTIVE_RESEARCH`. Any resulting evidence must remain research-only and must not be presented as evidence that was generated on the historical date.

## Answer to Owner

The requested window is 2026-01-01 through the observed canonical boundary 2026-08-13.

| Window | Safe disposition under the new authority |
|---|---|
| 2026-01-01 through 2026-02-01 | No canonical daily-price evidence is available. Lifecycle change evidence cannot be reconstructed; cells must be `UNAVAILABLE` / `FAIL_CLOSED`. No synthetic prices or returns are allowed. |
| 2026-02-02 | Canonical close evidence begins, but the available authority has no prior canonical close for a complete close-to-close change. Treat as a price warm-up / close-only date unless an accepted prior close is independently present for the specific instrument. |
| 2026-02-03 through 2026-08-13 | Candidate deterministic retrospective research window, per instrument/date where both accepted canonical closes exist and no fail-closed price or lineage condition is present. Use the frozen current taxonomy/relations, `instrument_id` identity, and explicit research-only caveats. |
| After 2026-08-13 | Not established by the inspected canonical boundary. Do not extend the reconstruction window from this preflight. |

Therefore, the practical answer is:

> A retrospective research evidence series can be safely designed for 2026-02-03 through 2026-08-13 at the raw observed close-to-close level, with per-instrument fail-closed gaps and explicit adjustment/identity limitations. The full requested 2026-01-01 start cannot yield full daily lifecycle evidence because the price authority starts later. No strict full-window, full-coverage lifecycle reconstruction is established.

This is a readiness disposition only. No historical reconstruction, backfill, database mutation, or engine execution was performed.

## Blocker reassessment

| Item | Previous concern | New disposition | What it still blocks |
|---|---|---|---|
| Historical topic relations / taxonomy | Current mapping was not PIT-safe before 2026-08-07 | **Resolved for this research authority**. Freeze and retrospectively apply the current canonical taxonomy and relation set. | Historical PIT truth, survivorship-safe membership, and `FORWARD_SHADOW` claims remain prohibited. |
| `LiveTrackingUniverse` | Current-state model has no historical membership interval | **Adapter blocker, resolvable**. It need not be the historical authority under the Owner Decision; a future deterministic retrospective adapter can use frozen canonical instrument IDs and frozen relations. | Running the current `TopicLifecycleEngine` unchanged for the historical window. No engine change is authorized in this task. |
| Corporate action / adjustment | Canonical bars report `adjustmentState=UNKNOWN`; continuity is not complete | **Research limitation, not a universal reconstruction blocker**. Consume only observed accepted closes; never silently back-adjust or infer economic returns. Mark unknown/discontinuous cases and fail closed per instrument/date. | Full adjustment-corrected return interpretation and continuity-complete lifecycle evidence. |
| Security identity | No populated security-identity history was found | **Research limitation, resolvable at instrument-ID level**. Frozen `instrument_id` joins can support topic aggregation. | Alias continuity, symbol-level historical truth, and survivorship-safe identity claims. |
| Daily price evidence | Static canonical OHLCV starts 2026-02-02 | **Hard bounded-window blocker**. No evidence supports 2026-01-01 through 2026-02-01; 2026-02-02 is warm-up unless a prior accepted close exists. | Any daily change/lifecycle state before the first complete close pair; exact per-cell coverage where a member bar is missing. |
| 4,235 / 4,236 discrepancy | Formal materialization reports 4,235 member facts; runtime aggregate is 4,236 | **Formal-exactness reconciliation blocker, not a hard blocker for frozen-taxonomy research reconstruction**. The retrospective route must not use the discrepancy as silently resolved; carry it as an unresolved reconciliation flag and cross-check only. | Exact parity with the existing formal member-fact artifact and formal closure claims. |
| Missing Migration 0032 / forward-shadow artifacts | No canonical Migration 0032 or committed forward-shadow readiness/reconciliation artifact was found | **Not required for this retrospective authority**, but remains a provenance boundary. | Formal promotion, forward evidence, or claims that this route is `FORWARD_SHADOW`. |

The former fully PIT-safe relation blocker is therefore removed, but the daily-price start, price-lineage uncertainty, formal member-fact discrepancy, and identity limitations remain material.

## Deterministic reconstruction contract implied by the decision

The future bounded route may be considered deterministic only if it uses all of the following rules:

1. Membership authority is the frozen canonical taxonomy and frozen canonical instrument-topic relation set, applied retrospectively from 2026-01-01 and marked `CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`.
2. Historical membership is not sourced from the current `LiveTrackingUniverse` state. A deterministic adapter must use explicit frozen instrument IDs and the frozen relation version.
3. Prices come only from accepted canonical daily-bar observations. Missing bars, missing previous closes, discontinuities, correction ambiguity, and unresolved lineage fail closed for the affected instrument/date; no synthetic fill is permitted.
4. `adjustmentState=UNKNOWN` remains unknown. Observed raw close-to-close movement may be reported as research evidence, but it must not be described as an adjustment-corrected economic return.
5. Instrument IDs may be used for aggregation. No claim is made that symbol aliases, security identity history, delistings, or survivorship are PIT-complete.
6. The first evaluable date has no asserted prior lifecycle state. Previous-stage state must bootstrap deterministically from an explicit null/initial state and the available evaluable sequence; it must not import future state or invent pre-window observations.
7. The 4,235/4,236 difference remains a visible reconciliation flag. It cannot be converted into a hidden inclusion or exclusion decision.
8. The output authority remains separate from both `HISTORICAL_RECONSTRUCTED_SHADOW` used by the prior strict audit and `FORWARD_SHADOW`. The prior audit is retained as historical evidence of the previous, stricter disposition.

## Coverage statement

The inspected canonical price authority contains 63,826 daily OHLCV rows across 507 symbols for 2026-02-02 through 2026-08-13. This is source coverage, not topic-date lifecycle coverage. Exact topic-date coverage would require the bounded reconstruction run and must not be fabricated in this preflight.

The earlier formal snapshot authority contains 460 rows across five dates (2026-08-07 through 2026-08-13), with 4,235 materialized member facts. The runtime aggregate observed 4,236 members over those snapshots. Those artifacts remain useful for reconciliation, but the Owner Decision permits the retrospective route to use the frozen canonical relation set rather than requiring those formal PIT member facts as its sole membership source.

## Bootstrap disposition

2026-01-01 is not an evaluable lifecycle date in the currently inspected price authority. It must bootstrap as an explicit no-price / fail-closed boundary, not as a synthetic initial return. The first date at which a close-to-close price evidence pair can normally be evaluated from the inspected authority is 2026-02-03, using 2026-02-02 as the observed prior close. The lifecycle stage sequence must begin with an explicit null/initial previous-stage state at the first evaluable date; no historical stage is inferred before that date.

## Owner decision required

No additional Owner decision is required to remove the historical-PIT relation blocker: the new authority already supplies that decision. The remaining scope choice is operational rather than semantic: approve a separate, read-only deterministic retrospective adapter/harness that excludes current `LiveTrackingUniverse` as the historical authority and emits the authority markers above. That route must still leave the Lifecycle policy unchanged and must remain separate from `FORWARD_SHADOW`.

## Minimum bounded next route

The smallest next route is a read-only reconstruction harness design/review, followed by one bounded execution only if separately authorized:

- freeze and hash the canonical taxonomy/relation/instrument inputs;
- build the date × topic × instrument price-pair availability contract;
- emit explicit unavailable/warm-up/fail-closed cells;
- reconcile, but do not silently repair, the 4,235/4,236 difference;
- report raw observed evidence with adjustment and identity caveats;
- keep output authority `CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION` and stop at 2026-08-13.

No implementation or execution of that route is part of this disposition.

## Scope and safety attestations

- Lifecycle thresholds, persistence/hysteresis, confidence, and Leader proxy were not changed.
- No Strength, volume, news, or total score was introduced.
- No `TopicLifecycleEngine` code was changed or executed for reconstruction.
- No historical reconstruction or backfill was executed.
- No DB mutation, deploy, push, reset, clean, restore, or `NEXT_TASK` modification was performed.
- Existing owner dirty/untracked state was preserved.
