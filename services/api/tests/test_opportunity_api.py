from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from topicpilot_api.main import create_app
from topicpilot_api.opportunity_api import (
    CanonicalOpportunityProvider,
    FormalOpportunityReadService,
    get_formal_opportunity_read_service,
    validate_formal_opportunity_detail,
    validate_formal_opportunity_page,
)

AS_OF = date(2026, 8, 28)
UPDATED_AT = datetime(2026, 8, 28, 8, 0, tzinfo=UTC)


def _lineage() -> dict[str, Any]:
    return {
        "provider": "canonical-opportunity-provider",
        "authority": "FORMAL_OPPORTUNITY_PUBLICATION",
        "contractVersion": "opportunity-page-read.v1",
        "sourceArtifactId": "opportunity-formal-test-artifact",
        "sourceArtifactHash": "sha256:test",
        "policyVersion": "opportunity-formal-policy.v1",
    }


def _lifecycle(topic_type: str = "LEAF") -> dict[str, Any]:
    if topic_type == "PARENT":
        return {
            "status": "UNAVAILABLE",
            "dataStatus": "NOT_PUBLISHED",
            "publicationStatus": "UNAVAILABLE",
        }
    return {
        "status": "AVAILABLE",
        "currentStage": "FERMENTING",
        "stageEnteredAt": AS_OF,
        "stageTradingDays": 3,
        "previousStage": "SPROUTING",
        "transitionReason": "FORMAL_PROVIDER_REASON",
        "policyVersion": "lifecycle-v1.3",
        "asOf": AS_OF,
        "dataStatus": "FORMAL_PUBLISHED",
        "publicationStatus": "FORMAL",
    }


def _selector(status: str = "AVAILABLE", *, topic_type: str = "LEAF") -> dict[str, Any]:
    if status == "AVAILABLE":
        return {
            "contractVersion": "selector-v1",
            "status": "AVAILABLE",
            "candidateStatus": "PUBLISHED",
            "asOf": AS_OF,
            "dataStatus": "FORMAL_PUBLISHED",
            "publicationStatus": "FORMAL",
            "candidates": [
                {
                    "rank": 1,
                    "instrument": {"id": "instrument-1", "symbol": "1101", "name": "Test One"},
                    "topicRole": "CORE",
                    "screenStatus": "PASSED",
                    "evidenceStatus": "AVAILABLE",
                    "asOf": AS_OF,
                    "dataStatus": "FORMAL_PUBLISHED",
                    "publicationStatus": "FORMAL",
                },
                {
                    "rank": 2,
                    "instrument": {"id": "instrument-2", "symbol": "1102", "name": "Test Two"},
                    "topicRole": "RELATED",
                    "screenStatus": "PASSED",
                    "evidenceStatus": "AVAILABLE",
                    "asOf": AS_OF,
                    "dataStatus": "FORMAL_PUBLISHED",
                    "publicationStatus": "FORMAL",
                },
            ],
        }
    return {
        "contractVersion": "selector-v1",
        "status": status,
        "candidateStatus": (
            "NO_CANDIDATE_AFTER_SCREEN" if status == "EMPTY" else "REQUIRED_EVIDENCE_MISSING"
        ),
        "asOf": None,
        "dataStatus": "NOT_PUBLISHED",
        "publicationStatus": "UNAVAILABLE",
        "missingEvidence": ["PRICE", "MA60"] if status == "FAIL_CLOSED" else [],
        "candidates": [],
    }


