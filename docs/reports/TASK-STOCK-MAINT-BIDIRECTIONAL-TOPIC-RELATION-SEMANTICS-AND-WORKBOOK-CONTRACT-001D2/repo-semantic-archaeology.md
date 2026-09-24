# TASK-STOCK-MAINT-BIDIRECTIONAL-TOPIC-RELATION-SEMANTICS-AND-WORKBOOK-CONTRACT-001D2

## Scope and evidence boundary

This is a read-only semantic reconciliation plus a bounded non-production
workbook candidate. No Production, canonical business data, migration apply,
deployment, or 001E apply was performed.

The primary Track C evidence is the E: worktree
`E:\topicpilot-stock-maint-bootstrap-001\canonical-main`, branch
`codex/task-stock-maint-topic-relation-weight-authority-implementation-001d` at
the start of this task. The 001D and 001D1 artifacts are local, uncommitted
Track C evidence and are explicitly labelled as such; they are not treated as
remote GitHub history.

## Repository and task lineage

| Evidence | Symbol / scope | Finding | Confidence |
|---|---|---|---|
| `docs/reports/TASK-STOCK-MAINT-LEGACY-MULTI-PRIMARY-SEMANTICS-RECONCILIATION-001D1/semantic-conclusion.json` | 001D1 conclusion | Legacy `主要` is a multi-primary relation role; no unique-primary rule; current workbook loses semantics. | PROVEN from prior task artifact |
| `services/api/src/topicpilot_api/relation_weight_workbook.py` | `validate_workbook_row`, `export_proposal_rows` | 001D local workbook proposal surface requires exactly one PRIMARY and uses `;` positional secondary pairs. | PROVEN at local Track C start |
| `services/api/src/topicpilot_api/relation_weight_authority.py` | `generate_proposals`, `resolve_approved_weight_by_identity` | Relation Weight is one value per exact relation identity; current authority has no one-PRIMARY-per-instrument rule and resolves by relation identity. | PROVEN |
| `services/api/src/topicpilot_api/orm/models.py` | `InstrumentTopicRelation` | Canonical relation carrier has instrument, Topic, relation type, effective interval and version; no stock-level unique PRIMARY constraint. | PROVEN |
| `services/api/src/topicpilot_api/orm/relation_weights.py` | `RelationWeightAuthority` | Separate additive authority keyed to canonical relation id, with PRIMARY/SECONDARY range checks. | PROVEN |
| `services/api/src/topicpilot_api/topic_engine/structural_role_authority.py` | `resolve_structural_role_records` | Formal role namespace is `REPRESENTATIVE`, `CORE`, `RELATED`; reads are approved, effective and fail-closed. | PROVEN |
| `services/api/src/topicpilot_api/topic_engine/score_projection.py` | `resolve_score_projection_records`, `build_governed_leader_set` | Score Importance belongs to an approved Topic score projection member and is adapted into a Leader Set input. | PROVEN |
| `services/api/src/topicpilot_api/topic_engine/production_policy.py` | `LeaderDefinition`, `evaluate_production_v1` | Importance `{1.00, 0.75, 0.50}` affects weighted Leadership/consensus and the final Score; the evaluator does not select members. | PROVEN |
| `E:\topicpilot-stock-maint-bootstrap-001\build_stock_maintenance_workbook.mjs` | `stockTopicHeaders`, stock-topic snapshot builder | Existing maintenance snapshot already preserves multiple PRIMARY topics with `|`, but labels the field singular and calls the secondary weight field `secondary_weight`. | PROVEN |

## GitHub evidence

The GitHub connector was used read-only against
[`Xiezhou0828/topicpilot-platform`](https://github.com/Xiezhou0828/topicpilot-platform),
default branch `main`.

| GitHub file | Returned blob SHA | Evidence |
|---|---|---|
| [`docs/research/topic-universe-mapping.v1.md`](https://github.com/Xiezhou0828/topicpilot-platform/blob/main/docs/research/topic-universe-mapping.v1.md) | `187c00c5e5b88ed69223596076c69ad61382a8f6` | `主要題材` maps to `PRIMARY`, `副題材` maps to `SECONDARY`, labels are exploded, and the artifact is research-only/not approved. |
| [`services/api/src/topicpilot_api/models.py`](https://github.com/Xiezhou0828/topicpilot-platform/blob/main/services/api/src/topicpilot_api/models.py) | `025833c4fbdb66756e2b87e165787c81e37ae440` | `StockTopicRelation` is unique on stock + Topic + relation type. This prevents duplicate copies of the same relation, not multiple different Topics with the same relation type. |
| [`services/api/src/topicpilot_api/topic_engine/production_policy.py`](https://github.com/Xiezhou0828/topicpilot-platform/blob/main/services/api/src/topicpilot_api/topic_engine/production_policy.py) | `38742ec93514e2c7327d9d171dc5de36ca78429f` | The formal evaluator receives explicit CORE ids and explicit `LeaderDefinition` importance. |
| [`services/api/src/topicpilot_api/topic_engine/runtime_readiness.py`](https://github.com/Xiezhou0828/topicpilot-platform/blob/main/services/api/src/topicpilot_api/topic_engine/runtime_readiness.py) | `9f51d5f11427324483e19f11324bbb50690355c0` | `GovernedLeaderSet` is an explicit versioned input with no default selector. |

The local Track C 001D workbook and Relation Weight authority files are not in
the GitHub default-branch tree at the queried revisions; 001D1 records them as
local uncommitted implementation. GitHub code-search calls for several exact
terms also encountered a transient API `429`; no conclusion below depends on
that incomplete search. Where remote evidence is absent, the report marks the
claim `UNPROVEN` rather than treating absence as a semantic rule.

## Key archaeology conclusions

1. The legacy and canonical relation carriers are relation-granular and
   multi-primary capable. `primary_topic` was a workbook editing convenience,
   not a proven business rule.
2. Structural Role answers a categorical Topic-to-Stock membership question;
   Relation Role answers a Stock-to-Topic classification question.
3. Leader Set membership and Score Importance are Topic Score consumer inputs,
   not universal replacements for Structural Role or Relation Weight.
4. Relation Weight has an approved separate authority and ranges, but 001C
   explicitly prohibits automatic use in Topic Score, Grade, Lifecycle, Today,
   Opportunity, Leader, or Structural Role logic.
5. No existing formal `representative_topic` field or rule was found. Legacy
   `題材順序` is a complete priority order in the audited multi-primary set,
   but its first row is not proven to be a representative-topic authority.

## Status labels used below

- **PROVEN**: directly stated by code, authority artifact, test, or prior task
  evidence with an exact path/symbol.
- **INFERRED**: the narrowest interpretation consistent with multiple proven
  facts, but not itself a separately approved semantic.
- **UNPROVEN**: no formal rule or authority was found; it must not be inferred
  or consumed as canonical behavior.
