# TASK-DATA-020｜V2 Production Formal Data Bootstrap & Reconciliation

**Status:** Historical pre-bootstrap handoff; superseded by §13 post-bootstrap reconciliation
**Scope:** Neon production read-model bootstrap and DB → FastAPI → Sites reconciliation  
**Date:** 2026-08-12  
**Repository:** `Xiezhou0828/topicpilot-platform` (`main`)

## 1. Executive Summary

The repository-side import path is ready and the formal input bundle passes a no-write dry-run. The protected Neon migration credential was not available in this session, so no production write was attempted. The public Render FastAPI and Sites runtime are healthy and correctly fail closed, but the V2 read model is still empty: public topics and stocks both return `total=0`, and formal detail identities are not yet present.

This report deliberately does not claim production data completion. The next safe action is for an authorized operator to run the documented importer with the Neon **direct** migration connection in a protected shell, then perform the DB/API/Sites reconciliation below. No secret should be pasted into chat, committed to GitHub, or printed in logs.

## 2. Scope and Guardrails

In scope:

- Audit the V2 formal importer, input bundle, Alembic configuration, FastAPI runtime, Render container startup, CORS, and public V2 read routes.
- Perform the importer dry-run and record its immutable input evidence.
- Define the protected first import and safe retry procedure.
- Reconcile the currently observable production state without writing to Neon.

Out of scope and unchanged:

- Topic/stock UI design, score/grade, lifecycle, opportunity, recommendation, favorites/watchlist, AI Studio, or `NEXT_TASK`.
- Any destructive database operation (`DROP`, `TRUNCATE`, reset, recreate, volume deletion, or demo bootstrap).
- Render/Neon login or browser provisioning. Render and Neon provisioning were user-confirmed in the preceding infrastructure handoff.

## 3. Current Deployment and Data Boundary

| Layer | Current evidence | Result |
|---|---|---|
| Formal source bundle | `C:\Users\acer\Desktop\題材領航\input` | Present and readable |
| Migration/import code | `infra/scripts/phase3_6_001b_legacy_import.py` and `topicpilot_api.legacy_import` | Audited |
| Public FastAPI | `https://topicpilot-api.onrender.com` | Provisioned and responding |
| API database runtime | `DATABASE_URL` (pooled Neon connection) | Runtime setting, secret not exposed |
| Alembic migration runtime | `MIGRATION_DATABASE_URL` (direct Neon connection, with safe fallback to `DATABASE_URL`) | Required for protected import/DDL |
| Public Sites API boundary | `NEXT_PUBLIC_API_BASE_URL=https://topicpilot-api.onrender.com` | Configured; demo fallback disabled |
| Current V2 read model | Public API response | Empty (`topics=0`, `stocks=0`) |

The production data boundary is formal-only: an unavailable or empty formal API remains unavailable/empty; it does not silently seed or substitute synthetic preview identities.

## 4. Phase 1 — Production Import Preflight

### 4.1 Source and importer audit

The importer reads the approved legacy export files from the private input directory and builds five formal entity batches:

- markets
- instruments
- topics
- topic hierarchy edges
- instrument-topic relations

The writer (`TransactionalV2Writer`) performs one transactional, stable-key upsert run and records import audit metadata. It does not drop, truncate, reset, recreate, or overwrite a row whose stable-key hash conflicts; conflicts fail the run rather than being silently replaced.

The source files used by the current importer are:

- `股票總覽.tsv`
- `股票題材關聯.tsv`
- `approved_topic_hierarchy.tsv`
- `族群資料庫.tsv`

The Docker image copies `fixtures/` for compatibility with existing package layout, but the production command does not import that directory and contains no demo seed/reset path.

### 4.2 Dry-run evidence (no database connection)

The following command was run with a deliberately non-production placeholder URL. It only parses and validates the bundle:

```powershell
$env:PYTHONPATH='services/api/src'
.\\.venv-live\\Scripts\\python.exe infra/scripts/phase3_6_001b_legacy_import.py `
  --input 'C:\\Users\\acer\\Desktop\\題材領航\\input' `
  --database-url 'postgresql+psycopg://not-used-for-dry-run'
```

Result:

```text
records_read = 1594
valid = 1594
rejected = 0
duplicate = 0
conflicts = 0
warnings = 0
critical_blockers = 0
issues = []

markets = 2
instruments = 507
topics = 130
topic_hierarchy = 107
instrument_topic = 848
```

