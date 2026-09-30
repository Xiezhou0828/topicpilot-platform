# TASK-CANONICAL-INTEGRATION-AND-BRANCH-HYGIENE-019

Date: 2026-09-30 (Asia/Taipei)

## Scope and safety boundary

This was a repository/mainline reconciliation only. No Production database,
deployment, migration apply, Worker release, API release, Web release,
Scheduler mutation, POST_CLOSE retry/recovery, or observation activation was
performed.

The first fetched canonical `main` was `aad2ae1f47c5a0a2ae389a541de213681a87558d`.
Concurrent TASK-POST-CLOSE-20260930-CURRENT-DAY-HEALTH-018 work advanced
`main` during this task. Candidate work was rebased to the then-current
`main` before promotion, and this report was based on the later
`7331daed7338c0f6b95d94c5af90bf3695655448` current main. No 018 production
activity was retried or changed by this task.

## Canonical integration result

One still-current, completed implementation was validated and promoted:

- `codex/task-reference-bundle-regression-closure-001` was reconciled onto
  current `main` as `codex/task-reference-bundle-regression-closure-019`.
- PR #33 was merged after exact-SHA CI and produced merge commit
  `7aa35ebd64ab946fb1b9a676a2f633169bc21ebb`.
- The promotion added deterministic canonical reference-bundle checking and
  reference-version lineage validation for the corporate-action research
  artifact. It did not change Production state or apply a migration.
- The report itself is this bounded governance checkpoint. No semantic product
  version was invented or bumped.

## Branch inventory at initial analysis

`REMOTE_BRANCH_COUNT_BEFORE=24` excludes `main`. `AHEAD_OF_MAIN` is the count
of commits in `main..branch`; `BEHIND_MAIN` is the count in `branch..main`.
`FILES_NOT_IN_MAIN` is the number of paths in `git diff --name-only
main...branch` at the initial `main` SHA. Squash-merged work is marked
`ALREADY_CANONICAL` when its actual change was present in `main`, even when the
branch tip was not an ancestor because GitHub created a new merge commit.

