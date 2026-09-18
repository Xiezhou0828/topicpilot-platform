# TASK-REL-002 Release Composition and Operator Readback

**Date:** `2026-09-13`
**Scope:** main-derived release composition after GOV-000, GOV-001, and REL-001
**Authority:** repository, Git, migration, deployment configuration, and
public runtime evidence only
**Product feature development:** `NOT PERFORMED`

This report records the exact candidate assembled for REL-002 and the
remaining protected operator checks. It does not reopen GOV-000/GOV-001/REL-001,
does not promote a formal Opportunity provider, and does not merge the Today or
A10/A9 branches incidentally.

## 1. Release result

```yaml
TASK_ID: REL-002
REL_002_STATUS: BLOCKED_OPERATOR_READBACK
MEMORY_RECOVERY: COMPLETE_INHERITED_FROM_GOV-000_AND_GOV-001
CURRENT_STATE_MAP: VERIFIED_AND_RECONCILED
CANONICAL_MAIN_BASE: origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
RELEASE_BRANCH: codex/rel-002-release-candidate-20260913
RELEASE_CANDIDATE_WORKTREE: C:\Users\acer\Desktop\題材領航\topicpilot-platform-rel002-20260913
RELEASE_SHA: a8357d46194f9669709f184949270e20a7a2546c
MAIN_DERIVED: VERIFIED
INCLUDED_COMMITS:
  - da9383614c2f0e46ab3e5817e50b2d71688e3258: bounded formal Opportunity composition
  - a8357d46194f9669709f184949270e20a7a2546c: exact Web release provenance
EXCLUDED_BRANCH_WORK:
  - origin/codex/today-production-convergence-20260913@bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
  - origin/codex/a10-a9-isolated-quote-closure-20260912@51dbe48db203adb56e5fbc47da2f44b0e33997d2
  - origin/codex/a9-b2-production-writer-closure-20260912@68600af
MIGRATION_INTENDED: 0039_task_a9_b2_formal_correction_supersession
MIGRATION_PRODUCTION: UNKNOWN_OPERATOR_REQUIRED
MIGRATION_MATCH: UNKNOWN
API_INTENDED_SHA: a8357d46194f9669709f184949270e20a7a2546c
API_RUNTIME_SHA: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b
API_MATCH: NO
WEB_INTENDED_SHA: a8357d46194f9669709f184949270e20a7a2546c
WEB_RUNTIME_SHA: UNKNOWN_OPAQUE_DEPLOYMENT_VERSION_ONLY
WEB_MATCH: UNKNOWN
WORKER_INTENDED_SHA: a8357d46194f9669709f184949270e20a7a2546c
WORKER_RUNTIME_SHA: UNKNOWN
WORKER_MATCH: UNKNOWN
OPPORTUNITY_FORMAL: CANDIDATE_ROUTE_PRESENT_PROVIDER_FAIL_CLOSED_RUNTIME_404
OPPORTUNITY_SHADOW: RUNTIME_READY_FIXTURE_SYNTHETIC_AS_OF_2026-08-12
TODAY: RUNTIME_PARTIAL_BRANCH_ONLY_NOT_INCLUDED
TOPIC: RUNTIME_PARTIAL_FORMAL_IDENTITY_WITH_DEFERRED_DOMAINS
A10_A9: BRANCH_ONLY_IN_PROGRESS_BLOCKED
MARKET_DATE: 2026-09-09
DATA_AS_OF: 2026-09-09T21:27:16.566804Z
PIPELINE_STATE: PARTIAL_POST_CLOSE_347_SUCCESS_205_FAILURE_240_RETRY
BACKEND_TESTS: FOCUSED_22_PASSED; FULL_684_PASSED_25_BASELINE_FAILURES_59_SKIPPED
FRONTEND_TESTS: 158_PASSED
BUILD: PASS
RUFF: SCOPED_PASS; FULL_REPOSITORY_BASELINE_751_EXISTING_VIOLATIONS
OPENAPI_DRIFT: PASS
MIGRATION_LINEAGE: ONE_HEAD_0039
PRODUCTION_MUTATION_PERFORMED: NO
DEPLOYMENT_PERFORMED: NO
OPERATOR_ACTION_REQUIRED: YES
OWNER_DECISION_REQUIRED: NO_FOR_THIS_COMPOSITION; YES_BEFORE_FORMAL_PROVIDER_ACTIVATION
RELEASE_GATE: BLOCKED
GOVERNANCE_COMMITS: THIS_REPORT_AND_CANONICAL_NAVIGATION_SYNC
PRODUCT_COMMITS: da9383614c2f0e46ab3e5817e50b2d71688e3258, a8357d46194f9669709f184949270e20a7a2546c
NEXT_SAFE_TASK: REL-002-OPERATOR-READBACK-001
ALLOW_NEW_PRODUCT_DEVELOPMENT: NO_UNTIL_OPERATOR_GATE_OR_NEW_OWNER_TASK
```

