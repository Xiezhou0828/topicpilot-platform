"""Deterministic ``tw-reference-v1`` bundle generation and validation.

The bundle is an offline artifact.  It is generated from an approved V1 stock
export plus explicit calendar, status-evidence, and adjustment-governance
inputs.  Database mutation is deliberately implemented in
``reference_data.bootstrap`` rather than in this module.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from topicpilot_api.market_data.history import DAILY_TRADING_STATUS_CODES

BUNDLE_SCHEMA_VERSION = "reference-bundle.v1"
BUNDLE_FILE_NAMES = (
    "markets.json",
    "instruments.json",
    "currencies.json",
    "timezones.json",
    "sessions.json",
    "trading_statuses.json",
    "adjustments.json",
    "calendar_dates.json",
    "evidence.json",
)
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REQUIRED_STOCK_HEADERS = ("股號", "名稱", "市場代碼")
_MARKET_DEFINITIONS = {
    "TPE": {
        "code": "TPE",
        "name": "TWSE Listed",
        "exchange_code": "TWSE",
        "timezone": "Asia/Taipei",
        "calendar_code": "TW_MARKET",
        "session_code": "REGULAR",
    },
    "TWO": {
        "code": "TWO",
        "name": "TPEx OTC",
        "exchange_code": "TPEx",
        "timezone": "Asia/Taipei",
        "calendar_code": "TW_MARKET",
        "session_code": "REGULAR",
    },
}


class BundleValidationError(ValueError):
    """Raised when a canonical bundle cannot be safely loaded or applied."""


@dataclass(frozen=True)
class ReferenceBundle:
    manifest: dict[str, Any]
    markets: tuple[dict[str, Any], ...]
    instruments: tuple[dict[str, Any], ...]
    currencies: tuple[dict[str, Any], ...]
    timezones: tuple[dict[str, Any], ...]
    sessions: tuple[dict[str, Any], ...]
    trading_statuses: tuple[dict[str, Any], ...]
    adjustments: tuple[dict[str, Any], ...]
    calendar_dates: tuple[dict[str, Any], ...]
    evidence: dict[str, Any]

    def data_payload(self) -> dict[str, Any]:
        return {
            "markets": list(self.markets),
            "instruments": list(self.instruments),
            "currencies": list(self.currencies),
            "timezones": list(self.timezones),
            "sessions": list(self.sessions),
            "tradingStatuses": list(self.trading_statuses),
            "adjustments": list(self.adjustments),
            "calendarDates": list(self.calendar_dates),
            "evidence": self.evidence,
        }

    def digest(self) -> str:
        return _sha256_bytes(_canonical_json(self.data_payload()).encode("utf-8"))

    def summary(self) -> dict[str, Any]:
        by_market: dict[str, int] = {}
        for row in self.instruments:
            by_market[row["market_code"]] = by_market.get(row["market_code"], 0) + 1
        return {
            "marketCount": len(self.markets),
            "instrumentCount": len(self.instruments),
            "instrumentCountByMarket": dict(sorted(by_market.items())),
            "currencyCount": len(self.currencies),
            "timezoneCount": len(self.timezones),
            "sessionCount": len(self.sessions),
            "tradingStatusCount": len(self.trading_statuses),
            "adjustmentCount": len(self.adjustments),
            "calendarDateCount": len(self.calendar_dates),
            "calendarHolidayCount": sum(
                row["date_kind"] == "HOLIDAY" for row in self.calendar_dates
            ),
            "calendarSuspendedCount": sum(
                row["date_kind"] == "SUSPENDED" for row in self.calendar_dates
            ),
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BundleValidationError(f"cannot read JSON input: {path.name}") from exc


def _first(row: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and value.strip():
            return value.strip()
    return ""


def _source_artifact(path: Path, *, role: str, **extra: Any) -> dict[str, Any]:
    return {
        "role": role,
        "fileName": path.name,
        "sha256": _sha256_file(path),
        **extra,
    }


def _parse_stock_export(path: Path) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    if not path.is_file():
        raise BundleValidationError(f"stock source does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            headers = tuple(reader.fieldnames or ())
            missing = [name for name in _REQUIRED_STOCK_HEADERS if name not in headers]
            if missing:
                raise BundleValidationError(
                    f"stock source is missing required headers: {', '.join(missing)}"
                )
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise BundleValidationError(f"cannot read stock source: {path.name}") from exc

    instruments: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    skipped = 0
    for row_number, row in enumerate(rows, start=2):
        code = _first(row, ("股號", "code", "instrument_code"))
        market_code = _first(row, ("市場代碼", "market", "market_code")).upper()
        name = _first(row, ("名稱", "name", "instrument_name"))
        if not code and not market_code and not name:
            skipped += 1
            continue
        if not code or not market_code:
            skipped += 1
            continue
        if market_code not in _MARKET_DEFINITIONS:
            raise BundleValidationError(
                f"stock source row {row_number} has unsupported market {market_code!r}"
            )
        if not _SYMBOL_RE.fullmatch(code) or not name:
            raise BundleValidationError(f"stock source row {row_number} has invalid identity")
        identity = (market_code, code)
        if identity in seen:
            raise BundleValidationError(f"duplicate stock identity at row {row_number}: {identity}")
        seen.add(identity)
        instruments.append(
            {
                "market_code": market_code,
                "instrument_code": code,
                "name": name,
                "instrument_type": "EQUITY",
                "currency": "TWD",
            }
        )
    return tuple(instruments), {
        "inputRowCount": len(rows),
        "acceptedRowCount": len(instruments),
        "skippedRowCount": skipped,
        "encoding": "utf-8-sig",
        "delimiter": "\\t",
    }


def _parse_calendar(path: Path) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("holidays"), dict):
        raise BundleValidationError("calendar source must contain a holidays object")
    if not isinstance(payload.get("suspended"), dict):
        raise BundleValidationError("calendar source must contain a suspended object")
    rows = [
        {"calendar_code": "TW_MARKET", "calendar_date": day, "date_kind": "HOLIDAY"}
        for day in sorted(payload["holidays"])
    ] + [
        {"calendar_code": "TW_MARKET", "calendar_date": day, "date_kind": "SUSPENDED"}
        for day in sorted(payload["suspended"])
    ]
    for row in rows:
        try:
            date.fromisoformat(row["calendar_date"])
        except ValueError as exc:
            raise BundleValidationError(f"invalid calendar date: {row['calendar_date']}") from exc
    return tuple(rows), {
        "calendarCode": "TW_MARKET",
        "timezone": payload.get("timezone"),
        "sourceVersion": payload.get("version"),
        "sourceDescription": payload.get("source"),
        "holidayCount": len(payload["holidays"]),
        "suspendedCount": len(payload["suspended"]),
    }


def _parse_evidence(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("suspensions"), dict):
        raise BundleValidationError("suspension evidence must contain a suspensions object")
    normalized = dict(payload)
    normalized["suspensions"] = {
        str(code): {**item, "market": item.get("market", "TPE")}
        for code, item in payload["suspensions"].items()
        if isinstance(item, dict)
    }
    if len(normalized["suspensions"]) != len(payload["suspensions"]):
        raise BundleValidationError("status evidence entries must be objects")
    return normalized


def _parse_adjustments(path: Path) -> tuple[dict[str, Any], ...]:
    payload = _read_json(path)
    if isinstance(payload, dict):
        codes = payload.get("codes")
        authority = payload.get("authority")
    else:
        codes = payload
        authority = None
    if not isinstance(codes, list) or not all(isinstance(code, str) for code in codes):
        raise BundleValidationError("adjustment catalogue must contain a string codes list")
    return tuple(
        {"code": code, "authority": authority}
        for code in sorted(set(code.strip() for code in codes if code.strip()))
    )


def build_bundle_from_sources(
    *,
    stock_source: Path,
    calendar_source: Path,
    evidence_source: Path,
    adjustment_source: Path,
    version: str = "tw-reference-v1",
) -> ReferenceBundle:
    instruments, stock_meta = _parse_stock_export(stock_source)
    calendar_dates, calendar_meta = _parse_calendar(calendar_source)
    evidence = _parse_evidence(evidence_source)
    adjustments = _parse_adjustments(adjustment_source)
    markets = tuple(_MARKET_DEFINITIONS.values())
    currencies = ({"code": "TWD", "scale": 2},)
    timezones = ({"name": "Asia/Taipei"},)
    sessions = ({"code": "REGULAR", "calendar_code": "TW_MARKET"},)
    evidence_statuses = {
        item.get("status")
        for item in evidence.get("suspensions", {}).values()
        if isinstance(item, dict) and item.get("status")
    }
    statuses = tuple(
        {"code": code}
        for code in sorted(set(DAILY_TRADING_STATUS_CODES) | evidence_statuses)
    )
    bundle = ReferenceBundle(
        manifest={
            "bundleSchemaVersion": BUNDLE_SCHEMA_VERSION,
            "referenceDataVersion": version,
            "generatedOrCurated": "GENERATED_WITH_CURATED_GOVERNANCE_INPUTS",
            "sourceArtifacts": [
                _source_artifact(stock_source, role="INSTRUMENT_SOURCE", **stock_meta),
                _source_artifact(calendar_source, role="CALENDAR_AUTHORITY", **calendar_meta),
                _source_artifact(evidence_source, role="STATUS_EVIDENCE"),
                _source_artifact(adjustment_source, role="ADJUSTMENT_GOVERNANCE_INPUT"),
            ],
            "governance": {
                "marketAuthority": "provider registry plus existing identity bootstrap defaults",
                "currencyAuthority": "existing live runtime/reference context contract",
                "statusAuthority": "DAILY_TRADING_STATUS_CODES plus explicit evidence validation",
                "adjustmentAuthority": "curated repository governance input; no implicit defaults",
                "calendarAuthority": calendar_meta.get("sourceDescription"),
                "activation": "operator must explicitly pass --activate",
            },
        },
        markets=markets,
        instruments=instruments,
        currencies=currencies,
        timezones=timezones,
        sessions=sessions,
        trading_statuses=statuses,
        adjustments=adjustments,
        calendar_dates=calendar_dates,
        evidence=evidence,
    )
    validate_bundle(bundle)
    bundle.manifest["derivedSummary"] = bundle.summary()
    bundle.manifest["bundleSha256"] = bundle.digest()
    return bundle


def validate_bundle(bundle: ReferenceBundle) -> None:
    manifest_version = bundle.manifest.get("referenceDataVersion")
    if not isinstance(manifest_version, str) or not manifest_version.strip():
        raise BundleValidationError("bundle referenceDataVersion is missing")
    if bundle.manifest.get("bundleSchemaVersion") != BUNDLE_SCHEMA_VERSION:
        raise BundleValidationError("unsupported reference bundle schema")
    market_codes = [row.get("code") for row in bundle.markets]
    if len(market_codes) != len(set(market_codes)) or not all(market_codes):
        raise BundleValidationError("markets must have unique non-empty codes")
    if len(bundle.markets) == 0:
        raise BundleValidationError("bundle has no markets")
    currency_codes = [row.get("code") for row in bundle.currencies]
    timezone_names = [row.get("name") for row in bundle.timezones]
    session_keys = [(row.get("code"), row.get("calendar_code")) for row in bundle.sessions]
    status_codes = [row.get("code") for row in bundle.trading_statuses]
    adjustment_codes = [row.get("code") for row in bundle.adjustments]
    if not currency_codes or len(currency_codes) != len(set(currency_codes)):
        raise BundleValidationError("currency catalogue is empty or duplicated")
    if not timezone_names or len(timezone_names) != len(set(timezone_names)):
        raise BundleValidationError("timezone catalogue is empty or duplicated")
    if not session_keys or len(session_keys) != len(set(session_keys)):
        raise BundleValidationError("session catalogue is empty or duplicated")
    if not status_codes or len(status_codes) != len(set(status_codes)):
        raise BundleValidationError("trading-status catalogue is empty or duplicated")
    if not adjustment_codes or len(adjustment_codes) != len(set(adjustment_codes)):
        raise BundleValidationError("adjustment catalogue is empty or duplicated")

    identity_keys: set[tuple[str, str]] = set()
    for row in bundle.instruments:
        key = (row.get("market_code", ""), row.get("instrument_code", ""))
        if key in identity_keys:
            raise BundleValidationError(f"duplicate instrument identity: {key}")
        identity_keys.add(key)
        if key[0] not in market_codes or not _SYMBOL_RE.fullmatch(key[1]):
            raise BundleValidationError(f"invalid instrument identity: {key}")
        if not row.get("name") or row.get("instrument_type") != "EQUITY":
            raise BundleValidationError(f"invalid instrument row: {key}")
        if row.get("currency") not in currency_codes:
            raise BundleValidationError(f"instrument currency is not catalogued: {key}")

    calendar_keys: set[tuple[str, str]] = set()
    for row in bundle.calendar_dates:
        key = (row.get("calendar_code", ""), row.get("calendar_date", ""))
        if key in calendar_keys:
            raise BundleValidationError(f"duplicate calendar date: {key}")
        calendar_keys.add(key)
        if key[0] not in {item[1] for item in session_keys}:
            raise BundleValidationError(f"calendar is not referenced by a session: {key[0]}")
        if row.get("date_kind") not in {"HOLIDAY", "SUSPENDED"}:
            raise BundleValidationError(f"unsupported calendar date kind: {row.get('date_kind')}")
        try:
            date.fromisoformat(key[1])
        except ValueError as exc:
            raise BundleValidationError(f"invalid calendar date: {key[1]}") from exc
    suspension_map = bundle.evidence.get("suspensions", {})
    if not isinstance(suspension_map, dict):
        raise BundleValidationError("status evidence is missing suspensions")
    for code, item in suspension_map.items():
        if not isinstance(item, dict) or not item.get("status"):
            raise BundleValidationError(f"incomplete status evidence: {code}")
        evidence_key = (item.get("market"), str(code))
        if evidence_key not in identity_keys:
            raise BundleValidationError(
                f"status evidence identity is not in bundle: {evidence_key}"
            )
        if item["status"] not in set(status_codes) | {"DELISTED"}:
            raise BundleValidationError(
                f"status evidence status is not catalogued: {item['status']}"
            )
    if bundle.manifest.get("derivedSummary"):
        expected = bundle.manifest["derivedSummary"]
        if expected != bundle.summary():
            raise BundleValidationError("bundle derivedSummary does not match data files")


def _file_payload(bundle: ReferenceBundle) -> dict[str, Any]:
    return {
        "markets.json": list(bundle.markets),
        "instruments.json": list(bundle.instruments),
        "currencies.json": list(bundle.currencies),
        "timezones.json": list(bundle.timezones),
        "sessions.json": list(bundle.sessions),
        "trading_statuses.json": list(bundle.trading_statuses),
        "adjustments.json": list(bundle.adjustments),
        "calendar_dates.json": list(bundle.calendar_dates),
        "evidence.json": bundle.evidence,
    }


def write_bundle(bundle: ReferenceBundle, output_dir: Path) -> Path:
    """Write a canonical bundle with stable JSON and manifest file hashes."""

    validate_bundle(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in _file_payload(bundle).items():
        (output_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    manifest = dict(bundle.manifest)
    manifest["bundleSha256"] = bundle.digest()
    manifest["files"] = {
        filename: _sha256_file(output_dir / filename) for filename in BUNDLE_FILE_NAMES
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_dir


def load_bundle(bundle_dir: Path) -> ReferenceBundle:
    if not bundle_dir.is_dir():
        raise BundleValidationError(f"bundle directory does not exist: {bundle_dir}")
    manifest_path = bundle_dir / "manifest.json"
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise BundleValidationError("bundle manifest must be an object")
    files = manifest.get("files", {})
    for filename in BUNDLE_FILE_NAMES:
        path = bundle_dir / filename
        if not path.is_file():
            raise BundleValidationError(f"bundle file is missing: {filename}")
        expected_hash = files.get(filename)
        if expected_hash and expected_hash != _sha256_file(path):
            raise BundleValidationError(f"bundle file hash mismatch: {filename}")
    payloads = {filename: _read_json(bundle_dir / filename) for filename in BUNDLE_FILE_NAMES}
    bundle = ReferenceBundle(
        manifest=manifest,
        markets=tuple(payloads["markets.json"]),
        instruments=tuple(payloads["instruments.json"]),
        currencies=tuple(payloads["currencies.json"]),
        timezones=tuple(payloads["timezones.json"]),
        sessions=tuple(payloads["sessions.json"]),
        trading_statuses=tuple(payloads["trading_statuses.json"]),
        adjustments=tuple(payloads["adjustments.json"]),
        calendar_dates=tuple(payloads["calendar_dates.json"]),
        evidence=payloads["evidence.json"],
    )
    validate_bundle(bundle)
    expected_bundle_hash = manifest.get("bundleSha256")
    if expected_bundle_hash and expected_bundle_hash != bundle.digest():
        raise BundleValidationError("bundle hash mismatch")
    return bundle


__all__ = [
    "BUNDLE_FILE_NAMES",
    "BundleValidationError",
    "ReferenceBundle",
    "build_bundle_from_sources",
    "load_bundle",
    "validate_bundle",
    "write_bundle",
]
