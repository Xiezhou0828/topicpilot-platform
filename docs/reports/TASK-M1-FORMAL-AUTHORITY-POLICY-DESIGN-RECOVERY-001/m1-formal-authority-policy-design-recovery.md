# TASK-M1-FORMAL-AUTHORITY-POLICY-DESIGN-RECOVERY-001

**結論狀態：** `TASK_COMPLETE_FOR_RECOVERY_REPORT / M1_BLOCKED / M2_NOT_STARTED`

本報告只做正式權威恢復、歷史語義對帳、技術缺口盤點與 Owner 決策抽取。
沒有新增政策、沒有啟用 provider、沒有發佈新的 Score/Grade/Lifecycle、沒有
修改 Production，也沒有修改受保護 Owner checkout。

## 1. Executive Summary

前一輪 M1 closure 的 `FORMAL_SCORE_GRADE_AUTHORITY_MISSING` 需要拆解修正。
目前 repository 已有 B2 Layer 2 正式 authority envelope 與 strict
`topic-score-pm-approval.v1` record：

- Score/Grade 政策已是 `APPROVED`，版本為 `topic-b2-layer2-policy-v1`，有效日
  `2026-09-15`，Owner 為 `topicpilot-owner`。
- 1,160 筆 Structural Role artifact row 已全部是 `APPROVED`，其中
  `CORE=650`、`REPRESENTATIVE=329`、`RELATED=181`。
- `WS1-P2B-D001` 已明確核准 Score 使用「approved effective CORE 的 bounded
  subset」，不是固定 Top-N，也不是每日自動選股；重要性只能為 `1.00/0.75/0.50`。
- 仍不能完成 M1 的原因是：正式 role/projection 資料沒有完成可驗證的 runtime
  readback，Score/Grade 沒有正式 writer/publication lane，Lifecycle transition
  policy 仍為 `PARTIAL_BY_DESIGN`，Formal Opportunity provider 仍是明確的
  `503 UNAVAILABLE` placeholder。

因此最早 blocker 不是重新設計 Score 公式，而是：

```text
FORMAL POLICY APPROVED
  -> RUNTIME AUTHORITY DATA / PROJECTION UNPOPULATED
  -> SCORE/GRADE WRITER AND PUBLICATION MISSING
  -> LIFECYCLE TRANSITION AUTHORITY PARTIAL
  -> OPPORTUNITY FORMAL PROVIDER INACTIVE
```

## 2. Current M1 Boundary

| Boundary | Current result | Meaning |
|---|---|---|
| Historical market sequence | `CURRENT_THROUGH_2026-09-18` | Existing close/replay evidence is not itself Score/Grade authority. |
| Formal Topic publication | `READY_AT_ARTIFACT/CONTRACT_LEVEL` | Topic snapshots have formal PIT, finality, correction and supersession contracts; live DB readback is not re-certified here. |
| Score policy | `POLICY_APPROVED` | B2 formal artifact exists; runtime publication is separately gated. |
| Score result | `UNPUBLISHED` | Non-activating evaluator and formal envelope exist; writer/read API is absent. |
| Grade | `DOWNSTREAM_OF_SCORE` | Thresholds are approved in the same policy record; Grade cannot publish before Score. |
| Lifecycle | `FORMAL IMPLEMENTATION EXISTS / PUBLICATION GATED` | Formal publisher and migration exist, but post-close still calls the shadow engine and transition authority is partial. |
| Formal Opportunity | `PROVIDER_INACTIVE` | Formal API validates only canonical formal payloads; default provider intentionally returns 503. |
| M2 | `NOT_STARTED` | No M2 work is authorized by this report. |

## 3. Evidence Sources

This recovery used the current governed tree plus history, not only the previous
closure report. The most important reconciliation evidence is:

| Evidence | Location / commit | Recovered fact |
|---|---|---|
| B2 formal contract | `docs/architecture/TOPIC_B2_LAYER2_FORMAL_AUTHORITY_CONTRACT.md`, `d1a822c36ed8a04b863950f7c75fbbabb55aa9ff` | Layer 2 composes Daily Strength, Score/Grade, and independent Lifecycle; policy approval is separate from publication/activation. |
| B2 approval records | `docs/reports/TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001-20260915/`, `abd2866a24a6b9ec1c24c70a9a6f3527911023d5` | Strict Score/Grade approval record is `APPROVED`; Layer 2 is `POLICY_APPROVED`, publication `BLOCKED`, activation `NOT_ACTIVE`. |
| B2 governed registration | `docs/reports/TASK-INT-TOPIC-B2-003F-GOVERNED-REGISTRATION-001-20260915.md` | 003F provenance and exact hashes are registered; formal publication remains inactive. |
| Structural Role artifact | `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json` | 1,160 approved role rows, effective `2026-08-24`, source artifact hash `c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc`. |
| D001 closure | `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-SCORE-PROJECTION-POLICY-AND-MINIMAL-AUTHORITY-CLOSURE-002/authority-readiness.json` | Score projection policy is `APPROVED_AND_CANONICALIZED`; exact populated projection artifact is still absent. |
| Role/projection implementation | `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-READ-MODEL-AND-SCORE-PROJECTION-MINIMAL-IMPLEMENTATION-003/implementation-evidence.json` | Resolvers and migration 0031 exist; historical evidence records role/projection row population as `0_NOT_YET_POPULATED`. |
| Score evaluator | `services/api/src/topicpilot_api/topic_engine/production_policy.py` and `topic_score_formal.py` | Exact Production V1 mechanics and fail-closed authority inputs are implemented without activation. |
| Topic PIT state | `services/api/src/topicpilot_api/topic_daily_state.py` | Formal boundary is `2026-08-07`; snapshot date, session, finality and correction lineage are explicit. |
| Lifecycle formal lane | `services/api/src/topicpilot_api/topic_lifecycle_v1_3_formal.py`, `lifecycle_formal_publication.py`, migration 0037 | Formal evaluator/publisher/readback path exists; post-close currently calls shadow `TopicLifecycleEngine`. |
| Opportunity formal boundary | `services/api/src/topicpilot_api/formal_opportunity_universe.py`, `opportunity_api.py` | Formal Topic universe contract exists; canonical provider is intentionally unavailable. |
| Previous M1 closure | `docs/reports/TASK-M1-FORMAL-PIPELINE-FINAL-CLOSURE-001/` | Historical blocker was broader than the current B2 evidence and is superseded by this reconciliation. |

## 4. Formal Authority Inventory

`CURRENT_CANONICAL_REACHABILITY` is an artifact/code reachability judgment, not
a claim that Production has been activated.

