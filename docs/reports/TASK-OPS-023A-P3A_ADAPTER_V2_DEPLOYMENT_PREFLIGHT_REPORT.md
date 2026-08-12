# TASK-OPS-023A-P3A｜Adapter-v2 Production Deployment Preflight & Canary #2 Operator Handoff

**Date:** 2026-08-12 (Asia/Taipei)
**Generation:** `NEXT / V2`
**Scope:** repository-side deployment provenance, read-only reference preflight,
operator runbook, and Canary #2 gate handoff
**Production deployment / write:** not performed
**Scheduler:** not authorized and unchanged

## 1. Executive Summary

`TASK-OPS-023A-P3A` is complete as an operator handoff package. FIX01A's
adapter-v2 implementation is present in the worktree, its deployment path is
traceable, a secret-free provider-lineage check is available, and a SELECT-only
`tw-reference-v1` preflight is available for the protected runtime.

The package stops before Production deployment and Canary #2. The current
branch is `main` at HEAD `e333ed3`, while the adapter-v2/P3A changes remain
uncommitted worktree changes. The checked-in release workflow requires a
committed `release_ref`; therefore no claim is made that the current adapter
code is deployed to Render.

## 2. FIX01A Verification

| Requirement | Result | Evidence |
|---|---|---|
| TWSE market-level one-date parser | PASS | `TwseOfficialDailyProvider._fetch_market_day()` / `MI_INDEX` |
| TPEx market-level one-date parser | PASS | `TpexOfficialDailyProvider._fetch_market_day()` / `dailyQuotes` |
| Single-date post-close batching | PASS | `PostCloseUpdater` passes `market_batch=True` |
| Shared adapter cache | PASS | one market response indexed by exact symbol |
| Multi-day fallback | PASS | existing instrument/month path remains for historical windows |
| Date validation | PASS | `PROVIDER_DATE_MISMATCH` |
| Table/duplicate validation | PASS | deterministic missing-table and duplicate-row checks |
| Missing markers | PASS | `---` and other markers remain null, never zero |
| 6806 | PASS | no row becomes `EXCHANGE_CONFIRMED_NO_DATA`, no fake bar |
| Authority | PASS | TPE→TWSE; TWO→TPEx; Yahoo verification-only; Taishin intraday-only |

## 3. Adapter-v2 Files / Versions

| Component | Location | Version / role |
|---|---|---|
| TWSE official daily | `services/api/src/topicpilot_api/market_data/exchange.py` | `twse-official-daily.v2` |
| TPEx official daily | same adapter module | `tpex-official-daily.v2` |
| Historical registry | `services/api/src/topicpilot_api/market_data/registry.py` | canonical TPE/TWO ownership; Yahoo verification-only |
| Post-close route | `services/api/src/topicpilot_api/live/post_close.py` | one-date `market_batch=True` |
| Provider lineage | `services/api/src/topicpilot_api/market_data/lineage.py` | secret-free runtime provenance |
| Provider CLI | `services/api/src/topicpilot_api/provider_lineage_cli.py` | `topicpilot-provider-lineage` |
| Reference preflight | `services/api/src/topicpilot_api/reference_check.py` | SELECT-only evaluator/ORM reader |
| Reference CLI | `services/api/src/topicpilot_api/reference_cli.py` | `topicpilot-reference-check` |

The local lineage command produced `status=READY`, both adapter-v2 versions,
`marketBatch=true`, and unchanged source roles. It performed no provider HTTP
request and no database access.

## 4. Regression Results

The new P3A and FIX01A focused suite passed:

```text
tests/test_deployment_preflight.py
tests/test_no_trade_contract.py
tests/test_v2_provider_registry.py
15 passed

FIX01A/P3A plus rate-limit, daily-market, historical, live-history,
orchestrator, and live-provider regressions: 40 passed
```

The new P3A files also passed targeted Ruff check, Ruff format check, and Python
`compileall`. The full backend suite remains subject to the repository's
existing PostgreSQL/environment skips and unrelated pre-existing warnings;
the release workflow remains the authoritative CI/build gate.

The older FIX01A files retain their repository line-ending convention and were
not bulk reformatted; changing them would create unrelated whitespace churn.

## 5. Deployment Architecture

The intended runtime is:

```text
GitHub release_ref (committed revision)
  -> Render build context = repository root
  -> infra/docker/api.Dockerfile
  -> COPY services/api/ /app/
  -> pip install . (services/api/pyproject.toml)
  -> topicpilot-live console script
  -> Render worker: alembic upgrade head && exec topicpilot-live
  -> PostCloseUpdater
  -> official adapter-v2
```

The API web service uses the same image and starts Uvicorn after the same
Alembic command. `render.yaml` defines both services with
`autoDeployTrigger: off`; the protected GitHub workflow may trigger the API
deploy hook only with the `production-api` environment.

## 6. Deployment Artifact Trace

