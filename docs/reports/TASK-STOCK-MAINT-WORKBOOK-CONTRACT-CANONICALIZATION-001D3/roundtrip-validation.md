# Round-trip fixture validation

The focused 001D3 fixture file is
`services/api/tests/test_relation_weight_workbook_001d3_roundtrip.py`.

```text
MULTI_PRIMARY_ROUNDTRIP=PASS
ZERO_PRIMARY_ROUNDTRIP=PASS
MULTI_SECONDARY_ROUNDTRIP=PASS
REPRESENTATIVE_TOPIC_RESERVED_FIELD_TEST=PASS
INVALID_POSITIONAL_COUNT_TEST=PASS
OUT_OF_RANGE_WEIGHT_TEST=PASS
```

Fixture coverage:

- Case A validates `2408` with `DRAM／DDR|記憶體模組／通路` and
  `1.4|1.4`; both PRIMARY relations and equal positional weights survive,
  without inferring a representative topic.
- Case B validates zero PRIMARY with a valid SECONDARY and a fully empty row.
- Case C validates `A|B|C` against `0.4|0.5|0.8`.
- Case D supplies an explicit representative candidate different from the
  first PRIMARY and confirms it remains independent.
- Cases E and F reject positional count mismatch and out-of-range weight.

The first run exposed and corrected a validator defect that treated repeated
numeric weights as duplicate Topics. After the correction, the complete
focused suite passed:

```text
37 passed
NEW_FAILURE_COUNT=0
```

