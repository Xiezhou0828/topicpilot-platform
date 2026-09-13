# TASK-GOV-001 Canonical Branch, Runtime, and Workstream Reconciliation

**Date:** `2026-09-13`
**Scope:** GOV-001 recovery continuation after GOV-000
**Product implementation at recovery start:** `NOT PERFORMED`
**Authority rule:** repository, Git, migration, deployment, and public-runtime evidence only

## 1. Outcome at recovery start

GOV-000 recovered the dated project state and identified the safe next task.
This report records the next read-only reconciliation before any product
implementation is promoted. Chat history is treated as an audit hypothesis
list only; it cannot promote a feature to `VERIFIED`.

```yaml
TASK_ID: GOV-001
PHASE: RECOVER
PHASE_STATUS: VERIFIED
PRODUCT_FEATURE_IMPLEMENTATION_DURING_RECOVERY: NO
CANONICAL_PRODUCT_BASELINE: origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
GOVERNANCE_CHECKPOINT_BASELINE: 27c5e137d957db6132734e680f09bd4f68f197d5
PUBLIC_API_RUNTIME_SHA: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
PUBLIC_API_RUNTIME_BRANCH: origin/codex/today-production-convergence-20260913
CANONICAL_MAIN_RUNTIME_MATCH: NO
OPPORTUNITY_OWNER_DISPOSITION: CANONICALIZE_EXISTING_FORMAL_SLICE_NO_REDESIGN
NEXT_TASK_MUTATION: NO
```

The canonical product baseline and the live API baseline are different Git
lines. The difference is a release-chain reconciliation finding, not evidence
that either line is universally correct.

## 2. Evidence capture

| Boundary | Evidence | State / interpretation |
|---|---|---|
| Canonical product baseline | `origin/main` at `b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40`, `fix(topics): batch relation authority preflight` | Recommended clean product baseline |
| Governance checkout | branch `codex/task-ops-023a-p3c-runtime-sha-audit-20260813`, HEAD `27c5e137d957db6132734e680f09bd4f68f197d5` | GOV-000 documentation lineage; not a Production release candidate |
| Public API | `/healthz` and `/readyz` HTTP 200, `gitSha=bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` | Runtime-only branch evidence |
| Public Web | `/opportunities` HTTP 200; opaque Sites `deploymentVersion=318c2e47-a67c-4724-bde0-bf75d8be14c0` | Web deployment is reachable, but no source SHA is exposed |
| Worker | No independently obtainable public worker SHA/readback | `UNKNOWN`; operator evidence required |
| Main migration head | `0039_task_a9_b2_formal_correction_supersession` | Canonical main schema head |
| A10 migration | `0040_task_a10_recovery_checkpoint_observability.py` exists on A10/A9 branch only | Branch-only; not canonical main migration authority |
| Working tree | 6 modified tracked entries plus 173 untracked entries; only 2 untracked application source/test files | `ACTION_REQUIRED`; pre-existing owner state retained, not cleaned automatically |

The two untracked application files are the formal Opportunity API module and
its focused test. The other untracked entries are documentation, reports,
architecture, work-order, research, or evidence artifacts. No untracked
migration, schema, or frontend source file was found at this capture.

## 3. Branch and runtime classification

The following vocabulary is used without collapsing states:

- `VERIFIED`: the named bounded contract or evidence is present and directly
  supported by the cited source.
- `IN_PROGRESS`: implementation or closure evidence exists, but canonical or
  release gates remain open.
- `PARTIAL`: some boundary is implemented, while required downstream pieces
  remain absent or deferred.
- `BLOCKED`: a named authority, credential, provider, data, or release gate is
  required and absent.
- `SUPERSEDED`: a later accepted decision explicitly replaces an earlier one;
  the earlier record remains historical.
- `ABANDONED`: explicit owner/repository evidence says the work was abandoned;
  code age alone never receives this state.
- `UNKNOWN`: available evidence cannot support a stronger state.

