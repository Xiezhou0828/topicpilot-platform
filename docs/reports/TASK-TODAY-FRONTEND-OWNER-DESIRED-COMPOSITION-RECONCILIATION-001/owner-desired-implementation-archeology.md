# TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001

## Closure

```text
OWNER_DESIRED_TODAY_IMPLEMENTATION_FOUND=YES
OWNER_DESIRED_TODAY_SOURCE_SHA=c544e2a5a6e3531232fb69e7580c99a0b1a5eef5
OWNER_DESIRED_TODAY_SOURCE_BRANCH=origin/codex/today-production-convergence-20260913
OWNER_DESIRED_TODAY_COMPONENT_ROOT=apps/web/app/components/v2/TodayMarketPage.tsx
OWNER_DESIRED_TODAY_ROUTE=/
CURRENT_CANONICAL_SOURCE_SHA=d783f624d3daa7f7928a1be49796bd39991a4f5b
WORKTREE_PATH=E:\topicpilot-worktrees\TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001
BRANCH_NAME=codex/task-today-frontend-owner-desired-composition-reconciliation-001
STORAGE_DRIVE=E:
C_DRIVE_NEW_WORKSPACE_CREATED=NO
```

The owner-desired composition was found as a safe, API-wired lineage rather than a mock-only implementation. The selected source is the production-convergence commit `c544e2a5a6e3531232fb69e7580c99a0b1a5eef5`; it retains the approved FE-002C/FE-002D/FE-002E reading order and compact card treatment while consuming the canonical Home response.

## Evidence chain

- `docs/reports/TASK-FE-002C_HOME_FINAL_FREEZE_REPORT.md`: Market Overview freshness belongs in the header, Today Focus is compact, and exactly three mainline cards retain grade and navigation.
- `docs/reports/TASK-FE-002D_HOME_MARKET_SUMMARY_DENSITY_REPORT.md`: the focus is investor-readable and avoids duplicate narrative blocks.
- `docs/reports/TASK-FE-002E_HOME_FINAL_FIX_REPORT.md`: removes `盤中快照` and `01/02/03`, and records the compact first-screen fit.
- `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`: defines the Home order as summary, Today Focus, Mainline TOP3 and specifies indices/OTC/turnover/breadth/update context.
- `c544e2a5a6e3531232fb69e7580c99a0b1a5eef5`: wires that composition to official market fields, backend-owned Today sections, compact disclosure and fail-closed states.

## Current canonical audit before reconciliation

At `d783f624d3daa7f7928a1be49796bd39991a4f5b`, `/` correctly routed to `TodayMarketPage` and already had Market Overview, Today Focus, backend-owned mainlines and downstream pulse/rotation/opportunity sections. The gaps were composition and field exposure, not a missing route:

- Market Overview exposed tracked counts and basic breadth but did not render official index, turnover and distribution fields supported by the Home API.
- Today Focus was present but its disclosure/state metadata competed with investor-facing content.
- Mainline data, grade and topic navigation existed, but the source did not provide the complete owner-desired official market summary treatment.
- The existing source already lacked rendered ordinal labels and the redundant `盤中快照`; those constraints were preserved.

## Cause classification

```text
市場概況=FRONTEND_LAYOUT_DIFFERENT + API_DATA_EMPTY (field-level availability can be empty)
今日市場重點=FRONTEND_LAYOUT_DIFFERENT + FORMAL_DATA_PARTIAL
今日主線=FRONTEND_LAYOUT_DIFFERENT (backend data and order already existed)
Top 3 / grade / navigation=API_DATA_EMPTY only when the formal payload is empty; otherwise frontend presentation match
```

No missing backend endpoint or schema migration was required. The current API contract already carries `marketOverview.indices`, `marketOverview.turnover`, `marketOverview.marketHealth`, breadth/distribution data, `dailyFocus`, and three backend-owned `mainTopics` in the production response.

## API compatibility

```text
DESIRED_TODAY_UI_SUPPORTED_BY_CURRENT_API=YES
BACKEND_CHANGE_REQUIRED=NO
MISSING_REQUIRED_API_FIELDS=
```

The frontend change updates the generated client declarations/openapi snapshot and adapters to consume fields already present in the canonical API contract. It does not change the API service, database, migration, publication gate, topic hierarchy, ranking, or scoring policy.

## Reconciliation performed

- Reconciled `TodayMarketPage` to the owner reading order: `市場概況` → `今日市場重點` → `今日主線`.
- Added official index/turnover presentation and breadth/distribution presentation from backend-owned fields.
- Kept Today Focus text backend-owned and moved provenance/status/quality details into a compact disclosure.
- Kept exactly three backend-ordered mainline cards, conditional formal grade badges, and canonical topic links.
- Preserved downstream pulse, rotation and opportunity surfaces without browser ranking or synthetic recommendations.
- Preserved explicit unavailable/partial/temporary/error semantics and never fabricated unavailable market facts.
- Added focused source-contract tests and retained Topic/Stock/Favorites regression coverage.

## Scope boundary

No backend, Production, migration, schema, scheduler, Topic hierarchy, Parent/Leaf, Stock Explorer, Favorites, scoring, ranking or policy change was made. No old mock/demo Today surface was restored.
