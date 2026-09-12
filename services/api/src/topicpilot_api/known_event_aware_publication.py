"""Known-event-aware publication policy for the formal Technical V0 path.

The policy is deliberately narrower than affirmative no-event authority.  A
successful, identity-bound official event lookup may return
``NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND`` without claiming that no event ever
occurred.  Lookup failure remains unavailable for ordinary formal clearance,
but an otherwise valid raw technical result may carry an explicit bounded
limitation.  Malformed evidence, ambiguous identity, or a known breaking event
does not receive that limited-publication allowance.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

KNOWN_EVENT_AWARE_PUBLICATION_POLICY = "KNOWN_EVENT_AWARE_TECHNICAL_PUBLICATION"
KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION = "stock-technical-v0-known-event-aware.v2"

EVENT_LOOKUP_SUCCESS = "SUCCESS"
EVENT_LOOKUP_UNAVAILABLE = "EVENT_LOOKUP_UNAVAILABLE"
NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND = "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND"
KNOWN_VERIFIED_BREAKING_EVENT_FOUND = "KNOWN_VERIFIED_BREAKING_EVENT_FOUND"


def _history_identity(history: Mapping[str, Any]) -> str:
    return f"{str(history.get('market', '')).upper()}:{str(history.get('code', '')).strip()}"


def _failure(reason: str, *, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    bounded_limitation_allowed = reason == "EVENT_LOOKUP_UNAVAILABLE"
    return {
        "policy": KNOWN_EVENT_AWARE_PUBLICATION_POLICY,
        "policy_version": KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION,
        "state": EVENT_LOOKUP_UNAVAILABLE,
        "publication_allowed": False,
        "bounded_limitation_allowed": bounded_limitation_allowed,
        "event_match_state": None,
        "known_events": [],
        "reason": reason,
        "evidence": dict(evidence) if evidence is not None else None,
    }


def _legacy_lookup_from_continuity(
    continuity: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Recognize only the old explicit bounded fixture contract.

    This compatibility path does not turn UNKNOWN into PASS.  It only accepts
    an already explicit ``COVERED_NO_EVENT`` envelope used by frozen callers.
    """

    if not isinstance(continuity, Mapping):
        return None
    if (
        continuity.get("coverage_complete") is True
        and continuity.get("coverage_state") == "COVERED_NO_EVENT"
    ):
        return {
            "lookup_state": EVENT_LOOKUP_SUCCESS,
            "query_completed": True,
            "response_parsed": True,
            "identity_binding_valid": True,
            "normalization_valid": True,
            "event_match_state": NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
            "known_events": [],
            "source_lineage": continuity.get("source_lineage") or {
                "lineage_state": "VERSIONED"
            },
            "legacy_bounded_evidence": True,
        }
    return None


def evaluate_known_event_lookup(
    history: Mapping[str, Any],
    *,
    continuity_evidence: Mapping[str, Any] | None = None,
    required_window: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate an official event lookup without proving universal absence."""

    if not history.get("code") or str(history.get("market", "")).upper() not in {"TPE", "TWO"}:
        return _failure("INVALID_INSTRUMENT_IDENTITY")

    lookup = history.get("known_event_lookup")
    if lookup is None:
        lookup = _legacy_lookup_from_continuity(continuity_evidence)
    if not isinstance(lookup, Mapping):
        return _failure("EVENT_LOOKUP_UNAVAILABLE")

    if lookup.get("lookup_state", lookup.get("status")) != EVENT_LOOKUP_SUCCESS:
        return _failure("EVENT_LOOKUP_UNAVAILABLE", evidence=lookup)
    for field in (
        "query_completed",
        "response_parsed",
        "identity_binding_valid",
        "normalization_valid",
    ):
        if lookup.get(field) is not True:
            return _failure(f"EVENT_LOOKUP_{field.upper()}_INVALID", evidence=lookup)

    lineage = lookup.get("source_lineage")
    if not isinstance(lineage, Mapping) or lineage.get("lineage_state") != "VERSIONED":
        return _failure("EVENT_LOOKUP_SOURCE_LINEAGE_INVALID", evidence=lookup)

    events = lookup.get("known_events", lookup.get("events"))
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return _failure("EVENT_LOOKUP_EVENT_SET_INVALID", evidence=lookup)

    identity = _history_identity(history)
    normalized_events: list[dict[str, Any]] = []
    window_start = required_window.get("start_session") if required_window else None
    window_end = required_window.get("end_session") if required_window else None
    if isinstance(window_start, str):
        window_start = date.fromisoformat(window_start)
    if isinstance(window_end, str):
        window_end = date.fromisoformat(window_end)
    for event in events:
        if not isinstance(event, Mapping):
            return _failure("EVENT_LOOKUP_EVENT_RECORD_INVALID", evidence=lookup)
        event_identity = event.get("canonical_identity", event.get("instrument_identity"))
        if event_identity is not None and str(event_identity) != identity:
            return _failure("EVENT_LOOKUP_IDENTITY_AMBIGUOUS", evidence=lookup)
        if event.get("verified") is not True:
            return _failure("EVENT_LOOKUP_EVENT_NOT_VERIFIED", evidence=lookup)
        event_date = event.get("effective_date", event.get("primary_effective_date"))
        if event_date is None:
            return _failure("EVENT_LOOKUP_EVENT_DATE_INVALID", evidence=lookup)
        try:
            normalized_date = date.fromisoformat(str(event_date))
        except ValueError:
            return _failure("EVENT_LOOKUP_EVENT_DATE_INVALID", evidence=lookup)
        if (
            window_start is not None
            and window_end is not None
            and not window_start <= normalized_date <= window_end
        ):
            continue
        handling = str(event.get("handling", "UNAVAILABLE")).upper()
        if handling not in {"EXCLUDE", "CORRECT", "ANNOTATE", "UNAVAILABLE"}:
            return _failure("EVENT_LOOKUP_HANDLING_INVALID", evidence=lookup)
        normalized_events.append(
            {**dict(event), "effective_date": normalized_date.isoformat(), "handling": handling}
        )

    if normalized_events:
        return {
            "policy": KNOWN_EVENT_AWARE_PUBLICATION_POLICY,
            "policy_version": KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION,
            "state": KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
            "publication_allowed": False,
            "bounded_limitation_allowed": False,
            "event_match_state": KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
            "known_events": normalized_events,
            "reason": "KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING",
            "evidence": dict(lookup),
        }

    if lookup.get("event_match_state") not in {
        None,
        NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
    }:
        return _failure("EVENT_LOOKUP_MATCH_STATE_INVALID", evidence=lookup)
    return {
        "policy": KNOWN_EVENT_AWARE_PUBLICATION_POLICY,
        "policy_version": KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION,
        "state": NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
        "publication_allowed": True,
        "bounded_limitation_allowed": False,
        "event_match_state": NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
        "known_events": [],
        "reason": "SUCCESSFUL_OFFICIAL_LOOKUP_NO_KNOWN_MATCH",
        "evidence": dict(lookup),
    }


__all__ = [
    "EVENT_LOOKUP_SUCCESS",
    "EVENT_LOOKUP_UNAVAILABLE",
    "KNOWN_EVENT_AWARE_PUBLICATION_POLICY",
    "KNOWN_EVENT_AWARE_PUBLICATION_POLICY_VERSION",
    "KNOWN_VERIFIED_BREAKING_EVENT_FOUND",
    "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND",
    "evaluate_known_event_lookup",
]
