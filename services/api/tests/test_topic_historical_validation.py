from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    CALIBRATION_REVIEW_STATUS,
    OBSERVED,
    CandidateValidationSummary,
    HistoricalTopicOutcome,
    HistoricalValidationDataset,
    ScoreObservation,
    export_historical_validation_report,
    run_historical_validation,
)
from topicpilot_api.topic_engine.research import FormulaResearchValidationError

pytestmark = pytest.mark.research


def _dataset() -> HistoricalValidationDataset:
    return HistoricalValidationDataset(
        "validation-demo",
        "v1",
        ("synthetic-score-output", "synthetic-outcomes"),
        (
            ScoreObservation(
                "candidate-a", "v1", "t1", date(2026, 8, 1), "SCORED", "ELIGIBLE", 1.0, "B"
            ),
            ScoreObservation(
                "candidate-a", "v1", "t2", date(2026, 8, 1), "SCORED", "ELIGIBLE", 2.0, "A"
            ),
            ScoreObservation(
                "candidate-a", "v1", "t3", date(2026, 8, 1), "DEFERRED", "INELIGIBLE", None, None
            ),
            ScoreObservation(
                "candidate-b", "v1", "t1", date(2026, 8, 1), "SCORED", "ELIGIBLE", 3.0, "A"
            ),
            ScoreObservation(
                "candidate-b", "v1", "t2", date(2026, 8, 1), "SCORED", "ELIGIBLE", 2.0, "A"
            ),
            ScoreObservation(
                "candidate-b", "v1", "t3", date(2026, 8, 1), "DEFERRED", "INELIGIBLE", None, None
            ),
        ),
        (
            HistoricalTopicOutcome(
                "t1", date(2026, 8, 1), "T+5", date(2026, 8, 8), OBSERVED, 10.0, "outcome-1"
            ),
            HistoricalTopicOutcome(
                "t2", date(2026, 8, 1), "T+5", date(2026, 8, 8), OBSERVED, 20.0, "outcome-2"
            ),
            HistoricalTopicOutcome(
                "t3", date(2026, 8, 1), "T+5", None, "MISSING", None, "outcome-3"
            ),
        ),
    )


def test_validation_is_deterministic_and_reports_descriptive_metrics_only():
    first = run_historical_validation(_dataset(), validation_runtime_version="validator.v1")
    second = run_historical_validation(_dataset(), validation_runtime_version="validator.v1")

    assert first == second
    assert first.calibration_status == CALIBRATION_REVIEW_STATUS
    assert first.selected_candidate_id is None
    assert first.summaries == (
        CandidateValidationSummary(
            "candidate-a", "v1", 3, 2, 2, 1, 2, 2, 66.66666666666666, 100.0, 1.5, 15.0, 1.0
        ),
        CandidateValidationSummary(
            "candidate-b", "v1", 3, 2, 2, 1, 2, 2, 66.66666666666666, 100.0, 2.5, 15.0, -1.0
        ),
    )
    report = export_historical_validation_report(first)
    assert '"selectedCandidateId":null' in report
    assert "PM_REVIEW_REQUIRED" in report
    assert "winner" not in report.lower()


def test_observed_outcome_requires_future_date_and_value():
    dataset = _dataset()
    invalid = HistoricalTopicOutcome(
        "t1", date(2026, 8, 1), "T+5", date(2026, 8, 1), OBSERVED, 10.0, "outcome"
    )
    invalid_dataset = HistoricalValidationDataset(
        dataset.dataset_id,
        dataset.dataset_version,
        dataset.source_references,
        dataset.observations,
        (invalid, *dataset.outcomes[1:]),
    )
    with pytest.raises(FormulaResearchValidationError, match="after"):
        run_historical_validation(invalid_dataset, validation_runtime_version="validator.v1")


def test_duplicate_observation_identity_is_rejected():
    dataset = _dataset()
    duplicate = HistoricalValidationDataset(
        dataset.dataset_id,
        dataset.dataset_version,
        dataset.source_references,
        (dataset.observations[0], *dataset.observations),
        dataset.outcomes,
    )
    with pytest.raises(FormulaResearchValidationError, match="observation identities"):
        run_historical_validation(duplicate, validation_runtime_version="validator.v1")


def test_result_digest_tampering_is_rejected():
    result = run_historical_validation(_dataset(), validation_runtime_version="validator.v1")
    tampered = result.__class__(
        result.dataset_id,
        result.dataset_version,
        result.validation_runtime_version,
        result.summaries,
        result.calibration_status,
        None,
        "0" * 64,
    )
    with pytest.raises(FormulaResearchValidationError, match="digest"):
        export_historical_validation_report(tampered)
