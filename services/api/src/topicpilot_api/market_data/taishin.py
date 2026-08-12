"""Optional Taishin historical daily-bar provider.

The vendor runtime is private and is intentionally not imported at module
import time.  Production callers must provide the vendor package and
credentials through the execution environment.  Tests can inject a small
client implementing :class:`TaishinHistoryClient` without installing the
vendor wheel.
"""

from __future__ import annotations

import os
import re
import threading
from collections.abc import Callable, Iterable, Mapping
from contextlib import suppress
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from topicpilot_api.live.contracts import IntradayBar, IntradayFetchResult, LiveProviderError

from .history import HistoricalBar, HistoricalFetchResult, HistoricalProviderError

TAISHIN_USER_ENV = "TOPICPILOT_TA_API_USER"
TAISHIN_PASSWORD_ENV = "TOPICPILOT_TA_API_PASSWORD"
TAISHIN_START_DATE_ENV = "TOPICPILOT_TA_API_HISTORY_START"
TAISHIN_TIMEOUT_ENV = "TOPICPILOT_TA_API_TIMEOUT"
TAISHIN_SOURCE_CODE = "TAISHIN_TECH_ANALYSIS"
TAISHIN_ADAPTER_VERSION = "taishin-tech-analysis.v1"
TAISHIN_INTRADAY_SOURCE_CODE = "TAISHIN_TECH_ANALYSIS_INTRADAY"
TAISHIN_INTRADAY_ADAPTER_VERSION = "taishin-tech-analysis-intraday.v1"
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TAIPEI = ZoneInfo("Asia/Taipei")


class TaishinHistoryClient(Protocol):
    """Small private-runtime boundary used by the provider adapter."""

    def fetch_daily_bars(self, instrument_code: str, market_code: str) -> Iterable[Any]: ...


class TaishinIntradayClient(Protocol):
    """Private-runtime boundary for intraday K-bar polling."""

    def fetch_intraday_bars(
        self, instrument_code: str, market_code: str, interval: str, session_date: date
    ) -> Iterable[Any]: ...


def _field(row: Any, *names: str) -> Any:
    if isinstance(row, Mapping):
        for name in names:
            if name in row:
                return row[name]
        return None
    for name in names:
        value = getattr(row, name, None)
        if value is not None:
            return value
    return None


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, bool) or value is None:
        raise HistoricalProviderError("INVALID_DATE", "Taishin bar date is missing")
    text = str(value).strip()
    for candidate in (text, text[:8]):
        try:
            if len(candidate) == 8 and candidate.isdigit():
                return datetime.strptime(candidate, "%Y%m%d").date()
            return date.fromisoformat(candidate)
        except ValueError:
            continue
    raise HistoricalProviderError("INVALID_DATE", "Taishin bar date is invalid")


def _decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise HistoricalProviderError("INVALID_NUMBER", f"{field_name} must be numeric or null")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalProviderError(
            "INVALID_NUMBER", f"{field_name} must be numeric or null"
        ) from exc
    if not result.is_finite():
        raise HistoricalProviderError("INVALID_NUMBER", f"{field_name} must be finite")
    return result


def _validate_bar(bar: HistoricalBar) -> None:
    numbers = (bar.open, bar.high, bar.low, bar.close)
    if any(value is None for value in numbers):
        return
    assert all(value is not None for value in numbers)
    if bar.low > min(numbers) or bar.high < max(numbers):
        raise HistoricalProviderError(
            "INVALID_OHLC", f"OHLC relationship is invalid on {bar.trading_date.isoformat()}"
        )
    if min(numbers) < 0:
        raise HistoricalProviderError(
            "INVALID_OHLC", f"OHLC values cannot be negative on {bar.trading_date.isoformat()}"
        )
    if bar.volume is not None and bar.volume < 0:
        raise HistoricalProviderError(
            "INVALID_VOLUME", f"volume cannot be negative on {bar.trading_date.isoformat()}"
        )


