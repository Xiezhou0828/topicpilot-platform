# Formal Strength fail-closed root cause

Production evaluated 107 effective Formal leaves and published zero Strength rows. The receipt revision 4 reason groups were:

- 62 `FORMAL_TOPIC_SNAPSHOT_NOT_PUBLISHED`: no exact current Formal snapshot exists for those effective leaves.
- 44 `FORMAL_MEMBER_OBSERVATION_UNAVAILABLE`: the exact current snapshot exists, but at least one member fact lacks the required price observation/change evidence for the daily-return dimension. The public receipt exposes this at Topic-result granularity, not the underlying member ID; the exact member cardinality is therefore not fabricated here.
- 1 `SNAPSHOT_DATA_STATUS_PARTIAL`: MLCC had 8 members, 7 observed, and 1 unknown member fact.

This is a correct fail-closed result for the evidence actually consumed. Strength does not substitute a prior close, zero, synthetic return, shadow row, or stale snapshot. It continues to evaluate all 107 leaves so the missing-snapshot population is auditable.

The bounded code fix adds the existing corporate-action availability policy to the formal member-fact reader. A file-backed official suspension is projected as `NO_TRADE` plus `DAILY_RETURN=ACCOUNTED_UNAVAILABLE`, not as an observed price and not as a fabricated numeric value. Strength accepts that member for formal membership while excluding it from the daily-return calculation dimension. The score formula, weights, thresholds, grade boundaries, and benchmark semantics are unchanged.

The fix is local at commit `918fa70d29d4c77de91b9118633d3241a88130c9`. It was not released because repeated branch pushes were rejected by GitHub with HTTP 500; Production remains on `646deea23ebfd7afb415201d0f9b2f11ab6fd099`.
