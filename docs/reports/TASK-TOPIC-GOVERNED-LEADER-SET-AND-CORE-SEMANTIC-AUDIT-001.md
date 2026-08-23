# TASK-TOPIC-GOVERNED-LEADER-SET-AND-CORE-SEMANTIC-AUDIT-001

## Audit identity and boundary

This report is the bounded WS1 semantic audit requested before continuing the
Phase 2A Leader Set / Score publication authority work. It is an evidence
audit, not a new architecture contract, role-design task, implementation task,
or production-policy approval.

| Field | Result |
|---|---|
| `TASK_ID` | `TASK-TOPIC-GOVERNED-LEADER-SET-AND-CORE-SEMANTIC-AUDIT-001` |
| `WORKSTREAM` | `WS1 / Topic Derived Intelligence / bounded semantic audit` |
| `SOURCE_HEAD` | `e1cfc3db7a8b6ce28461b245af3107fbecd71bd5` |
| `SOURCE_BRANCH` | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| `SOURCE_WORKTREE` | `C:\Users\acer\Documents\Codex\ws1-governed-leader-set-core-audit-20260816` |
| `WRITE_SET` | This report only |
| `APPLICATION_CODE_MODIFIED` | `NO` |
| `TESTS_MODIFIED` | `NO` |
| `SCHEMA_OR_MIGRATION_MODIFIED` | `NO` |
| `API_FRONTEND_DATABASE_MODIFIED` | `NO` |
| `NEXT_TASK_CHANGED` | `NO` |
| `PUSH_MERGE_DEPLOY_PRODUCTION_MUTATION` | `NO` |
| `CANONICAL_STATUS` | `CANONICALIZED` |
| `CANONICAL_PROMOTION_COMMIT` | `7055112615ccfcdd0f1b9d799df62327e5969e89` |
| `RELEASE_STATUS` | `NOT_RELEASE_CANDIDATE` |
| `PRODUCTION_VERIFICATION` | `NOT_PERFORMED` |

The canonical checkout was dirty at cold start: `18` tracked modifications and
`156` untracked paths. Those paths were preserved and were not used as formal
authority. `AI/NEXT_TASK.md` was read-only inspected; its SHA-256 was
`FF640C735A2CDD4D8238157B287D293D0385B67F673150249A90F49661FFEB70` and it
was not changed.

## 1. Evidence inventory

The audit used committed evidence from `SOURCE_HEAD`. Owner-untracked files,
old worktrees, task names, and folder names were not treated as authority.

