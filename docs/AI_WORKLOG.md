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

## 2026-08-14 TASK-GOV-CANONICAL-RECONCILIATION-001 009/009A consolidation

- Fetched `origin` before reconciliation and verified the current
  `origin/main=8402f141979e9924c9cfa8a1fc1b8e5b36f176ab`. The canonical task
  branch was independently at `0ffbdb991c603e2d23f41f317a22fbfe0c550d7b`;
  the source 009 worktree was at application SHA
  `edfeb0e59c53ccf957d2b100a4f4ec619f67b519` with only append-only evidence
  edits dirty.
- Reconciled only the date-effective lifecycle/G2 dependency, read-only G3
  market-semantics implementation, and 009 post-close eligible-universe,
  persistence, reconciliation, snapshot, and lifecycle propagation. Added
  the affected tests and formal TASK-DATA-REF-008/009/009A reports. No Today,
  Stock, Scheduler, deploy, Production mutation, or `NEXT_TASK` change was
  included.
- Preserved `TASK-DATA-REF-009A` as the named G0/G1/G2/G3/Canary baseline:
  runtime `edfeb0e…`, Canary `506/506`, failure `0`,
  `DOWNSTREAM_READY=true`. G1/G2/G3/Canary were not re-run because this is
  canonical consolidation rather than new Production behavior.
- Formal reconciliation report:
  `docs/reports/TASK-GOV-CANONICAL-RECONCILIATION-001_009_009A_RUNTIME_AND_EVIDENCE_CONSOLIDATION.md`.

## 2026-08-14 TASK-GOV-CANONICAL-RECONCILIATION-001 validation/push checkpoint

- Affected local validation passed: 44 focused unit/contract tests, Ruff,
  Python compile, and `git diff --check`. Five PostgreSQL integration tests
  were skipped because the local shell has no test database URL.
- Canonical reconciliation commit `0457de8e199e57d0a01cc3634169079b1fb44456`
  was pushed non-force to
  `codex/task-ops-023a-p3c-runtime-sha-audit-20260813`; PR #4 was opened for
  the repository's pull-request CI boundary. Exact-SHA CI is pending the
  GitHub Actions run; no runtime or baseline change was made in this checkpoint.

## 2026-08-14 Mainline C Today canonical reconciliation

- Canonical repository started at `7be817ec8e40b7a6cdce2fed9ff542ff2f4f7864`
  on `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` with unrelated user
  documentation/runtime changes already dirty. The accepted Today source was
  content-audited from the 004D continuation commit
  `4bb3a954760117a6e4aa424868101da5f1f20c2a`; unrelated Stock and DATA-REF
  patches were excluded.
- Reconciled the accepted shared Today Home path into canonical for Daily
  Focus, Main Topics, Heating/Cooling, Market Events, and Market Overview.
  Market Overview now uses the existing `GET /api/v2/home` /
  `HomeResponse.marketOverview` contract, with no hardcoded metrics, legacy
  snapshot fallback, browser aggregation, or mock fallback. Existing
  `FORMAL`, `TEMPORARY`, `PREVIEW`, and `UNAVAILABLE` semantics and metadata
  preservation remain explicit.
- Reconciled the associated Today adapter/tests and preserved the formal
  reports. Updated only the owner-document status in `PROJECT_CONTEXT.md`,
  `docs/ROADMAP.md`, and `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md` to state
  that wiring is complete while indices, turnover, narrative, volume trend,
  and derived market score remain formal-data follow-up gaps.
- Impact-based validation is required after the canonical commit: Today
  focused tests, frontend full tests/build, TypeScript, lint, generated-client
  idempotence, diff review, and secret-safe scan. G1/G2/G3/Post-Close Canary
  remain `PRESERVED PASS` because no protected DATA/runtime boundary changed.
- No Production mutation, deploy, scheduler activation, taxonomy/relation/
  scoring/recommendation/historical/reference change, remote push, or
  `NEXT_TASK` modification was performed. This entry is append-only.

## 2026-08-14 TASK-DATA-HIST-002B canonical reconciliation and closure

- Audited canonical `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` at
  `fcf2f2f8eca8c02b64b978203c3198086a86bf45`; the checkout was already dirty
  with unrelated user-owned changes and those changes were preserved.
- Reconciled isolated source commit
  `f4ae44b8d2f15ad1cc869b2b63cbb5bff25f8c27` as historical evidence. Canonical
  V2 already owns compatible official exchange, ingestion, rate-limit,
  lineage, reference-bundle, and idempotence paths; the isolated plain-table
  runner was not copied as a duplicate persistence contract.
- Verified local-only PostgreSQL evidence: 507 symbols, 63,826 rows, 0 extra
  universe rows, 0 invalid/duplicate/lineage/unexplained gaps, and correct
  6806 termination handling. No reseed, migration upgrade, Production write,
  scheduler, deploy, push, merge, or `NEXT_TASK` change occurred.
- Closure report: `docs/reports/TASK-DATA-HIST-002B_CANONICAL_RECONCILIATION_CLOSURE.md`.

## 2026-08-14 Mainline C Today cleanup checkpoint

- Canonical Today reconciliation commit is
  `4d11abe4c86d09c9019a334ad8a2feb836443611`. The accepted 004D continuation
  worktree was rechecked clean with no remaining explicit Today patch, then
  removed together with local branch
  `codex/task-fe-be-today-004d-20260814` after code and reports were preserved
  canonically.
- The canonical worktree still contains pre-existing unrelated user changes;
  they were not staged or modified. No remote push, deploy, Production
  mutation, protected-gate rerun, or `NEXT_TASK` change occurred. This entry is
  append-only.

## 2026-08-14 TASK-FE-BE-STOCK-005B canonical reconciliation and closure

- Re-audited canonical authority after the repository advanced to
  `017460da9d0a8fde2905e85f39e8670b5393b9c9`, with `origin/main` still at
  `26f635b95d8d88fd7ed7e43949583347f3ab5feb`. The canonical worktree remains
  dirty with unrelated user-owned Today/Topic/architecture/research and owner
  document changes; these were preserved.
- Rebased the clean Stock implementation worktree onto `017460d`, created a
  clean reconciliation commit, and cherry-picked it into canonical as
  `b78d4db` (`feat(stock): reconcile formal EOD read projection`). The exact
  Stock runtime/schema/test/OpenAPI/generated-client/report write set had no
  dirty-file collision. Owner-document changes were merged as separate
  append/minimal semantic updates; no blanket copy or `git add -A` was used.
- Canonical list/detail EOD projection, OpenAPI, generated client, focused
  tests, and formal report are now present. The canonical reconciliation
  impact checks passed after integration; protected DATA-REF gates remain
  preserved because no provider/reference/persistence/post-close boundary was
  changed.
- No Production mutation, Production DB access, push, deploy, scheduler,
  `NEXT_TASK`, provider, reference, migration, Historical, Today runtime,
  Topic runtime, taxonomy, relation, recommendation, or frontend UI change
  was performed. This entry is append-only.
