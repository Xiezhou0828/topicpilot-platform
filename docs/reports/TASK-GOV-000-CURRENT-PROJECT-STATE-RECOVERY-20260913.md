# GOV-000 Current Project State Recovery

**Date:** `2026-09-13`
**Scope:** repository archaeology, Git/deployment reconciliation, governance-document synchronization
**Product implementation:** `NOT PERFORMED`
**Authority baseline:** `origin/main` at `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40`
**Canonical repository:** `C:\Users\acer\Desktop\題材領航\topicpilot-platform`

## 1. Outcome

The current project state has been recovered from repository, Git, migration,
deployment, and public-runtime evidence. Chat history was used only as a list
of audit hypotheses; it was not used to promote any feature to complete.

`GOV-000` is a documentation-only recovery. No product feature, schema,
migration, runtime configuration, Production data, deployment, or
`NEXT_TASK` was changed.

```yaml
GOV_000_STATUS: VERIFIED
MEMORY_RECOVERY: COMPLETE
CURRENT_STATE_MAP: CANONICALIZED_IN_THIS_REPORT
NEW_PRODUCT_FEATURE_IMPLEMENTATION: NOT_AUTHORIZED_BY_THIS_TASK
PRODUCTION_RELEASE_GATE: BLOCKED_OR_UNVERIFIED
NEXT_TASK: OWNER_CONTROLLED_AND_UNCHANGED
ABANDONED_WORK_CONFIRMED_BY_REPO: NONE
```

This means the repository memory is now recoverable for the next agent. It does
not mean that the four requested product workstreams are complete or that the
currently live API is the canonical `main` release.

## 2. Evidence boundary and method

The evidence set was captured on `2026-09-13` from:

- `origin/main`, all relevant remote branches, Git history, branch ancestry,
  and the full Git worktree list;
- `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`, `docs/WORK_ORDERS.md`,
  `docs/DOCUMENTATION_GOVERNANCE.md`, `docs/DOCUMENTATION_INDEX.md`,
  work-order reports, closure reports, handoffs, and decision/architecture
  documents;
- Alembic migration heads and migration lineage;
- implementation paths under `apps/web/`, `services/api/`, and tests;
- public runtime readback from `https://topicpilot-api.onrender.com` for
  health, readiness, OpenAPI, Home, operations, Topic, Stock, and Opportunity
  endpoints.

The canonical Desktop checkout was already dirty and on a task branch before
this recovery. Existing code, reports, and untracked files were preserved.
The current report and the three navigation updates below are the only files
changed for `GOV-000`.

## 3. Repository and Git baseline

### 3.1 Canonical and reconciled heads

| Boundary | Evidence | Interpretation |
|---|---|---|
| Reconciled main baseline | `origin/main` = `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` (`fix(topics): batch relation authority preflight`, 2026-09-12) | Canonical committed baseline used for this report |
| Canonical checkout at capture | branch `codex/task-ops-023a-p3c-runtime-sha-audit-20260813`, HEAD `4053d655`, dirty | Owner work in progress; not promoted to main by this task |
| GOV-000 analysis checkout | clean isolated worktree based on `origin/main` | Read-only audit boundary; not a product release |
| Migration head on main | `0039_task_a9_b2_formal_correction_supersession` | Single Alembic head; A10 observability migration `0040` is branch-only |
| Final local branch relation | current task branch is `199` commits ahead and `95` behind `origin/main` after the two local GOV commits | Not a main checkout; includes pre-existing task history and must not be treated as a clean release baseline |

The canonical checkout has extensive pre-existing modifications and untracked
documentation/runtime artifacts. They were not staged, reset, cleaned, or
merged.

### 3.2 Relevant remote branches

