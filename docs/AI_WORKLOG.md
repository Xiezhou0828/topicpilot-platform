# AI Worklog

## 2026-08-12 — TASK-BE-021

- Audited the V2 production identity, canonical observation, topic snapshot,
  FastAPI read model, frontend contract, migrations, tests, and public API.
- Implemented the configurable Topic Lifecycle shadow engine and immutable
  explainability result table. The engine remains data-gated and does not
  activate production lifecycle semantics.
- Added the production integration report at
  `docs/reports/TASK-BE-021_TOPIC_LIFECYCLE_ENGINE_PRODUCTION_INTEGRATION_REPORT.md`.
- Added adjacent-stage transition guardrails, canonical live-universe membership
  filtering, active-policy read-model isolation, frontend pending-state tests,
  and deterministic replay/idempotency coverage. The prior targeted lifecycle
  verification was 21 passed and the frontend production build is green; live
  snapshot data remains empty, so activation is still waiting for formal
  observations.
- `NEXT_TASK` was not modified.

## 2026-08-12 — TASK-BE-021A

- Audited the existing lifecycle engine, shadow persistence, CLI, canonical
  observation path, topic snapshots, and the available DATA-022/022A evidence.
  No canonical DATA-022/022A task document or formal observations were present
  in this worktree; the repository does expose the underlying canonical trading
  status schema and accepted DAILY_BAR path.
- Added a deterministic PM calibration review contract with explicit evidence
  fields and blank PM judgement fields, representative-case selection, replay
  summary counts, and JSON/CSV/Markdown exports.
- Added tests for mapping, summary, missing representative cases, deterministic
  export, small-sample handling, PM placeholder safety, and projection
  immutability. The final combined targeted suite is 30 passed. Production
  lifecycle activation remains disabled and `NEXT_TASK` was not modified.

## 2026-08-12 — TASK-BE-024A Opportunity Decision Contract & Explainable Ranking

- Audited the existing TASK-BE-024 V1 shadow strategies, canonical OHLCV
  evidence builders, legacy Recommendation/StrategyCandidate read models,
  frontend Opportunity wording, product decisions, roadmap, and replay
  boundaries. Existing recommendation-score and catch-up concepts remain
  historical/provisional; current Opportunity semantics take priority.
- Added `topic_engine/opportunity_contract.py` with independent provisional
  Trend/Catch-up ranking profiles, deterministic decision states,
  structured `OpportunityExplanation`, provider-neutral
  `OpportunityReadModel`, deterministic frontend fixtures, and a calibration
  schema placeholder. No LLM or browser-side business inference is involved.
- Kept the existing A/B shadow strategy engine and no-look-ahead replay. The
  contract explicitly disables global cross-strategy ranking and leaves
  `EARLY_STRENGTH` / `PULLBACK_ACCEPTANCE` as future slots.
- Added focused contract tests covering profile independence, selected,
  waiting-retest, waiting-confirmation, deferred, excluded, fixtures,
  explanation/read projection, provisional policy labeling, and calibration
  placeholders. No outcome evaluation or parameter optimization was added.
- Updated the Opportunity Engine product spec, Product Decisions, Product
  Ideas, V2 frontend design spec, roadmap, and the TASK-BE-024A report.
- Verification boundary: no production API activation, DB write/migration,
  frontend runtime change, scheduler change, daily market pipeline change,
  Topic Lifecycle/Score change, or NEXT_TASK modification.

## 2026-08-12 TASK-BE-024B Opportunity Qualification Policy V1

- Audited the existing TASK-BE-024/024A strategy, evidence, decision/read,
  replay/calibration contracts and the legacy Recommendation/strategy-candidate
  terminology before adding the qualification boundary.
- Added the shadow-only deterministic qualification policy layer. PM-frozen
  semantics are: S/A formal universe; B warming/provenance exception;
  D/DECLINING hard exclusion; Close >= 20MA hard gate; 60MA as structure/rank
  context; risk before ranking; independent Trend/Catch-up paths; Trend Top 3
  and Catch-up Top 2 presentation caps; post-close ranking and intraday
  status-only behavior.
- Kept numeric thresholds, weights, pattern definitions, cooldowns, exception
  upgrades, validity windows, and transition parameters
  `PROVISIONAL / TUNABLE / VERSIONED`. Replay remains as-of bounded and the
  calibration contract records selection provenance without look-ahead.
- Added focused policy tests for the grade/lifecycle matrix, B exceptions,
  20MA/60MA behavior, risk ordering, strategy independence, caps, replay, and
  contract versioning. Backend verification: 342 passed, 31 skipped, 1
  pre-existing warning; targeted Ruff checks pass.
- Extended the placeholder calibration observation and PM calibration rows with
  explicit `selectionProvenance` values for lifecycle, topic grade, opportunity
  state, ranking-profile version, policy version, and parameter version.
- Final regression after the provenance addition: 345 passed, 31 skipped, 1
  pre-existing warning; focused Opportunity/evidence/shadow suite: 59 passed.
- Updated the Opportunity Engine spec, Product Ideas, Product Decisions,
  Product Roadmap, V2 Frontend Design Spec, and TASK-BE-024B report.
- No API, DB/schema, frontend runtime, scheduler, production data/write, or
  `AI/NEXT_TASK.md` change was made. `NEXT_TASK` remains untouched.

## 2026-08-12 TASK-BE-024C Opportunity Shadow Read API & Frontend Adapter V1

- Audited the BE-024/024A/024B strategy-local ranking, decision/read,
  qualification provenance, legacy Recommendation boundary, API route
  conventions, and V2 frontend adapter conventions before implementation.
- Added a provider-neutral, persistence-free `OpportunityShadowReadService`
  with topic, stock, list, and detail projections. Full backend strategy-local
  ranking metadata is retained while Trend Top 3 and Catch-up Top 2 are the
  presentation caps.
- Added deterministic synthetic fixture coverage, including all five decision
  states, a Grade-B warming exception with provenance, Mature context, and a
  Declining/D exclusion. The canonical production provider is an explicit
  unavailable placeholder; no production data is silently substituted.
- Added shadow-only `/api/v1/.../shadow` routes and a formal response contract
  with `publicationStatus=SHADOW`, `dataStatus=FIXTURE/SYNTHETIC`, policy/
  parameter/ranking-profile versions, structured evidence, and no BUY/SELL,
  target, or stop-loss semantics.
- Added `app/lib/opportunity-shadow-adapter.ts`, exposing backend state,
  sections, display order, evidence, detail fields, and
  `LOADING/READY/EMPTY/DEFERRED/UNAVAILABLE/ERROR` without business inference.
- Focused backend shadow tests: 11 passed (19 with existing Opportunity
  contracts); full backend regression was 362 passed, 31 skipped, 1
  pre-existing warning; targeted Ruff passed. Frontend adapter tests: 2
  passed; frontend lint completed with one pre-existing warning; TypeScript
  passed after correcting two small pre-existing `TopicListPage.tsx`
  compatibility defects; the frontend production build passed. The broader
  legacy source-contract suite remains 59 passed / 13 pre-existing failures
  in Home/Topic wrapper assertions outside this adapter. No persistence, migration, scheduler,
  daily-market, replay, calibration, production activation, or NEXT_TASK
  modification was performed.
- Added the API contract example at `docs/api/opportunity-shadow-read-v1.md`
  and architecture decision record at
  `docs/architecture/decisions/OPPORTUNITY_SHADOW_READ_API_V1.md`.

## 2026-08-13 TASK-DATA-REF-003 Reference Bootstrap Main Integration & Exact-SHA CI

- Reconciled the DATA-REF-001 reference bootstrap implementation at
  `c1a34de5a16f3d35188b50d0d0aaa2f8d47258b9` against local `main` and
  `origin/main`; both main refs were `44dcd6054ff21a2e64d9735e057dc7b66c94b984`,
  and the DATA-REF commit was a one-commit fast-forward descendant with no
  overlap with the dirty main worktree.
- Preserved the existing concurrent documentation and Today Market workstreams;
  no B/C files, `NEXT_TASK`, or Data Governance HOLD content is included.
- TASK-DATA-REF-002 disposable PostgreSQL 16 validation was complete before this
  integration: canonical bundle derivation, reference-only write boundary,
  activation/idempotency/rollback, 2 markets, 507 derived instruments, and
  `topicpilot-reference-check=READY`.
- Pre-push PostgreSQL validation exposed and fixed replacement activation ordering:
  the old ACTIVE registry is now flushed to RETIRED before the new registry is
  promoted, preserving the single-ACTIVE partial unique index under PostgreSQL.
- Exact-SHA CI exposed that the full backend suite runs after other PostgreSQL
  tests have populated identity tables, so the reference integration test could
  be skipped by its empty-database guard. Added a dedicated PostgreSQL service
  step immediately after migration rollback/re-upgrade and before the full
  backend suite; the targeted reference test must now pass rather than skip.
- This task is limited to main integration, exact pushed-SHA CI verification,
  and release-readiness evidence. No deploy, Production database connection,
  Production mutation, G1/G2/G3, Canary, Scheduler, Lifecycle, Opportunity,
  provider authority, or contract redesign is authorized here.

## 2026-08-13 TASK-FE-BE-TODAY-001/002 Today Market Mainlines Integration

- TASK-FE-BE-TODAY-001 audited the Today Market/Home surface, existing
  FastAPI read routes, Home/Topic/Lifecycle/Opportunity SHADOW contracts,
  generated API declarations, frontend adapters, mocks, and local business
  computation. The resulting contract-first plan keeps G1 failure fail-closed
  as `UNAVAILABLE` and allows read-only frontend integration in parallel with
  DATA-REF-001.
- TASK-FE-BE-TODAY-002 connected Today Market `mainTopics` to the existing
  `GET /api/v2/home` contract through the runtime `getHome()` client method
  and generated `HomeResponse` / `HomeTopicCard` types. The new
  `TodayMainlinesResource` preserves backend order and backend topic slugs;
  no browser ranking, lifecycle inference, breadth calculation, or business
  rule was added.
- Removed hardcoded formal-path mainlines from `TodayMarketPage.tsx`. The
  module now exposes `FORMAL`, explicit `PREVIEW`, and fail-closed
  `UNAVAILABLE` states. API errors, empty `mainTopics`, G1/unready, synthetic,
  temporary, and partial sources do not fall back to hardcoded cards.
