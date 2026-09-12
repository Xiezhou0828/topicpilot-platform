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

## SDLC lifecycle and canonicalization authority

Use this ordered lifecycle for every capability and release claim:

`IMPLEMENTED` -> `VALIDATED` -> `CANONICALIZED` -> `RELEASE_CANDIDATE` -> `PRODUCTION_RELEASED` -> `POST_DEPLOY_VERIFIED`

- `IMPLEMENTED` means the scoped source change exists; `VALIDATED` means the
  relevant checks passed for that source and scope.
- `CANONICALIZED` means the approved content is in the canonical repository at
  a committed SHA with source-to-canonical provenance. `RELEASE_CANDIDATE`
  means that exact committed SHA was checked out cleanly and passed the
  release-candidate gates. `PRODUCTION_RELEASED` requires owner-authorized
  promotion and exact API/Web, migration/data, and revision evidence.
  `POST_DEPLOY_VERIFIED` requires public/runtime verification after promotion.
- `FINAL_STATUS=COMPLETE`, `CAPABILITY_STATUS=COMPLETE`, and `tests PASS` are
  evidence about a task or check only; none of them implies canonicalization,
  release-candidate status, Production release, or public visibility.

Canonical repository state is the single authority. An isolated worktree PASS
is source evidence until its exact source SHA, canonical SHA, and accepted file
mapping are recorded. A committed consumer must never depend on a provider,
fixture, generated artifact, or document that is only dirty or untracked.
Clean-candidate evidence must come from the committed exact SHA in a clean
checkout; a dirty-worktree PASS is diagnostic only. An implementation closure
must report `CANONICAL_STATUS`, `RELEASE_STATUS`, and
`PRODUCTION_VERIFICATION`. If the result is not canonical, it must also report
exactly one `CANONICAL_RECONCILIATION_DISPOSITION`:
`READY_FOR_CANONICAL_RECONCILIATION`, `CANONICALIZED`, `BLOCKED_COLLISION`, or
`OWNER_DECISION_REQUIRED`.

Orphaned worktrees are forbidden: every isolated result must be reconciled,
explicitly retained under an owner decision, or closed with its evidence and
provenance preserved. Local migration, data, or materialization validation is
never Production-ready or Production-visible evidence. Exact-SHA API/Web
provenance, fail-closed behavior, migration/data state, rollback readiness,
and deployed revision verification are release-readiness requirements;
`PUSH_REMOTE=NO` and `DEPLOY=NO` are safety boundaries, not completion states.

Only explicit paths and hunks may be staged or cleaned. Blanket stage, clean,
reset, and stash operations are prohibited. `NEXT_TASK` changes require Owner
authorization; an agent may recommend a next task but may not set or advance it.

### Reproducible dependency environment

`RELEASE_CANDIDATE` and canonical validation require both
`CLEAN_SOURCE_STATE=PASS` and `REPRODUCIBLE_DEPENDENCY_STATE=PASS`. The
dependency environment must derive from the repository lockfile/declared
constraints through `npm ci`, `pnpm --frozen-lockfile`, an equivalent Python
locked/declared environment, or an approved container/CI environment selected
for the repository stack. A dirty worktree's `node_modules`, a temporary
junction, a partial install, or an unconstrained global package is not final
release proof. A borrowed dependency directory is
`DIAGNOSTIC_FALLBACK_ONLY`; it requires lockfile equivalence, dependency digest,
and approved reproducibility proof before it can support a clean-candidate
claim.

### Commit-based promotion preference

Canonical promotion SHOULD prefer a validated commit, cherry-pick, or
commit-preserving merge/rebase with deterministic reconciliation. Index-only or
manual hunk surgery is an exception only for a shared dirty file with proven
owner overlap and no complete source commit that can be promoted directly. An
exception must report `HUNK_LEVEL_RECONCILIATION_USED=YES`, `REASON`,
`HEAD_INDEX_WORKTREE_AUDIT=PASS`, and
`POST_RECONCILIATION_CLEAN_CANDIDATE=PASS`; it must verify HEAD, index, and
working tree alignment and leave no task-owned residual diff. They must not be
left permanently split.

### Repository/worktree/remote hygiene gate

