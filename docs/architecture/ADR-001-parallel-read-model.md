# ADR-001: Parallel PostgreSQL read model

Status: Accepted

## Decision

TopicPilot Platform consumes a versioned export from the existing validated snapshot process. PostgreSQL is a rebuildable read model, not the formal source of truth. The existing Google Sheets, Apps Script, Python engines, R2 publication, and production website continue operating independently.

The public deployment is seeded only from synthetic `enterprise_bundle.v1` data. Private formal data may be imported locally with private configuration, but the API never queries Google Sheets during a request.

## Consequences

- Migration can be verified without a big-bang cutover.
- Data lineage and parity are measurable through import runs and source hashes.
- A later source-of-truth change requires a separate PM decision after at least ten consecutive trading days of parity.
- The first public release has no authentication or write API.
