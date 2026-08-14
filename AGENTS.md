# TopicPilot Platform collaboration rules

This repository is the canonical checked-in home for the TopicPilot V2 platform,
its contracts, implementation, and current project documentation. It is also a
public portfolio repository; public fixtures and demo surfaces must remain
synthetic and safe to publish.

## Canonical repository and hard boundaries

- The canonical repository is permanently fixed at
  `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
- All permanent edits, reconciliation results, and canonical documentation must
  land in that repository. A task/worktree is an isolated execution area, not a
  source of authority and not a permanent parallel repository.
- Never infer authority from a folder name, branch name, task prompt, or stale
  worktree. Confirm the canonical path, branch, commit, status, and evidence.
- Do not modify application code, schema, migrations, runtime configuration,
  Production data, deploy configuration, or `NEXT_TASK` unless the active task
  explicitly authorizes that exact surface.
- Public fixtures must be synthetic and must not contain credentials, holdings,
  licensed market data, private news text, or private URLs.
- Missing numeric values stay `null`; they must never be silently converted to
  zero. Imports and write paths must remain versioned, hashed, idempotent, and
  transactional within their approved boundary.

## Current generation boundary

- `V2` is the active platform development generation in this repository:
  PostgreSQL, FastAPI, read models, contracts, frontend surfaces, and governed
  operator paths.
- `V1` is now `LEGACY BRIDGE / PARTIAL RETIREMENT`. Do not add new product
  features to V1 or treat it as the destination for new work.
- The following V1 bridges remain operationally protected until V2 replacement
  and dual-run/parity evidence are complete:
  - `price_engine.py`: TWSE MIS plus Yahoo fallback, Sheet/TSV input, and
    Google Sheets `H:I:J:K` quote write-back;
  - `ta_engine.py`: Yahoo approximately six-month OHLCV, MA/Market Structure/
    Volume/RS/Pullback technical factors, still connected to Sheets/CSV;
  - `radar.py`: Google Sheets groups/stocks/relations/synonyms, RSS/news,
    topic heat/warming/cooling, related stocks, sentiment, interpretation,
    AI題材雷達, and historical V2 output;
  - legacy master-data and scheduling bridges.
- V1 may be formally retired only after V2/PostgreSQL/FastAPI replacements for
  price update, technical factors, news ingestion/topic detection, master-data
  editing, and scheduling have completed dual-run/parity and an explicit
  cutover decision. Do not stop or delete a bridge merely because a V2 slice
  exists.

## Documentation ownership

Keep one owner for each kind of truth. Link to the owner instead of copying a
large status block into another document.

| Document | Responsibility |
|---|---|
| `AGENTS.md` | Collaboration, worktree, validation, safety, and documentation rules |
| `PROJECT_CONTEXT.md` | Short startup and handoff navigation plus current facts |
| `README.md` | Public repository and portfolio orientation |
| `docs/ROADMAP.md` | Execution sequence, phase priority, status, and next dependency routing |
| `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md` | High-level product routing and product-level deferrals |
| `docs/architecture/README.md` | Architecture authority map and four-layer documentation governance |
| `docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md` | Accepted product vision, surfaces, and frozen semantic boundaries |
| `docs/DOCUMENTATION_INDEX.md` | Repository documentation index and historical/evidence navigation |

Task reports, worklogs, screenshots, old handoffs, and task prompts are
historical evidence. They may prove what happened, but do not override the
current owners above. This checkout has no `docs/DOCUMENTATION_AUTHORITY_INDEX.md`
or `docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md`; do not create duplicate
authority files merely to satisfy an old task prompt. The 2026-08-13 chat
handoff and the old task-doc-001 documentation set are historical inputs only.

## Worktree lifecycle policy

Use the following lifecycle for every isolated task:

1. Create an isolated worktree only when isolation is needed.
2. Execute the task inside its explicit scope and write set.
3. Reconcile/integrate the accepted result into the canonical repository.
4. Run impact-based validation and record evidence.
5. Clean up the completed worktree/branch when no preservation need remains.

Prefer continuing the existing worktree and branch for the same mainline. Do
not create a permanent new folder for every small ticket. A missing field, one
UI bug, or one endpoint gap is not by itself a new mainline. Keep only the
number of active worktrees needed for concurrent, non-conflicting work.

Before cleanup, inspect the actual worktree path, branch, HEAD, dirty state,
containment in `origin/main`, unique patches, and whether any evidence or code
is absent from canonical. `git cherry` is a patch comparison, not proof that a
feature is absent from main; compare content and later replacements before
classifying a worktree as disposable.

## Impact-based validation and preserved evidence

Validation is proportional to the changed dependency. The repository-level
documentation lifecycle is described in
[Documentation Governance](docs/DOCUMENTATION_GOVERNANCE.md); the impact rules
below are the current collaboration summary and must be applied even when a
task-specific policy artifact is not checked out.

- Ordinary FastAPI read paths, read-only reconciliation, frontend changes, and
  ordinary UI bugs do not automatically rerun G1/G2/G3 or the Post-Close
  Canary. Run focused tests, affected API/PostgreSQL/OpenAPI/generated-client
  checks, frontend tests/typecheck/lint/build, and the relevant CI boundary.
- A preserved gate is explicit evidence, not a new execution claim. Name the
  baseline report, prove the protected dependency is unchanged, and record the
  targeted validation that was run.
- Re-run protected gates only when the change reaches their boundary: runtime
  provenance/provider authority (G0), reference registry/identity/lifecycle/
  calendar/bootstrap (G1), official provider/coverage/date-effective universe
  semantics (G2), market/no-trade/date semantics (G3), or post-close writer,
  persistence, reconciliation, snapshot, transaction/idempotence, or live
  runtime dependencies (Canary).
- If impact or provenance is uncertain, use `BLOCKED_NOT_REVALIDATED` and stop
  the affected path. `NOT_RUN` and `UNKNOWN` never mean `PASS`.
- Documentation-only work does not invalidate application gates when the
  application runtime and protected inputs are unchanged. It still requires
  link/path checks, diff review, and secret-safe scanning.

## Delivery and safety discipline

- Verify the exact canonical path and representative paths (`services/api`,
  `services/api/alembic.ini`, `apps/web`, and `docs`) before work.
- Read `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`, the applicable product or
  architecture authority, and the relevant evidence before editing.
- Work only inside the active modification whitelist. Stage explicit paths;
  never use blanket staging in a dirty worktree.
- Do not change product scoring, lifecycle, recommendation, or taxonomy rules
  while moving data or repairing presentation unless that exact change is
  authorized by a separate contract/work order.
- AI may propose topic discovery or correction suggestions, but AI must not
  directly mutate canonical taxonomy, stock-topic relations, or master data.
- Recommendation candidates remain downstream of Topic Intelligence and must
  not silently become production policy.
- Do not push, merge, deploy, activate a scheduler, mutate Production, or alter
  `NEXT_TASK` as an incidental step.
- Use repository-relative links in Markdown. Do not link to temporary work-mode
  paths or create a parallel version when a canonical file already exists.

## Required handoff report

After a task, report:

- Modified files and created files;
- modified sections and the owning authority for each;
- validation performed, including preserved/not-run/blocked states;
- open questions or blockers;
- local commit SHA when a local commit was intentionally created;
- explicit confirmation that push, merge, deploy, Production mutation, and
  `NEXT_TASK` changes did or did not occur.
