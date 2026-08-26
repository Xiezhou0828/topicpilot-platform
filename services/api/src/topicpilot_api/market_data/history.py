"""Provider-neutral historical daily-price capability contracts.

The provider adapter is deliberately separate from persistence and FastAPI.
It can prove whether a small historical sample is obtainable without making a
request handler depend on a live provider.  Missing observations remain
``None`` and are counted explicitly; they are never converted to zero.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Final, Protocol
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TAIPEI: Final = ZoneInfo("Asia/Taipei")
DEFAULT_CHART_BASE_URL: Final = "https://query1.finance.yahoo.com/v8/finance/chart"
DEFAULT_INTERVAL: Final = "1d"
DEFAULT_RANGE: Final = "1mo"
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MARKET_SUFFIX: Final = {"TPE": ".TW", "TWO": ".TWO"}
_MISSING: Final = object()

# These are the only daily instrument states that the formal coverage gate
# understands.  ``OPEN`` remains accepted by the older reference fixtures and
# is intentionally not used as the new daily status vocabulary.
DAILY_TRADING_STATUS_CODES: Final = frozenset(
    {
        "AVAILABLE",
        "SUSPENDED",
        "NO_TRADE",
        "EXCHANGE_CONFIRMED_NO_DATA",
        "DELISTED",
        "TERMINATED",
        "UNKNOWN",
        "OPEN",
    }
)
COVERED_NO_TRADE_STATUS_CODES: Final = frozenset(
    {"SUSPENDED", "NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA", "DELISTED", "TERMINATED"}
)


class HistoricalProviderError(ValueError):
    """A bounded, machine-readable historical-provider failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class HistoricalProvider(Protocol):
    """Source-neutral contract used by the capability probe."""

    source_code: str
    adapter_version: str

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult: ...


@dataclass(frozen=True)
class HistoricalBar:
    """One normalized daily point; missing fields remain ``None``."""

    trading_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal | None


@dataclass(frozen=True)
class HistoricalFetchResult:
    """Validated provider output without retaining the raw response payload."""

    instrument_code: str
    market_code: str
    source_symbol: str
    source_code: str
    adapter_version: str
    retrieved_at: datetime
    bars: tuple[HistoricalBar, ...]
    raw_point_count: int
    instrument_status: str = "AVAILABLE"
    status_reason: str | None = None
    status_explicit: bool = False

    @property
    def available_close_count(self) -> int:
        return sum(bar.close is not None for bar in self.bars)

    @property
    def missing_close_count(self) -> int:
        return sum(bar.close is None for bar in self.bars)

    @property
    def date_from(self) -> date | None:
        return self.bars[0].trading_date if self.bars else None

    @property
    def date_to(self) -> date | None:
        return self.bars[-1].trading_date if self.bars else None

    @property
    def has_priced_observation(self) -> bool:
        return any(bar.close is not None for bar in self.bars)

    @property
    def covered_no_trade(self) -> bool:
        return (
            not self.has_priced_observation
            and self.instrument_status in COVERED_NO_TRADE_STATUS_CODES
        )


@dataclass(frozen=True)
class HistoryAvailability:
    """Sanitized, JSON-safe capability evidence for one requested symbol."""

    instrument_code: str
    market_code: str
    source_code: str
    adapter_version: str
    status: str
    requested_minimum_points: int
    raw_point_count: int
    available_close_count: int
    missing_close_count: int
    date_from: date | None
    date_to: date | None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrumentCode": self.instrument_code,
            "marketCode": self.market_code,
            "sourceCode": self.source_code,
            "adapterVersion": self.adapter_version,
            "status": self.status,
            "requestedMinimumPoints": self.requested_minimum_points,
            "rawPointCount": self.raw_point_count,
            "availableCloseCount": self.available_close_count,
            "missingCloseCount": self.missing_close_count,
            "dateFrom": self.date_from.isoformat() if self.date_from else None,
            "dateTo": self.date_to.isoformat() if self.date_to else None,
            "errorCode": self.error_code,
        }


def _validate_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise HistoricalProviderError("INVALID_IDENTITY", f"{label} is invalid")
    return value


