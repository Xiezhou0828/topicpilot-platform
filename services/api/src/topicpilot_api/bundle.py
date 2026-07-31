from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from topicpilot_api.constants import (
    CONTRACT_VERSION,
    STRATEGY_HORIZONS,
    STRATEGY_KEYS,
)


class BundleError(ValueError):
    """Base class for fail-closed bundle errors."""


class BundleParseError(BundleError):
    pass


class BundleSchemaError(BundleError):
    pass


class BundleReferenceError(BundleError):
    pass


class BundleSemanticError(BundleError):
    pass


@dataclass(frozen=True)
class ArtifactInfo:
    name: str
    file_name: str
    sha256: str
    row_count: int
    byte_size: int


@dataclass(frozen=True)
class LoadedBundle:
    root: Path
    data: dict[str, Any]
    bundle_hash: str
    artifacts: tuple[ArtifactInfo, ...]
    row_counts: dict[str, int]

    @property
    def manifest(self) -> dict[str, Any]:
        return self.data["manifest"]


def default_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "fixtures"
        / "schema"
        / "enterprise_bundle.v1.schema.json"
    )


def _read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BundleParseError(f"Cannot read required bundle artifact {path}: {exc}") from exc
    try:
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise BundleParseError(
            f"{path} is not valid UTF-8. Re-export the source; "
            "do not repair or partially import it."
        ) from exc
    if "\ufffd" in text or "\x00" in text:
        raise BundleParseError(
            f"{path} contains replacement or NUL characters. Re-export the source before importing."
        )
    try:
        return json.loads(text), raw
    except json.JSONDecodeError as exc:
        raise BundleParseError(
            f"{path} is not valid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}. "
            "Re-export the complete snapshot; partial recovery is intentionally disabled."
        ) from exc


def _artifact_row_count(name: str, value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if name == "dailySnapshots":
        return sum(len(value.get(key, [])) for key in value)
    if name == "strategyCandidates":
        return len(value.get("strategyRuns", [])) + len(value.get("candidates", []))
    return 1


def _format_schema_errors(validator: Draft202012Validator, data: dict[str, Any]) -> str:
    errors = sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path))
    details = []
    for error in errors[:20]:
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        details.append(f"{path}: {error.message}")
    if len(errors) > 20:
        details.append(f"... {len(errors) - 20} additional validation errors")
    return "; ".join(details)


def _ensure_unique(rows: list[dict[str, Any]], fields: tuple[str, ...], label: str) -> None:
    keys = [tuple(row[field] for field in fields) for row in rows]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        raise BundleSemanticError(f"{label} contains duplicate keys: {duplicates[:5]}")


def _validate_public_safety(data: dict[str, Any]) -> None:
    source = data["manifest"]["source"]
    expected = {
        "synthetic": "PUBLIC_SYNTHETIC",
        "private_snapshot": "PRIVATE_FORMAL",
    }[source["kind"]]
    if source["classification"] != expected:
        raise BundleSemanticError(
            f"source.kind={source['kind']} requires classification={expected}"
        )
    if source["classification"] != "PUBLIC_SYNTHETIC":
        return

    forbidden_keys = {
        "credential",
        "credentials",
        "password",
        "privateKey",
        "serviceAccount",
        "holding",
        "holdings",
        "articleBody",
        "newsText",
        "privateUrl",
    }

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            found = forbidden_keys.intersection(value)
            if found:
                raise BundleSemanticError(
                    f"PUBLIC_SYNTHETIC bundle contains forbidden keys at {path}: {sorted(found)}"
                )
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(data, "$")


