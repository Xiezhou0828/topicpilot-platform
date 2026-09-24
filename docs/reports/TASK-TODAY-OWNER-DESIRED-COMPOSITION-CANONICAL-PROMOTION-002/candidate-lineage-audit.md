# Candidate lineage audit

## Lineage

```text
TODAY_CANDIDATE_SHA=38eed205f058fa86cb8a21f7fccf726d76ebd1db
TODAY_CANDIDATE_PARENT_SHA=d783f624d3daa7f7928a1be49796bd39991a4f5b
CURRENT_CANONICAL_BASE=c177b949df9dbd53044bc598b9f0a1a48cb6db12
CURRENT_CANONICAL_BASE_PARENT=d783f624d3daa7f7928a1be49796bd39991a4f5b
```

The candidate is a direct sibling of the current canonical `main` commit: both
start from the same `d783f62` parent. This made the Today change suitable for a
bounded commit-preserving composition.

## Candidate source files

```text
apps/web/app/components/v2/TodayMarketPage.tsx
apps/web/app/globals.css
apps/web/app/lib/commercial-state.d.mts
apps/web/app/lib/commercial-state.mjs
apps/web/app/lib/generated-api.d.ts
apps/web/app/lib/today-mainlines.ts
apps/web/app/lib/today-market-fields.ts
packages/api-client/openapi.json
packages/api-client/src/schema.d.ts
```

The generated client changes add the existing Home market distribution and
breadth fields required by the Today presentation. They do not alter the
FastAPI implementation or the `/api/v2/home` server contract.

## Candidate test files

```text
apps/web/tests/commercial-state.test.mjs
apps/web/tests/data-refresh.test.mjs
apps/web/tests/home-market-summary.test.mjs
apps/web/tests/rendered-html.test.mjs
apps/web/tests/today-commercial-redesign.test.mjs
apps/web/tests/today-daily-focus.test.mjs
apps/web/tests/today-home-resource.test.mjs
apps/web/tests/today-mainlines.test.mjs
apps/web/tests/today-market-events.test.mjs
apps/web/tests/today-market-fields.test.mjs
apps/web/tests/today-market-overview.test.mjs
apps/web/tests/today-opportunity-teaser.test.mjs
apps/web/tests/today-section-state-disclosure.test.mjs
```

## Candidate report-only files

```text
docs/reports/TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001/owner-desired-implementation-archeology.md
docs/reports/TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001/release-closure.json
docs/reports/TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001/today-product-match-matrix.csv
docs/reports/TASK-TODAY-FRONTEND-OWNER-DESIRED-COMPOSITION-RECONCILIATION-001/today-reconciliation-validation.md
```

The candidate commit contained no `services/api` source changes and no
`services/api/alembic/versions` changes. Its generated-client attempt to remove
the pre-existing read-only migration client surface was restored during bounded
composition, so it is not present in the final promotion diff.

```text
TODAY_CANDIDATE_BACKEND_CHANGE_COUNT=0
TODAY_CANDIDATE_MIGRATION_CHANGE_COUNT=0
UNRELATED_CHANGE_COUNT=0
```
