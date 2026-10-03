# TASK-TODAY-FINAL-CLOSURE-RECONSTRUCT-TASK025-SCOPE-20261003

## Authority and outcome boundary

This is the Owner-requested reconstruction of accepted requirements, not a
reconstruction of an unavailable original diff. The unavailable TASK-025 commit
was neither searched for, guessed, used, nor treated as an integration source.
Only one new branch/worktree was created. No remote write or canonical integration
is authorized by this implementation stage.

```text
TASK_TYPE=implementation
REQUIRED_TERMINAL_STATE=VALIDATED
TASK025_SOURCE_STATUS=UNAVAILABLE_RECONSTRUCTED_FROM_ACCEPTED_SCOPE
BASE_SHA=3f2d4761c665931708517f0501c57f2be257b641
PATH_POLICY=E_ONLY
WORKTREE=E:\TopicPilot\worktrees\TASK-TODAY-FINAL-CLOSURE-RECONSTRUCT-TASK025-SCOPE-20261003
BRANCH=codex/task-today-final-closure-reconstruct-task025-20261003
DEVELOPMENT_MODEL=SINGLE_OWNER
REVIEW_MODEL=OWNER_EXCEPTION
IMPLEMENTATION_SCOPE=CODE_TESTS_AND_TASK_REPORT_ONLY
MIGRATION_REQUIRED=NO
SEMANTICS_CHANGED=ACCEPTED_COVERED_STOCK_DISTRIBUTION_ONLY;NO_TOPIC_SCORE_GRADE_LIFECYCLE_CHANGE
PRODUCTION_DEPENDENCY=SEPARATE_OWNER_CANONICAL_AND_RELEASE_AUTHORIZATION
CANONICAL_STATUS=NOT_CANONICALIZED
CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION
RELEASE_STATUS=NOT_STARTED
PRODUCTION_VERIFICATION=NOT_PERFORMED
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Owner canonical review and single PR integration
```

Remote `refs/heads/main` was read through `git ls-remote` at local preflight and
again on 2026-10-03 around 14:28 Asia/Taipei; both returned the specified `3f2d4761...`
baseline. These are task-local observations, not permanent canonical authority.

## Verified source lineage

The separate existing G2 worktree was inspected read-only. Its exact head was
`a44576a00a84e53299f774414cdc5506d7079c99`; its parent was
`524739323befc2c3abcb0b48dbbc42b7ff54daf1`, whose parent was the exact base above.
The combined source diff, offline replay implementation, tests, and retained
evidence were inspected before local integration. Focused source validation in
the new declared dependency environment passed 96 tests with 1 database test
skipped. No execution or authority claim was inferred from historical report
test counts.

Only the new task branch was fast-forwarded to the verified G2 head. This was a
local source integration, **not** a merge into canonical `main`. The original G2
branch/worktree was not changed. The reconstruction implementation commit is
`bc8526aceaddc42ecaf8c79e69e3661d814a015f`, directly descended from `a44576a...`.
The report-owning commit is the final candidate; its exact SHA and clean-commit
validation results are recorded in the task handoff. This avoids inventing a
self-referential commit hash in its own contents.

```text
3f2d4761... -> 52473932... -> a44576a0... -> bc8526ac... -> report-owning candidate
```

The G2 source changes to `trading_status_authority.py` exclude internal
missing-price sentinels from official status authority. They do not change the
existing corporate-action policy or resolver. The price-free JSON evidence and
earlier report enter this candidate through that preserved source lineage; no
new Production forensic read, historical replay, or old-run operation was performed.

## Accepted scope implementation

### TAIEX target-date authority and provenance

The exact base already contained the dated TWSE close/change adapter and strict
date check. Those verified paths were preserved and tested, not attributed to an
imagined TASK-025 diff:

- Close/change: `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=YYYYMMDD&response=json`.
- Optional OHLC: `https://www.twse.com.tw/rwd/zh/indicesReport/MI_5MINS_HIST?date=YYYYMMDD&response=json`.
- `previousClose = close - signedChange` remains the existing formal derivation.
- A wrong, missing, or malformed close response date fails closed. A valid OHLC
  response cannot rescue a mismatched close response; no undated fallback was added.
- Missing OHLC stays `null`; no previous-day OHLC or synthetic value is substituted.

The fetch boundary now records each actual dated endpoint, requested date,
parsed response date, raw provider date, SHA-256 of received response bytes, and
adapter version, including rejection evidence. Parser-only callers retain the
existing deterministic decoded-payload hash. A joined close/OHLC result retains
both component responses and the existing combined-hash policy.

Home materialization retains this evidence in the existing INDEX
`HomeMarketFact.coverage` JSON and includes it in publication dataset identity.
No table, column, migration, public API schema, or generated client changed.
Persistence tests use an in-memory object sink which rejects SQL; no database
materialization was executed by this task.

