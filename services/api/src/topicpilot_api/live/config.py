"""Environment-driven live runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date


def _int(name: str, default: int, *, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _closed_dates(name: str) -> frozenset[date]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return frozenset()
    values: set[date] = set()
    for item in raw.split(","):
        try:
            values.add(date.fromisoformat(item.strip()))
        except ValueError as exc:
            raise ValueError(f"{name} must contain ISO dates") from exc
    return frozenset(values)


@dataclass(frozen=True)
class LiveRuntimeConfig:
    timezone_name: str = "Asia/Taipei"
    poll_interval_seconds: int = 300
    provider_timeout_seconds: float = 30.0
    max_retries: int = 2
    retry_backoff_seconds: float = 2.0
    session_open: str = "09:00"
    session_close: str = "13:30"
    moving_average_period: int = 60
    reference_data_version: str = "tw-reference-v1"
    session_code: str = "REGULAR"
    calendar_code: str = "TW_MARKET"
    normalization_contract_version: str = "normalization-contract-v1"
    mapping_policy_version: str = "live-intraday-mapping-v1"
    source_category: str = "INTRADAY_BAR"
    provider_code: str = "TAISHIN_TECH_ANALYSIS_INTRADAY"
    interval: str = "5m"
    provider_requests_per_minute: int = 60
    provider_symbols_per_request: int = 1
    provider_cooldown_seconds: float = 0.0
    provider_source_rank: int = 100
    yahoo_timeout_seconds: float = 15.0
    yahoo_requests_per_minute: int = 60
    yahoo_cooldown_seconds: float = 0.0
    yahoo_source_rank: int = 10
    taishin_source_rank: int = 20
    freshness_window_seconds: int = 900
    circuit_failure_threshold: int = 3
    circuit_open_seconds: float = 60.0
    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 30.0
    reconnect_jitter_seconds: float = 0.25
    timestamp_future_tolerance_seconds: int = 300
    history_batch_size: int = 20
    # Official TWSE/TPEx daily endpoints are intentionally paced below the
    # provider's observed ceiling.  Keep the safe recovery budget as the
    # production default; deployments may still override it explicitly.
    history_requests_per_minute: int = 30
    history_min_request_interval_seconds: float = 0.5
    history_max_retries: int = 4
    history_retry_backoff_seconds: float = 2.0
    tracking_refresh_batch_size: int = 50
    tracking_refresh_lock_timeout_seconds: float = 30.0
    tracking_refresh_statement_timeout_seconds: float = 120.0
    closed_dates: frozenset[date] = frozenset()

    def __post_init__(self) -> None:
        if self.poll_interval_seconds < 60:
            raise ValueError("poll_interval_seconds must be at least 60 seconds")
        if self.max_retries < 0 or self.provider_timeout_seconds <= 0:
            raise ValueError("retry and timeout configuration is invalid")
        if self.moving_average_period < 1:
            raise ValueError("moving_average_period must be positive")
        if self.provider_requests_per_minute < 1 or self.provider_symbols_per_request < 1:
            raise ValueError("provider budget limits must be positive")
        if self.yahoo_timeout_seconds <= 0 or self.yahoo_requests_per_minute < 1:
            raise ValueError("Yahoo provider configuration is invalid")
        if (
            self.yahoo_cooldown_seconds < 0
            or self.yahoo_source_rank < 0
            or self.taishin_source_rank < 0
        ):
            raise ValueError("provider source configuration is invalid")
        if self.provider_cooldown_seconds < 0 or self.freshness_window_seconds < 1:
            raise ValueError("provider freshness/budget configuration is invalid")
        if self.timestamp_future_tolerance_seconds < 0:
            raise ValueError("timestamp future tolerance must not be negative")
        if (
            self.history_batch_size < 1
            or self.history_requests_per_minute < 1
            or self.history_min_request_interval_seconds < 0
            or self.history_max_retries < 0
            or self.history_retry_backoff_seconds < 0
        ):
            raise ValueError("historical provider configuration is invalid")
        if (
            self.tracking_refresh_batch_size < 1
            or self.tracking_refresh_lock_timeout_seconds <= 0
            or self.tracking_refresh_statement_timeout_seconds <= 0
        ):
            raise ValueError("tracking refresh timeout/batch configuration is invalid")
        if self.circuit_failure_threshold < 1 or self.circuit_open_seconds <= 0:
            raise ValueError("circuit breaker configuration is invalid")
        if (
            self.reconnect_initial_seconds < 0
            or self.reconnect_max_seconds < self.reconnect_initial_seconds
            or self.reconnect_jitter_seconds < 0
        ):
            raise ValueError("reconnect configuration is invalid")
        for name in (
            "timezone_name",
            "session_open",
            "session_close",
            "reference_data_version",
            "session_code",
            "calendar_code",
            "normalization_contract_version",
            "mapping_policy_version",
            "source_category",
            "provider_code",
            "interval",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")

    @classmethod
    def from_environment(cls) -> LiveRuntimeConfig:
        return cls(
            timezone_name=os.getenv("TOPICPILOT_LIVE_TIMEZONE", "Asia/Taipei").strip(),
            poll_interval_seconds=_int("TOPICPILOT_LIVE_POLL_INTERVAL_SECONDS", 300, minimum=60),
            provider_timeout_seconds=_float(
                "TOPICPILOT_LIVE_PROVIDER_TIMEOUT_SECONDS", 30.0, minimum=0.1
            ),
            max_retries=_int("TOPICPILOT_LIVE_MAX_RETRIES", 2, minimum=0),
            retry_backoff_seconds=_float("TOPICPILOT_LIVE_RETRY_BACKOFF_SECONDS", 2.0, minimum=0.0),
            session_open=os.getenv("TOPICPILOT_LIVE_SESSION_OPEN", "09:00").strip(),
            session_close=os.getenv("TOPICPILOT_LIVE_SESSION_CLOSE", "13:30").strip(),
            moving_average_period=_int("TOPICPILOT_LIVE_60MA_PERIOD", 60, minimum=1),
            reference_data_version=os.getenv(
                "TOPICPILOT_LIVE_REFERENCE_DATA_VERSION", "tw-reference-v1"
            ).strip(),
            session_code=os.getenv("TOPICPILOT_LIVE_SESSION_CODE", "REGULAR").strip(),
            calendar_code=os.getenv("TOPICPILOT_LIVE_CALENDAR_CODE", "TW_MARKET").strip(),
            normalization_contract_version=os.getenv(
                "TOPICPILOT_LIVE_NORMALIZATION_VERSION", "normalization-contract-v1"
            ).strip(),
            mapping_policy_version=os.getenv(
                "TOPICPILOT_LIVE_MAPPING_VERSION", "live-intraday-mapping-v1"
            ).strip(),
            source_category=os.getenv("TOPICPILOT_LIVE_SOURCE_CATEGORY", "INTRADAY_BAR").strip(),
            provider_code=os.getenv(
                "TOPICPILOT_LIVE_PROVIDER_CODE", "TAISHIN_TECH_ANALYSIS_INTRADAY"
            ).strip(),
            interval=os.getenv("TOPICPILOT_LIVE_INTERVAL", "5m").strip(),
            provider_requests_per_minute=_int(
                "TOPICPILOT_PROVIDER_REQUESTS_PER_MINUTE", 60, minimum=1
            ),
            provider_symbols_per_request=_int(
                "TOPICPILOT_PROVIDER_SYMBOLS_PER_REQUEST", 1, minimum=1
            ),
            provider_cooldown_seconds=_float(
                "TOPICPILOT_PROVIDER_COOLDOWN_SECONDS", 0.0, minimum=0.0
            ),
            provider_source_rank=_int("TOPICPILOT_PROVIDER_SOURCE_RANK", 100, minimum=0),
            yahoo_timeout_seconds=_float(
                "TOPICPILOT_YAHOO_QUOTE_TIMEOUT_SECONDS", 15.0, minimum=0.1
            ),
            yahoo_requests_per_minute=_int(
                "TOPICPILOT_YAHOO_QUOTE_REQUESTS_PER_MINUTE", 60, minimum=1
            ),
            yahoo_cooldown_seconds=_float(
                "TOPICPILOT_YAHOO_QUOTE_COOLDOWN_SECONDS", 0.0, minimum=0.0
            ),
            yahoo_source_rank=_int("TOPICPILOT_YAHOO_QUOTE_SOURCE_RANK", 10, minimum=0),
            taishin_source_rank=_int("TOPICPILOT_TAISHIN_SOURCE_RANK", 20, minimum=0),
            freshness_window_seconds=_int(
                "TOPICPILOT_LIVE_FRESHNESS_WINDOW_SECONDS", 900, minimum=1
            ),
            circuit_failure_threshold=_int(
                "TOPICPILOT_PROVIDER_CIRCUIT_FAILURE_THRESHOLD", 3, minimum=1
            ),
            circuit_open_seconds=_float(
                "TOPICPILOT_PROVIDER_CIRCUIT_OPEN_SECONDS", 60.0, minimum=0.1
            ),
            reconnect_initial_seconds=_float(
                "TOPICPILOT_PROVIDER_RECONNECT_INITIAL_SECONDS", 1.0, minimum=0.0
            ),
            reconnect_max_seconds=_float(
                "TOPICPILOT_PROVIDER_RECONNECT_MAX_SECONDS", 30.0, minimum=0.0
            ),
            reconnect_jitter_seconds=_float(
                "TOPICPILOT_PROVIDER_RECONNECT_JITTER_SECONDS", 0.25, minimum=0.0
            ),
            timestamp_future_tolerance_seconds=_int(
                "TOPICPILOT_LIVE_TIMESTAMP_FUTURE_TOLERANCE_SECONDS", 300, minimum=0
            ),
            history_batch_size=_int("TOPICPILOT_HISTORY_BATCH_SIZE", 20, minimum=1),
            history_requests_per_minute=_int(
                "TOPICPILOT_HISTORY_REQUESTS_PER_MINUTE", 30, minimum=1
            ),
            history_min_request_interval_seconds=_float(
                "TOPICPILOT_HISTORY_MIN_REQUEST_INTERVAL_SECONDS", 0.5, minimum=0.0
            ),
            history_max_retries=_int("TOPICPILOT_HISTORY_MAX_RETRIES", 4, minimum=0),
            history_retry_backoff_seconds=_float(
                "TOPICPILOT_HISTORY_RETRY_BACKOFF_SECONDS", 2.0, minimum=0.0
            ),
            tracking_refresh_batch_size=_int(
                "TOPICPILOT_LIVE_TRACKING_REFRESH_BATCH_SIZE", 50, minimum=1
            ),
            tracking_refresh_lock_timeout_seconds=_float(
                "TOPICPILOT_LIVE_TRACKING_REFRESH_LOCK_TIMEOUT_SECONDS", 30.0, minimum=0.1
            ),
            tracking_refresh_statement_timeout_seconds=_float(
                "TOPICPILOT_LIVE_TRACKING_REFRESH_STATEMENT_TIMEOUT_SECONDS", 120.0, minimum=0.1
            ),
            closed_dates=_closed_dates("TOPICPILOT_LIVE_CLOSED_DATES"),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "timezoneName": self.timezone_name,
            "pollIntervalSeconds": self.poll_interval_seconds,
            "providerTimeoutSeconds": self.provider_timeout_seconds,
            "maxRetries": self.max_retries,
            "retryBackoffSeconds": self.retry_backoff_seconds,
            "sessionOpen": self.session_open,
            "sessionClose": self.session_close,
            "movingAveragePeriod": self.moving_average_period,
            "referenceDataVersion": self.reference_data_version,
            "sessionCode": self.session_code,
            "calendarCode": self.calendar_code,
            "interval": self.interval,
            "providerRequestsPerMinute": self.provider_requests_per_minute,
            "providerSymbolsPerRequest": self.provider_symbols_per_request,
            "providerCooldownSeconds": self.provider_cooldown_seconds,
            "providerSourceRank": self.provider_source_rank,
            "yahooTimeoutSeconds": self.yahoo_timeout_seconds,
            "yahooRequestsPerMinute": self.yahoo_requests_per_minute,
            "yahooCooldownSeconds": self.yahoo_cooldown_seconds,
            "yahooSourceRank": self.yahoo_source_rank,
            "taishinSourceRank": self.taishin_source_rank,
            "freshnessWindowSeconds": self.freshness_window_seconds,
            "circuitFailureThreshold": self.circuit_failure_threshold,
            "circuitOpenSeconds": self.circuit_open_seconds,
            "reconnectInitialSeconds": self.reconnect_initial_seconds,
            "reconnectMaxSeconds": self.reconnect_max_seconds,
            "reconnectJitterSeconds": self.reconnect_jitter_seconds,
            "timestampFutureToleranceSeconds": self.timestamp_future_tolerance_seconds,
            "historyBatchSize": self.history_batch_size,
            "historyRequestsPerMinute": self.history_requests_per_minute,
            "historyMinRequestIntervalSeconds": self.history_min_request_interval_seconds,
            "historyMaxRetries": self.history_max_retries,
            "historyRetryBackoffSeconds": self.history_retry_backoff_seconds,
            "trackingRefreshBatchSize": self.tracking_refresh_batch_size,
            "trackingRefreshLockTimeoutSeconds": self.tracking_refresh_lock_timeout_seconds,
            "trackingRefreshStatementTimeoutSeconds": (
                self.tracking_refresh_statement_timeout_seconds
            ),
            "closedDates": sorted(item.isoformat() for item in self.closed_dates),
        }

    def as_hash_dict(self) -> dict[str, object]:
        """Return the same config using the normalizer's JSON-safe scalar set."""

        return {
            key: str(value) if isinstance(value, float) else value
            for key, value in self.as_dict().items()
        }


__all__ = ["LiveRuntimeConfig"]
