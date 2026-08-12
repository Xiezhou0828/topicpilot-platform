# TopicPilot Platform collaboration rules

This repository is the standalone, public portfolio implementation of TopicPilot's enterprise read platform.

## Hard boundaries

- Google Sheets and the existing TopicPilot repository remain the formal source of truth.
- Generation labels are mandatory during the migration period:
  - `LEGACY / V1`: the existing production workflow (Google Sheets, Apps Script, private Python engines, R2 output, and historical docs).
  - `NEXT / V2`: the PostgreSQL, FastAPI, migration, contract, and platform work being developed in this repository. The current V1 React UI is a legacy consumer; it is not the authority for the V2 backend contract or a compatibility target for this migration.
  - `SHARED`: contracts, topic dictionaries, public-safe assets, and rules that both generations must understand.
- V1 and V2 are already maintained as separate Git repositories. Do not move, merge, or restructure either repository until V2 has passed the signed parity and cutover decision. Every new work order must state its generation.
- This repository is read-only with respect to formal TopicPilot data.
- Public fixtures must be synthetic and must not contain credentials, holdings, licensed market data, private news text, or private URLs.
- API routes are read-only in v1. Authentication, trading, order execution, and admin writes are out of scope.
- Missing numeric values stay `null`; they must never be silently converted to zero.
- Every import is versioned, hashed, idempotent, and transactional.

## Delivery discipline

- Work only inside the modification whitelist of the active work order.
- Run targeted tests first and report changed files and evidence.
- Do not change product scoring rules or strategy definitions while moving data.
- The stable strategy identifiers are `MAS`, `MAV`, `TMC`, `BB`, `PB`, and `KD`.

## TopicPilot Work Mode Repository Rules

### Mandatory startup check for V2 coding tasks

- Verify the active workspace is exactly `C:\Users\acer\Desktop\題材領航\topicpilot-platform` and confirm representative V2 paths (`services/api`, `services/api/alembic.ini`, and `docs`) before coding.
- Read the V2 `PROJECT_CONTEXT.md` and `docs/ROADMAP.md` before making changes.
- Never use `C:\Users\acer\Desktop\題材領航\AI\PROJECT_CONTEXT.md` as V2 authority; V1 remains the formal production system and must not be modified by V2 tasks.
- Stop and report the actual workspace and missing paths if V2 source or runtime paths are unavailable.

- Canonical repository root: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
- All permanent edits must be made inside this repository. `outputs/` and `work/` are temporary execution folders and must not contain canonical project files.
- Before asking for a file, search the full repository by exact filename, similar filename, and relevant content. If a path moved, use the canonical current file. Ask only after the search confirms it is absent.
- Documentation locations: workshops `docs/workshops/`; research `docs/research/`; architecture specifications `docs/architecture/`; ADRs use the existing ADR folder discovered in the repository; work orders `docs/work-orders/`; reports `docs/reports/`.
- Workshop documents record discussion status and conclusions. Research documents provide evidence and references; they do not automatically become approved Business Rules. ADRs record accepted architecture decisions and alternatives. Specifications record the current formal system contract.
- Documentation ownership and the four-layer governance model are defined in `docs/architecture/README.md`. Consult its canonical authority map before creating or editing a permanent document.
- `docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md` is the single source of truth for Product Vision, Mission, Product Philosophy, Product Surfaces, Core Principles, and frozen product semantics. Other documents link to it instead of copying those decisions.
- ADRs preserve decision context and consequences; they do not replace the current normative specification. Work orders preserve execution scope, whitelist, acceptance criteria, and evidence only; they must not preserve permanent product philosophy or architecture policy.
- Roadmap owns milestone sequence and status. Project Context owns startup navigation and current handoff facts. Daily Progress is historical and non-normative. OpenAPI, schema metadata, generated API clients, and Admin metadata are generated authorities and must not be maintained manually in prose.
- Preserve canonical documents and prefer incremental edits over replacement. Do not mark a document `Frozen` unless the discussion explicitly approved that status.
- Work on one active architecture topic at a time. Put new ideas outside the active scope in the existing Architecture Backlog. Do not silently expand Business Rules, algorithms, database schema, API contracts, or implementation scope.
- After every task, report Modified files, Created files, Modified sections, Validation performed, and Open questions or blockers.
- Do not modify code, database schema, migrations, triggers, production data, or deployment configuration unless explicitly authorized. Do not create duplicate files when a canonical equivalent already exists. Use repository-relative document links and never temporary Work-mode paths.
