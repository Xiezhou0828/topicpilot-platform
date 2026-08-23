# Today & Stock Surfaces

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; frontend, API, and data contracts own the
formal surface semantics.

## Scope

This series covers the current Home/Today and Stock Explorer/detail surfaces:
their API/read-model wiring, disclosure states, EOD and historical price
presentation, and the boundary between formal, preview, partial, and
unavailable data.

## Current state

- Daily Focus, Main Topics, Heating/Cooling, Market Events, and Market Overview
  are reconciled to the shared Home resource path.
- The typed TWSE/TPEx index contract and source-shaped fixtures exist, but the
  Today Market Index capability is `WAITING_SOURCE_USE_APPROVAL`; persistence,
  post-close capture, Home/API projection, and frontend rendering remain
  blocked. Turnover remains blocked by the TPEx semantic/usage authority gap.
- Stock code/name search, formal topic filtering, EOD list/detail, Explorer/
  Drawer wiring, historical bar backend, and raw historical price frontend
  publication are canonicalized at their documented boundaries.
- Technical detail is a separate WS2 policy/publication surface. Intraday quote
  update, institution flow, narrative, Opportunity, and recommendation remain
  separate follow-ups.

## Canonical authority

- [Accepted product surfaces and UX contract](../architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)
- [V2 frontend design specification](../architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md)
- [API guide](../api/api-guide.md)
- [V2 production data architecture](../architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md)
- [`PROJECT_CONTEXT.md` current surface matrix](../../PROJECT_CONTEXT.md)

## Completed

- Shared Home/Today resource-path wiring with explicit partial/temporary
  semantics.
- Formal Stock search, topic filter, EOD projection, Explorer, and Drawer
  boundaries.
- Historical bar backend and raw historical price frontend publication.
- Fail-closed handling where formal data is absent; Preview is not a formal API
  fallback.

## Unfinished / deferred

- Formal index persistence, post-close capture, complete market aggregate
  semantics, turnover, narrative, and derived market score.
- Technical V0 formal evidence provider/consumer integration.
- Stock institution flow, narrative, Opportunity, recommendation, and complete
  technical detail.
- Intraday quote update.

## Dependencies and blockers

- Source-use approval and upstream activation for Today indices/aggregates.
- TPEx turnover semantics and usage authority.
- WS2 technical evidence surface and the separate Opportunity contracts.

## Do not do

- Do not infer business fields in the browser.
- Do not treat `TopicSource=api` as proof that every Topic field is formally
  published.
- Do not use Preview as a silent formal-data fallback.
- Do not mix EOD, historical, intraday, technical, event, and recommendation
  semantics into one undocumented surface.

## Historical evidence

- [Today mainline reconciliation](../reports/TASK-FE-BE-TODAY-MAINLINE-C_TODAY_RECONCILIATION_20260814.md)
- [Today index typed contract](../reports/TASK-FE-BE-TODAY-005B_INDEX_TYPED_CONTRACT_AND_FIXTURE_BOUNDARY.md)
- [Today formal-data reassessment](../reports/TASK-FE-BE-TODAY-P0_REMAINING_FORMAL_DATA_REASSESSMENT.md)
- [Stock-005C Explorer/Drawer EOD wiring](../reports/TASK-FE-BE-STOCK-005C_EXPLORER_DRAWER_EOD_FORMAL_WIRING.md)
- [Historical price frontend wiring](../reports/TASK-FE-BE-STOCK-006A-FE_HISTORICAL_PRICE_UI_WIRING_REPORT.md)

## Next bounded route

Continue only the explicitly authorized formal-data/read-model boundary for
the affected surface. Preserve visible status (`temporary`, `preview`,
`deferred`, `unavailable`, or `error`) until source and contract gates are
closed; do not broaden a surface by inference.
