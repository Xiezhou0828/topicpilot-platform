# ruff: noqa: RUF001

"""Evidence, review, and public-safe projection boundaries for Company Research."""

from __future__ import annotations

from .contract import (
    PublicSafeCompanyResearchProjection,
    ResearchClaim,
    ResearchVersion,
)


def project_public_safe(version: ResearchVersion) -> PublicSafeCompanyResearchProjection:
    """Project only approved, rights-cleared research claims.

    Candidate Topic suggestions and valuation/target-price material are not part
    of this shape. The function is intentionally usable without a database and
    returns an unpublished projection unless the research version is explicitly
    published.
    """

    approved_evidence = {
        evidence.evidence_id
        for evidence in version.evidence
        if evidence.status == "VERIFIED" and evidence.rights_status == "APPROVED"
    }
    claims: list[ResearchClaim] = []
    for claim in version.claims:
        if claim.review_status != "APPROVED" or claim.is_formal_topic_authority:
            continue
        if claim.evidence_ids and not set(claim.evidence_ids) <= approved_evidence:
            continue
        claims.append(claim)
    return PublicSafeCompanyResearchProjection(
        ticker=version.ticker,
        version=version.version,
        publication_status=("PUBLISHED" if version.status == "PUBLISHED" else "UNPUBLISHED"),
        approved_claims=claims,
        sources=sorted(approved_evidence),
        limitations=[
            "題材建議不等於正式題材關聯，需另行審核。",
            "估值、目標價、DCF、SOTP 與未核准預測不在公開研究投影中。",
        ],
    )


__all__ = ["project_public_safe"]
