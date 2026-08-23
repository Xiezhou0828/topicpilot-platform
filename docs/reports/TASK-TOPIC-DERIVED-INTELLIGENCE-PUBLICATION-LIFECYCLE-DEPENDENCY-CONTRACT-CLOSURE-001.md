# TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001

## Closure identity and scope

This report closes **WS1 Phase 2 — Topic Derived Intelligence Publication &
Lifecycle Dependency Contract Closure**. It is a contract/dependency/authority
audit and documentation closure only. It does not implement or publish any
derived metric.

| Field | Result |
| --- | --- |
| `TASK_ID` | `TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001` |
| `WORKSTREAM` | `WS1 / Topic Derived Intelligence / Phase 2` |
| `SOURCE_HEAD` | `69b4166130554b9d1410b5f33c105fcf1ac70d67` |
| `SOURCE_BRANCH` | `codex/task-topic-derived-intelligence-phase2-20260816` |
| `SOURCE_WORKTREE` | `C:\Users\acer\Documents\Codex\ws1-p2-topic-derived-intelligence-20260816` |
| `WRITE_SET` | New Phase 2 architecture contract, closure report, machine-readable dependency matrix, and two documentation index links only |
| `FINAL_STATUS` | `COMPLETE_FOR_AUDIT_SCOPE` |
| `CAPABILITY_STATUS` | `CONTRACT_AND_AUTHORITY_AUDIT_CLOSED; DERIVED_PUBLICATION_NOT_IMPLEMENTED` |
| `CANONICAL_STATUS` | `CANONICALIZED` |
| `CANONICAL_RECONCILIATION_DISPOSITION` | `CANONICALIZED_ON_OWNER_BRANCH_WITHOUT_OVERLAP` |
| `CANONICAL_PROMOTION_SOURCE_COMMIT` | `a4b43c4f9bdd6a418de7207eb70c64d59c07283e` |
| `CANONICAL_PROMOTION_COMMIT` | `9d08eb8bb3ffdf46cfcccf17062e0fff58d56a26` |
| `RELEASE_STATUS` | `NOT_RELEASE_CANDIDATE` |
| `PRODUCTION_VERIFICATION` | `NOT_PERFORMED` |
| `PUSH_REMOTE` | `NO` |
| `DEPLOY` | `NO` |
| `PRODUCTION_MUTATION` | `NO` |
| `SCHEDULER_ACTIVATION` | `NO` |
| `NEXT_TASK_CHANGED` | `NO` |

The companion authority contract is
[`TOPIC_DERIVED_INTELLIGENCE_PUBLICATION_AND_LIFECYCLE_DEPENDENCY_CONTRACT.md`](../architecture/TOPIC_DERIVED_INTELLIGENCE_PUBLICATION_AND_LIFECYCLE_DEPENDENCY_CONTRACT.md).
The machine-readable matrix is
[`dependency-matrix.json`](TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001/dependency-matrix.json).

## Source authority and provenance

The audit used only committed canonical evidence at `SOURCE_HEAD` plus direct
inspection of the committed implementation, ORM, migrations, API serializers,
and frontend consumer code. The owner canonical checkout was separately
recorded as dirty/untracked and was not overwritten.

| Source | Role in the chain |
| --- | --- |
| `docs/reports/TASK-TOPIC-SCORE-FORMAL-DERIVATION-FOUNDATION-001.md` | Accepted/canonicalized Phase 1 foundation; deterministic Score/Grade derivation remains `UNPUBLISHED`. |
| `docs/reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md` | Accepted formal PIT migration/materialization boundary, dates, finality, lineage, and supersession evidence. |
| `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` | Committed product-surface authority for Score/Grade/Recommendation separation; Lifecycle independence is confirmed by the committed Lifecycle spec and implementation. |
| `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md` | Frozen Lifecycle meaning; provisional backend policy values and absent approved role semantics. |
| `services/api/src/topicpilot_api/topic_engine/topic_score_formal.py` | Fail-closed Phase 1 authority/lineage implementation. |
| `services/api/src/topicpilot_api/topic_engine/runtime_readiness.py` and `production_policy.py` | Explicit supplied policy/CORE/Leader Set/as-of contract; no defaults or authority creation. |
| `services/api/src/topicpilot_api/topic_lifecycle_engine.py` and `orm/lifecycle.py` | Actual Lifecycle inputs, provisional state machine, SHADOW persistence, and missing upstream lineage binding. |
| `services/api/src/topicpilot_api/topic_daily_state.py`, `orm/snapshots.py`, and migration `0030` | Formal PIT fields and immutable correction/supersession semantics. |
| `services/api/src/topicpilot_api/production_read_model.py`, `topic_snapshot_api.py`, and `topic_intelligence_api.py` | Formal consumer filter, nullable derived fields, and fail-closed unpublished intelligence API. |
| `apps/web/app/lib/topic-api.ts` and `apps/web/app/components/v2/TopicListPage.tsx` | Consumer-only boundary, publication disclosure, and preview isolation. |

