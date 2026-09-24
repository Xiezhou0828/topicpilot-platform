# Workbook contract reconciliation

`PROPOSED_WORKBOOK_SCHEMA_STATUS=SUFFICIENT_WITH_CHANGES`

The preferred shape is sufficient after the changes below. The current two
workbook surfaces are not interchangeable and must be aligned:

1. 001D `relation_weight_workbook.py` requires exactly one PRIMARY and exports
   `;`-separated secondary pairs.
2. The maintenance generator already joins multiple PRIMARY values with `|`,
   but names the field `primary_topic`, names the secondary weight field
   `secondary_weight`, and has no reserved `representative_topic` field.

## Proposed schema

| Column | Cardinality | Contract |
|---|---:|---|
| `symbol` | 1 | Exact stock identity key; compatibility alias `instrument` accepted on input. |
| `name` | 0..1 display | Display/provenance only; never an authority join key. |
| `market` | 1 | Exact market identity. |
| `representative_topic` | 0..1 | Reserved Owner-curated display/identity candidate; no auto derivation and no runtime effect. |
| `primary_topics` | 0..N | `|`-separated exact Topic values. |
| `secondary_topics` | 0..N | `|`-separated exact Topic values. |
| `primary_weights` | 0..N | Positional `|`-separated decimals; count equals `primary_topics`; each `0.5–2.0`. |
| `secondary_weights` | 0..N | Positional `|`-separated decimals; count equals `secondary_topics`; each `0.3–0.8`. |
| `effective_date` | 0..1 | Proposal effective-date text; not canonical approval. |
| `reason` | 0..1 | Owner proposal reason; no runtime effect. |
| `evidence_note` | 0..1 | Evidence/provenance note; no runtime effect. |

The Python candidate keeps legacy 001D aliases (`primary_topic`,
`primary_weight`, `secondary_weight`, `instrument`, and `;`) read-compatible,
but always exports the plural canonical names and `|` separator. This prevents
silent loss while making the new contract unambiguous.

## What the current contract loses

- The 001D parser/exporter rejects any stock with more than one PRIMARY.
- A singular `primary_topic` header can be read as “representative Topic” even
  though no such semantic was approved.
- The 001D authority workbook uses `;`, while the maintenance generator uses
  `|`; positional values are therefore not one interoperable format.
- `primary_weight` cannot carry one value per PRIMARY relation under a strict
  single-value interpretation.
- No explicit 0..1 `representative_topic` field exists.
- The current maintenance snapshot lacks the preferred `reason` and
  `evidence_note` names and uses `effective_from/effective_to` rather than the
  proposal-level `effective_date`.
- A zero-topic stock can be represented by the generator only as an empty
  snapshot row; the old 001D validator cannot validate an empty PRIMARY list.

## Sufficiency conditions

The proposed schema is lossless for the requested dimensions when:

- all relation lists are preserved, including 0..N PRIMARY;
- each weight list is positional and count-checked;
- representative_topic stays optional and non-derived;
- exact relation identity is checked against the current relation universe;
- duplicate and cross-role duplicate Topics are rejected; and
- the workbook remains proposal/input rather than canonical authority.

## Evidence and implementation boundary

- `services/api/src/topicpilot_api/relation_weight_workbook.py` now implements
  the bounded candidate parser, validator, and exporter.
- `E:\topicpilot-stock-maint-bootstrap-001\build_stock_maintenance_workbook.mjs`
  now emits `representative_topic`, plural topic/weight fields, `effective_date`,
  `reason`, and `evidence_note` in the current stock-topic snapshot.
- No `RelationWeightAuthority`, formal reader, canonical relation storage, or
  migration schema is changed by this reconciliation.
