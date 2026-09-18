from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from topicpilot_api.live.post_close import (
    PostCloseUpdater,
    _market_response_diagnostic,
    _provider_exception_classification,
)
from topicpilot_api.market_data.exchange import _require_exchange_ok
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.market_data.ingestion import HistoricalIngestionError


@pytest.mark.parametrize(
    ("payload", "code", "classification"),
    [
        ({"stat": "很抱歉\uff0c查無資料"}, "EXCHANGE_NO_DATA", "EXCHANGE_NO_DATA"),
        (
            {"stat": "很抱歉\uff0c沒有符合條件的資料"},
            "EXCHANGE_NO_DATA",
            "EXCHANGE_NO_DATA",
        ),
        ({"stat": "too many requests"}, "RATE_LIMITED", "RATE_LIMITED"),
        ({"stat": "unauthorized"}, "AUTH_FAILED", "AUTH_FAILED"),
        ({"stat": ""}, "EMPTY_RESPONSE", "EMPTY_RESPONSE"),
        ({}, "SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ],
)
def test_exchange_status_preserves_first_failure_class(payload, code, classification):
    with pytest.raises(HistoricalProviderError) as caught:
        _require_exchange_ok(payload)

    assert caught.value.code == code
    assert caught.value.classification == classification
    assert _provider_exception_classification(caught.value) == classification


def test_provider_and_normalization_layers_are_distinguishable():
    assert (
        _provider_exception_classification(
            HistoricalProviderError(
                "INVALID_PAYLOAD", "missing table", classification="SCHEMA_MISMATCH"
            )
        )
        == "SCHEMA_MISMATCH"
    )
    assert (
        _provider_exception_classification(
            HistoricalProviderError(
                "PROVIDER_DATE_MISMATCH",
                "wrong date",
                classification="TRADING_DATE_MISMATCH",
            )
        )
        == "TRADING_DATE_MISMATCH"
    )
    assert (
        _provider_exception_classification(
            HistoricalIngestionError(
                "REFERENCE_DATA_UNAVAILABLE",
                "reference context unavailable",
                classification="NORMALIZATION_FAILED",
            )
        )
        == "NORMALIZATION_FAILED"
    )


def test_market_response_diagnostic_reconciles_requested_and_provider_rows():
    diagnostic, failure = _market_response_diagnostic(
        requested_codes=("2330", "4979", "6806"),
        provider_codes=("2330", "4979", "9999"),
        provider="TWSE_OFFICIAL_DAILY",
        adapter_version="twse-official-daily.v2",
        target_date=date(2026, 9, 15),
        retrieved_at=datetime(2026, 9, 16, 3, 0, tzinfo=UTC),
        request_count=1,
    )

    assert failure is None
    assert diagnostic == {
        "status": "AVAILABLE",
        "provider": "TWSE_OFFICIAL_DAILY",
        "adapterVersion": "twse-official-daily.v2",
        "targetDate": "2026-09-15",
        "requestScope": "MARKET_DAY",
        "requestedCount": 3,
        "providerRowCount": 3,
        "matchedCount": 2,
        "missingCount": 1,
        "unrequestedRowCount": 1,
        "requestCount": 1,
        "retrievedAt": datetime(2026, 9, 16, 3, 0, tzinfo=UTC),
    }


@pytest.mark.parametrize(
    ("provider_codes", "classification"),
    [([], "EMPTY_RESPONSE"), (["9999"], "SYMBOL_MAPPING_FAILED")],
)
def test_empty_or_zero_match_market_response_is_systemic(provider_codes, classification):
    diagnostic, failure = _market_response_diagnostic(
        requested_codes=("2330", "4979"),
        provider_codes=provider_codes,
        provider="TWSE_OFFICIAL_DAILY",
        adapter_version="twse-official-daily.v2",
        target_date=date(2026, 9, 15),
    )

    assert failure == (classification, classification)
    assert diagnostic["status"] == "FAILED"
    assert diagnostic["classification"] == classification


def test_final_checkpoint_never_claims_completion_for_a_partial_run():
    run = SimpleNamespace(
        id="run-1",
        status="RUNNING",
        started_at=datetime(2026, 9, 15, 5, 35, tzinfo=UTC),
        requested_count=3,
        metadata_payload={},
    )

    class Session:
        def get(self, _model, _run_id):
            return run

        def commit(self):
            return None

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = Session()
    updater.config = SimpleNamespace(reference_data_version="tw-reference-v1")

    updater._finish(
        run.id,
        status="PARTIAL",
        success_count=2,
        failure_count=1,
        skipped_count=0,
        retry_count=1,
        point_count=2,
        failure_codes=("EXCHANGE_NO_DATA",),
        snapshot_result={"status": "BLOCKED_DAILY_MARKET_NOT_READY"},
        reconciliation=None,
        now=datetime(2026, 9, 15, 6, 0, tzinfo=UTC),
    )

    assert run.metadata_payload["recoveryProgress"]["CHECKPOINT"]["status"] == "PARTIAL"
    assert run.metadata_payload["forwardAutomation"]["status"] == "BLOCKED"
