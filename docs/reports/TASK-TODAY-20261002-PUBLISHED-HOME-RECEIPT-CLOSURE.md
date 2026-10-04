# 10/2 already-published Home: bounded terminal receipt closure

TASK_ID=TASK-TODAY-20261002-FINAL-PRODUCTION-PUBLICATION
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
PHASE_STATUS=VALIDATED_NOT_YET_CANONICALIZED_OR_RELEASED
BASELINE_SHA=ce351711ab64f8cfd929b7ece1202a97ebb25744
AUTHORITY=Owner continue-to-publication approval, including necessary bounded fixes
PATH_POLICY=E_ONLY
REVIEW_MODEL=OWNER_EXCEPTION_NO_INDEPENDENT_REVIEWER
SEMANTICS_CHANGED=NO
MIGRATION_REQUIRED=NO

## Observed failure, not an unconsumed Home authorization

The separately authorized ONE Home-only completion committed a PUBLISHED
2026-10-02 Home, then failed the LAST run-metadata commit. Its returned Home
dictionary contains Python date/datetime values; the final JSONB assignment did
not use the existing post-close `_json_safe` boundary. Actual failure was
`TypeError: Object of type date is not JSON serializable`.

The public API and rendered frontend subsequently read the PUBLISHED Home.
The source collector remains terminal PARTIAL; the consumed Home authorization
is FAILED. FINAL_PUBLICATION and COMPLETION have completed second events, and
the Home-only stream retains IN_PROGRESS, COMPLETED, FAILED. Neither the failed
claim nor any event may be deleted, rewritten, retried or treated as unconsumed.

## Bounded implementation and operator contract

- Use the existing JSON-safe conversion for Home-only success/failure metadata
  and CLI output. No hash, numeric authority, provider or product policy change.
- `home-receipt-preflight` is read-only. It requires the original exact-date
  NORMAL_CURRENT_DAY collector contract, original collection/status/Topic gates,
  all checkpoint continuity and execution-key bindings, the specific consumed
  TypeError claim, matching completed publication checkpoints, and ONE existing
  PUBLISHED Home with matching date/source run/publication identity/lineage.
- Independently re-read formal Topic, both institutional markets and Home before
  closure. Missing/mismatched evidence fails closed. No provider is contacted.
- `home-receipt-apply` requires a distinct explicit Owner receipt authorization,
  exact runtime SHA, migration 0048 and all identities. It invokes NO Home writer,
  provider, comparator, Topic calculation, normal run, resume or recovery.
- Acquire the existing date claim lock and run row lock. Atomically update ONLY
  source run terminal metadata and append ONE non-provider receipt checkpoint.
  Preserve the failed Home claim, original Owner no-reentry contract, historical
  failures and completed time in the receipt; do not change counters or old events.
- The source can become SUCCESS only when its already-committed formal output
  readback passes. Repeating the SAME receipt identity is a read-only idempotent
  result; a different identity is blocked. Transaction interruption rolls back
  both run metadata and receipt event, with no zombie RUNNING or Home repeat.

## Validation evidence before promotion

Equivalent native baseline: 1314 passed / 77 skipped / 0 failed.
Candidate: 1336 passed / 79 skipped / 0 failed (+22 unit tests, +2 PostgreSQL
tests skipped only in the native no-DB invocation). Disposable PostgreSQL focused
selection: 200 passed / 0 skipped / 0 failed. Its real psycopg JSONB regression
reproduces the predecessor boundary, proves Home remains committed on final
receipt failure, and verifies atomic rollback/idempotence/old-event preservation.
The existing Home-only PostgreSQL fixture now returns actual date/datetime and
nested Decimal/null, rather than an unrealistic already-serialized dictionary.

Frontend 203 passed, build passed; generated client 4 passed and unchanged.
OpenAPI unchanged. Compile, changed-scope Ruff and diff check pass. Full Ruff
retains 749 baseline findings with no new findings; this task does not fix or waive
that unrelated baseline debt. Alembic 49 revisions / one head, unchanged 0048.
Protected CI, canonical release and metadata-only Production receipt apply are
separate gates; these local results do not imply they have already occurred.

## Preserved limits and daily-forward acceptance

No schema/migration/API contract/frontend/formula/Opportunity changes. No old run
2284, 10/1 failed run or 10/2 failed run changes. No provider/normal/comparator
retry, Home rewrite, historical recovery/backfill, manual SQL, synthetic/zero-fill/
forward-fill or new scheduler activation.

Daily-forward tests verify Asia/Taipei target-date binding, configured 13:45
boundary, restart/date-key idempotence, holiday/weekend WAIT, and official runner
routing. Normal post-close already uses the JSON-safe finish boundary. Future
provider readiness is not guaranteed by tests. Before close, Home retains the
latest completed formal publication; only a successful newly dated normal run
may advance it. The 10/5 after-close result must be read back after it actually
occurs, not inferred from a dry run or future clock fixture.

Formal Grade/Lifecycle/Strength and Opportunity remain explicitly unavailable
where their formal authorities are absent. Their absence is not corrected by
receipt closure, and must not be represented as fabricated complete coverage.
