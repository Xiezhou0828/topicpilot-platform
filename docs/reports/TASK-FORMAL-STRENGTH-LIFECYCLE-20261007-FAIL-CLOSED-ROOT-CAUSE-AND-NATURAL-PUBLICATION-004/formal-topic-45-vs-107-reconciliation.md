# Formal Topic 45 vs 107 reconciliation

Session: `2026-10-07` (Asia/Taipei)

## Finding

- `45` is the count of exact-date, current, final, published Formal `topic_snapshots` rows returned by the Formal Topic readback. It is not the Formal Topic universe size.
- `107` is the dynamically derived effective Formal leaf scope used by both Formal Strength and Formal Lifecycle: active hierarchy children whose Topic identity is enabled and date-effective on `2026-10-07`.
- The public catalog contains 132 Topic identities because it includes parents and leaves. Filtering the effective leaf authority yields 107.
- The populations are therefore allowed to differ. The materializer writes only topics whose current member evidence is READY; downstream Strength/Lifecycle still evaluates every effective leaf and records an unavailable result when its current Formal snapshot is absent or unusable.

## Row reconciliation

The companion CSV contains one row for each of the 107 evaluated leaves. Production evidence classifies them as:

| Population | Count | Meaning |
|---|---:|---|
| Exact Formal Topic snapshots | 45 | 44 `COMPLETE` plus 1 `PARTIAL`, all `PUBLISHED`/`FINAL` for 2026-10-07 |
| Strength/Lifecycle evaluated leaves | 107 | Current effective formal leaf scope |
| Exact snapshot absent | 62 | `FORMAL_TOPIC_SNAPSHOT_NOT_PUBLISHED` |
| Exact snapshot present but member return evidence unavailable | 44 | Strength `FORMAL_MEMBER_OBSERVATION_UNAVAILABLE`; Lifecycle `OBSERVED_MEMBER_FACT_MISSING_PRICE_EVIDENCE` |
| Exact snapshot present but partial | 1 | MLCC, caused by the pre-fix 6173 authority projection gap |

The 107 rows are not stale or superseded Topic authority: the implementation derives them from effective `TopicHierarchy` children and Topic status/validity dates. No production code contains a business expectation of 45 or 107. Existing tests exercise dynamic scope changes rather than a fixed count.

## Why Topic PASS and downstream failure coexist

`_formal_snapshot_readback` asks whether the current date has valid Formal snapshot rows and whether their lineage is valid. It returns PASS for the 45 rows it sees. Strength and Lifecycle ask a stricter question for each of the 107 effective leaves: does this specific leaf have one current exact-date Formal snapshot and complete member evidence? The 62 missing rows therefore receive `FORMAL_TOPIC_SNAPSHOT_NOT_PUBLISHED`; this is a population/contract-semantics distinction, not a transaction-ordering or stale-revision defect.

## Authority chain

```text
effective Topic + hierarchy authority
  -> 107 effective Formal leaves
  -> PIT_FORMAL membership snapshot
  -> exact-date canonical member facts
  -> 45 READY Formal Topic snapshots
  -> Strength gate/evaluation for all 107 leaves
  -> Grade only from published Strength
  -> Lifecycle gate/evaluation for all 107 leaves
  -> post-close publication receipt
```

All stages remain point-in-time bound to `2026-10-07`. No historical Topic snapshot, Strength, Grade, or Lifecycle row was reconstructed.