| Workstream/ref | Tip | Relationship to `origin/main` | State |
|---|---|---:|---|
| A10 production / batching | `ce61762` / `74226c3` | contained by main | VERIFIED in main history; production readback still separate |
| A10/A9 isolated quote closure | `51dbe48db203adb56e5fbc47da2f44b0e33997d2` | 3 commits ahead, 0 behind | IN_PROGRESS / not canonicalized |
| A9/B2 production-writer closure | `68600af6f095fc84084cad9cde235cfee707df95` | 2 commits ahead, 0 behind | IN_PROGRESS / not canonicalized |
| B2 protected topic authority | `a50346b` | contained by main | BLOCKED by protected authority activation |
| Today commercial investor release | `569d2b4` | 6 ahead, 51 behind | PARTIAL / diverged branch |
| Today production convergence | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` | 8 ahead, 51 behind | live runtime branch; not canonical main |

Branch existence is not completion. A branch-only implementation is recorded
as branch evidence and is not promoted to `main`, Production, or a feature
registry `VERIFIED` state without reconciliation and release evidence.

## 4. State vocabulary

The following states are used consistently in this recovery:

- `VERIFIED` — the named contract, implementation, or evidence exists in the
  reconciled canonical baseline and its bounded claim is supported.
- `IN_PROGRESS` — active committed work exists, but its intended closure is
  not complete.
- `PARTIAL` — a usable subset exists while one or more required surfaces,
  data authorities, consumers, or release gates remain incomplete.
- `BLOCKED` — the next required action cannot safely proceed because an
  authority, protected credential, dependency, or acceptance gate is absent.
- `SUPERSEDED` — a historical claim or implementation has a newer explicit
  replacement; the old evidence remains preserved.
- `ABANDONED` — explicit repository or owner evidence says the work was
  abandoned. No candidate was promoted to this state without such evidence.
- `UNKNOWN` — the repository does not contain enough evidence to make a
  stronger claim.

`COMPLETE` is not used as a release state. Existing work-order states remain
authoritative for their own scope and are not rewritten by this snapshot.

## 5. Current-state map: requested parallel lines

| Line | State | Last known evidence | Ownership / dependency | Current conclusion |
|---|---|---|---|---|
| A10 EOD / post-close / quote resilience | `IN_PROGRESS` + `BLOCKED` for release verification | Main contains A10 activation/batching through `74226c3`; A10/A9 branch adds formal writers, 13:35 trigger, recovery observability, and isolated quote publication through `51dbe48` | Ops/data pipeline; protected Production runtime and provider success are required | Main has a canonical foundation. The newer closure is branch-only. Live POST_CLOSE is `PARTIAL`: 347 successes, 205 failures, 240 retries out of 552 requested, with `PROVIDER_REQUEST_FAILED`. |
| A9 structural correction / A9-B2 writer | `IN_PROGRESS` + `BLOCKED` | Main migration head includes `0039_task_a9_b2_formal_correction_supersession`; writer/13:35 closure remains on `68600af` / `51dbe48` | Topic authority, correction path, protected writer activation | Correction/supersession schema is canonical. The latest writer closure is not in main and has no canonical post-deploy verification. |
| B2 Lifecycle V1.3 / bootstrap / supersession | `BLOCKED` | B2 V1.3 contracts and migration `0037`/`0038`/`0039` are in main; reports record missing protected ontology activation authority | Topic ontology / formal structural-role authority | Production readback exposes contract V1.3, but lifecycle stage is unavailable and formal scope activation is blocked. B3 and B4 are explicitly not started. |
| B3 | `UNKNOWN` as a future execution state; operationally `NOT_STARTED` | B2 reports say `B3_STARTED=NO` | Depends on B2 formal activation | No implementation may be inferred from shared code paths. |
| B4 | `UNKNOWN` as a future execution state; operationally `NOT_STARTED` | B2 reports say `B4_STARTED=NO` | Depends on B2/B3 decisions | No implementation may be inferred from shared code paths. |
| Today Market / Market Signals | `PARTIAL` + `IN_PROGRESS` on diverged branch | Main has Home/read-model and rule-based Daily Focus foundations. `bf68cc8` adds deterministic market-signal publication and is the live runtime tip, but is not in main | Today FE/BE release, formal capability matrix, API/UI parity | A deterministic signal catalog is live with an empty signal set for the captured date. Main and live runtime are not reconciled; live `asOf` is 2026-09-09. Commercial closure report remains blocked. |
| Today institutional / FUND-001 | `UNKNOWN` / `BLOCKED` for formal development | No `FinMind` provider, FUND-001 task, dedicated formal migration, or formal institution-flow API was found. Existing institution fields are nullable or legacy/synthetic | Source/provider authority and owner-approved formal contract | Chat claims are not repo evidence. Do not start FUND-001 until its source authority, freshness, schema, consumer, and owner are explicitly recorded. |
| Topic Page / Topic Recovery | `PARTIAL` | Main contains Topic list/detail, Topic API, formal PIT snapshot publication, lifecycle contracts, and fail-closed UI/API disclosures | WS1 structural-role authority, Score/Grade publication, lifecycle stage rows, correction propagation | A formal snapshot exists, but derived intelligence is deferred: score/grade null, lifecycle `SHADOW_ONLY_UNPUBLISHED` or unavailable, ranking/breadth/concentration deferred, leadership unavailable. No dedicated “Topic Recovery” task/report was found in main. |
| Opportunity | `PARTIAL` + `BLOCKED` for formal publication | Shadow contract/API/read model/strategies/tests exist; a separate formal page API exists only in the dirty tree with generated contract changes; frontend route is still a shared V2 placeholder; canonical provider explicitly has no configured provider | Formal data, policy validation, strategy/research boundary, publication consumer, clean canonical commit | Runtime endpoint is `SHADOW`, `FIXTURE/SYNTHETIC`, dated 2026-08-12. The dirty formal API focused tests pass, but source/provider/frontend/release provenance is incomplete. This is not a production recommendation or formal opportunity publication. |
| WS1 structural role / score / lifecycle | `VERIFIED` infrastructure; `PARTIAL` data publication | Additive authority/read-model infrastructure and fail-closed resolvers are canonical; live stage-bearing rows are absent | Owner-reviewed effective-dated role/projection authority | Infrastructure is verified; data population and Score/Grade/Lifecycle publication remain gated. |
| WS2 Stock Technical V0 | `VERIFIED` policy/contracts; `PARTIAL` formal evidence | Project context records 14 PIT-safe indicators, 0 formal evidence instruments, 85 available with limitation, 422 blocked | Provider/consumer contract and continuity evidence | The policy surface is canonical; formal evidence publication is not complete. |
| WS3 research | `VERIFIED` as research evidence only | A1/A2 and lifecycle-conditioned studies are preserved as bounded descriptive evidence | Forward evidence; no strategy semantic promotion | No strategy, score, threshold, or Production promotion is authorized by these artifacts. |
| WS4 release qualification | `IN_PROGRESS` / `BLOCKED` for Production | Release-chain qualification is documented, but no canonical Production release/post-deploy verification is established | Exact release SHA, migration, runtime, data pipeline, operator gates | Ready-to-close release evidence is not equivalent to Production release. |

### 5.1 Explicit absence and non-claims

- `FUND-001` is not verified as started, implemented, or formally blocked by
  a dedicated work order. The safe state is `UNKNOWN` with a recommended
  owner decision, not `DONE`.
- No repository evidence establishes a completed Topic Page Recovery. Existing
  Topic code is a partial/fail-closed implementation, not proof of recovered
  UX or data semantics.
- No repository evidence establishes a formal Opportunity V1 publication.
  The existing endpoint is explicitly shadow and synthetic.
- No implementation was labelled `ABANDONED` solely because it is old,
  branch-only, unconnected, or under a placeholder route. Those items are
  retained as `PARTIAL`, `UNKNOWN`, or `OWNER_DECISION_REQUIRED` until an
  explicit disposition exists.

## 6. Implementation, schema, API, and consumer audit

| Area | Evidence | State / disposition |
|---|---|---|
| Topic schema and migration | Migrations `0030` through `0039`; one Alembic head at `0039` | `VERIFIED` bounded schema lineage; derived publication remains gated |
| Topic API | `/api/v2/topics`, `/api/v2/topic-snapshots`; V1.3 contract and fail-closed status fields | `PARTIAL`; live Topic score/grade/lifecycle publication is unavailable/deferred |
| Topic frontend | `apps/web/app/components/v2/TopicListPage.tsx`, `TopicDetailPage.tsx`, `topic-api.ts` | `PARTIAL`; disclosure/fail-closed consumers exist, but recovery completion is not evidenced |
| Today API | Home read model and publication contracts in main; deterministic signals added on `bf68cc8` | `PARTIAL`; live branch diverges from main and lacks clean canonical release evidence |
| Today frontend | Mainline Home components plus commercial branch changes | `PARTIAL`; branch-only UI changes must not be treated as canonical |
| Opportunity backend | `opportunity_shadow_api.py`, `opportunity_shadow_read.py`, `topic_engine/opportunity_*` | `PARTIAL`; canonical provider is explicitly unconfigured; fixture provider is synthetic |
| Opportunity frontend | `apps/web/app/opportunities/page.tsx` routes to `V2Page`; `V2Page.tsx` says data is not connected | `PARTIAL` / `UNWIRED`; no formal consumer |
| Institutional/FUND | Nullable `institutionFlows`, legacy/synthetic screener fields; no FinMind provider/task found | `UNKNOWN`; no formal authority promotion |
| A10 migration/observability | `0040_task_a10_recovery_checkpoint_observability.py` exists only on A10/A9 branch | `IN_PROGRESS`; not part of main migration head |
| Legacy bridges | `services/api/src/topicpilot_api/legacy_import/` and related V1 paths | `VERIFIED` as retained legacy bridge; not abandoned. V2 replacement, dual-run/parity, and explicit cutover are required before retirement |

## 7. Production and deployment state

### 7.1 Runtime readback

The public API was read back on `2026-09-13`:

| Check | Result |
|---|---|
| `/healthz` | HTTP 200; `gitSha=bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` |
| `/readyz` | HTTP 200; same SHA |
| `/openapi.json` | HTTP 200; deployment description says public data is synthetic |
| `/api/v2/home` | HTTP 200; `contract=v2.home-read-model.v2`, `asOf=2026-09-09`, deterministic signal catalog present, signal list empty |
| `/api/v1/operations/live/status` | `PARTIAL`; POST_CLOSE requested 552, success 347, failure 205, retry 240; provider failure `PROVIDER_REQUEST_FAILED` |
| `/api/v2/topic-snapshots?latest=true` | Formal snapshot exists; Score/Grade deferred; Lifecycle `SHADOW_ONLY_UNPUBLISHED` |
| `/api/v2/topics` | V1.3 contract; grade/score/lifecycle unavailable; reason `STRUCTURAL_ROLE_AUTHORITY_INCOMPLETE` |
| `/api/v2/stocks` | Formal stock EOD read exists; `adjustmentState=UNKNOWN` |
| `/api/v1/opportunities/shadow` | `status=READY`, `publicationStatus=SHADOW`, `dataStatus=FIXTURE/SYNTHETIC`, `asOf=2026-08-12` |

### 7.2 Deployment conclusion

The live API SHA `bf68cc8` is the tip of the diverged
`origin/codex/today-production-convergence-20260913` branch, not
`origin/main` `b2eaf33`. Therefore:

```yaml
CANONICAL_MAIN_RUNTIME_MATCH: NO
LIVE_RUNTIME_SHA: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
CANONICAL_MAIN_SHA: b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
PRODUCTION_DATA_AS_OF: 2026-09-09
PIPELINE_STATE: PARTIAL
TOPIC_DERIVED_PUBLICATION: NOT_AVAILABLE_OR_DEFERRED
OPPORTUNITY_FORMAL_PUBLICATION: NO
POST_DEPLOY_VERIFICATION: NOT_PASS
```

The runtime is useful evidence, but it cannot be used as proof that the
canonical main release is deployed. The branch/runtime split is a release
reconciliation blocker.

## 8. Incomplete, legacy, orphan, and conflicting work inventory

The lexical repository scan on `origin/main` found approximately:

```yaml
TODO/FIXME/HACK_MATCH_FILES: 1
PLACEHOLDER_OR_MOCK_MATCH_FILES: 96
LEGACY_OR_DEPRECATED_MATCH_FILES: 248
PARTIAL_OR_UNWIRED_MATCH_FILES: 221
ORPHAN_OR_DEAD_LEXICAL_MATCH_FILES: 20
```

These are triage counts, not automatic defect counts. Representative items:

| Item | State | Safe interpretation |
|---|---|---|
| `apps/web/app/components/v2/V2Page.tsx` shared placeholder | `PARTIAL` | Shared route foundation; not proof that every routed page is implemented |
| `V2Foundation.tsx` search/notification placeholders | `PARTIAL` | UI foundation placeholders; require explicit product scope before replacement |
| Topic detail history/timeline placeholder | `PARTIAL` | Consumer exists with missing formal history capability |
| `CanonicalOpportunityReadProvider` | `BLOCKED` | Explicitly raises because no canonical provider is configured |
| Opportunity calibration placeholder | `PARTIAL` | Research/contract placeholder; not a production algorithm |
| Legacy import/writer paths | `VERIFIED` as legacy bridge | Must be retained until V2 parity/cutover decision |
| Sites database-ID placeholder in Vite config | `UNKNOWN` / owner review | Deployment integration placeholder; not evidence of production data readiness |
| Old or detached worktrees | `OWNER_DECISION_REQUIRED` | Do not delete or label abandoned without owner evidence |

### 8.1 Worktree and parallel-line conflicts

Git reports `30` worktrees. The audit found the canonical Desktop checkout
dirty, several additional dirty task/review worktrees, detached historical
worktrees, and old task branches spanning August through September. No
worktree was removed or cleaned.

The material conflicts are:

1. **Canonical main versus live runtime:** live `bf68cc8` is not main
   `b2eaf33`.
2. **Today commercial versus main:** commercial UI/API work is on a diverged
   branch; its closure report explicitly remains blocked by stale protected
   API readback at capture time.
3. **A10/A9 writer closure versus main:** formal-writer, 13:35 trigger, and
   isolated-quote closure commits are branch-only; migration `0040` is not the
   main head.
4. **Topic implementation versus Topic recovery claim:** Topic API/UI and
   formal snapshot infrastructure exist, but derived publication and lifecycle
   rows are absent. No dedicated recovery closure was found.
5. **Historical reports versus current state:** older handoffs, including the
   2026-08-16 cold-start report and 2026-08-22 project context, remain valid
   historical evidence for their capture point but are superseded as the latest
   complete current-state snapshot by this `GOV-000` report.

No file or branch was deleted, renamed, reset, or force-updated.

## 9. Decision and authority reconciliation

- Existing product, architecture, work-order, and historical decisions were
  preserved. This report does not rewrite their acceptance status.
- Where a later branch changes an earlier operational claim, the relationship
  is recorded as branch-level `SUPERSEDES` evidence, not silently applied to
  main. Example: the branch-level 13:35 post-close trigger supersedes the old
  15:00 proposal only on that branch until canonical reconciliation.
- `docs/WORK_ORDERS.md` remains the task-status index. `NEXT_TASK` remains
  owner-controlled and was not edited.
- `PROJECT_CONTEXT.md` remains startup navigation; `docs/ROADMAP.md` remains
  execution routing; this report is the dated evidence snapshot and recovery
  map, not a replacement for either authority.

## 10. Safe next task recommendation

The next safe task is a release/reconciliation task, not a new FUND, Signals,
Topic, or Opportunity feature implementation:

```yaml
RECOMMENDED_TASK: GOV-001 Canonical Branch/Runtime Reconciliation and Release-Chain Readback
STATUS: RECOMMENDED_ONLY
OWNER: OWNER_ASSIGNMENT_REQUIRED
SCOPE:
  - reconcile or explicitly retain the live bf68cc8 branch/runtime split
  - compare exact API/Web/worker SHAs against the intended canonical baseline
  - verify migration head, protected data authority, scheduler state, and data date
  - produce a release readback with API/UI parity and post-deploy evidence
