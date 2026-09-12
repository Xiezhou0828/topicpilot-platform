from __future__ import annotations

import inspect
from datetime import date

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import (
    MAX_HISTORICAL_BAR_LIMIT,
    _validate_window,
    attach_bounded_continuity_evidence,
    read_historical_bars,
)


def _read(
    postgres_engine: Engine,
    code: str,
    market: str,
    from_date: date = date(2026, 2, 2),
    to_date: date = date(2026, 8, 13),
    limit: int = MAX_HISTORICAL_BAR_LIMIT,
) -> dict:
    with postgres_engine.connect() as connection, Session(connection) as session:
        return read_historical_bars(
            session,
            code,
            from_date,
            to_date,
            market,
            limit,
        )


def test_history_window_is_bounded_and_not_silently_reversed() -> None:
    with pytest.raises(ValueError, match="on or after"):
        _validate_window(date(2026, 8, 13), date(2026, 2, 2), 200)
    with pytest.raises(ValueError, match="between 1 and 200"):
        _validate_window(date(2026, 2, 2), date(2026, 8, 13), 201)


def test_history_read_path_does_not_reference_legacy_ohlcv_table() -> None:
    source = inspect.getsource(read_historical_bars)
    assert "market_data_ohlcv" not in source
    assert "canonical_observations" in source
    assert "reference_instrument_lifecycles" in source


def test_lifecycle_attachment_is_partial_and_never_proves_empty_event_coverage() -> None:
    result = attach_bounded_continuity_evidence(
        {
            "code": "6806",
            "market": "TPE",
            "requested_from": date(2026, 2, 2),
            "requested_to": date(2026, 8, 13),
            "lifecycle": {
                "status_code": "DELISTED",
                "effective_from": date(2026, 6, 23),
                "effective_to": None,
                "evidence_id": "lifecycle-6806-20260623",
            },
        }
    )

    envelope = result["continuity_evidence"]["default"]
    assert envelope["coverage_state"] == "PARTIAL_UNKNOWN"
    assert envelope["coverage_complete"] is False
    assert envelope["known_events"][0]["effective_date"] == date(2026, 6, 23)
    assert envelope["source_lineage"]["carrier"] == (
        "topicpilot.reference_instrument_lifecycles"
    )


def test_missing_lifecycle_keeps_runtime_continuity_unknown() -> None:
    result = attach_bounded_continuity_evidence(
        {"code": "2330", "market": "TPE", "lifecycle": None}
    )

    assert result["continuity_evidence"] is None


@pytest.mark.postgres
def test_tpe_2330_canonical_history_is_bounded_and_lineage_complete(
    postgres_engine: Engine,
) -> None:
    result = _read(postgres_engine, "2330", "TPE")

    assert result["status"] == "AVAILABLE"
    assert result["market"] == "TPE"
    assert result["point_count"] == 126
    assert result["returned_from"] == date(2026, 2, 2)
    assert result["returned_to"] == date(2026, 8, 13)
    assert result["has_more"] is False
    assert len(result["items"]) <= 200
    assert result["items"] == sorted(
        result["items"],
        key=lambda item: (item["trading_date"], item["observed_at"]),
    )
    item = result["items"][0]
    assert item["quality_state"] == "ACCEPTED"
    assert item["adjustment_state"] == "UNKNOWN"
    assert item["source"]["source_code"] == "TWSE_OFFICIAL_DAILY"
    assert item["source"]["adapter_version"]
    assert item["normalization_contract_version"]
    assert item["mapping_policy_version"]
    assert item["reference_data_version"]


@pytest.mark.postgres
def test_two_6488_canonical_history_uses_same_authority(postgres_engine: Engine) -> None:
    result = _read(postgres_engine, "6488", "TWO")

    assert result["point_count"] == 126
    assert result["returned_from"] == date(2026, 2, 2)
    assert result["returned_to"] == date(2026, 8, 13)
    assert {item["source_code"] for item in result["items"]} == {"TPEX_OFFICIAL_DAILY"}


@pytest.mark.postgres
def test_6806_lifecycle_cutoff_excludes_post_termination_bars(
    postgres_engine: Engine,
) -> None:
    result = _read(postgres_engine, "6806", "TPE")

    assert result["point_count"] == 88
    assert result["returned_to"] == date(2026, 6, 22)
    assert result["lifecycle"]["status_code"] == "DELISTED"
    assert result["lifecycle"]["effective_from"] == date(2026, 6, 23)
    assert all(item["trading_date"] < date(2026, 6, 23) for item in result["items"])


@pytest.mark.postgres
def test_unauthorized_symbol_has_no_history_fallback(postgres_engine: Engine) -> None:
    from topicpilot_api.problems import NotFoundProblem

    with pytest.raises(NotFoundProblem):
        _read(postgres_engine, "3059", "TPE")


@pytest.mark.postgres
def test_empty_range_is_explicitly_unavailable(postgres_engine: Engine) -> None:
    result = _read(
        postgres_engine,
        "2330",
        "TPE",
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 31),
    )

    assert result["status"] == "UNAVAILABLE"
    assert result["coverage_state"] == "EMPTY"
    assert result["items"] == []
    assert result["availability_reason"] == "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"
