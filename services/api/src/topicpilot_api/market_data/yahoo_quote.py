"""Yahoo chart quote adapter retained from the validated V1 fallback path.

This adapter is intentionally quote-only.  It does not become a historical
daily provider and it does not replace the official TWSE/TPEx daily adapters.
The V2 router can use it as the primary intraday quote source and fail over to
the Taishin intraday adapter.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Final
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from topicpilot_api.live.contracts import IntradayBar, IntradayFetchResult, LiveProviderError

TAIPEI: Final = ZoneInfo("Asia/Taipei")
YAHOO_QUOTE_SOURCE_CODE: Final = "YAHOO_QUOTE_INTRADAY"
YAHOO_QUOTE_ADAPTER_VERSION: Final = "yahoo-quote-intraday.v1"
YAHOO_CHART_BASE_URL: Final = "https://query1.finance.yahoo.com/v8/finance/chart"
MARKET_SUFFIX: Final = {"TPE": ".TW", "TWO": ".TWO"}

Transport = Callable[[str, float], bytes]


def _read_url(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _decimal(value: Any, field: str) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise LiveProviderError(
            "INVALID_NUMBER", f"Yahoo {field} is invalid", retryable=False
        ) from exc
    if not number.is_finite():
        raise LiveProviderError("INVALID_NUMBER", f"Yahoo {field} is not finite", retryable=False)
    return number


def _timestamp(value: Any) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise LiveProviderError(
            "INVALID_TIMESTAMP", "Yahoo quote timestamp is missing", retryable=False
        )
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise LiveProviderError(
            "INVALID_TIMESTAMP", "Yahoo quote timestamp is invalid", retryable=False
        ) from exc


class YahooQuoteProvider:
    """Normalize the V1 Yahoo quote fallback into the V2 intraday contract."""

    source_code = YAHOO_QUOTE_SOURCE_CODE
    adapter_version = YAHOO_QUOTE_ADAPTER_VERSION

    def __init__(
        self,
        *,
        base_url: str = YAHOO_CHART_BASE_URL,
        timeout: float = 15.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not base_url.strip() or timeout <= 0:
            raise ValueError("Yahoo quote configuration is invalid")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017

    def connect(self) -> None:
        """HTTP has no market session to hold; the worker lifecycle is a no-op."""

    def disconnect(self) -> None:
        """HTTP has no market session to close."""

    def health_check(self) -> bool:
        return True

    def fetch_intraday(
        self, instrument_code: str, market_code: str, *, session_date: date
    ) -> IntradayFetchResult:
        suffix = MARKET_SUFFIX.get(market_code)
        if suffix is None:
            raise LiveProviderError("UNSUPPORTED_MARKET", market_code, retryable=False)
        source_symbol = f"{instrument_code}{suffix}"
        query = urlencode({"range": "1d", "interval": "1m"})
        url = f"{self.base_url}/{quote(source_symbol, safe='')}?{query}"
        try:
            payload = json.loads(self.transport(url, self.timeout).decode("utf-8"))
        except Exception as exc:
            raise LiveProviderError("YAHOO_REQUEST_FAILED", "Yahoo quote request failed") from exc
        if not isinstance(payload, Mapping):
            raise LiveProviderError(
                "YAHOO_INVALID_PAYLOAD", "Yahoo response is not an object", retryable=False
            )
        chart = payload.get("chart")
        results = chart.get("result") if isinstance(chart, Mapping) else None
        if not isinstance(results, list) or not results or not isinstance(results[0], Mapping):
            raise LiveProviderError("YAHOO_EMPTY_RESULT", "Yahoo chart result is empty")
        result = results[0]
        meta = result.get("meta")
        if not isinstance(meta, Mapping):
            raise LiveProviderError(
                "YAHOO_INVALID_PAYLOAD", "Yahoo chart meta is missing", retryable=False
            )
        close = _decimal(meta.get("regularMarketPrice"), "regularMarketPrice")
        if close is None:
            raise LiveProviderError("YAHOO_EMPTY_PRICE", "Yahoo regularMarketPrice is empty")
        observed_value = meta.get("regularMarketTime")
        if not observed_value:
            timestamps = result.get("timestamp")
            if isinstance(timestamps, list) and timestamps:
                observed_value = timestamps[-1]
        observed_at = _timestamp(observed_value)
        retrieved_at = self.clock()
        if retrieved_at.tzinfo is None:
            raise LiveProviderError(
                "INVALID_RETRIEVAL_TIME", "retrieval time must be timezone-aware", retryable=False
            )
        local_date = observed_at.astimezone(TAIPEI).date()
        if local_date != session_date:
            raise LiveProviderError("YAHOO_STALE_QUOTE", f"quote date is {local_date.isoformat()}")
        bar = IntradayBar(
            instrument_code=instrument_code,
            market_code=market_code,
            observed_at=observed_at,
            open=_decimal(meta.get("regularMarketOpen"), "regularMarketOpen"),
            high=_decimal(meta.get("regularMarketDayHigh"), "regularMarketDayHigh"),
            low=_decimal(meta.get("regularMarketDayLow"), "regularMarketDayLow"),
            close=close,
            volume=_decimal(meta.get("regularMarketVolume"), "regularMarketVolume"),
            interval="quote",
            source_payload={
                "symbol": source_symbol,
                "close": str(close),
                "open": str(meta.get("regularMarketOpen"))
                if meta.get("regularMarketOpen") is not None
                else None,
                "high": str(meta.get("regularMarketDayHigh"))
                if meta.get("regularMarketDayHigh") is not None
                else None,
                "low": str(meta.get("regularMarketDayLow"))
                if meta.get("regularMarketDayLow") is not None
                else None,
                "volume": str(meta.get("regularMarketVolume"))
                if meta.get("regularMarketVolume") is not None
                else None,
                "interval": "quote",
                "provider_semantics": "V1_YAHOO_QUOTE_FALLBACK",
            },
        )
        return IntradayFetchResult(
            instrument_code=instrument_code,
            market_code=market_code,
            source_symbol=source_symbol,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            retrieved_at=retrieved_at,
            bars=(bar,),
        )


__all__ = ["YAHOO_QUOTE_ADAPTER_VERSION", "YAHOO_QUOTE_SOURCE_CODE", "YahooQuoteProvider"]
