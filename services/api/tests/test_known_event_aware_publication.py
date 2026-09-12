from __future__ import annotations

from datetime import date

from topicpilot_api.known_event_aware_publication import evaluate_known_event_lookup


def _history() -> dict:
    return {"market": "TPE", "code": "2330"}


def _lookup(*, events: list[dict], **overrides) -> dict:
    return {
        "lookup_state": "SUCCESS",
        "query_completed": True,
        "response_parsed": True,
        "identity_binding_valid": True,
        "normalization_valid": True,
        "known_events": events,
        "source_lineage": {"lineage_state": "VERSIONED", "source": "TEST"},
        **overrides,
    }


def test_missing_lookup_is_not_treated_as_no_event():
    result = evaluate_known_event_lookup(
        _history(),
        required_window={"start_session": date(2026, 1, 1), "end_session": date(2026, 1, 31)},
    )

    assert result["state"] == "EVENT_LOOKUP_UNAVAILABLE"


def test_successful_identity_bound_lookup_returns_no_known_match():
    result = evaluate_known_event_lookup(
        _history() | {"known_event_lookup": _lookup(events=[])},
        required_window={"start_session": date(2026, 1, 1), "end_session": date(2026, 1, 31)},
    )

    assert result["state"] == "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND"
    assert result["publication_allowed"] is True
    assert result["reason"] == "SUCCESSFUL_OFFICIAL_LOOKUP_NO_KNOWN_MATCH"


def test_verified_intersecting_event_is_not_ignored():
    result = evaluate_known_event_lookup(
        _history()
        | {
            "known_event_lookup": _lookup(
                events=[
                    {
                        "canonical_identity": "TPE:2330",
                        "effective_date": "2026-01-20",
                        "verified": True,
                        "handling": "EXCLUDE",
                    }
                ]
            )
        },
        required_window={"start_session": "2026-01-01", "end_session": "2026-01-31"},
    )

    assert result["state"] == "KNOWN_VERIFIED_BREAKING_EVENT_FOUND"
    assert result["publication_allowed"] is False
    assert result["known_events"][0]["effective_date"] == "2026-01-20"


def test_lookup_failure_is_fail_closed():
    result = evaluate_known_event_lookup(
        _history() | {"known_event_lookup": {"lookup_state": "TIMEOUT"}},
    )

    assert result["state"] == "EVENT_LOOKUP_UNAVAILABLE"
    assert result["publication_allowed"] is False
