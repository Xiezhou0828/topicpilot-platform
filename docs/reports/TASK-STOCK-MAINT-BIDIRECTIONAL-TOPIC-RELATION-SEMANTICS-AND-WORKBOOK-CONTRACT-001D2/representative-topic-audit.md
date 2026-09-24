# Representative Topic audit

`EXISTING_REPRESENTATIVE_TOPIC_CONCEPT_FOUND=NO`

## Search result

No formal field or authority equivalent to “the one Topic that best represents
this Stock” was found in the current Track C code, the 001B/001C/001D artifacts,
or the 001D1 legacy source audit.

| Candidate name / signal | Result | Evidence |
|---|---|---|
| `representative_topic` | No existing field; safe only as a reserved workbook field. | No matching current/historical authority field; 001D1 search/audit. |
| `primary_display_topic`, `default_topic`, `main_topic`, `market_identity_topic` | No formal authority found. | No current Track C symbol or approved artifact. |
| Structural Role `REPRESENTATIVE` | **Not equivalent.** It answers Topic → Stock representativeness for one relation, not Stock → Topic's one display Topic. | `structural_role_authority.py`; D4/D6 role separation. |
| Leader / `is_leader` | **Not equivalent.** Leader Set is a Score consumer set; current artifact is unproven. | `runtime_readiness.py`; maintenance generator emits `UNPROVEN`. |
| First PRIMARY / highest Relation Weight | **Not proven.** 001D1 found no unique-primary rule and equal weights in 75/79 legacy multi-primary stocks. | 001D1 `legacy-source-structure.md`, `multi-primary-pattern-analysis.md`. |
| 題材順序 minimum | **Priority only.** It produces one deterministic first row in 79/79 audited multi-primary stocks, but maximum order is also deterministic and no source says first means representative. | 001D1 audit. |

`EXISTING_REPRESENTATIVE_TOPIC_NAME=NONE`

`EXISTING_REPRESENTATIVE_TOPIC_AUTHORITY=NONE_FOUND`

`EXISTING_REPRESENTATIVE_TOPIC_CARDINALITY=NOT_APPLICABLE; NO_FORMAL_FIELD`

## Reserved field decision

`REPRESENTATIVE_TOPIC_RESERVED_FIELD_SAFE=YES`

The field is safe **only** with this exact non-runtime meaning:

> Optional Owner-curated display/identity candidate field. No automatic
> derivation. No runtime effect until separately governed.

Validation may check a supplied value against the enabled/formal Topic
vocabulary when that vocabulary is explicitly supplied to the validator. It
must not require the value to appear in `primary_topics`; the Owner has not
approved that relationship. An empty value is valid.

## Prohibitions

- Do not populate it from minimum/maximum `題材順序`.
- Do not populate it from first/highest PRIMARY.
- Do not populate it from Structural Role, Leader, Score Importance, or
  Relation Weight.
- Do not add a runtime reader, API field, database column, or canonical apply
  behavior in this task.
