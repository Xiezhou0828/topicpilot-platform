from __future__ import annotations

from pathlib import Path

from topicpilot_api.market_calendar_remediation import (
    MARKET_CALENDAR_REMEDIATION_WRITE_SET,
    NON_CALENDAR_CONTEXT_WRITE_SET,
)


def test_market_calendar_write_boundary_is_explicit():
    assert {"markets.calendar_code"} == MARKET_CALENDAR_REMEDIATION_WRITE_SET
    assert frozenset() == NON_CALENDAR_CONTEXT_WRITE_SET


def test_calendar_remediation_has_no_generic_or_non_calendar_mutation_path():
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "topicpilot_api"
        / "market_calendar_remediation.py"
    ).read_text(encoding="utf-8")
    assert "delete(" not in source
    assert "insert(" not in source
    assert "market.name =" not in source
    assert "market.exchange_code =" not in source
    assert "market.timezone =" not in source
    assert "instrument." not in source


def test_bootstrap_plan_and_activation_share_market_context_validator():
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "topicpilot_api"
        / "reference_data"
        / "bootstrap.py"
    ).read_text(encoding="utf-8")
    assert source.count("validate_market_context(market, row)") == 2
    for field in ("code", "name", "exchange", "timezone", "calendar"):
        assert f"market {{row['code']}} {field}" in source
