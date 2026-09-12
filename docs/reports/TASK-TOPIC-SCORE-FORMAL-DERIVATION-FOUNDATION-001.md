# TASK-TOPIC-SCORE-FORMAL-DERIVATION-FOUNDATION-001

## Closure scope

This is the documentation closure for **WS1 Phase 1 — Topic Score formal
derivation/publication foundation**. It records only the accepted foundation
that derives a Topic Score from already-canonicalized Topic PIT daily-state
evidence. It does not activate or publish a Topic Score read model and does
not expand into Grade publication, Lifecycle, Opportunity, Recommendation,
Production, deployment, scheduler, or `NEXT_TASK` work.

| Field | Evidence |
| --- | --- |
| `TASK_ID` | `TASK-TOPIC-SCORE-FORMAL-DERIVATION-FOUNDATION-001` |
| `WORKSTREAM` | `WS1 / Topic Derived Intelligence / Phase 1` |
| `FINAL_STATUS` | `COMPLETE_FOR_SCOPE` |
| `CAPABILITY_STATUS` | `FORMAL_DERIVATION_FOUNDATION_IMPLEMENTED` |
| `CANONICAL_STATUS` | `CANONICALIZED` |
| `CANONICAL_RECONCILIATION_DISPOSITION` | `CANONICALIZED` |
| `RELEASE_STATUS` | `NOT_RELEASE_CANDIDATE` |
| `PRODUCTION_VERIFICATION` | `NOT_PERFORMED` |
| `PUSH_REMOTE` | `NO` |
| `DEPLOY` | `NO` |
| `PRODUCTION_MUTATION` | `NO` |
| `SCHEDULER_ACTIVATION` | `NO` |
| `NEXT_TASK_CHANGED` | `NO` |

## Modified and created files

The accepted WS1 implementation commit changed only these files:

- `services/api/src/topicpilot_api/topic_engine/topic_score_formal.py`
  — formal PIT-to-policy derivation bridge, lineage, and non-persistent
  `UNPUBLISHED` envelope.
- `services/api/src/topicpilot_api/topic_engine/__init__.py` — explicit
  exports for the formal bridge.
- `services/api/tests/test_topic_score_formal.py` — nine fail-closed and
  derivation tests.

The present report is a documentation-only closure artifact. It does not
modify the Topic PIT migration, database schema, API route, frontend, provider
registry, scheduler, or any downstream Opportunity/Recommendation surface.

## Source-to-canonical provenance

| Evidence | SHA / state |
| --- | --- |
| Isolated WS1 implementation source commit | `f096aefd94d274dd2c01d17a84fe91f061c64385` |
| Canonical implementation promotion commit | `8777393cbf93328230aede38500d91f1007267d3` |
| Stable patch-id comparison | `635953ccec1c2643f7d12512b3c65f39a0eac180` on both commits |
| Canonical implementation files | Exact three paths listed above |
| Source worktree result | Reconciled to canonical; no WS1 worktree or branch retained |

The canonical implementation commit is in the current canonical branch
history. Its parent is `78b65c0546fb870f7376f1cd72e4e12998c4ef09`.

## Formal Score and Grade semantics

The `UNPUBLISHED` envelope is a publication-state boundary, not an empty
Grade schema placeholder. When formal authority is present, the implementation
executes the existing approved Production V1 Grade business logic and places
the resulting Grade in the envelope. It remains `UNPUBLISHED` because this
task did not add persistence, API publication, provider activation, or UI
publication.

Relevant code paths:

1. `topic_score_formal.py::derive_formal_topic_score` validates formal PIT
   snapshot state, date/session binding, member facts, CORE authority, and the
   approved Leader Set, then calls
   `production_policy.py::evaluate_production_v1`.
2. `production_policy.py::evaluate_production_v1` computes the eligible score
   and uses `grade_for_score` for the Grade result.
3. `production_policy.py::grade_for_score` implements the thresholds:
   `S >= 80.0`, `A >= 65.0`, `B >= 50.0`, and `D` below `50.0`; `None` remains
   `None` for an ineligible/unscored result, and non-finite/out-of-range values
   fail closed.
4. `topic_score_formal.py::FormalTopicScorePublication.as_dict` serializes
   `evaluation.score.grade` while retaining `publicationState=UNPUBLISHED`.