The candidate is a unique, clean, main-derived composition and is locally
qualified. It is not a Production release because the protected database
revision, API runtime SHA, Web source SHA, and Worker SHA cannot be read back
from this workspace.

## 2. Composition matrix

| Component | Evidence considered | REL-002 disposition | Reason |
|---|---|---|---|
| Canonical product base | `origin/main@b2eaf33...`; one-head migration line ending at `0039` | Included | Required main-derived baseline |
| Formal Opportunity bounded slice | Existing source intent `90c2916...`; reconciled into `da938361...` with API schemas, OpenAPI, generated clients, fail-closed provider, frontend boundary, and focused tests | Included | Explicit GOV-001 owner disposition; no provider or algorithm activation |
| Web release provenance | `a8357d461...`; workflow binds checked-out SHA to `NEXT_PUBLIC_RELEASE_SHA`; root document exposes `data-release-sha` | Included | Minimal release observability permitted by REL-002; no product semantics changed |
| Today production-convergence line | Eight branch-only commits from `1501468...` through `bf68cc8...`; broad branch divergence and runtime-only evidence | Excluded | No blind merge; branch needs separate semantic/release reconciliation |
| A10/A9 isolated quote and writer lines | `17523a8...`, `68600af...`, `51dbe48...`; branch-only writer/quote/migration changes | Excluded | Not required by the bounded Opportunity release; preserve dedicated ownership and gates |
| A10 migration `0040` | Exists on non-main A10/A9/Today lineage only | Excluded | Main intended migration is `0039`; no evidence authorizes promotion of `0040` |
| Existing legacy/V1 paths | Present in main and retained by architecture/governance docs | Retained | No age-only abandonment or cleanup is authorized |

The candidate is `origin/main` plus exactly two candidate commits. The
Opportunity cherry-pick had technical conflicts in shared schemas, generated
clients, OpenAPI, frontend wiring, and governance documents; main's newer
fields and governance history were preserved, the bounded Opportunity classes
were reconciled, and generated artifacts were regenerated and checked. No
mutually exclusive product semantic decision was required.

## 3. Exact-SHA candidate qualification

### Source, migration, and generated contract

- `origin/main` is an ancestor of `a8357d46194f9669709f184949270e20a7a2546c`.
- Candidate worktree was clean after qualification; owner dirty state in the
  canonical checkout was not staged, cleaned, reset, or deleted.
- Candidate migration graph has one head:
  `0039_task_a9_b2_formal_correction_supersession`.
- OpenAPI drift check passed after regeneration. The candidate OpenAPI includes
  `/api/v2/opportunities` and `/api/v2/opportunities/{opportunity_id}` while
  keeping `/api/v1/opportunities/shadow` separate.
- `@topicpilot/api-client` generation/check passed and synchronized the Web
  declaration.
- Scoped Ruff over the changed API and test files passed. Full repository Ruff
  reports 751 pre-existing violations in untouched areas; they are recorded as
  a baseline qualification limitation, not silently fixed in this release.
- `git diff --check` passed.

### Test and build evidence

| Gate | Result | Interpretation |
|---|---|---|
| Opportunity/Home/deployment backend scope | `22 passed` | Candidate release scope passes |
| Full backend suite | `684 passed, 25 failed, 59 skipped` | The 25 failures are in untouched baseline migration/reference/WS3 fixture contracts; PostgreSQL-dependent tests are skipped without protected/test DB credentials |
| Frontend full suite | `158 passed` | Candidate Web contract and preserved surfaces pass |
| Web TypeScript | `PASS` | No type errors |
| Web production build | `PASS` | Build with `NEXT_PUBLIC_RELEASE_SHA=a8357d461...` contains the exact SHA in `dist/server/index.js` |
| API client check | `PASS` | Generated OpenAPI/types are synchronized |
| OpenAPI drift | `PASS` | Required read-only routes and schemas are valid |
| Migration heads | `PASS` | Exactly one head at `0039` |
| Full Ruff | `BASELINE FAIL` | 751 existing repo violations; changed scope passes |

The full-suite failures are not promoted to `ABANDONED`; they identify
pre-existing validation debt. The release gate remains blocked because runtime
and protected deployment evidence are missing, independently of those baseline
failures.

## 4. Reconciled current-state map

The dated history from 2026-08-12 through 2026-09-13 is inherited from
GOV-000/GOV-001 and checked against the candidate and current public runtime.
Code presence is not treated as completion.

