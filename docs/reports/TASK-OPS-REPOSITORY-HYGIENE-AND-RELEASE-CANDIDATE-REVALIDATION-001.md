# TASK-OPS-REPOSITORY-HYGIENE-AND-RELEASE-CANDIDATE-REVALIDATION-001

## Fixed handoff

```text
TASK_ID=TASK-OPS-REPOSITORY-HYGIENE-AND-RELEASE-CANDIDATE-REVALIDATION-001
FINAL_STATUS=REPOSITORY_HYGIENE_AND_RELEASE_CANDIDATE_REVALIDATION_BLOCKED
CANONICAL_HEAD=c23d6f7f12fc53cb46ff08c437be6109d4658760
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
RELEASE_CANDIDATE_CODE_SHA=c23d6f7f12fc53cb46ff08c437be6109d4658760
RELEASE_CANDIDATE_REPORT_SHA=cc5c5c66b2fc9851f36e09a400229fb7fd2a579b
CANONICAL_BASELINE_SELF_CONTAINED=NO
REPOSITORY_HYGIENE_STATUS=BLOCKED
WORKTREE_COUNT=18
ACTIVE_OWNER_WORKTREES=1
COMPLETE_CANONICALIZED_WORKTREES=12
COMPLETE_NOT_CANONICALIZED_WORKTREES=1
SUPERSEDED_WORKTREES=3
STALE_UNKNOWN_OWNER_WORKTREES=0
ORPHANED_WORKSTREAM_COUNT=0
LOCAL_ONLY_COMMIT_COUNT=48
REMOTE_ONLY_COMMIT_COUNT=50
LOCAL_REMOTE_DIVERGENCE_SUMMARY=HEAD...origin/main 48 local-only / 50 remote-only; HEAD...same-name-origin 48 / 44; local-main...origin/main 60 / 0
TRACKED_DIRTY_COUNT=18
UNTRACKED_COUNT=167
UNATTRIBUTED_DIRTY_COUNT=8
HIDDEN_DEPENDENCY_CHECK=BLOCKED_COMMITTED_DOCUMENTATION_INDEX_TO_UNTRACKED_PROVIDERS
CANONICAL_RECONCILIATION_REQUIRED=YES
OWNER_DECISION_REQUIRED_ITEMS=stock search/topic-filter canonicalization; 13 broken-link occurrences from 8 untracked doc providers; 8 owner-doc files without explicit task provenance; 30 unmapped local branches; DB-enabled integration preconditions
CLEAN_SOURCE_STATE=PASS
REPRODUCIBLE_DEPENDENCY_STATE=PASS
DEPENDENCY_INSTALL_METHOD=npm ci for apps/web and packages/api-client; fresh Python 3.12 venv with services/api[dev] declared constraints
DEPENDENCY_PROOF=PASS; lockfile/declared-input hashes and environment digest recorded in repository-hygiene-inventory.json
BACKEND_TESTS=PASS_WITH_41_SKIPPED; 457 passed, 41 skipped in repository non-DB/full release-safe run
BACKEND_DB_INTEGRATION=FAILED_ENVIRONMENT; 485 passed, 5 skipped, 4 failed, 4 errors on empty ephemeral 0030 DB
FRONTEND_TESTS=PASS; 116 passed
TYPESCRIPT=PASS
ESLINT=PASS; 0 errors, 1 existing warning in FavoriteButton.tsx
BUILD=PASS
RUFF=PASS
COMPILE=PASS
OPENAPI_DRIFT=PASS
API_CLIENT_TESTS=PASS; 3 passed
MIGRATION_VALIDATION=PASS; single head 0030, upgrade -> downgrade -1 -> upgrade on ephemeral local PostgreSQL
GOVERNANCE_TESTS=PASS; 1 passed
ROUTE_SMOKE=PASS_LOCAL_DIAGNOSTIC; read-only TestClient probes against existing local Docker DB, not candidate data proof
DIFF_CHECK=PASS
SECRET_SCAN=HEURISTIC_PASS; high-risk regex matches 0; gitleaks unavailable
TEST_COUNT_PRE=backend 498 / frontend 116 / api-client 3 / governance 1
TEST_COUNT_POST=backend 498 / frontend 116 / api-client 3 / governance 1
TEST_COUNT_DELTA=0 per suite
TEST_COUNT_DELTA_REASON=No discovery reduction; DB-enabled rerun changed outcome distribution only and exposed empty-DB/reference-state preconditions
G1=PRESERVED_PASS_NOT_RERUN
G2=PRESERVED_PASS_NOT_RERUN
G3=PRESERVED_PASS_NOT_RERUN
POST_CLOSE_CANARY=PRESERVED_PASS_NOT_RERUN
READY_FOR_RELEASE_CHAIN_CLOSURE=NO
READY_FOR_PRODUCTION_RELEASE=NO
REMAINING_BLOCKERS=BLK-HYGIENE-01 completed Stock search/topic-filter lineage not canonical; BLK-HYGIENE-02 committed Documentation Index resolves to owner-untracked providers in clean candidate; BLK-HYGIENE-03 DB-enabled integration suite lacks approved seed/reference fixture environment; BLK-HYGIENE-04 30 unmapped local branches and retained owner state need owner disposition
REPORT_CREATED=YES
APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO_PRODUCTION
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
NEXT_RECOMMENDED_TASK=OWNER_CANONICAL_RECONCILIATION_AND_OWNER_STATE_DISPOSITION_REQUIRED
```