- Verification: frontend full suite 76/76 passed; focused Today suite 14/14
  passed; API client 3/3 passed; TypeScript, targeted ESLint, frontend build,
  OpenAPI gate/idempotence, `git diff --check`, and secret scan passed. Full
  lint timed out at 124 seconds without diagnostics; targeted lint passed.
- Shared-worktree reconciliation: the observed `9b97a38` commit was an
  external DATA-REF reference bootstrap activation-order fix and did not
  contain TODAY-002 files. `origin/main` later advanced to
  `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`; no rebase or merge was performed.
- No Production DB mutation, reference bootstrap action, provider authority,
  Lifecycle/Opportunity rule, Scheduler, Canary, deploy, push, merge,
  `NEXT_TASK`, or Data Governance HOLD change was performed for this workstream.

## 2026-08-13 TASK-FE-BE-TODAY-002B Today Mainlines Integration Reconciliation

- Reconciled the isolated TODAY-002 implementation commit
  `d89013b4333a5e6768d516228acc352ef6e6a4d5` onto the latest
  `origin/main` at `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c` in a clean
  worktree. The cherry-pick completed without conflict and produced the
  reconciled implementation commit `d7b621d`.
- The reconciliation changed no DATA-REF files, migration, reference bundle,
  provider authority, OpenAPI semantics, backend contract, Lifecycle,
  Opportunity, Scheduler, or production boundary. The existing DATA-REF
  worklog entries were preserved; this entry is append-only.
- TODAY-002 semantics remain unchanged: `GET /api/v2/home` → `getHome()` →
  generated HomeResponse types → TodayMainlinesResource → Today Market UI;
  backend order and slugs are preserved, hardcoded formal mainlines remain
  removed, browser ranking remains absent, and G1/unready/API-error/empty
  states remain fail-closed.
- Pre-push validation boundary: frontend focused/full tests, API client tests,
  TypeScript, targeted lint, frontend build, OpenAPI gate/idempotence,
  `git diff --check`, secret scan, Ruff, backend smoke, PostgreSQL reference
  integration, migration upgrade/rollback, and generated contract checks are
  run against the reconciled SHA before main integration. Full lint is recorded
  as pass only if the repository command completes; otherwise it remains
  `TIMEOUT_NO_DIAGNOSTICS` and targeted lint is reported separately.
- No production database mutation, production reference bootstrap, G1/G2/G3,
  Canary, Scheduler, Render deploy, or release activation is performed by this
  reconciliation. Main push, if all required gates pass, is the only external
  repository mutation authorized by TASK-FE-BE-TODAY-002B.
- The isolated Docker web-image build initially exposed that the repository-root
  build context did not include the generated API client imported by the Today
  adapter. Added the minimal web-Dockerfile source copy; the API/web image build
  and full isolated PostgreSQL/API/Web compose smoke test then passed. This is a
  packaging fix only; no API or data semantics changed.
## 2026-08-13 TASK-DATA-REF-004 Exact-SHA Production Deploy, Runtime Re-Verification & Reference Bootstrap Dry-Run

- The exact release revision was independently reconciled locally as
  `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`; prior operator evidence
  reported runtime SHA verified, G0=PASS, official TWSE/TPEx adapters,
  canonical daily `marketBatch=true`, and verification-only Yahoo/Taishin
  roles.
- Production SELECT-only precheck and post-dry-run baseline remained 2
  markets, 0 instruments, no active reference registry, and
  `REFERENCE_LOAD_STATUS=NOT_READY`. The reference bootstrap dry-run was a
  validated transactional PLAN with no non-reference write set and no state
  change. No Production activation was performed.
- The first screenshot transcription had a bundle-hash discrepancy; the
  following append-only correction supersedes that transcription.

## 2026-08-13 TASK-DATA-REF-004 Evidence Correction and Final Readiness

- The earlier Production dry-run bundle hash was transcribed incorrectly from
  a screenshot. The operator has now supplied a machine-readable extraction
  from the same Render Production runtime. Its `bundleSha256` is
  `5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`, which
  exactly matches the committed manifest at release SHA
  `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`.
- The previous `...aa5f17c...` value is superseded and is retained only in
  the preceding audit entry as the original transcription error.
  `BUNDLE_HASH_MATCH=PASS` and `PRODUCTION_BUNDLE_DRIFT=NO`.
- All other operator evidence remains unchanged: runtime full SHA verified,
  G0=PASS, precheck baseline is 2 markets / 0 instruments / NOT_READY,
  dry-run is VALIDATED / PLAN with transactional=true, no non-reference
  write set, and no before/after Production state change.
- The formal TASK-DATA-REF-004 report is updated to
  `READY_FOR_ONE_SHOT_PRODUCTION_REFERENCE_BOOTSTRAP_AUTHORIZATION`.
  This is readiness only; no bootstrap, activation, G1-after-bootstrap,
  G2/G3, Canary #2, Scheduler change, `NEXT_TASK` change, or Data Governance
  HOLD change occurred. Await separate explicit TASK-DATA-REF-005
  authorization.

## 2026-08-13 TASK-DATA-REF-005A Production Market Identity Conflict Read-Only Audit

- TASK-DATA-REF-005 one-shot activation was attempted once in the protected
  Production runtime with the approved exact release and canonical bundle.
  The command returned `{"status":"BLOCKED","error":"bundle/database
  conflict in market TPE name"}`. No retry, repair, manual SQL, seed,
  migration, bundle regeneration, or code change was performed.
- The Production SELECT-only evidence immediately after the blocked command
  remains the DATA-REF-004 baseline: 2 markets, 0 instruments, empty
  duplicate identities, missing instruments present, no active reference
  registry, and `REFERENCE_LOAD_STATUS=NOT_READY`. The operator reports
  `BOOTSTRAP_MUTATION_OCCURRED=NO`, `ROLLBACK_REQUIRED=NO`, and
  `PARTIAL_STATE_LEFT=NO`.
- The read-only Production market diagnostic reports TPE as
  `Taiwan Stock Exchange` with `exchange_code=TPE`, and TWO as
  `Taipei Exchange` with `exchange_code=TWO`. The exact-SHA canonical bundle
  and current exact-SHA reference/live identity defaults are TPE
  `TWSE Listed` / `TWSE` and TWO `TPEx OTC` / `TPEx`. Both markets therefore
  have a name and exchange-code identity drift relative to the approved
  bundle.
- Repository evidence shows the conflict path performs exact equality checks
  without normalization in `reference_data/bootstrap.py`; the conflicting
  existing market is rejected before its identity fields are changed. A
  provisional registry row may be flushed inside the same SQL transaction
  before market reconciliation, but the exception rolls that transaction
  back; the Production before/after SELECT-only evidence confirms no
  persisted mutation or partial state.
- The canonical naming authority remains the approved `tw-reference-v1`
  bundle at release SHA `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`, with its
  manifest authority statement tying market identity to the provider registry
  and current identity-bootstrap defaults. Production rows are conflict
  evidence, not an authority override. Root-cause classification is
  `PRODUCTION_LEGACY_NAME_DRIFT` with unresolved provenance of the original
  Production seed path; this requires a separate market-identity remediation
  review before any bootstrap retry.
- TASK-DATA-REF-005A is `READY_FOR_MARKET_IDENTITY_REMEDIATION_REVIEW`.
  G1 is not reached (effective gate FAIL); G2/G3, Canary #2, daily
  reconciliation, Topic Snapshot, Lifecycle, Opportunity, and Scheduler
  remain not run. `NEXT_TASK` and the Data Governance HOLD are untouched.

## 2026-08-13 TASK-DATA-REF-005B Production Market Identity Remediation Design and Disposable PostgreSQL Validation

- TASK-DATA-REF-005B is limited to remediation design, implementation, and
  disposable/isolated PostgreSQL validation. Production mutation, Production
  SELECT, bootstrap retry, market repair, migration, seed, deploy, G2/G3,
  Canary, Scheduler, `NEXT_TASK`, and the Data Governance HOLD were not
  touched.
- The fixed authority remains release SHA
  `a5fba9319a177a5da9fb8123b265ed05e7ff9f6c`, bundle `tw-reference-v1`,
  bundle SHA
  `5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`,
  `BUNDLE_HASH_MATCH=PASS`, and `PRODUCTION_BUNDLE_DRIFT=NO`. The prior
  Production evidence remains G0 PASS and the blocked DATA-REF-005 baseline:
  2 markets, 0 instruments, no active reference registry, and
  `REFERENCE_LOAD_STATUS=NOT_READY`.
- The semantic audit confirms that `market.code` is stable TopicPilot
  identity and must not change or be re-keyed; `market.name` and
  `market.exchange_code` are governed canonical metadata that may be updated
  in place. The approved canonical values are TPE `TWSE Listed` / `TWSE` and
  TWO `TPEx OTC` / `TPEx`; the observed Production values remain legacy drift
  evidence (`Taiwan Stock Exchange` / `TPE`, `Taipei Exchange` / `TWO`) with
  exact historical seed provenance not proven.
- Implemented a dedicated fail-closed
  `topicpilot-market-identity-remediation` entrypoint. Its exact write set is
  `markets.name` and `markets.exchange_code`; primary keys and market codes
  are preserved; `NON_MARKET_IDENTITY_WRITE_SET=NONE`. It supports explicit
  dry-run/apply modes, exact legacy preconditions, canonical NOOP reruns,
  single-transaction apply, postcondition checks, and rollback on failure.
- Added unit/contract and PostgreSQL integration coverage for dry-run no
  mutation, in-place apply, PK/code preservation, idempotent rerun, mixed and
  unexpected market state, unexpected instrument/reference state, injected
  rollback, and post-remediation reference bootstrap readiness.
- Fresh disposable PostgreSQL 16 validation passed: `7 passed`.
  Post-remediation isolated reference activation reached 2 markets, 507
  instruments (`TPE=314`, `TWO=193`), no missing/duplicate identities, and
  `REFERENCE_LOAD_STATUS=READY`. Migration downgrade `0028 -> 0027` and
  re-upgrade to head also passed.
- OpenAPI drift, generated contract idempotence, API client tests, task-scoped
  Ruff, AST compilation, pip check, diff check, and targeted secret-pattern
  scan passed. The root-level backend run reached `336 passed / 8 skipped`
  with two unrelated pre-existing/environmental failures in canonical trigger
  qualification and an observation migration test URL boundary; neither is
  in the remediation path.