| Workstream | Main / canonical evidence | Branch or runtime evidence | Reconciled state | Safe conclusion |
|---|---|---|---|---|
| A10 EOD, post-close, isolated quote resilience | A10 activation/batching foundation is in main history through `74226c3`; migration head remains `0039` | `51dbe48` adds isolated quote publication and recovery observability; live POST_CLOSE readback is `PARTIAL` with 552 requested, 347 success, 205 failure, 240 retry, `PROVIDER_REQUEST_FAILED` | `IN_PROGRESS + BLOCKED` | Keep the branch closure as branch evidence; no Production completion claim |
| A9 structural correction / A9-B2 writer | Correction/supersession schema is canonical through migration `0039` | `68600af` and `51dbe48` contain later writer/13:35 closure work; no canonical post-deploy proof | `IN_PROGRESS + BLOCKED` | Contract foundation is verified; writer activation and runtime readback remain open |
| B2 Lifecycle V1.3 | Migrations `0037`–`0039`, read contracts, and fail-closed API are present | Production Topic/Lifecycle readback has unavailable/deferred stage data; protected ontology activation is absent | `BLOCKED` | Do not infer formal stage publication from schema or branch code |
| B3 | No implementation evidence; B2 reports state not started | No runtime or branch evidence promoting B3 | `UNKNOWN / NOT_STARTED` | Keep unopened and dependency-bound to B2 |
| B4 | No implementation evidence; B2 reports state not started | No runtime or branch evidence promoting B4 | `UNKNOWN / NOT_STARTED` | Keep unopened and dependency-bound to B2/B3 |
| Today Market / Market Signals | Main has Home/read-model and earlier rule-based foundations | `bf68cc8` is the live API tip and adds deterministic signal publication; Today commercial branch is diverged from main | `PARTIAL + IN_PROGRESS` | Runtime behavior is real evidence but not a canonical main release |
| Topic Page / Topic Recovery | Topic list/detail, Topic API, snapshot contract, and fail-closed consumers exist | Runtime Topic V1.3 returns unavailable/deferred score, grade, Lifecycle, ranking, breadth, concentration, and leadership fields | `PARTIAL` | Recovery is not complete; no new Topic semantics are authorized |
| Opportunity shadow slice | Shadow API/read model/strategies/tests are tracked; runtime endpoint is available | Runtime is `SHADOW` with `FIXTURE/SYNTHETIC`, `asOf=2026-08-12` | `VERIFIED SHADOW / NOT FORMAL` | Preserve as separate legacy/research boundary |
| Opportunity formal page slice | Dirty tracked schema/wiring/OpenAPI/client changes plus two untracked source/test files | Default provider explicitly returns 503; no formal route exists in live runtime | `IMPLEMENTED + VALIDATED / UNCOMMITTED / BLOCKED` | Owner has authorized canonicalization of this exact slice; no provider or algorithm redesign |
| FUND-001 / institutional data | No FinMind provider, formal task, migration, or formal institution-flow API found | No production readback proving a formal institutional source | `UNKNOWN / BLOCKED FOR INITIATION` | Create an initiation packet only; do not implement |

## 4. API, schema, migration, frontend, and provider audit

### API and schema

- The tracked shadow boundary remains `/api/v1/opportunities/shadow` and its
  detail/topic routes.
- The dirty formal slice adds `/api/v2/opportunities` and
  `/api/v2/opportunities/{opportunity_id}` with contract
  `opportunity-page-read.v1`.
- Formal responses require `publicationStatus=FORMAL` and
  `sourceStatus=FORMAL_CANONICAL`; shadow, fixture, research, demo, and
  fallback payloads are rejected.
- The default `CanonicalOpportunityProvider` is an explicit unavailable
  placeholder and raises a 503. It does not borrow the shadow provider.
- The generated OpenAPI and TypeScript declarations are dirty copies of the
  formal slice. They have no canonical SHA at this capture.

### Migration and persistence

- No formal Opportunity migration or persistence table was found.
- That absence is consistent with the current provider boundary: the slice is
  a read-contract/provider seam, not an activated formal data authority.
- The canonical main migration head remains `0039`; branch-only A10
  observability migration `0040` is not promoted by this recovery.

### Frontend and deployed Web

- Canonical checkout `apps/web/app/opportunities/page.tsx` still routes to the
  shared `V2Page` placeholder.
- The Today production-convergence branch changes that shared route to an
  explicit fail-closed boundary: “機會功能尚未發布” and no frontend filtering
  or demonstration data. The public Web contains the same boundary wording.
- This is `BRANCH_ONLY / RUNTIME_ONLY` evidence until the exact intended
  consumer is committed in the canonical Opportunity lineage and its build is
  verified.

### Scheduler and data pipeline

- `render.yaml` keeps API and worker auto-deploy disabled and starts both with
  `alembic upgrade head`.
- Public operations readback remains `PARTIAL`; no evidence allows the data
  pipeline to be called fully verified.
- No scheduler activation, production write, protected database mutation, or
  deployment action was performed by this recovery phase.

## 5. Half-finished, legacy, orphan, and conflict inventory

