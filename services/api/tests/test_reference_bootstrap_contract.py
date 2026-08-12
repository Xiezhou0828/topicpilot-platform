from __future__ import annotations

from pathlib import Path

from topicpilot_api.reference_data.bootstrap import (
    NON_REFERENCE_WRITE_SET,
    REFERENCE_WRITE_SET,
)


def test_reference_bootstrap_has_explicit_reference_only_write_set():
    assert frozenset() == NON_REFERENCE_WRITE_SET
    assert frozenset(
        {
            "markets",
            "instruments",
            "reference_registry_sets",
            "reference_currencies",
            "reference_timezones",
            "reference_sessions",
            "reference_trading_statuses",
            "reference_adjustments",
            "reference_calendar_dates",
        }
    ) == REFERENCE_WRITE_SET


def test_reference_bootstrap_source_does_not_import_non_reference_domains():
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "topicpilot_api"
        / "reference_data"
        / "bootstrap.py"
    ).read_text(encoding="utf-8")
    assert "topicpilot_api.topic" not in source
    assert "canonical_observations" not in source
    assert "raw_market_observations" not in source
    assert "lifecycle" not in source
    assert "opportunity" not in source
