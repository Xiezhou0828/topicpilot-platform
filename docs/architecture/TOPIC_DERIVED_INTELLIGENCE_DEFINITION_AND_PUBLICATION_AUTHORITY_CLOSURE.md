# Topic Derived Intelligence Definition and Publication Authority Closure

**Status:** `COMMITTED AUTHORITY CONTRACT / D1-D8 SEMANTIC CLOSURE / IMPLEMENTATION-NEUTRAL`

**Scope:** WS1 Phase 2A plus structural-role authority and Score consumer projection closure

**Source HEAD:** `5186b2b086774ef9080bbc8767a937c942fec63e`

**Parent closure:** `TASK-TOPIC-DERIVED-INTELLIGENCE-PUBLICATION-LIFECYCLE-DEPENDENCY-CONTRACT-CLOSURE-001`

This contract closes the authority gaps that can be closed from the committed
repository and routes the remaining product/policy decisions to the Owner. It
does not select Leader Set members, invent a ranking or concentration formula,
approve provisional Lifecycle thresholds, create a policy approval artifact,
publish derived values, or start Phase 2B implementation.

## 1. Cold-start authority and evidence rule

The audit starts from the committed canonical tree at `SOURCE HEAD`. It does
not treat the prompt, prior chat, owner-untracked drafts, stale worktrees, or
folder names as authority.

Authority priority is:

1. committed canonical repository;
2. canonical Phase 1 and Phase 2 contracts/reports;
3. committed implementation, ORM, migrations, and tests;
4. explicitly navigated Owner-approved policy evidence that is itself present
   and reconstructable in the committed tree.

The committed `docs/WORK_ORDERS.md` and `docs/DAILY_PROGRESS.md` record
`PHASE-3.7-003F` as PM Approved and describe the Production V1 mechanics. They
also navigate to `docs/reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md`,
but that target is absent from the committed tree at this source HEAD. The
owner checkout contains an untracked copy; this task preserves it but does not
consume it as canonical evidence. Consequently, the committed status ledger
supports the existence and shape of the approved mechanics, while the formal
approval artifact identity, digest, and Leader Set member artifact remain
unreconstructable and are routed below.

| Committed source | Authority established | Phase 2A use |
| --- | --- | --- |
| `docs/architecture/TOPIC_DERIVED_INTELLIGENCE_PUBLICATION_AND_LIFECYCLE_DEPENDENCY_CONTRACT.md` | Phase 2 dependency boundary, on-read admissibility, historical boundary, correction requirements, and bounded blockers. | Parent contract; no re-audit into a global status. |
| `docs/reports/TASK-TOPIC-SCORE-FORMAL-DERIVATION-FOUNDATION-001.md` | Formal PIT-to-Score/Grade deterministic bridge and non-persistent `FORMAL / UNPUBLISHED` envelope. | Score/Grade implementation baseline. |
| `docs/WORK_ORDERS.md` and `docs/DAILY_PROGRESS.md` | PM status ledger and described Production V1 mechanics; activation remains blocked. | Approved-mechanics status, with missing artifact caveat above. |
| `services/api/src/topicpilot_api/topic_engine/production_policy.py` | Explicit Production V1 input, policy-bundle, CORE eligibility, participation, LeaderDefinition, aggregation, and Grade contracts; no defaults. | Exact consumed shape; not a substitute for approval evidence. |
| `services/api/src/topicpilot_api/topic_engine/policy_approval.py` | Strict `topic-score-pm-approval.v1` approval schema and fail-closed reason codes. | Minimum approval artifact contract. |
| `services/api/src/topicpilot_api/topic_engine/runtime_readiness.py` | Explicit `GovernedLeaderSet`, as-of binding, Eligibility Audit, and activation blockers. | Leader Set and activation authority. |
| `services/api/src/topicpilot_api/orm/models.py` | Effective-dated instrument-topic relation with `relation_type`, `relation_version`, validity interval, and JSON metadata. | Candidate source evidence only; not a formal Leader Set. |
| `services/api/src/topicpilot_api/orm/snapshots.py` and migration `0030` | Formal PIT snapshot/member facts, fact state, hashes, source references, and correction/supersession fields. | PIT, as-of, and correction binding. |
| `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md` | PM-frozen Lifecycle meaning; backend policy values remain provisional/tunable. | Lifecycle authority split. |
| `services/api/src/topicpilot_api/topic_lifecycle_engine.py` and `orm/lifecycle.py` | Current SHADOW evaluator, state machine, persistence identity, and missing exact upstream lineage. | Lifecycle-specific closure and blockers. |
| `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md` and committed frontend consumers | Backend-owned Topic semantics; browser does not derive formal business metrics. | Consumer readiness boundary. |

## 2. Closure principles

- A committed implementation shape is not by itself a committed policy
  approval artifact.
- A relation `role`, `relation_type`, display label, or existing `leaders`
  list is not automatically a formal Leader Set.
- The Phase 2A contract may formalize identity, lineage, state, and dependency
  requirements without choosing members, thresholds, formulas, or ranking
  order.
- Score, Grade, Breadth, Leadership, Ranking, Concentration, and Lifecycle are
  routed independently. A blocker in one lane does not become a global block.
- Lifecycle remains independent of Score and Grade. Its stateful correction
  requirement does not imply Score/Grade materialization.
- No current mapping is historical PIT authority. The formal PIT earliest date
  remains `2026-08-07`, with bounded evidence dates `2026-08-07` and
  `2026-08-10` through `2026-08-13`.

## 3. Lane A - Leader Set and formal Leadership authority

### 3.1 Formal purpose

The committed PM semantic record describes Leadership as support from a
semi-static, slow-changing, versionable Leader Set primarily drawn from CORE
members. Stable Leader identity is separate from today's movement evidence.
It is not a single daily top gainer, market-cap ranking, volume ranking, or
the shadow engine's strongest-observed-member proxy.

The Score consumer and the Leadership consumer need related but not identical
views:

| Consumer | Minimum consumed shape evidenced in code | Additional semantic requirement |
| --- | --- | --- |
| Production V1 Score | `leader_set_version`; unique member IDs; `LeaderDefinition.member_id`; importance in `{0.50, 0.75, 1.00}`; policy-version match. | Approved Leader Set artifact and policy binding. |
| Formal Leadership | Exact member facts and daily movement evidence; stable Leader identity; approved role semantics if role-aware evidence is used. | Approved role/Leader Set authority; proxy is not sufficient. |

The safest authority shape is one versioned governed artifact with
consumer-specific projections: Score consumes member identity and approved
importance; Leadership consumes the approved identity and role semantics plus
daily evidence. This does not authorize the same member list or role mapping
until the Owner approves the artifact.

### 3.2 Minimum formal artifact contract

An approved Leader Set artifact must carry, or point immutably to:

- topic identity;
- instrument/member identity;
- formal role when a Leadership consumer uses role semantics;
- importance/weight when the approved Score policy requires it;
- effective date and applicable as-of/session boundary;
- Leader Set version and lifecycle state;
- source relation/CORE lineage and source artifact references;
- policy approval reference and policy-version compatibility;
- artifact identity and SHA-256 digest;
- supersession/correction sequence and successor/predecessor semantics;
- complete topic coverage or an explicit bounded coverage disposition.

The code contract confirms the need for an explicit `GovernedLeaderSet`,
`artifact_id`, `effective_date`, lifecycle, topic coverage, and policy-version
match. The code does not supply a default or infer members.

### 3.3 Evidence finding and disposition

Committed relation rows provide effective-dated relation identity and optional
JSON metadata. Committed frontend and lifecycle evidence labels representative
or proxy information as non-authoritative. No committed approved Leader Set
artifact, member selection, artifact digest, or formal consumer authority was
found. Therefore:

