"""Formal Opportunity page API boundary.

The existing ``opportunity_shadow_api`` remains a separate fixture/shadow
surface.  This module defines the future formal page contract and deliberately
fails closed until an approved canonical provider is configured.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import date
from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from topicpilot_api.database import get_session_factory
from topicpilot_api.formal_opportunity_publication import (
    read_latest_formal_opportunity_publication,
)
from topicpilot_api.problems import ApiProblem, NotFoundProblem
from topicpilot_api.schemas import (
    OpportunityDetailResponse,
    OpportunityPageRead,
)

OPPORTUNITY_PAGE_READ_CONTRACT_VERSION = "opportunity-page-read.v1"
FORMAL_PUBLICATION_STATUS = "FORMAL"
FORMAL_SOURCE_STATUS = "FORMAL_CANONICAL"
UNAVAILABLE_SOURCE_STATUS = "UNAVAILABLE"
_FORBIDDEN_PUBLICATION_VALUES = {
    "SHADOW",
    "SHADOW_ONLY",
    "RESEARCH",
    "RESEARCH_ONLY",
    "FIXTURE",
    "FIXTURE/SYNTHETIC",
    "DEMO",
}

router = APIRouter(prefix="/api/v2", tags=["opportunities"])
AsOf = Annotated[date | None, Query(alias="asOf")]
SectionKey = Annotated[str | None, Query(alias="sectionKey")]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


class FormalOpportunityProviderUnavailable(RuntimeError):
    """Raised while no canonical formal Opportunity provider is configured."""


class FormalOpportunityProvider(Protocol):
    """Read-only provider seam for a future canonical Opportunity publication."""

    publication_status: str
    source_status: str

    def read_page(
        self,
        *,
        as_of: date | None,
        section_key: str | None,
        limit: int,
        offset: int,
    ) -> Mapping[str, Any]: ...

    def read_detail(self, opportunity_id: str) -> Mapping[str, Any]: ...


class CanonicalOpportunityProvider:
    """Explicit placeholder; it never falls back to shadow or fixture data."""

    publication_status = UNAVAILABLE_SOURCE_STATUS
    source_status = UNAVAILABLE_SOURCE_STATUS

    def read_page(
        self,
        *,
        as_of: date | None,
        section_key: str | None,
        limit: int,
        offset: int,
    ) -> Mapping[str, Any]:
        del as_of, section_key, limit, offset
        raise FormalOpportunityProviderUnavailable(
            "No approved canonical formal Opportunity provider is configured."
        )

    def read_detail(self, opportunity_id: str) -> Mapping[str, Any]:
        del opportunity_id
        raise FormalOpportunityProviderUnavailable(
            "No approved canonical formal Opportunity provider is configured."
        )


class PersistedFormalOpportunityProvider:
    """Read the governed formal publication envelope from PostgreSQL."""

    publication_status = FORMAL_PUBLICATION_STATUS
    source_status = FORMAL_SOURCE_STATUS

    def read_page(
        self,
        *,
        as_of: date | None,
        section_key: str | None,
        limit: int,
        offset: int,
    ) -> Mapping[str, Any]:
        try:
            with get_session_factory()() as session:
                publication = read_latest_formal_opportunity_publication(
                    session,
                    as_of=as_of,
                )
                if publication is None:
                    raise FormalOpportunityProviderUnavailable(
                        "No persisted formal Opportunity publication is available."
                    )
                payload = dict(publication.page_payload)
        except FormalOpportunityProviderUnavailable:
            raise
        except SQLAlchemyError as exc:
            raise FormalOpportunityProviderUnavailable(
                "Formal Opportunity publication storage is unavailable."
            ) from exc

        sections = list(payload.get("sections", []))
        if section_key is not None:
            sections = [section for section in sections if section.get("sectionKey") == section_key]
        paged_sections: list[dict[str, Any]] = []
        remaining = offset
        remaining_limit = limit
        for section in sections:
            opportunities = list(section.get("opportunities", []))
            if remaining >= len(opportunities):
                remaining -= len(opportunities)
                continue
            opportunities = opportunities[remaining:]
            remaining = 0
            if remaining_limit:
                selected = opportunities[:remaining_limit]
                remaining_limit -= len(selected)
                paged_sections.append(
                    {
                        **section,
                        "opportunityCount": len(selected),
                        "opportunities": selected,
                    }
                )
            if not remaining_limit:
                break
        payload["sections"] = paged_sections
        return payload

    def read_detail(self, opportunity_id: str) -> Mapping[str, Any]:
        try:
            with get_session_factory()() as session:
                publication = read_latest_formal_opportunity_publication(session)
                if publication is None:
                    raise FormalOpportunityProviderUnavailable(
                        "No persisted formal Opportunity publication is available."
                    )
                page = dict(publication.page_payload)
                details = dict(publication.detail_payloads)
        except FormalOpportunityProviderUnavailable:
            raise
        except SQLAlchemyError as exc:
            raise FormalOpportunityProviderUnavailable(
                "Formal Opportunity publication storage is unavailable."
            ) from exc

        if opportunity_id in details:
            return details[opportunity_id]
        for section in page.get("sections", []):
            for opportunity in section.get("opportunities", []):
                if opportunity.get("opportunityId") == opportunity_id:
                    return {
                        **page,
                        "query": {"opportunityId": opportunity_id},
                        "opportunity": opportunity,
                    }
        if page.get("state") in {"DEFERRED", "UNAVAILABLE", "EMPTY"}:
            return {
                "contractVersion": page["contractVersion"],
                "state": page["state"],
                "publicationStatus": page["publicationStatus"],
                "dataStatus": page["dataStatus"],
                "sourceStatus": page["sourceStatus"],
                "asOf": page.get("asOf"),
                "updatedAt": page.get("updatedAt"),
                "query": {"opportunityId": opportunity_id},
                "providerLineage": page["providerLineage"],
                "opportunity": None,
            }
        raise NotFoundProblem(f"Formal Opportunity {opportunity_id!r} was not found")

def _unavailable_problem(exc: Exception) -> ApiProblem:
    return ApiProblem(
        503,
        "Opportunity page unavailable",
        str(exc),
        "https://topicpilot.example/problems/opportunity-unavailable",
    )


def _invalid_problem(detail: str) -> ApiProblem:
    return ApiProblem(
        500,
        "Opportunity page contract invalid",
        detail,
        "https://topicpilot.example/problems/opportunity-invalid",
    )


def _forbidden_value(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().upper()
    return normalized in _FORBIDDEN_PUBLICATION_VALUES or any(
        token in normalized for token in ("SHADOW", "FIXTURE", "RESEARCH_ONLY", "DEMO")
    )


def _assert_formal_source(payload: Mapping[str, Any]) -> None:
    """Reject shadow/research/demo payloads before response-model validation."""

    for key, value in payload.items():
        lowered = str(key).lower()
        # Nested Lifecycle/Selector blocks may be explicitly unavailable while
        # the parent Opportunity itself is formally published.
        if lowered == "publicationstatus" and value not in {
            FORMAL_PUBLICATION_STATUS,
            UNAVAILABLE_SOURCE_STATUS,
        }:
            raise ValueError(f"{key} must be formal or explicitly unavailable, got {value!r}")
        if lowered == "sourcestatus" and value != FORMAL_SOURCE_STATUS:
            raise ValueError(f"{key} must be formal, got {value!r}")
        if lowered == "datastatus" and _forbidden_value(value):
            raise ValueError("formal Opportunity payload cannot use shadow/research data status")
        if lowered in {"mode", "source", "authority"} and _forbidden_value(value):
            raise ValueError(f"formal Opportunity payload cannot use {key}={value!r}")
        if isinstance(value, Mapping):
            _assert_formal_source(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    _assert_formal_source(item)


def _same_as_of(actual: date | None, expected: date | None, field: str) -> None:
    if actual != expected:
        raise ValueError(f"{field} must match the page as-of date")


def _validate_selector(selector: Any, *, as_of: date | None, topic_type: str) -> None:
    candidates = selector.candidates
    if len(candidates) > 2:
        raise ValueError("Selector V1 must publish at most Top2 candidates")
    if topic_type == "PARENT" and selector.status in {"AVAILABLE", "EMPTY"}:
        raise ValueError("Parent topics cannot publish Lifecycle/Selector analysis")
    if selector.status == "AVAILABLE":
        if not candidates or selector.candidate_status != "PUBLISHED":
            raise ValueError("available Selector V1 output requires published candidates")
        if selector.publication_status != FORMAL_PUBLICATION_STATUS:
            raise ValueError("available Selector V1 output must be formally published")
        if selector.as_of is None:
            raise ValueError("available Selector V1 output requires an as-of date")
        _same_as_of(selector.as_of, as_of, "Selector V1 as-of")
        ranks = [candidate.rank for candidate in candidates]
        if ranks != list(range(1, len(candidates) + 1)):
            raise ValueError("Selector V1 ranks must be deterministic and contiguous")
        for candidate in candidates:
            _same_as_of(candidate.as_of, as_of, "Selector candidate as-of")
    elif selector.status == "EMPTY":
        if candidates or selector.candidate_status != "NO_CANDIDATE_AFTER_SCREEN":
            raise ValueError("empty Selector V1 output must fail closed without fallback")
    elif selector.status == "FAIL_CLOSED" and not selector.missing_evidence:
        raise ValueError("fail-closed Selector V1 output requires missing evidence codes")
    elif candidates:
        raise ValueError("deferred/unavailable Selector V1 output cannot contain candidates")


def _validate_lifecycle(lifecycle: Any, *, as_of: date | None, topic_type: str) -> None:
    if topic_type == "PARENT" and lifecycle.status in {"AVAILABLE"}:
        raise ValueError("Parent topics cannot publish Lifecycle analysis")
    if lifecycle.status == "AVAILABLE":
        if lifecycle.current_stage is None:
            raise ValueError("available Lifecycle context requires a stage")
        if lifecycle.publication_status != FORMAL_PUBLICATION_STATUS:
            raise ValueError("available Lifecycle context must be formally published")
        _same_as_of(lifecycle.as_of, as_of, "Lifecycle as-of")
    elif lifecycle.current_stage is not None:
        raise ValueError("unavailable Lifecycle context cannot carry a stage")


def _validate_summary(item: Any, *, page_as_of: date | None) -> None:
    _same_as_of(item.as_of, page_as_of, "Opportunity as-of")
    _validate_lifecycle(item.lifecycle, as_of=page_as_of, topic_type=item.topic.topic_type)
    _validate_selector(
        item.selector_v1,
        as_of=page_as_of,
        topic_type=item.topic.topic_type,
    )
    if item.technical_validation is not None:
        _same_as_of(item.technical_validation.as_of, page_as_of, "technical validation as-of")


def validate_formal_opportunity_page(payload: Mapping[str, Any]) -> OpportunityPageRead:
    """Validate a provider payload and enforce the formal/PIT page boundary."""

    try:
        if not isinstance(payload, Mapping):
            raise TypeError("Opportunity page provider payload must be an object")
        _assert_formal_source(payload)
        page = OpportunityPageRead.model_validate(payload)
    except (TypeError, ValueError, ValidationError) as exc:
        raise ValueError(str(exc)) from exc

    if page.contract_version != OPPORTUNITY_PAGE_READ_CONTRACT_VERSION:
        raise ValueError("unsupported Opportunity page contract")
    if page.state == "READY" and page.as_of is None:
        raise ValueError("ready Opportunity page requires an as-of date")
    if page.section_mapping_status != "AVAILABLE" and page.sections:
        raise ValueError("sections must be empty until backend grouping mapping is available")
    if page.section_mapping_status == "AVAILABLE":
        orders = [section.display_order for section in page.sections]
        if len(orders) != len(set(orders)) or orders != sorted(orders):
            raise ValueError("Opportunity sections must use deterministic backend order")

    opportunity_ids: list[str] = []
    total = 0
    for section in page.sections:
        if section.opportunity_count != len(section.opportunities):
            raise ValueError("section opportunityCount must be provider-owned and exact")
        card_orders = [item.display_order for item in section.opportunities]
        if len(card_orders) != len(set(card_orders)) or card_orders != sorted(card_orders):
            raise ValueError("Opportunity cards must use deterministic backend order")
        for item in section.opportunities:
            if item.section_key != section.section_key:
                raise ValueError("Opportunity sectionKey must match its backend section")
            _validate_summary(item, page_as_of=page.as_of)
            opportunity_ids.append(item.opportunity_id)
        total += section.opportunity_count

    if len(opportunity_ids) != len(set(opportunity_ids)):
        raise ValueError("Opportunity identities must be unique")
    if page.state == "READY" and total == 0:
        raise ValueError("ready Opportunity page cannot be empty")
    if page.state == "EMPTY" and total != 0:
        raise ValueError("empty Opportunity page cannot contain opportunities")
    if page.state in {"DEFERRED", "UNAVAILABLE", "ERROR"} and page.sections:
        raise ValueError("deferred/unavailable Opportunity page cannot expose partial cards")
    return page


def validate_formal_opportunity_detail(payload: Mapping[str, Any]) -> OpportunityDetailResponse:
    """Validate detail payload, including full-member and PIT isolation."""

    try:
        if not isinstance(payload, Mapping):
            raise TypeError("Opportunity detail provider payload must be an object")
        _assert_formal_source(payload)
        detail = OpportunityDetailResponse.model_validate(payload)
    except (TypeError, ValueError, ValidationError) as exc:
        raise ValueError(str(exc)) from exc

    if detail.contract_version != OPPORTUNITY_PAGE_READ_CONTRACT_VERSION:
        raise ValueError("unsupported Opportunity detail contract")
    if detail.opportunity is None:
        if detail.state == "READY":
            raise ValueError("ready Opportunity detail requires an opportunity")
        return detail

    opportunity = detail.opportunity
    if detail.state != "READY":
        raise ValueError("Opportunity detail with a resource must be READY")
    if detail.as_of is None:
        raise ValueError("ready Opportunity detail requires an as-of date")
    if opportunity.publication_status != detail.publication_status:
        raise ValueError("detail and Opportunity publication statuses must match")
    if opportunity.source_status != detail.source_status:
        raise ValueError("detail and Opportunity source statuses must match")
    _same_as_of(opportunity.as_of, detail.as_of, "detail Opportunity as-of")
    _validate_summary(opportunity, page_as_of=detail.as_of)
    if opportunity.members.status != "AVAILABLE" and opportunity.members.items:
        raise ValueError("unavailable full-member read model cannot expose partial members")
    for member in opportunity.members.items:
        _same_as_of(member.as_of, detail.as_of, "member as-of")
    return detail


class FormalOpportunityReadService:
    """Read-only service that accepts only a formal canonical provider."""

    def __init__(self, provider: FormalOpportunityProvider | None = None) -> None:
        self.provider = provider or CanonicalOpportunityProvider()
        publication_status = getattr(self.provider, "publication_status", UNAVAILABLE_SOURCE_STATUS)
        source_status = getattr(self.provider, "source_status", UNAVAILABLE_SOURCE_STATUS)
        if publication_status not in {FORMAL_PUBLICATION_STATUS, UNAVAILABLE_SOURCE_STATUS}:
            raise ValueError("formal Opportunity service cannot use shadow/research providers")
        if source_status not in {FORMAL_SOURCE_STATUS, UNAVAILABLE_SOURCE_STATUS}:
            raise ValueError("formal Opportunity service requires a canonical source")

    def list_opportunities(
        self,
        *,
        as_of: date | None,
        section_key: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        try:
            payload = self.provider.read_page(
                as_of=as_of,
                section_key=section_key,
                limit=limit,
                offset=offset,
            )
        except FormalOpportunityProviderUnavailable as exc:
            raise _unavailable_problem(exc) from exc
        try:
            return validate_formal_opportunity_page(payload).model_dump(mode="json", by_alias=True)
        except ValueError as exc:
            raise _invalid_problem(str(exc)) from exc

    def detail(self, opportunity_id: str) -> dict[str, Any]:
        try:
            payload = self.provider.read_detail(opportunity_id)
        except FormalOpportunityProviderUnavailable as exc:
            raise _unavailable_problem(exc) from exc
        except NotFoundProblem:
            raise
        try:
            return validate_formal_opportunity_detail(payload).model_dump(
                mode="json", by_alias=True
            )
        except ValueError as exc:
            raise _invalid_problem(str(exc)) from exc


_DEFAULT_SERVICE = FormalOpportunityReadService(
    PersistedFormalOpportunityProvider()
    if os.getenv("TOPICPILOT_FORMAL_OPPORTUNITY_PROVIDER", "UNAVAILABLE").upper()
    == "POSTGRES"
    else CanonicalOpportunityProvider()
)


def get_formal_opportunity_read_service() -> FormalOpportunityReadService:
    """Dependency hook used by tests and the future approved provider wiring."""

    return _DEFAULT_SERVICE


FormalService = Annotated[
    FormalOpportunityReadService,
    Depends(get_formal_opportunity_read_service),
]


@router.get(
    "/opportunities",
    response_model=OpportunityPageRead,
    summary="Read the formal Opportunity page",
    responses={
        500: {"description": "Configured provider returned an invalid formal payload"},
        503: {"description": "No canonical formal Opportunity provider is configured"},
    },
)
def list_opportunities(
    service: FormalService,
    as_of: AsOf = None,
    section_key: SectionKey = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> dict[str, Any]:
    return service.list_opportunities(
        as_of=as_of,
        section_key=section_key,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetailResponse,
    summary="Read one formal Opportunity detail",
    responses={
        404: {"description": "Opportunity was not found"},
        500: {"description": "Configured provider returned an invalid formal payload"},
        503: {"description": "No canonical formal Opportunity provider is configured"},
    },
)
def opportunity_detail(opportunity_id: str, service: FormalService) -> dict[str, Any]:
    return service.detail(opportunity_id)


__all__ = [
    "FORMAL_PUBLICATION_STATUS",
    "FORMAL_SOURCE_STATUS",
    "OPPORTUNITY_PAGE_READ_CONTRACT_VERSION",
    "CanonicalOpportunityProvider",
    "FormalOpportunityProvider",
    "FormalOpportunityProviderUnavailable",
    "FormalOpportunityReadService",
    "PersistedFormalOpportunityProvider",
    "get_formal_opportunity_read_service",
    "router",
    "validate_formal_opportunity_detail",
    "validate_formal_opportunity_page",
]
