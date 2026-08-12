# TASK-OPS-023 | V2 Daily Close Production Activation & First-Run Reconciliation

**Date:** 2026-08-12
**Production origin:** `https://topicpilot-api.onrender.com`
**Overall result:** `WAITING_FOR_OPERATOR`
**Production writes:** none performed

## 1. Executive Summary

TASK-DATA-022 and TASK-DATA-022A are repository-side ready in this worktree:
official TPE/TWO daily sources, canonical observations, status-aware no-trade
coverage, stable idempotency keys, reconciliation, and the manual post-close
CLI are implemented and tested.

TASK-OPS-023 cannot be promoted to production from this environment. Protected
Neon migration access, production `DATABASE_URL`, Render control-plane
permission, and an approved production scheduler owner are unavailable. No
Neon migration, 507-instrument canary, topic snapshot write, Lifecycle shadow
evaluation, or scheduler activation was attempted.

Read-only public preflight confirmed: markets 2, instruments 507, topics 130,
and instrument-topic relations 848. It also showed `/healthz=200`,
`/readyz=200`, live status `NO_RUN`, and zero topic snapshots. Identity totals
alone are not daily market readiness evidence.

## 2. Production Preflight

### Repository

| Check | Result | Evidence |
|---|---|---|
| Alembic head | PASS | `0027_task_be_021_topic_lifecycle_results` |
| Combined lineage | PASS (repository) | 0024 -> 0025 -> 0026 -> 0027 |
| Combined offline migrations | PASS | additive daily/no-trade/lifecycle objects; no table drop/bootstrap |
| Manual CLI | PASS | `topicpilot-live --mode post-close --once --run-date YYYY-MM-DD` |
| Daily authority | PASS | TWSE official TPE; TPEx official TWO |
| No-trade contract | PASS | covered != priced; approved rows retain null OHLCV |
| Lifecycle algorithm changed | NO | no Lifecycle algorithm files changed by OPS-023 |

### Public production

| Check | Result | Evidence |
|---|---|---|
| Render `/healthz` | PASS | HTTP 200, `status=ok` |
| Render `/readyz` | PASS | HTTP 200, `status=ready` |
| Markets | PASS | `/api/v1/admin/markets?limit=200` total 2 |
| Instruments | PASS | `/api/v1/admin/instruments?limit=1` total 507 |
| Topics | PASS | `/api/v1/admin/topics?limit=1` total 130 |
| Relations | PASS | `/api/v1/admin/relations?limit=1` total 848 |
| V2 topics | PASS | `/api/v2/topics?limit=1` total 130 |
| V2 stocks | PASS | `/api/v2/stocks?limit=1` total 507 |
| Live run | NOT READY | `/api/v1/operations/live/status` = `NO_RUN` |
| Latest snapshot | NOT READY | `/api/v2/topic-snapshots?latest=true` total 0 |
| Production Alembic revision | NOT VERIFIED | no public revision endpoint; Neon unavailable |
| Production secrets | BLOCKED | local `DATABASE_URL`/`MIGRATION_DATABASE_URL` absent |
| Render control plane | BLOCKED | no Render API key/service permission |

The public OpenAPI description still says the deployment contains synthetic
data only. That wording and null observation fields are retained as a
readiness warning; formal identity totals do not satisfy the daily gate.

## 3. Migration Result

**`PRODUCTION_MIGRATION_0027 = NOT_RUN`**

Offline generation passed for the combined line. Migrations 0025 and 0026 create
the daily and no-trade contracts, and additive migration 0027 creates
`topicpilot.topic_lifecycle_results`; no identity table, canonical observation,
or existing data is dropped or bootstrapped. The historical 0025 collision was
resolved repository-side by renumbering the Lifecycle migration to 0027 with
`down_revision=0026`. Production activation still requires protected Neon
access and an approved release window; no production migration was run here.

Applying it requires protected direct Neon access (`MIGRATION_DATABASE_URL`) and
an approved release window. No secret was printed, copied, created, or
requested by this task.

## 4. Canary Date

**`CANARY_TRADE_DATE = NONE`**

No production canary date was selected because a canary performs Neon writes and
requires protected authorization. The authorized command is:

```console
topicpilot-live --mode post-close --once --run-date YYYY-MM-DD
```

