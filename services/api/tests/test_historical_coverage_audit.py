from datetime import date

import pytest

from topicpilot_api.market_data.coverage_audit import (
    AuditArtifacts,
    CalendarException,
    CoverageAuditError,
    InstrumentIdentity,
    LifecycleEvent,
    build_audit_artifacts,
    write_artifacts,
)


def _identity(*, valid_from: date | None = None) -> InstrumentIdentity:
    return InstrumentIdentity(
        instrument_id="instrument-2330",
        instrument_code="2330",
        market_code="TPE",
        calendar_code="TW_MARKET",
        valid_from=valid_from,
        valid_to=None,
    )


def _row(day: str, *, close: str | None = "100", covered: bool = True) -> dict:
    return {
        "instrument_id": "instrument-2330",
        "trade_date": date.fromisoformat(day),
        "close": close,
        "covered": covered,
        "status_code": "AVAILABLE" if close is not None else "UNKNOWN",
        "source_code": "TWSE_OFFICIAL_DAILY",
    }


def test_audit_classifies_weekend_holiday_lifecycle_and_unknown_gaps() -> None:
    artifacts = build_audit_artifacts(
        requested_from=date(2026, 8, 7),
        requested_to=date(2026, 8, 11),
        identities=(_identity(),),
        observations=(_row("2026-08-07"), _row("2026-08-11")),
        lifecycle_events=(
            LifecycleEvent("instrument-2330", "SUSPENDED", date(2026, 8, 10), None),
        ),
        calendar_exceptions=(CalendarException("TW_MARKET", date(2026, 8, 10), "HOLIDAY"),),
    )

    classes = {(row["trade_date"], row["gap_class"]) for row in artifacts.gap_classification}
    assert ("2026-08-08", "MARKET_NO_SESSION") in classes
    assert ("2026-08-09", "MARKET_NO_SESSION") in classes
    assert ("2026-08-10", "LIFECYCLE_SUSPENDED") in classes
    assert artifacts.coverage_by_instrument[0]["ma20_ready"] == "NO"
    assert artifacts.coverage_by_instrument[0]["coverage_state"] == "COMPLETE"


def test_audit_never_treats_missing_close_as_priced_or_zero() -> None:
    artifacts = build_audit_artifacts(
        requested_from=date(2026, 8, 7),
        requested_to=date(2026, 8, 7),
        identities=(_identity(),),
        observations=(_row("2026-08-07", close=None, covered=False),),
    )

    assert artifacts.coverage_by_date[0]["priced_instrument_count"] == 0
    assert artifacts.coverage_by_date[0]["covered_instrument_count"] == 0
    assert artifacts.gap_classification[0]["gap_class"] == "OBSERVED_UNEXPLAINED_NO_DATA"
    assert artifacts.gap_classification[0]["adjustment_state"] == "UNKNOWN"


def test_audit_rejects_duplicate_canonical_identity_and_bounds_window() -> None:
    with pytest.raises(CoverageAuditError, match="DUPLICATE_CANONICAL_KEY"):
        build_audit_artifacts(
            requested_from=date(2026, 8, 7),
            requested_to=date(2026, 8, 7),
            identities=(_identity(),),
            observations=(_row("2026-08-07"), _row("2026-08-07")),
        )

    with pytest.raises(CoverageAuditError, match="AUDIT_WINDOW_TOO_LARGE"):
        build_audit_artifacts(
            requested_from=date(2010, 1, 1),
            requested_to=date(2026, 8, 7),
            identities=(_identity(),),
            observations=(),
        )


def test_audit_respects_identity_listing_effective_date() -> None:
    artifacts = build_audit_artifacts(
        requested_from=date(2026, 8, 7),
        requested_to=date(2026, 8, 11),
        identities=(_identity(valid_from=date(2026, 8, 11)),),
        observations=(_row("2026-08-11"),),
    )

    rows = artifacts.coverage_by_instrument
    assert rows[0]["observed_count"] == 1
    assert rows[0]["primary_gap_class"] == "INSTRUMENT_NOT_LISTED"


def test_empty_runtime_snapshot_still_emits_stable_csv_schemas(tmp_path) -> None:
    write_artifacts(
        tmp_path,
        AuditArtifacts(
            coverage_by_date=(),
            coverage_by_instrument=(),
            gap_classification=(),
            summary={},
        ),
    )

    assert (tmp_path / "historical-coverage-by-date.csv").read_text().startswith("trade_date,")
    assert (tmp_path / "historical-coverage-by-instrument.csv").read_text().startswith(
        "market_code,"
    )
    assert (tmp_path / "gap-classification.csv").read_text().startswith("trade_date,")
