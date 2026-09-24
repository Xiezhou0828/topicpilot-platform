# Stock → Topic semantics

Question: **For this Stock, how important or core is this Topic?**

## Relation Role

- **Semantic — PROVEN:** `PRIMARY` and `SECONDARY` are Stock-to-Topic relation
  role labels. Legacy `主要` maps to `PRIMARY`; legacy `副題材` maps to
  `SECONDARY`.
- **Cardinality — PROVEN:** 0..N PRIMARY and 0..N SECONDARY per instrument.
  The legacy builder explodes every main Topic into a separate PRIMARY row and
  does not collapse multi-primary relations. The current relation universe has
  474 PRIMARY and 686 SECONDARY rows, with 102 symbols having more than one
  PRIMARY.
- **Authority — PROVEN:** canonical relation identity is market + instrument +
  Topic + relation type. The current ORM/authority has no stock-level unique
  PRIMARY constraint.

`STOCK_TO_TOPIC_RELATION_ROLE_SEMANTIC=PRIMARY_SECONDARY_RELATION_CLASSIFICATION`

`STOCK_TO_TOPIC_RELATION_ROLE_CARDINALITY=0..N_PRIMARY_AND_0..N_SECONDARY_PER_INSTRUMENT`

## Relation Weight

- **Semantic — PROVEN:** Owner-approved `TOPIC_MEMBERSHIP_IMPORTANCE` — the
  relative importance/strength of one Stock's membership in one Topic. It is a
  relation-level scalar, not a ranking ordinal, not Structural Role, and not
  Score Importance.
- **Authority — PROVEN:** separate effective-dated Option C authority in
  `topicpilot.relation_weight_authorities`; `RelationWeightReadModel.formal_weight`
  returns only an APPROVED row, and identity resolution is exact.
- **Ranges — PROVEN:** PRIMARY inclusive `0.5–2.0`; SECONDARY inclusive
  `0.3–0.8`. Values are validated by `parse_weight` and the ORM/migration
  check constraint.
- **Proposal state — PROVEN:** 001D exports PROPOSED values and disables Owner
  apply/auto-approval. Proposal/default values are not formal runtime truth.

`STOCK_TO_TOPIC_RELATION_WEIGHT_SEMANTIC=TOPIC_MEMBERSHIP_IMPORTANCE`

`STOCK_TO_TOPIC_RELATION_WEIGHT_AUTHORITY=SEPARATE_EFFECTIVE_DATED_RELATION_WEIGHT_AUTHORITY_APPROVED_ONLY`

`STOCK_TO_TOPIC_RELATION_WEIGHT_RANGE_PRIMARY=0.5-2.0_INCLUSIVE`

`STOCK_TO_TOPIC_RELATION_WEIGHT_RANGE_SECONDARY=0.3-0.8_INCLUSIVE`

## Automatic consumer audit

The answer is **NO** for every consumer below. This is not merely an absence
of code: 001C's Owner consumer policy explicitly prohibits these imports, and
001D's consumer regression audit records them as NONE.

| Consumer | Relation Weight automatically affects it? | Evidence |
|---|---|---|
| Topic Score | NO | 001C consumer policy; 001D consumer regression audit; no import in Score modules. |
| Heating | NO | 001C Today boundary remains price-change/rotation based. |
| Cooling | NO | Same Today boundary. |
| Grade | NO | Grade is downstream of the explicit Score policy, not Relation Weight. |
| Lifecycle | NO | 001D consumer audit; Lifecycle remains a separate/shadow contract. |
| Leader | NO | Leader Set is an explicit Score input; no relation-weight selector. |
| Structural Role | NO | Structural Role authority is independent and categorical. |
| Today | NO | Formal Today chain does not consume Relation Weight. |
| Opportunity | NO | 001C prohibits eligibility/ranking/opportunity use absent a new contract. |

## Evidence index

- `services/api/src/topicpilot_api/relation_weight_authority.py`:
  `PRIMARY_MIN`, `PRIMARY_MAX`, `SECONDARY_MIN`, `SECONDARY_MAX`,
  `RelationWeightReadModel.formal_weight`, `generate_proposals`,
  `resolve_approved_weight_by_identity`.
- `services/api/src/topicpilot_api/orm/relation_weights.py`:
  `RelationWeightAuthority` constraints.
- `services/api/src/topicpilot_api/orm/models.py`:
  `InstrumentTopicRelation` identity and relation fields.
- `docs/reports/TASK-STOCK-MAINT-TOPIC-RELATION-WEIGHT-SEMANTICS-OWNER-DECISION-001C/relation-weight-consumer-policy.md`.
- `docs/reports/TASK-STOCK-MAINT-TOPIC-RELATION-WEIGHT-AUTHORITY-IMPLEMENTATION-001D/consumer-regression-audit.md`.
- `docs/reports/TASK-STOCK-MAINT-LEGACY-MULTI-PRIMARY-SEMANTICS-RECONCILIATION-001D1/current-schema-cardinality-audit.md`.