This audit stops before release-chain closure. It does not authorize or execute
BLK-02 exact-SHA API deployment, BLK-03 Sites publication, BLK-04 Production
migration/materialization, BLK-05 fail-closed Production fallback changes, or
BLK-06 control-plane/revision verification.

## Scope and canonical freeze

The authoritative baselines were read before the audit: [AGENTS.md](../../AGENTS.md),
[PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md), [product roadmap](../product/TOPICPILOT_PRODUCT_ROADMAP.md),
[execution roadmap](../ROADMAP.md), [documentation index](../DOCUMENTATION_INDEX.md),
[documentation governance](../DOCUMENTATION_GOVERNANCE.md), the canonical governance
hardening closure, the hidden-dependency closure, and the prior public-site readiness
evidence. The previous `f8736cf` candidate was not reused. The current canonical
committed freeze is `c23d6f7f12fc53cb46ff08c437be6109d4658760`, which includes the
B implementation/report lineage and later governance metadata commits.

The clean candidate is a detached worktree at
`C:\Users\acer\Documents\Codex\tp-revalidation-candidate-20260816`. Its exact
source SHA is `c23d6f7f12fc53cb46ff08c437be6109d4658760`; `git status` is clean and
it did not inherit canonical dirty or untracked files. The machine-readable
topology and attribution ledger is
`reports/TASK-OPS-REPOSITORY-HYGIENE-AND-RELEASE-CANDIDATE-REVALIDATION-001/repository-hygiene-inventory.json`.

## Gate A — current topology snapshot

At the final snapshot, the canonical active worktree is branch
`codex/task-ops-023a-p3c-runtime-sha-audit-20260813` at `c23d6f7`. It has 18
tracked dirty files, 167 untracked files, and zero staged files. The audit found
one remote (`origin`), 44 local branches, six remote-tracking heads, and 18
worktrees after adding the new clean candidate. Fourteen local branches are
attached to worktrees; 30 named local branches remain unmapped and were not
deleted.

The exact comparison is:

| comparison | left-only | right-only |
|---|---:|---:|
| `HEAD...origin/main` | 48 | 50 |
| `HEAD...origin/codex/task-ops-023a-p3c-runtime-sha-audit-20260813` | 48 | 44 |
| `main...origin/main` | 60 | 0 |

