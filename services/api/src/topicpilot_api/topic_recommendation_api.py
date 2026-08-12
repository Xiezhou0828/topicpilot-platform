"""Read-only API boundary for the downstream Recommendation MVP.

Recommendation is intentionally downstream of Topic Intelligence.  This module
serializes an already-built RecommendationResult; it does not discover
candidates, calculate Topic Score, rank securities, or create trading advice.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from topicpilot_api.problems import ApiProblem
from topicpilot_api.schemas import RecommendationResponse
from topicpilot_api.topic_engine import RecommendationResult

RECOMMENDATION_API_VERSION = "recommendation-api.v1"
router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


def get_recommendation_result() -> RecommendationResult:
    """Fail closed until an approved candidate source and runtime are configured."""

    raise ApiProblem(
        503,
        "Recommendation unavailable",
        "No approved Recommendation runtime provider is configured.",
        "https://topicpilot.example/problems/recommendation-unavailable",
    )


RecommendationRuntimeResult = Annotated[
    RecommendationResult,
    Depends(get_recommendation_result),
]


@router.get(
    "/latest",
    response_model=RecommendationResponse,
    responses={503: {"description": "No approved Recommendation provider is configured"}},
)
def latest_recommendations(result: RecommendationRuntimeResult) -> dict[str, Any]:
    return serialize_recommendations(result)


def serialize_recommendations(result: RecommendationResult) -> dict[str, Any]:
    """Serialize the downstream result without deriving new business output."""

    items = []
    for item in result.items:
        context = item.topic_context
        items.append(
            {
                "candidateId": item.candidate_id,
                "topicId": item.topic_id,
                "label": item.label,
                "status": item.status,
                "reason": item.reason,
                "topicContext": None
                if context is None
                else {
                    "asOf": context.as_of,
                    "scorerRuntimeVersion": context.scorer_runtime_version,
                    "featureSetVersion": context.feature_set_version,
                    "featureRuntimeVersion": context.feature_runtime_version,
                    "aggregationVersion": context.aggregation_version,
                    "policyId": context.policy_id,
                    "policyVersion": context.policy_version,
                    "eligibility": context.eligibility,
                    "score": context.score,
                    "grade": context.grade,
                    "confidence": context.confidence,
                    "components": [
                        {"name": name, "value": value}
                        for name, value in (context.components or ())
                    ],
                    "evidenceReference": list(context.evidence_reference or ()),
                },
                "evidence": list(item.evidence),
            }
        )
    return {
        "contractVersion": RECOMMENDATION_API_VERSION,
        "asOf": result.as_of,
        "status": result.status,
        "items": items,
    }


__all__ = [
    "RECOMMENDATION_API_VERSION",
    "get_recommendation_result",
    "router",
    "serialize_recommendations",
]
