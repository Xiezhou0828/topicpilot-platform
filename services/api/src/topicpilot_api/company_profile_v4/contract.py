from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyResearchV4PublicResponse(BaseModel):
    """Explicit public envelope; evidence ledgers and authority IDs are excluded."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    stock_code: str = Field(alias="stockCode")
    display_name: str | None = Field(default=None, alias="displayName")
    package_version: str | None = Field(default=None, alias="packageVersion")
    contract_version: str | None = Field(default=None, alias="contractVersion")
    research_as_of: str | None = Field(default=None, alias="researchAsOf")
    publication_status: Literal["PUBLISHED", "UNPUBLISHED", "NOT_CONNECTED", "BLOCKED"] = Field(
        alias="publicationStatus"
    )
    research_governance: dict[str, Any] | None = Field(default=None, alias="researchGovernance")
    overview_data: dict[str, Any] | None = Field(default=None, alias="overviewData")
    sections: dict[str, Any] | None = None
    investment_themes: list[dict[str, Any]] = Field(default_factory=list, alias="investmentThemes")
    operating_matrix: list[dict[str, Any]] = Field(default_factory=list, alias="operatingMatrix")
    finance: dict[str, Any] | None = None
    limitations_zh_tw: list[str] = Field(default_factory=list, alias="limitationsZhTw")