Release readiness, canonical reconciliation, and fixed Owner review include
canonical versus `origin/main` divergence, local-only and remote-only commits,
completed branches not canonicalized, stale/superseded/orphaned worktrees or
commits, completion states whose `CANONICAL_STATUS` is not `CANONICALIZED`,
ownerless active branches/worktrees, dirty tracked-file aging and ownership,
untracked artifact aging/provenance, committed consumers relying on
uncommitted state, missing local-commit provenance mappings, and candidate
ancestor/descendant relationships. Report
`REPOSITORY_HYGIENE_STATUS=PASS`, `ACTION_REQUIRED`, or `BLOCKED`, together with
`LOCAL_ONLY_COMMIT_COUNT`, `STALE_WORKTREE_COUNT`,
`ORPHANED_WORKSTREAM_COUNT`, and `UNATTRIBUTED_DIRTY_COUNT`. An unhealthy gate
requires `OWNER_DECISION_REQUIRED` or
`CANONICAL_RECONCILIATION_REQUIRED`; it never authorizes `git clean`, branch
deletion, force reset, or force push.

### Parallel-workstream governance boundary (established 2026-08-19)

The two release-hygiene closure workstreams remain closed. Workstream A closed
the Stock-004 canonical reconciliation; workstream B closed the documentation
provider, DB integration fixture, and owner/branch disposition blockers. The
authoritative evidence is in the [Stock-004 closure report](docs/reports/TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001.md)
and the [documentation/fixture/disposition closure report](docs/reports/TASK-OPS-DOCUMENTATION-PROVIDERS-OWNER-DISPOSITION-AND-DB-INTEGRATION-FIXTURE-CLOSURE-001.md).

The current Parallel Plan has four isolated workstreams:

- `WS1` — Topic Derived Intelligence / Structural Role and Score Projection;
- `WS2` — Stock Technical V0 policy, publication, and formal evidence surface;
- `WS3` — Core V0 research and forward-evidence qualification; and
- `WS4` — Release-chain Closure / Release Candidate Qualification.

WS1, WS2, and WS3 may continue through their bounded authority or evidence
routes when their contracts and write sets do not conflict. WS4 remains an
independent release lane. Completion or readiness in one workstream does not
establish overall release readiness, and WS4 must not globally block unrelated
WS1-WS3 work. No workstream may silently change another workstream's semantic
authority, strategy meaning, taxonomy, MA60 policy, or production boundary.

`READY_FOR_RELEASE_CHAIN_CLOSURE=YES` and `READY_FOR_PRODUCTION_RELEASE=NO`
remain the WS4 release-hygiene disposition. Owner dirty/untracked state remains
preserved and classified; this does not authorize cleanup, branch deletion,
push, merge, deployment, scheduler activation, or Production mutation. `NEXT_TASK`
remains Owner-controlled and unchanged by this checkpoint.

### Canonical boundary reconciliation checkpoint (2026-08-22)

The current local integration lane has separately committed the Today surface
(`495619e`), Topic Lifecycle contract/UI/tests (`c5b2239`), research tooling
(`c92dbc0`), research-only Leader Set evidence (`e8bdca4`), L2/L5 and Lifecycle
Strength evidence (`6ba9dc9`), and the subordinate documentation navigation
layer (`a6b10bd`). These commits preserve the authority hierarchy: research
artifacts remain evidence-only, Lifecycle remains fail-closed until canonical
stage-bearing data exists, and the navigation layer does not replace existing
authority documents.

Historical evidence and cleanup candidates remain untouched. This checkpoint
does not authorize worktree/branch cleanup, C: → E: migration, push, merge,
deployment, or `NEXT_TASK` modification.

### Test-count delta attribution

Backend, frontend, integration, migration, contract, and governance full-suite
validation must compare the applicable last canonical baseline, release
candidate, or predecessor closure and report
`TEST_COUNT_PRE`, `TEST_COUNT_POST`, `TEST_COUNT_DELTA`, and
`TEST_COUNT_DELTA_REASON`. An unexplained reduction is
`TEST_COUNT_DELTA_STATUS=BLOCKED_UNEXPLAINED_REDUCTION`. Report
`PASSED`, `FAILED`, `SKIPPED`, `XFAILED`, and `DESELECTED` separately; skipped
or deselected tests are not PASS. `116/116 PASS` alone is not a
regression-free claim. Consolidation, duplicate removal, scope change, rename,
or framework discovery change requires explicit provenance.

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