| Evidence | What it proves | Authority state |
|---|---|---|
| `services/api/src/topicpilot_api/topic_engine/runtime_readiness.py:34-63,158-204` | Defines the explicit `GovernedLeaderSet` shape and fail-closed runtime blockers. | Formal input/readiness contract; no selector or default artifact. |
| `services/api/src/topicpilot_api/topic_engine/topic_score_formal.py:85-143,242-320` | Requires policy approval, CORE authority, approved Leader Set, exact PIT/as-of binding, and carries Leader Set lineage into the non-persistent envelope. | Formal derivation boundary; no publication writer. |
| `services/api/src/topicpilot_api/topic_engine/production_policy.py:73-240,345-502` | Consumes explicit CORE ids, explicit `LeaderDefinition` weights, and leader-set version; evaluates eligibility, weighted Leadership, Score, and Grade. | Non-activating Production V1 evaluator; no member selection. |
| `services/api/tests/test_topic_score_formal.py:26-128,146-243` | Builds a synthetic approved authority bundle and proves successful derivation and fail-closed cases. | Test-only synthetic prerequisite. |
| `services/api/tests/test_runtime_readiness.py:70-147` | Builds a synthetic readiness Leader Set and checks missing-prerequisite blockers. | Test-only synthetic prerequisite. |
| `services/api/src/topicpilot_api/topic_engine/research_history.py:384-404` and `fixtures/research/topic_formula_historical_evidence.v1.json` | Uses explicit synthetic `coreMembers` and `leaderInstrumentIds`; missing leaders become `NO_EXPLICIT_LEADER_SET`. | Research-only fixture/parser; not Production authority. |
| `services/api/src/topicpilot_api/orm/models.py:161-175` | Stores effective-dated relation type/version/metadata. | Formal relation storage, but no Leader Set or CORE authority. |
| `services/api/alembic/versions/0030_task_topic_daily_state_formal_authority.py` and `services/api/src/topicpilot_api/orm/snapshots.py` | Defines PIT snapshot/member-fact identity, finality, and correction/supersession fields. | Formal upstream PIT authority; no role selection. |
| `docs/DAILY_PROGRESS.md:292-306`, `docs/WORK_ORDERS.md:41-44` | PM-001/PM-002 conceptual meanings: CORE population and semi-static versionable Leader Set primarily drawn from CORE; exact mechanics deferred. | Committed product/policy evidence, not a concrete member artifact. |
| `services/api/src/topicpilot_api/topic_lifecycle_engine.py:174-199,239-271,420-453` and `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md:15-40,80-86` | Role-aware observed leader selection and strongest-observed proxy; no approved role/Leader Set semantic. | Shadow-only Lifecycle behavior. |
| `apps/web/app/lib/topic-api.ts:163-171,189-231,385-405` and `apps/web/app/lib/topic-preview.ts:100-103` | Maps relation strings to display labels; keeps `leaderCore` as `CONTRACT_GAP`; Preview contains synthetic `CORE` labels/weights. | Consumer/Preview mapping, not formal Leader Set authority. |
| `docs/product/TOPICPILOT_PRODUCT_DECISIONS.md:45-50,106-117` and `docs/reports/TASK-FE-TOPIC-DETAIL-001_TOPIC_DETAIL_RESEARCH_WORKSPACE.md` | Representative/Core/Related are product presentation roles; browser must not infer leaders or ranking. | Committed product semantics; backend role authority remains incomplete. |
| `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md:284-327` and `docs/architecture/CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md:155-176` | Trend/Catch-up and lagging/stronger concepts are downstream shadow/research candidates. | Shadow/research-only; not Topic Leader Set authority. |

## 2. Q1 — Actual `GovernedLeaderSet` use

### Definition

`GovernedLeaderSet` is a frozen input object with:

- `version`;
- `lifecycle` such as `APPROVED`;
- optional `artifact_id`;
- `effective_date`; and
- per-topic `topic_leaders` containing `LeaderDefinition(member_id,
  importance)` values.

The class validates identity shape, topic uniqueness, and duplicate members. It
does not select members, read a database, infer a current leader, or provide a
default set.

### Formal consumers and effects

1. `FormalTopicScoreAuthority` requires an approved Leader Set, a non-empty
   artifact id, a policy-version match, and an effective date.
2. `derive_formal_topic_score` requires the Leader Set to be effective for the
   PIT snapshot, requires a non-empty topic entry, and requires every Leader
   Set member to be in the explicit CORE authority.
3. The adapter passes the explicit leaders and `leader_set_version` into
   `ProductionTopicInput`; the evaluator uses `LeaderDefinition.importance`
   for weighted Leadership and consensus, then combines Breadth and Leadership
   into the existing Production V1 Score and Grade.
4. The non-persistent `topic-score-formal.v1` envelope carries
   `leaderSetVersion` and `leaderSetArtifactId` in lineage.
5. `evaluate_activation_readiness` checks for missing, unapproved, artifactless,
   or version-mismatched Leader Set input before runtime readiness can be
   `READY`.

There is no committed Leader Set selector, database authority table, approved
member artifact, API publication route, or Lifecycle import of the
`GovernedLeaderSet` type. Lifecycle instead reads effective relation metadata
and uses a role-aware observed member or a labelled maximum-change proxy.

## 3. Q2 — Temporal semantic

**Answer: `A. STRUCTURAL_LOW_FREQUENCY_SET` at the conceptual product/policy
layer.**

