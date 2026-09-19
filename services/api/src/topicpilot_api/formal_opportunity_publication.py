"""Formal Opportunity authority package, writer, and persisted readback."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .formal_opportunity_universe import FormalOpportunityUniverseReadModel
from .orm.formal_opportunity import FormalOpportunityPublication

FORMAL_OPPORTUNITY_AUTHORITY_VERSION = "opportunity-formal-authority-20260920.v1"
FORMAL_OPPORTUNITY_PROVIDER_VERSION = "formal-opportunity-provider.v1"
FORMAL_OPPORTUNITY_CONTRACT_VERSION = "opportunity-page-read.v1"
FORMAL_OPPORTUNITY_PUBLICATION_STATES = frozenset(
    {"PUBLISHED", "EMPTY", "DEFERRED", "UNAVAILABLE", "SUPERSEDED"}
)
PUBLICATION_NAMESPACE = uuid.UUID("8b5ebbc3-f6e1-5bd2-bd8b-32c85d98fdbb")


class FormalOpportunityPublicationError(ValueError):
    """Raised when a formal Opportunity publication cannot be trusted."""


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FormalOpportunityAuthorityPackage:
    as_of: date
    publication_state: str
    authority_version: str
    provider_version: str
    source_artifact_id: str
    source_artifact_hash: str
    lineage_hash: str
    page_payload: dict[str, Any]
    detail_payloads: dict[str, dict[str, Any]]
    diagnostic_reason: str | None = None

    @property
    def publication_key(self) -> str:
        return f"{self.authority_version}:{self.as_of.isoformat()}:{self.lineage_hash}"

    def __post_init__(self) -> None:
        if self.publication_state not in FORMAL_OPPORTUNITY_PUBLICATION_STATES:
            raise FormalOpportunityPublicationError(
                "unsupported formal Opportunity publication state"
            )
        if self.page_payload.get("publicationStatus") != "FORMAL":
            raise FormalOpportunityPublicationError("formal Opportunity page must be FORMAL")
        if self.page_payload.get("sourceStatus") != "FORMAL_CANONICAL":
            raise FormalOpportunityPublicationError(
                "formal Opportunity page must use FORMAL_CANONICAL source"
            )
        if self.page_payload.get("asOf") != self.as_of.isoformat():
            raise FormalOpportunityPublicationError("formal Opportunity page as-of mismatch")


def build_deferred_formal_opportunity_package(
    universe: FormalOpportunityUniverseReadModel,
    *,
    source_artifact_id: str | None = None,
) -> FormalOpportunityAuthorityPackage:
    """Publish the formal universe boundary without inventing downstream rules."""

    universe_payload = universe.to_dict()
    source_hash = _hash(universe_payload)
    if universe.status == "ZERO_VALID_CANDIDATES":
        state = "EMPTY"
    elif universe.status == "READY":
        state = "DEFERRED"
    else:
        state = "UNAVAILABLE"
    reason = ";".join(universe.reasons) or (
        "FORMAL_UNIVERSE_READY_DOWNSTREAM_PUBLICATION_NOT_AVAILABLE"
        if state == "DEFERRED"
        else "FORMAL_UNIVERSE_NOT_PUBLISHABLE"
    )
    page = {
        "contractVersion": FORMAL_OPPORTUNITY_CONTRACT_VERSION,
        "state": state,
        "publicationStatus": "FORMAL",
        "dataStatus": f"FORMAL_UNIVERSE_{universe.status}",
        "sourceStatus": "FORMAL_CANONICAL",
        "asOf": universe.as_of.isoformat(),
        "updatedAt": datetime(
            universe.as_of.year,
            universe.as_of.month,
            universe.as_of.day,
            tzinfo=UTC,
        ).isoformat(),
        "sectionMappingStatus": "UNAVAILABLE",
        "providerLineage": {
            "provider": "formal-opportunity-provider",
            "authority": "FORMAL_OPPORTUNITY_AUTHORITY",
            "contractVersion": FORMAL_OPPORTUNITY_CONTRACT_VERSION,
            "sourceArtifactId": source_artifact_id
            or f"formal-opportunity-universe:{universe.contract_version}:{universe.as_of}",
            "sourceArtifactHash": source_hash,
            "policyVersion": FORMAL_OPPORTUNITY_AUTHORITY_VERSION,
        },
        "sections": [],
    }
    return FormalOpportunityAuthorityPackage(
        as_of=universe.as_of,
        publication_state=state,
        authority_version=FORMAL_OPPORTUNITY_AUTHORITY_VERSION,
        provider_version=FORMAL_OPPORTUNITY_PROVIDER_VERSION,
        source_artifact_id=page["providerLineage"]["sourceArtifactId"],
        source_artifact_hash=source_hash,
        lineage_hash=_hash({"universe": universe_payload, "page": page}),
        page_payload=page,
        detail_payloads={},
        diagnostic_reason=reason,
    )


def build_formal_opportunity_package(
    *,
    as_of: date,
    page_payload: dict[str, Any],
    detail_payloads: dict[str, dict[str, Any]] | None = None,
    authority_version: str = FORMAL_OPPORTUNITY_AUTHORITY_VERSION,
    provider_version: str = FORMAL_OPPORTUNITY_PROVIDER_VERSION,
    source_artifact_id: str,
    source_artifact_hash: str,
    diagnostic_reason: str | None = None,
) -> FormalOpportunityAuthorityPackage:
    """Validate and package an already-authorized formal page payload."""

    from .opportunity_api import (
        validate_formal_opportunity_detail,
        validate_formal_opportunity_page,
    )

    page = validate_formal_opportunity_page(page_payload)
    if page.as_of != as_of:
        raise FormalOpportunityPublicationError("page as-of does not match package")
    normalized_page = page.model_dump(mode="json", by_alias=True)
    normalized_details: dict[str, dict[str, Any]] = {}
    for opportunity_id, payload in (detail_payloads or {}).items():
        detail = validate_formal_opportunity_detail(payload)
        if detail.as_of != as_of:
            raise FormalOpportunityPublicationError("detail as-of does not match package")
        normalized_details[opportunity_id] = detail.model_dump(mode="json", by_alias=True)
    lineage_hash = _hash(
        {
            "authorityVersion": authority_version,
            "sourceArtifactHash": source_artifact_hash,
            "page": normalized_page,
            "details": normalized_details,
        }
    )
    state_map = {
        "READY": "PUBLISHED",
        "EMPTY": "EMPTY",
        "DEFERRED": "DEFERRED",
        "UNAVAILABLE": "UNAVAILABLE",
        "ERROR": "UNAVAILABLE",
    }
    return FormalOpportunityAuthorityPackage(
        as_of=as_of,
        publication_state=state_map[page.state],
        authority_version=authority_version,
        provider_version=provider_version,
        source_artifact_id=source_artifact_id,
        source_artifact_hash=source_artifact_hash,
        lineage_hash=lineage_hash,
        page_payload=normalized_page,
        detail_payloads=normalized_details,
        diagnostic_reason=diagnostic_reason,
    )


def write_formal_opportunity_publication(
    session: Session,
    package: FormalOpportunityAuthorityPackage,
) -> dict[str, Any]:
    """Write one idempotent publication and reject duplicate conflicts."""

    existing = session.scalar(
        select(FormalOpportunityPublication).where(
            FormalOpportunityPublication.publication_key == package.publication_key
        )
    )
    if existing is not None:
        if (
            existing.lineage_hash != package.lineage_hash
            or existing.page_payload != package.page_payload
            or existing.detail_payloads != package.detail_payloads
        ):
            raise FormalOpportunityPublicationError(
                "FORMAL_OPPORTUNITY_DUPLICATE_PUBLICATION_CONFLICT"
            )
        return {
            "operation": "FORMAL_OPPORTUNITY_UNCHANGED",
            "publicationId": str(existing.id),
            "asOf": package.as_of.isoformat(),
            "lineageHash": package.lineage_hash,
        }

    publication = FormalOpportunityPublication(
        id=uuid.uuid5(PUBLICATION_NAMESPACE, package.publication_key),
        as_of=package.as_of,
        publication_state=package.publication_state,
        authority_version=package.authority_version,
        contract_version=FORMAL_OPPORTUNITY_CONTRACT_VERSION,
        publication_key=package.publication_key,
        provider_version=package.provider_version,
        source_artifact_id=package.source_artifact_id,
        source_artifact_hash=package.source_artifact_hash,
        lineage_hash=package.lineage_hash,
        page_payload=package.page_payload,
        detail_payloads=package.detail_payloads,
        published_at=datetime.now(UTC),
        diagnostic_reason=package.diagnostic_reason,
    )
    session.add(publication)
    session.flush()
    return {
        "operation": "FORMAL_OPPORTUNITY_PUBLISHED",
        "publicationId": str(publication.id),
        "asOf": package.as_of.isoformat(),
        "lineageHash": package.lineage_hash,
    }


def read_latest_formal_opportunity_publication(
    session: Session,
    *,
    as_of: date | None = None,
) -> FormalOpportunityPublication | None:
    """Read only the latest non-superseded formal publication at or before as-of."""

    statement = select(FormalOpportunityPublication).where(
        FormalOpportunityPublication.publication_state != "SUPERSEDED"
    )
    if as_of is not None:
        statement = statement.where(FormalOpportunityPublication.as_of == as_of)
    else:
        statement = statement.where(FormalOpportunityPublication.as_of <= date.today())
    return session.scalar(
        statement.order_by(
            FormalOpportunityPublication.as_of.desc(),
            FormalOpportunityPublication.created_at.desc(),
            FormalOpportunityPublication.id.desc(),
        ).limit(1)
    )


__all__ = [
    "FORMAL_OPPORTUNITY_AUTHORITY_VERSION",
    "FORMAL_OPPORTUNITY_CONTRACT_VERSION",
    "FORMAL_OPPORTUNITY_PROVIDER_VERSION",
    "FormalOpportunityAuthorityPackage",
    "FormalOpportunityPublicationError",
    "build_deferred_formal_opportunity_package",
    "build_formal_opportunity_package",
    "read_latest_formal_opportunity_publication",
    "write_formal_opportunity_publication",
]
