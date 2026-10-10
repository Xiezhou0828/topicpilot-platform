# Formal Lifecycle fail-closed root cause

Lifecycle evaluated the same 107 effective Formal leaves and published zero rows. Its receipt reasons were 62 missing exact Formal Topic snapshots, 44 `OBSERVED_MEMBER_FACT_MISSING_PRICE_EVIDENCE`, and one `INSUFFICIENT_FORMAL_INPUT:SNAPSHOT_DATA_STATUS_PARTIAL` for MLCC.

Lifecycle correctly remains unavailable when the current Formal observation is not established. It does not advance a stage because the calendar advanced, does not backfill failed sessions, and does not derive Grade independently of Strength. The existing bootstrap path is still authoritative: when the first valid observation exists, `_prior_or_bootstrap` supplies `BASE` initialization for the current evaluation date; missing data is not silently converted to BASE.

The bounded fix allows a formally present, officially suspended member to remain in the snapshot while being excluded from the daily-return observation set. Lifecycle coverage is then calculated over the dimension-eligible observations, not over a member that has no legitimate current close. This restores the existing dimension-scoped availability policy and does not add a new lifecycle stage or transition rule.

Production has not consumed this fix yet because the branch update was rejected by GitHub HTTP 500. Therefore the Production Lifecycle status remains the observed revision-4 `FAIL_CLOSED` state.
