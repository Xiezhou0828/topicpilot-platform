# TopicPilot V2 Daily Progress

# 2026-08-12 - TASK-BE-024A Opportunity Decision Contract & Explainable Ranking

- Added independent Trend Continuation and Catch-up provisional ranking
  profiles above the existing V1 shadow strategies; global cross-strategy
  ranking remains disabled.
- Added deterministic Opportunity decision states (`SELECTED`,
  `WAITING_RETEST`, `WAITING_CONFIRMATION`, `DEFERRED`, `EXCLUDED`) and
  structured explanation/read contracts with provider-neutral identity,
  evidence, entry/support/risk, data, and upstream Topic context.
- Added deterministic frontend fixtures for all states and a schema-only
  calibration contract for forward 1/3/5/10-day and MFE/MAE/support-touch/
  invalidation/threshold-hit metrics. No outcome evaluation or optimization
  was run.
- Added focused TASK-BE-024A contract tests. Existing A/B replay remains
  as-of bounded and no-look-ahead; future C/D strategy slots remain explicit.
- Updated product/specification documents and added the
  `TASK-BE-024A_OPPORTUNITY_DECISION_CONTRACT_REPORT.md` report.
- No production API, DB/schema, frontend runtime, scheduler, daily market
  pipeline, Topic Score/Grade/Lifecycle, or NEXT_TASK change was made.

# 2026-08-12 - TASK-BE-024 Opportunity Engine V1 Strategies

- Added the shadow-only V1 multi-strategy layer in `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py`.
- Implemented `TREND_CONTINUATION` and `CATCH_UP` over explicit Theme Context, effective membership/data-quality facts, canonical daily OHLCV evidence, relative stock-vs-topic performance, and deterministic volume/structure/risk evidence.
- Added strategy-specific ranking and separate confidence labels. There is no global cross-strategy ranking and no feedback into Topic Score.
- Added explicit future strategy results for `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE`; they remain `FUTURE_NOT_IMPLEMENTED`.
- Added versioned `topic-opportunity-policy.provisional.1`, deterministic as-of replay, and PM calibration report artifacts. All numeric values remain `PROVISIONAL / TUNABLE`.
- Added focused strategy tests and updated Product Ideas, Product Roadmap, and Opportunity Engine Specification with V1 strategy architecture, reconciliation labels, and shadow/activation boundaries.
- No API, DB/schema/migration, frontend, scheduler, deployment, V1 source, production activation, or NEXT_TASK change was made.

# 2026-08-10 — TASK-LIVE-002

- Implemented the V2 live runtime boundary: provider-neutral intraday
  collector, bounded retries, failure rollback, scheduler, 60MA tracking,
  post-close full-universe path, freshness/attempt/run observability, and
  read-only operations API.
- Added the Taishin intraday adapter for 1m/3m/5m K-bars without changing the
  verified historical daily adapter. Added a bounded historical window probe so
  missing data is tested against the existing provider before being classified
  as `NO_DATA`.
- Real capability evidence: 2330/TPE and 2317/TPE each returned nine daily
  closes for 2026-07-28 through 2026-08-07; 0050/TPE retained an explicit
  `TAISHIN_CONNECT_TIMEOUT`; 2330/TPE returned 54 five-minute bars for
  2026-08-07.
- PostgreSQL migration `0022_task_live_002_runtime`, live persistence/idempotency
  integration, API smoke, OpenAPI contract refresh, Compose/Render runtime
  entry points, and focused tests passed.
- Current work-order state is `WAITING_LIVE_VALIDATION`: the market was closed
  during review, so no live-session claim was made. Private Taishin runtime
  deployment and official holiday configuration remain external prerequisites.
- Completed the Phase 7 institution collector design handoff and Phase 8
  technical runtime inventory. Institution data, unsupported technical modules,
  and downstream Topic synchronization remain explicitly blocked or deferred;
  no values or algorithms were invented.

## 2026-08-09 — PHASE-3.7-002C kickoff

- Registered `PHASE-3.7-002C` as `IN_PROGRESS` under Topic Formula Research & Plug-in.
- Scope is limited to a deterministic, public-safe synthetic replay corpus and cross-case execution through the verified 002A harness.
- No candidate formula, expected score, production data, persistence, API, frontend, V1, Recommendation, Lifecycle, or Theme Governance change is authorized.
- Completed `PHASE-3.7-002C` as `PASS / VERIFIED`: strict synthetic corpus loading, canonical hashing, public-shape validation, cross-case execution, and deterministic run manifests are implemented.
- Validation: 23 focused Formula Research tests and 116 full backend tests passed; 22 PostgreSQL-dependent tests skipped without a database URL; fixture round-trip, Ruff, formatting, and diff checks passed.

## 2026-08-09 — PHASE-3.7-002D kickoff

- Registered `PHASE-3.7-002D` as `IN_PROGRESS` for explicitly configured, research-only participation/diffusion candidates.
- Recorded primary-source support from OECD/JRC, The Conference Board, and the Federal Reserve, together with the explicit inference and production limitations.
- No default weights, Grade thresholds, Confidence formula, Eligibility cutoff, production formula, persistence, API, frontend, or V1 change is authorized.
- Completed `PHASE-3.7-002D` as `PASS / VERIFIED`: strict/diffusion component candidates, mandatory explicit weighted aggregation, source/configuration lineage, and a separate count-evidence corpus are implemented.
- Validation: 39 focused Formula Research tests and 132 full backend tests passed; 22 PostgreSQL-dependent tests skipped without a database URL; candidate fixture round-trip, Ruff, formatting, and diff checks passed.

## 2026-08-09 — PHASE-3.7-002E kickoff

- Registered `PHASE-3.7-002E` as `IN_PROGRESS` to join the verified corpus and candidate specifications into a deterministic, locally runnable research experiment.
- Scope includes a strict manifest, integrated no-ranking report, local CLI, and README usage instructions.
- No real market history, predictive evaluation, production activation, persistence, API, frontend, or V1 change is authorized.
- Completed `PHASE-3.7-002E` as `PASS / VERIFIED`: strict manifest/corpus lineage, deterministic cross-case execution and analysis, integrated no-ranking report, and the installable local CLI are implemented.
- Validation: 45 focused Formula Research tests and 138 full backend tests passed; 22 PostgreSQL-dependent tests skipped without a database URL. Two installed CLI runs produced byte-identical reports; Ruff and formatting checks passed.

## 2026-08-09 — PHASE-3.7-002F kickoff