- A validation-hygiene issue was recorded: an early local Alembic invocation
  used `TEST_DATABASE_URL`, which this repository ignores for migrations, and
  advanced the existing local non-Production database from `0024` to `0028`.
  No Production database or credential was accessed; all subsequent validation
  used the explicit disposable PostgreSQL port `55433`.
- `AI_WORKLOG_UPDATED=YES`, formal report and runbook are present. Final status
  is `READY_FOR_ONE_SHOT_PRODUCTION_MARKET_IDENTITY_REMEDIATION_AUTHORIZATION`;
  STOP and wait for separate TASK-DATA-REF-005C authorization.
## 2026-08-13 TASK-FE-BE-TODAY-003 Today Heating/Cooling Topics Integration

- Started from `origin/main` at
  `9c1b1f9cc7c1e4510b61060ffa8a8a7928ee45bc` in the isolated
  `codex/task-fe-be-today-003-20260813` worktree. The current repository has no
  `docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md`; authority was cross-checked
  against `PROJECT_CONTEXT.md`, the V2 frontend design contract, the existing
  Home schemas/read model, generated API types, runtime client, and Today tests.
- Confirmed the existing formal read path is
  `GET /api/v2/home` → `getHome()` → `HomeResponse.heatingTopics` /
  `HomeResponse.coolingTopics`. No FastAPI route, OpenAPI schema, migration,
  provider, or backend rule change was needed.
- Reused the TODAY-002 Home request with zero additional Home requests. The
  Today resource now maps heating/cooling cards from the generated
  `HomeRotationTopic` contract, preserves backend order, nullable/invalid
  boundaries, backend `topicSlug`, `currentGrade`, and `summary`, and performs
  no browser sorting, ranking, direction inference, score, lifecycle, or
  breadth calculation.
- Removed the formal-path hardcoded warming/cooling arrays from
  `TodayMarketPage.tsx`. Rotation sections now support `FORMAL`, explicit
  `PREVIEW`, and fail-closed `UNAVAILABLE`; empty sections, incomplete fields,
  unknown publication metadata, G1/partial/temporary sources, and API errors
  never fall back to mock topic cards.
- Verification: focused Today/Home tests 16/16 passed; frontend full suite and
  build 78/78 passed; API client 3/3 passed; TypeScript, targeted/full lint,
  Ruff, OpenAPI gate/idempotence, diff check, and changed-file secret scan
  passed. Full lint retained one pre-existing warning in
  `TopicDetailPage.tsx` and no errors.
- `DATA-REF` files, provider authority, Lifecycle/Opportunity rules,
  Scheduler, production DB, G1/G2/G3, Canary, deploy, push, main merge,
  `NEXT_TASK`, and Data Governance HOLD were not touched. This worklog entry is
  append-only; implementation remains isolated for integration review.

## 2026-08-13 TASK-FE-BE-TODAY-003B Final Reconciliation

- DATA-REF-005C stabilized on `origin/main` at
  `446e318a9b158958ff3c6972994f68b2f5ca898b`; its remediation files and
  append-only worklog were preserved as the reconciliation base.
- TODAY-003 was cherry-picked from provenance commit
  `93a2579a6f5f43e9d1da8f6f56bee3d9c4b770e6` onto that exact base. The only
  content outside the DATA-REF base is the Today heating/cooling frontend
  adapter, UI, and focused tests; no backend/provider/data-rule files were
  added.
- The AI_WORKLOG overlap was resolved by retaining both DATA-REF-005B and
  TODAY-003 entries, then appending this reconciliation record. No production
  database mutation, reference bootstrap, provider authority change,
  Lifecycle/Opportunity rule change, Scheduler, Canary, deploy, or force push
  was performed.

## 2026-08-13 TASK-DATA-REF-005D Existing-Instrument Safety Contract Fix

- Started from `origin/main` at
  `8a818935fe63eb3c3db9592c5068363c7ec941e9` in the isolated
  `codex/task-data-ref-005d-20260813` worktree. Production was not connected or
  mutated, and the blocked remediation command was not retried.
- Confirmed the DATA-REF-005C blocker was a different-state-metric defect:
  reference check counts active canonical EQUITY identities with required
  reference context, while remediation had required the raw total count of
  `topicpilot.instruments` to be zero.
- Replaced the row-count-only precondition with fail-closed bundle semantic
  validation. Existing instruments must be empty or exactly match the
  validated bundle by market/code identity and canonical name, type, and
  currency. Missing, extra, duplicate, orphan, reassigned, and metadata-drift
  states block before mutation. The expected count is bundle-derived; 507 is
  not hardcoded.
- Preserved the exact write set `markets.name` and `markets.exchange_code`.
  Market primary keys/codes and the complete instrument row snapshot are
  verified unchanged; apply remains single-transaction, rollback-safe, and a
  second successful apply is `NOOP`.
- Fresh disposable PostgreSQL 16 validation reproduced 2 legacy markets, 507
  inactive bundle-compatible instruments, reference-check 0 / `NOT_READY`, a
  remediation dry-run plan, successful disposable apply with zero instrument
  changes, and subsequent formal bootstrap `READY` at 2/507 (`TPE=314`,
  `TWO=193`). Dedicated remediation/reference tests passed 11/11; contract
  tests passed 7/7.
- Ruff, migration downgrade/upgrade, OpenAPI and generated-contract gates, API
  client tests, AST compilation, pip check, and diff check passed. The
  CI-equivalent backend run reached 337 passed / 14 skipped / 59 deselected
  with one unrelated pre-existing Windows/PostgreSQL schema-qualified
  `regclass` assertion failure. No API contract or dependency file changed.
- Runbook and formal report were updated. `NEXT_TASK`, Data Governance HOLD,
  provider authority, Lifecycle/Opportunity, Scheduler, Production G1/G2/G3,
  Canary, deployment, push, and main merge were not touched. Final status is
  `READY_FOR_REMEDIATION_PRECONDITION_INTEGRATION_REVIEW`; STOP and wait for
  separately authorized TASK-DATA-REF-005E.

## 2026-08-13 TASK-FE-BE-TODAY-004B Shared Home Resource Envelope Integration

- Started from `origin/main` at `8a818935fe63eb3c3db9592c5068363c7ec941e9` in
  isolated branch `codex/task-fe-be-today-004b-20260813`.
- Added the frontend-only `TodayHomeResource` envelope in
  `apps/web/app/lib/today-home.ts`, using the generated `HomeResponse` and
  generated Home child types. It separates transport state from publication
  state and propagates data date, as-of, source, data quality, temporary and
  missing sections, classification/status, and reason.
- Reused exactly one existing `getHome()` request for main topics, heating,
  cooling, Daily Focus, Market Pulse, Opportunity, and Market Overview. The
  existing `today-mainlines.ts` API remains as a compatibility projection, so
  TODAY-002/003 backend order, slugs, null/empty behavior, and fail-closed
  semantics are preserved.
- Daily Focus, Market Pulse, Opportunity, and Market Overview are mapped into
  the shared resource only. Their existing UI was not replaced. No browser
  ranking, lifecycle, breadth, event, severity, deduplication, opportunity,
  provider, or reconciliation rules were added.
- Added focused envelope and regression tests. Frontend build and full suite
  passed (`83/83`); API client tests passed (`3/3`); TypeScript, targeted/full
  lint, OpenAPI gate/idempotence, diff check, and changed-file secret scan
  passed. Full lint retains one unrelated existing warning in
  `TopicDetailPage.tsx`.
- No backend/OpenAPI/data-ref/provider/migration/Production DB/Scheduler/
  Canary/G1/G2/G3 change was made or run. `NEXT_TASK` and Data Governance HOLD
  were not modified. This entry is append-only; `PUSH=NO`, `MERGE_MAIN=NO`,
  `DEPLOY=NO`, `PRODUCTION_MUTATION=NO`.

## 2026-08-13 TASK-FE-BE-TODAY-004B-R Shared Home Resource Reconciliation & Main Integration

- The initial 004B reconciliation was intentionally not pushed when a fresh
  remote check found `origin/main` had advanced from `8a818935…` to
  DATA-REF-005E `564c9d8e739e7485c4f76b8e058034e5742b8974`. The stale local
  fast-forward was retained only as audit evidence and was never pushed.
- Re-audited the current main tip. DATA-REF-005E is the only concurrent
  post-004B-base commit; it changes only its remediation service/tests/runbook/
  report and this worklog. No concurrent Today/Home, Stock Explorer, or unknown
  source changes were found.
- Recreated isolated branch `codex/task-fe-be-today-004b-r2-20260813` from
  fresh `origin/main@564c9d8…` and scoped-cherry-picked authoritative
  `ac4cf444574e4ffd6bb1dfbda78eac883ba499d4` as `8afad1a…`. The expected
  `docs/AI_WORKLOG.md` conflict was resolved append-preserving: DATA-REF-005D
  and TODAY-004B entries were both retained. `f87014e…` remained superseded.
- The shared Home resource, one Home request, generated HomeResponse, transport/
  publication separation, TODAY-002/003 regressions, and UI freeze boundary are
  preserved. No browser business rule, backend/OpenAPI semantics, DATA-REF
  logic, migration, Production DB, Scheduler, G1/G2/G3, or Canary change was
  made. `NEXT_TASK` and Data Governance HOLD remain unchanged.
- Local affected/release gates passed on the clean reconciliation scope:
  focused Today/Home `21/21`, frontend `83/83`, API client `3/3`, TypeScript,
  targeted/full lint (one pre-existing `TopicDetailPage.tsx` warning), build,
  OpenAPI gate/idempotence, diff check, and changed-file secret scan.
- Main fast-forward, non-force push, exact pushed SHA, and GitHub Actions result
  will be appended after the latest-main integration. `PRODUCTION_MUTATION=NO`,
  `DEPLOY=NO`, `G1/G2/G3=NOT_RUN`, `CANARY=NOT_RUN`, `PUSH` not yet executed.

## 2026-08-13 TASK-FE-BE-TODAY-004B-R Post-Push Verification

- Main integration passed: local `main` fast-forwarded from
  `564c9d8e739e7485c4f76b8e058034e5742b8974` to
  `ab3e1c3471d5226c576536842bcf783d98512ced`, then pushed to `origin/main`
  with a normal non-force push. Local and remote main are synchronized at that
  exact SHA.
