# Legacy evidence integration

Source: `C:\Users\acer\Desktop\股票題材關聯.tsv`.

The source was read only and not modified. 001D1 records SHA-256
`DFBE9AEC146939349740D257D0E06CA490445C64D597E1C340119925CB5C978A`, 848
non-empty records, 595 legacy `主要` rows, 253 legacy `副題材` rows, 507
distinct stocks, and 79 stocks with multiple PRIMARY rows.

| Required use | Result | Boundary |
|---|---|---|
| Role recovery | YES | `題材角色=主要` → PRIMARY and `副題材` → SECONDARY is proven by the legacy builder and crosswalk. |
| Weight proposal | YES, proposal-only | Exact identity matches can preserve historical values as PROPOSED evidence; 001D keeps invalid/ambiguous values separate and never auto-approves. |
| Multi-primary evidence | YES | 79 stocks, 167 PRIMARY rows; 65 same-parent and 14 cross-parent cases prove multiple PRIMARY is intentional legacy relation semantics. |
| Topic crosswalk | YES | 001D1 reports 85 exact current matches, 3 renamed/merged requiring crosswalk, 4 parent-only/obsolete unmatched. |
| representative_topic authority | NO | The source has no representative column; order/weight candidates do not prove a unique representative. It can support a research candidate list only. |
| Priority order | YES, as order/priority | `題材順序` is unique within all audited multi-primary stocks and can preserve display priority. It must not be elevated to representative authority. |
| 大族群內權重 | YES, as hierarchy evidence | It supports parent/group hierarchy interpretation and is distinct from stock–Topic Relation Weight. |

## Important non-inference findings

- Minimum `題材順序` selects one row in 79/79 multi-primary stocks, but maximum
  order also selects one row; no rule identifies either as representative.
- Maximum `大族群內權重` is unique in only 53/79; it is not a general
  representative selector.
- Maximum/minimum legacy relation weight selects one PRIMARY in only 4/79;
  75/79 have equal PRIMARY weights.
- All audited multi-primary rows have the same direct-standardization status;
  normalization does not identify a representative.

## Recovery policy

Legacy values may calibrate or propose Relation Weight, but they remain
PROPOSED until Owner review. Missing or ambiguous legacy values use the
Owner-approved neutral proposal only where 001C permits it; that proposal is
not historical truth and is not a representative-topic signal.