- Confirmed that V2 has effective-dated membership, Observation Timeline, and canonical PRICE foundations but lacks an approved classification policy, complete historical research dataset, and governed Leader Set history.
- Registered `PHASE-3.7-002F` as `IN_PROGRESS` to bridge explicitly preclassified point-in-time CORE/Leader evidence into the verified research-count and replay contracts.
- No price classifier, threshold, window, production formula, persistence, API, frontend, or V1 change is authorized.
- Completed `PHASE-3.7-002F` as `PASS / VERIFIED`: strict point-in-time evidence loading, effective-membership and Leader-subset validation, missing-safe participation counts, and deterministic conversion into the standard research corpus are implemented.
- Validation: 54 focused Formula Research tests and 147 full backend tests passed; 22 PostgreSQL-dependent tests skipped without a database URL. Fixture/corpus replay, Ruff, and formatting checks passed.

## 2026-08-09 — PHASE-3.7-003A kickoff

- Completed `PHASE-3.7-003B` as `PASS / VERIFIED`: the customer Topic Intelligence dashboard/detail route, typed adapter, API unavailable state, and nullable API-provided metrics are implemented without browser-side scoring or boundary changes. Focused API/integration tests (`8 passed`), frontend lint, frontend production build, and `git diff --check` pass.

- Registered the first Topic Intelligence API work order after completing the Formula Research infrastructure boundary.
- Scope is one deterministic GET endpoint over the verified ephemeral runtime. Its default provider remains unavailable until a separately approved production runtime/data source exists.
- Legacy `topic_snapshots`, PostgreSQL persistence, formulas, Recommendation, frontend, and V1 are explicitly excluded.
- Completed `PHASE-3.7-003A` as `PASS / VERIFIED`: the endpoint, deterministic serializer, nullable business outputs, evidence/quality lineage, fail-closed default provider, dependency override, and API documentation are implemented.
- Validation: 11 focused API/runtime tests and 153 full backend tests passed; 22 PostgreSQL-dependent tests skipped without a database URL. OpenAPI/default-503 smoke, Ruff, formatting, documentation links, and diff checks passed. One pre-existing Starlette `TestClient`/`httpx` deprecation warning remains.
- Stopped after API verification and governance acceptance as requested. No subsequent work order was opened.

## 2026-08-08 — PHASE-3.7-001F

- Implemented the Topic Intelligence integration runtime from FeatureAggregate through TopicScorer into deterministic, traceable per-topic outputs.
- Preserved eligibility-first execution and deferred formulas, persistence, Recommendation, and Theme Governance.

## 2026-08-08 — Theme Governance & Knowledge System planning

- Recorded the conceptual Theme Governance & Knowledge System in the [canonical architecture design](architecture/THEME_GOVERNANCE_KNOWLEDGE_SYSTEM.md). The design separates Theme Knowledge, Theme Governance, Theme Intelligence, and downstream Recommendation; preserves the News=Evidence/Explainability rule; and defines Theme Discovery as proposal generation rather than automatic canonical promotion.
- Recorded the one-Theme-identity rule across Candidate, Approved, Rejected, Archived, and other governance states, plus ThemeVersion, ThemeMembership, ThemeRelationship, ThemeEvidence, and append-only GovernanceEvent concepts for lineage and deterministic historical replay.
- Registered `THEME-GOVERNANCE-KNOWLEDGE-001` as `PLANNING / NEEDS PM DECISION`. No code, ORM, PostgreSQL schema, migration, API, frontend, crawler, clustering runtime, candidate score formula, or automatic knowledge promotion was authorized. Next workshop: Theme Governance State Machine.

## 2026-08-08 — Architecture Freeze Batch #2 (PM-003–PM-007)

- Completed the documentation-only freeze for PM-003 through PM-007. PM-003 Confidence, PM-004 Grade, PM-005 Topic Score composition, and PM-006 Scoring Eligibility are fully frozen at the semantic boundary with rationale, examples, and responsibility separation recorded in the canonical inventory and Topic Engine contract.
- PM-007 is partially frozen at the policy layer: bounded score direction (`0–100` recommended), feature-specific normalization before aggregation, parallel Breadth/Leadership components, transparent versioned aggregation, and explainability-first behavior.
- Exact normalization formulas, weights, thresholds, and aggregation equation remain intentionally Formula Pending until historical validation is available. No code, schema, migration, persistence, API, or frontend change was made.

## 2026-08-08 — Architecture Freeze and documentation governance

