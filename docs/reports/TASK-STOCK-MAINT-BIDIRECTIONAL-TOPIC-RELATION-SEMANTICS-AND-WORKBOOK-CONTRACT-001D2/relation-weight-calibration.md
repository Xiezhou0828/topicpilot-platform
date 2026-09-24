# Relation Weight calibration

## Observed versus approved ranges

| Relation type | Legacy observed range | Current approved range | Assessment |
|---|---:|---:|---|
| PRIMARY | `0.5–1.5` | `0.5–2.0` | Legacy evidence does not exercise `1.6–2.0`; current upper range is approved headroom, not an observed historical calibration. |
| SECONDARY | `0.4–0.8` | `0.3–0.8` | Current lower headroom `0.3–0.39` is also not represented by the known legacy range. |

`PRIMARY_WEIGHT_1_6_TO_2_0_SEMANTIC_STATUS=APPROVED_UNUSED_HEADROOM_WITHOUT_LEGACY_CALIBRATION_EVIDENCE`

The `1.6–2.0` PRIMARY range is intentionally available in the current Owner
decision and is documented in:

- `relation_weight_authority.py` (`PRIMARY_MAX=2.0`);
- `orm/relation_weights.py` and migration 0040 check constraints; and
- 001C `owner-decision-record.json` / `weight-concept-separation.md`.

It was not demonstrated by the legacy TSV and must not be described as
historical truth. A future calibration study may review high-end usage, but
this task must not reduce the approved range automatically.

`CURRENT_WEIGHT_RUBRIC_REQUIRES_RECALIBRATION=NO`

This means no immediate rubric change is required: the Owner-approved range is
internally consistent and the validator/tests enforce it. It does mean
`1.6–2.0` usage remains a future evidence/review item before frequent
production approval.

## Current proposal coverage

001D reports 1,160 current relations: 474 PRIMARY and 686 SECONDARY. It
created 1,160 non-production proposals: 198 valid historical recoveries, 23
invalid historical values defaulted to the current SECONDARY proposal `0.5`
while preserving the legacy value as evidence, and 939 default
initializations. None is APPROVED.

## Safety conclusion

Do not clamp, remap, or infer a high PRIMARY value from Structural Role, Score
Importance, Topic order, or parent/group weight. The workbook candidate keeps
the approved ranges and preserves provenance for later Owner review.