| Authority ID | Name | Location | Commit SHA | Owner / creator | Status | Approval | Schema / version | Effective / as-of | Writer | Consumers | Current reachability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AUTH-TOPIC-PIT | Formal Topic authority | `config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json` | `6d9b87a22be955ab3c19871d17a39037acd968d7` | Owner-authorized B2 topic authority | `FORMAL_ACTIVE` at contract level | `OWNER-AUTHORIZED-B2-PROTECTED-TOPIC-AUTHORITY-20260910` | `topic-authority-activation.v1` | Effective `2026-08-24`; PIT boundary `2026-08-07` | `topic_daily_state.materialize_formal_plan` | Topic Snapshot, Lifecycle gate, Opportunity universe | Reachable; DB readback remains a separate gate. |
| AUTH-ROLE-V4 | Structural Role authority | `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json` | `bfbad80` lineage; current at `6d9b87a...` | Owner-reviewed canonical role expansion | `FORMAL_BUT_DISCONNECTED` | `OWNER_APPROVES_CANONICAL_REFERENCE_EXPANSION_REVIEW_20260912`; all 1,160 rows `APPROVED` | `topic-structural-role-authority.v1` / `...20260912.v4` | Effective `2026-08-24`; interval-resolved | Role ingestion not yet connected to a proven current DB readback | CORE / REPRESENTATIVE / RELATED consumers, Score, Lifecycle | Artifact reachable; runtime population/readback not proven. |
| AUTH-SCORE-GRADE | Score/Grade policy | `score-grade-policy-approval-record.json` | `abd2866a24a6b9ec1c24c70a9a6f3527911023d5` | `topicpilot-owner` | `FORMAL_ACTIVE` as policy authority | `decision_status=APPROVED` | `topic-score-pm-approval.v1`, `topic-b2-layer2-policy-v1` | Effective `2026-09-15` | No formal result writer | Production V1 evaluator, policy guard, B2 envelope | Reachable and hash-bound. |
| AUTH-LAYER2 | Layer 2 envelope | `layer2-policy-approval-record.json` | `abd2866...` | `GOVERNANCE_OWNER:topicpilot-owner` | `FORMAL_BUT_DISCONNECTED` | `authorityState=POLICY_APPROVED` | `topic-layer2-formal-authority.v1` | Effective `2026-09-15` | Artifact readback only | B2 guard and metadata readback | Publication `BLOCKED`; activation `NOT_ACTIVE`. |
| AUTH-D001 | Score projection / Leader Set policy | D001 closure and architecture Addendum G | `bbd25caa81fab17f34c6a7805d76170bde185d2d` | Owner decision `WS1-P2B-D001` | `FORMAL_ACTIVE` as policy; data `FORMAL_BUT_DISCONNECTED` | `APPROVED_AND_CANONICALIZED` | D001 policy; projection read model in migration 0031 | Effective-dated by source role and projection | No automatic selector; compatibility adapter only | Score evaluator / Leader Set input | Policy reachable; no populated per-topic projection artifact. |
| AUTH-SCORE-EVAL | Production V1 Score evaluator | `topic_engine/production_policy.py` | current governed tree `0050d6d25a34938fa35225dade8541be9051d20c` | Engineering under 003F | `IMPLEMENTED_NOT_ACTIVATED` | Consumes explicit approved record | `production-v1`; policy bundle version supplied externally | Rejects pre-policy effective dates | No provider or persistence write | Formal Score bridge | Reachable only through explicit caller inputs. |
| AUTH-SCORE-BRIDGE | Formal Score authority/publication envelope | `topic_engine/topic_score_formal.py` | current governed tree | Engineering under formal authority contract | `FORMAL_BUT_DISCONNECTED` | Requires approved policy, CORE, Leader Set, as-of binding | `topic-score-formal.v1` | Formal PIT from `2026-08-07`; B2 policy effective `2026-09-15` | Explicitly non-persistent; future writer required | Score/Grade publication | Resolver path exists; `UNPUBLISHED`. |
| AUTH-LIFECYCLE | Lifecycle V1.3 | `topic_lifecycle_v1.py`, `topic_lifecycle_v1_3_formal.py` | current governed tree | Product/engineering historical V1.3 line | `IMPLEMENTED_NOT_FORMALLY_APPROVED` for transition parameters; stage contract approved | B2 lifecycle `APPROVED`; transition `PARTIAL_BY_DESIGN` | `topic-lifecycle-v1.3-formal.v2`, policy `topic-lifecycle-policy.v1` | Formal publisher starts at `2026-08-24`; prior formal state is date-ordered | `FormalLifecyclePublisher` exists; post-close still calls shadow engine | Lifecycle readback and Opportunity context | Formal path exists but is not connected to post-close activation. |
| AUTH-OPP-UNIVERSE | Formal Opportunity universe | `formal_opportunity_universe.py` | current governed tree | Engineering boundary contract | `FORMAL_BUT_DISCONNECTED` | Formal Topic/eligibility/relation requirements encoded; provider approval absent | `formal-opportunity-universe.v1` | Exact requested `as_of` | Consumer function only | Formal universe, dedupe, provenance, prices | Reachable as read-only consumer; not a provider. |
| AUTH-OPP-POLICY | Opportunity qualification semantics | `docs/architecture/decisions/OPPORTUNITY_QUALIFICATION_POLICY_V1.md`, `topic_engine/opportunity_qualification.py` | current governed tree | PM semantic freeze / BE-024B | `SHADOW` | Shadow-only; exact numeric parameters provisional | `opportunity-qualification.v1.shadow`, `...parameters.v1.provisional` | Post-close cadence; no intraday rerank | Shadow strategy evaluator | Shadow API only | Not authorized for formal Production publication. |
| AUTH-OPP-API | Formal Opportunity API | `opportunity_api.py` | current governed tree | Engineering seam | `IMPLEMENTED_NOT_FORMALLY_APPROVED` | Provider must be canonical/formal | `opportunity-page-read.v1` | Request `asOf` must bind all nested sections | `CanonicalOpportunityProvider` placeholder | Formal page/detail API | Default path returns 503 by design. |

## 5. Score Policy Recovery

### Exact policy identity

```text
SCORE_ENGINE_EXISTS=YES
SCORE_POLICY_EXISTS=YES
SCORE_POLICY_FORMALLY_APPROVED=YES_ARTIFACT_LEVEL
SCORE_POLICY_OWNER=topicpilot-owner
SCORE_POLICY_VERSION=topic-b2-layer2-policy-v1
CANDIDATE=TOPIC_B2_LAYER2_POLICY_V1:v1
EFFECTIVE_DATE=2026-09-15
```

The approval record binds breadth, leadership, normalization, aggregation,
weights, eligibility, Grade, and rollback references to the registered 003F
digest. It does not authorize runtime activation by itself.

### Exact dependency graph

```text
Formal Topic Snapshot(T), member facts(T), session(T)
  + approved Structural Role authority effective at T
  + approved Score Projection V1 / CORE subset and importance
  + ObservationAsOfBinding(T, latest-approved, fresh, input-hash)
  + approved policy record and Eligibility Audit
      -> FormalTopicScoreAuthority validation
      -> Production V1 evaluator
      -> Breadth + Leadership
      -> Score = 0.60 * Breadth + 0.40 * final Leadership
      -> Grade S/A/B/D
      -> future immutable Score/Grade publication row
```

Recovered mechanics, without changing them:

- Same-session absolute return classification is `STRONG_POSITIVE >= 7%`,
  `POSITIVE >= 2%`, `NEUTRAL > -2%`, `NEGATIVE > -7%`, otherwise
  `STRONG_NEGATIVE`.
- Breadth uses valid observed `CORE` members, a minimum 60% CORE coverage, at
  least 3 valid observed CORE members, and the approved piecewise normalization
  from `[-1,+1]` to `[0,100]`.
- Leadership uses explicit Leader Set member importance in `1.00/0.75/0.50`,
  weighted normalized participation, and the bounded consensus modifier. If
  observed Leader weight coverage is below 50%, the modifier is zero and the
  quality flag is retained.
- The evaluator returns null Score/Grade for ineligible or unavailable
  components. Missing data is not converted into zero or `D`.

### Input readiness

| Input | Current classification | Evidence |
|---|---|---|
| Formal Topic Snapshot/member facts | `FORMAL_READY_AT_CONTRACT_LEVEL` | Migration 0030 and `topic_score_formal.py`; current/superseded/finality checks exist. |
| Structural Role / CORE | `FORMAL_AUTHORITY_PRESENT_RUNTIME_READBACK_UNPROVEN` | 1,160 approved artifact rows; role resolver is fail-closed; B2 records DB readback pending. |
| Score Projection / Leader Set | `POLICY_READY_DATA_MISSING` | D001 and migration 0031 exist; no populated projection rows were proven. |
| Observation as-of | `CONTRACT_READY_RUNTIME_BINDING_REQUIRED` | `ObservationAsOfBinding` requires exact date, session, latest-approved, fresh, count, input hash and timezone-aware bind time. |
| Eligibility Audit | `IMPLEMENTED_NOT_CONNECTED_TO_PROVIDER` | Runtime readiness requires complete topic coverage at one shared as-of. |
| Writer / persistence | `IMPLEMENTATION_MISSING` | Formal Score publication envelope explicitly says non-persistent; no production writer is registered. |
| Publication / API | `PUBLICATION_MISSING` | Current formal Topic fields remain nullable/deferred; no formal Score/Grade provider. |

The current Score blocker is therefore multiple causes: `D` missing writer,
`E` missing persistence/readback, `G` missing populated authority inputs, and
`H` their combination. It is not a missing formula.

## 6. Grade Policy Recovery

```text
GRADE_ENGINE_EXISTS=YES
GRADE_POLICY_EXISTS=YES
GRADE_POLICY_FORMALLY_APPROVED=YES_ARTIFACT_LEVEL
GRADE_POLICY_OWNER=topicpilot-owner
GRADE_POLICY_VERSION=topic-b2-layer2-policy-v1
```

The canonical Grade is the Grade emitted by the approved Production V1 Score
evaluator, not an unrelated historical label system:

| Grade | Score threshold | Missing / partial behavior |
|---|---:|---|
| `S` | `>= 80.0` | Only after eligible, sufficiently covered, fresh Score. |
| `A` | `>= 65.0` | Same. |
| `B` | `>= 50.0` | Same; Opportunity may treat it as exception only under its separate shadow semantic contract. |
| `D` | `< 50.0` | A failed eligibility gate returns null Grade, not a synthetic D. |

Coverage, minimum sample, and as-of behavior are inherited from Score's
Eligibility Audit. There is no separate Grade transition machine; a correction
or new as-of session re-evaluates the Score/Grade lineage. Grade is blocked by
Score publication and by the same authority/readback chain, not by a second
threshold decision.