- Exact-SHA GitHub Actions run `31669302668` completed successfully with head
  SHA `ab3e1c3471d5226c576536842bcf783d98512ced`. Secret scan, Frontend,
  Backend/migration/OpenAPI/generated contract, and Docker Compose smoke all
  passed.
- Final reconciliation status is `READY_FOR_TODAY_004C`. No Production DB,
  deployment, G1/G2/G3, Canary, Scheduler, reference bootstrap, provider
  authority, DATA-REF logic, migration, `NEXT_TASK`, or Data Governance HOLD
  change was made by this task.
## 2026-08-13 TASK-FE-BE-STOCK-002 Formal Stock Explorer Query Wiring

- Authority was refreshed with `git fetch origin --prune`; implementation started
  from `origin/main` at `8a818935fe63eb3c3db9592c5068363c7ec941e9` in the isolated
  `codex/task-fe-be-stock-002-20260813` worktree. Post-Stock-001 commits were
  classified as Today Market and documentation only; no Stock/API contract
  change was found.
- Wired the existing formal Stock Explorer query state to backend-owned
  `market`, formal topic slug, `updateMode`, `sort`, `limit`, and `offset`
  parameters through the generated OpenAPI-backed `stock-api.ts` adapter.
  Filter/sort changes reset to offset zero; refresh preserves the same query and
  formal backend order.
- Removed V2 formal browser business filtering and formal browser reordering.
  Technical, chip, and strategy controls remain visible but disabled because
  the current formal contract does not provide those filters. No browser
  technical scoring, provider reconciliation, ranking, or canonical main-topic
  inference was added.
- Preserved explicit Formal/Preview/Unavailable boundaries, null market values,
  topic relation display, and the existing shared Stock Drawer UX. Search,
  history, lineage, technical-detail expansion, favorites backend, and
  Opportunity integration remain roadmap items.
- Verification: focused Stock tests 21/21 passed; frontend full suite/build
  99/99 passed; API client 3/3 passed; TypeScript, targeted/full lint,
  OpenAPI gate/idempotence, diff check, and secret scan passed. Full lint kept
  one pre-existing warning in `TopicDetailPage.tsx` and no errors.
- No backend/OpenAPI semantic change, DATA-REF/Today/provider/lifecycle/
  opportunity/scheduler change, Production DB mutation, G1/G2/G3, Canary,
  Scheduler execution, deploy, push, merge, or `NEXT_TASK` modification was
  performed. This entry is append-only; final status is
  `READY_FOR_STOCK_002_INTEGRATION_REVIEW`.

## 2026-08-13 TASK-FE-BE-STOCK-002B Query Integration Reconciliation & Exact-SHA Main Integration

- Re-fetched `origin/main` before integration. The initial current main was
  `8a818935fe63eb3c3db9592c5068363c7ec941e9`; during validation DATA-REF-005D
  advanced main to `564c9d8e739e7485c4f76b8e058034e5742b8974`. The concurrent
  commit touched DATA-REF remediation and documentation only; no Stock Explorer
  or API query semantics changed.
- Reconciled Stock-002 commit `c8d43955583f1a460aa45a31fd2304a302cf7c5c`
  onto the latest main in the isolated 002B worktree. The AI_WORKLOG conflict
  was resolved append-preserving: DATA-REF-005D and Stock-002 entries were both
  retained. Reconciliation commit is `40e72017b5dd30fed5d1a2f1a728a901a0cb9609`.
- Preserved Stock-002 formal query parameters, backend-owned filtering/order,
  offset reset, refresh query/order semantics, null handling,
  Formal/Preview/Unavailable boundaries, disabled technical/chip/strategy
  controls, generated OpenAPI types, no main-topic inference, and Drawer UX.
- Reconciliation validation passed: focused Stock tests 21/21, frontend full
  suite/build 99/99, API client 3/3, TypeScript, targeted/full lint, Ruff,
  OpenAPI gate/idempotence, diff check, and secret scan. Full lint retained the
  pre-existing `TopicDetailPage.tsx` warning with no errors.
- No DATA-REF, Today, provider authority, Lifecycle, Opportunity, Scheduler,
  backend contract, or OpenAPI implementation files were changed by 002B.
  Production DB, deploy, G1/G2/G3, Canary, Scheduler execution, and
  `NEXT_TASK` were untouched. This entry is append-only; main integration and
  exact-SHA CI remain the next controlled steps.

## 2026-08-13 TASK-FE-BE-STOCK-002B Fresh-Main Reconciliation Follow-up

- A final `git fetch origin --prune` found `origin/main` at
  `ab3e1c3471d5226c576536842bcf783d98512ced`, after concurrent Today commits
  `8afad1a` and `ab3e1c3`. No concurrent Stock Explorer or unknown semantic
  changes were found.
- Rebased the isolated Stock-002 implementation onto that exact main tip as
  `211c726`. The only conflict was `docs/AI_WORKLOG.md`; DATA-REF, Today, and
  Stock entries were retained append-preservingly.
- Re-ran the affected gates: Stock focused `21/21`, frontend build/full suite
  `104/104`, API client `3/3`, TypeScript, targeted/full lint, OpenAPI drift and
  idempotence, Ruff, diff check, and secret-pattern scan all passed. Full lint
  retains one pre-existing `TopicDetailPage.tsx` warning and no errors.
- Main push and exact-SHA GitHub Actions validation remain the next controlled
  steps. `PRODUCTION_MUTATION=NO`, `DEPLOY=NO`, `G1/G2/G3=NOT_RUN`,
  `CANARY=NOT_RUN`, and `NEXT_TASK` remains unchanged.

## 2026-08-13 TASK-FE-BE-STOCK-002B Final Main Integration Verification

- Final freshness check passed at `origin/main=82419a27d0ed0322a3070670f77fb0a74554b679`;
  the isolated branch was `ahead 2 / behind 0`, rebased cleanly, and was pushed
  non-force to `main` at exact SHA
  `69138c2575caf93214cc4fc7b1f6fde98d1ad98f`.
- Post-push synchronization is `0/0`. Exact-SHA GitHub Actions run
  `31671576938` for that SHA passed Secret scan, Frontend lint/test/build,
  Backend/PostgreSQL/migration/reference/OpenAPI/generated-contract gates, and
  Docker Compose smoke.
- This append-only verification record does not modify application semantics,
  Production DB, deployment, G1/G2/G3, Canary, Scheduler, or `NEXT_TASK`.
  `PRODUCTION_MUTATION=NO`, `DEPLOY=NO`, `STOCK_003_STARTED=NO`, final status is
  `READY_FOR_STOCK_003`.

## 2026-08-13 TASK-FE-BE-STOCK-002B Verification Record Correction

- Corrected the final report metadata without changing application semantics:
  application integration SHA is `69138c2575caf93214cc4fc7b1f6fde98d1ad98f`,
  the final documentation verification SHA is
  `8e0ffc713ccead047a97ea7b5c24c649cfa79230`, and its exact-SHA CI run is
  `31671892857`.
- Both the application SHA and final verification SHA passed the required CI
  jobs. `PRODUCTION_MUTATION=NO`, `DEPLOY=NO`, `NEXT_TASK` unchanged, and
  `STOCK_003_STARTED=NO`.

## 2026-08-13 TASK-DATA-REF-005E Semantic Remediation Release and Production Dry-Run

- Integrated the DATA-REF-005D semantic precondition correction from
  provenance commit `47c0c2d09bc0c5796a97fa1f81b4b6c1df28a7ad` onto the then-current
  `origin/main` without conflict. The initial integration release was
  `564c9d8e739e7485c4f76b8e058034e5742b8974`; exact-SHA CI run
  `31668931779` passed Frontend, Secret scan, Backend/PostgreSQL/migrations,
  OpenAPI/generated contract, and Docker Compose smoke.
- Concurrent Today and Stock frontend/documentation commits subsequently
  advanced main while the Render hook was building. Runtime evidence exposed
  the race as `82419a27...` rather than `564c9d8...`. Read-only audit proved
  that the intervening commits retained 005D and did not change any DATA-REF,
  reference bundle, remediation, or bootstrap path. No remediation apply or
  reference bootstrap was attempted under the mismatched runtime.
- Re-established release authority at stable main SHA
  `e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77`. It contains 005D with zero
  DATA-REF drift; exact-SHA CI run `31672214158` passed, and protected deploy
  workflow run `31673036818` validated the revision and successfully triggered
  only the Render API deploy hook. Sites packaging was skipped.
- Operator evidence from the authenticated Production Render Shell confirmed
  both `RENDER_GIT_COMMIT` and `topicpilot-provider-lineage.buildSha` equal
  `e9041887f0949fb38dbaa8c6519ba5cbd0fd0c77`. Provider lineage remained
  `READY`: TWSE/TPEx adapter-v2, market-batch canonical daily authority,
  Yahoo verification-only, and Taishin intraday-only. G0 passed.
- Production reference checks immediately before and after remediation
  dry-run were unchanged: 2 markets, 0 valid reference instruments, no
  duplicate identities or missing markets, missing instruments present,
  registry inactive, and `REFERENCE_LOAD_STATUS=NOT_READY`. This is the
  approved pre-bootstrap baseline, not a G1 pass.
- The Production remediation `--dry-run` returned `PLAN` / `VALIDATED`, 507
  existing instruments, `CANONICAL_BUNDLE_COMPATIBLE`, transactional and
  idempotent semantics, preserved market primary keys/codes, and exact planned
  changes TPE `Taiwan Stock Exchange`/`TPE` to `TWSE Listed`/`TWSE` and TWO
  `Taipei Exchange`/`TWO` to `TPEx OTC`/`TPEx`. Its only planned write set is
  `markets.name` and `markets.exchange_code`; instrument and non-market write
  sets are empty.
- No Production remediation apply, reference bootstrap, activation, G1
  post-bootstrap recheck, G2/G3, Canary, Scheduler, manual SQL, seed, or data
  mutation was executed. `NEXT_TASK` and Data Governance HOLD were not
  modified. Final status is
  `READY_FOR_ONE_SHOT_PRODUCTION_MARKET_IDENTITY_REMEDIATION_AUTHORIZATION`;
  STOP and wait for separately authorized TASK-DATA-REF-005F.

