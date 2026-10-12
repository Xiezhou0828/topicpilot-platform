from __future__ import annotations

from fastapi.testclient import TestClient

from topicpilot_api.config import Settings
from topicpilot_api.main import create_app


def test_real_financial_preview_exposes_three_pilot_companies_read_only() -> None:
    app = create_app(Settings(real_financial_preview=True))
    client = TestClient(app)

    for ticker in ("1303", "1314", "1319"):
        summary = client.get(f"/api/v2/stocks/{ticker}/financial-summary")
        coverage = client.get(f"/api/v2/stocks/{ticker}/financial-coverage")
        statements = client.get(f"/api/v2/stocks/{ticker}/financial-statements")
        status = client.get(f"/api/v2/stocks/{ticker}/financial-research-status")

        assert summary.status_code == coverage.status_code == 200
        assert statements.status_code == status.status_code == 200
        assert summary.json()["status"] == "AVAILABLE"
        assert summary.json()["source_rights_status"] == "UNVERIFIED"
        assert summary.json()["metrics"]
        assert coverage.json()["available_periods"]
        assert statements.json()["annual"]
        assert statements.json()["ytd"]
        assert status.json()["publication_status"] == "NOT_PUBLISHED"
        assert status.json()["forecast_available"] is False


def test_real_preview_keeps_1314_tieout_and_eps_limitations_visible() -> None:
    app = create_app(Settings(real_financial_preview=True))
    summary = TestClient(app).get("/api/v2/stocks/1314/financial-summary").json()

    net_income = next(
        metric
        for metric in summary["metrics"]
        if metric["metric"] == "net_income" and metric["period_label"] == "2026Q2_YTD"
    )
    eps = next(
        metric
        for metric in summary["metrics"]
        if metric["metric"] == "basic_eps" and metric["period_label"] == "2026Q2_YTD"
    )
    assert net_income["validation_status"] == "PARTIAL"
    assert "8,426,000" in net_income["validation_note"]
    assert eps["validation_status"] == "PASS"
    assert "相符" in eps["validation_note"]


def test_default_app_does_not_activate_real_preview_read_model() -> None:
    response = TestClient(create_app()).get("/api/v2/stocks/1303/financial-summary")
    assert response.status_code == 200
    assert response.json()["status"] == "MISSING"