- the Leader Set contract shape is closed;
- actual member selection is `OWNER_POLICY_DECISION_REQUIRED`;
- formal Leadership remains `BLOCKED_BY_LEADER_SET_AUTHORITY`;
- Score publication remains gated by the explicit Leader Set and policy
  approval artifact required by the current Production V1 input contract.

The following are explicitly prohibited as substitutes: Top N by change, Top N
by Score, highest-weight N without approved selection policy, largest daily
move, current relation order, and `maxObservedChange` from SHADOW Lifecycle.

## 4. Lane B - Score and Grade publication authority

### 4.1 What is closed

The Phase 1 envelope and committed code support an initial formal publication
design without a new derived table:

```text
FORMAL PIT snapshot
  -> exact current non-superseded resolution
  -> deterministic Production V1 derivation
  -> backend-owned formal Score/Grade response
```

The minimum formal response must bind the exact PIT snapshot identity and
snapshot identity string, membership snapshot ID/hash, member-fact hashes,
source artifact IDs/hashes, policy/candidate/algorithm/Grade versions, CORE
authority, approved Leader Set version/artifact, observation as-of/session and
input hash, correction sequence, and publication state.

No committed evidence demonstrates that Score/Grade requires materialization
for the initial publication. Materialization remains a future design trigger
only when performance, fan-out, durable historical identity, or replay/output
retention evidence requires it. Phase 2A adds no migration, table, or
persistence requirement.

### 4.2 Formal publication state contract

| State | Meaning | Formal consumer behavior |
| --- | --- | --- |
| `FORMAL / PUBLISHED` | Backend-owned value derived from an authorized exact PIT snapshot and complete approved policy/authority inputs. | May be returned as formal data with lineage and as-of disclosure. |
| `UNPUBLISHED` | Deterministic derivation or envelope exists, but publication authority is incomplete. | Must not be presented as formal Score/Grade. |
| `UNAVAILABLE` | A required input, authority, or data-quality condition cannot support derivation. | Return null value plus stable unavailable reason; do not infer or substitute. |
| `SUPERSEDED` | A previously materialized/published identity has been replaced by an authorized successor. | Current reads resolve the successor; historical reads retain explicit identity/as-of semantics. |
| `PREVIEW` / `SHADOW` | Non-formal product preview or calibration output. | May render only with explicit source disclosure and must never overwrite formal null/unavailable fields. |

Minimum reason categories use existing fail-closed vocabulary where available:
`PIT_NOT_FORMAL`, `PIT_SUPERSEDED`, `APPROVAL_ARTIFACT_MISSING`,
`POLICY_BUNDLE_MISSING`, `LEADER_SET_MISSING`,
`LEADER_SET_ARTIFACT_MISSING`, `LEADER_SET_VERSION_MISMATCH`,
`OBSERVATION_AS_OF_BINDING_MISSING`, `OBSERVATION_AS_OF_NOT_LATEST_APPROVED`,
`ELIGIBILITY_AUDIT_MISSING`, `DATA_INSUFFICIENT`, and
`PUBLICATION_CONTRACT_UNAVAILABLE`.

### 4.3 Correction and historical behavior

For a current read, an upstream PIT snapshot with a successor must not remain
the current formal source. The reader resolves the current non-superseded
successor and exposes the successor lineage. For an historical/as-of read, the
reader must not silently rewrite a previously authorized as-of response; it
must either return the historical identity with its supersession disclosure or
return `SUPERSEDED`/`UNAVAILABLE` according to the approved historical read
contract.

An old on-read envelope is not a durable formal publication. A materialized
future value would require an explicit successor derived identity and
supersession record. This requirement does not make materialization necessary
for the initial Score/Grade publication design.

### 4.4 Score/Grade disposition

- Score publication contract: `READY_AFTER_LEADER_SET_AND_POLICY_APPROVAL_ARTIFACT`.
- Grade publication contract: `READY_AFTER_SCORE_PUBLICATION`.
- Initial implementation routing: on-read deterministic backend publication;
  no persistence prerequisite is authorized by this task.
- Current formal publication remains unavailable because the committed
  approval artifact and approved Leader Set member artifact are absent.

## 5. Lane C - Breadth definition authority

### 5.1 Semantic boundary that can be closed

Committed PM status records Breadth as Market Participation. The conceptual
population is CORE topic members for the current/static interpretation;
historical expansion/contraction belongs to Lifecycle rather than redefining
the current Breadth metric. Breadth does not inherently consume Score, Grade,
or Leader Set.

The non-activating Production V1 implementation provides evidence for explicit
participation states, CORE coverage eligibility, null-safe observations, and a
versioned policy reference. Its exact values are implementation evidence of the
approved-mechanics status, not a new approval made by this task.

### 5.2 Formal definition requirements

Before formal Breadth publication, the approved policy artifact must identify:

- the exact PIT CORE denominator and member eligibility source;
- treatment of `OBSERVED`, `NO_TRADE`, and `UNKNOWN` member facts;
- positive, negative, neutral, and missing classification semantics;
- the approved policy/version and algorithm identity;
- coverage, small-sample, and null/unavailable behavior;
- as-of, correction, and supersession binding;
- output identity and consumer/read boundary.

The SHADOW Lifecycle engine's provisional `positiveBreadth` or
`strongBreadth` is not formal Breadth authority and cannot close this lane.

Disposition: `BLOCKED_BY_MISSING_COMMITTED_POLICY_APPROVAL_ARTIFACT` with
`OWNER_POLICY_DECISION_REQUIRED` for the artifact/identity reconciliation.
This does not block Score publication contract work, Ranking definition work,
or Topic Map Score lane routing.

## 6. Lane D - Ranking definition authority

No committed Topic-level global ranking semantic was found. Existing
Opportunity ranking is strategy-local/downstream and explicitly does not
define a global Topic ranking or feed back into Topic Score. The product and
frontend contracts require backend-owned ranking semantics but do not select a
Topic ranking metric.

The following remain unresolved and cannot be inferred:

- eligible Topic universe and completeness;
- ranking metric and whether it is Score, another strength metric, or a
  separate approved value;
- direction, tie-break, null/unavailable handling, and comparable-as-of rule;
- correction/replay behavior;
- rank-set identity/version and historical authority.

Disposition: `OWNER_POLICY_DECISION_REQUIRED` and
`BLOCKED_BY_RANKING_DEFINITION_AUTHORITY`. `Ranking = Score descending` is not
authorized by this closure.

## 7. Lane E - Concentration definition authority

No committed Topic concentration product semantic or contribution-weight
authority was found. Effective-dated relation metadata and member facts are
available as source evidence, but they do not choose equal-weight, weighted,
Top-N, HHI, share, denominator, or small-sample behavior.

The formal definition must separately authorize member contribution/weight
source, denominator, missing/null handling, small-sample behavior, PIT/as-of
and correction semantics, versioning, and read/publication identity.

Disposition: `OWNER_POLICY_DECISION_REQUIRED` and
`BLOCKED_BY_CONCENTRATION_DEFINITION_AUTHORITY`. HHI, Top-3, Top-5, or maximum
weight share are not selected.

## 8. Lane F - Lifecycle transition and lineage authority

### 8.1 Formal input and state contract

Formal Lifecycle may consume only an exact `FORMAL + PUBLISHED + FINAL +
non-superseded` PIT authority plus separately approved price evidence, relation
role evidence, and prior Lifecycle state. The current runner's date-only
snapshot query does not enforce this formal filter and the current result
identity is keyed by topic/date/policy/mode without exact upstream snapshot
identity, lineage, or correction sequence.

