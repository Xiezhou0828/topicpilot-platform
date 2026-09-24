# Structural Role vs Relation Role

`STRUCTURAL_ROLE_AND_RELATION_ROLE_ARE_DISTINCT=YES`

## Definitions

| Concept | Definition | Direction | Authority |
|---|---|---|---|
| Structural Role | The stock's categorical position within a Topic: `REPRESENTATIVE`, `CORE`, or `RELATED`. | Topic → Stock | Approved effective-dated Structural Role Authority. |
| Relation Role | The stock's relation classification toward a Topic: `PRIMARY` or `SECONDARY`. | Stock → Topic | Canonical relation role plus legacy mapping; Relation Weight Authority uses this type for range validation. |

Structural Role and Relation Role live on the same Topic–Stock relationship but
answer different questions. No current constraint says `PRIMARY` must equal
`REPRESENTATIVE` or `CORE`, or that `SECONDARY` must equal `RELATED`.

## Role combinations

The current ORM and Structural Role authority validate each namespace
independently. Therefore each combination below is **formally representable**;
there is no evidence-backed prohibition. Whether a particular row is
semantically appropriate remains Owner review, not an automatic parser rule.

| Combination | Formal status | Semantic conclusion |
|---|---|---|
| PRIMARY + RELATED | Allowed by current independent fields; no cross-constraint found. | VALID-REPRESENTABLE / semantic evidence required. |
| PRIMARY + CORE | Allowed by current independent fields; no cross-constraint found. | VALID-REPRESENTABLE / semantic evidence required. |
| PRIMARY + REPRESENTATIVE | Allowed by current independent fields; no cross-constraint found. | VALID-REPRESENTABLE / semantic evidence required. |
| SECONDARY + CORE | Allowed by current independent fields; no cross-constraint found. | VALID-REPRESENTABLE / semantic evidence required. |
| SECONDARY + REPRESENTATIVE | Allowed by current independent fields; no cross-constraint found. | VALID-REPRESENTABLE / semantic evidence required. |

The workbook candidate therefore does not derive or reject Structural Role from
PRIMARY/SECONDARY. It only validates relation-role cardinality and weights.

## Evidence

- `services/api/src/topicpilot_api/orm/models.py`: `InstrumentTopicRelation`
  stores `relation_type` separately from `structural_role`.
- `services/api/src/topicpilot_api/structural_role_authority.py`:
  `ALLOWED_ROLES` and independent role activation.
- `services/api/src/topicpilot_api/relation_weight_authority.py`:
  `relation_identity` allows only `PRIMARY` or `SECONDARY` and uses that type
  only for weight range selection.
- `docs/reports/TASK-TOPIC-STRUCTURAL-ROLE-AUTHORITY-AND-SCORE-PROJECTION-CLOSURE-001.md`:
  D4 explicitly separates structural roles from dynamic/consumer role names.