| Branch | HEAD SHA | Merge base | Ahead | Behind | Commits not in main | Files not in main | Classification |
|---|---|---:|---:|---:|---:|---:|---|
| `codex/production-readonly-forensic-channel-017b` | `da1dd50a223d2e07e0fa83249d7638074358430e` | `da1dd50a223d2e07e0fa83249d7638074358430e` | 0 | 14 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/production-readonly-forensic-channel-017b-disposable-ci` | `aeee7cd85c8cb75fcb683d762600d0c89b75af42` | `aeee7cd85c8cb75fcb683d762600d0c89b75af42` | 0 | 11 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/production-readonly-forensic-channel-017b-report-final` | `a5eef08cb29e65fdaf66674594b90835e5e62367` | `2d676d93b3c1f76f63c89e4d1246a1e674f7e77f` | 1 | 9 | 1 | 2 | `SUPERSEDED` |
| `codex/structural-role-production-read-boundary` | `51a74279c742e8ffaf769aba73031e62876a0e2d` | `75d271ed32f37e8bdd170967dd20671ad4990a5a` | 16 | 69 | 16 | 1 | `INCOMPLETE_OR_BLOCKED` |
| `codex/task-004-promotion-final-report` | `c0dc0ee4d8ccb01f51d0ce9efe4ce5cb4ed3fff4` | `c0dc0ee4d8ccb01f51d0ce9efe4ce5cb4ed3fff4` | 0 | 23 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/task-016-governed-migration-worker-path` | `d129c6201b1b93f211a1d9c114aea42eb422a885` | `73825bff33003b07b845ee1ec05edf7b656d231d` | 1 | 18 | 1 | 5 | `ALREADY_CANONICAL` |
| `codex/task-016-migration-closure-report` | `4f74def1bbbf6e46c783a997ee423a0dbff3c101` | `e8c35469e0134ae8c790f065b3f868cd4912ef94` | 1 | 17 | 1 | 1 | `ALREADY_CANONICAL` |
| `codex/task-a10-post-close-checkpoint-canonical-promotion-003` | `019dc4944d56b02814e668485e10dff6a5b76b37` | `019dc4944d56b02814e668485e10dff6a5b76b37` | 0 | 53 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/task-post-close-20260929-protected-readback-017a` | `9baaa09ed8b06655fa4165b1ce3e46090a3328a6` | `979f3509934b88a2dfbde507704b7511b42ac734` | 1 | 16 | 1 | 1 | `SUPERSEDED` |
| `codex/task-post-close-20260929-root-cause-017` | `759cfc3ba2e803f68d4f4df9e9851e497f7af642` | `979f3509934b88a2dfbde507704b7511b42ac734` | 1 | 16 | 1 | 1 | `SUPERSEDED` |
| `codex/task-reference-bundle-regression-closure-001` | `427946b5790cb4533f3006f0d8dc74f6a094de57` | `c3542a900d6c46e07bc4243804e9705475023316` | 1 | 68 | 1 | 11 | `VALID_PROMOTION_CANDIDATE` → PR #33 |
| `codex/task-today-topic-lower-half-activation-015` | `cd7018ad9625f1bf0aad61d058fc184c443a78b6` | `3e41b7499e7d26463777820997edd3e12ae00a53` | 1 | 20 | 1 | 1 | `ALREADY_CANONICAL` |
| `codex/task-topic-calibration-data-foundation-closure-002` | `27ac01eff270bf35b49d7112646d3393cf6b39ad` | `27ac01eff270bf35b49d7112646d3393cf6b39ad` | 0 | 61 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/task-topic-strength-migration-worker-authority-016` | `e819498c13aa49ec889d206d5784dfa370966400` | `cb67f9c599caf3ceabeb290a7b433e1d4a5210fa` | 1 | 19 | 1 | 1 | `ALREADY_CANONICAL` |
| `codex/today-mainline-topic-pulse-rotation-promotion-014-report` | `de5d916e188f28c1d8e5db0c127e537251e5d5f8` | `d0514eac064e823ddb46c25daa402619f06a1970` | 1 | 21 | 1 | 1 | `ALREADY_CANONICAL` |
| `codex/today-mainline-topic-pulse-rotation-redesign-013` | `08e25e15a9977a503b42889d866468a5e7fd3c4e` | `eb358c10968a78772376020a605edd62253e6dc4` | 6 | 36 | 6 | 25 | `SUPERSEDED` |
| `codex/today-market-signal-v1-implementation-011` | `99d5c0c7b252e3234369e252a4b377592b9af85f` | `99d5c0c7b252e3234369e252a4b377592b9af85f` | 0 | 49 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/today-official-source-worker-activation-009` | `50fa8be2e72929666d3a08ed655fa29812551c7e` | `50fa8be2e72929666d3a08ed655fa29812551c7e` | 0 | 66 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/today-ohlc-institutional-official-source-008` | `75d271ed32f37e8bdd170967dd20671ad4990a5a` | `75d271ed32f37e8bdd170967dd20671ad4990a5a` | 0 | 69 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/today-ohlc-institutional-source-worker-activation-009` | `c3542a900d6c46e07bc4243804e9705475023316` | `c3542a900d6c46e07bc4243804e9705475023316` | 0 | 68 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/topic-calibration-data-foundation-closure-002` | `1a140c63c703bf35b49d7112646d3393cf6b39ad` | `1a140c63c703bf35b49d7112646d3393cf6b39ad` | 0 | 56 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/topic-strength-lifecycle-canonical-promotion-004` | `c555c1d87f0537ed32c311cb0679260d2c001192` | `c555c1d87f0537ed32c311cb0679260d2c001192` | 0 | 25 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/topic-strength-lifecycle-forward-observation-activation-003` | `eb358c10968a78772376020a605edd62253e6dc4` | `eb358c10968a78772376020a605edd62253e6dc4` | 0 | 36 | 0 | 0 | `ALREADY_CANONICAL` |
| `codex/topic-strength-lifecycle-owner-review-002` | `04f208a6e3465207652938e1229f41be122f63f9` | `04f208a6e3465207652938e1229f41be122f63f9` | 0 | 54 | 0 | 0 | `ALREADY_CANONICAL` |

## Promotion and closure decisions

### Promoted

`codex/task-reference-bundle-regression-closure-001` was the only validated
promotion candidate. Its implementation was rebased onto the then-current
main, the documentation-index conflict was resolved by retaining both
canonical links, and PR #33 was opened from the rebased branch. The rebased
candidate SHA was `a48631904b27a939315ff81c242d699202f94196`; exact-SHA CI run
`36682807281` passed; the squash merge produced
`7aa35ebd64ab946fb1b9a676a2f633169bc21ebb`.

### Already canonical

The branches for 017B disposable CI, TASK-004, TASK-016, A10, TASK-015,
calibration foundation, Topic Strength migration/forward observation/owner
review, Today Market Signal, Today official-source, Today OHLC, and the prior
canonical promotion reports were all already represented in `main` through
ancestor or squash-merge evidence. They were not re-merged.

### Superseded and closed

- PR #22 (`codex/task-post-close-20260929-root-cause-017`) — closed as
  superseded by the later 017C/017D exact-SHA evidence on main.
- PR #23 (`codex/task-post-close-20260929-protected-readback-017a`) — closed as
  superseded by the later 017C/017D exact-SHA evidence on main.
- PR #27 (`codex/production-readonly-forensic-channel-017b-report-final`) —
  closed as superseded by the later 017D and current-day forensic checkpoints.

Each PR received a provenance close comment before closure. The historical
commits remain recoverable in repository history; none was merged merely
because it was open.

### Retained blocked work

`codex/structural-role-production-read-boundary` remains the sole 019-retained
blocked branch. Its unique path is `.github/workflows/relation-weight-bootstrap.yml`.
The workflow has a stale default migration head (`0046` while canonical main
is at `0047`), a historical release SHA default, and a Production `apply`
mode. It was not rebased, merged, or executed. It remains
`INCOMPLETE_OR_BLOCKED` pending owner review and a current migration/release
authority decision.

No branch is currently classified `REQUIRES_OWNER_DECISION` separately from
that retained blocked work.

## Branch cleanup

Twenty-four remote branches were deleted after canonical or superseded status
was established and all open PRs were closed or merged. Deleted branches were:

```text
codex/production-readonly-forensic-channel-017b
codex/production-readonly-forensic-channel-017b-disposable-ci
codex/production-readonly-forensic-channel-017b-report-final
codex/task-004-promotion-final-report
codex/task-016-governed-migration-worker-path
codex/task-016-migration-closure-report
codex/task-a10-post-close-checkpoint-canonical-promotion-003
codex/task-post-close-20260929-protected-readback-017a
codex/task-post-close-20260929-root-cause-017
codex/task-reference-bundle-regression-closure-001
codex/task-reference-bundle-regression-closure-019
codex/task-today-topic-lower-half-activation-015
codex/task-topic-calibration-data-foundation-closure-002
codex/task-topic-strength-migration-worker-authority-016
codex/today-mainline-topic-pulse-rotation-promotion-014-report
codex/today-mainline-topic-pulse-rotation-redesign-013
codex/today-market-signal-v1-implementation-011
codex/today-official-source-worker-activation-009
codex/today-ohlc-institutional-official-source-008
codex/today-ohlc-institutional-source-worker-activation-009
codex/topic-calibration-data-foundation-closure-002
codex/topic-strength-lifecycle-canonical-promotion-004
codex/topic-strength-lifecycle-forward-observation-activation-003
codex/topic-strength-lifecycle-owner-review-002
```

For every deleted branch, the delete reason was `ALREADY_CANONICAL` or
`SUPERSEDED`, and the canonical evidence was the current main lineage or the
specific merged PR listed above. Immediately after 019's cleanup, the remote
had one non-`main` branch: the retained structural-role blocked branch.

After that cleanup, concurrent TASK-POST-CLOSE-20260930-CURRENT-DAY-HEALTH-018
created its active branch `codex/current-day-health-018` at
`0cd163106c2365369ac405afcbfc668df5dc4262`. 019 did not delete, close,
rewrite, or otherwise interfere with that branch or its merged PR lineage
(PRs #32, #34, and #35). Therefore the final remote state has two non-`main`
branches: the 019-retained blocked branch and the 018 active branch.

## Canonical capability readback

```text
TODAY_IMPLEMENTATION_CANONICAL=YES
TOPIC_STRENGTH_IMPLEMENTATION_CANONICAL=YES
A10_IMPLEMENTATION_CANONICAL=YES
REFERENCE_BUNDLE_CANONICAL=YES
CALIBRATION_FOUNDATION_CANONICAL=YES
FORENSIC_CHANNEL_CANONICAL=YES