- Accepted [ADR-003](architecture/ADR-003_TOPICPILOT_PRODUCT_POSITIONING.md) as the decision record for product positioning and engine responsibilities.
- Merged the approved current product truth into the existing [Product Direction and Surfaces Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md); removed the duplicate Product Vision and Core Principles files.
- Established the four-layer documentation model and canonical authority map in the [Architecture Book](architecture/README.md#documentation-governance-and-single-source-of-truth).
- Redirected Project Context, Roadmap, Work Orders, architecture overview, and ADR indexes to their canonical authorities instead of retaining copied permanent rules.
- Confirmed documentation-only scope: no implementation logic, scoring formula, persistence, API, frontend, database, or deployment change was made.

Append-only engineering log. Entries describe V2 only; V1 remains the formal production system.

## 2026-08-09 — PHASE-3.5-002B validation continuation

- Re-audited the still-open Normalization Runtime work order before advancing the roadmap.
- Reformatted the Normalizer package and focused tests, replaced star imports with explicit contracts, and removed one unused runtime lookup; Ruff check/format now pass for the scoped package and tests.
- Validation: 4 focused Normalizer tests and 158 full backend tests passed; 22 PostgreSQL-dependent tests remained skipped without a database URL.
- Attempted `infra/scripts/validate.ps1 -SkipMigration`; Docker could not connect to the local PostgreSQL daemon, so database connectivity, persistence, rollback, Alembic, and full validation evidence remain pending. `PHASE-3.5-002B` remains `IN_PROGRESS`.

## 2026-08-09 — Roadmap status reconciliation

- `PHASE-3.7-003B` and `PHASE-3.7-003C` are recorded as `PASS / VERIFIED` in the work-order register and Project Context; the earlier 003A entry is historical and the register/Roadmap are authoritative for current status.

# 2026-08-09 — PHASE-3.7-003C registration

- Registered `PHASE-3.7-003C` as `IN_PROGRESS` after the verified completion of 003B; reconciled the pre-existing misnumbered 004A draft into this canonical work order.
- Authorized the Recommendation Read Model Boundary: immutable deterministic contracts/runtime downstream of Topic Intelligence, explicit explainability, and fail-closed unavailable/deferred handling.
- Excluded ranking formulas, prediction, trading/entry language, portfolio management, persistence/schema changes, production activation, Theme Governance, and unrelated roadmap work.

- Completed `PHASE-3.7-003C` as `PASS / VERIFIED`: immutable versioned Recommendation read model, explicit candidate-fact boundary, deterministic ordering, explainability, and fail-closed unavailable/deferred handling are implemented.
- Validation: 10 focused Recommendation/Topic Intelligence tests passed; Ruff and `git diff --check` passed. One pre-existing Starlette/httpx deprecation warning remains.

- Completed 003C Fix-001: Recommendation items now carry immutable `TopicIntelligenceLineage` (runtime/policy/feature/aggregation identity, eligibility, score, grade, confidence, components, and nullable evidence reference). `runtime=None` now yields `UNAVAILABLE` with `as_of=None`; inconsistent upstream identity fails closed. Focused validation evidence recorded after final test run.
- Fix-001 validation: focused `13 passed`; backend regression `158 passed, 22 skipped` (PostgreSQL tests skipped without database URL); Ruff, format, and `git diff --check` passed. The existing Starlette/httpx deprecation warning remains.

## 2026-08-08 — Phase 3.6-002A implementation

- Registered `PHASE-3.6-002A` as `IN_PROGRESS` for Admin/Data Explorer detail and ERD work.
- Completed Fix-001 for `PHASE-3.6-002A`: interactive ERD, audit lineage, topic ancestry, import filters, and governance-test path correction. Status: `PASS / VERIFIED`.
- Added read-only instrument/topic detail APIs and pages, import run/artifact/record drill-down, shared Admin navigation, relation/import list routes, and metadata-derived ERD graph nodes/edges with card fallback.
- Preserved the GET-only Admin boundary and customer-facing route separation. Validation is in progress; the environment currently exposes a pre-existing Admin governance test incompatibility and the web build exceeded the local validation timeout.

## 2026-08-05

- Progressed Database Foundation through Identity, Topic, and Instrument–Topic Relationship domains (3.4-001 through 3.4-004).
- Hardened the Alembic migration chain and associated domain/migration tests.
- Advanced Phase 3.4-005 Market Data Source & Raw Observation Foundation; final runtime validation remains pending.
- Advanced validation automation; the validation framework remains in progress until PostgreSQL/runtime evidence is recorded.

## 2026-08-06

- Started and completed the V2 project-governance/documentation boundary layer.
- Added the V2-only project context and roadmap, updated the canonical architecture overview, and recorded the daily handoff.
- Documented the V1/V2 boundary and mandatory repository verification rules; no V1 files were modified.
# 2026-08-07 — Fix-003

- Refactored the V2 ORM import surface into explicit implemented-domain modules.
- Removed future payload-only ORM skeleton registration and the malformed `common` declaration.
- Split V2 repositories into base, observation-timeline, and canonical-observation modules.
- Added architecture-freeze metadata and repository-boundary regression tests.
- Preserved Alembic head `0019`; no migration was added.
# 2026-08-07 — Phase 3.5-002B Fix-001

- Runtime correctness work is **IN PROGRESS**: neutral `RuntimeResult`, UUID-preserving envelope, context-driven registry request, anti-successor correction lookup, and explicit transaction ownership are implemented.
- Focused normalizer tests: 4 passed. Full PostgreSQL and validation evidence remains pending.

# 2026-08-07 — V2-VALIDATION-DEBT-001

- Fix-001 completed: detector timeout tests use an injectable monotonic clock,
  preserving deadline semantics; focused detector tests: 10 passed.
- Fix-002 completed in the test boundary: synthetic-news uses per-run unique
  identifiers and a scoped transaction rolled back after each test.
- PostgreSQL-focused validation remains pending because this environment has
  no `TEST_DATABASE_URL` or `DATABASE_URL`; the synthetic-news test skipped.
- Work order and Phase 3.5-002B remain IN_PROGRESS / not VERIFIED pending the
  PostgreSQL, full-suite, Alembic, API smoke, and validation-script evidence.

# 2026-08-07 — Phase 3.6-001

- Created the read-only V1→V2 legacy import foundation: typed batches/manifests,
  explicit field mappings, stable-key validation, lineage contracts, and an
  I/O-free orchestration interface.
- Inventoried markets, instruments/stocks, topics, instrument-topic relations,
  market-data sources, and reference data.
- No V1 files, V1 behavior, schema, provider adapter, scheduler, or production
  data was changed. Ready for PM review.

# 2026-08-07 — Phase 3.6-001A

- Added the canonical UTF-8 CSV/TSV export contract, artifact SHA-256 manifest,
  canonical record hashing, and delimiter parsing primitives.
- Added validation-only dry-run reports for stable keys, required fields,
  unsupported fields, duplicates, conflicts, and deterministic counters.
- No V1 data was read and no PostgreSQL, scheduler, adapter, synchronization, or
  cutover path was invoked. Ready for PM review.

# 2026-08-07 — Phase 3.6-001A Fix-001

- Fixed warning-only validity counting, full composite stable-key lookup,
  canonical mapped-payload hashing, and None/empty-string validation parity.
- Focused legacy-import tests: 5 passed; full backend tests: 65 passed, 22
  PostgreSQL tests skipped because no database URL was configured. The work order
  remained pending only for Ruff cleanup.

# 2026-08-07 — Phase 3.6-001A Fix-002

- Completed Ruff cleanup limited to the legacy_import package and focused dry-run test.
- Ruff check/format, focused tests (5 passed), full backend tests (65 passed, 22
  PostgreSQL tests skipped without a database URL), compile/import check, and
  `git diff --check` all passed.
- Phase 3.6-001A is now **PASS / PM Approved**. No V1 data or PostgreSQL write
  path was touched; the first real read-only V1 export dry run may begin.
# 2026-08-07 — Phase 3.6-001B Fix-001

- Implemented minimal import audit persistence and the transactional V1-to-V2 writer. Real PostgreSQL dry-run/import evidence remains pending.

# 2026-08-07 — Phase 3.6-001B kickoff

- Verified the V2 repository, existing legacy-import contracts, ORM, and Alembic head `0020_phase3_5_002a_reference_registry`.
- Resolved the four read-only TSV artifacts under `C:\Users\acer\Desktop\題材領航\input\` and recorded SHA-256 provenance in the Phase 3.6-001B work order.
- Registered the full Phase 3.6-001B work order. No V1 file or PostgreSQL row was modified.
- Write phase is currently stopped: the existing 0020 schema has no lineage persistence table and no approved real V1-to-ORM writer is present.
- 2026-08-07 — Phase 3.6-001B Fix-002: removed the per-export run uniqueness
  trap, added per-run artifact persistence, and implemented explicit
  `topic_hierarchy` writing with fail-closed orphan handling. The four local
  source hashes matched the recorded work order (row counts 19/107/800/130).
  Focused tests and Ruff passed. PostgreSQL execution was not attempted because
  no database URL is configured; status remains IN_PROGRESS.
## 2026-08-07 — Phase 3.6-001B

- PostgreSQL healthy; Alembic upgraded from `0020` to `0021_phase3_6_001b_import_audit`.
- Source verification and dry run: 1,594 valid, zero rejected/conflict/warning/blocker.
- First transaction committed 2 markets, 507 instruments, 130 topics, 107 hierarchy edges, and 848 relations (existing domain totals include prior 1 market and 1 instrument).
- Identical rerun committed a second audit run: all 1,594 records were `NOOP`; target UUIDs and domain row counts were unchanged.
- Focused legacy/domain tests: 10 passed. Ruff and `git diff --check`: passed.
- Governance cleanup synchronized all authoritative status documents: Phase 3.6-001B is `COMPLETED / POSTGRESQL IMPORT VERIFIED` and V2-VALIDATION-DEBT-001 is `PASS / VERIFIED`.

## 2026-08-07 — Product direction freeze and Phase 3.6-002 registration

- Historical note: this entry recorded the then-current two-surface direction. Its product-positioning wording and redesign assumption were superseded and clarified by the 2026-08-08 [Product Direction and Surfaces Contract](architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md) and [ADR-003](architecture/ADR-003_TOPICPILOT_PRODUCT_POSITIONING.md).
- The current rule is not restated in this historical log; consult the canonical product contract. In particular, the existing React UI remains the customer product surface and this history does not authorize a replacement frontend.
- Registered `PHASE-3.6-002 Admin/Data Explorer Foundation` as `PLANNED`. The planning-first scope starts with ERD/schema visualization, read-only browsing of PostgreSQL master data and LegacyImport audit/history, and API/Alembic/row-count health summary. No CRUD writes or customer redesign are authorized.
- Preserved the transition source-of-truth rule: Google Sheets V1 remains formal production source through export -> dry run -> audited PostgreSQL import; PostgreSQL is the long-term master-data target.
- The stale Alembic assertion now targets `0021_phase3_6_001b_import_audit`; the synthetic Phase-1 stock fixture now generates a unique code within the unchanged `varchar(16)` production contract.

## 2026-08-07 — Phase 3.6-002 implementation

- Delivered the read-only Admin/Data Explorer MVP: dashboard counts/health, dedicated admin API, metadata-derived schema explorer, and operator routes `/admin` and `/admin/schema`.
- Added read-only markets, instruments, topics, instrument-topic relations, and LegacyImport run browsing endpoints with pagination/search where applicable.
- Registered LegacyImport audit models in the V2 SQLAlchemy metadata registry. CRUD, auth redesign, customer redesign, and engine work remain excluded.
- 2026-08-08: Registered `PHASE-3.7-001` as `IN_PROGRESS`. Topic Engine foundation is limited to an explicit input bundle, pure deterministic state calculation, hierarchy-aware membership coverage, and PM-deferred business scoring formulas.
# 2026-08-08

## PHASE-3.7-002A kickoff

- Reconciled the canonical Scoring Policy Inventory so PM-001 through PM-007 appear as one current state instead of stale pre-freeze rows plus appended decisions.
- Registered `PHASE-3.7-002A Topic Formula Research Harness` as `IN_PROGRESS` under the Roadmap's Topic Formula Research & Plug-in capability.
- Scope is limited to deterministic research-only candidate execution, validation, comparison, and replay digest. No formula, production default, persistence, API, frontend, V1, Recommendation, Lifecycle, or Theme Governance change is authorized.
- Completed `PHASE-3.7-002A` as `PASS / VERIFIED`: canonical candidate execution, fail-closed output validation, policy-configuration lineage, per-topic comparison, and deterministic replay digest are implemented.
- Validation after final changes: 18 affected focused tests passed; full backend 106 passed with 22 PostgreSQL-dependent skips; Ruff and modified-file formatting passed.
- Registered `PHASE-3.7-002B` as `IN_PROGRESS` for deterministic descriptive analysis and JSON-safe export of research-only candidate results; ranking, winner selection, future-return validation, and production activation remain excluded.
- Completed `PHASE-3.7-002B` as `PASS / VERIFIED`: deterministic candidate distributions, null-safe pairwise differences, lineage-preserving JSON export, and analysis digest are implemented without ranking or production activation.
- Final validation for 002A + 002B: 17 focused Formula Research tests passed; full backend regression 110 passed with 22 PostgreSQL-dependent skips; Ruff and modified-file formatting checks passed.

- Implemented PHASE-3.7-001A Topic Feature Contract foundation: immutable results, deterministic evaluator, membership coverage/counts, hierarchy quality, observation availability, and shared coverage context with TopicState.
- PM-deferred: price/return windows, breadth, momentum, technical/news features, aggregation weights, and S/A/B/D thresholds. 001A validation is recorded in its work order.

## 2026-08-08 — PHASE-3.7-001B

- Registered the non-conflicting runtime/aggregator work order before coding.
- Added explicit immutable runtime configuration and deterministic score-free per-topic aggregation with raw feature evidence and quality summaries.
- PM-deferred: price/return windows, breadth/momentum/technical/news features, weights, Topic Scorer formulas, S/A/B/D thresholds, and aggregate persistence/replay identity.
## 2026-08-08 — PHASE-3.7-001C kickoff

- Registered `PHASE-3.7-001C` as `IN_PROGRESS` after confirming no conflicting work-order ID.
- Added immutable `ScoringInput`, `ScoringPolicy`, and `TopicScore` contracts with aggregate evidence traceability and deferred nullable business outputs.
- No scoring formulas, persistence, migrations, API/frontend, admin, or provider adapters were added.
- Verification: focused tests `20 passed`; full backend `88 passed, 22 skipped` without PostgreSQL URL; Ruff and `git diff --check` passed. 001C is `PASS / VERIFIED`.

## 2026-08-08 — PHASE-3.7-001D PM-001

- Frozen Breadth semantics as Market Participation: current participation breadth is the Static interpretation; historical expansion/contraction is Dynamic interpretation and belongs to lifecycle analysis.
- Frozen the conceptual Breadth population as CORE topic members, with current primary-topic membership as the default basis. Exact derivation, numeric weight cutoff, formula, windows, normalization, weights, and thresholds remain `NEEDS PM`.
- Clarified that Recommendation may consider secondary-topic members downstream when a topic is strong, but those candidates do not participate in Topic Strength unless they are core members. No code, schema, or migration changes.

## 2026-08-08 — PHASE-3.7-001D PM-002

- Frozen Leadership semantics: Leadership measures whether a topic's recognized representative Leader Set supports the current topic move; it is complementary to Breadth and is not a single leader or daily top-gainer/market-cap/volume ranking.
- Frozen the conceptual Leader Set as a semi-static, slow-changing, versionable set primarily drawn from CORE topic members. Stable Leader identity is separate from today's Leadership evidence; high-volatility and large-cap/structural representatives may coexist without separate v1 categories.
- Preserved the Topic Engine/Recommendation boundary: downstream secondary recommendations cannot retroactively change the Leader Set or Topic Leadership. Existing Demo/API `leaders` lists are not automatically the approved Leader Set. No code, schema, or migration changes.
- Kept exact eligibility, update cadence/persistence, leader count, evidence inputs, contribution/formula, normalization, thresholds, and weights as `NEEDS PM`.

## 2026-08-08 — PHASE-3.7-001E Fix-001

- Corrected Topic Scorer runtime ordering so eligibility gates component collection and all scoring providers.
- Ineligible results preserve evidence and identity/status traceability while returning null score, grade, and confidence; eligible deferred results collect components and confidence only after the gate.
- Focused Topic Scorer/Topic Engine tests: 6 passed. Full backend tests: 91 passed, 22 PostgreSQL-dependent tests skipped without a database URL. Ruff check/format and `git diff --check` passed.
- Governance cleanup: PHASE-3.7-001D / PM-001 is now `PASS / PM Approved`; scoring formulas and mechanics remain deferred.

## 2026-08-09 — Phase 3.5-002B final verification

- Completed the Normalization Runtime acceptance matrix without changing V1 or
  the existing customer React surface. Added focused PostgreSQL integration
  coverage for multi-family persistence, idempotent reruns,
  correction/supersession, missing-reference fail-closed behavior, and atomic
  rollback on persistence failure.
- Focused Normalizer unit tests: `4 passed`; focused PostgreSQL runtime tests:
  `4 passed`; full backend with PostgreSQL: `184 passed`, `2 warnings`.
- Ruff/format and `git diff --check` passed. Alembic upgrade/head consistency,
  API smoke (`/healthz`, `/readyz`, stock list, existing web container), and
  `infra/scripts/validate.ps1` all passed; validation summary: `READY`.
- `PHASE-3.5-002B` is now **PASS / VERIFIED**. No new downstream work order was
  opened in this turn; execution stops here for handoff as requested.

# 2026-08-09 — Topic Intelligence MVP Phase 4-6 continuation

- Confirmed `PHASE-3.7-003B` Customer Topic Dashboard remains PASS / VERIFIED
  on the existing React customer surface; no replacement frontend was created.
- Completed `PHASE-3.7-003D` Recommendation MVP API: added the read-only
  `/api/v1/recommendations/latest` contract, stable unavailable problem state,
  OpenAPI schemas, and lineage-preserving focused tests. No provider, ranking,
  trading behavior, persistence, or V1 change was introduced.
- Completed `PHASE-3.7-003E` Historical Validation / Calibration Review: added
  deterministic research-only score/outcome pairing, coverage and descriptive
  correlation metrics, digest-protected reports, and explicit
  `PM_REVIEW_REQUIRED` calibration state. No formula, weight, threshold,
  winner selection, or production promotion was added.
- Updated the Roadmap, Work Order register, Project Context, and individual
  work orders. The next authorized action is PM review of the historical report;
  production Topic Intelligence/Recommendation providers remain intentionally
  unavailable until separately approved.

## 2026-08-09 — PHASE-3.7-003F A-stage PM Formula Approval

- Confirmed that the Phase 4–6 capability sequence is complete and verified:
  Customer Topic Dashboard, Recommendation MVP API, and Historical Validation /
  Calibration Review.
- Registered `PHASE-3.7-003F` as `NEEDS_PM_DECISION` for the next roadmap gate:
  PM Formula Approval.
- Added the PM Formula Approval Brief as the single review entry point. It
  separates frozen semantic boundaries from Formula Pending mechanics and
  provides a decision matrix, approval record template, and implementation
  unlock conditions.
- No formula, weight, normalization, threshold, provider activation,
  persistence, API, frontend, V1, or Theme Governance change was made.
- A-stage governance is complete; B/C implementation is intentionally blocked
  until the PM supplies the exact policy decisions and approval record.

## 2026-08-09 — PHASE-3.7-003G A-stage Policy Approval Guard

- Registered `PHASE-3.7-003G` as `IN_PROGRESS` under the PM Formula Approval
  handoff.
- Defined a formula-agnostic guard for approval-record provenance, status,
  policy identity, production scope, and rollback metadata.
- The guard is permitted before PM formula approval because it only blocks
  incomplete or unapproved activation; it does not calculate, select, or run a
  Topic Score policy.
- Completed `PHASE-3.7-003G` as `PASS / VERIFIED`: immutable approval metadata,
  deterministic allow/block decisions, stable fail-closed reason codes, and a
  raising helper for future provider factories were implemented.
- C validation: 11 focused Guard tests; 176 full backend tests with 26
  PostgreSQL-dependent skips; 9 Topic Intelligence/Recommendation API tests;
  Ruff, formatting, and `git diff --check` passed.
- The current API defaults remain unchanged and fail-closed; PM Formula
  Approval and provider activation remain separate future work.

## 2026-08-09 — PHASE-3.7-003H A-stage Policy Approval Artifact Adapter

- Registered `PHASE-3.7-003H` as `IN_PROGRESS`.
- Defined a strict JSON-compatible parse/export boundary for the PM Formula
  Approval record, including exact fields, schema version, canonical dates, and
  fail-closed handling for missing/unknown/invalid values.
- No formula, policy selection, approval creation, provider activation,
  persistence, API, frontend, V1, or Theme Governance change is authorized.
- Completed `PHASE-3.7-003H` as `PASS / VERIFIED`: strict artifact field
  validation, canonical date round-trip, stable parse errors, and Guard
  composition were implemented.
- C validation: 17 focused artifact/Guard tests; 182 full backend tests with 26
  PostgreSQL-dependent skips; 9 Topic Intelligence/Recommendation API tests;
  Ruff, formatting, and `git diff --check` passed.

## 2026-08-09 — PLATFORM-PRIVATE-SYNC-001 A-stage Parity Evidence Validator

- Registered `PLATFORM-PRIVATE-SYNC-001` as `IN_PROGRESS` after confirming the
  existing parity runbook had no executable sanitized evidence validator.
- Defined a synthetic-only, read-only validator for ten explicit actual-trading
  day records, with blocking mismatch, replay/no-op, quality-event, and API
  compatibility gates.
- No V1 access, private-data access, importer/database/API change, scheduler,
  synchronization, or source-of-truth cutover is authorized.

## 2026-08-09 — PHASE-3.7-003F PM decision synchronization

- Updated the canonical scoring inventory, Topic Engine contract, Scorer
  contract, and 003F brief/work order with the frozen Production V1 direction:
  absolute-return Breadth states, governed Leader Set participation with bounded
  consensus, independent absolute 0–100 piecewise normalization, 60/40 weighted
  arithmetic aggregation, and fail-closed three-gate Eligibility.
- Recorded remaining Formula Pending / NEEDS_PM_DECISION blockers: normalization
  knots, Leader Set/importance configuration, consensus bounds, grade thresholds,
  final policy/approval identity, and approved live/as-of freshness binding.
- Engineering may open a bounded non-activating classifier/policy B-stage;
  provider activation remains blocked. No provider, V1, schema, migration, or
  runtime activation change was made.
## 2026-08-09 — PHASE-3.7-003F PM decision synchronization

- Consolidated the approved Production V1 classifier, Breadth, Leadership,
  consensus, normalization, aggregation, Eligibility, Grade, and immutable
  policy-bundle mechanics in the canonical 003F PM Formula Approval Brief.
- Formula/policy mechanics are complete; activation remains blocked by governed
  Leader Set approval, live/as-of freshness binding, 003G/003H approval metadata,
  and Eligibility Audit evidence. No code, schema, migration, or provider
  activation changed.

## 2026-08-09 — PHASE-3.7-003I A-stage Production V1 Policy Executor

- Reconciled the latest canonical 003F brief as the authority for the approved
  Production V1 mechanics: participation boundaries, CORE Breadth, governed
  Leader Set and bounded Consensus, piecewise normalization, 60/40 arithmetic
  aggregation, three-gate Eligibility, S/A/B/D Grade, and immutable policy
  lineage.
- Registered `PHASE-3.7-003I` for a bounded non-activating implementation. The
  work order explicitly forbids inventing policy identity values, leader
  identities, live-data fallbacks, or provider activation.
- A-stage governance is complete; B-stage code is limited to the pure
  provider-neutral executor and Eligibility Audit contract.

## 2026-08-09 — PHASE-3.7-003I B/C-stage verification

- Implemented the approved non-activating Production V1 policy executor in
  `production_policy.py`, including exact participation boundaries, CORE
  Breadth, governed Leader Set weighting, bounded Consensus, piecewise
  normalization, 60/40 aggregation, three-gate Eligibility Audit, S/A/B/D Grade,
  effective-date handling, and immutable rollback selection.
- Preserved candidate ID/version, policy ID/version, policy-reference lineage,
  effective date, weights reference, and rollback policy in the explicit policy
  bundle. No identity default was invented.
- Focused tests: `8 passed`; full backend: `190 passed`, `26` PostgreSQL skips;
  modified-file Ruff/format and `git diff --check` passed.
- `PHASE-3.7-003I` is now **PASS / VERIFIED / NON-ACTIVATING**. The existing
  Topic Intelligence default remains fail-closed with stable `503`; provider
  activation still requires the runtime prerequisites recorded in 003F.

## 2026-08-09 — PHASE-3.7-004 Backend Runtime Finalization Audit

- Registered and completed the bounded V2 backend/runtime finalization audit.
- Added explicit activation readiness checks for policy approval, policy/bundle
  lineage, governed Leader Set identity, canonical as-of binding, and complete
  Eligibility Audit coverage.
- Added a strict canonical PRICE query that requires source, session, timezone,
  as-of date, and instrument scope; no V1/stale/zero fallback is permitted.
- Added a deterministic Eligibility Audit report builder over explicit V2 topic
  inputs. Ineligible topics remain nullable evidence and are not silently
  converted into scores.
- The default Topic Intelligence provider remains stable `503`; no frontend or
  V1 path was modified. The missing governed artifacts are recorded as explicit
  activation blockers in the audit report.
- Focused runtime/query tests: 7 passed. Targeted Ruff and formatting checks:
  passed.
- 2026-08-09 — PM freeze: 今日市場 Home frontend design

  - Updated the canonical `TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` in place; no duplicate frontend design document was created.
  - Recorded the frozen Home section order, significant topic state-transition timeline, explicit Home exclusions, and the intraday-tracked scope of strong/weak stock rankings.
  - Recorded the light-first Modern Financial Workspace direction: `#8A7462`, white cards, restrained shadows, hierarchy/spacing-led emphasis, Taiwan red/green for price movement, and warm-neutral S/A/B/D chips.
  - Home is now `PM-FROZEN / VISUAL PROTOTYPE REVIEW PENDING`. No frontend code, API, schema, scoring, or production change was made.

## 2026-08-10 — PLATFORM-PRIVATE-SYNC-001 verification

- Implemented the strict, deterministic, sanitized parity evidence validator
  for exactly ten ordered daily records. NULL and value mismatches are now
  blocking evidence alongside ordinary blocking mismatches, replay failures,
  compatibility failures, and error-level quality events.
- Focused parity tests: 14 passed. Full backend tests: 213 passed, 26
  PostgreSQL integration tests skipped because no test database URL was
  configured. Targeted Ruff and formatting checks passed.
- Read-only historical availability probe passed for `2330.TW`, `2308.TW`,
  and `2454.TW`: 24 daily points each, including 14 latest non-null points.
  No raw prices were persisted, no importer/provider/API route was added, and
  no V1 frontend compatibility work was performed.
- The current official quote adapter remains snapshot/product-basic only;
  historical provider activation, PostgreSQL import, and V1/V2 source-of-truth
  cutover remain separately governed.

## 2026-08-10 — PLATFORM-V2-BACKEND-MIGRATION-001 opened

- Formalized the V2 backend migration boundary as Provider -> normalized
  observations -> PostgreSQL -> V2 read model -> FastAPI.
- Explicitly recorded that the current V1 frontend is a legacy consumer and
  is not the V2 backend contract authority or a compatibility target.
- Confirmed the local Compose API/read-model path is live for synthetic data;
  Topic Intelligence provider activation and production historical persistence
  remain governed follow-up gates.
## 2026-08-10 — PLATFORM-V2-BACKEND-MIGRATION-001 verification

  - Added the provider-neutral historical daily-price capability and a bounded
    live probe. Six representative symbols (three TPE, three TWO) each
    returned 24 daily points and 14 or more available closes for 2026-07-07
    through 2026-08-07.
  - Added the PostgreSQL-backed, date-bound V2 price-history read contract. It
    preserves nullable fields and returns an explicit unavailable reason when
    no accepted canonical history exists; it does not call a provider from
    FastAPI.
  - The first live route check exposed a PostgreSQL optional-parameter typing
    defect (HTTP 500). The defect was recorded, corrected with an explicit
    cast, rebuilt, and reverified as HTTP 200 with the expected unavailable
    reason.
  - Full backend validation: 220 passed, 26 existing PostgreSQL integration
    skips, 1 warning; Ruff, formatting, and `git diff --check` passed.
  - No V1 frontend change or compatibility adapter was made. Real historical
    observation persistence into the governed V2 canonical model remains a
    separate follow-up before production cutover.
  - A separate read-only Taishin technical-analysis API smoke test also
    succeeded for `2330/TPE` and `4979/TWO`: 27 daily rows each, dated
    2026-07-01 through 2026-08-07, with complete OHLCV fields. Credentials
    were used only from runtime environment and were not recorded.

## 2026-08-10 — PLATFORM-V2-HISTORICAL-INGESTION-001 verification

- Opened a separately named persistence follow-up so the active migration
  boundary could add database writes without silently expanding its whitelist.
- Implemented the optional Taishin provider adapter, historical daily-bar
  normalizer, and caller-transaction ingestion service. No market or
  instrument identity is auto-created.
- Isolated PostgreSQL end-to-end evidence passed: 54 real Taishin sample bars
  were persisted as 54 raw observations, 54 timeline entries, and 108
  canonical PRICE/VOLUME rows. FastAPI returned 27 available history points
  for both `2330/TPE` and `4979/TWO`.
- Replaying the identical request reused the same batch and all 108 canonical
  rows with no duplicates. Missing close values remain NULL in the integration
  contract, and a missing reference registry rolled back the entire write set.
- Acceptance defects were recorded and corrected: vendor `result.KBar`
  nesting, Python 3.10 UTC compatibility, and market-timezone date-boundary
  exclusion. `PLATFORM-V2-HISTORICAL-INGESTION-001` is now `PASS / VERIFIED`.
- V1 frontend and compatibility behavior were not changed. Production source
  approval, licensing, scheduling, and V1/V2 source-of-truth cutover remain
  open gates.

## 2026-08-10 — PLATFORM-V2-BACKEND-MIGRATION-001 accepted

- Reverified the real Taishin provider path for `2330/TPE` and `4979/TWO`:
  27 daily OHLCV rows and 27 non-null closes per symbol from 2026-07-01
  through 2026-08-07.
- Reverified isolated PostgreSQL readback: 54 raw observations, 54 timeline
  entries, and 108 canonical PRICE/VOLUME rows; FastAPI returned 27 points per
  symbol without a provider call in the request path.
- Corrected the history response date projection to use the instrument market
  timezone. Targeted historical tests passed 11/11; full backend tests passed
  224 with 29 PostgreSQL-dependent tests skipped and one pre-existing warning.
- Accepted `PLATFORM-V2-BACKEND-MIGRATION-001` as `PASS / VERIFIED` for the
  bounded migration path. V1 frontend compatibility, production source
  approval, scheduling, and V1/V2 source-of-truth cutover remain out of scope.

## 2026-08-12 TASK-BE-024B Opportunity Qualification Policy V1

- Added the shadow qualification policy above the existing Opportunity
  strategy/read contracts. The policy freezes the semantic matrix and keeps
  all numeric parameters provisional/versioned.
- Added policy tests and replay qualification provenance. Full backend suite:
  345 passed, 31 skipped, 1 pre-existing warning. Targeted Ruff checks pass.
- Updated product/spec/roadmap/frontend/worklog documents and added the
  TASK-BE-024B report. No API, DB, frontend runtime, scheduler, production
  write, or NEXT_TASK change was made.

## 2026-08-12 TASK-BE-024C Opportunity Shadow Read API & Frontend Adapter V1

- Added the provider-neutral shadow read service and deterministic fixture
  provider with topic, stock, list, and detail projections.
- Added read-only `/api/v1/opportunities/shadow`, topic, stock, and detail
  routes; publication remains `SHADOW` and data remains `FIXTURE/SYNTHETIC`.
- Preserved structured evidence, B warming exception provenance, policy/
  parameter/ranking-profile versions, A/B independent ranking, and backend
  full-ranking metadata with Trend Top 3 / Catch-up Top 2 presentation.
- Added the frontend adapter and explicit LOADING/READY/EMPTY/DEFERRED/
  UNAVAILABLE/ERROR state contract. No UI implementation, persistence,
  migration, scheduler, daily market, replay, calibration, or NEXT_TASK change.
- Verification: backend focused shadow/API suite 11 passed (19 with existing
  Opportunity contracts); full backend suite 362 passed / 31 skipped / one
  pre-existing warning; targeted Ruff passed; frontend adapter tests 2 passed;
  frontend lint has one pre-existing warning; TypeScript and frontend build
  passed. The broader legacy source-contract suite remains 59 passed / 13
  pre-existing Home/Topic wrapper failures.

## 2026-08-12 TASK-OPS-023A-P3A Adapter-v2 deployment preflight

- Verified FIX01A adapter-v2 remains in the worktree: official TWSE/TPEx
  market-level single-date batching, historical instrument/month fallback,
  response-date/table/duplicate validation, null-marker handling, and the
  unchanged TPE/TWO authority boundary.
- Added secret-free `topicpilot-provider-lineage`, plus SELECT-only
  `topicpilot-reference-check` for active `tw-reference-v1` context and
  formal identity coverage. No migration or schema change was required.
- Added the P3A operator deployment checklist, reference preflight, G0–G4
  Canary #2 matrix, and post-Canary ordering to deployment/architecture
  documentation and the P3A report. Current worktree changes are not claimed
  as deployed; protected deployment and Production reference verification
  remain `OPERATOR_REQUIRED`.
- P3A intentionally did not deploy, execute Canary #2, write Neon, run Topic
  Snapshot/Lifecycle, enable Scheduler, alter provider authority, or modify
  NEXT_TASK.

## 2026-08-12 TASK-REPO-002 Frontend failure classification and release gate

- Classified all 13 frontend failures left by TASK-REPO-001 against the
  PM-frozen V2 route/component architecture and current frontend specification:
  6 were test-migration debt, 7 were obsolete expectations, 0 were real
  regressions, and 0 required a new PM decision.
- Migrated the affected source-shape assertions to current V2 contracts for
  `V2Page`, `TodayMarketPage`, `TopicListPage`, `StockExplorerPage`, shared
  SnapshotProvider ownership, Preview/unavailable semantics, and retained
  route smoke behavior. No tests were skipped, deleted, or commented out.
- Final frontend suite is `72 passed / 0 failed`; production build and
  `npx tsc --noEmit` pass. Full ESLint exits successfully with one existing
  unused-variable warning in `TopicDetailPage.tsx`.
- Focused backend preflight, no-trade, Opportunity shadow-read, and Lifecycle
  contract tests passed `34/34`. No backend business logic, API contract,
  Lifecycle algorithm, daily-market logic, deployment, scheduler, or
  `NEXT_TASK` change was made.
- Added `TASK-REPO-002_FRONTEND_RELEASE_GATE_REPORT.md`. Frontend and Lifecycle
  gates are now READY; TASK-REPO-001 data-governance review remains unchanged.

## 2026-08-14 TASK-TOPIC-PUB-001 Field-Level Publication Disclosure

- Corrected Topic task/document naming to domain/task identities and removed the
  Topic work-slot use of `Mainline A` / `A1`; the existing Mainline A DATA /
  Reference / Post-Close authority is unchanged.
- Added adapter-owned field-level publication states for Topic identity,
  relations, score/grade, Snapshot-backed status, Lifecycle, and detail-domain
  gaps. Topic List/Detail now disclose `FORMAL`, `FORMAL_NOT_WIRED`, `PREVIEW`,
  `DEFERRED`, `UNAVAILABLE`, and `CONTRACT_GAP` without browser scoring, grade,
  Lifecycle, ranking, membership, or Preview fallback.
- Focused Topic tests passed `10/10`; TypeScript passed; changed-file ESLint
  passed; production build passed. Full ESLint timed out without diagnostics;
  route smoke was not run because the environment blocked starting a local
  background server. No backend, schema, provider, Today, Stock, or production
  behavior changed.

## 2026-08-14 TASK-DATA-HIST-002B canonical reconciliation and closure

- Reconciled the completed isolated full-universe historical seed against the
  canonical V2 repository and current local PostgreSQL evidence. The approved
  `tw-reference-v1` bundle contains 507 physical identities: 314 TPE and 193
  TWO.
- Read-only local verification confirms 63,826 OHLCV rows across 507 symbols,
  TWSE 39,523 and TPEx 24,303, from 2026-02-02 through 2026-08-13. Extra
  universe rows, invalid OHLCV, duplicate keys, missing required lineage, and
  unexplained gaps are all zero; 6806 stops at 2026-06-22 after its
  2026-06-23 termination event.
- Canonical V2 official exchange providers, transactional ingestion,
  request-keyed idempotence, provider lineage, reference-bundle validation,
  lifecycle/no-trade semantics, and local-only guards are present. The
  predecessor plain-table runner remains isolated evidence and was not copied
  as a duplicate V2 persistence path.
- Validation: canonical focused tests 16 passed; source historical contract
  tests 9 passed; canonical config/migration/reference/preflight tests 22
  passed with one PostgreSQL skip; bundle validation and diff/secret checks
  passed. Migration upgrade was not run because the local database is at
  Alembic 0017 while canonical head is 0029 and closure is read-only.
- No Production mutation, Production DB access, scheduler, deploy, push,
  merge, recommendation activation, or `NEXT_TASK` change occurred. G1/G2/G3
  and Post-Close Canary remain `PRESERVED PASS`.
- Closure report: `docs/reports/TASK-DATA-HIST-002B_CANONICAL_RECONCILIATION_CLOSURE.md`.

## 2026-08-15 TASK-FE-BE-STOCK-005C Stock Explorer / Drawer EOD formal wiring

- Wired the existing V2 Stock Explorer and shared Stock Encyclopedia Drawer to
  the canonical nullable `StockEodRead` projection from the formal list/detail
  routes. Completed-session rows render backend-owned close, previous close,
  change, change percentage, OHLC, volume, turnover, trading date, status, and
  source/as-of metadata.
- Preserved the intraday latest-quote boundary, explicit Preview disclosure,
  fail-closed null/error semantics, advanced topic filtering, and the Drawer
  push/close/Escape/header-offset/full-height/sticky/internal-scroll behavior.
- Added an EOD presenter and focused regression coverage for formal EOD,
  intraday/EOD separation, all canonical status values, null turnover, API
  error handling, Preview boundaries, stale-detail protection, and the
  browser render-only business-rule guard.
- Validation: focused EOD tests 8 passed, full frontend tests 104 passed,
  TypeScript passed, changed-file ESLint passed, production frontend build
  passed, and protected G1/G2/G3/Post-Close Canary evidence remains preserved.
  No backend, OpenAPI, generated client, historical, reference, Today, Topic,
  recommendation, Production, or `NEXT_TASK` change.

## 2026-08-15 TASK-FE-TOPIC-DETAIL-001 Topic Detail Research Workspace

- Completed the Topic Detail research workspace IA and formal-state-aware
  rendering: header identity, Today status, the existing three Topic status
  dimensions, formal constituents/relations, lifecycle, description,
  hierarchy/related topics, and a fail-closed historical/rotation shell.
- Preserved field-level publication disclosure from TASK-TOPIC-PUB-001. Mixed
  FORMAL, PREVIEW, DEFERRED, UNAVAILABLE, FORMAL_NOT_WIRED, and CONTRACT_GAP
  states remain explicit; API errors do not fall back to Preview.
- No fabricated score, grade, lifecycle, leadership, breadth, concentration,
  ranking, or historical metrics were added. Remaining Topic backend/data gaps
  stay deferred or unavailable. Backend, OpenAPI, database, Production, and
  `NEXT_TASK` state were unchanged.
- Validation: focused Topic tests 15 passed, full frontend tests 113 passed,
  TypeScript, changed-file ESLint, and production build passed. Route smoke was
  not run because the environment blocks the required background runtime.
- Closure report: `docs/reports/TASK-FE-TOPIC-DETAIL-001_TOPIC_DETAIL_RESEARCH_WORKSPACE.md`.

## 2026-08-15 TASK-FE-FAVORITES-001 Shared Favorites State and UX

- Completed the shared local-device Favorites capability for the currently supported `STOCK` and `TOPIC` entities across Stock Explorer, Stock Drawer, Topic List, Topic Detail, and the Favorites workspace. Shared state, reload persistence, cross-surface synchronization, malformed-storage fail-safe handling, and keyboard/accessibility semantics are in place.
- Kept local user preference state semantically separate from formal market data, Preview data, API errors, unavailable responses, Recommendation, backend read models, and server/account synchronization. API/data refresh cannot clear a stored favorite identity.
- Today currently has no favorite affordance and therefore remains explicitly out of scope for a toggle/sync claim. No backend, database, Production, `NEXT_TASK`, or server-sync change was made.
- Validation: Favorites focused tests 8 passed, related Stock/Topic regression tests 17 passed, full frontend source-contract tests 115 passed. TypeScript, changed-file ESLint, and production build were blocked by the incomplete local dependency tree; route smoke was not run because the environment restricts the required runtime.
- Closure report: `docs/reports/TASK-FE-FAVORITES-001_SHARED_FAVORITES_STATE_AND_UX.md`.
