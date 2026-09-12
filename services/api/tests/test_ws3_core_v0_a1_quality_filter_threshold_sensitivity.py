"""Focused contract tests for the WS3 A1 threshold-sensitivity research task."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from topicpilot_api.research import ws3_core_v0_a1_quality_filter_threshold_sensitivity as review
from topicpilot_api.research.ws3_core_v0_a1_ex_ante_discrimination import (
    build_feature_manifest,
)


class ThresholdSensitivityContractTests(unittest.TestCase):
    def _prior_stub(self) -> dict[str, object]:
        return {
            "top_findings": {
                name: {
                    "category": "TEST_PRIOR_FAMILY",
                    "classification": "ROBUST_CANDIDATE",
                    "direction": "HIGHER_IN_SUCCESS",
                    "standardized_effect_size": 0.25,
                    "validation_consistent": "YES",
                    "date_regime_confounding": "NO",
                }
                for name in review.PRIMARY_SELECTED_FEATURES
            }
        }

    def test_primary_selection_is_deterministic_and_fixed(self) -> None:
        first = review.select_primary_features(self._prior_stub())
        second = review.select_primary_features(self._prior_stub())
        self.assertEqual(first, second)
        self.assertEqual(
            [row["feature_name"] for row in first], list(review.PRIMARY_SELECTED_FEATURES)
        )

    def test_quantile_grid_is_coarse_and_percentile_is_deterministic(self) -> None:
        self.assertEqual(review.QUANTILE_LABELS, ("Q20", "Q30", "Q40", "Q50", "Q60", "Q70", "Q80"))
        self.assertEqual(review._percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5), 3.0)
        self.assertEqual(review._percentile([1.0, 2.0, 3.0], 0.2), 1.4)

    def test_region_metrics_reports_retention_and_primary_rates(self) -> None:
        baseline = [
            {"cohort": "SUCCESSFUL_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "SUCCESSFUL_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "FAILED_BREAKOUT_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "FAILED_BREAKOUT_A1", "returns": {}, "event_excluded_horizons": []},
        ]
        selected = baseline[:2]
        metrics = review._region_metrics(selected, baseline)
        self.assertEqual(metrics["retained_a1_count"], 2)
        self.assertEqual(metrics["resolved_primary_count"], 2)
        self.assertEqual(metrics["retention_rate"], 0.5)
        self.assertEqual(metrics["primary_retention_rate"], 0.5)
        self.assertEqual(metrics["filtered_success_rate"], 1.0)

    def test_segment_isolation_uses_frozen_date_segments(self) -> None:
        rows = [
            {"signal_date": date(2026, 6, 30)},
            {"signal_date": date(2026, 7, 1)},
            {"signal_date": date(2026, 8, 3)},
        ]
        self.assertEqual(len(review._segment_rows(rows, "TRAIN")), 1)
        self.assertEqual(len(review._segment_rows(rows, "VALIDATION")), 1)
        self.assertEqual(len(review._segment_rows(rows, "HOLDOUT")), 1)

    def test_selected_features_are_point_in_time_and_not_future_derived(self) -> None:
        manifest = {
            row["feature_name"]: row for row in build_feature_manifest()
        }
        for name in review.PRIMARY_SELECTED_FEATURES:
            spec = manifest[name]
            self.assertTrue(spec["point_in_time_available"])
            self.assertEqual(spec["timestamp_rule"], "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP")
            serialized = json.dumps(spec).lower()
            self.assertNotIn("future_return", serialized)
            self.assertNotIn("future_high", serialized)
            self.assertNotIn("future_low", serialized)

    def test_combination_search_is_bounded_and_pairwise(self) -> None:
        self.assertLessEqual(len(review.PAIR_CANDIDATES), review.MAX_COMBINATIONS)
        self.assertTrue(all(len(pair) == 2 for pair in review.PAIR_CANDIDATES))

    def test_artifact_hashes_normalize_line_endings(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lf_dir = root / "lf"
            crlf_dir = root / "crlf"
            lf_dir.mkdir()
            crlf_dir.mkdir()
            for name in review.ANALYTICAL_ARTIFACT_NAMES:
                (lf_dir / name).write_bytes(b"header\nvalue\n")
                (crlf_dir / name).write_bytes(b"header\r\nvalue\r\n")
            self.assertEqual(
                review._artifact_hashes(lf_dir), review._artifact_hashes(crlf_dir)
            )


if __name__ == "__main__":
    unittest.main()
