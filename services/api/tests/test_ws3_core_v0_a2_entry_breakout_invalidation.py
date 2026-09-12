from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from topicpilot_api.research.ws3_core_v0_a2_entry_breakout_invalidation import (
    ENTRY_PROXIES,
    _build_events,
    _entry_for_proxy,
    _horizon_metrics,
    _reference_path,
    _segment,
    build_a1_forward_validation_contract,
)


def _items() -> tuple[list[dict[str, object]], list[date]]:
    dates = [date(2026, 5, 1) + timedelta(days=index) for index in range(14)]
    items = []
    for index, trading_date in enumerate(dates):
        items.append(
            {
                "trading_date": trading_date,
                "open": Decimal("100") if index != 4 else Decimal("106"),
                "high": Decimal("101") if index < 3 else Decimal("110"),
                "low": Decimal("99") if index != 4 else Decimal("98"),
                "close": Decimal("100") if index < 3 else Decimal("105"),
                "volume": Decimal("1000"),
            }
        )
    return items, dates


def _row(
    index: int, dates: list[date], *, instrument_id: str = "instrument-1"
) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "stock_code": "TEST",
        "market": "TPE",
        "signal_date": dates[index],
        "index": index,
        "close": Decimal("105"),
        "ma60": Decimal("90"),
        "candidate_record_id": f"record-{index}",
        "candidate_source_lineage": ["source:TEST"],
        "event_excluded_horizons": set(),
        "candidate_inputs": {
            "reference_value": "100",
            "reference_policy_id": "PRIOR_20_ACCEPTED_SESSION_HIGH",
            "reference_birth_session": dates[0].isoformat(),
            "reference_age_sessions": "10",
            "gap_up": "False",
        },
    }


def _event() -> dict[str, object]:
    items, dates = _items()
    row = _row(3, dates)
    events = _build_events(
        [_row(2, dates)], [row], {"instrument-1": {"items": items, "dates": dates}}
    )
    event = events[0]
    _reference_path(event)
    return event


def test_a2_contiguous_observations_are_deduplicated_before_outcomes() -> None:
    items, dates = _items()
    rows = [_row(3, dates), _row(4, dates), _row(7, dates)]
    events = _build_events(
        [_row(2, dates)], rows, {"instrument-1": {"items": items, "dates": dates}}
    )
    assert len(events) == 2
    assert events[0]["observation_count"] == 2
    assert events[1]["observation_count"] == 1


def test_breakout_reference_and_entry_extensions_are_pit_safe() -> None:
    event = _event()
    assert event["reference"] == 100
    assert event["reference_policy_id"] == "PRIOR_20_ACCEPTED_SESSION_HIGH"
    assert _entry_for_proxy(event, "THEORETICAL_REFERENCE_FILL")["entry_extension_pct"] == 0
    assert _entry_for_proxy(event, "OBSERVABLE_A2_CLOSE")["entry_extension_pct"] == pytest.approx(
        0.05
    )
    assert (
        _entry_for_proxy(event, "NEXT_SESSION_OPEN")["execution_assumption"]
        == "NEXT_SESSION_OPEN_FILL"
    )


def test_all_required_entry_proxies_are_declared() -> None:
    assert ENTRY_PROXIES == (
        "THEORETICAL_REFERENCE_FILL",
        "OBSERVABLE_A2_CLOSE",
        "NEXT_SESSION_OPEN",
        "NEXT_SESSION_CLOSE",
    )


def test_mfe_mae_use_future_canonical_sessions_after_entry() -> None:
    event = _event()
    metrics = _horizon_metrics(event, "OBSERVABLE_A2_CLOSE", 3)
    assert metrics["status"] == "AVAILABLE"
    assert metrics["mfe"] == pytest.approx(110 / 105 - 1)
    assert metrics["mae"] < 0
    assert metrics["forward_return"] == 0


def test_reference_loss_and_reclaim_are_distinct_path_events() -> None:
    event = _event()
    assert event["reference_loss"] is True
    assert event["reference_close_loss"] is False
    assert event["reference_reclaimed"] is True
    assert event["sessions_to_reference_loss"] == 1
    assert event["sessions_to_reclaim"] == 1


def test_time_segments_are_frozen_chronological_segments() -> None:
    assert _segment(date(2026, 6, 30)) == "DEVELOPMENT_AVAILABLE"
    assert _segment(date(2026, 7, 15)) == "VALIDATION"
    assert _segment(date(2026, 8, 5)) == "HOLDOUT"


def test_a1_forward_contract_preserves_exact_seven_candidates() -> None:
    path = Path(
        "reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818/"
        "a1-quality-filter-confirmatory-freeze.json"
    )
    contract = build_a1_forward_validation_contract(path)
    assert contract["status"] == "FROZEN_AWAITING_FORWARD_EVIDENCE"
    assert contract["candidate_count"] == 7
    assert len(contract["candidates"]) == 7
    assert contract["threshold_retuning_performed"] is False
    assert contract["thresholds_immutable_until_next_confirmatory_review"] is True


def test_event_formation_definition_excludes_future_outcomes() -> None:
    event = _event()
    assert event["signal_date"] < event["_dates"][-1]
    assert "forward_return" not in event
    assert "mfe" not in event
    assert "mae" not in event