OUT_OF_SCOPE:
  - new product features
  - deleting old worktrees or legacy files
  - changing NEXT_TASK without owner approval
  - protected Production mutation without operator authority
EXIT_GATE: canonical/runtime/release evidence is either reconciled or explicitly dispositioned
```

After `GOV-001` is owner-assigned and its release boundary is resolved, the
four product lines may be opened one at a time under their existing work-order
and authority gates. `FUND-001` requires a new explicit owner-approved
contract before implementation.

## 11. Recovery acceptance checklist

- [x] Main baseline, task branch, remote refs, commits, and worktrees inspected.
- [x] `docs/tasks`, reports, handoffs, decisions, `NEXT_TASK` ownership, and
      existing documentation governance inspected.
- [x] FUND, Today Signals, Topic Recovery, Opportunity, A10/A9/B2, WS1–WS4,
      schema/migration/API/frontend and production evidence reconciled.
- [x] Statuses separated into `VERIFIED`, `IN_PROGRESS`, `PARTIAL`, `BLOCKED`,
      `SUPERSEDED`, `ABANDONED`, and `UNKNOWN` without promoting code presence
      to completion.
- [x] Legacy, placeholder, synthetic, unwired, branch-only, and stale-worktree
      candidates inventoried without destructive cleanup.
- [x] Governance navigation updated to point to this report.
- [x] Existing work orders and historical reports preserved.
- [x] No product implementation, deployment, Production mutation, or
      `NEXT_TASK` mutation performed.

**Final gate:** `記憶恢復完成`。新產品開發可以在讀取本報告、遵守既有
authority/release gates 且由 owner 指派下一個 work order 後開始；本次
`GOV-000` 本身沒有授權任何新功能實作。

## 12. Current dirty/untracked version inventory addendum

After the initial reconciliation, the canonical checkout was re-read at the
same capture date because the user-owned working tree contains more than the
committed main baseline. This is important for the next clean-development
handoff.

```yaml
TRACKED_MODIFIED_ENTRIES: 9
UNTRACKED_STATUS_ENTRIES: 154
TOTAL_STATUS_ENTRIES: 163
STATUS_OWNER: PRE_EXISTING_CANONICAL_CHECKOUT_STATE
AUTOMATIC_CLEANUP: NO
AUTOMATIC_PROMOTION_TO_MAIN: NO
```

The nine tracked modifications are:

```text
PROJECT_CONTEXT.md
apps/web/app/lib/generated-api.d.ts
docs/DOCUMENTATION_INDEX.md
docs/ROADMAP.md
fixtures/research/topic_formula_historical_evidence.v1.json
packages/api-client/openapi.json
packages/api-client/src/schema.d.ts
services/api/src/topicpilot_api/main.py
services/api/src/topicpilot_api/schemas.py
```

The governance files in this report are intentionally included in that dirty
state. The other modified paths pre-date this addendum and remain owner state.
The fixture change is formatting-only. The API/schema/generated-client changes
belong to the untracked formal Opportunity slice described below.

After the governance-only commit `745f9f3`, the final working-tree readback is
`6` modified tracked entries plus `153` untracked status entries (`159` total).
The remaining untracked source files are exactly the formal Opportunity module
and its focused test; no untracked migration, schema, or frontend source file
remains outside the already-recorded design/document package.

### 12.1 Version-family disposition

| Version family / path group | Evidence found | Current disposition |
|---|---|---|
| `V1` legacy engines and bridges | Explicit AGENTS boundary; `price_engine.py`, `ta_engine.py`, `radar.py`, legacy import/scheduling paths | `VERIFIED LEGACY BRIDGE`; retain until V2 parity and explicit cutover; do not add features |
| `V2` PostgreSQL/FastAPI/read-model/frontend | Current canonical generation and tracked main implementation | `VERIFIED ACTIVE GENERATION`; individual capabilities remain separately gated |
| API `v1` | Shadow/legacy operational paths, including `/api/v1/opportunities/shadow` and operations endpoints | `PARTIAL / LEGACY-SHADOW`; not formal Opportunity authority |
| API `v2` | Topic, Stock, Home, and current read-model contracts in main | `PARTIAL`; formal publication depends on capability-specific authorities |
| Topic Daily State `0030` | Mainline formal snapshot/member-fact lineage and related reports | `VERIFIED BOUNDED FOUNDATION`; derived Score/Grade/Lifecycle remain unpublished or shadow |
| Lifecycle V1.3 / B2 `0037`–`0039` | Canonical contracts, initialization/authority reports, one migration head at `0039` | `BLOCKED`; protected ontology activation and stage-bearing production rows are missing |
| A10 recovery observability `0040` | Migration and writer changes exist on A10/A9 branch only | `IN_PROGRESS / BRANCH-ONLY`; not main migration authority |
| Opportunity Shadow `opportunity-shadow-read.v1` | Tracked backend/frontend adapter and live synthetic endpoint | `VERIFIED SHADOW CONTRACT`; not formal publication |
| Opportunity formal page `opportunity-page-read.v1` | Untracked `opportunity_api.py`, untracked focused tests, modified schemas/OpenAPI/generated declarations | `IMPLEMENTED + VALIDATED / UNCOMMITTED / BLOCKED`; no provider, no canonical SHA, no formal frontend consumer |
| Selector V1 | Formal validator/tests and research boundary in untracked Opportunity slice; no provider output | `CONTRACT-READY / NOT-PUBLISHED`; not a recommendation or production strategy |
| Phase 2.1–2.9 architecture package | Untracked logical/physical/ORM/migration/persistence design files explicitly saying design/specification only | `DESIGN-ONLY / NOT CANONICALIZED`; not half-implemented runtime code |
| Phase 3.1 detector package | Untracked draft/blueprint/planning files; `DET_RANGE_V1` remains draft | `PLANNING / DRAFT`; no production detector promotion |
| Phase 3.4–3.6 observation/work-order package | Untracked contracts, plans, and “PASS” documents with implementation boundaries | `HISTORICAL EVIDENCE / OWNER REVIEW`; document PASS is not code canonicalization |
| Phase 3.7 Topic formula/scorer/recommendation package | Untracked work orders and reports; overlaps tracked WS1 authority and research-only surfaces | `PARTIAL / OVERLAPPING`; retain evidence, do not promote or reopen semantics automatically |

### 12.2 Untracked artifact groups

The current untracked state is grouped as follows. Directory-level counts are
Git status entries, not claims that every nested artifact has the same status.

| Group | Count | Evidence-based disposition |
|---|---:|---|
| `docs/architecture/` | 61 | Mixed draft, proposed, completed-spec, PM-pending, and duplicate-candidate documents. Retain; canonical owners are unresolved for a subset. |
| `docs/reports/` | 37 | Historical audits/closures, including explicit `AUDIT ONLY`, `BLOCKED`, `UNCOMMITTED`, and `NOT_RUN` states. Retain as evidence; do not use as current authority without reconciliation. |
| `docs/work-orders/` | 44 | Historical/planning work-order series, many with `PASS` meaning document/task-scope validation. Untracked status prevents canonical implementation claims. |
| `docs/business-rules/`, `docs/detectors/`, `docs/workshops/` | 3 | Rules/templates/workshop evidence; no automatic runtime authority. |
| `docs/handoffs/` | 1 | Dated chat handoff; superseded for startup navigation, retained for history. |
| `reports/` evidence directories | 4 | Raw JSON/CSV/research/runtime evidence; preserve provenance, do not treat as current code or production proof. |
| root Chinese explanation files | 2 | Unattributed owner artifacts; `UNKNOWN`, owner disposition required. |
| untracked formal Opportunity source/test | 2 | Active dirty implementation slice; must be reconciled as one atomic unit or explicitly retained/shelved. |

The existing Phase 2 provenance audit already records nine authority-unknown
architecture documents, fifteen architecture duplicate candidates, and eight
superseded-but-retained documents. Those classifications remain the safest
disposition; this recovery does not duplicate, delete, move, or merge them.

### 12.3 Unfinished implementation discovered in the dirty tree

The most material half-finished slice is the formal Opportunity API:

```yaml
SOURCE:
  - services/api/src/topicpilot_api/opportunity_api.py [UNTRACKED]
  - services/api/tests/test_opportunity_api.py [UNTRACKED]
