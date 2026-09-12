# Production Release Convergence | WS-B Topic Catalog — PASS

Date: 2026-09-10 (Asia/Taipei)

```text
TASK=Production Release Convergence for WS-B Topic Catalog
SOURCE_BRANCH=codex/release-convergence-wsb-20260910
PRODUCTION_SOURCE_BRANCH=codex/a10-batch-speed-20260908
PRODUCTION_REVISION_BEFORE=2f705c83edd768c68ef9d4f389e5f0fec2820acc
A10_BASE_SHA=ea564bb15adbf053f9a9022d9043dd5ca389bc29
B2_SCHEMA_BASELINE_SOURCE_SHA=d27981a7f9369762a31ecb06f3ab9c8b23a62ba3
WSB_SOURCE_SHA=4bdbffeaf64279ce751eb4afb12dc15c7d9df9d9
B2_SCHEMA_RECONCILED_SHA=1263d80
WSB_RECONCILED_SHA=163723a
EXACT_SHA_AFTER=74226c387ff36bf328936da0bd12114c2773d9e3
DEPLOYED_SHA=74226c387ff36bf328936da0bd12114c2773d9e3
DEPLOY_WORKFLOW_RUN=34439186917

RELEASE_CONVERGENCE_DEPLOYED=PASS
PRODUCTION_TOPIC_CATALOG_ROUTES=4/4
PRODUCTION_TOPIC_CATALOG_ROOT_NOT_404=PASS
PRODUCTION_TOPIC_CATALOG_PARENT_LEAF=PASS
PRODUCTION_TOPIC_CATALOG_FORMAL_CURRENT_READBACK=PASS
PRODUCTION_TOPIC_CATALOG_HISTORY_READBACK=PASS
PRODUCTION_OPENAPI_CONTRACT=PASS_45_OF_45
A10_SCHEDULER_REGRESSION=PASS
PRODUCTION_FINAL_SCHEDULE=15:00_ASIA_TAIPEI
PRODUCTION_FINAL_SCHEDULE_ACTIVE_READBACK=PASS_PRESERVED_A10_WORKER_READBACK
LATEST_FORMAL_EOD_DATE=2026-09-09
LATEST_FORMAL_TOPIC_SNAPSHOT_DATE=2026-09-09
PRODUCTION_HEALTH=PASS
F9_RELEASE_BOUNDARY_RESOLVED=YES
C_DRIVE_ARTIFACTS_CREATED=0
```

## Release decision

Production previously ran `2f705c83...`, while the repaired daily scheduler
was on the descendant A10 branch at `ea564bb...` and WS-B was on the divergent
commercial-integration branch at `4bdbffe...`. Deploying WS-B directly would
have omitted the A10 repair. The release candidate therefore started at the
deployed A10 repair and commit-preservingly applied the B2 publication schema
baseline and WS-B Topic Catalog. One narrow integration commit regenerated the
combined OpenAPI/types and added the already-committed four client methods.

The combined contract has 45 paths rather than F9's 44: the A10/Production
line has the read-only `/api/v1/admin/migration` route, and WS-B adds four
Topic Catalog routes. Runtime OpenAPI exactly equals the saved 45-path
contract. This is a legitimate baseline advance, not unexplained drift.

The candidate was fast-forward pushed to the Render service's configured
source branch. Protected GitHub workflow run `34439186917` completed
successfully and triggered the service-scoped deployment hook. `/healthz` and
`/readyz` subsequently reported exact SHA `74226c3...`.

## Production readback

- OpenAPI exposes all four `/api/v2/topic-catalog` routes, 4/4 within 45/45.
- Root catalog is HTTP 200 with 130 entries; it is no longer route-level 404.
- Parent `AI視覺` returns HTTP 200 with member/current/history state
  `NOT_APPLICABLE`.
- Leaf `12 吋矽晶圓` returns HTTP 200, members `AVAILABLE`, current formal
  snapshot `AVAILABLE`, and formal history `AVAILABLE` with six rows.
- Formal stock EOD remains at trading date 2026-09-09.
- Formal Topic Snapshot remains `FORMAL`, `PIT_FORMAL`, `FINAL`, `PUBLISHED`
  at snapshot date 2026-09-09.
- Home remains HTTP 200 with `asOf=2026-09-09`.

The API deploy hook targets only the web service. It did not redeploy or alter
the independent `topicpilot-live` worker or its environment. The latest A10
worker evidence remains the active readback owner: revision `ea564bb...`,
`TOPICPILOT_LIVE_POST_CLOSE_START=15:00`, `timezoneName=Asia/Taipei`, startup
readback 15:00, and a valid scheduler WAIT decision after restoration. The
combined candidate contains that exact repair and passed its scheduler/runner
regression set. No scheduler, environment, or Production data mutation was
performed during release convergence.

## Validation

- Focused WS-B, A10 scheduler/runner, Home, Topic, Stock, Technical, and
  Lifecycle backend contracts: 108 passed, 1 skipped, 0 failed. The skipped
  Home integration requires an explicit PostgreSQL test URL and is not counted
  as PASS.
- Direct WS-B Topic Catalog tests: 7/7 passed within the focused run.
- API client: 4/4 passed, including all four Topic Catalog calls.
- Runtime/saved OpenAPI parity: exact equality, 45/45; Topic Catalog 4/4.
- Generated TypeScript declarations: reproducible from the saved contract.
- Python compile and Ruff touched scope: PASS.
- Compose/Render configuration validation: PASS.
- `git diff --check` and staged-diff check: PASS.
- Prior comparable F9 backend scope was 64 passed and one skipped; the 108-test
  release scope is broader because it includes the A10 scheduler/runner and
  persistence regression set. No test-count reduction occurred.

## Preservation and mutation boundary

The shared canonical working tree's pre-existing owner/frontend/A10/B2 dirty
and untracked files were not staged, reset, cleaned, checked out, overwritten,
or stashed. Release work used the existing clean A10 worktree; its pre-existing
untracked `.venv-a10/` remained untracked. The only remote mutation was the
authorized fast-forward push and protected API deployment. No Production data,
worker schedule, frontend deployment, taxonomy, `NEXT_TASK`, B3, or B4 state
was changed.
