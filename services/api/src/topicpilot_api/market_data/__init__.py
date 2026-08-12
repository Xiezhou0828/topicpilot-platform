"""Provider-neutral market-data capability contracts."""

from .exchange import (
    TPEX_DAILY_ADAPTER_VERSION,
    TPEX_DAILY_SOURCE_CODE,
    TWSE_DAILY_ADAPTER_VERSION,
    TWSE_DAILY_SOURCE_CODE,
    TpexOfficialDailyProvider,
    TwseOfficialDailyProvider,
)
from .history import (
    HistoricalBar,
    HistoricalFetchResult,
    HistoricalProviderError,
    HistoryAvailability,
    YahooChartHistoricalProvider,
    probe_history_availability,
)
from .ingestion import (
    HistoricalIngestionError,
    HistoricalIngestionResult,
    HistoricalSourceRegistration,
    ingest_historical,
)
from .taishin import (
    TaishinHistoryClient,
    TaishinIntradayClient,
    TaishinIntradayProvider,
    TaishinTechnicalAnalysisProvider,
)
from .yahoo_quote import (
    YAHOO_QUOTE_ADAPTER_VERSION,
    YAHOO_QUOTE_SOURCE_CODE,
    YahooQuoteProvider,
)

__all__ = [
    "TPEX_DAILY_ADAPTER_VERSION",
    "TPEX_DAILY_SOURCE_CODE",
    "TWSE_DAILY_ADAPTER_VERSION",
    "TWSE_DAILY_SOURCE_CODE",
    "YAHOO_QUOTE_ADAPTER_VERSION",
    "YAHOO_QUOTE_SOURCE_CODE",
    "HistoricalBar",
    "HistoricalFetchResult",
    "HistoricalIngestionError",
    "HistoricalIngestionResult",
    "HistoricalProviderError",
    "HistoricalSourceRegistration",
    "HistoryAvailability",
    "TaishinHistoryClient",
    "TaishinIntradayClient",
    "TaishinIntradayProvider",
    "TaishinTechnicalAnalysisProvider",
    "TpexOfficialDailyProvider",
    "TwseOfficialDailyProvider",
    "YahooChartHistoricalProvider",
    "YahooQuoteProvider",
    "ingest_historical",
    "probe_history_availability",
]