## 2026-08-13 TASK-DATA-REF-005F Production Remediation Apply and Blocked Bootstrap

- The explicitly accepted Production authority was updated to docs-only
  descendant SHA `6d611cb7d5db589c375e27cb3e2abfef91e512e2`. Both
  `RENDER_GIT_COMMIT` and provider-lineage `buildSha` matched it, exact-SHA CI
  run `31673484828` had passed, provider lineage was `READY`, and G0 passed.
- Fresh pre-mutation evidence matched 005E: 2 markets, 507 total instrument
  rows but 0 valid reference instruments, inactive/missing registry state,
  no duplicate identities or missing markets, and bundle SHA-256
  `5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`.
  The remediation dry-run remained `PLAN` / `VALIDATED` with
  `CANONICAL_BUNDLE_COMPATIBLE` and the exact two-field market write set.
- Executed the one authorized Production market remediation apply. It returned
  `APPLIED` / `CANONICAL` transactionally. TPE became `TWSE Listed` / `TWSE`
  and TWO became `TPEx OTC` / `TPEx`; both primary keys and internal market
  codes were preserved. The 507 instrument rows and fingerprint
  `daddec45ba36b3571e5d07171a7a7bd8` were unchanged, and no non-market identity
  table was written. A follow-up remediation dry-run returned canonical
  `NOOP`.
- Reference bootstrap dry-run returned `PLAN` / `VALIDATED`, the reviewed
  bundle hash, 37 planned reference rows, no new market/instrument rows, and
  an empty non-reference write set. The subsequently authorized one-shot
  activation failed closed with `bundle/database conflict in market TPE
  calendar`.
- Immediate SELECT-only diagnostics proved both canonical Production market
  rows have `timezone=Asia/Taipei` but `calendar_code=NULL`, while the bundle
  requires `TW_MARKET`. The activation transaction rolled back completely:
  all seven reference registry/context/calendar tables remained at zero,
  no registry became ACTIVE, instruments remained 507, and reference-check
  remained 2/0, inactive, and `NOT_READY`.
- The dry-run planner did not expose this conflict because it plans from
  existing market codes/instrument keys and does not run the apply-time market
  context equality checks. This execution task does not change that code or
  authorize calendar repair, retry, manual SQL, or reversal of the successful
  market remediation.
- Product code, migrations, configuration, `NEXT_TASK`, and Data Governance
  HOLD were not changed. G1 was not reached; G2/G3, Canary, and Scheduler were
  not run. Final status is
  `MARKET_REMEDIATION_COMPLETE_REFERENCE_BOOTSTRAP_BLOCKED`; STOP pending a
  separately scoped review/remediation task.

## 2026-08-13 TASK-DATA-REF-005G Market Calendar Remediation and Dry-Run Parity

- Audited the Production calendar conflict against schema, migration, bundle,
  importer, bootstrap, and runtime consumers. `markets.calendar_code` is nullable
  and has no FK/default; the legacy importer omitted it while the canonical
  bundle requires `TW_MARKET`. Root cause is classified as legacy-importer
  context omission / historical data drift; no schema migration is required.
- Added the dedicated bundle-derived `topicpilot-market-calendar-remediation`
  dry-run/apply command. Its only write set is `markets.calendar_code`; it fails
  closed on any non-calendar context, market topology, registry, instrument, or
  conflicting non-null calendar drift. Apply is atomic, postcondition-verified,
  rollback-safe, and idempotent.
- Corrected reference bootstrap dry-run/activation parity with one shared market
  validator covering code, name, exchange code, timezone, and calendar code.
  The disposable 005F fixture now blocks during bootstrap dry-run before any
  mutation; after calendar remediation, dry-run and activation reach READY at
  bundle-derived 2/507 (TPE 314, TWO 193).
- Fresh PostgreSQL targeted and regression tests passed (`9/9`, `27/27`), along
  with Ruff, migration downgrade/upgrade, OpenAPI drift, generated-contract
  idempotence, API client `3/3`, AST compile, and pip check. The CI-equivalent
  backend run reached 340 passed / 20 skipped / 59 deselected with only the
  known unrelated Windows schema-qualified `regclass` assertion failure.
- Production was not connected or mutated; no remediation/bootstrap retry,
  deploy, push, merge, G1/G2/G3, Canary, or Scheduler action occurred.
  `NEXT_TASK` and Data Governance HOLD remain untouched. Final status is
  `READY_FOR_MARKET_CALENDAR_REMEDIATION_INTEGRATION_REVIEW`.
## 2026-08-13 — TASK-FE-BE-TODAY-004C Daily Focus / Market Story FastAPI Wiring

- Started from `origin/main` at
  `8e0ffc713ccead047a97ea7b5c24c649cfa79230`, which includes the authoritative
  TASK-FE-BE-TODAY-004B-R shared Home resource and reconciliation. Daily Focus
  is wired from `HomeResponse.dailyFocus` through the existing
  `TodayHomeResource`; no second Home request or runtime client helper was
  added (`HOME_REQUEST_REUSED=YES`, `EXTRA_HOME_REQUESTS_ADDED=0`).
- Removed the formal-path hardcoded Market Story bullets and one-line headline
  from `TodayMarketPage.tsx`. The UI now renders backend-owned `headline` and
  `bullets` in backend order, preserving `mode`, `source`, `dataDate`, shared
  `asOf`, and `temporary` metadata. No browser narrative generation,
  summarization, ranking, sentiment, or business-rule calculation was added.
- Daily Focus uses the shared publication boundary: valid formal data remains
  `FORMAL`; backend `temporary=true` cannot render as formal and is shown as
  persistent `TEMPORARY`; explicit Preview remains `PREVIEW`; null, empty,
  incomplete, gated, or transport-error data is `UNAVAILABLE`. Hardcoded story
  data is never used as an error/loading fallback.
- Added focused coverage for resource reuse, backend headline/bullet authority
  and order, metadata preservation, FORMAL/TEMPORARY/PREVIEW/UNAVAILABLE
  mapping, null/empty/incomplete/error fail-closed behavior, and TODAY-002 /
  TODAY-003 regression. Focused tests passed `27/27`; frontend full tests and
  build passed `110/110`; API client `3/3`; TypeScript, targeted/full lint,
  OpenAPI gate/idempotence, Ruff, backend tests, diff check, and secret sanity
  scan passed. Full lint retains the pre-existing TopicDetailPage warning only.
- No backend/OpenAPI contract change, provider authority change, DATA-REF
  change, Lifecycle/Opportunity rule change, Production DB mutation, G1/G2/G3,
  Canary, Scheduler, deploy, push, main merge, or `NEXT_TASK` modification was
  performed. This worklog entry is append-only.

## 2026-08-13 TASK-FE-BE-TODAY-004C-R Daily Focus Reconciliation and Exact-SHA Main Integration

- Reconciled the isolated implementation commit `b4c6dfb71d720fece3f5114b3607ddfa07d7e045`
  onto the latest `origin/main` base `00b40762a9484d951d4cfe776b40557c64fb08fb`.
  Concurrent DATA-REF-005E/005F/005G and Stock-002B documentation/worklog
  history was preserved; the only replay conflict was this append-only worklog.
- The reconciled candidate is `8a851edab54fa626e03114a678916d0327563579`.
  `TodayHomeResource` remains the single shared Home request, Daily Focus reads
  backend-owned `dailyFocus`, and no frontend mock fallback, business-rule
  recomputation, backend route/schema, OpenAPI, generated-client, Production DB,
  provider, Lifecycle, Opportunity, Scheduler, Canary, or reference-bootstrap
  change was introduced by this task.
- Latest-candidate validation passed: focused Today regression `12/12`, frontend
  `110/110`, API client `3/3`, TypeScript, targeted/full lint (one pre-existing
  TopicDetailPage warning), demo snapshot, Ruff, OpenAPI drift, backend
  `313 passed / 48 skipped / 59 deselected`, disposable migration rollback/
  upgrade, reference bootstrap PostgreSQL `1 passed`, and Compose API/Web smoke.
- This reconciliation record is append-only. Main fast-forward, push, and
  exact-SHA CI remain pending the final freshness check. Production actions are
  none; `NEXT_TASK` and Data Governance HOLD remain untouched.

## 2026-08-13 TASK-FE-BE-TODAY-004C-R Post-Push Exact-SHA Verification

- Final freshness check passed with no remote movement. Main was fast-forwarded
  non-force from `00b40762a9484d951d4cfe776b40557c64fb08fb` to
  `47b416fcd71845d91c2ea5577f8f7d2a2b1dab45` and pushed to `origin/main`.
- Exact-SHA GitHub Actions run `31680309265` for
  `47b416fcd71845d91c2ea5577f8f7d2a2b1dab45` passed Backend/OpenAPI,
  Frontend, Docker Compose smoke, and Secret scan. Production actions remain
  none; no deploy, reference bootstrap, provider change, Lifecycle/Opportunity
  rule change, Scheduler, Canary, or `NEXT_TASK`/Data Governance HOLD change
  was made.

## 2026-08-13 TASK-DATA-REF-005H Integration, Exact-SHA CI, and Runtime Drift Stop

- Verified authoritative 005G commit
  `a009953c2c9270b6c9ffbaef11ab4fe435cd0242`, reconciled it in a fresh
  worktree onto the then-current `origin/main`, and non-force pushed application
  release SHA `00b40762a9484d951d4cfe776b40557c64fb08fb` with 0/0 synchronization.
- Local scoped PostgreSQL/reference tests `27/27`, frontend `104/104`, API client
  `3/3`, Ruff, migration rollback/upgrade, OpenAPI/generated contract, AST, pip,
  diff, and secret gates passed. Exact-SHA CI run `31678008530` passed all jobs,
  including Linux backend and Docker Compose smoke.
- Protected release workflow run `31678267907` validated the exact release and
  triggered only the Render API deploy hook; Sites packaging was skipped.
- Production operator evidence reported runtime and provider-lineage SHA
  `32f15f3c57240151bc5d35761e88c764448fa1cc`, not the authorized application
  release SHA. Audit proved it is an exact-CI-passing descendant with only Today
  frontend/test and append-only worklog changes, and no DATA-REF path drift, but
  005H did not authorize replacing release authority with that descendant.
