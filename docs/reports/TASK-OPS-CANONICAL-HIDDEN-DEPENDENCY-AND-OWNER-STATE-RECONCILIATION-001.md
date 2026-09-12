# TASK-OPS-CANONICAL-HIDDEN-DEPENDENCY-AND-OWNER-STATE-RECONCILIATION-001

## Closure

```text
TASK_ID=TASK-OPS-CANONICAL-HIDDEN-DEPENDENCY-AND-OWNER-STATE-RECONCILIATION-001
FINAL_STATUS=COMPLETE_CANONICAL_BASELINE_SELF_CONTAINED
AUTHORITATIVE_PREDECESSOR=TASK-OPS-RELEASE-CANDIDATE-CANONICAL-RECONCILIATION-001
CANONICAL_PRE_SHA=309aa5f1cf222f5923fa9d6278705e4039804d9b
CANONICAL_POST_SHA=f8736cf
RELEASE_CANDIDATE_SHA=f8736cf
CANONICAL_BASELINE_SELF_CONTAINED=YES
DEPENDENCIES_AUDITED=25_BACKEND_FAILURES_AND_TOPIC_DETAIL_TYPESCRIPT_BUILD_FAILURE
REQUIRED_HIDDEN_DEPENDENCIES=apps/web/app/lib/topic-api.ts publication provider; 0030 migration-head and metadata expectations; three synthetic research fixtures; PHASE_3_6_001B governance work-order
CANONICALIZED_HIDDEN_DEPENDENCIES=apps/web/app/lib/topic-api.ts minimal publication provider hunk; three synthetic research fixtures; PHASE_3_6_001B governance work-order
EXCLUDED_OWNER_DIRTY_STATE=YES; unrelated dirty/untracked state remained outside the explicit write set
TOPIC_DETAIL_HIDDEN_DEPENDENCY_CLOSED=YES
MIGRATION_ASSERTION_DRIFT_CLOSED=YES
OWNER_FIXTURE_DOC_DEPENDENCIES_CLOSED=YES
SOURCE_B_IMPLEMENTATION_SHA=ad3d90c02161f183e6a7fa0aa13229138b8535b5
SOURCE_B_REPORT_SHA=39b03b922dfa3bfb311cbe3b74a3b43c8899907a
CANONICAL_B_IMPLEMENTATION_SHA=32ebea7
CANONICAL_B_REPORT_SHA=f8736cf
B_IMPLEMENTATION_CANONICAL=YES
B_REPORT_CANONICAL=YES
MIGRATION_HEAD=0030_task_topic_daily_state_formal_authority
MIGRATION_0030_CANONICAL=YES
BLK_01_CLOSED=YES
OWNER_DIRTY_TRACKED_PRESERVED=YES
OWNER_UNTRACKED_PRESERVED=YES
COLLISIONS=NONE
BACKEND_TESTS=PASS; 457 passed, 41 skipped, 1 pre-existing warning
B_FOCUSED_TESTS=PASS; predecessor clean-candidate evidence 18 passed; direct 0030 test 6 passed
FRONTEND_TESTS=PASS; 116 passed
TYPESCRIPT=PASS
ESLINT=PASS; 0 errors, 1 existing warning in FavoriteButton.tsx
BUILD=PASS
RUFF=PASS
COMPILE=PASS
OPENAPI_DRIFT=PASS
API_CLIENT_TESTS=PASS; 3 passed
MIGRATION_VALIDATION=PASS; ephemeral local DB 0029 -> 0030 -> 0029 -> 0030
DIFF_CHECK=PASS
SECRET_SCAN=HEURISTIC_PASS; gitleaks unavailable and no high-risk literal match
CLEAN_CANDIDATE_STATUS=PASS; isolated candidate c37c720 had no source dirty state
G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
READY_FOR_RELEASE_CHAIN_CLOSURE=YES
READY_FOR_PRODUCTION_RELEASE=NO
REMAINING_BLOCKERS=BLK-02;BLK-03;BLK-04;BLK-05;BLK-06
REPORT_CREATED=YES
APPLICATION_CODE_CHANGED=YES
DATABASE_MUTATION=NO_PRODUCTION; ephemeral local validation database only
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
NEXT_RECOMMENDED_TASK=TASK-OPS-SDLC-CANONICAL-RELEASE-GOVERNANCE-RECONCILIATION-001
```

