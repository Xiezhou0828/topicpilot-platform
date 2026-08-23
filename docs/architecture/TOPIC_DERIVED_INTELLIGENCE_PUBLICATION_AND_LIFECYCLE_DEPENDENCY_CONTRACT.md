# Topic Derived Intelligence Publication and Lifecycle Dependency Contract

**Status:** `COMMITTED AUDIT CONTRACT / IMPLEMENTATION-NEUTRAL`

**Scope:** WS1 Phase 2 — Topic Derived Intelligence Publication & Lifecycle Dependency Contract Closure
**Effective boundary:** exact committed source tree at
`69b4166130554b9d1410b5f33c105fcf1ac70d67`
**Authority type:** derived-intelligence publication, dependency, authority,
and consumer-boundary audit. This document does not approve a new formula,
threshold, Leader Set, ranking policy, persistence design, API, frontend, or
Lifecycle activation.

## 1. Purpose and non-goals

This contract closes the Phase 2 audit boundary between the canonical Topic PIT
daily state and downstream Topic derived intelligence. It answers which
authority each capability must consume, which capabilities are independent of
Score/Grade, what is formally available for current and historical dates, and
what correction/supersession propagation must preserve.

The contract is documentation-only. It does not authorize or implement:

- migration, persistence, materialization, API publication, or frontend wiring;
- historical backfill, provider/scheduler activation, deploy, Production, or
  database mutation;
- a Leader Set, ranking formula, breadth/concentration/leadership definition,
  Lifecycle threshold, transition policy, or hysteresis policy;
- Opportunity, Recommendation, or any downstream decision policy;
- a change to `NEXT_TASK`.

Unresolved authority gaps are intentionally bounded to the affected
capability. A blocked derived capability does not block the formal PIT daily
state or unrelated downstream work that has its own complete authority.

## 2. Canonical evidence chain

The audit starts from the committed tree, not from chat memory, folder names,
old worktrees, or owner-untracked drafts.

| Authority / evidence | What it establishes | Phase 2 use |
| --- | --- | --- |
| `docs/reports/TASK-TOPIC-SCORE-FORMAL-DERIVATION-FOUNDATION-001.md` | Phase 1 canonicalized the deterministic PIT-to-Score/Grade bridge as a non-persistent `FORMAL / UNPUBLISHED` envelope. It does not publish Score/Grade or establish a Lifecycle dependency. | Score/Grade baseline and explicit dependency boundary. |
| `docs/reports/TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION.md` | Migration `0030` defines formal PIT snapshot/member-fact authority, the `2026-08-07` earliest boundary, immutable correction/supersession fields, and bounded materialization evidence for `2026-08-07`, `2026-08-10`–`2026-08-13`. | PIT, current/historical, and correction authority. |
| `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` | Committed product-surface authority states Topic Score is market strength, Grade is not a recommendation, and Recommendation is downstream; the implementation audit separately verifies Lifecycle independence. | Product semantic separation. |
| `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md` | Lifecycle product meanings are frozen, while backend policy values remain provisional/tunable. The current relation data has no approved leader/core role semantic; the engine uses a labelled proxy. | Lifecycle transition-authority audit. |
| `services/api/src/topicpilot_api/topic_engine/topic_score_formal.py` | Phase 1 requires formal PIT state, policy approval, CORE authority, explicit approved Leader Set, exact as-of binding, and lineage; it rejects non-formal, pre-boundary, or superseded snapshots. | Minimum Score/Grade authority. |
| `services/api/src/topicpilot_api/topic_engine/runtime_readiness.py` and `production_policy.py` | Explicit supplied policy/CORE/Leader Set/as-of contract; no defaults or authority creation. | Leader Set and policy authority audit. |
| `services/api/src/topicpilot_api/topic_lifecycle_engine.py` and `services/api/src/topicpilot_api/orm/lifecycle.py` | Existing Lifecycle is a separate `SHADOW` engine/result table with provisional policy, multi-day confirmation, and evidence groups. | Actual Lifecycle inputs, outputs, and gaps. |
| `services/api/src/topicpilot_api/topic_daily_state.py`, `orm/snapshots.py`, and migration `0030` | Formal PIT fields and immutable correction/supersession semantics. | Upstream state and propagation authority. |
| `services/api/src/topicpilot_api/production_read_model.py` and `topic_snapshot_api.py` | Formal consumer queries select `FORMAL + PUBLISHED + non-superseded` Topic snapshots and expose nullable Score/Grade fields. | Backend publication boundary. |
| `apps/web/app/lib/topic-api.ts` and `apps/web/app/components/v2/TopicListPage.tsx` | Topic Overview/Detail consume backend values, expose publication disclosures, and keep preview data separate; formal browser paths do not derive business metrics. | Frontend lane classification. |

