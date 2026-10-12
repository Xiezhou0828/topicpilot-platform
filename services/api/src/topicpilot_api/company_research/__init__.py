"""Governed Company Research V3 read-only contract and publication boundary."""

from .contract import CompanyResearchReadModel, PublicCompanyResearchProjection
from .gate import build_public_projection, publication_issues

__all__ = [
    "CompanyResearchReadModel",
    "PublicCompanyResearchProjection",
    "build_public_projection",
    "publication_issues",
]
