# TASK-TODAY-20261002-FINAL-PRODUCTION-PUBLICATION

## Outcome and authority

```text
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
BUSINESS_TERMINAL_STATE=20261002_PRODUCTION_HOME_VERIFIED
CANONICAL_BASE=5b8443f5a8fe238fae21f5a74494d4a701b15aba
PATH_POLICY=E_ONLY
DEVELOPMENT_MODEL=SINGLE_OWNER
REVIEW_MODEL=OWNER_EXCEPTION
AUTHORITY_BOUNDARY=ONE_SUCCESSOR_PR_AND_EXACT_SHA_RELEASE_AND_BOUNDED_PUBLICATION
MIGRATION_HEAD=0048_task_checkpoint_provider_metric_applicability
SEMANTICS_CHANGED=NO
FOLLOW_UP_REQUIRED=YES_UNTIL_PRODUCTION_READBACK
```

The Owner's 2026-10-04 final-publication instruction authorizes a bounded
10/1 comparator-only transaction and one fresh 10/2 normal execution after
runtime/provider/identity gates. It does not authorize recovery, run 2284
re-entry, prior failed-run updates, historical backfill, manual Production
SQL, new schema, synthetic/fill data, or formula changes. A passing candidate
or merge alone is not task completion. No Production writer was invoked
during candidate validation.

## Bounded implementation

- `market_data/receipt.py`, `exchange.py`, `provider_preflight.py`: retain
  actual HTTP status, endpoint, requested/response date, raw status, byte
  size/hash and transport-versus-decode stage. Transport errors no longer
  claim a matched date. Endpoint, parser, adapter version, authority,
  publication and retry policies are unchanged.
- `comparator.py`: fetch the official exact-prior-session 10/1 payload once
  per market, validate the target-date effective identity set and existing
  status authority, and persist only accepted PRICE through existing raw,
  timeline and canonical normalization tables. Preserve retrieval time,
  content identity, provenance, idempotency and supersession. Validate all
  points before writing either market and commit both markets atomically.
  Missing OHLC is not filled. 2601 is accounted by legitimate-unavailable
  authority, never by a price row. No Home/Topic/Score/Grade/Lifecycle/run
  writer is imported or called by the comparator path.
- `live/normal_execution.py`: claim a new explicit Owner identity only
  after a terminal prior normal run with a known execution key and complete
  checkpoint continuity. Legacy keys are recognized explicitly, not inferred
  from a missing scope. A completed terminal checkpoint is mandatory.
  Reject any date RUNNING/SUCCESS run or previously claimed Owner identity.
  Do not resume, reuse checkpoints, or update the old run. Existing provider
  point idempotency and the normal publication engine remain authoritative.
  Register the active run immediately after creation so existing exception
  closure can prevent a zombie RUNNING run.
- `final_publication_cli.py`: versioned protected operator surface; read-only
  by default, hard-bounded target 2026-10-02 and comparator 2026-10-01;
  exact runtime SHA/0048 required. Writes additionally require explicit
  once-only Owner authorization. Normal execution requires verified G2 and
  two available target-date institutional-flow authorities. A PARTIAL result
  is failure, not successful publication. No retry loop is added.

No API schema, generated client, migration, frontend or Topic/Score/Grade/
Lifecycle/Opportunity policy changes are included. The separate local Web
governance candidate is not part of this release.

## Validation evidence (2026-10-04, before canonical integration)

Environment: task-local Python 3.12 declared API dev dependencies; npm lockfile
installs; PostgreSQL 16 disposable container bound only to 127.0.0.1:55439.
Existing migrations applied only to this test database, not Production.

| Gate | Baseline 5b8443f5 | Candidate |
|---|---|---|
| Full backend without database environment | 1149 passed, 60 skipped | 1176 passed, 66 skipped |
| CI-equivalent backend with disposable PostgreSQL | 1058 passed, 3 skipped, 148 deselected | 1091 passed, 3 skipped, 148 deselected |
| Added focused pure contract tests | N/A | 27 passed |
| Added comparator transactional DB tests | N/A | 4 passed |
| Added fresh normal claim/closure DB tests | N/A | 2 passed |
| Frontend | 203 passed, build PASS | 203 passed, build PASS |
| OpenAPI / generated client | unchanged | PASS; generated files unchanged; client tests 4 passed |
| Migration graph | one head 0048 | 49 revisions, one head 0048 |
| Changed Python Ruff / compile / diff check | N/A | PASS |
| Full-repository Ruff under identical configuration | 749 findings | 749 unchanged, 0 new, 0 resolved |

The discovered-test delta is +33: 27 pure contract tests and six actual DB
tests. In a no-database invocation the six additional DB tests are skipped,
not PASS. Existing Starlette deprecation and test-transaction warnings remain
baseline debt. Frontend lint has the existing FavoriteButton dependency
warning, no new error.

Directory-wide Gitleaks reproduces the same one baseline fixture finding in
`test_corporate_action_dataset.py`; no value is reproduced here. This does
not make that gate pass. New commit-range scanning and GitHub required
Secret Scan must independently pass before merge. Secret policy and branch
protection are unchanged; Owner exception cannot waive a failed check.

## Protected execution order

1. Verify the exact committed clean candidate, unique PR, all required checks,
   then preserve lineage with the authorized Owner-exception merge.
2. Release API/Worker/Web from the resulting exact canonical SHA. Verify
   actual runtime readback, 0048, Worker clean-process/dry-run, and Web
   artifact digest/source/Sites successor lineage. No migration execution.
3. Run `topicpilot-final-publication --operation comparator-preflight
   --target-date 2026-10-02 --comparator-date 2026-10-01 --expected-sha
   <exact-canonical-sha>`. This must prove official target-date payload,
   346 TPE + 206 TWO accepted points and 2601 legitimate unavailable.
4. Apply once with the same canonical command and
   `--operation comparator-apply --owner-authorized-once`. Verify committed
   raw/timeline/canonical provenance independently after commit. This is
   comparator-only persistence, not a full 10/1 historical publication.
5. Use a freshly generated explicit UUID for `--execution-id`, the read-only
   prior terminal 10/2 run as `--previous-run-id`, and exact canonical SHA.
   `--operation normal-preflight` must pass continuity, date-specific G2 and
   institutional-flow gates. Never substitute run 2284 or a 10/1 failed run.
6. Execute `--operation normal-run --owner-authorized-once` once with that
   identity. Do not retry or resume if any formal gate fails.
7. Verify formal market facts, institutional flow, Topic/Strength/Grade/
   Lifecycle, Home API and public Web date 2026-10-02. Optional downstream
   insufficient-history/unavailable results remain truthful; no fabricated
   history is allowed. Persist a separate operational closure evidence record
   tied to the exact release/run, not a false success claim in this candidate.

At the implementation checkpoint: Production deploy, comparator persistence,
normal run and Home publication are NOT_EXECUTED; TASK_COMPLETE=NO until the
declared business terminal and post-deploy readback are achieved.