| Workstream | Status | Evidence-backed current state |
|---|---|---|
| A10 EOD / 13:35 POST_CLOSE / isolated quote resilience | `IN_PROGRESS + BLOCKED` | Branch-only closure work exists; public POST_CLOSE is partial with provider failures and no canonical runtime SHA alignment |
| A9 structural correction / B2 writer | `IN_PROGRESS + BLOCKED` | Main has correction/supersession schema through `0039`; writer activation/readback remains branch-only and protected |
| B2 Lifecycle V1.3 | `BLOCKED` | Formal contracts/migrations exist; public Topic lifecycle reports `HOLD_FORMAL_GATE` because structural-role authority is incomplete |
| B3 | `UNKNOWN / NOT_STARTED` | No implementation or runtime evidence promoting it |
| B4 | `UNKNOWN / NOT_STARTED` | No implementation or runtime evidence promoting it |
| Today Market / Market Signals | `PARTIAL + IN_PROGRESS` | Live API is `bf68cc8` on a diverged branch; Home is formally published for 2026-09-09, but this line is not the REL-002 candidate |
| Topic Page / Recovery | `PARTIAL` | Identity and snapshots are published, while grade/score/ranking/lifecycle/leadership domains remain deferred or unavailable |
| Opportunity shadow | `VERIFIED SHADOW` | Public shadow route is READY, explicitly `SHADOW`, `FIXTURE/SYNTHETIC`, and as of 2026-08-12 |
| Opportunity formal bounded slice | `VERIFIED CANDIDATE / NOT PRODUCTION` | Candidate route and fail-closed consumer are present; provider deliberately has no formal data authority and must remain unavailable |
| FUND-001 | `UNKNOWN / BLOCKED FOR INITIATION` | No formal FinMind/institution provider, migration, writer, API, or owner approval evidence |
| F1-F9 commercial UI line | `HISTORICALLY CLOSED, RUNTIME/CANDIDATE RECONCILIATION REQUIRED` | Closure artifacts exist, but later branch UI/runtime changes must not be conflated with the candidate or treated as a single release |

No item is labelled `ABANDONED` from age, duplication, or lack of wiring alone.
Legacy, orphan-looking, partial, and failed artifacts remain in the owner
workspace for explicit disposition. `SUPERSEDED` is used only where a later
decision or schema records the relationship; earlier records remain historical.

## 5. Production and public-runtime readback

Readbacks were performed on 2026-09-13 and are evidence of the deployed state,
not of the candidate.

| Boundary | Exact evidence | State |
|---|---|---|
| API `/healthz` | HTTP 200; `status=ok`; `gitSha=bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` | `VERIFIED RUNTIME_ONLY`; mismatch with candidate |
| API `/readyz` | HTTP 200; `status=ready`; same `bf68cc8...` | `VERIFIED RUNTIME_ONLY`; mismatch with candidate |
| API OpenAPI | HTTP 200; shadow route present; formal Opportunity route absent | `RUNTIME_OLD_OR_DIVERGED`; formal API not deployed |
| Home | HTTP 200; publication `PUBLISHED`; data date 2026-09-09; as-of `2026-09-09T21:27:16.566804Z`; Market Overview available; events/opportunities optional-unavailable; heating/cooling insufficient history | `PARTIAL FORMAL READMODEL` |
| Topic | HTTP 200; total 87; formal identity published; lifecycle `HOLD_FORMAL_GATE`; score/grade/deeper domains deferred/unavailable | `PARTIAL` |
| Topic snapshots | HTTP 200; total 92; latest 2026-09-09; snapshot published; `scoreStatus=DEFERRED` | `PARTIAL` |
| Stocks | HTTP 200; total 555 | `PRESENT`; current compact readback did not expose EOD fields on the first row |
| POST_CLOSE | HTTP 200; `PARTIAL`; 552 requested, 347 success, 205 failure, 240 retry, `PROVIDER_REQUEST_FAILED`; universe total 555, unknown 555 | `BLOCKED / PARTIAL` |
| Shadow Opportunity | HTTP 200; `READY`; `SHADOW`; `FIXTURE/SYNTHETIC`; as-of 2026-08-12; count 1 | `VERIFIED SHADOW ONLY` |
| Formal Opportunity | HTTP 404 | `ABSENT IN RUNTIME`; candidate intentionally remains fail-closed without provider activation |
| Admin schema | HTTP 200; metadata-derived schema payload | Does not prove migration revision |
| Protected Production migration | No protected DB access | `UNKNOWN_OPERATOR_REQUIRED` |
| Web `/opportunities` | HTTP 200; fail-closed text present; opaque `deploymentVersion=318c2e47-a67c-4724-bde0-bf75d8be14c0`; no source SHA | `REACHABLE / SHA UNKNOWN` |
| Worker | No independently obtainable runtime SHA | `UNKNOWN_OPERATOR_REQUIRED` |

