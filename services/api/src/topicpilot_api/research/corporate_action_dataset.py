"""Bounded, research-only corporate-action dataset contracts.

This module deliberately has no network, database, scheduler, or production
integration.  It validates reduced semantic records imported from an
operator-controlled official query/export and keeps them separate from raw
OHLCV persistence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.reference_data.bundle import load_bundle

CA_EVENT_SCHEMA_VERSION = "CA-EVENT-SCHEMA-V0"
DATASET_SCHEMA_VERSION = "rec-a1-corporate-action-research-dataset.v0"
DATASET_VERSION = "REC-A1-CA-EVENTS-V0"
REFERENCE_VERSION = "tw-reference-v1"
UNIVERSE_POLICY = "LIFECYCLE_GATED_507"
WINDOW_START = date(2026, 2, 2)
WINDOW_END = date(2026, 8, 13)

EVENT_TYPES = frozenset(
    {
        "CASH_DIVIDEND_EX_DIVIDEND",
        "STOCK_DIVIDEND_EX_RIGHT",
        "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET",
        "CAPITAL_REDUCTION",
        "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE",
        "MERGER_SHARE_CONVERSION_DEMERGER",
        "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY",
        "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL",
    }
)
EVENT_REASON_CODES = {
    "CASH_DIVIDEND_EX_DIVIDEND": "CA_EX_DIVIDEND",
    "STOCK_DIVIDEND_EX_RIGHT": "CA_EX_RIGHT",
    "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET": (
        "CA_CAPITAL_INCREASE_REFERENCE_RESET"
    ),
    "CAPITAL_REDUCTION": "CA_CAPITAL_REDUCTION",
    "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE": "CA_SPLIT_REVERSE_SPLIT",
    "MERGER_SHARE_CONVERSION_DEMERGER": "CA_SHARE_CONVERSION",
    "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY": "CA_LISTING_TERMINATION",
    "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL": (
        "CA_COMBINED_EX_RIGHT_EX_DIVIDEND"
    ),
}
PRIMARY_EVENT_FAMILIES = (
    "CASH_DIVIDEND_EX_DIVIDEND",
    "STOCK_DIVIDEND_EX_RIGHT",
    "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET",
    "CAPITAL_REDUCTION",
)
SEMANTIC_PARTIAL_EVENT_FAMILIES = (
    "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE",
    "MERGER_SHARE_CONVERSION_DEMERGER",
    "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY",
    "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL",
)
ALL_EVENT_FAMILIES = PRIMARY_EVENT_FAMILIES + SEMANTIC_PARTIAL_EVENT_FAMILIES
COVERAGE_STATES = frozenset(
    {"COVERED_EVENT", "COVERED_NO_EVENT", "UNKNOWN", "OUTSIDE_SCOPE"}
)
REVIEW_STATES = frozenset(
    {
        "CONFIRMED_EVENT",
        "AUTHORITATIVE_NO_EVENT",
        "UNREVIEWED_UNKNOWN",
        "REVIEWED_UNKNOWN_NO_EVENT_FOUND",
    }
)
FREEZE_POLICIES = frozenset(
    {"BEST_EFFORT_RESEARCH_INTEGRITY_WITH_REVIEWED_RESIDUAL_UNCERTAINTY"}
)
RESIDUAL_RISK_CLASSIFICATIONS = frozenset({"BOUNDED_RESEARCH_DATA_UNCERTAINTY"})
AUTHORITY_STATES = frozenset({"AUTHORITATIVE", "PARTIAL", "UNKNOWN"})
ACCESS_METHODS = frozenset(
    {
        "OFFICIAL_API_AUTOMATED_ALLOWED",
        "MANUAL_OR_BOUNDED_QUERY_ONLY",
        "CANONICAL_REFERENCE_BUNDLE",
    }
)
ALLOWED_SOURCE_HOSTS = frozenset(
    {
        "openapi.twse.com.tw",
        "www.twse.com.tw",
        "wwwc.twse.com.tw",
        "eshop.twse.com.tw",
        "www.tpex.org.tw",
        "eshop.tpex.org.tw",
    }
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class TpexBoundedArtifactRequirements:
    """The operator-controlled artifact contract; it does not fetch TPEx."""

    official_surfaces: tuple[str, ...]
    query_date_range: tuple[str, str]
    security_scope: str
    event_families: tuple[str, ...]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    accepted_file_formats: tuple[str, ...]
    expected_export_semantics: tuple[str, ...]
    manual_steps_required: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "official_surface": list(self.official_surfaces),
            "query_date_range": {
                "start": self.query_date_range[0],
                "end": self.query_date_range[1],
            },
            "security_scope": self.security_scope,
            "event_families": list(self.event_families),
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "accepted_file_formats": list(self.accepted_file_formats),
            "expected_export_semantics": list(self.expected_export_semantics),
            "manual_steps_required": list(self.manual_steps_required),
        }


TPEX_BOUNDED_ARTIFACT_REQUIREMENTS = TpexBoundedArtifactRequirements(
    official_surfaces=(
        "https://www.tpex.org.tw/en-us/announce/market/ex/announce.html",
        "https://www.tpex.org.tw/en-us/announce/market/ex/cal.html",
        "https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html",
        "https://www.tpex.org.tw/en-us/announce/market/reduction-tdr.html",
    ),
    query_date_range=(WINDOW_START.isoformat(), WINDOW_END.isoformat()),
    security_scope=(
        "TWO current tw-reference-v1 identities; identify outside-507 rows, "
        "do not discard silently"
    ),
    event_families=PRIMARY_EVENT_FAMILIES + SEMANTIC_PARTIAL_EVENT_FAMILIES,
    required_fields=(
        "source_name",
        "official_product_or_surface",
        "access_method",
        "source_url",
        "source_record_id_or_canonical_row_key",
        "market_code",
        "instrument_code",
        "canonical_identity",
        "event_type",
        "primary_effective_date",
        "retrieved_at",
        "semantic_version",
        "authority_state",
        "query_or_export_manifest_id",
        "checkpoint_id",
        "reason_code",
    ),
    optional_fields=(
        "announcement_date_if_available",
        "reference_price_if_officially_returned",
        "source_as_of_if_available",
        "source_content_hash_if_storage_permitted",
    ),
    accepted_file_formats=("JSON_OBJECT", "JSON_ARRAY", "CSV_UTF8", "CSV_UTF8_BOM"),
    expected_export_semantics=(
        "date/code or date-range scope is explicit",
        "event-family scope is explicit",
        "issuer announcement precedence is preserved where TPEx states it",
        "zero rows are not PASS_NO_EVENT without completed authoritative scope",
        "raw bulk response is not retained unless terms permit",
    ),
    manual_steps_required=(
        "operator performs the official TPEx query/export manually",
        "operator records the exact surface, date range, and event-family scope",
        "operator places the reduced export in the agreed research handoff location",
        "TopicPilot importer validates and hashes without making network calls",
    ),
)


class CorporateActionDatasetError(ValueError):
    """Raised when a research artifact cannot be safely accepted."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CorporateActionDatasetError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _iso_date(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    text = _text(value, field)
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise CorporateActionDatasetError(f"{field} is not an ISO date") from exc