The committed repository contains the `GovernedLeaderSet` input type and tests
that construct synthetic explicit inputs, but no approved Leader Set artifact
or approved formal Leader Set consumer authority. This distinction is the
source of the Leader Set bounded blockers below.

## Six audit dimensions

### 1. Score/Grade Publication Authority

**Finding:** Phase 1 already proves deterministic Score/Grade derivation from an
exact formal PIT snapshot. The minimum formal publication authority is the PIT
snapshot/member-fact bundle, approved policy/candidate/algorithm and Grade
references, explicit CORE authority, approved Leader Set version/artifact and
effective date, exact observation-as-of binding, complete lineage, and a
backend-owned publication state/correction contract.

The current evidence does not prove that Score/Grade persistence is required.
An on-read deterministic formal derivation is sufficient for an initial
publication design if the response resolves exact non-superseded upstream state
and carries all lineage. Materialized derived state remains an admissible future
design if performance, historical replay, stable downstream identity, or fan-out
evidence requires it. Neither path is implemented or authorized here.

**Disposition:** `BLOCKED_BY_LEADER_SET_AUTHORITY_AND_SCORE_PUBLICATION_CONTRACT`.

### 2. Derived Metrics Dependency Matrix

The matrix is capability-level, not global. Score/Grade inherit the explicit
Phase 1 Leader Set requirement. Ranking, Breadth, and Concentration do not
automatically depend on Score or Grade, but their formal definitions are not
authorized. Leadership requires an approved Leader Set/role authority. Lifecycle
is independent of Score/Grade and remains blocked only by its own transition,
formal-input, and correction-authority gaps.

The exact machine-readable rows are in the companion JSON. The central human
readable matrix is Section 5 of the architecture contract.

### 3. Lifecycle Dependency / Transition Authority

**Actual inputs:** current `TopicLifecycleEngine.run_once` reads TopicSnapshot rows for a
date, accepted canonical DAILY_BAR price evidence, LiveTrackingUniverse ids,
effective-dated instrument-topic relations and optional role metadata, previous
SHADOW state for the policy version, and the provisional `LifecyclePolicy`.

**No Score/Grade dependency:** the code does not import or consume the Phase 1
Score/Grade derivation for stage selection. It computes its own provisional
positive/strong breadth, weak ratio, average change, and leadership evidence.

**Bounded implementation gap:** `_date_rows` filters only by date rather than
the formal `FORMAL + PUBLISHED + non-superseded` filter. The post-close path
writes the research/current-mapping snapshot and then calls Lifecycle. The
runner's actual boundary is therefore not sufficient for formal Lifecycle
publication, even though the documented intent says it reads formal snapshots.

**Transition authority:** the code contains confirmation days, adjacent-stage
guardrails, strong jump/decline paths, and threshold values, but the canonical
Lifecycle contract labels the policy `PROVISIONAL/TUNABLE`. No approved PM
threshold/multi-day persistence/hysteresis/minimum-duration policy or approved
formal role/Leader Set semantics was found.

**Disposition:** `BLOCKED_BY_TRANSITION_POLICY_AND_FORMAL_UPSTREAM_LINEAGE_AUTHORITY`;
state remains `SHADOW_ONLY / UNPUBLISHED`. This does not block Score/Grade or
Topic Map work that has its own complete authority.

### 4. Frontend Publication Boundary