| Trace link | Result | Evidence |
|---|---|---|
| Render context → Dockerfile | PASS | `render.yaml` uses `dockerContext: .`, `infra/docker/api.Dockerfile` |
| Dockerfile → adapter source | PASS | `COPY services/api/ /app/` includes `src/topicpilot_api/market_data` |
| Package → CLI | PASS | `pyproject.toml` defines `topicpilot-live`, provider-lineage, reference-check scripts |
| Worker → post-close | PASS | `dockerCommand` invokes `topicpilot-live`; CLI builds `PostCloseUpdater` |
| Post-close → adapter-v2 | PASS | registry `market_batch=True`; lineage reports both v2 adapters |
| Current worktree → deployed artifact | NOT YET | GitHub workflow checks out committed `release_ref`; current changes are uncommitted |

`git branch --show-current` is `main`; current HEAD is `e333ed3`. A production
operator must publish a reviewed committed revision containing these files
before deployment. No commit, push, Render deploy hook, or external deployment
control-plane action was performed by P3A.

## 7. Production Version Verification Method

Before Canary #2, the operator should run `topicpilot-provider-lineage` in the
same protected image/runtime used by the worker:

The response is secret-free and must show:

```text
TWSE_OFFICIAL_DAILY = twse-official-daily.v2, marketBatch=true
TPEX_OFFICIAL_DAILY = tpex-official-daily.v2, marketBatch=true
TPE authority = TWSE_OFFICIAL_DAILY
TWO authority = TPEX_OFFICIAL_DAILY
```

The optional `buildSha` is sourced from `RENDER_GIT_COMMIT` or `GIT_SHA` when
available. A missing SHA is reported as null and must be checked against the
operator's release record rather than guessed.

## 8. `tw-reference-v1` Architecture

`tw-reference-v1` is the `reference_data_version` passed to
`NormalizationRuntime`. `DatabaseReferenceContextLoader` requires exactly one
active `ReferenceRegistrySet` for that version, exactly one requested currency,
timezone, and session/calendar, plus non-empty trading-status and adjustment
catalogues. Any missing, duplicate, inactive, or mismatched item raises a
fail-closed `RuntimeLoadError`; ingestion maps that independent condition to
`REFERENCE_DATA_UNAVAILABLE`.

The versioned reference registry contains:

- `reference_registry_sets`;
- `reference_currencies`;
- `reference_timezones`;
- `reference_sessions`;
- `reference_trading_statuses`;
- `reference_adjustments`.

Markets and instruments are not reference-catalogue rows. They are formal
identity rows in `topicpilot.markets` and `topicpilot.instruments`, joined by
the existing market/instrument model. Topics, hierarchy, and
instrument-topic relations are also outside `tw-reference-v1`.

The normalizer therefore needs both: a complete active versioned context and a
valid active formal identity row with currency/timezone/calendar. Without
attempt-level evidence, P3A does not claim that the first 507/0 run was caused
by reference incompleteness; it only confirms the independent failure path.

## 9. Reference Preflight Tool

`topicpilot-reference-check` is read-only. It derives expected daily markets
from non-verification registrations and counts active `EQUITY` instruments
from the formal identity tables. It reports:

```text
referenceVersion
referenceActive
marketCount
instrumentCount
missingMarkets
missingInstruments
duplicateIdentities
missingReferenceContexts
tradingStatusCatalogueCount
adjustmentCatalogueCount
referenceLoadStatus
```

The expected protected Production result is `tw-reference-v1`, `ACTIVE`, two
markets, the current formal instrument count (currently 507), no missing or
duplicate identities, and `referenceLoadStatus=READY`. The count is derived
at runtime; 507 is not embedded as a business-rule constant.

The command does not bootstrap, seed, repair, change active status, migrate,
write, or contact an exchange. It should be run with the protected
Production `DATABASE_URL`; do not paste the secret into chat or the repository.

## 10. 6806 No-data Contract

The existing DATA-022A contract treats an official exchange-confirmed no-row as
covered but unpriced. For 6806 this means:

```text
status = EXCHANGE_CONFIRMED_NO_DATA
close/open/high/low/volume = NULL
covered = true
priced = false
```

It must not be zero-filled, forward-filled, deleted from the identity domain,
or converted into a fake daily bar. If the protected reconciliation does not
recognize this approved status, the operator must stop and request a PM
decision; P3A does not widen the policy.

## 11. Canary #2 Gate Matrix

| Gate | Required evidence | P3A state | If missing |
|---|---|---|---|
| G0 Adapter deployment | Runtime lineage shows both adapter-v2 versions | OPERATOR_REQUIRED | STOP |
| G1 Reference context | `tw-reference-v1`, active, complete, `READY` | OPERATOR_REQUIRED | STOP |
| G2 Provider preflight | Official TWSE/TPEx reachable and target date available | OPERATOR_REQUIRED | STOP |
| G3 6806 semantics | Existing approved no-data contract or PM decision | READY (repository contract) / operator verify | STOP |
| G4 Authorization | Explicit one-shot Production Canary authorization | OPERATOR_REQUIRED | STOP |

Only G0–G4 together permit the operator to run Canary #2. Scheduler
authorization is not included.

## 12. Operator Deployment Checklist

