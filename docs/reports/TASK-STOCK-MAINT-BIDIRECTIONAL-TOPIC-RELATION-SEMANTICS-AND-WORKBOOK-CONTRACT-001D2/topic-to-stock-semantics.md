# Topic → Stock semantics

Question: **Within a Topic, how important or representative is this Stock?**

## Structural Role

`REPRESENTATIVE`, `CORE`, and `RELATED` are the formal categorical answer to
the Topic-to-Stock membership-position question.

- **Semantic — PROVEN:** Structural Role classifies one Topic–Stock relation
  as representative, core, or related. The closure report defines
  Representative as representativeness, Core as important positioning/linkage,
  and Related as supported but non-core linkage.
- **Authority — PROVEN:** `structural_role_authority.py` and
  `topic_engine/structural_role_authority.py` require approved,
  effective-dated, versioned, lineage-bearing authority and fail closed on a
  missing or conflicting record.
- **Cardinality — PROVEN:** at most one effective Structural Role per
  Topic–Stock relation at an as-of date; many stocks can share a Topic role and
  one stock can have roles across many Topics. No stock-level “one role” rule
  was found.
- **Runtime scope — PROVEN:** formal membership validation and the approved
  CORE projection path. It is not Relation Weight, Score Importance, or a
  daily market state.

`TOPIC_TO_STOCK_STRUCTURAL_ROLE_SEMANTIC=FORMAL_CATEGORICAL_TOPIC_MEMBERSHIP_POSITION`

`TOPIC_TO_STOCK_STRUCTURAL_ROLE_AUTHORITY=APPROVED_EFFECTIVE_DATED_STRUCTURAL_ROLE_AUTHORITY`

## Leader / is_leader

- **Semantic — PROVEN for the contract, UNPROVEN for a current production
  artifact:** `GovernedLeaderSet` is an explicit per-Topic set of member
  instruments, each with a Score consumer importance. It is not a daily
  top-gainer or automatic alias for Representative/Core.
- **Authority — PROVEN as a required input contract; UNPROVEN as current
  authority data:** `runtime_readiness.py` requires an approved, versioned,
  effective Leader Set, but no approved production Leader Set selector or
  artifact exists in the current Track C evidence. The maintenance generator
  therefore exports `is_leader=UNPROVEN` and forbids inference from role.
- **Cardinality — PROVEN:** 0..N leaders per Topic in the `GovernedLeaderSet`
  shape. A stock may appear in more than one Topic's set.
- **Runtime scope — PROVEN:** only the formal Score path when an explicit
  approved set is supplied. Lifecycle and UI role-like labels are not Leader
  authority.

`TOPIC_TO_STOCK_LEADER_SEMANTIC=EXPLICIT_TOPIC_SCORE_LEADER_SET_MEMBERSHIP_NOT_DAILY_LEADERSHIP`

`TOPIC_TO_STOCK_LEADER_AUTHORITY=FORMAL_APPROVED_INPUT_CONTRACT_CURRENT_ARTIFACT_UNPROVEN`

## Score Importance

- **Semantic — PROVEN:** `TopicScoreProjectionMember.score_importance` is the
  selected member's contribution importance inside one approved Topic Score
  projection. Allowed values are exactly `1.00`, `0.75`, and `0.50`.
- **Scope — PROVEN:** projection-specific. It is not a generic Topic
  membership scalar and cannot be copied into Relation Weight.
- **Runtime effect — PROVEN:** `ProductionV1` uses `LeaderDefinition.importance`
  in the weighted Leadership and consensus calculation. The final Score is
  `0.60 * breadth + 0.40 * final_leadership`; Grade is downstream of that
  Score. The projection resolver validates selected members as CORE and does
  not select members itself.
- **Authority type — PROVEN:** owner-reviewed, effective-dated, versioned
  Score projection input; its values are formal only within that projection.

`TOPIC_TO_STOCK_SCORE_IMPORTANCE_SEMANTIC=CONSUMER_SPECIFIC_SCORE_PROJECTION_MEMBER_IMPORTANCE`

`TOPIC_TO_STOCK_SCORE_IMPORTANCE_SCOPE=APPROVED_TOPIC_SCORE_PROJECTION_ONLY`

## Topic-to-Stock primary formal concept

`TOPIC_TO_STOCK_PRIMARY_FORMAL_CONCEPT=STRUCTURAL_ROLE_AUTHORITY`

This does **not** erase the two overlays: an approved Leader Set and its Score
Importance are separate Topic Score consumer inputs. No single scalar is
authorized to replace all three concepts.

## Evidence index

- `services/api/src/topicpilot_api/structural_role_authority.py`: `ALLOWED_ROLES`,
  `parse_artifact`, `activate`.
- `services/api/src/topicpilot_api/topic_engine/structural_role_authority.py`:
  `resolve_structural_role_records`.
- `services/api/src/topicpilot_api/topic_engine/runtime_readiness.py`:
  `GovernedLeaderSet`, `evaluate_activation_readiness`.
- `services/api/src/topicpilot_api/topic_engine/score_projection.py`:
  `ALLOWED_SCORE_IMPORTANCE`, `resolve_score_projection_records`,
  `build_governed_leader_set`.
- `services/api/src/topicpilot_api/topic_engine/production_policy.py`:
  `LeaderDefinition`, `evaluate_production_v1`.
- `E:\topicpilot-stock-maint-bootstrap-001\build_stock_maintenance_workbook.mjs`:
  `roleHeaders`, `roleRows`.