Topic Overview/Market Map consume the backend. Formal Score/Grade fields are
rendered only when supplied by the API; null fields remain unavailable. The
frontend preview adapter may provide labelled synthetic Preview content only on
the preview source path and never replaces a reachable formal API value.

| Lane | Disposition |
| --- | --- |
| Formal Score | `READY_AFTER_SCORE_PUBLICATION`; `UNAVAILABLE` until backend field is published; browser derivation prohibited. |
| Formal Grade lanes | `READY_AFTER_GRADE_PUBLICATION`; `UNAVAILABLE` until backend field is published; browser derivation prohibited. |
| Formal direction/coverage/participation fields | `READY_AFTER_BACKEND_PUBLICATION` for fields returned by the formal read model; no new browser metric. |
| Formal Lifecycle/derived lanes | `UNAVAILABLE`; `READY_AFTER_LIFECYCLE_FORMAL_PUBLICATION`; browser derivation prohibited. |
| Preview-only data | `PREVIEW` only under the explicit preview source boundary; not formal evidence. |

No UI or API source file was changed.

### 5. Current vs Historical Authority Boundary

Formal current state means the latest formal, published, non-superseded PIT row
available from the backend. It does not mean current mapping reconstruction.
Formal historical state is authorized only on bounded PIT dates at or after
`2026-08-07`; the committed PIT closure evidence names
`2026-08-07` and `2026-08-10`–`2026-08-13`.

Historical Score, Grade, Ranking, and Lifecycle are not formal on any date in
the current closure because their derived publication/definition authorities
are open. Dates before `2026-08-07` are explicitly
`NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY`. A current relation map or OHLCV
history must not be used to backfill historical Topic state.

### 6. Correction / Supersession Propagation

Upstream PIT corrections create a new immutable snapshot identity and explicit
supersession. Phase 1's on-read envelope already binds exact upstream snapshot
and lineage fields, but it is `UNPUBLISHED`. Every future derived publication
must reject the old current snapshot and either re-derive on read from the
successor or create an explicitly superseding materialized derived result.

The current Lifecycle result identity is only `(topic_id, evaluation_date,
policy_version, evaluation_mode)` and stores `snapshot_date`, not the exact
upstream snapshot id/identity, lineage hash, member-fact hashes, or correction
sequence. A retry with the same key can leave the old result intact. This is
adequate for its documented SHADOW fixture behavior but not a formal correction
propagation contract.

**Disposition:** Score/Grade correction semantics are pending publication
contract; Breadth/Leadership/Concentration/Ranking lack definitions; Lifecycle
is blocked by exact upstream lineage and correction authority. This finding does
not itself mandate materialization for Score/Grade.

## Capability disposition matrix

| Capability | PIT | Score | Grade | Leader Set | Definition Authority | Other Authority | Ready / disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Score Publication | Required | — | — | Required | Policy/algorithm/publication contract missing | CORE, as-of, lineage, correction | `BLOCKED_BY_LEADER_SET_AUTHORITY_AND_SCORE_PUBLICATION_CONTRACT` |
| Grade Publication | Required | Required | — | Inherited | Existing Grade logic; publication contract missing | Score lineage/correction | `BLOCKED_BY_SCORE_PUBLICATION_AND_LEADER_SET_AUTHORITY` |
| Ranking | Required | Independent | Independent | Independent | Universe/order/tie-break/as-of missing | Replay/correction | `BLOCKED_BY_RANKING_DEFINITION_AUTHORITY` |
| Breadth | Required | Independent | Independent | Independent | Definition/denominator missing | Member state and null policy | `BLOCKED_BY_BREADTH_DEFINITION_AUTHORITY` |
| Leadership | Required | Independent | Independent | Required | Formal role/Leader Set missing | Weights/effective dates/correction | `BLOCKED_BY_LEADER_SET_AUTHORITY` |
| Concentration | Required | Independent | Independent | Independent | Contribution/weight definition missing | Small sample/null policy | `BLOCKED_BY_CONCENTRATION_DEFINITION_AUTHORITY` |
| Lifecycle | Required for formal input | Independent | Independent | Proxy only in SHADOW; no formal dependency established | Transition policy provisional | Prior state, price evidence, exact snapshot lineage | `BLOCKED_BY_TRANSITION_POLICY_AND_FORMAL_UPSTREAM_LINEAGE_AUTHORITY` |
| Topic Map Score lane | Required | Required | Independent | Inherited from Score policy | Score publication contract | Backend field availability | `READY_AFTER_SCORE_PUBLICATION` |
| Topic Map Grade lanes | Required | Required | Required | Inherited from Score policy | Grade publication contract | Backend field availability | `READY_AFTER_GRADE_PUBLICATION` |
| Topic Map derived/Lifecycle lane | Required | Display-only separate | Display-only separate | Only if a formal lane consumes it | Lifecycle publication contract | Backend read model | `READY_AFTER_LIFECYCLE_FORMAL_PUBLICATION_AND_SCORE_DISPLAY_AUTHORITY` |
| Historical Topic Score | Bounded dates only | Required | Independent | Required by current policy | Score publication | No pre-boundary history | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_SCORE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Grade | Bounded dates only | Required | Required | Inherited | Grade publication | No pre-boundary history | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_GRADE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Ranking | Bounded dates only | Independent | Independent | Independent | Ranking definition | Walk-forward/correction | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_RANKING_DEFINITION_AUTHORITY_AFTER_BOUNDARY` |
| Historical Topic Lifecycle | Bounded dates only | Independent | Independent | Formal role gap remains | Transition/lineage policy | Prior-state chain/correction | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_TRANSITION_POLICY_AND_FORMAL_UPSTREAM_LINEAGE_AUTHORITY_AFTER_BOUNDARY` |

