# Final workbook contract

```text
FINAL_WORKBOOK_COLUMNS=symbol,name,market,representative_topic,primary_topics,secondary_topics,primary_weights,secondary_weights,effective_date,reason,evidence_note
MULTI_PRIMARY_SUPPORTED=YES
ZERO_PRIMARY_SUPPORTED=YES
MULTI_SECONDARY_SUPPORTED=YES
ZERO_SECONDARY_SUPPORTED=YES
REPRESENTATIVE_TOPIC_OPTIONAL=YES
REPRESENTATIVE_TOPIC_AUTO_DERIVED=NO
```

The implemented ordering is exactly the ordering above. Topic and weight lists
use `|` positional separators. A legacy `;` separator remains accepted on input
only for transition compatibility; generated output uses `|`.

`representative_topic` is an optional Owner-curated display/identity candidate.
It is not inferred from the first PRIMARY topic, does not change relation
cardinality, and has no runtime effect.

The relation model remains stock-row friendly while preserving relation-level
semantics: each row can contain 0..N PRIMARY and 0..N SECONDARY relations, and
the corresponding weight list must preserve positional alignment.

