"""Official corporate-action authority for date-effective trading status.

The exchange/MOPS notice is an authority event, not a price observation.  This
adapter normalizes the small, explicit source contract into the shared trading
status record consumed by the resolver.  It intentionally has no database or
network side effects; a deployment can replace the checked-in authority
snapshot with an approved ingestion result without changing resolver logic.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from topicpilot_api.trading_status_authority import (
    AuthorityClass,
    TradingStatusAuthorityError,
    TradingStatusAuthorityRecord,
)

TWSE_OFFICIAL_CORPORATE_ACTION = "TWSE_OFFICIAL_CORPORATE_ACTION"
TPEX_OFFICIAL_CORPORATE_ACTION = "TPEX_OFFICIAL_CORPORATE_ACTION"
OFFICIAL_CORPORATE_ACTION_SOURCES = frozenset(
    {TWSE_OFFICIAL_CORPORATE_ACTION, TPEX_OFFICIAL_CORPORATE_ACTION}
)
CAPITAL_REDUCTION_EVENT = "CAPITAL_REDUCTION"
SHARE_CONVERSION_EVENT = "MERGER_SHARE_CONVERSION_DEMERGER"
SUPPORTED_CORPORATE_ACTION_EVENTS = frozenset(
    {CAPITAL_REDUCTION_EVENT, SHARE_CONVERSION_EVENT}
)
CORPORATE_ACTION_REASON_CODES = {
    CAPITAL_REDUCTION_EVENT: "CAPITAL_REDUCTION_TRADING_SUSPENSION",
    SHARE_CONVERSION_EVENT: "SHARE_CONVERSION_TRADING_SUSPENSION",
}
AUTHORITY_SNAPSHOT = Path(__file__).with_name("corporate_action_authority.json")


class CorporateActionAuthorityError(TradingStatusAuthorityError):
    """Raised when an official corporate-action payload is unsafe to use."""


def _required_text(payload: Mapping[str, Any], *names: str) -> str:
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise CorporateActionAuthorityError(f"MISSING_CORPORATE_ACTION_FIELD:{names[0]}")


def _date(payload: Mapping[str, Any], *names: str) -> date:
    raw = _required_text(payload, *names)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_DATE:{names[0]}") from exc


def _optional_date(payload: Mapping[str, Any], *names: str) -> date | None:
    value = next((payload.get(name) for name in names if payload.get(name) is not None), None)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_DATE:{names[0]}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_DATE:{names[0]}") from exc


def _optional_datetime(payload: Mapping[str, Any], *names: str) -> datetime | None:
    value = next((payload.get(name) for name in names if payload.get(name) is not None), None)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CorporateActionAuthorityError(f"INVALID_CORPORATE_ACTION_TIMESTAMP:{names[0]}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CorporateActionAuthorityError(
            f"INVALID_CORPORATE_ACTION_TIMESTAMP:{names[0]}"
        ) from exc
    if parsed.tzinfo is None:
        raise CorporateActionAuthorityError(f"NAIVE_CORPORATE_ACTION_TIMESTAMP:{names[0]}")
    return parsed


@dataclass(frozen=True)
class CorporateActionAuthorityRecord:
    """One official, effective-dated event for an existing instrument identity."""

    market_code: str
    instrument_code: str
    event_type: str
    effective_from: date
    effective_to: date
    resume_date: date
    source: str
    source_reference: str
    source_url: str
    observed_at: datetime | None = None
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        market = self.market_code.upper()
        if market not in {"TPE", "TWO"}:
            raise CorporateActionAuthorityError("UNSUPPORTED_CORPORATE_ACTION_MARKET")
        if not self.instrument_code.strip():
            raise CorporateActionAuthorityError("MISSING_CORPORATE_ACTION_INSTRUMENT")
        if self.event_type not in SUPPORTED_CORPORATE_ACTION_EVENTS:
            raise CorporateActionAuthorityError("UNSUPPORTED_CORPORATE_ACTION_EVENT")
        if self.source not in OFFICIAL_CORPORATE_ACTION_SOURCES:
            raise CorporateActionAuthorityError("UNSUPPORTED_CORPORATE_ACTION_SOURCE")
        if not self.source_reference.strip() or not self.source_url.strip():
            raise CorporateActionAuthorityError("MISSING_CORPORATE_ACTION_PROVENANCE")
        if self.effective_to < self.effective_from:
            raise CorporateActionAuthorityError("INVALID_CORPORATE_ACTION_RANGE")
        if self.resume_date <= self.effective_to:
            raise CorporateActionAuthorityError("INVALID_CORPORATE_ACTION_RESUME_DATE")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CorporateActionAuthorityRecord:
        source = _required_text(payload, "source", "sourceCode")
        return cls(
            market_code=_required_text(payload, "market_code", "marketCode").upper(),
            instrument_code=_required_text(payload, "instrument_code", "instrumentCode"),
            event_type=_required_text(payload, "event_type", "eventType").upper(),
            effective_from=_date(payload, "effective_from", "effectiveFrom"),
            effective_to=_date(payload, "effective_to", "effectiveTo"),
            resume_date=_date(payload, "resume_date", "resumeDate"),
            source=source,
            source_reference=_required_text(
                payload, "source_reference", "sourceReference", "evidenceId"
            ),
            source_url=_required_text(payload, "source_url", "sourceUrl"),
            observed_at=_optional_datetime(payload, "observed_at", "observedAt"),
            published_at=_optional_datetime(payload, "published_at", "publishedAt"),
        )

    def to_trading_status_record(self) -> TradingStatusAuthorityRecord:
        return TradingStatusAuthorityRecord(
            status_code="SUSPENDED",
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            resume_date=self.resume_date,
            source=self.source,
            source_reference=self.source_reference,
            reason_code=CORPORATE_ACTION_REASON_CODES[self.event_type],
            observed_at=self.observed_at,
            published_at=self.published_at,
            authority_class=AuthorityClass.OFFICIAL_CORPORATE_ACTION.value,
        )


def parse_official_corporate_action_payload(
    payload: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> tuple[CorporateActionAuthorityRecord, ...]:
    """Parse an explicit official payload without fuzzy text inference."""

    rows: Any = payload
    if isinstance(payload, Mapping):
        rows = payload.get("events")
    if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes, Mapping)):
        raise CorporateActionAuthorityError("CORPORATE_ACTION_PAYLOAD_NOT_AN_EVENT_LIST")
    result = tuple(CorporateActionAuthorityRecord.from_payload(row) for row in rows)
    identities = {
        (item.market_code, item.instrument_code, item.source_reference) for item in result
    }
    if len(identities) != len(result):
        raise CorporateActionAuthorityError("DUPLICATE_CORPORATE_ACTION_AUTHORITY")
    return result


def load_official_corporate_action_snapshot(
    path: Path | None = None,
) -> tuple[CorporateActionAuthorityRecord, ...]:
    """Load the approved, sanitized source snapshot shipped with the worker."""

    source_path = path or AUTHORITY_SNAPSHOT
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorporateActionAuthorityError("CORPORATE_ACTION_SNAPSHOT_UNAVAILABLE") from exc
    return parse_official_corporate_action_payload(payload)


def authority_by_identity(
    records: Iterable[CorporateActionAuthorityRecord | TradingStatusAuthorityRecord],
) -> dict[tuple[str, str], tuple[TradingStatusAuthorityRecord, ...]]:
    """Group normalized authority by market-aware identity for reconciliation."""

    grouped: dict[tuple[str, str], list[TradingStatusAuthorityRecord]] = {}
    for item in records:
        if isinstance(item, CorporateActionAuthorityRecord):
            normalized = item.to_trading_status_record()
            identity = (item.market_code, item.instrument_code)
        else:
            normalized = item
            identity = tuple(
                part.strip()
                for part in item.source_reference.split(":", 2)[:2]
            )
            if len(identity) != 2:
                continue
        grouped.setdefault(identity, []).append(normalized)
    return {key: tuple(value) for key, value in grouped.items()}


__all__ = [
    "AUTHORITY_SNAPSHOT",
    "CAPITAL_REDUCTION_EVENT",
    "CORPORATE_ACTION_REASON_CODES",
    "OFFICIAL_CORPORATE_ACTION_SOURCES",
    "SHARE_CONVERSION_EVENT",
    "TPEX_OFFICIAL_CORPORATE_ACTION",
    "TWSE_OFFICIAL_CORPORATE_ACTION",
    "CorporateActionAuthorityError",
    "CorporateActionAuthorityRecord",
    "authority_by_identity",
    "load_official_corporate_action_snapshot",
    "parse_official_corporate_action_payload",
]