## 7. Leader Set Recovery

```text
LEADER_SET_ENGINE_EXISTS=YES
LEADER_SET_DERIVED=YES
LEADER_SET_PERSISTED=SCHEMA_EXISTS_ROWS_NOT_PROVEN_POPULATED
LEADER_SET_FORMAL=POLICY_YES_DATA_NO
LEADER_SET_POLICY=APPROVED_D001_BOUNDED_CORE_SUBSET
LEADER_SET_AS_OF=EFFECTIVE_DATED_AND_VERSIONED
```

The recovered architecture is:

```text
Approved effective Structural Role CORE population
  -> approved, bounded CORE subset per Topic
  -> explicit importance 1.00 / 0.75 / 0.50
  -> Score Projection V1
  -> deterministic GovernedLeaderSet compatibility adapter
```

This is not equivalent to Structural Role, not a daily top-gainer list, not a
market-cap ranking, and not a runtime AI selector. The adapter cannot select
members or change importance. D001 is already approved; the remaining issue is
the absent exact per-topic projection artifact and runtime readback.

| Consumer | Required? | Recovered result |
|---|---|---|
| Score | `YES` | `ProductionTopicInput` requires explicit CORE IDs, leaders and matching version. |
| Grade | `YES, THROUGH SCORE` | Grade is emitted by the same evaluator. |
| Lifecycle | `NO` | Lifecycle is explicitly independent from Score/Grade and Leader Set; it may use formal role fields, not a Score Leader Set. |
| Formal Opportunity universe | `NO / NOT A GATE` | `leader_status=UNAVAILABLE_NOT_GATING`; no current formal universe rule makes Leader Set a hard gate. |
| Opportunity strategy cards | `NOT YET AUTHORIZED` | Any future leadership use requires a separate provider contract; shadow strategies cannot be promoted silently. |

## 8. CORE Semantic Recovery

The word `CORE` has several bounded uses and must not be collapsed:

| Concept | Definition | Authority | Human / derived | Persisted / formal | As-of | Consumers |
|---|---|---|---|---|---|---|
| `CORE-A` Structural Role CORE | One of `CORE`, `REPRESENTATIVE`, `RELATED` on an instrument-topic relation. | `structural-role-authority-20260912.v4` and `InstrumentTopicRelation`. | Human/formal; not algorithmically inferred. | Yes in artifact and additive DB columns; formal resolver exists. | Effective interval plus current/historical supersession. | Score population, Lifecycle role-aware evidence, Opportunity metadata. |
| `CORE-B` Score CORE input | The explicit `core_member_ids` used for one Score evaluation, resolved from approved effective CORE authority. | Score Projection V1 / `FormalTopicScoreAuthority`. | Derived projection from formal CORE, with Owner-approved member selection. | Intended persisted projection; current rows not proven populated. | Projection effective interval and Score snapshot date. | Score Breadth and Eligibility Audit. |
| `CORE-C` CORE V0 research concept | Candidate-formation/research policy in the separate CORE V0 workstream. | CORE V0 research documents. | Research/proposed. | Not a Topic Score authority. | Research-specific. | M2+ research only. |
| Display / legacy `core` tokens | UI or old labels such as `PRIMARY`, `LEADER`, or `CORE` in historical/shadow paths. | No authority unless bound to CORE-A. | Mixed / often derived. | Not formal by name alone. | Not safe to infer. | Must remain labelled and isolated. |

```text
WHICH_CORE_DOES_SCORE_REQUIRE=CORE-A resolved into CORE-B
WHICH_CORE_DOES_LIFECYCLE_REQUIRE=Formal role evidence if role-aware; not CORE-B and not Leader Set
WHICH_CORE_DOES_OPPORTUNITY_REQUIRE=No independent CORE gate in current formal universe boundary
CORE_SEMANTIC_COLLISION=YES_BUT_BOUNDED
```

The previous blocker was partly caused by treating “CORE authority missing” as
meaning “no CORE policy exists”. The precise current statement is: CORE policy
and approved source artifact exist, but the runtime projection/readback chain is
not proven complete.

## 9. As-Of Authority Recovery

### State table

| State | Effective date | As-of date / cutoff | Publication date | Lookback / D-1 | D+1 | Late publication / correction |
|---|---|---|---|---|---|---|
| Daily Close | Provider/session close | Accepted `DAILY_BAR` session date | After final close materialization | Previous session only when an explicit consumer asks; absent evidence stays unavailable | `NO` | Late source stays unavailable until accepted; correction creates a new immutable lineage. |
| Daily Strength | B2 effective `2026-09-15` | Current approved session, but standalone level/history parameters are not complete | Not active | Not formally defined beyond verified components | `NO` | Fail closed; never fill unresolved parameters with zero/default. |
| Score | Policy effective `2026-09-15`; formal PIT boundary `2026-08-07` | Snapshot date and `ObservationAsOfBinding.as_of` must match exact session | Future writer must publish after evaluation | No implicit prior-day substitution for the same-session Score input | `NO` | Recompute against corrected successor snapshot; superseded result is not current. |
| Grade | Inherited from Score policy | Same Score as-of and session | Inherited from Score publication | No separate D-1 policy | `NO` | Same Score correction/supersession lineage. |
| Structural Role | Artifact effective `2026-08-24` | `effective_from <= as_of <= effective_to`; current/historical mode explicit | Artifact/database publication separate | No future relation allowed | `NO` | Use approved successor in CURRENT mode; retain historical effective row in HISTORICAL mode. |
| Score Projection / Leader Set | Projection effective interval | Projection and source role version must be effective at Score as-of | Future writer only | No daily re-selection | `NO` | New approved projection supersedes old; adapter cannot mutate it. |
| Lifecycle | Formal publisher start `2026-08-24` | Snapshot date, exact member facts and prior formal state chain | Formal result row after gate | Prior published formal state only; first eligible date uses explicit BASE bootstrap | `NO` | Re-run affected date/state chain and append a superseding result. |
| Topic Snapshot | Formal boundary `2026-08-07` | `snapshot_date`, `PIT_FORMAL`, `FINAL`, `PUBLISHED`, non-superseded | `published_at` after materialization | Membership is effective at snapshot date | `NO` | Correction increments sequence and links `supersedes_snapshot_id`. |
| Formal Opportunity | Request `asOf` | Topic, eligibility, relations, prices, Lifecycle/Selector nested payloads must match the page as-of | Provider publication only after all formal checks | OHLCV evidence is filtered `<= as_of`; missing history becomes `DEFERRED/UNAVAILABLE` | `NO` | Late/corrected upstream facts require new provider output; stale cards are not retained as current. |

### Canonical temporal dependency diagram

```text
Approved DAILY_BAR at session T
  -> Topic Snapshot(T): PIT_FORMAL + FINAL + PUBLISHED + current correction
      + member facts(T)
      + Structural Role authority effective at T
      + Score Projection effective at T
      + ObservationAsOfBinding(T, session, fresh, input-hash)
          -> Score(T)
          -> Grade(T)

Topic Snapshot(T) + exact member/price evidence(T)
  + prior PUBLISHED formal Lifecycle state before T
  + approved Lifecycle transition authority
      -> Lifecycle(T)

Topic(T) + approved eligibility(T) + effective relations(T)
  + exact prices/technical evidence <= T
  + formal Score/Grade/Lifecycle where the approved provider contract consumes them
  + dedupe/provenance/C1-C5/S1-S2/FUND-C boundary
      -> Formal Opportunity(T)
```

No node may read `T+1` to publish `T`. D-1 is only an explicit prior-session
input (for example, a technical comparison or prior formal state); if it is
missing, the result is unavailable/deferred rather than zero or inferred.

## 10. Lifecycle V1.3 Recovery

```text
LIFECYCLE_ENGINE_EXISTS=YES
LIFECYCLE_POLICY_EXISTS=YES
LIFECYCLE_POLICY_APPROVED=STAGE_AND_INDEPENDENCE_APPROVED;TRANSITION_PARTIAL
LIFECYCLE_FORMAL_GATE=YES
LIFECYCLE_WRITER=YES_FORMAL_LIFECYCLE_PUBLISHER
LIFECYCLE_PERSISTENCE=YES_MIGRATION_0037_FORMAL_RESULTS
LIFECYCLE_READER=YES_READ_FORMAL_LIFECYCLE
LIFECYCLE_PUBLICATION=BLOCKED_NOT_CONNECTED_TO_POST_CLOSE
```

Recovered stages are exactly `SPROUTING`, `FERMENTING`, `MAIN_RISE`, `MATURE`,
and `DECLINING`. The formal adapter preserves V1.3 state memory, confirmation,
illegal backward-transition hold, `FERMENTING -> BASE` failure handling, and
`MATURE -> MAIN_RISE` re-entry behavior. It does not read shadow rows.

