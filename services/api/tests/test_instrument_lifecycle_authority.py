from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from topicpilot_api.instrument_lifecycle_authority import (
    InstrumentLifecycleAuthority,
    LifecycleAuthorityError,
    LifecycleEventRecord,
    TradingExpectation,
    decide_missing_bar,
    load_corporate_action_events,
)


def event(
    code: str,
    status: str,
    start: str,
    end: str | None = None,
    *,
    market: str = "TWO",
    evidence: str | None = "fixture-evidence",
) -> LifecycleEventRecord:
    return LifecycleEventRecord(
        market_code=market,
        instrument_code=code,
        status_code=status,
        effective_from=date.fromisoformat(start),
        effective_to=date.fromisoformat(end) if end else None,
        evidence_id=evidence,
        source_url="https://authority.example.test/event",
        reason=f"fixture {status}",
    )


def test_date_effective_suspension_resume_and_termination_are_deterministic() -> None:
    authority = InstrumentLifecycleAuthority(
        known_identities={("TWO", "5371")},
        lifecycle_events=(
            event("5371", "SUSPENDED", "2026-08-24", "2026-09-02"),
            event("5371", "TERMINATED", "2026-09-03", evidence="termination-evidence"),
        ),
        authority_version="fixture-v1",
    )

    before = authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 21))
    during = authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 24))
    last_suspended = authority.resolve_trading_expectation(
        "TWO", "5371", date(2026, 9, 2)
    )
    terminated = authority.resolve_trading_expectation("TWO", "5371", date(2026, 9, 3))

    assert before.expectation is TradingExpectation.EXPECTED_TO_TRADE
    assert during.expectation is TradingExpectation.LEGAL_NO_TRADE
    assert during.lifecycle_status == "SUSPENDED"
    assert during.evidence_id == "fixture-evidence"
    assert last_suspended.expectation is TradingExpectation.LEGAL_NO_TRADE
    assert terminated.expectation is TradingExpectation.TERMINATED
    assert terminated.evidence_id == "termination-evidence"
    assert during == authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 24))


def test_expected_missing_bar_fails_closed_and_legal_no_trade_does_not_make_a_bar() -> None:
    authority = InstrumentLifecycleAuthority(
        known_identities={("TWO", "6241"), ("TWO", "5371")},
        lifecycle_events=(event("5371", "SUSPENDED", "2026-08-24", "2026-09-02"),),
    )
    expected = authority.resolve_trading_expectation("TWO", "6241", date(2026, 8, 20))
    missing = decide_missing_bar(expected, has_observation=False, has_priced_bar=False)
    assert expected.expectation is TradingExpectation.EXPECTED_TO_TRADE
    assert missing.disposition == "MISSING_MARKET_DATA"
    assert missing.status_code == "UNKNOWN"
    assert not missing.covered

    no_trade = authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 24))
    covered = decide_missing_bar(no_trade, has_observation=False, has_priced_bar=False)
    assert covered.disposition == "COVERED_BY_LIFECYCLE_AUTHORITY"
    assert covered.status_code == "SUSPENDED"
    assert covered.covered
    assert not covered.provider_conflict
    conflict = decide_missing_bar(no_trade, has_observation=True, has_priced_bar=False)
    assert conflict.provider_conflict


def test_corporate_action_does_not_become_legal_no_trade() -> None:
    authority = InstrumentLifecycleAuthority(
        known_identities={("TPE", "1563")},
        corporate_events=(
            type(
                "Event",
                (),
                {
                    "market_code": "TPE",
                    "instrument_code": "1563",
                    "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
                },
            )(),
        ),
    )
    resolution = authority.resolve_trading_expectation("TPE", "1563", date(2026, 8, 28))
    assert resolution.expectation is TradingExpectation.EXPECTED_TO_TRADE
    assert authority.corporate_events_for("TPE", "1563")[0].event_type == (
        "CASH_DIVIDEND_EX_DIVIDEND"
    )


