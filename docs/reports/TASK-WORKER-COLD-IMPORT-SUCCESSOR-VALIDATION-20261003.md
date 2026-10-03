# Worker cold-import successor validation

## Manifest and authority

```text
TASK_ID=TASK-TODAY-FINAL-CLOSURE-WORKER-SITES-READBACK-AND-20261002-20261003
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
BASE_SHA=e698603a8033f6f1a4b7c41f62f903b5caf88985
PATH_POLICY=E_ONLY
BRANCH=codex/task-today-final-closure-worker-sites-20261003
DEVELOPMENT_MODEL=SINGLE_OWNER
REVIEW_MODEL=OWNER_EXCEPTION
REVIEW_AUDIT=OWNER_EXCEPTION_NO_INDEPENDENT_REVIEWER
ACHIEVED_TERMINAL_STATE=VALIDATED
TASK_COMPLETE=NO
FOLLOW_UP_REQUIRED=YES
```

This report records the implementation/validation boundary, not a completed
Production release. Owner authorized one successor branch/PR, merge-commit
integration, safe supported Sites source reconciliation, exact-SHA release,
protected read-only forensic readback, and only then one gated 2026-10-02
NORMAL_CURRENT_DAY publication. Recovery, run 2284 re-entry, historical
backfill, manual SQL, policy/schema changes and synthetic data remain forbidden.
Sites lineage or runtime/data-gate failure must stop downstream operations.

All repository operations used the task worktree under `E:\TopicPilot\worktrees`.
No C-drive project checkout was used. The environment's Python interpreter and
instruction/attachment files are not project checkouts.

## Exact root cause

In a clean Python 3.12.10 process, importing `topicpilot_api.live.cli` at the
baseline fails before provider construction or DB access:

```text
live.cli -> live.collector -> live.persistence -> normalizer.__init__
  -> normalizer.historical -> market_data.history
  -> market_data.__init__ -> market_data.ingestion -> normalizer.__init__
ImportError: cannot import name 'HISTORICAL_MAPPING_POLICY_VERSION'
from partially initialized module 'topicpilot_api.normalizer'
```

Python initializes a package before its submodule. `market_data.__init__`
eagerly imported ingestion, which requested normalizer exports before
normalizer.historical could finish initializing. This is a package import
cycle, not evidence of provider, credential, migration or DB failure.
The previous suite could pass with a warmed module cache/import order; that
does not prove a clean Worker process starts.

## Minimal change and compatibility

Only `services/api/src/topicpilot_api/market_data/__init__.py` changes runtime
code. Four ingestion exports use the module-level lazy attribute boundary:
`HistoricalIngestionError`, `HistoricalIngestionResult`,
`HistoricalSourceRegistration`, and `ingest_historical`.

The original `__all__` list and ordering are unchanged. TYPE_CHECKING imports
preserve static visibility. Access resolves the original ingestion objects,
caches them in the package namespace, and preserves identity; `dir()` advertises
the lazy exports. Unknown attributes raise AttributeError. Import failures are
not caught or transformed. No provider, normalizer mapping, retry, execution,
publication, Topic, Score, Grade, Lifecycle, Opportunity or data semantics change.

`test_worker_import_boundary.py` starts isolated fresh processes, explicitly
selects this checkout's source, removes inherited DB/vendor credentials, and
rejects network connections. It checks six first-import entry points, absence
of eager ingestion, original public exports/star import/object identity,
unknown attributes, propagation of real import failures, Worker dry-run startup
in two modes, missing credentials, and nonzero provider-failure exit behavior.
Controlled failures are test-only, not formal market data or provider evidence.

## Validation evidence

Verified 2026-10-03; completed local results inspected at 14:49:58 UTC. Python
3.12.10, fresh E-drive venv installed from the existing `services/api[dev]`
requirements; frontend/client dependencies installed from unchanged npm lockfiles.
No Production DB credentials were supplied to local tests.

| Gate | Baseline | Successor candidate |
|---|---|---|
| Full backend | 1135 passed, 60 skipped | 1149 passed, 60 skipped |
| New cold-process regressions against baseline | 10 failed, 4 passed | 14 passed |
| Focused new imports plus live CLI tests | Not a pre-existing gate | 18 passed |
| Frontend tests/build | 203 passed; build PASS | Same unchanged frontend tree; PASS |
| Frontend lint | Existing FavoriteButton dependency warning | 0 errors; warning unchanged |
| TypeScript noEmit | Unchanged frontend | PASS |
| Generated API client | Unchanged contract | 4 passed; regeneration no diff |
| OpenAPI drift | Unchanged contract | PASS |
| Migration graph | Head 0048 | 49 revisions, one head 0048; PASS |
| Full-scope Ruff attribution | 749 existing findings | 749 identical; 0 new/0 resolved |
| Changed-source/test Ruff | N/A | PASS |
| Compile/diff check | N/A | PASS |
| Secret policy regression | Existing approved policy | PASS; 18 cases, true positives rejected |

The 60 PostgreSQL tests are skipped locally because no disposable DB URL is
configured, not because they passed. Required CI must separately pass its
disposable PostgreSQL migration/rollback/read-only privilege tests and Docker
Compose smoke. No gate may be bypassed using Owner exception. No secret policy
or CI workflow was changed. Existing npm audit debt was not modified.

The installed `topicpilot-live --mode auto --dry-run` exits zero and reports a
scheduler decision without provider or DB execution. This is a startup smoke,
not a Production runtime readback or scheduler activation.

Evidence XML and Ruff JSON are retained in this worktree's ignored `work/`
directory. Changed files: the package initializer, cold-process tests and this
report. OpenAPI, generated client, frontend, migrations and secret policy have
no candidate diff. Production deployment, Sites publishing, forensic DB
readback and current-day publication have not been performed at this boundary.

## Remaining gates in this same task

1. Exact-parent/clean candidate; unique PR; required checks; Owner-exception
   merge commit; verify canonical ancestry and clean checkout.
2. Read current Sites source/artifact provenance, compare the final canonical
   commit, and use only supported safe source reconciliation. Stop on divergence
   without a proven supported update; never overwrite or force-push.
3. Exact canonical API/Worker/Web release and protected runtime/migration
   readback. A successful deploy hook is not Worker runtime evidence.
4. Protected forensic readback and official date/previousClose/coverage/flow/
   Topic gates; only then the single authorized normal 2026-10-02 publication.

The closure/readback report must identify the achieved terminal state and
unexecuted operations if any gate blocks. This validation report does not
claim `POST_DEPLOY_VERIFIED` or full task completion.