The current `LifecyclePolicy` numeric values include coverage/sample gates,
positive/strong/weak breadth boundaries, drawdown and structural-breakdown
conditions, confirmation days, and state-memory persistence. Historical reports
explicitly label the numeric policy `PROVISIONAL_TUNABLE`; B2 therefore records
Lifecycle stage identity as `APPROVED` but transition status as
`PARTIAL_BY_DESIGN` with `transitionPolicyRef=null`.

| Prerequisite | Result | Why |
|---|---|---|
| Formal Topic Snapshot with exact facts | `READY_BY_CONTRACT / DATA_READBACK_REQUIRED` | Formal gate checks COMPLETE data, observed counts, role fields and lineage. |
| Previous formal state / bootstrap | `IMPLEMENTED` | Formal publisher resolves prior published state or explicit BASE bootstrap. |
| Stage ontology | `READY` | B2 and product contract agree on five stages. |
| Transition numeric authority | `MISSING_AUTHORITY` | Existing implementation is provisional; no approved transition artifact/ref. |
| Formal correction lineage | `IMPLEMENTED_SCHEMA / WRITER_READBACK_REQUIRED` | Formal ORM carries snapshot identity, lineage, correction and supersession fields. |
| Post-close wiring | `DISCONNECTED` | Current post-close invokes `TopicLifecycleEngine` shadow path. |

```text
LIFECYCLE_BLOCKERS_AFTER_SCORE_GRADE=
  TRANSITION_POLICY_AUTHORITY_PARTIAL_BY_DESIGN;
  FORMAL_SNAPSHOT_AND_MEMBER_FACT_READBACK;
  FORMAL_WRITER_NOT_WIRED_TO_POST_CLOSE;
  CORRECTION_CHAIN_READBACK_NOT_RECERTIFIED
```

Lifecycle is not blocked only because Score/Grade is unavailable. The B2
contract explicitly says it is independent from both; it has its own policy and
lineage gates.

## 11. Formal Opportunity Authority Recovery

### Dependency state

| Dependency | Current classification | Recovered fact |
|---|---|---|
| Formal Topic Universe | `READY_BY_CONTRACT` | Full expected Topic set, leaf scope, formal publication and as-of checks exist. |
| Topic eligibility | `AUTHORITY_MISSING_FOR_PROVIDER` | Consumer requires one same-as-of eligibility row per Topic; provider is not configured. |
| Approved members / dedupe / multi-Topic provenance | `READY_BY_CONTRACT` | Approved effective relations are grouped by instrument, retaining all Topic relation IDs/types. |
| Structural Role / CORE | `NOT_REQUIRED_AS_HARD_GATE` | Roles are carried as metadata; formal universe does not infer or require a Leader Set. |
| Score / Grade | `BLOCKED_BY_SCORE_PUBLICATION` | Current formal Qualification semantics consume Grade, but no formal Score/Grade provider exists. |
| Lifecycle | `BLOCKED_BY_LIFECYCLE_PUBLICATION` | Page validation accepts only same-as-of formal Lifecycle or explicit unavailable. |
| Strategy / Selector | `IMPLEMENTED_SHADOW_ONLY` | Trend/Catch-up strategy and Selector shapes exist, but production provider/policy promotion is absent. |
| C1-C5 / S1-S2 | `FROZEN_BOUNDARY_NOT_EXECUTED` | Preserve the existing semantics; current formal universe does not execute them. |
| FUND-C | `EVIDENCE_ONLY_NOT_CONSUMED` | It is not ranking and not gating. |
| Formal writer / persistence | `IMPLEMENTATION_MISSING` | No canonical Opportunity publication writer/read model population is present. |
| Formal provider / API | `PROVIDER_INACTIVE` | `CanonicalOpportunityProvider` raises `FormalOpportunityProviderUnavailable`; API returns 503. |
| No D+1 / stale protection / ZERO vs UNAVAILABLE | `READY_BY_CONTRACT` | Formal contracts distinguish state and require exact as-of; no fallback to shadow/fixture. |

```text
OPPORTUNITY_BLOCKERS_AFTER_LIFECYCLE=
  FORMAL_PROVIDER_POLICY_AND_EFFECTIVE_DATE;
  FORMAL_SCORE/GRADE/LIFECYCLE_UPSTREAM_READBACK;
  OPPORTUNITY_WRITER/PERSISTENCE;
  FORMAL_API_PROVIDER_WIRING;
  CANONICAL_FRESHNESS_AND_OPERATOR_READBACK
```

The existing Opportunity qualification policy is intentionally
`COMMITTED / SHADOW ONLY`: S/A formal universe, B exception provenance, D and
Declining exclusions, `Close >= 20MA`, risk-before-ranking, independent A/B
ranking, post-close cadence, Top 3/Top 2 caps are the recovered semantic
boundary. Numeric thresholds, weights, support/risk details, validity and
transition parameters remain provisional. Promoting the shadow policy is a
real Owner product decision, not an implementation detail.

## 12. Technical Bottleneck Inventory

| ID | Component | Description | Severity | Blocks M1 | Root cause | Engineering can resolve without Owner | Owner decision required | Recommended approach | Alternative / trade-off | Migration | Production risk | Dependencies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-01 | Role authority readback | Artifact rows are approved, but formal DB readback for 1,160 roles / 107 leaves / 25 parents is not proven. | Critical | Yes | Materialization/readback gate remains pending. | Yes, once using the approved artifact only. | No new role semantics; Owner supplies no new policy. | Controlled idempotent ingestion/readback with counts, hashes, current/historical resolver checks. | Read artifact-only; does not prove runtime. | Existing 0031; production migration/readback separately authorized. | Wrong or partial role population could change Score/Lifecycle. | AUTH-ROLE-V4, DB/operator access. |
| T-02 | Score Projection | No per-topic approved projection/member rows are proven populated. | Critical | Yes | D001 policy exists, exact content/artifact binding does not. | Partly; engineering can load only an Owner-approved artifact. | Yes for exact member/importance artifact (DEC-01). | Use `TopicScoreProjection` and fail-closed resolver; no runtime selector. | All CORE or daily selector are not compatible with D001 without new policy. | Existing 0031. | Silent member drift would invalidate Score lineage. | DEC-01, AUTH-ROLE-V4. |
| T-03 | Score/Grade writer | `topic_score_formal.py` derives a non-persistent envelope; no formal writer/API publication. | Critical | Yes | Implementation deliberately stopped before activation. | Yes. | No after DEC-01 and approval record are bound. | Append-only derived publication keyed by snapshot/projection/policy/as-of; explicit supersession/readback. | On-read derivation is simpler but weakens operator readback and correction audit. | Likely additive migration/read model; confirm in implementation task. | Duplicate or stale Score/Grade publication. | T-01/T-02, observation binding, Eligibility Audit. |
| T-04 | Lifecycle activation lane | Post-close calls shadow `TopicLifecycleEngine`, not `FormalLifecyclePublisher`. | Critical | Yes | Formal lane was implemented separately and kept gated. | Yes after transition authority is supplied. | DEC-02 for transition policy only. | Wire formal publisher behind existing snapshot gate; preserve shadow as separate. | Keep shadow only; M1 remains blocked. | Existing 0037/0039. | Shadow-to-formal contamination or broken state chain. | DEC-02, formal snapshot readback. |
| T-05 | Lifecycle lineage/readback | Formal result needs exact input snapshot identity, member facts, prior state and correction sequence. | High | Yes | Historical contract gaps remain in writer/readback certification. | Yes. | No additional product decision if DEC-02 fixes transition authority. | Verify lineage hash, append-only supersession, prior-state ordering and 107-leaf coverage. | Recompute on read; less durable audit. | Existing schema; no new policy. | Incorrect state on correction/late data. | T-04, Topic Snapshot. |
| T-06 | Opportunity provider | Formal API seam has no canonical provider and returns 503. | Critical | Yes | Formal provider/effective date/owner authority absent. | No, not without DEC-03. | Yes (DEC-03). | Implement only the selected formal provider contract; reject shadow/fixture payloads. | Keep 503 fail-closed; safe but not M1-complete. | Unknown until provider design; avoid migration before authority. | Publishing provisional recommendations. | Score/Grade/Lifecycle readback, DEC-03. |
| T-07 | Post-close checkpoint/resume | New formal lanes must be idempotent and independently retryable without discarding Topic/Home success. | High | Yes | Existing post-close has separate gates but no completed Score/Grade/Opportunity stages. | Yes. | No. | Stage checkpoints by as-of, policy/projection version and lineage; commit each bounded lane atomically. | One large transaction; simpler but increases rollback blast radius. | Maybe none; use existing run/checkpoint patterns. | Duplicate rows or partial formal publication. | T-03/T-04/T-06. |
| T-08 | Operator / DB readback | Production verification, migration state and complete formal cardinality are not certified in this task. | High | Yes | No DB/Production mutation or access was authorized. | Only read-only checks in next task; Production proof needs operator gate. | No policy decision; external technical gate. | Re-run bounded readback queries and attach exact hashes/counts before activation. | Treat artifact status as runtime truth; unsafe and prohibited. | Existing migrations only. | False readiness claim. | Operator access, protected deployment boundary. |
| T-09 | Readiness / observability | Current statuses need explicit distinction between policy-approved, publication-blocked and activation-not-active across lanes. | Medium | Yes | B2 metadata exists, but end-to-end readiness surface is not wired. | Yes. | No. | Preserve stable machine states and reason codes in post-close/read APIs; never collapse unavailable into zero. | Boolean ready flag; loses gate cause. | Usually none. | Operators may activate wrong lane. | All formal lanes. |

