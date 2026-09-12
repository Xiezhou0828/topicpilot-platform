# Lifecycle V1 State Memory Specification

The persisted `state_memory` JSON is versioned as `topic-lifecycle-v1.state-memory.1` and is carried with the typed columns used by the API.

```json
{
  "mainRiseSegment": 1,
  "segmentEntryDate": "2026-08-10",
  "segmentAnchorDate": "2026-08-10",
  "daysSinceMeaningfulExpansion": 0,
  "lastMeaningfulExpansionDate": "2026-08-10",
  "drawdownFromPeakPct": 0.0,
  "runningPeakCloseByMember": {"instrument-id": 100.0},
  "runningPeakDateByMember": {"instrument-id": "2026-08-10"},
  "trajectoryRecovered": false,
  "lastAuthorityWeightedPositiveBreadth": 0.7,
  "lastLeadCoreAverageChangePct": 1.5,
  "memoryVersion": "topic-lifecycle-v1.state-memory.1"
}
```

Rules:

1. State is advanced only on an eligible, evaluated date. Insufficient data holds the previous stage and memory.
2. Peak and expansion memory uses Lead/Core members only. Related-only movement cannot reset the Main Rise clock.
3. A new Main Rise entry starts a segment; Mature→Main Rise re-entry increments it.
4. Stage entry/trading-day fields remain separate from the segment fields.
5. Memory is deterministic JSON derived from immutable input facts and the previous result; it is not inferred from the frontend or current mutable membership.
