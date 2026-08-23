# TASK-DATA-HIST-002B Canonical Reconciliation & Closure

## Final status

```text
TASK_ID=TASK-DATA-HIST-002B
TASK_NAME=Full Canonical Universe Local Six-Month Seed
FINAL_STATUS=FULL_UNIVERSE_HISTORICAL_SEED_CANONICAL_COMPLETE
NEXT_RESEARCH=REC_A1_DATA_READINESS_AUDIT
```

This closure reconciles the completed isolated historical seed with the
canonical V2 repository and the existing local PostgreSQL evidence. It does
not promote historical data to Production, activate a scheduler, or start
Recommendation backtesting.

## Repository audit

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_PRE_SHA=fcf2f2f8eca8c02b64b978203c3198086a86bf45
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
CANONICAL_DIRTY_STATE=YES
CANONICAL_DIRTY_FILE_COUNT=155

SOURCE_WORKTREE=C:\Users\acer\.codex\worktrees\e558\題材領航
SOURCE_BRANCH=codex/task-data-hist-002b
SOURCE_IMPLEMENTATION_COMMIT=f4ae44b8d2f15ad1cc869b2b63cbb5bff25f8c27
SOURCE_WORKTREE_CLEAN=YES
HIST_002B_COMMIT_REACHABLE_FROM_CANONICAL=NO
```

The canonical checkout contained pre-existing user-owned application,
architecture, research, and owner-document changes. Those changes were not
reset, stashed, overwritten, or blanket-staged. The canonical repository is a
separate Git repository from the predecessor isolated task repository; the
source commit is therefore evidence, not a directly cherry-pickable canonical
commit.

## Exact collision matrix

| Isolated source surface | Canonical reconciliation | Decision |
|---|---|---|
| `tools/historical_market_data/**` | Canonical V2 already owns official exchange providers and transactional ingestion under `services/api/src/topicpilot_api/market_data/`. The isolated runner writes a different plain-table persistence family. | `CANONICAL_ADVANCED_COMPATIBLE`; do not copy or cherry-pick duplicate runtime |
| `tools/test_historical_market_data_001.py` | Canonical has focused provider, no-trade, rate-limit, reference-bundle, and ingestion tests under `services/api/tests/`. | `CANONICAL_ADVANCED_COMPATIBLE`; source test remains predecessor evidence |
| `db/migrations/001_market_data.sql` | No matching canonical migration is present. Canonical V2 uses the Alembic observation/reference chain. | `OBSOLETE_SOURCE_FILE`; no migration copy |
| `tw-reference-v1` bundle | Same approved bundle is present and validates in canonical `reference_data`. | `ALREADY_INTEGRATED` |
| HIST-001 / isolated HIST-002B reports | Task evidence is historical; the canonical owner report is this closure report. | `NO_COLLISION`; canonical report added under `docs/reports/` |
| `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`, `docs/WORK_ORDERS.md`, `docs/DAILY_PROGRESS.md` | Files were already dirty, so only minimal additive historical status updates were made. | `USER_OWNED_DIRTY` preserved; scoped append/minimal semantic edit |
| Product roadmap, documentation index, canonical worklog | No conflicting dirty patch at the affected sections. | `NO_COLLISION`; minimal owner links/status added |
| Production/runtime/`NEXT_TASK` surfaces | Not in scope for closure. | `NO_WRITE` |

```text
COLLISION_AUDIT=PASS
APPLICATION_RECONCILIATION=PASS_WITH_V2_COMPATIBILITY_BOUNDARY
CANONICAL_CONTENT_RECONCILED=YES
```

## Canonical application reconciliation

The canonical V2 application already contains the compatible implementation
surfaces:

- `market_data/exchange.py`: official TWSE and TPEx providers, market-batch
  handling, ROC/Gregorian conversion, missing-value normalization, response
  date validation, and lifecycle/no-trade status semantics;
- `market_data/ingestion.py`: transactional provider-to-observation ingestion,
  request-keyed batches, provider lineage, no synthetic bars, and idempotent
  raw/timeline/canonical reuse;
- `market_data/rate_limit.py`: injected-clock request budget and exponential
  retry/backoff boundary;
- `market_data/lineage.py`: secret-free official-provider provenance;
- `reference_data/bundle.py` and the bundle CLI: versioned, hashed,
  lifecycle-aware `tw-reference-v1` validation.

The isolated runner's exact randomized 3–5 second full-seed pacing and its
2,392-item checkpoint log remain task-scoped operational evidence. They were
not copied into the V2 runtime because doing so would create a second importer
and persistence contract. Canonical V2 pacing remains configuration-driven;
Production activation is not implied by this closure.

```text
HISTORICAL_IMPORTER_CANONICAL=YES
REFERENCE_BUNDLE_SUPPORT_CANONICAL=YES
CHECKPOINT_RESUME_CANONICAL=YES (request-keyed transactional batch boundary)
IDEMPOTENCE_CANONICAL=YES
LIFECYCLE_AWARE_CANONICAL=YES
LOCAL_DB_GUARD_CANONICAL=YES
RANDOMIZED_3_5_FULL_SEED_RUN=ISOLATED_EVIDENCE_ONLY
```

## Local PostgreSQL reconciliation

Read-only verification used the local-only database URL and the approved
`tw-reference-v1` bundle. No reseed, truncate, delete, refetch, or migration
was executed during closure.

```text
PHYSICAL_IDENTITIES=507
SYMBOLS_WITH_DATA=507
OHLCV_ROWS=63826
TWSE_ROWS=39523
TPEX_ROWS=24303
MIN_DATE=2026-02-02
MAX_DATE=2026-08-13
SYMBOLS_GE60=507
EXTRA_UNIVERSE_ROWS=0
REQUIRED_NULL_FIELDS=0
INVALID_OHLCV=0
DUPLICATE_KEYS=0
MISSING_REQUIRED_LINEAGE=0
UNEXPLAINED_GAPS=0
CLASSIFIED_OFFICIAL_NO_DATA_GAPS=19
```

The database also contains one synthetic local-test identity, `TEST/TEST.EQ`,
in the V2 instrument registry. It has no historical OHLCV row and is not part
of the 507 approved market-data universe; it is not an extra historical row.

### Lifecycle and legacy reconciliation

```text
SYMBOL_6806_TERMINATED_ON=2026-06-23
SYMBOL_6806_LAST_TRADING_ROW=2026-06-22
SYMBOL_6806_POST_TERMINATION_ROWS=0
SYMBOL_3059_PRESENT=NO
```

The prior HIST-002A local sample had 126 legacy `TWSE/3059` rows. They were
removed before the predecessor run was finalized because `3059` is not in the
approved bundle. The final local count is therefore expected and authoritative
for the approved 507-symbol universe.

### Checkpoint and idempotence evidence

```text
RUN_ID=HIST-002B-20260814
WORK_ITEMS=2392
COMPLETE=2322
NO_DATA=68
SKIPPED_LIFECYCLE=2
ERROR=0

IDEMPOTENT_RERUN_REQUESTS_ATTEMPTED=0
IDEMPOTENT_RERUN_ROWS_WRITTEN=0
IDEMPOTENT_RERUN_SKIPPED_REQUESTS=2392
```

## Owner-document reconciliation

The following owner surfaces were updated with the completed historical state:

- `PROJECT_CONTEXT.md`: Mainline B now records HIST-002B completion and keeps
  the historical Topic/System State limitation explicit.
- `docs/ROADMAP.md`: historical routing now points to research/readiness work
  after the full seed.
- `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`: Historical is now complete for
  the six-month OHLCV seed and remains research follow-up.
- `docs/WORK_ORDERS.md`: HIST-002B is registered as canonical-complete with
  its evidence and safety boundary.
- `docs/DAILY_PROGRESS.md`: append-only completion milestone added.
- `docs/DOCUMENTATION_INDEX.md`: this closure report is linked under historical
  evidence.
- `docs/AI_WORKLOG.md`: append-only closure entry added.

No `NEXT_TASK`, product scoring formula, topic taxonomy, relation, Production
configuration, scheduler, or protected reference data was changed.

## Validation

```text
FOCUSED_CANONICAL_TESTS=16 passed
SOURCE_HISTORICAL_CONTRACT_TESTS=9 passed
CANONICAL_CONFIG/MIGRATION/REFERENCE/PREFLIGHT_TESTS=22 passed, 1 skipped
CANONICAL_POSTGRES_TESTS=4 skipped (database URL gate not enabled for pytest)
SOURCE_COMPILE=PASS
CANONICAL_COMPILE=PASS
REFERENCE_BUNDLE_VALIDATION=PASS (507; 314 TPE; 193 TWO; 1 lifecycle event)
LOCAL_DB_INTEGRITY_RECONCILIATION=PASS
DIFF_CHECK=PASS (pre-existing line-ending warning only)
SECRET_SCAN=PASS (no literal credential/private-key match)
```

The local database reports Alembic `0017` while the canonical repository head
is `0029`. Migration upgrade/idempotence was intentionally not run because it
would mutate the local database and was outside this read-only closure gate.

Protected gates were preserved, not rerun: `G1`, `G2`, `G3`, and the
Post-Close Canary remain `PRESERVED PASS`. Benchmark/index history is not part
of this seed, so relative strength remains partial; historical Topic/System
State replay is not supplied by OHLCV alone.

## Cleanup decision

```text
WORKTREE_CLEAN_BEFORE_CLEANUP=YES
WORKTREE_UNIQUE_COMMITS_BEFORE_CLEANUP=YES
WORKTREE_UNIQUE_FILES_BEFORE_CLEANUP=YES
WORKTREE_REMOVED=NO
TASK_BRANCH_REMOVED=NO
SAFE_NEXT_ACTION=RETAIN_PREDECESSOR_WORKTREE_AS_HISTORICAL_EVIDENCE_UNTIL_EXPLICIT_ARCHIVAL
```

The isolated worktree is clean, but its runner, tests, progress logs, and
commit are not present in the canonical V2 tree. Removing it now would destroy
unique evidence and source material. No cleanup deletion was performed.

## Safety handoff

```text
HISTORICAL_DATA_RESEED=NO
REC_A1_STARTED=NO
PRODUCTION_MUTATION=NO
PRODUCTION_DB=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
TODAY_CHANGED=NO
STOCK_CHANGED=NO
TOPIC_CHANGED=NO
RECOMMENDATION_CHANGED=NO
G1=PRESERVED PASS
G2=PRESERVED PASS
G3=PRESERVED PASS
POST_CLOSE_CANARY=PRESERVED PASS
```

The next research boundary is `REC-A1` data-readiness audit. It must be opened
as a separate task and must not be inferred as a Production recommendation
activation from this historical seed.