Formal state must bind:

- prior result identity and prior stage/candidate confirmation state;
- policy and calculation versions;
- evaluation date and market/trading-day chain;
- exact Topic Snapshot identity and correction sequence;
- member-fact and price-evidence identities/hashes;
- relation/reference versions and role authority if consumed;
- correction/supersession outcome for Day T and downstream replay impact.

### 8.2 Transition policy audit

The product meanings of the five Lifecycle stages are PM-frozen. The following
implementation values remain `PROVISIONAL_TUNABLE` under
`topic-lifecycle-policy.provisional.1`: stage breadth boundaries, leader proxy
cutoff, ordinary and decline confirmation days, strong jump/decline rules,
adjacent-stage guardrails, minimum observed/coverage requirements, candidate
streak, and hysteresis/hold behavior. The calibration report confirms that
shadow evidence is reviewable but no PM judgement or activation decision has
been recorded.

Therefore this task closes the distinction between product meaning and
implementation policy but does not approve the numeric transition policy.

### 8.3 Stateful correction requirement

Lifecycle is a multi-day stateful consumer. If Day T PIT is corrected, the
formal contract must either replay Day T and every affected downstream trading
day under a new/versioned state identity or create explicit superseding
versioned results with equivalent historical lineage. The requirement is
Lifecycle-specific; it does not imply Score/Grade persistence.

The current shadow table can preserve policy/calculation identity and same-key
immutability, but it does not bind the exact upstream snapshot identity and
correction sequence. Formal Lifecycle is therefore
`READY_AFTER_OWNER_POLICY_APPROVAL_AND_FORMAL_UPSTREAM_LINEAGE` and remains
`SHADOW_ONLY / UNPUBLISHED`.

### 8.4 Leader/role dependency

Lifecycle does not inherently require Score, Grade, Ranking, or the separate
Leadership capability. However, the current evaluator uses role-aware members
when present and otherwise records a labelled proxy. A formal activation must
either receive an approved role authority for any role-aware transition or
explicitly approve a role-independent transition contract. The proxy itself is
not formal authority.

## 9. Owner decision table

The machine-readable version is linked from the Phase 2A closure report. These
decisions are bounded to missing product/policy authority and do not cover
engineering choices already closed by this contract.

| Decision ID | Capability | Question | Existing evidence | Candidate choices supported by evidence | Architectural consequence | Blocks | Does not block | Recommended default | Owner approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WS1-P2A-D001` | Leader Set | Which approved members, version, effective dates, and source artifact form the governed Leader Set? | PM semantics require a semi-static versionable set primarily from CORE; code requires explicit version/artifact but no default. | Approve an explicit versioned artifact with member identities and policy-required importance; relation-order or daily-move inference is not supported. | Supplies the authority consumed by Score and any formal Leadership projection. | Leader Set, Score publication, Leadership. | Breadth semantic closure, Ranking decision, Concentration decision, Lifecycle product meaning. | Approve the artifact shape first; do not infer members. | YES |
| `WS1-P2A-D002` | Leader Set / Leadership | Should Score and Leadership share one governed artifact? | Score needs member/importance/version; Leadership needs stable identity and approved role semantics. | One base artifact with consumer-specific projections is evidence-compatible; separate artifacts require explicit linkage. | Defines whether consumers share identity and correction/supersession lineage. | Leadership and Score if no binding is chosen. | Breadth, Ranking, Concentration. | Shared identity with explicit consumer projections, subject to Owner approval. | YES |
| `WS1-P2A-D003` | Score / Grade | Where is the committed PM approval artifact and exact digest/identity that activates the already implemented mechanics? | Work order/status ledger says PM Approved; the navigated 003F brief is absent from committed HEAD; `policy_approval.py` requires a strict artifact. | Commit/reconcile the referenced approval artifact and bind its digest; otherwise remain fail-closed. | Enables `ProductionV1PolicyBundle.from_approval` and formal publication prerequisites. | Score and Grade publication. | Breadth semantic, Ranking, Concentration, Lifecycle independence. | Restore the referenced artifact as committed canonical evidence; do not copy owner-untracked content automatically. | YES |
| `WS1-P2A-D004` | Breadth | Which committed policy artifact is the formal identity for CORE Market Participation and its null/coverage rules? | PM-001 freezes meaning/population; code contains non-activating mechanics; exact approval artifact is absent at HEAD. | Reconcile the approved artifact and code references; no new formula choice is supported by this task. | Formal Breadth publication. | Score publication contract and Topic Map Score routing. | Ranking, Concentration, Lifecycle. | Reconcile artifact identity before publishing Breadth. | YES |
| `WS1-P2A-D005` | Ranking | What is the Topic-level global ranking universe and metric? | Opportunity ranking is strategy-local; no global Topic ranking authority is committed. | No candidate metric is supported by current evidence. | Defines rank-set/read model, tie-break, null, replay, and historical contract. | Ranking and Historical Ranking. | Score, Grade, Breadth, Concentration, Lifecycle. | Keep deferred; do not equate ranking with Score descending. | YES |
| `WS1-P2A-D006` | Concentration | What product semantic and contribution/weight definition is formal? | No committed Topic concentration authority; relation metadata alone is insufficient. | No formula choice is supported; HHI/Top-N/max-share remain undecided. | Defines member contribution, denominator, small-sample, and correction contract. | Concentration and Historical Concentration if later added. | Score, Grade, Breadth, Ranking, Lifecycle. | Keep deferred pending product decision. | YES |
| `WS1-P2A-D007` | Lifecycle | Which numeric transition policy version is approved for formal activation? | Five stage meanings are frozen; current numeric values are explicitly provisional/tunable and calibration has blank PM judgement fields. | Approve a new version after PM calibration; do not mutate provisional rows. | Formal Lifecycle transition/activation. | Score/Grade publication, Ranking, Breadth, Concentration. | YES |
| `WS1-P2A-D008` | Lifecycle | Does formal Lifecycle use approved role semantics, and what is the correction/replay state identity? | Current engine has role-aware path plus labelled proxy; result lacks exact PIT snapshot/correction binding. | Approve role-aware input authority or a role-independent transition contract, plus versioned downstream replay/supersession. | Formal Lifecycle and correction propagation. | Score, Grade, Ranking, Breadth, Concentration. | Require explicit lineage either way; never promote proxy. | YES |

## 10. Capability-level routing

| Capability | Disposition | Boundary |
| --- | --- | --- |
| Leader Set authority | `OWNER_POLICY_DECISION_REQUIRED` | Contract shape closed; member artifact/version/effective authority absent. |
| Score publication | `READY_AFTER_LEADER_SET_AND_POLICY_APPROVAL_ARTIFACT` | On-read deterministic backend publication is the admissible minimum; no persistence prerequisite. |
| Grade publication | `READY_AFTER_SCORE_PUBLICATION` | Existing Grade logic is exercised; Grade remains downstream of formal Score output. |
| Breadth | `BLOCKED_BY_MISSING_COMMITTED_POLICY_APPROVAL_ARTIFACT` | Meaning/population boundary closed; formal policy identity and publication authority unresolved. |
| Ranking | `OWNER_POLICY_DECISION_REQUIRED` | No global Topic ranking metric/universe authority. |
| Leadership | `READY_AFTER_LEADER_SET_AUTHORITY` | Formal role/Leader Set artifact required; shadow proxy prohibited. |
| Concentration | `OWNER_POLICY_DECISION_REQUIRED` | No product semantic or contribution/weight definition. |
| Lifecycle | `READY_AFTER_OWNER_POLICY_APPROVAL_AND_FORMAL_UPSTREAM_LINEAGE` | Independent lane; product meaning closed, transition values and exact lineage unresolved; remains SHADOW_ONLY. |
| Topic Map Score lane | `READY_AFTER_SCORE_PUBLICATION` | Consumer-only; browser derivation prohibited. |
| Topic Map Grade lane | `READY_AFTER_GRADE_PUBLICATION` | Consumer-only; browser derivation prohibited. |
| Topic Map Lifecycle/derived lane | `READY_AFTER_LIFECYCLE_FORMAL_PUBLICATION` | Does not wait for Ranking, Breadth, or Concentration; browser derivation prohibited. |
| Historical Topic Score/Grade | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY` plus the current publication blockers after boundary | No pre-boundary reconstruction. |
| Historical Topic Ranking | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; OWNER_POLICY_DECISION_REQUIRED_AFTER_BOUNDARY` | Requires approved universe, as-of, rank identity, and replay. |
| Historical Topic Lifecycle | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; READY_AFTER_OWNER_POLICY_APPROVAL_AND_FORMAL_UPSTREAM_LINEAGE_AFTER_BOUNDARY` | Requires stateful replay/versioning and correction propagation. |

