from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


ResearchPublicationStatus = Literal[
    "DRAFT",
    "SOURCE_PENDING",
    "REVIEW_REQUIRED",
    "APPROVED",
    "PUBLISHED",
    "RETRACTED",
]
ResearchReviewStatus = Literal["PENDING", "APPROVED", "REJECTED"]
ResearchContentStatus = Literal["VERIFIED", "PENDING_REVIEW", "UNAVAILABLE"]
ResearchRightsStatus = Literal["APPROVED", "UNVERIFIED", "BLOCKED"]


class ResearchSourceRef(CompanyResearchModel):
    source_id: str = Field(min_length=1)
    source_type: Literal[
        "official_company_website",
        "official_filing",
        "official_exchange",
        "other",
    ]
    title_zh_tw: str = Field(min_length=1)
    url: str = Field(min_length=1)
    published_at: date | None = None
    retrieved_at: datetime | None = None
    content_status: ResearchContentStatus = "PENDING_REVIEW"
    rights_status: ResearchRightsStatus = "UNVERIFIED"


class ResearchSection(CompanyResearchModel):
    key: Literal[
        "overview",
        "business",
        "industry",
        "growth_risk",
        "financial",
        "sources",
    ]
    title_zh_tw: str = Field(min_length=1)
    body_zh_tw: str = Field(min_length=1)
    status: ResearchContentStatus = "PENDING_REVIEW"
    source_ids: list[str] = Field(default_factory=list)


class ResearchApprovalEvidence(CompanyResearchModel):
    reviewer: str = Field(min_length=1)
    approved_at: datetime
    decision_id: str = Field(min_length=1)
    notes: str | None = None


class CompanyResearchReadModel(CompanyResearchModel):
    """Versioned, owner-reviewed Company Research V3 read model.

    This is intentionally read-only. A record cannot become public merely by
    existing in a fixture or by setting a frontend flag; the publication gate
    checks every required authority field before building a public projection.
    """

    schema_version: Literal["company-research-v3"] = "company-research-v3"
    company_code: str = Field(min_length=1)
    research_version: str = Field(min_length=1)
    effective_date: date
    as_of_date: date
    publication_status: ResearchPublicationStatus
    review_status: ResearchReviewStatus
    source_rights_status: ResearchRightsStatus
    reviewer: str | None = None
    approval_evidence: ResearchApprovalEvidence | None = None
    company_website: str | None = None
    sections: list[ResearchSection] = Field(default_factory=list)
    sources: list[ResearchSourceRef] = Field(default_factory=list)
    limitations_zh_tw: list[str] = Field(default_factory=list)
    supersedes_version: str | None = None
    formal_topic_authority_mutation: Literal[False] = False


class PublicCompanyResearchProjection(CompanyResearchModel):
    """Public-safe projection; internal evidence and third-party sources stay out."""

    company_code: str
    research_version: str | None = None
    publication_status: Literal["PUBLISHED", "UNPUBLISHED", "NOT_CONNECTED", "BLOCKED"]
    effective_date: date | None = None
    as_of_date: date | None = None
    company_website: str | None = None
    sections: list[ResearchSection] = Field(default_factory=list)
    official_sources: list[str] = Field(default_factory=list)
    limitations_zh_tw: list[str] = Field(default_factory=list)