## 13. Undesigned / Partially Designed Capabilities

| Capability | Status | What exists | What is missing | Why it matters | Engineering without Owner? | Recommended direction |
|---|---|---|---|---|---|---|
| Score | `APPROVED_NOT_IMPLEMENTED_AS_PUBLICATION` | Exact evaluator, authority contract, resolver infrastructure. | Populated projection, writer, persistence/readback, provider gate. | Score is upstream of Grade and formal Opportunity. | Yes after DEC-01. | Implement the approved evaluator as a fail-closed formal writer; do not change formula. |
| Grade | `APPROVED_NOT_CONNECTED` | Exact S/A/B/D thresholds in approved record. | Score publication and same lineage/readback. | Grade must not be recomputed by UI or Opportunity. | Yes. | Publish only as Score-derived output. |
| Leader Set | `POLICY_APPROVED_DATA_ABSENT` | D001, projection schema, adapter and resolver. | Exact per-topic selected CORE members/importance and readback. | Score leadership cannot be authoritative without it. | Only ingestion after Owner artifact. | DEC-01, then deterministic adapter. |
| CORE | `FORMAL_SOURCE_PRESENT_RUNTIME_CHAIN_PARTIAL` | Structural Role artifact and resolver. | Verified runtime population and Score projection binding. | Prevents semantic collision and invalid denominator. | Yes after approved artifact. | Keep CORE-A human authority; derive CORE-B only through D001 projection. |
| as-of semantics | `CONTRACT_READY_RUNTIME_CHAIN_PARTIAL` | PIT boundary, effective intervals, session binding, correction fields. | End-to-end writer/readback and operator proof. | Prevents look-ahead and stale publication. | Yes. | One shared `topic_id + as_of + session + lineage` identity. |
| Lifecycle | `IMPLEMENTED_NOT_FULLY_APPROVED/CONNECTED` | V1.3 formal evaluator, publisher, ORM/migrations, stage ontology. | Transition authority ref, formal post-close wiring, replay/readback proof. | Independent blocker remains after Score/Grade. | Wiring yes; policy ref no. | DEC-02 then formal publisher only. |
| Formal Opportunity | `DESIGNED_BOUNDARY_PROVIDER_INACTIVE` | Formal universe and page validation, shadow semantic matrix. | Formal provider authority, effective date, writer/persistence, upstream readback. | M1 cannot claim formal Opportunity publication. | Only after DEC-03. | Keep shadow and formal lanes separate; no fixture fallback. |
| Formal publication | `PARTIALLY_DESIGNED` | B2 state taxonomy and fail-closed guards. | Complete Score/Grade/Lifecycle/Opportunity writers and readback. | Policy approval is not activation. | Yes by lane. | Treat `POLICY_APPROVED`, `PUBLICATION_BLOCKED`, `NOT_ACTIVE` as separate states. |
| Readiness semantics | `DESIGNED_PARTIAL` | Runtime blockers and B2 metadata. | Unified post-close reason/readback projection. | Operator must know the exact gate. | Yes. | Stable machine reason codes; preserve ZERO vs UNAVAILABLE. |
| Scheduler dependencies | `IMPLEMENTED_BASELINE / FORMAL LANES NOT WIRED` | Post-close orchestration and retry patterns. | Formal lane checkpoints and activation gate. | Prevents partial daily state. | Yes after authority artifacts. | One post-close run with independent, idempotent bounded stages. |

## 14. Recovered Policy Table

| Policy | Authority | Version | Source | Status | Current consumer | Canonical? | Action needed |
|---|---|---|---|---|---|---|---|
| Formal Topic authority / PIT boundary | Owner-authorized topic artifact | `topic-authority-activation.v1` | `config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json` | Formal active at contract level | Topic Snapshot, Lifecycle, Opportunity | Yes | Runtime readback only. |
| Structural Role | Owner-reviewed role artifact | `topic-structural-role-authority.v1` / V4 | `config/topic_structural_role_authority/...v4.json` | Approved artifact; runtime disconnected | Score, Lifecycle, Opportunity metadata | Yes | Populate/read back; do not infer. |
| Score mechanics | 003F / B2 policy record | `topic-b2-layer2-policy-v1` | `score-grade-policy-approval-record.json` | Approved | Production V1 evaluator | Yes | No re-approval; bind to writer. |
| Grade thresholds | Same Score policy | `...#grade`, S/A/B/D | B2 approval record and `production_policy.py` | Approved | Score evaluator / Opportunity semantic consumer | Yes | No threshold redesign. |
| Score Projection / Leader Set direction | `WS1-P2B-D001` | D001 | Architecture Addendum G and D001 report | Approved and canonicalized | Projection adapter | Yes | Exact artifact still required. |
| CORE meaning | Structural Role CORE -> Score CORE input projection | D001 / role V4 | Role artifact, D001, formal score contract | Recovered | Score, Lifecycle role evidence | Yes with bounded collision | Keep CORE V0 separate. |
| Score as-of / correction | Formal PIT contract | `topic-score-formal.v1` | `topic_score_formal.py`, Topic Snapshot | Approved contract | Score/Grade writer | Yes | End-to-end readback. |
| Lifecycle stage ontology | B2 Layer 2 and V1.3 product contract | `topic-lifecycle-v1.3-formal.v2` | B2 contract, lifecycle modules | Approved | Formal Lifecycle | Yes | Preserve stages. |
| Lifecycle transition parameters | Historical V1.3 implementation | `topic-lifecycle-policy.v1` | `topic_lifecycle_v1.py`, calibration report | Provisional / partial | Shadow and formal evaluator code | No formal activation yet | DEC-02. |
| Opportunity semantic matrix | BE-024B PM semantic freeze | `opportunity-qualification.v1.shadow` | Opportunity decision/spec/report | Shadow only; parameters provisional | Shadow strategies | No formal Production authority | DEC-03 if formal promotion is required. |
| C1-C5 / S1-S2 | Frozen existing boundary | Existing versions | User-frozen rules and Opportunity docs | Preserve / not executed by formal universe | Future provider | Boundary yes; execution not proven | Do not tune in M1 recovery. |
| FUND-C V1 | Evidence-only | Existing V1 | FUND-C reports and Opportunity contract | Evidence only | Diagnostics, not ranking/gating | Yes as non-gating boundary | No promotion. |
| ZERO vs UNAVAILABLE / no D+1 | Formal availability contract | Current formal contracts | Topic state, universe, Opportunity API | Approved | All formal readers | Yes | Test in activation task. |

These rows are excluded from the Owner decision table where the contract is
already sufficient. The Owner is not asked to re-decide Score weights, Grade
thresholds, D001, CORE role taxonomy, C1-C5, S1-S2, FUND-C non-gating, or no
D+1 semantics.

## 15. OWNER DECISION POLICY TABLE

Only the following three issues still require Owner/PM authority. D001 itself is
not reopened; DEC-01 requests the missing concrete artifact that D001 already
requires.

