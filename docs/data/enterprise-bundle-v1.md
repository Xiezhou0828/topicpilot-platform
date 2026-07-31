# `enterprise_bundle.v1` contract overview

## Purpose

The enterprise bundle is the only supported data exchange between the private
formal workflow and this read platform. It is also used by public synthetic
fixtures, tests, CI, and local demos. The API never reads Google Sheets during
a request.

## Directory shape

```text
bundle/
├─ manifest.json
├─ stocks.json
├─ topics.json
├─ topic_hierarchy.json
├─ stock_topic_relations.json
├─ daily_snapshots.json
├─ strategy_candidates.json
└─ strategy_performance.json
```

JSON Schemas under `fixtures/schema/` are authoritative for field shape. This
document defines cross-file and operational rules that JSON Schema alone cannot
express.

## Manifest responsibilities

The manifest identifies:

- contract version (`enterprise_bundle.v1`);
- globally unique bundle version;
- Taipei trading date and UTC generation timestamp;
- source kind/name and public-data classification;
- the exact logical-name-to-filename map for all seven artifacts.

The importer calculates artifact SHA-256 values, UTF-8 byte sizes, logical row
counts, and an overall bundle hash from the exact validated inputs, then stores
them in `source_artifacts` and `ingestion_runs`. Producers must write
deterministic UTF-8 JSON with no secrets or environment-specific paths.

## Validation order

1. Require the exact eight filenames and reject unexpected private artifacts.
2. Validate manifest contract version and allowed classification.
3. Verify SHA-256, byte size, and row count for each artifact.
4. Validate each JSON document against its matching schema.
5. Validate stable natural keys and cross-file references.
6. Validate strategy keys against `MAS`, `MAV`, `TMC`, `BB`, `PB`, and `KD`.
7. Begin one database transaction and write dimensions, facts, lineage, and
   quality events.
8. Commit the complete bundle or roll back every change.

## Cross-file invariants

- Stock code and topic slug are unique and non-empty.
- Every hierarchy endpoint refers to a topic in `topics.json`; a topic cannot be
  its own parent.
- Every stock-topic relation refers to an existing stock and topic.
- Every daily stock/topic fact uses the manifest trading date unless explicitly
  carrying a historical date permitted by the schema.
- Every strategy candidate references an existing stock and matching strategy
  run identity.
- Performance horizons are preserved as contract values; unknown horizons are
  rejected rather than guessed.
- Missing numeric data remains JSON `null` and becomes SQL `NULL`.
- Numeric zero is valid only when the source explicitly provides zero.

## Idempotency and conflicts

| Existing state | Incoming bundle | Result |
|---|---|---|
| No matching version | Valid version/hash | Import and record `completed` |
| Same version and hash | Identical bytes | Successful no-op |
| Same version, different hash | Mutated content | Reject as conflict |
| Failed prior transaction | Corrected new version | Import normally |

Changing an already published bundle requires a new `bundle_version`; silently
reusing a version destroys lineage and is prohibited.

## Classification

Public fixtures must declare a synthetic/public-safe classification. Private
formal exports must be stored outside the public repository and should declare
a private classification accepted only when the operator explicitly enables a
private import mode. Classification is not a substitute for content review.

## Compatibility

Backward-compatible additions require optional fields and a minor producer
revision while preserving `enterprise_bundle.v1`. Renaming, changing meaning,
changing nullability, or removing a field requires a new contract version and
an ADR. Consumers must reject unknown major contract versions.
