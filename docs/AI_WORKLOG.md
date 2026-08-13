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
