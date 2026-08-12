# Opportunity Shadow Read API V1

This is the additive, shadow-only read contract from `TASK-BE-024C`.

## Endpoints

```text
GET /api/v1/opportunities/shadow
GET /api/v1/topics/{topic_id}/opportunities/shadow
GET /api/v1/stocks/{instrument_id}/opportunities/shadow
GET /api/v1/opportunities/shadow/{opportunity_id}
```

The list endpoint accepts bounded `strategy`, `state`, `topicId`,
`instrumentId`, `grade`, `lifecycle`, `limit`, `page`, and `cursor` filters.
It does not accept buy/sell, minimum-score, expected-return, target-price, or
stop-loss filters.

## Response identity

Every response has `contractVersion=opportunity-shadow-read.v1`,
`publicationStatus=SHADOW`, `dataStatus`, `asOf`, and explicit `status`:
`READY`, `EMPTY`, `DEFERRED`, or `UNAVAILABLE` at the provider boundary.

## Topic example

```json
{
  "contractVersion": "opportunity-shadow-read.v1",
  "status": "READY",
  "publicationStatus": "SHADOW",
  "dataStatus": "FIXTURE/SYNTHETIC",
  "topicId": "topic-warming",
  "topicName": "Warming Topic",
  "topicGrade": "B",
  "topicLifecycle": "FERMENTING",
  "strategies": {
    "trendContinuation": {
      "strategyId": "TREND_CONTINUATION",
      "candidateCount": 1,
      "backendCandidateCount": 1,
      "presentedCount": 1,
      "presentationCap": 3,
      "fullRankingRetained": true
    },
    "catchUp": {
      "strategyId": "CATCH_UP",
      "candidateCount": 0,
      "backendCandidateCount": 0,
      "presentedCount": 0,
      "presentationCap": 2,
      "fullRankingRetained": true
    }
  }
}
```

## Summary card fields

Cards preserve deterministic `opportunityId`/`opportunityKey`, strategy,
instrument and topic identity, Grade/Lifecycle, state, qualification class and
provenance, rank metadata, confidence basis, entry/support/risk contexts,
positive/waiting/risk/exclusion factors, policy/parameter/ranking-profile
versions, as-of, publication status, data status, display keys, and reason
codes.

## Detail and UI states

Detail adds Topic Context, why included, waiting-for, risk, entry,
invalidation, data/confidence, and provenance groups. The frontend adapter maps
backend status to LOADING, READY, EMPTY, DEFERRED, UNAVAILABLE, and ERROR. It
does not derive business semantics from raw fields.
