# ruff: noqa: RUF001

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from .contract import CompanyResearchV4PublicResponse


def _minimal(code: str, status: str, note: str) -> CompanyResearchV4PublicResponse:
    return CompanyResearchV4PublicResponse(
        stockCode=code,
        publicationStatus=status,  # type: ignore[arg-type]
        limitationsZhTw=[note],
    )


class DatabaseCompanyProfileV4ReadStore:
    """Read the newest immutable, owner-approved public research publication."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_public(self, stock_code: str) -> CompanyResearchV4PublicResponse:
        code = stock_code.strip()
        if not code:
            return _minimal(code, "BLOCKED", "股票代碼格式無效。")

        identities = self.session.execute(
            text(
                "SELECT COUNT(DISTINCT i.id) "
                "FROM topicpilot.instruments AS i "
                "WHERE i.instrument_code = :code"
            ),
            {"code": code},
        ).scalar_one()
        if identities == 0:
            return _minimal(code, "NOT_CONNECTED", "目前沒有可公開的公司研究資料。")
        if identities != 1:
            return _minimal(code, "BLOCKED", "股票代碼對應多筆市場資料，暫不公開。")

        instrument = (
            self.session.execute(
                text(
                    "SELECT id, is_active FROM topicpilot.instruments WHERE instrument_code = :code"
                ),
                {"code": code},
            )
            .mappings()
            .one()
        )
        if not instrument["is_active"]:
            return _minimal(code, "NOT_CONNECTED", "此股票目前未啟用，暫不公開研究資料。")

        row = (
            self.session.execute(
                text(
                    "SELECT p.public_payload "
                    "FROM topicpilot.company_research_publications AS p "
                    "WHERE p.instrument_id = :instrument_id "
                    "ORDER BY p.publication_version DESC, p.published_at DESC "
                    "LIMIT 1"
                ),
                {"instrument_id": instrument["id"]},
            )
            .mappings()
            .first()
        )
        if row is None:
            return _minimal(code, "NOT_CONNECTED", "目前沒有可公開的公司研究資料。")
        try:
            result = CompanyResearchV4PublicResponse.model_validate(row["public_payload"])
        except (TypeError, ValueError):
            return _minimal(code, "BLOCKED", "正式研究發布資料不符合公開契約，暫不公開。")
        if result.stock_code != code or result.publication_status != "PUBLISHED":
            return _minimal(code, "BLOCKED", "正式研究發布身份或狀態不一致，暫不公開。")
        return result


__all__ = ["DatabaseCompanyProfileV4ReadStore"]