| ID | Component | Decision Class | Current State | Exact Missing Decision | Why It Matters | Option A | Option B | Option C | Engineering Recommendation | Recommendation Rationale | Consequence If A | Consequence If B | Consequence If C | Blocks M1? | Owner Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-01 | Score Projection / Leader Set | D2 — Owner policy confirmation | D001 approved bounded CORE subset, but no exact per-topic member/importance artifact is bound to runtime. | Confirm the concrete versioned artifact: topic, selected CORE member IDs, importance, effective interval, source role authority, approval reference and lineage. | Without it, Score leadership and CORE coverage cannot be authoritative. | Preserve D001: approve a bounded CORE subset per Topic with `1.00/0.75/0.50`; no fixed Top-N; no runtime AI. | Approve all effective CORE as the Score projection, which changes D001 and requires a new policy version. | Keep Score/Grade fail-closed until a concrete artifact is supplied. | A | It executes the already recovered policy and avoids silently changing semantics. | Enables deterministic adapter, Score and Grade implementation. | M1 remains blocked; no data risk. | M1 remains blocked and D001 is reopened later. | Yes | PENDING |
| DEC-02 | Lifecycle V1.3 transition authority | D2 — Owner policy confirmation | Five stages and formal evaluator exist; B2 says transition `PARTIAL_BY_DESIGN`; current numeric policy is provisional. | Decide whether the exact existing `topic-lifecycle-policy.v1` parameter set may be formalized for V1.3, or must remain shadow/calibration-only. | Lifecycle is independent of Score/Grade; approving Score alone will not close this gate. | Approve the existing version/parameters unchanged as formal V1.3 transition authority, with artifact hash/effective date. | Preserve shadow/fail-closed Lifecycle until history replay and a future approved version. | Approve only stage ontology; keep transitions unavailable, which is not M1-complete. | A for an M1 completion path; B if the Owner does not accept provisional numeric authority. | A does not invent or tune values, but it requires an explicit Owner promotion of the already existing bundle. | Formal publisher can run with exact state/correction lineage. | Lifecycle stays unavailable; M1 stays blocked safely. | Formal stage labels exist but no usable formal state; M1 stays blocked. | Yes | PENDING |
| DEC-03 | Formal Opportunity provider/policy | D3 — Owner product policy design | Formal page contract and universe boundary exist; qualification engine is `COMMITTED / SHADOW ONLY`, provider is 503. | Decide whether Formal Opportunity may publish production-backed strategy/selector outputs, and identify the exact approved policy version/effective date/provider scope. | It determines whether shadow Opportunity semantics may ever become formal authority. | Authorize a new explicit formal Opportunity authority package derived from the frozen semantic matrix, with provider, effective date, parameter status and gates. | Preserve `SHADOW ONLY` and keep formal provider unavailable until replay/calibration and a later policy package. | Limit M1 to formal Topic/eligibility universe only and defer strategy cards/provider activation beyond M1. | B unless the Owner explicitly wants Formal Opportunity included in M1; if included, A is the only safe route. | Existing docs expressly prohibit silent promotion of provisional thresholds and fixtures. | After DEC-03A, engineering can build the canonical provider and readback lane. | Safe 503/shadow boundary; M1 cannot claim formal Opportunity. | Requires a roadmap/M1 boundary change; no false publication. | Yes under the current M1 definition | PENDING |

## 16. Technical Design Recommendation Table

| ID | Component | Technical Problem | Existing Architecture | Recommended Design | Alternative | Why Recommended | Migration? | Deployment Risk | Blocks M1? |
|---|---|---|---|---|---|---|---|---|---|
| TD-01 | Role ingestion | Approved artifact is not proven in runtime readback. | Effective-dated relation authority and fail-closed resolver. | Idempotent artifact-driven ingestion with cardinality/hash/readback report; no inference. | Read artifact directly in memory. | Proves the same authority is used by production consumers. | Use existing 0031; production migration/readback separately gated. | Medium; incorrect binding affects all downstream lanes. | Yes |
| TD-02 | Score Projection | Resolver exists but no populated rows. | `TopicScoreProjection` + member rows + D001 adapter. | Load only DEC-01-approved rows, validate source role version, importance, interval, supersession and lineage. | Keep all projection data external. | Reuses fail-closed resolver and gives operator-visible provenance. | Existing 0031. | Medium. | Yes |
| TD-03 | Score/Grade publication | Non-persistent formal envelope cannot support readback. | `FormalTopicScorePublication` is non-persistent; Topic snapshot has nullable fields. | Add an append-only formal derived result/read model keyed by snapshot identity, policy/projection version and as-of; update current view only through supersession. | Deterministic on-read derivation from Snapshot. | Stable audit and correction behavior are required by downstream Lifecycle/Opportunity. | Likely additive; finalize in implementation task after schema check. | High if writer is not idempotent. | Yes |
| TD-04 | Eligibility Audit | Complete topic coverage is required but not wired to provider. | Runtime readiness has complete-universe audit. | Run one shared `topic_id + as_of` audit before Score provider activation; publish machine reason codes. | Per-topic lazy readiness. | Prevents partial universe being represented as formal complete. | None expected. | Medium. | Yes |
| TD-05 | Lifecycle | Formal publisher exists but post-close calls shadow engine. | Formal publisher + migration 0037/0039; shadow engine remains separate. | Wire formal publisher after snapshot gate and DEC-02; leave shadow rows labelled and isolated. | Keep shadow path only. | Preserves the formal/shadow boundary and existing fail-closed behavior. | Existing migrations. | High if rollback/supersession is bypassed. | Yes |
| TD-06 | Opportunity | Provider is deliberately unavailable. | Formal page validator and formal universe consumer; shadow provider separate. | Implement canonical provider only after DEC-03; reject shadow/fixture/research payloads; require same-as-of nested data. | Keep 503 and publish only formal universe boundary. | Prevents provisional recommendation leakage. | Unknown; do not pre-create schema from shadow assumptions. | High. | Yes |
| TD-07 | Post-close execution | Multiple formal stages need restart safety. | Existing post-close transaction/retry patterns. | Add stage checkpoints keyed by as-of and authority versions; commit lane-by-lane and preserve successful Topic/Home stages. | One transaction for all stages. | Smaller recovery blast radius and clearer operator replay. | Usually none. | Medium. | Yes |
| TD-08 | Readback / operator gate | Artifact readiness is being confused with runtime readiness. | B2 metadata and historical readback reports. | Require exact DB counts, hashes, current/historical resolver checks, API state and scheduler evidence before activation. | Trust committed artifacts as runtime truth. | Prevents false M1 completion. | No. | High if skipped. | Yes |
| TD-09 | Readiness surface | Boolean readiness hides policy/publication/activation distinction. | B2 has `POLICY_APPROVED`, `BLOCKED`, `NOT_ACTIVE`. | Preserve structured lane statuses and reason codes in post-close and API diagnostics. | Single `ready=false`. | Gives Owner/operator the exact next action. | No. | Low. | Yes |

## 17. Deferred / Future Design Table

| Item | Current gap | Target milestone | Why deferred | Dependency |
|---|---|---|---|---|
| Global Topic Ranking | No formal universe, metric, tie-break or replay authority. | M2 | Not consumed by current Score/Grade/Lifecycle closure; do not confuse with Opportunity strategy-local ranking. | Separate Owner policy decision. |
| Topic Concentration | No formal contribution/denominator/null policy. | M2 | Not a prerequisite for recovered Score/Grade mechanics. | Separate Owner policy decision. |
| Opportunity calibration / numeric tuning | Provisional thresholds, weights, validity and transition parameters. | M2 | Requires canonical production history and PM review; no fake calibration. | DEC-03 and point-in-time replay data. |
| CORE V0 research promotion | Separate research candidate-formation policy. | M3 | Must not be used as Topic Score CORE-A/CORE-B authority. | WS3/CORE V0 authority and outcome provenance. |

No deferred item is being placed on the M1 critical path. M1 still remains
blocked by the explicit decisions and technical gates above.

## 18. Critical Path After Owner Decisions

Assuming `DEC-01=A`, `DEC-02=A`, and a formal Opportunity decision that supplies
an explicit authority package, the shortest governed continuation is:

```text
Owner decisions
  -> register exact projection / Lifecycle / Opportunity authority artifacts and hashes
  -> read back approved Structural Role rows and Score Projection rows
  -> bind ObservationAsOfBinding and complete Eligibility Audit
  -> Score writer and immutable Score/Grade readback
  -> formal Lifecycle replay/publisher/readback from A9 formal snapshot start
  -> formal Opportunity provider/universe/strategy readback under DEC-03
  -> post-close checkpoint/resume/idempotency proof
  -> operator/API/scheduler readback
  -> M1 acceptance; M2 remains unopened
```