The canonical source checkout was dirty and contained owner-tracked and
owner-untracked work outside this write set. Those files are preserved and are
not authority for this audit unless they are linked above as committed
evidence. In particular, an owner-untracked Leader Set candidate or lifecycle
audit draft cannot satisfy a formal authority gap.

## 3. Accepted baseline facts

### 3.1 Phase 1 Score/Grade boundary

The accepted foundation is:

```text
canonical formal PIT daily state
  -> formal authority validation
  -> Production V1 evaluation
  -> deterministic Score and Grade derivation
  -> lineage-bearing FORMAL / UNPUBLISHED envelope
```

The existing Grade business logic is exercised by the foundation. The
foundation report records the approved Grade thresholds as `S >= 80.0`,
`A >= 65.0`, `B >= 50.0`, and `D < 50.0`; Phase 2 does not redesign or
re-approve that logic. Formal Grade publication is still incomplete.

The envelope binds `snapshot_id`, `snapshot_identity`, PIT membership id/hash,
relation and reference versions, source artifact id/hash, snapshot lineage,
policy/candidate/approval references, Leader Set version/artifact, observation
query/source/input hash, and session code. It is not a persisted read model or
an API publication.

### 3.2 Formal PIT boundary

Migration `0030` and the bounded materialization report establish the following
authority boundary:

- formal PIT membership is effective-dated and uses immutable instrument
  identity, accepted canonical member facts, session/calendar binding, finality,
  lineage, and explicit correction/supersession;
- the formal mapping earliest date is `2026-08-07`; no pre-boundary backfill is
  authorized;
- the reported bounded formal evidence dates are `2026-08-07`,
  `2026-08-10`, `2026-08-11`, `2026-08-12`, and `2026-08-13`;
- formal PIT rows carry `FORMAL / PIT_FORMAL / PUBLISHED / FINAL` semantics,
  while Score, Grade, breadth, leadership, concentration, and ranking remain
  deferred or unavailable in the bounded evidence;
- current-mapping reconstruction is explicitly
  `RESEARCH_ONLY / CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY` and is never a
  historical formal PIT substitute.

### 3.3 Lifecycle boundary

Lifecycle is independent of Score and Grade. The current implementation is a
shadow evaluator with policy version
`topic-lifecycle-policy.provisional.1`, calculation version
`topic-lifecycle-shadow.v1`, and `evaluation_mode=SHADOW`. It may consume a
previous shadow state to calculate confirmation and Day N, but it does not
promote a stage to a formal production semantic.

The presence of Lifecycle code, a result table, or a frontend component does
not establish formal Lifecycle publication. The product meaning is frozen; the
numeric threshold and transition policy remain provisional and require a
separate authority decision.

## 4. Minimum authority for Score/Grade publication

The minimum formal publication contract is the following. Each item is
necessary for a formal result; none is supplied by a browser, a current mapping,
or a missing-value fallback.

