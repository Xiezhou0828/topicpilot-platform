from __future__ import annotations

from datetime import date

from topicpilot_api.market_data.readiness import (
    BLOCKED_AUTHORITY_CONFLICT,
    BLOCKED_PROVIDER_DATE_AUTHORITY,
    BLOCKED_REQUIRED_DATA,
    WAIT_PROVIDER_NOT_READY,
    WAIT_PROVIDER_PUBLICATION_LAG,
    OperationalReadiness,
    classify_eod_readiness,
    classify_provider_error,
)

TARGET = date(2026, 10, 6)
PREVIOUS = date(2026, 10, 5)


def test_valid_official_target_session_is_ready_without_finality_metadata():
    decision = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=TARGET,
        payload_valid=True,
        required_rows_present=True,
        required_ohlcv_parseable=True,
        minimum_coverage=True,
    )

    assert decision.state is OperationalReadiness.READY
    assert decision.reason_code == "OPERATIONAL_EOD_READY"


def test_explicit_not_ready_is_wait():
    decision = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=None,
        payload_valid=False,
        required_rows_present=False,
        required_ohlcv_parseable=False,
        minimum_coverage=False,
        explicit_not_ready=True,
    )

    assert decision.state is OperationalReadiness.WAIT
    assert decision.reason_code == WAIT_PROVIDER_NOT_READY


def test_previous_valid_session_during_publication_lag_is_wait():
    decision = classify_provider_error(
        "PROVIDER_DATE_MISMATCH",
        target_session=TARGET,
        served_session=PREVIOUS,
        previous_session=PREVIOUS,
    )

    assert decision.state is OperationalReadiness.WAIT
    assert decision.reason_code == WAIT_PROVIDER_PUBLICATION_LAG


def test_unexplained_date_mismatch_is_blocked():
    decision = classify_provider_error(
        "PROVIDER_DATE_MISMATCH",
        target_session=TARGET,
        served_session=date(2026, 10, 7),
        previous_session=PREVIOUS,
    )

    assert decision.state is OperationalReadiness.BLOCKED
    assert decision.reason_code == BLOCKED_PROVIDER_DATE_AUTHORITY


def test_malformed_payload_and_incomplete_coverage_are_blocked():
    malformed = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=TARGET,
        payload_valid=False,
        required_rows_present=True,
        required_ohlcv_parseable=False,
        minimum_coverage=True,
    )
    incomplete = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=TARGET,
        payload_valid=True,
        required_rows_present=True,
        required_ohlcv_parseable=True,
        minimum_coverage=False,
    )

    assert malformed.state is OperationalReadiness.BLOCKED
    assert malformed.reason_code == BLOCKED_REQUIRED_DATA
    assert incomplete.state is OperationalReadiness.BLOCKED
    assert incomplete.reason_code == BLOCKED_REQUIRED_DATA


def test_material_authority_conflict_is_blocked():
    decision = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=TARGET,
        payload_valid=True,
        required_rows_present=True,
        required_ohlcv_parseable=True,
        minimum_coverage=True,
        authority_conflict=True,
    )

    assert decision.state is OperationalReadiness.BLOCKED
    assert decision.reason_code == BLOCKED_AUTHORITY_CONFLICT


def test_wait_provider_not_ready_can_transition_to_ready():
    waiting = classify_provider_error("EXCHANGE_NOT_READY")
    ready = classify_eod_readiness(
        source_official=True,
        retrieval_succeeded=True,
        target_session=TARGET,
        served_session=TARGET,
        payload_valid=True,
        required_rows_present=True,
        required_ohlcv_parseable=True,
        minimum_coverage=True,
    )

    assert waiting.state is OperationalReadiness.WAIT
    assert ready.state is OperationalReadiness.READY