Input artifact hashes recorded by the dry-run:

| Artifact | SHA-256 | Logical rows |
|---|---|---:|
| `股票總覽.tsv` | `25d0b40cc2d5ff58112456c4a307e28309e83c8fcaa266750c7169221031b28f` | 539 |
| `approved_topic_hierarchy.tsv` | `8d7d8174dd1ec2e602b2fd3f8b16a6d83f37fc4e9edf566773347f74806a5b5d` | 107 |
| `股票題材關聯.tsv` | `dfbe9aec146939349740d257d0e06ca490445c64d597e1c340119925cb5c978a` | 848 |
| `族群資料庫.tsv` | `a0deea0902cd68080a767252710af378b57fdb1f78da81651daedcafc526b35c` | 131 |

### 4.3 Schema and readiness preflight

The public service currently passes:

- `GET /healthz` → `200 {"status":"ok"}`
- `GET /readyz` → `200 {"status":"ready"}`
- `GET /openapi.json` → `200`, with six V2 paths including stocks, topics, detail, snapshots, and home
- `GET /api/v1/admin/schema` → `200`, exposing the current V2 SQLAlchemy schema metadata

Alembic reads `MIGRATION_DATABASE_URL` first and otherwise falls back to `DATABASE_URL`; the production Docker command runs `alembic upgrade head` before binding Uvicorn. The current head in the repository is `0024_task_be_007_topic_snapshots`. This startup migration is additive/idempotent and is not a formal data import.

Local process inspection found no `DATABASE_URL` or `MIGRATION_DATABASE_URL` in the current shell. The local `.env` was not used as Neon production authority. No production credential was read, printed, or stored.

## 5. Production Import Procedure (Protected Operator Only)

### 5.1 Credential policy

Set the Neon **direct/unpooled** connection string in `MIGRATION_DATABASE_URL` inside a protected operator shell or Render one-off job. Do not paste it into this chat, a ticket, GitHub, a report, or a command log. The long-lived API should continue to use the Neon pooled connection in `DATABASE_URL`.

### 5.2 First formal import

After the operator has verified the target is the Neon production project and the input hashes above match, run:

```powershell
$env:PYTHONPATH='services/api/src'
python infra/scripts/phase3_6_001b_legacy_import.py `
  --input 'C:\Users\acer\Desktop\題材領航\input' `
  --database-url "$env:MIGRATION_DATABASE_URL" `
  --apply