- Production calendar remediation dry-run returned `PLAN` / `VALIDATED`, 507
  compatible instruments, NULL-to-`TW_MARKET` changes for TPE/TWO, and only
  `markets.calendar_code` in its write set. Bootstrap dry-run correctly blocked
  on the TPE calendar conflict, proving parity behavior; pre/post reference
  checks remained 2/0, inactive, and `NOT_READY`, proving zero mutation.
- No calendar apply, reference bootstrap/activation, G1/G2/G3, Canary, or
  Scheduler action occurred. `NEXT_TASK` and Data Governance HOLD are untouched.
  Final status is `BLOCKED_RUNTIME_SHA_DRIFT`; STOP pending explicit release-SHA
  authority or a new exact-SHA deploy.

## 2026-08-13 TASK-DATA-REF-005H-A Runtime Authority Rebind

- Applied the user's explicit authority to evaluate rebinding the 005H runtime
  from original release `00b40762a9484d951d4cfe776b40557c64fb08fb` to
  observed SHA `32f15f3c57240151bc5d35761e88c764448fa1cc` without
  rewriting the earlier runtime-drift stop record.
- Git merge-base and ancestor checks passed. The three intervening commits
  changed only Today frontend/test files and append-only `docs/AI_WORKLOG.md`;
  DATA-REF, reference runtime, remediation, provider authority, tests/contracts,
  and migrations had zero diff.
- Exact-SHA CI run `31680613603` for the observed runtime passed all jobs.
  `RENDER_GIT_COMMIT` and provider-lineage `buildSha` both matched it, and the
  prior Production dry-runs proved the calendar-only PLAN, bootstrap parity
  conflict, and unchanged pre/post reference state.
- Runtime authority is therefore rebound to
  `32f15f3c57240151bc5d35761e88c764448fa1cc`. No deploy, calendar apply,
  reference bootstrap/activation, G1/G2/G3, Canary, Scheduler, SQL mutation,
  `NEXT_TASK`, or Data Governance HOLD change occurred. Final status is
  `READY_FOR_TASK_DATA_REF_005I`; STOP pending a separately authorized 005I.

## 2026-08-13 TASK-DATA-REF-005I Gate 1 Runtime Authority Provenance Audit

- Operator Gate 1 stopped immediately because runtime
  `c75956336df03a1fd661a054b33b0c4845d4f159` did not equal the prior 005I
  authority `32f15f3c57240151bc5d35761e88c764448fa1cc`. No Production mutation,
  calendar apply, bootstrap, activation, or G1 occurred.
- Read-only Git audit passed: merge-base and ancestor relationship are exact;
  intervening commits are only the 005H docs stop record and rebind record;
  changed files are only `docs/AI_WORKLOG.md` and the 005H formal report.
  DATA-REF, reference runtime, provider, bundle, bootstrap, remediation, test,
  and migration paths have zero diff.
- c759 exact-SHA CI run `31694695626` passed Backend/migration/OpenAPI,
  Frontend, Secret scan, and Docker Compose smoke. Therefore c759 is
  documentation-only and behaviorally equivalent for the 005I reference and
  calendar paths.
- Prepared the dedicated report
  `TASK-DATA-REF-005I_RUNTIME_AUTHORITY_PROVENANCE_AND_REBIND_DECISION.md`.
  The rebind is ready for explicit approval only; authority was not silently
  changed and no Production command was run.

## 2026-08-13 TASK-DATA-REF-005I Production Execution Closure

- Closed the authorized 005I Production sequence using the operator evidence
  already captured; no Production command was rerun. Application/runtime
  authority was `c75956336df03a1fd661a054b33b0c4845d4f159`, runtime remained
  unchanged during execution, and the Production execution freeze remained
  active.
- Calendar remediation completed `APPLIED / CANONICAL`: only TPE/TWO
  `NULL -> TW_MARKET` changes were applied; market primary keys, codes,
  identity fields, and all 507 instrument rows were preserved. Postcheck
  passed and the second dry-run returned `NOOP / CANONICAL`.
- The canonical bundle hash matched. Bootstrap dry-run returned
  `PLAN / VALIDATED` with 37 reference rows and no non-reference writes;
  authorized activation returned `ACTIVATED / ACTIVE` transactionally with
  no non-reference writes.
- Reference postcheck returned READY: active registry, complete contexts, 24
  calendar dates, 7 trading statuses, 3 adjustments, 2 markets, 507 total
  instruments (TPE 314/TWO 193), and no missing markets, instruments,
  contexts, or duplicate identities. G1 passed.
- No G2, G3, Canary #2, Scheduler, DATA-REF-006, deploy, or documentation
  push was performed. Formal closure report:
  `TASK-DATA-REF-005I_PRODUCTION_CALENDAR_REMEDIATION_REFERENCE_BOOTSTRAP_AND_G1.md`.
  Final status is `READY_FOR_G2_AUTHORIZATION`; blocker is `NONE`.

## 2026-08-14 TASK-DATA-REF-006 G2 Authority Re-entry Audit

- Performed a repository-only, read-only authority audit after the 005I G1
  closure. No Production command, database connection, provider request,
  mutation, deploy, Scheduler change, G2, G3, or Canary action occurred.
- The deployment runbook and P3A handoff define G2 only as official
  TWSE/TPEx reachability and target-date availability; neither names an exact
  G2 preflight entrypoint or a complete read-only/shadow-safe contract.
- `topicpilot-provider-lineage` is provenance-only and performs no provider
  request. `topicpilot-reference-check` is the existing SELECT-only G1 check.
  `topicpilot-history-probe` is a Taishin historical capability probe, not the
  official TPE/TWO daily G2 path.
- The only checked-in CLI that invokes official daily providers is
  `topicpilot-live --mode post-close --once --run-date YYYY-MM-DD`. Its code
  creates run/attempt records, persists raw/timeline/canonical observations,
  refreshes tracking, and may run Topic Snapshot/Lifecycle. Its `--dry-run`
  returns before provider creation and only prints a scheduler decision.
- Because no unique non-mutating G2 authority exists, execution stopped with
  `FINAL_STATUS = BLOCKED_G2_AUTHORITY_AMBIGUOUS`. Runtime/G1 re-entry evidence
  remains operator-required. No flags were guessed and no mutating path was
  promoted to G2 preflight.
- Formal report:
  `TASK-DATA-REF-006_POST_G1_G2_AUTHORITY_REENTRY_AND_PROVIDER_DATA_PREFLIGHT.md`.
  `NEXT_TASK`, Data Governance HOLD, PUSH, and DEPLOY remain unchanged.

## 2026-08-14 TASK-DATA-REF-006A G2 Official Provider Read-Only Preflight

- Implemented a dedicated `topicpilot-provider-preflight --run-date
  YYYY-MM-DD --reference-version tw-reference-v1` operator path on isolated
  branch `codex/task-data-ref-006a-20260814`. The application/runtime
  authority remains `c75956336df03a1fd661a054b33b0c4845d4f159`; any local
  documentation/implementation commit SHA is distinct and is not a Production
  runtime authority.
- The path validates the explicit target date against the active reference
  session/calendar context, derives active EQUITY identity coverage from the
  database at runtime, and calls only the official one-date market-batch
  providers: TPE/TWSE `TWSE_OFFICIAL_DAILY` with
  `twse-official-daily.v2`, and TWO/TPEx `TPEX_OFFICIAL_DAILY` with
  `tpex-official-daily.v2`. Yahoo and Taishin cannot satisfy G2.
- The result is deterministic machine-readable JSON with per-market
  reachability, parse, target-date, data-availability, and full-coverage
  evidence. The command has an empty Production/non-reference write set and
  does not call live persistence, observations, tracking, snapshots,
  Lifecycle, Opportunity, or Scheduler paths. Failures are sanitized and do
  not expose DATABASE_URL or secrets.
- Added the canonical runbook and deployment/index links, plus unit and
  PostgreSQL boundary tests. Focused validation passed `24 passed / 1 skipped`
  without a configured database; the same PostgreSQL boundary test passed `1/1`
  against an isolated disposable database after loading the completed bundle.
  The CI-equivalent backend passed `322/322` with 49 PostgreSQL/environment
  skips and 59 research/governance deselections. Full Ruff, targeted format,
  Python compile, pip check, OpenAPI drift, migration upgrade/downgrade/upgrade,
  reference bootstrap PostgreSQL `1/1`, provider preflight PostgreSQL `1/1`,
  diff, and changed-file secret-value scans passed. The disposable database
  stack was removed after testing.
- No Production DB connection, provider request, G2/G3, Canary, Scheduler,
  deploy, push, `NEXT_TASK`, or Data Governance HOLD change occurred.
- Formal report:
  `TASK-DATA-REF-006A_G2_OFFICIAL_PROVIDER_READ_ONLY_PREFLIGHT_CONTRACT_AND_ENTRYPOINT.md`.
  Final status is `READY_FOR_G2_PREFLIGHT_INTEGRATION_REVIEW`; blocker is
  `NONE`.

## 2026-08-14 TASK-DATA-REF-006B G2 Preflight Integration and Release Handoff

- Fetched `origin/main` and verified current main authority remains
  `c75956336df03a1fd661a054b33b0c4845d4f159`. It is an ancestor of the 006A
  base `1c9938733d3befc2e3d6e7fffd5763197986d19f`; there are zero concurrent
  main commits after that base. The three local append-only documentation
  commits were replayed in order, then 006A was replayed cleanly in the
  dedicated 006B reconciliation worktree. No application-path conflict or
  historical-report rewrite occurred.
- G2 authority remains the dedicated read-only
  `topicpilot-provider-preflight --run-date YYYY-MM-DD
  --reference-version tw-reference-v1` path. Official TPE/TWO authority,
  adapter versions, market-batch semantics, explicit target-date validation,
  runtime-derived identity coverage, empty write sets, and no-live-persistence
  boundary were preserved. Existing live, live dry-run, lineage,
  reference-check, registry, migration, and OpenAPI behavior remains unchanged.
- Created formal report
  `TASK-DATA-REF-006B_G2_PREFLIGHT_INTEGRATION_EXACT_SHA_CI_AND_PRODUCTION_RELEASE_HANDOFF.md`.
  Release SHA, exact-SHA CI, protected deploy workflow, and post-deploy runtime
  evidence are recorded only after their respective gates; no Production G2
  command is run by this task.
