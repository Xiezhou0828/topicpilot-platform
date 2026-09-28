# TASK-REFERENCE-BUNDLE-REGRESSION-CLOSURE-001

## Closure state

This report records the reference-bundle audit from canonical `origin/main`
SHA `c3542a900d6c46e07bc4243804e9705475023316`, fetched on 2026-09-29, and
the bounded repair in this worktree. No Production database, deployed
runtime, migration, or remote branch was changed during the audit.

## A. Reference bundle inventory

| Bundle ID | Path | Format | Consumers | Generator / update path | Source authority | Status |
|---|---|---|---|---|---|---|
| `tw-reference-v1` | `services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/` | `manifest.json` plus ten canonical JSON data files | reference bootstrap/preflight, market data consumers, corporate-action research tests and artifact | `build_bundle_from_sources` → `write_bundle`; explicit `reference_bundle_cli generate` | manifest-recorded approved stock export, TWSE calendar, status evidence, adjustment governance, plus governed rollover metadata | `CANONICAL_ACTIVE` |
| `tw-reference-v1-expansion-20260912` | `services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1-expansion-20260912/` | same bundle format | no active runtime or test consumer found; used by the expansion builder as a derived handoff | `tools/build_canonical_instrument_expansion_20260912.py` | owner-approved instrument expansion inputs and historical listing evidence | `GENERATED_DERIVED` / inactive |
| `REC-A1-CA-EVENTS-V0` | `reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json` | normalized JSON research artifact | `test_corporate_action_dataset.py` and research-only consumers | bounded import builders plus `export_dataset_document` | exact `referenceDataVersion` from the active canonical bundle | `GENERATED_DERIVED` |

Other files named `fixture`, `snapshot`, `schema`, or `reference` are ordinary
test/demo/research evidence or database migration inputs, not members of the
canonical reference-bundle family. No duplicate active bundle consumer was
found for the expansion directory.

### Required inventory fields

| Bundle ID | Version field | Normalization / ordering | Migration dependency | Last-known update commit | Current status |
|---|---|---|---|---|---|
| `tw-reference-v1` | `manifest.referenceDataVersion` | canonical UTF-8 JSON; approved stock-export order; explicit calendar, lifecycle, adjustment, and status ordering | reference-only bootstrap lineage in migrations 0005, 0020, 0028, 0033, 0036; no closure migration | `4e09384` (active bundle path history) | active canonical bundle |
| `tw-reference-v1-expansion-20260912` | `manifest.referenceDataVersion` | same serializer; generated expansion handoff | none; inactive and not registered as runtime authority | `bfbad80` | derived inactive handoff |
| `REC-A1-CA-EVENTS-V0` | each event `reference_version` plus dataset metadata | normalized research JSON; content hash over canonical payload | consumes the active bundle; no schema migration | `d5ce718` | derived research artifact |

### Canonical artifact metadata

The active bundle currently records:

- schema version: `reference-bundle.v1`;
- reference version: `tw-reference-v1-rollover-55684037eef58f10`;
- bundle SHA-256: `57247b5a861c0ae3b82792a128d275b75742f5cfbedaf1ad6348cc2be9d70fd8`;
- derived universe: 507 instruments, TPE 314 and TWO 193;
- lifecycle events: 5; calendar dates: 24; trading statuses: 8.

The exact version is read from the canonical manifest by
`canonical_bundle_version`; consumers must not reconstruct it from the
directory name or use the retired family alias as an exact registry version.

### Normalization and ordering policy

- JSON is UTF-8, indented, key-sorted, and newline-terminated by
  `write_bundle`; file hashes are recorded in the manifest.
- Instrument rows preserve the approved stock export order because that order
  is part of the source artifact lineage; duplicate market/code identities are
  rejected.
- Calendar rows are ordered by source category: sorted holidays followed by
  sorted suspended dates.
- Lifecycle rows are ordered by instrument code and effective date.
- Adjustment codes are sorted; the trading-status catalogue uses an explicit
  legacy-compatible order and appends unknown future codes deterministically.
- No current timestamp, UUID, filesystem path, locale, or database row order
  is generated into the bundle. Canonical instrument UUID derivation is
  UUIDv5 from the market-aware identity and is separate from this JSON digest.

## B. Current failure matrix

Initial Python 3.12 backend run on the audited canonical SHA:

`790 passed / 59 skipped / 15 failed`.

Ten failures formed one reference-bundle family:

| Test | Bundle / artifact | Difference | Classification | Cause |
|---|---|---|---|---|
| `test_versioned_artifact_loads_against_canonical_reference_bundle` | `tw-reference-v1` + REC-A1 artifact | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | consumer and artifact used `tw-reference-v1`; manifest used governed rollover version |
| `test_control_cases_preserve_identity_and_effective_date_boundaries` | `instrument_lifecycles.json` | first row was 1563, not 6806 | `TEST_BUG` / ordering assumption | test used positional index instead of stable identity |
| `test_coverage_matrix_keeps_tpex_partial_with_method_gaps_and_freeze_closed` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_identity_coverage_does_not_infer_no_event_from_absent_export_rows` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_identity_coverage_requires_explicit_empty_set_proof_for_no_event` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_reviewed_residual_uncertainty_is_metadata_only_and_can_pass_freeze_gate` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_reviewed_residual_uncertainty_does_not_override_known_integrity_failure` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_coverage_artifact_is_metadata_only_and_hashable` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_freeze_gate_refuses_partial_twse_even_if_tpex_is_closed` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |
| `test_owner_bounded_csv_normalization_splits_explicit_tpex_components_and_keeps_outside` | same | exact version mismatch | `AUTHORITY_SOURCE_CHANGE` | same shared loader guard |

