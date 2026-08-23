"""Focused contract tests for the frozen A1 confirmatory-validation workflow."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from topicpilot_api.research import ws3_core_v0_a1_quality_filter_confirmatory_validation as confirm


class ConfirmatoryValidationContractTests(unittest.TestCase):
    def test_candidate_freeze_is_deterministic_and_complete(self) -> None:
        first = confirm.build_confirmatory_freeze()
        second = confirm.build_confirmatory_freeze()
        self.assertEqual(first, second)
        self.assertTrue(first["created_before_confirmatory_outcome_review"])
        self.assertEqual(first["candidate_count"], 7)
        self.assertEqual(first["single_feature_candidate_count"], 6)
        self.assertEqual(first["combination_candidate_count"], 1)
        candidate_ids = {candidate["candidate_id"] for candidate in first["candidates"]}
        self.assertTrue(set(confirm.REQUIRED_LEADING_CANDIDATES).issubset(candidate_ids))
        self.assertEqual(first["confirmatory_independence"]["level"], "BOUNDED")

    def test_thresholds_and_operators_are_immutable_freeze_values(self) -> None:
        freeze = confirm.build_confirmatory_freeze()
        expected = {
            "recent_20_high_proximity__UPPER_GE_Q30": (">=", "Q30"),
            "return_5d__LOWER_LE_Q60": ("<=", "Q60"),
            "true_range_pct__LOWER_LE_Q70": ("<=", "Q70"),
        }
        for candidate in freeze["candidates"]:
            if candidate["candidate_id"] in expected:
                self.assertEqual(
                    (candidate["operator"], candidate["threshold_quantile"]),
                    expected[candidate["candidate_id"]],
                )
        self.assertTrue(freeze["protocol"]["no_retuning"])
        self.assertTrue(freeze["protocol"]["no_new_feature_search"])

    def test_pit_and_outcome_boundaries_are_explicit(self) -> None:
        freeze = confirm.build_confirmatory_freeze()
        for candidate in freeze["candidates"]:
            self.assertTrue(candidate["pit_validity"])
            self.assertNotIn("future_return", json.dumps(candidate).lower())
            self.assertNotIn("future_high", json.dumps(candidate).lower())
            self.assertNotIn("future_low", json.dumps(candidate).lower())
        self.assertTrue(freeze["protocol"]["forward_outcomes_are_evaluation_only"])
        self.assertTrue(freeze["protocol"]["raw_a1_preserved"])

    def test_raw_cohort_authority_is_preserved(self) -> None:
        freeze = confirm.build_confirmatory_freeze()
        authority = freeze["a1_cohort_authority"]
        self.assertEqual(authority["raw_a1_count"], 700)
        self.assertEqual(authority["successful_a1_count"], 386)
        self.assertEqual(authority["failed_breakout_a1_count"], 214)
        self.assertTrue(authority["definitions_reused"])
        self.assertTrue(authority["taxonomy_reused"])

    def test_retention_and_success_failure_rate_calculation(self) -> None:
        baseline = [
            {"cohort": "SUCCESSFUL_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "SUCCESSFUL_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "FAILED_BREAKOUT_A1", "returns": {}, "event_excluded_horizons": []},
            {"cohort": "FAILED_BREAKOUT_A1", "returns": {}, "event_excluded_horizons": []},
        ]
        metrics = confirm._primary_and_forward(baseline[:2], baseline)
        self.assertEqual(metrics["filtered"]["retention_rate"], 0.5)
        self.assertEqual(metrics["filtered"]["success_rate"], 1.0)
        self.assertEqual(metrics["success_rate_uplift"], 0.5)
        self.assertEqual(metrics["failed_breakout_rate_reduction"], 0.5)
        self.assertEqual(len(metrics["filtered"]["success_rate_ci95"]), 2)

    def test_temporal_and_july_segmentation_is_frozen(self) -> None:
        rows = [
            {"signal_date": date(2026, 6, 30)},
            {"signal_date": date(2026, 7, 1)},
            {"signal_date": date(2026, 8, 1)},
        ]
        self.assertEqual(len(confirm._segment_rows(rows, "TRAIN")), 1)
        self.assertEqual(len(confirm._segment_rows(rows, "VALIDATION")), 1)
        self.assertEqual(len(confirm._segment_rows(rows, "HOLDOUT")), 1)

    def test_market_split_and_concentration_are_explicit(self) -> None:
        rows = []
        for index in range(4):
            rows.append(
                {
                    "cohort": "SUCCESSFUL_A1" if index < 2 else "FAILED_BREAKOUT_A1",
                    "market": "TPE" if index < 2 else "TWO",
                    "signal_date": date(2026, 8, 1 + index),
                    "instrument_id": f"instrument-{index}",
                    "returns": {},
                    "event_excluded_horizons": [],
                }
            )
        market = confirm._market_metrics(rows, rows)
        concentration = confirm._concentration(rows)
        self.assertEqual(set(market), {"TPE", "TWO"})
        self.assertEqual(concentration["resolved_primary_count"], 4)
        self.assertEqual(concentration["active_filtered_dates"], 4)
        self.assertIn(concentration["date_concentration_classification"], {"LOW", "MEDIUM", "HIGH"})

    def test_artifact_hash_normalization_is_reproducible(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            for name in confirm.ANALYTICAL_ARTIFACT_NAMES:
                (first / name).write_bytes(b"header\nvalue\n")
                (second / name).write_bytes(b"header\r\nvalue\r\n")
            self.assertEqual(confirm._normalized_hashes(first), confirm._normalized_hashes(second))


if __name__ == "__main__":
    unittest.main()