def _iso_timestamp(value: Any, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CorporateActionDatasetError(f"{field} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise CorporateActionDatasetError(f"{field} must include a timezone")
    return parsed.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _hash(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    text = _text(value, field).lower()
    if not HEX64.fullmatch(text):
        raise CorporateActionDatasetError(f"{field} must be a lowercase SHA-256 hash")
    return text


def _numeric_text(value: Any, field: str) -> str | None:
    text = _optional_text(value, field)
    if text is None:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise CorporateActionDatasetError(f"{field} must be a decimal string") from exc
    if not number.is_finite():
        raise CorporateActionDatasetError(f"{field} must be finite")
    return "0" if number == 0 else format(number.normalize(), "f")


def _official_url(value: Any) -> str:
    text = _text(value, "source_url")
    parsed = urlparse(text)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
        raise CorporateActionDatasetError("source_url must be an approved official HTTPS host")
    return text


def stable_event_key(
    source_name: str,
    market_code: str,
    instrument_code: str,
    event_type: str,
    primary_effective_date: str,
    source_record_id: str,
) -> str:
    """Return the idempotent identity of one normalized source event."""

    return "|".join(
        (
            source_name,
            market_code,
            instrument_code,
            event_type,
            primary_effective_date,
            source_record_id,
        )
    )


EVENT_FIELDS = frozenset(
    {
        "source_name",
        "official_product_or_surface",
        "access_method",
        "source_url",
        "source_record_id_or_canonical_row_key",
        "market_code",
        "instrument_code",
        "canonical_identity",
        "event_type",
        "announcement_date_if_available",
        "primary_effective_date",
        "reference_price_if_officially_returned",
        "source_as_of_if_available",
        "retrieved_at",
        "source_content_hash_if_storage_permitted",
        "normalized_semantic_hash",
        "semantic_version",
        "authority_state",
        "query_or_export_manifest_id",
        "checkpoint_id",
        "reason_code",
        "stable_event_key",
    }
)


def _semantic_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "normalized_semantic_hash",
        "source_content_hash_if_storage_permitted",
        "retrieved_at",
        "query_or_export_manifest_id",
        "checkpoint_id",
        "stable_event_key",
    }
    return {key: payload[key] for key in sorted(payload) if key not in excluded}


@dataclass(frozen=True)
class CorporateActionEvent:
    source_name: str
    official_product_or_surface: str
    access_method: str
    source_url: str
    source_record_id_or_canonical_row_key: str
    market_code: str
    instrument_code: str
    canonical_identity: str
    event_type: str
    announcement_date_if_available: str | None
    primary_effective_date: str
    reference_price_if_officially_returned: str | None
    source_as_of_if_available: str | None
    retrieved_at: str
    source_content_hash_if_storage_permitted: str | None
    normalized_semantic_hash: str
    semantic_version: str
    authority_state: str
    query_or_export_manifest_id: str
    checkpoint_id: str
    reason_code: str
    stable_event_key: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CorporateActionEvent:
        unknown = set(payload) - EVENT_FIELDS
        missing = EVENT_FIELDS - set(payload)
        if unknown:
            raise CorporateActionDatasetError(f"event has unknown fields: {sorted(unknown)}")
        if missing:
            raise CorporateActionDatasetError(f"event is missing fields: {sorted(missing)}")

        source_name = _text(payload["source_name"], "source_name")
        product = _text(payload["official_product_or_surface"], "official_product_or_surface")
        access_method = _text(payload["access_method"], "access_method")
        if access_method not in ACCESS_METHODS:
            raise CorporateActionDatasetError(f"unsupported access_method: {access_method}")
        source_url = _official_url(payload["source_url"])
        source_record = _text(
            payload["source_record_id_or_canonical_row_key"],
            "source_record_id_or_canonical_row_key",
        )
        market_code = _text(payload["market_code"], "market_code").upper()
        instrument_code = _text(payload["instrument_code"], "instrument_code")
        canonical_identity = _text(payload["canonical_identity"], "canonical_identity")
        if canonical_identity != f"{market_code}:{instrument_code}":
            raise CorporateActionDatasetError("canonical_identity does not match market/code")
        event_type = _text(payload["event_type"], "event_type")
        if event_type not in EVENT_TYPES:
            raise CorporateActionDatasetError(f"unsupported event_type: {event_type}")
        announcement_date = _iso_date(
            payload["announcement_date_if_available"],
            "announcement_date_if_available",
            optional=True,
        )
        effective_date = _iso_date(payload["primary_effective_date"], "primary_effective_date")
        assert effective_date is not None
        effective = date.fromisoformat(effective_date)
        if not WINDOW_START <= effective <= WINDOW_END:
            raise CorporateActionDatasetError("primary_effective_date is outside the fixed window")
        reference_price = _numeric_text(
            payload["reference_price_if_officially_returned"],
            "reference_price_if_officially_returned",
        )
        source_as_of = _iso_date(
            payload["source_as_of_if_available"],
            "source_as_of_if_available",
            optional=True,
        )
        retrieved_at = _iso_timestamp(payload["retrieved_at"], "retrieved_at")
        source_hash = _hash(
            payload["source_content_hash_if_storage_permitted"],
            "source_content_hash_if_storage_permitted",
            optional=True,
        )
        semantic_version = _text(payload["semantic_version"], "semantic_version")
        if semantic_version != CA_EVENT_SCHEMA_VERSION:
            raise CorporateActionDatasetError("unsupported semantic_version")
        authority_state = _text(payload["authority_state"], "authority_state").upper()
        if authority_state not in AUTHORITY_STATES:
            raise CorporateActionDatasetError(f"unsupported authority_state: {authority_state}")
        manifest_id = _text(payload["query_or_export_manifest_id"], "query_or_export_manifest_id")
        checkpoint_id = _text(payload["checkpoint_id"], "checkpoint_id")
        reason_code = _text(payload["reason_code"], "reason_code")
        expected_reason = EVENT_REASON_CODES[event_type]
        if authority_state == "AUTHORITATIVE" and reason_code != expected_reason:
            raise CorporateActionDatasetError("authoritative event has the wrong reason_code")
        expected_key = stable_event_key(
            source_name,
            market_code,
            instrument_code,
            event_type,
            effective_date,
            source_record,
        )
        actual_key = _text(payload["stable_event_key"], "stable_event_key")
        if actual_key != expected_key:
            raise CorporateActionDatasetError("stable_event_key is not deterministic")
        semantic_hash = _hash(payload["normalized_semantic_hash"], "normalized_semantic_hash")
        assert semantic_hash is not None
        normalized_payload = {
            "source_name": source_name,
            "official_product_or_surface": product,
            "access_method": access_method,
            "source_url": source_url,
            "source_record_id_or_canonical_row_key": source_record,
            "market_code": market_code,
            "instrument_code": instrument_code,
            "canonical_identity": canonical_identity,
            "event_type": event_type,
            "announcement_date_if_available": announcement_date,
            "primary_effective_date": effective_date,
            "reference_price_if_officially_returned": reference_price,
            "source_as_of_if_available": source_as_of,
            "retrieved_at": retrieved_at,
            "source_content_hash_if_storage_permitted": source_hash,
            "normalized_semantic_hash": semantic_hash,
            "semantic_version": semantic_version,
            "authority_state": authority_state,
            "query_or_export_manifest_id": manifest_id,
            "checkpoint_id": checkpoint_id,
            "reason_code": reason_code,
            "stable_event_key": actual_key,
        }
        if stable_hash(_semantic_payload(normalized_payload)) != semantic_hash:
            raise CorporateActionDatasetError("normalized_semantic_hash mismatch")
        return cls(**normalized_payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            field: getattr(self, field)
            for field in sorted(EVENT_FIELDS)
        }


def build_event(payload: Mapping[str, Any]) -> CorporateActionEvent:
    """Normalize an operator-provided reduced event row and compute its hash."""

    candidate = dict(payload)
    candidate.setdefault("source_content_hash_if_storage_permitted", None)
    candidate.setdefault(
        "reason_code",
        EVENT_REASON_CODES.get(candidate.get("event_type"), "CA_AUTHORITY_UNKNOWN"),
    )
    candidate["stable_event_key"] = stable_event_key(
        _text(candidate.get("source_name"), "source_name"),
        _text(candidate.get("market_code"), "market_code").upper(),
        _text(candidate.get("instrument_code"), "instrument_code"),
        _text(candidate.get("event_type"), "event_type"),
        _text(candidate.get("primary_effective_date"), "primary_effective_date"),
        _text(
            candidate.get("source_record_id_or_canonical_row_key"),
            "source_record_id_or_canonical_row_key",
        ),
    )
    candidate["normalized_semantic_hash"] = stable_hash(_semantic_payload(candidate))
    return CorporateActionEvent.from_dict(candidate)


def parse_tpex_bounded_artifact(
    payload: Mapping[str, Any],
) -> tuple[CorporateActionEvent, ...]:
    """Parse a manual TPEx handoff without performing any TPEx request.

    The envelope carries acquisition scope and lineage defaults. Records must
    still contain a market/code, event type, effective date, authority state,
    and stable source record identity. The parser rejects non-TWO identities,
    incomplete scope, duplicate semantic identities, and raw-response-shaped
    payloads.
    """

    required = {
        "artifact_type",
        "source_name",
        "official_surface",
        "source_url",
        "access_method",
        "query_window_start",
        "query_window_end",
        "event_family_scope",
        "security_scope",
        "retrieved_at",
        "manifest_id",
        "checkpoint_id",
        "records",
    }
    optional = {
        "source_as_of_if_available",
        "content_hash_if_allowed",
        "record_count",
        "source_file_name",
        "source_file_sha256",
        "raw_row_count",
        "canonical_source_rows",
        "canonical_identities",
        "outside_rows",
        "outside_identities",
        "outside_canonical_507_audit_rows",
        "raw_originals",
        "artifact_content_hash",
    }
    unknown = set(payload) - required - optional
    missing = required - set(payload)
    if unknown:
        raise CorporateActionDatasetError(
            f"TPEx artifact has unknown fields: {sorted(unknown)}"
        )
    if missing:
        raise CorporateActionDatasetError(
            f"TPEx artifact is missing fields: {sorted(missing)}"
        )
    if payload["artifact_type"] != "TPEX_BOUNDED_CORPORATE_ACTION_ARTIFACT":
        raise CorporateActionDatasetError("unsupported TPEx artifact type")
    if payload["source_name"] != "TPEx":
        raise CorporateActionDatasetError("TPEx artifact source_name must be TPEx")
    if payload["access_method"] != "MANUAL_OR_BOUNDED_QUERY_ONLY":
        raise CorporateActionDatasetError("TPEx artifact access method is not bounded manual")
    official_surface = _text(payload["official_surface"], "official_surface")
    source_url = _official_url(payload["source_url"])
    if "www.tpex.org.tw" not in urlparse(source_url).hostname:
        raise CorporateActionDatasetError("TPEx artifact source_url must be a TPEx surface")
    query_start = _iso_date(payload["query_window_start"], "query_window_start")
    query_end = _iso_date(payload["query_window_end"], "query_window_end")
    assert query_start is not None and query_end is not None
    if query_start < WINDOW_START.isoformat() or query_end > WINDOW_END.isoformat():
        raise CorporateActionDatasetError("TPEx artifact query window exceeds REC-A1 window")
    if query_end < query_start:
        raise CorporateActionDatasetError("TPEx artifact query window is reversed")
    scope = payload["event_family_scope"]
    if not isinstance(scope, list) or not scope or not all(isinstance(item, str) for item in scope):
        raise CorporateActionDatasetError("TPEx event_family_scope must be a non-empty string list")
    if any(item not in EVENT_TYPES for item in scope):
        raise CorporateActionDatasetError("TPEx artifact contains an unsupported event family")
    security_scope = payload["security_scope"]
    if not isinstance(security_scope, (str, list)) or not security_scope:
        raise CorporateActionDatasetError("TPEx security_scope must be explicit")
    retrieved_at = _iso_timestamp(payload["retrieved_at"], "retrieved_at")
    manifest_id = _text(payload["manifest_id"], "manifest_id")
    checkpoint_id = _text(payload["checkpoint_id"], "checkpoint_id")
    source_as_of = _iso_date(
        payload.get("source_as_of_if_available"),
        "source_as_of_if_available",
        optional=True,
    )
    content_hash = _hash(
        payload.get("content_hash_if_allowed"),
        "content_hash_if_allowed",
        optional=True,
    )
    records = payload["records"]
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise CorporateActionDatasetError("TPEx artifact records must be a list of objects")
    if "record_count" in payload and payload["record_count"] != len(records):
        raise CorporateActionDatasetError("TPEx artifact record_count mismatch")
    if "source_file_sha256" in payload:
        _hash(payload["source_file_sha256"], "source_file_sha256")
    if "artifact_content_hash" in payload:
        expected_content_hash = stable_hash(
            {key: value for key, value in payload.items() if key != "artifact_content_hash"}
        )
        if payload["artifact_content_hash"] != expected_content_hash:
            raise CorporateActionDatasetError("TPEx artifact_content_hash mismatch")
    if "raw_originals" in payload and payload["raw_originals"] != "READ_ONLY_EXTERNAL_NOT_STORED":
        raise CorporateActionDatasetError("TPEx raw originals must remain read-only and external")
    if any(key in record for record in records for key in ("raw_response", "raw_rows")):
        raise CorporateActionDatasetError("raw TPEx response content is not an import contract")

    normalized: list[CorporateActionEvent] = []
    for record in records:
        row = dict(record)
        row.setdefault("source_name", "TPEx")
        row.setdefault("official_product_or_surface", official_surface)
        row.setdefault("access_method", "MANUAL_OR_BOUNDED_QUERY_ONLY")
        row.setdefault("source_url", source_url)
        row.setdefault("retrieved_at", retrieved_at)
        row.setdefault("source_as_of_if_available", source_as_of)
        row.setdefault("source_content_hash_if_storage_permitted", content_hash)
        row.setdefault("semantic_version", CA_EVENT_SCHEMA_VERSION)
        row.setdefault("query_or_export_manifest_id", manifest_id)
        row.setdefault("checkpoint_id", checkpoint_id)
        row.setdefault("announcement_date_if_available", None)
        row.setdefault("reference_price_if_officially_returned", None)
        row.setdefault("canonical_identity", None)
        if row.get("market_code") != "TWO":
            raise CorporateActionDatasetError("TPEx source record market_code must be TWO")
        instrument_code = _text(row.get("instrument_code"), "instrument_code")
        expected_identity = f"TWO:{instrument_code}"
        if row["canonical_identity"] not in (None, expected_identity):
            raise CorporateActionDatasetError("TPEx canonical identity is ambiguous")
        row["canonical_identity"] = expected_identity
        event_type = _text(row.get("event_type"), "event_type")
        if event_type not in scope:
            raise CorporateActionDatasetError("TPEx record event family is outside artifact scope")
        effective = _iso_date(row.get("primary_effective_date"), "primary_effective_date")
        assert effective is not None
        if not query_start <= effective <= query_end:
            raise CorporateActionDatasetError("TPEx event effective date is outside artifact scope")
        normalized.append(build_event(row))
    unique, duplicates = deduplicate_events(tuple(normalized))
    if duplicates:
        raise CorporateActionDatasetError("TPEx artifact contains duplicate semantic events")
    return unique


@dataclass(frozen=True)
class BoundedExportNormalization:
    """Reduced import output for one operator-provided official CSV."""

    source_name: str
    market_code: str
    source_file_name: str
    source_file_sha256: str
    raw_row_count: int
    canonical_source_rows: int
    canonical_identities: int
    outside_rows: int
    outside_identities: int
    raw_event_label_counts: dict[str, int]
    normalized_event_family_counts: dict[str, int]
    events: tuple[CorporateActionEvent, ...]
    outside_audit_rows: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]
    checkpoint: dict[str, Any]
    source_url: str
    official_surface: str
    retrieved_at: str

    def to_envelope(self) -> dict[str, Any]:
        artifact_type = (
            "TPEX_BOUNDED_CORPORATE_ACTION_ARTIFACT"
            if self.source_name == "TPEx"
            else "TWSE_BOUNDED_CORPORATE_ACTION_ARTIFACT"
        )
        payload: dict[str, Any] = {
            "artifact_type": artifact_type,
            "source_name": self.source_name,
            "official_surface": self.official_surface,
            "source_url": self.source_url,
            "access_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
            "query_window_start": WINDOW_START.isoformat(),
            "query_window_end": WINDOW_END.isoformat(),
            "event_family_scope": list(PRIMARY_EVENT_FAMILIES + SEMANTIC_PARTIAL_EVENT_FAMILIES),
            "security_scope": (
                f"{self.market_code} tw-reference-v1 canonical identities plus "
                "outside audit rows"
            ),
            "retrieved_at": self.retrieved_at,
            "manifest_id": self.manifest["manifest_id"],
            "checkpoint_id": self.checkpoint["checkpoint_id"],
            "records": [event.to_dict() for event in self.events],
            "record_count": len(self.events),
            "content_hash_if_allowed": self.source_file_sha256,
            "source_file_name": self.source_file_name,
            "source_file_sha256": self.source_file_sha256,
            "raw_row_count": self.raw_row_count,
            "canonical_source_rows": self.canonical_source_rows,
            "canonical_identities": self.canonical_identities,
            "outside_rows": self.outside_rows,
            "outside_identities": self.outside_identities,
            "outside_canonical_507_audit_rows": list(self.outside_audit_rows),
            "raw_originals": "READ_ONLY_EXTERNAL_NOT_STORED",
        }
        payload["artifact_content_hash"] = stable_hash(payload)
        return payload


def _bounded_code(value: Any) -> str:
    text = _text(value, "instrument_code")
    return text.lstrip('="').rstrip('"').strip()


def _bounded_effective_date(value: Any) -> str:
    text = _text(value, "primary_effective_date")
    parts = re.findall(r"\d+", text)
    if len(parts) != 3:
        raise CorporateActionDatasetError("bounded export date is not ROC year/month/day")
    year, month, day = (int(item) for item in parts)
    if year < 1911:
        year += 1911
    return _iso_date(f"{year:04d}-{month:02d}-{day:02d}", "primary_effective_date") or ""


def _bounded_positive(value: Any, field: str) -> bool:
    text = _optional_text(value, field)
    if text is None or text.upper() in {"N/A", "NA", "-", "--"}:
        return False
    try:
        number = Decimal(text.replace(",", ""))
    except InvalidOperation as exc:
        raise CorporateActionDatasetError(f"{field} is not numeric") from exc
    if not number.is_finite():
        raise CorporateActionDatasetError(f"{field} is not finite")
    return number > 0


def _bounded_reference_price(value: Any) -> str | None:
    text = _optional_text(value, "reference_price_if_officially_returned")
    if text is None or text.upper() in {"N/A", "NA", "-", "--"}:
        return None
    return _numeric_text(text.replace(",", ""), "reference_price_if_officially_returned")


def _bounded_specs(
    source_name: str,
    event_label: str,
    row: list[str],
) -> tuple[tuple[str, str], ...]:
    if source_name == "TWSE":
        if event_label == "息":
            return (("CASH_DIVIDEND_EX_DIVIDEND", "AUTHORITATIVE"),)
        if event_label == "權":
            return (("STOCK_DIVIDEND_EX_RIGHT", "PARTIAL"),)
        if event_label == "權息":
            return (("COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL", "PARTIAL"),)
        raise CorporateActionDatasetError(f"unsupported TWSE bounded event label: {event_label}")

    if source_name != "TPEx":
        raise CorporateActionDatasetError(f"unsupported bounded source: {source_name}")
    cash = _bounded_positive(row[13], "cash_dividend") or _bounded_positive(
        row[6], "interest_value"
    )
    stock = _bounded_positive(row[14], "stock_dividend")
    rights = _bounded_positive(row[15], "capital_increase_shares")
    if event_label == "除息":
        if not cash:
            raise CorporateActionDatasetError("TPEx ex-dividend row has no cash component")
        return (("CASH_DIVIDEND_EX_DIVIDEND", "AUTHORITATIVE"),)
    if event_label not in {"除權", "除權息"}:
        raise CorporateActionDatasetError(f"unsupported TPEx bounded event label: {event_label}")
    specs: list[tuple[str, str]] = []
    if event_label == "除權息":
        if not cash:
            raise CorporateActionDatasetError("TPEx ex-right/ex-dividend row has no cash component")
        specs.append(("CASH_DIVIDEND_EX_DIVIDEND", "AUTHORITATIVE"))
    if stock:
        specs.append(("STOCK_DIVIDEND_EX_RIGHT", "AUTHORITATIVE"))
    if rights:
        specs.append(("RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET", "AUTHORITATIVE"))
    if not specs:
        raise CorporateActionDatasetError("TPEx ex-right row has no explicit component")
    return tuple(specs)


def normalize_official_bounded_csv(
    path: Path,
    *,
    source_name: str,
    source_url: str,
    official_surface: str,
    encoding: str,
    retrieved_at: str,
    manifest_id: str,
    checkpoint_id: str,
    reference_bundle_dir: Path,
) -> BoundedExportNormalization:
    """Normalize one official bounded CSV without modifying or copying its raw bytes."""

    if source_name not in {"TWSE", "TPEx"}:
        raise CorporateActionDatasetError("bounded source_name must be TWSE or TPEx")
    official_url = _official_url(source_url)
    retrieved = _iso_timestamp(retrieved_at, "retrieved_at")
    try:
        raw = path.read_bytes()
        text = raw.decode(encoding)
    except (OSError, UnicodeError) as exc:
        raise CorporateActionDatasetError(f"cannot read bounded export: {path}") from exc
    source_file_sha256 = hashlib.sha256(raw).hexdigest()
    rows = list(csv.reader(text.splitlines()))
    market_code = "TPE" if source_name == "TWSE" else "TWO"
    identity_set = _load_identity_set(reference_bundle_dir)
    data_rows: list[tuple[int, list[str]]] = []
    for row_position, row in enumerate(rows, start=1):
        if len(row) < 9:
            continue
        code = _bounded_code(row[1])
        if len(code) < 4 or not code[:4].isdigit():
            continue
        data_rows.append((row_position, row))
    if not data_rows:
        raise CorporateActionDatasetError("bounded export contains no event rows")

    events: list[CorporateActionEvent] = []
    outside_audit_rows: list[dict[str, Any]] = []
    raw_event_label_counts: Counter[str] = Counter()
    normalized_event_family_counts: Counter[str] = Counter()
    canonical_identities: set[str] = set()
    for row_position, row in data_rows:
        code = _bounded_code(row[1])
        event_label = _text(row[6 if source_name == "TWSE" else 8], "event_label")
        effective_date = _bounded_effective_date(row[0])
        specs = _bounded_specs(source_name, event_label, row)
        raw_event_label_counts[event_label] += 1
        identity = f"{market_code}:{code}"
        source_record_base = f"{source_name}:BOUNDED_CSV:ROW:{row_position}"
        if identity not in identity_set:
            outside_audit_rows.append(
                {
                    "classification": "OUTSIDE_CANONICAL_507",
                    "source_name": source_name,
                    "source_file_name": path.name,
                    "source_file_sha256": source_file_sha256,
                    "source_record_id_or_canonical_row_key": source_record_base,
                    "source_row_position": row_position,
                    "market_code": market_code,
                    "instrument_code": code,
                    "canonical_identity": None,
                    "instrument_type": None,
                    "source_instrument_name": row[2].strip() if len(row) > 2 else "",
                    "raw_event_label": event_label,
                    "primary_effective_date": effective_date,
                    "normalized_event_types": [event_type for event_type, _ in specs],
                }
            )
            continue

        canonical_identities.add(identity)
        for event_type, authority_state in specs:
            source_record = f"{source_record_base}:{event_type}"
            event = build_event(
                {
                    "source_name": source_name,
                    "official_product_or_surface": official_surface,
                    "access_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
                    "source_url": official_url,
                    "source_record_id_or_canonical_row_key": source_record,
                    "market_code": market_code,
                    "instrument_code": code,
                    "canonical_identity": identity,
                    "event_type": event_type,
                    "announcement_date_if_available": None,
                    "primary_effective_date": effective_date,
                    "reference_price_if_officially_returned": _bounded_reference_price(row[4]),
                    "source_as_of_if_available": None,
                    "retrieved_at": retrieved,
                    "source_content_hash_if_storage_permitted": source_file_sha256,
                    "semantic_version": CA_EVENT_SCHEMA_VERSION,
                    "authority_state": authority_state,
                    "query_or_export_manifest_id": manifest_id,
                    "checkpoint_id": checkpoint_id,
                    "reason_code": EVENT_REASON_CODES[event_type],
                }
            )
            events.append(event)
            normalized_event_family_counts[event_type] += 1

    unique_events, duplicates = deduplicate_events(tuple(events))
    if duplicates:
        raise CorporateActionDatasetError("bounded export contains duplicate semantic events")
    checkpoint_event_keys = sorted(event.stable_event_key for event in unique_events)
    manifest = {
        "manifest_id": manifest_id,
        "source_name": source_name,
        "source_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
        "official_surface": official_surface,
        "query_window_start": WINDOW_START.isoformat(),
        "query_window_end": WINDOW_END.isoformat(),
        "retrieved_at": retrieved,
        "source_as_of_if_available": None,
        "record_count": len(unique_events),
        "content_hash_if_allowed": source_file_sha256,
        "semantic_version": CA_EVENT_SCHEMA_VERSION,
        "reference_version": REFERENCE_VERSION,
        "status": "PARTIAL",
    }
    checkpoint_base = {
        "checkpoint_id": checkpoint_id,
        "manifest_id": manifest_id,
        "dataset_version": DATASET_VERSION,
        "event_keys": checkpoint_event_keys,
        "status": "COMPLETED",
    }
    checkpoint = {
        **checkpoint_base,
        "checkpoint_hash": stable_hash(checkpoint_base),
    }
    return BoundedExportNormalization(
        source_name=source_name,
        market_code=market_code,
        source_file_name=path.name,
        source_file_sha256=source_file_sha256,
        raw_row_count=len(data_rows),
        canonical_source_rows=len(data_rows) - len(outside_audit_rows),
        canonical_identities=len(canonical_identities),
        outside_rows=len(outside_audit_rows),
        outside_identities=len(
            {
                row["instrument_code"]
                for row in outside_audit_rows
            }
        ),
        raw_event_label_counts=dict(sorted(raw_event_label_counts.items())),
        normalized_event_family_counts=dict(sorted(normalized_event_family_counts.items())),
        events=unique_events,
        outside_audit_rows=tuple(outside_audit_rows),
        manifest=manifest,
        checkpoint=checkpoint,
        source_url=official_url,
        official_surface=official_surface,
        retrieved_at=retrieved,
    )


def build_owner_bounded_import_envelope(
    normalizations: tuple[BoundedExportNormalization, ...],
) -> dict[str, Any]:
    """Combine source-specific normalized envelopes without retaining raw CSV bytes."""

    if not normalizations:
        raise CorporateActionDatasetError("at least one bounded export is required")
    source_names = [item.source_name for item in normalizations]
    if len(set(source_names)) != len(source_names):
        raise CorporateActionDatasetError("bounded export sources must be unique")
    all_events = tuple(event for item in normalizations for event in item.events)
    unique_events, duplicates = deduplicate_events(all_events)
    if duplicates:
        raise CorporateActionDatasetError("combined bounded exports contain duplicate events")
    payload: dict[str, Any] = {
        "artifact_type": "OWNER_BOUNDED_CORPORATE_ACTION_IMPORT_V0",
        "reference_version": REFERENCE_VERSION,
        "universe_policy": UNIVERSE_POLICY,
        "query_window_start": WINDOW_START.isoformat(),
        "query_window_end": WINDOW_END.isoformat(),
        "access_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
        "raw_originals": "READ_ONLY_EXTERNAL_NOT_STORED",
        "sources": [
            {
                "source_name": item.source_name,
                "market_code": item.market_code,
                "source_file_name": item.source_file_name,
                "source_file_sha256": item.source_file_sha256,
                "source_url": item.source_url,
                "official_surface": item.official_surface,
                "raw_row_count": item.raw_row_count,
                "canonical_source_rows": item.canonical_source_rows,
                "canonical_identities": item.canonical_identities,
                "outside_rows": item.outside_rows,
                "outside_identities": item.outside_identities,
                "raw_event_label_counts": item.raw_event_label_counts,
                "normalized_event_family_counts": item.normalized_event_family_counts,
                "manifest_id": item.manifest["manifest_id"],
                "checkpoint_id": item.checkpoint["checkpoint_id"],
            }
            for item in normalizations
        ],
        "manifests": [item.manifest for item in normalizations],
        "checkpoints": [item.checkpoint for item in normalizations],
        "records": [event.to_dict() for event in unique_events],
        "outside_canonical_507_audit_rows": [
            row
            for item in normalizations
            for row in item.outside_audit_rows
        ],
    }
    payload["canonical_record_count"] = len(unique_events)
    payload["outside_audit_row_count"] = len(payload["outside_canonical_507_audit_rows"])
    payload["import_content_hash"] = stable_hash(payload)
    return payload


def build_coverage_matrix(document: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Recompute exchange/family coverage without treating absence as no-event."""

    events = tuple(CorporateActionEvent.from_dict(item) for item in document["events"])
    source_coverage = document["source_coverage"]
    rows: list[dict[str, Any]] = []
    for exchange in ("TWSE", "TPEx"):
        source_status = source_coverage[exchange]["status"]
        family_status = source_coverage[exchange].get("family_status", {})
        for family in ALL_EVENT_FAMILIES:
            count = sum(
                event.source_name == exchange and event.event_type == family for event in events
            )
            if family in family_status:
                state = family_status[family]
            elif source_status == "UNKNOWN":
                state = "UNKNOWN"
            elif count:
                state = "PARTIAL"
            else:
                state = "UNKNOWN"
            rows.append(
                {
                    "exchange": exchange,
                    "event_family": family,
                    "coverage_state": state,
                    "materialized_rows": count,
                }
            )
    return tuple(rows)


def build_identity_coverage_matrix(
    document: Mapping[str, Any], *, reference_bundle_dir: Path
) -> tuple[dict[str, Any], ...]:
    """Build identity x family x window coverage without inventing event rows.

    A bounded event export proves ``COVERED_EVENT`` only for identities and
    families with materialized rows.  An absent row becomes
    ``COVERED_NO_EVENT`` only when the source metadata explicitly records a
    completed authoritative empty-set proof.  Otherwise it remains
    ``UNKNOWN``.  ``OUTSIDE_SCOPE`` is reserved for audit rows and is not
    emitted for the canonical identity matrix.
    """

    identities = sorted(_load_identity_set(reference_bundle_dir))
    events = tuple(CorporateActionEvent.from_dict(item) for item in document["events"])
    source_coverage = document["source_coverage"]
    event_counts = Counter(
        (event.canonical_identity, event.event_type) for event in events
    )
    rows: list[dict[str, Any]] = []
    for identity in identities:
        market_code, _ = identity.split(":", 1)
        exchange = {"TPE": "TWSE", "TWO": "TPEx"}.get(market_code)
        if exchange is None:
            for family in ALL_EVENT_FAMILIES:
                rows.append(
                    {
                        "canonical_identity": identity,
                        "event_family": family,
                        "window_start": document["research_window_start"],
                        "window_end": document["research_window_end"],
                        "coverage_state": "OUTSIDE_SCOPE",
                        "materialized_rows": 0,
                        "source_exchange": None,
                        "authority_basis": "IDENTITY_OUTSIDE_SUPPORTED_MARKETS",
                        "reason_code": "OUTSIDE_CANONICAL_507_OR_MARKET_SCOPE",
                    }
                )
            continue

        coverage = source_coverage[exchange]
        complete_empty_families = set(
            coverage.get("complete_empty_set_families", ())
        )
        for family in ALL_EVENT_FAMILIES:
            count = event_counts.get((identity, family), 0)
            if count:
                state = "COVERED_EVENT"
                authority_basis = "NORMALIZED_EVENT_ROW_PRESENT"
                reason_code = EVENT_REASON_CODES.get(family, "CA_EVENT_ROW_PRESENT")
            elif family in complete_empty_families:
                state = "COVERED_NO_EVENT"
                authority_basis = "EXPLICIT_COMPLETE_EMPTY_SET_PROOF"
                reason_code = "CA_COMPLETE_EMPTY_SET"
            else:
                state = "UNKNOWN"
                authority_basis = "NO_AUTHORITATIVE_ZERO_EVENT_PROOF"
                reason_code = "CA_AUTHORITY_UNKNOWN"
            rows.append(
                {
                    "canonical_identity": identity,
                    "event_family": family,
                    "window_start": document["research_window_start"],
                    "window_end": document["research_window_end"],
                    "coverage_state": state,
                    "materialized_rows": count,
                    "source_exchange": exchange,
                    "authority_basis": authority_basis,
                    "reason_code": reason_code,
                }
            )
    return tuple(rows)


def summarize_identity_coverage(
    coverage_matrix: tuple[Mapping[str, Any], ...],
    *,
    outside_scope_rows: int = 0,
    outside_scope_identities: int = 0,
) -> dict[str, Any]:
    """Aggregate identity coverage while keeping event and no-event distinct."""

    by_identity: dict[str, list[Mapping[str, Any]]] = {}
    for cell in coverage_matrix:
        state = cell.get("coverage_state")
        if state not in COVERAGE_STATES:
            raise CorporateActionDatasetError(f"invalid coverage state: {state}")
        by_identity.setdefault(str(cell["canonical_identity"]), []).append(cell)

    event_identities = {
        identity
        for identity, cells in by_identity.items()
        if any(cell["coverage_state"] == "COVERED_EVENT" for cell in cells)
    }
    no_event_identities = {
        identity
        for identity, cells in by_identity.items()
        if cells
        and all(cell["coverage_state"] == "COVERED_NO_EVENT" for cell in cells)
    }
    unknown_identities = set(by_identity) - event_identities - no_event_identities
    state_counts = Counter(cell["coverage_state"] for cell in coverage_matrix)
    return {
        "identity_count": len(by_identity),
        "event_identities": len(event_identities),
        "covered_identities": len(event_identities | no_event_identities),
        "no_event_identities": len(no_event_identities),
        "unknown_identities": len(unknown_identities),
        "outside_scope_rows": outside_scope_rows,
        "outside_scope_identities": outside_scope_identities,
        "coverage_cell_counts": dict(sorted(state_counts.items())),
        "identity_state_rule": (
            "EVENT if any family is COVERED_EVENT; NO_EVENT only if every family is "
            "COVERED_NO_EVENT; otherwise UNKNOWN"
        ),
    }


def build_identity_coverage_artifact(
    document: Mapping[str, Any],
    *,
    reference_bundle_dir: Path,
    outside_scope_rows: int = 0,
    outside_scope_identities: int = 0,
) -> dict[str, Any]:
    """Return a deterministic, metadata-only coverage reassessment artifact."""

    matrix = build_identity_coverage_matrix(
        document, reference_bundle_dir=reference_bundle_dir
    )
    payload: dict[str, Any] = {
        "artifact_type": "REC_A1_IDENTITY_EVENT_FAMILY_WINDOW_COVERAGE_V0",
        "coverage_schema_version": "rec-a1-identity-event-family-window-coverage.v0",
        "dataset_version": document["dataset_version"],
        "reference_version": document["reference_version"],
        "universe_policy": document["universe_policy"],
        "research_window_start": document["research_window_start"],
        "research_window_end": document["research_window_end"],
        "coverage_states": sorted(COVERAGE_STATES),
        "summary": summarize_identity_coverage(
            matrix,
            outside_scope_rows=outside_scope_rows,
            outside_scope_identities=outside_scope_identities,
        ),
        "outside_scope": {
            "coverage_state": "OUTSIDE_SCOPE",
            "rows": outside_scope_rows,
            "identities": outside_scope_identities,
            "canonical_dataset_inclusion": "EXCLUDED",
            "classification_basis": (
                "Exact (market_code, instrument_code) lookup against tw-reference-v1; "
                "outside rows remain audit rows"
            ),
        },
        "cells": list(matrix),
    }
    payload["coverage_content_hash"] = stable_hash(payload)
    return payload


def build_reviewed_residual_coverage_metadata(
    coverage_summary: Mapping[str, Any],
    *,
    reviewed_unknown_identities: int,
    unreviewed_unknown_identities: int,
    confirmed_additional_event_identities: int,
    authoritative_no_event_identities: int,
    no_event_found_in_bounded_review: bool,
    residual_unknown_accepted: bool,
    owner_risk_acceptance: bool,
    lineage_complete: bool,
    fail_closed_outcome_policy_present: bool,
    unresolved_confirmed_continuity_events: int,
    dataset_rows_before: int,
    dataset_rows_after: int,
) -> dict[str, Any]:
    """Build freeze-risk metadata without changing factual coverage states."""

    if reviewed_unknown_identities < 0 or unreviewed_unknown_identities < 0:
        raise CorporateActionDatasetError("reviewed identity counts must be non-negative")
    if confirmed_additional_event_identities < 0:
        raise CorporateActionDatasetError("confirmed event identity count must be non-negative")
    if authoritative_no_event_identities < 0:
        raise CorporateActionDatasetError(
            "authoritative no-event identity count must be non-negative"
        )
    if unresolved_confirmed_continuity_events < 0:
        raise CorporateActionDatasetError(
            "unresolved confirmed continuity count must be non-negative"
        )
    if dataset_rows_before < 0 or dataset_rows_after < 0:
        raise CorporateActionDatasetError("dataset row counts must be non-negative")
    if coverage_summary.get("unknown_identities") != (
        reviewed_unknown_identities + unreviewed_unknown_identities
    ):
        raise CorporateActionDatasetError(
            "reviewed and unreviewed unknown counts do not match coverage summary"
        )
    if confirmed_additional_event_identities or authoritative_no_event_identities:
        raise CorporateActionDatasetError(
            "this residual-uncertainty policy cannot silently absorb new event or "
            "no-event identities"
        )
    if dataset_rows_before != dataset_rows_after:
        raise CorporateActionDatasetError(
            "dataset rows changed during risk acceptance reassessment"
        )
    metadata = {
        "review_state": (
            "REVIEWED_UNKNOWN_NO_EVENT_FOUND"
            if reviewed_unknown_identities
            else "UNREVIEWED_UNKNOWN"
        ),
        "reviewed_unknown_identities": reviewed_unknown_identities,
        "unreviewed_unknown_identities": unreviewed_unknown_identities,
        "confirmed_additional_event_identities": confirmed_additional_event_identities,
        "authoritative_no_event_identities": authoritative_no_event_identities,
        "no_event_found_in_bounded_review": no_event_found_in_bounded_review,
        "residual_unknown_accepted": residual_unknown_accepted,
        "owner_risk_acceptance": owner_risk_acceptance,
        "freeze_policy": "BEST_EFFORT_RESEARCH_INTEGRITY_WITH_REVIEWED_RESIDUAL_UNCERTAINTY",
        "residual_risk_classification": "BOUNDED_RESEARCH_DATA_UNCERTAINTY",
        "lineage_complete": lineage_complete,
        "fail_closed_outcome_policy_present": fail_closed_outcome_policy_present,
        "unresolved_confirmed_continuity_events": unresolved_confirmed_continuity_events,
        "dataset_rows_before": dataset_rows_before,
        "dataset_rows_after": dataset_rows_after,
        "coverage_summary": {
            "canonical_identities": coverage_summary.get("identity_count", 0),
            "event_identities": coverage_summary.get("event_identities", 0),
            "authoritative_no_event_identities": coverage_summary.get(
                "no_event_identities", 0
            ),
            "unknown_identities": coverage_summary.get("unknown_identities", 0),
            "coverage_states_preserved": True,
        },
        "outcome_integrity": {
            "event_excluded_raw_policy": "READY",
            "trading_decision_use": "FORBIDDEN",
            "post_hoc_outcome_integrity_exclusion": "ALLOWED",
        },
    }
    validate_reviewed_residual_coverage_metadata(metadata)
    return metadata


def validate_reviewed_residual_coverage_metadata(
    metadata: Mapping[str, Any],
) -> None:
    """Validate the explicit reviewed-residual freeze acceptance contract."""

    required = {
        "review_state",
        "reviewed_unknown_identities",
        "unreviewed_unknown_identities",
        "confirmed_additional_event_identities",
        "authoritative_no_event_identities",
        "no_event_found_in_bounded_review",
        "residual_unknown_accepted",
        "owner_risk_acceptance",
        "freeze_policy",
        "residual_risk_classification",
        "lineage_complete",
        "fail_closed_outcome_policy_present",
        "unresolved_confirmed_continuity_events",
        "dataset_rows_before",
        "dataset_rows_after",
        "coverage_summary",
        "outcome_integrity",
    }
    if set(metadata) != required:
        raise CorporateActionDatasetError(
            "reviewed residual metadata fields do not match the contract"
        )
    review_state = metadata["review_state"]
    if review_state not in REVIEW_STATES:
        raise CorporateActionDatasetError(f"unsupported review_state: {review_state}")
    for field in (
        "reviewed_unknown_identities",
        "unreviewed_unknown_identities",
        "confirmed_additional_event_identities",
        "authoritative_no_event_identities",
        "unresolved_confirmed_continuity_events",
        "dataset_rows_before",
        "dataset_rows_after",
    ):
        value = metadata[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise CorporateActionDatasetError(f"{field} must be a non-negative integer")
    for field in (
        "no_event_found_in_bounded_review",
        "residual_unknown_accepted",
        "owner_risk_acceptance",
        "lineage_complete",
        "fail_closed_outcome_policy_present",
    ):
        if not isinstance(metadata[field], bool):
            raise CorporateActionDatasetError(f"{field} must be boolean")
    if metadata["freeze_policy"] not in FREEZE_POLICIES:
        raise CorporateActionDatasetError("unsupported freeze_policy")
    if metadata["residual_risk_classification"] not in RESIDUAL_RISK_CLASSIFICATIONS:
        raise CorporateActionDatasetError("unsupported residual_risk_classification")
    coverage = metadata["coverage_summary"]
    if not isinstance(coverage, dict):
        raise CorporateActionDatasetError("coverage_summary must be an object")
    if coverage.get("unknown_identities") != (
        metadata["reviewed_unknown_identities"]
        + metadata["unreviewed_unknown_identities"]
    ):
        raise CorporateActionDatasetError(
            "coverage unknown count does not match review state counts"
        )
    if coverage.get("coverage_states_preserved") is not True:
        raise CorporateActionDatasetError("coverage states must remain factual and preserved")
    outcome = metadata["outcome_integrity"]
    if outcome != {
        "event_excluded_raw_policy": "READY",
        "trading_decision_use": "FORBIDDEN",
        "post_hoc_outcome_integrity_exclusion": "ALLOWED",
    }:
        raise CorporateActionDatasetError("outcome integrity policy is not fail-closed")
    if metadata["review_state"] == "REVIEWED_UNKNOWN_NO_EVENT_FOUND":
        if metadata["reviewed_unknown_identities"] == 0:
            raise CorporateActionDatasetError("reviewed state requires reviewed unknown identities")
        if not (
            metadata["no_event_found_in_bounded_review"]
            and metadata["residual_unknown_accepted"]
            and metadata["owner_risk_acceptance"]
        ):
            raise CorporateActionDatasetError(
                "reviewed residual acceptance predicates are incomplete"
            )



@dataclass(frozen=True)
class FreezeGateDecision:
    authorized: bool
    reasons: tuple[str, ...]


def evaluate_freeze_gate(
    coverage_matrix: tuple[Mapping[str, Any], ...],
    stats: DatasetValidationStats,
    *,
    complete_empty_set_validated: bool,
    controls_passed: bool,
    identity_coverage_summary: Mapping[str, Any] | None = None,
    reviewed_residual_metadata: Mapping[str, Any] | None = None,
) -> FreezeGateDecision:
    """Evaluate Freeze with an explicit reviewed-residual exception policy."""

    reasons: list[str] = []
    reviewed_residual_allowed = False
    if reviewed_residual_metadata is not None:
        try:
            validate_reviewed_residual_coverage_metadata(reviewed_residual_metadata)
        except CorporateActionDatasetError:
            reasons.append("REVIEWED_RESIDUAL_METADATA_INVALID")
        else:
            reviewed_residual_allowed = (
                reviewed_residual_metadata["review_state"]
                == "REVIEWED_UNKNOWN_NO_EVENT_FOUND"
                and reviewed_residual_metadata["reviewed_unknown_identities"] > 0
                and reviewed_residual_metadata["unreviewed_unknown_identities"] == 0
                and reviewed_residual_metadata["no_event_found_in_bounded_review"]
                and reviewed_residual_metadata["residual_unknown_accepted"]
                and reviewed_residual_metadata["owner_risk_acceptance"]
                and reviewed_residual_metadata["lineage_complete"]
                and reviewed_residual_metadata["fail_closed_outcome_policy_present"]
                and reviewed_residual_metadata["unresolved_confirmed_continuity_events"] == 0
                and reviewed_residual_metadata["dataset_rows_before"]
                == reviewed_residual_metadata["dataset_rows_after"]
            )
            if not reviewed_residual_allowed:
                reasons.append("REVIEWED_RESIDUAL_ACCEPTANCE_PREDICATES_INCOMPLETE")
    if not reviewed_residual_allowed:
        for cell in coverage_matrix:
            if (
                cell["event_family"] in PRIMARY_EVENT_FAMILIES
                and cell["coverage_state"] != "COMPLETE"
            ):
                reasons.append(
                    f"{cell['exchange']}:{cell['event_family']}={cell['coverage_state']}"
                )
    covered_identities = stats.covered_identities
    if identity_coverage_summary is not None:
        covered_identities = int(
            identity_coverage_summary.get("covered_identities", covered_identities)
        )
        unknown_identities = int(
            identity_coverage_summary.get("unknown_identities", 0)
        )
        if unknown_identities and not reviewed_residual_allowed:
            reasons.append("UNKNOWN_IDENTITY_COVERAGE")
    if covered_identities < 507 and not reviewed_residual_allowed:
        reasons.append("COVERED_IDENTITIES_LT_CURRENT_507")
    if not complete_empty_set_validated and not reviewed_residual_allowed:
        reasons.append("COMPLETE_EMPTY_SET_NOT_VALIDATED")
    if not controls_passed:
        reasons.append("CONTROL_CASES_NOT_PASSED")
    if (
        stats.duplicates
        or stats.invalid_identities
        or stats.invalid_effective_dates
        or stats.missing_lineage
        or stats.semantic_hash_collisions
    ):
        reasons.append("DATASET_VALIDATION_ERRORS")
    return FreezeGateDecision(not reasons, tuple(reasons))


@dataclass(frozen=True)
class DatasetManifest:
    manifest_id: str
    source_name: str
    source_method: str
    official_surface: str
    query_window_start: str
    query_window_end: str
    retrieved_at: str
    source_as_of_if_available: str | None
    record_count: int
    content_hash_if_allowed: str | None
    semantic_version: str
    reference_version: str
    status: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DatasetManifest:
        expected = {
            "manifest_id",
            "source_name",
            "source_method",
            "official_surface",
            "query_window_start",
            "query_window_end",
            "retrieved_at",
            "source_as_of_if_available",
            "record_count",
            "content_hash_if_allowed",
            "semantic_version",
            "reference_version",
            "status",
        }
        if set(payload) != expected:
            raise CorporateActionDatasetError("manifest fields do not match the contract")
        record_count = payload["record_count"]
        if (
            not isinstance(record_count, int)
            or isinstance(record_count, bool)
            or record_count < 0
        ):
            raise CorporateActionDatasetError(
                "manifest record_count must be a non-negative integer"
            )
        status = _text(payload["status"], "manifest.status").upper()
        if status not in {"READY", "PARTIAL", "UNKNOWN"}:
            raise CorporateActionDatasetError("manifest status is invalid")
        return cls(
            manifest_id=_text(payload["manifest_id"], "manifest_id"),
            source_name=_text(payload["source_name"], "manifest.source_name"),
            source_method=_text(payload["source_method"], "manifest.source_method"),
            official_surface=_text(payload["official_surface"], "manifest.official_surface"),
            query_window_start=_iso_date(payload["query_window_start"], "query_window_start"),
            query_window_end=_iso_date(payload["query_window_end"], "query_window_end"),
            retrieved_at=_iso_timestamp(payload["retrieved_at"], "manifest.retrieved_at"),
            source_as_of_if_available=_iso_date(
                payload["source_as_of_if_available"],
                "manifest.source_as_of_if_available",
                optional=True,
            ),
            record_count=record_count,
            content_hash_if_allowed=_hash(
                payload["content_hash_if_allowed"],
                "manifest.content_hash_if_allowed",
                optional=True,
            ),
            semantic_version=_text(payload["semantic_version"], "manifest.semantic_version"),
            reference_version=_text(payload["reference_version"], "manifest.reference_version"),
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "source_name": self.source_name,
            "source_method": self.source_method,
            "official_surface": self.official_surface,
            "query_window_start": self.query_window_start,
            "query_window_end": self.query_window_end,
            "retrieved_at": self.retrieved_at,
            "source_as_of_if_available": self.source_as_of_if_available,
            "record_count": self.record_count,
            "content_hash_if_allowed": self.content_hash_if_allowed,
            "semantic_version": self.semantic_version,
            "reference_version": self.reference_version,
            "status": self.status,
        }


@dataclass(frozen=True)
class DatasetCheckpoint:
    checkpoint_id: str
    manifest_id: str
    dataset_version: str
    event_keys: tuple[str, ...]
    status: str
    checkpoint_hash: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DatasetCheckpoint:
        expected = {
            "checkpoint_id",
            "manifest_id",
            "dataset_version",
            "event_keys",
            "status",
            "checkpoint_hash",
        }
        if set(payload) != expected:
            raise CorporateActionDatasetError("checkpoint fields do not match the contract")
        event_keys = payload["event_keys"]
        if not isinstance(event_keys, list) or not all(
            isinstance(item, str) for item in event_keys
        ):
            raise CorporateActionDatasetError("checkpoint.event_keys must be a string list")
        if event_keys != sorted(set(event_keys)):
            raise CorporateActionDatasetError("checkpoint.event_keys must be sorted and unique")
        status = _text(payload["status"], "checkpoint.status").upper()
        if status != "COMPLETED":
            raise CorporateActionDatasetError("checkpoint status must be COMPLETED")
        checkpoint = cls(
            checkpoint_id=_text(payload["checkpoint_id"], "checkpoint_id"),
            manifest_id=_text(payload["manifest_id"], "checkpoint.manifest_id"),
            dataset_version=_text(payload["dataset_version"], "checkpoint.dataset_version"),
            event_keys=tuple(event_keys),
            status=status,
            checkpoint_hash=_hash(payload["checkpoint_hash"], "checkpoint_hash") or "",
        )
        expected_hash = stable_hash(
            {
                "checkpoint_id": checkpoint.checkpoint_id,
                "manifest_id": checkpoint.manifest_id,
                "dataset_version": checkpoint.dataset_version,
                "event_keys": list(checkpoint.event_keys),
                "status": checkpoint.status,
            }
        )
        if checkpoint.checkpoint_hash != expected_hash:
            raise CorporateActionDatasetError("checkpoint_hash mismatch")
        return checkpoint

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "manifest_id": self.manifest_id,
            "dataset_version": self.dataset_version,
            "event_keys": list(self.event_keys),
            "status": self.status,
            "checkpoint_hash": self.checkpoint_hash,
        }


@dataclass(frozen=True)
class DatasetValidationStats:
    dataset_rows: int
    twse_rows: int
    tpex_rows: int
    unknown_rows: int
    covered_identities: int
    covered_events: int
    date_range: tuple[str, str] | None
    duplicates: int
    invalid_identities: int
    invalid_effective_dates: int
    missing_lineage: int
    semantic_hash_collisions: int


def _canonical_dataset_payload(document: Mapping[str, Any]) -> dict[str, Any]:
    payload = {key: value for key, value in document.items() if key != "dataset_content_hash"}
    for key in ("manifests", "checkpoints", "events"):
        if isinstance(payload.get(key), list):
            sort_key = {
                "manifests": "manifest_id",
                "checkpoints": "checkpoint_id",
                "events": "stable_event_key",
            }[key]
            payload[key] = sorted(payload[key], key=lambda item: item[sort_key])
    return payload


def dataset_content_hash(document: Mapping[str, Any]) -> str:
    return stable_hash(_canonical_dataset_payload(document))


def _load_identity_set(reference_bundle_dir: Path) -> frozenset[str]:
    bundle = load_bundle(reference_bundle_dir)
    if bundle.manifest.get("referenceDataVersion") != REFERENCE_VERSION:
        raise CorporateActionDatasetError("reference bundle version mismatch")
    return frozenset(f"{row['market_code']}:{row['instrument_code']}" for row in bundle.instruments)


def validate_dataset_document(
    document: Mapping[str, Any], *, reference_bundle_dir: Path | None = None
) -> DatasetValidationStats:
    required = {
        "artifact_type",
        "dataset_schema_version",
        "dataset_version",
        "semantic_version",
        "reference_version",
        "research_window_start",
        "research_window_end",
        "universe_policy",
        "source_method_version",
        "storage_policy",
        "source_coverage",
        "manifests",
        "checkpoints",
        "events",
        "dataset_content_hash",
    }
    if set(document) != required:
        raise CorporateActionDatasetError("dataset fields do not match the contract")
    if document["artifact_type"] != "NORMALIZED_SEMANTIC_DATASET":
        raise CorporateActionDatasetError("artifact must be a normalized semantic dataset")
    if document["dataset_schema_version"] != DATASET_SCHEMA_VERSION:
        raise CorporateActionDatasetError("unsupported dataset schema version")
    if document["dataset_version"] != DATASET_VERSION:
        raise CorporateActionDatasetError("unsupported dataset version")
    if document["semantic_version"] != CA_EVENT_SCHEMA_VERSION:
        raise CorporateActionDatasetError("dataset semantic version mismatch")
    if document["reference_version"] != REFERENCE_VERSION:
        raise CorporateActionDatasetError("dataset reference version mismatch")
    if document["research_window_start"] != WINDOW_START.isoformat():
        raise CorporateActionDatasetError("dataset research window start mismatch")
    if document["research_window_end"] != WINDOW_END.isoformat():
        raise CorporateActionDatasetError("dataset research window end mismatch")
    if document["universe_policy"] != UNIVERSE_POLICY:
        raise CorporateActionDatasetError("dataset universe policy mismatch")
    source_coverage = document["source_coverage"]
    if not isinstance(source_coverage, dict) or set(source_coverage) != {"TWSE", "TPEx"}:
        raise CorporateActionDatasetError("source_coverage must define TWSE and TPEx")
    for exchange, coverage in source_coverage.items():
        if not isinstance(coverage, dict):
            raise CorporateActionDatasetError(f"{exchange} coverage must be an object")
        if coverage.get("status") not in {"READY", "PARTIAL", "UNKNOWN"}:
            raise CorporateActionDatasetError(f"{exchange} coverage status is invalid")
        if (
            not isinstance(coverage.get("rows"), int)
            or isinstance(coverage.get("rows"), bool)
            or coverage["rows"] < 0
        ):
            raise CorporateActionDatasetError(f"{exchange} coverage rows must be non-negative")
        _text(coverage.get("coverage_basis"), f"{exchange}.coverage_basis")
    storage_policy = document["storage_policy"]
    if (
        not isinstance(storage_policy, dict)
        or storage_policy.get("raw_source_artifact") != "NOT_STORED"
    ):
        raise CorporateActionDatasetError("raw source artifact must remain outside this dataset")
    if storage_policy.get("normalized_semantic_dataset") != "RESEARCH_ONLY":
        raise CorporateActionDatasetError("dataset storage must be research-only")

    manifests_payload = document["manifests"]
    checkpoints_payload = document["checkpoints"]
    events_payload = document["events"]
    if not all(
        isinstance(items, list) and all(isinstance(item, dict) for item in items)
        for items in (manifests_payload, checkpoints_payload, events_payload)
    ):
        raise CorporateActionDatasetError("manifests, checkpoints, and events must be lists")
    manifests = tuple(DatasetManifest.from_dict(item) for item in manifests_payload)
    checkpoints = tuple(DatasetCheckpoint.from_dict(item) for item in checkpoints_payload)
    events = tuple(CorporateActionEvent.from_dict(item) for item in events_payload)
    manifest_by_id = {item.manifest_id: item for item in manifests}
    checkpoint_by_id = {item.checkpoint_id: item for item in checkpoints}
    if len(manifest_by_id) != len(manifests) or len(checkpoint_by_id) != len(checkpoints):
        raise CorporateActionDatasetError("manifest/checkpoint IDs must be unique")
    event_keys = [item.stable_event_key for item in events]
    duplicates = len(event_keys) - len(set(event_keys))
    if duplicates:
        raise CorporateActionDatasetError("duplicate stable event key")
    hash_counts = Counter(item.normalized_semantic_hash for item in events)
    semantic_hash_collisions = sum(count - 1 for count in hash_counts.values() if count > 1)
    if semantic_hash_collisions:
        raise CorporateActionDatasetError("normalized semantic hash collision")
    for event in events:
        manifest = manifest_by_id.get(event.query_or_export_manifest_id)
        checkpoint = checkpoint_by_id.get(event.checkpoint_id)
        if manifest is None or checkpoint is None:
            raise CorporateActionDatasetError(
                "event lineage points to a missing manifest/checkpoint"
            )
        if event.semantic_version != manifest.semantic_version:
            raise CorporateActionDatasetError("event/manifest semantic version mismatch")
        if (
            checkpoint.manifest_id != manifest.manifest_id
            or event.stable_event_key not in checkpoint.event_keys
        ):
            raise CorporateActionDatasetError("event checkpoint lineage mismatch")
    for manifest in manifests:
        count = sum(item.query_or_export_manifest_id == manifest.manifest_id for item in events)
        if count != manifest.record_count:
            raise CorporateActionDatasetError("manifest record_count mismatch")
    for checkpoint in checkpoints:
        if not set(checkpoint.event_keys).issubset(set(event_keys)):
            raise CorporateActionDatasetError("checkpoint contains an unknown event key")
    source_row_counts = {
        "TWSE": sum(item.source_name == "TWSE" for item in events),
        "TPEx": sum(item.source_name == "TPEx" for item in events),
    }
    if any(source_coverage[key]["rows"] != value for key, value in source_row_counts.items()):
        raise CorporateActionDatasetError("source coverage row counts do not match events")

    identities = _load_identity_set(reference_bundle_dir) if reference_bundle_dir else None
    invalid_identities = 0
    for event in events:
        if identities is not None and event.canonical_identity not in identities:
            invalid_identities += 1
    if invalid_identities:
        raise CorporateActionDatasetError("event identity is not in tw-reference-v1")
    invalid_effective_dates = sum(
        not WINDOW_START <= date.fromisoformat(item.primary_effective_date) <= WINDOW_END
        for item in events
    )
    if invalid_effective_dates:
        raise CorporateActionDatasetError("event effective date is outside the research window")
    missing_lineage = sum(
        not all(
            getattr(item, field)
            for field in (
                "source_name",
                "official_product_or_surface",
                "access_method",
                "source_url",
                "source_record_id_or_canonical_row_key",
                "query_or_export_manifest_id",
                "checkpoint_id",
                "normalized_semantic_hash",
            )
        )
        for item in events
    )
    if missing_lineage:
        raise CorporateActionDatasetError("event lineage is incomplete")
    if document["dataset_content_hash"] != dataset_content_hash(document):
        raise CorporateActionDatasetError("dataset_content_hash mismatch")
    if events:
        dates = sorted(item.primary_effective_date for item in events)
        date_range: tuple[str, str] | None = (dates[0], dates[-1])
    else:
        date_range = None
    return DatasetValidationStats(
        dataset_rows=len(events),
        twse_rows=source_row_counts["TWSE"],
        tpex_rows=source_row_counts["TPEx"],
        unknown_rows=sum(item.authority_state == "UNKNOWN" for item in events),
        covered_identities=len({item.canonical_identity for item in events}),
        covered_events=len(events),
        date_range=date_range,
        duplicates=duplicates,
        invalid_identities=invalid_identities,
        invalid_effective_dates=invalid_effective_dates,
        missing_lineage=missing_lineage,
        semantic_hash_collisions=semantic_hash_collisions,
    )


def load_dataset(path: Path, *, reference_bundle_dir: Path | None = None) -> DatasetValidationStats:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorporateActionDatasetError(f"cannot read dataset artifact: {path}") from exc
    if not isinstance(document, dict):
        raise CorporateActionDatasetError("dataset artifact must be a JSON object")
    return validate_dataset_document(document, reference_bundle_dir=reference_bundle_dir)


def export_dataset_document(document: Mapping[str, Any]) -> str:
    """Export a canonical JSON representation without mutating the input."""

    canonical = _canonical_dataset_payload(document)
    canonical["dataset_content_hash"] = dataset_content_hash(canonical)
    return json.dumps(canonical, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def merge_owner_bounded_import_into_dataset(
    document: Mapping[str, Any], import_payload: Mapping[str, Any]
) -> dict[str, Any]:
    """Merge normalized owner records while replacing same-semantic prior rows."""

    if import_payload.get("artifact_type") != "OWNER_BOUNDED_CORPORATE_ACTION_IMPORT_V0":
        raise CorporateActionDatasetError("unsupported owner bounded import artifact")
    if import_payload.get("import_content_hash") != stable_hash(
        {key: value for key, value in import_payload.items() if key != "import_content_hash"}
    ):
        raise CorporateActionDatasetError("owner bounded import_content_hash mismatch")
    records = import_payload.get("records")
    sources = import_payload.get("sources")
    manifests_payload = import_payload.get("manifests")
    checkpoints_payload = import_payload.get("checkpoints")
    if not all(
        isinstance(items, list) and all(isinstance(item, dict) for item in items)
        for items in (records, sources, manifests_payload, checkpoints_payload)
    ):
        raise CorporateActionDatasetError("owner bounded import collections are invalid")
    imported_events = tuple(CorporateActionEvent.from_dict(item) for item in records)
    imported_keys = {
        (
            event.market_code,
            event.instrument_code,
            event.event_type,
            event.primary_effective_date,
        )
        for event in imported_events
    }
    existing_events = tuple(
        CorporateActionEvent.from_dict(item)
        for item in document.get("events", [])
        if (
            item.get("market_code"),
            item.get("instrument_code"),
            item.get("event_type"),
            item.get("primary_effective_date"),
        )
        not in imported_keys
    )
    merged_events = tuple(
        sorted(
            (*existing_events, *imported_events),
            key=lambda event: event.stable_event_key,
        )
    )
    event_keys = {event.stable_event_key for event in merged_events}

    manifests = [*document.get("manifests", []), *manifests_payload]
    manifest_by_id = {manifest["manifest_id"]: manifest for manifest in manifests}
    kept_manifests = [
        manifest
        for manifest in manifest_by_id.values()
        if any(
            event.query_or_export_manifest_id == manifest["manifest_id"]
            for event in merged_events
        )
    ]
    checkpoints = [*document.get("checkpoints", []), *checkpoints_payload]
    checkpoint_by_id = {checkpoint["checkpoint_id"]: checkpoint for checkpoint in checkpoints}
    kept_checkpoints = [
        checkpoint
        for checkpoint in checkpoint_by_id.values()
        if checkpoint["checkpoint_id"] in {event.checkpoint_id for event in merged_events}
        and set(checkpoint["event_keys"]).issubset(event_keys)
    ]

    source_summaries = {source["source_name"]: source for source in sources}
    source_coverage: dict[str, Any] = {}
    for exchange in ("TWSE", "TPEx"):
        source_events = [event for event in merged_events if event.source_name == exchange]
        summary = source_summaries.get(exchange)
        family_status = {
            family: (
                "PARTIAL"
                if any(event.event_type == family for event in source_events)
                else "UNKNOWN"
            )
            for family in PRIMARY_EVENT_FAMILIES + SEMANTIC_PARTIAL_EVENT_FAMILIES
        }
        if exchange == "TWSE" and any(
            event.event_type == "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY"
            for event in source_events
        ):
            family_status["LISTING_TERMINATION_RESUMPTION_DISCONTINUITY"] = "PARTIAL"
        source_coverage[exchange] = {
            "status": "PARTIAL",
            "rows": len(source_events),
            "coverage_basis": (
                f"Owner bounded export: {summary['canonical_source_rows']} canonical source rows, "
                f"{summary['canonical_identities']} identities, "
                f"{summary['outside_rows']} outside rows; lifecycle controls retained"
                if summary is not None
                else "Canonical lifecycle evidence retained"
            ),
            "raw_row_count": summary["raw_row_count"] if summary is not None else 0,
            "canonical_source_rows": (
                summary["canonical_source_rows"] if summary is not None else 0
            ),
            "canonical_identities": summary["canonical_identities"] if summary else 0,
            "outside_rows": summary["outside_rows"] if summary else 0,
            "outside_identities": summary["outside_identities"] if summary else 0,
            "family_status": family_status,
        }

    merged = {
        **document,
        "source_coverage": source_coverage,
        "manifests": sorted(kept_manifests, key=lambda item: item["manifest_id"]),
        "checkpoints": sorted(kept_checkpoints, key=lambda item: item["checkpoint_id"]),
        "events": [event.to_dict() for event in merged_events],
    }
    merged["dataset_content_hash"] = dataset_content_hash(merged)
    return merged


def deduplicate_events(
    events: tuple[CorporateActionEvent, ...],
) -> tuple[tuple[CorporateActionEvent, ...], int]:
    """Return deterministic reuse output and the number of duplicate inputs."""

    by_key: dict[str, CorporateActionEvent] = {}
    duplicates = 0
    for event in events:
        if event.stable_event_key in by_key:
            duplicates += 1
            if by_key[event.stable_event_key] != event:
                raise CorporateActionDatasetError("same event key has conflicting semantic rows")
        else:
            by_key[event.stable_event_key] = event
    return tuple(by_key[key] for key in sorted(by_key)), duplicates


def classify_empty_query(
    *,
    query_completed: bool,
    authority_sufficient: bool,
    scope_explicit: bool,
    response_proves_empty: bool,
) -> str:
    """Implement the strict empty-set versus unknown contract."""

    if query_completed and authority_sufficient and scope_explicit and response_proves_empty:
        return "PASS_NO_EVENT"
    return "CA_AUTHORITY_UNKNOWN"


@dataclass(frozen=True)
class EpisodeWindow:
    feature_start: date
    signal_date: date
    trigger_dates: tuple[date, ...]
    execution_date: date
    outcome_dates: tuple[date, ...]


@dataclass(frozen=True)
class EpisodeExclusion:
    excluded: bool
    primary_reason: str | None
    matches: tuple[tuple[str, str], ...]


def evaluate_episode(
    events: tuple[CorporateActionEvent, ...], episode: EpisodeWindow
) -> EpisodeExclusion:
    """Apply only post-hoc integrity overlap rules; never alter signal facts."""

    matches: list[tuple[str, str]] = []
    for event in sorted(events, key=lambda item: item.stable_event_key):
        effective = date.fromisoformat(event.primary_effective_date)
        reason = event.reason_code if event.authority_state != "UNKNOWN" else "CA_AUTHORITY_UNKNOWN"
        if episode.feature_start <= effective <= episode.signal_date:
            matches.append(("PRE_SIGNAL_FEATURE_CONTAMINATION", reason))
        if effective in episode.trigger_dates:
            matches.append(("TRIGGER_WINDOW_CONTAMINATION", reason))
        if effective == episode.execution_date:
            matches.append(("EXECUTION_CONTAMINATION", reason))
        if effective in episode.outcome_dates:
            matches.append(("OUTCOME_CONTAMINATION", reason))
    return EpisodeExclusion(bool(matches), matches[0][0] if matches else None, tuple(matches))


__all__ = [
    "ALL_EVENT_FAMILIES",
    "CA_EVENT_SCHEMA_VERSION",
    "COVERAGE_STATES",
    "DATASET_SCHEMA_VERSION",
    "DATASET_VERSION",
    "FREEZE_POLICIES",
    "PRIMARY_EVENT_FAMILIES",
    "REFERENCE_VERSION",
    "RESIDUAL_RISK_CLASSIFICATIONS",
    "REVIEW_STATES",
    "SEMANTIC_PARTIAL_EVENT_FAMILIES",
    "TPEX_BOUNDED_ARTIFACT_REQUIREMENTS",
    "UNIVERSE_POLICY",
    "WINDOW_END",
    "WINDOW_START",
    "BoundedExportNormalization",
    "CorporateActionDatasetError",
    "CorporateActionEvent",
    "DatasetValidationStats",
    "EpisodeExclusion",
    "EpisodeWindow",
    "FreezeGateDecision",
    "TpexBoundedArtifactRequirements",
    "build_coverage_matrix",
    "build_event",
    "build_identity_coverage_artifact",
    "build_identity_coverage_matrix",
    "build_owner_bounded_import_envelope",
    "build_reviewed_residual_coverage_metadata",
    "classify_empty_query",
    "dataset_content_hash",
    "deduplicate_events",
    "evaluate_episode",
    "evaluate_freeze_gate",
    "export_dataset_document",
    "load_dataset",
    "merge_owner_bounded_import_into_dataset",
    "normalize_official_bounded_csv",
    "parse_tpex_bounded_artifact",
    "stable_event_key",
    "summarize_identity_coverage",
    "validate_dataset_document",
    "validate_reviewed_residual_coverage_metadata",
]
