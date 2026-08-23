# TopicPilot Documentation Governance

**Status:** `CANONICAL / DOCUMENT LIFECYCLE POLICY`
**Effective:** 2026-08-10

## Authority hierarchy

1. Explicit PM-approved product contracts and decision records.
2. Canonical architecture, data contract, source strategy, API, frontend design, operations, and product documents listed in [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
3. Current roadmap/status and active work orders.
4. Reports, task prompts, worklogs, screenshots, and validation artifacts as historical evidence.
5. Chat messages and uncommitted drafts are context only.

If documents conflict, record the conflict and point to the higher authority. Do not silently rewrite history.

## Canonical versus historical

Canonical documents answer “what is current?” and have an owner, status, date, and source links. Historical evidence answers “what happened and what proved it?” Completed task prompts, implementation/acceptance reports, old phase plans, superseded drafts, and repeated runtime evidence are historical even when technically useful.

## Lifecycle

`DRAFT` -> `REVIEW` -> `ACCEPTED`/`COMMITTED` -> `SUPERSEDED` or `ARCHIVED`. `REJECTED` is retained when the rejection is useful evidence. A work order does not become canonical merely because it was completed.

## Archive rules

- Keep completed work orders in `docs/work-orders/` while they are actively referenced; later, archive by year/month only after inbound links are updated.
- Keep reports in `docs/reports/`; future completed-report batches may use `docs/reports/archive/<year>/<month>/`.
- Put old planning documents in `docs/archive/` only after checking links and adding a superseded pointer.
- Never delete solely for neatness. `DELETE_CANDIDATE` is a review recommendation, not an instruction.
- Do not change evidence content except for a clearly labelled archive/superseded header.

## Worklog rule

Long-term worklog entries contain Date/Task ID, Outcome, Key verification, Canonical docs affected, Evidence pointer, and Remaining issues. Full prompts and raw evidence stay in their original task/report files or a historical worklog archive. This repository currently has no `AI/AI_WORKLOG.md`; create it only when an active worklog owner and source are identified.

## Safe cleanup protocol

Before moving a file: inventory exact path, search inbound links, classify role, choose destination, move with Git-visible history, update links, and verify links. When the worktree is already heavily modified or file role is uncertain, leave the file in place and record the recommended action in the cleanup report.

## SDLC state and canonicalization rules

The governed lifecycle is:

`IMPLEMENTED` -> `VALIDATED` -> `CANONICALIZED` -> `RELEASE_CANDIDATE` -> `PRODUCTION_RELEASED` -> `POST_DEPLOY_VERIFIED`.

`FINAL_STATUS=COMPLETE`, `CAPABILITY_STATUS=COMPLETE`, or `tests PASS` does
not by itself mean `CANONICALIZED`, `RELEASE_CANDIDATE`,
`PRODUCTION_RELEASED`, or public visibility. `CANONICALIZED` requires the
approved result in the canonical repository at a committed SHA and a preserved
source-to-canonical SHA provenance mapping. The canonical repository is the
single authority; an isolated PASS is source evidence only.

Every implementation closure records `CANONICAL_STATUS`, `RELEASE_STATUS`, and
`PRODUCTION_VERIFICATION`. If its result is not canonical, it also records one
of `READY_FOR_CANONICAL_RECONCILIATION`, `CANONICALIZED`,
`BLOCKED_COLLISION`, or `OWNER_DECISION_REQUIRED` as
`CANONICAL_RECONCILIATION_DISPOSITION`. A committed consumer may not depend on
a dirty or untracked provider, fixture, generated artifact, or document. Clean
candidate evidence must come from the committed exact SHA in a clean checkout;
dirty PASS is diagnostic only.

Orphaned worktrees are not an accepted lifecycle state. Reconcile or explicitly
retain them under Owner decision with evidence and provenance. Local migration,
data, and materialization checks cannot be labelled Production-ready or
Production-visible. Release readiness must cover exact-SHA API/Web provenance,
fail-closed behavior, migration/data state, rollback readiness, and deployed
revision verification. `PUSH_REMOTE=NO` and `DEPLOY=NO` are safety boundaries,
not evidence that promotion is complete.

## Report tier authority and handoff

The report tiers are intentionally non-overlapping: implementation reports own
implementation facts; canonical-closure reports own canonical provenance;
release reports own Production promotion; post-deploy reports own public
verification. Later reports link prior evidence and record transitions but do
not rewrite the prior report's historical status. New work starts by reading
`AGENTS.md`, `PROJECT_CONTEXT.md`, the related roadmap/work order, and the
latest capability closure; release work additionally reads readiness and
canonical-closure reports. `NEXT_TASK` is Owner-authorized; agents may
recommend but may not change it.

## Current release-hygiene checkpoint

The 2026-08-16 closure reports establish that release-hygiene workstreams A
and B are closed and that `BLK-HYGIENE-01/02/03/04` are closed.
`READY_FOR_RELEASE_CHAIN_CLOSURE=YES` while
`READY_FOR_PRODUCTION_RELEASE=NO`. Owner dirty/untracked state remains
preserved and classified. These current facts may be reflected in canonical
navigation and routing documents, but the reports remain the detailed evidence
owners; release-chain closure still requires Owner authorization and does not
change `NEXT_TASK`.

## Canonical boundary reconciliation (2026-08-22)

Today, Topic Lifecycle, research tooling, research-only inputs, L2/L5 evidence,
and the subordinate documentation navigation layer are committed in separate
boundaries. Historical evidence and cleanup candidates remain preserved. A
committed consumer must not be treated as self-contained until its referenced
provider, fixture, generated artifact, and source hash are also committed in
the same canonical lineage. This checkpoint does not authorize cleanup,
worktree/branch deletion, C: → E: migration, push, deployment, or `NEXT_TASK`
mutation.

## Safe modification boundary

Governance edits preserve concurrent owner state. Use explicit paths and hunks
only; blanket stage, clean, reset, and stash operations are prohibited. When a
dirty or untracked collision cannot be isolated, fail closed with the exact
file/hunk and use `BLOCKED_COLLISION` or `OWNER_DECISION_REQUIRED` rather than
overwriting the owner state.

## Reproducible validation environment

Release-candidate and canonical validation require both
`CLEAN_SOURCE_STATE=PASS` and `REPRODUCIBLE_DEPENDENCY_STATE=PASS`. The latter
comes from lockfile-derived installation (`npm ci`, frozen pnpm, equivalent
Python locked/declared environment) or an approved container/CI environment.
Another dirty worktree's dependency directory, junction, partial install, or
unconstrained global package is not final proof. A borrowed dependency
directory is `DIAGNOSTIC_FALLBACK_ONLY` unless lockfile equivalence, dependency
digest, and approved reproducibility evidence are recorded.

## Commit-preserving promotion evidence

Canonical promotion SHOULD use a validated commit, cherry-pick, or deterministic
commit-preserving merge/rebase. Index-only or manual hunk reconciliation is an
exception only for a proven shared dirty-file owner overlap without a complete
source commit. The closure then records `HUNK_LEVEL_RECONCILIATION_USED=YES`,
`REASON`, `HEAD_INDEX_WORKTREE_AUDIT=PASS`, and
`POST_RECONCILIATION_CLEAN_CANDIDATE=PASS`, and proves no task-owned residual
diff or persistent HEAD/index/worktree split.

## Repository/worktree/remote hygiene evidence

Release readiness, canonical closure, and fixed Owner review classify canonical
versus `origin/main` divergence; local-only and remote-only commits; completed
branches not canonicalized; stale, superseded, or orphaned worktrees/commits;
completion states whose `CANONICAL_STATUS` is not `CANONICALIZED`; ownerless
active worktrees; dirty tracked-file aging/ownership; untracked artifact
aging/provenance; committed consumers using uncommitted state; missing
local-commit provenance mappings; and candidate ancestry. Reports include
`REPOSITORY_HYGIENE_STATUS`, `LOCAL_ONLY_COMMIT_COUNT`,
`STALE_WORKTREE_COUNT`, `ORPHANED_WORKSTREAM_COUNT`, and
`UNATTRIBUTED_DIRTY_COUNT`. `ACTION_REQUIRED` or `BLOCKED` prevents direct
cleanup, branch deletion, force reset, or force push and requires Owner
disposition or `CANONICAL_RECONCILIATION_REQUIRED`.

## Test-count delta evidence

Backend, frontend, integration, migration, contract, and governance full-suite
reports compare the applicable last canonical baseline, release candidate, or
predecessor closure using `TEST_COUNT_PRE`, `TEST_COUNT_POST`,
`TEST_COUNT_DELTA`, and `TEST_COUNT_DELTA_REASON`. An unexplained reduction is
`TEST_COUNT_DELTA_STATUS=BLOCKED_UNEXPLAINED_REDUCTION`. `PASSED`, `FAILED`,
`SKIPPED`, `XFAILED`, and `DESELECTED` remain separate; skipped or deselected
tests are not PASS, and `116/116 PASS` is not alone a regression-free claim.
Consolidation, duplicate removal, scope/rename changes, or framework discovery
changes require explicit provenance.