| Step | Inputs | Authority | Implementation | Persistence | Validation | Production action |
|---|---|---|---|---|---|---|
| 1. Authority registration | DEC-01/02/03 selections | Owner artifacts and B2 record | Governance-only registration | Artifact registry | Hash/schema/lineage checks | None. |
| 2. Role/projection readback | V4 role artifact, D001 projection | Effective role/projection versions | Existing 0031 resolvers/adapter | Relation/projection rows | 1,160 roles, 107 leaves, 25 parents, per-topic projection, current/historical tests | Controlled readback only. |
| 3. Score/Grade | Topic Snapshot/member facts, as-of binding, Eligibility Audit | B2 Score/Grade approval | Existing evaluator + new writer | Append-only derived result | Formula/lineage/null/supersession/API checks | No public activation until gate passes. |
| 4. Lifecycle | Formal snapshots/facts, prior formal state, DEC-02 | Lifecycle transition artifact | FormalLifecyclePublisher wired into post-close | Existing formal result table | 107-leaf coverage, correction replay, no shadow contamination | Controlled formal replay/readback. |
| 5. Opportunity | Topic/Score/Grade/Lifecycle/relations/prices, DEC-03 | Formal Opportunity package | Canonical provider and formal page validator | Provider/read model as authorized | Same-as-of, dedupe, C1-C5/S1-S2, FUND-C non-gating, 503 on missing | Only after operator gate. |
| 6. Operational proof | All previous stage identities | Release/operator gates | Checkpoint/resume and readiness surface | Run/checkpoint evidence | Retry/idempotency, stale/no-look-ahead, API/scheduler proof | M1 acceptance only; no automatic M2. |

Steps 1–5 can be one subsequent governed implementation task only if the Owner
supplies all three decisions and the task explicitly allows the required schema,
readback and provider surfaces. If DEC-03 remains B, the same task may complete
Score/Grade/Lifecycle technical closure but must leave Formal Opportunity at
503/shadow and therefore cannot mark current M1 complete.

## 19. Implementation-Ready Policy Skeletons

These are deliberately incomplete at the decision field. They preserve the
recovered policy without filling an Owner choice.

### DEC-01 — Score Projection V1 concrete artifact

```text
POLICY_ID: TOPIC_SCORE_PROJECTION_V1
POLICY_OWNER: topicpilot-owner
POLICY_VERSION: PENDING_ARTIFACT_VERSION
STATUS: PENDING_OWNER_DECISION

INPUTS:
  approved effective Structural Role CORE rows
  topic_id and as_of interval
  source authority id/version/hash
  selected CORE member ids and score importance
OUTPUTS:
  one approved Score Projection V1 row per Topic/projection interval
  deterministic GovernedLeaderSet compatibility view
AS_OF: effective_from <= score_as_of <= effective_to; no future selection
MISSING_DATA_BEHAVIOR: UNAVAILABLE_FAIL_CLOSED
PARTIAL_DATA_BEHAVIOR: no projection publication; do not auto-complete from all CORE
FORMAL_GATE: approval_state=APPROVED; source role version matches; lineage/supersession valid
PERSISTENCE: TopicScoreProjection + members; append-only correction identity
CONSUMERS: Score, Grade through Score, formal audit
AUDIT_FIELDS: approval reference, role authority id/version/hash, lineage hash, correction sequence

OWNER_SELECTION_REQUIRED:
  Confirm the exact per-topic bounded CORE subset and importance values under D001,
  or explicitly choose not to provide it yet.

OPTIONS:
  A: Preserve D001 bounded CORE subset, Owner-approved, versioned and effective-dated.
  B: Approve all effective CORE; requires a new policy version and reopens D001.
  C: Keep Score/Grade fail-closed until a concrete artifact exists.

RECOMMENDED: A
```

### DEC-02 — Lifecycle V1.3 transition authority

```text
POLICY_ID: TOPIC_LIFECYCLE_V1_3_TRANSITION
POLICY_OWNER: topicpilot-owner
POLICY_VERSION: topic-lifecycle-policy.v1 or new Owner-selected version
STATUS: PENDING_OWNER_DECISION

INPUTS: formal Topic Snapshot(T), member facts(T), prior formal state, role evidence, price/change evidence
OUTPUTS: one formal Lifecycle result or explicit UNAVAILABLE/HOLD result per topic/date
AS_OF: evaluation_date equals formal snapshot_date; prior state must be earlier published date
MISSING_DATA_BEHAVIOR: UNAVAILABLE / HOLD_FORMAL_GATE
PARTIAL_DATA_BEHAVIOR: no current stage publication; never use shadow result
FORMAL_GATE: approved transition policy ref + exact input snapshot lineage + no superseded input
PERSISTENCE: TopicLifecycleFormalResult append-only with correction/supersession
CONSUMERS: formal Topic readers and Formal Opportunity when available
AUDIT_FIELDS: policy version, calculation version, transition reason, prior state, snapshot lineage, correction sequence

OWNER_SELECTION_REQUIRED:
  May the exact existing topic-lifecycle-policy.v1 parameter set be promoted as
  formal V1.3 transition authority without numeric changes?

OPTIONS:
  A: Approve existing parameter bundle unchanged with artifact hash/effective date.
  B: Keep shadow/fail-closed until replay/calibration produces a later approved version.
  C: Approve stage ontology only; keep transitions unavailable.

RECOMMENDED: A for M1; B if Owner does not authorize the existing provisional numeric bundle.
```

### DEC-03 — Formal Opportunity authority package

```text
POLICY_ID: TOPIC_FORMAL_OPPORTUNITY_V1
POLICY_OWNER: Product / Release Owner with formal-data authority
POLICY_VERSION: PENDING_OWNER_AUTHORITY_PACKAGE
STATUS: PENDING_OWNER_DECISION

INPUTS: formal Topic universe(T), exact Topic eligibility(T), approved members/relations(T),
        formal Score/Grade/Lifecycle where consumed, canonical prices/OHLCV <= T
OUTPUTS: formal Opportunity page/detail or explicit ZERO/UNAVAILABLE/DEFERRED state
AS_OF: page as_of binds every nested Topic, member, Lifecycle, Selector and technical field
MISSING_DATA_BEHAVIOR: UNAVAILABLE or DEFERRED; never shadow/fixture fallback
PARTIAL_DATA_BEHAVIOR: no partial formal cards; retain reason codes
FORMAL_GATE: approved provider/policy/effective date, same-as-of payload, C1-C5/S1-S2 preserved,
             FUND-C evidence-only and non-gating
PERSISTENCE: provider/read model as authorized; deterministic dedupe and multi-Topic provenance
CONSUMERS: Formal Opportunity API; no browser business logic
AUDIT_FIELDS: policy/parameter versions, source hashes, as_of, freshness, relation ids, status/reasons

OWNER_SELECTION_REQUIRED:
  Decide whether the current shadow semantic freeze may become a formal provider
  authority, or whether Formal Opportunity remains unavailable/shadow-only.

OPTIONS:
  A: Issue a new explicit formal authority package and effective date.
  B: Preserve shadow-only semantics and keep canonical provider unavailable.
  C: Limit M1 to formal Topic/eligibility universe and defer strategy cards/provider.

RECOMMENDED: B by default; A only if the Owner explicitly requires Formal Opportunity in M1.
```

## 20. Exact Next Task Recommendation

Recommended next task name:

```text
TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002
```

Exact objective: after Owner supplies DEC-01/02/03 outcomes, implement only the
approved authority-to-runtime chain in an isolated worktree: register hashes,
populate/read back approved role and projection data, publish Score/Grade with
immutable lineage, wire formal Lifecycle (never shadow promotion), and wire
Formal Opportunity only if DEC-03 authorizes it. Include checkpoint/resume,
idempotency, same-as-of validation, correction/supersession and operator
readback. Do not start M2, tune C1-C5/S1-S2, calibrate provisional parameters,
use fixtures as formal data, or mutate Production until the separate release
gate authorizes it.

Validation boundary for this recovery task:

```text
APPLICATION_CODE_CHANGED=NO
SCHEMA_OR_MIGRATION_CHANGED=NO
DATABASE_MUTATION=NO
PRODUCTION_MUTATION=NO
OWNER_CHECKOUT_MODIFIED=NO
M2_STARTED=NO
```

Machine closeout:

