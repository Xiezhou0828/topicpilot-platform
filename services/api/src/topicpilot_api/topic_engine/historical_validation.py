"""Research-only historical validation and calibration review.

This module evaluates explicit Topic Score observations against explicit
subsequent topic outcomes.  It deliberately reports descriptive evidence only:
it does not normalize values, invent thresholds, choose a winner, or promote a
formula to production.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from statistics import fmean

from .research import RESEARCH_ONLY, FormulaResearchResult, FormulaResearchValidationError

HISTORICAL_VALIDATION_SCHEMA_VERSION = "topic-score-historical-validation.v1"
CALIBRATION_REVIEW_STATUS = "PM_REVIEW_REQUIRED"
OBSERVED = "OBSERVED"
MISSING = "MISSING"
_OUTCOME_STATUSES = frozenset({OBSERVED, MISSING})


@dataclass(frozen=True)
class ScoreObservation:
    """One candidate output at one point in time, copied without recalculation."""

    candidate_id: str
    candidate_version: str
    topic_id: str
    as_of: date
    status: str
    eligibility: str
    score: float | None
    grade: str | None


@dataclass(frozen=True)
class HistoricalTopicOutcome:
    """Explicit subsequent topic behavior used as a validation outcome."""

    topic_id: str
    as_of: date
    horizon: str
    observed_until: date | None
    status: str
    value: float | None
    source_reference: str


@dataclass(frozen=True)
class HistoricalValidationDataset:
    dataset_id: str
    dataset_version: str
    source_references: tuple[str, ...]
    observations: tuple[ScoreObservation, ...]
    outcomes: tuple[HistoricalTopicOutcome, ...]
    mode: str = RESEARCH_ONLY
    schema_version: str = HISTORICAL_VALIDATION_SCHEMA_VERSION


@dataclass(frozen=True)
class CandidateValidationSummary:
    candidate_id: str
    candidate_version: str
    observation_count: int
    eligible_count: int
    scored_count: int
    missing_score_count: int
    outcome_count: int
    paired_count: int
    score_coverage_pct: float | None
    outcome_coverage_pct: float | None
    mean_score: float | None
    mean_outcome: float | None
    score_outcome_correlation: float | None


@dataclass(frozen=True)
class HistoricalValidationResult:
    dataset_id: str
    dataset_version: str
    validation_runtime_version: str
    summaries: tuple[CandidateValidationSummary, ...]
    calibration_status: str
    selected_candidate_id: str | None = None
    report_digest: str = ""
    mode: str = RESEARCH_ONLY
    schema_version: str = HISTORICAL_VALIDATION_SCHEMA_VERSION


def observations_from_research_results(
    results: Sequence[FormulaResearchResult],
) -> tuple[ScoreObservation, ...]:
    """Extract candidate outputs from replay results without changing them."""

    observations: list[ScoreObservation] = []
    for result in results:
        for comparison in result.topic_comparisons:
            for output in comparison.candidates:
                observations.append(
                    ScoreObservation(
                        output.candidate_id,
                        output.candidate_version,
                        comparison.topic_id,
                        comparison.as_of,
                        output.status,
                        output.eligibility,
                        output.score,
                        output.grade,
                    )
                )
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.candidate_id,
                item.candidate_version,
                item.as_of,
                item.topic_id,
            ),
        )
    )


def build_historical_validation_dataset(
    dataset_id: str,
    dataset_version: str,
    results: Sequence[FormulaResearchResult],
    outcomes: Sequence[HistoricalTopicOutcome],
    source_references: Sequence[str],
) -> HistoricalValidationDataset:
    """Build a replayable research dataset from explicit replay and outcome data."""

    return HistoricalValidationDataset(
        dataset_id,
        dataset_version,
        tuple(sorted(_identity(value, "source reference") for value in source_references)),
        observations_from_research_results(results),
        tuple(
            sorted(
                outcomes,
                key=lambda item: (item.topic_id, item.as_of, item.horizon),
            )
        ),
    )


def run_historical_validation(
    dataset: HistoricalValidationDataset,
    *,
    validation_runtime_version: str,
) -> HistoricalValidationResult:
    """Measure candidate/outcome relationships without making a calibration choice."""

    _validate_dataset(dataset)
    runtime_version = _identity(validation_runtime_version, "validation runtime version")
    identities = sorted(
        {(item.candidate_id, item.candidate_version) for item in dataset.observations}
    )
    summaries = tuple(
        _summarize_candidate(
            candidate_id,
            candidate_version,
            dataset.observations,
            dataset.outcomes,
        )
        for candidate_id, candidate_version in identities
    )
    draft = HistoricalValidationResult(
        dataset.dataset_id,
        dataset.dataset_version,
        runtime_version,
        summaries,
        CALIBRATION_REVIEW_STATUS,
    )
    return HistoricalValidationResult(
        draft.dataset_id,
        draft.dataset_version,
        draft.validation_runtime_version,
        draft.summaries,
        draft.calibration_status,
        None,
        _report_digest(draft),
    )


def export_historical_validation_report(result: HistoricalValidationResult) -> str:
    """Export a deterministic, non-promoting validation/calibration report."""

    _validate_result(result)
    return json.dumps(
        _report_document(result, include_digest=True), sort_keys=True, separators=(",", ":")
    )


def _summarize_candidate(
    candidate_id: str,
    candidate_version: str,
    observations: tuple[ScoreObservation, ...],
    outcomes: tuple[HistoricalTopicOutcome, ...],
) -> CandidateValidationSummary:
    candidate_observations = tuple(
        item
        for item in observations
        if (item.candidate_id, item.candidate_version) == (candidate_id, candidate_version)
    )
    scored = tuple(
        item
        for item in candidate_observations
        if item.score is not None and item.status == "SCORED" and item.eligibility == "ELIGIBLE"
    )
    paired: list[tuple[float, float]] = []
    outcome_count = 0
    for item in scored:
        matching = tuple(
            outcome
            for outcome in outcomes
            if (outcome.topic_id, outcome.as_of) == (item.topic_id, item.as_of)
        )
        outcome_count += len(matching)
        for outcome in matching:
            if outcome.status == OBSERVED and outcome.value is not None:
                paired.append((item.score, outcome.value))
    score_values = tuple(item.score for item in scored if item.score is not None)
    outcome_values = tuple(value for _, value in paired)
    return CandidateValidationSummary(
        candidate_id,
        candidate_version,
        len(candidate_observations),
        sum(item.eligibility == "ELIGIBLE" for item in candidate_observations),
        len(scored),
        len(candidate_observations) - len(scored),
        outcome_count,
        len(paired),
        _percentage(len(scored), len(candidate_observations)),
        _percentage(len(paired), outcome_count),
        fmean(score_values) if score_values else None,
        fmean(outcome_values) if outcome_values else None,
        _pearson(paired),
    )


def _validate_dataset(dataset: HistoricalValidationDataset) -> None:
    if (
        dataset.mode != RESEARCH_ONLY
        or dataset.schema_version != HISTORICAL_VALIDATION_SCHEMA_VERSION
    ):
        raise FormulaResearchValidationError("historical validation must remain RESEARCH_ONLY v1")
    _identity(dataset.dataset_id, "dataset id")
    _identity(dataset.dataset_version, "dataset version")
    if not dataset.source_references:
        raise FormulaResearchValidationError("historical validation source references are required")
    if any(not value.strip() or value != value.strip() for value in dataset.source_references):
        raise FormulaResearchValidationError("source references must be trimmed")
    observation_keys = tuple(
        (item.candidate_id, item.candidate_version, item.topic_id, item.as_of)
        for item in dataset.observations
    )
    if len(observation_keys) != len(set(observation_keys)):
        raise FormulaResearchValidationError("score observation identities must be unique")
    outcome_keys = tuple((item.topic_id, item.as_of, item.horizon) for item in dataset.outcomes)
    if len(outcome_keys) != len(set(outcome_keys)):
        raise FormulaResearchValidationError("historical outcome identities must be unique")
    for observation in dataset.observations:
        _identity(observation.candidate_id, "candidate id")
        _identity(observation.candidate_version, "candidate version")
        _identity(observation.topic_id, "topic id")
        _identity(observation.status, "score status")
        _identity(observation.eligibility, "eligibility")
        if observation.score is not None and not _finite(observation.score):
            raise FormulaResearchValidationError("score observations must be finite")
        if observation.grade is not None:
            _identity(observation.grade, "grade")
    for outcome in dataset.outcomes:
        _identity(outcome.topic_id, "outcome topic id")
        _identity(outcome.horizon, "outcome horizon")
        _identity(outcome.status, "outcome status")
        if outcome.status not in _OUTCOME_STATUSES:
            raise FormulaResearchValidationError("unsupported historical outcome status")
        _identity(outcome.source_reference, "outcome source reference")
        if outcome.status == OBSERVED:
            if (
                outcome.observed_until is None
                or outcome.value is None
                or not _finite(outcome.value)
            ):
                raise FormulaResearchValidationError(
                    "observed outcomes require observed_until and finite value"
                )
            if outcome.observed_until <= outcome.as_of:
                raise FormulaResearchValidationError(
                    "observed_until must be after the score as_of date"
                )
        elif outcome.observed_until is not None or outcome.value is not None:
            raise FormulaResearchValidationError("missing outcomes must not contain observations")


def _validate_result(result: HistoricalValidationResult) -> None:
    if (
        result.mode != RESEARCH_ONLY
        or result.schema_version != HISTORICAL_VALIDATION_SCHEMA_VERSION
    ):
        raise FormulaResearchValidationError("validation result must remain RESEARCH_ONLY v1")
    if result.calibration_status != CALIBRATION_REVIEW_STATUS:
        raise FormulaResearchValidationError("calibration status must require PM review")
    if result.selected_candidate_id is not None:
        raise FormulaResearchValidationError("historical validation cannot select a candidate")
    if result.report_digest != _report_digest(result):
        raise FormulaResearchValidationError("historical validation report digest does not match")


def _report_digest(result: HistoricalValidationResult) -> str:
    return hashlib.sha256(
        json.dumps(
            _report_document(result, include_digest=False),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _report_document(
    result: HistoricalValidationResult, *, include_digest: bool
) -> dict[str, object]:
    document: dict[str, object] = {
        "schemaVersion": result.schema_version,
        "mode": result.mode,
        "datasetId": result.dataset_id,
        "datasetVersion": result.dataset_version,
        "validationRuntimeVersion": result.validation_runtime_version,
        "calibration": {
            "status": result.calibration_status,
            "selectedCandidateId": result.selected_candidate_id,
        },
        "candidates": [_summary_document(summary) for summary in result.summaries],
    }
    if include_digest:
        document["reportDigest"] = result.report_digest
    return document


def _summary_document(summary: CandidateValidationSummary) -> dict[str, object]:
    return {
        "candidateId": summary.candidate_id,
        "candidateVersion": summary.candidate_version,
        "observationCount": summary.observation_count,
        "eligibleCount": summary.eligible_count,
        "scoredCount": summary.scored_count,
        "missingScoreCount": summary.missing_score_count,
        "outcomeCount": summary.outcome_count,
        "pairedCount": summary.paired_count,
        "scoreCoveragePct": summary.score_coverage_pct,
        "outcomeCoveragePct": summary.outcome_coverage_pct,
        "meanScore": summary.mean_score,
        "meanOutcome": summary.mean_outcome,
        "scoreOutcomeCorrelation": summary.score_outcome_correlation,
    }


def _percentage(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator * 100


def _pearson(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    xs = tuple(pair[0] for pair in pairs)
    ys = tuple(pair[1] for pair in pairs)
    mean_x = fmean(xs)
    mean_y = fmean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denominator_x == 0 or denominator_y == 0:
        return None
    return round(numerator / (denominator_x * denominator_y), 12)


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FormulaResearchValidationError(f"{label} must be a trimmed non-empty string")
    return value


__all__ = [
    "CALIBRATION_REVIEW_STATUS",
    "HISTORICAL_VALIDATION_SCHEMA_VERSION",
    "MISSING",
    "OBSERVED",
    "CandidateValidationSummary",
    "HistoricalTopicOutcome",
    "HistoricalValidationDataset",
    "HistoricalValidationResult",
    "ScoreObservation",
    "build_historical_validation_dataset",
    "export_historical_validation_report",
    "observations_from_research_results",
    "run_historical_validation",
]