- At this point Production DB connection/mutation, G2, G3, Canary, Scheduler,
  deploy, and push remain pending their explicitly ordered release gates.
  `NEXT_TASK` and Data Governance HOLD remain untouched.

- Integrated validation completed before release: focused provider suite
  `24 passed / 1 skipped`, PostgreSQL read-only boundary `1/1`, reference
  bootstrap PostgreSQL `1/1`, backend `322 passed / 49 skipped / 59 deselected`,
  Ruff, Python compile, pip check, migrations, OpenAPI drift, generated API
  contract/idempotence, API client `3/3`, frontend `110/110` plus build,
  isolated Compose PostgreSQL/API/Web smoke, diff check, secret-value scan,
  and CLI help/mutation-flag rejection all passed. Existing frontend lint has
  only the prior TopicDetailPage unused-variable warning.

## 2026-08-14 TASK-DATA-REF-006B Release Push, Exact-SHA CI, and Deploy Handoff

- Freshness check confirmed `origin/main` was still
  `c75956336df03a1fd661a054b33b0c4845d4f159`; the integrated release was
  pushed non-force to main at
  `3366ee61ba71a4f98ad886b53284e3faedbf44e0`. This is the application release
  SHA and must remain distinct from any later local documentation-only SHA.
- Exact-SHA CI run `31755965560` for `3366ee61...` passed Backend/migration/
  OpenAPI, Frontend, Secret scan, and Docker Compose smoke.
- Protected deploy workflow `31756161527` used exactly that release ref with
  `deploy_api=true` and `package_web=false`. Release validation and the Render
  API deploy hook passed; Sites packaging was intentionally skipped.
- No Production database connection, G2 provider request, reference bootstrap,
  activation, remediation, G3, Canary, or Scheduler action occurred. Runtime
  SHA and provider lineage still require operator evidence from the same
  authenticated Render runtime. `NEXT_TASK` and Data Governance HOLD remain
  untouched.
- This closure evidence is local-only after the release handoff and is not
  pushed. Final status is `OPERATOR_RUNTIME_EVIDENCE_REQUIRED`; blocker is
  runtime verification of `3366ee61ba71a4f98ad886b53284e3faedbf44e0`.

## 2026-08-14 TASK-DATA-REF-006B Runtime Authority Verification

- Operator evidence from the same authenticated Render runtime confirmed
  `RENDER_GIT_COMMIT` and `topicpilot-provider-lineage.buildSha` both equal
  `3366ee61ba71a4f98ad886b53284e3faedbf44e0`. Lineage status is `READY`.
- Provider authority remains canonical and market-batched: TPE uses
  `TWSE_OFFICIAL_DAILY` / `twse-official-daily.v2`; TWO uses
  `TPEX_OFFICIAL_DAILY` / `tpex-official-daily.v2`. Yahoo is verification-only
  and Taishin is intraday-only. Runtime SHA verification passed and G0 passed.
- No G2 preflight, provider request, Production database connection or
  mutation, G3, Canary, Scheduler, or further deploy was performed. The
  application release SHA remains distinct from local documentation SHA
  `7f37bdea1c5575669ff85392933e9e0e231b0eb9`; documentation remains unpushed.
- TASK-DATA-REF-006B final status is now
  `READY_FOR_G2_PRODUCTION_PREFLIGHT_AUTHORIZATION`; blocker is `NONE`.
  Stop and wait for explicit G2 preflight authorization.

## 2026-08-14 TASK-DATA-REF-006C G2 Official Provider Read-Only Preflight

- Verified the 006C repository authority: the exact operator entrypoint is
  `topicpilot-provider-preflight --run-date YYYY-MM-DD
  --reference-version tw-reference-v1`. The CLI requires an explicit ISO
  target date and the runbook explicitly forbids deriving it from the browser,
  local system date, or a hardcoded trading date.
- The supplied same-runtime evidence confirms application SHA and provider
  lineage `3366ee61ba71a4f98ad886b53284e3faedbf44e0`; G0 is PASS. The prior
  006B Production baseline remains the last verified G1 evidence: active and
  READY reference, 2 markets, and 507 instruments. No new 006C G1 check was
  represented as completed.
- 006C stopped fail-closed before any provider request because no explicit,
  authorized `G2_RUN_DATE` was supplied. Consequently TPE/TWO preflight,
  Production DB access, G2, G3, Canary, and Scheduler were not run or changed.
  The planned database boundary remains SELECT-only with empty production and
  non-reference write sets.
- Created formal report
  `TASK-DATA-REF-006C_PRODUCTION_G2_OFFICIAL_PROVIDER_READ_ONLY_PREFLIGHT_EXECUTION.md`.
  Documentation is local-only, with no push or deploy. Final status is
  `BLOCKED_G2_RUN_DATE_AUTHORITY_AMBIGUOUS`; blocker is an explicitly
  authorized G2 run date.

## 2026-08-14 TASK-DATA-REF-006C-A Explicit G2 Run-Date Authorization

- The operator explicitly authorized `G2_RUN_DATE=2026-08-13` and prohibited
  date substitution. Repository-level validation against the committed
  `tw-reference-v1` calendar passed: the date is Thursday and has no persisted
  `TW_MARKET` `HOLIDAY` or `SUSPENDED` row. `DATE_SUBSTITUTED=NO`.
- The exact Production sequence is preserved: same-runtime SHA/lineage check,
  `topicpilot-reference-check --reference-version tw-reference-v1`, then
  `topicpilot-provider-preflight --run-date 2026-08-13
  --reference-version tw-reference-v1`. The latter remains SELECT-only with
  empty Production and non-reference write sets and official TPE/TWO
  market-batch providers only.
- Production Phase 2/3 evidence and the G2 provider result have not yet been
  supplied by the authenticated Render runtime. No Production database
  connection, provider request, mutation, deploy, push, G3, Canary, or
  Scheduler action occurred. Created continuation report
  `TASK-DATA-REF-006C-A_EXPLICIT_G2_RUN_DATE_AUTHORIZATION_AND_PREFLIGHT_RESUME.md`;
  documentation is local-only.

## 2026-08-14 TASK-DATA-REF-006C-A Production G2 Preflight Result

- Operator evidence confirmed the authorized runtime remained
  `3366ee61ba71a4f98ad886b53284e3faedbf44e0`; provider-lineage `buildSha`
  matched and status was `READY`. Fresh G1 reference-check passed with active
  READY `tw-reference-v1`, 2 markets, 507 instruments, no missing markets or
  instruments, no duplicates, and complete reference context.
- The authorized date `2026-08-13` was a valid session date and was not
  substituted. The dedicated read-only G2 preflight reached both official
  market-batch providers with target-date matches and no fallback. TWO passed
  193/193 coverage; TPE failed closed at 313/314 coverage with
  `errorCode=PARTIAL_PROVIDER_COVERAGE` and `missingInstrumentCount=1`.
  The CLI did not emit the missing identity code, so none is inferred.
- The preflight reported `readOnly=true`, `productionWriteSet=[]`, and
  `nonReferenceWriteSet=[]`. No remediation, retry, live collector,
  persistence, G3, Canary, or Scheduler action occurred. Final status is
  `BLOCKED_G2_PROVIDER_COVERAGE_FAILURE`; the formal continuation report was
  updated append-only and remains local-only/unpushed.

## 2026-08-14 TASK-DATA-REF-006D G2 Missing Identity and Instrument Lifecycle Audit

- Audited the 006C TPE `313/314` failure against the committed bundle, status
  evidence, ORM/migrations, reference bootstrap, reference-check, provider
  preflight, official provider diagnostics, and no-trade contract. The single
  reconciled missing identity is `TPE:6806`: it remains in the canonical 314
  identity bundle and retained formal universe, while committed evidence marks
  it `DELISTED` effective `2026-06-23`; prior official row-level evidence
  records its TWSE no-row result.
- The root cause is not provider mapping or an identity deletion requirement.
  The model has partial lifecycle-shaped fields (`is_active`, `valid_from`,
  `valid_to`, and effective security identities), but bundle/bootstrap data do
  not populate instrument lifecycle dates/status. G2 expected identities are
  derived from active EQUITY instruments joined to active markets and do not
  apply `run-date` validity or lifecycle status. This is classified as
  `INSTRUMENT_LIFECYCLE_DATA_MISSING` plus
  `G2_DATE_EFFECTIVE_UNIVERSE_LOGIC_GAP`.
- The G2 CLI also emits only aggregate missing counts, not missing/extra codes;
  the 006C raw JSON therefore did not itself contain `6806`. No identity code
  was invented; the reconciliation uses repository bundle/status evidence and
  the prior exact official no-row diagnostic. The observability gap is recorded
  for 006E.
- No Production retry, provider request, mutation, deletion, remediation,
  bootstrap, activation, deploy, push, G3, Canary, or Scheduler action
  occurred. Formal report:
  `TASK-DATA-REF-006D_G2_MISSING_IDENTITY_AND_INSTRUMENT_LIFECYCLE_ROOT_CAUSE_AUDIT.md`.
  Final status is `AUDIT_COMPLETE_READY_FOR_006E`; next recommended task is
  `TASK-DATA-REF-006E Instrument Lifecycle / Date-Effective Universe Contract`.

## 2026-08-14 TASK-DATA-REF-006E Date-Effective Instrument Universe and G2 Lifecycle Eligibility Contract

- Implemented the shared provider-independent date-effective eligibility path
  in `services/api/src/topicpilot_api/instrument_universe.py`. It validates
  instrument/market validity ranges, lifecycle effective ranges and known
  lifecycle statuses, fails closed on malformed metadata, preserves physical
  identities, and derives sorted market universes for the explicit run date.
- Added migration
  `0029_task_data_ref_006e_instrument_lifecycle` and ORM model
  `ReferenceInstrumentLifecycle`. The reference-only bootstrap now validates,
  plans, writes, and idempotently rechecks lifecycle evidence in the same
  atomic reference transaction. Non-reference write set remains empty.
- Extended the canonical `tw-reference-v1` bundle with generated
  `instrument_lifecycles.json` derived from the approved status evidence.
  Bundle SHA is now
  `daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295`;
  6806 is represented as generic DELISTED evidence effective 2026-06-23,
  not as a hardcoded implementation rule.
