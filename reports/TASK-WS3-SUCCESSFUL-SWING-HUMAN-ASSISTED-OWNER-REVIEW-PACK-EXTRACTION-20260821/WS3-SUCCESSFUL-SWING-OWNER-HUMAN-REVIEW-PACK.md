# WS3 Successful Swing Owner Human Review Pack

This is an evidence-only, human-assisted review handoff. It consumes the completed canonical Successful Swing discovery artifacts and does not rerun research, create rules, or accept/reject a strategy.

## Section 1 — Research context

- Source task: `TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821`; source canonical head: `8faf8f89750c35b659686ebce317a9b1be0e9157`.
- Dataset: `603` instruments; `288881` accepted OHLCV rows; `2024-08-13 .. 2026-08-13`; SHA256 `e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4`.
- Existing discovery: `246689` eligible anchors; `35285` distinct episodes; `35285` matched controls; robust `11`; promising `88`.
- A-state context: A1-only `17.28%`; A2-related `36.05%`; A1→A2 `23.58%`; neither `46.67%`.
- Relative Strength: `UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK`; this is not a no-signal conclusion.
- This pack is discovery evidence only. A1/A2, definitions, thresholds, feature families, confirmatory validation, production, and NEXT_TASK were not changed.

## Section 2 — 11 Robust signals

| Rank | Family | Feature | Day | Stratum | SMD | Overlap |
|---:|---|---|---:|---|---:|---:|
| 1 | TREND_STRUCTURE | `ma_alignment_bearish` | D0 | T5_GE_3 | 0.3452 | 0.8352 |
| 2 | TREND_STRUCTURE | `ma_alignment_bearish` | D0 | T5_GE_5 | 0.2834 | 0.8677 |
| 3 | TREND_STRUCTURE | `ma_alignment_bearish` | D-1 | T5_GE_3 | 0.2792 | 0.871 |
| 4 | TREND_STRUCTURE | `ma_alignment_bearish` | D0 | T10_GE_3 | 0.2738 | 0.87 |
| 5 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-3 | T5_GE_3 | 0.2481 | 0.8884 |
| 6 | TREND_STRUCTURE | `ma_alignment_bearish` | D-1 | T5_GE_5 | 0.2232 | 0.9004 |
| 7 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-1 | T5_GE_3 | 0.2207 | 0.9023 |
| 8 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-1 | T5_GE_5 | 0.2177 | 0.903 |
| 9 | TREND_STRUCTURE | `ma_alignment_bearish` | D0 | T10_GE_5 | 0.2168 | 0.8982 |
| 10 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-3 | T5_GE_5 | 0.2076 | 0.9068 |
| 11 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D0 | T5_GE_3 | 0.204 | 0.9313 |

Full definitions, medians, stability, gradient labels, and interpretations: [ws3-owner-review-robust-signals.md](ws3-owner-review-robust-signals.md).

## Section 3 — Top 20 Promising signals

| Rank | Family | Feature | Day | Stratum | SMD | Why not robust |
|---:|---|---|---:|---|---:|---|
| 1 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-3 | T10_GE_3 | 0.1996 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 2 | TREND_STRUCTURE | `ma_alignment_bearish` | D-1 | T10_GE_3 | 0.1934 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 3 | TREND_STRUCTURE | `ma_alignment_bearish` | D-3 | T5_GE_3 | 0.1864 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 4 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D0 | T5_GE_5 | 0.1854 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 5 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-3 | T5_GE_10 | 0.181 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 6 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D0 | T5_GE_10 | 0.1792 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 7 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D-10 | T5_GE_10 | 0.1777 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 8 | VOLATILITY_COMPRESSION | `realized_vol_20` | D-20 | T5_GE_10 | 0.1769 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 9 | VOLUME_PARTICIPATION | `volume_contraction_state` | D-5 | T5_GE_3 | 0.1759 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 10 | TREND_STRUCTURE | `ma_alignment_bearish` | D0 | T5_GE_10 | 0.1723 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 11 | VOLATILITY_COMPRESSION | `realized_vol_20` | D-10 | T5_GE_10 | 0.166 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 12 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D-5 | T5_GE_10 | 0.1656 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 13 | TREND_STRUCTURE | `ma_alignment_bearish` | D-1 | T10_GE_5 | 0.1609 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 14 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D0 | T10_GE_10 | 0.1604 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 15 | VOLATILITY_COMPRESSION | `realized_vol_20` | D-10 | T5_GE_5 | 0.1587 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 16 | VOLATILITY_COMPRESSION | `true_range_pct` | D-10 | T5_GE_10 | 0.1577 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 17 | VOLATILITY_COMPRESSION | `realized_vol_20` | D-20 | T5_GE_5 | 0.1573 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 18 | VOLATILITY_COMPRESSION | `rolling_range_pct_5` | D-10 | T5_GE_10 | 0.1552 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 19 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D-20 | T5_GE_10 | 0.1514 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |
| 20 | VOLATILITY_COMPRESSION | `rolling_range_pct_20` | D-10 | T5_GE_5 | 0.1512 | existing classification reason: bounded_effect_requires_confirmatory_research; higher distribution overlap; weaker standardized effect size; confirmatory research remained out of scope |