```

The command must be run once against the intended production database. It uses one transaction and is safe to retry after a clean failure. A successful result must print a run id and domain counts matching the expected formal totals. It must not be replaced with a bootstrap script, fixture import, schema reset, or local database URL.

### 5.3 Normal deploy migration

Normal Render deploys may run the container's existing:

```text
alembic upgrade head && exec uvicorn topicpilot_api.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers
```

This applies repository migrations only. It does not re-run the formal importer. Future formal data refreshes must use the reviewed importer with a new, explicitly approved input artifact and audit run.

## 6. FastAPI Runtime Verification

The application entrypoint is `topicpilot_api.main:app`. Render binds Uvicorn to `0.0.0.0` and Render's `$PORT`; there is no production `localhost:8000` binding. The readiness implementation executes a database `SELECT 1` and returns `ready` only when the service can reach its configured database.

The container image and `render.yaml` agree on:

- Dockerfile: `infra/docker/api.Dockerfile`
- build context: repository root (`.`)
- start: Alembic upgrade, then `topicpilot_api.main:app`
- health path: `/readyz`
- CORS: explicit origins from `TOPICPILOT_CORS_ORIGINS`, credentials disabled

## 7. CORS and Sites Runtime

The production browser origin is allowed explicitly:

```text
https://topicpilot-platform.game0962046460.chatgpt.site
```

An OPTIONS preflight to `/api/v2/topics` returned `200` with the exact `Access-Control-Allow-Origin`, `GET` in allowed methods, no wildcard origin, and no credentials wildcard. The Sites deployment has:

```text
NEXT_PUBLIC_API_BASE_URL=https://topicpilot-api.onrender.com
NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false
```

Browser checks show no CORS error. `/topics` and `/stocks` correctly render formal-only empty states while the read model has no rows; no Preview badge or DEMO row is used as an authority.

## 8. Current DB → API → UI Reconciliation

The public API is the only production observation available without Neon credentials. Current results:

| Check | Current result | Expected after import |
|---|---:|---:|
| `/api/v2/topics?limit=200&offset=0` | `200`, `total=0`, `items=0` | `total=130`, `items=130` |
| `/api/v2/stocks?limit=1000&offset=0` | `200`, `total=0`, `items=0` | `total=507`, `items=507` |
| `/api/v2/stocks/2330` | `404` | `200` |
| `/api/v2/stocks/6806` | `404` | `200`, nullable price allowed |
| `/api/v2/topics/ai-server` | `404` | `200` for an approved topic slug |
| Sites `/topics` | formal empty state, no preview | 130 formal identities |
| Sites `/stocks` | formal empty state, no DEMO rows | 507 formal identities |

The current empty results reconcile with the missing production import; they are not evidence that the private bundle is empty. Direct Neon table counts must be captured by the authorized operator after import. The required post-import database targets are:

```text
markets = 2
instruments = 507
topics = 130
topic_hierarchy_edges = 107
instrument_topic_relations = 848
```

The post-import operator must also verify TPE/TWO membership, identities `2330` and `6806`, no duplicate stable keys, no orphan relations, and no synthetic/demo rows before declaring the chain ready.

## 9. Failure Handling and Safe Retry

If the credential is unavailable, the connection fails, the schema is not at the expected Alembic head, the importer reports conflicts, or the resulting counts are unexpected:

```text
PRODUCTION_IMPORT = NOT_RUN or FAILED
FAILURE_CLASS = credential | connection | schema | validation | conflict | unexpected-state
PRODUCTION_DB_STATE = report the observed state without changing it
SAFE_RETRY = YES only after the cause is corrected and the same input hashes are revalidated
```

Do not reset the database, delete a Neon branch, truncate tables, rerun a demo bootstrap, or make the Render Web Service startup perform the import. A transactionally failed import should leave the existing state unchanged; verify this with the operator's protected database readback before retrying.

## 10. Verification Suites Already Run

- Import dry-run: pass (`1594/1594`, zero errors/warnings/conflicts).
- Backend targeted configuration/database/freeze tests: `10 passed, 1 skipped` (Postgres integration skipped without a test database).
- Backend compile check: pass.
- Frontend formal topic tests: `3 passed`.
- Frontend lint: pass.
- Frontend TypeScript check: pass.
- Frontend production build: pass.
- Public health/OpenAPI/V2/CORS checks: pass for service availability and CORS; data counts remain empty.
- Browser `/topics` and `/stocks` smoke checks: pass for formal-only unavailable/empty behavior; data identities are not yet available.
- `git diff --check`: pass for task files.

The full legacy frontend suite still contains pre-existing failures in unrelated source-contract/rendered-HTML tests. They are not used as evidence of a formal import failure.

## 11. Remaining Issues and Recommended Next Step

Remaining issue: production Neon formal entities have not yet been written. Consequently the V2 public data chain is partial and the requested 130-topic/507-stock UI acceptance cannot yet pass.

Recommended next step: an authorized operator sets `MIGRATION_DATABASE_URL` to the Neon direct connection in a protected shell, runs the exact importer command in §5.2, captures the run id and five table counts, then rechecks the public API and Sites pages. Only after all counts and detail identities reconcile should the production data chain be marked ready and any downstream lifecycle/read-model activation be considered.

## 12. Fixed Final Output

```text
PRODUCTION_IMPORT_PREFLIGHT = PASS
FORMAL_DRY_RUN = PASS
FORMAL_DRY_RUN_RECORDS = 1594
PRODUCTION_MIGRATION_CREDENTIAL = WAITING_FOR_OPERATOR_SECRET
PRODUCTION_FORMAL_IMPORT = NOT_RUN
NEON_MARKETS = 0 (current public readback; expected after import: 2)
NEON_INSTRUMENTS = 0 (current public readback; expected after import: 507)
NEON_TOPICS = 0 (current public readback; expected after import: 130)
NEON_HIERARCHY_EDGES = 0 (no current row evidence; expected after import: 107)
NEON_INSTRUMENT_TOPIC_RELATIONS = 0 (no current row evidence; expected after import: 848)
PUBLIC_FASTAPI_READY = PASS
PUBLIC_FASTAPI_TOPICS = 0
PUBLIC_FASTAPI_STOCKS = 0
PUBLIC_FASTAPI_2330 = FAIL
PUBLIC_FASTAPI_6806 = FAIL
PUBLIC_SITES_TOPICS = FAIL
PUBLIC_SITES_STOCKS = FAIL
PRODUCTION_DEMO_FIXTURE_USED = NO
PRODUCTION_PREVIEW_FALLBACK = REMOVED
DB_API_UI_RECONCILIATION = PARTIAL
V2_PRODUCTION_DATA_CHAIN = PARTIAL
NEXT_TASK_MODIFIED = NO
EXACT_NEXT_USER_ACTION = In a protected operator shell, set MIGRATION_DATABASE_URL to the Neon direct connection without sharing it, run the documented phase3_6 importer against C:\Users\acer\Desktop\題材領航\input, then perform DB/API/Sites reconciliation.
```

## 13. Post-bootstrap reconciliation (2026-08-12)

The user subsequently confirmed that the protected Neon production bootstrap
was completed and manually verified the production `topicpilot` schema. This
is the resolution of the earlier credential/bootstrap gap; the import was not
re-run by this session.

### Production DB evidence

| Table | User-confirmed Neon count | Expected | Result |
|---|---:|---:|---|
| `topicpilot.instruments` | 507 | 507 | PASS |
| `topicpilot.topics` | 130 | 130 | PASS |
| `topicpilot.topic_hierarchy` | 107 | 107 | PASS |
| `topicpilot.instrument_topic_relations` | 848 | 848 | PASS |

The relation table name is confirmed as `topicpilot.instrument_topic_relations`.
The original dry-run evidence remains unchanged: `records_read=1594`,
`valid=1594`, zero rejected/duplicate/conflict/warning records and zero
critical blockers. The operator confirmed that these counts reconcile with
Neon. No destructive bootstrap was performed during this continuation.

### Public FastAPI evidence

Read-only checks against `https://topicpilot-api.onrender.com` now return:

