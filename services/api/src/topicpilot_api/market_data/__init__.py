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
from .index_contract import (
    IndexContractError,
    IndexDataStatus,
    MarketIndexResult,
    TpexIndexCrossCheck,
    fetch_official_market_indexes,
    parse_tpex_index_crosscheck,
    parse_tpex_market_index,
    parse_twse_market_index,
    unavailable_market_index,
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
    "IndexContractError",
    "IndexDataStatus",
    "MarketIndexResult",
    "TaishinHistoryClient",
    "TaishinIntradayClient",
    "TaishinIntradayProvider",
    "TaishinTechnicalAnalysisProvider",
    "TpexIndexCrossCheck",
    "TpexOfficialDailyProvider",
    "TwseOfficialDailyProvider",
    "YahooChartHistoricalProvider",
    "YahooQuoteProvider",
    "fetch_official_market_indexes",
    "ingest_historical",
    "parse_tpex_index_crosscheck",
    "parse_tpex_market_index",
    "parse_twse_market_index",
    "probe_history_availability",
    "unavailable_market_index",
]
