# TopicPilot V2 Project Context

## Current handoff objective

**Primary objective:** Build the first production-ready Topic Intelligence platform.

Future AI contributors must follow the [execution roadmap](docs/ROADMAP.md): Topic Engine Foundation -> Topic Formula Research & Plug-in -> Topic Intelligence API -> Customer Topic Dashboard -> Recommendation MVP -> Historical Validation / Calibration. Recommendation is downstream of Topic Intelligence. Theme Governance, Theme Discovery, and the Knowledge Graph are future planning milestones and must not block current implementation.

## Canonical product and documentation governance

- **PASS / VERIFIED:** Phase 3.7-001F integrates `FeatureAggregate` -> `TopicScorer` into deterministic, ephemeral Topic Intelligence outputs with versioned runtime identity. Eligibility-first execution and PM-001–PM-007 boundaries remain intact.

- Current Product Vision, Mission, Product Philosophy, Product Surfaces, Core Principles, and semantic boundaries: [Product Direction and Surfaces Contract](docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md).
- Theme Discovery, Theme Knowledge, and Theme Governance conceptual authority: [Theme Governance & Knowledge System](docs/architecture/THEME_GOVERNANCE_KNOWLEDGE_SYSTEM.md).
- Decision context and consequences: [ADR-003](docs/architecture/ADR-003_TOPICPILOT_PRODUCT_POSITIONING.md).
- Document ownership, four-layer model, and cross-reference rules: [Architecture Book](docs/architecture/README.md#documentation-governance-and-single-source-of-truth).

This file is a repository navigation and handoff layer. It must not become a duplicate authority for permanent product or architecture decisions.

Phase 3.7-001 is IN PROGRESS; 3.7-001A, 3.7-001B, 3.7-001C, 3.7-001E, and 3.7-001F are PASS / VERIFIED. Together they are the Topic Engine Foundation: deterministic ephemeral runtimes over explicit input bundles. The current primary milestone is Topic Intelligence MVP. `PHASE-3.7-002A` through `PHASE-3.7-002F` and `PHASE-3.7-003A` through `PHASE-3.7-003E` are `PASS / VERIFIED`. 003B is the existing customer Topic Dashboard; 003C is the Recommendation Read Model Boundary; 003D exposes the Recommendation MVP API; and 003E provides research-only Historical Validation / Calibration Review. Recommendation remains downstream, deterministic, explainable, read-only, and fail-closed over unavailable/deferred Topic Intelligence. These work orders do not authorize ranking formulas, trading behavior, persistence, or production activation. The default Topic Intelligence and Recommendation providers remain unavailable with stable `503` responses until separately approved.

Theme Governance & Knowledge System planning is registered as `THEME-GOVERNANCE-KNOWLEDGE-001`, `PLANNING / NEEDS PM DECISION`. It separates Theme Knowledge, Theme Governance, Theme Intelligence, and Recommendation; treats News and other market inputs as Evidence rather than Knowledge; and preserves one stable Theme identity across governance states. It is future planning only: no implementation or schema change is authorized, and it must not block the Topic Intelligence MVP path.

The Phase 4–6 capability path is complete through `PHASE-3.7-003E`.
`PHASE-3.7-003F` is `PASS / PM Approved`: formula/policy mechanics are
approved and frozen in the [canonical PM Formula Approval Brief](docs/reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md).
`PHASE-3.7-003I` is `PASS / VERIFIED`: the bounded non-activating Production V1
mechanics, policy lineage, and Eligibility Audit contract are implemented and
tested. Providers remain fail-closed with stable `503` responses until governed
Leader Set approval, live/as-of freshness binding, approval artifact metadata,
and Eligibility Audit evidence are complete.

`PHASE-3.7-003G` is `PASS / VERIFIED`: the formula-agnostic Policy Approval
Guard validates a future approval record but does not choose or execute a Topic
Score policy. Provider activation remains deferred to a separate post-PM work
order.

`PHASE-3.7-003H` is `PASS / VERIFIED`: it adds strict parse/export for the PM
Formula Approval artifact and composes with 003G without changing provider
activation or policy semantics.

`PLATFORM-PRIVATE-SYNC-001` is `PASS / VERIFIED` for the synthetic parity
evidence validator and a small read-only historical-price availability probe.
It does not access private source data, does not perform import or cutover, and
does not claim that the required ten actual trading days have passed. The
current official quote adapter remains snapshot-only; historical daily data
must use an explicitly approved historical provider contract.

`PLATFORM-V2-BACKEND-MIGRATION-001` is `PASS / VERIFIED` for the bounded clean
Provider -> PostgreSQL -> V2 Read Model -> FastAPI path. The current V1
frontend is a legacy consumer and is not a V2 contract authority or migration
blocker. Provider approval, production scheduling, and source-of-truth cutover
remain separately gated where the work order records them.

`PLATFORM-V2-HISTORICAL-INGESTION-001` is `PASS / VERIFIED` for the bounded
private Taishin sample path. Its isolated PostgreSQL run proved raw,
Observation Timeline, canonical PRICE/VOLUME, idempotent replay, and FastAPI
date-bound readback. Production source approval, licensing, scheduling, and
source-of-truth cutover remain open gates.

`PHASE-3.7-004` is `PASS / AUDITED — ACTIVATION BLOCKED`: V2 now has an
explicit Production V1 activation-readiness boundary, a strict canonical PRICE
as-of query, and a deterministic Eligibility Audit report builder. These are
non-activating boundaries. No governed Leader Set, real 003G/003H approval
artifact, live/as-of freshness binding, or production provider default may be
invented by implementation. See the [Backend Runtime Finalization Audit](docs/reports/PHASE_3_7_004_BACKEND_RUNTIME_FINALIZATION_AUDIT.md).

**Status:** VERIFIED repository navigation layer; milestone status below is evidence-based as of 2026-08-10.

`TASK-LIVE-002` is `WAITING_LIVE_VALIDATION`: V2 live collection,
intraday-capable Taishin adapter, retry/failure recovery, PostgreSQL live
observability, 60MA tracking, post-close execution, operations API, bounded
historical recovery probe, and deployment entry points are implemented and
offline-verified. The next open Taiwan session is still required for live
validation; the private Taishin runtime/credentials and official holiday list
must be supplied by deployment. See
[TASK-LIVE-002 Production Readiness](docs/reports/TASK-LIVE-002_PRODUCTION_READINESS.md).
The Phase 7 institution collector design and Phase 8 technical runtime
inventory are retained in that report and its linked design handoff; no
institution values or new technical scoring rules are active.

## Identity and boundary

- Product: TopicPilot V2
- Repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
- V1 formal production system: `C:\Users\acer\Desktop\題材領航\AI` (Google Sheets / Apps Script and related production workflow).
- V2 is the PostgreSQL/FastAPI platform under development and a parallel, rebuildable read model. V2 work must not modify V1 files, data, workflows, or source-of-truth assumptions.

## Stack and verified paths

PostgreSQL, Alembic, SQLAlchemy, FastAPI, Docker, and pytest are present. API configuration is at `services/api/alembic.ini`; migrations are under `services/api/alembic/versions/`; tests are under `services/api/tests/`; validation entry point is `infra/scripts/validate.ps1`.

The repository has no root `alembic.ini` and no root `scripts/` directory. Use the verified paths above.

## Milestone status

- **VERIFIED / completed:** 3.4-001 Database Foundation; 3.4-002 Identity Domain; 3.4-003 Topic Domain; 3.4-004 Instrument-Topic Relationship Domain.
- **PASS / VERIFIED:** 3.4-005 Market Data Source & Raw Observation Foundation.
- **PASS / VERIFIED:** 3.4-005A Validation Framework; `infra/scripts/validate.ps1` is the recorded full-validation entry point.
- **Alembic repository head (Fix-001 implementation):** `0021_phase3_6_001b_import_audit`, adding only legacy import audit/lineage persistence.

- **V2-FOUNDATION-CONSISTENCY-001 Fix-003:** **PASS / COMPLETE**. ORM and repository boundaries are frozen at revision `0019`; full backend tests, targeted Ruff, API smoke, and infrastructure validation passed.
- **PASS / VERIFIED:** 3.4-006 Observation Timeline implementation is present at revision `0018`; 3.4-006A planning and 3.4-006B implementation are complete.
- **PASS / COMPLETE:** V2-FOUNDATION-CONSISTENCY-001 Fix-002A; canonical detail append-only enforcement, hostile-search-path regression coverage, and validation evidence are recorded in the 3.5-001B work order.
- **PASS / VERIFIED:** Phase 3.5-002B runtime execution is complete; versioned reference registry tables remain authoritative, NormalizerMappers remain pure functions with the approved three-input/one-output boundary, and PostgreSQL persistence is caller-transaction scoped with idempotent correction/supersession behavior.
- **PASS / VERIFIED:** Phase 3.7-001B defines explicit feature runtime configuration and score-free per-topic aggregation. Aggregate persistence/replay identity and Topic Scorer policy remain deferred.
- **PASS / VERIFIED:** Phase 3.7-001C defines `ScoringInput`, `ScoringPolicy`, and `TopicScore` with preserved aggregate evidence and nullable business outputs. Numeric Production V1 policy is governed by the 003F brief.
- **PASS / VERIFIED:** Phase 3.7-003A exposes the ephemeral Topic Intelligence result through one deterministic GET-only FastAPI contract. The default provider fails closed with `503`; no persistence, production formula/default, frontend replacement, or V1 change was introduced.
- **PASS / VERIFIED:** Phase 3.7-003B exposes the first customer-visible Topic Intelligence dashboard/detail experience through the existing customer shell. Focused API/integration tests, frontend lint, frontend production build, and diff checks pass. No browser-side scoring or semantic boundary changed.
- **PASS / PM-001 semantic freeze:** Breadth means Market Participation over governed CORE members; current primary-topic membership is the default conceptual basis. Numeric mechanics are in the 003F brief. Recommendation may consider secondary-topic members downstream without feeding them back into Topic Strength. No schema or migration change.
- **PASS / PM-002 semantic freeze:** Leadership means whether the governed semi-static Leader Set of representative CORE members supports the current move. Identity and daily evidence remain separate; numeric mechanics are in the 003F brief. Demo/API `leaders` lists are not the approved Leader Set without a governed artifact. No schema or migration change.
- **PASS / PM-003–PM-006 Freeze Batch #2:** Confidence is independent evidence-quality output and never changes Score; Grade is canonical `S/A/B/D` Market Strength classification derived from Score and is not a recommendation; Topic Score composition is Breadth plus Leadership only; Eligibility is a CORE/required-feature evidence gate where missing is not zero and topic size is irrelevant. Detailed rationale and examples are in the canonical inventory and Topic Engine contract.
- **PASS / PM-007:** Topic Score uses the frozen normalized parallel components and versioned 60/40 weighted arithmetic aggregation in the 003F brief. No implementation, schema, or migration change in this documentation task.
- **PASS / V2 scoring semantic freeze synchronization:** The canonical scoring inventory records that Topic Score excludes news, technical indicators, sentiment/heat, and entry timing; V1 is a Legacy Research Baseline, not Production. Weighted Return and Strong/Weak Diffusion remain Breadth research evidence, `ln(N)` moves to Confidence/Evidence Quality, Coverage belongs to Eligibility/Confidence, `X` is replaced by `INELIGIBLE`, and Leadership is a new V2 capability. The workflow is PM Semantic Freeze → Research Candidate → Historical Validation → PM Formula Approval → Production Policy.
- **PASS / PM Approved:** Phase 3.5-002 planning contract.
- **PASS / VERIFIED:** Phase 3.5-002A synthetic reference normalizer.
- **PASS / VERIFIED:** Phase 3.5-002B Fix-001 Runtime Correctness; focused PostgreSQL runtime tests, full backend validation, Alembic, API smoke, and infrastructure validation passed.
- **PASS / VERIFIED:** V2-VALIDATION-DEBT-001; the unrelated detector-timeout and synthetic-news fixture blockers are cleared.

## Mandatory startup rules

1. Verify the exact repository root and representative V2 paths before coding.
2. Read this file and `docs/ROADMAP.md`.
3. Inspect existing architecture/work-order documents before creating a new equivalent.
4. Keep statuses explicit: `VERIFIED`, `IN PROGRESS`, `DRAFT`, or `FUTURE`.
5. Stop if V2 source/runtime paths are unavailable. Do not fall back to V1 or its context file.
6. Never modify anything under `C:\Users\acer\Desktop\題材領航\AI` during a V2 task.

- **READY FOR PM REVIEW:** Phase 3.6-001 Legacy Import Foundation. The contract/mapping/validation framework is under services/api/src/topicpilot_api/legacy_import/; no V1 data was read or migrated.
- **PASS / PM Approved:** Phase 3.6-001A V1 Export Contract & Dry-Run Validation. Ruff, focused/full backend tests, compile/import check, and diff checks pass. No V1 data was read and no PostgreSQL write path was invoked; the first real V1 export dry run may begin under the read-only contract.
- **PASS / VERIFIED:** Phase 3.6-001B first PostgreSQL legacy import. Alembic is at `0021_phase3_6_001b_import_audit`; real dry run had 1,594 valid records and zero blockers. Two committed runs produced 1,594 `CREATED` and 1,594 rerun `NOOP` audit records with unchanged domain totals and stable target UUIDs. V2 now contains real TopicPilot master data for markets, instruments, topics, hierarchy, and instrument-topic relations.
- **IMPLEMENTED — MVP READ-ONLY SLICE:** Phase 3.6-002 Admin/Data Explorer Foundation. `/admin` and `/admin/schema` use dedicated read-only endpoints; schema cards derive from SQLAlchemy metadata and the dashboard reports V2 counts, latest import, Alembic revision, and readiness.
- **PASS / VERIFIED:** Phase 3.6-002A Fix-001 adds interactive metadata-derived ERD, bounded import lineage, all-path topic ancestry, filtered import pagination, and corrected governance validation. No Admin writes or schema migration.

## Product-development direction

Do not restate product positioning or frontend responsibilities here. Use the [Product Direction and Surfaces Contract](docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md) for the current product truth and [generation-model.md](docs/architecture/generation-model.md) for the V1/V2 coexistence model.
