# Opportunity Shadow Read API V1

**Decision:** `COMMITTED / SHADOW ONLY`
**Date:** 2026-08-12
**Work order:** `TASK-BE-024C`

## Context

BE-024/024A/024B already provide deterministic Trend Continuation and Catch-up
strategy results, qualification policy, decision states, structured
explainability, strategy-local ranking, and a provider-neutral read contract.
TopicPilot needs a read surface for Topic, Stock Encyclopedia, and future
Opportunity UI without activating a production Recommendation API.

## Decision

Introduce `OpportunityShadowReadService` behind a provider-neutral
`OpportunityReadProvider` interface. The fixture provider is deterministic and
synthetic. `CanonicalOpportunityReadProvider` is a future production adapter
placeholder and remains unavailable until canonical point-in-time data and
publication gates are approved.

The additive routes are:

- `GET /api/v1/opportunities/shadow`
- `GET /api/v1/topics/{topic_id}/opportunities/shadow`
- `GET /api/v1/stocks/{instrument_id}/opportunities/shadow`
- `GET /api/v1/opportunities/shadow/{opportunity_id}`

Responses use `publicationStatus=SHADOW` and preserve topic/stock identity,
Opportunity state, qualification provenance, structured evidence, policy,
parameter, and ranking-profile versions. Trend and Catch-up are never globally
merged. Presentation caps remain backend-owned: Trend Top 3 and Catch-up Top 2
per topic, with full strategy-local ranking metadata retained.

## Frontend authority

The frontend adapter may map, group, localize, and follow backend display order.
It must not derive eligibility, 20MA, Lifecycle qualification, risk, rank,
Opportunity state, technical classification, or B exception status. It exposes
LOADING, READY, EMPTY, DEFERRED, UNAVAILABLE, and ERROR semantics.

## Boundary

This decision does not authorize production persistence, migrations, scheduler
changes, daily-market changes, Recommendation activation, historical replay,
calibration, fake performance, or NEXT_TASK changes. Fixtures and synthetic
data are never calibration evidence.
