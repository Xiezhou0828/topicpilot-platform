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