- [ ] Review FIX01A/P3A files and publish a committed release revision.
- [ ] Run release CI against that exact revision.
- [ ] Confirm `0024 → 0025 → 0026 → 0027` migration lineage; no P3A migration is needed.
- [ ] Deploy through the protected Render workflow only.
- [ ] Confirm runtime `/readyz` and provider-lineage output.
- [ ] Keep Scheduler disabled.

## 13. Operator Reference Check

From the deployed worker image/protected runtime:

```console
topicpilot-reference-check
```

Require `referenceLoadStatus=READY`, `referenceVersion=tw-reference-v1`,
active registry, complete session/calendar/currency/timezone/status/adjustment
catalogues, active TPE/TWO markets, and zero missing/duplicate identities.
Do not run this command against the local default URL and interpret its result
as Production evidence.

## 14. Canary #2 Command

Prepare but do not execute under P3A:

```console
topicpilot-live --mode post-close --once --run-date 2026-08-12
```

Use the protected runner's documented wrapper if it differs. No Neon secret is
required in chat or the repository.

## 15. Post-Canary Verification

After separate operator authorization and a successful POST_CLOSE run, verify
in this order:

1. POST_CLOSE status, 507 requested identities, provider outcomes, priced,
   approved no-price, unexplained failures, date and duplicate diagnostics.
2. Daily reconciliation `READY`, trade date `2026-08-12`, expected coverage,
   `coveredCount=expectedCount`, zero unexplained/wrong-date/duplicate counts,
   and `downstreamReady=true`.
3. Topic Snapshot with the same date and formal 130-topic coverage.
4. Lifecycle `evaluation_mode=SHADOW` only after Snapshot succeeds.
5. Stop. Do not enable Scheduler.

## 16. Scheduler Boundary

Scheduler remains `NOT AUTHORIZED`. No Render Cron, Windows Task Scheduler,
worker schedule activation, or automatic daily execution was added or enabled.
Canary #2 success would not authorize it.

## 17. Production Actions NOT Performed

- no adapter-v2 Production deployment;
- no protected `tw-reference-v1` readback;
- no Production Canary #2;
- no Neon write, migration, bootstrap, seed, or reference mutation;
- no Topic Snapshot or Lifecycle SHADOW execution;
- no Scheduler or Render Cron activation;
- no provider-authority, identity, topic, hierarchy, relation, or NEXT_TASK change.

The Docker daemon was unavailable in this AI environment, so a container image
build could not be executed. `docker compose config --quiet`, source/package
compile, provider-lineage, tests, Ruff, and formatting checks passed; the
protected release CI remains the authoritative container-build gate.

## 18. Remaining Operator Actions

1. Publish a reviewed committed revision containing FIX01A/P3A.
2. Deploy that revision through the protected Render workflow.
3. Verify provider lineage in the deployed runtime (G0).
4. Run the SELECT-only reference preflight in protected Production (G1).
5. Verify official endpoints and 6806 policy (G2/G3).
6. Obtain explicit one-shot Canary #2 authorization (G4).
7. Run the command and follow the post-Canary sequence; stop before Scheduler.

## 19. Suggested Next Step

`TASK-OPS-023A-P3A` stops at `OPERATOR_HANDOFF_READY`. The next operator-owned
step is to publish and deploy the reviewed adapter-v2 revision, then return
the provider-lineage and reference-preflight evidence. Do not start Canary #2
from this repository without separate explicit authorization.

## Fixed Completion Fields

```text
TASK_OPS_023A_P3A = COMPLETE
ADAPTER_V2_WORKTREE = PASS
TWSE_ADAPTER_VERSION = twse-official-daily.v2
TPEX_ADAPTER_VERSION = tpex-official-daily.v2
MARKET_BATCH = PASS
HISTORICAL_FALLBACK_PRESERVED = YES
PROVIDER_AUTHORITY_UNCHANGED = YES
ADAPTER_V2_TESTS = PASS (15 focused; 40 relevant current run)
RUFF = PASS
BUILD = NOT_VERIFIED (Docker daemon unavailable; Compose config/static trace PASS)
MIGRATION_REQUIRED = NO
DEPLOYMENT_ARTIFACT_TRACE = PASS (repository-to-runtime mechanism; committed release still required)
PRODUCTION_VERSION_CHECK = READY (tool available; Production readback pending)
TW_REFERENCE_V1_AUDIT = PASS (repository architecture/runtime contract)
REFERENCE_PREFLIGHT_TOOL = READY
PRODUCTION_REFERENCE_CHECK = OPERATOR_REQUIRED
6806_POLICY = PASS (existing DATA-022A contract)
CANARY_2_GATE_MATRIX = READY
CANARY_2_RUNBOOK = READY
PRODUCTION_DEPLOYMENT = OPERATOR_REQUIRED
PRODUCTION_CANARY_2 = NOT_RUN
PRODUCTION_DB_WRITE = NO
PRODUCTION_MIGRATION = NO
SCHEDULER_CHANGED = NO
LIFECYCLE_PRODUCTION = NO
OPPORTUNITY_PRODUCTION = NO
NEXT_TASK_MODIFIED = NO
OPERATOR_HANDOFF_READY = YES
```
