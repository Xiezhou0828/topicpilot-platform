"""Provider-neutral contracts for live polling and operational evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID


class LiveProviderError(RuntimeError):
    """A sanitized live-provider failure with retry semantics."""

    def __init__(self, code: str, message: str, *, retryable: bool = True):
        self.code = code
        self.retryable = retryable
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class IntradayBar:
    instrument_code: str
    market_code: str
    observed_at: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal | None
    interval: str
    source_payload: Mapping[str, Any]

    @property
    def last(self) -> Decimal | None:
        return self.close


@dataclass(frozen=True)
class IntradayFetchResult:
    instrument_code: str
    market_code: str
    source_symbol: str
    source_code: str
    adapter_version: str
    retrieved_at: datetime
    bars: tuple[IntradayBar, ...]

    @property
    def latest(self) -> IntradayBar | None:
        return self.bars[-1] if self.bars else None


class IntradayProvider(Protocol):
    source_code: str
    adapter_version: str

    def fetch_intraday(
        self, instrument_code: str, market_code: str, *, session_date: date
    ) -> IntradayFetchResult: ...


@dataclass(frozen=True)
class TrackingInstrument:
    instrument_id: UUID
    instrument_code: str
    market_code: str
    update_mode: str
    moving_average_state: str
    latest_close: Decimal | None
    moving_average: Decimal | None


@dataclass(frozen=True)
class CollectorRunResult:
    run_id: UUID
    run_type: str
    status: str
    requested_count: int
    success_count: int
    failure_count: int
    retry_count: int
    latency_ms: int | None
    freshness_state: str
    provider_status: str
    failure_codes: tuple[str, ...] = ()


__all__ = [
    "CollectorRunResult",
    "IntradayBar",
    "IntradayFetchResult",
    "IntradayProvider",
    "LiveProviderError",
    "TrackingInstrument",
]
