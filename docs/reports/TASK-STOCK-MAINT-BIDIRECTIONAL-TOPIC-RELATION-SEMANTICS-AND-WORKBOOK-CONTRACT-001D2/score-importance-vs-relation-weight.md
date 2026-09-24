# Score Importance vs Relation Weight

`SCORE_IMPORTANCE_AND_RELATION_WEIGHT_ARE_DISTINCT=YES`

`SCORE_IMPORTANCE_GENERIC_RELATION_WEIGHT=NO`

`SCORE_IMPORTANCE_PROJECTION_SPECIFIC=YES`

## Exact separation

| Dimension | Score Importance | Relation Weight |
|---|---|---|
| Question answered | How much should this selected member contribute to this Topic Score projection? | How important/strong is this Stock's membership in this Topic? |
| Direction | Topic → Stock, but only inside one Score projection | Stock → Topic relation |
| Entity | `TopicScoreProjectionMember` / `LeaderDefinition` | `InstrumentTopicRelation` plus `RelationWeightAuthority` |
| Values | Exactly `1.00`, `0.75`, `0.50` | PRIMARY `0.5–2.0`; SECONDARY `0.3–0.8` |
| Authority | Approved effective-dated Score projection and its Leader Set adapter | Separate effective-dated Relation Weight authority; only APPROVED is formal |
| Calculation | Weighted Leadership and consensus; final Score combines Breadth and Leadership | No automatic Topic Score, Grade, Lifecycle, Today, Opportunity, Leader, or Structural Role effect |
| Cardinality | One value per selected projection member | One value per relation revision / relation identity |

The values overlap numerically only by coincidence. A `1.00` Score Importance
does not mean a `1.00` Relation Weight, and a `1.50` Relation Weight cannot be
used as a Score Importance because `1.50` is illegal in the Score projection
domain.

## Why replacement is unsafe

Replacing Score Importance with Relation Weight would change the selected Score
member contribution using a Stock-to-Topic membership scalar. Replacing
Relation Weight with Score Importance would erase the approved PRIMARY/SECONDARY
range model and would lose relation-level Owner maintenance. Neither mapping
has an Owner decision or code contract.

## Evidence

- `services/api/src/topicpilot_api/topic_engine/score_projection.py`:
  `ALLOWED_SCORE_IMPORTANCE`, `ScoreProjectionMemberRecord`, and
  `resolve_score_projection_records`.
- `services/api/src/topicpilot_api/topic_engine/production_policy.py`:
  `LeaderDefinition` and `evaluate_production_v1` lines that compute
  `leadership_raw`, `consensus_raw`, and `score_value`.
- `services/api/src/topicpilot_api/relation_weight_authority.py`:
  `parse_weight`, `RelationWeightReadModel.formal_weight`, and exact identity
  resolution.
- `docs/reports/TASK-STOCK-MAINT-TOPIC-RELATION-WEIGHT-SEMANTICS-OWNER-DECISION-001C/weight-concept-separation.md`:
  Owner-approved three-concept separation.

## Conclusion

Score Importance is a **projection-internal Topic Score input**. Relation
Weight is a **separately governed Stock-to-Topic membership importance**. They
must remain separate workbook columns/semantics even if a future UI shows them
side by side.
