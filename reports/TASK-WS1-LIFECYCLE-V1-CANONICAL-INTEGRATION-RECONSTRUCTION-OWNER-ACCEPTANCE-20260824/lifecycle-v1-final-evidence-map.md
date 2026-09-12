# Lifecycle V1 final evidence map

| Owner dimension | Reconstruction evidence |
|---|---|
| Participation | Overall, Lead/Core, Related, authority-weighted positive breadth, coverage, observed/expected count |
| Intensity | Average change, strong breadth, weak ratio, Lead/Core average change |
| Progression | Meaningful expansion, segment, segment entry/anchor, days since expansion |
| Trajectory | Running peak drawdown, trajectory recovery, stage memory and decline context |

The main dataset is `lifecycle-v1-historical-reconstruction.csv`. The member-level sidecar is `lifecycle-v1-member-evidence.csv`; it contains same-day canonical close, previous close, change, role, role source, and missing-evidence status for the frozen current membership projection.

Every row is marked `CURRENT_TAXONOMY_HISTORICAL_V1_RECONSTRUCTION`, `RETROSPECTIVE_RESEARCH_ONLY`, and `UNPUBLISHED_RESEARCH_ARTIFACT`. Current membership is projected backward across the requested window; no PIT claim is made. The Owner pack contains raw component evidence only and leaves Owner judgment fields blank.
