"""Cold-process Worker/package imports must not rely on pytest import order."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
INGESTION_EXPORTS = (
    "HistoricalIngestionError",
    "HistoricalIngestionResult",
    "HistoricalSourceRegistration",
    "ingest_historical",
)
PUBLIC_EXPORTS = (
    "INSTITUTIONAL_FLOW_ADAPTER_VERSION",
    "TPEX_DAILY_ADAPTER_VERSION", "TPEX_DAILY_SOURCE_CODE",
    "TPEX_INSTITUTIONAL_FLOW_ENDPOINT", "TPEX_INSTITUTIONAL_FLOW_SOURCE",
    "TWSE_DAILY_ADAPTER_VERSION", "TWSE_DAILY_SOURCE_CODE",
    "TWSE_INSTITUTIONAL_FLOW_ENDPOINT", "TWSE_INSTITUTIONAL_FLOW_SOURCE",
    "YAHOO_QUOTE_ADAPTER_VERSION", "YAHOO_QUOTE_SOURCE_CODE",
    "AggregateContractError", "HistoricalBar", "HistoricalFetchResult",
    "HistoricalIngestionError", "HistoricalIngestionResult", "HistoricalProviderError",
    "HistoricalSourceRegistration", "HistoryAvailability", "IndexContractError",
    "IndexDataStatus", "InstitutionalFlowContractError", "MarketAggregateResult",
    "MarketIndexResult", "MarketInstitutionalFlowResult", "TaishinHistoryClient",
    "TaishinIntradayClient", "TaishinIntradayProvider", "TaishinTechnicalAnalysisProvider",
    "TpexIndexCrossCheck", "TpexOfficialDailyProvider", "TwseOfficialDailyProvider",
    "YahooChartHistoricalProvider", "YahooQuoteProvider", "fetch_official_market_aggregates",
    "fetch_official_market_indexes", "fetch_official_market_institutional_flows",
    "ingest_historical", "parse_tpex_index_crosscheck", "parse_tpex_institutional_flow",
    "parse_tpex_market_aggregate", "parse_tpex_market_index", "parse_twse_institutional_flow",
    "parse_twse_market_aggregate", "parse_twse_market_index", "parse_twse_market_index_ohlc",
    "persist_market_institutional_flows", "probe_history_availability", "unavailable_market_index",
)


def _cold_process(code: str) -> subprocess.CompletedProcess[str]:
    # No inherited DB or vendor credentials; even accidental network access fails.
    env = {
        key: value for key, value in os.environ.items()
        if not any(part in key.upper() for part in ("DATABASE", "TEST_DB", "TAISHIN", "TA_API"))
    }
    prelude = (
        "import sys, socket\n"
        f"sys.path.insert(0, {json.dumps(str(SOURCE_ROOT))})\n"
        "def forbid_network(*args, **kwargs):\n"
        "    raise AssertionError('cold-import tests must not access network/DB')\n"
        "socket.socket.connect = forbid_network\n"
    )
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", prelude + textwrap.dedent(code)],
        env=env, capture_output=True, text=True, timeout=30, check=False,
    )


def _assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", [
    "topicpilot_api.live.cli",
    "topicpilot_api.normalizer.historical",
    "topicpilot_api.market_data.ingestion",
    "topicpilot_api.normalizer",
    "topicpilot_api.market_data.history",
    "topicpilot_api.provider_preflight_cli",
])
def test_clean_interpreter_first_import(module: str) -> None:
    _assert_success(_cold_process(f"import importlib; importlib.import_module({module!r})"))


def test_history_contract_does_not_eagerly_import_ingestion() -> None:
    _assert_success(_cold_process("""
        import topicpilot_api.market_data.history
        assert 'topicpilot_api.market_data.ingestion' not in sys.modules
    """))


def test_public_exports_and_star_import_keep_original_object_identity() -> None:
    _assert_success(_cold_process(f"""
        import topicpilot_api.market_data as market_data
        assert tuple(market_data.__all__) == {PUBLIC_EXPORTS!r}
        assert set({INGESTION_EXPORTS!r}).issubset(dir(market_data))
        assert 'topicpilot_api.market_data.ingestion' not in sys.modules
        namespace = {{}}
        exec('from topicpilot_api.market_data import *', namespace)
        from topicpilot_api.market_data import ingestion
        for name in {INGESTION_EXPORTS!r}:
            expected = getattr(ingestion, name)
            assert getattr(market_data, name) is expected
            assert namespace[name] is expected
            assert market_data.__dict__[name] is expected
        assert set(namespace) - {{'__builtins__'}} == set(market_data.__all__)
    """))


def test_unknown_export_remains_attribute_error() -> None:
    _assert_success(_cold_process("""
        import topicpilot_api.market_data as market_data
        try:
            market_data.nonexistent_provider
        except AttributeError:
            pass
        else:
            raise AssertionError('unknown exports must not be invented')
    """))


def test_lazy_export_does_not_swallow_real_import_failure() -> None:
    _assert_success(_cold_process("""
        import topicpilot_api.market_data as market_data
        def fail_import(name):
            raise ImportError('controlled dependency failure')
        market_data.import_module = fail_import
        try:
            market_data.ingest_historical
        except ImportError as exc:
            assert str(exc) == 'controlled dependency failure'
        else:
            raise AssertionError('dependency failure must propagate')
        assert 'ingest_historical' not in market_data.__dict__
    """))


@pytest.mark.parametrize("mode", ["auto", "post-close"])
def test_worker_startup_dry_run_never_calls_provider_or_database(mode: str) -> None:
    _assert_success(_cold_process(f"""
        import topicpilot_api.live.cli as cli
        def forbidden(*args, **kwargs):
            raise AssertionError('dry-run must not access provider or DB')
        cli.build_live_provider_router = forbidden
        cli.create_engine = forbidden
        assert cli.main(['--mode', {mode!r}, '--dry-run']) == 0
    """))


def test_worker_missing_credentials_still_fail_closed() -> None:
    _assert_success(_cold_process("""
        import topicpilot_api.live.cli
        from topicpilot_api.live.contracts import LiveProviderError
        from topicpilot_api.market_data.history import HistoricalProviderError
        from topicpilot_api.market_data.taishin import (
            TaishinIntradayProvider, TaishinTechnicalAnalysisProvider,
        )
        for provider, error in (
            (TaishinIntradayProvider, LiveProviderError),
            (TaishinTechnicalAnalysisProvider, HistoricalProviderError),
        ):
            try:
                provider.from_environment()
            except error as exc:
                assert exc.code == 'TAISHIN_CREDENTIALS_UNAVAILABLE'
            else:
                raise AssertionError('missing credentials must remain a failure')
    """))


def test_worker_provider_failure_is_not_reported_as_startup_success() -> None:
    result = _cold_process("""
        import topicpilot_api.live.cli as cli
        from topicpilot_api.live.contracts import LiveProviderError
        def provider_failure(*args, **kwargs):
            raise LiveProviderError('CONTROLLED_PROVIDER_FAILURE', 'test transport failure')
        cli.build_live_provider_router = provider_failure
        cli.create_engine = forbid_network
        cli.main(['--mode', 'intraday', '--once'])
    """)
    assert result.returncode != 0
    assert "LiveProviderError: CONTROLLED_PROVIDER_FAILURE" in result.stderr
    assert "partially initialized module" not in result.stderr
    assert "cold-import tests must not access network/DB" not in result.stderr
