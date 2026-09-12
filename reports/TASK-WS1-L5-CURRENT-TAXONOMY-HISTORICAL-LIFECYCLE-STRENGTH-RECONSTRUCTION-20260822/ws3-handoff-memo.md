# WS3 handoff memo — L5 reconstructed research panel

## Eligibility

`READY_FOR_RESEARCH=YES` when consuming the panel as retrospective evidence
only. The panel has `16250` Topic×Date rows across
`130` topics and `125` trading dates,
with normalized replay status `YES`.

## Approved use

WS3 may condition descriptive or pre-registered expectancy analysis on the raw
Strength vector within lifecycle stages:

- `positive_breadth`
- `strong_breadth`
- `weak_ratio`
- `average_change_pct`

`leader_change_pct` is proxy/context only. Keep `coverage`, `confidence`,
sample size, data status, and lineage as quality controls; they are not
Strength dimensions.

## Required guardrails

- Keep `source_class=CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION` visible in every panel and result.
- Do not call this PIT truth, FORWARD_SHADOW, or formal publication.
- Do not mix with formal/PIT performance claims without a separately approved
  authority and validation design.
- Keep rows with `PARTIAL`, `UNKNOWN`, and `FAIL_CLOSED` lineage explicit;
  missing future outcomes must remain missing rather than zero.
- Do not change A2, Legacy-5, or BOTH definitions, eligibility, entry/exit,
  position logic, thresholds, or production policy.
- Do not create a Strength label, dimension label, overall level, or score.

## Research question

The next bounded question is whether the raw vector adds conditional
information within the same Lifecycle stage for the already-frozen
`A2 / Legacy-5 / BOTH` research cohorts. This is an expectancy study, not a
strategy rewrite or threshold optimization.