The other five initial failures were unrelated WS3 research tests whose
historical report inputs are absent from this canonical checkout:
`ConfirmatoryValidationContractTests` (four methods) and
`test_a1_forward_contract_preserves_exact_seven_candidates`. They are
classified `PRE_EXISTING` / `UNRELATED`, not hidden under the bundle label.

## C. Root-cause analysis

The recurring cluster began when the reference registry moved from the family
alias to immutable rollover versions. The canonical manifest on `main` has
continued to identify the active 507-row bundle with
`tw-reference-v1-rollover-55684037eef58f10`, while the research consumer kept
the pre-transition alias in a module constant and in the committed REC-A1
artifact. Nine tests therefore failed at one shared version guard. The tenth
failure was a brittle positional assertion exposed by the intentional addition
of the 1563 lifecycle event.

The generator also had an implicit set-order boundary for status catalogues.
The committed active bundle preserved the established legacy order with the
new `TERMINATED` code appended, while `sorted(set(...))` could place it before
`UNKNOWN`. The generator now has an explicit order, so future regeneration is
byte-stable without changing status semantics.

No timestamp, UUID, hash-randomization, locale, path, or database-order
nondeterminism was found in the active bundle writer. Hashes are content
hashes over the canonical data payload and file bytes; the reference version
is registry lineage metadata, not a substitute for the bundle digest.

## D. Canonical authority map

1. Formal reference-registry transition and bootstrap contracts define
   immutable versioning and the reference-only write set.
2. The checked-in active bundle manifest and data files are the current
   generated evidence of that contract.
3. `build_bundle_from_sources` and `write_bundle` are the offline generator
   and serializer.
4. Research artifacts consume the exact manifest version and must be
   regenerated when the canonical authority intentionally rolls over.
5. Tests validate the contract; they do not define the reference version.

The expansion directory is not active merely because it is committed. It has
no activation/registry consumer in the current source tree and remains a
derived, inactive handoff.

## E. Regeneration and check flow

Non-mutating validation of the checked-in artifact:

```console
PYTHONPATH=services/api/src python -m topicpilot_api.reference_bundle_cli check \
  --bundle-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1
```

With all approved source inputs, `check` regenerates in a temporary directory
and compares every artifact. A mismatch returns non-zero and reports
`artifactPath`, `semanticPath`, `expected`, and `actual`. It never overwrites
the target directory.

Intentional update only:

```console
PYTHONPATH=services/api/src python -m topicpilot_api.reference_bundle_cli generate \
  --stock-source <approved-stock-export.tsv> \
  --calendar-source <approved-calendar.json> \
  --evidence-source <approved-evidence.json> \
  --reference-version <reviewed-target-version> \
  --output-dir services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1
```

When an immutable active registry already exists with a different hash, use
the documented transition flow; do not overwrite the old version or invent a
migration to satisfy a fixture. Updating is valid only for an intentional
contract, schema, serializer, or authority change. “Test failed”, “CI is
red”, and “expected output is inconvenient” are invalid update reasons.

CI runs the non-mutating check and never auto-updates bundles. The current
checkout does not contain the raw approved source files named in the active
manifest, so source-input regeneration remains an explicit operator/review
step; the checked-in serializer check is always available.

## F. Regression test report

Added/preserved focused coverage:

- exact dataset lineage equals the active manifest version;
- same source inputs produce byte-identical bundle files;
- lifecycle checks select by stable identity, not array position;
- canonical status ordering is explicit;
- stale generated output causes check-mode failure with semantic location;
- explicit write mode repairs the stale output and a subsequent check passes.

The canonical check itself returned
`CURRENT_BUNDLE_MATCHES_CANONICAL_GENERATOR=YES` after the repair.

Final verification on the repaired worktree: the focused reference suite passed
31 tests; the full backend suite reported `803 passed / 59 skipped / 5 failed`.
The remaining five failures are the same unrelated WS3 tests with absent
historical report inputs; reference-bundle failure count is zero.

## G. Governance report

- Product semantics changed: `NO`.
- Migration created/applied: `NO` / `NO`.
- Production DB mutated: `NO`.
- Deployed or pushed: `NO` / `NO`.
- Reference data rows regenerated: `NO`; only consumer lineage metadata and
  the generated REC-A1 artifact hash were reconciled.
- Active bundle count: 1; inactive derived bundle count: 1.
- Bundle ownership: reference registry/data authority; research artifact is a
  downstream generated consumer.
- CI policy: fail on check drift; never auto-update.

Future feature tasks should treat any reference failure as a typed authority
or serialization diagnosis first. They should run the check, inspect the
manifest version and bundle hash, and update a reference only after proving
the canonical source/contract changed.