| Required authority | Minimum contract | Evidence / current state |
| --- | --- | --- |
| PIT snapshot | Exact `FORMAL + PIT_FORMAL + PUBLISHED + FINAL + non-superseded` snapshot at an authorized date/session, with mapping boundary, membership snapshot id/hash, relation version, reference version, source artifact/hash, and lineage hash. | Implemented by `0030` and consumed fail-closed by Phase 1; bounded dates only. |
| Member facts | Immutable member facts keyed to the exact snapshot and observation date; `OBSERVED`, `NO_TRADE`, and `UNKNOWN` remain distinct; missing values remain null. | Implemented in the formal PIT model; Score publication does not yet persist or expose a derived result. |
| CORE authority | Versioned, explicit CORE membership authority covering the member facts used by the policy. | Required by Phase 1 input contract; no separate repository publication artifact was found in the committed tree. |
| Policy approval | Approved policy/candidate/algorithm identity, effective date, all referenced breadth/leadership/normalization/aggregation/weights/eligibility/Grade/rollback references, and approval digest. | Explicit input contract exists; no provider/API activation is authorized. |
| Leader Set authority | Approved, versioned Leader Set artifact with topic coverage, member identities/weights, effective date, artifact id/hash, and policy-version match. | The implementation accepts an explicit `GovernedLeaderSet`, but no approved Leader Set artifact/consumer authority is present in the committed repository. This is a bounded blocker; Phase 2 does not create one. |
| Observation as-of | Exact query version, source id, trading date, session, latest-approved-session flag, freshness, observation count, input hash, and bound timestamp. | Required and validated by Phase 1; no default or browser inference is allowed. |
| Derived contract | Stable contract version, topic/as-of identity, score/grade/status/eligibility, explainable components, and complete lineage. | Non-persistent `topic-score-formal.v1` envelope exists; formal publication/read contract is not complete. |
| Correction state | The derived identity must reference the exact upstream snapshot identity/id, source lineage, and correction sequence; a superseded upstream snapshot must not remain the current formal derived result. | Upstream PIT correction fields exist; Score/Grade publication propagation is not implemented. |
| Publication boundary | A backend-owned read model/API must distinguish `FORMAL/PUBLISHED`, `UNPUBLISHED`, `SUPERSEDED`, `UNAVAILABLE`, and preview/shadow states without deriving on the client. | Existing read models expose nullable Score/Grade but no formal published Score/Grade rows. |

### 4.1 On-read versus materialized derived state

Persistence is not assumed to be a prerequisite. The two admissible designs
must satisfy the same authority contract:

| Axis | On-read deterministic formal derivation | Materialized formal derived state |
| --- | --- | --- |
| PIT correctness | Reads one exact immutable, non-superseded PIT snapshot and its member facts at request/as-of time. | Stores a derived row/artifact whose source identity is one exact PIT snapshot. |
| Algorithm identity | Response carries policy, candidate, algorithm, Grade, and contract versions. | Row/artifact carries the same versions and a deterministic identity key. |
| Lineage | Response is traceable to snapshot/member/source hashes. | Persisted row/artifact is traceable to snapshot/member/source hashes. |
| Replay | Replays the same upstream snapshot and policy deterministically. | Replays materialized versions and can compare/supersede derived outputs. |
| Correction/supersession | A new read must reject the superseded snapshot and derive from its successor. Historical responses need an explicit as-of/supersession rule. | A successor derived result must be created and the prior derived result explicitly superseded or retained as historical. |
| Performance/downstream use | Suitable when request volume and downstream fan-out are within measured limits. | Suitable when stable cross-request/cross-consumer identity, replay, or fan-out is required. |
| Current evidence | Phase 1 proves this shape as a non-persistent envelope; performance and downstream-consumption evidence is absent. | PIT materialization exists, but no derived Score/Grade materialization is authorized or proven necessary. |

**Phase 2 disposition:** on-read deterministic formal derivation is sufficient
as the minimum authority design for an initial Score/Grade publication; current
canonical evidence does not prove that materialized Score/Grade state is
necessary. Either design must add the missing publication contract, approved
Leader Set authority, exact correction semantics, and a backend-owned read
boundary before publication. A future performance, historical-audit, or
downstream-fan-out decision may choose materialization without changing the
Score formula.

