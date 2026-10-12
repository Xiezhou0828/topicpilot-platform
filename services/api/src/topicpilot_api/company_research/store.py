from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .contract import CompanyResearchReadModel, PublicCompanyResearchProjection
from .gate import build_public_projection


class CompanyResearchReadStore(Protocol):
    def get_public(self, company_code: str) -> PublicCompanyResearchProjection: ...


def not_connected(company_code: str) -> PublicCompanyResearchProjection:
    return PublicCompanyResearchProjection(
        company_code=company_code,
        publication_status="NOT_CONNECTED",
        limitations_zh_tw=["正式研究資料來源尚未接通。"],
    )


class EmptyCompanyResearchReadStore:
    def get_public(self, company_code: str) -> PublicCompanyResearchProjection:
        return not_connected(company_code)


class FileCompanyResearchReadStore:
    """Read-only adapter for an explicitly supplied, versioned JSON read model."""

    def __init__(self, path: str | None) -> None:
        self.path = Path(path) if path else None

    def _records(self) -> list[CompanyResearchReadModel]:
        if self.path is None or not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            items = raw.get("records", []) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                return []
            return [CompanyResearchReadModel.model_validate(item) for item in items]
        except (OSError, json.JSONDecodeError, ValidationError, TypeError, ValueError):
            return []

    def get_public(self, company_code: str) -> PublicCompanyResearchProjection:
        normalized = company_code.strip()
        for record in self._records():
            if record.company_code == normalized:
                return build_public_projection(record)
        return not_connected(normalized)
