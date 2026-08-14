from datetime import date

import pytest

from topicpilot_api.instrument_universe import (
    InstrumentLifecycle,
    InstrumentUniverseRow,
    LifecycleValidationError,
    build_date_effective_instrument_universe,
    evaluate_instrument_eligibility,
    is_instrument_eligible_on_date,
)


def _delisted_row(
    *,
    effective_from: date = date(2026, 6, 23),
    effective_to: date | None = None,
    status_code: str = "DELISTED",
) -> InstrumentUniverseRow:
    return InstrumentUniverseRow(
        market_code="TPE",
        instrument_code="6806",
        instrument_type="EQUITY",
        is_active=True,
        lifecycle_events=(
            InstrumentLifecycle(
                status_code=status_code,
                effective_from=effective_from,
                effective_to=effective_to,
                evidence_id="evidence-6806",
            ),
        ),
    )


def test_delisting_boundary_is_inclusive_and_date_effective():
    row = _delisted_row()

    assert is_instrument_eligible_on_date(row, date(2026, 6, 22)) is True
    assert is_instrument_eligible_on_date(row, date(2026, 6, 23)) is False
    assert is_instrument_eligible_on_date(row, date(2026, 8, 13)) is False


def test_future_validity_is_not_eligible_before_valid_from():
    row = InstrumentUniverseRow(
        market_code="TPE",
        instrument_code="FUTURE",
        instrument_type="EQUITY",
        is_active=True,
        valid_from=date(2026, 8, 14),
    )

    assert evaluate_instrument_eligibility(row, date(2026, 8, 13)).reason_code == (
        "INSTRUMENT_NOT_YET_VALID"
    )
    assert is_instrument_eligible_on_date(row, date(2026, 8, 14)) is True


@pytest.mark.parametrize(
    "row, message",
    [
        (
            InstrumentUniverseRow(
                "TPE",
                "BAD-RANGE",
                "EQUITY",
                True,
                valid_from=date(2026, 8, 14),
                valid_to=date(2026, 8, 13),
            ),
            "INVALID_INSTRUMENT_VALID_RANGE",
        ),
        (_delisted_row(status_code="UNKNOWN_LIFECYCLE"), "UNKNOWN_LIFECYCLE_STATUS"),
        (
            InstrumentUniverseRow(
                "TPE",
                "NO-EVIDENCE",
                "EQUITY",
                True,
                lifecycle_events=(
                    InstrumentLifecycle("DELISTED", date(2026, 6, 23), evidence_id=None),
                ),
            ),
            "LIFECYCLE_EVIDENCE_ID_MISSING",
        ),
        (
            InstrumentUniverseRow(
                "TPE",
                "BAD-LIFECYCLE-RANGE",
                "EQUITY",
                True,
                lifecycle_events=(
                    InstrumentLifecycle(
                        "DELISTED",
                        date(2026, 8, 14),
                        effective_to=date(2026, 8, 13),
                        evidence_id="bad-range",
                    ),
                ),
            ),
            "INVALID_LIFECYCLE_VALID_RANGE",
        ),
    ],
)
def test_malformed_lifecycle_fails_closed(row, message):
    with pytest.raises(LifecycleValidationError, match=message):
        is_instrument_eligible_on_date(row, date(2026, 8, 13))


def test_expected_universe_excludes_lifecycle_event_without_deleting_physical_identity():
    rows = [
        _delisted_row(),
        InstrumentUniverseRow("TPE", "2330", "EQUITY", True),
        InstrumentUniverseRow("TWO", "6488", "EQUITY", True),
    ]

    assert build_date_effective_instrument_universe(
        rows, date(2026, 8, 13)
    ) == {"TPE": ("2330",), "TWO": ("6488",)}


def test_duplicate_identity_fails_closed():
    row = InstrumentUniverseRow("TPE", "2330", "EQUITY", True)
    with pytest.raises(LifecycleValidationError, match="DUPLICATE_INSTRUMENT_IDENTITY"):
        build_date_effective_instrument_universe([row, row], date(2026, 8, 13))