## 5. Derived capability dependency matrix

`Required` means the capability cannot be formally published without that
authority. `Independent` means the capability must not inherit an artificial
dependency merely because the field is displayed near Score/Grade. `Missing`
means data or code existence was found, but the formal definition authority was
not found.

| Capability | PIT | Score | Grade | Leader Set | Definition Authority | Other Authority | Ready / disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Score Publication | Required | — | — | Required by current Production V1 policy | Required; approved policy, algorithm, and Grade/score references | CORE, member facts, as-of binding, lineage, correction, publication contract | `BLOCKED_BY_LEADER_SET_AUTHORITY_AND_SCORE_PUBLICATION_CONTRACT` |
| Grade Publication | Required | Required derived input | — | Inherited from Score policy | Existing Grade business logic is exercised; publication definition is missing | Score lineage, correction, publication state/API | `BLOCKED_BY_SCORE_PUBLICATION_AND_LEADER_SET_AUTHORITY` |
| Ranking | Required for any PIT ranking | Not inherently required | Not inherently required | Not inherently required | Missing approved universe, ordering, tie-break, and as-of definition | Cross-topic completeness, null policy, correction/replay | `BLOCKED_BY_RANKING_DEFINITION_AUTHORITY` |
| Breadth | Required | Independent | Independent | Not inherently required | Missing formal breadth denominator/classification definition; raw counts/coverage are not enough | Member state/eligibility, missing/no-trade semantics, lineage | `BLOCKED_BY_BREADTH_DEFINITION_AUTHORITY` |
| Leadership | Required | Independent | Independent | Required for formal leader semantics | Missing approved role/Leader Set authority; current shadow proxy is not formal leadership | Member contribution/weights, effective dates, correction | `BLOCKED_BY_LEADER_SET_AUTHORITY` |
| Concentration | Required | Independent | Independent | Not inherently required unless approved definition consumes it | Missing formal concentration/contribution/weight definition | Member weights/contributions, null and small-sample policy | `BLOCKED_BY_CONCENTRATION_DEFINITION_AUTHORITY` |
| Lifecycle | Required formal PIT input; current code does not enforce this filter | Independent | Independent | Current shadow code may use role metadata or a max-change proxy; no formal Leader Set dependency is established | Product meaning is frozen, but transition thresholds/persistence/activation authority are provisional | Exact prior state, multi-day history, canonical price evidence, source snapshot lineage, correction policy | `BLOCKED_BY_TRANSITION_POLICY_AND_FORMAL_UPSTREAM_LINEAGE_AUTHORITY` (`SHADOW_ONLY / UNPUBLISHED`) |
| Topic Map Score lane | Required | Required | Not separately required | Inherited only if Score policy requires it | Score publication/read contract | Backend field availability; no browser derivation | `READY_AFTER_SCORE_PUBLICATION` |
| Topic Map Grade lanes (`S/A/B/D`) | Required | Required | Required | Inherited from Score policy | Existing Grade mapping; formal publication contract missing | Backend field availability; no browser derivation | `READY_AFTER_GRADE_PUBLICATION` |
| Topic Map derived/lifecycle lane | Required | Score display is separate; not a Lifecycle input | Grade display is separate; not a Lifecycle input | Formal leadership semantics only if the lane exposes leadership | Lifecycle publication/transition definition | Backend-owned stage/read model; no browser derivation | `READY_AFTER_LIFECYCLE_FORMAL_PUBLICATION_AND_SCORE_DISPLAY_AUTHORITY` |
| Historical Topic Score | Only authorized PIT dates | Required | Not required | Required by current Score policy | Score publication contract | Exact as-of/correction lineage; no pre-boundary reconstruction | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_SCORE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Grade | Only authorized PIT dates | Required | Required | Inherited from Score policy | Grade publication contract | Exact as-of/correction lineage; no pre-boundary reconstruction | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_GRADE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Ranking | Only authorized PIT dates | Not inherently required | Not inherently required | Not inherently required | Missing ranking universe/tie-break/history authority | Walk-forward leakage controls, correction/replay | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_RANKING_DEFINITION_AUTHORITY_AFTER_BOUNDARY` |
| Historical Topic Lifecycle | Only authorized PIT dates | Independent | Independent | Role/leader authority remains a formal semantic gap | Transition policy and exact upstream snapshot binding missing | Prior-state chain, trading-day persistence, correction/supersession | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_TRANSITION_POLICY_AND_FORMAL_UPSTREAM_LINEAGE_AUTHORITY_AFTER_BOUNDARY` |

