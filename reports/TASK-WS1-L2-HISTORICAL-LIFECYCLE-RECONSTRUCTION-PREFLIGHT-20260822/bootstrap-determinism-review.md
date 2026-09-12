# Bootstrap Determinism Review

## Boundary

The first eligible PIT date is `2026-08-07`. The available formal evidence
starts on that date and continues through `2026-08-13` on the five observed
trading sessions. No prior Lifecycle result rows are available, so the replay
must not read a fabricated or inferred pre-boundary state.

## Required initial state

```json
{
  "previous_stage": null,
  "previous_stage_entered_at": null,
  "previous_stage_trading_days": null,
  "previous_candidate_stage": null,
  "previous_candidate_streak": 0,
  "bootstrap_state": "UNSEEN_PRIOR_STATE",
  "history_state": "TRUNCATED_AT_PIT_BOUNDARY",
  "authority": "HISTORICAL_RECONSTRUCTED_SHADOW",
  "evaluation_mode": "SHADOW",
  "policy_version": "topic-lifecycle-policy.provisional.1",
  "calculation_version": "topic-lifecycle-shadow.v1"
}
```

This state is deterministic only as a declared boundary condition. It does not
mean that the Topic had no Lifecycle stage before `2026-08-07`; it means that
the state prior to the first PIT-safe evidence date is unknown and excluded.

## Replay order

For a future evidence-only replay, the input sequence must be ordered by:

1. `trading_date` ascending over the five formal dates;
2. `topic_id` or the canonical `topic_slug` tie-break used by the snapshot
   authority;
3. immutable member-fact identity/order from the PIT snapshot artifact;
4. the declared source/correction lineage tie-break, with superseded rows
   excluded.

The existing `TopicLifecycleEngine` reads formal `TopicSnapshot` dates and
current relation/tracking projections; it does not consume the immutable
`TopicSnapshotMemberFact` artifact directly. Therefore the current engine
cannot be treated as a strict historical replay adapter from this preflight
alone. A later bounded route must either provide a separately approved adapter
contract or stop with `FAIL_CLOSED`.

## Persistence and confirmation

The first date starts with no previous stage and no candidate streak. Normal
confirmation, strong jump/decline behavior, and Day-N continue to use the
existing frozen provisional policy after the first date. The replay must not:

- carry state from any date before `2026-08-07`;
- treat the first candidate as a confirmed transition solely because it is the
  first observed row;
- claim a stage-entry date earlier than the PIT boundary;
- convert an insufficient observation into a zero-return observation;
- combine this reconstructed sequence with a `FORWARD_SHADOW` sequence.

If a later date has no valid member fact, the engine must hold/fail closed under
the frozen insufficient-data semantics. It must not advance Day-N based on a
missing date.

## Determinism checks still required before replay

The following checks are prerequisites for a future bounded route:

- Reconcile the committed materialization count of 4,235 member facts with the
  current snapshot aggregate sum of 4,236.
- Prove that the adapter consumes the same PIT member set and member-fact hash
  as the formal snapshot authority for each of the 460 partial cells.
- Prove that any relation/member tie-break is explicit and stable. The current
  engine's relation query is not itself a substitute for the immutable PIT
  member-fact ordering contract.
- Preserve the source lineage difference between `tw-reference-v1` membership
  evidence and `sdf-reference-603-v1` historical price evidence.
- Fail closed on `adjustment_state=UNKNOWN`, known or suspected corporate
  action discontinuity, missing previous close, supersession ambiguity, or
  missing source artifact hash.
- Verify that no result is labelled `FORWARD_SHADOW`; the only permitted
  authority marker for the bounded sequence is
  `HISTORICAL_RECONSTRUCTED_SHADOW`.

## Review conclusion

Bootstrap is conceptually bounded and deterministic as an explicit input
contract, but the current runtime path is not ready to execute a strict
historical replay. The correct outcome is `PARTIAL`, with no reconstruction or
database write performed by WS1/L2.