def _decimal(value: object, label: str) -> Decimal | None:
    if value is None or value is _MISSING or value == "":
        return None
    if isinstance(value, bool):
        raise HistoricalProviderError("INVALID_NUMBER", f"{label} must be numeric or null")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalProviderError("INVALID_NUMBER", f"{label} must be numeric or null") from exc
    if not number.is_finite():
        raise HistoricalProviderError("INVALID_NUMBER", f"{label} must be finite")
    return number


def _timestamp_date(value: object) -> date:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HistoricalProviderError("INVALID_TIMESTAMP", "timestamp must be numeric")
    if not math.isfinite(float(value)):
        raise HistoricalProviderError("INVALID_TIMESTAMP", "timestamp must be finite")
    return datetime.fromtimestamp(float(value), tz=TAIPEI).date()


def _sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key, [])
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise HistoricalProviderError("INVALID_PAYLOAD", f"{key} must be an array")
    return value


def _at(values: Sequence[Any], index: int) -> object:
    return values[index] if index < len(values) else _MISSING


def _validate_bar(bar: HistoricalBar) -> None:
    numbers = (bar.open, bar.high, bar.low, bar.close)
    if any(value is None for value in numbers):
        return
    assert all(value is not None for value in numbers)
    if bar.low > min(numbers) or bar.high < max(numbers):
        raise HistoricalProviderError(
            "INVALID_OHLC", f"OHLC relationship is invalid on {bar.trading_date.isoformat()}"
        )
    if bar.low < 0 or bar.high < 0:
        raise HistoricalProviderError(
            "INVALID_OHLC", f"OHLC values cannot be negative on {bar.trading_date.isoformat()}"
        )
    if bar.volume is not None and bar.volume < 0:
        raise HistoricalProviderError(
            "INVALID_VOLUME", f"volume cannot be negative on {bar.trading_date.isoformat()}"
        )


def _parse_result(
    payload: Mapping[str, Any],
    *,
    instrument_code: str,
    market_code: str,
    source_symbol: str,
    source_code: str,
    adapter_version: str,
    retrieved_at: datetime,
) -> HistoricalFetchResult:
    chart = payload.get("chart")
    if not isinstance(chart, Mapping):
        raise HistoricalProviderError("INVALID_PAYLOAD", "chart must be an object")
    results = chart.get("result")
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)) or not results:
        raise HistoricalProviderError("EMPTY_RESULT", "chart.result is empty")
    first = results[0]
    if not isinstance(first, Mapping):
        raise HistoricalProviderError("INVALID_PAYLOAD", "chart.result[0] must be an object")
    timestamps = _sequence(first, "timestamp")
    indicators = first.get("indicators")
    if not isinstance(indicators, Mapping):
        raise HistoricalProviderError("INVALID_PAYLOAD", "indicators must be an object")
    quotes = indicators.get("quote")
    if not isinstance(quotes, Sequence) or isinstance(quotes, (str, bytes)) or not quotes:
        raise HistoricalProviderError("INVALID_PAYLOAD", "indicators.quote is empty")
    quote = quotes[0]
    if not isinstance(quote, Mapping):
        raise HistoricalProviderError("INVALID_PAYLOAD", "indicators.quote[0] must be an object")

    bars: list[HistoricalBar] = []
    seen_dates: set[date] = set()
    for index, timestamp in enumerate(timestamps):
        trading_date = _timestamp_date(timestamp)
        if trading_date in seen_dates:
            raise HistoricalProviderError("DUPLICATE_DATE", trading_date.isoformat())
        seen_dates.add(trading_date)
        bar = HistoricalBar(
            trading_date=trading_date,
            open=_decimal(_at(_sequence(quote, "open"), index), "open"),
            high=_decimal(_at(_sequence(quote, "high"), index), "high"),
            low=_decimal(_at(_sequence(quote, "low"), index), "low"),
            close=_decimal(_at(_sequence(quote, "close"), index), "close"),
            volume=_decimal(_at(_sequence(quote, "volume"), index), "volume"),
        )
        _validate_bar(bar)
        bars.append(bar)

    bars.sort(key=lambda bar: bar.trading_date)
    inferred_status = "AVAILABLE" if all(bar.close is not None for bar in bars) else "UNKNOWN"
    return HistoricalFetchResult(
        instrument_code=instrument_code,
        market_code=market_code,
        source_symbol=source_symbol,
        source_code=source_code,
        adapter_version=adapter_version,
        retrieved_at=retrieved_at,
        bars=tuple(bars),
        raw_point_count=len(timestamps),
        instrument_status=inferred_status,
        status_explicit=False,
    )