The strongest committed evidence is PM-002 in `docs/DAILY_PROGRESS.md`: the
Leader Set is described as semi-static, slow-changing, versionable, primarily
drawn from CORE, and distinct from a daily top gainer, market-cap list, or
volume ranking. Stable Leader identity is explicitly separated from today's
Leadership evidence.

The formal adapter also uses the set as a **score-eligible governed member
subset**: it enforces `Leader Set members ⊆ explicit CORE authority` and passes
the explicit weighted members to the evaluator. That is an implementation
consumption shape, not evidence that the product definition is “daily market
leaders” or that a selection rule exists.

Still unresolved from committed evidence are member selection, update cadence,
member count, source authority, weights, effective-scope rules, correction
semantics, and the concrete approved artifact. No Top-N, return, market-cap,
volume, or Score-contribution rule is authorized.

## 4. Q3 — CORE authority and relation

### What CORE currently means

PM-001 freezes CORE as the conceptual population for current/static Market
Participation/Breadth, with current primary-topic membership as the default
basis. Exact derivation, cutoffs, formulas, windows, normalization, weights,
and thresholds remain unresolved.

The formal Score code does not resolve CORE. It accepts an explicit
`core_member_ids` tuple plus `core_authority_id`, checks identity shape, uses the
ids as the eligibility population, requires at least 60% observed coverage and
at least three valid observed members, and includes CORE identity in lineage.
The current ORM relation model has effective dates and free-text
`relation_type`/metadata, but no committed CORE authority artifact or role
enum. The current Topic Snapshot engine aggregates effective relations as
members and does not establish a CORE subset.

### CORE versus `GovernedLeaderSet`

**`CORE_AND_LEADER_SET_RELATION = SUBSET` for the current formal Score path.**

The formal adapter explicitly rejects any Leader Set member that is not in the
supplied CORE ids. This does not prove that CORE and Leader Set are equivalent,
nor does it provide an independent source authority for either set. At the
conceptual layer, PM-002 says “primarily drawn from CORE,” while the concrete
formal adapter enforces the stricter subset relation. Whether that relation is
normative for every future consumer remains an Owner decision.

## 5. Q4 — Phase 1 synthetic Leader Set trace

The formal Phase 1 test helper in
`services/api/tests/test_topic_score_formal.py` constructs:

- a synthetic `PolicyApprovalRecord` with approved policy references;
- `ProductionV1PolicyBundle(... leader_set_version="leaders.v1")`;
- `GovernedLeaderSet(version="leaders.v1", lifecycle="APPROVED",`
  `artifact_id="leader-set-artifact-v1", effective_date=2026-08-01)`;
- one synthetic topic containing `s1` with importance `1.0` and `s2` with
  importance `0.75`;
- explicit CORE ids `s1`, `s2`, `s3` and `core-authority-v1`;
- an exact 2026-08-07 observation/as-of binding; and
- a formal PIT snapshot plus three immutable synthetic member facts.

The derivation validates PIT mode/finality/date/session, facts, CORE coverage,
Leader Set effectiveness and subset relation, then calls Production V1
evaluation. The successful result is a Score/Grade-bearing
`FORMAL / UNPUBLISHED` envelope. The empty-topic Leader Set test fails during
derivation; the empty CORE authority test fails during authority construction.

The runtime-readiness tests use a second synthetic one-topic set with `s1` and
the same version/artifact shape. The research fixture
`topic_formula_historical_evidence.v1.json` separately declares
`coreMembers`, `leaderInstrumentIds`, and synthetic Leader Set versions. Its
parser only proves that the listed leaders are explicit CORE members; its mode
is `RESEARCH_ONLY`, and missing leaders produce `NO_EXPLICIT_LEADER_SET` and
`DATA_INSUFFICIENT` in the research corpus.

None of these construction methods is an approved production selection rule.
They contain no evidence for “top gainers,” market cap, volume, contribution
ranking, or any other member-selection algorithm.

## 6. Q5 — Exact missing-Leader-Set failure semantics

