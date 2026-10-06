"""Official price-basis authority for corporate-action resume sessions.

Trading-status authority and price-basis authority are intentionally separate
inputs.  A status record explains why an instrument was unavailable; this
record explains which official price is permitted for the resume-session daily
comparison while retaining the last actually traded close as provenance.

This module is read-only and contains no database or publication behavior.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

_AUTHORITY_FILE = (
    Path(__file__).with_name("reference_data") / "corporate_action_price_authorities.json"
)
_OFFICIAL_DAILY_SOURCES = {"TPE": "TWSE_OFFICIAL_DAILY", "TWO": "TPEX_OFFICIAL_DAILY"}
_OFFICIAL_ACTION_SOURCES = frozenset({"TWSE_OFFICIAL_REDUCTION", "TPEX_OFFICIAL_REDUCTION"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CorporateActionPriceAuthorityError(ValueError):
    """Raised when official price-basis evidence cannot be trusted."""


def _positive_decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CorporateActionPriceAuthorityError(f"INVALID_{field.upper()}") from exc
    if not number.is_finite() or number <= 0:
        raise CorporateActionPriceAuthorityError(f"INVALID_{field.upper()}")
    return number


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise CorporateActionPriceAuthorityError(f"MISSING_{field.upper()}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CorporateActionPriceAuthorityError(f"INVALID_{field.upper()}") from exc


def _parse_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise CorporateActionPriceAuthorityError(f"INVALID_{field.upper()}")
    return value


def _parse_url(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.startswith(("https://", "http://")):
        raise CorporateActionPriceAuthorityError(f"MISSING_{field.upper()}")
    return value


@dataclass(frozen=True)
class CorporateActionPriceAuthorityRecord:
    """One fully sourced official price-basis record for a resume session."""

    symbol: str
    market: str
    action_type: str
    effective_from: date
    effective_to: date
    resume_date: date
    previous_traded_close_date: date
    previous_traded_close: Decimal
    comparison_reference_date: date
    comparison_reference: Decimal
    source_authority: str
    source_reference: str
    source_response_hash: str
    previous_traded_close_source: str
    previous_traded_close_source_reference: str
    previous_traded_close_response_hash: str
    detail_source_reference: str | None = None
    detail_response_hash: str | None = None
    finality: str = "FINAL"

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.market.strip():
            raise CorporateActionPriceAuthorityError("MISSING_INSTRUMENT_IDENTITY")
        if not self.action_type.strip():
            raise CorporateActionPriceAuthorityError("MISSING_ACTION_TYPE")
        if self.effective_to < self.effective_from:
            raise CorporateActionPriceAuthorityError("INVALID_EFFECTIVE_RANGE")
        if self.resume_date <= self.effective_to:
            raise CorporateActionPriceAuthorityError("INVALID_RESUME_BOUNDARY")
        if self.previous_traded_close_date >= self.resume_date:
            raise CorporateActionPriceAuthorityError("INVALID_PREVIOUS_TRADE_DATE")
        if self.comparison_reference_date != self.resume_date:
            raise CorporateActionPriceAuthorityError("COMPARISON_REFERENCE_DATE_MISMATCH")
        if self.source_authority not in _OFFICIAL_ACTION_SOURCES:
            raise CorporateActionPriceAuthorityError(
                f"UNSUPPORTED_CORPORATE_ACTION_SOURCE:{self.source_authority}"
            )
        if self.previous_traded_close_source != _OFFICIAL_DAILY_SOURCES.get(self.market.upper()):
            raise CorporateActionPriceAuthorityError("INVALID_PREVIOUS_TRADE_SOURCE")
        if self.finality != "FINAL":
            raise CorporateActionPriceAuthorityError("PRICE_AUTHORITY_NOT_FINAL")
        for field in (
            "source_response_hash",
            "previous_traded_close_response_hash",
        ):
            if _SHA256_RE.fullmatch(getattr(self, field)) is None:
                raise CorporateActionPriceAuthorityError(f"INVALID_{field.upper()}")
        if (
            self.detail_response_hash is not None
            and _SHA256_RE.fullmatch(self.detail_response_hash) is None
        ):
            raise CorporateActionPriceAuthorityError("INVALID_DETAIL_RESPONSE_HASH")
        if self.detail_source_reference is not None and not self.detail_source_reference.startswith(
            ("https://", "http://")
        ):
            raise CorporateActionPriceAuthorityError("INVALID_DETAIL_SOURCE_REFERENCE")

    def is_applicable_on(self, *, target: date, prior: date) -> bool:
        return (
            self.resume_date == target
            and self.effective_to < target
            and self.effective_from <= prior <= self.effective_to
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "market": self.market,
            "actionType": self.action_type,
            "effectiveFrom": self.effective_from.isoformat(),
            "effectiveTo": self.effective_to.isoformat(),
            "resumeDate": self.resume_date.isoformat(),
            "previousTradedCloseDate": self.previous_traded_close_date.isoformat(),
            "previousTradedClose": str(self.previous_traded_close),
            "comparisonReferenceDate": self.comparison_reference_date.isoformat(),
            "comparisonReference": str(self.comparison_reference),
            "sourceAuthority": self.source_authority,
            "sourceReference": self.source_reference,
            "sourceResponseHash": self.source_response_hash,
            "previousTradedCloseSource": self.previous_traded_close_source,
            "previousTradedCloseSourceReference": self.previous_traded_close_source_reference,
            "previousTradedCloseResponseHash": self.previous_traded_close_response_hash,
            "detailSourceReference": self.detail_source_reference,
            "detailResponseHash": self.detail_response_hash,
            "finality": self.finality,
        }


def corporate_action_price_authority_from_mapping(
    payload: Mapping[str, Any],
) -> CorporateActionPriceAuthorityRecord:
    """Validate one official, non-synthetic price-basis authority input."""

    return CorporateActionPriceAuthorityRecord(
        symbol=str(payload.get("symbol") or ""),
        market=str(payload.get("market") or "").upper(),
        action_type=str(payload.get("actionType") or ""),
        effective_from=_parse_date(payload.get("effectiveFrom"), "effective_from"),
        effective_to=_parse_date(payload.get("effectiveTo"), "effective_to"),
        resume_date=_parse_date(payload.get("resumeDate"), "resume_date"),
        previous_traded_close_date=_parse_date(
            payload.get("previousTradedCloseDate"), "previous_traded_close_date"
        ),
        previous_traded_close=_positive_decimal(
            payload.get("previousTradedClose"), "previous_traded_close"
        ),
        comparison_reference_date=_parse_date(
            payload.get("comparisonReferenceDate"), "comparison_reference_date"
        ),
        comparison_reference=_positive_decimal(
            payload.get("comparisonReference"), "comparison_reference"
        ),
        source_authority=str(payload.get("sourceAuthority") or ""),
        source_reference=_parse_url(payload.get("sourceReference"), "source_reference"),
        source_response_hash=_parse_hash(payload.get("sourceResponseHash"), "source_response_hash"),
        previous_traded_close_source=str(payload.get("previousTradedCloseSource") or ""),
        previous_traded_close_source_reference=_parse_url(
            payload.get("previousTradedCloseSourceReference"),
            "previous_traded_close_source_reference",
        ),
        previous_traded_close_response_hash=_parse_hash(
            payload.get("previousTradedCloseResponseHash"),
            "previous_traded_close_response_hash",
        ),
        detail_source_reference=(
            _parse_url(payload.get("detailSourceReference"), "detail_source_reference")
            if payload.get("detailSourceReference") is not None
            else None
        ),
        detail_response_hash=(
            _parse_hash(payload.get("detailResponseHash"), "detail_response_hash")
            if payload.get("detailResponseHash") is not None
            else None
        ),
        finality=str(payload.get("finality") or ""),
    )


def parse_corporate_action_price_authorities(
    payload: Mapping[str, Any],
) -> tuple[CorporateActionPriceAuthorityRecord, ...]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise CorporateActionPriceAuthorityError("PRICE_AUTHORITY_RECORDS_MISSING")
    parsed = tuple(
        corporate_action_price_authority_from_mapping(item)
        for item in records
        if isinstance(item, Mapping)
    )
    if len(parsed) != len(records):
        raise CorporateActionPriceAuthorityError("PRICE_AUTHORITY_RECORD_NOT_OBJECT")
    keys = [(item.symbol, item.market, item.action_type, item.effective_from) for item in parsed]
    if len(keys) != len(set(keys)):
        raise CorporateActionPriceAuthorityError("DUPLICATE_PRICE_AUTHORITY_RECORD")
    return parsed


@lru_cache(maxsize=1)
def load_corporate_action_price_authorities() -> tuple[CorporateActionPriceAuthorityRecord, ...]:
    """Load only the bounded repository copy of official evidence metadata."""

    try:
        payload = json.loads(_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorporateActionPriceAuthorityError("PRICE_AUTHORITY_UNAVAILABLE") from exc
    if not isinstance(payload, Mapping):
        raise CorporateActionPriceAuthorityError("PRICE_AUTHORITY_INVALID")
    return parse_corporate_action_price_authorities(payload)


def corporate_action_price_authorities_for(
    *, symbol: str, market: str, target: date, prior: date
) -> tuple[CorporateActionPriceAuthorityRecord, ...]:
    """Return price authorities whose official interval covers the resume case."""

    return tuple(
        item
        for item in load_corporate_action_price_authorities()
        if item.symbol == symbol
        and item.market == market.upper()
        and item.is_applicable_on(target=target, prior=prior)
    )


__all__ = [
    "CorporateActionPriceAuthorityError",
    "CorporateActionPriceAuthorityRecord",
    "corporate_action_price_authorities_for",
    "corporate_action_price_authority_from_mapping",
    "load_corporate_action_price_authorities",
    "parse_corporate_action_price_authorities",
]
