# Parent / Leaf reconciliation

## Dynamic canonical counts

Read-only requests were made against the configured public API on 2026-09-24:

`GET https://topicpilot-api.onrender.com/api/v2/topic-catalog?limit=500&offset=0`

| Measure | Result |
| --- | ---: |
| Catalog total / returned | 132 / 132 |
| Parent nodes | 25 |
| Leaf nodes | 107 |
| Parent → child edges | 107 |
| Leaf → parent edges | 107 |
| Legacy Leaf state rows | 107 |
| Leaf nodes missing legacy state | 0 |
| Parent state rows | 0 |
| Parents without children | 0 |
| Catalog `asOf` | `2026-09-24` |

The legacy `/api/v2/topics` response contains exactly the 107 Leaf state rows. The 25 Catalog Parents are intentionally absent from that state response; this is the expected separation, not a missing-data failure.

## Detail boundary checks

Live detail checks selected one Parent and one Leaf from the Catalog response:

- Parent `AI視覺`: `kind=PARENT`, `currentFormalSnapshot.availability.state=NOT_APPLICABLE`, `membersAvailability.state=NOT_APPLICABLE`, five canonical children.
- Leaf `12 吋矽晶圓`: `kind=LEAF`, one canonical Parent, `currentFormalSnapshot.availability.state=AVAILABLE`.

The frontend now carries the complete Catalog identity/hierarchy universe while displaying Leaf state only where it exists. It does not infer Parent status from naming, `groupName`, missing snapshots, or the legacy row count.
