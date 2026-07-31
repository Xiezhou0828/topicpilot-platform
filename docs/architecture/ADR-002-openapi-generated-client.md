# ADR-002: Generate the TypeScript client from FastAPI OpenAPI

Status: Accepted

## Context

The API and React application are implemented in different languages. Manually
maintaining matching Python response models and TypeScript interfaces would
allow silent drift, especially around nullable numeric values and pagination.

## Decision

FastAPI's generated OpenAPI document is the public API contract. A committed,
normalized schema and generated TypeScript client live under
`packages/api-client/`. CI performs two checks:

1. The live application schema contains all required v1 read-only endpoints.
2. The normalized live schema must match the committed baseline.

An intentional API change updates response models, tests, OpenAPI baseline, and
generated client in the same pull request. The frontend imports the generated
wire interfaces, then maps them into UI-specific presentation models. A copy is
kept inside `apps/web` so the independently deployable Sites artifact remains
self-contained.

## Consequences

- Nullable values and error shapes remain consistent across languages.
- API changes become reviewable diffs instead of runtime surprises.
- The client can be regenerated without running a public server.
- Generated files must not be edited by hand.
- CI regenerates both the package declaration and the self-contained web copy;
  any diff fails the build.

## Generation acceptance

- The OpenAPI document is deterministic after JSON key normalization.
- The generator command and version are documented beside the client package.
- A clean checkout can regenerate without contacting production.
- Regeneration produces no diff when the API contract is unchanged.
- The generated client test covers one success response and one RFC 9457-style
  `application/problem+json` response.