| Layer | Formal Phase 1 behavior when no approved `GovernedLeaderSet` exists |
|---|---|
| `DERIVATION` | Cannot execute to completion. Authority validation or the topic lookup raises `FormalTopicScoreAuthorityError` for unapproved/missing artifact, version/effective-date mismatch, or empty topic members. |
| `EVALUATION` | `evaluate_production_v1` is not reached by the formal adapter when the set is absent/empty. No formal weighted Leadership or Score is evaluated. |
| `ELIGIBILITY` | This is not converted into a CORE coverage eligibility result. Runtime readiness separately reports `LEADER_SET_MISSING`, `LEADER_SET_NOT_APPROVED`, `LEADER_SET_ARTIFACT_MISSING`, or `LEADER_SET_VERSION_MISMATCH`; `ELIGIBILITY_AUDIT_MISSING` is a separate blocker. |
| `PUBLICATION` | No formal `FORMAL / UNPUBLISHED` Score/Grade envelope is created as a missing-authority fallback. `UNPUBLISHED` describes a successfully derived non-persistent envelope, not an authority waiver. |
| `PERSISTENCE` | No persistence path is entered. Missing Leader Set does not create a derived row, supersession row, or materialization result. |
| `READ_MODEL` | No formal Score/Grade read model is produced. The generic research API may return `DATA_INSUFFICIENT`/`NO_EXPLICIT_LEADER_SET`, while the default Topic Intelligence provider may return its separate 503 unavailable response; neither is formal publication. |
| `GRADE` | Grade is downstream of successful Score evaluation. With the formal Leader Set missing, the formal Score/Grade result is unavailable/null rather than silently downgraded to a Grade. |

Therefore the exact conclusion is: **missing approved Leader Set blocks the
formal derivation path before evaluation; it is not a “derive and publish as
UNPUBLISHED” fallback, not a persistence-only failure, and not equivalent to a
CORE coverage failure.**

## 7. Q6 — Existing role-semantics inventory

| Concept | Status | Evidence-backed meaning | Semantic bucket |
|---|---|---|---|
| `GovernedLeaderSet` | `FORMAL` contract / authority artifact absent | Explicit approved input with version, effective date, topic members, importance, and lineage. | Structural identity plus Score eligibility; collision-sensitive. |
| `CORE` / core member | `AMBIGUOUS` | PM conceptual structural/current population; formal Score input and eligibility denominator; no independent committed source artifact. | Structural role plus Score eligibility. |
| Score-eligible governed member set | `FORMAL` input contract | Explicit CORE ids and explicit Leader Set are required by the formal adapter; selection authority is absent. | Score eligibility. |
| Leadership | `SHADOW_ONLY` | Non-activating weighted evaluator shape exists; Lifecycle exposes role-aware evidence or a labelled proxy; no approved formal role authority. | Dynamic evidence plus Score component. |
| Leader / leader role token | `AMBIGUOUS` | Lifecycle treats `LEADER`, `PRIMARY`, and `REPRESENTATIVE` as role-aware inputs; frontend maps `LEADER` to representative; neither proves a formal Leader Set. | Structural and dynamic role token collision. |
| Representative stock/member | `DOC_ONLY` | Product documents expose Representative/Core/Related roles; frontend display mapping and Preview examples exist, but formal Leader Set is explicitly a contract gap. | Structural role. |
| Related member | `AMBIGUOUS` | Formal relation payloads use relation metadata; committed fixture schema uses `RELATED`, while exact product role authority is not unified with CORE/Leader semantics. | Structural membership role. |
| Follower | `ABSENT` | No committed formal or shadow Topic role authority was found. | Dynamic market role. |
| Laggard / lagging member | `SHADOW_ONLY` | Catch-up strategy uses a lagging-but-healthy stock; Core V0 documents leave laggard identity and improvement semantics unresolved. | Dynamic market role / research input. |
| Catch-up | `SHADOW_ONLY` | V1 Opportunity Catch-up is an independent provisional shadow strategy; it is not a Topic Leader Set or Topic Score input authority. | Dynamic market state. |
| Weakening / `DECLINING` | `SHADOW_ONLY` | Lifecycle uses weak ratio, divergence/decay, confirmation, and provisional transition policy; it is not a member role. | Dynamic topic state. |
| Topic member role | `AMBIGUOUS` | ORM relation type is effective-dated/free-text; metadata may contain `topicRole`/`role`; frontend maps several strings; no single formal role authority is committed. | Structural/dynamic boundary. |
| Topic exposure / weight | `AMBIGUOUS` | Preview/demo relations expose weights, while formal LeaderDefinition uses importance; no unified approved exposure/weight authority was found. | Structural contribution plus Score eligibility. |