| Request | Result |
|---|---|
| `/healthz` | 200 |
| `/readyz` | 200 |
| `/openapi.json` | 200; V2 list/detail routes present |
| `/api/v2/topics?limit=200&offset=0` | 200; `total=130`, `items=130` |
| `/api/v2/stocks?limit=1000&offset=0` | 200; `total=507`, `items=507` |
| `/api/v2/stocks/2330` | 200; formal identity and topic relations present |
| `/api/v2/stocks/6806` | 200; formal identity present and `price=null` preserved |
| `/api/v2/topics/ASIC` | 200; formal topic identity and 34 constituents present |
| OPTIONS from the Sites origin | 200; exact origin, GET allowed, no wildcard credentials |

The public stock universe contains both `TPE` and `TWO` (314 and 193 rows),
with no `DEMO`/`PREVIEW` identity rows. Stock 2330 exposes the formal ASIC
relation; the topic detail exposes formal constituents. No fixture or browser
synthetic fallback was used for these responses.

### Sites browser evidence

The production Sites environment remains:

```text
NEXT_PUBLIC_API_BASE_URL=https://topicpilot-api.onrender.com
NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false
```

The real production browser now shows:

- `/topics`: formal `130 個題材`, identity rows retained with `—` scores/grades and pending lifecycle data.
- `/stocks`: formal `507/507 檔`, TPE/TWO filters, 2330 visible, no Preview/DEMO rows.
- Stock 2330 drawer: formal detail response, ASIC relation, no Preview badge.
- Topic `/topics/ASIC`: formal API detail, 34 constituents, no synthetic research sections.

One small frontend display defect found during this reconciliation was fixed:
formal topic detail with `dataDate=null` no longer renders the word `Preview`; it
now renders `資料日期待補`. Explicit local preview mode keeps its existing
Preview disclosure. This is a presentation-state correction only.

### Tests and current status

- Backend targeted suite: `15 passed, 1 skipped` (PostgreSQL integration skip is expected without a test DB).
- Frontend lint: PASS.
- Frontend TypeScript check: PASS.
- Frontend production build: PASS.
- Full frontend suite: `55 passed, 13 failed`; the same legacy source-contract/rendered-HTML failures remain unrelated to formal data integration. No test was deleted, skipped, or weakened.

## 14. Current fixed final output

