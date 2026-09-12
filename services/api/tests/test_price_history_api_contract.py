from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

import topicpilot_api.main as main_module
import topicpilot_api.production_read_model_api as production_read_model_api
from topicpilot_api.config import Settings
from topicpilot_api.database import get_db
from topicpilot_api.main import create_app


def test_price_history_contract_is_read_model_only_and_nullable(monkeypatch):
    calls: list[tuple] = []

    def fake_list_price_history(session, code, from_date, to_date, market_code, limit):
        calls.append((session, code, from_date, to_date, market_code, limit))
        return {
            "code": code,
            "market": market_code or "TPE",
            "requested_from": from_date,
            "requested_to": to_date,
            "status": "AVAILABLE",
            "availability_reason": None,
            "point_count": 1,
            "items": [
                {
                    "trading_date": from_date,
                    "observed_at": datetime(2026, 8, 3, tzinfo=UTC),
                    "open": None,
                    "high": 11.0,
                    "low": 9.0,
                    "close": 10.0,
                    "volume": None,
                    "source_code": "TEST_SOURCE",
                    "quality_state": "ACCEPTED",
                }
            ],
        }

    monkeypatch.setattr(main_module, "list_price_history", fake_list_price_history)
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/stocks/2330/price-history",
            params={"from": "2026-08-03", "to": "2026-08-14", "market": "TPE"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "AVAILABLE"
    assert payload["items"][0]["open"] is None
    assert payload["items"][0]["volume"] is None
    assert calls[0][1:] == (
        "2330",
        date(2026, 8, 3),
        date(2026, 8, 14),
        "TPE",
        200,
    )


def test_price_history_rejects_reversed_date_window_without_provider_call(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("repository must not be called for an invalid window")

    monkeypatch.setattr(main_module, "list_price_history", fail_if_called)
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/stocks/2330/price-history",
            params={"from": "2026-08-14", "to": "2026-08-03"},
        )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_v2_price_history_is_bounded_subresource_over_shared_read_authority(monkeypatch):
    calls: list[tuple] = []

    def fake_read_historical_bars(session, symbol, from_date, to_date, market_code, limit):
        calls.append((session, symbol, from_date, to_date, market_code, limit))
        return {
            "code": symbol,
            "market": market_code or "TPE",
            "requested_from": from_date,
            "requested_to": to_date,
            "returned_from": from_date,
            "returned_to": to_date,
            "latest_trading_date": to_date,
            "latest_observed_at": datetime(2026, 8, 14, tzinfo=UTC),
            "latest_retrieved_at": datetime(2026, 8, 14, tzinfo=UTC),
            "status": "AVAILABLE",
            "coverage_state": "AVAILABLE",
            "availability_reason": None,
            "point_count": 1,
            "has_more": False,
            "lifecycle": None,
            "items": [
                {
                    "trading_date": from_date,
                    "observed_at": datetime(2026, 8, 14, tzinfo=UTC),
                    "retrieved_at": datetime(2026, 8, 14, tzinfo=UTC),
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.0,
                    "close": 10.5,
                    "volume": 1000,
                    "source_code": "TEST_SOURCE",
                    "quality_state": "ACCEPTED",
                    "adjustment_state": "UNKNOWN",
                    "source": {
                        "source_code": "TEST_SOURCE",
                        "adapter_version": "test.v1",
                        "observation_semantics": "DAILY_BAR",
                        "reference_data_version": "ref.v1",
                        "normalization_contract_version": "norm.v1",
                        "mapping_policy_version": "map.v1",
                    },
                    "adapter_version": "test.v1",
                    "normalization_contract_version": "norm.v1",
                    "mapping_policy_version": "map.v1",
                    "reference_data_version": "ref.v1",
                }
            ],
        }

    monkeypatch.setattr(
        production_read_model_api,
        "read_historical_bars",
        fake_read_historical_bars,
    )
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v2/stocks/2330/price-history",
            params={"from": "2026-08-03", "to": "2026-08-14", "market": "TPE", "limit": 200},
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["adjustmentState"] == "UNKNOWN"
    assert response.json()["items"][0]["source"]["adapterVersion"] == "test.v1"
    assert calls[0][1:] == (
        "2330",
        date(2026, 8, 3),
        date(2026, 8, 14),
        "TPE",
        200,
    )


def test_v2_price_history_rejects_reversed_date_window(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("shared historical reader must not run for an invalid window")

    monkeypatch.setattr(production_read_model_api, "read_historical_bars", fail_if_called)
    app = create_app(Settings(DATABASE_URL="postgresql+psycopg://unused/unused"))

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get(
            "/api/v2/stocks/2330/price-history",
            params={"from": "2026-08-14", "to": "2026-08-03"},
        )

    assert response.status_code == 422
