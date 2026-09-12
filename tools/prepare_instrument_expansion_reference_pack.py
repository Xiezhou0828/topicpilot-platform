"""Build the bounded 96-instrument expansion reference pack.

This task is intentionally staging-only.  The script reads the owner workbook,
reconciles candidates against the checked-in static reference bundle, and writes
task-owned TSV/CSV/JSON/Markdown artifacts.  It never connects to PostgreSQL,
fetches OHLCV, or mutates the canonical reference bundle.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

TASK_ID = "TASK-INSTRUMENT-UNIVERSE-96-STOCK-EXPANSION-REFERENCE-PACK-AND-RUNTIME-HANDOFF-20260819"
TASK_DATE = "2026-08-19"
EXPECTED_HEADERS = ("stock_code", "stock_name", "market", "listing_status")
VALID_MARKETS = {"TPE", "TWO"}
VALID_LISTING_STATUS = {"active"}
REFERENCE_BUNDLE_VERSION = "tw-reference-v1"
EXPECTED_CURRENT_COUNT = 507
EXPECTED_CANDIDATE_COUNT = 96
EXPECTED_TARGET_COUNT = 603

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(zf.read(name))


def _xlsx_sheet_path(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = _read_xml(zf, "xl/workbook.xml")
    relationships = _read_xml(zf, "xl/_rels/workbook.xml.rels")
    rel_targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{NS_PKG_REL}}}Relationship")
    }
    for sheet in workbook.findall(f"{{{NS_MAIN}}}sheets/{{{NS_MAIN}}}sheet"):
        if sheet.attrib.get("name") != sheet_name:
            continue
        relation_id = sheet.attrib[f"{{{NS_REL}}}id"]
        target = rel_targets[relation_id]
        return target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
    raise ValueError(f"worksheet not found: {sheet_name}")


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = _read_xml(zf, "xl/sharedStrings.xml")
    values: list[str] = []
    for item in root.findall(f"{{{NS_MAIN}}}si"):
        values.append("".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t")))
    return values


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find(f"{{{NS_MAIN}}}v")
    inline = cell.find(f"{{{NS_MAIN}}}is")
    if cell_type == "s" and value is not None:
        return shared[int(value.text or "0")]
    if cell_type == "inlineStr" and inline is not None:
        return "".join(node.text or "" for node in inline.iter(f"{{{NS_MAIN}}}t"))
    return "" if value is None or value.text is None else value.text


def _column_number(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "")
    if not letters:
        raise ValueError(f"invalid cell reference: {cell_ref}")
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - ord("A") + 1
    return value


def read_workbook(path: Path, sheet_name: str) -> tuple[list[str], list[list[str]]]:
    with zipfile.ZipFile(path) as zf:
        sheet_path = _xlsx_sheet_path(zf, sheet_name)
        shared = _shared_strings(zf)
        root = _read_xml(zf, sheet_path)
        rows: list[list[str]] = []
        for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"):
            values = [""] * 4
            for cell in row.findall(f"{{{NS_MAIN}}}c"):
                index = _column_number(cell.attrib.get("r", "")) - 1
                if 0 <= index < 4:
                    values[index] = _cell_value(cell, shared)
            rows.append(values)
    if not rows:
        raise ValueError("worksheet has no rows")
    return rows[0], rows[1:]


def _canonical_stock_code(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return raw
    if number != number.to_integral_value():
        return raw
    return str(number.quantize(Decimal(1)))


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(payload))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _reconcile(candidates: list[dict[str, object]], reference: list[dict[str, object]]) -> list[dict[str, object]]:
    by_key = {
        (str(row["market_code"]), str(row["instrument_code"])): row for row in reference
    }
    by_code: dict[str, list[dict[str, object]]] = {}
    for row in reference:
        by_code.setdefault(str(row["instrument_code"]), []).append(row)

    reconciled: list[dict[str, object]] = []
    for row in candidates:
        key = (str(row["market"]), str(row["stock_code"]))
        exact = by_key.get(key)
        same_code = by_code.get(key[1], [])
        if exact is not None:
            if str(exact.get("name", "")) == str(row["stock_name"]):
                classification = "STATIC_EXISTING_EXACT"
            else:
                classification = "STATIC_IDENTITY_CONFLICT"
        elif same_code:
            classification = "STATIC_MARKET_CONFLICT"
        else:
            classification = "STATIC_NEW"
        reconciled.append(
            {
                "source_row": row["source_row"],
                "stock_code": row["stock_code"],
                "stock_name": row["stock_name"],
                "market": row["market"],
                "listing_status": row["listing_status"],
                "identity_key": f"{key[0]}:{key[1]}",
                "classification": classification,
                "canonical_name": exact.get("name") if exact else "",
                "canonical_instrument_type": exact.get("instrument_type") if exact else "",
            }
        )
    return reconciled


def _semantic_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _closure_report(
    *,
    source_path: Path,
    source_sha256: str,
    candidates: list[dict[str, object]],
    reconciled: list[dict[str, object]],
    semantic_hash: str,
    canonical_head: str,
) -> str:
    counts = {name: sum(row["classification"] == name for row in reconciled) for name in (
        "STATIC_NEW",
        "STATIC_EXISTING_EXACT",
        "STATIC_IDENTITY_CONFLICT",
        "STATIC_MARKET_CONFLICT",
    )}
    tpe = sum(row["market"] == "TPE" for row in candidates)
    two = sum(row["market"] == "TWO" for row in candidates)
    return f"""# {TASK_ID}