The full worktree/branch mapping, status counts, ancestry result, provenance,
and recommended disposition are in the JSON inventory. No reset, stash, clean,
branch deletion, force push, merge, or blanket staging was performed.

## Gate B — worktree and branch disposition

The 18 worktrees resolve to 12 complete/canonicalized lineages, one completed
but not canonicalized lineage, three superseded historical candidates, one
current release-candidate-only clean worktree, and one active canonical owner
worktree. The completed-not-canonicalized lineage is `stock-004`: its branch
contains the completed formal Stock code/name search and topic-filter commits
`06437119c0064ba8541be9734b571b8c05d8125f` and
`429bff35368a7e90558fa5b00364c64cd8fd1d2b`, but its head is not an ancestor of
the canonical freeze and the corresponding query contract is absent from the
candidate. This is not classified as orphaned because the branch and task
provenance are known.

The prior P1C release candidate, Today-004A audit candidate, and prior hidden-
dependency candidate are retained as superseded evidence. The new detached
candidate is the only current release-candidate-only worktree. No branch or
worktree was automatically removed.

## Gate C — local/remote commit reconciliation

The 48 local-only commits group into governance/B/hidden-dependency closure,
REC-A1 and historical authority, Stock-006A/Favorites/Topic research, Stock
EOD, and Today reconciliation lineages. The 50 remote-only commits group into
Today-004D/governance merges, DATA-REF-009, Stock search/topic-filter and
Explorer integration, reference/G2/G3/bootstrap remediation, Today Home, and
CI/bundle-hash lineages. These are SHA-lineage divergences; no remote commit
was merged or pushed.

The candidate contains the completed B implementation/report and its hidden
dependencies, the 0030 assertions, generated API contracts, Today Home
canonical lineage, Stock EOD/history lineage, and prior governance commits.
It does not contain the completed Stock code/name search and formal topic
filter from `stock-004`. Therefore:

```text
CANONICAL_RECONCILIATION_REQUIRED=YES
COMPLETED_NOT_CANONICALIZED=TASK-FE-BE-STOCK-004 search/topic-filter capability
```

This is a release blocker. The task did not cherry-pick, merge, or implement
that feature because the current task is an audit/revalidation task and the
owner dirty branch must be reconciled explicitly.

## Gate D — dirty/untracked attribution and hidden dependency check

All canonical dirty/untracked state was preserved. The 18 tracked files are
path-attributed to retained Today/Topic frontend/tests, architecture/data
documentation, roadmap/work-order, project context, and research fixture
owner state. The 167 untracked files are path-attributed to the owner
architecture document set, task reports/work-orders, research, fixtures,
validation scripts, and task metadata. Eight files under business-rules,
detectors, handoffs, and workshops do not carry enough explicit task
provenance and are `OWNER_DECISION_REQUIRED`; they are not called orphaned
workstreams because their owner-retained path is known.

Application hidden-dependency proof passed in the clean candidate: all 18
expected B/0030/provider/fixture/work-order/generated/report paths are tracked,
backend collection completes, OpenAPI generation/check is clean, and the clean
candidate has no dirty provider state. The documentation boundary does not
pass: the committed `DOCUMENTATION_INDEX.md` resolves to 13 broken-link
occurrences representing 8 unique provider paths that currently exist only in
canonical owner-untracked state, including the Product Surfaces contract,
architecture overview/system docs, research/workshop directories, and the
documentation cleanup report. This creates a committed-consumer to untracked-
provider hygiene blocker.

## Gate E — hygiene decision

```text
REPOSITORY_HYGIENE_STATUS=BLOCKED
UNATTRIBUTED_DIRTY_COUNT=8
ORPHANED_WORKSTREAM_COUNT=0
OWNER_STATE_CLEANUP=NOT_AUTHORIZED
```