The matrix deliberately does not declare a global `READY` or `BLOCKED` state.
Each gap blocks only its consumer capability.

## 6. Lifecycle dependency and transition-authority audit

### 6.1 Inputs actually consumed by the current SHADOW runner

The current `TopicLifecycleEngine.run_once` and its pure evaluator consume:

1. `TopicSnapshot` rows for the requested date. The current `_date_rows` query
   filters only `snapshot_date`; it does not enforce the formal consumer filter
   `publication_mode='FORMAL'`, `publication_state='PUBLISHED'`, and
   `superseded_by_snapshot_id IS NULL`.
2. Accepted canonical `PRICE` observations with `DAILY_BAR` semantics, source
   ranking, latest two dates, and accepted-price supersession filtering through
   `read_price_evidence`.
3. `LiveTrackingUniverse` instrument ids, unless an explicit eligible-id
   collection is supplied.
4. Effective-dated `InstrumentTopicRelation` rows and optional
   `relationship_metadata` role values (`topicRole` or `role`). This is not an
   approved Leader Set authority and does not establish historical role
   semantics.
5. Previous `SHADOW` Lifecycle rows for the same policy version, including
   previous stage, stage-entry date, trading-day count, candidate stage, and
   candidate streak.
6. `LifecyclePolicy` values and the calculation version. The code records these
   values in the result but does not turn them into PM approval.

This is an audit of actual consumption, not an authorization of those inputs
for formal publication. The current post-close path first writes the legacy
research/current-mapping Topic snapshot and then invokes the shadow Lifecycle
runner; therefore the runner's unfiltered date query is a formal-boundary gap.

### 6.2 Transition policy evidence

The implementation contains explicit provisional values, including:

- minimum observed members `3` and minimum coverage `60%`;
- strong/weak member changes `+4%` / `-4%`;
- ordinary and decline confirmation of `2` trading days;
- adjacent-stage transition guardrails, strong jump/decline paths, and
  minimum transition confidence `30%`;
- stage-specific positive breadth, strong breadth, weak ratio, average-change,
  and confidence thresholds.

The canonical Lifecycle specification labels these values
`PROVISIONAL/TUNABLE`. No committed evidence approves them as production
transition policy, and no approved formal Leader/Core role authority was found.
The existing code therefore proves a deterministic SHADOW state machine, not a
formal Lifecycle transition contract.

The audit found:

| Question | Result |
| --- | --- |
| Does Lifecycle require Score or Grade? | `NO`; the code and product contract keep the dependency independent. |
| Is an approved ranking formula required by current Lifecycle? | `NO`; ranking is not consumed. |
| Is a formal breadth definition approved for Lifecycle publication? | `NO`; the shadow engine computes provisional positive/strong breadth for its own evidence, but this does not approve the separate Breadth capability. |
| Is a formal Leadership/Leader Set authority approved? | `NO`; the engine records `leaderSemanticAvailable` and uses `maxObservedChange` as a labelled proxy when role metadata is absent. |
| Are thresholds, multi-day persistence, hysteresis, and minimum duration approved? | `NO`; implementation exists, but policy values remain provisional/tunable. |
| Must Lifecycle wait for Topic Map or all derived metrics? | `NO`; it can progress on its own authority path once its formal input, transition, and correction contracts are closed. |

## 7. Current versus historical authority boundary

### 7.1 Current formal state