- Updated G2 SELECT-only context loading to use the shared date-effective
  universe and to emit deterministic sorted `missingIdentityCodes` and
  `extraIdentityCodes`. Extra identities fail closed. Official providers and
  market-batch/fallback rules remain unchanged; reference-check remains the
  separate formal 507-identity G1 contract.
- Added lifecycle unit, bundle, bootstrap contract, PostgreSQL bootstrap,
  date-effective PostgreSQL context, missing/extra identity, migration, and
  architecture-boundary coverage. Disposable PostgreSQL migration upgrade,
  downgrade, re-upgrade, bootstrap, and 2026-08-13 context validation passed;
  targeted unit/contract tests passed.
- No Production DB connection, Production mutation, G2 retry, provider
  request, deploy, push, G3, Canary, Scheduler, NEXT_TASK, or Data Governance
  HOLD action occurred. Formal report:
  `TASK-DATA-REF-006E_DATE_EFFECTIVE_INSTRUMENT_UNIVERSE_AND_G2_LIFECYCLE_ELIGIBILITY_CONTRACT.md`.
  Final status is `READY_FOR_G2_DATE_EFFECTIVE_INTEGRATION_REVIEW`; next
  recommended task is 006F.

## 2026-08-14 TASK-DATA-REF-006G Reference Registry Version Transition and Lifecycle Bundle Activation Contract

- Audited the TASK-DATA-REF-006F blocker against the committed registry,
  bootstrap, reference-check, provider-preflight, migration, ORM, bundle, and
  runbook paths. Confirmed that `reference_data_version` is unique and the
  ordinary bootstrap correctly rejects same-version/different-hash overwrite;
  the missing capability was an explicit immutable rollover/provenance path.
- Implemented migration
  `0030_task_data_ref_006g_registry_transition` and ORM
  `ReferenceRegistryTransition`. The transition service derives
  `<source>-rollover-<bundle_sha256[:16]>`, preserves complete old registry
  provenance, binds lifecycle rows to the target registry, retires the prior
  ACTIVE set, activates exactly one validated target, and records the full
  from/to hashes in one atomic transaction.
- Added the secret-safe operator entrypoint
  `topicpilot-reference-transition --from-reference-version
  --expected-from-bundle-sha256 --bundle-dir --dry-run|--activate`. Dry-run is
  read-only; activation is reference-only; same-version overwrite, target hash
  collision, stale source precondition, incomplete lifecycle/catalogue state,
  and any failed post-write validation stop and roll back.
- Disposable PostgreSQL evidence passed: migration upgrade/downgrade/
  re-upgrade, dry-run no mutation, 3 transition tests, old registry RETIRED and
  provenance preserved, one ACTIVE target, idempotent NOOP, rollback on injected
  market conflict, untouched non-reference tables, 507 physical instruments,
  one 6806 lifecycle row, and date-effective 2026-08-13 TPE 313/TWO 193.
- Full backend CI-equivalent validation passed `360 passed / 24 skipped /
  59 deselected`; Ruff, Python 3.12 compile, pip check, CLI help, diff check,
  and changed-file secret scan passed. Research/governance tests remained under
  the existing exclusion boundary.
- Implementation commit is
  `be976963c1c6fc3b040390c3d7e6687322c365d0`; no push, merge, deploy,
  Production DB connection, reference activation, G2, G3, Canary, Scheduler,
  NEXT_TASK, or Data Governance HOLD change occurred. Formal report:
  `TASK-DATA-REF-006G_REFERENCE_REGISTRY_VERSION_TRANSITION_AND_LIFECYCLE_BUNDLE_ACTIVATION_CONTRACT.md`.
  Final status is `READY_FOR_REFERENCE_REGISTRY_TRANSITION_INTEGRATION_REVIEW`.
## 2026-08-13 TASK-FE-BE-STOCK-003 Formal Stock Search Contract & FastAPI Integration

- Started from fresh isolated worktree
  `codex/task-fe-be-stock-003-20260813` at current `origin/main`
  `71ba1ac27f2f72378df3df9266271de4f05f27d1`. The latest concurrent main
  change was DATA-REF-005F documentation only; no Stock/Today application
  change was included. The requested `docs/TOPICPILOT_CURRENT_HANDOFF.md`,
  `docs/DOCUMENTATION_AUTHORITY_INDEX.md`, and `docs/PROJECT_CONTEXT.md`
  paths were absent; available root/architecture/deployment authority files
  were used and the discrepancy is recorded in the formal report.
- Audited the existing `/api/v2/stocks` contract and confirmed no search,
  query, or keyword parameter existed. Implemented the smallest Case-B
  contract addition: optional `search` over formal stock code/name only,
  case-insensitive deterministic substring semantics with trim normalization.
  Search is database-side and backend-owned; no browser business filtering,
  ranking, topic inference, technical scoring, or semantic search was added.
- Wired FastAPI, production read-model SQL, OpenAPI, generated package/web
  types, the Stock Explorer search input, 250ms debounce, adapter trim,
  existing market/topic/updateMode/sort composition, offset reset, refresh
  preservation, stale-request protection, valid-empty/error distinction, and
  explicit Formal/Preview/Unavailable boundaries.
- Preserved disabled technical/chip/strategy controls, backend order, null
  semantics, main-topic authority boundary, and the shared sticky/full-height
  push Drawer. Application implementation commit is
  `3c8d10024f8172168f822cacf6b924b393bcfe1a`.
- Validation passed: focused Stock `24/24`, focused backend search `3/3`,
  frontend full suite/build `107/107`, API client `3/3`, backend release
  `313 passed, 42 skipped, 59 deselected`, TypeScript, lint, OpenAPI drift and
  generated idempotence, Ruff, diff check, and secret scan. Full lint retains
  one pre-existing `TopicDetailPage.tsx` warning. PostgreSQL integration tests
  were skipped locally because no test database URL was configured.
- No DATA-REF/provider/reference/Production files or semantics changed.
  Production DB, deploy, G1/G2/G3, Canary, Scheduler, `NEXT_TASK`, and Data
  Governance HOLD were untouched. This entry is append-only;
  `PUSH=NO`, `MERGE_MAIN=NO`, `DEPLOY=NO`, final status is
  `READY_FOR_STOCK_003_INTEGRATION_REVIEW`.

## 2026-08-14 TASK-FE-BE-STOCK-004 Topic Filter Formal Wiring & Advanced Filter Integration

- Created isolated continuation branch/worktree
  `codex/task-fe-be-stock-004-20260814` from the verified Stock-003
  implementation state. `STOCK_003_BASE_SHA` is
  `3c8d10024f8172168f822cacf6b924b393bcfe1a`; continuation base includes the
  Stock-003 documentation commit `2069ccc43bccaf079009fd30eef0049f72430c4d`.
  Fresh `origin/main` was `eb50d2d1e242290e2b9c6c95389bd7cd257caf26`, with 15
  commits of main drift intentionally not reconciled into this task.
- Audited the existing formal contracts. `/api/v2/stocks` already accepts
  `topic` as the canonical topic `slug`; `/api/v2/topics?limit=200&offset=0`
  is the formal topic-options source. This is Case A: no backend, OpenAPI, or
  generated-contract change was needed.
- Replaced Stock Explorer's result-set-derived topic options with the existing
  `fetchTopics()` formal/explicit-Preview resource. The advanced single-select
  preserves slug values, all/clear behavior, search/market/updateMode/sort
  composition, offset reset, backend order, and unavailable/disabled behavior.
  No hardcoded options or browser topic membership/filtering was added.
- Preserved Stock-003 search behavior, explicit Formal/Preview/Unavailable
  boundaries, disabled technical/chip/strategy controls, and the sticky,
  full-height push Drawer. Application commit is
  `b1d436b7a5e022d34f63d33be3b69882e3d9a081`.
- Validation passed: focused Stock `26/26`, frontend build/full suite
  `109/109`, API client `3/3`, TypeScript, lint, generated client
  idempotence, diff check, and secret scan. Full lint retains one pre-existing
  `TopicDetailPage.tsx` warning. Backend tests and OpenAPI gate were not
  required because no backend/OpenAPI contract changed.
- No DATA-REF/provider/reference/Production/Today/Topic Detail files or
  semantics changed. G0/G1/G2/G3, Canary, Scheduler, `NEXT_TASK`, and
  Production were untouched. This entry is append-only; `PUSH_MAIN=NO`,
  `MERGE_MAIN=NO`, `DEPLOY=NO`, final status is
  `READY_FOR_STOCK_004_INTEGRATION_REVIEW`.

## 2026-08-14 TASK-FE-BE-STOCK-004R Stock-003 + Stock-004 Main Reconciliation

- Fresh `origin/main` authority is
  `eb50d2d1e242290e2b9c6c95389bd7cd257caf26`; main drift from the Stock base
  is 15 commits. Provenance classified `DATA_REF=12`, `TODAY=3`,
  `HIST=0`, `STOCK=0`, `GOVERNANCE=0`, `UNKNOWN=0`; all Stock-003/004 lineage
  commits are present and continuous.
- Rebasing the Stock continuation onto current main produced one
  `docs/AI_WORKLOG.md` conflict. Resolved it append-preserving by retaining all
  main DATA-REF/Today entries and appending the Stock history; no application
  conflict or conflict marker remains. Reconciled local head before this
  report is `37bbc8d64afde66a3328470e0ac55a97d293d5f8`.
- Impact analysis is `REFERENCE=NO`, `PROVIDER=NO`, `MARKET_SEMANTICS=NO`,
  `POST_CLOSE_PERSISTENCE=NO`, `SCHEDULER=NO`, with API contract, frontend,
  and Stock feature impact limited to the already validated Stock-003/004
  scope. G1/G2/G3/Canary are preserved as
  `PRESERVED PASS / TASK-DATA-REF-009A`; no Production gates were rerun.
- Affected validation passed: focused Stock `26/26`, backend focused `3/3`,
  frontend build/full suite `115/115`, API client `3/3`, TypeScript, lint,
  OpenAPI gate, generated idempotence, Ruff, diff check, and secret scan.
  Full lint retains one pre-existing `TopicDetailPage.tsx` warning.
- Non-force main push is authorized after this pre-push pass. This entry is
  append-only; `PRODUCTION_MUTATION=NO`, `MANUAL_DEPLOY=NO`,
  `NEXT_TASK_MODIFIED=NO`, `STOCK_005_STARTED=NO`. Final push SHA and
  exact-SHA CI result will be appended after push.
