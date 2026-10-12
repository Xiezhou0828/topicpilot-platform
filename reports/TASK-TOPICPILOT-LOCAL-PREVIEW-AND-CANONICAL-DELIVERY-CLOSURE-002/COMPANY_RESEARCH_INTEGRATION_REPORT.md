# Company Research Integration Report

The integrated Company Research V3 surface keeps six public content groups and a formal read-model boundary for 1303, 1314, and 1319. The route is:

`GET /api/v2/stocks/{symbol}/research`

When the read model is absent or not approved, the route returns HTTP 200 with `NOT_CONNECTED` and no public sections. Publication requires the existing source-rights, reviewer evidence, owner approval, and publication gate; no fixture is silently promoted.

The five financial read-only routes remain separate from formal Topic Authority. Existing EPS evidence remains unchanged: 1303 2026 Q1 `1.80`; 1314 2026 Q1 `-0.07`; 1314 2026 H1 `-0.52` with manual review and the `8,426,000` difference preserved; 1319 FY2025 `6.43`. H1 is not converted into Q2, and missing values are not converted into zero.

Formal Topic Authority, the unique 132-topic authority, and formal stock-topic relations were not changed.