Transport = Callable[[str, float], bytes]


def _read_url(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


class YahooChartHistoricalProvider:
    """Read-only daily history adapter for the existing chart API path.

    This adapter is a capability bridge, not a production-source approval. Its
    source and policy metadata must be supplied to any later persistence
    workflow and it is never called from a FastAPI request handler.
    """

    source_code = "YAHOO_CHART_DAILY"
    adapter_version = "yahoo-chart-daily.v1"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_CHART_BASE_URL,
        period: str = DEFAULT_RANGE,
        interval: str = DEFAULT_INTERVAL,
        timeout: float = 15.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must be non-empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.period = period
        self.interval = interval
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(TAIPEI))

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        instrument_code = _validate_identifier(instrument_code, "instrument_code")
        market_code = _validate_identifier(market_code, "market_code")
        suffix = _MARKET_SUFFIX.get(market_code)
        if suffix is None:
            raise HistoricalProviderError("UNSUPPORTED_MARKET", market_code)
        source_symbol = f"{instrument_code}{suffix}"
        query = urlencode({"range": self.period, "interval": self.interval})
        url = f"{self.base_url}/{quote(source_symbol, safe='')}?{query}"
        try:
            raw = self.transport(url, self.timeout)
            payload = json.loads(raw.decode("utf-8"))
        except HistoricalProviderError:
            raise
        except Exception as exc:
            raise HistoricalProviderError(
                "PROVIDER_REQUEST_FAILED", "historical request failed"
            ) from exc
        if not isinstance(payload, Mapping):
            raise HistoricalProviderError("INVALID_PAYLOAD", "provider response must be an object")
        return _parse_result(
            payload,
            instrument_code=instrument_code,
            market_code=market_code,
            source_symbol=source_symbol,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            retrieved_at=self.clock(),
        )


def probe_history_availability(
    provider: HistoricalProvider,
    instruments: Iterable[tuple[str, str]],
    *,
    minimum_points: int = 14,
) -> tuple[HistoryAvailability, ...]:
    """Probe a bounded sample and retain failure status per instrument."""

    if isinstance(minimum_points, bool) or minimum_points < 1:
        raise ValueError("minimum_points must be a positive integer")
    results: list[HistoryAvailability] = []
    for instrument_code, market_code in instruments:
        try:
            fetched = provider.fetch_daily(instrument_code, market_code)
            status = (
                "AVAILABLE"
                if fetched.available_close_count >= minimum_points
                else "INSUFFICIENT_HISTORY"
            )
            results.append(
                HistoryAvailability(
                    instrument_code=fetched.instrument_code,
                    market_code=fetched.market_code,
                    source_code=fetched.source_code,
                    adapter_version=fetched.adapter_version,
                    status=status,
                    requested_minimum_points=minimum_points,
                    raw_point_count=fetched.raw_point_count,
                    available_close_count=fetched.available_close_count,
                    missing_close_count=fetched.missing_close_count,
                    date_from=fetched.date_from,
                    date_to=fetched.date_to,
                )
            )
        except HistoricalProviderError as exc:
            results.append(
                HistoryAvailability(
                    instrument_code=instrument_code,
                    market_code=market_code,
                    source_code=provider.source_code,
                    adapter_version=provider.adapter_version,
                    status="PROVIDER_ERROR",
                    requested_minimum_points=minimum_points,
                    raw_point_count=0,
                    available_close_count=0,
                    missing_close_count=0,
                    date_from=None,
                    date_to=None,
                    error_code=exc.code,
                )
            )
    return tuple(results)


__all__ = [
    "COVERED_NO_TRADE_STATUS_CODES",
    "DAILY_TRADING_STATUS_CODES",
    "HistoricalBar",
    "HistoricalFetchResult",
    "HistoricalProvider",
    "HistoricalProviderError",
    "HistoryAvailability",
    "YahooChartHistoricalProvider",
    "probe_history_availability",
]
