# TopicPilot Platform collaboration rules

This repository is the standalone, public portfolio implementation of TopicPilot's enterprise read platform.

## Hard boundaries

- Google Sheets and the existing TopicPilot repository remain the formal source of truth.
- This repository is read-only with respect to formal TopicPilot data.
- Public fixtures must be synthetic and must not contain credentials, holdings, licensed market data, private news text, or private URLs.
- API routes are read-only in v1. Authentication, trading, order execution, and admin writes are out of scope.
- Missing numeric values stay `null`; they must never be silently converted to zero.
- Every import is versioned, hashed, idempotent, and transactional.

## Delivery discipline

- Work only inside the modification whitelist of the active work order.
- Run targeted tests first and report changed files and evidence.
- Do not change product scoring rules or strategy definitions while moving data.
- The stable strategy identifiers are `MAS`, `MAV`, `TMC`, `BB`, `PB`, and `KD`.