```text
TASK_STATUS=COMPLETE_FOR_RECOVERY_REPORT;M1_BLOCKED
M1_COMPLETE=NO
M2_STARTED=NO
EARLIEST_BLOCKER=FORMAL_RUNTIME_AUTHORITY_CHAIN_UNPOPULATED_AND_PUBLICATION_GATED
SCORE_ENGINE_EXISTS=YES
SCORE_POLICY_EXISTS=YES
SCORE_POLICY_FORMALLY_APPROVED=YES_ARTIFACT_LEVEL
SCORE_AUTHORITY_STATUS=POLICY_APPROVED_RUNTIME_NOT_READY
GRADE_ENGINE_EXISTS=YES
GRADE_POLICY_EXISTS=YES
GRADE_POLICY_FORMALLY_APPROVED=YES_ARTIFACT_LEVEL
GRADE_AUTHORITY_STATUS=DOWNSTREAM_SCORE_PUBLICATION_BLOCKED
LEADER_SET_STATUS=POLICY_APPROVED_EXACT_PROJECTION_ARTIFACT_NOT_POPULATED
LEADER_SET_REQUIRED_FOR_SCORE=YES
LEADER_SET_REQUIRED_FOR_LIFECYCLE=NO
LEADER_SET_REQUIRED_FOR_OPPORTUNITY=NO_CURRENT_UNIVERSE_GATE
CORE_SEMANTICS_STATUS=RECOVERED_STRUCTURAL_CORE_PLUS_SCORE_CORE_SUBSET
CORE_SEMANTIC_COLLISION=YES_BUT_BOUNDED
AS_OF_AUTHORITY_STATUS=DEFINED_IN_CONTRACT_RUNTIME_CHAIN_NOT_READ_BACK
LIFECYCLE_POLICY_STATUS=STAGES_APPROVED_TRANSITION_PARTIAL_PUBLICATION_BLOCKED
LIFECYCLE_BLOCKERS_AFTER_SCORE_GRADE=TRANSITION_AUTHORITY;FORMAL_SNAPSHOT_READBACK;FORMAL_POST_CLOSE_WIRING;CORRECTION_READBACK
OPPORTUNITY_AUTHORITY_STATUS=FORMAL_BOUNDARY_READY_PROVIDER_INACTIVE
OPPORTUNITY_BLOCKERS_AFTER_LIFECYCLE=FORMAL_PROVIDER_POLICY;WRITER_PERSISTENCE;UPSTREAM_READBACK;OPERATOR_GATE
RECOVERED_POLICY_COUNT=13
OWNER_DECISION_COUNT=3
TECHNICAL_BOTTLENECK_COUNT=9
DEFERRED_ITEM_COUNT=4
OWNER_DECISION_POLICY_TABLE_READY=YES
TECHNICAL_DESIGN_RECOMMENDATION_TABLE_READY=YES
IMPLEMENTATION_READY_POLICY_SKELETONS_READY=YES
OWNER_CHECKOUT_PRESERVED=YES
NEXT_TASK_RECOMMENDATION=TASK-M1-FORMAL-AUTHORITY-ACTIVATION-AND-READBACK-002
```

# OWNER 決策中心

目前真正需要 Owner 決定：3 項
工程團隊可自行處理：9 項
已從既有正式政策恢復：13 項
延後至 M2+：4 項

## DEC-01 — 核准具體 Score Projection / Leader Set artifact

問題：D001 已核准「approved effective CORE 的 bounded subset」，但 repository
沒有可供 runtime 綁定的每題材實際 member IDs、importance、version、effective
interval 與 lineage artifact。這不是要重新設計 D001，而是要把 D001 的核准內容
補成可讀回的正式資料。

為什麼現在要決定：Score 的 Leadership、CORE coverage、Grade 以及後續正式
Opportunity 都不能使用未綁定的 Leader Set。

既有證據：Structural Role V4 有 1,160 筆 approved rows；D001 已明確禁止固定
Top-N、runtime AI selection 與 dynamic reweighting；resolver 與 migration 0031
已存在。

A. Preserve D001：每一題材提供 Owner-reviewed bounded CORE subset，importance 只用 1.00/0.75/0.50。
   - behavior：由 approved projection 產生 deterministic GovernedLeaderSet。
   - advantage：完全沿用現行正式政策，不重開公式。
   - disadvantage：需要逐題材的正式 artifact/readback。

B. 改為全體 effective CORE。
   - behavior：所有 CORE 直接進 Score projection。
   - advantage：資料準備較簡單。
   - disadvantage：改變已核准 D001，必須新版本政策；不可由工程默認。

C. 暫不提供 artifact。
   - behavior：Score/Grade 持續 fail-closed。
   - advantage：零 authority 風險。
   - disadvantage：M1 持續 blocked。

工程建議：A

理由：A 是既有核准政策的唯一直接落地方式；B 是新政策，C 是安全停等。

如果選這個，接下來：建立並 hash-bind projection artifact，完成 1,160 role 與
projection readback，再開啟 Score writer 的工程實作。

Owner 決策：PENDING

## DEC-02 — 是否正式採用 Lifecycle V1.3 既存 transition parameters

問題：五個 stage 與 formal evaluator 已存在，但 B2 明確把 transition policy
標為 `PARTIAL_BY_DESIGN`；目前 `topic-lifecycle-policy.v1` 的 numeric values
仍被歷史 calibration 報告標成 provisional/tunable。

為什麼現在要決定：Lifecycle 不依賴 Score/Grade。即使 Score/Grade 完成，沒有
transition authority，Lifecycle 仍只能 shadow/unavailable。

既有證據：`topic_lifecycle_v1_3_formal.py`、`FormalLifecyclePublisher`、migration
0037/0039、五-stage contract 都已存在；post-close 目前仍呼叫 shadow engine。

A. 原值不變，正式核准現有 `topic-lifecycle-policy.v1`。
   - behavior：把現有版本/hash/effective date 納入 formal transition authority。
   - advantage：不發明、不調參，可直接接正式 publisher。
   - disadvantage：Owner 必須明確承擔目前 provisional values 的正式使用。

B. 保持 shadow/fail-closed，等待歷史 replay 與新版本核准。
   - behavior：正式 Lifecycle 不發布。
   - advantage：不把未校準值升格。
   - disadvantage：M1 仍 blocked。

C. 只核准 stage ontology，不核准 transitions。
   - behavior：可顯示 stage vocabulary，但沒有正式 state transition。
   - advantage：保留產品語義。
   - disadvantage：對 M1 沒有可用的 formal Lifecycle output。

工程建議：A（若目標是完成 M1）；否則 B

理由：A 只是 promotion of existing bundle，不是調參；若 Owner 不接受 provisional
numeric authority，工程不能用 B 以外的方式安全繞過。

如果選這個，接下來：註冊 transition artifact/ref，將 post-close 改接 formal
publisher，執行 A9 起點的 correction-aware readback。

Owner 決策：PENDING

## DEC-03 — Formal Opportunity 是否從 Shadow 升格

問題：Formal Opportunity page contract、Topic universe、dedupe、multi-Topic
provenance、same-as-of validation 都存在，但 qualification policy 明確是
`COMMITTED / SHADOW ONLY`，canonical provider 目前固定回 503。

為什麼現在要決定：目前 M1 定義把 Formal Opportunity 放在完成鏈上；沒有 provider
authority、effective date 與 production policy package，工程不能自行把 shadow
或 fixture 變成正式推薦。

既有證據：`formal_opportunity_universe.py` 是 formal boundary consumer，
`opportunity_api.py` 只接受 formal/canonical payload；BE-024B 的 semantic
matrix 已凍結，但 numeric parameters、ranking/validity/transition details
仍 provisional。

A. 建立新的 explicit Formal Opportunity authority package。
   - behavior：核准 provider scope、policy/parameter versions、effective date、freshness/persistence gates。
   - advantage：可在 Owner 明確授權後完成正式 provider。
   - disadvantage：這是產品政策升格，不能由工程自行決定，且仍需 canonical history。

B. 保持 shadow-only，formal provider 繼續 503。
   - behavior：所有 provisional/fixture 輸出留在 shadow。
   - advantage：符合現行文件與 fail-closed 安全邊界。
   - disadvantage：M1 不可宣稱 Formal Opportunity complete。

C. M1 只完成 Formal Topic/eligibility universe，不發布 strategy cards。
   - behavior：把 provider/strategy cards 明確移出本 M1 completion boundary。
   - advantage：不升格未校準政策。
   - disadvantage：需要 Owner/roadmap 對 M1 邊界作明確調整。

工程建議：B 為預設；若 Owner 堅持 Formal Opportunity 是 M1 必要輸出，才選 A

理由：現有 evidence 不足以安全升格 shadow numeric policy；B 是唯一不發明政策
的預設。A 需要一個新的、可審計的 authority package，不是工程默認。

如果選這個，接下來：若選 A，先登錄 authority package，再實作 provider/writer/readback；
若選 B，完成 Score/Grade/Lifecycle 但保留 Opportunity 503，M1 狀態仍為 NO。

Owner 決策：PENDING

# 建議一次核准格式

```text
DEC-01=A
DEC-02=A
DEC-03=B

ADDITIONAL_OWNER_RULES:
- DEC-01 不得改為 runtime AI selection、固定 Top-N、每日自動選股或 dynamic reweighting。
- DEC-02 若選 A，核准的是既存 topic-lifecycle-policy.v1 原值，不是本任務新增調參。
- DEC-03 若選 B，Formal Opportunity provider 必須維持 503/shadow-only，不得用 fixture 或 shadow fallback。
```
