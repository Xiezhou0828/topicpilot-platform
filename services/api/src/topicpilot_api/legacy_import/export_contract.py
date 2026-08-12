from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

EXPORT_CONTRACT_VERSION = "3.6-001A.v1"
SUPPORTED_DELIMITERS = {"csv": ",", "tsv": "\t"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_record_hash(record: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(record).encode("utf-8"))


@dataclass(frozen=True)
class ExportArtifact:
    entity: str
    filename: str
    format: str
    encoding: str
    delimiter: str
    row_count: int
    sha256: str


@dataclass(frozen=True)
class ExportManifest:
    contract_version: str
    export_id: str
    exported_at: str
    artifacts: tuple[ExportArtifact, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "export_id": self.export_id,
            "exported_at": self.exported_at,
            "artifacts": [a.__dict__ for a in self.artifacts],
        }


def build_manifest(
    artifacts: Iterable[ExportArtifact], export_id: str, exported_at: datetime | None = None
) -> ExportManifest:
    stamp = (exported_at or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")
    return ExportManifest(
        EXPORT_CONTRACT_VERSION,
        export_id,
        stamp,
        tuple(sorted(artifacts, key=lambda a: a.filename)),
    )


def parse_delimited(
    content: bytes, *, format: str, encoding: str = "utf-8-sig"
) -> list[dict[str, str]]:
    if format not in SUPPORTED_DELIMITERS:
        raise ValueError(f"unsupported format: {format}")
    if encoding.lower().replace("-", "") not in {"utf8", "utf8sig"}:
        raise ValueError("export encoding must be UTF-8 or UTF-8 with BOM")
    text = content.decode(encoding)
    return list(
        csv.DictReader(io.StringIO(text, newline=""), delimiter=SUPPORTED_DELIMITERS[format])
    )