The release-candidate SHA above is the exact committed code/report baseline
after the B implementation, B closure report, hidden dependency reconciliation,
and 0030 contract assertions were canonically committed. It is not a
Production-release authorization. The inherited release blockers BLK-02
through BLK-06 remain open.

## Scope and safety boundary

This closure only made the canonical checkout self-contained for the already
completed B capability and the committed code that consumed completed Topic
publication disclosure work. It did not implement lifecycle, score, grade,
ranking, concentration, REC-A1 Walk-Forward, STOCK-006B, fallback configuration,
Render control-plane changes, deployment, Production migration, or Production
data materialization.

No reset, stash, clean, restore, blanket stage, owner-state deletion, remote
push, merge to `main`, deploy, scheduler activation, or `NEXT_TASK` change was
performed. The canonical worktree remained dirty where parallel owner work was
not proven to belong to this task.

## Gate A — canonical topology and ownership

The authoritative canonical repository is
`C:\Users\acer\Desktop\題材領航\topicpilot-platform`. At task start the
canonical state was:

```text
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_HEAD=309aa5f1cf222f5923fa9d6278705e4039804d9b
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_COUNT=16_PRE_EXISTING
OWNER_DIRTY_TRACKED_AT_START=18
OWNER_UNTRACKED_AT_START=171
```

The four selected untracked artifacts below were proven completed, public-safe,
and required by committed tests. They were the only owner untracked artifacts
canonicalized. All other owner dirty/untracked state, including the remaining
parallel Today, Topic, architecture, data, research, and report artifacts,
was preserved and excluded.

## Gate B — dependency ledger

The predecessor clean candidate had `432 passed, 41 skipped, 25 failed` and a
frontend TypeScript/build failure. The 25 backend failures were reproduced in
an isolated candidate based on `309aa5f` plus the two B source commits. Each
failure was attributed before any file was accepted:

| Ledger | Failing tests | Class | Required provider / cause | Provenance and disposition |
|---|---|---|---|---|
| D-01 | `test_canonical_observation_implementation.py::test_canonical_revision_is_linear_after_0018` | B | Expected migration head was still `0029`; B legitimately adds `0030_task_topic_daily_state_formal_authority`. | Updated only the exact head expectation. Integrity/linearity assertion remains active. |
| D-02 | `test_v2_architecture_freeze.py::test_v2_metadata_contains_only_implemented_tables` | B | Expected metadata set omitted B's `topic_snapshot_member_facts`. | Added only the new implemented table to the exact set. Detector/strategy/runtime exclusions remain active. |
| D-03 | `test_governance_consistency.py::test_completed_phase_36_import_is_not_stale_in_register` | C | Required completed `docs/work-orders/PHASE_3_6_001B_FIRST_POSTGRESQL_LEGACY_IMPORT.md` was owner-untracked. | Work order status is `COMPLETED / POSTGRESQL IMPORT VERIFIED` and matches the tracked work-order register; canonicalized explicitly. |
| D-04 | six `test_topic_formula_research_corpus.py` tests: public fixture load, fixture order, tamper duplicate/quality, non-finite/private shape, cross-case replay, corpus/run digest | C | Required `fixtures/research/topic_formula_replay_corpus.v1.json` was owner-untracked. | PHASE-3.7-002C is `PASS / VERIFIED`; four synthetic public-safe cases and the declared digest match; canonicalized explicitly. |
| D-05 | six `test_topic_formula_research_experiment.py` tests: manifest load/order, manifest tamper/path, deterministic report, lineage tamper, byte-identical CLI, unknown fields/duplicate candidates | C | Required `fixtures/research/topic_formula_experiment.v1.json` was owner-untracked. | PHASE-3.7-002E is `PASS / VERIFIED`; manifest binds the approved synthetic candidate corpus and remains research-only; canonicalized explicitly. |
| D-06 | `test_topic_formula_research_history.py::test_generated_corpus_is_deterministic_and_runs_existing_candidates` | C | The historical bridge test consumes the same completed 002E experiment fixture; the failure was missing artifact, not bridge logic. | PHASE-3.7-002F is `PASS / VERIFIED`; the already tracked historical fixture remains unchanged by this task; the missing experiment artifact was canonicalized under D-05. |
| D-07 | nine `test_topic_formula_research_policies.py` tests: strict/diffusion mechanics, valid zero versus missing, candidate order/lineage, five malformed-count cases, and zero denominator | C | Required `fixtures/research/topic_formula_candidate_evidence.v1.json` was owner-untracked. | PHASE-3.7-002D is `PASS / VERIFIED`; synthetic evidence is explicit `RESEARCH_ONLY`, no production default/ranking; canonicalized explicitly. |

