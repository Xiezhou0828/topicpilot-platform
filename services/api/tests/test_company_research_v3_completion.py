from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from topicpilot_api.config import Settings
from topicpilot_api.financial_research.contract import (
    ResearchClaim,
    ResearchEvidence,
    ResearchVersion,
)
from topicpilot_api.financial_research.forecast import advance_forecast_state, build_forecast_run
from topicpilot_api.financial_research.real_preview import build_real_financial_preview_store
from topicpilot_api.financial_research.reconciliation import reconcile_reported_line
from topicpilot_api.financial_research.research_contract import project_public_safe
from topicpilot_api.main import create_app


def test_1303_q1_eps_bridge_matches_official_reported_eps() -> None:
    app = create_app(Settings(real_financial_preview=True))
    response = TestClient(app).get("/api/v2/stocks/1303/eps-bridge")

    assert response.status_code == 200
    record = next(
        item for item in response.json()["records"] if item["period_label"] == "2026Q1_YTD"
    )
    assert record["parent_net_income"] == "14254717000"
    assert record["weighted_average_basic_shares"] == "7930822000"
    assert record["reported_basic_eps"] == "1.80"
    assert record["recomputed_basic_eps"] == "1.80"
    assert record["status"] == "RECOMPUTED_MATCH"


def test_1314_and_1319_only_claim_eps_bridge_for_same_period_shares() -> None:
    store = build_real_financial_preview_store()
    cpdc = store.eps_bridge("1314")
    tyg = store.eps_bridge("1319")
    assert cpdc.records and tyg.records
    assert {
        record.period_label: record.status
        for record in cpdc.records
        if record.period_label in {"2026Q1_YTD", "2026Q2_YTD"}
    } == {
        "2026Q1_YTD": "RECOMPUTED_MATCH",
        "2026Q2_YTD": "RECOMPUTED_MATCH",
    }
    q2 = next(record for record in cpdc.records if record.period_label == "2026Q2_YTD")
    assert q2.source_note_status == "MANUAL_REVIEW_REQUIRED"
    assert q2.period_type == "half_year"
    annual = next(record for record in tyg.records if record.period_label == "FY2025")
    assert annual.status == "RECOMPUTED_MATCH"
    assert annual.weighted_average_basic_shares == Decimal("591477000")
    assert all(
        record.status != "RECOMPUTED_MATCH"
        for record in tyg.records
        if record.period_label in {"2026Q1_YTD", "2026Q2_YTD"}
    )


def test_1314_reconciliation_preserves_8426000_variance() -> None:
    result = reconcile_reported_line(
        ticker="1314",
        period_label="2026Q2_YTD",
        line_item="net_income",
        statement_value=Decimal("-1985639000"),
        reported_value=Decimal("-1994065000"),
    )
    assert result.status == "UNRESOLVED"
    assert result.variance == Decimal("8426000")


def test_forecast_requires_explicit_assumptions_and_stops_at_review_pending() -> None:
    blocked = build_forecast_run("1303", {"base_revenue": Decimal("100")})
    assert blocked.state == "DRAFT"
    assert blocked.outputs == []
    assert blocked.missing_prerequisites

    assumptions = {
        "base_revenue": Decimal("100"),
        "revenue_growth": Decimal("0.05"),
        "gross_margin": Decimal("0.20"),
        "operating_margin": Decimal("0.10"),
        "tax_rate": Decimal("0.20"),
        "weighted_average_shares": Decimal("10"),
    }
    run = build_forecast_run("1303", assumptions)
    assert run.state == "CALCULATED"
    assert len(run.outputs) == 7
    run = advance_forecast_state(run, "VALIDATED")
    run = advance_forecast_state(run, "REVIEW_PENDING")
    assert run.state == "REVIEW_PENDING"


def test_public_projection_filters_unapproved_topic_and_unapproved_evidence() -> None:
    version = ResearchVersion(
        research_id="R-1303",
        ticker="1303",
        version="v3.0.0",
        status="PUBLISHED",
        created_at=datetime(2026, 10, 12),
        evidence=[
            ResearchEvidence(
                evidence_id="E-APPROVED",
                source_id="SRC-OFFICIAL",
                source_title="官方報告",
                claim_scope="公司概況",
                status="VERIFIED",
                rights_status="APPROVED",
            ),
            ResearchEvidence(
                evidence_id="E-PENDING",
                source_id="SRC-UNKNOWN",
                source_title="待審來源",
                claim_scope="估值",
                status="PENDING_REVIEW",
                rights_status="UNVERIFIED",
            ),
        ],
        claims=[
            ResearchClaim(
                claim_id="C-OK",
                text_zh_tw="公司定位為多事業材料供應商。",
                evidence_ids=["E-APPROVED"],
                review_status="APPROVED",
            ),
            ResearchClaim(
                claim_id="C-TOPIC",
                text_zh_tw="候選題材建議。",
                evidence_ids=["E-APPROVED"],
                review_status="APPROVED",
                is_formal_topic_authority=True,
            ),
            ResearchClaim(
                claim_id="C-PENDING",
                text_zh_tw="尚待證實的估值觀點。",
                evidence_ids=["E-PENDING"],
                review_status="APPROVED",
            ),
        ],
    )
    projection = project_public_safe(version)
    assert [claim.claim_id for claim in projection.approved_claims] == ["C-OK"]
    assert "估值" not in " ".join(claim.text_zh_tw for claim in projection.approved_claims)