TASK_015_CODE_CANONICAL=YES
TASK_015_PRODUCTION_ACTIVE=NO; BLOCKED_MIGRATION_ACTIVATION_REQUIRED
```

TASK-015 code/report content is canonical through PR #18, but its separate
Production activation was not performed and remains blocked by the governed
0047 migration/release boundary. This task did not deploy or apply that
migration.

## Validation and CI evidence

Candidate-focused validation after rebasing to current main:

- Python 3.12 reference/corporate-action tests: `31 passed`.
- Ruff: passed.
- Python compile: passed.
- Canonical reference-bundle serialization check: passed with
  `CURRENT_BUNDLE_MATCHES_CANONICAL_GENERATOR=YES`.
- Alembic graph: `48` revisions, exactly one head
  `0047_task_topic_role_strength_design_freeze`; passed.
- `git diff --check`: passed.

Exact-SHA GitHub CI for candidate `a48631904b27a939315ff81c242d699202f94196`:

- CI run `36682807281`: Frontend install/test/build passed.
- Backend, migration, and OpenAPI passed, including bundle check, Ruff,
  migration upgrade/rollback, disposable PostgreSQL privilege test, reference
  bootstrap integration, backend tests, OpenAPI drift, and generated TypeScript
  contract checks.
- Secret scan passed.
- Docker Compose smoke passed.

The current main also contains the concurrent 018 current-day forensic
readback commits through `7331daed...`; this task did not alter their
Production behavior. A 018 Production forensic workflow failure is reported
separately by that task and is not a 019 candidate regression. The 018 branch
was discovered after the initial 019 cleanup and is counted separately in the
final remote inventory below.

## Final status

```text
TASK_ID=TASK-CANONICAL-INTEGRATION-AND-BRANCH-HYGIENE-019
TASK_STATUS=COMPLETE_WITH_RETAINED_BLOCKED_AND_CONCURRENT_ACTIVE_WORK