The date must be a Taiwan exchange trading date. A weekend/configured closed
date must produce `MARKET_CLOSED` and no topic snapshot.

## 5. Canary Run Result

**`MANUAL_POST_CLOSE_CANARY = NOT_RUN`**

The public live status reports `NO_RUN`, `requested=0`, and no provider
attempts. This is a direct read-only observation, not a simulated canary. The
local CLI cannot open a production repository without `DATABASE_URL`.

## 6. TPE/TWO Coverage

The expected universe is derived from production identity, not hard-coded:

`expectedCount = 507`; per-market expected counts must be read from the
production universe during the canary.

The public preflight exposes no post-close reconciliation readback. Therefore
requested, success, failure, skipped, retry, observed, priced, covered,
unavailable, unexplained, wrong-date, duplicate, and coverage values are all
`NONE`. No 507-instrument daily coverage claim is made.

## 7. No-Trade Cases

| Status | Covered | Priced | Close/OHLCV |
|---|---:|---:|---|
| `AVAILABLE` | Yes | Yes | official values |
| `SUSPENDED` | Yes | No | all null |
| `NO_TRADE` | Yes | No | all null |
| `EXCHANGE_CONFIRMED_NO_DATA` | Yes | No | all null |
| `UNKNOWN` | No | No | unresolved/missing |

Readiness requires `coveredCount == expectedCount`,
`unexplainedMissingCount == 0`, `wrongDateCount == 0`, and
`duplicateKeyCount == 0`:

`506 priced + 1 approved no-trade = 507 covered = READY`
`506 priced + 1 unknown missing = 506 covered = PARTIAL`

No production instrument was verified as `EXCHANGE_CONFIRMED_NO_DATA` in this
task. Provider failure must not be reclassified as no-trade.

The public edge-case read for `/api/v2/stocks/6806` returned HTTP 200 with
`price=null`, `observedAt=null`, and a pending market status. This confirms the
identity exists, but it is not exchange-confirmed no-trade evidence and cannot
be counted as covered by the production gate.

## 8. Daily Reconciliation

**`DAILY_RECONCILIATION = NOT_RUN`**

The local gate in `daily_market.py` is consumed by `PostCloseUpdater` before
the topic snapshot call. A canary must capture `READY`, 100% coverage,
`coveredCount=expectedCount`, zero unexplained/date/duplicate errors, and
`downstreamReady=true`. Until those values are observed from a protected
production run, downstream processing remains blocked.

## 9. Topic Snapshot Result

**`TOPIC_SNAPSHOT = NOT_RUN`**
**`TOPIC_SNAPSHOT_DATE = NONE`**

`/api/v2/topic-snapshots?latest=true&limit=1` returns an empty page (`total=0`).
The repository `TopicSnapshotEngine` writes only `topicpilot.topic_snapshots`,
does not invent scores, and never turns missing prices into zero. It may run
only after the daily gate is `READY` and must verify date, 130-topic coverage,
as-of relations, no Preview/Demo fallback, and null no-trade prices.

## 10. Lifecycle Shadow Handoff

**`LIFECYCLE_SHADOW_HANDOFF = NOT_RUN`**
**`LIFECYCLE_PRODUCTION_ACTIVATION = NO`**

The public V2 topic response reports lifecycle `dataStatus=NOT_AVAILABLE`, no
current stage, and no history. A parallel lifecycle worktree was audited
read-only at
`C:\Users\acer\Documents\Codex\2026-08-09\referenced-chatgpt-conversation-this-is-an-13\work\TopicPilot-v2-task-be-021`.
It contains the authoritative lifecycle spec and integration report. Its
markers are `LIFECYCLE_ENGINE=PASS`, state machine/explainability/API/frontend
integration `PASS`, historical replay `BLOCKED_BY_DATA`, and production
activation `WAITING_FOR_FORMAL_OBSERVATIONS`. The implementation is now
integrated into the repository candidate by TASK-OPS-023A-P1, but it remains
undeployed and data-gated, so it does not constitute a production shadow
handoff.

The permitted sequence is:

`daily market READY -> topic snapshot verified -> Lifecycle evaluation_mode=SHADOW`

No Lifecycle algorithm, threshold, state machine, or production activation was
changed or invoked by OPS-023.

