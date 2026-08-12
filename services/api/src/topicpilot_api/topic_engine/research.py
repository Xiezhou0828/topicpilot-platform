"""Deterministic, ephemeral harness for research-only Topic Score candidates."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from .aggregation import AggregationResult
from .integration import TopicIntelligenceRuntimeResult, run_topic_intelligence
from .scorer import TopicScorer
from .scoring_contracts import ScoringPolicy, TopicScore

RESEARCH_ONLY = "RESEARCH_ONLY"
FROZEN_COMPONENT_NAMES = ("breadth", "leadership")
FROZEN_GRADE_VOCABULARY = frozenset({"S", "A", "B", "D"})


class FormulaResearchValidationError(ValueError):
    """Raised when a research candidate violates the frozen policy boundary."""


@dataclass(frozen=True)
class ResearchBounds:
    """Candidate-declared bounds; these do not become global scoring policy."""

    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.minimum) or not math.isfinite(self.maximum):
            raise FormulaResearchValidationError("research bounds must be finite")
        if self.minimum > self.maximum:
            raise FormulaResearchValidationError("research bounds minimum exceeds maximum")

    def contains(self, value: float) -> bool:
        return self.minimum <= value <= self.maximum


@dataclass(frozen=True)
class ResearchCandidate:
    """An explicitly identified scorer candidate that can never be a production default."""

    candidate_id: str
    candidate_version: str
    scorer: TopicScorer
    policy: ScoringPolicy
    score_bounds: ResearchBounds
    component_bounds: ResearchBounds | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise FormulaResearchValidationError("candidate_id must be non-empty")
        if not self.candidate_version.strip():
            raise FormulaResearchValidationError("candidate_version must be non-empty")
        if self.candidate_id != self.candidate_id.strip():
            raise FormulaResearchValidationError("candidate_id must not contain outer whitespace")
        if self.candidate_version != self.candidate_version.strip():
            raise FormulaResearchValidationError(
                "candidate_version must not contain outer whitespace"
            )
        if self.policy.policy_id != self.candidate_id:
            raise FormulaResearchValidationError("candidate_id must match ScoringPolicy.policy_id")
        if self.policy.policy_version != self.candidate_version:
            raise FormulaResearchValidationError(
                "candidate_version must match ScoringPolicy.policy_version"
            )

    @property
    def identity(self) -> tuple[str, str]:
        return self.candidate_id, self.candidate_version


@dataclass(frozen=True)
class CandidateResearchSummary:
    candidate_id: str
    candidate_version: str
    scorer_runtime_version: str
    topic_count: int
    scored_count: int
    eligible_count: int
    ineligible_count: int
    status_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class CandidateResearchResult:
    candidate_id: str
    candidate_version: str
    policy_configuration: tuple[tuple[str, str], ...]
    score_bounds: ResearchBounds
    component_bounds: ResearchBounds | None
    runtime_result: TopicIntelligenceRuntimeResult
    summary: CandidateResearchSummary


@dataclass(frozen=True)
class CandidateTopicOutput:
    candidate_id: str
    candidate_version: str
    status: str
    eligibility: str
    score: float | None
    grade: str | None
    confidence: float | None
    components: tuple[tuple[str, float | None], ...]


@dataclass(frozen=True)
class TopicResearchComparison:
    topic_id: str
    as_of: date
    candidates: tuple[CandidateTopicOutput, ...]


@dataclass(frozen=True)
class FormulaResearchResult:
    research_runtime_version: str
    as_of: date
    feature_set_version: str
    feature_runtime_version: str
    aggregation_version: str
    candidate_results: tuple[CandidateResearchResult, ...]
    topic_comparisons: tuple[TopicResearchComparison, ...]
    replay_digest: str
    mode: str = RESEARCH_ONLY


def run_formula_research(
    aggregates: AggregationResult,
    candidates: Sequence[ResearchCandidate],
    *,
    research_runtime_version: str,
) -> FormulaResearchResult:
    """Execute candidate plug-ins without choosing or persisting a production formula."""

    if not research_runtime_version.strip():
        raise FormulaResearchValidationError("research_runtime_version must be non-empty")
    if research_runtime_version != research_runtime_version.strip():
        raise FormulaResearchValidationError(
            "research_runtime_version must not contain outer whitespace"
        )
    if not candidates:
        raise FormulaResearchValidationError("at least one research candidate is required")

    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.identity))
    identities = tuple(candidate.identity for candidate in ordered_candidates)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("research candidate identities must be unique")

    results = tuple(_run_candidate(aggregates, candidate) for candidate in ordered_candidates)
    comparisons = _compare_topics(results, aggregates.as_of)
    digest = _replay_digest(
        aggregates,
        results,
        comparisons,
        research_runtime_version=research_runtime_version,
    )
    return FormulaResearchResult(
        research_runtime_version,
        aggregates.as_of,
        aggregates.feature_set_version,
        aggregates.runtime_version,
        aggregates.aggregation_version,
        results,
        comparisons,
        digest,
    )


def _run_candidate(
    aggregates: AggregationResult, candidate: ResearchCandidate
) -> CandidateResearchResult:
    runtime_result = run_topic_intelligence(aggregates, candidate.scorer, candidate.policy)
    for score in runtime_result.scores:
        _validate_topic_score(score, candidate)

    status_counts = Counter(score.status for score in runtime_result.scores)
    summary = CandidateResearchSummary(
        candidate.candidate_id,
        candidate.candidate_version,
        candidate.scorer.runtime_version,
        len(runtime_result.scores),
        sum(score.score is not None for score in runtime_result.scores),
        sum(score.eligibility == "ELIGIBLE" for score in runtime_result.scores),
        sum(score.eligibility == "INELIGIBLE" for score in runtime_result.scores),
        tuple(sorted(status_counts.items())),
    )
    return CandidateResearchResult(
        candidate.candidate_id,
        candidate.candidate_version,
        candidate.policy.configuration,
        candidate.score_bounds,
        candidate.component_bounds,
        runtime_result,
        summary,
    )


def _validate_topic_score(score: TopicScore, candidate: ResearchCandidate) -> None:
    if score.policy_id != candidate.candidate_id:
        raise FormulaResearchValidationError("result policy_id does not match candidate")
    if score.policy_version != candidate.candidate_version:
        raise FormulaResearchValidationError("result policy_version does not match candidate")

    if score.eligibility == "INELIGIBLE":
        if (
            any(value is not None for value in (score.score, score.grade, score.confidence))
            or score.components
        ):
            raise FormulaResearchValidationError(
                "ineligible research output must remain null and component-free"
            )
        return

    if score.eligibility != "ELIGIBLE":
        raise FormulaResearchValidationError(
            f"unexpected research eligibility: {score.eligibility}"
        )

    component_names = tuple(name for name, _ in score.components)
    if component_names != FROZEN_COMPONENT_NAMES:
        raise FormulaResearchValidationError(
            "eligible output must contain only breadth and leadership components"
        )
    for name, value in score.components:
        if value is None:
            continue
        _require_finite(value, f"component {name}")
        if candidate.component_bounds and not candidate.component_bounds.contains(value):
            raise FormulaResearchValidationError(
                f"component {name} is outside candidate-declared research bounds"
            )

    if score.score is None:
        if score.grade is not None:
            raise FormulaResearchValidationError("null score must not have a grade")
    else:
        _require_finite(score.score, "score")
        if not candidate.score_bounds.contains(score.score):
            raise FormulaResearchValidationError(
                "score is outside candidate-declared research bounds"
            )
        if score.status != "SCORED":
            raise FormulaResearchValidationError("non-null score must have SCORED status")

    if score.grade is not None and score.grade not in FROZEN_GRADE_VOCABULARY:
        raise FormulaResearchValidationError(
            f"unsupported research grade vocabulary: {score.grade}"
        )
    if score.confidence is not None:
        _require_finite(score.confidence, "confidence")


def _require_finite(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FormulaResearchValidationError(f"{label} must be numeric")
    if not math.isfinite(value):
        raise FormulaResearchValidationError(f"{label} must be finite")


def _compare_topics(
    results: tuple[CandidateResearchResult, ...], as_of: date
) -> tuple[TopicResearchComparison, ...]:
    expected_topics = tuple(score.topic_id for score in results[0].runtime_result.scores)
    comparisons: list[TopicResearchComparison] = []
    for result in results[1:]:
        topics = tuple(score.topic_id for score in result.runtime_result.scores)
        if topics != expected_topics:
            raise FormulaResearchValidationError(
                "research candidates must return the same canonical topic set"
            )
    for index, topic_id in enumerate(expected_topics):
        outputs = tuple(
            CandidateTopicOutput(
                result.candidate_id,
                result.candidate_version,
                result.runtime_result.scores[index].status,
                result.runtime_result.scores[index].eligibility,
                result.runtime_result.scores[index].score,
                result.runtime_result.scores[index].grade,
                result.runtime_result.scores[index].confidence,
                result.runtime_result.scores[index].components,
            )
            for result in results
        )
        comparisons.append(TopicResearchComparison(topic_id, as_of, outputs))
    return tuple(comparisons)


def _replay_digest(
    aggregates: AggregationResult,
    results: tuple[CandidateResearchResult, ...],
    comparisons: tuple[TopicResearchComparison, ...],
    *,
    research_runtime_version: str,
) -> str:
    payload = {
        "mode": RESEARCH_ONLY,
        "research_runtime_version": research_runtime_version,
        "aggregates": aggregates,
        "candidate_declarations": tuple(
            {
                "candidate_id": result.candidate_id,
                "candidate_version": result.candidate_version,
                "policy_configuration": result.policy_configuration,
                "score_bounds": result.score_bounds,
                "component_bounds": result.component_bounds,
                "scorer_runtime_version": result.summary.scorer_runtime_version,
            }
            for result in results
        ),
        "comparisons": comparisons,
    }
    encoded = json.dumps(
        _canonicalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        _require_finite(value, "digest value")
        return value
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _canonicalize(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    raise FormulaResearchValidationError(
        f"unsupported replay digest value type: {type(value).__name__}"
    )


__all__ = [
    "FROZEN_COMPONENT_NAMES",
    "FROZEN_GRADE_VOCABULARY",
    "RESEARCH_ONLY",
    "CandidateResearchResult",
    "CandidateResearchSummary",
    "CandidateTopicOutput",
    "FormulaResearchResult",
    "FormulaResearchValidationError",
    "ResearchBounds",
    "ResearchCandidate",
    "TopicResearchComparison",
    "run_formula_research",
]