def validate_semantics(data: dict[str, Any]) -> None:
    manifest = data["manifest"]
    if manifest["contractVersion"] != CONTRACT_VERSION:
        raise BundleSemanticError(
            f"Unsupported contractVersion {manifest['contractVersion']!r}; "
            f"expected {CONTRACT_VERSION!r}"
        )

    _validate_public_safety(data)

    stocks = data["stocks"]
    topics = data["topics"]
    hierarchy = data["topicHierarchy"]
    relations = data["stockTopicRelations"]
    daily = data["dailySnapshots"]
    strategy_runs = data["strategyCandidates"]["strategyRuns"]
    candidates = data["strategyCandidates"]["candidates"]
    performance = data["strategyPerformance"]

    _ensure_unique(stocks, ("code",), "stocks")
    _ensure_unique(topics, ("slug",), "topics")
    _ensure_unique(hierarchy, ("parentSlug", "childSlug"), "topicHierarchy")
    _ensure_unique(relations, ("stockCode", "topicSlug", "relationType"), "stockTopicRelations")
    _ensure_unique(daily["marketSnapshots"], ("dataDate", "market"), "marketSnapshots")
    _ensure_unique(daily["stockSnapshots"], ("dataDate", "stockCode"), "stockSnapshots")
    _ensure_unique(daily["topicSnapshots"], ("dataDate", "topicSlug"), "topicSnapshots")
    _ensure_unique(
        strategy_runs,
        ("strategyKey", "dataDate", "modelVersion"),
        "strategyRuns",
    )
    _ensure_unique(
        candidates,
        ("strategyKey", "dataDate", "modelVersion", "stockCode"),
        "strategyCandidates",
    )
    _ensure_unique(
        performance,
        ("strategyKey", "dataDate", "modelVersion", "horizon"),
        "strategyPerformance",
    )

    stock_codes = {row["code"] for row in stocks}
    topic_slugs = {row["slug"] for row in topics}
    unknown_hierarchy = sorted(
        {
            slug
            for row in hierarchy
            for slug in (row["parentSlug"], row["childSlug"])
            if slug not in topic_slugs
        }
    )
    unknown_relation_stocks = sorted(
        {row["stockCode"] for row in relations if row["stockCode"] not in stock_codes}
    )
    unknown_relation_topics = sorted(
        {row["topicSlug"] for row in relations if row["topicSlug"] not in topic_slugs}
    )
    unknown_snapshot_stocks = sorted(
        {row["stockCode"] for row in daily["stockSnapshots"] if row["stockCode"] not in stock_codes}
    )
    unknown_snapshot_topics = sorted(
        {row["topicSlug"] for row in daily["topicSnapshots"] if row["topicSlug"] not in topic_slugs}
    )
    unknown_candidate_stocks = sorted(
        {row["stockCode"] for row in candidates if row["stockCode"] not in stock_codes}
    )
    reference_errors = {
        "topicHierarchy": unknown_hierarchy,
        "relationStocks": unknown_relation_stocks,
        "relationTopics": unknown_relation_topics,
        "snapshotStocks": unknown_snapshot_stocks,
        "snapshotTopics": unknown_snapshot_topics,
        "candidateStocks": unknown_candidate_stocks,
    }
    present_errors = {key: value for key, value in reference_errors.items() if value}
    if present_errors:
        raise BundleReferenceError(f"Bundle contains unresolved references: {present_errors}")

    if any(row["parentSlug"] == row["childSlug"] for row in hierarchy):
        raise BundleSemanticError("topicHierarchy cannot contain self-references")

    run_keys = {row["strategyKey"] for row in strategy_runs}
    if run_keys != set(STRATEGY_KEYS):
        raise BundleSemanticError(
            f"strategyRuns must contain exactly {list(STRATEGY_KEYS)}; got {sorted(run_keys)}"
        )
    run_identity = {
        (row["strategyKey"], row["dataDate"], row["modelVersion"]): row for row in strategy_runs
    }
    for row in candidates:
        identity = (row["strategyKey"], row["dataDate"], row["modelVersion"])
        if identity not in run_identity:
            raise BundleReferenceError(f"Candidate has no strategy run: {identity}")
    for row in performance:
        identity = (row["strategyKey"], row["dataDate"], row["modelVersion"])
        if identity not in run_identity:
            raise BundleReferenceError(f"Performance row has no strategy run: {identity}")

    candidates_by_key = Counter(row["strategyKey"] for row in candidates if row["selected"])
    for row in strategy_runs:
        if row["selectedCount"] != candidates_by_key[row["strategyKey"]]:
            raise BundleSemanticError(
                f"{row['strategyKey']} selectedCount does not match selected candidates"
            )
        if row["candidateCount"] < row["selectedCount"]:
            raise BundleSemanticError(
                f"{row['strategyKey']} candidateCount cannot be below selectedCount"
            )

    horizons_by_key: dict[str, set[str]] = {key: set() for key in STRATEGY_KEYS}
    for row in performance:
        horizons_by_key[row["strategyKey"]].add(row["horizon"])
        numeric_fields = ("sampleCount", "winRatePct", "averageReturnPct")
        if row["status"] == "NOT_DUE" and any(row[field] is not None for field in numeric_fields):
            raise BundleSemanticError(
                f"{row['strategyKey']}/{row['horizon']} NOT_DUE metrics must remain null"
            )
    for strategy_key, horizons in horizons_by_key.items():
        if horizons != set(STRATEGY_HORIZONS):
            raise BundleSemanticError(
                f"{strategy_key} performance must contain {list(STRATEGY_HORIZONS)}"
            )

    manifest_date = date.fromisoformat(manifest["dataDate"])
    observed_dates = [
        date.fromisoformat(row["dataDate"])
        for collection in (
            daily["marketSnapshots"],
            daily["stockSnapshots"],
            daily["topicSnapshots"],
            strategy_runs,
        )
        for row in collection
    ]
    if not observed_dates or max(observed_dates) != manifest_date:
        raise BundleSemanticError("manifest.dataDate must equal the latest observation date")
    if any(day > manifest_date for day in observed_dates):
        raise BundleSemanticError("Bundle contains observations after manifest.dataDate")


