# Topic framework regression tests

## Passed checks

| Check | Result |
| --- | --- |
| `apps/web`: `npm test` | PASS — 162/162 |
| `apps/web`: `npx tsc --noEmit` | PASS |
| `apps/web`: `npm run build` | PASS — `/topics` and `/topics/:slug` retained |
| Focused hierarchy/catalog/lifecycle Node tests | PASS — 10/10 |
| Python 3.12 backend Catalog/formal read-model tests | PASS — 35/35 |
| `packages/api-client`: `npm run check` | PASS — generated OpenAPI declarations unchanged |
| `packages/api-client`: `npm test` | PASS — 4/4 |
| `git diff --check` | PASS |

The added frontend regression suite is `apps/web/tests/topic-hierarchy-reconciliation.test.mjs`. It covers Catalog-first identity, state-unavailable composition, canonical Parent/Leaf list behavior, Parent `NOT_APPLICABLE` detail, and the prohibition on using `groupName` as hierarchy authority.

The backend test command was run with the repository-required Python 3.12 interpreter. The machine default Python 3.10 was not used for the final result because the project requires `>=3.12,<3.13`.
