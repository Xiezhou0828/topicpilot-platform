from __future__ import annotations

from .contract import (
    CompanyResearchReadModel,
    PublicCompanyResearchProjection,
)


def publication_issues(record: CompanyResearchReadModel) -> list[str]:
    issues: list[str] = []
    if record.publication_status != "PUBLISHED":
        issues.append("PUBLICATION_STATUS_NOT_PUBLISHED")
    if record.review_status != "APPROVED":
        issues.append("OWNER_REVIEW_NOT_APPROVED")
    if record.source_rights_status != "APPROVED":
        issues.append("SOURCE_RIGHTS_NOT_APPROVED")
    if record.approval_evidence is None or not record.reviewer:
        issues.append("APPROVAL_EVIDENCE_MISSING")
    if record.formal_topic_authority_mutation:
        issues.append("FORMAL_TOPIC_AUTHORITY_MUTATION_FORBIDDEN")
    if not record.sections:
        issues.append("RESEARCH_SECTIONS_MISSING")
    if any(section.status != "VERIFIED" for section in record.sections):
        issues.append("RESEARCH_SECTION_NOT_VERIFIED")
    if any(source.content_status != "VERIFIED" for source in record.sources):
        issues.append("SOURCE_CONTENT_NOT_VERIFIED")
    if any(source.rights_status != "APPROVED" for source in record.sources):
        issues.append("SOURCE_RIGHTS_NOT_VERIFIED")
    return issues


def build_public_projection(
    record: CompanyResearchReadModel,
) -> PublicCompanyResearchProjection:
    issues = publication_issues(record)
    if issues:
        status = "BLOCKED" if "SOURCE_RIGHTS_NOT_APPROVED" in issues else "UNPUBLISHED"
        return PublicCompanyResearchProjection(
            company_code=record.company_code,
            publication_status=status,
            limitations_zh_tw=["研究內容尚未通過正式發布 Gate; 暫不公開。"],
        )

    official_sources = [
        source.url
        for source in record.sources
        if source.source_type == "official_company_website"
    ]
    return PublicCompanyResearchProjection(
        company_code=record.company_code,
        research_version=record.research_version,
        publication_status="PUBLISHED",
        effective_date=record.effective_date,
        as_of_date=record.as_of_date,
        company_website=record.company_website,
        sections=record.sections,
        official_sources=official_sources,
        limitations_zh_tw=record.limitations_zh_tw,
    )
