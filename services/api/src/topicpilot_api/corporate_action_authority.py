"""Governed, date-effective corporate-action trading-status authority.

This module is a small input boundary for official exchange company-action
records.  It deliberately contains no price data and does not write to the
database.  Records are data, not instrument-specific resolver rules.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

from .market_data.availability import LEGITIMATE_UNAVAILABLE_CODES

_AUTHORITY_FILE = Path(__file__).with_name("reference_data") / "corporate_action_authorities.json"
_OFFICIAL_REDUCTION_SOURCES = frozenset(
    {"TWSE_OFFICIAL_REDUCTION", "TPEX_OFFICIAL_REDUCTION"}
)


class CorporateActionAuthorityError(ValueError):
    """Raised when a corporate-action authority record is unsafe to use."""


@dataclass(frozen=True)
class CorporateActionAuthorityRecord:
    """One official company-action interval that maps to trading status."""

    symbol: str
    market: str
    action_type: str
    effective_from: date
    effective_to: date
    resume_date: date | None
    source_authority: str
    source_reference: str
    status_mapping: str
    reason_code: str
    published_at: datetime | None = None
    observed_at: datetime | None = None
    reduction_ratio_pct: Decimal | None = None
    expected_close: bool = False

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.market.strip():
            raise CorporateActionAuthorityError("MISSING_INSTRUMENT_IDENTITY")
        if not self.action_type.strip():
            raise CorporateActionAuthorityError("MISSING_ACTION_TYPE")
        if self.effective_to < self.effective_from:
            raise CorporateActionAuthorityError("INVALID_EFFECTIVE_RANGE")
        if self.resume_date is not None and self.resume_date <= self.effective_to:
            raise CorporateActionAuthorityError("INVALID_RESUME_BOUNDARY")
        if self.source_authority not in _OFFICIAL_REDUCTION_SOURCES:
            raise CorporateActionAuthorityError(
                f"UNSUPPORTED_CORPORATE_ACTION_SOURCE:{self.source_authority}"
            )
        if not self.source_reference.startswith(("https://", "http://")):
            raise CorporateActionAuthorityError("MISSING_CORPORATE_ACTION_REFERENCE")
        if self.status_mapping not in LEGITIMATE_UNAVAILABLE_CODES:
            raise CorporateActionAuthorityError(
                f"UNSUPPORTED_CORPORATE_ACTION_STATUS:{self.status_mapping}"
            )
        if not self.reason_code.strip():
            raise CorporateActionAuthorityError("MISSING_CORPORATE_ACTION_REASON")
        if self.reduction_ratio_pct is not None and self.reduction_ratio_pct < 0:
            raise CorporateActionAuthorityError("INVALID_REDUCTION_RATIO")

    def is_effective_on(self, trading_date: date) -> bool:
        return self.effective_from <= trading_date <= self.effective_to

    def to_trading_status_record(self) -> Any:
        """Convert to the resolver's common authority record lazily."""

        from .trading_status_authority import AuthorityClass, TradingStatusAuthorityRecord

        return TradingStatusAuthorityRecord(
            status_code=self.status_mapping,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            source=self.source_authority,
            source_reference=self.source_reference,
            reason_code=self.reason_code,
            observed_at=self.observed_at,
            published_at=self.published_at,
            authority_class=AuthorityClass.CORPORATE_ACTION.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "market": self.market,
            "actionType": self.action_type,
            "effectiveFrom": self.effective_from,
            "effectiveTo": self.effective_to,
            "resumeDate": self.resume_date,
            "sourceAuthority": self.source_authority,
            "sourceReference": self.source_reference,
            "statusMapping": self.status_mapping,
            "reasonCode": self.reason_code,
            "publishedAt": self.published_at,
            "observedAt": self.observed_at,
            "reductionRatioPct": self.reduction_ratio_pct,
            "expectedClose": self.expected_close,
        }


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise CorporateActionAuthorityError(f"MISSING_CORPORATE_ACTION_{field.upper()}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_{field.upper()}") from exc


def _parse_datetime(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_{field.upper()}")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_{field.upper()}") from exc


def corporate_action_from_mapping(payload: Mapping[str, Any]) -> CorporateActionAuthorityRecord:
    """Validate one sanitized authority input record."""

    reduction_ratio = payload.get("reductionRatioPct")
    parsed_ratio: Decimal | None = None
    if reduction_ratio is not None:
        try:
            parsed_ratio = Decimal(str(reduction_ratio))
        except (InvalidOperation, ValueError) as exc:
            raise CorporateActionAuthorityError("INVALID_REDUCTION_RATIO") from exc
    return CorporateActionAuthorityRecord(
        symbol=str(payload.get("symbol") or ""),
        market=str(payload.get("market") or "").upper(),
        action_type=str(payload.get("actionType") or ""),
        effective_from=_parse_date(payload.get("effectiveFrom"), "effective_from"),
        effective_to=_parse_date(payload.get("effectiveTo"), "effective_to"),
        resume_date=(
            _parse_date(payload.get("resumeDate"), "resume_date")
            if payload.get("resumeDate") is not None
            else None
        ),
        source_authority=str(payload.get("sourceAuthority") or ""),
        source_reference=str(payload.get("sourceReference") or ""),
        status_mapping=str(payload.get("statusMapping") or "").upper(),
        reason_code=str(payload.get("reasonCode") or ""),
        published_at=_parse_datetime(payload.get("publishedAt"), "published_at"),
        observed_at=_parse_datetime(payload.get("observedAt"), "observed_at"),
        reduction_ratio_pct=parsed_ratio,
        expected_close=bool(payload.get("expectedClose", False)),
    )


def parse_corporate_action_authorities(
    payload: Mapping[str, Any],
) -> tuple[CorporateActionAuthorityRecord, ...]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise CorporateActionAuthorityError("CORPORATE_ACTION_RECORDS_MISSING")
    parsed = tuple(
        corporate_action_from_mapping(item) for item in records if isinstance(item, Mapping)
    )
    if len(parsed) != len(records):
        raise CorporateActionAuthorityError("CORPORATE_ACTION_RECORD_NOT_OBJECT")
    keys = [(item.symbol, item.market, item.action_type, item.effective_from) for item in parsed]
    if len(keys) != len(set(keys)):
        raise CorporateActionAuthorityError("DUPLICATE_CORPORATE_ACTION_RECORD")
    return parsed


@lru_cache(maxsize=1)
def load_corporate_action_authorities() -> tuple[CorporateActionAuthorityRecord, ...]:
    """Load the bounded, sanitized repository authority input."""

    try:
        payload = json.loads(_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorporateActionAuthorityError("CORPORATE_ACTION_AUTHORITY_UNAVAILABLE") from exc
    if not isinstance(payload, Mapping):
        raise CorporateActionAuthorityError("CORPORATE_ACTION_AUTHORITY_INVALID")
    return parse_corporate_action_authorities(payload)


def corporate_action_authorities_for(
    *, symbol: str, market: str, trading_date: date
) -> tuple[CorporateActionAuthorityRecord, ...]:
    """Return only records effective for one date-effective instrument."""

    return tuple(
        item
        for item in load_corporate_action_authorities()
        if item.symbol == symbol
        and item.market == market.upper()
        and item.is_effective_on(trading_date)
    )


__all__ = [
    "CorporateActionAuthorityError",
    "CorporateActionAuthorityRecord",
    "corporate_action_authorities_for",
    "corporate_action_from_mapping",
    "load_corporate_action_authorities",
    "parse_corporate_action_authorities",
]
