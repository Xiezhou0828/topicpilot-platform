"""Read-only API boundary for verified ephemeral Topic Intelligence output."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from topicpilot_api.problems import ApiProblem
from topicpilot_api.schemas import TopicIntelligenceResponse
from topicpilot_api.topic_engine import TopicIntelligenceRuntimeResult

TOPIC_INTELLIGENCE_API_VERSION = "topic-intelligence-api.v1"
router = APIRouter(prefix="/api/v1/topic-intelligence", tags=["topic-intelligence"])


def get_topic_intelligence_result() -> TopicIntelligenceRuntimeResult:
    """Fail closed until a production runtime provider is approved and configured."""

    raise ApiProblem(
        503,
        "Topic Intelligence unavailable",
        "No approved Topic Intelligence runtime provider is configured.",
        "https://topicpilot.example/problems/topic-intelligence-unavailable",
    )


RuntimeResult = Annotated[
    TopicIntelligenceRuntimeResult,
    Depends(get_topic_intelligence_result),
]


@router.get(
    "/latest",
    response_model=TopicIntelligenceResponse,
    responses={
        500: {"description": "Configured provider returned invalid evidence"},
        503: {"description": "No approved runtime provider is configured"},
    },
)
def latest_topic_intelligence(result: RuntimeResult) -> dict[str, Any]:
    try:
        return serialize_topic_intelligence(result)
    except ValueError as exc:
        raise ApiProblem(
            500,
            "Topic Intelligence output invalid",
            "The configured Topic Intelligence provider returned invalid evidence.",
            "https://topicpilot.example/problems/topic-intelligence-invalid",
        ) from exc


def serialize_topic_intelligence(
    result: TopicIntelligenceRuntimeResult,
) -> dict[str, Any]:
    """Serialize without deriving or changing any business output."""

    scores = tuple(sorted(result.scores, key=lambda score: score.topic_id))
    topic_ids = tuple(score.topic_id for score in scores)
    if len(topic_ids) != len(set(topic_ids)):
        raise ValueError("Topic Intelligence topic identities must be unique")
    topics = [_serialize_score(result, score) for score in scores]
    scored = sum(topic["status"] == "SCORED" for topic in topics)
    status = (
        "AVAILABLE" if topics and scored == len(topics) else "PARTIAL" if scored else "DEFERRED"
    )
    return {
        "contractVersion": TOPIC_INTELLIGENCE_API_VERSION,
        "mode": "EPHEMERAL",
        "status": status,
        "asOf": result.as_of,
        "versions": {
            "featureSet": _identity(result.feature_set_version, "feature-set version"),
            "featureRuntime": _identity(result.feature_runtime_version, "feature runtime version"),
            "aggregation": _identity(result.aggregation_version, "aggregation version"),
            "scorerRuntime": _identity(result.scorer_runtime_version, "scorer runtime version"),
        },
        "policy": {
            "policyId": _identity(result.policy_id, "policy id"),
            "policyVersion": _identity(result.policy_version, "policy version"),
        },
        "topics": topics,
    }


def _serialize_score(result: TopicIntelligenceRuntimeResult, score: Any) -> dict[str, Any]:
    if score.as_of != result.as_of:
        raise ValueError("Topic score as-of identity does not match runtime")
    for actual, expected, label in (
        (score.policy_id, result.policy_id, "policy id"),
        (score.policy_version, result.policy_version, "policy version"),
        (score.feature_set_version, result.feature_set_version, "feature-set version"),
        (score.runtime_version, result.scorer_runtime_version, "scorer runtime version"),
        (score.aggregation_version, result.aggregation_version, "aggregation version"),
    ):
        if actual != expected:
            raise ValueError(f"Topic score {label} does not match runtime")
    evidence = score.evidence
    if evidence is None:
        raise ValueError("Topic score evidence is required by the API contract")
    if (
        evidence.topic_id != score.topic_id
        or evidence.as_of != score.as_of
        or evidence.feature_set_version != score.feature_set_version
        or evidence.aggregation_version != score.aggregation_version
    ):
        raise ValueError("Topic score evidence identity does not match score")
    components = tuple(sorted(score.components))
    component_names = tuple(name for name, _ in components)
    if len(component_names) != len(set(component_names)):
        raise ValueError("Topic score component identities must be unique")
    features = tuple(
        sorted(
            evidence.feature_results,
            key=lambda feature: (feature.feature_name, feature.feature_version),
        )
    )
    feature_ids = tuple((feature.feature_name, feature.feature_version) for feature in features)
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError("Topic feature identities must be unique")
    return {
        "topicId": _identity(score.topic_id, "topic id"),
        "status": _identity(score.status, "score status"),
        "eligibility": _identity(score.eligibility, "eligibility"),
        "score": _optional_number(score.score, "score"),
        "grade": _optional_identity(score.grade, "grade"),
        "strength": _optional_identity(score.strength, "strength"),
        "confidence": _optional_number(score.confidence, "confidence"),
        "components": [
            {
                "name": _identity(name, "component name"),
                "value": _optional_number(value, f"component {name}"),
            }
            for name, value in components
        ],
        "evidence": {
            "aggregateStatus": _identity(evidence.status, "aggregate status"),
            "quality": {
                "readyFeatureCount": _count(
                    evidence.quality.ready_feature_count, "ready feature count"
                ),
                "insufficientFeatureCount": _count(
                    evidence.quality.insufficient_feature_count,
                    "insufficient feature count",
                ),
                "invalidFeatureCount": _count(
                    evidence.quality.invalid_feature_count, "invalid feature count"
                ),
                "coverageMin": _optional_number(evidence.quality.coverage_min, "minimum coverage"),
                "coverageMean": _optional_number(evidence.quality.coverage_mean, "mean coverage"),
            },
            "qualityFlags": sorted(
                _identity(flag, "quality flag") for flag in evidence.quality_flags
            ),
            "features": [_serialize_feature(feature) for feature in features],
        },
    }


def _serialize_feature(feature: Any) -> dict[str, Any]:
    metadata_items = tuple(sorted(feature.metadata))
    metadata_keys = tuple(key for key, _ in metadata_items)
    if len(metadata_keys) != len(set(metadata_keys)):
        raise ValueError("Topic feature metadata keys must be unique")
    return {
        "name": _identity(feature.feature_name, "feature name"),
        "version": _identity(feature.feature_version, "feature version"),
        "status": _identity(feature.status, "feature status"),
        "value": _json_safe(feature.value, "feature value"),
        "coverage": _optional_number(feature.coverage, "feature coverage"),
        "qualityFlags": sorted(
            _identity(flag, "feature quality flag") for flag in feature.quality_flags
        ),
        "metadata": {
            _identity(key, "feature metadata key"): _json_safe(value, f"feature metadata {key}")
            for key, value in metadata_items
        },
    }


def _identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a trimmed non-empty string")
    return value


def _optional_identity(value: object, label: str) -> str | None:
    return None if value is None else _identity(value, label)


def _optional_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric or null")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _count(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _json_safe(value: object, label: str) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{label} contains a non-finite number")
        return value
    if isinstance(value, (tuple, list)):
        return [_json_safe(item, label) for item in value]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError(f"{label} keys must be strings")
        return {key: _json_safe(value[key], label) for key in sorted(value)}
    raise ValueError(f"{label} must contain only JSON-safe values")


__all__ = [
    "TOPIC_INTELLIGENCE_API_VERSION",
    "get_topic_intelligence_result",
    "router",
    "serialize_topic_intelligence",
]
