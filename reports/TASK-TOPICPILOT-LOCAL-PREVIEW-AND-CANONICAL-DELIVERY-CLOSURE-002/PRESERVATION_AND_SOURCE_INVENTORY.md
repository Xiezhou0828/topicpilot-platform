# Preservation and Source Inventory

## Preservation

The previous bounded snapshot remains at:

`E:\TopicPilot\preservation\TASK-TOPICPILOT-ONE-SHOT-DELIVERY-GOVERNANCE-AND-COMPANY-RESEARCH-CLOSURE-001-BOUNDED`

Its original result was 48 rows, 45 copied, 3 skipped, 0 missing. A fresh validation found two later source-content mismatches in the old snapshot; it was not overwritten.

This task created a new bounded snapshot:

`E:\TopicPilot\preservation\TASK-TOPICPILOT-LOCAL-PREVIEW-AND-CANONICAL-DELIVERY-CLOSURE-002-BOUNDED`

Result: 61 rows, 59 copied, 2 explicitly skipped, 0 missing, 0 mismatched, `PRESERVATION_VERIFIED`.

The two skipped entries are non-existent optional source paths recorded by the preservation tool; no existing file was treated as deleted.

## Integrated source inventory

Integrated and explicitly staged later:

- Company Research Read Model: `services/api/src/topicpilot_api/company_research/**`, its read-model tests, and `services/api/src/topicpilot_api/config.py` / `main.py`.
- Financial Research and EPS: `services/api/src/topicpilot_api/financial_research/**`, the bounded financial fixture, and eight focused backend test files.
- Company Research V3 frontend: `StockDetailPage.tsx`, `StockOverviewV1.tsx`, `StockResearchCards.tsx`, the six-group research fixtures, the topic-story dependency fixtures, and the read-only frontend adapters.
- Preview configuration: `infra/scripts/preview_review.mjs`, `preview_review_config.mjs`, the frontend README, and the configuration contract test.
- Governance: existing preservation/delivery scripts plus `development_preflight.mjs`, `delivery_preflight.mjs`, `two_gate.test.mjs`, and the existing governance tests.
- Documentation and this task's reports.

Explicitly excluded: `node_modules`, build output, caches, temporary files, credentials, PDFs/downloads, the original dirty worktrees, Stock Topic Impact worktree changes not required by the Company Research V3 integration, Publication Flow V2 changes, Formal Topic Authority, Production data, and generated API files (no generated change was required).