"Current" means the latest available row returned by a backend formal read
model after filtering to `FORMAL + PUBLISHED + non-superseded`. It does not mean
the latest current mapping reconstructed from today’s relations. The formal
Topic read model may expose identity, date, direction, coverage, constituent
count, and nullable derived fields; a null Score/Grade/Lifecycle remains
unavailable.

The current formal PIT authority is bounded by the materialized dates and
lineage evidence in the PIT closure report. A runtime/database may have no rows
until the separately governed materialization is present; this audit does not
claim a live database state or rerun a database operation.

### 7.2 Historical formal state

Historical formal Topic Score, Grade, Ranking, and Lifecycle are not authorized
for dates before `2026-08-07`. For dates on or after the boundary, only an exact
formal PIT snapshot/member-fact authority with date/session/reference/lineage
evidence may be consumed. The bounded PIT evidence currently names
`2026-08-07` and `2026-08-10`–`2026-08-13`; it does not authorize unlisted dates.

The legacy/current-mapping Topic Snapshot engine is explicitly research-only
and cannot be used to fill historical gaps. Six months of canonical OHLCV
history is not historical Topic state: it cannot supply historical membership,
roles, policy versions, Score/Grade, ranking, or Lifecycle transitions by
itself.

This boundary is a walk-forward protection: a future research task may use only
the PIT rows, member facts, policies, relation versions, and corrections that
were authoritative as of each evaluation date. No current mapping or later
policy may be projected backward.

## 8. Correction and supersession propagation

Migration `0030` makes Topic snapshots immutable by identity and correction
sequence, with explicit `supersedes_snapshot_id`,
`superseded_by_snapshot_id`, `superseded_at`, and reason. Formal readers select
the latest non-superseded formal row. That upstream rule must propagate to every
derived capability.

| Capability | Exact upstream binding required | If the upstream snapshot is superseded | Current audit result |
| --- | --- | --- | --- |
| Score / Grade | Snapshot id/identity, membership id/hash, member-fact hashes, source/lineage hashes, policy/candidate/approval refs, Leader Set version/artifact, as-of/session, and correction sequence. | Reject the old current result; re-derive from the successor. A materialized result must be explicitly superseded; an on-read result must resolve the successor and preserve historical as-of semantics. | Phase 1 envelope carries much of this lineage but remains `UNPUBLISHED`; no formal derived correction writer exists. |
| Breadth | Exact PIT membership/fact set, classification/denominator definition version, and correction sequence. | Recompute or supersede the derived value; never silently retain a value sourced from a superseded set. | Definition authority and propagation contract missing. |
| Leadership | Exact PIT member facts plus approved role/Leader Set artifact/version/effective date and correction sequence. | Recompute or supersede the leader evidence; a max-change proxy cannot become formal leadership. | Leader Set authority missing. |
| Concentration | Exact PIT member contribution/weight authority, definition version, and correction sequence. | Recompute or supersede from the successor contribution set. | Definition authority missing. |
| Ranking | Exact topic universe, as-of policy, Score/Grade inputs if consumed, tie-break/version, and correction sequence for every member. | Re-run the affected universe or supersede the rank set; retaining only a topic/date key is insufficient. | Ranking definition and publication contract missing. |
| Lifecycle | Exact formal Topic Snapshot id/identity/lineage, member-fact/price evidence identities, prior-state identity, policy/calculation version, and correction sequence. | Re-run the affected date and downstream state chain, or create an explicit superseding shadow/formal result according to an approved policy. | Current `TopicLifecycleResult` stores date/policy/mode but not upstream snapshot identity/lineage/correction sequence; formal propagation is blocked. |

This propagation requirement does **not** by itself prove that Score/Grade must
be materialized. On-read derivation can satisfy it if the read contract
resolves exact current/superseded upstream identities and historical semantics.
For Ranking and Lifecycle history, the existing stateful consumers make a
materialized or equivalently versioned state boundary a likely future design
question, but Phase 2 does not choose or implement it.

## 9. Frontend publication boundary