| Item | Evidence-based status | Disposition |
|---|---|---|
| Formal Opportunity API source/test | `DIRTY_ONLY`, focused backend tests previously passed; no canonical SHA | `CANONICALIZE` as one atomic bounded slice |
| Formal Opportunity generated OpenAPI/client types | `DIRTY_ONLY`, coupled to the source/schema diff | Canonicalize only with source and wiring; regenerate/check together |
| Formal Opportunity provider | Explicit unavailable placeholder | Keep `BLOCKED`; do not create a provider without formal authority/data approval |
| Current shared V2 page | Placeholder in canonical checkout | Replace only with the already evidenced fail-closed consumer; no redesign |
| Today production convergence branch | `RUNTIME_ONLY / BRANCH_ONLY` against main | Reconcile by evidence; do not merge the entire branch incidentally |
| A10/A9 closure branches | `BRANCH_ONLY` | Preserve; promotion requires a separate release chain and protected readback |
| Legacy V1/import/writer paths | Retained V1 bridge | Not abandoned; retirement requires V2 parity and explicit cutover |
| Large untracked architecture/research/report package | Mixed historical, draft, and owner artifacts | Retain; no deletion, rename, or blanket staging |

No item is labelled `ABANDONED` from age, duplication, or non-use alone. No
branch, worktree, file, or historical decision was deleted, reset, force-pushed,
or silently rewritten.

## 6. Owner decisions and blockers

The explicit GOV-001 owner disposition is:

```yaml
DEC_GOV_001_A:
  opportunity_existing_formal_slice: CANONICALIZE
  redesign: NO
  allowed: source/tests/schemas/OpenAPI/generated-client/wiring/frontend-consumer/provider-boundary/release-evidence
  forbidden: new-opportunity-algorithm, recommendation-semantics, scoring-semantics, formal-provider-activation
```

The following are separate blockers and are not silently treated as code work:

1. Protected Production credentials/database access are not available for
   operator-only migration, write, or runtime lineage verification.
2. No approved formal Opportunity provider/data authority exists. The formal
   API therefore remains fail-closed even after canonicalization.
3. Public Web exposes an opaque deployment version rather than a source SHA;
   exact Web provenance remains an operator/release-chain gap.
4. A10/A9 and Today runtime branches are not reconciled to canonical main.
5. Current workspace hygiene is action-required because pre-existing owner
   artifacts remain untracked; automatic cleanup is prohibited.

## 7. Phase routing

| Phase | State at this checkpoint | Next allowed action |
|---|---|---|
| `RECOVER` | `VERIFIED` | Preserve this report and link it from canonical navigation |
| `CANONICALIZE` | `IN_PROGRESS` | Canonicalize only the existing formal Opportunity slice |
| `VERIFY` | `PENDING` | Run focused backend, OpenAPI/client, frontend boundary, and clean-candidate checks |
| `RELEASE` | `BLOCKED / NOT_REQUESTED` | No deployment; record exact-SHA and operator gaps |
| `CLOSE` | `PENDING` | Update governance registry, handoff, and next-safe-task routing after verification |

The recommended baseline for new work is `origin/main@b2eaf33` plus explicitly
committed GOV-001 governance and Opportunity changes. The live API SHA
`bf68cc8` remains runtime evidence only until an owner-approved release chain
reconciles it.

## 8. Safe next task

```yaml
TASK_ID: OPP-REC-001
STATE: READY_FOR_CANONICALIZATION
OWNER: GOV-001 execution boundary; formal provider activation remains owner-gated
BRANCH: codex/task-ops-023a-p3c-runtime-sha-audit-20260813
WORKTREE: C:\Users\acer\Desktop\題材領航\topicpilot-platform
DEPENDENCIES: existing Opportunity formal contract; no new data authority
LAST_KNOWN_COMMIT: dirty working tree; no canonical SHA yet
CANONICAL_BASELINE: origin/main@b2eaf33 plus GOV-000 docs
IMPLEMENTATION_STATE: bounded source/schema/API/provider-boundary slice exists
TEST_STATE: focused backend evidence exists; clean candidate verification pending
RELEASE_STATE: NOT_RELEASED
RUNTIME_STATE: formal route absent; shadow route remains synthetic
BLOCKERS: no formal provider; protected production and exact Web SHA unavailable
OWNER_DECISION: DEC-GOV-001-A canonicalize, no redesign
OPERATOR_ACTION: none required for local canonicalization; required for production readback
NEXT_SAFE_ACTION: stage only the reviewed Opportunity slice, commit it atomically, then verify clean candidate
```

No new FUND, Signals, Topic, or Opportunity algorithm work is opened by this
report. `NEXT_TASK` remains owner-controlled and was not edited.