class _VendorTaishinHistoryClient:
    """Synchronous bridge around the private ``tech_analysis_api_v2`` wheel."""

    def __init__(self, username: str, password: str, start_date: date, timeout: float):
        self.username = username
        self.password = password
        self.start_date = start_date
        self.timeout = timeout

    def fetch_daily_bars(self, instrument_code: str, market_code: str) -> Iterable[Any]:
        try:
            from tech_analysis_api_v2.api import TechAnalysis, eNK_Kind, eTA_Type
        except Exception as exc:  # pragma: no cover - depends on private runtime
            raise HistoricalProviderError(
                "VENDOR_RUNTIME_UNAVAILABLE", "Taishin technical-analysis runtime is unavailable"
            ) from exc

        connected = threading.Event()
        completed = threading.Event()
        state: dict[str, Any] = {"login_failed": False, "rows": None}

        def on_sso(ok: bool, _message: str) -> None:
            if not ok:
                state["login_failed"] = True
                connected.set()

        def on_connection(ok: bool) -> None:
            if ok:
                connected.set()
            else:
                state["login_failed"] = True
                connected.set()

        def on_update(*_args: Any) -> None:
            return None

        def on_done(_ta_type: Any, result: Any) -> None:
            state["rows"] = list(result or [])
            completed.set()

        client = TechAnalysis(on_sso, on_connection, on_update, on_done)
        setting = None
        try:
            client.Login(self.username, self.password)
            if not connected.wait(self.timeout):
                raise HistoricalProviderError("TAISHIN_CONNECT_TIMEOUT", "Taishin login timed out")
            if state["login_failed"]:
                raise HistoricalProviderError("TAISHIN_LOGIN_FAILED", "Taishin login failed")
            setting = TechAnalysis.get_k_setting(
                instrument_code,
                eTA_Type.SMA,
                eNK_Kind.DAY,
                self.start_date.strftime("%Y%m%d"),
            )
            client.SubTA(setting)
            if not completed.wait(self.timeout):
                raise HistoricalProviderError(
                    "TAISHIN_HISTORY_TIMEOUT", "Taishin history timed out"
                )
            return state["rows"] or []
        except HistoricalProviderError:
            raise
        except Exception as exc:  # pragma: no cover - depends on private runtime
            raise HistoricalProviderError(
                "TAISHIN_REQUEST_FAILED", "Taishin request failed"
            ) from exc
        finally:
            if setting is not None:
                with suppress(Exception):
                    client.UnSubTA(setting)
            with suppress(Exception):
                disconnect = getattr(client, "DisConnect", None)
                if callable(disconnect):
                    disconnect()


class _VendorTaishinIntradayClient:
    """Synchronous bridge for the vendor's 1m/3m/5m K-bar endpoint."""

    def __init__(self, username: str, password: str, timeout: float):
        self.username = username
        self.password = password
        self.timeout = timeout
        self._client: Any | None = None
        self._connected = False
        self._lock = threading.Lock()
        self._completed: threading.Event | None = None
        self._request_state: dict[str, Any] | None = None

    def connect(self) -> None:
        if self._connected and self._client is not None:
            return
        try:
            from tech_analysis_api_v2.api import TechAnalysis
        except Exception as exc:  # pragma: no cover - private runtime
            raise LiveProviderError(
                "VENDOR_RUNTIME_UNAVAILABLE",
                "Taishin technical-analysis runtime is unavailable",
                retryable=False,
            ) from exc

        connected = threading.Event()
        state: dict[str, Any] = {"login_failed": False}

        def on_sso(ok: bool, _message: str) -> None:
            if not ok:
                state["login_failed"] = True
                connected.set()

        def on_connection(ok: bool) -> None:
            if ok:
                connected.set()
            else:
                state["login_failed"] = True
                connected.set()

        def on_update(*_args: Any) -> None:
            return None

        def on_done(_ta_type: Any, result: Any) -> None:
            if self._request_state is not None:
                self._request_state["rows"] = list(result or [])
            if self._completed is not None:
                self._completed.set()

        client = TechAnalysis(on_sso, on_connection, on_update, on_done)
        try:
            client.Login(self.username, self.password)
            if not connected.wait(self.timeout):
                raise LiveProviderError("TAISHIN_CONNECT_TIMEOUT", "login timed out")
            if state["login_failed"]:
                raise LiveProviderError("TAISHIN_LOGIN_FAILED", "login failed", retryable=False)
            self._client = client
            self._connected = True
        except LiveProviderError:
            with suppress(Exception):
                disconnect = getattr(client, "DisConnect", None)
                if callable(disconnect):
                    disconnect()
            raise
        except Exception as exc:  # pragma: no cover - private runtime
            raise LiveProviderError("TAISHIN_REQUEST_FAILED", "login failed") from exc

    def disconnect(self) -> None:
        client = self._client
        self._client = None
        self._connected = False
        if client is not None:
            with suppress(Exception):
                disconnect = getattr(client, "DisConnect", None)
                if callable(disconnect):
                    disconnect()

    def health_check(self) -> bool:
        return self._connected and self._client is not None

    def fetch_intraday_bars(
        self, instrument_code: str, market_code: str, interval: str, session_date: date
    ) -> Iterable[Any]:
        try:
            from tech_analysis_api_v2.api import TechAnalysis, eNK_Kind, eTA_Type
        except Exception as exc:  # pragma: no cover - private runtime
            raise LiveProviderError(
                "VENDOR_RUNTIME_UNAVAILABLE",
                "Taishin technical-analysis runtime is unavailable",
                retryable=False,
            ) from exc

        interval_map = {"1m": eNK_Kind.K_1m, "3m": eNK_Kind.K_3m, "5m": eNK_Kind.K_5m}
        if interval not in interval_map:
            raise LiveProviderError("UNSUPPORTED_INTERVAL", interval, retryable=False)
        with self._lock:
            self.connect()
            client = self._client
            if client is None:
                raise LiveProviderError("TAISHIN_NOT_CONNECTED", "Taishin session is not connected")
            completed = threading.Event()
            state: dict[str, Any] = {"rows": None}
            self._completed = completed
            self._request_state = state
            setting = None
            try:
                setting = TechAnalysis.get_k_setting(
                    instrument_code,
                    eTA_Type.SMA,
                    interval_map[interval],
                    session_date.strftime("%Y%m%d"),
                )
                client.SubTA(setting)
                if not completed.wait(self.timeout):
                    raise LiveProviderError("TAISHIN_HISTORY_TIMEOUT", "intraday request timed out")
                return state["rows"] or []
            except LiveProviderError:
                raise
            except Exception as exc:  # pragma: no cover - private runtime
                raise LiveProviderError(
                    "TAISHIN_REQUEST_FAILED", "intraday request failed"
                ) from exc
            finally:
                self._completed = None
                self._request_state = None
                if setting is not None:
                    with suppress(Exception):
                        client.UnSubTA(setting)