Topic Overview and Market Map are consumers. They cannot create a business
value by calculating from member rows, raw counts, direction, or preview data.

| Consumer lane | Backend authority required | Classification now |
| --- | --- | --- |
| Topic identity, group, date, constituent count, and formal PIT direction/coverage when non-null | Formal Topic read model and PIT snapshot fields | `READY_AFTER_BACKEND_PUBLICATION`; null fields remain unavailable. |
| Topic Map Score value | Published backend Score field with exact lineage | `READY_AFTER_SCORE_PUBLICATION`; `UNAVAILABLE` while null; browser derivation is `PROHIBITED_BROWSER_DERIVATION`. |
| Topic Map `S/A/B/D` Grade lanes | Published backend Grade field; the lane is classification, not a browser-computed rank | `READY_AFTER_GRADE_PUBLICATION`; `UNAVAILABLE` while null; browser derivation is `PROHIBITED_BROWSER_DERIVATION`. |
| Topic Map direction/participation/coverage presentation | Backend-owned formal fields and definitions | `READY_AFTER_BACKEND_PUBLICATION` only for returned formal fields; browser must not turn them into new metrics. |
| Topic Map Lifecycle/derived lane | Formal Lifecycle read model and approved transition authority | `UNAVAILABLE` for formal publication; `READY_AFTER_LIFECYCLE_FORMAL_PUBLICATION`; browser derivation is `PROHIBITED_BROWSER_DERIVATION`. |
| Ranking, leadership, concentration, or heatmap sizing | Separate backend definitions and read models | `UNAVAILABLE`; browser derivation is `PROHIBITED_BROWSER_DERIVATION`. |
| Development-only synthetic Preview | Explicit preview source and badge, only when formal API is not the source | `PREVIEW`; never promoted to formal state and never used to fill a reachable formal API null. |

The current frontend disclosure path is consistent with this boundary: API
responses retain nullable formal Score/Grade/Lifecycle values; preview values
are isolated to the preview source; formal Lifecycle is not inferred from
Score, Grade, direction, news, or constituent percentages.

## 10. Capability-level disposition summary

The canonical machine-readable matrix is
`docs/reports/TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001/dependency-matrix.json`.
The human-readable dispositions are repeated in Section 5 so a cold start does
not require a generated artifact to understand the authority boundary.

The bounded blockers are:

1. no committed approved Leader Set artifact/authority for the Phase 1 policy;
2. no formal Score/Grade publication/read contract or correction writer;
3. no approved Ranking, Breadth, or Concentration definition authority;
4. provisional Lifecycle threshold/transition policy and no approved formal
   role/Leader Set semantics;
5. Lifecycle runner/result lineage is not bound to exact formal upstream
   snapshot identity and supersession state.

None of these blockers authorizes a substitute formula, proxy promotion, browser
calculation, historical reconstruction, API publication, or UI change.

## 11. Governance and state markers

```text
TASK_ID=TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001
WORKSTREAM=WS1 / Topic Derived Intelligence / Phase 2
SCOPE=CONTRACT_DEPENDENCY_AUTHORITY_AUDIT_AND_DOCUMENTATION_CLOSURE
APPLICATION_CODE_CHANGED=NO
SCHEMA_OR_MIGRATION_CHANGED=NO
PERSISTENCE_OR_MATERIALIZATION_IMPLEMENTED=NO
API_PUBLICATION_IMPLEMENTED=NO
FRONTEND_CHANGED=NO
HISTORICAL_BACKFILL=NO
PROVIDER_OR_SCHEDULER_CHANGED=NO
OPPORTUNITY_OR_RECOMMENDATION_CHANGED=NO
NEXT_TASK_CHANGED=NO
PUSH_REMOTE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
```

The closure report owns source-to-canonical provenance, validation results,
preserved/not-rerun gates, and final SDLC state. This contract does not convert
an isolated task commit into `CANONICALIZED`, `RELEASE_CANDIDATE`, or
`PRODUCTION_RELEASED` until the governed promotion evidence says so.