No production write, deployment, migration, scheduler activation, branch
cleanup, deletion, force push, or `NEXT_TASK` mutation was performed.

## 6. Incomplete, conflicting, and orphan-risk work

1. The candidate formal Opportunity provider is an explicit unavailable
   placeholder. There is no formal Opportunity migration, persisted authority,
   or provider approval; a 503/fail-closed result is correct for this slice.
2. The Today branch contains meaningful UI/data changes and is also the live
   API line, but it is not a main-derived release composition. Its eight
   commits remain excluded pending a separately owned reconciliation.
3. A10/A9 writer and isolated-quote work, including branch-only migration
   `0040`, remain outside this release. Their existence does not establish
   Production activation or completeness.
4. Public runtime data is behind the current date and the POST_CLOSE pipeline
   is partial. This is a data/release verification gap, not an authorization to
   change provider policy or invent data.
5. Canonical checkout owner state remains dirty: one tracked fixture modified
   and 151 untracked owner-retained entries. They were deliberately excluded
   from the release candidate.
6. The full backend suite has 25 untouched baseline failures and 59 protected
   database/integration skips. These remain validation debt for their owning
   workstreams.
7. No explicit evidence authorizes deleting or marking any legacy/orphan-looking
   file `ABANDONED`; cleanup remains a separate governed task.

## 7. Operator-only packet

The following actions require the protected Production operator. They are not
performed by this task.

1. Freeze the release input to the exact candidate SHA:
   `a8357d46194f9669709f184949270e20a7a2546c`.
2. Before any protected migration, read the revision with the existing admin
   authority:

   ```sql
   SELECT version_num
   FROM topicpilot.alembic_version
   LIMIT 1;
   ```

   Record the pre-state and post-state. The intended post-state is exactly
   `0039_task_a9_b2_formal_correction_supersession`; stop if the operator
   cannot prove the revision or if an unexpected head appears.
3. Use the manual release workflow with `release_ref` set to the full SHA,
   retaining the protected API/Web environment controls. The workflow must
   validate the exact checked-out SHA, build Web with
   `NEXT_PUBLIC_RELEASE_SHA`, and retain the artifact-to-SHA mapping.
4. After API deployment, read `/healthz`, `/readyz`, and `/openapi.json` and
   record that the runtime `gitSha` equals the candidate SHA. The formal
   Opportunity route may remain unavailable/fail-closed because no provider
   authority is included; a synthetic formal 200 is a release failure.
5. After Web publication, read the document root `data-release-sha` and record
   that it equals the candidate SHA. The prior opaque Sites deployment version
   is not sufficient by itself.
6. After Worker deployment/startup, capture the hosting revision or an
   equivalent startup provenance record and require the candidate SHA. Do not
   activate a new scheduler policy in this packet.
7. Re-read Home, Topic, Topic Snapshot, Stocks, POST_CLOSE, and Shadow
   Opportunity. Record market date, data as-of, publication state, freshness,
   failure counts, and formal/shadow separation. Do not call the pipeline
   complete while POST_CLOSE is partial or protected data lineage is unknown.
8. If any component SHA, migration revision, data lineage, or Web provenance
   cannot be matched, keep `REL_002_STATUS=BLOCKED_OPERATOR_READBACK` and do
   not promote the release.

## 8. Governance routing and next safe task

GOV-000, GOV-001, and REL-001 remain immutable historical checkpoints. This
report adds the REL-002 exact candidate and does not rewrite their decisions.
The current canonical navigation documents link this report; they continue to
state that `NEXT_TASK` is Owner-controlled.

```yaml
TASK_ID: REL-002-OPERATOR-READBACK-001
STATUS: BLOCKED_OPERATOR_REQUIRED
OWNER: Production operator / release owner
RELEASE_SHA: a8357d46194f9669709f184949270e20a7a2546c
DEPENDENCIES:
  - protected Production database read access
  - Render API and Worker deployment controls
  - Sites publication and runtime HTML readback
  - exact artifact-to-SHA mapping
SAFE_ACTION: perform the operator packet above, then attach exact readbacks
FORBIDDEN: new Opportunity provider, Today Signals, Topic semantics, FUND, UI redesign, cleanup, deletion, NEXT_TASK mutation
```

Until that packet succeeds, memory recovery is complete but the release gate is
not. New product development is not opened by this report.