`FORMAL` above means a typed/runtime contract exists; it does not mean that a
production authority artifact or publication path exists. `DOC_ONLY`,
`SHADOW_ONLY`, and `RESEARCH_ONLY` evidence must not be promoted by naming
similarity.

## 8. Q7 — Semantic collision findings

```text
STRUCTURAL_VS_DYNAMIC_ROLE_COLLISION = YES
LEADER_SET_SEMANTIC_AMBIGUITY = YES
CORE_AND_LEADER_SET_RELATION = SUBSET
```

The collision risk is concrete but is not a reason to invent a replacement
architecture in this audit:

- PM-002 separates stable Leader identity from daily Leadership evidence, but
  Lifecycle uses the same role-like strings to select a daily role-aware
  observation or fall back to the strongest observed member.
- The frontend maps `LEADER` to `代表股` and `CORE` to `核心股`, while formal
  relation fixtures use `PRIMARY`/`SECONDARY`/`RELATED` and Preview data also
  uses `CORE`; these are consumer mappings, not a single authority model.
- The Score adapter requires a governed Leader subset of explicit CORE, while
  the product role surface describes Representative/Core/Related and the
  Opportunity/Catch-up surface describes lagging/improving dynamic states.
- No evidence authorizes treating Representative as Leader, Core as Leader,
  daily strongest change as Leader, or Score contribution as Leader selection.

## 9. Exact Score dependency trace

```text
0030 formal PIT snapshot
        │ exact mode/finality/date/session/supersession checks
        ▼
immutable PIT member facts
        │ exact fact date/hash/source; no missing-to-zero conversion
        ├── explicit CORE authority (core_member_ids + core_authority_id)
        │       └── eligibility population, coverage/count, lineage
        ├── approved policy bundle / approval artifact
        │       └── policy refs and leader_set_version binding
        ├── explicit GovernedLeaderSet
        │       └── topic leaders, importance, effective date, artifact lineage
        └── ObservationAsOfBinding
                └── exact as-of/session/freshness/input hash
                         ▼
              Production V1 evaluation
                         ▼
              deterministic Score / Grade
                         ▼
              FORMAL / UNPUBLISHED envelope
```

The arrows are the observed formal adapter dependency, not a new product
definition. PIT and member facts supply immutable evidence; CORE supplies the
explicit eligibility population; policy approval supplies algorithm and
reference identity; Leader Set supplies the explicit Leadership members and
weighted evidence; as-of supplies the observation boundary; Score/Grade are
derived only after all of those checks pass. No persistence, API, frontend, or
Lifecycle dependency is introduced by this trace.

## 10. Bounded Owner decision surface

These are the only unresolved questions that materially affect the next
Leader Set / CORE authority closure. This audit does not answer them.

| Decision ID | Owner question | Evidence implication if unresolved |
|---|---|---|
| `WS1-GLS-SEM-001` | Confirm whether `GovernedLeaderSet` retains the PM-002 conceptual meaning: semi-static, slow-changing, versionable structural set primarily drawn from CORE. | No formal member-selection authority or artifact may be inferred. |
| `WS1-CORE-SEM-002` | Identify the committed authority/artifact for CORE membership, effective dates, role meaning, and correction lineage; clarify whether CORE is structural membership or the Score eligibility population. | Formal CORE authority remains an explicit input with no source resolver. |
| `WS1-GLS-CORE-003` | Confirm whether the current formal adapter rule `Leader Set ⊆ CORE` is normative for all Score consumers, or only the present derivation boundary. | Score/Leader binding cannot be generalized beyond the observed adapter. |
| `WS1-ROLE-SEM-004` | Decide whether Representative/Core/Related structural roles are orthogonal to dynamic Leader/Follower/Laggard/Catch-up/Weakening states, and what consumer projections are allowed. | Prevents the existing role-token collision from becoming a formal cross-consumer dependency. |
| `WS1-LEAD-SEM-005` | Identify the formal role authority and daily evidence contract for Leadership; confirm whether stable Leader identity and daily Leadership evidence remain separate. | Formal Leadership remains unavailable even though a weighted evaluator shape exists. |
| `WS1-LIFE-SEM-006` | Decide whether Lifecycle may consume approved role metadata or must remain on its labelled strongest-observed proxy until such authority exists. | Lifecycle remains `SHADOW_ONLY / UNPUBLISHED`; no role-aware activation is authorized. |

