# WS1 L1.2 Generated API Client `dataStatus` Contract Reconciliation

## Result

- `PROMOTION=YES`
- `CANONICAL_FORWARD_SHADOW_RUNTIME_READY=YES`
- L1.2 blocker `GENERATED_API_CLIENT_DATASTATUS_CONTRACT_DRIFT=RESOLVED`
- No Lifecycle threshold, five-stage semantic, Strength, WS2, WS3, WS4, or `NEXT_TASK` change was made by L1.2.

## Canonical source-of-truth

`services/api/src/topicpilot_api/schemas.py` is authoritative for `HomeMarketOverview.dataStatus`. The runtime read model emits only `PARTIAL` and `UNAVAILABLE`; the field is therefore represented as `Literal["PARTIAL", "UNAVAILABLE"]` with the JSON alias `dataStatus`.

The same contract is now synchronized across:

1. FastAPI/Pydantic model and generated OpenAPI.
2. `packages/api-client/src/schema.d.ts` and `packages/api-client/openapi.json`.
3. `apps/web/app/lib/generated-api.d.ts` and the existing frontend consumer.

The frontend consumer was not weakened to `string`; it now type-checks against the generated finite union. `today-home.ts` required no semantic change.

## Evidence and tests

- OpenAPI regeneration completed and the `HomeMarketOverview.dataStatus` enum is exactly `PARTIAL | UNAVAILABLE`.
- Added regression test: `services/api/tests/test_home_status_contract.py`.
- Full frontend TypeScript: PASS.
- API contract/read-model/lifecycle regression suite: 16 passed, 1 skipped because PostgreSQL integration requires `TEST_DATABASE_URL` or `DATABASE_URL`.
- API client tests: 3 passed.
- Related frontend tests: 34 passed.
- Canonical collision-aware reconciliation: PASS. Non-Owner paths applied cleanly; both Owner overlap files passed targeted merge checks and their final content hashes match the candidate.

## Promotion and preservation

- Isolated candidate implementation commit: `336735fe4cfc4a74207660d9f1bd19e11947827b`.
- Runtime promotion commit: `5c2f304aed483c1d5a55d6d37cec392ab2a0b61c`.
- The Owner changes in `apps/web/app/components/v2/TopicListPage.tsx` and `apps/web/app/lib/topic-api.ts` were retained through targeted reconciliation; no reset, clean, or overwrite operation was used.
- Other canonical dirty/untracked files were not staged or committed.

## Remaining blocker

No L1.2 promotion blocker remains. The PostgreSQL integration skip is an environment-dependent test limitation, not a contract or promotion failure.
