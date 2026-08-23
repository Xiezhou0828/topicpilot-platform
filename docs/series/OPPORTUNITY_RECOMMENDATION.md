# Opportunity / Recommendation

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; product and shadow contracts own the
formal semantics.

## Scope

This series covers the Opportunity qualification boundary, shadow-only Trend
Continuation and Catch-up research paths, structured explanation, ranking
profiles, and the separate Recommendation/product-publication boundary.

## Current state

- Opportunity semantics and state vocabulary are frozen as a shadow contract,
  not as a customer Buy/Sell instruction.
- `S/A` are the formal Opportunity universe; `B` may enter only as a qualified
  warming/improving exception; `D` is excluded; new `DECLINING` opportunities
  are excluded.
- `Close >= 20MA` is a hard gate; 60MA is a structure/ranking factor and not a
  hard gate. Trend and Catch-up rank independently, with post-close ranking and
  status-only intraday behavior.
- Shadow read models and deterministic explanation fields may exist for
  research/adapter purposes. Production API publication, persistence,
  scheduler activation, and customer recommendation publication are not
  complete.
- WS3 A1/A2 evidence remains research-only and does not become an Opportunity
  strategy merely because a shadow surface exists.

## Canonical authority

- [Opportunity Engine Specification](../product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md)
- [Opportunity qualification policy](../architecture/decisions/OPPORTUNITY_QUALIFICATION_POLICY_V1.md)
- [Opportunity shadow read API](../architecture/decisions/OPPORTUNITY_SHADOW_READ_API_V1.md)
- [Opportunity shadow read API guide](../api/opportunity-shadow-read-v1.md)

## Completed

- Evidence-first, fail-closed shadow semantics.
- Five user-facing shadow states: `SELECTED`, `WAITING_RETEST`,
  `WAITING_CONFIRMATION`, `DEFERRED`, and `EXCLUDED`.
- Independent Trend/Catch-up ranking profiles and structured explanation
  contract.
- Deterministic no-look-ahead replay boundary and provider-neutral read model.

## Unfinished / not published

- Forward calibration, outcome evaluation, and any parameter optimization.
- Production provider, persistence, scheduler, and customer-facing API/UI
  activation.
- Formal recommendation publication, trade instruction, position sizing,
  stop-loss, or target-price semantics.

## Dependencies and blockers

- Formal Topic Grade/Lifecycle/context inputs and their PIT provenance.
- Formal technical and historical evidence providers.
- Owner acceptance of research and any later production contract.

## Do not do

- Do not present Opportunity as investment advice or a Buy/Sell/Hold signal.
- Do not recalculate Topic Score, Grade, or Lifecycle inside Opportunity.
- Do not let an LLM decide state, ranking, eligibility, or risk; it may only
  verbalize structured backend evidence in a later approved surface.
- Do not turn fixtures, old Recommendation scores, or historical labels into
  current policy authority.

## Historical evidence

- [Opportunity decision contract](../reports/TASK-BE-024A_OPPORTUNITY_DECISION_CONTRACT_REPORT.md)
- [Opportunity qualification policy](../reports/TASK-BE-024B_OPPORTUNITY_QUALIFICATION_POLICY_REPORT.md)
- [Opportunity shadow read API](../reports/TASK-BE-024C_OPPORTUNITY_SHADOW_READ_API_REPORT.md)
- [Opportunity engine V1 report](../reports/TASK-BE-024_OPPORTUNITY_ENGINE_V1_REPORT.md)
- [Opportunity runtime boundary](../reports/TASK-OPPORTUNITY-SHADOW-001_RUNTIME_BOUNDARY_REPORT.md)

## Next bounded route

Keep Opportunity in its shadow/research boundary while qualifying the required
PIT data and forward-evaluation protocol. Any production implementation needs
an explicit separate contract, write set, owner decision, and release path.