Full machine-readable fields: [ws3-owner-review-top20-promising-signals.csv](ws3-owner-review-top20-promising-signals.csv). Ranking is the stable source-evidence reconstruction described in the robust-signals pack; it is not a new search.

## Section 4 — Feature-family summary

See [ws3-owner-review-feature-family-summary.md](ws3-owner-review-feature-family-summary.md). The family summary preserves discovery-only and benchmark limitations.

## Section 5 — Seven Owner reference cases

See [ws3-owner-review-reference-case-cards.md](ws3-owner-review-reference-case-cards.md) and [ws3-owner-review-reference-case-cards.json](ws3-owner-review-reference-case-cards.json).

## Section 6 — 20 Successful vs matched-control pairs

See [ws3-owner-review-success-control-pairs.md](ws3-owner-review-success-control-pairs.md) and [ws3-owner-review-success-control-pairs.csv](ws3-owner-review-success-control-pairs.csv). Control-side PIT feature values are not persisted in the source artifacts and remain explicitly unavailable.

## Section 7 — False-friend cases

See [ws3-owner-review-false-friend-cases.md](ws3-owner-review-false-friend-cases.md). `FALSE_FRIEND_EXTRACTION=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.

## Section 8 — Extreme success cases

See [ws3-owner-review-extreme-success-cases.md](ws3-owner-review-extreme-success-cases.md). `EXTREME_CASES_NOT_REPRESENTATIVE`.

## Section 9 — Human research question sheet

See [ws3-owner-human-research-question-sheet.md](ws3-owner-human-research-question-sheet.md). Questions are intentionally unanswered.

## Section 10 — Artifact index

| Artifact | Purpose |
|---|---|
| [ws3-owner-human-research-question-sheet.md](ws3-owner-human-research-question-sheet.md) | Supporting owner-review artifact |
| [ws3-owner-review-extraction-manifest.json](ws3-owner-review-extraction-manifest.json) | Supporting owner-review artifact |
| [ws3-owner-review-extreme-success-cases.md](ws3-owner-review-extreme-success-cases.md) | Supporting owner-review artifact |
| [ws3-owner-review-false-friend-cases.md](ws3-owner-review-false-friend-cases.md) | Supporting owner-review artifact |
| [ws3-owner-review-feature-family-summary.md](ws3-owner-review-feature-family-summary.md) | Supporting owner-review artifact |
| [ws3-owner-review-pack-summary.json](ws3-owner-review-pack-summary.json) | Supporting owner-review artifact |
| [ws3-owner-review-reference-case-cards.json](ws3-owner-review-reference-case-cards.json) | Supporting owner-review artifact |
| [ws3-owner-review-reference-case-cards.md](ws3-owner-review-reference-case-cards.md) | Supporting owner-review artifact |
| [ws3-owner-review-robust-signals.csv](ws3-owner-review-robust-signals.csv) | Supporting owner-review artifact |
| [ws3-owner-review-robust-signals.md](ws3-owner-review-robust-signals.md) | Supporting owner-review artifact |
| [ws3-owner-review-source-artifact-inventory.csv](ws3-owner-review-source-artifact-inventory.csv) | Supporting owner-review artifact |
| [ws3-owner-review-source-artifact-inventory.md](ws3-owner-review-source-artifact-inventory.md) | Supporting owner-review artifact |
| [ws3-owner-review-success-control-pairs.csv](ws3-owner-review-success-control-pairs.csv) | Supporting owner-review artifact |
| [ws3-owner-review-success-control-pairs.md](ws3-owner-review-success-control-pairs.md) | Supporting owner-review artifact |
| [ws3-owner-review-top20-promising-signals.csv](ws3-owner-review-top20-promising-signals.csv) | Supporting owner-review artifact |

### Stop boundary

No new research conclusion is made. This pack is returned to Owner for human review and Strategy Review input only; no accepted/rejected owner decision is made here.