The ledger accounts for all 25 failures: `1 + 1 + 1 + 6 + 6 + 1 + 9 = 25`.
No failure required weakening an integrity test, deleting a test, broad xfail,
or broad skip. No failure was classified as genuinely stale/broken code after
the exact contract review.

## Gate C — Topic Detail hidden dependency

Committed `apps/web/app/components/v2/TopicDetailPage.tsx` imports
`getTopicPublication` and `TopicPublicationDisclosure`. At the predecessor
canonical head, the consuming file was committed but the provider exports were
absent from committed `apps/web/app/lib/topic-api.ts`; the exports existed only
in the owner state. The clean candidate therefore failed TypeScript/build with
the exact missing-export error.

The provider provenance is the completed Topic publication disclosure
workstream, `TASK-TOPIC-PUB-001`, whose closure report records
`PASS_VERIFIED_ARCHIVED_WAITING_DEPENDENCIES`, no browser derivation, and the
field-level publication mapping. Source commit `e5fc35d` contains the provider
implementation. The canonicalization accepted only the types, optional status
shape, disclosure mapping, and `getTopicPublication` hunk needed by the
committed Topic Detail consumer. The same-file `sourceLabel` and
`fetchTopicRotation` owner hunks were deliberately excluded and remain dirty.

```text
TOPIC_DETAIL_CONSUMER=committed TopicDetailPage.tsx
TOPIC_DETAIL_PROVIDER_SOURCE=e5fc35d
TOPIC_DETAIL_PROVIDER_CANONICAL=5014d82 (minimal hunk)
TOPIC_DETAIL_HIDDEN_DEPENDENCY_CLOSED=YES
TOPIC_DETAIL_UNRELATED_OWNER_HUNKS_CANONICALIZED=NO
```

The isolated candidate then passed TypeScript, production build, the full
canonical frontend test set, and focused ESLint for the provider/consumer.

## Gate D — migration 0030 assertion reconciliation

B's migration and formal Topic Daily State implementation were verified in the
isolated candidate before permanent promotion. The only exact committed
assertion drift found was:

1. the migration-head expectation in
   `test_canonical_observation_implementation.py`; and
2. the ORM metadata allow-list in `test_v2_architecture_freeze.py`.

The first now expects the single head
`0030_task_topic_daily_state_formal_authority`. The second now includes only
the new `topic_snapshot_member_facts` table. The tests still assert a single
linear head and still reject unapproved `detectors`, `strategy_runs`, and
`runtime_runs`; no integrity test was weakened or removed.

The ephemeral local PostgreSQL round-trip was:

```text
0029 -> 0030 -> 0029 -> 0030 = PASS
```

The ephemeral database was local-only and was not Production. No Production
migration or data materialization was executed.

## Gate E — fixture and documentation provenance

Accepted owner artifacts were limited to these exact files:

```text
docs/work-orders/PHASE_3_6_001B_FIRST_POSTGRESQL_LEGACY_IMPORT.md
fixtures/research/topic_formula_replay_corpus.v1.json
fixtures/research/topic_formula_experiment.v1.json
fixtures/research/topic_formula_candidate_evidence.v1.json
```

The fixtures are synthetic, public-safe, versioned, digest-checked, and
explicitly research-only. Their completed work-order provenance is
PHASE-3.7-002C, 002D, and 002E; the historical bridge is PHASE-3.7-002F. The
governance document is a completed PHASE-3.6-001B work order already named by
the tracked register and required by a committed governance test.

Drafts, generated scratch, temporary reports, unknown-source files, the other
research documents, and unrelated owner reports were not canonicalized. The
selected work-order markdown had one trailing-whitespace cleanup so the
canonical committed dependency passes `git diff --check`; no semantic content
was changed.

