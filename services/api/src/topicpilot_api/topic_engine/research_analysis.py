"""Descriptive analysis and export for research-only Topic Formula results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import combinations
from statistics import fmean, median

from .research import (
    RESEARCH_ONLY,
    CandidateResearchResult,
    CandidateTopicOutput,
    FormulaResearchResult,
    FormulaResearchValidationError,
    ResearchBounds,
)

ANALYSIS_SCHEMA_VERSION = "topic-formula-research-analysis.v1"


@dataclass(frozen=True)
class CandidateScoreDistribution:
    candidate_id: str
    candidate_version: str
    scorer_runtime_version: str
    policy_configuration: tuple[tuple[str, str], ...]
    score_bounds: ResearchBounds
    component_bounds: ResearchBounds | None
    topic_count: int
    scored_count: int
    null_count: int
    zero_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None

    @property
    def identity(self) -> tuple[str, str]:
        return self.candidate_id, self.candidate_version


@dataclass(frozen=True)
class TopicAbsoluteDifference:
    topic_id: str
    absolute_difference: float


@dataclass(frozen=True)
class PairwiseScoreComparison:
    left_candidate_id: str
    left_candidate_version: str
    right_candidate_id: str
    right_candidate_version: str
    topic_count: int
    both_scored_count: int
    left_only_count: int
    right_only_count: int
    both_null_count: int
    mean_absolute_difference: float | None
    maximum_absolute_difference: float | None
    topic_differences: tuple[TopicAbsoluteDifference, ...]


@dataclass(frozen=True)
class FormulaResearchAnalysis:
    analysis_runtime_version: str
    source_replay_digest: str
    source_research_runtime_version: str
    as_of: str
    feature_set_version: str
    feature_runtime_version: str
    aggregation_version: str
    candidate_distributions: tuple[CandidateScoreDistribution, ...]
    pairwise_comparisons: tuple[PairwiseScoreComparison, ...]
    analysis_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = ANALYSIS_SCHEMA_VERSION


def analyze_formula_research(
    result: FormulaResearchResult, *, analysis_runtime_version: str
) -> FormulaResearchAnalysis:
    """Create descriptive evidence without ranking candidates or selecting a winner."""

    _validate_source_result(result)
    if not analysis_runtime_version.strip():
        raise FormulaResearchValidationError("analysis_runtime_version must be non-empty")
    if analysis_runtime_version != analysis_runtime_version.strip():
        raise FormulaResearchValidationError(
            "analysis_runtime_version must not contain outer whitespace"
        )

    distributions = tuple(_distribution(item) for item in result.candidate_results)
    comparisons = tuple(
        _pairwise(result, left, right) for left, right in combinations(result.candidate_results, 2)
    )
    draft = FormulaResearchAnalysis(
        analysis_runtime_version,
        result.replay_digest,
        result.research_runtime_version,
        result.as_of.isoformat(),
        result.feature_set_version,
        result.feature_runtime_version,
        result.aggregation_version,
        distributions,
        comparisons,
        analysis_digest="",
    )
    digest = hashlib.sha256(
        json.dumps(
            _analysis_document(draft, include_digest=False),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    return FormulaResearchAnalysis(
        draft.analysis_runtime_version,
        draft.source_replay_digest,
        draft.source_research_runtime_version,
        draft.as_of,
        draft.feature_set_version,
        draft.feature_runtime_version,
        draft.aggregation_version,
        draft.candidate_distributions,
        draft.pairwise_comparisons,
        digest,
    )


def export_formula_research_analysis(analysis: FormulaResearchAnalysis) -> str:
    """Export a deterministic, JSON-safe research document."""

    if analysis.mode != RESEARCH_ONLY:
        raise FormulaResearchValidationError("analysis must remain RESEARCH_ONLY")
    expected = hashlib.sha256(
        json.dumps(
            _analysis_document(analysis, include_digest=False),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    if analysis.analysis_digest != expected:
        raise FormulaResearchValidationError("analysis digest does not match content")
    return json.dumps(
        _analysis_document(analysis, include_digest=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _validate_source_result(result: FormulaResearchResult) -> None:
    if result.mode != RESEARCH_ONLY:
        raise FormulaResearchValidationError("source result must be RESEARCH_ONLY")
    if len(result.replay_digest) != 64:
        raise FormulaResearchValidationError("source replay digest must be SHA-256")
    try:
        int(result.replay_digest, 16)
    except ValueError as exc:
        raise FormulaResearchValidationError("source replay digest must be hexadecimal") from exc

    candidate_identities = tuple(
        (item.candidate_id, item.candidate_version) for item in result.candidate_results
    )
    if not candidate_identities or candidate_identities != tuple(sorted(candidate_identities)):
        raise FormulaResearchValidationError(
            "source candidate results must be non-empty and canonically ordered"
        )
    if len(candidate_identities) != len(set(candidate_identities)):
        raise FormulaResearchValidationError("source candidate identities must be unique")

    topic_ids = tuple(item.topic_id for item in result.topic_comparisons)
    if topic_ids != tuple(sorted(topic_ids)) or len(topic_ids) != len(set(topic_ids)):
        raise FormulaResearchValidationError(
            "source topic comparisons must be unique and canonically ordered"
        )

    runtime_by_candidate = {
        (item.candidate_id, item.candidate_version): {
            score.topic_id: score for score in item.runtime_result.scores
        }
        for item in result.candidate_results
    }
    for item in result.candidate_results:
        if item.summary.topic_count != len(topic_ids):
            raise FormulaResearchValidationError(
                "candidate summary topic count does not match comparisons"
            )
    for topic in result.topic_comparisons:
        identities = tuple((item.candidate_id, item.candidate_version) for item in topic.candidates)
        if identities != candidate_identities:
            raise FormulaResearchValidationError(
                "topic comparison candidate order does not match source candidates"
            )
        for output in topic.candidates:
            identity = output.candidate_id, output.candidate_version
            runtime_score = runtime_by_candidate[identity].get(topic.topic_id)
            if runtime_score is None or not _matches_runtime(output, runtime_score):
                raise FormulaResearchValidationError(
                    "topic comparison does not match candidate runtime output"
                )


def _matches_runtime(output: CandidateTopicOutput, runtime_score) -> bool:
    return (
        output.status == runtime_score.status
        and output.eligibility == runtime_score.eligibility
        and output.score == runtime_score.score
        and output.grade == runtime_score.grade
        and output.confidence == runtime_score.confidence
        and output.components == runtime_score.components
    )


def _distribution(result: CandidateResearchResult) -> CandidateScoreDistribution:
    scores = tuple(score.score for score in result.runtime_result.scores if score.score is not None)
    return CandidateScoreDistribution(
        result.candidate_id,
        result.candidate_version,
        result.summary.scorer_runtime_version,
        result.policy_configuration,
        result.score_bounds,
        result.component_bounds,
        result.summary.topic_count,
        len(scores),
        result.summary.topic_count - len(scores),
        sum(score == 0 for score in scores),
        min(scores) if scores else None,
        max(scores) if scores else None,
        fmean(scores) if scores else None,
        median(scores) if scores else None,
    )


def _pairwise(
    source: FormulaResearchResult,
    left: CandidateResearchResult,
    right: CandidateResearchResult,
) -> PairwiseScoreComparison:
    left_scores = {score.topic_id: score.score for score in left.runtime_result.scores}
    right_scores = {score.topic_id: score.score for score in right.runtime_result.scores}
    differences: list[TopicAbsoluteDifference] = []
    left_only = 0
    right_only = 0
    both_null = 0
    for topic in source.topic_comparisons:
        left_score = left_scores[topic.topic_id]
        right_score = right_scores[topic.topic_id]
        if left_score is not None and right_score is not None:
            differences.append(
                TopicAbsoluteDifference(topic.topic_id, abs(left_score - right_score))
            )
        elif left_score is not None:
            left_only += 1
        elif right_score is not None:
            right_only += 1
        else:
            both_null += 1
    difference_values = tuple(item.absolute_difference for item in differences)
    return PairwiseScoreComparison(
        left.candidate_id,
        left.candidate_version,
        right.candidate_id,
        right.candidate_version,
        len(source.topic_comparisons),
        len(differences),
        left_only,
        right_only,
        both_null,
        fmean(difference_values) if difference_values else None,
        max(difference_values) if difference_values else None,
        tuple(differences),
    )


def _analysis_document(
    analysis: FormulaResearchAnalysis, *, include_digest: bool
) -> dict[str, object]:
    document: dict[str, object] = {
        "schemaVersion": analysis.schema_version,
        "mode": analysis.mode,
        "analysisRuntimeVersion": analysis.analysis_runtime_version,
        "source": {
            "replayDigest": analysis.source_replay_digest,
            "researchRuntimeVersion": analysis.source_research_runtime_version,
            "asOf": analysis.as_of,
            "featureSetVersion": analysis.feature_set_version,
            "featureRuntimeVersion": analysis.feature_runtime_version,
            "aggregationVersion": analysis.aggregation_version,
        },
        "candidateDistributions": [
            {
                "candidateId": item.candidate_id,
                "candidateVersion": item.candidate_version,
                "scorerRuntimeVersion": item.scorer_runtime_version,
                "policyConfiguration": [list(pair) for pair in item.policy_configuration],
                "scoreBounds": _bounds_document(item.score_bounds),
                "componentBounds": _bounds_document(item.component_bounds),
                "topicCount": item.topic_count,
                "scoredCount": item.scored_count,
                "nullCount": item.null_count,
                "zeroCount": item.zero_count,
                "minimum": item.minimum,
                "maximum": item.maximum,
                "mean": item.mean,
                "median": item.median,
            }
            for item in analysis.candidate_distributions
        ],
        "pairwiseComparisons": [
            {
                "leftCandidateId": item.left_candidate_id,
                "leftCandidateVersion": item.left_candidate_version,
                "rightCandidateId": item.right_candidate_id,
                "rightCandidateVersion": item.right_candidate_version,
                "topicCount": item.topic_count,
                "bothScoredCount": item.both_scored_count,
                "leftOnlyCount": item.left_only_count,
                "rightOnlyCount": item.right_only_count,
                "bothNullCount": item.both_null_count,
                "meanAbsoluteDifference": item.mean_absolute_difference,
                "maximumAbsoluteDifference": item.maximum_absolute_difference,
                "topicDifferences": [
                    {
                        "topicId": difference.topic_id,
                        "absoluteDifference": difference.absolute_difference,
                    }
                    for difference in item.topic_differences
                ],
            }
            for item in analysis.pairwise_comparisons
        ],
    }
    if include_digest:
        document["analysisDigest"] = analysis.analysis_digest
    return document


def _bounds_document(bounds: ResearchBounds | None) -> dict[str, float] | None:
    if bounds is None:
        return None
    return {"minimum": bounds.minimum, "maximum": bounds.maximum}


__all__ = [
    "ANALYSIS_SCHEMA_VERSION",
    "CandidateScoreDistribution",
    "FormulaResearchAnalysis",
    "PairwiseScoreComparison",
    "TopicAbsoluteDifference",
    "analyze_formula_research",
    "export_formula_research_analysis",
]