def _summary(*, topic_type: str = "LEAF", selector_status: str = "AVAILABLE") -> dict[str, Any]:
    return {
        "opportunityId": "opportunity-1",
        "opportunityKey": "topic-1:opportunity-1",
        "displayOrder": 1,
        "topic": {
            "id": "topic-1",
            "name": "Test Topic",
            "slug": "test-topic",
            "topicType": topic_type,
        },
        "opportunityState": "SELECTED",
        "displayKey": "OPPORTUNITY_STATE_SELECTED",
        "sectionKey": "new-opportunities",
        "topicGrade": None,
        "topicStrength": None,
        "summary": "Provider-owned qualification evidence.",
        "evidence": [
            {
                "code": "FORMAL_REASON",
                "kind": "OBSERVED",
                "detail": "Provider-owned evidence",
                "source": "canonical",
                "status": "AVAILABLE",
            }
        ],
        "lifecycle": _lifecycle(topic_type),
        "technicalValidation": {
            "status": "AVAILABLE",
            "memberCount": 2,
            "evaluatedCount": 2,
            "validatedCount": 2,
            "dataStatus": "FORMAL_PUBLISHED",
            "asOf": AS_OF,
            "publicationStatus": "FORMAL",
        },
        "selectorV1": _selector(selector_status, topic_type=topic_type),
        "primaryRisk": None,
        "asOf": AS_OF,
        "updatedAt": UPDATED_AT,
        "publicationStatus": "FORMAL",
        "dataStatus": "FORMAL_PUBLISHED",
        "sourceStatus": "FORMAL_CANONICAL",
        "providerLineage": _lineage(),
    }


def _page(*, state: str = "READY", summary: dict[str, Any] | None = None) -> dict[str, Any]:
    opportunities = [] if summary is None else [summary]
    return {
        "contractVersion": "opportunity-page-read.v1",
        "state": state,
        "publicationStatus": "FORMAL",
        "dataStatus": "FORMAL_PUBLISHED" if state == "READY" else "FORMAL_EMPTY",
        "sourceStatus": "FORMAL_CANONICAL",
        "asOf": AS_OF,
        "updatedAt": UPDATED_AT,
        "sectionMappingStatus": "AVAILABLE",
        "providerLineage": _lineage(),
        "sections": (
            [
                {
                    "sectionKey": "new-opportunities",
                    "displayKey": "opportunity.section.new",
                    "displayOrder": 1,
                    "opportunityCount": len(opportunities),
                    "opportunities": opportunities,
                }
            ]
            if opportunities
            else []
        ),
    }


class StaticFormalProvider:
    publication_status = "FORMAL"
    source_status = "FORMAL_CANONICAL"

    def __init__(self, page: dict[str, Any] | None = None) -> None:
        self.page = page or _page(summary=_summary())

    def read_page(self, **_: Any) -> dict[str, Any]:
        return self.page

    def read_detail(self, opportunity_id: str) -> dict[str, Any]:
        assert opportunity_id == "opportunity-1"
        item = _summary()
        item.update(
            {
                "lifecycleEvidence": [],
                "selectorEvidence": [],
                "members": {
                    "status": "UNAVAILABLE",
                    "reason": "COMPLETE_MEMBER_READ_MODEL_NOT_PUBLISHED",
                    "items": [],
                },
            }
        )
        return {
            "contractVersion": "opportunity-page-read.v1",
            "state": "READY",
            "publicationStatus": "FORMAL",
            "dataStatus": "FORMAL_PUBLISHED",
            "sourceStatus": "FORMAL_CANONICAL",
            "asOf": AS_OF,
            "updatedAt": UPDATED_AT,
            "query": {"opportunityId": opportunity_id},
            "providerLineage": _lineage(),
            "opportunity": item,
        }


class ShadowProvider:
    publication_status = "SHADOW"
    source_status = "SHADOW"


def _client(provider: object | None = None) -> TestClient:
    app = create_app()
    if provider is not None:
        app.dependency_overrides[get_formal_opportunity_read_service] = (
            lambda: FormalOpportunityReadService(provider)  # type: ignore[arg-type]
        )
    return TestClient(app)


def test_formal_opportunity_endpoints_fail_closed_without_canonical_provider() -> None:
    with _client() as client:
        list_response = client.get("/api/v2/opportunities")
        detail_response = client.get("/api/v2/opportunities/opportunity-1")

    assert list_response.status_code == 503
    assert detail_response.status_code == 503
    assert list_response.json()["type"].endswith("/opportunity-unavailable")
    assert "SHADOW" not in list_response.text.upper()