CONSUMER_WIRING:
  - services/api/src/topicpilot_api/main.py [DIRTY TRACKED]
CONTRACTS:
  - services/api/src/topicpilot_api/schemas.py [DIRTY TRACKED]
  - packages/api-client/openapi.json [DIRTY TRACKED]
  - packages/api-client/src/schema.d.ts [DIRTY TRACKED]
  - apps/web/app/lib/generated-api.d.ts [DIRTY TRACKED]
VALIDATION: 11 focused tests passed, 1 warning, in current dirty environment
DEFAULT_PROVIDER: explicitly unavailable; returns fail-closed 503
FORMAL_DATA_PROVIDER: NOT_CONFIGURED
FRONTEND_PAGE: still routes to shared V2 placeholder
CANONICAL_SHA: NONE
RELEASE_STATUS: NOT_RELEASED
PRODUCTION_VERIFICATION: NOT_RUN
```

This is a coherent bounded implementation, not an abandoned artifact, but it
is not a finished feature. The generated client and modified schema are
dependent on an untracked provider module. Under the repository rules, that is
a hidden dependency and cannot be promoted or called canonical until the exact
source, test, generated artifacts, and frontend boundary are reconciled in a
clean committed candidate.

### 12.4 Clean-development rule after this audit

The next agent must not start a new product line from the current dirty tree
without first choosing one of these explicit dispositions for the Opportunity
slice and the untracked document package:

1. `CANONICALIZE` — owner accepts the exact source/test/generated contract,
   creates a clean commit, runs impact validation, and records release status;
2. `RETAIN_FOR_FOLLOW-UP` — preserve the artifacts with an owner, task ID,
   dependency list, and next action, without wiring them into new consumers;
3. `SUPERSEDE_AND_RETAIN` — link a newer accepted artifact and preserve the
   old evidence; or
4. `ABANDONED` — only after explicit owner evidence, never by age or filename
   alone.

Until then, the recommended next task remains `GOV-001` release/runtime and
dirty-tree reconciliation. New FUND, Signals, Topic Recovery, or Opportunity
feature work should not begin from these uncommitted artifacts.

### 12.5 Final completion audit

```yaml
CURRENT_BRANCH_AND_HEAD_RECORDED: PASS
ORIGIN_MAIN_BASELINE_RECORDED: PASS
GOVERNANCE_FILES_COMMITTED: PASS
GOVERNANCE_FILES_HAVE_NO_RESIDUAL_DIFF: PASS
DIRTY_SOURCE_SURFACE_RECONCILED: PASS
UNTRACKED_MIGRATION_SOURCE_FOUND: NO
UNTRACKED_SCHEMA_SOURCE_FOUND: NO
UNTRACKED_FRONTEND_SOURCE_FOUND: NO
UNREGISTERED_HALF_FINISHED_IMPLEMENTATION_FOUND: NO
OWNER_DISPOSITION_QUEUE: PRESENT_AND_EXPLICIT
PRODUCT_FEATURE_DEVELOPMENT_STARTED_BY_GOV_000: NO
```

`UNREGISTERED_HALF_FINISHED_IMPLEMENTATION_FOUND=NO` means every current
dirty implementation surface found by this audit has an entry and disposition
in this report. It does not mean the Opportunity slice is complete; its
incomplete provider, frontend, canonicalization, and release gates remain
explicitly open.

## 13. Clean-worktree recovery result

The existing GOV isolated worktree was clean at `origin/main` before a
checkpoint-switch experiment. The experiment attempted to materialize
branch-only LFS/research artifacts and exhausted the local C: volume. The
experiment was reverted without touching the canonical checkout:

```yaml
WORKTREE: C:\Users\acer\.codex\worktrees\GOV-000-Current-Project-State-Recovery
FINAL_HEAD: b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
FINAL_STATE: CLEAN
GOVERNANCE_CHECKPOINT_PRESENT_IN_WORKTREE: NO
CANONICAL_CHECKOUT_MODIFIED_BY_RECOVERY: NO
CHECKOUT_GENERATED_ARTIFACT_COPIES_REMOVED: 6
SOURCE_BLOBS_DELETED_FROM_CANONICAL_REPOSITORY: NO
```

This worktree is therefore a clean `origin/main` analysis baseline, not a
release candidate and not a substitute for the canonical repository. The
latest governance commits remain in the canonical task branch; a future clean
development worktree should be created or reconciled by `GOV-001` after owner
selection of the canonical branch/runtime baseline.
