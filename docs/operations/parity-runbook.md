# Ten-trading-day parity runbook

## Goal

Demonstrate that the PostgreSQL read model reproduces the approved private
snapshot for ten consecutive trading days without writing to the formal system.
Passing this exercise is evidence only; it does not authorize a source-of-truth
cutover.

## Preconditions

- The private bundle is stored outside the public repository.
- The operator has read-only access to the validated source snapshot.
- Migrations, importer, and parity query revision are fixed for the run.
- The target database is private and separate from the public synthetic demo.
- The comparison output is sanitized before any public portfolio use.

## Daily procedure

1. Record the Taipei trading date, source snapshot version/hash, code revision,
   database target alias, and operator in a private copy of the template.
2. Export the private `enterprise_bundle.v1` after the existing validation and
   publication gates complete.
3. Validate manifest, artifact hashes, classification, schemas, and references.
4. Import the bundle transactionally. Re-run the exact bundle and record that
   the second execution is a no-op.
5. Compare the approved measures below using the same business definitions.
6. Investigate every discrepancy; do not overwrite source or database values to
   force equality.
7. Sign off PASS only when all blocking measures match and nullable-value rules
   are preserved.

## Required comparisons

| Domain | Blocking measures |
|---|---|
| Bundle | Contract/version/hash, source data date, artifact row counts |
| Stocks | Natural-key set, active status, primary labels |
| Topics | Slug set, enabled status, hierarchy edges |
| Relations | Stock/topic/relation-type natural-key set and weight nullability |
| Market snapshots | Market keys, counts, availability/null states |
| Stock snapshots | Code/date keys and approved core observations |
| Topic snapshots | Slug/date keys, score/grade/state/coverage nullability |
| Strategies | Six keys, run identity, candidate/selected counts |
| Candidates | Strategy/date/rank/stock keys and approved values |
| Performance | Strategy/date/horizon keys, samples and nullable metrics |
| Data quality | Error/warning counts and stable event codes |
| Compatibility API | Existing Snapshot validator accepts the generated response |

Numeric comparisons must use contract precision, not display-formatted strings.
Do not treat two missing values as zero equality.

## Pass criteria

A trading day passes when:

- all key sets and blocking row counts match;
- exact fields match after documented normalization;
- decimal differences are within contract precision only;
- no source `null` became zero, empty string, or false;
- importer replay is a no-op;
- no unexplained error-level quality event exists;
- API compatibility validation passes.

Ten PASS trading days must be consecutive among actual trading days. A market
holiday does not break the sequence. A FAIL resets the consecutive counter after
the correction is deployed and verified on the next ten trading days.

## Handling discrepancies

Classify each discrepancy as:

- `SOURCE_EXPORT`: exporter omitted or transformed a valid source value.
- `CONTRACT`: schema/semantic ambiguity.
- `IMPORTER`: transaction, mapping, null, or reference error.
- `QUERY_VIEW`: SQL view or API projection error.
- `SOURCE_QUALITY`: approved source already contains the issue.
- `EXPECTED_NORMALIZATION`: documented and approved transformation.

Any proposed business-rule change is out of migration scope and requires PM
review. Attach a sanitized diff summary and link to the corrective revision.

## Final report

After day ten, summarize:

- date range and revisions;
- ten daily PASS records;
- resolved discrepancies and regression coverage;
- remaining non-blocking differences;
- security/data-classification review;
- recommendation: continue parallel operation, extend validation, or request a
  separate source-of-truth decision.

Use [the template](parity-template.md) for each day and the final summary.
