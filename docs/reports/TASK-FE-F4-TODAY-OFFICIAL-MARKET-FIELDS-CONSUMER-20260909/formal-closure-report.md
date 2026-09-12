# Frontend F4｜Today Official Market Fields Consumer

```text
TASK=F4
ROADMAP=N5
EXACT_SHA_BEFORE=b8f854db08de379c6d9b6eba27575fc4afd5cc45
EXACT_SHA_AFTER=reported in final handoff after commit (self-referential commit field)
COMMIT_SHA=reported in final handoff after commit (self-referential commit field)
COMMIT_MESSAGE=feat(today): connect official market fields

TODAY_OFFICIAL_MARKET_FIELDS_CONSUMER=PASS
INDEX_DISPLAY=PASS
TURNOVER_DISPLAY=PASS
ASOF_TRADING_DATE=PASS
UNIT_SEMANTICS=PASS
EOD_NOT_LIVE=PASS
NON_TRADING_DAY_ASOF=PASS
NULL_PARTIAL_UNAVAILABLE_ERROR_STATES=PASS
UNAVAILABLE_STATE=PASS
NO_FAKE_OR_LEGACY_FALLBACK=PASS
NO_LEGACY_FALLBACK=PASS
TYPED_GENERATED_CLIENT_ONLY=PASS

LATEST_PRODUCTION_DATA_VALIDATION=PENDING_A10
A10_PRODUCTION_ACTIVATION=NOT_RUN
PRODUCTION_MUTATION=NO
PUSH=NO
MERGE=NO
DEPLOY=NO

TSC_NO_EMIT=PASS
WEB_PRODUCTION_BUILD=PASS
API_CLIENT_TESTS=PASS (4 passed)
FRONTEND_TESTS=PASS (182 passed)
FOCUSED_TODAY_HOME_TESTS=PASS (17 passed)
BACKEND_TODAY_HOME_CONTRACT_TESTS=PASS (7 passed, 1 skipped PostgreSQL integration without TEST_DATABASE_URL/DATABASE_URL)
GIT_DIFF_CHECK=PASS

CANONICAL_STATUS=CANONICALIZED_IN_REQUESTED_CHECKOUT
RELEASE_STATUS=NOT_RELEASED
PRODUCTION_VERIFICATION=PENDING_A10
CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION
F4_TASK_OWNED_TRACKED_DIRTY=0 (the residual TodayMarketPage file change is a pre-existing owner hunk)
NEXT_FRONTEND_TASK_RECOMMENDATION=After A10 evidence is available, perform Today official market freshness readback and production UI verification; do not start in this task.
```

## F4 write-set

- `apps/web/app/components/v2/TodayMarketPage.tsx` — typed official index and turnover consumer with explicit EOD, as-of, source, lineage, unit, and availability disclosures.
- `apps/web/app/globals.css` — Today official market field presentation styles.
- `apps/web/app/lib/today-market-fields.ts` — generated-contract field guards, state mapping, and metadata-preserving formatters.
- `apps/web/tests/today-market-fields.test.mjs` — contract and state coverage for official EOD, non-trading-day as-of, null/partial/unavailable/error, and fallback boundaries.
- `apps/web/tests/today-market-overview.test.mjs`
- `apps/web/tests/home-market-summary.test.mjs`
- `apps/web/tests/today-section-state-disclosure.test.mjs`
- `docs/reports/TASK-FE-F4-TODAY-OFFICIAL-MARKET-FIELDS-CONSUMER-20260909/formal-closure-report.md`

The implementation consumes only the generated `HomeResponse` contract through the existing `client.getHome()` path. It renders backend-provided `indices[]` and `turnover[]` records individually, preserves `tradingDate`, `asOf`, `source`, `lineage`, `currency`, `unit`, and `scale`, and never combines or estimates values. Formal data is labeled official EOD/close and explicitly excludes live or intraday meaning. Missing or unavailable records remain unavailable in the UI; no demo, mock, legacy, or static fallback is used.

## Remaining pre-existing dirty work

The following owner/parallel changes were present before F4 and remain uncommitted: `apps/web/app/components/v2/TodayMarketPage.tsx` (owner hunk only), `apps/web/app/components/v2/TopicDetailPage.tsx`, `apps/web/app/lib/today-mainlines.ts`, `apps/web/app/lib/topic-api.ts`, `compose.yaml`, `docs/operations/deployment.md`, `packages/api-client/src/client.d.mts`, `packages/api-client/src/client.mjs`, `render.yaml`, `services/api/.env.example`, `services/api/pyproject.toml`, `services/api/src/topicpilot_api/live/cli.py`, `services/api/src/topicpilot_api/live/config.py`, `services/api/src/topicpilot_api/live/post_close.py`, `services/api/src/topicpilot_api/live/scheduler.py`, `services/api/src/topicpilot_api/main.py`, `services/api/src/topicpilot_api/orm/__init__.py`, `services/api/src/topicpilot_api/production_read_model.py`, `services/api/src/topicpilot_api/schemas.py`, `services/api/tests/test_v2_architecture_freeze.py`, `apps/web/app/lib/formal-topic-snapshot.ts`, `apps/web/tests/formal-topic-snapshot.test.mjs`, `reports/TASK-SOURCE-WORKSPACE-HYGIENE-DIRTY-STATE-CLASSIFICATION-CLOSURE-20260831/`, `services/api/alembic/versions/0037_task_b2_lifecycle_v1_3_formal_publication.py`, `services/api/src/topicpilot_api/lifecycle_formal_publication.py`, `services/api/src/topicpilot_api/live/daily_forward.py`, `services/api/src/topicpilot_api/orm/formal_lifecycle.py`, `services/api/src/topicpilot_api/topic_catalog.py`, `services/api/src/topicpilot_api/topic_catalog_api.py`, `services/api/src/topicpilot_api/topic_catalog_schemas.py`, `services/api/src/topicpilot_api/topic_lifecycle_formal_cli.py`, `services/api/src/topicpilot_api/topic_lifecycle_v1_3_formal.py`, `services/api/tests/test_daily_forward.py`, `services/api/tests/test_lifecycle_v1_3_formal_publication.py`, `services/api/tests/test_topic_catalog.py`, `tools/ws4_bounded_eod_catchup.py`, `tools/ws4_formal_eod_publication.py`.
