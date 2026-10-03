"""Price comparator authority; never a price fill or publication-date selector."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

OFFICIAL_SOURCES = {"TPE": "TWSE_OFFICIAL_DAILY", "TWO": "TPEX_OFFICIAL_DAILY"}


def previous_session_date(target: date, closed_dates: Collection[date]) -> date:
    """Use the governed TW_MARKET weekday/closure calendar, not observed prices."""
    candidate = target - timedelta(days=1)
    for _ in range(366):
        if candidate.weekday() < 5 and candidate not in closed_dates:
            return candidate
        candidate -= timedelta(days=1)
    raise ValueError("PREVIOUS_FORMAL_SESSION_NOT_RESOLVED")


def valid_close(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        return False
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False
    return number.is_finite() and number > 0


@dataclass(frozen=True)
class PreviousCloseEvidence:
    instrument_id: str
    market_code: str
    instrument_code: str
    as_of_date: date
    value: Any
    source: str
    authority: str  # PROVIDER_EXPLICIT_PREVIOUS_CLOSE or FORMAL_CANONICAL_CLOSE
    lineage: str
    payload_date: date | None = None
    quality_state: str = "ACCEPTED"

    def rejection_reason(
        self, *, instrument_id: str, market: str, code: str, target: date, prior: date
    ) -> str | None:
        if (self.instrument_id, self.market_code, self.instrument_code) != (
            instrument_id,
            market,
            code,
        ):
            return "PREVIOUS_CLOSE_IDENTITY_MISMATCH"
        if self.as_of_date != prior:
            return "PREVIOUS_CLOSE_DATE_MISMATCH"
        if (
            self.source != OFFICIAL_SOURCES.get(market)
            or not isinstance(self.lineage, str)
            or not self.lineage.strip()
        ):
            return "PREVIOUS_CLOSE_AUTHORITY_INVALID"
        if self.authority == "PROVIDER_EXPLICIT_PREVIOUS_CLOSE":
            if self.payload_date != target:
                return "PREVIOUS_CLOSE_PAYLOAD_DATE_MISMATCH"
        elif self.authority == "FORMAL_CANONICAL_CLOSE":
            if self.quality_state != "ACCEPTED":
                return "PREVIOUS_CLOSE_AUTHORITY_INVALID"
        else:
            return "PREVIOUS_CLOSE_AUTHORITY_INVALID"
        if not valid_close(self.value):
            return "PREVIOUS_CLOSE_INVALID"
        return None

    def price_free_metadata(self) -> dict[str, Any]:
        return {
            "instrumentId": self.instrument_id,
            "marketCode": self.market_code,
            "instrumentCode": self.instrument_code,
            "asOfDate": self.as_of_date.isoformat(),
            "source": self.source,
            "authority": self.authority,
            "lineage": self.lineage,
            "payloadDate": self.payload_date.isoformat() if self.payload_date else None,
            "qualityState": self.quality_state,
        }


@dataclass(frozen=True)
class G2PriceEvidence:
    instrument_id: str
    market_code: str
    instrument_code: str
    trading_date: date
    close: Any
    response_hash: str
    provider_previous: PreviousCloseEvidence | None = None
    formal_previous: PreviousCloseEvidence | None = None

    def previous(self) -> PreviousCloseEvidence | None:
        # An explicit invalid value is rejected, not hidden by another source.
        return (
            self.provider_previous if self.provider_previous is not None else self.formal_previous
        )