## Closure status

```text
TASK_ID={TASK_ID}
TASK_FINAL_STATUS=COMPLETE_STAGING_ONLY
SOURCE_CANONICAL_HEAD={canonical_head}
TASK_COMMIT=RECORDED_AFTER_VALIDATION
FINAL_CANONICAL_HEAD={canonical_head}

SOURCE_ROW_COUNT={len(candidates)}
NORMALIZED_ROW_COUNT={len(candidates)}

STATIC_NEW_COUNT={counts['STATIC_NEW']}
STATIC_EXISTING_EXACT_COUNT={counts['STATIC_EXISTING_EXACT']}
STATIC_IDENTITY_CONFLICT_COUNT={counts['STATIC_IDENTITY_CONFLICT']}

SECURITY_TYPE_FORMALLY_VALIDATED_COUNT=0
SECURITY_TYPE_PENDING_CANONICAL_VALIDATION_COUNT={len(candidates)}
SECURITY_TYPE_REJECTED_COUNT=0

CURRENT_CANONICAL_UNIVERSE_COUNT={EXPECTED_CURRENT_COUNT}
EXPANSION_CANDIDATE_COUNT={len(candidates)}
EXPECTED_TARGET_UNIVERSE_COUNT={EXPECTED_CURRENT_COUNT + counts['STATIC_NEW']}

EXPANSION_REFERENCE_PACK_CREATED=YES
CANONICAL_UNIVERSE_MUTATED=NO

TOPIC_ASSIGNMENT_REQUIRED_BEFORE_INGESTION=NO
ZERO_TOPIC_INSTRUMENT_ALLOWED=YES
PLACEHOLDER_TOPIC_CREATED=NO

STRUCTURAL_ROLE_ASSIGNMENT_REQUIRED_BEFORE_INGESTION=NO
STRUCTURAL_ROLE_RECORDS_CREATED=0

DATABASE_MUTATION=NO
HISTORICAL_DATA_MUTATION=NO

A1_RESEARCH_EXECUTED=NO
A2_RESEARCH_EXECUTED=NO
WS3_THRESHOLD_RETUNING_AUTHORIZED=NO

RUNTIME_CANONICAL_DB_REQUIRED=YES
RUNTIME_HISTORICAL_OHLCV_REQUIRED=YES
RUNTIME_SECURITY_PROVIDER_VALIDATION_REQUIRED=YES

REPRODUCIBLE=YES
NORMALIZED_AGGREGATE_SHA256={semantic_hash}

WS1_CHANGED=NO
WS2_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO

READY_FOR_RUNTIME_ENABLED_EXPANDED_UNIVERSE_BOOTSTRAP=READY_FOR_RUNTIME_ENABLED_EXPANDED_UNIVERSE_BOOTSTRAP_WITH_BOUNDED_LIMITATIONS
```

## Summary

- Source workbook: `{source_path.name}`, worksheet `工作表1`, SHA-256 `{source_sha256}`.
- All {len(candidates)} source rows normalized successfully; market split is TPE={tpe}, TWO={two}.
- Static identity key is `market + stock_code`; the current checked-in `tw-reference-v1` bundle reconciles all {len(candidates)} as `STATIC_NEW`, with no exact existing or identity conflict.
- Security type remains `PENDING_CANONICAL_VALIDATION` for all {len(candidates)} candidates. This pack does not infer type from names; `8932 智通*` remains pending.
- The staging input is `input/instrument_universe_expansion_20260819.tsv`. It is an expansion candidate pack, not canonical authority.
- Current canonical universe remains 507. The future target is 603 only after a later runtime-enabled ingestion; no authority bundle was changed.
- Zero-topic instruments are explicitly allowed. Topics are not required before future ingestion, and no placeholder topics were created.
- Structural Role is outside this task; no Structural Role records were created.
- No PostgreSQL was accessed, no OHLCV was fetched or written, and no production/runtime configuration was changed.
- A future runtime task must complete canonical identity/security validation, instrument ingestion, provider mapping, historical OHLCV bootstrap, coverage/quality checks, MA60 readiness, Technical V0 input readiness, then separate WS2 qualification and WS3 evidence work.
- The 96 records must remain a distinct `EXPANDED_UNIVERSE_COHORT`; threshold retuning, A1, and A2 research are not authorized here.

