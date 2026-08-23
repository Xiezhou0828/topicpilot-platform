from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from topicpilot_api.market_data.historical_promotion import (
    BRIDGE_CONTRACT_VERSION,
    BRIDGE_MAPPING_POLICY_VERSION,
    HistoricalPromotionError,
    _assert_local_target,
    _manifest_rows,
    _market_date_anchor,
    _payload,
)


def _legacy_row(row_id: int) -> dict:
    return {
        "id": row_id,
        "market": "TWSE",
        "security_code": "2330",
        "trading_date": date(2026, 2, row_id),
        "open": "100",
        "high": "110",
        "low": "90",
        "close": "105",
        "volume": 1000,
        "provider": "TWSE",
        "source_url": "https://example.test/twse",
        "provider_lineage": {
            "provider": "TWSE",
            "normalizer": "topicpilot.official_ohlcv.v1",
            "source_url": "https://example.test/twse",
            "source_kind": "official_exchange",
            "retrieved_at": "2026-08-14T13:00:00+00:00",
            "request_params": {"date": "2026/02/02"},
            "response_sha256": "a" * 64,
        },
        "lifecycle_status": "active",
        "created_at": "2026-08-14T13:01:00+00:00",
    }


def test_manifest_digest_is_independent_of_query_order():
    rows = [_legacy_row(2), _legacy_row(1)]
    assert _manifest_rows(rows) == _manifest_rows(list(reversed(rows)))


def test_market_date_anchor_is_explicit_taipei_midnight():
    anchored = _market_date_anchor(date(2026, 2, 2), "Asia/Taipei")
    assert anchored.isoformat() == "2026-02-02T00:00:00+08:00"


def test_payload_preserves_legacy_lineage_and_does_not_invent_status():
    row = _legacy_row(1)
    source = SimpleNamespace(
        source_code="TWSE_OFFICIAL_DAILY", adapter_version="twse-official-daily.v1"
    )
    manifest = SimpleNamespace(manifest_sha256="manifest")
    payload = _payload(row, source, manifest)
    assert payload["open"] == "100"
    assert payload["volume"] == "1000"
    assert "instrument_status" not in payload
    assert payload["legacy_evidence"]["row_id"] == "1"
    assert payload["legacy_evidence"]["legacy_normalizer"] == "topicpilot.official_ohlcv.v1"
    assert payload["legacy_evidence"]["bridge_contract_version"] == BRIDGE_CONTRACT_VERSION
    assert (
        payload["legacy_evidence"]["bridge_mapping_policy_version"] == BRIDGE_MAPPING_POLICY_VERSION
    )


def test_local_only_guard_rejects_nonlocal_database_without_connecting():
    engine = create_engine("sqlite://")
    with pytest.raises(HistoricalPromotionError, match="not local"):
        _assert_local_target(engine, local_only=True)
    engine.dispose()