### Distribution scope

`COVERED_STOCKS` / `COMPLETE_CLOSE_PREVIOUS_CLOSE` are fixed. The eligible universe
is the canonical covered-stock observation population, not the independent
official whole-market breadth population. Complete rows require finite positive
current and previous closes; invalid or missing prices are excluded, not filled.
The public Home displays complete count, eligible universe, excluded count, and
backend-provided coverage percentage separately. Missing percentage stays
unavailable rather than being computed by the browser.

No subset distribution is labelled `上市＋上櫃全市場`. The independent official
breadth and institutional aggregate surfaces retain their existing authorities;
their labels are not reinterpreted as distribution coverage.

### Today presentation

- Existing hundred-million/ten-thousand formatting (億 / 萬) is retained and directly
  tested; blank/null/non-finite institutional values cannot become zero.
- Index high/low colors compare with `previousClose`: above red, below green,
  equal neutral, invalid/unavailable inputs uncolored.
- Distribution count, label, and bar alignment is centered on the actual flex axis.
- Existing Home filtering requires both `isActive=true` and `signalStatus=ACTIVE`.
- The existing all-signals modal consumes the full backend catalog; it now
  exposes the formal data date and an explicit empty-catalog state. All catalog
  statuses remain visible there, not as inactive Home signal cards.
- Public quality disclosures exclude engineering diagnostics while preserving
  product availability disclosures. Operator metadata is not removed.
- Home latest-completed-publication selection and date semantics are unchanged.

### G2 authority and status accounting

The verified G2 source requires target-date official close evidence, and either
explicit same-payload previous close or the same instrument's exact preceding
formal trading session close. Source, as-of date, authority, identity and lineage
are retained. Wrong identity/date/hash, missing prior close, 0/null/non-finite
prices, shadow/research/synthetic authority, UNKNOWN, provider error and missing
market data remain blocking. No arbitrary nearest-price lookup or fill was added.

Synthetic tests prove TPE 346 price candidates plus the existing official 2601
unavailable status, TWO 206 price candidates, and 553 accounted targets. The
2601 resolver still returns `SUSPENDED` / `LEGITIMATE_UNAVAILABLE` through
`TWSE_OFFICIAL_REDUCTION`, without a price. These are executable contract tests,
**not** fresh Production target coverage or payload readiness evidence.

Weekend and Monday pre-close tests preserve Friday publication selection;
Monday's completed formal publication is selected only after it is supplied as
the completed session. Previous-close comparison never substitutes yesterday's
Home snapshot, and the task creates no time-triggered publication behavior.

## Validation and attribution

Environment: Python 3.12.10 in a newly created task-local `.venv`, installed from
`services/api[dev]` declared constraints; pytest 8.4.2 / Ruff 0.16.10.
Node 24.16.0 / npm 11.13.0; fresh `npm ci` in web and generated-client packages.
No borrowed modules/junctions. No dependency manifests or lockfiles changed.
All database environment URLs were removed before test invocation; database
integration tests were skipped, not reported as passing. No migration was run.

The baseline was tested on the clean exact base before G2 integration. The
finalized reconstruction tree produced the following diagnostic counts; the
final candidate closure requires the same gates on the committed clean report
candidate, with exact SHA/result emitted in the final handoff.

| Gate | Clean baseline | Finalized implementation tree |
| --- | --- | --- |
| Full backend | 1032 passed, 60 skipped | 1135 passed, 60 skipped |
| Focused G2 source before integration | N/A | 96 passed, 1 skipped |
| Focused index/Home/G2/status/post-close | N/A | 156 passed |
| Full frontend, including build | 187 passed | 203 passed |
| New/existing focused frontend | N/A | 33 passed |
| TypeScript | Preserved | PASS |
| OpenAPI comparison with committed client schema | PASS | PASS |
| Generated-client regeneration / diff check | Preserved | Unchanged; 4 tests passed |
| Changed Python Ruff, base-to-candidate paths | N/A | PASS |
| All `services/api` Ruff | 764 findings | 764 findings; 0 added / 0 removed |
| Compile | Preserved | PASS |
| Migration graph | Unchanged source | One head 0048, 49 revisions |
| Git whitespace / conflict-marker diff check | PASS | PASS |

Ruff attribution compares filename/code/message multisets, ignoring moved line
numbers. Existing 764 `services/api` findings remain visible as baseline debt;
this is not a full-repository Ruff PASS or a debt remediation claim. The older
source report's full-repository Ruff counts are historical, not re-labelled as
this task's latest measurement. Fresh npm installation also reported existing
lockfile audit findings (web 22; client 4); no dependency/security remediation or
security-audit PASS is claimed.