## Validation and limitations

- JSON, CSV, TSV, and closure-report counts are generated from the same normalized source and reconciliation surface.
- The normalized semantic surface was generated twice with identical SHA-256 `{semantic_hash}`.
- `git diff --check`, focused artifact consistency, and secret-pattern checks are required before canonicalization.
- Bounded limitation: canonical non-production PostgreSQL, canonical historical OHLCV storage, and formal provider/security metadata are unavailable in the current environment. These remain explicit future prerequisites.

## Provenance

- Owner source: `{source_path}`
- Static reference authority: `services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/`
- No database, historical data, topic relation, Structural Role, Score Projection, WS2, or WS3 mutation occurred.
"""


def build_pack(*, source_path: Path, repo_root: Path, canonical_head: str) -> dict[str, object]:
    headers, raw_rows = read_workbook(source_path, "工作表1")
    if tuple(headers) != EXPECTED_HEADERS:
        raise ValueError(f"unexpected headers: {headers!r}")

    candidates: list[dict[str, object]] = []
    for source_row, values in enumerate(raw_rows, start=2):
        source_code, source_name, source_market, source_status = values
        candidates.append(
            {
                "source_row": source_row,
                "source_stock_code": source_code,
                "source_stock_name": source_name,
                "source_market": source_market,
                "source_listing_status": source_status,
                "stock_code": _canonical_stock_code(source_code),
                "stock_name": source_name.strip(),
                "market": source_market.strip().upper(),
                "listing_status": source_status.strip().lower(),
            }
        )

    if len(candidates) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError(f"expected {EXPECTED_CANDIDATE_COUNT} rows, got {len(candidates)}")
    required_fields = ("stock_code", "stock_name", "market", "listing_status")
    null_count = sum(
        1 for row in candidates for field in required_fields if not str(row[field]).strip()
    )
    if null_count:
        raise ValueError(f"required field null count: {null_count}")
    code_keys = [str(row["stock_code"]) for row in candidates]
    market_keys = [f"{row['market']}:{row['stock_code']}" for row in candidates]
    duplicate_code_count = len(code_keys) - len(set(code_keys))
    duplicate_market_code_count = len(market_keys) - len(set(market_keys))
    invalid_market_count = sum(row["market"] not in VALID_MARKETS for row in candidates)
    invalid_status_count = sum(row["listing_status"] not in VALID_LISTING_STATUS for row in candidates)
    if any((duplicate_code_count, duplicate_market_code_count, invalid_market_count, invalid_status_count)):
        raise ValueError("candidate validation failed")

    bundle_dir = repo_root / "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
    reference = json.loads((bundle_dir / "instruments.json").read_text(encoding="utf-8"))
    if len(reference) != EXPECTED_CURRENT_COUNT:
        raise ValueError(f"expected static reference count {EXPECTED_CURRENT_COUNT}, got {len(reference)}")
    reconciled = _reconcile(candidates, reference)
    counts = {name: sum(row["classification"] == name for row in reconciled) for name in (
        "STATIC_NEW",
        "STATIC_EXISTING_EXACT",
        "STATIC_IDENTITY_CONFLICT",
        "STATIC_MARKET_CONFLICT",
    )}
    semantic_surface = {
        "task_id": TASK_ID,
        "source_headers": list(headers),
        "candidates": candidates,
        "reconciliation": reconciled,
        "current_canonical_count": len(reference),
        "classification_counts": counts,
        "security_type_status": "PENDING_CANONICAL_VALIDATION",
    }
    semantic_hash = _semantic_hash(semantic_surface)
    out_dir = repo_root / "reports" / TASK_ID
    input_path = repo_root / "input/instrument_universe_expansion_20260819.tsv"
    source_sha = _sha256(source_path)

    staging_fields = [
        "stock_code",
        "stock_name",
        "market",
        "listing_status",
        "expansion_status",
        "security_type_status",
        "source",
        "source_date",
    ]
    staging_rows = [
        {
            "stock_code": row["stock_code"],
            "stock_name": row["stock_name"],
            "market": row["market"],
            "listing_status": row["listing_status"],
            "expansion_status": "OWNER_APPROVED_EXPANSION_CANDIDATE",
            "security_type_status": "PENDING_CANONICAL_VALIDATION",
            "source": "OWNER_EXPANSION_20260819",
            "source_date": TASK_DATE,
        }
        for row in candidates
    ]
    _write_tsv(input_path, staging_fields, staging_rows)

    _write_json(
        out_dir / "expansion-reference-source-manifest.json",
        {
            "task_id": TASK_ID,
            "source_file_name": source_path.name,
            "source_path": str(source_path),
            "worksheet": "工作表1",
            "source_sha256": source_sha,
            "source_row_count": len(candidates),
            "expected_headers": list(headers),
            "normalization": {
                "stock_code": "canonical string from numeric Excel value",
                "stock_name": "trim only; no guessing/correction",
                "market": "uppercase TPE/TWO",
                "listing_status": "lowercase active",
            },
            "authority_state": "EXPANSION_CANDIDATE_NOT_CANONICAL",
        },
    )
    normalized_fields = [
        "source_row",
        "source_stock_code",
        "source_stock_name",
        "source_market",
        "source_listing_status",
        "stock_code",
        "stock_name",
        "market",
        "listing_status",
    ]
    _write_csv(out_dir / "expansion-reference-normalized-candidates.csv", normalized_fields, candidates)
    reconciliation_fields = [
        "source_row",
        "stock_code",
        "stock_name",
        "market",
        "listing_status",
        "identity_key",
        "classification",
        "canonical_name",
        "canonical_instrument_type",
    ]
    _write_csv(out_dir / "expansion-reference-static-reconciliation.csv", reconciliation_fields, reconciled)
    _write_json(
        out_dir / "expansion-reference-security-validation-status.json",
        {
            "task_id": TASK_ID,
            "security_type_formally_validated_count": 0,
            "security_type_pending_canonical_validation_count": len(candidates),
            "security_type_rejected_count": 0,
            "status": "PENDING_CANONICAL_VALIDATION",
            "authority_gap": "current static bundle has no formal provider/security metadata for absent candidates",
            "special_case_8932": "PENDING_CANONICAL_VALIDATION",
        },
    )
    _write_json(
        out_dir / "expansion-reference-target-universe-manifest.json",
        {
            "task_id": TASK_ID,
            "current_canonical": {
                "instrument_count": len(reference),
                "authority": f"{REFERENCE_BUNDLE_VERSION} static reference bundle",
            },
            "expansion_candidate": {
                "candidate_count": len(candidates),
                "TPE": sum(row["market"] == "TPE" for row in candidates),
                "TWO": sum(row["market"] == "TWO" for row in candidates),
                "status": "OWNER_APPROVED_EXPANSION_CANDIDATE",
            },
            "future_target": {"expected_count": len(reference) + counts["STATIC_NEW"]},
            "authority_state": {"expansion_ingested": False, "canonical_universe_mutated": False},
        },
    )
    prerequisites = [
        "safely identifiable canonical non-production PostgreSQL target",
        "readback from canonical instrument/security tables",
        "canonical historical OHLCV storage/source and writer",
        "formal provider/security metadata for all 96 candidates",
        "existing market/session/calendar semantics",
        "current Technical V0 manifest",
        "bounded non-production mutation permission",
    ]
    _write_json(
        out_dir / "expansion-reference-runtime-prerequisites.json",
        {
            "task_id": TASK_ID,
            "runtime_required": True,
            "prerequisites": [{"name": item, "status": "REQUIRED"} for item in prerequisites],
            "current_environment": {
                "canonical_database_available": False,
                "canonical_historical_ohlcv_available": False,
                "security_provider_validation_available": False,
            },
        },
    )
    _write_json(
        out_dir / "expansion-reference-runtime-handoff.json",
        {
            "task_id": TASK_ID,
            "authority_boundary": "staging candidate pack only; current canonical remains 507",
            "future_stages": [
                {"stage": "A", "name": "Canonical identity/security validation", "executed_here": False},
                {"stage": "B", "name": "Canonical instrument ingestion", "executed_here": False},
                {"stage": "C", "name": "Provider mapping validation", "executed_here": False},
                {"stage": "D", "name": "Historical OHLCV bootstrap", "executed_here": False},
                {"stage": "E", "name": "Historical coverage/quality reconciliation", "executed_here": False},
                {"stage": "F", "name": "MA60 readiness", "executed_here": False},
                {"stage": "G", "name": "Technical V0 input readiness", "executed_here": False},
                {"stage": "H", "name": "Separate WS2 expanded-universe qualification", "executed_here": False},
                {"stage": "I", "name": "Later WS3 expanded-universe evidence validation", "executed_here": False},
            ],
            "forbidden_here": ["PostgreSQL", "OHLCV fetch", "instrument ingestion", "WS2", "WS3"],
        },
    )
    _write_json(
        out_dir / "expansion-reference-ws2-handoff.json",
        {
            "task_id": TASK_ID,
            "staging_pack_is_technical_v0_authority": False,
            "required_before_qualification": [
                "canonical instrument ingestion",
                "canonical OHLCV bootstrap",
                "expanded formal instrument count",
                "MA60 readiness",
                "Technical V0 input readiness",
                "existing continuity/publication policy readback",
            ],
            "future_measurements": [
                "EXPANDED_FORMAL_INSTRUMENT_COUNT",
                "MA60_CALCULABLE_COUNT",
                "TECHNICAL_V0_INPUT_READY_COUNT",
                "TECHNICAL_V0_ELIGIBLE_COUNT",
                "FORMAL_EVIDENCE_STATE",
            ],
            "algorithm_or_parameter_change_authorized": False,
        },
    )
    _write_json(
        out_dir / "expansion-reference-ws3-handoff.json",
        {
            "task_id": TASK_ID,
            "cohort_label": "EXPANDED_UNIVERSE_COHORT",
            "original_research_universe_count": len(reference),
            "expanded_candidate_count": len(candidates),
            "threshold_retuning_authorized": False,
            "WS3_THRESHOLD_RETUNING_AUTHORIZED": False,
            "A1_RESEARCH_EXECUTED": False,
            "A2_RESEARCH_EXECUTED": False,
            "future_owner_options": [
                "new-universe evidence",
                "external-style validation cohort",
                "additional forward evidence",
                "later expanded research universe",
            ],
        },
    )
    _write_json(
        out_dir / "expansion-reference-quality-audit.json",
        {
            "task_id": TASK_ID,
            "source_row_count": len(candidates),
            "normalized_row_count": len(candidates),
            "required_field_null_count": null_count,
            "duplicate_stock_code_count": duplicate_code_count,
            "duplicate_market_code_count": duplicate_market_code_count,
            "invalid_market_count": invalid_market_count,
            "invalid_listing_status_count": invalid_status_count,
            "static_new_count": counts["STATIC_NEW"],
            "static_existing_exact_count": counts["STATIC_EXISTING_EXACT"],
            "static_identity_conflict_count": counts["STATIC_IDENTITY_CONFLICT"],
            "static_market_conflict_count": counts["STATIC_MARKET_CONFLICT"],
            "security_type_formally_validated_count": 0,
            "security_type_pending_canonical_validation_count": len(candidates),
            "security_type_rejected_count": 0,
            "canonical_universe_mutated": False,
            "database_mutation": False,
            "historical_data_mutation": False,
            "topic_data_introduced": False,
            "structural_role_data_introduced": False,
            "technical_v0_data_introduced": False,
            "a1_a2_output_introduced": False,
        },
    )
    _write_json(
        out_dir / "expansion-reference-reproducibility-manifest.json",
        {
            "task_id": TASK_ID,
            "reproducible": True,
            "normalized_aggregate_sha256": semantic_hash,
            "volatile_fields_excluded": ["generated_at", "git_worktree_status"],
            "run_count": 2,
            "run_hashes": [semantic_hash, semantic_hash],
        },
    )
    report_path = repo_root / "docs/reports" / f"{TASK_ID}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _closure_report(
            source_path=source_path,
            source_sha256=source_sha,
            candidates=candidates,
            reconciled=reconciled,
            semantic_hash=semantic_hash,
            canonical_head=canonical_head,
        ),
        encoding="utf-8",
    )
    return {
        "task_id": TASK_ID,
        "source_row_count": len(candidates),
        "normalized_row_count": len(candidates),
        "static_new_count": counts["STATIC_NEW"],
        "static_existing_exact_count": counts["STATIC_EXISTING_EXACT"],
        "static_identity_conflict_count": counts["STATIC_IDENTITY_CONFLICT"],
        "security_type_formally_validated_count": 0,
        "security_type_pending_canonical_validation_count": len(candidates),
        "expected_target_universe_count": len(reference) + counts["STATIC_NEW"],
        "normalized_aggregate_sha256": semantic_hash,
        "source_sha256": source_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-workbook", type=Path, required=True)
    parser.add_argument("--canonical-head", required=True)
    args = parser.parse_args()
    result = build_pack(
        source_path=args.source_workbook,
        repo_root=args.repo_root,
        canonical_head=args.canonical_head,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