## 11. Historical and frontend boundaries

The formal PIT earliest date remains `2026-08-07`; bounded formal evidence dates
remain `2026-08-07`, `2026-08-10`, `2026-08-11`, `2026-08-12`, and
`2026-08-13`. Current mapping reconstruction remains `RESEARCH_ONLY` and cannot
be used as historical Topic state. The 63,826 canonical OHLCV rows are not
historical Topic/System State.

Topic Overview and Market Map remain consumer-only. Browser code must not
calculate Score, assign Grade, calculate Ranking/Breadth/Concentration, infer
Leadership, or infer Lifecycle. Formal null/unavailable values must not be
overwritten by Preview. Formal lanes are `READY_AFTER_*` only after backend
publication; unavailable lanes remain explicit and browser derivation is
`PROHIBITED_BROWSER_DERIVATION`.

## 12. Implementation, release, and governance boundary

This Phase 2A closure authorizes no migration, persistence implementation, API
implementation, frontend wiring, Lifecycle activation, historical backfill,
provider/scheduler activation, Opportunity/Recommendation change, Production
mutation, deployment, push, main/canonical convergence, or `NEXT_TASK` change.

`READY_AFTER_*` is routing evidence for a future separately authorized task;
this task does not start it. Application/DB/Production gates are not rerun for
this docs/policy-only write set. G1/G2/G3/Canary remain preserved/not rerun and
Production remains not run.

```text
IMPLEMENTED=YES (authority closure artifacts exist)
VALIDATED=YES (docs/link/JSON/cross-check/whitespace/secret-scan checks PASS)
CANONICAL_STATUS=CANONICALIZED_PREDECESSOR_CLOSURE
CANONICAL_PROMOTION_COMMIT=2196956affe936b26e666484967b5039251d579c
RELEASE_STATUS=NOT_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_PERFORMED
PUSH_REMOTE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

## Addendum A - Owner-approved structural role semantics and authority boundary

This addendum is the normative structural-role and Score-projection extension
for `TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001`.
It records the Owner-approved D1-D8 product semantic decisions as closed. Any
earlier `OWNER_POLICY_DECISION_REQUIRED` wording about the *meaning* of
Representative, Core, Related, or Dynamic Leadership is superseded by this
addendum. Remaining blockers are authority artifacts, implementation/read
model gaps, exact consumer projection, or unresolved downstream definitions;
they are not permission to reopen those meanings.

### A.1 Structural role policy

| Contract item | Closed value |
| --- | --- |
| Structural role model | `REPRESENTATIVE`, `CORE`, `RELATED` |
| Classification mode | `SEMI_MANUAL_GOVERNED` - evidence collection, AI-assisted proposal, human/Owner review, approved role, effective-dated/versioned authority |
| Frequency | `LOW_FREQUENCY`; not a daily market reassignment |
| Automatic hard selector | `NOT_AUTHORIZED` - no Top-N, threshold, market-cap, revenue, return, volume, or contribution selector is created here |
| Role authority | Owner-governed structural metadata, not a frontend label or a daily dynamic leader result |
| Representative | High topic representativeness; not a daily leader and not a universal market-cap/revenue threshold |
| Core | Important business/market positioning and high topic-market linkage; its meaning does not depend on Score being available |
| Related | Supported business/market linkage that is not the main positioning/core identity; it may still be a dynamic market leader in a separate namespace |

The classification lifecycle is explicitly:

```text
evidence collection
  -> AI-assisted proposal
  -> human/Owner review
  -> approved structural role
  -> effective-dated, versioned authority
```

This task does not implement any classifier, proposal pipeline, approval UI,
or canonical write path.

### A.2 Structural and dynamic namespaces remain separate

The structural namespace (`REPRESENTATIVE`, `CORE`, `RELATED`) and the dynamic
market namespace (`LEADER`, `LEADERSHIP`, `FOLLOWER`, `CONFIRMING`, `LAGGARD`,
`CATCH-UP`, `WEAKENING`, `ROTATION`) are different authorities and may coexist.
The following combinations are valid examples, not universal mappings:

| Structural role | Dynamic market state | Contract result |
| --- | --- | --- |
| `REPRESENTATIVE` | `CONFIRMING` | Allowed |
| `CORE` | `LEADER` | Allowed |
| `RELATED` | `CATCH-UP` or `LEADER` | Allowed |

The contract therefore does **not** establish `REPRESENTATIVE = LEADER`,
`CORE = LEADER`, or `LEADER subset-of CORE`. Formal Dynamic Leadership remains
an evidence capability and no formula, Top-N rule, or daily dynamic assignment
is created by this task.

### A.3 Existing Score adapter constraint

The existing formal Production V1 adapter constraint
`GovernedLeaderSet subset-of CORE` remains valid only as a Score-consumer
eligibility requirement. It is not a universal product rule and must not be
used to infer structural roles or dynamic Leadership. If the existing name is
retained, the contract meaning is **Score-governed structural input**, not
"today's dynamic leaders".

Lifecycle may consume formally published structural metadata in a future
contract, but it cannot create structural roles, infer authority from browser
labels, or write roles automatically. Current Lifecycle remains shadow and
fail-closed until its own transition and upstream-lineage authority is closed.

## Addendum B - Structural Role Authority contract

### B.1 Logical authority identity

The canonical logical authority is one approved, versioned structural-role
record per topic/instrument/effective interval. The minimum identity and
lineage contract is:

| Field | Required semantic |
| --- | --- |
| `authority_id` | Stable identity of the approved structural-role authority record or immutable authority artifact |
| `topic_id` | Canonical Topic identity; never a display slug alone |
| `instrument_id` | Canonical instrument/stock identity; never a display name alone |
| `structural_role` | Exactly one of `REPRESENTATIVE`, `CORE`, `RELATED` |
| `effective_from` / `effective_to` | Half-open or explicitly documented effective interval; an as-of read must resolve the interval at the requested date |
| `authority_version` | Version of the structural-role policy/authority namespace |
| `approval_state` | Explicit governed state; only `APPROVED` is consumable by formal projections; proposed/draft rows are not authority |
| `source_artifact_id` / `source_artifact_hash` | Immutable evidence/provenance identity for the approved classification |
| `reviewer_or_approval_ref` | Owner/human approval provenance; AI proposal identity alone is insufficient |
| `correction_sequence` | Monotonic correction identity for append-only correction/supersession semantics |
| `supersedes_authority_id` / `superseded_by_authority_id` | Explicit correction relationship; a correction does not mutate the old authority row |
| `lineage_hash` | Deterministic binding of identity, role, interval, version, provenance, approval, and correction state |

The read contract is as-of and fail-closed: select only an approved record
whose effective interval contains the requested date, resolve a single
applicable version, and return no structural role when authority is missing,
ambiguous, or superseded. Historical reads preserve the authority that was
effective at that date; current reads do not rewrite historical roles.

### B.2 Existing repository carrier and exact gap

The best existing canonical carrier is `InstrumentTopicRelation` in
`services/api/src/topicpilot_api/orm/models.py`. It already provides canonical
topic/instrument identity, `relation_type`, `relation_version`, `valid_from`,
`valid_to`, and `relationship_metadata`. It is reusable as the identity and
effective-date carrier, so a parallel manual role table is not authorized by
this closure.

The committed carrier is not yet a formal Structural Role Authority because it
does not enforce or independently expose all of the following: the constrained
three-value structural-role namespace, explicit approval state, immutable
source artifact identity/hash and reviewer reference, correction/supersession
identity, or a canonical approved as-of projection/read resolver. Existing
metadata such as `topicRole`/`role` is evidence of a shadow consumer path, not
formal role authority.

Therefore:

```text
STRUCTURAL_ROLE_AUTHORITY_CONTRACT = CLOSED
STRUCTURAL_ROLE_AUTHORITY_REPOSITORY_ARTIFACT = NOT_FOUND
STRUCTURAL_ROLE_AUTHORITY_IMPLEMENTATION = NOT_READY
STRUCTURAL_ROLE_AUTHORITY_DISPOSITION = READY_AFTER_APPROVED_ROLE_READ_MODEL
```

No schema, migration, ORM, import, admin, or API change is included here.

### B.3 Correction and supersession propagation

If an approved structural-role record is corrected, the successor authority
must supersede the old record by identity and correction sequence. Consumers
must bind their derived value to the exact structural authority id/version,
effective date, provenance hash, and correction state. A superseded role must
not remain the current CORE projection or current Score consumer input.

The propagation boundary is:

```text
PIT snapshot/member facts
  + approved structural-role authority
    -> CORE population projection
    -> Score consumer projection / GovernedLeaderSet compatibility input
    -> Score / Grade or other separately authorized consumer