The derivation dependency is the explicit authority bundle:
`PolicyApprovalRecord`, `ProductionV1PolicyBundle`, approved `GovernedLeaderSet`,
CORE member authority, and `ObservationAsOfBinding`. The policy bundle's own
`lifecycle=APPROVED` field is policy approval state, not Topic Lifecycle.

This WS1 code path has no import or call to the Topic Lifecycle engine and does
not establish a Score-to-Lifecycle or Grade-to-Lifecycle dependency. Topic
Lifecycle therefore remains governed by its existing shadow/unpublished
boundary; this report does not infer a dependency in either direction.

## Validation and test-count attribution

Validation was performed against the exact committed WS1 implementation SHA,
with the following evidence:

| Validation | Result |
| --- | --- |
| Focused formal Topic Score tests | `9 passed` |
| Exact parent baseline (`c40a1d4`) backend suite | `460 passed, 41 skipped` |
| Exact WS1 canonical implementation (`8777393`) backend suite | `469 passed, 41 skipped, 1 warning` |
| WS1 test-count delta | `+9 passed; skipped unchanged` |
| Changed-file lint/format checks | `PASS` |
| Exact-commit whitespace/diff check | `PASS` |
| Clean source checkout at implementation commit | `PASS` |
| Declared dependency environment for validation | `PASS for validation; not a release-candidate claim` |

The later owner Stock implementation evidence reported `474 passed, 41
skipped`; the additional five passing tests are attributed to that concurrent
Stock work, not WS1. The subsequent `e4d7754` owner commit is documentation
only and was not counted as a WS1 application test run.

PostgreSQL evidence is recorded explicitly as:

`POSTGRESQL_TESTS=SKIPPED / NOT_RUN — ENVIRONMENT_NOT_PROVIDED`

There were **41 skipped integration tests and zero PostgreSQL PASS claims** in
the cited full-suite result. The missing environment was the required
`TEST_DATABASE_URL`/`DATABASE_URL` (and the historical-ingestion test-specific
database URL where applicable). Skipped or not-run PostgreSQL tests are not
treated as PASS and do not establish database integration or Production
readiness.

## Canonical branch and topology evidence

At report preparation, the exact canonical ref was:

`refs/heads/codex/task-ops-023a-p3c-runtime-sha-audit-20260813`

with HEAD:

`e4d77543f411e8a87310309b2210b8f5d373485e`

The relevant topology is:

```text
78b65c0  docs(research): fail closed Core V0 walk-forward preflight
   |
8777393  feat(topic): add formal score derivation boundary
   |
2ef975d  feat(stock): add fail-closed technical publication foundation
   |
193a9c5  docs(stock): close technical publication foundation
   |
f8c26ca  docs(stock): record canonical technical promotion
   |
e4d7754  docs(stock): record canonical validation   (current canonical HEAD)
```

Thus `8777393...` is an ancestor of `f8c26ca...` and of the current canonical
HEAD; `f8c26ca...` is the immediate parent of `e4d7754...`.

The separate local `main` worktree remains at:

`refs/heads/main -> 32f15f3c57240151bc5d35761e88c764448fa1cc`

Its parent is `47b416fcd71845d91c2ea5577f8f7d2a2b1dab45`. It is not an
ancestor of the current canonical branch. The observed symmetric difference
was `main...canonical = 22 67` (22 commits only on local `main`, 67 only on
the canonical branch), with merge base
`9b97a38bdca3c0c1b12b065a9ad23e47b79e87a2`.

No `main` merge, reset, clean, stash, or conflict resolution was performed for
this closure. Existing owner dirty/untracked state in the canonical worktree
was preserved; the canonical worktree was not presented as a clean release
candidate.

## Closure boundaries and remaining owner decisions

- Topic Score is now a validated, canonicalized, non-persistent derivation
  foundation only.
- Formal Grade business logic exists and is exercised by the foundation, but
  formal Grade publication remains outside this task.
- Topic Lifecycle remains separate and `SHADOW_ONLY / UNPUBLISHED`; no
  dependency direction is asserted by this task.
- No release candidate, remote push, deployment, Production revision, or
  post-deploy verification exists from this task.
- `NEXT_TASK` was read-only and unchanged. Any later Grade/Lifecycle
  publication or release work requires its own Owner-authorized task and
  closure evidence.