Backend delta is +103 tests: 85 retained G2/source tests and 18 reconstruction
cases. Frontend delta is +16. No new test failure was observed. The remaining
FastAPI/httpx deprecation warning is dependency-level, not silently fixed here.

Reproduction commands, from this task root with DB URLs unset:

```powershell
.venv/Scripts/python.exe -m pytest services/api/tests -q -o cache_dir=work/pytest-cache
.venv/Scripts/python.exe infra/scripts/check_openapi_drift.py --baseline packages/api-client/openapi.json
.venv/Scripts/python.exe -m compileall -q services/api/src services/api/tests
# Web directory: npm test; npx tsc --noEmit
# API-client directory: npm run check; npm test
# Ruff: explicit base-to-candidate changed *.py paths; separately services/api JSON attribution
# Alembic ScriptDirectory graph inspection only: no env.py execution or database connection
git diff --check
```

### Local browser acceptance

The browser skill was used only for local presentation QA against a schema-
validated, clearly labelled synthetic in-memory fixture. The server bound only
127.0.0.1; the frontend pointed only to that local fixture. Unserved snapshot
routes returned 404, never a Production fallback. Both local processes and the
verification tab were closed afterwards.

Observed: 552 complete / 553 eligible / 1 excluded / 99.82% display; proper 億/萬
format; one ACTIVE card; modal opens with all 16 catalog entries and ACTIVE,
INACTIVE, NOT_EVALUABLE states plus date; modal closes; all nine bars/counts/labels
are centered (largest measured center delta 0.01px). Local screenshots are
retained under ignored `work/`, not promoted as market data or public fixtures.
Browser QA influenced the flex-axis centering verification, not any semantics.

## Exact changed-file mapping

New reconstruction commit (`bc8526ac...`, eight paths):

- `apps/web/app/components/v2/TodayMarketPage.tsx`
- `apps/web/app/globals.css`
- `apps/web/app/lib/today-market-fields.ts`
- `apps/web/tests/task025-reconstructed-scope.test.mjs`
- `services/api/src/topicpilot_api/home_v2_publication.py`
- `services/api/src/topicpilot_api/market_data/index_contract.py`
- `services/api/tests/fixtures/market_index/task025_twse_target_date_synthetic.json`
- `services/api/tests/test_task025_reconstructed_scope.py`

Verified G2 lineage relative to exact base (18 paths):

- `docs/reports/TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION.md`
- `docs/reports/TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/baseline-replay-price-free.json`
- `docs/reports/TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/candidate-replay-price-free.json`
- `docs/reports/TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/protected-readback-price-free.json`
- `infra/scripts/replay_target_universe_readiness.py`
- `services/api/src/topicpilot_api/daily_market.py`
- `services/api/src/topicpilot_api/market_data/exchange.py`
- `services/api/src/topicpilot_api/market_data/history.py`
- `services/api/src/topicpilot_api/market_data/ingestion.py`
- `services/api/src/topicpilot_api/normalizer/historical.py`
- `services/api/src/topicpilot_api/previous_close_authority.py`
- `services/api/src/topicpilot_api/provider_preflight.py`
- `services/api/src/topicpilot_api/trading_status_authority.py`
- `services/api/tests/test_g2_previous_close_authority.py`
- `services/api/tests/test_missing_price_status_provenance.py`
- `services/api/tests/test_provider_preflight.py`
- `services/api/tests/test_provider_preflight_postgres.py`
- `services/api/tests/test_target_universe_readiness_replay.py`

This report is the final additional documentation path: 27 distinct paths in
the candidate relative to the exact base. No generated client, API schema, migration, Topic engine/formula,
corporate-action policy, operator execution workflow, or dependency file changed.

## Stop boundary

No unavailable source search, no original TASK-025 diff assumption, no C owner
checkout operation, no second branch/PR, no push, no canonical merge, no release,
no Production DB read/write, no SQL, no migration execution, no scheduler
activation, no historical replay/backfill, no recovery, no POST_CLOSE, and no
read/resume/update/reuse of run 2284 or the October 1 failed run was performed.

Final closure is implementation-only. The clean candidate is deliberately
retained for Owner review and the single authorized future PR; all Production
actions remain outside this authorization.

```text
PRODUCTION_DEPLOYED=NO
PRODUCTION_DB_MUTATED=NO
RECOVERY_EXECUTED=NO
POST_CLOSE_EXECUTED=NO
RUN_2284_TOUCHED=NO
20261001_RUN_TOUCHED=NO
UNAUTHORIZED_RETRY=NO
HISTORICAL_BACKFILL=NO
NEXT_TASK_CHANGED=NO
NEXT_STEP=Owner canonical review and single PR integration
```