def test_market_aware_identity_and_unknown_identity_are_isolated() -> None:
    authority = InstrumentLifecycleAuthority(
        known_identities={("TPE", "3707"), ("TWO", "3707")},
        lifecycle_events=(event("3707", "SUSPENDED", "2026-08-24", market="TPE"),),
    )
    assert authority.resolve_trading_expectation("TPE", "3707", date(2026, 8, 24)).expectation == (
        TradingExpectation.LEGAL_NO_TRADE
    )
    assert authority.resolve_trading_expectation("TWO", "3707", date(2026, 8, 24)).expectation == (
        TradingExpectation.EXPECTED_TO_TRADE
    )
    unknown = authority.resolve_trading_expectation("TWO", "9999", date(2026, 8, 24))
    assert unknown.expectation is TradingExpectation.UNKNOWN


def test_future_listing_and_expired_event_boundaries() -> None:
    authority = InstrumentLifecycleAuthority(
        known_identities={("TPE", "NEW")},
        lifecycle_events=(event("NEW", "LISTED", "2026-09-01", market="TPE"),),
    )
    assert authority.resolve_trading_expectation("TPE", "NEW", date(2026, 8, 31)).expectation == (
        TradingExpectation.NOT_YET_LISTED
    )
    assert authority.resolve_trading_expectation("TPE", "NEW", date(2026, 9, 1)).expectation == (
        TradingExpectation.EXPECTED_TO_TRADE
    )


def test_duplicate_rows_are_idempotent_but_conflicting_overlap_is_rejected() -> None:
    row = event("6241", "SUSPENDED", "2026-08-18", "2026-08-24")
    authority = InstrumentLifecycleAuthority(
        known_identities={("TWO", "6241")},
        lifecycle_events=(row, row),
    )
    assert len(authority.lifecycle_events) == 1
    with pytest.raises(LifecycleAuthorityError, match="overlapping lifecycle statuses"):
        InstrumentLifecycleAuthority(
            known_identities={("TWO", "6241")},
            lifecycle_events=(
                row,
                event("6241", "TERMINATED", "2026-08-20", "2026-08-24", evidence="other"),
            ),
        )


def test_orm_shaped_lifecycle_rows_receive_the_market_aware_identity_from_join() -> None:
    authority = InstrumentLifecycleAuthority.from_reference_rows(
        known_identities={("TWO", "5371")},
        identity=("TWO", "5371"),
        rows=[
            {
                "status_code": "SUSPENDED",
                "effective_from": date(2026, 8, 24),
                "effective_to": date(2026, 9, 2),
                "evidence_id": "orm-shaped-evidence",
                "source_url": "https://authority.example.test/orm-shaped",
            }
        ],
    )
    resolution = authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 24))
    assert resolution.expectation is TradingExpectation.LEGAL_NO_TRADE
    assert resolution.identity == ("TWO", "5371")


def test_existing_bundle_and_event_artifact_are_read_when_present() -> None:
    repo = Path(__file__).resolve().parents[3]
    bundle_path = repo / "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
    event_path = repo / (
        "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
        "/REC-A1-CA-EVENTS-V0.json"
    )
    if not bundle_path.exists() or not event_path.exists():
        pytest.skip("owner-provided lifecycle/event artifacts are not present in this checkout")

    events = load_corporate_action_events(event_path)
    authority = InstrumentLifecycleAuthority.from_bundle_path(
        bundle_path,
        corporate_event_path=event_path,
    )
    assert any(
        event.market_code == "TPE"
        and event.instrument_code == "1563"
        and event.event_type == "CASH_DIVIDEND_EX_DIVIDEND"
        for event in events
    )
    assert authority.resolve_trading_expectation("TWO", "5371", date(2026, 8, 24)).expectation == (
        TradingExpectation.LEGAL_NO_TRADE
    )
    assert authority.resolve_trading_expectation("TPE", "1563", date(2026, 8, 28)).expectation == (
        TradingExpectation.LEGAL_NO_TRADE
    )
    assert authority.resolve_trading_expectation("TWO", "6241", date(2026, 8, 20)).expectation == (
        TradingExpectation.LEGAL_NO_TRADE
    )
