# Recommended Topic Strength Evidence Contract V0

## Contract decision

```text
CONTRACT_VERSION = topic-strength-evidence.v0
MODE = EVIDENCE_VECTOR
OVERALL_LEVEL = NULL / NOT_DEFINED
TOTAL_SCORE = NOT_CREATED
PRODUCTION_RULE = NO
LIFECYCLE_SEMANTICS = UNCHANGED
```

V0 is a grouped raw evidence vector. The grouping gives consumers a stable
map, but it does not assert that all groups are available or that any group
has a categorical strength label.

## Proposed semantic envelope

```json
{
  "contractVersion": "topic-strength-evidence.v0",
  "mode": "EVIDENCE_VECTOR",
  "overallLevel": null,
  "score": null,
  "dimensions": {
    "participation": {
      "status": "AVAILABLE | PARTIAL | UNAVAILABLE",
      "positiveBreadth": null,
      "strongBreadth": null,
      "weakRatio": null,
      "basis": "valid_observed_members"
    },
    "intensity": {
      "status": "AVAILABLE | PARTIAL | UNAVAILABLE",
      "averageChangePct": null,
      "leaderProxy": {
        "changePct": null,
        "memberId": null,
        "method": "maxObservedChange | roleAwareObservedChange | unavailable",
        "semanticAvailable": false
      }
    },
    "persistence": {
      "status": "CONTEXT_ONLY | UNAVAILABLE",
      "stageTradingDays": null,
      "stageEnteredAt": null,
      "candidateStage": null,
      "candidateStreak": null,
      "recentBreadthPersistence": null,
      "unavailableReason": "NO_PIT_ROLLING_WINDOW"
    }
  },
  "quality": {
    "coveragePct": null,
    "expectedMemberCount": null,
    "observedMemberCount": null,
    "validChangeCount": null,
    "sampleConfidence": null,
    "coverageConfidence": null,
    "confidence": null,
    "smallSample": null,
    "dataStatus": "",
    "evaluationStatus": "",
    "evaluationMode": "SHADOW",
    "policyVersion": "",
    "calculationVersion": ""
  }
}
```

The JSON is a proposal, not an instruction to edit `topic-api.ts`, schemas, or
the engine in this task. The current API can supply portions of it through the
existing lifecycle evidence/confidence payload; missing portions must remain
null/unavailable until a separately authorized read-model implementation.

## Evidence mapping

### Participation

- `positiveBreadth`: primary participation evidence.
- `strongBreadth`: retained as related conviction/participation evidence;
  preserve the classifier version and note that it is a subset of positive
  breadth under current semantics.
- `weakRatio`: retained as counter-participation evidence; do not invert or
  turn it into a label.

### Intensity

- `averageChangePct`: primary group intensity evidence.
- `leaderProxy.changePct`: supplemental asymmetric intensity evidence only.
- `leaderProxy.semanticAvailable`: mandatory interpretation flag.
- `leaderProxy.memberId`: context/provenance only, never formal Leader
  authority.

### Persistence

- `stageTradingDays`, `stageEnteredAt`, `candidateStage`, and
  `candidateStreak`: Lifecycle context only.
- `recentBreadthPersistence`: null/unavailable until an explicit PIT-safe
  rolling window exists.

### Quality

Quality fields gate interpretation. They are not dimensions and must not be
fed into a future total score or ordinal level. `coveragePct` is especially
important: coverage high means the evidence is more complete, not that the
topic is stronger.

## Consumer rules

1. The Lifecycle object is authoritative for stage meaning. Strength is
   display/research evidence and cannot select or revise a stage.
2. Raw null stays null. `UNAVAILABLE` is not `WEAK`; `PARTIAL` is not
   `NORMAL`.
3. The frontend renders only backend-provided fields and their status. It does
   not derive levels, scores, breadth, persistence, or Leader identity.
4. WS3 may consume the vector as a versioned research feature, with quality and
   missingness preserved, but may not alter A2/Legacy-5/BOTH strategy rules.
5. No volume, news/Radar, formal Leader Set, institutional flow, benchmark, or
   intraday data is part of V0.
6. Any dimension label or overall level requires a new contract version and
   Owner-approved validation evidence.

## Ready now vs deferred

| Field group | Status now | Safe claim |
|---|---|---|
| Participation raw values | Current shadow evidence | Backend evidence vector, with data status |
| Intensity average change | Current shadow evidence | Backend evidence vector, with valid-count/quality context |
| Leader proxy | Current shadow research evidence | Labelled proxy only; no formal Leader claim |
| Lifecycle persistence context | Current lifecycle evidence | Day N/candidate context only |
| Recent breadth persistence | Unavailable | Must not be invented or zero-filled |
| Dimension labels | Deferred/provisional | Need separate policy and validation |
| Overall ordinal level | Deferred | Not needed for V0 |
| 0–100 score | Rejected/deferred | Default `NO` |