```

Each downstream result must re-derive or explicitly supersede when either the
PIT snapshot or structural-role authority changes. This requirement does not
by itself require materialization; exact on-read resolution is acceptable when
the read model preserves the same identity and historical semantics.

## Addendum C - Structural Role Authority to Score projection

### C.1 CORE projection

The only deterministic structural-role projection closed by this contract is:

```text
approved + effective Structural Role Authority
  where structural_role = CORE
  -> core_member_ids
  -> core_authority_id = authority artifact/version/as-of identity
```

`REPRESENTATIVE` is not automatically included in CORE. `RELATED` is not
automatically included in CORE. No role is promoted because it improves Score,
has a higher return, or appears as a dynamic leader. A formal Score consumer
may use the CORE projection only after the approved role read model and its
exact as-of identity exist.

`CORE_AUTHORITY_DISPOSITION=READY_AFTER_APPROVED_STRUCTURAL_ROLE_READ_MODEL`.

### C.2 GovernedLeaderSet disposition

The required disposition is:

```text
GOVERNED_LEADER_SET_DISPOSITION=COMPATIBILITY_ADAPTER_OVER_STRUCTURAL_ROLE_AUTHORITY
GOVERNED_LEADER_SET_EXACT_PROJECTION=OWNER_DECISION_REQUIRED_FOR_EXACT_SCORE_PROJECTION
GOVERNED_LEADER_SET_PROJECTION_READY=NO
DUPLICATED_MANUAL_ROLE_AUTHORITY_REQUIRED=NO
```

This is a bounded compatibility result, not a deterministic role shortcut.
The existing formal Score input requires per-topic member identity and
importance, a version, artifact identity, approval state, effective date, and
the invariant `leaders subset-of core_member_ids`. D1-D8 intentionally do not
say whether the Score projection is Representative-only, Representative plus
Core, all Core, or another approved subset; they also do not define how the
existing importance values are projected from structural roles. The repository
contains no approved projection artifact or rule that resolves that choice.

Accordingly, the existing `GovernedLeaderSet` shape may remain as a
consumer-facing compatibility artifact **linked to** the Structural Role
Authority. It must not become a second, manually maintained structural-role
authority. A future implementation may produce it deterministically only after
an Owner-approved projection rule/consumer profile supplies the exact member
set and importance semantics. Until then, fail closed; do not infer from
relation order, Score, daily movement, Top-N, volume, market cap, or frontend
labels.

### C.3 Score and Grade readiness flags

| Flag | Value | Exact explanation |
| --- | --- | --- |
| `SCORE_OWNER_SEMANTIC_GAP_CLOSED` | `YES` | D1-D8 close the structural/dynamic role semantic gap; they do not close implementation authority or Score projection gaps. |
| `GRADE_OWNER_SEMANTIC_GAP_CLOSED` | `YES` | Grade remains the existing downstream Score classification; no new Grade role meaning is required. |
| `SCORE_STRUCTURAL_ROLE_AUTHORITY_READY` | `NO` | No committed approved structural-role artifact/read model with approval, provenance, correction, and as-of semantics exists. |
| `SCORE_GOVERNED_INPUT_PROJECTION_READY` | `NO` | Exact Score member/importance projection is not uniquely authorized by D1-D8 or the committed repository. |
| `SCORE_READY_FOR_IMPLEMENTATION` | `NO` | Blocked by the structural-role read-model gap, exact Score projection decision, and the existing policy-approval/publication prerequisites. |
| `GRADE_READY_FOR_IMPLEMENTATION` | `NO` | Blocked by Score publication readiness; no additional Grade semantic blocker was introduced. |
| `WS1_SCORE_GRADE_IMPLEMENTATION_CAN_BE_OWNER_AUTHORIZED` | `NO` | The required Score and Grade readiness flags are not both `YES`. |

## Addendum D - On-read versus materialized derived state

The current evidence supports **on-read deterministic formal derivation as the
minimum admissible publication design**:

| Dimension | On-read deterministic formal derivation | Materialized derived state |
| --- | --- | --- |
| Immutable PIT | Resolves exact approved, non-superseded PIT identity at read time | Stores exact PIT identity in an immutable/versioned result |
| Algorithm/version | Carries policy, candidate, algorithm, Grade, role-authority, and projection versions in lineage | Stores the same versions in an immutable result identity |
| Correction/supersession | Resolves successor authority and rejects superseded current input | Supersedes/re-derives affected derived rows explicitly |
| Historical replay | Permitted only for formally bounded PIT dates and exact as-of authorities | Permitted with immutable derived history tied to those same inputs |
| Performance/downstream consumption | No canonical evidence currently proves a materialized Score/Grade result is required | Becomes justified only by a separately evidenced performance, stateful consumer, audit, or replay requirement |
| Current disposition | `ADMISSIBLE_MINIMUM; NOT_IMPLEMENTED` | `NOT_REQUIRED_BY_CURRENT_EVIDENCE; FUTURE_TRIGGER_ONLY` |

The existing Phase 1 envelope proves deterministic non-persistent derivation,
not formal publication. Formal publication still needs the approved role
authority/projection, the strict PM policy approval artifact required by the
runtime (the referenced 003F artifact is not present in this committed tree),
and a backend-owned publication/read contract. This closure neither chooses a
database persistence design nor authorizes an API writer.

## Addendum E - Updated capability and frontend disposition

The following matrix is the post-D1-D8 routing authority for this closure. A
bounded blocker blocks only the named capability.

| Capability | PIT | Score | Grade | Leader Set | Definition Authority | Other Authority | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Score Publication | Required exact formal snapshot/member facts | - | - | Required through the compatibility adapter | Score policy/algorithm/approval plus structural-role projection | CORE authority, as-of, lineage, correction, backend publication | `READY_AFTER_STRUCTURAL_ROLE_AUTHORITY_AND_EXACT_SCORE_PROJECTION` |
| Grade Publication | Required | Required derived input | - | Inherited from Score | Existing Grade business logic; publication state still needed | Score lineage/correction/backend read contract | `READY_AFTER_SCORE_PUBLICATION` |
| Ranking | Required for any formal ranking | Not inherently required | Not inherently required | Not inherently required | Global Topic ranking definition, universe, tie-break, null/as-of/replay | Cross-topic completeness | `BLOCKED_BY_RANKING_DEFINITION_AUTHORITY` |
| Breadth | Required | Independent | Independent | Not inherently required | CORE participation denominator/formula/null policy authority | Member state and correction lineage | `BLOCKED_BY_BREADTH_DEFINITION_AUTHORITY` |
| Leadership | Required | Independent | Independent | Structural authority may be an input, but is not the dynamic result | Dynamic Leadership definition/formula and evidence policy | Member contribution, as-of, correction | `BLOCKED_BY_DYNAMIC_LEADERSHIP_DEFINITION_AUTHORITY` |
| Concentration | Required | Independent | Independent | Not inherently required | Contribution/weight/denominator/small-sample definition | Null and correction policy | `BLOCKED_BY_CONCENTRATION_DEFINITION_AUTHORITY` |
| Lifecycle | Required formal PIT lineage | Independent | Independent | May consume future formal structural metadata; does not create it | Transition thresholds, persistence, hysteresis, minimum duration | Prior-state identity, correction propagation, formal snapshot filter | `BLOCKED_BY_LIFECYCLE_TRANSITION_AUTHORITY_AND_FORMAL_UPSTREAM_LINEAGE` / `SHADOW_ONLY` |
| Topic Map Score lane | Required | Required | Not separately required | Inherited only from Score consumer | Backend Score publication/read contract | Nullable field and lineage | `READY_AFTER_BACKEND_PUBLICATION`; `UNAVAILABLE` now; `PROHIBITED_BROWSER_DERIVATION` |
| Topic Map Grade lane | Required | Required | Required | Inherited from Score | Backend Grade publication/read contract | Nullable field and lineage | `READY_AFTER_BACKEND_PUBLICATION`; `UNAVAILABLE` now; `PROHIBITED_BROWSER_DERIVATION` |
| Historical Topic Score | Only bounded formal PIT dates | Required | Not separately required | Required through Score projection | Score publication and historical as-of contract | No current-mapping substitution | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_SCORE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Grade | Only bounded formal PIT dates | Required | Required | Inherited from Score | Grade publication and historical as-of contract | No current-mapping substitution | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_GRADE_PUBLICATION_AFTER_BOUNDARY` |
| Historical Topic Ranking | Only bounded formal PIT dates | Not inherently required | Not inherently required | Not inherently required | Ranking universe/tie-break/replay authority | Walk-forward leakage control | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_RANKING_DEFINITION_AUTHORITY_AFTER_BOUNDARY` |
| Historical Topic Lifecycle | Only bounded formal PIT dates | Independent | Independent | Structural role may be consumed only when formally versioned | Lifecycle transition and exact upstream lineage authority | Prior-state chain/correction propagation | `NOT_AUTHORIZED_BEFORE_FORMAL_PIT_BOUNDARY; BLOCKED_BY_LIFECYCLE_TRANSITION_AUTHORITY_AND_FORMAL_UPSTREAM_LINEAGE_AFTER_BOUNDARY` |

Topic Overview and Market Map remain consumers. Formal role labels, Score,
Grade, Ranking, Breadth, Leadership, Concentration, and Lifecycle are backend
owned. Browser code may display returned values, but may not calculate,
project, rank, infer roles, or turn preview/current mapping data into formal
state. Preview remains explicitly `PREVIEW` and cannot fill a formal null.

## Addendum F - Governance markers

```text
TASK_ID=TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001
PREDECESSOR_TASK=TASK-TOPIC-GOVERNED-LEADER-SET-AND-CORE-SEMANTIC-AUDIT-001
STRUCTURAL_ROLE_MODEL=REPRESENTATIVE_CORE_RELATED
CLASSIFICATION_MODE=SEMI_MANUAL_GOVERNED
STRUCTURAL_ROLE_FREQUENCY=LOW_FREQUENCY
STRUCTURAL_ROLE_EFFECTIVE_DATED=YES
STRUCTURAL_ROLE_VERSIONED=YES
AUTOMATIC_HARD_SELECTOR_AUTHORIZED=NO
STRUCTURAL_DYNAMIC_ROLE_SEPARATED=YES
DYNAMIC_LEADERSHIP_FORMULA_CREATED=NO
GOVERNED_LEADER_SET_DISPOSITION=COMPATIBILITY_ADAPTER_OVER_STRUCTURAL_ROLE_AUTHORITY
CORE_AUTHORITY_DISPOSITION=READY_AFTER_APPROVED_STRUCTURAL_ROLE_READ_MODEL
DUPLICATED_MANUAL_ROLE_AUTHORITY_REQUIRED=NO
SCORE_OWNER_SEMANTIC_GAP_CLOSED=YES
GRADE_OWNER_SEMANTIC_GAP_CLOSED=YES
SCORE_STRUCTURAL_ROLE_AUTHORITY_READY=NO
SCORE_GOVERNED_INPUT_PROJECTION_READY=NO
SCORE_READY_FOR_IMPLEMENTATION=NO
GRADE_READY_FOR_IMPLEMENTATION=NO
WS1_SCORE_GRADE_IMPLEMENTATION_CAN_BE_OWNER_AUTHORIZED=NO
APPLICATION_BEHAVIOR_CHANGED=NO
DATABASE_MUTATION=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
```

The companion machine-readable matrix and closure report are:

- `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001/authority-readiness.json`
- `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001.md`

## Addendum G - WS1-P2B-D001 policy and minimal authority closure

This addendum is the normative policy extension for
`TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002`.
The Owner-approved D001 decision is canonicalized here without reopening the
structural-role meanings, changing Production V1 Score mechanics, or creating
an implementation path that requires a migration, API, frontend, or database
write.

### G.1 D001 policy values

| Policy item | Canonical value |
| --- | --- |
| `WS1_P2B_D001` | `APPROVED_AND_CANONICALIZED` |
| `SCORE_PROJECTION_UNIVERSE` | `APPROVED_EFFECTIVE_CORE_MEMBERS` |
| `SCORE_PROJECTION_SELECTION` | `BOUNDED_CORE_SUBSET` |
| `FIXED_TOP_N` | `NO` |
| `SUBSET_SELECTION` | `AI_ASSISTED_PROPOSAL_PLUS_OWNER_REVIEW` |
| `RUNTIME_AI_SELECTION` | `PROHIBITED` |
| `OWNER_REVIEW_REQUIRED` | `YES` |
| `IMPORTANCE_VALUES` | `1.00`, `0.75`, `0.50` |
| `IMPORTANCE_GOVERNANCE` | `LOW_FREQUENCY`, `GOVERNED`, `OWNER_REVIEWED`, `EFFECTIVE_DATED`, `VERSIONED` |
| `DYNAMIC_MARKET_AUTO_SELECTION` | `NO` |
| `DYNAMIC_MARKET_AUTO_REWEIGHTING` | `NO` |
| `SECOND_STRUCTURAL_ROLE_AUTHORITY_CREATED` | `NO` |
| `GOVERNED_LEADER_SET` | `COMPATIBILITY_ADAPTER_OVER_STRUCTURAL_ROLE_AUTHORITY` |

The bounded subset is not equal to all CORE and does not have a fixed count.
Each Topic may have a different approved member count. `minimum sufficient
representative CORE subset` describes the human-governed artifact intent; it is
not a runtime sufficiency score, threshold, optimizer, clustering rule, or
selector. The approved artifact contains the selected members.

AI may assist an offline proposal using low-frequency structural evidence, but
the proposal is not authority. Formal use requires human/Owner review,
approval, effective dating, versioning, and lineage. Application runtime must
not call an LLM or automatically mutate membership or importance.

### G.2 Importance is Score consumer metadata, not a structural role

The existing legal `LeaderDefinition.importance` values remain unchanged:

| Importance | Score consumer meaning |
| --- | --- |
| `1.00` | `PRIMARY_STRUCTURAL_REPRESENTATIVE_WITHIN_CORE` |
| `0.75` | `STRONG_CORE_REPRESENTATIVE` |
| `0.50` | `SUPPORTING_CORE_REPRESENTATIVE_INCLUDED_IN_SCORE_PROJECTION` |

These values are consumer-specific metadata on an already approved CORE
member. They cannot promote `REPRESENTATIVE` or `RELATED` to CORE and are not a
second taxonomy such as `LEADER_ROLE`, `PRIMARY_ROLE`, `SECONDARY_ROLE`, or
`SCORE_ROLE`.

Importance is low-frequency and Owner-reviewed. Price return, intraday return,
volume, RSI, MACD, technical evidence, Topic Score, Grade, Ranking, Dynamic
Leadership, Lifecycle, Opportunity, Recommendation, and news sentiment must
not automatically change member selection or importance.

### G.3 Exact deterministic authority chain

```text
approved, effective, non-superseded Structural Role Authority
  where structural_role = CORE
    -> approved effective CORE population
      -> approved Score Projection V1 bounded CORE subset
        -> deterministic GovernedLeaderSet compatibility adapter
          -> existing Production V1 Score evaluator
