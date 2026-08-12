from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

import topicpilot_api.main as main_module
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