The status is `BLOCKED`, not because retained owner state must be deleted, but
because a completed capability is still outside canonical and committed
documentation links are not self-contained in a clean checkout. The 30
unmapped local branches and the 48/50 divergence also require owner review;
they do not authorize cleanup.

## Gates F–I — exact candidate and validation evidence

The code candidate is exactly `c23d6f7f12fc53cb46ff08c437be6109d4658760`.
The candidate passed clean source state. Dependency installation was done in
the candidate only: `npm ci --no-audit --no-fund` in `apps/web` and
`packages/api-client`, plus a fresh Python 3.12 venv installed from
`services/api[dev]` declared constraints. Lockfile/declared-input hashes,
runtime versions, and the Python distribution digest are in the JSON metadata;
no dependency directory was borrowed from another worktree.

Validation results:

| check | result |
|---|---|
| Backend non-DB/full release-safe suite | `457 passed, 41 skipped` |
| Backend DB-enabled suite on empty ephemeral 0030 DB | `485 passed, 5 skipped, 4 failed, 4 errors` |
| Frontend full suite | `116 passed` |
| TypeScript | PASS |
| ESLint | PASS, 0 errors and 1 existing warning in `FavoriteButton.tsx` |
| Production build | PASS; route tree rendered |
| Ruff | PASS |
| Python compile | PASS |
| OpenAPI drift | PASS |
| Generated API client check | PASS; `3 passed` client tests and generated files unchanged |
| Migration | PASS; `0030` single head, upgrade → downgrade -1 → upgrade |
| Governance test | PASS; `1 passed` |
| Route smoke | local read-only diagnostic PASS; not candidate data/Production proof |
| `git diff --check` | PASS |
| Secret scan | heuristic high-risk match count 0; `gitleaks` unavailable |

The DB-enabled failures are not silently converted to PASS: historical read
tests require HIST-002B rows, and normalizer/live fixture tests require an
approved replaceable ACTIVE reference registry state. The migration round-trip
itself passed on an isolated local PostgreSQL database. No Production database
or materialization was touched.

Test discovery did not decrease: the applicable baseline and candidate counts
are backend 498, frontend 116, API client 3, and governance 1. The delta is
zero per suite. The DB-enabled run changes outcome attribution, not discovery;
there is no unexplained test-count reduction.

G1, G2, G3, and the Post-Close Canary remain preserved PASS evidence and were
not rerun because this audit did not change provider authority, reference/
calendar semantics, market/no-trade semantics, or the post-close writer.

## Gate J — readiness decision

```text
READY_FOR_RELEASE_CHAIN_CLOSURE=NO
READY_FOR_PRODUCTION_RELEASE=NO
```

Remaining blockers are:

1. Reconcile the completed `stock-004` search/topic-filter capability into a
   committed canonical lineage, then revalidate the affected API/OpenAPI/Web
   boundary.
2. Resolve the eight owner-untracked documentation providers referenced by
   committed documentation, or explicitly update their owner/disposition under
   the documentation governance process; do not clean them automatically.
3. Provide an approved DB integration fixture/environment for the historical
   and reference-dependent backend tests, or record the exact permitted skip
   boundary in the next canonical closure.
4. Owner-review the 30 unmapped local branches, retained dirty/untracked
   state, and remote divergence; no deletion/reset/stash/force-push is implied.

Until those are resolved, `NEXT_RECOMMENDED_TASK` is intentionally not the
release-chain task. This audit stops here and does not start
`TASK-OPS-PUBLIC-SITE-EXACT-SHA-RELEASE-CHAIN-CLOSURE-001`.

## Safety record

Only this report and the machine-readable inventory are task-created artifacts.
No application code, schema, migration, runtime/deploy configuration, or
Production data was changed. Two exact-name ephemeral local PostgreSQL
databases were created and dropped for migration/full-suite diagnostics. No
remote push, merge to main, deploy, scheduler activation, Production mutation,
branch deletion, reset, stash, or clean operation occurred. `NEXT_TASK` was not
changed.