No decision in this table authorizes a Top-N rule, dynamic-role algorithm,
renaming, selection threshold, implementation, migration, or publication.

## 11. Phase 2A impact

```text
PHASE_2A_IMPACT = PARTIAL_PROCEED_WITH_EXACT_BOUNDARIES
```

Phase 2A may continue its contract/authority work without redefining roles:

- use the PM-002 structural/low-frequency meaning as the current conceptual
  evidence;
- preserve the observed formal Score constraint that explicit Leader Set
  members are a subset of explicit CORE ids;
- keep Leader Set members, CORE source authority, policy approval, PIT/as-of,
  and lineage as separate evidence inputs; and
- keep Lifecycle/Opportunity role and Catch-up semantics outside the formal
  Leader Set until their own authorities close.

Phase 2A may not claim that a production Leader Set exists, select members,
publish Score/Grade, activate Leadership, or use Lifecycle/Opportunity role
tokens as a substitute. Owner decisions `WS1-GLS-SEM-001` through
`WS1-LIFE-SEM-006` remain bounded prerequisites for the affected formal paths.

## 12. Validation and stop boundary

| Check | Result |
|---|---|
| Canonical source/ref/HEAD and owner-state inspection | `PASS` |
| Isolated task worktree | `PASS` |
| Evidence path and line-reference review | `PASS` |
| Markdown write-set scope review | `PASS` |
| `git diff --check` | `PASS` |
| Secret-safe scan of report write-set | `PASS` |
| Application/static tests | `NOT_RUN_BY_SCOPE` — no code changed |
| DB/PostgreSQL/migration/API/frontend/provider/scheduler | `NOT_RUN_BY_SCOPE` |
| G1/G2/G3/Post-Close Canary | `PRESERVED / NOT_RERUN` |
| Production/deploy/push/merge | `NOT_RUN / NO` |
| `NEXT_TASK` | `NOT_MODIFIED` |

The audit stops here. It does not start Phase 2A implementation, create a new
formal architecture contract, alter existing contracts, define roles, create
a Leader Set, or open a successor task.

## 13. Source-to-canonical provenance

The report was created in the isolated task worktree at source commit
`7db37980d24fb6c75ae5b222bdf02a8d0549fd20`, then promoted by an explicit
commit-preserving cherry-pick into the canonical branch. The canonical HEAD
after promotion was
`7055112615ccfcdd0f1b9d799df62327e5969e89`. Only the report path was promoted;
no owner dirty/untracked path was staged, reset, cleaned, or overwritten.

## Final status markers

```text
AUDIT_STATUS=COMPLETE_FOR_BOUNDED_SEMANTIC_SCOPE
PHASE_2A_IMPACT=PARTIAL_PROCEED_WITH_EXACT_BOUNDARIES
STRUCTURAL_VS_DYNAMIC_ROLE_COLLISION=YES
LEADER_SET_SEMANTIC_AMBIGUITY=YES
CORE_AND_LEADER_SET_RELATION=SUBSET
CANONICAL_STATUS=CANONICALIZED
CANONICAL_PROMOTION_COMMIT=7055112615ccfcdd0f1b9d799df62327e5969e89
RELEASE_STATUS=NOT_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_PERFORMED
PUSH_REMOTE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```