## 11. FastAPI Reconciliation

| Endpoint | Result |
|---|---|
| `/healthz` | 200 / `ok` |
| `/readyz` | 200 / `ready` |
| `/api/v2/topics?limit=1` | 200 / total 130, data date null |
| `/api/v2/stocks?limit=1` | 200 / total 507, price/date null |
| `/api/v2/topic-snapshots?latest=true&limit=1` | 200 / total 0 |
| `/api/v1/operations/live/status` | 200 / `NO_RUN`, no attempts |
| `/api/v1/operations/live/configuration` | 200 / Asia/Taipei, 09:00-13:30, max retries 2 |

The old `/api/v1/meta/data-status` and `/api/v1/snapshot/latest` routes return
404 on the current public deployment. `/api/v1/admin/dashboard` returns 500;
both are operator follow-ups, not activation evidence.

## 12. Scheduler Architecture

`render.yaml` defines a web service and a long-running `topicpilot-live` worker,
both with `autoDeployTrigger: off`; it defines no Render Cron. The worker
command is:

```console
alembic upgrade head && exec topicpilot-live
```

The portable scheduler can run from Render Worker, Windows Task Scheduler,
GitHub Actions, or another explicitly approved owner, but one production owner
must be selected.

```text
PRODUCTION_SCHEDULER_OWNER = UNDECIDED
PRODUCTION_SCHEDULER_IMPLEMENTATION = PARTIAL
PRODUCTION_1440_SCHEDULE = WAITING/BLOCKED
```

## 13. Trading-Day Calendar

`MarketSessionClock` supports weekends and configured closed dates, but the
public configuration has `closedDates=[]`. No operator-approved Taiwan
exchange holiday catalogue is present in the repository. Unattended production
scheduling therefore cannot be marked ready.

## 14. Retry Policy

The repository configuration exposes bounded retry (`maxRetries=2`) and records
actual retry counts in post-close metadata:

`14:40 initial -> bounded provider retry window -> exact-key reconciliation`

Retries preserve `market_code:instrument_code:trade_date` and canonical
idempotency. They must not zero-fill, forward-fill, drop unresolved rows, or
reinterpret provider failure as no-trade.

## 15. Backfill

The authorized recovery command is:

```console
topicpilot-live --mode post-close --once --run-date YYYY-MM-DD
```

Backfill uses the same canonical raw/timeline/observation path and is not a
delete-then-reinsert operation. No production backfill was run.

## 16. Monitoring

The first production run must retain run id, trade date, start/end, requested,
success, failure, skipped, retry, provider status, observed/priced/covered/
unavailable/unexplained counts, wrong-date/duplicate counts, reconciliation
status, `downstreamReady`, latest canonical date, and latest snapshot date.

The public live endpoint currently provides `NO_RUN` and zero attempt counts.
No production alert or scheduler notification was provisioned.

## 17. Tests

Available repository evidence:

- combined DATA-022/022A + BE-021/BE-021A backend suite: **53 passed, 1 skipped**;
- Lifecycle targeted suite: **25 passed** (included in the combined run);
- targeted Ruff checks for changed implementation/tests: **PASS**;
- broad Ruff: **legacy E501 findings remain in `production_read_model.py` and
  `schemas.py`; no functional test failure**;
- Alembic 0027 offline SQL generation and single-head check: **PASS**;
- Python compileall for API `src` and `tests`: **PASS**.

Activation-specific production checks are `NOT_RUN`: migration, 507 canary,
no-trade production case, downstream reconciliation, topic snapshot, Lifecycle
shadow handoff, and first scheduled run.

## 18. Files Changed

TASK-OPS-023 documentation files:

