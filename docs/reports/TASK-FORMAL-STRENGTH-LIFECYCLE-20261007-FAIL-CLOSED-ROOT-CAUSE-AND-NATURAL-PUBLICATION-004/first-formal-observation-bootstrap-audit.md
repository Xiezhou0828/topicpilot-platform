# First Formal observation bootstrap audit

## Result

`BOOTSTRAP_PRESENT_NO_DEFECT`.

The approved implementation has an explicit `_prior_or_bootstrap` path. If no prior published Formal Lifecycle state exists for a Topic, it returns a `BASE` initialization record for the current evaluation date with zero prior trading days and the `FORMAL_BASE_BOOTSTRAP_V1` initialization contract. The first successful observation can therefore establish a legitimate current Formal observation without historical reconstruction.

The existing tests cover:

- first eligible Formal observation bootstrapping from BASE;
- incomplete first observation remaining unavailable;
- missing history not being silently treated as an observation;
- no historical replay as a substitute for current evidence.

Strength is computed from the current authorized snapshot and does not require historical Strength. Grade remains downstream of published Strength. Lifecycle history is used only after the current gate passes.

The 2026-10-07 failure is therefore not a bootstrap-semantics defect. It is current-input unavailability: 62 missing exact snapshots, 44 member-level price-evidence gaps at Topic-result granularity, and the pre-fix 6173 corporate-action projection gap.