class TaishinTechnicalAnalysisProvider:
    """Normalize daily bars returned by the optional Taishin runtime."""

    source_code = TAISHIN_SOURCE_CODE
    adapter_version = TAISHIN_ADAPTER_VERSION

    def __init__(
        self,
        *,
        client: TaishinHistoryClient | None = None,
        username: str | None = None,
        password: str | None = None,
        start_date: date | None = None,
        timeout: float = 30.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if client is None and (not username or not password):
            raise ValueError("username and password are required without an injected client")
        self.timeout = timeout
        self.start_date = start_date or date.today()
        # The private Taishin runtime currently requires Python 3.10 support;
        # keep the cross-version spelling instead of datetime.UTC.
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017
        self.client = client or _VendorTaishinHistoryClient(
            username or "", password or "", self.start_date, timeout
        )

    @classmethod
    def from_environment(
        cls, *, clock: Callable[[], datetime] | None = None
    ) -> TaishinTechnicalAnalysisProvider:
        username = os.getenv(TAISHIN_USER_ENV, "").strip()
        password = os.getenv(TAISHIN_PASSWORD_ENV, "")
        if not username or not password:
            raise HistoricalProviderError(
                "TAISHIN_CREDENTIALS_UNAVAILABLE", "Taishin credentials are not configured"
            )
        start_text = os.getenv(TAISHIN_START_DATE_ENV, "").strip()
        try:
            start_date = date.fromisoformat(start_text) if start_text else date.today()
            timeout = float(os.getenv(TAISHIN_TIMEOUT_ENV, "30"))
        except ValueError as exc:
            raise HistoricalProviderError(
                "TAISHIN_CONFIGURATION_INVALID", "Taishin history configuration is invalid"
            ) from exc
        return cls(
            username=username,
            password=password,
            start_date=start_date,
            timeout=timeout,
            clock=clock,
        )

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        if not isinstance(instrument_code, str) or not _IDENTIFIER_RE.fullmatch(instrument_code):
            raise HistoricalProviderError("INVALID_IDENTITY", "instrument_code is invalid")
        if not isinstance(market_code, str) or not _IDENTIFIER_RE.fullmatch(market_code):
            raise HistoricalProviderError("INVALID_IDENTITY", "market_code is invalid")
        try:
            raw_rows = list(self.client.fetch_daily_bars(instrument_code, market_code))
        except HistoricalProviderError:
            raise
        except Exception as exc:
            raise HistoricalProviderError(
                "TAISHIN_REQUEST_FAILED", "Taishin request failed"
            ) from exc

        bars: list[HistoricalBar] = []
        seen: set[date] = set()
        for row in raw_rows:
            # The current Taishin SMA response wraps the daily bar under
            # ``result.KBar``; injected clients may return the bar directly.
            bar_row = _field(row, "KBar", "kbar") or row
            trading_date = _parse_date(_field(bar_row, "date", "Date", "trading_date"))
            if trading_date in seen:
                raise HistoricalProviderError("DUPLICATE_DATE", trading_date.isoformat())
            seen.add(trading_date)
            bar = HistoricalBar(
                trading_date=trading_date,
                open=_decimal(_field(bar_row, "open", "Open", "OPrice"), "open"),
                high=_decimal(_field(bar_row, "high", "High", "HPrice"), "high"),
                low=_decimal(_field(bar_row, "low", "Low", "LPrice"), "low"),
                close=_decimal(_field(bar_row, "close", "Close", "CPrice"), "close"),
                volume=_decimal(
                    _field(bar_row, "volume", "Volume", "quantity", "Quantity"),
                    "volume",
                ),
            )
            _validate_bar(bar)
            bars.append(bar)
        bars.sort(key=lambda item: item.trading_date)
        retrieved_at = self.clock()
        if retrieved_at.tzinfo is None:
            raise HistoricalProviderError(
                "INVALID_RETRIEVAL_TIME",
                "retrieval time must be timezone-aware",
            )
        return HistoricalFetchResult(
            instrument_code=instrument_code,
            market_code=market_code,
            source_symbol=f"{instrument_code}@{market_code}",
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            retrieved_at=retrieved_at,
            bars=tuple(bars),
            raw_point_count=len(raw_rows),
            instrument_status=(
                "AVAILABLE" if all(bar.close is not None for bar in bars) else "UNKNOWN"
            ),
            status_explicit=False,
        )


def _parse_clock(value: Any) -> time:
    if isinstance(value, bool) or value is None:
        raise LiveProviderError("INVALID_INTRADAY_TIME", "bar time is missing", retryable=False)
    text = str(value).strip()
    if ":" in text:
        parts = text.split(":")
        if len(parts) not in (2, 3):
            raise LiveProviderError("INVALID_INTRADAY_TIME", text, retryable=False)
        try:
            hour, minute = int(parts[0]), int(parts[1])
            second = int(parts[2]) if len(parts) == 3 else 0
            return time(hour, minute, second)
        except ValueError as exc:
            raise LiveProviderError("INVALID_INTRADAY_TIME", text, retryable=False) from exc
    digits = text.split(".", 1)[0].zfill(4)
    if len(digits) not in (4, 6) or not digits.isdigit():
        raise LiveProviderError("INVALID_INTRADAY_TIME", text, retryable=False)
    try:
        if len(digits) == 4:
            return time(int(digits[:2]), int(digits[2:]))
        return time(int(digits[:2]), int(digits[2:4]), int(digits[4:]))
    except ValueError as exc:
        raise LiveProviderError("INVALID_INTRADAY_TIME", text, retryable=False) from exc


def _intraday_bar(
    row: Any, *, instrument_code: str, market_code: str, interval: str
) -> IntradayBar:
    bar_row = _field(row, "KBar", "kbar") or row
    trading_date = _parse_date(_field(bar_row, "date", "Date", "trading_date"))
    clock = _parse_clock(_field(bar_row, "time_display", "TimeSn_Dply", "time", "TimeSn"))
    observed_at = datetime.combine(trading_date, clock, tzinfo=TAIPEI).astimezone(
        timezone.utc  # noqa: UP017
    )

    def number(name: str, *aliases: str) -> Decimal | None:
        return _decimal(_field(bar_row, name, *aliases), name)

    bar = IntradayBar(
        instrument_code=instrument_code,
        market_code=market_code,
        observed_at=observed_at,
        open=number("open", "Open", "OPrice"),
        high=number("high", "High", "HPrice"),
        low=number("low", "Low", "LPrice"),
        close=number("close", "Close", "CPrice"),
        volume=number("volume", "Volume", "quantity", "Quantity"),
        interval=interval,
        source_payload={
            "date": trading_date.isoformat(),
            "time": clock.isoformat(),
            "open": str(number("open", "Open", "OPrice"))
            if number("open", "Open", "OPrice") is not None
            else None,
            "high": str(number("high", "High", "HPrice"))
            if number("high", "High", "HPrice") is not None
            else None,
            "low": str(number("low", "Low", "LPrice"))
            if number("low", "Low", "LPrice") is not None
            else None,
            "close": str(number("close", "Close", "CPrice"))
            if number("close", "Close", "CPrice") is not None
            else None,
            "volume": str(number("volume", "Volume", "quantity", "Quantity"))
            if number("volume", "Volume", "quantity", "Quantity") is not None
            else None,
            "interval": interval,
        },
    )
    values = (bar.open, bar.high, bar.low, bar.close)
    if any(value is not None for value in values):
        present = tuple(value for value in values if value is not None)
        if (
            bar.low is not None
            and bar.high is not None
            and (bar.low > min(present) or bar.high < max(present))
        ):
            raise LiveProviderError(
                "INVALID_OHLC", "intraday OHLC relationship is invalid", retryable=False
            )
    if bar.volume is not None and bar.volume < 0:
        raise LiveProviderError("INVALID_VOLUME", "intraday volume is negative", retryable=False)
    return bar


class TaishinIntradayProvider:
    """Provider-neutral intraday K-bar adapter for polling cycles."""

    source_code = TAISHIN_INTRADAY_SOURCE_CODE
    adapter_version = TAISHIN_INTRADAY_ADAPTER_VERSION

    def __init__(
        self,
        *,
        client: TaishinIntradayClient | None = None,
        username: str | None = None,
        password: str | None = None,
        interval: str = "5m",
        timeout: float = 30.0,
        clock: Callable[[], datetime] | None = None,
    ):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if interval not in {"1m", "3m", "5m"}:
            raise ValueError("interval must be 1m, 3m, or 5m")
        if client is None and (not username or not password):
            raise ValueError("username and password are required without an injected client")
        self.interval = interval
        self.timeout = timeout
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017
        self.client = client or _VendorTaishinIntradayClient(
            username or "", password or "", timeout
        )

    @classmethod
    def from_environment(cls, *, clock: Callable[[], datetime] | None = None):
        username = os.getenv(TAISHIN_USER_ENV, "").strip()
        password = os.getenv(TAISHIN_PASSWORD_ENV, "")
        if not username or not password:
            raise LiveProviderError(
                "TAISHIN_CREDENTIALS_UNAVAILABLE",
                "Taishin credentials are not configured",
                retryable=False,
            )
        try:
            timeout = float(os.getenv(TAISHIN_TIMEOUT_ENV, "30"))
        except ValueError as exc:
            raise LiveProviderError(
                "TAISHIN_CONFIGURATION_INVALID", "timeout is invalid", retryable=False
            ) from exc
        return cls(
            username=username,
            password=password,
            interval=os.getenv("TOPICPILOT_LIVE_INTERVAL", "5m").strip(),
            timeout=timeout,
            clock=clock,
        )

    def fetch_intraday(
        self, instrument_code: str, market_code: str, *, session_date: date
    ) -> IntradayFetchResult:
        try:
            rows = list(
                self.client.fetch_intraday_bars(
                    instrument_code, market_code, self.interval, session_date
                )
            )
        except LiveProviderError:
            raise
        except Exception as exc:
            raise LiveProviderError("TAISHIN_REQUEST_FAILED", "intraday request failed") from exc
        bars = tuple(
            sorted(
                (
                    _intraday_bar(
                        row,
                        instrument_code=instrument_code,
                        market_code=market_code,
                        interval=self.interval,
                    )
                    for row in rows
                ),
                key=lambda bar: bar.observed_at,
            )
        )
        retrieved_at = self.clock()
        if retrieved_at.tzinfo is None:
            raise LiveProviderError(
                "INVALID_RETRIEVAL_TIME", "retrieval time must be timezone-aware", retryable=False
            )
        if not bars:
            raise LiveProviderError(
                "EMPTY_INTRADAY_DATA", "provider returned no intraday bars", retryable=True
            )
        return IntradayFetchResult(
            instrument_code,
            market_code,
            f"{instrument_code}@{market_code}",
            self.source_code,
            self.adapter_version,
            retrieved_at,
            bars,
        )

    def connect(self) -> None:
        connect = getattr(self.client, "connect", None)
        if callable(connect):
            connect()

    def disconnect(self) -> None:
        disconnect = getattr(self.client, "disconnect", None)
        if callable(disconnect):
            disconnect()

    def health_check(self) -> bool:
        check = getattr(self.client, "health_check", None)
        return bool(check()) if callable(check) else True
