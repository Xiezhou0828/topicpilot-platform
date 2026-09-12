# Data / Reference / Historical

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; data architecture, schema, source, and
lineage documents own the formal rules.

## Scope

This series covers the date-effective reference universe, canonical identity,
historical OHLCV persistence, source lineage, PIT reconstruction limits, and
data-quality or licensing boundaries shared by WS1, WS2, and WS3.

## Current state

- The Data / Reference / Post-Close mainline is complete through
  `TASK-DATA-REF-009A`; the TPE 313 plus TWO 193 date-effective universe
  reconciled to `506/506` with `DOWNSTREAM_READY=true`.
- The V2 canonical observation chain owns the reconciled local evidence of 507
  symbols and 63,826 canonical OHLCV rows covering 2026-02-02 through
  2026-08-13.
- The 96-stock expansion toward a 603-candidate universe is a staging/reference
  route, not an automatically qualified runtime universe.
- Historical OHLCV readiness does not equal historical Topic/System State
  readiness. Prices alone cannot replay historical Topic Score, Grade,
  Lifecycle, or relation state without point-in-time inputs and lineage.

## Canonical authority

- [V2 Production Data Architecture](../architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md)
- [ERD](../architecture/erd.md)
- [Data dictionary](../data/data-dictionary.md)
- [Enterprise bundle v1](../data/enterprise-bundle-v1.md)
- [Market data source decision record](../architecture/PHASE_3_1E_MARKET_DATA_SOURCE_DECISION_RECORD.md)
- [Reference bootstrap runbook](../operations/reference-bootstrap.md)
- [Public data and licensing policy](../policies/public-data-and-licensing.md)

## Completed

- Date-effective reference universe reconciliation through the current A
  mainline boundary.
- Canonical historical OHLCV persistence and read/publication handoff at the
  documented boundary.
- Identity, source, PIT, and missing-data governance for the V2 observation
  chain.

## Unfinished / bounded limitations

- Raw observed adjustment state and corporate-action continuity remain
  deferred.
- Historical Topic/System State replay remains unavailable where role,
  relation, score, grade, Lifecycle, or source lineage is missing.
- Expanded 603-universe runtime and historical qualification is not complete.
- Some market aggregates and provider/source-use approvals remain separate
  dependencies of the Today series.

## Dependencies and blockers

- Source authority, licensing, and provider-use approval.
- Effective-dated identity and observation lineage.
- Point-in-time snapshots for every downstream derived field.

## Do not do

- Do not treat raw reports or a browser snapshot as canonical data authority.
- Do not fill missing numeric values with zero or silently carry values forward.
- Do not backfill historical Topic/System State from price-only OHLCV.
- Do not call the staged 603 universe Production-ready without identity,
  coverage, quality, and consumer evidence.

## Historical evidence

- [Reference A mainline closure](../reports/TASK-DATA-REF-009A_RUNTIME_ACTIVE_REFERENCE_BINDING_FIX_AND_SINGLE_POST_CLOSE_CANARY_RETRY.md)
- [Historical persistence authority promotion](../reports/TASK-DATA-HIST-PERSISTENCE-AUTHORITY-PROMOTION.md)
- [603 universe and OHLCV authority promotion](../reports/TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-CANONICAL-AUTHORITY-PROMOTION-AND-CONSUMER-HANDOFF-20260820/formal-closure-report.md)
- [Historical bootstrap execution evidence](../reports/TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-BOOTSTRAP-EXECUTION-20260819/formal-task-closure-report.md)
- [Historical validation and calibration work order](../work-orders/PHASE_3_7_003E_HISTORICAL_VALIDATION_CALIBRATION.md)

## Next bounded route

Protect the canonical reference and observation chain while qualifying only the
approved downstream consumer. Any corporate-action, adjustment, or expanded-
universe work must preserve PIT, lineage, idempotency, and rollback evidence.