INITIAL_MAIN_SHA=aad2ae1f47c5a0a2ae389a541de213681a87558d
FINAL_MAIN_SHA=9790f3d58f1eec6c88c2351acfed43b158f71ab3

REMOTE_BRANCH_COUNT_BEFORE=24
REMOTE_BRANCH_COUNT_AFTER=2

ALREADY_CANONICAL_BRANCHES=18
SUPERSEDED_BRANCHES=4
PROMOTED_BRANCHES=1
RETAINED_BLOCKED_BRANCHES=1
OWNER_DECISION_BRANCHES=0

PRS_MERGED=#33 (validated reference promotion), #36 (019 report); prior canonical PR evidence retained: #11-#21, #24-#26, #28-#31; concurrent 018 PRs #32,#34,#35 were not modified
PRS_CLOSED_SUPERSEDED=#22,#23,#27
PRS_LEFT_OPEN=NONE

TODAY_IMPLEMENTATION_CANONICAL=YES
TOPIC_STRENGTH_IMPLEMENTATION_CANONICAL=YES
A10_IMPLEMENTATION_CANONICAL=YES
REFERENCE_BUNDLE_CANONICAL=YES
CALIBRATION_FOUNDATION_CANONICAL=YES
FORENSIC_CHANNEL_CANONICAL=YES

TASK_015_CODE_CANONICAL=YES
TASK_015_PRODUCTION_ACTIVE=NO; BLOCKED_MIGRATION_ACTIVATION_REQUIRED

CANONICAL_INTEGRATION_CHECKPOINT_SHA=9790f3d58f1eec6c88c2351acfed43b158f71ab3
TAG_CREATION_REQUIRES_OWNER_AUTHORIZATION=YES

BACKEND_VALIDATION=PASS; exact-SHA CI run 36682807281
FRONTEND_VALIDATION=PASS; exact-SHA CI run 36682807281
RUFF_STATUS=PASS
MIGRATION_GRAPH_STATUS=PASS; 48 revisions, one head 0047
CI_STATUS=PASS; exact candidate SHA a48631904b27a939315ff81c242d699202f94196

PRODUCTION_DB_MUTATED=NO
PRODUCTION_DEPLOYED=NO
POST_CLOSE_RETRIED=NO
SCHEDULER_CHANGED=NO

TASK_COMPLETE=YES

NEXT_ACTIVE_BRANCHES=codex/structural-role-production-read-boundary; codex/current-day-health-018 (concurrent 018, out of 019 scope)
NEXT_RECOMMENDED_TASK=Owner review and current-SHA reconciliation of the retained structural-role relation-weight bootstrap workflow; do not execute its Production apply mode as part of 019.
```
