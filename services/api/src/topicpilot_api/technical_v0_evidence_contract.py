"""Bounded Technical V0 evidence provider/consumer contract.

This module is deliberately a domain boundary, not an HTTP route or a
persistence layer.  It wraps the existing deterministic Technical V0 builder
with stable identity, version, availability, PIT, and lineage envelopes so a
future adapter can consume one bounded observation without depending on the
large E1 validation CSV.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from topicpilot_api.technical_publication import (
    TECHNICAL_CONTRACT_VERSION,
    TECHNICAL_INPUT_AUTHORITY,
    TECHNICAL_POLICY_VERSION,
    TECHNICAL_SPECS,
    build_technical_publication,
)

PROVIDER_CONTRACT_VERSION = "stock-technical-v0-formal-evidence-provider.v1"
CONSUMER_CONTRACT_VERSION = "stock-technical-v0-formal-evidence-consumer.v1"
EVIDENCE_SCHEMA_VERSION = "stock-technical-v0-formal-evidence.v1"
SOURCE_FOUNDATION_VERSION = "sdf-603-ohlcv-2y.v1"
SOURCE_FOUNDATION_SHA256 = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
SOURCE_FOUNDATION_AUTHORITY_SHA256 = (
    "fe1a51015d48d64b28007d36e291bed59085e7beacf5599ee5d5a35569747fcf"
)
SOURCE_FOUNDATION_INSTRUMENT_COUNT = 603
SOURCE_FOUNDATION_ACCEPTED_OHLCV_ROWS = 288_881
SOURCE_FOUNDATION_WINDOW = (date(2024, 8, 13), date(2026, 8, 13))

E1_ARTIFACT_SHA256 = "48bdc38b9da4e2ba7e298f5341d04ad5dd11475c6019df1ac80593c9858ec254"
E1_ARTIFACT_BYTES = 6_726_285_286
E1_ARTIFACT_ROLE = "REPRODUCIBILITY_VALIDATION_ARTIFACT"
E1_ARTIFACT_RUNTIME_DEPENDENCY = "NO"

CONTINUITY_STATES = {
    "CONTINUITY_PASS_BOUNDED",
    "CONTINUITY_FAIL",
    "CONTINUITY_UNKNOWN",
}
PUBLICATION_STATES = {
    "FORMAL",
    "FORMAL_WITH_LIMITATION",
    "UNAVAILABLE",
    "DEFERRED",
}
AVAILABILITY_STATES = {
    "AVAILABLE",
    "AVAILABLE_WITH_LIMITATION",
    "BLOCKED",
    "UNAVAILABLE",
    "ERROR",
}
FORMAL_INDICATOR_IDS = tuple(str(spec["indicator_id"]) for spec in TECHNICAL_SPECS)
_SPECS_BY_ID = {str(spec["indicator_id"]): spec for spec in TECHNICAL_SPECS}


class TechnicalV0ContractError(ValueError):
    """Raised when a provider/consumer request violates the contract."""


class EvidenceUnavailable(TechnicalV0ContractError):
    """Raised only when a consumer explicitly asks to unwrap an unavailable value."""


@dataclass(frozen=True)
class TechnicalV0Request:
    """A provider request; the logical key is not the metadata envelope."""

    instrument_identity: str
    indicator_id: str
    session_date: date
    as_of: date | datetime | None = None


def _as_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _as_of_date(value: date | datetime | str | None) -> date | None:
    return None if value is None else _as_date(value)


def _session_date(item: Mapping[str, Any]) -> date:
    return _as_date(item["trading_date"])


def _event_date(event: Mapping[str, Any]) -> date | None:
    for key in ("primary_effective_date", "effective_date", "event_effective_session"):
        if event.get(key) is not None:
            return _as_date(event[key])
    return None


def _filter_events(value: Any, upper_session: date) -> Any:
    """Remove future event knowledge from a bounded in-memory request copy."""

    if isinstance(value, Mapping):
        result = {key: deepcopy(item) for key, item in value.items()}
        events = result.get("known_events")
        if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
            result["known_events"] = [
                event
                for event in events
                if isinstance(event, Mapping)
                and (_event_date(event) is None or _event_date(event) <= upper_session)
            ]
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_filter_events(item, upper_session) for item in value]
    return deepcopy(value)


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _history_identity(history: Mapping[str, Any]) -> str:
    value = history.get("instrument_id") or history.get("identity_id")
    return (
        str(value)
        if value is not None
        else f"{history.get('market', '')}:{history.get('code', '')}"
    )


def _source_identity(lineage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_foundation_version": SOURCE_FOUNDATION_VERSION,
        "source_foundation_sha256": SOURCE_FOUNDATION_SHA256,
        "source_authority_content_sha256": SOURCE_FOUNDATION_AUTHORITY_SHA256,
        "price_authority": TECHNICAL_INPUT_AUTHORITY,
        "series_semantics": "RAW_OBSERVED_DAILY_BAR",
        "adjustment_state": lineage.get("adjustment_state", "UNKNOWN"),
        "lineage_state": lineage.get("lineage_state", "INCOMPLETE"),
        "source_lineage": dict(lineage),
    }


def _availability_state(publication_state: str, reason: str | None) -> str:
    if publication_state == "FORMAL":
        return "AVAILABLE"
    if publication_state == "FORMAL_WITH_LIMITATION":
        return "AVAILABLE_WITH_LIMITATION"
    if publication_state == "DEFERRED":
        return "BLOCKED"
    if reason in {"CONTINUITY_FAIL", "CONTINUITY_UNKNOWN", "AS_OF_VIOLATION"}:
        return "BLOCKED"
    return "UNAVAILABLE"


def _pit_envelope(
    record: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    requested_as_of: date | datetime | None,
) -> dict[str, Any]:
    session = _as_date(record["session_date"])
    actual = record.get("actual_observation_window") or {}
    source_max_session = _session_date(items[-1]) if items else None
    effective_as_of = record.get("as_of") or requested_as_of
    return {
        "session_date": session,
        "as_of": effective_as_of,
        "required_observation_window": record.get("required_observation_window"),
        "actual_observation_window": actual,
        "source_max_session": source_max_session,
        "pit_status": "PIT_SAFE",
        "future_observations_consumed": False,
        "future_revision_silently_backfilled": False,
    }


def _decorate_record(
    record: Mapping[str, Any],
    publication: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    requested_as_of: date | datetime | None,
) -> dict[str, Any]:
    indicator_id = str(record["indicator_id"])
    lineage = record.get("source_lineage") or {}
    publication_state = str(record.get("publication_state"))
    reason = record.get("availability_reason")
    identity = str(record["instrument_identity"])
    session = _as_date(record["session_date"])
    version_identity = {
        "technical_contract_version": publication["technical_contract_version"],
        "technical_policy_version": publication["technical_policy_version"],
        "indicator_id": indicator_id,
        "indicator_version": record["indicator_version"],
        "algorithm_id": record["algorithm_id"],
        "algorithm_version": record["algorithm_version"],
        "parameter_set": record["parameter_set"],
    }
    logical_identity = {
        "instrument_identity": identity,
        "market": record.get("market"),
        "session_date": session,
        "indicator_id": indicator_id,
    }
    source = _source_identity(
        {
            **lineage,
            "adjustment_state": publication.get("provenance", {}).get(
                "adjustment_state", "UNKNOWN"
            ),
        }
    )
    output = dict(record)
    output.update(
        {
            "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
            "provider_contract_version": PROVIDER_CONTRACT_VERSION,
            "evidence_logical_identity": logical_identity,
            "evidence_key": f"{identity}|{session.isoformat()}|{indicator_id}",
            "evidence_version_identity": version_identity,
            "source_identity": source,
            "lineage_reference": f"sha256:{_json_hash(source)}",
            "availability": {
                "state": _availability_state(publication_state, reason),
                "publication_state": publication_state,
                "publication_status": publication.get("publication_status"),
                "reason": reason,
                "limitation_reasons": list(record.get("limitation_reasons") or []),
            },
            "pit": _pit_envelope(record, items, requested_as_of),
            "technical_surface": {
                "technical_result_status": publication.get("technical_result_status"),
                "technical_eligibility": publication.get("technical_eligibility"),
                "publication_status": publication.get("publication_status"),
                "reason_codes": list(publication.get("reason_codes") or []),
            },
        }
    )
    return output


def _unavailable_record(
    history: Mapping[str, Any],
    indicator_id: str,
    session: date,
    reason: str,
    *,
    as_of: date | datetime | None,
) -> dict[str, Any]:
    spec = _SPECS_BY_ID[indicator_id]
    identity = _history_identity(history)
    source = _source_identity(
        {
            "authority": TECHNICAL_INPUT_AUTHORITY,
            "lineage_state": "VERSIONED",
            "source_codes": [],
            "adapter_versions": [],
            "normalization_contract_versions": [],
            "mapping_policy_versions": [],
            "reference_data_versions": [],
            "observation_semantics": [],
        }
    )
    lineage_reference = f"sha256:{_json_hash(source)}"
    logical = {
        "instrument_identity": identity,
        "market": history.get("market"),
        "session_date": session,
        "indicator_id": indicator_id,
    }
    record: dict[str, Any] = {
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "provider_contract_version": PROVIDER_CONTRACT_VERSION,
        "instrument_identity": identity,
        "symbol": history.get("code"),
        "market": history.get("market"),
        "indicator_id": indicator_id,
        "indicator_family": spec["family"],
        "indicator_version": TECHNICAL_POLICY_VERSION,
        "value": None,
        "session_date": session,
        "as_of": as_of,
        "required_observation_count": int(spec["minimum"]),
        "actual_observation_count": 0,
        "required_observation_window": None,
        "actual_observation_window": None,
        "algorithm_id": spec["algorithm_id"],
        "algorithm_version": spec["algorithm_id"],
        "parameter_set": spec["parameters"],
        "price_basis": spec["price_basis"],
        "continuity_state": "CONTINUITY_UNKNOWN",
        "continuity_evidence": {
            "indicator_id": indicator_id,
            "state": "CONTINUITY_UNKNOWN",
            "reason": "CONTINUITY_AUTHORITY_UNAVAILABLE",
        },
        "event_authority_status": "NOT_APPLICABLE",
        "event_lookup_state": "NOT_APPLICABLE",
        "event_lookup_evidence": {},
        "known_event_handling": [],
        "source_authority": TECHNICAL_INPUT_AUTHORITY,
        "source_lineage": source["source_lineage"],
        "publication_state": "UNAVAILABLE",
        "availability_reason": reason,
        "limitation_reasons": [],
        "evidence_logical_identity": logical,
        "evidence_key": f"{identity}|{session.isoformat()}|{indicator_id}",
        "evidence_version_identity": {
            "technical_contract_version": TECHNICAL_CONTRACT_VERSION,
            "technical_policy_version": TECHNICAL_POLICY_VERSION,
            "indicator_id": indicator_id,
            "indicator_version": TECHNICAL_POLICY_VERSION,
            "algorithm_id": spec["algorithm_id"],
            "algorithm_version": spec["algorithm_id"],
            "parameter_set": spec["parameters"],
        },
        "source_identity": source,
        "lineage_reference": lineage_reference,
        "availability": {
            "state": _availability_state("UNAVAILABLE", reason),
            "publication_state": "UNAVAILABLE",
            "publication_status": "UNAVAILABLE",
            "reason": reason,
            "limitation_reasons": [],
        },
        "pit": {
            "session_date": session,
            "as_of": as_of,
            "required_observation_window": None,
            "actual_observation_window": None,
            "source_max_session": None,
            "pit_status": "PIT_SAFE" if reason != "AS_OF_VIOLATION" else "BLOCKED",
            "future_observations_consumed": False,
            "future_revision_silently_backfilled": False,
        },
        "technical_surface": {
            "technical_result_status": "UNAVAILABLE",
            "technical_eligibility": "UNAVAILABLE",
            "publication_status": "UNAVAILABLE",
            "reason_codes": [reason],
        },
    }
    return record


def validate_evidence_record(record: Mapping[str, Any]) -> None:
    """Validate the stable contract fields without binding to a database model."""

    required = {
        "evidence_schema_version",
        "provider_contract_version",
        "evidence_logical_identity",
        "evidence_version_identity",
        "source_identity",
        "lineage_reference",
        "availability",
        "pit",
        "continuity_state",
        "publication_state",
        "value",
    }
    missing = sorted(required - set(record))
    if missing:
        raise TechnicalV0ContractError(f"missing evidence contract fields: {missing}")
    if record["continuity_state"] not in CONTINUITY_STATES:
        raise TechnicalV0ContractError("invalid continuity state")
    if record["publication_state"] not in PUBLICATION_STATES:
        raise TechnicalV0ContractError("invalid publication state")
    availability = record["availability"]
    if availability.get("state") not in AVAILABILITY_STATES:
        raise TechnicalV0ContractError("invalid availability state")
    if record["publication_state"] in {"UNAVAILABLE", "DEFERRED"} and record["value"] is not None:
        raise TechnicalV0ContractError("unavailable evidence cannot carry a value")
    pit = record["pit"]
    if pit.get("pit_status") != "PIT_SAFE":
        raise TechnicalV0ContractError("consumer contract requires explicit PIT_SAFE evidence")


class TechnicalV0EvidenceProvider:
    """Reference provider over a bounded canonical-history envelope."""

    def __init__(self, history: Mapping[str, Any]):
        self._history = deepcopy(dict(history))

    @property
    def provider_contract_version(self) -> str:
        return PROVIDER_CONTRACT_VERSION

    def _bounded_history(
        self,
        session: date,
        as_of: date | datetime | None,
    ) -> dict[str, Any]:
        as_of_session = _as_of_date(as_of)
        upper_session = min(session, as_of_session) if as_of_session else session
        items = [
            deepcopy(item)
            for item in self._history.get("items", [])
            if isinstance(item, Mapping) and _session_date(item) <= upper_session
        ]
        bounded = deepcopy(self._history)
        bounded["items"] = items
        bounded["continuity_evidence"] = _filter_events(
            bounded.get("continuity_evidence"), upper_session
        )
        bounded["known_event_lookup"] = _filter_events(
            bounded.get("known_event_lookup"), upper_session
        )
        bounded["as_of"] = as_of or (items[-1].get("retrieved_at") if items else None)
        bounded["latest_trading_date"] = _session_date(items[-1]) if items else None
        bounded["latest_retrieved_at"] = items[-1].get("retrieved_at") if items else None
        return bounded

    def _publication(self, session: date, as_of: date | datetime | None) -> dict[str, Any]:
        return build_technical_publication(self._bounded_history(session, as_of))

    def get_evidence(
        self,
        *,
        indicator_id: str,
        session_date: date | str,
        as_of: date | datetime | str | None = None,
    ) -> dict[str, Any]:
        if indicator_id not in _SPECS_BY_ID:
            raise TechnicalV0ContractError(f"indicator is not frozen Technical V0: {indicator_id}")
        session = _as_date(session_date)
        as_of_value = as_of
        if as_of_value is not None and _as_of_date(as_of_value) < session:
            return _unavailable_record(
                self._history,
                indicator_id,
                session,
                "AS_OF_VIOLATION",
                as_of=(
                    as_of_value
                    if isinstance(as_of_value, (date, datetime))
                    else _as_date(as_of_value)
                ),
            )
        publication = self._publication(session, as_of_value)
        identity = _history_identity(self._history)
        records = [
            record
            for record in publication["technical_evidence"]
            if record.get("indicator_id") == indicator_id
            and _as_date(record["session_date"]) == session
        ]
        if not records:
            reason = (
                "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS"
                if not publication["technical_evidence"]
                else "NO_EVIDENCE_AT_AS_OF"
            )
            return _unavailable_record(
                self._history,
                indicator_id,
                session,
                reason,
                as_of=(
                    as_of_value
                    if isinstance(as_of_value, (date, datetime))
                    else _as_date(as_of_value)
                    if as_of_value
                    else None
                ),
            )
        record = _decorate_record(
            records[-1],
            publication,
            self._bounded_history(session, as_of_value)["items"],
            as_of_value,
        )
        # The existing publication builder can expose an explicit event-lookup
        # limitation for a bounded analytical surface.  A provider request
        # with no continuity envelope at all is stronger: D1 requires
        # CONTINUITY_UNKNOWN to fail closed, never to become an implicit
        # limited value merely because the event table was not queried.
        if (
            record["continuity_state"] == "CONTINUITY_UNKNOWN"
            and not self._history.get("continuity_evidence")
        ):
            record["value"] = None
            record["publication_state"] = "UNAVAILABLE"
            record["availability_reason"] = "CONTINUITY_UNKNOWN"
            record["availability"] = {
                "state": "BLOCKED",
                "publication_state": "UNAVAILABLE",
                "publication_status": "BLOCKED",
                "reason": "CONTINUITY_UNKNOWN",
                "limitation_reasons": [],
            }
            record["technical_surface"] = {
                "technical_result_status": "UNAVAILABLE",
                "technical_eligibility": "UNAVAILABLE",
                "publication_status": "BLOCKED",
                "reason_codes": ["CONTINUITY_UNKNOWN"],
            }
        if record["instrument_identity"] != identity:
            raise TechnicalV0ContractError("provider identity changed during lookup")
        validate_evidence_record(record)
        return record

    def get_batch(
        self,
        *,
        indicator_ids: Sequence[str],
        session_date: date | str,
        as_of: date | datetime | str | None = None,
    ) -> list[dict[str, Any]]:
        if not indicator_ids:
            raise TechnicalV0ContractError("batch lookup requires at least one indicator")
        return [
            self.get_evidence(indicator_id=indicator_id, session_date=session_date, as_of=as_of)
            for indicator_id in indicator_ids
        ]

    def get_historical(
        self,
        *,
        indicator_ids: Sequence[str],
        from_session: date | str,
        to_session: date | str,
        as_of: date | datetime | str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if not indicator_ids:
            raise TechnicalV0ContractError("historical lookup requires at least one indicator")
        start = _as_date(from_session)
        end = _as_date(to_session)
        if end < start:
            raise TechnicalV0ContractError("historical lookup window is reversed")
        if limit < 1:
            raise TechnicalV0ContractError("historical lookup limit must be positive")
        publication = self._publication(end, as_of)
        allowed = set(indicator_ids)
        unknown = sorted(allowed - set(_SPECS_BY_ID))
        if unknown:
            raise TechnicalV0ContractError(f"indicator is not frozen Technical V0: {unknown}")
        bounded_items = self._bounded_history(end, as_of)["items"]
        output = [
            _decorate_record(record, publication, bounded_items, as_of)
            for record in publication["technical_evidence"]
            if record.get("indicator_id") in allowed
            and start <= _as_date(record["session_date"]) <= end
        ]
        output.sort(
            key=lambda record: (
                _as_date(record["session_date"]),
                str(record["indicator_id"]),
            )
        )
        return output[:limit]


class TechnicalV0EvidenceConsumer:
    """Read-only consumer facade that preserves unavailable evidence."""

    def __init__(self, provider: TechnicalV0EvidenceProvider):
        self.provider = provider

    def request_one(self, request: TechnicalV0Request) -> dict[str, Any]:
        return self.provider.get_evidence(
            indicator_id=request.indicator_id,
            session_date=request.session_date,
            as_of=request.as_of,
        )

    def request_many(
        self,
        *,
        indicator_ids: Sequence[str],
        session_date: date | str,
        as_of: date | datetime | str | None = None,
    ) -> list[dict[str, Any]]:
        return self.provider.get_batch(
            indicator_ids=indicator_ids,
            session_date=session_date,
            as_of=as_of,
        )

    def request_history(
        self,
        *,
        indicator_ids: Sequence[str],
        from_session: date | str,
        to_session: date | str,
        as_of: date | datetime | str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self.provider.get_historical(
            indicator_ids=indicator_ids,
            from_session=from_session,
            to_session=to_session,
            as_of=as_of,
            limit=limit,
        )

    @staticmethod
    def value(record: Mapping[str, Any]) -> Any:
        """Unwrap only available evidence; never coerce unavailable to zero/false."""

        validate_evidence_record(record)
        if record["availability"]["state"] not in {"AVAILABLE", "AVAILABLE_WITH_LIMITATION"}:
            raise EvidenceUnavailable(str(record.get("availability_reason")))
        return record["value"]


__all__ = [
    "AVAILABILITY_STATES",
    "CONSUMER_CONTRACT_VERSION",
    "CONTINUITY_STATES",
    "E1_ARTIFACT_BYTES",
    "E1_ARTIFACT_ROLE",
    "E1_ARTIFACT_RUNTIME_DEPENDENCY",
    "E1_ARTIFACT_SHA256",
    "EVIDENCE_SCHEMA_VERSION",
    "FORMAL_INDICATOR_IDS",
    "PROVIDER_CONTRACT_VERSION",
    "PUBLICATION_STATES",
    "SOURCE_FOUNDATION_ACCEPTED_OHLCV_ROWS",
    "SOURCE_FOUNDATION_AUTHORITY_SHA256",
    "SOURCE_FOUNDATION_INSTRUMENT_COUNT",
    "SOURCE_FOUNDATION_SHA256",
    "SOURCE_FOUNDATION_VERSION",
    "EvidenceUnavailable",
    "TechnicalV0ContractError",
    "TechnicalV0EvidenceConsumer",
    "TechnicalV0EvidenceProvider",
    "TechnicalV0Request",
    "validate_evidence_record",
]