```

The adapter only translates the approved projection artifact into the existing
`GovernedLeaderSet` representation. It does not select members, change
importance, read market performance, read Dynamic Leadership, or adjust inputs
after seeing Score output.

### G.4 Minimal Structural Role Authority contract

The formal authority record must be resolvable by `topic_id`, `instrument_id`,
and requested as-of date, and must contain at least:

| Field | Required behavior |
| --- | --- |
| `topic_id`, `instrument_id` | Canonical identities; display slug/name is insufficient |
| `structural_role` | Exactly `REPRESENTATIVE`, `CORE`, or `RELATED` |
| `approval_state` | Only `APPROVED` is consumable; proposed/draft is not authority |
| `effective_from`, `effective_to` | Deterministic interval resolution at requested as-of |
| `authority_version` | Version identity bound to every consumer |
| `source_artifact_id`, `source_artifact_hash` | Immutable provenance reference |
| `approval_reference`, approved identity | Human/Owner approval evidence |
| `correction_sequence`, supersession links | Append-only correction and current/non-superseded resolution |
| `lineage_hash` | Reconstructable identity/role/interval/approval/provenance binding |

For `(topic, instrument, as_of)` the resolver must answer whether a relation
exists, its role, approval state, effective state, supersession state, version,
and lineage. Missing, unknown, conflicting, or ambiguous authority fails
closed; it is never inferred from relation order or metadata labels.

`InstrumentTopicRelation` is the only existing canonical carrier suitable for
minimal reuse. It currently supplies topic/instrument identity,
`relation_version`, `valid_from`, `valid_to`, and JSON metadata. It does not
currently supply or enforce the required approval, provenance,
correction/supersession, constrained role namespace, or formal as-of resolver.
Therefore:

```text
STRUCTURAL_ROLE_POLICY_READY=YES
STRUCTURAL_ROLE_AUTHORITY_READY=NO
STRUCTURAL_ROLE_AUTHORITY_CARRIER=InstrumentTopicRelation_REUSE_WITH_MINIMAL_AUTHORITY_EXTENSION
IMPLEMENTATION_DISPOSITION=BLOCKED_BY_STRUCTURAL_ROLE_AUTHORITY_READ_MODEL
```

No migration, schema, ORM, import, admin, or API implementation is included in
this closure.

### G.5 Minimal Score Projection V1 contract

The projection artifact/read contract must contain:

| Field | Required behavior |
| --- | --- |
| `topic_id` | Canonical Topic identity |
| `projection_version` | Consumer projection version |
| `effective_from`, `effective_to` | As-of eligibility interval |
| `approval_state`, `approval_reference` | Only approved projection is formal |
| `source_structural_role_authority_id`, `source_authority_version` | Exact upstream binding |
| selected CORE members | Explicit bounded subset; no automatic selection |
| per-member `score_importance` | Exactly `1.00`, `0.75`, or `0.50` |
| projection lineage | Reconstructable source/projection identity and digest |
| correction/supersession identity | Append-only successor and current resolution |

For every selected member at the same relevant as-of, the projection resolver
must validate: approved, effective, non-superseded, and structural role `CORE`.
The projection itself must be approved, effective, non-superseded, versioned,
lineage-complete, and non-conflicting. Any failure is `FAIL_CLOSED`.

The projection artifact is a Score-consumer artifact, not a second Structural
Role Authority. It adds only `selected_for_score_projection`,
`score_importance`, and projection approval/version/effective metadata.

```text
SCORE_PROJECTION_POLICY_READY=YES
SCORE_GOVERNED_INPUT_PROJECTION_READY=NO
GOVERNED_LEADER_SET_ADAPTER_READY=NO
IMPLEMENTATION_DISPOSITION=BLOCKED_BY_SCORE_PROJECTION_ARTIFACT_AND_READ_RESOLVER
```

The repository has the existing `GovernedLeaderSet` shape and validators, but
no approved projection artifact or resolver that can produce it from one
Structural Role Authority. The existing shape therefore remains a compatibility
boundary, not proof that the adapter is ready.

### G.6 Fail-closed validation matrix

| Condition | Formal result |
| --- | --- |
| Member absent from Structural Role Authority | `FAIL_CLOSED` |
| Member role is `RELATED` or `REPRESENTATIVE` | `FAIL_CLOSED` |
| CORE relation unapproved | `FAIL_CLOSED` |
| CORE relation outside effective interval | `FAIL_CLOSED` |
| CORE relation superseded | `FAIL_CLOSED` |
| Importance outside `{1.00, 0.75, 0.50}` | `FAIL_CLOSED` |
| Projection unapproved or outside effective interval | `FAIL_CLOSED` |
| Source authority id/version missing or not reconstructable | `FAIL_CLOSED` |
| Conflicting active projection versions | `FAIL_CLOSED` |
| Missing lineage or approval reference | `FAIL_CLOSED` |
| Topic A valid while Topic B has no projection | A may be eligible; B is unavailable; no global failure |
| Dynamic Leadership or daily market evidence changes | No automatic projection or importance change |

### G.7 Readiness and scope boundary

| Capability state | Result |
| --- | --- |
| `POLICY_READY` | `YES` for D001 policy values |
| `AUTHORITY_READY` | `NO`; required persisted/read authority fields and resolver are absent |
| `IMPLEMENTATION_READY` | `NO`; formal minimal path needs the authority/projection read model |
| `PUBLICATION_READY` | `NO`; Score/Grade API/publication remains outside scope |
| `PM_APPROVAL_ARTIFACT_READY` | `NO`; referenced 003F artifact is not tracked canonical evidence |
| `SCORE_READY_FOR_IMPLEMENTATION` | `NO` |
| `GRADE_READY_FOR_IMPLEMENTATION` | `NO`, downstream of Score |
| `SCORE_READY_FOR_PUBLICATION` | `NO` |
| `GRADE_READY_FOR_PUBLICATION` | `NO` |

The exact routing is:

```text
READY_FOR_STRUCTURAL_ROLE_AUTHORITY_READ_MODEL_AND_SCORE_PROJECTION_MINIMAL_IMPLEMENTATION
BLOCKED_BY_STRUCTURAL_ROLE_AUTHORITY_READ_MODEL
BLOCKED_BY_SCORE_PROJECTION_ARTIFACT_AND_READ_RESOLVER
BLOCKED_BY_COMMITTED_PM_APPROVAL_ARTIFACT_RECONCILIATION
```

This is not a new NEXT_TASK and does not authorize the routed implementation.
The missing projection for one Topic blocks only that Topic's eligibility; it
does not globally block all Topics or redefine the Score system.

## Addendum H - WS1 structural-role authority and projection implementation

This addendum records the bounded implementation authorized by
`TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003`.
It does not reopen `WS1_P2B_D001`, create role data, publish Score/Grade, or
activate any downstream derived lane.

### H.1 Implemented read-model boundary

The existing `InstrumentTopicRelation` remains the single Structural Role
Authority carrier. Migration `0031_task_topic_structural_role_score_projection`
adds nullable formal fields for role, approval, provenance, correction, and
supersession. Legacy relation rows remain non-formal until an approved,
effective-dated, lineage-complete authority ingest populates those fields.

The additive Score Projection V1 read model consists of
`topic_score_projections` and `topic_score_projection_members`. A projection
stores an approved bounded CORE subset, legal Score importance values, exact
authority-version binding, projection lineage, and append-only correction /
supersession identity. No member selector, Top-N rule, runtime AI, or formula
implementation is included.

### H.2 Resolver and adapter contract

`resolve_structural_role` supports explicit `CURRENT` and `HISTORICAL` modes.
Current mode excludes superseded authorities; historical mode preserves the
authority effective at the requested as-of date. Missing, unapproved,
ineffective, ambiguous, conflicting, or lineage-incomplete authority fails
closed.

`resolve_score_projection` validates the projection and every selected member
against the same as-of Structural Role Authority. Every member must resolve to
`CORE`, remain approved/effective/non-superseded for the selected read mode,
and match its exact authority ID/version. Invalid importance, missing lineage,
conflicting active versions, or supersession ambiguity fails closed.

`build_governed_leader_set` is a deterministic compatibility adapter only. It
maps the validated projection to the existing `GovernedLeaderSet` shape and
cannot select members, change importance, inspect market evidence, or read
Score/Grade/Lifecycle outputs.

### H.3 Population and publication boundary

No governed Structural Role Authority records or Score Projection records were
bulk-created by this task. Coverage therefore remains `0 / NOT_YET_POPULATED`.
Infrastructure is ready for separately authorized Owner-reviewed authority
ingestion and projection ingestion. Score/Grade publication remains outside
scope and unavailable until formal approved data, publication authority, and
the 003F approval artifact provenance are complete.

The owner-untracked 003F brief was observed with SHA-256
`C304032F41BCA466B70C5F1919F239B52030E6F1D5D284506C63623F649AADDF`, but no
committed digest, commit provenance, or canonical attestation binds that copy
as the original approval artifact. It remains
`BLOCKED_BY_COMMITTED_PM_APPROVAL_ARTIFACT_RECONCILIATION`; this task does not
recreate or canonicalize a look-alike artifact.

### H.4 Implementation readiness markers

```text
STRUCTURAL_ROLE_POLICY_READY=YES
STRUCTURAL_ROLE_AUTHORITY_INFRASTRUCTURE_READY=YES
STRUCTURAL_ROLE_AS_OF_RESOLVER_READY=YES
SCORE_PROJECTION_POLICY_READY=YES
SCORE_PROJECTION_INFRASTRUCTURE_READY=YES
SCORE_PROJECTION_AS_OF_RESOLVER_READY=YES
GOVERNED_LEADER_SET_ADAPTER_READY=YES
PM_APPROVAL_ARTIFACT_READY=NO
GOVERNED_ROLE_DATA_POPULATED=0_NOT_YET_POPULATED
SCORE_PROJECTION_DATA_POPULATED=0_NOT_YET_POPULATED
READY_FOR_GOVERNED_ROLE_DATA_INGESTION=YES
READY_FOR_SCORE_PROJECTION_DATA_INGESTION=YES
READY_FOR_SCORE_GRADE_BACKEND_PUBLICATION_IMPLEMENTATION=YES
SCORE_READY_FOR_IMPLEMENTATION=YES
GRADE_READY_FOR_IMPLEMENTATION=YES
SCORE_READY_FOR_PUBLICATION=NO
GRADE_READY_FOR_PUBLICATION=NO
```

The implementation remains non-publishing and non-Production. Migration
upgrade/downgrade SQL, focused fail-closed tests, and the full backend suite
are validation evidence only; no database URL was provided and no database
fixture or Production gate was run.

### G.8 D001 governance markers

```text
TASK_ID=TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002
PREDECESSOR_TASK=TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001
WS1_P2B_D001=APPROVED_AND_CANONICALIZED
SCORE_PROJECTION_UNIVERSE=APPROVED_EFFECTIVE_CORE_MEMBERS
SCORE_PROJECTION_SELECTION=BOUNDED_CORE_SUBSET
FIXED_TOP_N=NO
RUNTIME_AI_SELECTION=PROHIBITED
OWNER_REVIEW_REQUIRED=YES
IMPORTANCE_VALUES=1.00,0.75,0.50
DYNAMIC_MARKET_AUTO_SELECTION=NO
DYNAMIC_MARKET_AUTO_REWEIGHTING=NO
SECOND_STRUCTURAL_ROLE_AUTHORITY_CREATED=NO
GOVERNED_LEADER_SET_DISPOSITION=COMPATIBILITY_ADAPTER_OVER_STRUCTURAL_ROLE_AUTHORITY
STRUCTURAL_ROLE_POLICY_READY=YES
STRUCTURAL_ROLE_AUTHORITY_READY=NO
SCORE_PROJECTION_POLICY_READY=YES
SCORE_GOVERNED_INPUT_PROJECTION_READY=NO
GOVERNED_LEADER_SET_ADAPTER_READY=NO
PM_APPROVAL_ARTIFACT_READY=NO
SCORE_READY_FOR_IMPLEMENTATION=NO
GRADE_READY_FOR_IMPLEMENTATION=NO
SCORE_READY_FOR_PUBLICATION=NO
GRADE_READY_FOR_PUBLICATION=NO
RANKING_CHANGED=NO
BREADTH_CHANGED=NO
DYNAMIC_LEADERSHIP_CHANGED=NO
CONCENTRATION_CHANGED=NO
LIFECYCLE_CHANGED=NO
TOPIC_MAP_IMPLEMENTED=NO
FRONTEND_CHANGED=NO
OPPORTUNITY_CHANGED=NO
RECOMMENDATION_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER_ACTIVATION=NO
NEXT_TASK_CHANGED=NO
```

The companion machine-readable artifact and closure report are:

- `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002/authority-readiness.json`
- `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002.md`