- `docs/reports/TASK-OPS-023_V2_DAILY_CLOSE_PRODUCTION_ACTIVATION_REPORT.md`
- `docs/WORK_ORDERS.md`
- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`
- `docs/operations/deployment.md`

Existing TASK-DATA-022/022A implementation files were preserved while the
TASK-BE-021/BE-021A implementation was integrated into this repository-side
combined candidate. The existing migration-head assertion in
`services/api/tests/test_canonical_observation_implementation.py` was updated
from the historical 0024 head to the current repository head 0027; this is a
test consistency correction only and changes no runtime behavior.

## 19. Documents Updated

This report, `docs/WORK_ORDERS.md`, the production architecture document, and
the deployment runbook were updated. Historical reports were retained. No
authoritative `NEXT_TASK` file or decision was modified.

## 20. Production Actions Performed

Only read-only HTTP preflight was performed against the public Render API.

Not performed: Neon migration 0027; any Neon write; production 507 canary;
secret creation/rotation; topic snapshot write; Lifecycle shadow evaluation;
Render scheduler provisioning; first scheduled run; identity bootstrap.

No changes were made to 2 markets, 507 instruments, 130 topics, 107 hierarchy
rows, or 848 relations.

## 21. Known Issues

- Production Alembic revision is not exposed publicly and remains unverified.
- Production has not yet been verified at combined Alembic head 0027; the
  repository collision is resolved, but the protected database revision is
  still unknown.
- `/api/v1/admin/dashboard` returns HTTP 500.
- `/api/v1/meta/data-status` and `/api/v1/snapshot/latest` return 404.
- Public live status is `NO_RUN`; topic snapshots are empty; daily readiness is
  unestablished.
- Public OpenAPI wording still says synthetic data only.
- Lifecycle implementation is integrated in the repository candidate but is not
  deployed or executed against production.
- No approved Taiwan holiday catalogue or single scheduler owner is recorded.
- The current worktree changes are local/uncommitted and not deployed to Render.

## 22. Risks

- Applying a migration without verifying current revision could be unsafe.
- Running before TWSE/TPEx close files are complete can create partial data.
- Identity totals must not be mistaken for daily data readiness.
- Misclassifying provider failure as no-trade would contaminate breadth.
- A scheduler without holiday authority can create false closed-date runs.

## 23. Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Repository DATA-022 | PASS | prior report and targeted tests |
| Repository DATA-022A | PASS | prior report, migration 0026, 29 tests |
| Production health/readiness | PASS (infra only) | public `/healthz`/`/readyz` 200 |
| Identity counts | PASS | public totals 2 / 507 / 130 / 848 |
| Production Alembic revision | NOT VERIFIED | protected Neon read unavailable |
| Combined DATA/Lifecycle migration lineage | PASS (repository) | explicit 0024 -> 0025 -> 0026 -> 0027 line |
| Production migration 0027 | NOT_RUN | protected migration URL absent |
| Manual 507 canary | NOT_RUN | public live status `NO_RUN` |
| TPE/TWO daily coverage | NOT VERIFIED | no reconciliation readback |
| Approved no-trade case | NOT_RUN | no canary |
| Daily reconciliation READY | NOT_RUN | no coverage/downstream evidence |
| Topic snapshot | NOT_RUN | public page total 0 |
| Lifecycle engine implementation | PASS (combined candidate) | 25 targeted lifecycle/snapshot tests passed |
| Lifecycle shadow handoff | NOT_RUN | lifecycle `NOT_AVAILABLE` |
| Lifecycle production activation | NO | explicitly not activated |
| Scheduler implementation | PARTIAL/BLOCKED | worker exists; no Cron/owner/calendar |
| 14:40 schedule | WAITING/BLOCKED | no scheduler permission |
| First scheduled run | NOT_RUN | no production scheduler |
| Identity/bootstrap/destructive action | PASS | read-only execution |
| NEXT_TASK modified | NO | authority file unchanged |

## 24. Suggested NEXT_TASK

`TASK-OPS-023A-P2 | Protected Production Migration, Canary & Scheduler Owner Handoff`

Minimal operator action, in order:

1. provide protected direct Neon read/migration access and confirm current
   Alembic revision;
3. apply the reconciled additive migrations only if lineage is clean;
4. choose one scheduler owner and provide a reviewed Taiwan holiday authority;
5. run one manual canary and capture the complete 507-instrument reconciliation;
6. verify `READY`, 100% covered, zero unexplained/date/duplicate errors, and
   `downstreamReady=true`;
7. verify the 130-topic snapshot, then run Lifecycle in `evaluation_mode=SHADOW`;
8. activate 14:40 and capture first scheduled-run evidence.

This is a suggestion only. No `NEXT_TASK` authority or production state was
modified by TASK-OPS-023.