## Validation and preserved evidence

This is a contract/docs-only task. The following were performed or explicitly
preserved:

| Check / gate | Result | Reason |
| --- | --- | --- |
| Exact source HEAD and worktree isolation | `PASS` | Task worktree was created from `69b4166130554b9d1410b5f33c105fcf1ac70d67`; owner checkout was not used for edits. |
| Contract/report/matrix path review | `PASS` | New paths are explicit and linked from the architecture/index owners. |
| Docs link/path consistency | `PASS` | Referenced repository paths and added README/index links were checked against the task worktree. |
| Markdown/JSON syntax | `PASS` | Added Markdown files were read as text and the dependency matrix parsed as JSON. |
| `git diff --check` | `PASS` | No whitespace errors were found in the explicit task write-set. |
| Relevant static/focused application tests | `NOT_RUN_BY_SCOPE` | No application code, schema, API, or frontend changed. Existing Phase 1/Lifecycle evidence is preserved by exact source references. |
| PostgreSQL / migration / DB integration | `NOT_RUN` | No DB or migration write set; not rerun and not a PASS claim. |
| G1 / G2 / G3 / Post-Close Canary | `PRESERVED / NOT_RERUN` | Contract/docs-only change does not reach provider, reference, market-semantics, persistence, or live-runtime boundaries. |
| Production/deploy/scheduler | `NOT_RUN` | Explicitly prohibited by scope. |
| Secret-safe scan | `PASS` | No high-risk credential/key literal patterns were found in the explicit task write-set. |

The checks above are docs-only impact validation. Application, database,
protected-gate, and Production checks remain explicitly not run or preserved
below because this task has no runtime/schema/Production write-set.

## SDLC, canonicalization, and cleanup

The result was validated in the isolated task worktree and promoted by
commit-preserving cherry-pick without write-set overlap. The governed lifecycle
markers are:

```text
IMPLEMENTED=YES (task-owned documentation exists)
VALIDATED=YES (docs/link/JSON/whitespace/secret-scan checks PASS)
CANONICAL_STATUS=CANONICALIZED
CANONICAL_PROMOTION_COMMIT=9d08eb8bb3ffdf46cfcccf17062e0fff58d56a26
RELEASE_STATUS=NOT_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_PERFORMED
PUSH_REMOTE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

Promotion used the task commit and explicit paths. The canonical owner had no
overlapping dirty/untracked path, so `OWNER_DECISION_REQUIRED` was not needed.
The final handoff records the exact source commit, canonical promotion commit,
and final canonical HEAD. No local `main`/canonical convergence or existing
parallel worktree conflict is solved by this task.

After accepted promotion and evidence capture, only the task-owned worktree and
branch may be removed. `tp-b`, `ws2-2a-20260816`, and all other active
worktrees/branches remain untouched.
