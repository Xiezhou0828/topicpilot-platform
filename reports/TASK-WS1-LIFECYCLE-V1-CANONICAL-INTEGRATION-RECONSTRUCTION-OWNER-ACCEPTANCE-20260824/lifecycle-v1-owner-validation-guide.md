# Lifecycle V1 Owner validation guide

Review each row against the raw Lead/Core/Related member summaries and the four evidence dimensions. `owner_label` and `owner_comment` are intentionally blank for manual acceptance.

Case selection is deterministic and based only on same-day and prior-state evidence. No future return or outcome was used.

Suggested labels: `CORRECT`, `TOO_EARLY`, `TOO_LATE`, `FALSE_MAIN_RISE`, `MISSED_MAIN_RISE`, `WHIPSAW`, `MATURITY_TOO_EARLY`, `MATURITY_TOO_LATE`, `DECLINE_TOO_EARLY`, `DECLINE_TOO_LATE`, `IDENTITY_PROBLEM`, `OTHER`.

A case with `NOT_FOUND_IN_RECONSTRUCTION` is an honest absence in this date window, not a fabricated example. In particular, Segment 3 is only populated when a real segment-3 row exists.

Evidence fields: participation = breadth/coverage; intensity = average/strong/weak movement; progression = expansion and segment clock; trajectory = recovery, peak drawdown, and lineage context.

The reconstruction is retrospective and current-taxonomy projected backward, not PIT history and not production Forward Shadow publication.
