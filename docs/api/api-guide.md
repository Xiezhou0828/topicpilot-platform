# API guide

## Conventions

- Base path: `/api/v1`
- Content type: `application/json; charset=utf-8`
- Error type: `application/problem+json`
- Authentication: none in v1
- Mutation methods: not supported
- Trading dates: ISO `YYYY-MM-DD` in Asia/Taipei
- Timestamps: ISO 8601 UTC with offset or `Z`
- Missing numeric observations: JSON `null`, never implicit zero

Interactive documentation is exposed by FastAPI at `/docs`; the raw schema is
available at `/openapi.json`. The generated schema/client policy is recorded in
[ADR-002](../architecture/ADR-002-openapi-generated-client.md).

## Health and readiness

### `GET /healthz`

Reports process liveness. It must not execute expensive queries.

### `GET /readyz`

Reports whether PostgreSQL is reachable, migrations are current enough for the
application, and an approved dataset is available. A process can be healthy but
not ready.

## Data status

### `GET /api/v1/meta/data-status`

Returns the latest completed bundle version, contract version, data date,
generation/import timestamps, classification, row counts, freshness status,
and quality-event summary. Public responses must not expose source paths,
private URLs, or operator identities.

## Snapshot compatibility

### `GET /api/v1/snapshot/latest`

Returns the approved compatibility representation for the existing web
Snapshot validator. The compatibility route is a migration bridge, not a new
place to add frontend-only calculations.

If there is no completed import, return a problem response rather than an empty
object that looks valid.

## Stocks

### `GET /api/v1/stocks`

Parameters:

| Name | Type | Default | Rule |
|---|---|---:|---|
| `limit` | integer | 50 | Bounded by the service maximum |
| `offset` | integer | 0 | Non-negative |
| `topic` | string | — | Optional topic slug filter |
| `strategy` | string | — | Optional stable strategy key |
| `data_date` | date | latest | Optional trading date |

### `GET /api/v1/stocks/{code}`

Returns one stock dimension, latest/requested observation, and approved topic
relations. Unknown codes return 404 `application/problem+json`.

## Topics

### `GET /api/v1/topics`

Supports `limit`, `offset`, optional `data_date`, and enabled-only filtering.

### `GET /api/v1/topics/{slug}`

Returns topic metadata, hierarchy context, snapshot state, and constituents.
Unknown slugs return 404.

## Strategies

### `GET /api/v1/strategies`

Returns the registry/status for `MAS`, `MAV`, `TMC`, `BB`, `PB`, and `KD`.

### `GET /api/v1/strategies/{key}/candidates`

Parameters include `data_date`, `limit`, and `offset`. Strategy identifiers are
case-normalized only if the OpenAPI contract documents that behavior; clients
should send uppercase stable keys.

## Analytics

### `GET /api/v1/analytics/topic-rotation`

Returns topic observations over a bounded window, defaulting to 14 trading
days. Calendar-day arithmetic must not substitute for actual available trading
dates.

### `GET /api/v1/analytics/strategy-performance`

Returns strategy/horizon metrics with sample count and availability status.
Unavailable metrics remain `null` and include a reason when supplied.

## Pagination response

List endpoints expose items plus explicit pagination metadata. Consumers must
not infer total counts from a short final page. The exact generated shape in
OpenAPI is authoritative.

## Problem responses

Errors use a stable problem shape based on RFC 9457 concepts:

```json
{
  "type": "https://topicpilot.example/problems/not-found",
  "title": "Resource not found",
  "status": 404,
  "detail": "No synthetic stock exists for the requested code.",
  "instance": "/api/v1/stocks/DEMO-999"
}
```

Do not put stack traces, SQL, credentials, bundle paths, or private identifiers
in public problem details.

## Client and caching guidance

- Treat dimension and historical analytics responses as cacheable only when
  response headers permit it.
- Use `data-status` to display version/freshness rather than guessing from the
  browser clock.
- During a Render cold start, retry network failures with bounded exponential
  backoff and a visible warming state; do not retry 4xx contract errors.
- Do not calculate missing values as zero in API clients or visualizations.