def calculate_bundle_hash(artifacts: list[ArtifactInfo]) -> str:
    digest = hashlib.sha256()
    for artifact in sorted(artifacts, key=lambda item: item.name):
        digest.update(artifact.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(artifact.sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_bundle(bundle_dir: Path, schema_path: Path | None = None) -> LoadedBundle:
    bundle_dir = bundle_dir.resolve()
    if not bundle_dir.is_dir():
        raise BundleParseError(f"Bundle directory does not exist: {bundle_dir}")

    manifest_path = bundle_dir / "manifest.json"
    manifest, manifest_raw = _read_json(manifest_path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise BundleParseError(f"{manifest_path} must be an object with a files map")

    data: dict[str, Any] = {"manifest": manifest}
    artifacts = [
        ArtifactInfo(
            name="manifest",
            file_name="manifest.json",
            sha256=hashlib.sha256(manifest_raw).hexdigest(),
            row_count=1,
            byte_size=len(manifest_raw),
        )
    ]
    for logical_name, file_name in manifest["files"].items():
        artifact_path = (bundle_dir / file_name).resolve()
        if bundle_dir not in artifact_path.parents:
            raise BundleParseError(f"Artifact escapes bundle directory: {file_name}")
        value, raw = _read_json(artifact_path)
        data[logical_name] = value
        artifacts.append(
            ArtifactInfo(
                name=logical_name,
                file_name=file_name,
                sha256=hashlib.sha256(raw).hexdigest(),
                row_count=_artifact_row_count(logical_name, value),
                byte_size=len(raw),
            )
        )

    schema_file = (schema_path or default_schema_path()).resolve()
    schema, _ = _read_json(schema_file)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    error_text = _format_schema_errors(validator, data)
    if error_text:
        raise BundleSchemaError(f"Bundle does not satisfy {schema_file.name}: {error_text}")

    validate_semantics(data)
    row_counts = {
        "stocks": len(data["stocks"]),
        "topics": len(data["topics"]),
        "topicHierarchy": len(data["topicHierarchy"]),
        "stockTopicRelations": len(data["stockTopicRelations"]),
        "marketSnapshots": len(data["dailySnapshots"]["marketSnapshots"]),
        "stockSnapshots": len(data["dailySnapshots"]["stockSnapshots"]),
        "topicSnapshots": len(data["dailySnapshots"]["topicSnapshots"]),
        "strategyRuns": len(data["strategyCandidates"]["strategyRuns"]),
        "strategyCandidates": len(data["strategyCandidates"]["candidates"]),
        "strategyPerformance": len(data["strategyPerformance"]),
        "dataQualityEvents": len(data["dailySnapshots"]["dataQualityEvents"]),
    }
    return LoadedBundle(
        root=bundle_dir,
        data=data,
        bundle_hash=calculate_bundle_hash(artifacts),
        artifacts=tuple(artifacts),
        row_counts=row_counts,
    )


def load_private_snapshot_json(path: Path) -> dict[str, Any]:
    """Fail-closed guard for a future private converter.

    Raw private snapshots are deliberately not accepted by the public importer. This helper only
    verifies that a source file is intact enough for a separately reviewed converter. It never
    repairs encoding, substitutes missing roots, or writes data.
    """
    value, _ = _read_json(path.resolve())
    if not isinstance(value, dict):
        raise BundleSchemaError("Private snapshot root must be a JSON object")
    required = {
        "snapshotVersion",
        "generatedAt",
        "dataDate",
        "quoteMeta",
        "marketSession",
        "topics",
        "stocks",
        "strategyRegistry",
        "strategyCandidates",
        "strategyPerformance",
    }
    missing = sorted(required - set(value))
    if missing:
        raise BundleSchemaError(
            "Private snapshot is incomplete and was rejected; missing roots: "
            f"{missing}. Re-run the validated private exporter before conversion."
        )
    if not isinstance(value["stocks"], dict) or not isinstance(value["topics"], list):
        raise BundleSchemaError(
            "Private snapshot has incompatible stocks/topics containers; "
            "re-run the validated exporter."
        )
    return value
