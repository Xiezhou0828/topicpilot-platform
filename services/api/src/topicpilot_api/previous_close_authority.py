"""Price comparator authority; never a price fill or publication-date selector."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from topicpilot_api.corporate_action_authority import (
    CorporateActionAuthorityRecord,
    load_corporate_action_authorities,
)

OFFICIAL_SOURCES = {"TPE": "TWSE_OFFICIAL_DAILY", "TWO": "TPEX_OFFICIAL_DAILY"}


class ComparatorStatus(StrEnum):
    """Status of the formal daily comparison reference."""

    READY = "READY"
    ACCOUNTED_UNAVAILABLE = "ACCOUNTED_UNAVAILABLE"
    ERROR = "ERROR"


class ComparatorType(StrEnum):
    """Governed semantic types; none of these values is a price fill."""

    PREVIOUS_FORMAL_CLOSE = "PREVIOUS_FORMAL_CLOSE"
    LAST_VALID_FORMAL_CLOSE = "LAST_VALID_FORMAL_CLOSE"
    EX_DIVIDEND_REFERENCE = "EX_DIVIDEND_REFERENCE"
    EX_RIGHT_REFERENCE = "EX_RIGHT_REFERENCE"
    EX_RIGHT_DIVIDEND_REFERENCE = "EX_RIGHT_DIVIDEND_REFERENCE"
    SPLIT_ADJUSTED_REFERENCE = "SPLIT_ADJUSTED_REFERENCE"
    CAPITAL_REDUCTION_REFERENCE = "CAPITAL_REDUCTION_REFERENCE"


AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE = (
    "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE"
)

_COMPARATOR_TYPE_BY_ACTION = {
    "CAPITAL_REDUCTION_SHARE_EXCHANGE": ComparatorType.CAPITAL_REDUCTION_REFERENCE,
    "EX_DIVIDEND": ComparatorType.EX_DIVIDEND_REFERENCE,
    "EX_RIGHT": ComparatorType.EX_RIGHT_REFERENCE,
    "EX_RIGHT_DIVIDEND": ComparatorType.EX_RIGHT_DIVIDEND_REFERENCE,
    "STOCK_SPLIT": ComparatorType.SPLIT_ADJUSTED_REFERENCE,
}


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
class ComparatorResolution:
    """Price-free comparator decision with authority lineage."""

    status: ComparatorStatus
    comparator_type: ComparatorType | None
    reason_code: str | None = None
    authority_source: str | None = None
    source_reference: str | None = None
    authority_action_type: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    resume_date: date | None = None

    @property
    def ready(self) -> bool:
        return self.status == ComparatorStatus.READY

    @property
    def accounted_unavailable(self) -> bool:
        return self.status == ComparatorStatus.ACCOUNTED_UNAVAILABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "comparatorType": (
                self.comparator_type.value if self.comparator_type is not None else None
            ),
            "reasonCode": self.reason_code,
            "authoritySource": self.authority_source,
            "sourceReference": self.source_reference,
            "authorityActionType": self.authority_action_type,
            "effectiveFrom": self.effective_from.isoformat() if self.effective_from else None,
            "effectiveTo": self.effective_to.isoformat() if self.effective_to else None,
            "resumeDate": self.resume_date.isoformat() if self.resume_date else None,
        }


def _resume_comparator_authority(
    *,
    symbol: str,
    market: str,
    target: date,
    prior: date,
    authorities: tuple[CorporateActionAuthorityRecord, ...],
) -> ComparatorResolution:
    candidates = tuple(
        record
        for record in authorities
        if (
            record.symbol == symbol
            and record.market == market.upper()
            and record.resume_date == target
            and record.effective_to < target
            and record.is_effective_on(prior)
            and not record.expected_close
        )
    )
    if not candidates:
        return ComparatorResolution(
            ComparatorStatus.ERROR,
            None,
            "MISSING_PREVIOUS_FORMAL_CLOSE",
        )
    if len(candidates) != 1:
        return ComparatorResolution(
            ComparatorStatus.ERROR,
            None,
            "CORPORATE_ACTION_COMPARATOR_AUTHORITY_CONFLICT",
        )
    record = candidates[0]
    comparator_type = _COMPARATOR_TYPE_BY_ACTION.get(record.action_type)
    if comparator_type is None:
        return ComparatorResolution(
            ComparatorStatus.ERROR,
            None,
            "CORPORATE_ACTION_COMPARATOR_TYPE_UNSUPPORTED",
            record.source_authority,
            record.source_reference,
            record.action_type,
            record.effective_from,
            record.effective_to,
            record.resume_date,
        )
    return ComparatorResolution(
        ComparatorStatus.ACCOUNTED_UNAVAILABLE,
        comparator_type,
        AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
        record.source_authority,
        record.source_reference,
        record.action_type,
        record.effective_from,
        record.effective_to,
        record.resume_date,
    )


def resolve_missing_daily_comparator(
    *,
    symbol: str,
    market: str,
    target: date,
    prior: date,
    authorities: tuple[CorporateActionAuthorityRecord, ...] | None = None,
) -> ComparatorResolution:
    """Resolve a missing exact-prior comparator without manufacturing a price."""

    return _resume_comparator_authority(
        symbol=symbol,
        market=market,
        target=target,
        prior=prior,
        authorities=(
            authorities
            if authorities is not None
            else load_corporate_action_authorities()
        ),
    )


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