def test_formal_page_preserves_backend_order_and_pit_context() -> None:
    with _client(StaticFormalProvider()) as client:
        response = client.get("/api/v2/opportunities?asOf=2026-08-28")

    assert response.status_code == 200
    body = response.json()
    assert body["publicationStatus"] == "FORMAL"
    assert body["sourceStatus"] == "FORMAL_CANONICAL"
    assert body["asOf"] == "2026-08-28"
    assert body["sections"][0]["displayKey"] == "opportunity.section.new"
    assert len(body["sections"][0]["opportunities"][0]["selectorV1"]["candidates"]) == 2


def test_formal_detail_keeps_full_members_unavailable_instead_of_partial_fallback() -> None:
    with _client(StaticFormalProvider()) as client:
        response = client.get("/api/v2/opportunities/opportunity-1")

    assert response.status_code == 200
    body = response.json()
    assert body["opportunity"]["members"]["status"] == "UNAVAILABLE"
    assert body["opportunity"]["members"]["items"] == []
    assert body["opportunity"]["selectorV1"]["candidateStatus"] == "PUBLISHED"


def test_parent_topic_cannot_publish_lifecycle_or_selector_analysis() -> None:
    payload = _page(summary=_summary(topic_type="PARENT"))
    with pytest.raises(ValueError, match="Parent topics"):
        validate_formal_opportunity_page(payload)


def test_selector_empty_and_single_candidate_semantics_are_not_filled() -> None:
    payload = _page(summary=_summary(selector_status="EMPTY"))
    page = validate_formal_opportunity_page(payload)
    selector = page.sections[0].opportunities[0].selector_v1
    assert selector.candidate_status == "NO_CANDIDATE_AFTER_SCREEN"
    assert selector.candidates == []

    single_payload = _page(summary=_summary())
    single_payload["sections"][0]["opportunities"][0]["selectorV1"]["candidates"] = single_payload[
        "sections"
    ][0]["opportunities"][0]["selectorV1"]["candidates"][:1]
    single_page = validate_formal_opportunity_page(single_payload)
    assert len(single_page.sections[0].opportunities[0].selector_v1.candidates) == 1


def test_selector_missing_required_evidence_is_explicitly_fail_closed() -> None:
    payload = _page(summary=_summary(selector_status="FAIL_CLOSED"))
    page = validate_formal_opportunity_page(payload)
    selector = page.sections[0].opportunities[0].selector_v1
    assert selector.status == "FAIL_CLOSED"
    assert selector.candidates == []
    assert selector.missing_evidence == ["PRICE", "MA60"]


def test_shadow_payload_is_rejected_by_formal_boundary() -> None:
    payload = _page(summary=_summary())
    payload["publicationStatus"] = "SHADOW"
    with pytest.raises(ValueError, match="formal"):
        validate_formal_opportunity_page(payload)


def test_default_provider_is_an_explicit_unavailable_placeholder() -> None:
    provider = CanonicalOpportunityProvider()
    assert provider.publication_status == "UNAVAILABLE"
    assert provider.source_status == "UNAVAILABLE"
    assert FormalOpportunityReadService(provider).provider is provider


def test_formal_service_rejects_shadow_provider_at_construction() -> None:
    with pytest.raises(ValueError, match="shadow/research"):
        FormalOpportunityReadService(ShadowProvider())


def test_openapi_exposes_separate_formal_and_shadow_routes() -> None:
    openapi = create_app().openapi()
    assert "/api/v2/opportunities" in openapi["paths"]
    assert "/api/v2/opportunities/{opportunity_id}" in openapi["paths"]
    assert "/api/v1/opportunities/shadow" in openapi["paths"]
    operation = openapi["paths"]["/api/v2/opportunities"]["get"]
    assert {"asOf", "sectionKey", "limit", "offset"} == {
        parameter["name"] for parameter in operation["parameters"]
    }
    assert operation["responses"]["503"]["description"].startswith("No canonical")


def test_detail_validator_accepts_formal_detail_with_member_gap() -> None:
    payload = StaticFormalProvider().read_detail("opportunity-1")
    detail = validate_formal_opportunity_detail(payload)
    assert detail.opportunity is not None
    assert detail.opportunity.members.status == "UNAVAILABLE"