```text
PRODUCTION_IMPORT_PREFLIGHT = PASS
FORMAL_DRY_RUN = PASS
FORMAL_DRY_RUN_RECORDS = 1594
PRODUCTION_MIGRATION_CREDENTIAL = AVAILABLE (operator-completed; secret not exposed here)
PRODUCTION_FORMAL_IMPORT = PASS (user-confirmed)
NEON_MARKETS = 2 (user-confirmed production readback)
NEON_INSTRUMENTS = 507
NEON_TOPICS = 130
NEON_HIERARCHY_EDGES = 107
NEON_INSTRUMENT_TOPIC_RELATIONS = 848
PUBLIC_FASTAPI_READY = PASS
PUBLIC_FASTAPI_TOPICS = 130
PUBLIC_FASTAPI_STOCKS = 507
PUBLIC_FASTAPI_2330 = PASS
PUBLIC_FASTAPI_6806 = PASS
PUBLIC_SITES_TOPICS = PASS
PUBLIC_SITES_STOCKS = PASS
PRODUCTION_DEMO_FIXTURE_USED = NO
PRODUCTION_PREVIEW_FALLBACK = REMOVED
DB_API_UI_RECONCILIATION = PASS
V2_PRODUCTION_DATA_CHAIN = READY
NEXT_TASK_MODIFIED = NO
EXACT_NEXT_USER_ACTION = Keep monitoring formal API freshness; the next feature task may be proposed separately and is not started by this reconciliation.
```

## 15. Implementation / reconciliation close-out

### Previous blocker

The prior blocker was external-state related: Neon/Render access was not
available to the session and the public V2 read model returned zero rows. The
historical reports retain that state and the original `0/130`, `0/507`, and
404 detail evidence.

### Blocker resolution

The user completed the protected Neon production bootstrap and manually
verified the four formal table counts. The existing Render service and Sites
runtime then served the formal read model. This session performed only
read-only API/browser verification and one narrowly scoped formal-display fix;
it did not repeat bootstrap or use a second data path.

### Files changed in this close-out

- `apps/web/app/components/v2/TopicDetailPage.tsx` — formal null data-date
  label changed from `Preview` to `資料日期待補`; explicit local preview is
  unchanged.
- This report and the historical deployment/infrastructure/FE-BE reports were
  appended with post-bootstrap evidence and current fixed outputs.

No database schema, importer, score/grade, lifecycle, opportunity,
recommendation, favorites, watchlist, UI layout, or `NEXT_TASK` was changed.

### Documents updated

- `docs/reports/TASK-DATA-020_V2_PRODUCTION_FORMAL_DATA_BOOTSTRAP_REPORT.md`
- `docs/reports/TASK-DEPLOY-017_PUBLIC_FASTAPI_ORIGIN_AND_V2_SITES_RUNTIME_INTEGRATION.md`
- `docs/reports/TASK-INFRA-019_V2_PRODUCTION_INFRASTRUCTURE_REPORT.md`
- `docs/reports/TASK-INFRA-019_RENDER_MANUAL_PROVISIONING_HANDOFF.md`
- `docs/reports/TASK-FE-BE-014_TOPIC_CATALOG_FULL_IMPORT_AND_TOPICS_FORMAL_INTEGRATION.md`
- `docs/reports/TASK-FE-BE-015_STOCK_UNIVERSE_FULL_IMPORT_AND_STOCKS_FORMAL_INTEGRATION.md`
- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`

### Remaining known issues

- Formal optional evidence remains nullable by design: scores/grades,
  lifecycle, prices such as 6806, technical evidence, and institution fields
  must remain pending rather than inferred.
- The existing full frontend suite has 13 unrelated source-contract/
  rendered-HTML failures (`55 passed, 13 failed`); no test was weakened.
- Render Cron ownership, private Taishin runtime, protected GitHub deployment
  environments, and backup/restore evidence remain separate infrastructure
  follow-ups.

### Risks / technical debt

- A future deployment must preserve `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false`
  and the exact Render API origin.
- Production data refreshes need a reviewed artifact/import audit; Web Service
  startup must remain migration-only and demo-free.
- The React production bundle still emits an existing minified hydration
  warning (#418) during browser smoke tests; it did not block formal API data
  or create a CORS error and is outside this data bootstrap scope.

### Final status

**PASS — Production formal data bootstrap and DB → FastAPI → Sites
reconciliation are complete.** The historical blocked state is resolved; no
new parallel production architecture was introduced.

### Suggested NEXT_TASK (proposal only)

Evaluate the separate operational follow-up for formal data freshness and
protected deployment/backup ownership. This is a suggestion only; no next task
was started or selected here.