## Gate F — isolated candidate and permanent mapping

The candidate was created from a clean checkout of `309aa5f`, then received
only B's implementation/report commits and the explicit seven-file hidden
dependency/assertion change. It never inherited the canonical worktree's
dirty or untracked state.

```text
ISOLATED_CANDIDATE=C:\Users\acer\Documents\Codex\tp-hidden-deps-candidate-20260815
CANDIDATE_B_IMPLEMENTATION_COMMIT=14b5155
CANDIDATE_B_REPORT_COMMIT=3c84d26
CANDIDATE_HIDDEN_DEPENDENCY_COMMIT=c37c720
CANDIDATE_FINAL_SHA=c37c720
CANONICAL_HIDDEN_DEPENDENCY_COMMIT=5014d82
CANONICAL_B_IMPLEMENTATION_SHA=32ebea7
CANONICAL_B_REPORT_SHA=f8736cf
```

The source-to-canonical mapping is explicit. The different SHA values are
expected because cherry-pick creates new canonical commits; the file/tree
contents were validated before promotion.

## Gate G — validation evidence

The clean candidate and then the canonicalized affected paths were validated
without Production access:

| Check | Result |
|---|---|
| Backend full suite | `457 passed, 41 skipped`; skipped PostgreSQL tests reported authentication/explicit test-DB unavailability and were not promoted to PASS |
| B-focused | predecessor isolated candidate `18 passed`; direct `test_topic_daily_state_formal.py` recheck `6 passed` |
| Frontend full tests | `116 passed` on the clean candidate |
| TypeScript | PASS |
| ESLint | PASS: 0 errors, 1 pre-existing warning in `FavoriteButton.tsx` |
| Production build | PASS; Topic routes enumerated |
| Ruff | PASS |
| Python compile | PASS |
| OpenAPI drift | PASS; required read-only routes present |
| API client tests | `3 passed` |
| Migration chain/round-trip | PASS: `0029 -> 0030 -> 0029 -> 0030` on ephemeral local DB |
| `git diff --check` | PASS for candidate and explicit canonical write set |
| Secret/raw scan | Heuristic PASS; gitleaks executable unavailable, no high-risk literal match found |
| Clean candidate status | PASS; source tree clean after `c37c720` |

G1, G2, G3, and the Post-Close Canary remain named preserved PASS evidence
from the predecessor/current protected reports and were not rerun. This task
did not change provider authority, reference/calendar semantics, market/no-trade
semantics, or the post-close writer. Preservation is not Production-release
proof.

## Gate H/I — canonical result and remaining blockers

The permanent canonical repository now contains B's migration/runtime,
generated/OpenAPI contract, B closure report, the proven hidden provider hunk,
the two exact 0030 assertion updates, and the four proven fixture/document
dependencies. It does not contain the unrelated owner state.

```text
CANONICAL_BASELINE_SELF_CONTAINED=YES
BLK_01_CLOSED=YES
B_IMPLEMENTATION_CANONICAL=YES
B_REPORT_CANONICAL=YES
MIGRATION_0030_CANONICAL=YES
TOPIC_DETAIL_HIDDEN_DEPENDENCY_CLOSED=YES
MIGRATION_ASSERTION_DRIFT_CLOSED=YES
OWNER_FIXTURE_DOC_DEPENDENCIES_CLOSED=YES
CLEAN_CANDIDATE_VALIDATION=PASS
RELEASE_CANDIDATE_SHA=f8736cf
READY_FOR_RELEASE_CHAIN_CLOSURE=YES
READY_FOR_PRODUCTION_RELEASE=NO
```

Inherited release blockers remain `BLK-02` exact-SHA API deployment,
`BLK-03` exact-SHA Web/Sites publish, `BLK-04` Production migration and
bounded materialization, `BLK-05` fail-closed Production fallback, and
`BLK-06` protected control-plane/revision verification. Those are intentionally
not acted on here.

No governance-document reconciliation or release-chain task was started after
this successful closure. The next recommended task is
`TASK-OPS-SDLC-CANONICAL-RELEASE-GOVERNANCE-RECONCILIATION-001`, to be opened
separately and explicitly.
